# Summary of changes (camera-ready)

One row per edit. Reviewer items use the codes from `docs/reviews.md`: A/B/C plus a keyword.
This file becomes the summary of changes for the editors.

| # | Reviewer item | Section | Change | Evidence | Status |
|---|---|---|---|---|---|
| 1 | — | — | *(example)* Added Fig. 1 walkthrough at the start of Section III | — | todo |
| 2 | C — bimodal ASR | IV.D, Table VII | Table VII gains an `ASR per seed (42, 123, 2026)` column with raw counts, and a dagger note on both Multi-Krum rows stating that the across-seed range is >= 0.5, so the mean describes no individual run | `results/tables/summary.md` (per-seed long table); `results/runs.csv` | done |
| 3 | C — bimodal ASR | IV.D | Rewrote the paragraph introducing Table VII: Multi-Krum's effect is described as bimodal rather than as graded partial mitigation, and the single-seed screening in Table VI is now flagged as using seed 42, the seed at which blue/fusion + Multi-Krum fails | `results/tables/summary.md` | done |
| 4 | C — "partially suppresses" imprecise | IV.D (Fig. 7 discussion) | Replaced "can partially suppress the backdoor effect" with the per-seed statement that for each trigger there is one seed at which Multi-Krum does not suppress the backdoor at all | `results/tables/summary.md` | done |
| 5 | C — conclusions overconfident | Conclusion | Replaced "Multi-Krum partially reduced ASR, but its effectiveness was inconsistent" with the bimodal description (15/15 on one of three seeds per trigger) | `results/tables/summary.md` | done |
| 6 | — (page limit) | II.A | Replaced the three sentences of II.A that repeated Introduction paragraph 2 almost verbatim with one sentence that keeps all four citations | — | done |
| 7 | — (page limit) | IV.C, IV.D | Reduced Figs. 5 and 6 from 0.75 to 0.65 of the column width and Fig. 7 from 0.40 to 0.38 of the text width, which brings the paper back to 6 pages | trial builds, see the note below | done |
| 8 | C — bimodal ASR / thin statistics | IV.C, Table V | Table V gains a `Per seed (42, 123, 2026)` column: trigger-control target rates 4/15, 1/15, 1/15 (blue) and 4/15, 1/15, 2/15 (full RGB), and 15/15 on every seed for both FedAvg backdoors | `results/tables/summary.md` | done |
| 9 | — (numbers) | Table V | Corrected the clean-model standard deviations to the generated values: accuracy 0.0133 -> 0.0134 and macro-F1 0.0105 -> 0.0104, in all three rows that carry them | `results/tables/summary.md`; std over 3 seeds with ddof = 1 is 0.013350 and 0.010427 | done |
| 10 | C — abstract overstates the defense; A/C — novelty | Abstract | Added an explicit novelty sentence (channels as the attack surface, fusion channel alone as effective as all three); replaced the 51.11 / 60.00 per cent average-ASR claim with the bimodal description; added Multi-Krum's clean-accuracy cost (84.00 -> 76.00 per cent on full RGB in the single-seed screening); qualified "serious threat" with "in this controlled IID setting" | `results/tables/summary.md`; Table VI for the utility drop | done |
| 11 | — (page limit) | IV.C / IV.D | Merged Table VII into Table V. The two `Backdoor, FedAvg` rows of Table VII duplicated Table V exactly, so the merged table carries clean FL, both trigger controls, both FedAvg backdoors and both Multi-Krum rows, with the dagger note. **The paper now has six tables; there is no Table VII.** | — | done |
| 12 | A/C — method transparency (D1) | III.H | Disclosed that the seed-42 clean FL baseline and its trigger controls come from a 30-round, one-local-epoch run; gave the re-trained values under the common budget (0.7867 accuracy, 0.7869 macro-F1, control rate 6/15 instead of 4/15) and stated that this sets a higher bar for the clean-performance claim and a lower one for the trigger-control argument | `results/runs.csv` rows `fl_clean_rgb_resnet18_iid_seed42_r50` and `clean_model_*_trigger_control_r50`; `docs/DISCREPANCIES.md` D1 | done |
| 13 | C — conclusions overconfident | IV.C | Replaced "the low trigger-control target rates indicate..." with the measured statement: in 7 of the 8 controls the target rate is identical with and without the trigger, so the control measures the clean model's baseline AgentTesla-to-FormBook confusion, not a trigger effect | `results/runs.csv`; the re-runs reproduce this on all four channels | done |
| 14 | B — Table II never mentioned | III.G | Folded the paragraph that restated Table II's contents into a single sentence that cites Table II, which also gives the table its first reference in the text | — | done |
| 15 | — (page limit) | III.D | Dropped "clients train locally for two epochs" from III.D; III.H states the local-epoch count | — | done |
| 16 | C — conclusions overconfident | Abstract | Aligned the abstract with row 13: "trigger-control experiments produce low target prediction rates" becomes "in seven of the eight trigger controls the target rate is identical with and without the trigger", so the abstract states the measured result rather than a weaker paraphrase of it | `results/runs.csv` | done |
| 17 | C — dense methodology | III opening | New opening paragraph citing Fig. 1 and mapping each workflow block to its subsection | — | done |
| 18 | B — Table I never mentioned | III.A | Added the first in-text reference to Table I | — | done |
| 19 | B — Fig. 4 never mentioned | III.D | Fig. 4 is now referenced, together with the client partition (5 clients, 70 images each, 14 per family, balanced IID) | docs/CODE_FACTS.md | done |
| 20 | B — SmallCNN undescribed | III.C | Described SmallCNN (3 blocks 32/64/128, Conv 3x3 + BN + ReLU, max-pool after the first two, adaptive average pool, Linear(128->5)) and stated that all backbones are trained from scratch | docs/CODE_FACTS.md | done |
| 21 | C — method underspecified (D3) | III.E | Stated the attack as implemented: 20 per cent of the attacker's 14 AgentTesla images = 2 images per round, resampled every round; white 12x12 trigger written after normalization; channel-wise T(.); malicious client 0 in every round; pure data poisoning, no scaling or model replacement, so [12] is background only | docs/CODE_FACTS.md | done |
| 22 | A/C — defenses underspecified | III.F | Multi-Krum f = 1 and |S| = 2 of 5; named the three screened coordinate-level defenses; defined the trigger control | docs/CODE_FACTS.md | done |
| 23 | C — reporting unclear (D4) | III.H | AdamW, ResNet18 from scratch, final-round model with no best-validation selection, validation split unused in the backdoor runs, so the per-round curves are test-set curves | docs/CODE_FACTS.md | done |
| 24 | C — unpaired comparison (D2) | III.C, IV.A, Abstract, Conclusion | Dropped the cross-representation performance claim: the two representations were measured on different splits, so Table III is not a paired comparison. RGB-stack is now selected on the design argument (explicit channel separation), with macro-F1 choosing the backbone within it | docs/DISCREPANCIES.md D2 | done |
| 25 | C — why does blue work | IV.B | Added the per-channel intensity mechanism: mean trigger-region intensity 241.7 R / 81.5 G / 10.2 B, so a white trigger moves B by 233 levels and R by 40, and 37.7 per cent of red trigger-region pixels are already >= 254. Contrast explains red's failure but not green's | results/tables/channel_stats.md | done |
| 26 | C — why does Multi-Krum fail | IV.D | Added the selection mechanism: the malicious client survives selection in 8-50 per cent of rounds and that rate correlates with final ASR (Pearson r = 0.893, p = 0.017, n = 6); with f = 1 and |S| = 2 of 5 the poisoned update is not an outlier. Also added the utility cost 0.8400 -> 0.7600 | results/tables/selection_stats.md | done |
| 27 | — (D5) | IV.C | Explained the round-1 ASR artefact: the near-initialization model collapses onto one or two classes | docs/DISCREPANCIES.md D5 | done |
| 28 | C — generalization, thin evidence | Conclusion | Positioned the attack against [8], [12], [24] and the colour-space backdoor [9], and listed the limitations: single source-target pair, IID, 1-of-5 malicious client with full participation, 15 source-class test samples per seed | — | done |
| 29 | A/C — missing related work | II.C | Added Severi et al. (USENIX Security 2021) and Yang et al. (IEEE S&P 2023) with a sentence positioning this work against them | — | done |
| 30 | B — too many keywords | Keywords | Reduced from 7 to 5 | — | done |
| 31 | A — Fig. 2 referenced in the wrong section | III.A, III.B | Moved the Fig. 2 reference from III.B to III.A, where the dataset-creation pipeline it depicts is described; Fig. 3 stays in III.B | — | done |
| 32 | B, C — no significance testing | IV.B | Reported the Fisher exact tests on the pooled triggered samples and corrected the red/green claim: they are indistinguishable from their trigger controls ($p = 1$, 5/15 against 4/15), not merely "less effective". Blue/fusion and full RGB differ from their controls at $p = 3.5 \times 10^{-19}$ and $p = 2.6 \times 10^{-18}$, and blue differs from red and green at $p = 4.0 \times 10^{-8}$. Stated that pooling is legitimate because the split is re-drawn per seed | `results/tables/stats.md` | done |
| 33 | B, C — no significance testing | IV.D | Added the Multi-Krum comparisons ($p = 1.5 \times 10^{-8}$ blue, $p = 9.1 \times 10^{-7}$ full RGB) and the caveat that no paired clean-performance difference across the three seeds is significant, including the utility drop (all $p \geq 0.42$, low-powered at $n = 3$) | `results/tables/stats.md` | done |
| 34 | A/C — representation underspecified | III.B | Wrote the actual construction of both representations. RGB-stack: grayscale, per-image min-max normalization, resize to 128x128, then R = API, G = network, B = FindEdges((R+G)/2). Stated that the blue channel is a deterministic function of the other two, adds no independent information, and is the emptiest channel (54.5 per cent of its pixels are zero). Opacity blend: 0.30 A + 0.70 clip(A (0.70 + 0.90 T)) with T the shaped network texture, so no channel corresponds to one source | `scripts/creation/`, verified against the shipped dataset; `docs/CODE_FACTS.md` | done |
| 35 | C — blue's information content untested | IV.B | Replaced the "channel semantics" claim: since the blue channel is a deterministic edge map of the other two, its effectiveness cannot come from information the others lack, so what distinguishes it is that it is almost empty. The remaining explanation is named as a hypothesis and pointed at the contrast-matched trigger run | `docs/CODE_FACTS.md`; `results/tables/channel_stats.md` | done |
| 36 | — (6-page limit) | IV.C | Dropped the two single-quantity per-round figures. The surviving per-round figure shows clean macro-F1 and ASR for every setting across all three seeds, so no measurement is lost | — | done |
| 37 | — (6-page limit) | IV.D | Turned the single-seed defense-screening table into one sentence carrying the same numbers: clipping, median and trimmed mean leave ASR at 1.0000; only Multi-Krum reduces it, and only on full RGB (1.0000 to 0.4000, clean accuracy 0.8400 to 0.7600) | `results/tables/summary.md` | done |
| 38 | — (6-page limit) | III.G | Condensed the experimental-environment table from seven rows to four, keeping every fact, and paid for it by reducing Figs. 2 and 3 from 0.80 to 0.70 of the column width. The table is kept | — | done |
| 39 | — (6-page limit) | throughout | Compressed fifteen passages without dropping a fact: III.B, III.C, III.E, III.F, III.H, the Section III opener, II.C, IV.A, IV.B, IV.D, the abstract and the conclusion | — | done |
| 40 | — (6-page limit) | References, Intro | Applied IEEE's "et al." rule to the two entries with seven and eight authors, dropped two optional DOI strings, and removed the browser-extension sentence in the Introduction together with its reference | — | done |
| 41 | — (6-page limit) | III.D | Reduced Fig. 4 from 0.95 to 0.60 of the column width; the figure is kept | — | done |
| 42 | C — conclusions overconfident | Conclusion | Matched the conclusion to Section IV (seven of eight controls identical with and without the trigger) and merged the two overlapping future-work sentences | `results/runs.csv` | done |
| 43 | — (narrative order) | IV.C | Moved the single-seed defense screening into its own subsection ahead of the multi-seed results, so the screening now reads as what it is: a cheap pass over four defenses on one seed, used to choose which one is worth evaluating across seeds. Added the reason explicitly --- screening every defense on every seed would multiply the training budget by the number of seeds for candidates that may not survive, and all runs share one GPU. The screening table is now Table V and the multi-seed table Table VI | — | done |
| 44 | — (concision) | Conclusion | Cut the limitation list to the three that carry weight (IID-only partition, single source-target pair, three seeds with red and green on seed 42 alone) and the future-work list to the three matching tests. Dropped the malicious-client-participation and test-set-size items, and the generic "larger datasets" future-work entry; representation-aware defenses already close the first paragraph | — | done |
| 45 | A/B — proofreading, notation, references | throughout | Unified the model notation (client subscript, round superscript) across (1), (3)--(5) and noted that Fig. 4 writes it as omega; stated that the equal client sizes make the sample-weighted Multi-Krum average reduce to the printed one; stopped citing [15] to justify Multi-Krum's robustness and used [13] as the standard baseline; dropped the reference cited only for cross-entropy loss; renumbered Severi and Yang to match citation order; added the seed to the sweep table caption; corrected "normalized to [0,255]" to 8-bit then [-1,1]; fixed a dangling "the two stages" left by an earlier cut; and condensed fourteen further passages | `docs/CODE_FACTS.md` | done |
| 46 | A — figures must state the seed | IV.C | Figs. 5 and 6 captions now say seed 42, confirmed by the author | — | done |
| 47 | — (concision) | Introduction | Cut from five paragraphs to four: the browser-extension sentence folded into the citation list of the opening sentence, the dynamic-analysis paragraph reduced to one sentence, and the five-sentence gap paragraph to three | — | done |
| 48 | — (concision) | Conclusion | Removed the positioning sentence against [8], [12], [24] and [9]. The capability difference (pure data poisoning, no update scaling) is already stated in III.E and the related-work positioning in II.C, so this was its third statement. Also merged the limitations and future-work sentences | — | done |
| 49 | — (concision) | Abstract | Same content in fewer words: the backbone and baseline sentences merged | — | done |
| 50 | — (6-page limit) | II.A, II.B, III.B, IV.C, IV.E, Abstract | Eight more passages condensed: II.B from three sentences to two, the II.B/III.B openings that restated their own first sentence, the Fig. 5/6 and Fig. 7 discussions that repeated their captions, and the abstract | — | done |
| 51 | — (6-page limit) | all figures | Every figure reduced to 0.90 of its width: Fig. 1 to 0.90 and Fig. 7 to 0.34 of the text width, Figs. 2 and 3 to 0.63, Fig. 4 to 0.54, Figs. 5 and 6 to 0.59 of the column width | — | done |
| 52 | — (legibility) | III.D | Fig. 4 enlarged from 0.54 to 0.75 of the column width, the largest size that still fits 6 pages with every reference kept. At 0.80 the paper runs to 7 pages, and at the 0.94 that was tried first it would have cost two references | measured with full builds | done |
| 53 | A — figure legibility | IV.E, `scripts/plot_per_round.py` | Regenerated Fig. 7 from `results/*/history.json` at the size it is placed at, instead of exporting at 8.5 in and shrinking to 2.4 in. Text now prints at 7.2 pt (axis), 6.2 pt (ticks) and 5.6 pt (legend) instead of 2.9 / 2.3 / 2.3 pt, and the figure occupies the same 245 x 148 pt as before, so the paper stays at 6 pages with every reference kept. Final-round ASR of all four curves reproduces Table VI exactly | `results/*/history.json`; `results/tables/summary.md` | done |
| 54 | — (reference pruning) | Introduction, References | Dropped the browser-extension reference, cited once in the opening sentence where the two remaining citations already carry the claim and where browser extensions play no further part in the paper. 25 references remain, all cited and in citation order | — | done |

