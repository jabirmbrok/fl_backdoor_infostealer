---
description: Draft paper text or reviewer responses from the current results via the paper-editor subagent
argument-hint: [what to draft, e.g. "III.E threat model" | "discussion why blue" | "response letter"]
allowed-tools: Read, Grep, Glob, Edit, Write, Task
---
# Task
Draft: $ARGUMENTS

Use the paper-editor subagent. Ground every number in results/tables/ (regenerate first with
/lab-analyze if the tables are older than the newest row in results/runs.csv — say so instead of
guessing). Follow docs/REVISION_PLAN.md and docs/reviews.md; write in IEEE conference style.

Requirements:
- Name the reviewer item(s) each edit addresses.
- Keep per-seed reporting and the bimodal description of Multi-Krum intact.
- Leave \todo{...} for anything not yet supported by results, and list it.
- Append the change to docs/CHANGES.md.

Report: the drafted text, the reviewer items covered, and any remaining placeholders.
