"""nauty backend via the Levi bipartite reduction.

Uses the ``pynauty`` Python binding to McKay's nauty 2.8 to canonicalise the
Levi graph and emit its canonical labelling as the fingerprint.

nauty takes the colouring as an ordered partition, which loses absolute label
identity, and ``pynauty.certificate`` is the canonical *adjacency* alone -- it
omits the colouring entirely, so two Levi graphs with different colour class
sizes can share a certificate. Both fingerprint and isomorphism test therefore
carry ``LeviGraph.color_signature`` alongside nauty's answer; see
:mod:`isalhg.core.levi_reduction` for why the pair is exact.

Imports ``pynauty`` lazily inside method bodies so the package remains
importable without the optional dependency.
"""

from __future__ import annotations

from typing import Any

from isalhg.core.levi_reduction import LeviGraph, to_levi
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.errors import BackendUnavailableError
from isalhg.iso_backends.base import IsoBackend
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
        levi = to_levi(H)
        cert = pynauty.certificate(_to_pynauty(levi))
        return levi.color_signature() + bytes(cert)

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
        levi1, levi2 = to_levi(H1), to_levi(H2)
        if levi1.color_profile() != levi2.color_profile():
            return False
        return bool(pynauty.isomorphic(_to_pynauty(levi1), _to_pynauty(levi2)))

    def bijection_certificate(
        self, H1: SparseHypergraph, H2: SparseHypergraph
    ) -> dict[NodeId, NodeId] | None:
        """Return a vertex bijection ``H1 -> H2`` if iso, else ``None``.

        Uses pynauty's ``canon_label`` to compute the canonical labellings
        of both Levi graphs and composes them to obtain the vertex-side
        bijection. The edge-side bijection is discarded.

        ``canon_label(g)`` returns a list ``pi`` such that ``pi[i]`` is
        the *original vertex* that ends up at canonical position ``i``
        (i.e. the inverse of "canonical position of vertex ``i``").
        Hence to map vertex ``v`` of ``H1`` to ``H2``: find its canonical
        position ``p = pi1^{-1}(v)``, then look up the vertex at the
        same position in ``H2`` via ``pi2(p)``.
        """
        if not self.are_isomorphic(H1, H2):
            return None
        pynauty = _import_pynauty()
        levi1 = to_levi(H1)
        levi2 = to_levi(H2)
        g1 = _to_pynauty(levi1)
        g2 = _to_pynauty(levi2)
        pi1 = pynauty.canon_label(g1)
        pi2 = pynauty.canon_label(g2)
        pi1_inv = [0] * len(pi1)
        for i, p in enumerate(pi1):
            pi1_inv[p] = i
        bijection: dict[NodeId, NodeId] = {}
        for v in range(levi1.n_vertex_nodes):
            target = pi2[pi1_inv[v]]
            if target >= levi2.n_vertex_nodes:
                # Should not happen when iso and colouring is correct.
                return None
            bijection[v] = target
        return bijection


# Self-register at import time.
register_backend("pynauty_levi", lambda: PynautyLeviBackend())
