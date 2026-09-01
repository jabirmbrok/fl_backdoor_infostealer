# Metrics and statistics

## Definitions

- **Clean accuracy / macro-F1**: on the 75 clean test samples (15 per family). One sample = 1.33
  accuracy points, so 0.7867 = 59/75, 0.8267 = 62/75, 0.84 = 63/75.
- **ASR** (paper eq. 2): among test samples with source label ys (AgentTesla, n = 15), the fraction
  predicted as the target label yt (FormBook) after the trigger T(·) is applied. Resolution 1/15 =
  6.67 points; every ASR in the paper is a multiple of 1/15 (0.3333 = 5/15, 0.4 = 6/15).
- **Trigger-control target rate**: the same quantity measured on the *clean* (unpoisoned) FL model.
  It is the baseline: an attack is effective only relative to it. Note that it includes the natural
  AgentTesla→FormBook confusion of the clean model.
- **Malicious-selection rate** (defense runs): fraction of rounds in which the attacker's update
  survived Multi-Krum, from `selected_clients` in `history.json`. Across the six existing runs it
  correlates with the final ASR at Pearson r = 0.893 (p = 0.017) — this is the mechanism behind the
  seed-dependent failure, and `selection_stats.py` computes it.

## Aggregation conventions

- Mean ± std across seeds with **std ddof = 1** (sample std). This reproduces the paper's numbers
  (e.g., clean FL 0.8267 ± 0.0133 from 63/75, 62/75, 61/75).
- Report 4 decimals in tables, percentages with 2 decimals in text.
- Always show the per-seed values (accuracy per seed, `hits/n` per seed) next to the mean ± std.
  With 3–5 seeds the mean hides the distribution; reviewer C explicitly asked for this.
- Flag any group whose ASR range across seeds is ≥ 0.5 (`aggregate.py` does). Such a group is
  described as "the defense failed completely in k of n seeds and reduced ASR to x–y in the others",
  never as "reduced the average ASR to 51%".

## Significance tests (`stats_tests.py`)

**ASR comparisons — Fisher exact test on pooled counts.** Pool hits and n across seeds for the two
groups (e.g., backdoor 45/45 vs trigger-control 6/45) and run a two-sided Fisher exact test.
In this repository the split **is re-drawn per seed** (test-set overlap between seeds 42 and 123 is
8/75), so the pooled samples are genuinely different images and the test is defensible. Say so in
the paper; do not pass `--shared-test-split`.
Default comparisons: each attack vs its trigger-control; FedAvg vs Multi-Krum per channel; blue vs
red and blue vs green.

**Clean-performance comparisons — paired across seeds.** Paired t-test and Wilcoxon signed-rank on
clean accuracy / macro-F1 with seeds as pairs. With n = 3 the smallest achievable two-sided
Wilcoxon p is 0.25 and the t-test has 2 df; with n = 5 it is 0.0625 / 4 df. State n and the caveat.
A non-significant difference here supports "clean performance is preserved" only weakly; say
"no detectable difference at n = 5 seeds", not "no difference".

**What not to do.** No tests on single-seed rows (Tables III, IV, VI). No confidence intervals
computed from n = 3 as if they were tight. No claims of "significant" without the test named,
the n, and the p-value in the same sentence.

## Phrasing rules for the paper

- "reached 100% ASR in all five seeds (75/75 triggered samples)" — counts, not just percentages.
- "Multi-Krum eliminated the backdoor in two seeds (3/15, 5/15) and failed in one (15/15)" — per seed.
- "the poisoned update survived selection in 25 of 50 rounds in that seed, against 4 of 50 where the
  defense held" — the mechanism, not just the outcome.
- "two relabelled images per round, 0.6% of the global training set" — the actual attack budget.
- "clean accuracy differed from the clean baseline by +0.4 ± 6.0 points (paired t, n = 5, p = 0.9)".
- "in this controlled IID setting with one malicious client out of five" — every strong claim
  carries its scope.
