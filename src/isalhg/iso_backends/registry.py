"""Backend registry.

Maps backend names (the value of :attr:`IsoBackend.name`) to zero-argument
factories. Concrete backend modules call :func:`register_backend` at import
time; the orchestrator looks up backends by name through :func:`get_backend`.

Factories are lazy so optional dependencies (pynauty, python-igraph,
dreadnaut) are only imported when the corresponding backend is actually
requested.
"""

from __future__ import annotations

from collections.abc import Callable

from isalhg.errors import BackendUnavailableError
from isalhg.iso_backends.base import IsoBackend
from isalhg.types import BackendName

BackendFactory = Callable[[], IsoBackend]

_REGISTRY: dict[BackendName, BackendFactory] = {}


def register_backend(name: BackendName, factory: BackendFactory) -> None:
    """Register a backend under a canonical name.

    Raises
    ------
    ValueError
        If ``name`` is already registered.
    """
    raise NotImplementedError


def get_backend(name: BackendName) -> IsoBackend:
    """Instantiate the backend registered under ``name``.

    Raises
    ------
    isalhg.errors.BackendUnavailableError
        If no backend is registered under ``name``.
    """
    raise NotImplementedError


def available_backends() -> tuple[BackendName, ...]:
    """Return the names of all registered backends."""
    raise NotImplementedError


__all__ = [
    "BackendFactory",
    "BackendUnavailableError",
    "available_backends",
    "get_backend",
    "register_backend",
]
