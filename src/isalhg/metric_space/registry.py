"""Distance registry.

Maps distance names (the value of :attr:`HypergraphDistance.name`) to
zero-argument factories, mirroring :mod:`isalhg.iso_backends.registry`.
Concrete distance modules call :func:`register_distance` at import time; the
experiment runner looks them up by name through :func:`get_distance`.

Factories are lazy so optional dependencies (rapidfuzz, pynauty, netlsd, ...)
are only imported when the corresponding distance is actually requested. The
:data:`_LAZY_MODULES` map points each distance name at the module that registers
it; it is empty at the metric-space foundation (T-M1a) and grows as concrete
distances land (``d_I`` and WL in T-M1b, the competitors in T-M3).
"""

from __future__ import annotations

import contextlib
import importlib
from collections.abc import Callable

from isalhg.errors import DistanceUnavailableError
from isalhg.metric_space.base import HypergraphDistance
from isalhg.types import DistanceName

DistanceFactory = Callable[[], HypergraphDistance]

_REGISTRY: dict[DistanceName, DistanceFactory] = {}

# Name → module that calls register_distance(name, ...) at import time. Grows as
# concrete distances land (d_I + WL in T-M1b; the competitors in T-M3).
_LAZY_MODULES: dict[DistanceName, str] = {
    "isalhg_levenshtein": "isalhg.metric_space.distances.isalhg_levenshtein",
    "hypergraph_wl_l1": "isalhg.metric_space.representations.wl",
    "hypergraph_wl_chi2": "isalhg.metric_space.representations.wl",
    "exact_hged": "isalhg.metric_space.distances.hged",
    "bipartite_hged": "isalhg.metric_space.distances.hged",
    "qin_hged": "isalhg.metric_space.distances.qin_hged",
    "nauty_levi_edit": "isalhg.metric_space.representations.nauty_levi_edit",
    "netlsd_l2": "isalhg.metric_space.representations.netlsd",
    "hpd_jsd": "isalhg.metric_space.representations.hpd",
    "hypercot": "isalhg.metric_space.representations.hypercot",
}


def register_distance(name: DistanceName, factory: DistanceFactory) -> None:
    """Register a distance under a canonical name.

    Raises
    ------
    ValueError
        If ``name`` is already registered.
    """
    if name in _REGISTRY:
        raise ValueError(f"distance {name!r} already registered")
    _REGISTRY[name] = factory


def get_distance(name: DistanceName) -> HypergraphDistance:
    """Instantiate the distance registered under ``name``.

    Triggers a lazy import of the distance's module if needed.

    Raises
    ------
    isalhg.errors.DistanceUnavailableError
        If no distance is registered under ``name`` (after the lazy import
        attempt) or if the lazy import itself failed.
    """
    if name not in _REGISTRY and name in _LAZY_MODULES:
        try:
            importlib.import_module(_LAZY_MODULES[name])
        except ImportError as exc:
            raise DistanceUnavailableError(f"distance {name!r} cannot be loaded: {exc}") from exc
    if name not in _REGISTRY:
        raise DistanceUnavailableError(
            f"distance {name!r} is not registered; available: {available_distances()}"
        )
    return _REGISTRY[name]()


def available_distances() -> tuple[DistanceName, ...]:
    """Return the names of all registered distances, sorted alphabetically.

    Triggers lazy import of every known distance module first so the listing
    reflects the actual installable set, not just whatever has already been
    requested in the current session.
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
    "DistanceFactory",
    "DistanceUnavailableError",
    "available_distances",
    "get_distance",
    "register_distance",
]
