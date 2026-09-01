"""

Dataset Creation for API Call sequence
Based on the paper:
    - Tang & Qian (IET Inf. Sec., 2019)
    - Dynamic API call sequence visualization for malware classification
    - Link: https://ietresearch.onlinelibrary.wiley.com/doi/pdf/10.1049/iet-ifs.2018.5268
API call sequence -> 16×16 feature image

Step 1 (Part B): Global timeline
    - Extract API calls (with timestamps) from all processes.
    - Sort strictly by time and zero-base the timeline.
    - Divide the total runtime into 16 equal time slices for the x-axis.

Step 2 (Part A) — 16-category API categorization:
    - Map each call to one of 16 fixed categories (row order matches slides).
    - Use Cuckoo's category names with regex fallbacks.

Step 2 (Part B) — Count per cell:
    - For each (category, row) x (time-slice,column), count occurrences.

Step 2 (Part C) — Image generation:
    - Encode counts as color: 0 calls -> white, the more calls the darker the shade
    - This follows Tang & Qian (IET Inf. Sec., 2019)

I/O
    - Inputs: <ROOT>/<FAMILY>/<N>.zip, inner …/reports/report.json
    - Outputs:  
            ./final_api_dataset_paper/<family>/<family>_<sample>_APIxTIME_16x16.png (dataset)
            ./final_api_dataset_paper/manifest.csv (per-sample statistics)
            ./final_api_dataset_paper/run.log (single representative log)
            
"""

from __future__ import annotations
import csv
import json
import logging
import math
import re
import sys
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from PIL import Image
from tqdm import tqdm  # progress bar

# Hyperparameter Section
DEFAULT_ROOTS = [
    # "/Users/mad_red_life/Desktop/Ai_Sec_Midterm/Malware_cuckoo_Jabir",
    # "/Users/mad_red_life/Desktop/Ai_Sec_Midterm/Malware_cuckoo_Gracenda",
    "/Users/jabir/Project/Malware Classification/Preprocessing/Malware Reports"
]
OUTPUT_DIRECTORY = "./dataset_api_call_sequences"
SLICES = 16
ROWS = 16

# Step 2A (slides): 16 category names in fixed row order (y-axis, top to bottom).
CATEGORY_NAMES = [
    "networking",
    "register",
    "service",
    "file",
    "hardware and system",
    "message",
    "process and thread",
    "system",
    "shellcode",
    "keylogging",
    "obfuscation",
    "password dumping/hash",
    "anti-debugging/reversing",
    "handle manipulation",
    "high risk",
    "other",
]
CATEGORY_INDEX = {name: i for i, name in enumerate(CATEGORY_NAMES)}

# Cuckoo -> category, anything unknown goes into the "other" category.
CUCKOO_TO_CAT = {
    "network": CATEGORY_INDEX["networking"],
    "socket": CATEGORY_INDEX["networking"],
    "internet": CATEGORY_INDEX["networking"],
    "registry": CATEGORY_INDEX["register"],
    "services": CATEGORY_INDEX["service"],
    "service": CATEGORY_INDEX["service"],
    "file": CATEGORY_INDEX["file"],
    "filesystem": CATEGORY_INDEX["file"],
    "system": CATEGORY_INDEX["system"],
    "os": CATEGORY_INDEX["system"],
    "message": CATEGORY_INDEX["message"],
    "process": CATEGORY_INDEX["process and thread"],
    "thread": CATEGORY_INDEX["process and thread"],
    "synchronization": CATEGORY_INDEX["process and thread"],
}

