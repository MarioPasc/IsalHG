# T-M5i — fix runner._build_dataset kwarg mismatch with dataset registry
**Declared:** 2026-07-19 17:40 CEST
**Status:** OPEN
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
