"""Registry of H2S algorithm variants.

Maps algorithm names (the value of :attr:`H2SAlgorithm.name`) to
factories taking ``k`` and ``structural_depth``. Concrete algorithm
modules call :func:`register_algorithm` at import time; callers look up
algorithms by name through :func:`get_algorithm`.

Factories are lazy so the registry never imports every algorithm module
eagerly. :data:`_LAZY_MODULES` points each algorithm name at the module
that registers it; :func:`get_algorithm` imports the module on first
request.

Mirrors the ``IsoBackend`` registry pattern documented in
``docs/engineering/CODE_DESIGN.md`` Section 3. Restriction: stdlib only.
"""

from __future__ import annotations

import contextlib
import importlib
from collections.abc import Callable

from isalhg.core.algorithms.base import H2SAlgorithm
from isalhg.errors import AlgorithmUnavailableError

AlgorithmFactory = Callable[[int, int], H2SAlgorithm]

_REGISTRY: dict[str, AlgorithmFactory] = {}

# Name -> module that calls register_algorithm(name, ...) at import time.
_LAZY_MODULES: dict[str, str] = {
    "greedy_min": "isalhg.core.algorithms.greedy_min",
    "greedy_single": "isalhg.core.algorithms.greedy_single",
    "exhaustive": "isalhg.core.algorithms.exhaustive",
    "greedy_min_inplace": "isalhg.core.algorithms.greedy_min_inplace",
    "greedy_min_wl_pruned": "isalhg.core.algorithms.greedy_min_wl_pruned",
    "greedy_min_inplace_wl_pruned": "isalhg.core.algorithms.greedy_min_inplace_wl_pruned",
    "pruned_exhaustive": "isalhg.core.algorithms.pruned_exhaustive",
    "greedy_min_complete": "isalhg.core.algorithms.greedy_min_complete",
}


def register_algorithm(name: str, factory: AlgorithmFactory) -> None:
    """Register an algorithm under a canonical name.

    Parameters
    ----------
    name : str
        Algorithm identifier (matches :attr:`H2SAlgorithm.name`).
    factory : AlgorithmFactory
        Callable ``(k, structural_depth) -> H2SAlgorithm``.

    Raises
    ------
    ValueError
        If ``name`` is already registered.
    """
    if name in _REGISTRY:
        raise ValueError(f"algorithm {name!r} already registered")
    _REGISTRY[name] = factory


def get_algorithm(name: str, *, k: int, structural_depth: int = 3) -> H2SAlgorithm:
    """Instantiate the algorithm registered under ``name``.

    Triggers a lazy import of the algorithm's module if needed.

    Raises
    ------
    isalhg.errors.AlgorithmUnavailableError
        If no algorithm is registered under ``name`` after the lazy
        import attempt.
    """
    if name not in _REGISTRY and name in _LAZY_MODULES:
        try:
            importlib.import_module(_LAZY_MODULES[name])
        except ImportError as exc:
            raise AlgorithmUnavailableError(f"algorithm {name!r} cannot be loaded: {exc}") from exc
    if name not in _REGISTRY:
        raise AlgorithmUnavailableError(
            f"algorithm {name!r} is not registered; available: {available_algorithms()}"
        )
    return _REGISTRY[name](k, structural_depth)


def available_algorithms() -> tuple[str, ...]:
    """Return the names of all registered algorithms, sorted alphabetically.

    Triggers lazy import of every known algorithm module first so the
    listing reflects the actual registered set.
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
    "AlgorithmFactory",
    "AlgorithmUnavailableError",
    "available_algorithms",
    "get_algorithm",
    "register_algorithm",
]
