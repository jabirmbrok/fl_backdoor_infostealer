from pathlib import Path
import json
import csv
import re

ROOT = Path("results")
OUT = ROOT / "backbone_summary_seed42.csv"

# Fixed param counts without importing torch/torchvision/PIL.
# ResNet18 and MobileNetV2 are standard torchvision backbones with final classifier adjusted to 5 classes.
# SmallCNN depends on the project implementation, so it is left blank to avoid another import error.
PARAMS_MILLION = {
    "small_cnn": "",
    "mobilenet_v2": 2.23,
    "resnet18": 11.18,
}

rows = []
for path in sorted(ROOT.glob("backbone_*_seed42/test_metrics.json")):
    parent = path.parent.name
    m = re.match(r"backbone_(rgb_stack|opacity_blend)_(small_cnn|mobilenet_v2|resnet18)_seed42", parent)
    if not m:
        continue

    representation = m.group(1)
    backbone = m.group(2)

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    rows.append({
        "representation": representation,
        "backbone": backbone,
        "seed": 42,
        "accuracy": data.get("accuracy"),
        "macro_f1": data.get("macro_f1"),
        "params_million": PARAMS_MILLION.get(backbone, ""),
        "result_path": str(path),
    })

if not rows:
    print("Tidak ada hasil backbone seed42 ditemukan.")
    print("Cek folder: results\\backbone_*_seed42\\test_metrics.json")
    raise SystemExit(1)

rows = sorted(rows, key=lambda x: float(x["macro_f1"] or 0), reverse=True)

OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "rank",
            "representation",
            "backbone",
            "seed",
            "accuracy",
            "macro_f1",
            "params_million",
            "result_path",
        ],
    )
    writer.writeheader()
    for i, row in enumerate(rows, start=1):
        writer.writerow({"rank": i, **row})

print("\nBackbone Selection Summary - seed 42")
print("-" * 100)
print(f"{'rank':>4s} {'representation':16s} {'backbone':14s} {'acc':>8s} {'macro_f1':>10s} {'params(M)':>10s}")
print("-" * 100)
for i, r in enumerate(rows, start=1):
    params = r["params_million"]
    params_text = f"{float(params):10.2f}" if params != "" else f"{'-':>10s}"
    print(
        f"{i:4d} "
        f"{r['representation'][:16]:16s} "
        f"{r['backbone'][:14]:14s} "
        f"{float(r['accuracy'] or 0):8.4f} "
        f"{float(r['macro_f1'] or 0):10.4f} "
        f"{params_text}"
    )
print("-" * 100)

best = rows[0]
print("Selected candidate:", best["representation"], "+", best["backbone"])
print("Saved:", OUT.resolve())
