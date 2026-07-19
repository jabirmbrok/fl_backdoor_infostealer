import argparse
import copy
import json
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
from src.training.engine import train_one_epoch, evaluate
from src.training.utils import load_yaml, set_seed, get_device, ensure_dir, save_checkpoint


def aggregate_states(client_states, client_sizes):
    total = sum(client_sizes)
    new_state = copy.deepcopy(client_states[0])
    for k in new_state.keys():
        if not torch.is_floating_point(new_state[k]):
            new_state[k] = client_states[0][k]
            continue
        new_state[k] = sum(state[k] * (size / total) for state, size in zip(client_states, client_sizes))
    return new_state


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/fl_clean_rgb.yaml")
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

    df = pd.read_csv(split_csv)
    train_df = df[df["split"] == "train"].copy()

    global_model = build_model(cfg["model"]["name"], num_classes=num_classes, pretrained=False).to(device)
    criterion = nn.CrossEntropyLoss()

    val_ds = MalwareImageDataset(split_csv, "val", image_size=image_size, dataset_root=dataset_root)
    test_ds = MalwareImageDataset(split_csv, "test", image_size=image_size, dataset_root=dataset_root)
    val_loader = DataLoader(val_ds, batch_size=cfg["train"]["batch_size"], shuffle=False, num_workers=0)
    test_loader = DataLoader(test_ds, batch_size=cfg["train"]["batch_size"], shuffle=False, num_workers=0)

    output_dir = Path(cfg["output_dir"])
    ensure_dir(output_dir)
    history = []

    for round_id in range(1, int(cfg["fl"]["rounds"]) + 1):
        client_states = []
        client_sizes = []

        for client_id in range(num_clients):
            client_indices = train_df.index[train_df[client_col] == client_id].tolist()
            if len(client_indices) == 0:
                print(f"[WARN] Client {client_id} kosong, dilewati.")
                continue

            local_model = build_model(cfg["model"]["name"], num_classes=num_classes, pretrained=False).to(device)
            local_model.load_state_dict(copy.deepcopy(global_model.state_dict()))

            local_ds = MalwareImageDataset(
                split_csv,
                split="train",
                image_size=image_size,
                dataset_root=dataset_root,
                indices=client_indices,
            )
            local_loader = DataLoader(local_ds, batch_size=cfg["train"]["batch_size"], shuffle=True, num_workers=0)

            optimizer = torch.optim.AdamW(
                local_model.parameters(),
                lr=float(cfg["train"]["lr"]),
                weight_decay=float(cfg["train"].get("weight_decay", 0.0)),
            )

            for _ in range(int(cfg["fl"]["local_epochs"])):
                train_one_epoch(local_model, local_loader, optimizer, criterion, device)

            client_states.append({k: v.detach().cpu().clone() for k, v in local_model.state_dict().items()})
            client_sizes.append(len(local_ds))

        new_state = aggregate_states(client_states, client_sizes)
        global_model.load_state_dict(new_state)

        if round_id % int(cfg["fl"]["eval_every"]) == 0 or round_id == 1:
            val_metrics = evaluate(global_model, val_loader, criterion, device, num_classes)
            row = {
                "round": round_id,
                "val_accuracy": val_metrics["accuracy"],
                "val_macro_f1": val_metrics["macro_f1"],
            }
            history.append(row)
            print(
                f"Round {round_id:03d} | "
                f"val_acc={val_metrics['accuracy']:.4f} | "
                f"val_f1={val_metrics['macro_f1']:.4f}"
            )

    test_metrics = evaluate(global_model, test_loader, criterion, device, num_classes)
    save_checkpoint(output_dir / "final_model.pt", global_model, {"test_metrics": test_metrics})

    with open(output_dir / "history.json", "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

    with open(output_dir / "test_metrics.json", "w", encoding="utf-8") as f:
        json.dump(test_metrics, f, indent=2)

    print("\nFL clean test accuracy:", round(test_metrics["accuracy"], 4))
    print("FL clean test macro-F1:", round(test_metrics["macro_f1"], 4))
    print("Saved results to:", output_dir.resolve())

if __name__ == "__main__":
    main()
