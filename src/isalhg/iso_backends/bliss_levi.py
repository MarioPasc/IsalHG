"""bliss backend via the Levi bipartite reduction.

Uses ``python-igraph`` (which links against bliss) to canonicalise the Levi
graph. Imports ``igraph`` lazily inside method bodies so the package remains
importable without the optional dependency.
"""

from __future__ import annotations

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.iso_backends.base import IsoBackend
from isalhg.types import BackendName, Fingerprint, NodeId


class BlissLeviBackend(IsoBackend):
    """bliss isomorphism backend over the Levi bipartite reduction."""

    @property
    def name(self) -> BackendName:
        return "bliss_levi"

    def fingerprint(self, H: SparseHypergraph) -> Fingerprint:
        raise NotImplementedError

    def are_isomorphic(self, H1: SparseHypergraph, H2: SparseHypergraph) -> bool:
        raise NotImplementedError

    def bijection_certificate(
        self, H1: SparseHypergraph, H2: SparseHypergraph
    ) -> dict[NodeId, NodeId] | None:
        raise NotImplementedError
