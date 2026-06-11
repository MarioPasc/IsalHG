"""Pairwise isomorphism protocol -- Tiers 1 and 3.

Iterates over the dataset's ``DatasetItem`` cross-product, queries
``backend.are_isomorphic`` for every pair, and records
``(false_positives, false_negatives, per_pair_wall_clock_s)`` against the
ground-truth ``iso_class`` labels.

Tier 1 sets a tight time budget; Tier 3 sets a 600 s per-instance timeout.
Both use the same protocol class; the orchestrator differentiates them by
parameters.
"""

from __future__ import annotations

from isalhg.datasets.base import HypergraphDataset
from isalhg.iso_backends.base import IsoBackend
from isalhg.protocols.base import BenchmarkProtocol, ProtocolResult
from isalhg.types import ProtocolName, Seed


class PairwiseIsoProtocol(BenchmarkProtocol):
    """Pairwise isomorphism decision over a labelled dataset."""

    def __init__(self, *, timeout_s: float = 600.0, check_bijection: bool = True) -> None:
        """Configure per-pair timeout and whether to verify bijection certificates."""
        self._timeout_s = timeout_s
        self._check_bijection = check_bijection

    @property
    def name(self) -> ProtocolName:
        return "pairwise_iso"

    def measure(
        self,
        backend: IsoBackend,
        dataset: HypergraphDataset,
        seed: Seed,
    ) -> ProtocolResult:
        raise NotImplementedError
