# Paper revision workflow

The full plan with checkboxes is `docs/REVISION_PLAN.md`; the reviewer reports are
`docs/reviews.md`. This file is the process, not the content.

## Order of work

0. Done already: the code audit (`docs/CODE_FACTS.md`), the paper-vs-code diff
   (`docs/DISCREPANCIES.md`), and the Tier 0 export — all 21 groups in `results/paper_reported.csv`
   reproduce from `results/runs.csv`.
1. Decide on each D1–D8 item: re-run or disclose. D1 (clean FL seed 42 trained for 30 rounds instead
   of 50) is blocking and cheap; D2 (Table III compares across two different test splits) needs
   either three re-runs or a reworded claim.
2. Tier 1 runs via `/lab-run 1`, then Tier 2 via `/lab-run 2`, each followed by `/lab-analyze`.
3. Text edits via `paper-editor` (or the ARS plugin, see below), using `results/tables/` and
   `docs/CODE_FACTS.md` — the methods section must describe the code, not the current prose.
4. `/lab-report` → tables, interpretation paragraphs, `docs/CHANGES.md`.
6. Final pass: every table and figure cited in the text; every reference cited and listed;
   `\todo{}` count = 0; page limit respected.

## Where things go in the paper

| Paper part | Source |
|---|---|
| Tables V, VII (multi-seed) | `results/tables/summary.tex` (filtered to the relevant groups) |
| Per-seed table (new) | `results/tables/summary.tex`, second table |
| Significance statements | `results/tables/stats.md` |
| "Why blue" paragraph in IV | `results/tables/channel_stats.md` + Fig. 3 |
| Multi-Krum failure paragraph | `results/tables/selection_stats.md` |
| Poison-rate / trigger-size robustness | the three D6 ablation rows in `results/runs.csv` |
| Figs. 5–7 | `results/<run>/history.json` |

Never type numbers by hand into `paper/`; `\input` the generated `.tex` or copy from
`results/tables/` and record the source file in `docs/CHANGES.md`.

## `docs/CHANGES.md` format

One row per change: reviewer item (A-method, B-tables, C-stats-2 …), section touched, what
changed, evidence file (table/stat/log), status (todo / done). This file becomes the summary of
changes for the editors and the basis for any response letter. Cuts made for page limit are logged
too, with the reason.

## Using the ARS plugin alongside this skill (optional)

Academic Research Skills (`/plugin marketplace add Imbad0202/academic-research-skills`,
`/plugin install academic-research-skills`) covers the writing side. Sensible touchpoints:

- `revision-coach` mode on `docs/reviews.md` → compare its roadmap with `docs/REVISION_PLAN.md`.
- `citation-check` mode on the reference list (uncited [19], contradictory [15], DOI consistency).
- `re-review` mode on the revised manuscript with `docs/reviews.md` as the original reports → a
  simulated check that each reviewer point is addressed, before submission.

ARS does not run experiments; this skill does. Do not let ARS write numbers into the paper — point
it at `results/tables/`.

## Page-limit reclaim list

II.A repeats intro paragraph 2 almost verbatim; the browser-extension sentence [3] in the intro;
"two local epochs" appears in III.D and III.H; Table II can become one sentence.
