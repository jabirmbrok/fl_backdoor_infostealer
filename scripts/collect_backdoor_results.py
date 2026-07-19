from pathlib import Path
import json
import csv

RESULTS_ROOT = Path("results")
OUT_CSV = RESULTS_ROOT / "backdoor_sweep_summary.csv"

rows = []
for metrics_path in sorted(RESULTS_ROOT.glob("fl_backdoor_rgb_resnet18_*/final_metrics.json")):
    with metrics_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    clean = data.get("clean_test_metrics", {})
    rows.append({
        "experiment": metrics_path.parent.name,
        "clean_accuracy": clean.get("accuracy"),
        "clean_macro_f1": clean.get("macro_f1"),
        "asr": data.get("asr_source_to_target"),
        "source_label": data.get("source_label"),
        "target_label": data.get("target_label"),
        "trigger_channel": data.get("trigger_channel"),
        "poison_rate": data.get("poison_rate"),
        "metrics_path": str(metrics_path),
    })

if not rows:
    print("Tidak ada final_metrics.json ditemukan.")
    raise SystemExit(1)

OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

fieldnames = list(rows[0].keys())
with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print("\nBackdoor sweep summary:")
print("-" * 100)
print(f"{'experiment':45s} {'acc':>8s} {'f1':>8s} {'asr':>8s} {'channel':>10s} {'poison':>8s}")
print("-" * 100)
for r in sorted(rows, key=lambda x: (x["asr"] if x["asr"] is not None else -1), reverse=True):
    acc = r["clean_accuracy"]
    f1 = r["clean_macro_f1"]
    asr = r["asr"]
    print(
        f"{r['experiment'][:45]:45s} "
        f"{acc if acc is not None else 0:8.4f} "
        f"{f1 if f1 is not None else 0:8.4f} "
        f"{asr if asr is not None else 0:8.4f} "
        f"{str(r['trigger_channel']):>10s} "
        f"{r['poison_rate'] if r['poison_rate'] is not None else 0:8.2f}"
    )
print("-" * 100)
print("Saved:", OUT_CSV.resolve())
