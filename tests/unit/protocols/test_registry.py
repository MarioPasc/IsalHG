"""Unit tests for :mod:`isalhg.protocols.registry`."""

from __future__ import annotations

import pytest

from isalhg.errors import ProtocolNotFoundError
from isalhg.protocols import registry
from isalhg.protocols.base import BenchmarkProtocol, ProtocolResult

pytestmark = pytest.mark.unit


class _Dummy(BenchmarkProtocol):
    @property
    def name(self) -> str:
        return "_dummy"

    def measure(self, backend, dataset, seed):  # type: ignore[override]
        return ProtocolResult(
            protocol=self.name,
            backend=backend.name,
            dataset=dataset.name,
            seed=seed,
            wall_clock_s=0.0,
            measurements={},
        )


@pytest.fixture(autouse=True)
def _snapshot_registry():
    """Snapshot existing keys; teardown removes only test-added entries."""
    snapshot = set(registry._REGISTRY.keys())  # noqa: SLF001
    yield
    for k in list(registry._REGISTRY.keys()):  # noqa: SLF001
        if k not in snapshot:
            del registry._REGISTRY[k]  # noqa: SLF001


def test_register_and_resolve() -> None:
    registry.register_protocol("_dummy", lambda params: _Dummy())
    p = registry.get_protocol("_dummy", {})
    assert isinstance(p, _Dummy)


def test_register_duplicate_raises() -> None:
    registry.register_protocol("_dummy", lambda params: _Dummy())
    with pytest.raises(ValueError, match="already registered"):
        registry.register_protocol("_dummy", lambda params: _Dummy())


def test_get_unknown_raises_protocol_not_found() -> None:
    with pytest.raises(ProtocolNotFoundError):
        registry.get_protocol("__never_registered__", {})


def test_available_returns_sorted_tuple() -> None:
    names = registry.available_protocols()
    assert names == tuple(sorted(names))
    assert "pairwise_iso" in names
