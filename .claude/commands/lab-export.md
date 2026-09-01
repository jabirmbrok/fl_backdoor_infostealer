---
description: Re-read results/ into the canonical runs.csv and validate it
allowed-tools: Bash(python3:*), Bash(python:*), Read, Glob
---
!`python .claude/skills/fl-backdoor-lab/scripts/export_runs.py --dry-run 2>&1 | tail -25`

# Task
Review the preview above, then run export_runs.py --force and check_runs.py.

Report: how many runs were exported, any row the exporter flagged with `<<`, whether runs.csv
validates, and how the tier counts changed. If a results directory was skipped as unrecognised,
say which one and why — the naming rule is in
.claude/skills/fl-backdoor-lab/references/experiment_protocol.md.
