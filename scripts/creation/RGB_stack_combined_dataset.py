from __future__ import annotations
from pathlib import Path
import re
from typing import Dict, Tuple, List, Optional
import numpy as np
from PIL import Image, ImageFilter
import pandas as pd
from tqdm import tqdm

# Hyperparameters (edit if needed)
API_DIR = Path("./dataset_api_call_sequences")
NET_DIR = Path("./dataset_network_packets/images")
OUT_DIR = Path("./dataset_rgb_stack_combined")

EXTENSIONS = [".png", ".jpg", ".jpeg", ".bmp"]
TILE_SIZE = 128
# per-image min-max to [0,255] before fusion
NORMALIZE = True
# skip samples with no NET sessions
SKIP_IF_NO_SESSIONS = True
# skip samples with no API image
SKIP_IF_NO_API = True

# Custom ID extraction
ID_REGEX_API = re.compile(r'_(\d+)', re.IGNORECASE)
ID_REGEX_NET  = re.compile(r'/(\d+)/', re.IGNORECASE)
SESSION_ID_REGEX = re.compile(r'session(\d+)', re.IGNORECASE)

# Utility functions
def as_posix_relative(path: Path, root: Path) -> str:
    # Create a clean relative path String
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name

def infer_label_from_parent(path: Path, root: Path) -> str:
    # Get label name from directory structure
    try:
        rel = path.relative_to(root)
    except ValueError:
        return ""
    parts = rel.parts
    return parts[0] if len(parts) >= 2 else ""

def extract_sample_id(path: Path, root: Path, pattern: Optional[re.Pattern[str]]) -> str:
    # Extract sample ID from the path
    rel = as_posix_relative(path, root)
    if pattern is not None:
        m = pattern.search(rel)
        if m:
            return m.group(1).lower()
    return path.stem.lower()

def extract_session_id(path: Path, root: Path, pattern: Optional[re.Pattern[str]]) -> str:
    # Extract session ID from the path
    rel = as_posix_relative(path, root)
    if pattern is not None:
        m = pattern.search(rel)
        if m:
            return m.group(1)
    m = re.search(r"session(\d+)", rel, re.IGNORECASE) or re.search(r"session(\d+)", path.stem, re.IGNORECASE)
    return m.group(1) if m else path.stem

def load_l(path: Path) -> Image.Image:
    # Loading an image file and converting it into a grayscale (luminance-only) format
    return Image.open(path).convert("L")

def normalize_l(img: Image.Image) -> Image.Image:
    # Grayscale intensity normalization on an image.
    # Ensures the pixel values span the full 0–255 range
    arr = np.asarray(img, dtype=np.float32)
    mn, mx = float(arr.min()), float(arr.max())
    if mx <= mn:
        return Image.fromarray(np.zeros_like(arr, dtype=np.uint8), mode="L")
    out = ((arr - mn) / (mx - mn) * 255.0 + 0.5).astype(np.uint8)
    return Image.fromarray(out, mode="L")

def resize_l(img: Image.Image, size: int) -> Image.Image:
    # Resize the greyscale image
    return img.resize((size, size), resample=Image.BICUBIC)

