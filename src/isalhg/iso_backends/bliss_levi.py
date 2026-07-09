"""bliss backend via the Levi bipartite reduction.

Uses ``python-igraph`` (which links against bliss) to canonicalise the Levi
graph. Imports ``igraph`` lazily inside method bodies so the package remains
importable without the optional dependency.

Unlike the nauty and Traces backends, this one needs no colour signature:
igraph hands bliss the per-node colour *values* rather than an ordered
partition, so absolute label identity survives, and the fingerprint already
embeds the canonical colour vector and the ``(|V|, |E|)`` split.
"""

from __future__ import annotations

from typing import Any

from isalhg.core.levi_reduction import LeviGraph, to_levi
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.errors import BackendUnavailableError
from isalhg.iso_backends.base import IsoBackend
from isalhg.iso_backends.registry import register_backend
from isalhg.types import BackendName, Fingerprint, NodeId


def _import_igraph() -> Any:
    try:
        import igraph
    except ImportError as exc:
        raise BackendUnavailableError(
            "python-igraph is required for BlissLeviBackend; install via "
            "`pip install python-igraph`"
        ) from exc
    return igraph


def _to_igraph(levi: LeviGraph) -> tuple[Any, list[int]]:
    """Build an ``igraph.Graph`` from a :class:`LeviGraph` plus its colour list."""
    igraph = _import_igraph()
    g = igraph.Graph(
        n=levi.n_nodes,
        edges=[list(e) for e in levi.edges],
        directed=False,
    )
    colors = list(levi.colors)
    g.vs["color"] = colors
    return g, colors


class BlissLeviBackend(IsoBackend):
    """bliss isomorphism backend over the Levi bipartite reduction."""

    @property
    def name(self) -> BackendName:
        return "bliss_levi"

    def fingerprint(self, H: SparseHypergraph) -> Fingerprint:
        if H.n_nodes == 0:
            return b""
        levi = to_levi(H)
        g, colors = _to_igraph(levi)
        perm = g.canonical_permutation(color=colors)
        canon = g.permute_vertices(perm)
        # Byte-stable certificate: sorted edge list + canonical colour list.
        sorted_edges = tuple(sorted(tuple(sorted(e.tuple)) for e in canon.es))
        canon_colors = tuple(canon.vs["color"])
        payload = repr((levi.n_vertex_nodes, levi.n_edge_nodes, canon_colors, sorted_edges))
        return payload.encode("utf-8")

    def are_isomorphic(self, H1: SparseHypergraph, H2: SparseHypergraph) -> bool:
        if H1.n_vertex_labels != H2.n_vertex_labels:
            return False
        if H1.n_edge_labels != H2.n_edge_labels:
            return False
        if H1.n_nodes != H2.n_nodes or H1.n_edges != H2.n_edges:
            return False
        if H1.n_nodes == 0:
            return True
        levi1, levi2 = to_levi(H1), to_levi(H2)
        g1, c1 = _to_igraph(levi1)
        g2, c2 = _to_igraph(levi2)
        return bool(g1.isomorphic_bliss(g2, color1=c1, color2=c2))

    def bijection_certificate(
        self, H1: SparseHypergraph, H2: SparseHypergraph
    ) -> dict[NodeId, NodeId] | None:
        """Return a vertex bijection ``H1 -> H2`` if iso, else ``None``.

        igraph's ``canonical_permutation(g)`` returns a list ``pi`` such
        that ``pi[i]`` is the *original vertex* at canonical position
        ``i`` (inverse of "canonical position of vertex ``i``"). Hence to
        map ``v`` in ``H1`` to ``H2``: find ``v``'s canonical position
        ``p = pi1^{-1}(v)``, then look up the vertex at the same
        position in ``H2`` via ``pi2(p)``.
        """
        if not self.are_isomorphic(H1, H2):
            return None
        levi1, levi2 = to_levi(H1), to_levi(H2)
        g1, c1 = _to_igraph(levi1)
        g2, c2 = _to_igraph(levi2)
        pi1 = g1.canonical_permutation(color=c1)
        pi2 = g2.canonical_permutation(color=c2)
        pi1_inv = [0] * len(pi1)
        for i, p in enumerate(pi1):
            pi1_inv[p] = i
        bijection: dict[NodeId, NodeId] = {}
        for v in range(levi1.n_vertex_nodes):
            target = pi2[pi1_inv[v]]
            if target >= levi2.n_vertex_nodes:
                return None
            bijection[v] = target
        return bijection


# Self-register at import time.
register_backend("bliss_levi", lambda: BlissLeviBackend())
