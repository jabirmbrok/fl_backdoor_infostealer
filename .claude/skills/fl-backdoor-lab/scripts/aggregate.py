#!/usr/bin/env python3
"""Aggregate results/runs.csv into per-seed and mean ± std tables.

Outputs (in --out, default results/tables/):
  summary.csv   one row per (scenario, variant, channel, defense) with means, stds, per-seed lists
  summary.md    the same as a Markdown table, plus a per-seed long table
  summary.tex   booktabs LaTeX tables ready for \\input in the paper

Options:
  --scenario NAME        keep only one scenario (repeatable)
  --compare-paper CSV    compare means/stds with the numbers printed in the submitted paper
  --tol 0.0005           tolerance for the comparison (4-decimal rounding noise)

Conventions (match the paper): std uses ddof = 1; ASR per seed = asr_hits / asr_n; 4 decimals.
"""
import argparse
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
GROUP = ["scenario", "variant", "channel", "defense"]
SCENARIO_ORDER = ["backbone_sel", "clean_fl", "trigger_control", "backdoor_fedavg", "backdoor_defense"]
CHANNEL_ORDER = ["none", "red", "green", "blue", "full"]
DEFENSE_ORDER = ["none", "clipping", "median", "trimmed_mean", "multikrum"]


def f4(x) -> str:
    return "–" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.4f}"


def mean_std(vals: list[float]) -> tuple[float, float]:
    a = np.asarray(vals, dtype=float)
    if len(a) == 0:
        return float("nan"), float("nan")
    return float(a.mean()), (float(a.std(ddof=1)) if len(a) > 1 else float("nan"))


def ms(m, s, tex: bool = False) -> str:
    if isinstance(m, float) and math.isnan(m):
        return "--" if tex else "–"
    if math.isnan(s):
        return f4(m)
    return f"{m:.4f} $\\pm$ {s:.4f}" if tex else f"{m:.4f} ± {s:.4f}"


def tex_escape(s: str) -> str:
    return str(s).replace("_", "\\_").replace("%", "\\%")


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for key, g in df.groupby(GROUP, sort=False):
        g = g.sort_values("seed")
        seeds = g["seed"].astype(int).tolist()
        acc_m, acc_s = mean_std(g["clean_acc"].tolist())
        f1_m, f1_s = mean_std(g["macro_f1"].tolist())
        has_asr = g["asr_n"].notna().all() and len(g) > 0
        if has_asr:
            asr_seed = (g["asr_hits"] / g["asr_n"]).tolist()
            asr_m, asr_s = mean_std(asr_seed)
            hits, n = int(g["asr_hits"].sum()), int(g["asr_n"].sum())
            per_seed_asr = ", ".join(f"{int(h)}/{int(k)}" for h, k in zip(g["asr_hits"], g["asr_n"]))
            bimodal = (max(asr_seed) - min(asr_seed)) >= 0.5 if len(asr_seed) > 1 else False
        else:
            asr_m = asr_s = float("nan")
            hits = n = None
            per_seed_asr = ""
            bimodal = False
        rows.append(dict(
            scenario=key[0], variant=key[1], channel=key[2], defense=key[3],
            n_seeds=len(g), seeds=" ".join(map(str, seeds)),
            clean_acc_mean=acc_m, clean_acc_std=acc_s,
            macro_f1_mean=f1_m, macro_f1_std=f1_s,
            asr_mean=asr_m, asr_std=asr_s,
            asr_pooled=(f"{hits}/{n}" if has_asr else ""),
            asr_pooled_rate=(hits / n if has_asr else float("nan")),
            per_seed_clean_acc=", ".join(f"{v:.4f}" for v in g["clean_acc"]),
            per_seed_macro_f1=", ".join(f"{v:.4f}" for v in g["macro_f1"]),
            per_seed_asr=per_seed_asr,
            asr_range_ge_0_5=bimodal,
        ))
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["_s"] = out["scenario"].map({s: i for i, s in enumerate(SCENARIO_ORDER)}).fillna(99)
    out["_c"] = out["channel"].map({s: i for i, s in enumerate(CHANNEL_ORDER)}).fillna(99)
    out["_d"] = out["defense"].map({s: i for i, s in enumerate(DEFENSE_ORDER)}).fillna(99)
    return out.sort_values(["_s", "variant", "_c", "_d"]).drop(columns=["_s", "_c", "_d"]).reset_index(drop=True)


