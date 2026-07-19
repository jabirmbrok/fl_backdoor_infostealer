from pathlib import Path
from typing import Optional, Iterable

import pandas as pd
import torch
from torch.utils.data import Dataset
from PIL import Image
from torchvision import transforms


def build_transform(image_size: int = 128, train: bool = False):
    transform_list = [
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
    ]
    return transforms.Compose(transform_list)


def apply_square_trigger(
    x: torch.Tensor,
    channel: str = "full",
    size_ratio: float = 0.08,
    value: float = 1.0,
    location: str = "bottom_right",
) -> torch.Tensor:
    """
    x: tensor [C,H,W] setelah Normalize. Nilai trigger default 1.0 berarti putih pada skala normalized.
    channel: red/api, green/network, blue/fusion, full.
    """
    x = x.clone()
    c, h, w = x.shape
    patch = max(1, int(min(h, w) * size_ratio))

    if location == "bottom_right":
        y0, x0 = h - patch, w - patch
    elif location == "bottom_left":
        y0, x0 = h - patch, 0
    elif location == "top_right":
        y0, x0 = 0, w - patch
    elif location == "top_left":
        y0, x0 = 0, 0
    else:
        raise ValueError(f"Unknown trigger location: {location}")

    channel_map = {
        "red": [0], "api": [0],
        "green": [1], "network": [1],
        "blue": [2], "fusion": [2],
        "full": [0, 1, 2], "rgb": [0, 1, 2],
    }
    channels = channel_map.get(channel.lower())
    if channels is None:
        raise ValueError(f"Unknown trigger channel: {channel}")

    for ch in channels:
        if ch < c:
            x[ch, y0:y0 + patch, x0:x0 + patch] = value

    return x


class MalwareImageDataset(Dataset):
    def __init__(
        self,
        split_csv: str,
        split: str,
        image_size: int = 128,
        dataset_root: Optional[str] = None,
        indices: Optional[Iterable[int]] = None,
        triggered: bool = False,
        trigger_channel: str = "full",
        trigger_size_ratio: float = 0.08,
        trigger_location: str = "bottom_right",
        trigger_value: float = 1.0,
        source_label: Optional[int] = None,
        target_label: Optional[int] = None,
        poison_rate: float = 1.0,
        seed: int = 42,
    ):
        self.split_csv = Path(split_csv)
        self.df = pd.read_csv(self.split_csv)

        if split != "all":
            self.df = self.df[self.df["split"] == split].copy()

        if indices is not None:
            self.df = self.df.loc[list(indices)].copy()

        self.df = self.df.reset_index(drop=False).rename(columns={"index": "original_index"})

        self.dataset_root = Path(dataset_root) if dataset_root else None
        self.transform = build_transform(image_size=image_size, train=(split == "train"))

        self.triggered = triggered
        self.trigger_channel = trigger_channel
        self.trigger_size_ratio = trigger_size_ratio
        self.trigger_location = trigger_location
        self.trigger_value = trigger_value
        self.source_label = source_label
        self.target_label = target_label
        self.poison_rate = poison_rate

        self.poison_indices = set()
        if triggered and split == "train" and source_label is not None and poison_rate < 1.0:
            source_rows = self.df.index[self.df["label_id"] == source_label].to_numpy()
            import numpy as np
            rng = np.random.default_rng(seed)
            n_poison = max(1, int(len(source_rows) * poison_rate)) if len(source_rows) else 0
            chosen = rng.choice(source_rows, size=n_poison, replace=False) if n_poison > 0 else []
            self.poison_indices = set(map(int, chosen))

    def __len__(self):
        return len(self.df)

    def _resolve_path(self, row) -> Path:
        abs_path = Path(row["absolute_path"])
        if abs_path.exists():
            return abs_path

        if self.dataset_root is not None:
            candidate = self.dataset_root / row["relative_path"]
            if candidate.exists():
                return candidate

        # fallback relatif dari folder split csv
        candidate = self.split_csv.parent.parent.parent / "processed" / "dataset_rgb_stack_combined" / row["relative_path"]
        if candidate.exists():
            return candidate

        raise FileNotFoundError(f"Image tidak ditemukan: {row['relative_path']}")

    def __getitem__(self, idx: int):
        row = self.df.iloc[idx]
        path = self._resolve_path(row)
        label = int(row["label_id"])

        img = Image.open(path).convert("RGB")
        x = self.transform(img)

        apply_trigger = False
        if self.triggered:
            if self.source_label is None:
                apply_trigger = True
            elif int(row["label_id"]) == int(self.source_label):
                if len(self.poison_indices) == 0:
                    apply_trigger = True
                else:
                    apply_trigger = idx in self.poison_indices

        if apply_trigger:
            x = apply_square_trigger(
                x,
                channel=self.trigger_channel,
                size_ratio=self.trigger_size_ratio,
                value=self.trigger_value,
                location=self.trigger_location,
            )
            if self.target_label is not None:
                label = int(self.target_label)

        return x, torch.tensor(label, dtype=torch.long)
