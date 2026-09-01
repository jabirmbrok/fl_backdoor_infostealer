---
name: fl-backdoor-lab
description: Run, track, analyse and report the federated-learning backdoor experiments behind the channel-aware infostealer classification paper (run matrix, results/runs.csv, per-seed tables, Fisher and paired tests, per-channel intensity statistics) and drive the camera-ready revision plan. Use for any request about experiments, seeds, ASR, Multi-Krum, defenses, result tables, figures, or reviewer comments on this paper.
---

# fl-backdoor-lab

Project skill for the paper *Channel-Aware Backdoor Attacks Against Federated Infostealer Malware
Classification Using Dynamic API-Call and Network Representations* (IWBIS, accepted with minor
revisions). One skill, six modes. Pick the mode from what the user asks; when unsure, start with
`status`.

| Mode | Use when | Reads | Writes |
|---|---|---|---|
| `map` | "where is X implemented"; a methods detail the paper does not state | repo, `docs/CODE_FACTS.md` | `docs/CODE_FACTS.md`, `docs/DISCREPANCIES.md` |
| `export` | after any new run, or when runs.csv looks stale | `results/<run>/*.json` | `results/runs.csv` |
| `run` | "run the pending experiments", "launch seed 7", any training/evaluation | `experiments/run_matrix.csv`, `results/runs.csv` | `results/<run>/`, `logs/`, then `results/runs.csv` via export |
| `analyze` | tables, mean ± std, significance, "why does blue work", channel statistics | `results/runs.csv`, images | `results/tables/*` |
| `report` | text/tables for the paper, reviewer responses, summary of changes | `results/tables/*`, `docs/REVISION_PLAN.md`, `docs/reviews.md`, `docs/CODE_FACTS.md` | `paper/`, `docs/CHANGES.md` |
| `status` | "where are we", start of any session | everything above | nothing |

Delegate heavy work to the subagents in `.claude/agents/`: `experiment-runner` (run),
`results-analyst` (analyze), `paper-editor` (report). Keep the main session for decisions.

## Iron rules (hold even in long sessions)

1. Numbers come from `results/<run>/*.json` → `export_runs.py` → `results/runs.csv` →
   `aggregate.py` → `results/tables/`. Never type a result into the paper or a message from memory.
   If a number is not in runs.csv, say so.
2. `results/runs.csv` is generated. Re-run `export_runs.py --force` after new runs, then
   `check_runs.py`; if it reports validation errors, stop.
3. Methods statements come from `docs/CODE_FACTS.md`, not from the submitted paper's prose — the
   two disagree in the ways listed in `docs/DISCREPANCIES.md`.
4. One GPU job at a time. Hyperparameters stay exactly as in the paper unless the matrix row says
   otherwise. New runs get new configs under `configs/camera_ready/`; never edit the configs that
   produced the submitted results.
5. Per-seed values are always shown next to mean ± std (ddof = 1). When the ASR range across seeds
   is ≥ 0.5, describe the outcome as bimodal/unstable — never as a mean alone.
6. Never modify `dataset/processed/`, `dataset/splits/`, or an existing `results/<run>/`.
7. Every paper edit is logged in `docs/CHANGES.md` with the reviewer item it addresses.

## Quick commands

```
S=.claude/skills/fl-backdoor-lab/scripts
python $S/export_runs.py --force                        # results/ -> results/runs.csv
python $S/check_runs.py --pending --tier 1              # validate + queue
python $S/aggregate.py --compare-paper results/paper_reported.csv
python $S/stats_tests.py                                # split is re-drawn per seed: pooling is OK
python $S/selection_stats.py                            # Multi-Krum selection rate vs ASR
python $S/channel_stats.py --split-csv dataset/splits/split_rgb_seed42.csv
```

Slash commands `/lab-status`, `/lab-map`, `/lab-run`, `/lab-analyze`, `/lab-report` wrap these.

## References (read the one you need, not all)

- `references/experiment_protocol.md` — how to launch each run type against this repo's scripts and
  configs, the run matrix and its tiers, naming, and how the new Tier 1/3 runs are defined.
- `references/results_schema.md` — the repo's per-run output files, and the columns of runs.csv.
- `references/metrics_and_stats.md` — metric definitions, ASR resolution, std convention, Fisher and
  paired tests with their caveats, how to phrase results.
- `references/paper_revision_workflow.md` — tiers, reviewer mapping, where tables go, CHANGES.md
  format, how the ARS plugin fits in.
