from pathlib import Path
import argparse
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

def assign_iid_clients(train_df: pd.DataFrame, num_clients: int, seed: int) -> pd.Series:
    rng = np.random.default_rng(seed)
    client_ids = pd.Series(index=train_df.index, dtype="Int64")

    for _, group in train_df.groupby("label_id"):
        idxs = group.index.to_numpy()
        rng.shuffle(idxs)
        for j, idx in enumerate(idxs):
            client_ids.loc[idx] = j % num_clients

    return client_ids.astype(int)

def assign_dirichlet_clients(train_df: pd.DataFrame, num_clients: int, alpha: float, seed: int) -> pd.Series:
    rng = np.random.default_rng(seed)
    client_ids = pd.Series(index=train_df.index, dtype="Int64")

    for _, group in train_df.groupby("label_id"):
        idxs = group.index.to_numpy()
        rng.shuffle(idxs)
        proportions = rng.dirichlet([alpha] * num_clients)
        counts = (proportions * len(idxs)).astype(int)

        while counts.sum() < len(idxs):
            counts[rng.integers(0, num_clients)] += 1
        while counts.sum() > len(idxs):
            candidates = np.where(counts > 0)[0]
            counts[rng.choice(candidates)] -= 1

        start = 0
        for client_id, count in enumerate(counts):
            selected = idxs[start:start + count]
            client_ids.loc[selected] = client_id
            start += count

    missing = client_ids.isna()
    if missing.any():
        missing_idxs = client_ids.index[missing].to_numpy()
        for j, idx in enumerate(missing_idxs):
            client_ids.loc[idx] = j % num_clients

    return client_ids.astype(int)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="results/manifest_rgb.csv")
    parser.add_argument("--output", default="dataset/splits/split_rgb_seed42.csv")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--train-size", type=float, default=0.70)
    parser.add_argument("--val-size", type=float, default=0.15)
    parser.add_argument("--test-size", type=float, default=0.15)
    parser.add_argument("--num-clients", type=int, default=5)
    parser.add_argument("--dirichlet-alpha", type=float, default=0.5)
    args = parser.parse_args()

    manifest = Path(args.manifest)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(manifest)
    if len(df) == 0:
        raise RuntimeError("Manifest kosong.")

    total = args.train_size + args.val_size + args.test_size
    if abs(total - 1.0) > 1e-6:
        raise ValueError("train-size + val-size + test-size harus = 1.0")

    train_df, temp_df = train_test_split(
        df,
        train_size=args.train_size,
        random_state=args.seed,
        stratify=df["label_id"],
    )

    relative_test_size = args.test_size / (args.val_size + args.test_size)
    val_df, test_df = train_test_split(
        temp_df,
        test_size=relative_test_size,
        random_state=args.seed,
        stratify=temp_df["label_id"],
    )

    df["split"] = ""
    df.loc[train_df.index, "split"] = "train"
    df.loc[val_df.index, "split"] = "val"
    df.loc[test_df.index, "split"] = "test"

    df["client_iid"] = -1
    df["client_noniid"] = -1

    train_mask = df["split"] == "train"
    train_part = df.loc[train_mask].copy()

    df.loc[train_mask, "client_iid"] = assign_iid_clients(train_part, args.num_clients, args.seed)
    df.loc[train_mask, "client_noniid"] = assign_dirichlet_clients(
        train_part, args.num_clients, args.dirichlet_alpha, args.seed
    )

    df.to_csv(output, index=False)

    print("Split saved:", output.resolve())
    print("\nSplit counts:")
    print(df["split"].value_counts().to_string())

    print("\nSplit x family:")
    print(pd.crosstab(df["family"], df["split"]).to_string())

    print("\nIID client x family:")
    print(pd.crosstab(df.loc[train_mask, "client_iid"], df.loc[train_mask, "family"]).to_string())

    print("\nNon-IID client x family:")
    print(pd.crosstab(df.loc[train_mask, "client_noniid"], df.loc[train_mask, "family"]).to_string())

if __name__ == "__main__":
    main()
