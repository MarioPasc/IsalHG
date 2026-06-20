"""Dataset registry.

Maps dataset names to factories that take a ``dict[str, Any]`` of parameters
(from YAML config) and return a :class:`HypergraphDataset`. The orchestrator
discovers datasets exclusively through this registry.

Concrete dataset modules call :func:`register_dataset` at import time;
:data:`_LAZY_MODULES` lets :func:`get_dataset` and :func:`available_datasets`
import them on demand.
"""

from __future__ import annotations

import contextlib
import importlib
from collections.abc import Callable
from typing import Any

from isalhg.datasets.base import HypergraphDataset
from isalhg.errors import DatasetNotFoundError
from isalhg.types import DatasetName

DatasetFactory = Callable[[dict[str, Any]], HypergraphDataset]

_REGISTRY: dict[DatasetName, DatasetFactory] = {}

# Name → module that calls register_dataset(name, ...) at import time.
_LAZY_MODULES: dict[DatasetName, str] = {
    "exhaustive_small": "isalhg.datasets.synthetic.exhaustive_small",
    "random_erdos_renyi": "isalhg.datasets.synthetic.erdos_renyi",
}


def register_dataset(name: DatasetName, factory: DatasetFactory) -> None:
    """Register a dataset under a canonical name.

    Raises
    ------
    ValueError
        If ``name`` is already registered.
    """
    if name in _REGISTRY:
        raise ValueError(f"dataset {name!r} already registered")
    _REGISTRY[name] = factory


def get_dataset(name: DatasetName, params: dict[str, Any]) -> HypergraphDataset:
    """Instantiate the dataset registered under ``name`` with ``params``.

    Triggers a lazy import of the dataset's module if needed.

    Raises
    ------
    isalhg.errors.DatasetNotFoundError
        If no dataset is registered under ``name``.
    """
    if name not in _REGISTRY and name in _LAZY_MODULES:
        try:
            importlib.import_module(_LAZY_MODULES[name])
        except ImportError as exc:
            raise DatasetNotFoundError(f"dataset {name!r} cannot be loaded: {exc}") from exc
    if name not in _REGISTRY:
        raise DatasetNotFoundError(
            f"dataset {name!r} is not registered; available: {available_datasets()}"
        )
    return _REGISTRY[name](params)


def available_datasets() -> tuple[DatasetName, ...]:
    """Return the names of all registered datasets, sorted alphabetically."""
    for name, module_path in _LAZY_MODULES.items():
        if name not in _REGISTRY:
            with contextlib.suppress(ImportError):
                importlib.import_module(module_path)
    return tuple(sorted(_REGISTRY.keys()))


def _reset_for_testing() -> None:
    """Empty the registry. For test isolation only -- not public API."""
    _REGISTRY.clear()


__all__ = [
    "DatasetFactory",
    "DatasetNotFoundError",
    "available_datasets",
    "get_dataset",
    "register_dataset",
]
