"""Structural tuples ``xi`` (per-node) and ``eta`` (per-edge).

``xi_h(v)`` = number of primal-graph neighbours of ``v`` at distance exactly ``h``.
``eta_h(e)`` = sum over ``v in e`` of ``xi_h(v)``.

Used both for seed selection (argmax-lex ``xi`` over nodes, invariant 4) and
for tie-breaking during greedy H2S (lex ``eta`` over candidate edges).
Default depth ``3`` is inherited from IsalGraph (invariant 8); deviation
requires re-validating Theorem 2 (canonical completeness conjecture).

Both implementations live in this module: the pure-Python reference under
``_python_max_xi_nodes`` and the C++-backed wrapper under
``_cpp_max_xi_nodes``. :func:`max_xi_nodes` dispatches between them via
the ``backend=`` kwarg (default ``"cpp"``).
"""

from __future__ import annotations

from isalhg.core._core import max_xi_nodes as _core_max_xi_nodes
from isalhg.core.backends import Backend, resolve
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.types import EdgeId, NodeId

DEFAULT_DEPTH: int = 3


def _bfs_counts(H: SparseHypergraph, v: NodeId, depth: int) -> list[set[NodeId]]:
    """Return ``[shell_1, ..., shell_depth]`` where ``shell_h`` is the set of
    vertices at primal-graph distance exactly ``h`` from ``v``.
    """
    adj = H.primal_graph()
    seen: set[NodeId] = {v}
    frontier: set[NodeId] = {v}
    shells: list[set[NodeId]] = []
    for _ in range(depth):
        nxt: set[NodeId] = set()
        for u in frontier:
            nxt.update(adj[u] - seen)
        seen.update(nxt)
        shells.append(nxt)
        frontier = nxt
    return shells


def xi(H: SparseHypergraph, v: NodeId, depth: int = DEFAULT_DEPTH) -> tuple[int, ...]:
    """Return ``(|shell_1(v)|, ..., |shell_depth(v)|)``."""
    if depth < 1:
        return ()
    shells = _bfs_counts(H, v, depth)
    return tuple(len(s) for s in shells)


def xi_labelled(
    H: SparseHypergraph,
    v: NodeId,
    depth: int = DEFAULT_DEPTH,
) -> tuple[tuple[int, ...], ...]:
    """Label-aware xi: ``[(count_per_label at h=1), (... at h=2), ...]``.

    For the trivial vocabulary this is equivalent to ``xi`` lifted into a
    1-element inner tuple per shell.
    """
    if depth < 1:
        return ()
    shells = _bfs_counts(H, v, depth)
    sigma_v = H.n_vertex_labels
    out: list[tuple[int, ...]] = []
    for shell in shells:
        counts = [0] * sigma_v
        for u in shell:
            counts[H.vertex_label(u)] += 1
        out.append(tuple(counts))
    return tuple(out)


def eta(H: SparseHypergraph, e: EdgeId, depth: int = DEFAULT_DEPTH) -> tuple[int, ...]:
    """Return ``(eta_1(e), ..., eta_depth(e))`` where
    ``eta_h(e) = sum_{v in e} xi_h(v)``.
    """
    if depth < 1:
        return ()
    accum = [0] * depth
    for v in H.members(e):
        for h, count in enumerate(xi(H, v, depth)):
            accum[h] += count
    return tuple(accum)


def _seed_key(H: SparseHypergraph, v: NodeId, depth: int) -> tuple[object, ...]:
    """Composite seed-selection key.

    Maximised lexicographically:
    1. ``xi_labelled(v)`` -- shell-by-shell label-aware count tuple.
    2. ``H.vertex_label(v)`` -- the seed's own label.
    """
    return (xi_labelled(H, v, depth), H.vertex_label(v))


def _python_max_xi_nodes(
    H: SparseHypergraph,
    depth: int = DEFAULT_DEPTH,
) -> tuple[NodeId, ...]:
    """Pure-Python reference implementation of :func:`max_xi_nodes`."""
    if H.n_nodes == 0:
        return ()
    best_key = max(_seed_key(H, v, depth) for v in H.nodes())
    return tuple(v for v in H.nodes() if _seed_key(H, v, depth) == best_key)


def _cpp_max_xi_nodes(
    H: SparseHypergraph,
    depth: int = DEFAULT_DEPTH,
) -> tuple[NodeId, ...]:
    """C++-backed implementation of :func:`max_xi_nodes`."""
    if H.n_nodes == 0:
        return ()
    return tuple(_core_max_xi_nodes(H, depth))


_MAX_XI_BACKENDS: dict[str, object] = {
    "python": _python_max_xi_nodes,
    "cpp": _cpp_max_xi_nodes,
}


def max_xi_nodes(
    H: SparseHypergraph,
    depth: int = DEFAULT_DEPTH,
    *,
    backend: Backend | None = None,
) -> tuple[NodeId, ...]:
    """Return all nodes attaining the lexicographic maximum of the seed key.

    Invariant 4: this is the *only* admissible seed set for the canonical
    algorithm.

    Parameters
    ----------
    H, depth
        See module docstring.
    backend : {"cpp", "python"}, optional
        Implementation to use. Defaults to ``"cpp"`` (see
        :data:`isalhg.core.backends.DEFAULT_BACKEND`).
    """
    if H.n_nodes == 0:
        return ()
    impl = resolve(backend, _MAX_XI_BACKENDS)
    return impl(H, depth)
