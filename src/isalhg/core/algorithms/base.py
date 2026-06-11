"""Abstract base class for H2S (hypergraph-to-string) algorithm variants.

All H2S variants take a hypergraph and return a ``Sigma_HG*`` token
sequence. They differ in how they pick seed nodes and how exhaustively
they explore the tie-breaking tree.

Concrete classes are not registered through a registry pattern (these
are not extension points consumed by experiment configs -- they are
internal strategies driven by :mod:`isalhg.core.canonical`).

Restriction: ZERO external dependencies. Only Python stdlib + abc +
isalhg.core.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.types import TokenSequence


class H2SAlgorithm(ABC):
    """Abstract hypergraph-to-string algorithm."""

    @abstractmethod
    def encode(self, H: SparseHypergraph) -> TokenSequence:
        """Convert ``H`` to a ``Sigma_HG*`` token sequence."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier for this algorithm variant."""
        ...

    def __repr__(self) -> str:
        return f"{type(self).__name__}()"
