"""Tier 1 dataset: all connected hypergraphs with ``n in {3..6}`` and ``r in {2,3,4}``.

Enumerates via XGI under the hood and groups items by ground-truth isomorphism
class so the correctness protocol can assert ``FP = FN = 0``. The class
guarantees ``has_iso_labels = True``.
"""

from __future__ import annotations

from collections.abc import Iterator

from isalhg.datasets.base import HypergraphDataset
from isalhg.datasets.schemas import DatasetItem, DatasetMetadata
from isalhg.types import DatasetName


class ExhaustiveSmallHypergraphs(HypergraphDataset):
    """Enumeration of all connected hypergraphs in a small parameter window."""

    def __init__(
        self,
        n_range: tuple[int, int] = (3, 6),
        arity_range: tuple[int, int] = (2, 4),
    ) -> None:
        self._n_range = n_range
        self._arity_range = arity_range

    @property
    def name(self) -> DatasetName:
        return "exhaustive_small"

    @property
    def metadata(self) -> DatasetMetadata:
        raise NotImplementedError

    def __iter__(self) -> Iterator[DatasetItem]:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError
