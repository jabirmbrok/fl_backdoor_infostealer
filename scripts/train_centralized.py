import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import torch
from torch import nn
from torch.utils.data import DataLoader

from src.data.image_dataset import MalwareImageDataset
from src.models.build import build_model
from src.training.engine import train_one_epoch, evaluate
from src.training.utils import load_yaml, set_seed, get_device, ensure_dir, save_checkpoint


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/centralized_rgb.yaml")
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

    train_ds = MalwareImageDataset(split_csv, "train", image_size=image_size, dataset_root=dataset_root)
    val_ds = MalwareImageDataset(split_csv, "val", image_size=image_size, dataset_root=dataset_root)
    test_ds = MalwareImageDataset(split_csv, "test", image_size=image_size, dataset_root=dataset_root)

    train_loader = DataLoader(train_ds, batch_size=cfg["train"]["batch_size"], shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=cfg["train"]["batch_size"], shuffle=False, num_workers=0)
    test_loader = DataLoader(test_ds, batch_size=cfg["train"]["batch_size"], shuffle=False, num_workers=0)

    model = build_model(
        cfg["model"]["name"],
        num_classes=int(cfg["model"]["num_classes"]),
        pretrained=bool(cfg["model"].get("pretrained", False)),
    ).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=float(cfg["train"]["lr"]),
        weight_decay=float(cfg["train"].get("weight_decay", 0.0)),
    )

    best_val_f1 = -1.0
    output_dir = Path(cfg["output_dir"])
    ensure_dir(output_dir)
    history = []

    for epoch in range(1, int(cfg["train"]["epochs"]) + 1):
        train_loss = train_one_epoch(model, train_loader, optimizer, criterion, device)
        val_metrics = evaluate(model, val_loader, criterion, device, int(cfg["model"]["num_classes"]))

        row = {
            "epoch": epoch,
            "train_loss": train_loss,
            "val_loss": val_metrics["loss"],
            "val_accuracy": val_metrics["accuracy"],
            "val_macro_f1": val_metrics["macro_f1"],
        }
        history.append(row)

        print(
            f"Epoch {epoch:03d} | "
            f"train_loss={train_loss:.4f} | "
            f"val_acc={val_metrics['accuracy']:.4f} | "
            f"val_f1={val_metrics['macro_f1']:.4f}"
        )

        if val_metrics["macro_f1"] > best_val_f1:
            best_val_f1 = val_metrics["macro_f1"]
            save_checkpoint(output_dir / "best_model.pt", model, {"epoch": epoch, "val_metrics": val_metrics})

    ckpt = torch.load(output_dir / "best_model.pt", map_location=device)
    model.load_state_dict(ckpt["model_state"])
    test_metrics = evaluate(model, test_loader, criterion, device, int(cfg["model"]["num_classes"]))

    with open(output_dir / "history.json", "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

    with open(output_dir / "test_metrics.json", "w", encoding="utf-8") as f:
        json.dump(test_metrics, f, indent=2)

    print("\nBest epoch:", ckpt["epoch"])
    print("Test accuracy:", round(test_metrics["accuracy"], 4))
    print("Test macro-F1:", round(test_metrics["macro_f1"], 4))
    print("Saved results to:", output_dir.resolve())

if __name__ == "__main__":
    main()
