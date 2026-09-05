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
    "fact_rank": "isalhg.metric_space.distances.fact_levenshtein",
    "fact_rank_roles": "isalhg.metric_space.distances.fact_levenshtein",
    "fact_local_colour": "isalhg.metric_space.distances.fact_addressing_ablations",
    "fact_local_key": "isalhg.metric_space.distances.fact_addressing_ablations",
    "fact_degree_key": "isalhg.metric_space.distances.fact_addressing_ablations",
    "hypergraph_wl_l1": "isalhg.metric_space.representations.wl",
    "hypergraph_wl_chi2": "isalhg.metric_space.representations.wl",
    "exact_hged": "isalhg.metric_space.distances.hged",
    "bipartite_hged": "isalhg.metric_space.distances.hged",
    "qin_hged": "isalhg.metric_space.distances.qin_hged",
    "nauty_levi_edit": "isalhg.metric_space.representations.nauty_levi_edit",
    "netlsd_l2": "isalhg.metric_space.representations.netlsd",
    "hpd_jsd": "isalhg.metric_space.representations.hpd",
    "hypercot": "isalhg.metric_space.representations.hypercot",
    "degree_seq_l1": "isalhg.metric_space.representations.degree_seq_l1",
    "size_l1": "isalhg.metric_space.representations.size_l1",
    # The second nauty tokenization (DESIGN.md G3): same canonical form as
    # nauty_levi_edit, one symbol per Levi node instead of per certificate byte.
    "nauty_cert_rows": "isalhg.metric_space.representations.nauty_levi_edit",
    # The two readings of the bipartite GED, separated because they fail
    # differently: the edit-path cost bounds the exact oracle, the raw
    # assignment value has false zeros. RQ2 reports both.
    "bipartite_ged_path": "isalhg.metric_space.distances.hged",
    "bipartite_ged_assign": "isalhg.metric_space.distances.hged",
    # Aliases. Each resolves to the same class as its canonical name, so
    # ``get_distance(alias).name`` returns the canonical name, not the alias --
    # callers that record both should take the requested string as the arm id
    # and ``distance.name`` as the canonical id.
    "nauty_cert": "isalhg.metric_space.representations.nauty_levi_edit",
    "wl_l1": "isalhg.metric_space.representations.wl",
    "netlsd": "isalhg.metric_space.representations.netlsd",
    "exact_ged": "isalhg.metric_space.distances.hged",
}

# Alias -> canonical registered name, for callers that need to collapse the two.
ALIASES: dict[DistanceName, DistanceName] = {
    "nauty_cert": "nauty_levi_edit",
    "wl_l1": "hypergraph_wl_l1",
    "netlsd": "netlsd_l2",
    "exact_ged": "exact_hged",
    "bipartite_ged_path": "bipartite_hged",
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


def labels_used(name: DistanceName) -> frozenset[str]:
    """Return the label kinds the distance registered under ``name`` reads.

    Reads :attr:`isalhg.metric_space.base.HypergraphDistance.labels_used` off
    the instantiated distance -- the class attribute is the single source of
    truth, and it is pinned against measured relabel-sensitivity by
    ``tests/unit/metric_space/test_representations_kb.py``. The audit table and
    the experiment runners print this so a reader can see at a glance which
    competitors compare the same information as ``fact_rank`` and which compare
    less.

    Parameters
    ----------
    name : DistanceName
        A registered distance name or alias.

    Returns
    -------
    frozenset[str]
        A subset of ``{"vertex", "edge"}``. Empty for the label-blind arms
        (``netlsd_l2``, ``hpd_jsd``, ``hypercot``, ``size_l1``,
        ``degree_seq_l1``).

    Raises
    ------
    isalhg.errors.DistanceUnavailableError
        If ``name`` is not registered, or its module cannot be imported.
    """
    return get_distance(name).labels_used


def _reset_for_testing() -> None:
    """Empty the registry. For test isolation only -- not public API."""
    _REGISTRY.clear()


__all__ = [
    "ALIASES",
    "DistanceFactory",
    "DistanceUnavailableError",
    "available_distances",
    "get_distance",
    "labels_used",
    "register_distance",
]
