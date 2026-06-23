"""Weisfeiler--Leman (1-WL) colour refinement for sparse hypergraphs.

Computes an iteration-stabilised colour per vertex that is invariant under
hypergraph isomorphism. Used by the pruned canonical-string algorithms in
``isalhg.core.algorithms.*_wl_pruned`` to filter candidate seeds and to
collapse vertex orbits during V-branch backtracking.

The implementation refines on hyperedge incidence (not just the primal
graph) so that hyperedge-arity information participates in the colour:
each round computes a per-edge signature from the multiset of incident
vertex colours, then refines every vertex colour by the multiset of
signatures of its incident edges. This is the canonical "colour
refinement on bipartite incidence graph" extension of 1-WL to
hypergraphs (see Boker, "Weisfeiler-Leman Indistinguishability of
Graphs", 2019, and the standard hypergraph WL formulation used by Bai,
Zhang & Torr 2021 for the Levi/incidence reduction).

Caveat. WL on the incidence structure is strictly weaker than the
individualisation-refinement procedures used by nauty/Traces/bliss --
colour-refinement plateaus on vertex-transitive designs (Fano, STS(9),
GQ(2,2)), so the pruned algorithms degenerate to the unpruned greedy
search on those inputs. This is the known wall described in
``docs/research/HANDOFF_canonical_backtracking.md``.

Restriction: ZERO non-stdlib dependencies.
"""

from __future__ import annotations

from isalhg._core import wl_hash as _cpp_wl_hash
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.types import NodeId

__all__ = ["wl_hash", "wl_partition"]

_MAX_ROUNDS: int = 64

# ---------------------------------------------------------------------------
# FNV-1a 64-bit deterministic hash (mirrors src/isalhg/_core/include/isalhg/fnv.hpp).
# Replaces Python's salted hash() so the colour partition is cross-process
# stable. The pure-Python implementation below produces byte-identical
# output to the C++ ``_core.wl_hash`` path.
# ---------------------------------------------------------------------------

_FNV_OFFSET = 14695981039346656037
_FNV_PRIME = 1099511628211
_MASK64 = (1 << 64) - 1
_DOMAIN_VERTEX_INIT = 0xABCD0001
_DOMAIN_EDGE_SIG = 0xABCD0002
_DOMAIN_VERTEX_NEW = 0xABCD0003


def _fnv1a_mix(h: int, v: int) -> int:
    return ((h ^ (v & _MASK64)) * _FNV_PRIME) & _MASK64


def _fnv1a_init(v: int) -> int:
    return _fnv1a_mix(_FNV_OFFSET, v)


def _python_wl_hash(H: SparseHypergraph, *, max_rounds: int = _MAX_ROUNDS) -> list[int]:
    """Pure-Python reference WL hash (FNV-1a). Kept for differential tests."""
    n = H.n_nodes
    if n == 0:
        return []

    colours: list[int] = [
        _fnv1a_mix(_fnv1a_init(_DOMAIN_VERTEX_INIT), H.vertex_label(v)) for v in range(n)
    ]
    edges_data: list[tuple[int, frozenset[NodeId]]] = [
        (H.edge_label(e), H.members(e)) for e in H.edges()
    ]
    incident: list[tuple[int, ...]] = [tuple(sorted(H.incident_edges(v))) for v in range(n)]

    if not edges_data:
        return colours

    for _round in range(max_rounds):
        edge_sigs: list[int] = []
        for lab, members in edges_data:
            h = _fnv1a_init(_DOMAIN_EDGE_SIG)
            h = _fnv1a_mix(h, lab)
            for c in sorted(colours[u] for u in members):
                h = _fnv1a_mix(h, c)
            edge_sigs.append(h)
        new_colours: list[int] = []
        for v in range(n):
            h = _fnv1a_init(_DOMAIN_VERTEX_NEW)
            h = _fnv1a_mix(h, colours[v])
            for s in sorted(edge_sigs[e] for e in incident[v]):
                h = _fnv1a_mix(h, s)
            new_colours.append(h)
        if _partition_equiv(new_colours, colours):
            colours = new_colours
            break
        colours = new_colours
    return colours


def wl_hash(H: SparseHypergraph, *, max_rounds: int = _MAX_ROUNDS) -> list[int]:
    """Return per-vertex stable 1-WL colours (cross-process stable, FNV-1a).

    Parameters
    ----------
    H : SparseHypergraph
        Input hypergraph (any connectivity).
    max_rounds : int, optional
        Cap on refinement rounds. Convergence is guaranteed in at most
        ``H.n_nodes`` rounds; the cap is a safety bound.

    Returns
    -------
    list[int]
        ``hashes`` such that ``hashes[v]`` is the WL colour of vertex
        ``v``. Two vertices with the same colour are WL-equivalent
        (necessary but not sufficient for being in the same automorphism
        orbit). Colours are FNV-1a 64-bit values — stable across
        processes regardless of ``PYTHONHASHSEED``.
    """
    if H.n_nodes == 0:
        return []
    raw = _cpp_wl_hash(H, max_rounds)
    # nanobind returns int64; values are FNV-1a uint64. Re-interpret to the
    # unsigned domain so downstream comparisons match the Python reference.
    return [v & _MASK64 for v in raw]


def wl_partition(H: SparseHypergraph, *, max_rounds: int = _MAX_ROUNDS) -> dict[int, list[NodeId]]:
    """Group vertices by stable WL colour.

    Parameters
    ----------
    H : SparseHypergraph
        Input hypergraph.
    max_rounds : int, optional
        See :func:`wl_hash`.

    Returns
    -------
    dict[int, list[NodeId]]
        Mapping ``colour -> sorted list of vertices with that colour``.
    """
    hashes = wl_hash(H, max_rounds=max_rounds)
    partition: dict[int, list[NodeId]] = {}
    for v, h in enumerate(hashes):
        partition.setdefault(h, []).append(v)
    return partition


def _partition_equiv(a: list[int], b: list[int]) -> bool:
    """True iff ``a`` and ``b`` induce the same vertex partition.

    Colours are opaque, so equality is checked on the partition not on
    the raw integer values: build canonical IDs by first appearance.
    """
    if len(a) != len(b):
        return False
    map_a: dict[int, int] = {}
    map_b: dict[int, int] = {}
    next_a = 0
    next_b = 0
    for x, y in zip(a, b, strict=True):
        if x not in map_a:
            map_a[x] = next_a
            next_a += 1
        if y not in map_b:
            map_b[y] = next_b
            next_b += 1
        if map_a[x] != map_b[y]:
            return False
    return True