## Cuts made for the page limit

| What was cut | Where it was | Why |
|---|---|---|
| Prose enumeration of the per-seed Multi-Krum ASR values | IV.D, paragraph before Table VII | The values are now a column in Table VII; repeating them in prose cost about four lines |
| Restatement of the ASR definition and of the mean +/- std convention | Table VII note | ASR is already defined formally in Section III (eq. before Table IV) |
| Three sentences of II.A (API-call, network, RGB-fusion) | II.A Dynamic Malware Representation | Near-verbatim repeat of Introduction paragraph 2; the citations are kept in one summarising sentence. Reclaimed about one line -- not enough on its own, see the note below |
| Sentence repeating Table V's clean-baseline numbers in prose | IV.C, before Table V | The table states them; the sentence added nothing |
| Table VII as a separate float, with its two duplicated FedAvg rows and its caption | IV.D | Merged into Table V, see row 11 |
| Paragraph restating Table II (Cuckoo/Ubuntu/Windows/PyTorch/CUDA/RTX 3080) | III.G Experimental Setup | The table lists all of it; the replacement sentence cites the table instead |
| "clients train locally for two epochs" | III.D | Duplicated III.H |

Note on the page limit: the per-seed column in Table V and the rewritten abstract pushed the paper to 7 pages
again. This time the cause was float placement, not text volume: a probe that removed the Table VII float
showed every line of text fitting on 6 pages, while the float itself could not be placed and was flushed to a
page of its own. None of the typographic remedies worked -- shrinking Figs. 5-7 (down to 0.50/0.30), relaxing
\dbltopfraction, \topfraction, \textfraction and the float counters, [!t] on the double floats, or shortening
the captions -- because the paper carries two full-width table* floats competing for the same page tops.
Merging Table VII into Table V removed one of them and the paper fits in 6 pages with no figure shrunk further
(Figs. 5 and 6 stay at 0.65 of the column width, Fig. 7 at 0.38 of the text width).

