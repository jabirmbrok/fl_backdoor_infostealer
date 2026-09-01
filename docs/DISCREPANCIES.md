# Discrepancies between the paper and the code

Found by auditing the repository against the submitted PDF. Ordered by how much they matter.
Each one needs a decision: fix by re-running, or disclose in the text.

## D1 — The clean FL baseline for seed 42 used a different training budget (**blocking**)

`configs/fl_clean_rgb.yaml` sets `rounds: 30`, `local_epochs: 1`, and
`results/fl_clean_rgb_resnet18_iid_seed42/history.json` indeed has **30 rows**. The seed 123 and
2026 clean runs (`configs/multiseed/fl_clean_seed*.yaml`) use `rounds: 50`, `local_epochs: 2`, and
their histories have 50 rows. Every backdoor and defense run uses 50 / 2.

The paper reports the clean FL baseline as a single three-seed number (0.8267 ± 0.0133, Table V) and
states 50 rounds with 2 local epochs in III.H. One of the three seeds was therefore trained for
30 rounds with half the local work — 30 effective epochs against 100.

Knock-on effect: the seed-42 trigger controls load
`results/fl_clean_rgb_resnet18_iid_seed42/final_model.pt`, i.e. the 30-round model. That is very
likely why the seed-42 control rate (4/15) is four times the other seeds (1/15) and why the paper's
trigger-control std is so large.

**Fix:** re-run clean FL seed 42 at 50 rounds / 2 local epochs, then re-run the four seed-42 trigger
controls against the new checkpoint. Six cheap runs (`clean_fl_s42_r50` + 4 controls). Tier 1 in the
run matrix. If for some reason it cannot be re-run, the mismatch must be stated in III.H.

### Outcome of the re-run (done, 5 runs)

`results/fl_clean_rgb_resnet18_iid_seed42_r50` + the four `*_trigger_control_r50` evaluations.
Configs in `configs/camera_ready/`; the submitted runs were not touched.

The re-run does **not** improve the baseline and the knock-on hypothesis above is **refuted**:

| seed 42 clean FL | accuracy | macro-F1 | test loss | control rate (all four channels) |
|---|---|---|---|---|
| 30 rounds / 1 epoch (submitted) | 0.8267 | 0.8264 | 0.781 | 4/15 |
| 50 rounds / 2 epochs (re-run) | 0.7867 | 0.7869 | 1.209 | 6/15 |

The larger budget overfits: test loss rises by 55 per cent. The elevated seed-42 control rate is
therefore not a training-budget artefact. It is simply the model's baseline AgentTesla-to-FormBook
confusion: row 0 of the confusion matrix is [9, 6, 0, 0, 0] for the 50-round model and
[9, 4, 0, 2, 0] for the 30-round one, i.e. exactly the 6/15 and 4/15 reported as "control rate".
In all four new controls the untriggered and triggered rates are identical, as in 7 of the 8
submitted controls, so the trigger contributes nothing to that number.

If the re-run is adopted for the paper, the three-seed numbers become:

| | as printed | with the 50-round seed 42 |
|---|---|---|
| Clean FL accuracy | 0.8267 +/- 0.0134 | 0.8133 +/- 0.0267 |
| Clean FL macro-F1 | 0.8255 +/- 0.0104 | 0.8124 +/- 0.0244 |
| Trigger control, blue | 6/45 = 0.1333 | 8/45 = 0.1778 |
| Trigger control, full | 7/45 = 0.1556 | 9/45 = 0.2000 |

Everything gets worse and roughly twice as noisy, and the trigger-control rates that the paper uses
to argue "the high ASR is caused by poisoning rather than the trigger alone" move closer to the
backdoor numbers. Note that no backdoor or defense run is affected: those were all 50 / 2 already.

