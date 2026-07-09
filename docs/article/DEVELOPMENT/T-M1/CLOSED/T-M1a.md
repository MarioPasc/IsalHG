# T-M1a — `metric_space/` foundation + shared promotions
**Declared:** 2026-07-08 12:20 CEST · **split from T-M1** 2026-07-08 13:40 CEST
**Status:** DONE
**Depends on:** — (parallel-safe with the now-DONE T-M0; use an isolated worktree)
**Context to read first:**
- `docs/article/CODE_DESIGN.md` §3 ("HypergraphDistance"), §4 (shared promotions), §5 (errors/types)
- `docs/article/empirical/correlation.md` — how `matrix()` feeds the study
- `src/isalhg/iso_backends/levi_reduction.py` — the module to move to `core/` (+ its 3 importers: `pynauty_levi`, `bliss_levi`, `traces_levi`)
- `src/isalhg/core/sparse_hypergraph.py::permute` — pattern for the new edit ops
- `src/isalhg/iso_backends/base.py` and `registry.py` — ABC + registry pattern to mirror
- `.claude/rules/coding_rules.md` — always
**Description:** The foundation every metric-space task builds on. Create
`metric_space/{base,registry}` with the `HypergraphDistance` ABC
(`pairwise`/`matrix`); move `levi_reduction` → `core/levi_reduction.py` (update
the three iso backends); add the six structural edit ops (vertex/hyperedge/
incidence ins-del + `random_edit` + `edit_path`) to `core/sparse_hypergraph.py`;
extend `errors.py` (`MetricSpaceError` hierarchy) and `types.py` (`DistanceName`,
numpy-free). **No concrete distance yet.**
**Acceptance:** package imports; ABC+registry unit-tested via a trivial stub
distance; the six edit ops each unit-tested (incidence changes as expected);
iso-backend tests still green after the `levi_reduction` move; full suite + ruff
+ mypy green.
**Out of scope here:** any concrete distance (T-M1b), HGED (T-M2), competitors
(T-M3a–d), the `isomorphisms/` reparent (T-M6).
**Closing (2026-07-08 14:04 CEST):**
- *`metric_space/` skeleton:* `metric_space/{__init__,base,registry}.py`. `base.py`
  holds the `HypergraphDistance` ABC (abstract `name`/`pairwise`; default
  `matrix()` loops the upper triangle → symmetric zero-diagonal `np.ndarray`;
  optional `fingerprint()` → `None`). `registry.py` mirrors
  `iso_backends/registry.py` verbatim (`register_/get_/available_distance(s)` +
  `_reset_for_testing`, `_LAZY_MODULES` empty until T-M1b/T-M3 populate it).
  **No concrete distance** — T-M1a is the foundation only.
- *`levi_reduction` → `core` (the one required move, `CODE_DESIGN.md` §4.3):*
  `iso_backends/levi_reduction.py` **deleted**, recreated as
  `core/levi_reduction.py` (still stdlib-only; forbidden doc-path comment removed
  per coding_rules §7.2). The three importers (`pynauty_levi`, `bliss_levi`,
  `traces_levi`) repointed to `isalhg.core.levi_reduction`; test moved
  `tests/unit/iso_backends/test_levi_reduction.py` →
  `tests/unit/core/test_levi_reduction.py`. `metric_space` now depends only on
  `core`, never on `isomorphisms` — the separation the article's §8 requires.
- *Six edit ops (+`random_edit`/`edit_path`) in `core/sparse_hypergraph.py`:*
  pure free functions beside `permute` (never mutate their argument). They are
  the Qin et al. (2023) unit-cost HGED generating set (`correlation.md` §HGED).
- *Errors/types:* `errors.py` gained `MetricSpaceError` → {`DistanceUnavailable`,
  `DistanceComputation`, `HGEDComputation`, `RepresentationDependencyMissing`,
  `SubprocessRepresentation`}`Error` (§5's four + `DistanceUnavailableError` for
  registry parity with `BackendUnavailableError`) and a core `HypergraphEditError`
  for edit preconditions. `types.py` gained `DistanceName` (str, numpy-free).
- *Decisions taken (flagged, spec-grounded, reversible):*
  (D1) **`delete_vertex` deletes an isolated vertex only** — Qin's taxonomy lists
  `incidence remove` separately, so vertex-deletion is the atomic unit op (a
  non-isolated delete is a compound edit); this keeps every op unit-cost so
  `edit_path`'s budget `t` is a valid HGED upper bound. **T-M2's `ExactHGED` must
  adopt the same convention.** (D2) **duplicate-merge guard**: `add_incidence` /
  `insert_hyperedge` / `remove_incidence` raise `HypergraphEditError` rather than
  let `add_hyperedge`'s silent dedup drop an edge. (D3) **numpy guarded** inside
  `matrix()` (raises `RepresentationDependencyMissingError`) + `NDArray`
  annotation under `TYPE_CHECKING`, so `import isalhg.metric_space` works without
  numpy — numpy is an extra (`bench`/`eval`), not a base dep.
- *Caveat noted in the edit-ops docstring:* the ops preserve neither connectivity
  nor `arity ≤ k`; corpus generators that need those (T-M4 planted families)
  filter downstream.
- *Closing checks* (`python -m pytest tests/unit tests/property tests/integration
  -m "not slow" --hypothesis-seed=0`): **449 passed, 8 skipped, 0 failed**
  (+41 vs T-M0's 408 = 7 base + 4 registry + 30 edit-ops new; the 8 `levi` tests
  relocated, not net-new). ruff **3 violations == baseline** (all pre-existing:
  `isalhg_backend.py:36`, `viz/instruction_view.py:135`,
  `test_registry.py:48`; none in changed files). mypy **21 errors == baseline**
  (all pre-existing `resolve()`-dispatch; none from new code). No C++ change → no
  rebuild.
- *Follow-ups for downstream tasks (no handoff — they are the next tasks' scope):*
  T-M1b registers `IsalHGLevenshtein`/`HypergraphWLDistance` + populates
  `_LAZY_MODULES`; T-M2's `ExactHGED` must honour D1 (isolated-only vertex delete).