Consequences to keep in mind:
  - There is no Table VII any more. `results/paper_reported.csv` still says "Table VII" and "Table VI", which is
    correct -- that file records the submitted paper -- but the response letter must use the new numbering.
  - The paper is exactly full again. Any further addition needs a build to check, and float packing here is not
    monotonic, so a smaller float does not reliably mean fewer pages.

Note on the D1 disclosure (rows 12-15): the two disclosure edits pushed the paper to 7 pages, but this time the
seventh page held only reference text and no float, so prose cuts did move it -- unlike the float-bound case
above, where they did not. Measured: cutting the browser-extension sentence together with reference [3] gives
6 pages, and so do the two duplication cuts in III.D and III.G. The duplication cuts were chosen because they
lose no citation and no result, and because folding the Table II paragraph gives Table II its first mention in
the text, which is one of Reviewer B's items. Shrinking Figs. 5 and 6 further (0.60, 0.55) does not reach 6
pages here and was not used.

Note on the remaining Tier 1 batch (rows 17-30): **these do not fit in 6 pages.** With all of them applied the
paper builds to 7 pages, and the seventh page carries 4409 characters, roughly three quarters of a page, so
this is not a matter of a few lines. Measured with trial builds on top of the full batch:
  - dropping Figs. 5 and 6, whose content Fig. 7 already covers for every setting and seed: still 7 pages,
    2280 characters on the last page;
  - dropping Table II and folding it back into one sentence: still 7 pages, 3905 characters;
  - doing both: still 7 pages, 1974 characters.
