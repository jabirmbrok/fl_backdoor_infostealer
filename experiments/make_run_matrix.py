#!/usr/bin/env python3
"""Regenerate experiments/run_matrix.csv.

Edit the seed lists or add rows here, then run:  python experiments/make_run_matrix.py
The matrix is the single queue that /lab-run and check_runs.py work from.
"""
import csv
from pathlib import Path

OLD_SEEDS = [42, 123, 2026]   # seeds already used in the submitted paper
NEW_SEEDS = [7, 99]           # extra seeds for the 5-seed camera-ready results (change if you like)

rows = []


def add(exp_id, tier, scenario, variant, channel, defense, seed, training, status, note=""):
    rows.append(dict(exp_id=exp_id, tier=tier, scenario=scenario, variant=variant, channel=channel,
                     defense=defense, seed=seed, needs_training=training, status=status, note=note))


# ---- Tier 0: already in the repo. `export_runs.py` puts these into results/runs.csv; no retraining.
for rep in ["opacity_blend", "rgb_stack"]:
    for bb in ["small_cnn", "mobilenet_v2", "resnet18"]:
        add(f"backbone_{rep}_{bb}_seed42", 0, "backbone_sel", f"{rep}-{bb}", "none", "none", 42, 1,
            "done_in_paper", "Table III, centralized")
for s in OLD_SEEDS:
    add(f"fl_clean_rgb_resnet18_iid_seed{s}", 0, "clean_fl", "-", "none", "none", s, 1, "done_in_paper",
        "Table V" + ("  -- 30 rounds / 1 local epoch, see D1" if s == 42 else ""))
for ch in ["red", "green"]:
    add(f"fl_backdoor_rgb_resnet18_{ch}_p20_s10_r50", 0, "backdoor_fedavg", "at2fb", ch, "none", 42, 1,
        "done_in_paper", "Table IV sweep")
for ch in ["blue", "full"]:
    add(f"fl_backdoor_rgb_resnet18_{ch}_p20_s10_r50", 0, "backdoor_fedavg", "at2fb", ch, "none", 42, 1,
        "done_in_paper", "Tables IV/V/VII")
    for s in [123, 2026]:
        add(f"fl_backdoor_rgb_resnet18_{ch}_p20_s10_seed{s}", 0, "backdoor_fedavg", "at2fb", ch, "none", s, 1,
            "done_in_paper", "Tables V/VII")
for ch in ["blue", "full"]:
    for s in OLD_SEEDS:
        suffix = "" if s == 42 else f"_seed{s}"
        add(f"clean_model_{ch}_trigger_control{suffix}", 0, "trigger_control", "at2fb", ch, "none", s, 0,
            "done_in_paper", "Table V; clean model + trigger, no poisoning")
for ch in ["red", "green"]:
    add(f"clean_model_{ch}_trigger_control", 0, "trigger_control", "at2fb", ch, "none", 42, 0,
        "done_in_paper", "not in a table; seed 42 only")
for d in ["clipping", "median", "trimmed_mean", "multikrum"]:
    for ch in ["blue", "full"]:
        raw = "multi_krum" if d == "multikrum" else d
        add(f"defense_{ch}_{raw}", 0, "backdoor_defense", "at2fb", ch, d, 42, 1, "done_in_paper",
            "Table VI screening")
for ch in ["blue", "full"]:
    for s in [123, 2026]:
        add(f"defense_{ch}_multi_krum_seed{s}", 0, "backdoor_defense", "at2fb", ch, "multikrum", s, 1,
            "done_in_paper", "Table VII")
# unreported ablations that already exist (see D6)
add("fl_backdoor_rgb_resnet18_red_p30_s12_r50", 0, "backdoor_fedavg", "at2fb-p30-s12", "red", "none", 42, 1,
    "done_not_in_paper", "poison 30%, trigger 12% -- free robustness check, D6")
add("fl_backdoor_rgb_resnet18_full_p30_s12_r50", 0, "backdoor_fedavg", "at2fb-p30-s12", "full", "none", 42, 1,
    "done_not_in_paper", "poison 30%, trigger 12% -- free robustness check, D6")
add("fl_backdoor_rgb_resnet18_api_trigger_seed42", 0, "backdoor_fedavg", "at2fb-p10", "red", "none", 42, 1,
    "done_not_in_paper", "poison 10%, 30 rounds, trigger 8% -- earliest run, D6")