# Regex fallbacks (used only when the Cuckoo category is absent/odd).
# Created by combining: Tang & Qian (IET Inf. Sec., 2019)
# And: Nawaz et al.: Metamorphic Malware Behavior Analysis using Sequential Pattern Mining (MLiSE 2021)
# Link: https://www.philippe-fournier-viger.com/MLiSE_2021_paper.pdf
API_REGEX_RULES: List[Tuple[re.Pattern, int]] = [
    (re.compile(r"(?i)Reg(Open|Set|Query|Create|Delete)"), CATEGORY_INDEX["register"]),
    (re.compile(r"(?i)(Create|Read|Write|Delete|Move|Copy)File|Find(First|Next)File"), CATEGORY_INDEX["file"]),
    (re.compile(r"(?i)(connect|send|recv|WSA|Internet(Open|Read|Connect))"), CATEGORY_INDEX["networking"]),
    (re.compile(r"(?i)(Create|Open|Terminate)Process|CreateRemoteThread"), CATEGORY_INDEX["process and thread"]),
    (re.compile(r"(?i)GetVersion|GetSystemInfo|NtQuerySystemInformation"), CATEGORY_INDEX["hardware and system"]),
    (re.compile(r"(?i)(FindWindow|ShowWindow|GetForegroundWindow|SendMessage|PostMessage)"), CATEGORY_INDEX["message"]),
    (re.compile(r"(?i)(Crypt|BCrypt|AES|MD5|SHA)"), CATEGORY_INDEX["obfuscation"]),
    (re.compile(r"(?i)(SetWindowsHook|GetAsyncKeyState|GetKeyState|WH_KEYBOARD)"), CATEGORY_INDEX["keylogging"]),
    (re.compile(r"(?i)(IsDebuggerPresent|CheckRemoteDebuggerPresent|OutputDebugString|NtSetInformationThread)"),
     CATEGORY_INDEX["anti-debugging/reversing"]),
    (re.compile(r"(?i)(VirtualAlloc(Ex)?|VirtualProtect|WriteProcessMemory|NtMapViewOfSection)"),
     CATEGORY_INDEX["shellcode"]),
    (re.compile(r"(?i)(OpenProcess(Token)?|DuplicateHandle|OpenThread)"), CATEGORY_INDEX["handle manipulation"]),
]

# HSL color settings: brightness encodes frequency (white means 0 calls)
# Note that there are 2 files that have no API calls (probably obscured)
# For example, Vidar 63
CATEGORY_HUES = np.linspace(0, 330, ROWS, endpoint=True)
SATURATION = 0.75
LIGHTNESS_MIN = 0.25
LIGHTNESS_MAX = 1.00

# Logging Setup, to get a feeling if everything worked correctly
def setup_logger(output_directory: Path) -> logging.Logger:
    output_directory.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("api_paper")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fh = logging.FileHandler(output_directory / "run.log", mode="w", encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s  %(message)s"))
    logger.addHandler(fh)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.WARNING)
    logger.addHandler(ch)
    return logger

# Core data structures
@dataclass(frozen=True)
class APICall:
    ts: float
    api: str
    cuckoo_cat: str