So even after giving up two of the three per-round figures and the environment table -- content Reviewer C
praised -- about 2000 characters would still have to go. The decision is therefore between publishing at
7 pages, if the camera-ready allows it, and dropping some of the reviewer items above.

Build hygiene: MiKTeX's `pdflatex -output-directory` still writes `.aux`, `.log`, `.pdf` and `.synctex.gz`
into the working directory as well as into the output directory, and it reads the working-directory `.aux` in
preference to the one it just wrote. Two consequences, both found on 2026-09-02:

  - The two new citations reported as undefined even after three passes, because the stale working-directory
    `.aux` was the one being read.
  - Every build run from inside `paper/` also overwrote `paper/ieee_malware_fl_backdoor.pdf`, so the build of
    the submitted paper was replaced by a camera-ready build. The author confirmed a copy of the submitted PDF
    is kept elsewhere, so it was not restored; `paper/ieee_malware_fl_backdoor.pdf` is now the camera-ready
    build, not the submitted one. The `.tex` was never affected.

Builds are now made in an isolated scratch directory holding only the `.tex` and the figures, which is the
only safe way to compile this project. The leftover `.aux`, `.log` and `.synctex.gz` in `paper/` were deleted
on request; `.gitignore` already covers them.

Significance tests (`results/tables/stats.md`, generated 2026-09-02) are available but **not yet written into
the paper**. Two reviewers asked for them. The results that change what the paper should say:

  - Blue and full-RGB backdoors versus their trigger controls: Fisher exact p = 3.5e-19 and p = 2.6e-18.
  - **Red and green backdoors versus their controls: p = 1 in both cases** (5/15 against 4/15). The red and
    green triggers are not distinguishable from the clean model's baseline family confusion, so the current
    wording "remain less effective" overstates them; the measured result is no detectable effect at all.
  - Blue and full-RGB against blue and full-RGB under Multi-Krum: p = 1.5e-08 and p = 9.1e-07.
  - Blue against red and against green: p = 4.0e-08 for both.
  - Paired clean-performance comparisons across the three seeds: nothing significant (all p >= 0.42),
    including the Multi-Krum utility drop, which is why that drop is reported as a single-seed observation.
    With n = 3 these paired tests are low-powered and must be reported with that caveat.