**Decision still open:** adopt the re-run (Table V and the abstract's clean-baseline numbers change),
or keep the submitted numbers and state in III.H that the seed-42 clean baseline used 30 rounds and
one local epoch. The second option keeps the better-looking numbers, so it must be disclosed
explicitly rather than quietly.

## D2 — Table III compares representations across different test splits (**important**)

The RGB-stack backbone runs use `dataset/splits/split_rgb_stack_seed42.csv`; the opacity-blend runs
use `split_opacity_blend_seed42.csv`. Those two files do not select the same images (the RGB-stack
split is identical to `split_rgb_seed42.csv`, the opacity one is not).

So "RGB-stack ResNet18 0.7867 vs opacity blend ResNet18 0.7733" is a **one-sample difference measured
on two different 75-image test sets**. It cannot support "RGB-stack achieves the best clean
performance" as a performance claim.

**Fix (cheap):** re-run the three opacity-blend backbones on the RGB split file so the comparison is
paired, or drop the performance framing and select RGB-stack on the design argument the paper
already makes (explicit channel separation is required for channel-aware analysis). The second
option costs nothing and is more honest.

## D3 — The poisoned subset is resampled every round (**must be stated**)

`train_fl_backdoor.py` rebuilds the malicious client's dataset each round with
`seed = cfg.seed + round_id + client_id`, so the 2 poisoned images change from round to round. The
paper's III.E reads as if a fixed 20% subset is poisoned once. Both facts — 2 images, and per-round
resampling — belong in the threat model. See `docs/CODE_FACTS.md`.

## D4 — Per-round curves are test-set curves (**must be stated**)

The backdoor and defense scripts evaluate the global model on the **test** split every round and
never touch `val_ds`. Figures 5–7 are therefore test-set trajectories. The paper does not say which
split they come from. Monitoring the test set does not bias the reported numbers here (no model
selection is done on it), but it must be labelled correctly.

## D5 — Round-1 ASR artefact (**explain, don't hide**)

`results/defense_blue_multi_krum/history.json` round 1: clean accuracy 0.24, ASR 0.60. The untrained
global model collapses onto one or two classes, so ASR at the start is meaningless. The paper says
ASR "gradually increases", which contradicts the visible early spike in Fig. 6. One sentence fixes it.

## D6 — Unreported runs that would strengthen the paper (**opportunity**)

Three finished runs are not in any table:

| Run | Setting | Result |
|---|---|---|
| `fl_backdoor_rgb_resnet18_red_p30_s12_r50` | red, poison 30%, trigger 12% | ASR 5/15 |
| `fl_backdoor_rgb_resnet18_full_p30_s12_r50` | full, poison 30%, trigger 12% | ASR 15/15 |
| `fl_backdoor_rgb_resnet18_api_trigger_seed42` | red, poison 10%, 30 rounds, trigger 8% | ASR 5/15 |

Together they show that the red channel stays at 5/15 even when the poison rate is tripled and the
trigger enlarged, while full-RGB is already saturated at 20%. That is a free robustness check
against "your 20% / 10% choice is arbitrary" and belongs in the sweep discussion as a sentence or a
small table.

## D7 — Naming inconsistencies (**cosmetic, but confusing**)

`fl_backdoor_rgb_resnet18_api_trigger_seed42` is a red-channel run, not an "API trigger" run in the
sweep sense; the two `_r50` directories are seed 42 but do not say so; `defense_*` without a seed
suffix means seed 42. The exporter (`scripts/export_runs.py`) resolves all of this into
`results/runs.csv`, so nothing downstream depends on the directory names — but new runs should
follow the naming rule in `references/experiment_protocol.md`.

## D8 — Repository hygiene (**do before sharing the code**)

- `results/` and `drafts/` are untracked and there is no `.gitignore`.
- The split CSVs contain absolute Windows paths (`C:\Users\wwyl5\...`) in `absolute_path`, which is
  why they show as modified in `git status`. `MalwareImageDataset._resolve_path` falls back to
  `dataset_root`, so the column is not needed — consider dropping or blanking it before publishing.
- `dataset/processed/` holds the derived images; decide what is redistributable before any
  artefact release.
