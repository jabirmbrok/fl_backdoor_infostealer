import argparse
import csv
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
from src.training.engine import evaluate, attack_success_rate
from src.training.utils import load_yaml, set_seed, get_device, ensure_dir


def load_model_from_checkpoint(checkpoint_path, model_name, num_classes, device):
    model = build_model(model_name, num_classes=num_classes, pretrained=False).to(device)
    ckpt = torch.load(checkpoint_path, map_location=device)

    if isinstance(ckpt, dict) and "model_state" in ckpt:
        model.load_state_dict(ckpt["model_state"])
    elif isinstance(ckpt, dict):
        model.load_state_dict(ckpt)
    else:
        raise RuntimeError(f"Format checkpoint tidak dikenali: {checkpoint_path}")

    model.eval()
    return model


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/trigger_control/blue_clean_control.yaml")
    args = parser.parse_args()

    cfg = load_yaml(args.config)
    set_seed(int(cfg.get("seed", 42)))

    device = get_device()
    print("Device:", device)
    if device.type == "cuda":
        print("GPU:", torch.cuda.get_device_name(0))

    split_csv = cfg["data"]["split_csv"]
    dataset_root = cfg["data"]["dataset_root"]
    image_size = int(cfg["data"]["image_size"])
    num_classes = int(cfg["model"]["num_classes"])
    model_name = cfg["model"]["name"]

    source_label = int(cfg["control"]["source_label"])
    target_label = int(cfg["control"]["target_label"])
    trigger_channel = cfg["control"]["trigger_channel"]
    trigger_size_ratio = float(cfg["control"]["trigger_size_ratio"])
    trigger_location = cfg["control"]["trigger_location"]
    checkpoint_path = cfg["control"]["checkpoint_path"]

    output_dir = Path(cfg["output_dir"])
    ensure_dir(output_dir)

    model = load_model_from_checkpoint(checkpoint_path, model_name, num_classes, device)
    criterion = nn.CrossEntropyLoss()

    df = pd.read_csv(split_csv)

    test_ds = MalwareImageDataset(
        split_csv,
        split="test",
        image_size=image_size,
        dataset_root=dataset_root,
    )
    test_loader = DataLoader(test_ds, batch_size=int(cfg["control"]["batch_size"]), shuffle=False, num_workers=0)

    source_test_indices = df.index[(df["split"] == "test") & (df["label_id"] == source_label)].tolist()
    if len(source_test_indices) == 0:
        raise RuntimeError(f"Tidak ada test sample untuk source_label={source_label}")

    clean_source_test = MalwareImageDataset(
        split_csv,
        split="test",
        image_size=image_size,
        dataset_root=dataset_root,
        indices=source_test_indices,
        triggered=False,
    )
    clean_source_loader = DataLoader(
        clean_source_test,
        batch_size=int(cfg["control"]["batch_size"]),
        shuffle=False,
        num_workers=0,
    )

    triggered_source_test = MalwareImageDataset(
        split_csv,
        split="test",
        image_size=image_size,
        dataset_root=dataset_root,
        indices=source_test_indices,
        triggered=True,
        trigger_channel=trigger_channel,
        trigger_size_ratio=trigger_size_ratio,
        trigger_location=trigger_location,
        source_label=None,
        target_label=None,
    )
    triggered_source_loader = DataLoader(
        triggered_source_test,
        batch_size=int(cfg["control"]["batch_size"]),
        shuffle=False,
        num_workers=0,
    )

    clean_test_metrics = evaluate(model, test_loader, criterion, device, num_classes)

    # Target prediction rate pada source clean tanpa trigger.
    clean_source_tpr = attack_success_rate(model, clean_source_loader, device, target_label)

    # Target prediction rate pada source dengan trigger, tetapi model clean.
    triggered_source_tpr = attack_success_rate(model, triggered_source_loader, device, target_label)

    result = {
        "experiment": cfg.get("experiment_name", Path(args.config).stem),
        "checkpoint_path": checkpoint_path,
        "trigger_channel": trigger_channel,
        "trigger_size_ratio": trigger_size_ratio,
        "trigger_location": trigger_location,
        "source_label": source_label,
        "target_label": target_label,
        "source_test_count": len(source_test_indices),
        "clean_test_accuracy": clean_test_metrics["accuracy"],
        "clean_test_macro_f1": clean_test_metrics["macro_f1"],
        "clean_source_target_prediction_rate": clean_source_tpr,
        "triggered_source_target_prediction_rate": triggered_source_tpr,
    }

    out_json = output_dir / f"{result['experiment']}.json"
    out_csv = output_dir / f"{result['experiment']}.csv"

    with out_json.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(result.keys()))
        writer.writeheader()
        writer.writerow(result)

    print("\nTrigger control result")
    print("-" * 80)
    print("Experiment:", result["experiment"])
    print("Checkpoint:", checkpoint_path)
    print("Trigger channel:", trigger_channel)
    print("Source test count:", result["source_test_count"])
    print("Clean test accuracy:", round(result["clean_test_accuracy"], 4))
    print("Clean test macro-F1:", round(result["clean_test_macro_f1"], 4))
    print("Clean source -> target rate:", round(result["clean_source_target_prediction_rate"], 4))
    print("Triggered source -> target rate:", round(result["triggered_source_target_prediction_rate"], 4))
    print("Saved:", out_csv.resolve())

if __name__ == "__main__":
    main()