Pooling the triggered samples across seeds for the Fisher tests is legitimate here because the split is
re-drawn per seed (`docs/CODE_FACTS.md`); the paper must say so when it reports these p-values.

Page-limit conclusion (measured 2026-09-02, after rows 32-33): **6 pages is not reachable with the reviewer
items accommodated.** The paper builds to 7 pages with 5109 characters on the seventh page. Ladder of cuts,
each measured with a full build:

| cut | result |
|---|---|
| drop Figs. 5 and 6 (Fig. 7 already covers both quantities for every setting and seed) | 7 pages, 3146 chars |
| turn Table VI into one sentence | 7 pages, 4409 chars |
| both of the above | 7 pages, 2280 chars |
| both, plus dropping Table II | 7 pages, 1536 chars |

So even after giving up two of the three per-round figures and two of the six tables, roughly 1500 characters
-- about twenty lines of prose -- would still have to go. At that point the paper is being dismantled to fit a
page limit, and what would be cut is exactly what the reviewers asked to have added. The realistic choices are
to publish at 7 pages if the camera-ready allows it, or to decide which reviewer items to drop. None of the
cuts in this ladder has been applied; the paper keeps all its figures and tables.

Fusion formula (2026-09-02): `scripts/creation/` was added to the repo, closing the one methods gap the code
audit could not. The blue channel turns out to be `FIND_EDGES((R+G)/2)`, reproduced with zero difference on
400 of 400 shipped images, so it is a deterministic function of the red and green channels rather than a
fusion carrying new information. This settles the alternative explanation Reviewer C raised for the blue
trigger's effectiveness -- it cannot be information content, because there is none that is independent -- and
it sharpens the headline result: the most effective attack surface is a derived channel that adds nothing, and
is therefore the channel a defender is most likely to dismiss as redundant. Full formulas for both
representations are in `docs/CODE_FACTS.md`.

