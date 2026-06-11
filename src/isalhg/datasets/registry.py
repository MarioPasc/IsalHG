"""Dataset registry.

Maps dataset names to factories that take a ``dict[str, Any]`` of parameters
(from YAML config) and return a :class:`HypergraphDataset`. The orchestrator
discovers datasets exclusively through this registry.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from isalhg.datasets.base import HypergraphDataset
from isalhg.errors import DatasetNotFoundError
from isalhg.types import DatasetName

DatasetFactory = Callable[[dict[str, Any]], HypergraphDataset]

_REGISTRY: dict[DatasetName, DatasetFactory] = {}


def register_dataset(name: DatasetName, factory: DatasetFactory) -> None:
    """Register a dataset under a canonical name.

    Raises
    ------
    ValueError
        If ``name`` is already registered.
    """
    raise NotImplementedError


def get_dataset(name: DatasetName, params: dict[str, Any]) -> HypergraphDataset:
    """Instantiate the dataset registered under ``name`` with ``params``.

    Raises
    ------
    isalhg.errors.DatasetNotFoundError
        If no dataset is registered under ``name``.
    """
    raise NotImplementedError


def available_datasets() -> tuple[DatasetName, ...]:
    """Return the names of all registered datasets."""
    raise NotImplementedError


__all__ = [
    "DatasetFactory",
    "DatasetNotFoundError",
    "available_datasets",
    "get_dataset",
    "register_dataset",
]
