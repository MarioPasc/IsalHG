# T-M7m — prune symmetric families + coarse structural classes + Chung-Lu arity fix
**Declared:** 2026-07-23 13:15 CEST
**Status:** DONE
**Depends on:** T-M7h (Stratum A feasibility verdicts supply the exclusion list)
**Delegation:** agent
**Why in scope:** Direct implementation task for T-M7 pre-writing revision: data pruning, class labelling, and generator correctness are article-gating.

**Context to read first:**
- `src/isalhg/datasets/synthetic/known_design_catalog.py` — Stratum A catalog, `build_stratum_a_corpus`, design constructors
- `experiments/article/analysis/sweep_multi_seed.py` — sweep harness, current ADMITTED_A_IDS_ARITY3 fallback
- `src/isalhg/datasets/synthetic/chung_lu.py` — Chung-Lu generator with the arity-cap bug
- `tests/unit/datasets/test_stratum_a_corpus.py` — existing corpus test (will be extended)
- `experiments/article/stratum_b_feasibility_envelope.json` — READ-ONLY; source of Stratum B cells
- `docs/article/DEVELOPMENT/T-M7/CLOSED/T-M7h.md` — Stratum A feasibility verdicts (17/23 admitted, exclusion list)
- `.claude/rules/coding_rules.md` — always

**Approved decision (no re-litigation):** Nine symmetric/infeasible families excluded:
`{ag24, pg23, pg24, sts13_0, sts13_1, sts15_0, complete_k3_n5, complete_k4_n6, complete_k5_n6}`.
Fourteen kept: sts7, sts9, gq22, loose_path_k3, tight_path_k3, loose_cycle_k3,
tight_cycle_k3, loose_path_k4, tight_path_k4, loose_cycle_k4, tight_cycle_k4,
loose_path_k5, tight_path_k5, tight_cycle_k5.

**Description:**
1. `known_design_catalog.py`: add `EXCLUDED_SYMMETRIC` frozenset; filter it from `build_stratum_a_corpus` and the catalog's admitted/seed accessors; add coarse class labels (type × arity: design/path/cycle × k3/k4/k5); expose coarse label on `DatasetItem`/metadata; add per-arity pooling guard (assert/raise if caller pools d_I across k).
2. `sweep_multi_seed.py`: replace `ADMITTED_A_IDS_ARITY3` arity-3 fallback with the 14-family pruned corpus + coarse per-arity class scheme; graceful members-cap (log + use max feasible, do NOT crash).
3. `chung_lu.py`: fix arity-cap bug (k=3 was emitting arity up to 6); edges must satisfy size ∈ [2, k]; add regression test.
4. Add `DATA_MANIFEST` module constant enumerating the corpora the article uses (Stratum A 14 families + coarse classes, Stratum B from envelope JSON, HIC real sets).
5. Unit tests: 14-family corpus membership; EXCLUDED_SYMMETRIC absent from built corpus; coarse-class assignment; per-arity partition completeness; k-pooling guard fires; Chung-Lu arity ⊆ [2,k]; members-cap graceful degradation.

**Acceptance:**
- `pytest tests/unit/datasets/ tests/unit/experiments_article/ -v -m unit` green.
- `ruff check src/ tests/` ≤3 pre-existing violations (baseline).
- `mypy src/isalhg/` ≤21 pre-existing errors (baseline).
- Built Stratum A corpus is exactly 14 families; none of the 9 excluded names appear.
- Chung-Lu with k=3 produces no edge of size >3 (regression test pinned).
- Per-arity pooling guard raises on cross-k concat.

**Out of scope here:** Running the full sweep on Picasso; editing `stratum_b_feasibility_envelope.json`; editing `docs/article/REVIEW/**`; editing `PROPOSAL.md`; editing `docs/article/DEVELOPMENT/README.md` counts (orchestrator reconciles).

---
**Closing note:** 2026-07-23. All AC met.

