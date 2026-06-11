"""Isomorphism backends.

Every isomorphism algorithm (IsalHG, nauty, Traces, bliss, ...) implements
``IsoBackend`` from :mod:`isalhg.iso_backends.base`. Concrete backends are
registered in :mod:`isalhg.iso_backends.registry` and discovered by name at
experiment-orchestration time.

This package may import from :mod:`isalhg.core` and :mod:`isalhg.adapters` but
not from :mod:`isalhg.datasets`, :mod:`isalhg.protocols`, or
:mod:`isalhg.metrics` (one-way dependency direction).
"""

from __future__ import annotations