After rows 34-35 the paper is 7 pages with 5704 characters on the seventh. Every Tier 1 item that does not
require new experiments is now done; the page-limit decision is the only thing blocking the camera-ready.

## Page budget: 6 pages attempted, 7 pages adopted

The camera-ready was first cut back to 6 pages on the understanding that the venue enforces that limit
strictly. The author then decided 7 pages is acceptable, so everything that had been sacrificed purely for
the limit was restored:

  - the two per-round figures (clean macro-F1 and ASR for the strongest settings);
  - the single-seed defense-screening table;
  - the browser-extension sentence in the Introduction and its reference.

The experimental-environment table had already been restored, condensed from seven rows to four. The paper
is now 7 pages with 7 figures, 6 tables and 27 references: the full float inventory of the submitted version,
except that the old Tables V and VII are merged into one, which removed two duplicated rows rather than any
result.

**If the 6-page limit turns out to be binding after all**, the measured route back is in the git history of
this file and in the scripts under the session scratchpad: drop the two per-round figures, fold the
defense-screening and environment tables into sentences, drop the browser-extension reference, and keep the
compressed wording. That combination was verified at 6 pages with no overfull boxes.

What was kept from the compression pass, because it lost no facts and reads better:

  - fifteen passages tightened across III.B, III.C, III.E, III.F, III.H, the Section III opener, II.C, IV.A,
    IV.B, IV.D, the abstract and the conclusion;
  - IEEE's "et al." rule applied to the two entries with seven and eight authors, and two optional DOI
    strings dropped;
  - Fig. 4 at 0.60 and Figs. 2 and 3 at 0.70 of the column width.