def to_markdown(summary: pd.DataFrame, runs: pd.DataFrame) -> str:
    lines = ["# Results summary", "",
             "Std uses ddof = 1 (as in the paper). ASR per seed = hits/n; pooled = sum(hits)/sum(n).", "",
             "| Scenario | Variant | Channel | Defense | Seeds | Clean acc | Macro-F1 | ASR | ASR pooled | ASR per seed | Note |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in summary.iterrows():
        note = "ASR range ≥ 0.5 across seeds — describe as bimodal/unstable, not as a mean" if r["asr_range_ge_0_5"] else ""
        lines.append(f"| {r['scenario']} | {r['variant']} | {r['channel']} | {r['defense']} | {r['n_seeds']} ({r['seeds']}) | "
                     f"{ms(r['clean_acc_mean'], r['clean_acc_std'])} | {ms(r['macro_f1_mean'], r['macro_f1_std'])} | "
                     f"{ms(r['asr_mean'], r['asr_std'])} | {r['asr_pooled']} | {r['per_seed_asr']} | {note} |")
    lines += ["", "## Per-seed values", "",
              "| exp_id | Scenario | Variant | Channel | Defense | Seed | Clean acc | Macro-F1 | ASR |",
              "|---|---|---|---|---|---|---|---|---|"]
    for _, r in runs.sort_values(GROUP + ["seed"]).iterrows():
        asr = "" if pd.isna(r["asr_n"]) else f"{int(r['asr_hits'])}/{int(r['asr_n'])} = {r['asr_hits'] / r['asr_n']:.4f}"
        lines.append(f"| {r['exp_id']} | {r['scenario']} | {r['variant']} | {r['channel']} | {r['defense']} | {int(r['seed'])} | "
                     f"{r['clean_acc']:.4f} | {r['macro_f1']:.4f} | {asr} |")
    return "\n".join(lines) + "\n"


def to_latex(summary: pd.DataFrame, runs: pd.DataFrame) -> str:
    out = ["% Generated by aggregate.py — do not edit by hand; regenerate from results/runs.csv.",
           "% Requires \\usepackage{booktabs}.", "",
           "\\begin{table}[t]", "\\centering",
           "\\caption{Mean $\\pm$ std across seeds (std with $n-1$). ASR is the fraction of triggered source-class test samples predicted as the target class.}",
           "\\label{tab:summary}", "\\small",
           "\\begin{tabular}{llllccc}", "\\toprule",
           "Scenario & Variant & Channel & Defense & Clean Acc. & Macro-F1 & ASR \\\\", "\\midrule"]
    for _, r in summary.iterrows():
        out.append(" & ".join([tex_escape(r["scenario"]), tex_escape(r["variant"]), tex_escape(r["channel"]),
                               tex_escape(r["defense"]),
                               ms(r["clean_acc_mean"], r["clean_acc_std"], tex=True),
                               ms(r["macro_f1_mean"], r["macro_f1_std"], tex=True),
                               ms(r["asr_mean"], r["asr_std"], tex=True)]) + " \\\\")
    out += ["\\bottomrule", "\\end{tabular}", "\\end{table}", "",
            "\\begin{table}[t]", "\\centering",
            "\\caption{Per-seed values (ASR shown as hits/$n$).}", "\\label{tab:per_seed}", "\\small",
            "\\begin{tabular}{lllcccc}", "\\toprule",
            "Scenario & Channel & Defense & Seed & Clean Acc. & Macro-F1 & ASR \\\\", "\\midrule"]
    for _, r in runs.sort_values(GROUP + ["seed"]).iterrows():
        asr = "--" if pd.isna(r["asr_n"]) else f"{int(r['asr_hits'])}/{int(r['asr_n'])}"
        out.append(" & ".join([tex_escape(r["scenario"]), tex_escape(r["channel"]), tex_escape(r["defense"]),
                               str(int(r["seed"])), f"{r['clean_acc']:.4f}", f"{r['macro_f1']:.4f}", asr]) + " \\\\")
    out += ["\\bottomrule", "\\end{tabular}", "\\end{table}", ""]
    return "\n".join(out)


def compare_with_paper(summary: pd.DataFrame, paper_csv: Path, tol: float) -> int:
    paper = pd.read_csv(paper_csv, dtype={"variant": str})
    paper["variant"] = paper["variant"].fillna("-")
    merged = paper.merge(summary, on=GROUP, how="left", suffixes=("_paper", "_ours"))
    mismatches = 0
    print(f"\nComparison with {paper_csv.name} (tolerance {tol}):")
    for _, r in merged.iterrows():
        label = f"{r['scenario']}/{r['variant']}/{r['channel']}/{r['defense']}"
        if pd.isna(r.get("n_seeds_ours")):
            print(f"  [missing ] {label}: not in runs.csv yet ({r['source_table']})")
            mismatches += 1
            continue
        probs = []
        for col in ["clean_acc_mean", "clean_acc_std", "macro_f1_mean", "macro_f1_std", "asr_mean", "asr_std"]:
            p, o = r[f"{col}_paper"], r[f"{col}_ours"]
            if pd.isna(p):
                continue
            if pd.isna(o) or abs(float(p) - float(o)) > tol:
                probs.append(f"{col}: paper {p} vs ours {f4(o)}")
        if int(r["n_seeds_paper"]) != int(r["n_seeds_ours"]):
            probs.append(f"n_seeds: paper {int(r['n_seeds_paper'])} vs ours {int(r['n_seeds_ours'])} (expected when new seeds were added)")
        if probs:
            mismatches += 1
            print(f"  [differs ] {label}: " + "; ".join(probs))
        else:
            print(f"  [match   ] {label}")
    return mismatches


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", default=ROOT / "results" / "runs.csv", type=Path)
    ap.add_argument("--out", default=ROOT / "results" / "tables", type=Path)
    ap.add_argument("--scenario", action="append", default=None)
    ap.add_argument("--compare-paper", type=Path, default=None)
    ap.add_argument("--tol", type=float, default=0.0005)
    args = ap.parse_args()

    runs = pd.read_csv(args.runs, dtype={"variant": str, "notes": str})
    if runs.empty:
        print("runs.csv has no rows yet — nothing to aggregate.")
        return 0
    runs["variant"] = runs["variant"].fillna("-").astype(str)
    if args.scenario:
        runs = runs[runs["scenario"].isin(args.scenario)]
    summary = summarize(runs)
    args.out.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.out / "summary.csv", index=False)
    (args.out / "summary.md").write_text(to_markdown(summary, runs), encoding="utf-8")
    (args.out / "summary.tex").write_text(to_latex(summary, runs), encoding="utf-8")

    with pd.option_context("display.width", 200, "display.max_columns", 20):
        show = summary[["scenario", "variant", "channel", "defense", "n_seeds", "clean_acc_mean", "clean_acc_std",
                        "macro_f1_mean", "macro_f1_std", "asr_mean", "asr_std", "asr_pooled", "asr_range_ge_0_5"]]
        print(show.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    flagged = summary[summary["asr_range_ge_0_5"]]
    if not flagged.empty:
        print("\nASR range ≥ 0.5 across seeds (report per seed, describe as bimodal/unstable):")
        for _, r in flagged.iterrows():
            print(f"  {r['scenario']}/{r['variant']}/{r['channel']}/{r['defense']}: {r['per_seed_asr']}")
    print(f"\nwrote {args.out / 'summary.csv'}, summary.md, summary.tex")

    if args.compare_paper:
        n_bad = compare_with_paper(summary, args.compare_paper, args.tol)
        print(f"{n_bad} group(s) differ from or are missing relative to the paper.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:  # e.g. piped into head
        sys.exit(0)
