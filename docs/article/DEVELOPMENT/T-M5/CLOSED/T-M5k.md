# T-M5k — Regenerate T-M5j clean-dataset tables clobbered by the R2 HPD patch
**Declared:** 2026-07-20 16:05 CEST
**Status:** DONE
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

---

## Closing note — 2026-07-20

**Root cause.** Step 6 of `run_hic_dataset()` called `_write_csv(path, rows)` where
`rows` only contained representations processed in the current run. The R2 HPD patch
supplied `distance_names=["hpd_jsd"]`, so `rows` was HPD-only and the write truncated
the 5-rep tables to 1 row.

**Fix** (`experiments/article/analysis/hic_od6.py`):
- `_write_csv`: union fieldnames across all rows so mixed-schema rows coexist.
- `_read_existing_rows_json(path)`: reads `{"rows": [...]}` from the JSON artifact;
  returns `[]` on missing/error. Uses JSON not CSV to preserve numeric types.
- `_merge_repr_rows(existing, new_rows, new_repr_labels, repr_key)`: keeps rows whose
  `repr_key` is NOT in `new_repr_labels`, then appends `new_rows`.
- Step 6 computes `_processed_reprs` (display labels for current run), then
  read existing JSON -> merge -> write both CSV and JSON.

**Regression test** (`tests/unit/analysis/test_hic_od6.py` — `TestMergeTableRows`, 4 tests):
- HPD-only re-run keeps all 5 reps, no duplicates.
- HPD row is replaced, not duplicated.
- Missing-file returns [].
- Full re-run replaces stale rows correctly.
Teeth: functions did not exist pre-fix so tests failed with ImportError.

**Backup**: 12 damaged files copied to
`/media/.../results/T-M5j/tables/.pre-t-m5k-backup/` before overwrite.

**Regeneration**: from cached D.npy (no distances recomputed);
`survivor_indices.json` cache used for w*_c censoring step.

**Acceptance criteria**:
1. All 6 tables contain 5 rows each; HPD rows carry `hpd_n_errors`/`hpd_note`. ✓
2. Wri-Genre WL-L1 hub_skew=7.4116 (≈7.412); Wri-Genre-M 4.5493 (≈4.549);
   mean AUC@k=9 IsalHG 0.6731 (≈0.673), NetLSD 0.6539 (≈0.654), WL-L1 0.6236 (≈0.624). ✓
3. `TestMergeTableRows` regression suite passes. ✓

**Checks**:
- `pytest tests/unit/analysis/test_hic_od6.py`: 23 passed (19 existing + 4 new)
- Full unit+integration: 983 passed, 8 skipped
- `ruff check experiments/article/ tests/`: 2 errors (pre-existing; none in my files)
- `mypy src/isalhg/`: 21 errors — baseline matched

**Files changed**: `experiments/article/analysis/hic_od6.py`,
`tests/unit/analysis/test_hic_od6.py`.
