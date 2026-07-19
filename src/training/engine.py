from typing import Dict
import numpy as np
import torch
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support, confusion_matrix


def train_one_epoch(model, loader, optimizer, criterion, device):
    model.train()
    total_loss = 0.0
    total_samples = 0

    for x, y in loader:
        x = x.to(device, non_blocking=True)
        y = y.to(device, non_blocking=True)

        optimizer.zero_grad(set_to_none=True)
        logits = model(x)
        loss = criterion(logits, y)
        loss.backward()
        optimizer.step()

        total_loss += float(loss.item()) * y.size(0)
        total_samples += y.size(0)

    return total_loss / max(1, total_samples)


@torch.no_grad()
def evaluate(model, loader, criterion, device, num_classes: int) -> Dict:
    model.eval()
    total_loss = 0.0
    total_samples = 0
    ys, preds = [], []

    for x, y in loader:
        x = x.to(device, non_blocking=True)
        y = y.to(device, non_blocking=True)

        logits = model(x)
        loss = criterion(logits, y)
        pred = torch.argmax(logits, dim=1)

        total_loss += float(loss.item()) * y.size(0)
        total_samples += y.size(0)
        ys.extend(y.cpu().numpy().tolist())
        preds.extend(pred.cpu().numpy().tolist())

    if len(ys) == 0:
        return {
            "loss": 0.0,
            "accuracy": 0.0,
            "macro_f1": 0.0,
            "confusion_matrix": np.zeros((num_classes, num_classes), dtype=int).tolist(),
        }

    precision, recall, f1, support = precision_recall_fscore_support(
        ys, preds, labels=list(range(num_classes)), zero_division=0
    )

    return {
        "loss": total_loss / max(1, total_samples),
        "accuracy": accuracy_score(ys, preds),
        "macro_f1": f1_score(ys, preds, average="macro", zero_division=0),
        "per_class_precision": precision.tolist(),
        "per_class_recall": recall.tolist(),
        "per_class_f1": f1.tolist(),
        "per_class_support": support.tolist(),
        "confusion_matrix": confusion_matrix(ys, preds, labels=list(range(num_classes))).tolist(),
    }


@torch.no_grad()
def attack_success_rate(model, loader, device, target_label: int) -> float:
    model.eval()
    total = 0
    success = 0
    for x, _ in loader:
        x = x.to(device, non_blocking=True)
        logits = model(x)
        pred = torch.argmax(logits, dim=1).cpu()
        total += pred.numel()
        success += int((pred == target_label).sum().item())
    return success / max(1, total)
