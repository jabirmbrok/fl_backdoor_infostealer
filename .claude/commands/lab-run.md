---
description: Launch pending experiments for a tier via the experiment-runner subagent
argument-hint: [tier: 0 | 2 | 3] [optional: exp_id filter]
allowed-tools: Bash(python3:*), Bash(python:*), Read, Glob, Task
---
Pending runs for the requested tier:
!`python .claude/skills/fl-backdoor-lab/scripts/check_runs.py --pending --tier ${1:-2} 2>&1 | tail -40`

# Task
Arguments: $ARGUMENTS

Use the experiment-runner subagent to execute the pending runs listed above (tier ${1:-2}, filtered
by any exp_id pattern in the arguments). Before delegating:

1. Confirm runs.csv validates. If not, stop and report.
2. Show me the ordered plan (exp_id, seed, command, estimated time) and the total estimated GPU time.
3. Ask me to confirm before launching if the plan is longer than 6 runs or 4 hours.

Runs execute one at a time. After each one, the row must be appended to results/runs.csv and the
file must still validate. Report progress as runs complete.
