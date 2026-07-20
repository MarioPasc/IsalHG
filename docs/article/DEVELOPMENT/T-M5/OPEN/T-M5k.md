# T-M5k — Regenerate T-M5j clean-dataset tables clobbered by the R2 HPD patch
**Declared:** 2026-07-20 16:05 CEST
**Status:** OPEN
**Depends on:** T-M5j (CLOSED — its D.npy caches and R1 numbers are the inputs)
**Delegation:** agent
**Why out of scope:** discovered during the S5 preflight audit (orchestrator,
verifying the applications.md measured prose against artifacts) while executing
T-M5a part 2 — it is T-M5j artifact hygiene, not discussion evidence.
**Context to read first:**
- `experiments/article/analysis/hic_od6.py` — the T-M5j pipeline; find the R2
  HPD-patch path that rewrites per-dataset tables
- `docs/article/DEVELOPMENT/T-M5/CLOSED/T-M5j.md` — the R1 full-representation
  numbers (geometry/clustering/kNN tables for the 6 datasets) that the
  regenerated artifacts must reproduce
- `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/T-M5j/` — `d_matrix/`
  caches (all reps, all 6 datasets, intact) and `tables/` (the damaged outputs)
- `.claude/rules/coding_rules.md` — always
**Description:** The T-M5j round-2 fix (surfacing HPD-JSD on its
per-instance-computable subset) rewrote `tables/{geometry,clustering,knn}_table_
IMDB-Wri-Genre{,-M}.{csv,json}` with **HPD-only rows**, dropping the
IsalHG/WL-L1/NetLSD/NautyEdit rows for exactly the two clean datasets the
article's HIC claims rest on. The full-representation numbers survive only as
text in the closing note; the `D.npy` caches are intact, so the tables are
regenerable without recomputing any distances. Fix the patch path so an HPD
re-run merges rather than truncates, then regenerate the six damaged files.
**Acceptance:** (1) `tables/geometry_table_IMDB-Wri-Genre{,-M}.{csv,json}` and
the clustering/kNN counterparts contain one row (per k, where applicable) for
each of the five representations, HPD rows still flagged with
`hpd_n_errors`/`hpd_note`; (2) regenerated values reproduce the T-M5j closing
note (e.g. Wri-Genre WL-L1 hub_skew 7.412, Wri-Genre-M 4.549; mean AUC@k=9
IsalHG 0.673 / NetLSD 0.654 / WL-L1 0.624); (3) a regression test (or a
pinned re-run check in the closing note) shows the HPD-patch path no longer
drops non-HPD rows.
**Out of scope here:** any change to distances, censoring policy, or the
T-M5j conclusions; `experiments/article/runner.py` (T-M5i);
`analysis/correlation.py` / `analysis/information_content.py` (T-M5a).
