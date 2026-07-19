from pathlib import Path
import json
import csv
import re
from statistics import mean, stdev

ROOT = Path("results")
RAW_OUT = ROOT / "multiseed_core_raw.csv"
AGG_OUT = ROOT / "multiseed_core_mean_std.csv"

rows = []

def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def add_row(scenario, seed, channel, defense, clean_acc, clean_f1, asr, path):
    rows.append({
        "scenario": scenario,
        "seed": int(seed),
        "channel": channel,
        "defense": defense,
        "clean_accuracy": clean_acc,
        "clean_macro_f1": clean_f1,
        "asr": asr,
        "path": str(path),
    })

# FL clean seed42,123,2026
for path in sorted(ROOT.glob("fl_clean_rgb_resnet18_iid_seed*/test_metrics.json")):
    m = re.search(r"seed(\d+)", str(path.parent))
    if not m:
        continue
    seed = int(m.group(1))
    if seed not in {42, 123, 2026}:
        continue
    data = read_json(path)
    add_row("fl_clean", seed, "none", "none", data.get("accuracy"), data.get("macro_f1"), None, path)

# Backdoor no defense, prefer multiseed naming; also include seed42 sweep names.
patterns = [
    "fl_backdoor_rgb_resnet18_blue_p20_s10_seed*/final_metrics.json",
    "fl_backdoor_rgb_resnet18_full_p20_s10_seed*/final_metrics.json",
    "fl_backdoor_rgb_resnet18_blue_p20_s10_r50/final_metrics.json",
    "fl_backdoor_rgb_resnet18_full_p20_s10_r50/final_metrics.json",
]
for pattern in patterns:
    for path in sorted(ROOT.glob(pattern)):
        data = read_json(path)
        clean = data.get("clean_test_metrics", {})
        parent = path.parent.name
        seed_match = re.search(r"seed(\d+)", parent)
        seed = int(seed_match.group(1)) if seed_match else 42
        channel = data.get("trigger_channel")
        add_row(
            "backdoor_no_defense",
            seed,
            channel,
            "fedavg",
            clean.get("accuracy"),
            clean.get("macro_f1"),
            data.get("asr_source_to_target"),
            path,
        )

# Trigger control.
for path in sorted((ROOT / "trigger_control").glob("*.json")):
    data = read_json(path)
    exp = data.get("experiment", path.stem)
    seed_match = re.search(r"seed(\d+)", exp)
    seed = int(seed_match.group(1)) if seed_match else 42
    if seed not in {42, 123, 2026}:
        continue
    channel = data.get("trigger_channel")
    add_row(
        "trigger_control_clean_model",
        seed,
        channel,
        "none",
        data.get("clean_test_accuracy"),
        data.get("clean_test_macro_f1"),
        data.get("triggered_source_target_prediction_rate"),
        path,
    )

# Multi-Krum defense.
patterns = [
    "defense_blue_multi_krum/final_metrics.json",
    "defense_full_multi_krum/final_metrics.json",
    "defense_blue_multi_krum_seed*/final_metrics.json",
    "defense_full_multi_krum_seed*/final_metrics.json",
]
for pattern in patterns:
    for path in sorted(ROOT.glob(pattern)):
        data = read_json(path)
        clean = data.get("clean_test_metrics", {})
        seed_match = re.search(r"seed(\d+)", path.parent.name)
        seed = int(seed_match.group(1)) if seed_match else 42
        if seed not in {42, 123, 2026}:
            continue
        add_row(
            "backdoor_multi_krum",
            seed,
            data.get("trigger_channel"),
            "multi_krum",
            clean.get("accuracy"),
            clean.get("macro_f1"),
            data.get("asr_source_to_target"),
            path,
        )

if not rows:
    print("Tidak ada hasil multi-seed ditemukan.")
    raise SystemExit(1)

