"""Abstract base class for benchmark protocols.

A protocol takes a backend and a dataset, runs one measurement pass, and
returns a :class:`ProtocolResult`. The orchestrator owns the outer loop
(protocol x backend x dataset x seed).

Restriction: only Python stdlib + abc + typing + isalhg.{core,iso_backends,datasets}.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from isalhg.datasets.base import HypergraphDataset
from isalhg.iso_backends.base import IsoBackend
from isalhg.types import BackendName, DatasetName, ProtocolName, Seed


@dataclass(frozen=True)
class ProtocolResult:
    """Outcome of one ``(protocol, backend, dataset, seed)`` measurement.

    Attributes
    ----------
    protocol : ProtocolName
        Identifier of the protocol that produced this result.
    backend : BackendName
        Identifier of the backend the protocol ran on. ``""`` for protocols
        that do not invoke a backend (Tier 4 calibration).
    dataset : DatasetName
        Identifier of the dataset.
    seed : Seed
        Seed used for the run.
    wall_clock_s : float
        Total wall-clock time the protocol spent.
    measurements : dict[str, Any]
        Protocol-specific payload (per-item timings, fingerprint bytes,
        partition labels, FP/FN counts, ...). The schema is documented by the
        concrete protocol's docstring.
    """

    protocol: ProtocolName
    backend: BackendName
    dataset: DatasetName
    seed: Seed
    wall_clock_s: float
    measurements: dict[str, Any] = field(default_factory=dict)


class BenchmarkProtocol(ABC):
    """Abstract benchmark protocol."""

    @property
    @abstractmethod
    def name(self) -> ProtocolName:
        """Short identifier used in registries, configs, and result records."""
        ...

    @abstractmethod
    def measure(
        self,
        backend: IsoBackend,
        dataset: HypergraphDataset,
        seed: Seed,
    ) -> ProtocolResult:
        """Execute one measurement pass.

        Parameters
        ----------
        backend : IsoBackend
            Backend under test. Protocols that do not exercise a backend (Tier
            4) accept any backend and ignore it.
        dataset : HypergraphDataset
            Source of items to measure on.
        seed : Seed
            Random seed for any stochastic component of the measurement.

        Returns
        -------
        ProtocolResult
            Self-describing payload (see :class:`ProtocolResult`).
        """
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"
