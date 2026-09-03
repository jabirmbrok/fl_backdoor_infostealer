# Camera-ready revision plan

All three reviewers: score 3, accept with minor revisions. Reviewer tags: (A), (B), (C).
Full reports in `reviews.md`.

## Reviewer comments, grouped

1. Figures/tables not referenced or misplaced (A, B): Fig. 1 never discussed; Fig. 2 cited in
   III.B but shows dataset creation (III.A); Fig. 4, Table I, Table II never cited.
2. Experimental procedure unclear (A, C): stages not defined step by step; Fig. 1 blocks not
   mapped to the text; methodology dense, no transitions.
3. Thin statistics (B, C): 3 seeds only; no significance tests; 0.5111 ± 0.4286 is bimodal, not
   "partial mitigation"; seed 42 reused for backbone selection, trigger sweep and defense screening.
4. Over-claiming (C): one source→target pair; IID-only while the motivation is non-IID;
   "serious threat" needs moderating.
5. Threat model underspecified (C): pure data poisoning or model replacement/scaling as in [12]?
6. Multi-Krum utility cost hidden (C): clean acc 0.84 → 0.76 in Table VI must appear in the
   abstract and discussion.
7. Discussion lacks interpretation and citations (A, C): explain *why*; compare with prior work;
   address the alternative explanation for the blue channel (channel information/contrast).
8. Novelty (A, B, C): abstract must state novelty explicitly; compare with closest related work.
9. Small: SmallCNN architecture (B); too many keywords (B): 7 to 4-5; English "Fair" (A).

Code audit results are in `docs/CODE_FACTS.md` and `docs/DISCREPANCIES.md`. Several Tier 1 items
below are now answered or have become concrete re-runs (D1, D2). Read those two files first.

Additional issues found in our own read-through (cheap, fix while we are at it):
- Ref [19] is in the list but never cited (probably meant for SmallCNN in III.C → "[19]-[21]").
- Ref [15] used contradictorily: II.C says robust aggregation is insufficient, III.F uses it to
  justify Multi-Krum's "robustness" → cite [13] and frame Multi-Krum as a standard baseline.
- Ref [25] cited for cross-entropy loss; drop it.
- Text says ASR "gradually increases" but Fig. 6 starts at ≈0.9 at round 1 (untrained model
  collapsing to one class) → explain the artefact.
- Notation: w^(k)_{t+1} in (1) vs w^{t+1}_k in (3)-(5); Fig. 4 uses ω.
- Table IV, Fig. 5, Fig. 6 do not state the seed; trigger-control not defined in Methodology.
- "Normalized to [0, 255]" → say rescaled to 8-bit, then to [0, 1] for the CNN (verify in code).
- Affiliation: "BPS-Statistics Indonesia, Bantaeng Regency". Ref [23] formatting; DOIs inconsistent.

## Tier 1: text only (mandatory)

- [x] New opening paragraph of Section III that cites Fig. 1 and maps each block to a subsection:
      Dataset Creation → III.A, Representation Construction → III.B, Model Selection → III.C,
      FL Experiments → III.D, Backdoor Attack Evaluation → III.E, Trigger Control & Defense → III.F,
      Result Analysis → IV. Add one transition sentence between III.B/III.C/III.D/III.E.
- [x] Cite Table I in III.A, move the Fig. 2 reference to III.A, Fig. 3 in III.B, Fig. 4 in III.D,
      Table II in III.G. Every table/figure discussed in at least one sentence.
- [x] III.E: state explicitly, from `docs/CODE_FACTS.md`, that the attack is data poisoning only, no update scaling or
      model replacement; the malicious client is client 0 and participates in every round; the poison
      rate is 20% of the attacker's 14 source samples = 2 images, resampled every round; the
      trigger is a white 12x12 square written after normalization; channel-wise definition of T(.).
      Keep [12] as background only. Define the trigger-control experiment here, and state that in
      7 of 8 controls the target rate is identical with and without the trigger.
- [x] III.B: define the fusion channel and the opacity-blend formula. Closed 2026-09-02:
      `scripts/creation/` was added to the repo; see `docs/CODE_FACTS.md`. The note it replaced
      read: the RGB-stack images are pre-built in `dataset/processed/`; the script that produced
      them is not in this repo, so the fusion formula must come from the notebook or script used at
      dataset-construction time. This is the one methods gap the code audit could not close.
- [x] III.C: describe SmallCNN (3 conv blocks 32/64/128, Conv3x3 + BN + ReLU, MaxPool after the
      first two, AdaptiveAvgPool, Linear(128->5)); cite [19]-[21]. Also resolve D2: either re-run the
      opacity-blend backbones on the RGB split, or drop the performance framing of Table III.
- [x] III.D/III.H: 5 IID clients of 70 samples, 14 per family; AdamW; ResNet18 from scratch;
      the reported FL model is the final round (no best-val selection) while Table III uses the
      best-validation centralized checkpoint; the validation split is unused in the backdoor runs
      and Figs. 5-7 are test-set curves (D4). Disclose or fix D1 (seed 42 clean FL at 30 rounds).
- [x] III.F: describe clipping (L2 clip to max_norm), coordinate-wise median and trimmed mean with
      their parameters, and Multi-Krum with f = 1 and |S| = 2 of 5 clients.
- [x] Abstract: one explicit novelty sentence; mention Multi-Krum's clean-accuracy cost; replace
      "serious threat" with "a serious threat in this controlled IID setting".
- [x] IV: add interpretation paragraphs, starting with why blue works (per-channel intensity statistics; contrast
      vs. channel semantics), why Multi-Krum fails (poisoned update not an outlier; consistent with
      [15], [22]), position 100% ASR relative to [8], [12], [24], relation to color backdoor [9].
      Explain the round-1 ASR artefact in Fig. 6 (D5). Emphasise the 0.84 -> 0.76 utility drop.
      Use the two measured mechanisms: the malicious-selection rate vs ASR correlation
      (r = 0.893, p = 0.017, `results/tables/selection_stats.md`) and the per-channel intensity
      statistics (R already saturated in 37.7% of the trigger region, B empty;
      `results/tables/channel_stats.md`). Note that contrast explains red's failure but not green's,
      which is why the contrast-matched run matters.
- [x] Conclusion: replace "partially reduced" with the bimodal description (defense failed entirely
      in one of three seeds); add limitations: single source→target pair, IID, 1-of-5 malicious
      client with full participation, small test set (15 source samples per seed).
- [x] II.C: add backdoor-on-malware-classifier work: Severi et al., USENIX Security 2021
      (explanation-guided backdoor poisoning) and Yang et al., IEEE S&P 2023 (Jigsaw Puzzle).
      One sentence positioning our work against them and against [9].
- [x] Tables V and VII: show per-seed values (footnote or extra columns). Done; the two tables are now one.
- [ ] Keywords: 4-5. Fix the notation, affiliation, references listed above. Proofread English.
- [ ] Keep `docs/CHANGES.md` updated; it becomes the summary of changes for the editors.

Space to reclaim if there is a page limit: II.A repeats intro paragraph 2 almost verbatim; the
browser-extension sentence [3] in the intro; "two local epochs" appears in III.D and III.H;
Table II can become one sentence.

## Tier 1b: re-runs required by the audit (see `docs/DISCREPANCIES.md`)

- [x] D1: clean FL seed 42 at 50 rounds / 2 local epochs + its four trigger controls (5 runs, cheap).
      Done; the re-run is worse (0.7867 acc) and the hypothesis about the control rate was refuted, so the
      submitted numbers were kept and the deviation is disclosed in III.H. See `docs/DISCREPANCIES.md` D1.
- [x] D2: three opacity-blend backbones on `split_rgb_seed42.csv`, or reword the Table III claim.
      Done by rewording: the cross-representation performance claim is dropped in III.C, IV.A, the abstract
      and the conclusion; RGB-stack is now selected on the channel-separation argument.
- [ ] D6: add the three existing unreported ablations (red/full at poison 30% + trigger 12%, and the
      10%-poison red run) to the sweep discussion; no new compute, they are already in runs.csv.

## Tier 2: cheap experiments (strongly recommended; answers B and C directly)

- [ ] Create `dataset/splits/split_rgb_seed7.csv` and `split_rgb_seed99.csv` first, because the split is
      seed-dependent in this repo.
- [ ] Add 2 seeds (-> 5 total) for: clean FL, blue/fusion FedAvg, full-RGB FedAvg,
      blue/fusion + Multi-Krum, full-RGB + Multi-Krum -> 10 runs.
- [ ] Red/API and green/network across all seeds → 4 runs (seed 42 exists).
- [ ] Clipping, median, trimmed mean × {blue, full-RGB} × 2 extra seeds → 12 runs. This removes the
      "seed-42 selected the defense" objection.
- [ ] Trigger-control across all seeds for red/green too (evaluation only, no training).
- [x] Log per round which clients Multi-Krum selects: already implemented; `selection_stats.py`
      reports it (r = 0.893 with final ASR across the six existing runs).
- [x] Per-channel intensity statistics: done, `results/tables/channel_stats.md`.
      R mean 241.7 / G 81.5 / B 10.2; 37.7% of the red trigger region is already >= 254.
- [x] Significance tests (results-analyst): done, `results/tables/stats.md`, written into IV.B and IV.D:
      - ASR: hits/n per seed; pooled Fisher exact test backdoor vs trigger-control and FedAvg vs
        Multi-Krum. The split is re-drawn per seed here, so pooling is legitimate; state that.
      - Clean accuracy / macro-F1: paired test across seeds (Wilcoxon or paired t), with the caveat
        that n is small.
- [ ] Regenerate Tables III-VII and Figs. 5-7 from `results/runs.csv`.

## Tier 3: optional

- [ ] Second source→target pair for the blue trigger (e.g., Vidar → StealC), all seeds.
- [ ] Contrast-matched trigger (same per-channel intensity delta in R, G, B) to test the saliency
      hypothesis against the "channel semantics" narrative.
- [ ] Backbone selection across 3 seeds (centralized, 6 configs × 2 extra seeds = 12 short runs).

## Workflow blocks (mirror of Fig. 1)

Keep the code organised as one module/entry point per block so each block can be re-run alone:
`dataset_creation` → `representation` → `model_selection` → `fl_train` → `backdoor_attack` →
`trigger_control_and_defense` → `result_analysis`. Map existing scripts onto these in the Repo map.
