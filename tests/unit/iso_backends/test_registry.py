"""Unit tests for :mod:`isalhg.iso_backends.registry`."""

from __future__ import annotations

import pytest

from isalhg.errors import BackendUnavailableError
from isalhg.iso_backends import registry
from isalhg.iso_backends.base import IsoBackend
from isalhg.iso_backends.isalhg_backend import IsalHGBackend  # triggers self-register

pytestmark = pytest.mark.unit


class TestRegistryAPI:
    def test_isalhg_in_available(self) -> None:
        assert "isalhg" in registry.available_backends()

    def test_get_backend_returns_instance(self) -> None:
        backend = registry.get_backend("isalhg")
        assert isinstance(backend, IsoBackend)
        assert isinstance(backend, IsalHGBackend)
        # The ``"isalhg"`` registry key resolves to the production default,
        # whose per-algorithm name is ``isalhg_<algorithm>``.
        assert backend.name.startswith("isalhg_")

    def test_get_unknown_raises(self) -> None:
        with pytest.raises(BackendUnavailableError):
            registry.get_backend("definitely_does_not_exist")

    def test_duplicate_registration_raises(self) -> None:
        with pytest.raises(ValueError):
            registry.register_backend("isalhg", lambda: IsalHGBackend())
