---
description: Explore the repo, fill the CLAUDE.md repo map, and answer the open questions from code
argument-hint: [optional: subset of questions, e.g. "1-5"]
allowed-tools: Read, Grep, Glob, Bash(ls:*), Bash(find:*), Bash(wc:*), Edit, Write
---
Read CLAUDE.md, docs/CODE_FACTS.md, docs/DISCREPANCIES.md, and
.claude/skills/fl-backdoor-lab/SKILL.md.

Task (mode: map): $ARGUMENTS

Answer the question from the code, citing file and line. Do not train anything and do not edit
experiment code.

Rules:
- docs/CODE_FACTS.md already records what the implementation does for the settings the paper leaves
  open. Check it first; only re-read the source if the question is not covered or you suspect the
  file is stale.
- If your finding contradicts either the paper or CODE_FACTS.md, say so plainly and add it to
  docs/DISCREPANCIES.md with a proposed fix (re-run or disclose).
- Cite file:line for every claim. Mark anything you cannot establish as unresolved rather than
  guessing.

Report: the answer with citations, any new discrepancy, and which revision items it unblocks.
