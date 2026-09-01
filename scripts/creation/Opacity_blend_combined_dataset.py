from __future__ import annotations
from pathlib import Path
import re
from typing import Dict, Tuple, List, Optional
import numpy as np
from PIL import Image, ImageFilter
import pandas as pd
from tqdm import tqdm

# Hyperparameters
API_DIR = Path("./dataset_api_call_sequences")
NET_DIR = Path("./dataset_network_packets/images")
OUT_DIR = Path("dataset_opacity_blend")
EXTENSIONS = [".png", ".jpg", ".jpeg", ".bmp"]

# Image size (128 or 96 px)
TILE_SIZE = 128
RESAMPLE = Image.LANCZOS

# Overlay balance parameters
ALPHA = 0.70
BASE_GAIN = 0.70
TEX_GAIN  = 0.90

# Texture shaping parameters
CONTRAST_POW = 0.85
UNSHARP_RADIUS_TEX = 0.9
UNSHARP_PERCENT_TEX = 140
UNSHARP_THRESHOLD_TEX = 2

# Final crispness after blending
FINAL_UNSHARP_RADIUS = 0.6
FINAL_UNSHARP_PERCENT = 80
FINAL_UNSHARP_THRESHOLD = 2

# Skipping logic
SKIP_IF_NO_API = True
SKIP_IF_NO_SESSIONS = True

# Regex patterns (reused these :)
ID_REGEX_API = re.compile(r'_(\d+)', re.IGNORECASE)
ID_REGEX_NET = re.compile(r'/(\d+)/', re.IGNORECASE)
SESSION_ID_REGEX = re.compile(r'session(\d+)', re.IGNORECASE)

# Helper functions
def as_posix_relative(path: Path, root: Path) -> str:
    # Return a POSIX-style relative path string from `root` to `path`.
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def infer_label_from_parent(path: Path, root: Path) -> str:
    # Infers the top-level folder name (label) of a file relative to `root`.
    try:
        rel = path.relative_to(root)
    except ValueError:
        return ""
    parts = rel.parts
    return parts[0] if len(parts) >= 2 else ""


def extract_sample_id(path: Path, root: Path, pattern: Optional[re.Pattern[str]]) -> str:
    # Extracts a sample ID from a file path using a regex pattern.
    rel = as_posix_relative(path, root)
    if pattern is not None:
        m = pattern.search(rel)
        if m:
            return m.group(1).lower()
    return path.stem.lower()


def extract_session_id(path: Path, root: Path, pattern: Optional[re.Pattern[str]]) -> str:
    # Extracts a session ID from a path using a regex.
    rel = as_posix_relative(path, root)
    if pattern is not None:
        m = pattern.search(rel)
        if m:
            return m.group(1)
    m = re.search(r"session(\d+)", rel, re.IGNORECASE) or re.search(r"session(\d+)", path.stem, re.IGNORECASE)
    return m.group(1) if m else path.stem


def ensure_out_dir(root: Path) -> Path:
    # Creates the output directory if it doesn’t exist
    root.mkdir(parents=True, exist_ok=True)
    img_dir = root / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    return img_dir


def sanitize_filename(filename: str) -> str:
    # Replace invalid characters in the filename with underscores
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

