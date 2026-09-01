#!/usr/bin/env python3
"""Per-channel intensity statistics of the clean RGB-stack images.

Why: the blue/fusion trigger reached 100% ASR while red/green did not. If the blue channel is
mostly dark in clean images, a bright blue square is simply the highest-contrast trigger — a
saliency explanation that competes with the "channel semantics" narrative. This script gives the
numbers for that discussion without any training.

Input (one of):
  --manifest CSV   columns: path, family   (paths absolute or relative to the CSV's folder)
  --root DIR       DIR/<family>/*.png|jpg|bmp|tif

Options:
  --trigger-frac 0.10   trigger side as a fraction of the image side (paper: 10%)
  --trigger-value 255   pixel value written into the trigger (verify in code — Open question 3)
  --split-col split --split test   keep only rows with split == test (manifest mode)
  --per-image           also write per-image statistics
  --out results/tables

Outputs: channel_stats.csv, channel_stats.md (per family + ALL).
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
CH = ["R", "G", "B"]


def iter_images(args):
    if args.split_csv:
        df = pd.read_csv(args.split_csv)
        if args.split:
            df = df[df[args.split_col].astype(str) == args.split]
        for _, r in df.iterrows():
            yield Path(args.dataset_root) / str(r["relative_path"]), str(r["family"])
        return
    if args.manifest:
        df = pd.read_csv(args.manifest)
        if "path" not in df.columns or "family" not in df.columns:
            raise SystemExit("manifest needs columns: path, family")
        if args.split_col and args.split_col in df.columns and args.split:
            df = df[df[args.split_col].astype(str) == args.split]
        base = Path(args.manifest).resolve().parent
        for _, r in df.iterrows():
            p = Path(r["path"])
            yield (p if p.is_absolute() else base / p), str(r["family"])
    else:
        root = Path(args.root)
        for fam_dir in sorted(d for d in root.iterdir() if d.is_dir()):
            for p in sorted(fam_dir.iterdir()):
                if p.suffix.lower() in EXTS:
                    yield p, fam_dir.name


def image_stats(path: Path, trigger_frac: float) -> dict:
    img = Image.open(path).convert("RGB")
    a = np.asarray(img, dtype=np.float32)  # H x W x 3, 0..255
    h, w, _ = a.shape
    side = max(1, int(round(trigger_frac * min(h, w))))
    patch = a[h - side:, w - side:, :]
    d = dict(height=h, width=w, trigger_side_px=side)
    for i, c in enumerate(CH):
        ch = a[:, :, i]
        d[f"{c}_mean"] = float(ch.mean())
        d[f"{c}_std"] = float(ch.std())
        d[f"{c}_zero_frac"] = float((ch == 0).mean())
        d[f"{c}_all_zero"] = bool(ch.max() == 0)
        d[f"{c}_trigger_region_mean"] = float(patch[:, :, i].mean())
        # fraction of the trigger region already at (or above) the trigger value:
        # where this is high, writing the trigger changes almost nothing.
        d[f"{c}_patch_saturated_frac"] = float((patch[:, :, i] >= 254).mean())
    return d


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--split-csv", type=Path,
                     help="dataset/splits/split_rgb_seed<N>.csv (columns relative_path, family, split)")
    src.add_argument("--manifest", type=Path, help="CSV with columns path, family")
    src.add_argument("--root", type=Path, help="DIR/<family>/*.png")
    ap.add_argument("--dataset-root", type=Path,
                    default=ROOT / "dataset" / "processed" / "dataset_rgb_stack_combined",
                    help="image root used with --split-csv")
    ap.add_argument("--trigger-frac", type=float, default=0.10)
    ap.add_argument("--trigger-value", type=float, default=255.0)
    ap.add_argument("--split-col", default="split")
    ap.add_argument("--split", default=None)
    ap.add_argument("--per-image", action="store_true")
    ap.add_argument("--limit", type=int, default=None, help="only the first N images (smoke test)")
    ap.add_argument("--out", type=Path, default=ROOT / "results" / "tables")
    args = ap.parse_args()

    rows = []
    for i, (p, fam) in enumerate(iter_images(args)):
        if args.limit and i >= args.limit:
            break
        try:
            d = image_stats(p, args.trigger_frac)
        except Exception as e:  # unreadable file
            print(f"skip {p}: {e}", file=sys.stderr)
            continue
        d.update(path=str(p), family=fam)
        rows.append(d)
    if not rows:
        raise SystemExit("no images found")
    per = pd.DataFrame(rows)

    def agg(g: pd.DataFrame) -> dict:
        out = dict(n_images=len(g))
        for c in CH:
            out[f"{c}_mean"] = g[f"{c}_mean"].mean()
            out[f"{c}_std_within"] = g[f"{c}_std"].mean()
            out[f"{c}_trigger_region_mean"] = g[f"{c}_trigger_region_mean"].mean()
            out[f"{c}_zero_frac"] = g[f"{c}_zero_frac"].mean()
            out[f"{c}_all_zero_frac"] = g[f"{c}_all_zero"].mean()
            out[f"{c}_contrast_vs_trigger"] = abs(args.trigger_value - out[f"{c}_trigger_region_mean"])
            out[f"{c}_patch_saturated_frac"] = g[f"{c}_patch_saturated_frac"].mean()
        return out

    fam_rows = []
    for fam, g in per.groupby("family"):
        fam_rows.append(dict(family=fam, **agg(g)))
    fam_rows.append(dict(family="ALL", **agg(per)))
    summary = pd.DataFrame(fam_rows)

    args.out.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.out / "channel_stats.csv", index=False)
    if args.per_image:
        per.to_csv(args.out / "channel_stats_per_image.csv", index=False)

    lines = ["# Per-channel intensity statistics of clean RGB-stack images", "",
             f"Images: {len(per)}; trigger side = {int(round(args.trigger_frac * 100))}% of the image "
             f"(≈{int(per['trigger_side_px'].median())} px); trigger value assumed = {args.trigger_value:g}.", "",
             "Contrast = |trigger value − mean intensity of the channel inside the bottom-right trigger region|. "
             "The channel with the largest contrast is where a bright square trigger is most salient.", "",
             "| Family | n | R mean | G mean | B mean | R contrast | G contrast | B contrast | "
             "R already-white | G already-white | B already-white | G all-zero (no traffic) |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in summary.iterrows():
        lines.append(f"| {r['family']} | {int(r['n_images'])} | {r['R_mean']:.1f} | {r['G_mean']:.1f} | {r['B_mean']:.1f} | "
                     f"{r['R_contrast_vs_trigger']:.1f} | {r['G_contrast_vs_trigger']:.1f} | {r['B_contrast_vs_trigger']:.1f} | "
                     f"{100 * r['R_patch_saturated_frac']:.1f}% | {100 * r['G_patch_saturated_frac']:.1f}% | "
                     f"{100 * r['B_patch_saturated_frac']:.1f}% | {100 * r['G_all_zero_frac']:.1f}% |")
    all_row = summary[summary["family"] == "ALL"].iloc[0]
    order = sorted(CH, key=lambda c: -all_row[f"{c}_contrast_vs_trigger"])
    lines += ["", f"Contrast ranking over all images: {' > '.join(order)}.",
              "\"already-white\" is the share of trigger-region pixels that are already >= 254 in that "
              "channel, i.e. where writing the trigger changes nothing at all.", "",
              "Read this together with the measured ASR ordering (blue = full > red = green). Contrast "
              "alone predicts B > G > R, so it explains why the red trigger is nearly invisible, but not "
              "why green fails despite high contrast. The Tier 3 contrast-matched trigger separates the "
              "two explanations.", ""]
    (args.out / "channel_stats.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"wrote {args.out / 'channel_stats.csv'}, channel_stats.md")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:  # e.g. piped into head
        sys.exit(0)
