"""Protocol registry.

Maps protocol names to factories that take a ``dict[str, Any]`` of parameters
(from YAML config) and return a :class:`BenchmarkProtocol`.

Concrete protocol modules call :func:`register_protocol` at import time;
:data:`_LAZY_MODULES` lets the orchestrator resolve names without manual
imports.
"""

from __future__ import annotations

import contextlib
import importlib
from collections.abc import Callable
from typing import Any

from isalhg.errors import ProtocolNotFoundError
from isalhg.protocols.base import BenchmarkProtocol
from isalhg.types import ProtocolName

ProtocolFactory = Callable[[dict[str, Any]], BenchmarkProtocol]

_REGISTRY: dict[ProtocolName, ProtocolFactory] = {}

# Name → module that calls register_protocol(name, ...) at import time.
_LAZY_MODULES: dict[ProtocolName, str] = {
    "pairwise_iso": "isalhg.protocols.pairwise_iso",
    "fingerprint_timing": "isalhg.protocols.fingerprint_timing",
    "algorithm_benchmark": "isalhg.protocols.algorithm_benchmark",
}


def register_protocol(name: ProtocolName, factory: ProtocolFactory) -> None:
    """Register a protocol under a canonical name.

    Raises
    ------
    ValueError
        If ``name`` is already registered.
    """
    if name in _REGISTRY:
        raise ValueError(f"protocol {name!r} already registered")
    _REGISTRY[name] = factory


def get_protocol(name: ProtocolName, params: dict[str, Any]) -> BenchmarkProtocol:
    """Instantiate the protocol registered under ``name`` with ``params``.

    Triggers a lazy import of the protocol's module if needed.

    Raises
    ------
    isalhg.errors.ProtocolNotFoundError
        If no protocol is registered under ``name``.
    """
    if name not in _REGISTRY and name in _LAZY_MODULES:
        try:
            importlib.import_module(_LAZY_MODULES[name])
        except ImportError as exc:
            raise ProtocolNotFoundError(f"protocol {name!r} cannot be loaded: {exc}") from exc
    if name not in _REGISTRY:
        raise ProtocolNotFoundError(
            f"protocol {name!r} is not registered; available: {available_protocols()}"
        )
    return _REGISTRY[name](params)


def available_protocols() -> tuple[ProtocolName, ...]:
    """Return the names of all registered protocols, sorted alphabetically."""
    for name, module_path in _LAZY_MODULES.items():
        if name not in _REGISTRY:
            with contextlib.suppress(ImportError):
                importlib.import_module(module_path)
    return tuple(sorted(_REGISTRY.keys()))


def _reset_for_testing() -> None:
    """Empty the registry. For test isolation only -- not public API."""
    _REGISTRY.clear()


__all__ = [
    "ProtocolFactory",
    "ProtocolNotFoundError",
    "available_protocols",
    "get_protocol",
    "register_protocol",
]
