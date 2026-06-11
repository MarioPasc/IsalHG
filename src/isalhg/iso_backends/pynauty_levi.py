"""nauty backend via the Levi bipartite reduction.

Uses the ``pynauty`` Python binding to McKay's nauty 2.8 to canonicalise the
Levi graph and emit its canonical labelling as the fingerprint.

Imports ``pynauty`` lazily inside method bodies so the package remains
importable without the optional dependency.
"""

from __future__ import annotations

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.iso_backends.base import IsoBackend
from isalhg.types import BackendName, Fingerprint, NodeId


class PynautyLeviBackend(IsoBackend):
    """nauty isomorphism backend over the Levi bipartite reduction."""

    @property
    def name(self) -> BackendName:
        return "pynauty_levi"

    def fingerprint(self, H: SparseHypergraph) -> Fingerprint:
        raise NotImplementedError

    def are_isomorphic(self, H1: SparseHypergraph, H2: SparseHypergraph) -> bool:
        raise NotImplementedError

    def bijection_certificate(
        self, H1: SparseHypergraph, H2: SparseHypergraph
    ) -> dict[NodeId, NodeId] | None:
        raise NotImplementedError
