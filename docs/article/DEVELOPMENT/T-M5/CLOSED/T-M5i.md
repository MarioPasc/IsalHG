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

**Closing note (2026-07-20):**

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

**Fix.** One character changed on line 87:
- Before: `return get_dataset(name, **params)`
- After:  `return get_dataset(name, params)`

**YAML note updated.** `mds_planted.yaml` IMPORTANT block replaced with a
post-fix note (workaround language removed).

**Tests added to `tests/unit/experiments_article/test_runner.py`:**
- T11 `test_build_dataset_old_kwarg_style_raises_type_error`: calls
  `get_dataset("planted_families", n_families=1, seed=42)` (the pre-fix
  unpacked-kwarg form) and asserts `TypeError` — demonstrates the bug existed.
- T12 `test_build_dataset_registry_fallback_passes_positional_dict`: patches
  `isalhg.datasets.registry.get_dataset` with a capturing mock, creates a
  `planted_families` CellSpec, calls `_build_dataset`, and asserts the mock
  received `(name, params_dict)` form with the correct values — confirms the fix.

**Closing check:**
```
pytest tests/unit/ -q
914 passed, 5 skipped in 133.15s
ruff: 14 errors (baseline, unchanged)
mypy: 21 errors in 7 files (baseline, unchanged)
```
