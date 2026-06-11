"""Tier 2 dataset: r-uniform Erdos-Renyi hypergraphs.

Wraps ``xgi.generators.uniform.uniform_erdos_renyi_hypergraph`` (Chodrow,
2020, arXiv:1902.09302). Used for runtime-scaling measurements; no iso labels.
"""

from __future__ import annotations

from collections.abc import Iterator

from isalhg.datasets.base import HypergraphDataset
from isalhg.datasets.schemas import DatasetItem, DatasetMetadata
from isalhg.types import DatasetName, Seed


class UniformErdosRenyiHypergraphs(HypergraphDataset):
    """``n``-node ``r``-uniform Erdos-Renyi hypergraphs at given density."""

    def __init__(
        self,
        n: int,
        r: int,
        edge_density: float,
        n_items: int,
        seed: Seed = 0,
    ) -> None:
        self._n = n
        self._r = r
        self._edge_density = edge_density
        self._n_items = n_items
        self._seed = seed

    @property
    def name(self) -> DatasetName:
        return "erdos_renyi"

    @property
    def metadata(self) -> DatasetMetadata:
        raise NotImplementedError

    def __iter__(self) -> Iterator[DatasetItem]:
        raise NotImplementedError

    def __len__(self) -> int:
        return self._n_items

    def seed(self, seed: Seed) -> UniformErdosRenyiHypergraphs:
        return UniformErdosRenyiHypergraphs(
            n=self._n,
            r=self._r,
            edge_density=self._edge_density,
            n_items=self._n_items,
            seed=seed,
        )
