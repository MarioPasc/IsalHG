"""Name-keyed registry for visualisation backends.

Concrete backend modules register themselves at import time via
:func:`register_backend`. The :func:`get_backend` accessor lazily
imports the backend module on first request so optional library
dependencies stay out of the import path until used.
"""

from __future__ import annotations

import contextlib
import importlib
from collections.abc import Callable

from isalhg.errors import VizBackendNotFoundError
from isalhg.viz.base import HypergraphVizBackend

_BACKENDS: dict[str, Callable[[], HypergraphVizBackend]] = {}

# Map of backend name -> module path that will register it on import.
_LAZY_MODULES: dict[str, str] = {
    "xgi": "isalhg.viz.backends.xgi_backend",
    "hypernetx": "isalhg.viz.backends.hypernetx_backend",
    "hypergraphx": "isalhg.viz.backends.hypergraphx_backend",
}


def register_backend(
    name: str,
    factory: Callable[[], HypergraphVizBackend],
) -> None:
    """Register ``factory`` under ``name`` (overwrites any prior entry)."""
    _BACKENDS[name] = factory


def get_backend(name: str) -> HypergraphVizBackend:
    """Return a fresh instance of the backend registered under ``name``.

    Raises
    ------
    VizBackendNotFoundError
        If ``name`` is unknown after lazy import.
    """
    if name not in _BACKENDS and name in _LAZY_MODULES:
        importlib.import_module(_LAZY_MODULES[name])
    if name not in _BACKENDS:
        raise VizBackendNotFoundError(
            f"viz backend {name!r} is not registered (known: {sorted(_BACKENDS)})"
        )
    return _BACKENDS[name]()


def available_backends() -> tuple[str, ...]:
    """Return the sorted tuple of registered backend names.

    Triggers lazy import of every backend module first so the listing
    reflects the actual installed set, not just whatever has been
    requested earlier in the session.
    """
    for name, module_path in _LAZY_MODULES.items():
        if name not in _BACKENDS:
            # Library missing or backend's own dependency error;
            # the backend stays unregistered and is filtered out.
            with contextlib.suppress(ImportError):
                importlib.import_module(module_path)
    return tuple(sorted(_BACKENDS.keys()))