# Fusion (rgb_stack)
def fuse_rgb_stack(api_L: Image.Image, net_L: Image.Image) -> Image.Image:
    """
    RGB composite:
      R = API (grayscale)
      G = NET (grayscale)
      B = edges (mean(API, NET))
    """
    api_arr = np.asarray(api_L, np.uint8)
    net_arr = np.asarray(net_L, np.uint8)
    mean_img = Image.fromarray(((api_arr.astype(np.uint16) + net_arr.astype(np.uint16)) // 2).astype(np.uint8), "L")
    edge = mean_img.filter(ImageFilter.FIND_EDGES)
    return Image.merge("RGB", (api_L, net_L, edge))

# Indexing
def index_api_single(api_root: Path, exts: List[str]) -> Dict[str, Tuple[Path, str]]:
    # Sample_id + Family -> (api_path, label). First match wins.
    idx = {}
    for p in api_root.rglob("*"):
        if p.is_file() and p.suffix.lower() in exts:
            label = infer_label_from_parent(p, api_root) or "_nolabel"
            base_id = extract_sample_id(p, api_root, ID_REGEX_API)  # e.g., "117"
            sid = f"{label}::{base_id}"                             # e.g., "Vidar::117"
            if sid not in idx:
                idx[sid] = (p, label)
    return idx

def index_net_multi(net_root: Path, exts: List[str]) -> Dict[str, List[Tuple[Path, str, str]]]:
    # sample_id + Family -> list of (net_path, label, session_id)
    from collections import defaultdict
    d = defaultdict(list)
    for p in net_root.rglob("*"):
        if p.is_file() and p.suffix.lower() in exts:
            label = infer_label_from_parent(p, net_root) or "_nolabel"
            base_id = extract_sample_id(p, net_root, ID_REGEX_NET)  # e.g., "117"
            sid = f"{label}::{base_id}"                             # match API convention
            sess = extract_session_id(p, net_root, SESSION_ID_REGEX)
            d[sid].append((p, label, sess))
    return d

# Function to sanitize filenames
def sanitize_filename(filename: str) -> str:
    # Replace invalid characters in the filename with underscores
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

# Build dataset
def ensure_out_dir(root: Path) -> Path:
    # Ensure the output directory exists, if not create it
    root.mkdir(parents=True, exist_ok=True)
    img_dir = root / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    return img_dir

# Main method, this is where things happen
def main() -> None:
    print(f"[Index] API root: {API_DIR}")
    api_idx = index_api_single(API_DIR, [e.lower() for e in EXTENSIONS])
    print(f"[Index] API samples: {len(api_idx)}")

    print(f"[Index] NET root: {NET_DIR}")
    net_idx = index_net_multi(NET_DIR, [e.lower() for e in EXTENSIONS])
    net_sessions_total = sum(len(v) for v in net_idx.values())
    print(f"[Index] NET samples: {len(net_idx)} (sessions total: {net_sessions_total})")

    img_dir = ensure_out_dir(OUT_DIR)
    rows: List[dict] = []

    all_ids = sorted(set(api_idx.keys()) | set(net_idx.keys()))
    paired_ids = [sid for sid in all_ids if sid in api_idx and sid in net_idx and len(net_idx[sid]) > 0]
    print(f"[Pairing] total_ids={len(all_ids)} | paired_ids={len(paired_ids)}")

    # Iterate all sids
    for sid in tqdm(paired_ids, desc="Fusing (rgb_stack × sessions)", unit="sample"):
        api_path, api_label = api_idx.get(sid)
        nets = net_idx.get(sid, [])

        if SKIP_IF_NO_API and api_path is None:
            continue
        if SKIP_IF_NO_SESSIONS and len(nets) == 0:
            continue

        # Load once: API grayscale tile
        api_img = load_l(api_path)
        if NORMALIZE:
            api_img = normalize_l(api_img)
        api_img = resize_l(api_img, TILE_SIZE)

        # For each session, fuse and write
        for net_path, net_label, session_id in nets:
            net_img = load_l(net_path)
            if NORMALIZE:
                net_img = normalize_l(net_img)
            net_img = resize_l(net_img, TILE_SIZE)

            fused = fuse_rgb_stack(api_img, net_img)

            label = api_label or net_label or "_nolabel"
            subdir = img_dir / label
            subdir.mkdir(parents=True, exist_ok=True)

            # Sanitize filename before saving
            out_name = f"{sanitize_filename(sid)}__sess-{session_id}_rgb_stack.png"
            out_path = subdir / out_name
            fused.save(out_path)

            # Construct summary
            rows.append({
                "sample_id": sid,
                "session_id": session_id,
                "label": label,
                "api_path": str(api_path),
                "net_path": str(net_path),
                "fused_path": str(out_path),
                "fusion_mode": "rgb_stack",
                "size_each": TILE_SIZE,
                "fused_width": fused.size[0],
                "fused_height": fused.size[1],
                "normalized": int(NORMALIZE),
            })

    # Write manifest
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = OUT_DIR / "manifest.csv"
    pd.DataFrame(rows).to_csv(manifest_path, index=False)

    print(f"[Done] Wrote {len(rows)} fused images → {img_dir}")
    print(f"[Done] Manifest → {manifest_path}")

if __name__ == "__main__":
    main()
