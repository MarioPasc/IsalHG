"""Tier 4 dataset: hypergraphs from ``xgi.load_xgi_data``.

Calibration-only. Pulls named datasets (``email-Enron``,
``contact-high-school``, ``congress-bills``, ...) from the XGI hosted
collection (Landry et al. 2023, DOI:10.21105/joss.05162).
"""

from __future__ import annotations

from collections.abc import Iterator

from isalhg.datasets.base import HypergraphDataset
from isalhg.datasets.schemas import DatasetItem, DatasetMetadata
from isalhg.types import DatasetName


class XGIDataDataset(HypergraphDataset):
    """Loader around ``xgi.load_xgi_data``."""

    def __init__(self, xgi_name: str) -> None:
        self._xgi_name = xgi_name

    @property
    def name(self) -> DatasetName:
        return f"xgi_data:{self._xgi_name}"

    @property
    def metadata(self) -> DatasetMetadata:
        raise NotImplementedError

    def __iter__(self) -> Iterator[DatasetItem]:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError
