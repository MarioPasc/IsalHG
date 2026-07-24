# T-M7s — Harvest and accept the S=27 sweep (array 1640910)
**Declared:** 2026-07-24 16:05 CEST
**Status:** OPEN
**Depends on:** T-M7d (harness + submission — CLOSED), SLURM array **1640910**
reaching terminal state on Picasso.
**Origin:** 2026-07-24 S7 re-run session, filed by the orchestrator at T-M7d's
merge. T-M7d delivered the corrected harness, the S=8 validation
(array 1640880 — 56/56 `D.npy`, 72 BCa CI entries across all 7 representations,
60 Holm-corrected Wilcoxon entries), and the S=27 submission. Its acceptance,
however, is stated over *emitted tables*: "every emitted A1/A2/A3/G1/bits table
cell carries a 95% CI ... the geometry-vs-axis curves exist for ≥3 values on
each of the n, density, and arity axes with error bands". Those artifacts do
not exist until the full array lands and is harvested, so the acceptance is
verified here rather than at T-M7d.
**Context to read first:**
- `docs/article/DEVELOPMENT/T-M7/CLOSED/T-M7d.md` — the harness, the four
  corrections, the per-arity fix, and the S=8 validation record
- `experiments/article/analysis/sweep_multi_seed.py` — the emitting code
- `docs/article/REVIEW/STATS_PASS_PLAN.md` — what each statistic must be
- results root on Picasso:
  `/mnt/home/users/tic_163_uma/mpascual/fscratch/results/T-M7d/`
  (`seed_metrics/{a,b}/`, `stats/`, `d_matrix/`, `figures/`,
  `sweep_summary.json`)
**Description:** Wait for array 1640910 (77 tasks = 11 cells × 7
representations, S = 27) to reach a terminal state; harvest the results to the
local results drive; verify the acceptance clause by clause; and record what
did *not* complete. Specifically: (1) reconcile task exit states — any
TIMEOUT/OOM/FAILED task is reported as a measured outcome with its cell and
representation, never silently dropped; (2) confirm every emitted A1/A2/A3/G1/
bits cell carries a 95 % BCa CI and every competitor-vs-IsalHG comparison a
Holm-corrected p plus effect size; (3) confirm the per-arity breakdown is
populated for arities 3, 4 and 5 on Stratum A (the T-M7d fix — spot-checked at
`seed_metrics/a/stratum_a/seed0/isalhg_levenshtein.json` during the run) and
that no phantom arity group appears; (4) confirm the geometry-vs-axis curves
have ≥3 values with error bands on each of n, density, arity, and state which
axis coverage comes from Stratum B's 10 admitted cells; (5) emit the harvest
summary the prose pass (T-M8f) will cite.
**Acceptance:** array 1640910 terminal-state census recorded (completed /
timeout / OOM / failed, per cell × representation); harvested artifacts present
locally; the four verification clauses above checked and their outcomes written
into the closing note with the actual numbers; any cell that did not complete
is named, with its measured reason, and is excluded whole-cell (never
per-pair); a one-page harvest summary exists for T-M8f to cite; suite matches
the session baselines (1432 passed / 9 skipped / 25 deselected, ruff 3,
mypy 21).
**Out of scope here:** re-running or re-tuning the sweep (if a cell failed for a
resource reason, record it — resubmission is a separate decision); prose
folding (T-M8f); the capability matrix (T-M8b); the real anchor (T-M7g).
