"""Abstract base class for hypergraph dataset loaders.

A :class:`HypergraphDataset` is an iterable of :class:`DatasetItem` produced
either by enumeration (Tier 1), a random generator (Tiers 2-3), or by reading
a curated archive (Tiers 4-5).

Restriction: only Python stdlib + abc + typing + isalhg.core +
isalhg.datasets.schemas.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator

from isalhg.datasets.schemas import DatasetItem, DatasetMetadata
from isalhg.types import DatasetName, Seed


class HypergraphDataset(ABC):
    """Abstract hypergraph dataset.

    Concrete subclasses are typically constructed with their generator
    parameters (size, arity, density) and then iterated once per experimental
    seed. They are expected to be deterministic functions of the
    ``(parameters, seed)`` pair so reruns produce identical items.
    """

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def name(self) -> DatasetName:
        """Canonical identifier (registry key)."""
        ...

    @property
    @abstractmethod
    def metadata(self) -> DatasetMetadata:
        """Static description of this dataset instantiation."""
        ...

    # ------------------------------------------------------------------
    # Iteration
    # ------------------------------------------------------------------

    @abstractmethod
    def __iter__(self) -> Iterator[DatasetItem]:
        """Yield items in the dataset's natural order."""
        ...

    @abstractmethod
    def __len__(self) -> int:
        """Return the number of items that will be yielded."""
        ...

    # ------------------------------------------------------------------
    # Optional hooks
    # ------------------------------------------------------------------

    def seed(self, seed: Seed) -> HypergraphDataset:
        """Return a copy of this dataset bound to ``seed``.

        Default implementation returns ``self`` (deterministic datasets ignore
        the seed). Random-generator datasets override this to rebind their
        PRNG state.
        """
        return self

    # ------------------------------------------------------------------
    # Plumbing
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, n_items={len(self)})"