# ---- Tier 1: fixes that must be re-run before the camera-ready (see docs/DISCREPANCIES.md)
# NOTE: the re-runs carry a distinct variant tag ("r50") so they can coexist with the original
# seed-42 rows in results/runs.csv and be compared, instead of colliding on the same group key.
add("fl_clean_rgb_resnet18_iid_seed42_r50", 1, "clean_fl", "r50", "none", "none", 42, 1, "todo",
    "D1: re-run clean FL seed 42 at 50 rounds / 2 local epochs to match the other seeds")
for ch in ["blue", "full", "red", "green"]:
    add(f"clean_model_{ch}_trigger_control_r50", 1, "trigger_control", "at2fb-r50", ch, "none", 42, 0, "todo",
        "D1: re-evaluate the seed-42 control against the re-run clean model")
for bb in ["small_cnn", "mobilenet_v2", "resnet18"]:
    add(f"backbone_opacity_blend_{bb}_seed42_rgbsplit", 1, "backbone_sel", f"opacity_blend-{bb}-rgbsplit",
        "none", "none", 42, 1, "optional",
        "D2: re-run on split_rgb_seed42.csv so Table III is a paired comparison (or drop the perf claim)")

# ---- Tier 2: cheap additions that answer reviewers B and C
for s in NEW_SEEDS:
    add(f"split_rgb_seed{s}", 2, "split", "-", "none", "none", s, 0, "todo",
        "create_splits.py first -- a new seed needs its own split file")
    add(f"fl_clean_rgb_resnet18_iid_seed{s}", 2, "clean_fl", "-", "none", "none", s, 1, "todo", "5-seed baseline")
for ch in ["blue", "full"]:
    for s in NEW_SEEDS:
        add(f"fl_backdoor_rgb_resnet18_{ch}_p20_s10_seed{s}", 2, "backdoor_fedavg", "at2fb", ch, "none", s, 1,
            "todo", "5-seed main result")
        add(f"defense_{ch}_multi_krum_seed{s}", 2, "backdoor_defense", "at2fb", ch, "multikrum", s, 1,
            "todo", "5-seed Multi-Krum")
        add(f"clean_model_{ch}_trigger_control_seed{s}", 2, "trigger_control", "at2fb", ch, "none", s, 0,
            "todo", f"eval only; needs fl_clean_rgb_resnet18_iid_seed{s}")
for ch in ["red", "green"]:
    for s in [123, 2026]:
        add(f"fl_backdoor_rgb_resnet18_{ch}_p20_s10_seed{s}", 2, "backdoor_fedavg", "at2fb", ch, "none", s, 1,
            "todo", "Table IV across seeds -- red/green currently seed 42 only")
    for s in [123, 2026]:
        add(f"clean_model_{ch}_trigger_control_seed{s}", 2, "trigger_control", "at2fb", ch, "none", s, 0,
            "todo", "eval only; red/green controls across seeds")
for d in ["clipping", "median", "trimmed_mean"]:
    for ch in ["blue", "full"]:
        for s in [123, 2026]:
            add(f"defense_{ch}_{d}_seed{s}", 2, "backdoor_defense", "at2fb", ch, d, s, 1, "todo",
                "defense screening across seeds (removes the seed-42 selection bias, reviewer C)")

# ---- Tier 3: optional
for s in OLD_SEEDS:
    add(f"fl_backdoor_rgb_resnet18_blue_vd2sc_seed{s}", 3, "backdoor_fedavg", "vd2sc", "blue", "none", s, 1,
        "optional", "second source-target pair Vidar(4) -> StealC(3); ASR then over the 15 Vidar test samples")
    add(f"clean_model_blue_trigger_control_vd2sc_seed{s}", 3, "trigger_control", "vd2sc", "blue", "none", s, 0,
        "optional", "eval only")
for ch in ["red", "green", "blue"]:
    for s in OLD_SEEDS:
        add(f"fl_backdoor_rgb_resnet18_{ch}_contrast_seed{s}", 3, "backdoor_fedavg", "at2fb-contrast", ch,
            "none", s, 1, "optional",
            "contrast-matched trigger: same intensity delta per channel; separates saliency from channel semantics")
for rep in ["opacity_blend", "rgb_stack"]:
    for bb in ["small_cnn", "mobilenet_v2", "resnet18"]:
        for s in [123, 2026]:
            add(f"backbone_{rep}_{bb}_seed{s}", 3, "backbone_sel", f"{rep}-{bb}", "none", "none", s, 1,
                "optional", "backbone selection across seeds")

out = Path(__file__).with_name("run_matrix.csv")
with out.open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)

from collections import Counter
c = Counter((r["tier"], r["status"], "train" if r["needs_training"] else "eval") for r in rows)
for k in sorted(c):
    print(f"tier {k[0]}  {k[1]:<14} {k[2]:<5} {c[k]:>3}")
print(f"wrote {out} ({len(rows)} rows)")
