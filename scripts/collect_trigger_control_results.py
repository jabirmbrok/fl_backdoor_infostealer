from pathlib import Path
import csv
import json

ROOT = Path("results/trigger_control")
OUT = Path("results/trigger_control_summary.csv")

rows = []
for path in sorted(ROOT.glob("*.json")):
    with path.open("r", encoding="utf-8") as f:
        rows.append(json.load(f))

if not rows:
    print("Tidak ada hasil trigger control ditemukan.")
    raise SystemExit(1)

fieldnames = list(rows[0].keys())
with OUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print("\nTrigger control summary")
print("-" * 110)
print(f"{'experiment':28s} {'channel':8s} {'clean_acc':>10s} {'clean_f1':>10s} {'src->tgt':>10s} {'trig->tgt':>10s} {'n':>5s}")
print("-" * 110)
for r in rows:
    print(
        f"{r['experiment'][:28]:28s} "
        f"{str(r['trigger_channel'])[:8]:8s} "
        f"{r['clean_test_accuracy']:10.4f} "
        f"{r['clean_test_macro_f1']:10.4f} "
        f"{r['clean_source_target_prediction_rate']:10.4f} "
        f"{r['triggered_source_target_prediction_rate']:10.4f} "
        f"{r['source_test_count']:5d}"
    )
print("-" * 110)
print("Saved:", OUT.resolve())