# Deduplicate same scenario/seed/channel/defense, keep latest in scan order.
dedup = {}
for r in rows:
    key = (r["scenario"], r["seed"], r["channel"], r["defense"])
    dedup[key] = r
rows = list(dedup.values())

RAW_OUT.parent.mkdir(parents=True, exist_ok=True)
fieldnames = ["scenario", "seed", "channel", "defense", "clean_accuracy", "clean_macro_f1", "asr", "path"]
with RAW_OUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(sorted(rows, key=lambda x: (x["scenario"], str(x["channel"]), str(x["defense"]), x["seed"])))

def ms(vals):
    vals = [float(v) for v in vals if v is not None]
    if len(vals) == 0:
        return (None, None, 0)
    if len(vals) == 1:
        return (vals[0], 0.0, 1)
    return (mean(vals), stdev(vals), len(vals))

groups = {}
for r in rows:
    key = (r["scenario"], r["channel"], r["defense"])
    groups.setdefault(key, []).append(r)

agg_rows = []
for (scenario, channel, defense), items in sorted(groups.items()):
    acc_m, acc_s, n_acc = ms([x["clean_accuracy"] for x in items])
    f1_m, f1_s, n_f1 = ms([x["clean_macro_f1"] for x in items])
    asr_m, asr_s, n_asr = ms([x["asr"] for x in items])
    agg_rows.append({
        "scenario": scenario,
        "channel": channel,
        "defense": defense,
        "n_runs": len(items),
        "seeds": ";".join(str(x["seed"]) for x in sorted(items, key=lambda y: y["seed"])),
        "clean_accuracy_mean": acc_m,
        "clean_accuracy_std": acc_s,
        "clean_macro_f1_mean": f1_m,
        "clean_macro_f1_std": f1_s,
        "asr_mean": asr_m,
        "asr_std": asr_s,
    })

with AGG_OUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(agg_rows[0].keys()))
    writer.writeheader()
    writer.writerows(agg_rows)

print("\nMulti-seed raw results")
print("-" * 115)
print(f"{'scenario':28s} {'seed':>6s} {'channel':8s} {'defense':12s} {'acc':>8s} {'f1':>8s} {'asr':>8s}")
print("-" * 115)
for r in sorted(rows, key=lambda x: (x["scenario"], str(x["channel"]), str(x["defense"]), x["seed"])):
    print(
        f"{r['scenario'][:28]:28s} "
        f"{r['seed']:6d} "
        f"{str(r['channel'])[:8]:8s} "
        f"{str(r['defense'])[:12]:12s} "
        f"{float(r['clean_accuracy'] or 0):8.4f} "
        f"{float(r['clean_macro_f1'] or 0):8.4f} "
        f"{float(r['asr'] or 0):8.4f}"
    )

print("\nMean ± std summary")
print("-" * 135)
print(f"{'scenario':28s} {'channel':8s} {'defense':12s} {'n':>3s} {'acc_mean':>9s} {'acc_std':>8s} {'f1_mean':>9s} {'f1_std':>8s} {'asr_mean':>9s} {'asr_std':>8s}")
print("-" * 135)
for r in agg_rows:
    print(
        f"{r['scenario'][:28]:28s} "
        f"{str(r['channel'])[:8]:8s} "
        f"{str(r['defense'])[:12]:12s} "
        f"{r['n_runs']:3d} "
        f"{float(r['clean_accuracy_mean'] or 0):9.4f} "
        f"{float(r['clean_accuracy_std'] or 0):8.4f} "
        f"{float(r['clean_macro_f1_mean'] or 0):9.4f} "
        f"{float(r['clean_macro_f1_std'] or 0):8.4f} "
        f"{float(r['asr_mean'] or 0):9.4f} "
        f"{float(r['asr_std'] or 0):8.4f}"
    )
print("-" * 135)
print("Saved raw:", RAW_OUT.resolve())
print("Saved aggregate:", AGG_OUT.resolve())
