# Installing this kit into the repository

The kit is additive: it does not modify any existing file except by moving `drafts/` to `paper/`.

## 1. Copy the files in

From the repo root (`.../malware/`), unzip the kit so that these land alongside `src/`:

```
CLAUDE.md          README.md          INSTALL.md       .gitignore
.claude/           docs/              experiments/     results/paper_reported.csv
```

`README.md` replaces nothing (the repo had none). If you already have a `.gitignore` or
`README.md`, merge by hand rather than overwriting.

## 2. Move the paper source out of drafts/

```bash
git mv drafts paper        # or: mv drafts paper
```

`paper/` then holds `ieee_malware_fl_backdoor.{tex,pdf,aux,log,synctex.gz}` plus the figures
(`dataset.png`, `method.png`, `federated.jpg`, `malware.png`, `asr_per_round.png`,
`clean_per_round.png`, `all_settings_f1_asr_per_round.pdf`) and the two `.docx` notes.
Nothing in the kit depends on the old path; `CLAUDE.md` and `README.md` already say `paper/`.

## 3. Build the canonical result table

```bash
python .claude/skills/fl-backdoor-lab/scripts/export_runs.py --dry-run   # preview 40 runs
python .claude/skills/fl-backdoor-lab/scripts/export_runs.py             # write results/runs.csv
python .claude/skills/fl-backdoor-lab/scripts/check_runs.py              # expect: 40 rows OK, tier 0 complete
python .claude/skills/fl-backdoor-lab/scripts/aggregate.py --compare-paper results/paper_reported.csv
```

The last command should report `[match]` for all 21 groups from Tables III–VII. If it does not,
something changed in `results/` and that is worth understanding before writing anything.

## 4. Generate the analysis the revision needs

```bash
python .claude/skills/fl-backdoor-lab/scripts/stats_tests.py
python .claude/skills/fl-backdoor-lab/scripts/selection_stats.py
python .claude/skills/fl-backdoor-lab/scripts/channel_stats.py --split-csv dataset/splits/split_rgb_seed42.csv
```

## 5. Open Claude Code in the repo root

```
/lab-status
```

Then read `docs/DISCREPANCIES.md` and decide on D1 and D2 before launching new runs.

## Requirements

The kit's scripts need `pandas`, `numpy`, `scipy`, `Pillow` — all already required by the
experiments. Nothing else is installed.
