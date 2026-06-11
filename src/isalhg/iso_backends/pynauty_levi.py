"""nauty backend via the Levi bipartite reduction.

Uses the ``pynauty`` Python binding to McKay's nauty 2.8 to canonicalise the
Levi graph and emit its canonical labelling as the fingerprint.

Imports ``pynauty`` lazily inside method bodies so the package remains
importable without the optional dependency.
"""

from __future__ import annotations

from typing import Any

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.errors import BackendUnavailableError
from isalhg.iso_backends.base import IsoBackend
from isalhg.iso_backends.levi_reduction import LeviGraph, to_levi
from isalhg.iso_backends.registry import register_backend
from isalhg.types import BackendName, Fingerprint, NodeId


def _import_pynauty() -> Any:
    try:
        import pynauty
    except ImportError as exc:
        raise BackendUnavailableError(
            "pynauty is required for PynautyLeviBackend; install via `pip install pynauty`"
        ) from exc
    return pynauty


def _to_pynauty(levi: LeviGraph) -> Any:
    """Build a ``pynauty.Graph`` from a :class:`LeviGraph` with vertex colouring."""
    pynauty = _import_pynauty()
    adjacency: dict[int, list[int]] = {node: [] for node in range(levi.n_nodes)}
    for u, v in levi.edges:
        adjacency[u].append(v)
        adjacency[v].append(u)
    g = pynauty.Graph(
        number_of_vertices=levi.n_nodes,
        directed=False,
        adjacency_dict=adjacency,
        vertex_coloring=levi.color_classes(),
    )
    return g


class PynautyLeviBackend(IsoBackend):
    """nauty isomorphism backend over the Levi bipartite reduction."""

    @property
    def name(self) -> BackendName:
        return "pynauty_levi"

    def fingerprint(self, H: SparseHypergraph) -> Fingerprint:
        pynauty = _import_pynauty()
        if H.n_nodes == 0:
            return b""
        g = _to_pynauty(to_levi(H))
        cert = pynauty.certificate(g)
        return bytes(cert)

    def are_isomorphic(self, H1: SparseHypergraph, H2: SparseHypergraph) -> bool:
        if H1.n_vertex_labels != H2.n_vertex_labels:
            return False
        if H1.n_edge_labels != H2.n_edge_labels:
            return False
        if H1.n_nodes != H2.n_nodes or H1.n_edges != H2.n_edges:
            return False
        pynauty = _import_pynauty()
        if H1.n_nodes == 0:
            return True
        g1 = _to_pynauty(to_levi(H1))
        g2 = _to_pynauty(to_levi(H2))
        return bool(pynauty.isomorphic(g1, g2))

    def bijection_certificate(
        self, H1: SparseHypergraph, H2: SparseHypergraph
    ) -> dict[NodeId, NodeId] | None:
        """Return a vertex bijection ``H1 -> H2`` if iso, else ``None``.

        Uses pynauty's ``canon_label`` to compute canonical permutations of
        both Levi graphs and composes them to obtain the vertex-side
        bijection. The edge-side bijection is discarded.
        """
        if not self.are_isomorphic(H1, H2):
            return None
        pynauty = _import_pynauty()
        levi1 = to_levi(H1)
        levi2 = to_levi(H2)
        g1 = _to_pynauty(levi1)
        g2 = _to_pynauty(levi2)
        # canon_label returns a permutation pi such that pi[i] = canonical
        # position of node i. Composition: vertex v in H1 maps to canon
        # position p; same p in H2's canonical maps back via pi2^{-1}.
        pi1 = pynauty.canon_label(g1)
        pi2 = pynauty.canon_label(g2)
        pi2_inv = [0] * len(pi2)
        for i, p in enumerate(pi2):
            pi2_inv[p] = i
        bijection: dict[NodeId, NodeId] = {}
        for v in range(levi1.n_vertex_nodes):
            target = pi2_inv[pi1[v]]
            if target >= levi2.n_vertex_nodes:
                # Should not happen when iso and colouring is correct.
                return None
            bijection[v] = target
        return bijection


# Self-register at import time.
register_backend("pynauty_levi", lambda: PynautyLeviBackend())
