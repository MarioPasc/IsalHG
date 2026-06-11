"""Tier 5 dataset: the 12 HIC iso-equivalence atlas datasets.

Bundled with the HIC GitHub repo (Feng et al. 2024, Table 5):
``RHG-10``, ``RHG-3``, ``RHG-Table``, ``RHG-Pyramid``, ``IMDB-Dir-Form``,
``IMDB-Dir-Genre``, ``IMDB-Dir-Genre-M``, ``IMDB-Wri-Form``,
``IMDB-Wri-Genre``, ``IMDB-Wri-Genre-M``, ``Steam-Player``, ``Twitter-Friend``.

Each item carries an iso-equivalence class label so the partition-agreement
protocol can compute the cross-backend agreement matrix.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from isalhg.datasets.base import HypergraphDataset
from isalhg.datasets.schemas import DatasetItem, DatasetMetadata
from isalhg.types import DatasetName


class HICAtlasDataset(HypergraphDataset):
    """One of the 12 HIC atlas datasets."""

    KNOWN_NAMES: tuple[str, ...] = (
        "RHG-10",
        "RHG-3",
        "RHG-Table",
        "RHG-Pyramid",
        "IMDB-Dir-Form",
        "IMDB-Dir-Genre",
        "IMDB-Dir-Genre-M",
        "IMDB-Wri-Form",
        "IMDB-Wri-Genre",
        "IMDB-Wri-Genre-M",
        "Steam-Player",
        "Twitter-Friend",
    )

    def __init__(self, root: Path, hic_name: str) -> None:
        self._root = root
        self._hic_name = hic_name

    @property
    def name(self) -> DatasetName:
        return f"hic:{self._hic_name}"

    @property
    def metadata(self) -> DatasetMetadata:
        raise NotImplementedError

    def __iter__(self) -> Iterator[DatasetItem]:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError
