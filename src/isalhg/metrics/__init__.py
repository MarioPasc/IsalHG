"""Stateless metric primitives consumed by benchmark protocols.

Each module exposes pure functions: protocols and the analysis layer combine
them as needed. No module owns state; no module depends on
:mod:`isalhg.iso_backends`, :mod:`isalhg.datasets`, or
:mod:`isalhg.protocols` (one-way dependency direction).
"""

from __future__ import annotations
