from pathlib import Path
import csv
import json

ROOT = Path("results")
OUT = ROOT / "defense_summary.csv"

rows = []

# Baseline backdoor tanpa defense dari sweep.
for metrics_path in sorted(ROOT.glob("fl_backdoor_rgb_resnet18_*/final_metrics.json")):
    with metrics_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    clean = data.get("clean_test_metrics", {})
    rows.append({
        "experiment": metrics_path.parent.name,
        "defense": "fedavg_baseline",
        "trigger_channel": data.get("trigger_channel"),
        "poison_rate": data.get("poison_rate"),
        "clean_accuracy": clean.get("accuracy"),
        "clean_macro_f1": clean.get("macro_f1"),
        "asr": data.get("asr_source_to_target"),
        "metrics_path": str(metrics_path),
    })

# Defense experiments.
for metrics_path in sorted(ROOT.glob("defense_*/final_metrics.json")):
    with metrics_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    clean = data.get("clean_test_metrics", {})
    rows.append({
        "experiment": data.get("experiment", metrics_path.parent.name),
        "defense": data.get("defense"),
        "trigger_channel": data.get("trigger_channel"),
        "poison_rate": data.get("poison_rate"),
        "clean_accuracy": clean.get("accuracy"),
        "clean_macro_f1": clean.get("macro_f1"),
        "asr": data.get("asr_source_to_target"),
        "metrics_path": str(metrics_path),
    })

if not rows:
    print("Tidak ada hasil ditemukan.")
    raise SystemExit(1)

fieldnames = list(rows[0].keys())
with OUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print("\nDefense summary")
print("-" * 120)
print(f"{'experiment':45s} {'defense':16s} {'channel':8s} {'poison':>7s} {'acc':>8s} {'f1':>8s} {'asr':>8s}")
print("-" * 120)
for r in sorted(rows, key=lambda x: (str(x["trigger_channel"]), str(x["defense"]))):
    print(
        f"{str(r['experiment'])[:45]:45s} "
        f"{str(r['defense'])[:16]:16s} "
        f"{str(r['trigger_channel'])[:8]:8s} "
        f"{float(r['poison_rate'] or 0):7.2f} "
        f"{float(r['clean_accuracy'] or 0):8.4f} "
        f"{float(r['clean_macro_f1'] or 0):8.4f} "
        f"{float(r['asr'] or 0):8.4f}"
    )
print("-" * 120)
print("Saved:", OUT.resolve())
