"""Tier 3 dataset: large-automorphism hard hypergraphs.

Curated family of hypergraphs designed to stress the canonical algorithm:

- Projective planes ``PG(2, q)`` for ``q in {7, 8, 9, 11, 13}`` (SageMath designs.*).
- Steiner triple systems ``STS(n)`` with large automorphism groups.
- Generalised quadrangles ``GQ(2, 4)`` and ``GQ(3, 5)`` (GAP + FinInG).
- Non-group Latin squares with large autotopy groups.
- Random ``r``-uniform ``d``-regular hypergraphs at threshold density.

Each item carries an ``iso_class`` label so the partition-agreement protocol
can run alongside the timeouts.
"""

from __future__ import annotations

from collections.abc import Iterator

from isalhg.datasets.base import HypergraphDataset
from isalhg.datasets.schemas import DatasetItem, DatasetMetadata
from isalhg.types import DatasetName


class HardnessHypergraphs(HypergraphDataset):
    """Curated hardness family for Tier 3."""

    def __init__(self, family: str) -> None:
        """Select one of ``{"projective_plane", "sts", "gq", "latin", "regular"}``."""
        self._family = family

    @property
    def name(self) -> DatasetName:
        return f"hardness_{self._family}"

    @property
    def metadata(self) -> DatasetMetadata:
        raise NotImplementedError

    def __iter__(self) -> Iterator[DatasetItem]:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError
