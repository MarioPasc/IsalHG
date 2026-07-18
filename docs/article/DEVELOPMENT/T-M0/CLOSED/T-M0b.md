# T-M0b — Python `_neighbour_degree_key` rebuilds `primal_graph()` per node
**Declared:** 2026-07-08 13:13 CEST (handoff from T-M0)
**Status:** DONE
**Depends on:** —
**Context to read first:**
- `src/isalhg/core/structural_tuples.py::_neighbour_degree_key` + `::_python_max_neighbor_degree_nodes`
- `src/isalhg/core/sparse_hypergraph.py::primal_graph` (line 254) — uncached; rebuilds the adjacency dict every call
- `.claude/rules/coding_rules.md` — always
**Description:** `_python_max_neighbor_degree_nodes` builds `adj = H.primal_graph()`
once, but `_neighbour_degree_key` calls `H.primal_graph()` again per survivor
node, so the adjacency is rebuilt `(1 + m)` times — `O((1+m)·Σ|e|²)`. Reference
(Python) path only; the C++ default seeder uses the prebuilt `primal_adj` and is
unaffected. Fix: thread `adj` into `_neighbour_degree_key` (2-line change);
optionally memoise `primal_graph` on `SparseHypergraph` (broader — also helps the
`xi` BFS).
**Acceptance:** `_neighbour_degree_key` consumes a passed-in `adj`; no behaviour
change (`test_backend_equivalence.py` + `test_canonical_invariance.py` green);
`primal_graph` built once per seeder call.
**Out of scope here:** the C++ path (already uses prebuilt adjacency); a general
`primal_graph` cache is a separate decision.

---

**Closing note (2026-07-18):**

Change: `_neighbour_degree_key(H, v)` → `_neighbour_degree_key(adj, v)` — removed
the internal `adj = H.primal_graph()` call and threaded the pre-built `adj` from
`_python_max_neighbor_degree_nodes`. The redundant rebuild was `(1 + |survivors|)`
total builds per seeder call; after the fix it is exactly 1. On the vertex-transitive
Fano plane (all 7 nodes survive step 2) this reduces 8 builds to 1.

Files changed:
- `src/isalhg/core/structural_tuples.py`: signature + call site (2 effective lines)
- `tests/unit/core/test_structural_tuples.py`: added `TestNeighbourDegreeKeyCallCount`
  with two tests that patch `SparseHypergraph.primal_graph` at the class level
  (instance-level patching blocked by `__slots__`) and assert `call_count == 1`.
  Restoring `adj = H.primal_graph()` inside `_neighbour_degree_key` raises both tests
  from 1 to 8 (Fano) / >1 (path), demonstrating the guard is live.

Acceptance check:
  pytest tests/unit/core/test_structural_tuples.py tests/property/test_backend_equivalence.py
        tests/property/test_canonical_invariance.py --hypothesis-seed=0 -q
  → 57 passed
  pytest tests/unit tests/property tests/integration -m "not slow" --hypothesis-seed=0 -q
  → 879 passed, 18 skipped, 13 deselected  (baseline 877 + 2 new tests)
  ruff: Found 3 errors  (baseline matched)
  mypy: Found 21 errors in 7 files  (baseline matched)
