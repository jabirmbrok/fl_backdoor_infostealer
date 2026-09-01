#!/usr/bin/env python3
"""Export the existing results/ tree into the canonical results/runs.csv.

The repo already stores every finished run as results/<dir>/{final_metrics,test_metrics}.json plus
results/trigger_control/*.json. This script reads them, converts ASR ratios back to raw hit counts,
and writes one row per run, so every downstream table comes from a single file.

Usage:
  python export_runs.py --dry-run      # show what would be written
  python export_runs.py                # write results/runs.csv (refuses to clobber; use --force)
  python export_runs.py --force        # overwrite results/runs.csv

Nothing under results/ is modified apart from runs.csv itself.
"""
import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
RESULTS = ROOT / "results"
SPLITS = ROOT / "dataset" / "splits"
COLS = ["exp_id", "scenario", "variant", "channel", "defense", "seed",
        "clean_acc", "macro_f1", "asr_hits", "asr_n", "notes"]
ASR_N_DEFAULT = 15  # AgentTesla test samples per seed


def asr_to_hits(asr, n=ASR_N_DEFAULT):
    if asr is None:
        return "", ""
    hits = asr * n
    if abs(hits - round(hits)) > 1e-6:
        print(f"  ! ASR {asr} does not map to an integer count out of {n}", file=sys.stderr)
    return int(round(hits)), n


def seed_from_name(name, default=42):
    m = re.search(r"seed(\d+)", name)
    return int(m.group(1)) if m else default


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def rows_from_backbone(rows):
    """results/backbone_<rep>_<backbone>_seed<seed>/test_metrics.json"""
    for d in sorted(RESULTS.glob("backbone_*")):
        if not d.is_dir():
            continue
        f = d / "test_metrics.json"
        if not f.exists():
            continue
        m = re.match(r"backbone_(opacity_blend|rgb_stack)_(small_cnn|mobilenet_v2|resnet18)_seed(\d+)", d.name)
        if not m:
            print(f"  ? skipping unrecognised backbone dir {d.name}", file=sys.stderr)
            continue
        rep, bb, seed = m.group(1), m.group(2), int(m.group(3))
        j = load(f)
        rows.append(dict(exp_id=d.name, scenario="backbone_sel", variant=f"{rep}-{bb}",
                         channel="none", defense="none", seed=seed,
                         clean_acc=j["accuracy"], macro_f1=j["macro_f1"], asr_hits="", asr_n="",
                         notes=f"centralized, best-val checkpoint; split=split_{'rgb_stack' if rep == 'rgb_stack' else 'opacity_blend'}_seed{seed}.csv"))


def rows_from_clean_fl(rows):
    for d in sorted(RESULTS.glob("fl_clean_rgb_resnet18_iid_seed*")):
        f = d / "test_metrics.json"
        if not f.exists():
            continue
        seed = seed_from_name(d.name)
        m = re.match(r"fl_clean_rgb_resnet18_iid_seed\d+(?:_(\w+))?$", d.name)
        variant = m.group(1) if m and m.group(1) else "-"
        j = load(f)
        hist = load(d / "history.json") if (d / "history.json").exists() else []
        note = f"final round; rounds={len(hist)}"
        if len(hist) and len(hist) != 50:
            note += "  << NOT 50 ROUNDS — see docs/DISCREPANCIES.md"
        rows.append(dict(exp_id=d.name, scenario="clean_fl", variant=variant, channel="none",
                         defense="none", seed=seed, clean_acc=j["accuracy"], macro_f1=j["macro_f1"],
                         asr_hits="", asr_n="", notes=note))


def rows_from_backdoor(rows):
    for d in sorted(RESULTS.glob("fl_backdoor_*")):
        f = d / "final_metrics.json"
        if not f.exists():
            continue
        j = load(f)
        ch = j.get("trigger_channel", "?")
        seed = seed_from_name(d.name)
        poison = j.get("poison_rate")
        hist = load(d / "history.json") if (d / "history.json").exists() else []
        size = re.search(r"_s(\d+)_", d.name)
        variant = "at2fb"
        note = f"poison_rate={poison}; rounds={len(hist)}"
        if poison not in (0.2, 0.20):
            variant = f"at2fb-p{int(round(float(poison) * 100))}"
            note += "  << ablation, not in the paper's main tables"
        if size and size.group(1) != "10":
            variant += f"-s{size.group(1)}"
        if len(hist) and len(hist) != 50:
            note += f"  << {len(hist)} rounds"
        hits, n = asr_to_hits(j.get("asr_source_to_target"))
        cm = j["clean_test_metrics"]
        rows.append(dict(exp_id=d.name, scenario="backdoor_fedavg", variant=variant, channel=ch,
                         defense="none", seed=seed, clean_acc=cm["accuracy"], macro_f1=cm["macro_f1"],
                         asr_hits=hits, asr_n=n, notes=note))


