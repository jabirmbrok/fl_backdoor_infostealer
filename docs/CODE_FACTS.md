# Code facts — what the implementation actually does

Answers to the questions the paper leaves open, read out of this repository. Cite these when
writing the camera-ready; they are the ground truth, not the paper's prose. Update this file if the
code changes.

Verified on the state of the repo as uploaded (commit `16b996c`, results generated 2026-07-18/21).

## Representation and data

| Question | Answer | Where |
|---|---|---|
| Image size and format | 128×128 RGB PNG, 500 files under `dataset/processed/dataset_rgb_stack_combined/<Family>/` | split CSVs, `width`/`height` columns |
| Normalization | `Resize(128) → ToTensor() → Normalize(mean=.5, std=.5)` → tensor in [-1, 1]. **No augmentation.** | `src/data/image_dataset.py:build_transform` |
| Label mapping | AgentTesla 0, FormBook 1, SalatStealer 2, StealC 3, Vidar 4 (alphabetical) | `dataset/splits/*.csv` `label_id` |
| Split | 350 train / 75 val / 75 test, 100 per family | `dataset/splits/split_rgb_seed<N>.csv` |
| **Split vs seed** | **Re-drawn per seed.** Test-set overlap between seed 42 and 123 is 8/75, and 13/75 between 42 and 2026. | comparison of the three split CSVs |
| Client partition | 5 clients × 70 samples, exactly **14 per family per client** — perfectly balanced IID. Comes from the `client_iid` column, so it changes with the seed. A `client_noniid` column already exists but is unused. | split CSVs |

*Consequence:* because the split is re-drawn per seed, pooling triggered samples across seeds for a
Fisher exact test is defensible — the samples differ. Say so explicitly in the paper.

## Representation construction (`scripts/creation/`, added 2026-09-02)

The builders that were missing during the audit are now in the repo, so the fusion formula is no longer
an open question.

**RGB-stack** (`RGB_stack_combined_dataset.py`). The API tile (natively 16x16 RGB) and the network tile
are each converted to grayscale, min-max normalized per image to the full 0-255 range, and resized to
128x128 with bicubic resampling. Then:

    R = API tile (grayscale, normalized, 128x128)
    G = network tile (grayscale, normalized, 128x128)
    B = FIND_EDGES( (R + G) / 2 )

where `FIND_EDGES` is PIL's 3x3 edge-detection convolution and the mean uses integer division.

**The blue channel is therefore a deterministic function of the other two.** It carries no information
that R and G do not already contain. Verified against the shipped dataset: recomputing
`FIND_EDGES(mean(R, G))` reproduces the stored blue channel with zero difference on 400 of 400 images.
Measured on the images themselves, 54.5 per cent of blue pixels are exactly 0 and the channel mean is
11.9, which is why the trigger-region contrast in `results/tables/channel_stats.md` is 233 for B against
40 for R.

*Consequence for the paper:* calling B "fused information derived from both sources" is misleading. It is
an edge map of the average. This also settles the alternative explanation Reviewer C raised, that blue's
effectiveness might come from its information content: blue has no independent information content by
construction, so the explanation has to be saliency in an otherwise near-empty channel.

**Opacity blend** (`Opacity_blend_combined_dataset.py`). The API tile is kept in colour and resized to
128x128 (Lanczos); the network tile is grayscale. With `A` the API image in [0,1] and `T` the shaped
network texture:

    T = unsharp( normalize(NET)^0.85, radius 0.9, percent 140, threshold 2 )
    k = 0.70 + 0.90 * T
    O = clip(A * k)
    OUT = clip(0.30 * A + 0.70 * O)

followed by a final unsharp mask (radius 0.6, percent 80, threshold 2). Constants in the script:
`ALPHA = 0.70`, `BASE_GAIN = 0.70`, `TEX_GAIN = 0.90`, `CONTRAST_POW = 0.85`.

So opacity blend modulates a colour API image by a network-derived texture; it has no channel that
corresponds to one source, which is the design reason RGB-stack is used for channel-aware analysis.

## Trigger

| Question | Answer | Where |
|---|---|---|
| Trigger value | `value=1.0` written **after** normalization, i.e. the maximum of the normalized range, equivalent to raw 255 (white) in the selected channel(s) | `image_dataset.py:apply_square_trigger` |
| Patch size | `patch = max(1, int(min(h, w) * size_ratio))` = `int(128 × 0.10)` = **12 px** (not 12.8, not 13) | same function |
| Location | bottom-right corner | `trigger_location: bottom_right` in every config |
| Channel map | red/api → channel 0, green/network → 1, blue/fusion → 2, full/rgb → all three | same function |
| Applied to | training: only the malicious client's poisoned samples. Evaluation: all 15 source-class test samples, labels unchanged; ASR counts predictions equal to the target label | `train_fl_backdoor.py`, `engine.py:attack_success_rate` |

## Attack

| Question | Answer | Where |
|---|---|---|
| Attacker | client 0 of 5, participates in **every** round | `attack.malicious_client: 0`, loop in `train_fl_backdoor.py` |
| Capability | **pure data poisoning**. No update scaling, no model replacement. The malicious client trains and submits like everyone else. | `train_fl_backdoor.py` (no scaling anywhere) |
| Poison rate denominator | the malicious client's **source-class** training samples: `n_poison = max(1, int(len(source_rows) × poison_rate))` = `int(14 × 0.2)` = **2 images** | `image_dataset.py`, poison-index block |
| Poisoned set stability | **re-sampled every round**: `seed = cfg.seed + round_id + client_id`. Over 50 rounds the attacker touches many different AgentTesla images, not a fixed pair. | `train_fl_backdoor.py`, dataset construction inside the round loop |
| Relabelling | poisoned samples get `label = target_label` (FormBook) | `image_dataset.py:__getitem__` |

