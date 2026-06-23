"""Type stubs for the C++ extension ``isalhg.core._core``.

The actual implementation lives in
``src/isalhg/core/_core.cpython-*.so`` built by scikit-build-core +
nanobind from the C++ sources under ``src/isalhg/core/_native/``. This
stub declares the public surface so mypy ``--strict`` passes on the
Python shims that consume it.
"""

from __future__ import annotations

from isalhg.core.sparse_hypergraph import SparseHypergraph

def ping() -> str: ...
def required_k(H: SparseHypergraph) -> int: ...
def greedy_h2s(
    H: SparseHypergraph,
    seed_node: int,
    k: int,
    wl_colors: list[int] | None = None,
) -> str: ...
def greedy_h2s_tokens(
    H: SparseHypergraph,
    seed_node: int,
    k: int,
    wl_colors: list[int] | None = None,
) -> list[tuple]: ...
def max_xi_nodes(H: SparseHypergraph, depth: int = 3) -> list[int]: ...
def wl_hash(H: SparseHypergraph, max_rounds: int = 64) -> list[int]: ...
def canonical_string(
    H: SparseHypergraph,
    k: int,
    structural_depth: int,
    algorithm_id: int,
) -> str: ...