def rows_from_defense(rows):
    for d in sorted(RESULTS.glob("defense_*")):
        if not d.is_dir():
            continue
        f = d / "final_metrics.json"
        if not f.exists():
            continue
        j = load(f)
        m = re.match(r"defense_(blue|full|red|green)_(clipping|median|multi_krum|trimmed_mean)(?:_seed(\d+))?$", d.name)
        if not m:
            print(f"  ? skipping unrecognised defense dir {d.name}", file=sys.stderr)
            continue
        ch, defense, seed = m.group(1), m.group(2), int(m.group(3) or 42)
        defense = {"multi_krum": "multikrum"}.get(defense, defense)
        hits, n = asr_to_hits(j.get("asr_source_to_target"))
        cm = j["clean_test_metrics"]
        note = ""
        hist_f = d / "history.json"
        if hist_f.exists():
            hist = load(hist_f)
            sel = [r for r in hist if r.get("selected_clients") is not None]
            if sel:
                mal = sum(1 for r in sel if 0 in r["selected_clients"])
                note = f"malicious client selected in {mal}/{len(sel)} rounds"
        rows.append(dict(exp_id=d.name, scenario="backdoor_defense", variant="at2fb", channel=ch,
                         defense=defense, seed=seed, clean_acc=cm["accuracy"], macro_f1=cm["macro_f1"],
                         asr_hits=hits, asr_n=n, notes=note))


def rows_from_trigger_control(rows):
    for f in sorted((RESULTS / "trigger_control").glob("*.json")):
        j = load(f)
        m = re.match(r"clean_model_(blue|full|red|green)_trigger_control(?:_seed(\d+))?(?:_(r\d+))?$", f.stem)
        if not m:
            print(f"  ? skipping unrecognised trigger-control file {f.name}", file=sys.stderr)
            continue
        ch, seed = m.group(1), int(m.group(2) or 42)
        variant = "at2fb-" + m.group(3) if m.group(3) else "at2fb"
        n = int(j.get("source_test_count", ASR_N_DEFAULT))
        hits, n = asr_to_hits(j["triggered_source_target_prediction_rate"], n)
        clean_hits, _ = asr_to_hits(j["clean_source_target_prediction_rate"], n)
        note = (f"clean model, no poisoning; untriggered target rate {clean_hits}/{n}"
                + ("  << identical to triggered" if clean_hits == hits else ""))
        rows.append(dict(exp_id=f.stem, scenario="trigger_control", variant=variant, channel=ch,
                         defense="none", seed=seed, clean_acc=j["clean_test_accuracy"],
                         macro_f1=j["clean_test_macro_f1"], asr_hits=hits, asr_n=n, notes=note))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=RESULTS / "runs.csv")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    rows = []
    rows_from_backbone(rows)
    rows_from_clean_fl(rows)
    rows_from_backdoor(rows)
    rows_from_defense(rows)
    rows_from_trigger_control(rows)
    for r in rows:
        for k in ("clean_acc", "macro_f1"):
            r[k] = f"{float(r[k]):.4f}"

    print(f"{len(rows)} runs found:")
    for r in rows:
        asr = f"{r['asr_hits']}/{r['asr_n']}" if r["asr_n"] != "" else "-"
        flag = "  <<<" if "<<" in r["notes"] else ""
        print(f"  {r['exp_id']:<48} {r['scenario']:<17} {r['channel']:<6} {r['defense']:<10} "
              f"s{r['seed']:<5} acc {r['clean_acc']} f1 {r['macro_f1']} asr {asr}{flag}")

    if args.dry_run:
        print("\n(dry run — nothing written)")
        return 0
    if args.out.exists() and args.out.stat().st_size > 0 and not args.force:
        with args.out.open() as f:
            existing = sum(1 for _ in f) - 1
        if existing > 0:
            print(f"\n{args.out} already has {existing} rows. Re-run with --force to overwrite.")
            return 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {args.out}")
    flagged = [r["exp_id"] for r in rows if "<<" in r["notes"]]
    if flagged:
        print("rows flagged for review (see docs/DISCREPANCIES.md):")
        for e in flagged:
            print("  -", e)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        sys.exit(0)
