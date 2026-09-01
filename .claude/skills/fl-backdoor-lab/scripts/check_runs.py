#!/usr/bin/env python3
"""Validate results/runs.csv and compare it with experiments/run_matrix.csv.

Usage:
  python check_runs.py                      # validate + summary per tier
  python check_runs.py --pending --tier 2   # list runs still to do in tier 2
  python check_runs.py --pending --training-only
  python check_runs.py --json               # machine-readable summary

Exit code 1 if runs.csv fails validation (so the runner stops before launching anything).
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[4]  # repo root (…/.claude/skills/fl-backdoor-lab/scripts -> root)
RUNS_COLS = ["exp_id", "scenario", "variant", "channel", "defense", "seed",
             "clean_acc", "macro_f1", "asr_hits", "asr_n", "notes"]
KEY = ["scenario", "variant", "channel", "defense", "seed"]
SCENARIOS = {"backbone_sel", "clean_fl", "trigger_control", "backdoor_fedavg", "backdoor_defense", "split"}
CHANNELS = {"none", "red", "green", "blue", "full"}
DEFENSES = {"none", "clipping", "median", "trimmed_mean", "multikrum"}
NEEDS_ASR = {"trigger_control", "backdoor_fedavg", "backdoor_defense"}


def load_runs(path: Path) -> tuple[pd.DataFrame, list[str]]:
    errors = []
    if not path.exists():
        return pd.DataFrame(columns=RUNS_COLS), [f"{path} does not exist"]
    df = pd.read_csv(path, dtype={"variant": str, "notes": str})
    missing = [c for c in RUNS_COLS if c not in df.columns]
    if missing:
        errors.append(f"runs.csv is missing columns: {missing}")
        return df, errors
    if df.empty:
        return df, errors
    df["variant"] = df["variant"].fillna("-").astype(str)
    df["notes"] = df["notes"].fillna("")

    dup_ids = df[df["exp_id"].duplicated(keep=False)]["exp_id"].unique().tolist()
    if dup_ids:
        errors.append(f"duplicate exp_id: {dup_ids}")
    dup_keys = df[df.duplicated(KEY, keep=False)]
    if not dup_keys.empty:
        errors.append("duplicate (scenario, variant, channel, defense, seed): "
                      + ", ".join(dup_keys["exp_id"].tolist()))
    bad = df[~df["scenario"].isin(SCENARIOS)]
    if not bad.empty:
        errors.append(f"unknown scenario values: {sorted(bad['scenario'].unique())} (allowed: {sorted(SCENARIOS)})")
    bad = df[~df["channel"].isin(CHANNELS)]
    if not bad.empty:
        errors.append(f"unknown channel values: {sorted(bad['channel'].unique())}")
    bad = df[~df["defense"].isin(DEFENSES)]
    if not bad.empty:
        errors.append(f"unknown defense values: {sorted(bad['defense'].unique())}")
    for col in ["clean_acc", "macro_f1"]:
        vals = pd.to_numeric(df[col], errors="coerce")
        if vals.isna().any():
            errors.append(f"{col} has empty or non-numeric values in: {df[vals.isna()]['exp_id'].tolist()}")
        elif ((vals < 0) | (vals > 1)).any():
            errors.append(f"{col} outside [0,1] in: {df[(vals < 0) | (vals > 1)]['exp_id'].tolist()}")
    hits = pd.to_numeric(df["asr_hits"], errors="coerce")
    n = pd.to_numeric(df["asr_n"], errors="coerce")
    need = df["scenario"].isin(NEEDS_ASR)
    if (need & (hits.isna() | n.isna())).any():
        errors.append("asr_hits/asr_n missing for attack rows: "
                      + ", ".join(df[need & (hits.isna() | n.isna())]["exp_id"].tolist()))
    if ((hits > n) & hits.notna()).any():
        errors.append("asr_hits > asr_n in: " + ", ".join(df[(hits > n) & hits.notna()]["exp_id"].tolist()))
    if ((n <= 0) & n.notna()).any():
        errors.append("asr_n must be > 0 in: " + ", ".join(df[(n <= 0) & n.notna()]["exp_id"].tolist()))
    return df, errors


def load_matrix(path: Path) -> pd.DataFrame:
    m = pd.read_csv(path, dtype={"variant": str, "note": str})
    m["variant"] = m["variant"].fillna("-").astype(str)
    return m


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", default=ROOT / "results" / "runs.csv", type=Path)
    ap.add_argument("--matrix", default=ROOT / "experiments" / "run_matrix.csv", type=Path)
    ap.add_argument("--tier", type=int, default=None, help="restrict to one tier (0, 2, 3)")
    ap.add_argument("--pending", action="store_true", help="list matrix rows not yet present in runs.csv")
    ap.add_argument("--training-only", action="store_true", help="with --pending: only rows that need training")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    runs, errors = load_runs(args.runs)
    matrix = load_matrix(args.matrix)
    if args.tier is not None:
        matrix = matrix[matrix["tier"] == args.tier]

    done_keys = set()
    if not runs.empty and not errors:
        done_keys = set(tuple(r) for r in runs[KEY].astype(str).itertuples(index=False, name=None))
    mkeys = [tuple(r) for r in matrix[KEY].astype(str).itertuples(index=False, name=None)]
    matrix = matrix.assign(in_runs=[k in done_keys for k in mkeys])

    extra = []
    if not runs.empty:
        mk = set(mkeys) if args.tier is None else set(
            tuple(r) for r in load_matrix(args.matrix)[KEY].astype(str).itertuples(index=False, name=None))
        extra = [r["exp_id"] for _, r in runs.iterrows()
                 if tuple(str(r[k]) for k in KEY) not in mk]

    summary = []
    for tier, g in matrix.groupby("tier"):
        summary.append(dict(tier=int(tier), rows=int(len(g)), in_runs=int(g["in_runs"].sum()),
                            pending=int((~g["in_runs"]).sum()),
                            pending_training=int(((~g["in_runs"]) & (g["needs_training"] == 1)).sum())))

    if args.json:
        pending = matrix[~matrix["in_runs"]]
        if args.training_only:
            pending = pending[pending["needs_training"] == 1]
        print(json.dumps(dict(errors=errors, summary=summary, pending=pending["exp_id"].tolist(),
                              not_in_matrix=extra), indent=2))
        return 1 if errors else 0

    if errors:
        print("runs.csv VALIDATION ERRORS:")
        for e in errors:
            print("  -", e)
    else:
        print(f"runs.csv OK: {len(runs)} rows")
    if extra:
        print(f"rows in runs.csv that are not in the run matrix ({len(extra)}): {extra}")
    print("\nper tier (rows / recorded in runs.csv / pending / pending that need training):")
    for s in summary:
        print(f"  tier {s['tier']}: {s['rows']:>3} / {s['in_runs']:>3} / {s['pending']:>3} / {s['pending_training']:>3}")

    if args.pending:
        pending = matrix[~matrix["in_runs"]]
        if args.training_only:
            pending = pending[pending["needs_training"] == 1]
        print(f"\npending ({len(pending)}):")
        for _, r in pending.iterrows():
            kind = "train" if r["needs_training"] == 1 else "eval "
            print(f"  [{kind}] {r['exp_id']:<34} tier {r['tier']}  {r['scenario']}/{r['variant']}/{r['channel']}/{r['defense']}  seed {r['seed']}  {r['note']}")
    return 1 if errors else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:  # e.g. piped into head
        sys.exit(0)
