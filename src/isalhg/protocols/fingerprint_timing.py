"""Fingerprint + timing protocol -- Tier 2.

Calls ``backend.fingerprint`` on every dataset item and records per-item
wall-clock and peak resident-set size. Outputs feed the runtime-scaling
sweep ``T ~ n^alpha m^beta r^gamma`` regression in
:mod:`isalhg.metrics.complexity_fit`.
"""

from __future__ import annotations

from isalhg.datasets.base import HypergraphDataset
from isalhg.iso_backends.base import IsoBackend
from isalhg.protocols.base import BenchmarkProtocol, ProtocolResult
from isalhg.types import ProtocolName, Seed


class FingerprintTimingProtocol(BenchmarkProtocol):
    """Wall-clock and memory measurement of fingerprint computation."""

    def __init__(self, *, timeout_s: float = 600.0, repeats: int = 1) -> None:
        self._timeout_s = timeout_s
        self._repeats = repeats

    @property
    def name(self) -> ProtocolName:
        return "fingerprint_timing"

    def measure(
        self,
        backend: IsoBackend,
        dataset: HypergraphDataset,
        seed: Seed,
    ) -> ProtocolResult:
        raise NotImplementedError
