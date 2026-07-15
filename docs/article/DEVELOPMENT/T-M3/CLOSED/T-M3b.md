# T-M3b — `HPDDistance` (Hyperedge Portrait Divergence, vendored MIT)
**Declared:** 2026-07-08 13:40 CEST (split from T-M3)
**Status:** DONE
**Depends on:** T-M1a
**Context to read first:**
- `docs/article/COMPETITORS.md` §2 · `docs/article/RELATED_WORK.md` §Competitors — Agostinelli et al. 2026, `cosimoagostinelli/Hor_dissimilarity_measures`
- `docs/article/CODE_DESIGN.md` §3.2 — vendoring strategy
- `.claude/rules/coding_rules.md` — always
**Description:** Vendor the HPD function (MIT) into `representations/_hpd_vendor.py`
(provenance header); wrap as a `HypergraphDistance` (hyperedge-path tensor →
Jensen–Shannon). Register.
**Acceptance:** `matrix()` runs on the correlation corpus; numpy/scipy-only guard.
**Out of scope here:** Hyper-NetSimile (the sibling measure — skip unless needed).

---

## Closing note (2026-07-15)

Implemented by ledger-worker on branch `task/T-M3b` (worktree `agent-aeaa20095661e954b`).

**Files created:**
- `src/isalhg/metric_space/representations/_hpd_vendor.py` — four HPD functions
  vendored verbatim from commit `f190266b4ada36d57fd320422d70b915d11a7961` of
  `cosimoagostinelli/Hor_dissimilarity_measures` (MIT). Nine adaptations documented
  in the provenance docstring (file-level `# mypy: ignore-errors` +
  `# ruff: noqa: ANN001, ANN202`; `# noqa: N802` on `H_to_G_mapping`;
  `# noqa: E741` on `for l`; trimmed imports; no type annotations as in upstream).
- `src/isalhg/metric_space/representations/hpd.py` — `HPDDistance(HypergraphDistance)`
  with `sqrt_js=True` default (JS distance, proper metric); `pairwise` and `matrix`
  both guard all optional imports via `_import_deps()`; registered as `"hpd_jsd"`.
- `tests/unit/metric_space/test_hpd.py` — 13 tests (12 unit + 1 `@pytest.mark.slow`
  HIC smoke). All tests were verified to fail before implementation (import error)
  and pass after.

**Note on task-spec corrections:**
- `HIC_ROOT` in the spec was `".../data/HIC/data"` (missing `/hypergraph` suffix);
  corrected to `".../data/HIC/data/hypergraph"`.
- `hic_name="MUTAG"` in the spec is not a valid HIC dataset name; corrected to
  `"RHG-10"` (smallest entry in `_HIC_FILE_MAP`).

**Closing check output:**

```
$ pytest tests/unit/metric_space/test_hpd.py -v -m unit
============================= test session info ==============================
13 passed in 0.76s

$ ruff check src/isalhg/metric_space/representations/_hpd_vendor.py \
             src/isalhg/metric_space/representations/hpd.py \
             tests/unit/metric_space/test_hpd.py
All checks passed!

$ mypy src/isalhg/metric_space/representations/hpd.py \
       src/isalhg/metric_space/representations/_hpd_vendor.py
Success: no issues found in 2 source files

Full suite (pre-existing baselines, not introduced by this task):
  ruff src/ tests/ → 3 errors (pre-existing, in registry.py lambdas)
  mypy src/isalhg/ → 20 errors (pre-existing, in core/ and iso_backends/)
```