# Image operations utilities.
def load_color(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB")

def load_gray(path: Path) -> Image.Image:
    return Image.open(path).convert("L")

def resize_exact(img: Image.Image, size: int) -> Image.Image:
    return img.resize((size, size), resample=RESAMPLE)

def normalize_0_1(img_l: Image.Image) -> np.ndarray:
    # Return float32 array in [0,1]; flat → zeros.
    arr = np.asarray(img_l, dtype=np.float32)
    mn, mx = float(arr.min()), float(arr.max())
    if mx <= mn:
        return np.zeros_like(arr, dtype=np.float32)
    return (arr - mn) / (mx - mn)

def unsharp(img: Image.Image, radius: float, percent: int, threshold: int) -> Image.Image:
    return img.filter(ImageFilter.UnsharpMask(radius=radius, percent=percent, threshold=threshold))

# Indexing utility functions
def index_api_single(api_root: Path, exts: List[str]) -> Dict[str, Tuple[Path, str]]:
    idx = {}
    for p in api_root.rglob("*"):
        if p.is_file() and p.suffix.lower() in exts:
            label = infer_label_from_parent(p, api_root) or "_nolabel"
            base_id = extract_sample_id(p, api_root, ID_REGEX_API)
            sid = f"{label}::{base_id}"
            if sid not in idx:
                idx[sid] = (p, label)
    return idx

def index_net_multi(net_root: Path, exts: List[str]) -> Dict[str, List[Tuple[Path, str, str]]]:
    from collections import defaultdict
    d = defaultdict(list)
    for p in net_root.rglob("*"):
        if p.is_file() and p.suffix.lower() in exts:
            label = infer_label_from_parent(p, net_root) or "_nolabel"
            base_id = extract_sample_id(p, net_root, ID_REGEX_NET)
            sid = f"{label}::{base_id}"
            sess = extract_session_id(p, net_root, SESSION_ID_REGEX)
            d[sid].append((p, label, sess))
    return d

# Image fusion
def make_texture(net_gray_resized: Image.Image) -> np.ndarray:
    # Texture T in [0,1] from NET gray:normalize to [0,1] + gamma/contrast shaping
    t = normalize_0_1(net_gray_resized)
    if CONTRAST_POW != 1.0 and CONTRAST_POW > 0:
        t = np.clip(t, 0.0, 1.0) ** CONTRAST_POW
    tex_u8 = (t * 255.0 + 0.5).astype(np.uint8)
    tex_img = Image.fromarray(tex_u8, mode="L")
    tex_img = unsharp(tex_img, UNSHARP_RADIUS_TEX, UNSHARP_PERCENT_TEX, UNSHARP_THRESHOLD_TEX)
    t2 = np.asarray(tex_img, dtype=np.float32) / 255.0
    return np.clip(t2, 0.0, 1.0)

def fuse_overlay(api_color_resized: Image.Image, net_gray_resized: Image.Image) -> Image.Image:
    # Overlay look with stronger texture and reduced API base:
    # Overlay = API * (BASE_GAIN + TEX_GAIN * T), where T in [0,1]
    # OUT = (1-ALPHA) * API + ALPHA * Overlay
    # Final: light unsharp for crispness.

    # Base color
    a = np.asarray(api_color_resized, dtype=np.float32) / 255.0

    # Texture from NET
    t = make_texture(net_gray_resized)
    k = BASE_GAIN + TEX_GAIN * t

    # Overlay image
    o = np.clip(a * k[..., None], 0.0, 1.0)

    # Alpha blend toward overlay
    output = np.clip((1.0 - ALPHA) * a + ALPHA * o, 0.0, 1.0)

    # Back to PIL + final sharpening
    out_u8 = (output * 255.0 + 0.5).astype(np.uint8)
    out_img = Image.fromarray(out_u8, mode="RGB")
    out_img = unsharp(out_img, FINAL_UNSHARP_RADIUS, FINAL_UNSHARP_PERCENT, FINAL_UNSHARP_THRESHOLD)
    return out_img

# Main method (this is where things happen :)
def main() -> None:
    # Echo deterministic config for reproducibility
    print("Strong-Texture Overlay (smaller, sharper, higher opacity)")
    print(f"[Config] API_DIR   : {API_DIR}")
    print(f"[Config] NET_DIR   : {NET_DIR}")
    print(f"[Config] OUT_DIR   : {OUT_DIR}")
    print(f"[Config] TILE_SIZE : {TILE_SIZE}, RESAMPLE={RESAMPLE}")
    print(f"[Config] ALPHA={ALPHA}, BASE_GAIN={BASE_GAIN}, TEX_GAIN={TEX_GAIN}, CONTRAST_POW={CONTRAST_POW}")
    print("")

    # Normalize allowed extensions to lowercase for case-insensitive matching
    exts = [e.lower() for e in EXTENSIONS]

    # Build 1:1 index of API color images
    print(f"[Index] API root: {API_DIR}")
    api_idx = index_api_single(API_DIR, exts)
    print(f"[Index] API samples: {len(api_idx)}")

    # Build 1:1 index of NET grayscale images (multiple sessions per sample)
    print(f"[Index] NET root: {NET_DIR}")
    net_idx = index_net_multi(NET_DIR, exts)
    net_sessions_total = sum(len(v) for v in net_idx.values())
    print(f"[Index] NET samples: {len(net_idx)} (sessions total: {net_sessions_total})")

    # Ensure output directories exist, initialize manifest rows
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "images").mkdir(parents=True, exist_ok=True)
    rows: List[dict] = []

    # Union of sample IDs across API and NET to maximize coverage
    all_ids = sorted(set(api_idx.keys()) | set(net_idx.keys()))
    print(f"[Pairing] total_ids={len(all_ids)}")

    # Audit lists for deterministic reporting of skipped samples
    skipped_no_api, skipped_no_sessions = [], []

    # Iterate over samples; expand to all sessions per sample for many-to-one fusion
    for sid in tqdm(all_ids, desc="Fusing (overlay strongtex × sessions)", unit="sample"):
        api_entry = api_idx.get(sid)
        nets = net_idx.get(sid, [])

        # Handle missing API image
        if api_entry is None:
            if SKIP_IF_NO_API:
                skipped_no_api.append(sid)
                continue
            else:
                api_img = Image.fromarray(np.zeros((TILE_SIZE, TILE_SIZE, 3), dtype=np.uint8), mode="RGB")
                api_label = "_nolabel"
                api_path = ""
        else:
            api_path, api_label = api_entry
            api_img = load_color(api_path)
            api_img = resize_exact(api_img, TILE_SIZE)

        # Handle missing NET sessions
        if len(nets) == 0:
            if SKIP_IF_NO_SESSIONS:
                skipped_no_sessions.append(sid)
                continue
            else:
                nets = [(None, api_label or "_nolabel", "nosession")]

        # Fuse API color with each available NET session texture
        for net_path, net_label, session_id in nets:
            # Load or synthesize grayscale texture input
            if net_path is None:
                net_img = Image.fromarray(np.zeros((TILE_SIZE, TILE_SIZE), dtype=np.uint8), mode="L")
                net_path_str = ""
            else:
                net_img = load_gray(net_path)
                net_img = resize_exact(net_img, TILE_SIZE)
                net_path_str = str(net_path)

            # Perform overlay fusion (per-pixel gain modulation and alpha blend)
            fused = fuse_overlay(api_img, net_img)

            # Resolve label precedence and prepare an output path
            label = api_label or net_label or "_nolabel"
            subdir = OUT_DIR / "images" / label
            subdir.mkdir(parents=True, exist_ok=True)

            # Deterministic filename encodes sample and session identity
            out_name = f"{sanitize_filename(sid)}__sess-{session_id}_overlay_strongtex.png"
            out_path = subdir / out_name
            fused.save(out_path)

            # Append structured record for downstream bookkeeping/analysis
            rows.append({
                "sample_id": sid,
                "session_id": session_id,
                "label": label,
                "api_path": str(api_path) if api_entry else "",
                "net_path": net_path_str,
                "fused_path": str(out_path),
                "fusion_mode": "overlay_strongtex",
                "tile_size": TILE_SIZE,
                "width": fused.size[0],
                "height": fused.size[1],
                "alpha": ALPHA,
                "base_gain": BASE_GAIN,
                "tex_gain": TEX_GAIN,
                "contrast_pow": CONTRAST_POW,
                "resize": str(RESAMPLE),
                "tex_unsharp": f"{UNSHARP_RADIUS_TEX}/{UNSHARP_PERCENT_TEX}/{UNSHARP_THRESHOLD_TEX}",
                "final_unsharp": f"{FINAL_UNSHARP_RADIUS}/{FINAL_UNSHARP_PERCENT}/{FINAL_UNSHARP_THRESHOLD}",
            })

    # Persist manifest as a reproducible, analysis-friendly CSV
    manifest_path = OUT_DIR / "manifest.csv"
    pd.DataFrame(rows).to_csv(manifest_path, index=False)

    # Final telemetry: production count and manifest location
    print(f"\n[Done] Wrote {len(rows)} fused images → {OUT_DIR / 'images'}")
    print(f"[Done] Manifest → {manifest_path}")

    # Explicit lists of skipped identifiers for traceability and debugging
    if skipped_no_api:
        print(f"[Skipped: no API image] {len(skipped_no_api)}")
        for s in skipped_no_api:
            print(f"  - {s}")
    if skipped_no_sessions:
        print(f"[Skipped: no NET sessions] {len(skipped_no_sessions)}")
        for s in skipped_no_sessions:
            print(f"  - {s}")


if __name__ == "__main__":
    main()
