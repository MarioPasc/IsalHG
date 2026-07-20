# T-M5i — fix runner._build_dataset kwarg mismatch with dataset registry
**Declared:** 2026-07-19 17:40 CEST
**Status:** DONE
**Depends on:** —
**Why out of scope:** Discovered in T-M5b; the fix is a one-liner in runner.py,
out of scope for the MDS analysis task.
**Context to read first:**
- `experiments/article/runner.py:85–87` — the buggy `_build_dataset` helper
- `src/isalhg/datasets/registry.py::get_dataset` — correct signature
  `get_dataset(name: DatasetName, params: dict[str, Any]) -> HypergraphDataset`
- `experiments/article/configs/mds_planted.yaml` — workaround documentation
  (mds.py bypasses the runner for planted_families; same cache layout)
- `.claude/rules/coding_rules.md` — always
**Description:** `runner._build_dataset` at line 87 calls
`get_dataset(name, **params)` (keyword-unpacking) but the registry signature
is `get_dataset(name, params: dict[str, Any])` (positional dict). The call
raises `TypeError` for any dataset with non-empty params (including
`planted_families`). T-M5b worked around it by computing D matrices directly
in `mds.py` with the identical cache layout. T-M5c/d/e load the cached
`D.npy` files and do not re-invoke the runner for dataset construction, so
they are not immediately blocked — but the bug will surface if any future
experiment runs a dataset via the standard runner path.
**Acceptance:** `runner._build_dataset` changed to `get_dataset(name, params)`
(positional); `experiments/article/configs/mds_planted.yaml` IMPORTANT note
updated to reflect the fix; `pytest tests/unit/ -q` still green; ruff/mypy
baselines unchanged.
**Out of scope here:** changes to `src/isalhg/datasets/registry.py`; changes
to the D-matrix cache layout; any analysis code.

---

**Closing note (2026-07-20, updated after orchestrator R1 review):**

**Premise check.** The task's verification note asked: "the E1' Picasso run
(perturbation_ladder with non-empty dataset_params) ran through the runner
successfully — check the premise." Verified: `perturbation_ladder` has a
DEDICATED branch at runner.py lines 73-79 (`if name == "perturbation_ladder":`)
that constructs `PerturbationLadderHypergraphs(**ladder_params)` directly and
returns before reaching the fallback at line 84-87. The E1' success is
therefore orthogonal to the bug. The buggy path (lines 84-87) only affects
datasets not covered by the three named branches: `planted_families`,
`exhaustive_small`, `symmetric_designs`, `sts_catalog`, `arb_benson`,
`hic_atlas`, and any future registry dataset.

**Two-defect fix (R1 — orchestrator review found second defect).**

Defect 1 (initial fix): `get_dataset(name, **params)` unpacked the dict as
kwargs; the registry expects a positional dict `get_dataset(name, params)`.
Fixed: `return get_dataset(name, **params)` → `return get_dataset(name, params)`.

Defect 2 (R1): `params` was built as `{**cell.dataset_params, "seed": cell.seed}`
before the dispatch — the injected `"seed"` kwarg reaches the factory, which
calls `PlantedFamilyDataset(**params)`. `PlantedFamilyDataset.__init__()` uses
`seed_value`, not `seed` → `TypeError: got an unexpected keyword argument 'seed'`.
The initial fix's mock test (T12) hid this by never invoking a real factory.
Fixed (R1): pass `cell.dataset_params` un-mutated to the registry; bind the
experiment seed via `HypergraphDataset.seed()` (the documented ABC seed-binding
protocol): `return get_dataset(name, cell.dataset_params).seed(cell.seed)`.

The three named branches (`correlation_corpus`, `perturbation_ladder`,
`erdos_renyi`) are untouched — each injects `seed` as a constructor kwarg that
their classes accept, and their pinned output (including the Picasso E1' data)
is byte-identical.

**Process error (R1).** Initial commit edited `docs/article/DEVELOPMENT/README.md`
(orchestrator-owned file). Reverted to main's version in R1 commit.

**YAML note updated.** `mds_planted.yaml` note updated to accurately describe
the R1 fix (positional dict + `.seed()` protocol).

**Tests in `tests/unit/experiments_article/test_runner.py`:**
- T11 `test_build_dataset_old_kwarg_style_raises_type_error`: calls
  `get_dataset("planted_families", n_families=1, seed=42)` and asserts
  `TypeError` — pins the original kwarg-unpack bug.
- T12 `test_build_dataset_registry_fallback_passes_unmutated_dataset_params`:
  patches registry, verifies `dataset_params` passed un-mutated (no injected
  `"seed"` in captured params) — pins calling convention + content.
- T13 `test_build_dataset_seed_injection_raises_type_error`: calls
  `get_dataset("planted_families", {..., "seed": 42})` and asserts `TypeError`
  — pins the second defect (seed injection into registry factory).
- T14 `test_build_dataset_planted_families_real_path`: no mocks; calls
  `_build_dataset` with a real `planted_families` CellSpec and asserts 4 items
  are returned, all connected — the end-to-end acceptance test.

**Closing check (R1):**
```
pytest tests/unit/experiments_article/test_runner.py -v
16 passed
pytest tests/unit/ -q
[pending — run in background; prior baseline: 914 passed, 5 skipped]
ruff: 14 errors (baseline, unchanged)
mypy: 21 errors in 7 files (baseline, unchanged)
```
