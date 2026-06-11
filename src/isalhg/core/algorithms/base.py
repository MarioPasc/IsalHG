"""Abstract base class for H2S (hypergraph-to-string) algorithm variants.

All H2S variants take a hypergraph and return a ``Sigma_HG*`` string. They
differ in how they pick seed nodes and how exhaustively they explore the
tie-breaking tree.

Restriction: ZERO external dependencies. Only Python stdlib + abc + isalhg.core.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from isalhg.core.sparse_hypergraph import SparseHypergraph


class H2SAlgorithm(ABC):
    """Abstract hypergraph-to-string algorithm."""

    @abstractmethod
    def encode(self, H: SparseHypergraph) -> str:
        """Convert ``H`` to a ``Sigma_HG*`` instruction string."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier for this algorithm variant."""
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
