"""IsalHG backend.

Wraps the canonical-string algorithm from :mod:`isalhg.core.canonical` behind
the :class:`IsoBackend` interface. The fingerprint is the canonical string
itself, UTF-8 encoded.
"""

from __future__ import annotations

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.iso_backends.base import IsoBackend
from isalhg.types import BackendName, Fingerprint


class IsalHGBackend(IsoBackend):
    """``IsoBackend`` adapter for the IsalHG canonical-string algorithm.

    Parameters
    ----------
    k : int
        Maximum hyperedge arity supported. Must equal the pointer count.
    structural_depth : int
        Depth of the ``xi`` / ``eta`` structural tuples used for seeding and
        tie-breaking. Default 3 (inherited from IsalGraph).
    """

    def __init__(self, *, k: int, structural_depth: int = 3) -> None:
        self._k = k
        self._structural_depth = structural_depth

    @property
    def name(self) -> BackendName:
        return "isalhg"

    def fingerprint(self, H: SparseHypergraph) -> Fingerprint:
        raise NotImplementedError

    def are_isomorphic(self, H1: SparseHypergraph, H2: SparseHypergraph) -> bool:
        raise NotImplementedError
