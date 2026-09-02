"""Regenerate the per-round figures from results/*/history.json.

The figure that shipped with the submission was exported at 8.5 in wide and then
placed in a 3.5 in column, so its 8 pt tick labels printed at about 2.3 pt. This
script exports at the final size instead, so the text prints at its true size.

Usage (from the repository root):
    python scripts/plot_per_round.py
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
OUT = ROOT / "paper" / "all_settings_f1_asr_per_round.pdf"

# Exported at the size it is placed at, with fonts that survive printing.
import sys
FIGSIZE = (3.45, float(sys.argv[1]) if len(sys.argv) > 1 else 2.10)   # inches; the IEEE column is 3.5 in
plt.rcParams.update({
    "font.size": 6.5,
    "axes.labelsize": 7,
    "xtick.labelsize": 6,
    "ytick.labelsize": 6,
    "legend.fontsize": 5.5,
    "axes.linewidth": 0.6,
    "lines.linewidth": 0.9,
    "grid.linewidth": 0.4,
    "xtick.major.width": 0.5,
    "ytick.major.width": 0.5,
    "pdf.fonttype": 42,
})

SERIES = [
    ("Blue + FedAvg", "tab:blue", [
        "fl_backdoor_rgb_resnet18_blue_p20_s10_r50",
        "fl_backdoor_rgb_resnet18_blue_p20_s10_seed123",
        "fl_backdoor_rgb_resnet18_blue_p20_s10_seed2026"]),
    ("Blue + Multi-Krum", "tab:orange", [
        "defense_blue_multi_krum",
        "defense_blue_multi_krum_seed123",
        "defense_blue_multi_krum_seed2026"]),
    ("Full-RGB + FedAvg", "tab:green", [
        "fl_backdoor_rgb_resnet18_full_p20_s10_r50",
        "fl_backdoor_rgb_resnet18_full_p20_s10_seed123",
        "fl_backdoor_rgb_resnet18_full_p20_s10_seed2026"]),
    ("Full-RGB + Multi-Krum", "tab:red", [
        "defense_full_multi_krum",
        "defense_full_multi_krum_seed123",
        "defense_full_multi_krum_seed2026"]),
]


def load(run: str, key: str) -> np.ndarray:
    with (RESULTS / run / "history.json").open(encoding="utf-8") as f:
        hist = json.load(f)
    return np.array([row[key] for row in hist], dtype=float)


def band(ax, key: str) -> None:
    for label, colour, runs in SERIES:
        curves = np.vstack([load(r, key) for r in runs])
        mean = curves.mean(axis=0)
        sd = curves.std(axis=0, ddof=1)
        rounds = np.arange(1, len(mean) + 1)
        ax.plot(rounds, mean, color=colour, label=label)
        ax.fill_between(rounds, mean - sd, mean + sd, color=colour, alpha=0.18, linewidth=0)


def main() -> None:
    fig, (ax_f1, ax_asr) = plt.subplots(2, 1, figsize=FIGSIZE, sharex=True)

    band(ax_f1, "clean_macro_f1")
    ax_f1.set_ylabel("Clean macro-F1")
    ax_f1.set_ylim(0.0, 1.05)

    band(ax_asr, "asr")
    ax_asr.set_ylabel("ASR")
    ax_asr.set_xlabel("Communication round")
    ax_asr.set_ylim(0.0, 1.05)

    for ax in (ax_f1, ax_asr):
        ax.grid(True, alpha=0.3)
        ax.margins(x=0.01)

    ax_f1.legend(ncol=2, loc="lower right", frameon=True, framealpha=0.9,
                 handlelength=1.4, columnspacing=0.9, borderpad=0.3, handletextpad=0.5)

    fig.tight_layout(pad=0.3)
    fig.savefig(OUT, bbox_inches="tight", pad_inches=0.01)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
