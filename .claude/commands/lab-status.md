---
description: Show experiment queue status, latest result tables, and revision progress
allowed-tools: Bash(python3:*), Bash(python:*), Read, Glob
---
# Current state

Run matrix vs recorded runs:
!`python .claude/skills/fl-backdoor-lab/scripts/check_runs.py 2>&1 | head -20`

Generated tables:
!`ls -la results/tables 2>/dev/null | tail -n +2`

Unresolved paper-vs-code discrepancies:
!`grep -c '^## D' docs/DISCREPANCIES.md 2>/dev/null || echo 0`

Revision plan progress (Tier 1 unchecked items):
!`grep -c '^- \[ \]' docs/REVISION_PLAN.md 2>/dev/null || echo 0`

# Task
Summarise where the project stands in at most 10 lines: what is done, what is pending per tier,
whether runs.csv validates, and the single next action you recommend. Do not start any work.
