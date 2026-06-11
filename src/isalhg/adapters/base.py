"""Abstract adapter interface (ABC) for external hypergraph-library bridges.

Bridge pattern (Gamma et al. 1994). Concrete adapters translate between
external types and :class:`SparseHypergraph`. The adapter is the single
point at which the external library is imported.

Restriction: only Python stdlib + abc + typing + isalhg.core. External
hypergraph libraries (hypernetx, xgi, hypergraphx) MUST be imported inside
method bodies, not at module top level.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from isalhg.core.sparse_hypergraph import SparseHypergraph

T = TypeVar("T")


class HypergraphAdapter(ABC, Generic[T]):
    """Abstract bridge between an external hypergraph library and IsalHG core."""

    @abstractmethod
    def from_external(self, obj: T) -> SparseHypergraph:
        """Convert an external hypergraph object to :class:`SparseHypergraph`.

        Raises
        ------
        isalhg.errors.AdapterDependencyMissingError
            If the external library is not installed.
        isalhg.errors.AdapterTranslationError
            If the object cannot be translated faithfully (multi-hyperedges,
            non-integer labels, etc.).
        """
        ...

    @abstractmethod
    def to_external(self, H: SparseHypergraph) -> T:
        """Convert a :class:`SparseHypergraph` to the external library's type."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier (e.g. ``"hypernetx"``, ``"xgi"``)."""
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"
