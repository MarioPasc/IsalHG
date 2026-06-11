"""Tier 2 dataset: Chung-Lu hypergraphs.

Wraps ``xgi.generators.random.chung_lu_hypergraph`` (Chodrow, 2020,
arXiv:1902.09302). Used for runtime-scaling measurements with prescribed
node-degree distributions; no iso labels.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence

from isalhg.datasets.base import HypergraphDataset
from isalhg.datasets.schemas import DatasetItem, DatasetMetadata
from isalhg.types import DatasetName, Seed


class ChungLuHypergraphs(HypergraphDataset):
    """Chung-Lu hypergraph generator with given node and edge degree sequences."""

    def __init__(
        self,
        node_degrees: Sequence[int],
        edge_degrees: Sequence[int],
        n_items: int,
        seed: Seed = 0,
    ) -> None:
        self._node_degrees = tuple(node_degrees)
        self._edge_degrees = tuple(edge_degrees)
        self._n_items = n_items
        self._seed = seed

    @property
    def name(self) -> DatasetName:
        return "chung_lu"

    @property
    def metadata(self) -> DatasetMetadata:
        raise NotImplementedError

    def __iter__(self) -> Iterator[DatasetItem]:
        raise NotImplementedError

    def __len__(self) -> int:
        return self._n_items

    def seed(self, seed: Seed) -> ChungLuHypergraphs:
        return ChungLuHypergraphs(
            node_degrees=self._node_degrees,
            edge_degrees=self._edge_degrees,
            n_items=self._n_items,
            seed=seed,
        )
