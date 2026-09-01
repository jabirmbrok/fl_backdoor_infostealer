#!/usr/bin/env python3
"""Significance tests on results/runs.csv (answers reviewers B and C).

Group keys are written as  scenario/variant/channel/defense  e.g.  backdoor_fedavg/at2fb/blue/none

Usage:
  python stats_tests.py                                  # run the default comparison set
  python stats_tests.py --fisher A B [--fisher C D ...]  # pooled Fisher exact test on ASR (A vs B)
  python stats_tests.py --paired A B --metric clean_acc  # paired t-test + Wilcoxon across seeds
  python stats_tests.py --shared-test-split              # add the pseudo-replication caveat to the report

Writes results/tables/stats.md and prints the same report.

Statistical notes (also written into the report):
  * Fisher exact pools triggered source-class samples across seeds. If the 15 test samples are the
    same in every seed (fixed split), the pooled test treats repeated evaluations of the same samples
    as independent — that is pseudo-replication. Report it as descriptive in that case.
  * Paired tests across seeds have n = number of seeds; with n = 3 the smallest two-sided Wilcoxon
    p-value is 0.25 and the t-test has 2 degrees of freedom. Say so in the paper.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[4]
GROUP = ["scenario", "variant", "channel", "defense"]

DEFAULT_FISHER = [
    ("backdoor_fedavg/at2fb/blue/none", "trigger_control/at2fb/blue/none"),
    ("backdoor_fedavg/at2fb/full/none", "trigger_control/at2fb/full/none"),
    ("backdoor_fedavg/at2fb/red/none", "trigger_control/at2fb/red/none"),
    ("backdoor_fedavg/at2fb/green/none", "trigger_control/at2fb/green/none"),
    ("backdoor_fedavg/at2fb/blue/none", "backdoor_defense/at2fb/blue/multikrum"),
    ("backdoor_fedavg/at2fb/full/none", "backdoor_defense/at2fb/full/multikrum"),
    ("backdoor_fedavg/at2fb/blue/none", "backdoor_fedavg/at2fb/red/none"),
    ("backdoor_fedavg/at2fb/blue/none", "backdoor_fedavg/at2fb/green/none"),
]
DEFAULT_PAIRED = [
    ("clean_fl/-/none/none", "backdoor_fedavg/at2fb/blue/none", "clean_acc"),
    ("clean_fl/-/none/none", "backdoor_fedavg/at2fb/blue/none", "macro_f1"),
    ("clean_fl/-/none/none", "backdoor_fedavg/at2fb/full/none", "clean_acc"),
    ("clean_fl/-/none/none", "backdoor_fedavg/at2fb/full/none", "macro_f1"),
    ("backdoor_fedavg/at2fb/blue/none", "backdoor_defense/at2fb/blue/multikrum", "clean_acc"),
    ("backdoor_fedavg/at2fb/full/none", "backdoor_defense/at2fb/full/multikrum", "clean_acc"),
]


def parse_key(key: str) -> dict:
    parts = key.split("/")
    if len(parts) != 4:
        raise SystemExit(f"bad group key '{key}' — use scenario/variant/channel/defense")
    return dict(zip(GROUP, parts))


def select(df: pd.DataFrame, key: str) -> pd.DataFrame:
    k = parse_key(key)
    m = np.ones(len(df), dtype=bool)
    for col, val in k.items():
        m &= (df[col].astype(str) == val).to_numpy()
    return df[m].sort_values("seed")


def fisher(df: pd.DataFrame, a: str, b: str, lines: list[str]) -> None:
    ga, gb = select(df, a), select(df, b)
    if ga.empty or gb.empty or ga["asr_n"].isna().any() or gb["asr_n"].isna().any():
        lines.append(f"- **{a} vs {b}**: skipped (group missing or without ASR)")
        return
    ha, na = int(ga["asr_hits"].sum()), int(ga["asr_n"].sum())
    hb, nb = int(gb["asr_hits"].sum()), int(gb["asr_n"].sum())
    table = [[ha, na - ha], [hb, nb - hb]]
    odds, p = stats.fisher_exact(table, alternative="two-sided")
    per_a = ", ".join(f"s{int(s)}: {int(h)}/{int(n)}" for s, h, n in zip(ga["seed"], ga["asr_hits"], ga["asr_n"]))
    per_b = ", ".join(f"s{int(s)}: {int(h)}/{int(n)}" for s, h, n in zip(gb["seed"], gb["asr_hits"], gb["asr_n"]))
    lines.append(f"- **{a}** ({ha}/{na} = {ha / na:.4f}; {per_a})  vs  **{b}** ({hb}/{nb} = {hb / nb:.4f}; {per_b})  "
                 f"→ Fisher exact two-sided p = {p:.4g}, odds ratio = {odds:.3g}")


def paired(df: pd.DataFrame, a: str, b: str, metric: str, lines: list[str]) -> None:
    ga, gb = select(df, a), select(df, b)
    m = ga[["seed", metric]].merge(gb[["seed", metric]], on="seed", suffixes=("_a", "_b"))
    if len(m) < 2:
        lines.append(f"- **{a} vs {b}** on {metric}: skipped (fewer than 2 shared seeds)")
        return
    x, y = m[f"{metric}_a"].to_numpy(float), m[f"{metric}_b"].to_numpy(float)
    d = y - x
    t_stat, t_p = stats.ttest_rel(y, x)
    try:
        w_stat, w_p = stats.wilcoxon(y, x)
        w_txt = f"Wilcoxon p = {w_p:.4g}"
    except ValueError as e:  # all differences zero
        w_txt = f"Wilcoxon n/a ({e})"
    pairs = ", ".join(f"s{int(s)}: {va:.4f}→{vb:.4f}" for s, va, vb in zip(m["seed"], x, y))
    lines.append(f"- **{a} → {b}** on {metric} (n = {len(m)} seeds): mean diff = {d.mean():+.4f} "
                 f"(sd {d.std(ddof=1):.4f}); paired t p = {t_p:.4g} (df = {len(m) - 1}); {w_txt}. [{pairs}]")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", default=ROOT / "results" / "runs.csv", type=Path)
    ap.add_argument("--out", default=ROOT / "results" / "tables" / "stats.md", type=Path)
    ap.add_argument("--fisher", nargs=2, action="append", metavar=("A", "B"))
    ap.add_argument("--paired", nargs=2, action="append", metavar=("A", "B"))
    ap.add_argument("--metric", default="clean_acc", choices=["clean_acc", "macro_f1"])
    ap.add_argument("--shared-test-split", action="store_true",
                    help="the test split is identical across seeds (pooling = pseudo-replication)")
    args = ap.parse_args()

    df = pd.read_csv(args.runs, dtype={"variant": str, "notes": str})
    if df.empty:
        print("runs.csv has no rows yet.")
        return 0
    df["variant"] = df["variant"].fillna("-").astype(str)

    lines = ["# Significance tests", ""]
    lines.append("## ASR comparisons — Fisher exact test on pooled triggered source-class samples")
    lines.append("")
    if args.shared_test_split:
        lines.append("> Caveat: the test split is the same in every seed, so pooled counts re-use the same 15 "
                     "samples across seeds (pseudo-replication). Treat these p-values as descriptive; the "
                     "per-seed hits/n are the primary evidence.")
    else:
        lines.append("> Note: pooling assumes the triggered samples are independent across seeds. State in the "
                     "paper whether the test split changes with the seed.")
    lines.append("")
    for a, b in (args.fisher or DEFAULT_FISHER):
        fisher(df, a, b, lines)

    lines += ["", "## Clean-performance comparisons — paired across seeds", "",
              "> n = number of shared seeds. With n = 3 the two-sided Wilcoxon minimum p is 0.25 and the "
              "paired t-test has 2 df; these tests are low-powered and should be reported with that caveat.", ""]
    if args.paired:
        for a, b in args.paired:
            paired(df, a, b, args.metric, lines)
    else:
        for a, b, metric in DEFAULT_PAIRED:
            paired(df, a, b, metric, lines)

    report = "\n".join(lines) + "\n"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report, encoding="utf-8")
    print(report)
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:  # e.g. piped into head
        sys.exit(0)