# Utility functions
def _safe_float_time(t: Any) -> Optional[float]:
    # Parse numeric or common string timestamps into float seconds
    if t is None:
        return None
    if isinstance(t, (int, float)):
        return float(t)
    if isinstance(t, str):
        s = t.strip()
        for fmt in ("%Y-%m-%d %H:%M:%S,%f",
                    "%Y-%m-%d %H:%M:%S.%f",
                    "%Y-%m-%dT%H:%M:%S.%fZ",
                    "%Y-%m-%dT%H:%M:%SZ",
                    "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(s, fmt).timestamp()
            except Exception:
                pass
        try:
            return float(s)
        except Exception:
            return None
    return None

def _hsl_to_rgb(h: float, s: float, l: float) -> Tuple[int, int, int]:
    # Minimal HSL -> RGB (h∈[0,360), s,l∈[0,1]) converter function
    c = (1 - abs(2*l - 1)) * s
    x = c * (1 - abs(((h / 60.0) % 2) - 1))
    m = l - c/2
    if   0 <= h < 60:   r1,g1,b1 = c,x,0
    elif 60 <= h < 120: r1,g1,b1 = x,c,0
    elif 120<= h < 180: r1,g1,b1 = 0,c,x
    elif 180<= h < 240: r1,g1,b1 = 0,x,c
    elif 240<= h < 300: r1,g1,b1 = x,0,c
    else:               r1,g1,b1 = c,0,x
    r,g,b = (r1+m), (g1+m), (b1+m)
    return int(round(r*255)), int(round(g*255)), int(round(b*255))

def _count_to_lightness(count: int, max_count: float) -> float:
    # Monotone mapping: 0 -> white, larger counts -> darker via log scaling
    if count <= 0 or max_count <= 0:
        return LIGHTNESS_MAX
    v = math.log1p(count) / math.log1p(max_count)
    return float(max(0.0, min(1.0, LIGHTNESS_MAX - (LIGHTNESS_MAX - LIGHTNESS_MIN) * v)))

# Read report.json from the provided zip files provided by Jabir and Gracenda
def read_report_from_zip(zip_path: Path) -> Optional[Dict[str, Any]]:
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
            pref = [n for n in names if n.lower().endswith("reports/report.json")]
            target = pref[0] if pref else None
            # If folder structure deviates still find the file
            if target is None:
                cand = [n for n in names if n.lower().endswith("report.json")]
                target = cand[0] if cand else None
            if not target:
                return None
            # Open and read the file
            with zf.open(target, "r") as f:
                raw = f.read()
            try:
                return json.loads(raw.decode("utf-8"))
            except UnicodeDecodeError:
                return json.loads(raw.decode("latin-1", errors="ignore"))
    except Exception:
        return None

# Step 1B: extract the API calls and normalize
def extract_calls(report: Dict[str, Any]) -> List[APICall]:
    # Collect all API calls with valid timestamps from all processes
    calls: List[APICall] = []
    beh = (report or {}).get("behavior") or {}
    for proc in (beh.get("processes") or []):
        for c in (proc.get("calls") or []):
            ts = _safe_float_time(c.get("time")) or _safe_float_time(c.get("timestamp"))
            if ts is None:
                continue
            calls.append(APICall(ts=ts, api=c.get("api") or "", cuckoo_cat=c.get("category") or ""))
    return calls

def zero_base_and_duration(calls_abs: List[APICall]) -> Tuple[List[APICall], float]:
    # Sort API calls by time. Shift so the earliest call is at t=0 then return total duration
    if not calls_abs:
        return [], 0.0
    calls_sorted = sorted(calls_abs, key=lambda x: x.ts)
    t0 = calls_sorted[0].ts
    shifted = [APICall(ts=c.ts - t0, api=c.api, cuckoo_cat=c.cuckoo_cat) for c in calls_sorted]
    return shifted, max(0.0, shifted[-1].ts)

# Step 2A: categorize the API calls using the helper functions
def categorize(api: str, cuckoo_cat: str) -> int:
    # Map to one of 16 categories (Cuckoo, then regex, else 'other')
    if cuckoo_cat:
        cid = CUCKOO_TO_CAT.get(cuckoo_cat.lower())
        if cid is not None:
            return cid
    for pat, cid in API_REGEX_RULES:
        if pat.search(api):
            return cid
    return CATEGORY_INDEX["other"]

# Step 2B: count the API calls per (row,col)
def build_matrix(calls: List[APICall], duration: float, slices: int) -> np.ndarray:
    # Return 16×16 integer counts (rows=categories, columns=time slices)
    mat = np.zeros((ROWS, slices), dtype=np.int32)
    if not calls or duration <= 0:
        return mat
    dt = duration / slices
    for c in calls:
        col = int(min(slices - 1, math.floor(c.ts / dt))) if dt > 0 else 0
        row = categorize(c.api, c.cuckoo_cat)
        mat[row, col] += 1
    return mat

# Step 2C: finally the image generation
def matrix_to_image(mat: np.ndarray, out_png: Path) -> None:
    # Encode API call counts as color (per-category hue, brightness resembles frequency)
    rows, cols = mat.shape
    max_count = float(mat.max())
    rgb = np.zeros((rows, cols, 3), dtype=np.uint8)
    for r in range(rows):
        hue = float(CATEGORY_HUES[r])
        for c in range(cols):
            cnt = int(mat[r, c])
            if cnt == 0:
                rgb[r, c] = (255, 255, 255)
            else:
                l = _count_to_lightness(cnt, max_count)
                rgb[r, c] = _hsl_to_rgb(hue, SATURATION, l)
    Image.fromarray(rgb, mode="RGB").save(out_png)

# Discovery of the files and saving extracts as work items to process
@dataclass
class WorkItem:
    family: str
    zip_path: Path

def discover(roots: List[Path]) -> List[WorkItem]:
    # Discovery helper function
    items: List[WorkItem] = []
    for root in roots:
        if not root.exists():
            continue
        for family_dir in sorted([p for p in root.iterdir() if p.is_dir()]):
            for z in sorted(family_dir.glob("*.zip")):
                items.append(WorkItem(family=family_dir.name, zip_path=z))
    return items

# Main function (this is where things happen)
def main():
    # Output directory and logger
    output_directory = Path(OUTPUT_DIRECTORY).expanduser()
    output_directory.mkdir(parents=True, exist_ok=True)
    logger = setup_logger(output_directory)

    # Discover the items
    roots = [Path(p).expanduser() for p in DEFAULT_ROOTS]
    items = discover(roots)
    total_items = len(items)
    if total_items == 0:
        print("[ERROR] No ZIP reports found under the default roots.", file=sys.stderr)
        return

    # Create the manifest file
    manifest = output_directory / "manifest.csv"
    with open(manifest, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["family", "sample", "zip_path", "total_calls", "total_runtime_sec", "png_path"])

        images_written = 0
        total_calls_all = 0
        zero_or_skipped = 0

        # Start processing (with TQDM loading bar :)
        print(f"Processing {total_items} ZIPs...")
        for it in tqdm(items, unit="zip", ncols=80):
            family_directory = output_directory / it.family
            family_directory.mkdir(parents=True, exist_ok=True)
            sample = it.zip_path.stem
            out_png = family_directory / f"{it.family}_{sample}_APIxTIME_{ROWS}x{SLICES}.png"

            report = read_report_from_zip(it.zip_path)
            if report is None:
                # No report? Create the all-white image and log it.
                white = np.full((ROWS, SLICES, 3), 255, dtype=np.uint8)
                Image.fromarray(white, mode="RGB").save(out_png)
                logger.info(f"[SKIP: no report.json] {it.family}/{sample} → white image {out_png}")
                print(f"[SKIPPED] {it.zip_path}")  # explicit console note
                w.writerow([it.family, sample, str(it.zip_path), 0, 0.0, str(out_png)])
                images_written += 1
                zero_or_skipped += 1
                continue

            calls_abs = extract_calls(report)
            calls, duration = zero_base_and_duration(calls_abs)

            if len(calls) == 0 or duration <= 0:
                # Zero-call report: white image.
                white = np.full((ROWS, SLICES, 3), 255, dtype=np.uint8)
                Image.fromarray(white, mode="RGB").save(out_png)
                logger.info(f"[ZERO-CALL] {it.family}/{sample}  calls=0  → white image {out_png}")
                w.writerow([it.family, sample, str(it.zip_path), 0, 0.0, str(out_png)])
                images_written += 1
                zero_or_skipped += 1
                continue

            # Create the image for API calls
            mat = build_matrix(calls, duration, SLICES)
            matrix_to_image(mat, out_png)

            total = int(mat.sum())
            w.writerow([it.family, sample, str(it.zip_path), total, float(duration), str(out_png)])
            logger.info(f"{it.family}/{sample}  calls={len(calls)}  runtime={duration:.6f}s  total_binned={total}  → {out_png}")

            images_written += 1
            total_calls_all += len(calls)

    # Final Summary of the transformation
    print(f"[OK] ZIPs processed: {total_items}  |  images written: {images_written}")
    print(f"[OK] Manifest: {manifest}")
    print(f"[OK] Log: {output_directory/'run.log'}")
    print(f"[OK] Total API calls processed (non-zero reports): {total_calls_all}")
    print(f"[OK] Zero-call or skipped (white images): {zero_or_skipped}")

if __name__ == "__main__":
    main()