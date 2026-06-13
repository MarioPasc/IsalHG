"""Backend registry.

Maps backend names (the value of :attr:`IsoBackend.name`) to zero-argument
factories. Concrete backend modules call :func:`register_backend` at import
time; the orchestrator looks up backends by name through :func:`get_backend`.

Factories are lazy so optional dependencies (pynauty, python-igraph,
dreadnaut) are only imported when the corresponding backend is actually
requested. The :data:`_LAZY_MODULES` map points each backend name at the
module that registers it; :func:`get_backend` imports the module on first
request.
"""

from __future__ import annotations

import contextlib
import importlib
from collections.abc import Callable

from isalhg.errors import BackendUnavailableError
from isalhg.iso_backends.base import IsoBackend
from isalhg.types import BackendName

BackendFactory = Callable[[], IsoBackend]

_REGISTRY: dict[BackendName, BackendFactory] = {}

# Name → module that calls register_backend(name, ...) at import time.
_LAZY_MODULES: dict[BackendName, str] = {
    "isalhg": "isalhg.iso_backends.isalhg_backend",
    "pynauty_levi": "isalhg.iso_backends.pynauty_levi",
    "bliss_levi": "isalhg.iso_backends.bliss_levi",
    "traces_levi": "isalhg.iso_backends.traces_levi",
}


def register_backend(name: BackendName, factory: BackendFactory) -> None:
    """Register a backend under a canonical name.

    Raises
    ------
    ValueError
        If ``name`` is already registered.
    """
    if name in _REGISTRY:
        raise ValueError(f"backend {name!r} already registered")
    _REGISTRY[name] = factory


def get_backend(name: BackendName) -> IsoBackend:
    """Instantiate the backend registered under ``name``.

    Triggers a lazy import of the backend's module if needed.

    Raises
    ------
    isalhg.errors.BackendUnavailableError
        If no backend is registered under ``name`` (after the lazy
        import attempt) or if the lazy import itself failed.
    """
    if name not in _REGISTRY and name in _LAZY_MODULES:
        try:
            importlib.import_module(_LAZY_MODULES[name])
        except ImportError as exc:
            raise BackendUnavailableError(f"backend {name!r} cannot be loaded: {exc}") from exc
    if name not in _REGISTRY:
        raise BackendUnavailableError(
            f"backend {name!r} is not registered; available: {available_backends()}"
        )
    return _REGISTRY[name]()


def available_backends() -> tuple[BackendName, ...]:
    """Return the names of all registered backends, sorted alphabetically.

    Triggers lazy import of every known backend module first so the
    listing reflects the actual installable set, not just whatever has
    already been requested in the current session.
    """
    for name, module_path in _LAZY_MODULES.items():
        if name not in _REGISTRY:
            with contextlib.suppress(ImportError):
                importlib.import_module(module_path)
    return tuple(sorted(_REGISTRY.keys()))


def _reset_for_testing() -> None:
    """Empty the registry. For test isolation only -- not public API."""
    _REGISTRY.clear()


__all__ = [
    "BackendFactory",
    "BackendUnavailableError",
    "available_backends",
    "get_backend",
    "register_backend",
]
