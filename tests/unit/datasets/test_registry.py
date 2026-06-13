"""Unit tests for :mod:`isalhg.datasets.registry`."""

from __future__ import annotations

import pytest

from isalhg.datasets import registry
from isalhg.datasets.base import HypergraphDataset
from isalhg.datasets.schemas import DatasetMetadata
from isalhg.errors import DatasetNotFoundError

pytestmark = pytest.mark.unit


class _Dummy(HypergraphDataset):
    @property
    def name(self) -> str:
        return "_dummy"

    @property
    def metadata(self) -> DatasetMetadata:
        return DatasetMetadata(
            name="_dummy",
            n_items=0,
            arity_range=(2, 2),
            n_nodes_range=(0, 0),
            has_iso_labels=False,
            source="test",
        )

    def __iter__(self):  # type: ignore[override]
        return iter(())

    def __len__(self) -> int:
        return 0


@pytest.fixture(autouse=True)
def _snapshot_registry():
    """Snapshot existing keys; teardown removes only test-added entries.

    Real registrations happen at module import; clearing the dict and
    re-importing is a no-op because Python caches sys.modules. Hence we
    only roll back the test-added keys.
    """
    snapshot = set(registry._REGISTRY.keys())  # noqa: SLF001
    yield
    for k in list(registry._REGISTRY.keys()):  # noqa: SLF001
        if k not in snapshot:
            del registry._REGISTRY[k]  # noqa: SLF001


def test_register_and_resolve() -> None:
    registry.register_dataset("_dummy", lambda params: _Dummy())
    ds = registry.get_dataset("_dummy", {})
    assert isinstance(ds, _Dummy)


def test_register_duplicate_raises() -> None:
    registry.register_dataset("_dummy", lambda params: _Dummy())
    with pytest.raises(ValueError, match="already registered"):
        registry.register_dataset("_dummy", lambda params: _Dummy())


def test_get_unknown_raises_dataset_not_found() -> None:
    with pytest.raises(DatasetNotFoundError):
        registry.get_dataset("__never_registered__", {})


def test_available_returns_sorted_tuple() -> None:
    names = registry.available_datasets()
    assert names == tuple(sorted(names))
    # exhaustive_small is lazy-registered on access.
    assert "exhaustive_small" in names
