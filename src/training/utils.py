import os
import random
from pathlib import Path

import numpy as np
import torch
import yaml


def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    # Reproducibility mode. Untuk speed maksimal bisa dimatikan.
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True


def get_device():
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def save_checkpoint(path, model, extra=None):
    ensure_dir(Path(path).parent)
    payload = {"model_state": model.state_dict()}
    if extra:
        payload.update(extra)
    torch.save(payload, path)