*Consequence:* 20% is 2 images out of the 350-sample global training set, about **0.6%**, and yet ASR
reaches 100%. That is a stronger result than the paper currently claims, and it also explains why
robust aggregation struggles: an update built from 2 relabelled images is not an outlier. Both the
2-image figure and the per-round resampling must be stated in III.E — as written, the paper implies
a fixed poisoned subset.

## Training

| Question | Answer | Where |
|---|---|---|
| Optimizer | **AdamW**, lr 1e-4, weight decay 1e-4 | `train_fl_backdoor.py`, `train_fl_clean.py` |
| Pretrained weights | **No** — `build_model(..., pretrained=False)` hardcoded in the FL scripts; `pretrained: false` in the centralized configs | `src/models/build.py`, configs |
| Loss | `nn.CrossEntropyLoss` | training scripts |
| FL aggregation | FedAvg weighted by client sample count; non-float buffers copied from client 0 | `train_fl_backdoor.py:aggregate_states` |
| Reported checkpoint (FL) | **final round**, no best-val selection | end of the FL scripts |
| Reported checkpoint (centralized) | **best validation macro-F1**, then evaluated on test — no leakage in Table III | `train_centralized.py:82-88` |
| Validation set use | clean FL logs per-round val metrics; the **backdoor** scripts build `val_ds` and never use it, logging per-round **test** metrics instead | `train_fl_backdoor.py` |
| SmallCNN | 3 conv blocks (32 → 64 → 128), each Conv3×3 + BatchNorm + ReLU, MaxPool after the first two, AdaptiveAvgPool after the third, then Linear(128 → 5) | `src/models/build.py:SmallCNN` |
| Seeding | `random`, `numpy`, `torch`, `cuda`, plus `cudnn.deterministic = True`, `benchmark = False` | `src/training/utils.py:set_seed` |

*Consequence:* Figs. 5–7 are **test-set** curves, not validation curves. Describe them as such. The
validation split plays no role in the FL experiments — either say that or use it.

## Defenses

| Question | Answer | Where |
|---|---|---|
| Multi-Krum f | `byzantine_clients: 1` | `configs/defense/*multi_krum*.yaml` |
| Multi-Krum \|S\| | `selected_clients: 2` — the **2** lowest-scoring updates out of 5 are averaged, weighted by sample count | same, `train_fl_backdoor_defense.py:multi_krum` |
| Krum score | sum of squared L2 distances to the `n − f − 2 = 2` nearest updates, computed on flattened update vectors (local minus global) | `train_fl_backdoor_defense.py:krum_scores` |
| Clipping | L2-norm clip of each update to `max_norm` from the config | `clip_update` |
| Median / trimmed mean | coordinate-wise median; trimmed mean drops `trim_count` from each end | `coordinate_median`, `trimmed_mean` |
| Selection log | already recorded per round as `selected_clients` in `results/defense_*/history.json` | defense script, history rows |

## Numbers that matter for the discussion

**Multi-Krum selection rate vs ASR** (`scripts/selection_stats.py`, from the existing logs):

| Run | Malicious client selected | Final ASR |
|---|---|---|
| blue, seed 42 | 25/50 rounds (50%) | 15/15 |
| blue, seed 123 | 4/50 (8%) | 3/15 |
| blue, seed 2026 | 16/50 (32%) | 5/15 |
| full, seed 42 | 14/50 (28%) | 6/15 |
| full, seed 123 | 22/50 (44%) | 15/15 |
| full, seed 2026 | 9/50 (18%) | 6/15 |

Pearson r = 0.893 (p = 0.017), Spearman rho = 0.794 (p = 0.059), n = 6. **This is the mechanism**:
Multi-Krum is not weaker against one channel than another; it fails in the seeds where the poisoned
update happens to stay inside the selected pair often enough. That is what the discussion should say
instead of "partially suppresses the backdoor".

**Per-channel intensity of the clean RGB-stack images** (`scripts/channel_stats.py`, all 500 images):

| | R | G | B |
|---|---|---|---|
| mean intensity | 241.7 | 81.5 | 10.2 |
| contrast of a white trigger | 40.4 | 206.7 | 233.4 |
| trigger-region pixels already ≥ 254 | 37.7% | 0.3% | 0.0% |

The red channel is nearly saturated: over a third of the trigger region is already white, so the
red trigger is close to a no-op — that explains its failure without any appeal to semantics. But
green has almost as much headroom as blue and still fails, so contrast alone does **not** explain
the full ordering. This is a better, more honest discussion than either the pure "channel semantics"
story or the pure saliency story, and the Tier 3 contrast-matched run is the experiment that
separates them.

**Trigger control**: for 7 of the 8 control runs, the target-prediction rate is **identical** with
and without the trigger (only full/seed 2026 moves, 1/15 → 2/15). So the control measures the clean
model's natural AgentTesla→FormBook confusion, and the trigger by itself changes essentially
nothing. The paper's conclusion holds; the wording should be this precise.
