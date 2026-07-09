# T-M0b — Python `_neighbour_degree_key` rebuilds `primal_graph()` per node
**Declared:** 2026-07-08 13:13 CEST (handoff from T-M0)
**Status:** OPEN
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
