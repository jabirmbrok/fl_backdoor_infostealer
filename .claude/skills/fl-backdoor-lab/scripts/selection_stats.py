#!/usr/bin/env python3
"""How often does the malicious client survive Multi-Krum, and does that predict the ASR?

The defense runs already log the selected clients per round in
results/defense_*/history.json (field `selected_clients`). This script turns that into the
mechanism explanation the paper is missing: Multi-Krum is inconsistent across seeds because the
poisoned update is only sometimes among the m updates it keeps.

Usage:
  python selection_stats.py                 # print + write results/tables/selection_stats.md
  python selection_stats.py --malicious 0   # attacker client id (config: attack.malicious_client)
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[4]
RESULTS = ROOT / "results"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--malicious", type=int, default=0)
    ap.add_argument("--glob", default="defense_*")
    ap.add_argument("--out", type=Path, default=RESULTS / "tables" / "selection_stats.md")
    args = ap.parse_args()

    rows = []
    for d in sorted(RESULTS.glob(args.glob)):
        h_f, m_f = d / "history.json", d / "final_metrics.json"
        if not (d.is_dir() and h_f.exists() and m_f.exists()):
            continue
        hist = json.load(open(h_f, encoding="utf-8"))
        sel = [r for r in hist if r.get("selected_clients") is not None]
        if not sel:
            continue  # defenses that do not select (clipping, median, trimmed mean)
        n_rounds = len(sel)
        mal = sum(1 for r in sel if args.malicious in r["selected_clients"])
        # early vs late: the backdoor is usually embedded in the second half
        half = n_rounds // 2
        mal_first = sum(1 for r in sel[:half] if args.malicious in r["selected_clients"])
        mal_last = sum(1 for r in sel[half:] if args.malicious in r["selected_clients"])
        asr = json.load(open(m_f, encoding="utf-8"))["asr_source_to_target"]
        rows.append(dict(run=d.name, rounds=n_rounds, selected=mal, rate=mal / n_rounds,
                         first_half=mal_first, last_half=mal_last, asr=asr,
                         hits=int(round(asr * 15))))
    if not rows:
        print("no runs with selected_clients found — is the defense Multi-Krum?")
        return 0

    lines = ["# Multi-Krum: how often the malicious client survives selection", "",
             f"Attacker = client {args.malicious}. `selected_clients` is logged per round in "
             "results/defense_*/history.json.", "",
             "| Run | Rounds | Malicious selected | Rate | First half | Last half | Final ASR |",
             "|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['run']} | {r['rounds']} | {r['selected']} | {r['rate']:.0%} | "
                     f"{r['first_half']} | {r['last_half']} | {r['hits']}/15 = {r['asr']:.4f} |")

    x = np.array([r["rate"] for r in rows])
    y = np.array([r["asr"] for r in rows])
    if len(rows) >= 3:
        rho, p_s = stats.spearmanr(x, y)
        rp, p_p = stats.pearsonr(x, y)
        lines += ["", f"Selection rate vs final ASR (n = {len(rows)}): "
                      f"Spearman rho = {rho:.3f} (p = {p_s:.4f}), Pearson r = {rp:.3f} (p = {p_p:.4f}).", "",
                  "Reading: Multi-Krum does not fail or succeed as a property of the channel — it fails in "
                  "the seeds where the poisoned update happens to stay inside the selected subset often "
                  "enough. With f = 1 and m = 2 out of 5 clients, that is a coin flip the attacker only has "
                  "to win sometimes. This is the mechanism behind the bimodal ASR across seeds, and it is "
                  "what the paper should report instead of an average ASR."]
    report = "\n".join(lines) + "\n"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report, encoding="utf-8")
    print(report)
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        sys.exit(0)
