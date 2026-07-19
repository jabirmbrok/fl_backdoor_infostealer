from pathlib import Path
import argparse
import hashlib
import pandas as pd
from PIL import Image
from tqdm import tqdm

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}

def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", default="dataset/processed/dataset_rgb_stack_combined")
    parser.add_argument("--output", default="results/manifest_rgb.csv")
    args = parser.parse_args()

    dataset_root = Path(args.dataset_root)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    if not dataset_root.exists():
        raise FileNotFoundError(
            f"Dataset root tidak ditemukan: {dataset_root.resolve()}\n"
            "Pastikan dataset ada di dataset/processed/dataset_rgb_stack_combined"
        )

    family_dirs = sorted([p for p in dataset_root.iterdir() if p.is_dir()])
    if not family_dirs:
        raise RuntimeError(f"Tidak ada folder family di: {dataset_root.resolve()}")

    label_map = {p.name: i for i, p in enumerate(family_dirs)}
    rows = []

    for family_dir in family_dirs:
        image_paths = sorted([p for p in family_dir.rglob("*") if p.suffix.lower() in IMAGE_EXTS])
        for path in tqdm(image_paths, desc=f"Scanning {family_dir.name}"):
            try:
                with Image.open(path) as img:
                    width, height = img.size
                    mode = img.mode
            except Exception as e:
                width, height, mode = None, None, "ERROR"
                print(f"[WARN] Gagal buka image: {path} | {e}")

            rows.append({
                "relative_path": path.relative_to(dataset_root).as_posix(),
                "absolute_path": str(path.resolve()),
                "family": family_dir.name,
                "label_id": label_map[family_dir.name],
                "file_name": path.name,
                "extension": path.suffix.lower(),
                "width": width,
                "height": height,
                "mode": mode,
                "file_size_bytes": path.stat().st_size,
                "image_sha256": sha256_file(path),
            })

    df = pd.DataFrame(rows)
    df.to_csv(output, index=False)

    print("\nManifest saved:", output.resolve())
    print("\nLabel map:")
    for family, label in label_map.items():
        print(f"  {label}: {family}")

    print("\nFamily counts:")
    print(df["family"].value_counts().sort_index().to_string())

    if len(df) == 0:
        print("\n[WARN] Manifest kosong.")
        return

    print("\nImage size counts:")
    print(df.groupby(["width", "height"]).size().sort_values(ascending=False).head(10).to_string())

    dup_count = int(df.duplicated("image_sha256").sum())
    print(f"\nDuplicate image hashes: {dup_count}")
    if dup_count > 0:
        print("\nTop duplicate hashes:")
        print(df["image_sha256"].value_counts().head(10).to_string())

if __name__ == "__main__":
    main()