Items that remain in the limitations rather than being accommodated, all of them needing runs we did not do:
three seeds only with the red and green results resting on seed 42 alone, a single source-target pair, the
IID-only partition, and the saliency explanation for the blue channel with the contrast-matched trigger named
as its test.

Reference hygiene after this pass: 26 entries, all cited, none orphaned, all in order of first
citation (checked mechanically).

**The paper is back to 6 pages** with the full float inventory intact: 7 figures, 6 tables, 26 references,
no overfull boxes, no undefined references, every reference cited and in citation order. This was reached by
condensing wording and shrinking figures by 10 per cent, so nothing measured and no reviewer item was given up
to get there.

Figure sizing, measured: Fig. 4 at 0.75 of the column width is the ceiling for a 6-page paper with all 26
references. Going to 0.94 costs two of them, and the cheapest pair would be [26] (cited once, for the
definition of ASR, which Eq. (2) already gives) and [3] (cited once in the opening sentence, where [1] and [2]
already carry the claim). The author chose to keep both references and hold Fig. 4 at 0.75.

Fig. 7 was regenerated rather than resized. The shipped version was exported 612 pt wide with 8 pt tick
labels and then placed in a 175 pt column, printing them at 2.3 pt; no placement inside one column could fix
that, since even full column width reached only 3.3 pt. `scripts/plot_per_round.py` now rebuilds it from the
per-round histories at 3.45 x 2.10 in with 6-7 pt fonts, so it is placed at column width essentially 1:1. The
plotting code was previously missing from the repository; it is now in it, which also makes the figure
reproducible. Note that the conda environment must be on PATH for matplotlib to load its DLLs.

## Tier 2 completed (2026-09-03): five seeds, and the headline claim changes

34 jobs, 0 failures, 54 minutes. New splits for seeds 7 and 99 (test-set overlap with the existing seeds is
8-14 of 75, so the splits are genuinely re-drawn); configs in `configs/camera_ready/tier2/`, driver in
`scripts/run_tier2.sh`, generator in `scripts/make_tier2_configs.py`. `results/runs.csv` is now 79 rows and
validates.

**The paper's central number does not survive two more seeds.** Per seed, ASR out of 15:

| setting | seeds 7, 42, 99, 123, 2026 | pooled | as printed with 3 seeds |
|---|---|---|---|
| Backdoor, blue/fusion, FedAvg | 12, 15, 10, 15, 15 | 67/75 = 0.8933 +/- 0.1535 | 1.0000 +/- 0.0000 |
| Backdoor, full RGB, FedAvg | 15, 15, 11, 15, 15 | 71/75 = 0.9467 +/- 0.1193 | 1.0000 +/- 0.0000 |

Both new seeds fall short of 15/15, so "reach 100% ASR across three seeds" was true of the three seeds chosen
and is not a property of the attack. The attack is still overwhelmingly real: against its own trigger control
the blue backdoor gives Fisher exact p = 3.2e-22 (odds ratio 54) and full RGB p = 2.5e-25 (odds ratio 103).

What the extra seeds confirmed rather than changed:
  - Red and green remain indistinguishable from their controls, now on three seeds each rather than one:
    red 8/45 against 6/45, p = 0.77; green 10/45 against 6/45, p = 0.41. The seed-42-only caveat in the
    conclusion can go.
  - Multi-Krum is still bimodal, and more clearly so at five seeds: blue 15, 15, 2, 3, 5 and full 15, 6, 15,
    15, 6.
  - Clipping, median and trimmed mean still fail on three seeds each (blue 44/45, 42/45, 45/45; full 45/45 for
    all three), so the choice of Multi-Krum was not an artefact of seed 42. This answers Reviewer C's
    selection-bias objection directly.

Other numbers that move: the clean FL baseline over five seeds is 0.8080 +/- 0.0307 accuracy and
0.8090 +/- 0.0264 macro-F1, against 0.8267 +/- 0.0134 and 0.8255 +/- 0.0104 over three.

**No paper text has been changed on the basis of these runs yet.** Adopting them rewrites Tables IV, V and VI,
the abstract and the conclusion, and the space budget has to be re-checked.
