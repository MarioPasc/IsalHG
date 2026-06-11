"""Partition-agreement protocol -- Tier 5.

For each dataset, groups items by ``backend.fingerprint`` to obtain that
backend's iso-equivalence partition ``P_backend``. The orchestrator then
asserts ``P_IsalHG = P_pynauty = P_Traces = P_bliss`` across the 12 HIC
atlas datasets via :mod:`isalhg.metrics.partition`.
"""

from __future__ import annotations

from isalhg.datasets.base import HypergraphDataset
from isalhg.iso_backends.base import IsoBackend
from isalhg.protocols.base import BenchmarkProtocol, ProtocolResult
from isalhg.types import ProtocolName, Seed


class PartitionAgreementProtocol(BenchmarkProtocol):
    """Compute a backend's induced iso-equivalence partition of a dataset."""

    def __init__(self, *, timeout_s: float = 600.0) -> None:
        self._timeout_s = timeout_s

    @property
    def name(self) -> ProtocolName:
        return "partition_agreement"

    def measure(
        self,
        backend: IsoBackend,
        dataset: HypergraphDataset,
        seed: Seed,
    ) -> ProtocolResult:
        raise NotImplementedError