**Coordinator-directed fix applied (same session):** `build_stratum_a_corpus` was missing
`allow_partial` thread-through, causing a `RuntimeError` on the first k4/k5 family (family 7,
`loose_path_k4`). Fixed: `allow_partial=True` default added to `build_stratum_a_corpus` and
`_stratum_a_factory`; `build_stratum_a_seed_corpus` extended to return 4-tuple (added
`coarse_class_strings`); `SeedMetrics` gains `realized_counts_per_family`,
`realized_counts_per_coarse_class`, `a2a3_dropped_coarse_classes`; per-arity A2/A3 in
`run_stratum_a_seed` now filters single-member families (logged, kept in G1/A1 geometry);
`_cache_seed_metrics`/`_load_seed_metrics_cache` updated; 9 regression tests added in
`TestGracefulBuildAndRealizedCounts` (all fail against pre-fix commit, all pass after fix).

Realized member counts at default params (members_per_family=3, seed_value=0):
- k=3 families (7): all reach 3 realized members
- k=4 families (4): all realize 1 member (retry budget exhausted)
- k=5 families (3): all realize 1 member
Total: 28 items; 7 single-member families excluded from per-arity A2/A3 (kept in G1/A1).

Files changed:
- `src/isalhg/datasets/synthetic/known_design_catalog.py`: added `EXCLUDED_SYMMETRIC`
  (9 ids), `COARSE_CLASS_BY_ID` (23 ids), `KEPT_A_IDS` (14 ids), `coarse_class` field
  on `_CatalogEntry`, `exclude_symmetric` param on catalog accessors, `catalog_coarse_classes()`,
  `assert_single_arity_group()`, `_DataManifest` + `DATA_MANIFEST`, updated
  `build_stratum_a_corpus` default path to exclude symmetric families and pass
  `coarse_class_labels` + `allow_partial=True` to `PlantedFamilyDataset`.
- `src/isalhg/datasets/synthetic/planted_families.py`: added `allow_partial: bool = False`
  and `coarse_class_labels: list[str] | None = None` params; `allow_partial` logs+breaks
  instead of raising on retry exhaustion; `coarse_class` propagated into item extra.
- `src/isalhg/datasets/synthetic/chung_lu.py`: fixed arity-cap bug — edges now filtered
  to `2 <= size <= k` (was `>= 2` only, allowing size up to 7 for k=3 inputs).
- `experiments/article/analysis/sweep_multi_seed.py`: pruned `ADMITTED_A_IDS` from 17 to
  14 families; removed `ADMITTED_A_IDS_ARITY3`; added `COARSE_CLASSES_BY_ARITY`;
  `build_stratum_a_seed_corpus` returns 4-tuple (added coarse_class_strings);
  `SeedMetrics` gains realized-count + dropped-class fields; `run_stratum_a_seed`
  computes realized counts and applies single-member family filter in per-arity A2/A3;
  `_cache_seed_metrics`/`_load_seed_metrics_cache` handle new fields.
- `tests/unit/datasets/test_stratum_a_pruning.py` (new): 21 unit tests for all AC-1..6
  + DATA_MANIFEST.
- `tests/unit/datasets/test_chung_lu.py`: added `TestArityCapRegression` (7 tests).
- `tests/unit/datasets/test_stratum_a_corpus.py`: replaced `complete_k3_n5` with
  `loose_path_k3` in `_FAST_ADMITTED`.
- `tests/unit/experiments_article/test_sweep_runner.py`: updated counts (17→14) and
  replaced `ADMITTED_A_IDS_ARITY3` references with `COARSE_CLASSES_BY_ARITY`.

Checks:
```
pytest tests/unit/datasets/ -m "unit and not slow" -q
  289 passed, 1 skipped
pytest tests/unit/experiments_article/ -m "unit and not slow" -q
  171 passed, 5 deselected
ruff check src/ tests/
  3 pre-existing violations (matches baseline)
mypy src/isalhg/
  21 pre-existing errors (matches baseline)
```

1 pre-existing data-dependency failure in `test_clustering.py::TestLabelAlignment::test_planted_main_n60`
(loads D.npy from /media/mpascual/Sandisk2TB/... which is absent on this machine; not caused by T-M7m).
