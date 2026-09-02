"""Generate every Tier 2 config under configs/camera_ready/tier2/.

Hyperparameters are copied from the configs that produced the submitted runs;
only the seed, the split file, the channel and the defense change.

Usage (from the repository root):
    python scripts/make_tier2_configs.py
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "configs" / "camera_ready" / "tier2"

COMMON = """data:
  dataset_root: dataset/processed/dataset_rgb_stack_combined
  split_csv: dataset/splits/split_rgb_seed{seed}.csv
  image_size: 128

model:
  name: resnet18
  num_classes: 5

train:
  batch_size: 16
  lr: 0.0001
  weight_decay: 0.0001

fl:
  num_clients: 5
  rounds: 50
  local_epochs: 2
  eval_every: 1
  client_col: client_iid
"""

ATTACK = """
attack:
  source_label: 0
  target_label: 1
  malicious_client: 0
  poison_rate: 0.20
  trigger_channel: {channel}
  trigger_size_ratio: 0.10
  trigger_location: bottom_right
"""

DEFENSE_BLOCK = {
    "multi_krum": "\ndefense:\n  name: multi_krum\n  byzantine_clients: 1\n  selected_clients: 2\n",
    "clipping": "\ndefense:\n  name: clipping\n  max_norm: 5.0\n",
    "median": "\ndefense:\n  name: median\n",
    "trimmed_mean": "\ndefense:\n  name: trimmed_mean\n  trim_count: 1\n",
}

DEFENSE_TAG = {"multi_krum": "multi_krum", "clipping": "clipping",
               "median": "median", "trimmed_mean": "trimmed_mean"}

jobs = []       # (kind, config path, exp_id)


def write(name: str, text: str) -> Path:
    p = OUT / name
    p.write_text(text, encoding="utf-8", newline="\n")
    return p


def clean_fl(seed: int) -> None:
    exp = "fl_clean_rgb_resnet18_iid_seed%d" % seed
    body = "seed: %d\noutput_dir: results/%s\n\n" % (seed, exp) + COMMON.format(seed=seed)
    jobs.append(("clean", write("fl_clean_seed%d.yaml" % seed, body), exp))


def backdoor(channel: str, seed: int) -> None:
    exp = "fl_backdoor_rgb_resnet18_%s_p20_s10_seed%d" % (channel, seed)
    body = ("seed: %d\noutput_dir: results/%s\n\n" % (seed, exp)
            + COMMON.format(seed=seed) + ATTACK.format(channel=channel))
    jobs.append(("backdoor", write("backdoor_%s_seed%d.yaml" % (channel, seed), body), exp))


def defense(channel: str, defense_name: str, seed: int) -> None:
    exp = "defense_%s_%s_seed%d" % (channel, DEFENSE_TAG[defense_name], seed)
    body = ("seed: %d\nexperiment_name: %s\noutput_dir: results/%s\n\n" % (seed, exp, exp)
            + COMMON.format(seed=seed) + ATTACK.format(channel=channel)
            + DEFENSE_BLOCK[defense_name])
    jobs.append(("defense", write("defense_%s_%s_seed%d.yaml" % (channel, DEFENSE_TAG[defense_name], seed), body), exp))


def control(channel: str, seed: int) -> None:
    exp = "clean_model_%s_trigger_control_seed%d" % (channel, seed)
    body = ("seed: %d\nexperiment_name: %s\noutput_dir: results/trigger_control\n\n" % (seed, exp)
            + COMMON.format(seed=seed).split("\nmodel:")[0]
            + "\nmodel:\n  name: resnet18\n  num_classes: 5\n"
            + "\ncontrol:\n"
              "  checkpoint_path: results/fl_clean_rgb_resnet18_iid_seed%d/final_model.pt\n"
              "  batch_size: 16\n"
              "  source_label: 0\n"
              "  target_label: 1\n"
              "  trigger_channel: %s\n"
              "  trigger_size_ratio: 0.10\n"
              "  trigger_location: bottom_right\n" % (seed, channel))
    jobs.append(("control", write("control_%s_seed%d.yaml" % (channel, seed), body), exp))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    # two new seeds: clean baseline, both strong channels, Multi-Krum, controls
    for seed in (7, 99):
        clean_fl(seed)
    for seed in (7, 99):
        for ch in ("blue", "full"):
            backdoor(ch, seed)
            defense(ch, "multi_krum", seed)
            control(ch, seed)

    # red and green across the existing seeds
    for seed in (123, 2026):
        for ch in ("red", "green"):
            backdoor(ch, seed)
            control(ch, seed)

    # the three screened defenses across the existing seeds
    for seed in (123, 2026):
        for ch in ("blue", "full"):
            for dname in ("clipping", "median", "trimmed_mean"):
                defense(ch, dname, seed)

    order = {"clean": 0, "backdoor": 1, "defense": 2, "control": 3}
    jobs.sort(key=lambda j: (order[j[0]], j[2]))
    manifest = OUT / "run_order.txt"
    manifest.write_text(
        "\n".join("%s\t%s\t%s" % (k, p.relative_to(ROOT).as_posix(), e) for k, p, e in jobs) + "\n",
        encoding="utf-8", newline="\n")

    n_train = sum(1 for k, _, _ in jobs if k != "control")
    print("wrote %d configs (%d training, %d evaluation) and %s"
          % (len(jobs), n_train, len(jobs) - n_train, manifest.relative_to(ROOT).as_posix()))


if __name__ == "__main__":
    main()
