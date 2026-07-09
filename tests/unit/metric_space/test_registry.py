"""Unit tests for :mod:`isalhg.metric_space.registry`."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.errors import DistanceUnavailableError
from isalhg.metric_space import registry
from isalhg.metric_space.base import HypergraphDistance

pytestmark = pytest.mark.unit


class _StubDistance(HypergraphDistance):
    @property
    def name(self) -> str:
        return "stub_zero"

    def pairwise(self, H1: SparseHypergraph, H2: SparseHypergraph) -> float:
        return 0.0


@pytest.fixture(autouse=True)
def _isolate_registry() -> Iterator[None]:
    """Snapshot and restore the module registry so stubs do not leak across tests."""
    saved = dict(registry._REGISTRY)
    yield
    registry._REGISTRY.clear()
    registry._REGISTRY.update(saved)


class TestRegistryAPI:
    def test_register_and_get(self) -> None:
        registry.register_distance("stub_zero", _StubDistance)
        d = registry.get_distance("stub_zero")
        assert isinstance(d, HypergraphDistance)
        assert isinstance(d, _StubDistance)
        assert d.name == "stub_zero"

    def test_available_lists_registered(self) -> None:
        registry.register_distance("stub_zero", _StubDistance)
        assert "stub_zero" in registry.available_distances()

    def test_get_unknown_raises(self) -> None:
        with pytest.raises(DistanceUnavailableError):
            registry.get_distance("definitely_not_a_distance")

    def test_duplicate_registration_raises(self) -> None:
        registry.register_distance("stub_zero", _StubDistance)
        with pytest.raises(ValueError):
            registry.register_distance("stub_zero", _StubDistance)
