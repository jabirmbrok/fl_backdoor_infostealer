import argparse
import copy
import json
import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader

from src.data.image_dataset import MalwareImageDataset
from src.models.build import build_model
from src.training.engine import train_one_epoch, evaluate, attack_success_rate
from src.training.utils import load_yaml, set_seed, get_device, ensure_dir, save_checkpoint


def subtract_states(local_state, global_state):
    update = {}
    for k, v in local_state.items():
        if torch.is_floating_point(v):
            update[k] = v.detach().cpu() - global_state[k].detach().cpu()
    return update


def add_update_to_state(global_state, update):
    new_state = copy.deepcopy(global_state)
    for k, v in update.items():
        if k in new_state and torch.is_floating_point(new_state[k]):
            new_state[k] = new_state[k].detach().cpu() + v.detach().cpu()
    return new_state


def flatten_update(update):
    return torch.cat([v.reshape(-1).float().cpu() for _, v in sorted(update.items())])


def weighted_mean_updates(updates, sizes):
    total = float(sum(sizes))
    out = {}
    for k in updates[0].keys():
        out[k] = sum(u[k] * (s / total) for u, s in zip(updates, sizes))
    return out


def clip_update(update, max_norm):
    flat = flatten_update(update)
    norm = torch.norm(flat, p=2).item()
    scale = min(1.0, max_norm / (norm + 1e-12))
    return {k: v * scale for k, v in update.items()}, norm, scale


def coordinate_median(updates):
    out = {}
    for k in updates[0].keys():
        stacked = torch.stack([u[k].float() for u in updates], dim=0)
        out[k] = torch.median(stacked, dim=0).values
    return out


def trimmed_mean(updates, trim_count):
    out = {}
    n = len(updates)
    if 2 * trim_count >= n:
        raise ValueError(f"trim_count terlalu besar untuk n={n}: {trim_count}")
    for k in updates[0].keys():
        stacked = torch.stack([u[k].float() for u in updates], dim=0)
        sorted_vals, _ = torch.sort(stacked, dim=0)
        trimmed = sorted_vals[trim_count:n - trim_count]
        out[k] = trimmed.mean(dim=0)
    return out


def krum_scores(flat_updates, f):
    n = len(flat_updates)
    neighbor_count = n - f - 2
    if neighbor_count < 1:
        raise ValueError(f"Krum butuh n - f - 2 >= 1, dapat n={n}, f={f}")

    scores = []
    for i in range(n):
        dists = []
        for j in range(n):
            if i == j:
                continue
            d = torch.sum((flat_updates[i] - flat_updates[j]) ** 2).item()
            dists.append(d)
        dists.sort()
        scores.append(sum(dists[:neighbor_count]))
    return scores


def multi_krum(updates, sizes, f, m):
    n = len(updates)
    if m is None:
        m = max(1, n - f - 2)
    if m < 1 or m > n:
        raise ValueError(f"multi_krum_selected tidak valid: {m}")

    flat_updates = [flatten_update(u) for u in updates]
    scores = krum_scores(flat_updates, f=f)
    selected = sorted(range(n), key=lambda i: scores[i])[:m]

    selected_updates = [updates[i] for i in selected]
    selected_sizes = [sizes[i] for i in selected]
    agg = weighted_mean_updates(selected_updates, selected_sizes)
    return agg, selected, scores


