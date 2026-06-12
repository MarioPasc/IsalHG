"""Tests for :mod:`isalhg.viz.registry`."""

from __future__ import annotations

import pytest

from isalhg.errors import VizBackendNotFoundError
from isalhg.viz.base import HypergraphVizBackend
from isalhg.viz.registry import (
    available_backends,
    get_backend,
    register_backend,
)

pytestmark = pytest.mark.unit


def test_unknown_backend_raises() -> None:
    with pytest.raises(VizBackendNotFoundError):
        get_backend("nonexistent_backend_xyz")


def test_register_and_resolve() -> None:
    class _Dummy(HypergraphVizBackend):
        @property
        def name(self) -> str:
            return "_test_dummy"

        def draw(self, H, ax, **kwargs):  # type: ignore[no-untyped-def]
            return {}

    register_backend("_test_dummy", _Dummy)
    inst = get_backend("_test_dummy")
    assert isinstance(inst, _Dummy)


def test_available_includes_installed_backends() -> None:
    names = available_backends()
    # XGI, hypernetx, hypergraphx are pinned in the isalhg conda env;
    # at least one of them must be present.
    assert any(b in names for b in ("xgi", "hypernetx", "hypergraphx"))
