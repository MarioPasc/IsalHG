"""Protocol registry.

Maps protocol names to factories that take a ``dict[str, Any]`` of parameters
(from YAML config) and return a :class:`BenchmarkProtocol`.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from isalhg.errors import ProtocolNotFoundError
from isalhg.protocols.base import BenchmarkProtocol
from isalhg.types import ProtocolName

ProtocolFactory = Callable[[dict[str, Any]], BenchmarkProtocol]

_REGISTRY: dict[ProtocolName, ProtocolFactory] = {}


def register_protocol(name: ProtocolName, factory: ProtocolFactory) -> None:
    """Register a protocol under a canonical name.

    Raises
    ------
    ValueError
        If ``name`` is already registered.
    """
    raise NotImplementedError


def get_protocol(name: ProtocolName, params: dict[str, Any]) -> BenchmarkProtocol:
    """Instantiate the protocol registered under ``name`` with ``params``.

    Raises
    ------
    isalhg.errors.ProtocolNotFoundError
        If no protocol is registered under ``name``.
    """
    raise NotImplementedError


def available_protocols() -> tuple[ProtocolName, ...]:
    """Return the names of all registered protocols."""
    raise NotImplementedError


__all__ = [
    "ProtocolFactory",
    "ProtocolNotFoundError",
    "available_protocols",
    "get_protocol",
    "register_protocol",
]
