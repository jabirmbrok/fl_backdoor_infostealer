---
description: Regenerate result tables, significance tests and channel statistics
argument-hint: [optional: what to focus on, e.g. "multikrum bimodality"]
allowed-tools: Bash(python3:*), Bash(python:*), Read, Glob, Write, Task
---
!`python .claude/skills/fl-backdoor-lab/scripts/export_runs.py --force 2>&1 | tail -4`
!`python .claude/skills/fl-backdoor-lab/scripts/check_runs.py 2>&1 | head -12`

# Task
Focus: $ARGUMENTS

Use the results-analyst subagent to:
1. Regenerate results/tables/summary.{csv,md,tex} with aggregate.py, including
   `--compare-paper results/paper_reported.csv`, and report any group that differs from the paper.
2. Regenerate results/tables/stats.md with stats_tests.py. Do NOT pass --shared-test-split: the
   split is re-drawn per seed in this repo, so pooling is legitimate.
3. Report per-seed values for every multi-seed group, and name explicitly any group whose ASR range
   across seeds is ≥ 0.5.
4. Run selection_stats.py and report the malicious-selection rate against ASR whenever Multi-Krum
   is discussed.
5. If the focus mentions channels or "why blue", also run
   channel_stats.py --split-csv dataset/splits/split_rgb_seed42.csv.

Finish with two or three sentences of interpretation that can go into the paper's discussion,
and the list of files written.