def aggregate_updates(updates, sizes, cfg_defense):
    name = cfg_defense["name"].lower()
    info = {"defense": name}

    if name == "fedavg":
        return weighted_mean_updates(updates, sizes), info

    if name == "clipping":
        max_norm = float(cfg_defense["max_norm"])
        clipped = []
        norms = []
        scales = []
        for u in updates:
            cu, norm, scale = clip_update(u, max_norm=max_norm)
            clipped.append(cu)
            norms.append(norm)
            scales.append(scale)
        info["client_update_norms"] = norms
        info["client_clip_scales"] = scales
        info["max_norm"] = max_norm
        return weighted_mean_updates(clipped, sizes), info

    if name == "median":
        return coordinate_median(updates), info

    if name == "trimmed_mean":
        trim_count = int(cfg_defense.get("trim_count", 1))
        info["trim_count"] = trim_count
        return trimmed_mean(updates, trim_count=trim_count), info

    if name == "multi_krum":
        f = int(cfg_defense.get("byzantine_clients", 1))
        m = cfg_defense.get("selected_clients", None)
        m = int(m) if m is not None else None
        agg, selected, scores = multi_krum(updates, sizes, f=f, m=m)
        info["byzantine_clients"] = f
        info["selected_clients"] = selected
        info["krum_scores"] = scores
        return agg, info

    raise ValueError(f"Defense tidak dikenali: {name}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/defense/blue_median.yaml")
    args = parser.parse_args()

    cfg = load_yaml(args.config)
    set_seed(int(cfg["seed"]))

    device = get_device()
    print("Device:", device)
    if device.type == "cuda":
        print("GPU:", torch.cuda.get_device_name(0))

    split_csv = cfg["data"]["split_csv"]
    dataset_root = cfg["data"].get("dataset_root", None)
    image_size = int(cfg["data"]["image_size"])
    num_classes = int(cfg["model"]["num_classes"])
    client_col = cfg["fl"]["client_col"]
    num_clients = int(cfg["fl"]["num_clients"])

    source_label = int(cfg["attack"]["source_label"])
    target_label = int(cfg["attack"]["target_label"])
    malicious_client = int(cfg["attack"]["malicious_client"])
    poison_rate = float(cfg["attack"]["poison_rate"])

    df = pd.read_csv(split_csv)
    train_df = df[df["split"] == "train"].copy()

    global_model = build_model(cfg["model"]["name"], num_classes=num_classes, pretrained=False).to(device)
    criterion = nn.CrossEntropyLoss()

    test_ds = MalwareImageDataset(split_csv, "test", image_size=image_size, dataset_root=dataset_root)
    test_loader = DataLoader(test_ds, batch_size=cfg["train"]["batch_size"], shuffle=False, num_workers=0)

    source_test_indices = df.index[(df["split"] == "test") & (df["label_id"] == source_label)].tolist()
    triggered_source_test = MalwareImageDataset(
        split_csv,
        split="test",
        image_size=image_size,
        dataset_root=dataset_root,
        indices=source_test_indices,
        triggered=True,
        trigger_channel=cfg["attack"]["trigger_channel"],
        trigger_size_ratio=float(cfg["attack"]["trigger_size_ratio"]),
        trigger_location=cfg["attack"]["trigger_location"],
        source_label=None,
        target_label=None,
    )
    triggered_loader = DataLoader(
        triggered_source_test,
        batch_size=cfg["train"]["batch_size"],
        shuffle=False,
        num_workers=0,
    )

    output_dir = Path(cfg["output_dir"])
    ensure_dir(output_dir)
    history = []

    for round_id in range(1, int(cfg["fl"]["rounds"]) + 1):
        global_state_cpu = {k: v.detach().cpu().clone() for k, v in global_model.state_dict().items()}
        client_updates = []
        client_sizes = []
        round_info = {}

        for client_id in range(num_clients):
            client_indices = train_df.index[train_df[client_col] == client_id].tolist()
            if len(client_indices) == 0:
                print(f"[WARN] Client {client_id} kosong, dilewati.")
                continue

            is_malicious = client_id == malicious_client

            local_model = build_model(cfg["model"]["name"], num_classes=num_classes, pretrained=False).to(device)
            local_model.load_state_dict(copy.deepcopy(global_model.state_dict()))

            local_ds = MalwareImageDataset(
                split_csv,
                split="train",
                image_size=image_size,
                dataset_root=dataset_root,
                indices=client_indices,
                triggered=is_malicious,
                trigger_channel=cfg["attack"]["trigger_channel"],
                trigger_size_ratio=float(cfg["attack"]["trigger_size_ratio"]),
                trigger_location=cfg["attack"]["trigger_location"],
                source_label=source_label,
                target_label=target_label,
                poison_rate=poison_rate,
                seed=int(cfg["seed"]) + round_id + client_id,
            )
            local_loader = DataLoader(local_ds, batch_size=cfg["train"]["batch_size"], shuffle=True, num_workers=0)

            optimizer = torch.optim.AdamW(
                local_model.parameters(),
                lr=float(cfg["train"]["lr"]),
                weight_decay=float(cfg["train"].get("weight_decay", 0.0)),
            )

            for _ in range(int(cfg["fl"]["local_epochs"])):
                train_one_epoch(local_model, local_loader, optimizer, criterion, device)

            local_state_cpu = {k: v.detach().cpu().clone() for k, v in local_model.state_dict().items()}
            update = subtract_states(local_state_cpu, global_state_cpu)
            client_updates.append(update)
            client_sizes.append(len(local_ds))

        aggregated_update, agg_info = aggregate_updates(client_updates, client_sizes, cfg["defense"])
        new_state = add_update_to_state(global_state_cpu, aggregated_update)
        global_model.load_state_dict(new_state)

        if round_id % int(cfg["fl"]["eval_every"]) == 0 or round_id == 1:
            clean_metrics = evaluate(global_model, test_loader, criterion, device, num_classes)
            asr = attack_success_rate(global_model, triggered_loader, device, target_label)
            row = {
                "round": round_id,
                "clean_accuracy": clean_metrics["accuracy"],
                "clean_macro_f1": clean_metrics["macro_f1"],
                "asr": asr,
                "defense": cfg["defense"]["name"],
            }
            if cfg["defense"]["name"].lower() == "multi_krum":
                row["selected_clients"] = agg_info.get("selected_clients")
            history.append(row)
            print(
                f"Round {round_id:03d} | "
                f"defense={cfg['defense']['name']} | "
                f"clean_acc={clean_metrics['accuracy']:.4f} | "
                f"clean_f1={clean_metrics['macro_f1']:.4f} | "
                f"ASR={asr:.4f}"
            )

    clean_metrics = evaluate(global_model, test_loader, criterion, device, num_classes)
    asr = attack_success_rate(global_model, triggered_loader, device, target_label)

    final_metrics = {
        "experiment": cfg.get("experiment_name", Path(args.config).stem),
        "defense": cfg["defense"]["name"],
        "clean_test_metrics": clean_metrics,
        "asr_source_to_target": asr,
        "source_label": source_label,
        "target_label": target_label,
        "malicious_client": malicious_client,
        "trigger_channel": cfg["attack"]["trigger_channel"],
        "trigger_size_ratio": float(cfg["attack"]["trigger_size_ratio"]),
        "poison_rate": poison_rate,
        "rounds": int(cfg["fl"]["rounds"]),
        "local_epochs": int(cfg["fl"]["local_epochs"]),
        "client_col": client_col,
        "defense_config": cfg["defense"],
    }

    save_checkpoint(output_dir / "final_defended_model.pt", global_model, {"final_metrics": final_metrics})

    with open(output_dir / "history.json", "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

    with open(output_dir / "final_metrics.json", "w", encoding="utf-8") as f:
        json.dump(final_metrics, f, indent=2)

    print("\nDefense experiment:", final_metrics["experiment"])
    print("Defense:", cfg["defense"]["name"])
    print("Clean test accuracy:", round(clean_metrics["accuracy"], 4))
    print("Clean test macro-F1:", round(clean_metrics["macro_f1"], 4))
    print("ASR:", round(asr, 4))
    print("Saved results to:", output_dir.resolve())

if __name__ == "__main__":
    main()
