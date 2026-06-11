"""Tier 4 dataset: Austin Benson ARB hypergraph collection.

Calibration-only. Source: https://www.cs.cornell.edu/~arb/data/. No iso
labels; the structural-calibration protocol consumes these to set the Tier 2
sweep ranges.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from isalhg.datasets.base import HypergraphDataset
from isalhg.datasets.schemas import DatasetItem, DatasetMetadata
from isalhg.types import DatasetName


class ARBBensonDataset(HypergraphDataset):
    """ARB collection loader."""

    def __init__(self, root: Path, name: str) -> None:
        """Load the dataset rooted at ``root`` with subfolder ``name``."""
        self._root = root
        self._name = name

    @property
    def name(self) -> DatasetName:
        return f"arb_benson:{self._name}"

    @property
    def metadata(self) -> DatasetMetadata:
        raise NotImplementedError

    def __iter__(self) -> Iterator[DatasetItem]:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError
