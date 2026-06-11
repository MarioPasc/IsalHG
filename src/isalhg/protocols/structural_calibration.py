"""Structural calibration protocol -- Tier 4.

Does NOT invoke the backend. For each dataset item, records structural
descriptors: ``n_nodes``, ``n_edges``, ``arity_min``, ``arity_max``,
``arity_mean``, edge-density, degree-distribution moments. Used to set the
Tier 2 sweep ranges so the synthetic distributions match real-world
hypergraphs in scale.

The protocol still accepts an :class:`IsoBackend` argument so the orchestrator
can drive it through the same ``(protocol, backend, dataset)`` loop; the
argument is ignored.
"""

from __future__ import annotations

from isalhg.datasets.base import HypergraphDataset
from isalhg.iso_backends.base import IsoBackend
from isalhg.protocols.base import BenchmarkProtocol, ProtocolResult
from isalhg.types import ProtocolName, Seed


class StructuralCalibrationProtocol(BenchmarkProtocol):
    """Backend-free structural statistics collector."""

    @property
    def name(self) -> ProtocolName:
        return "structural_calibration"

    def measure(
        self,
        backend: IsoBackend,
        dataset: HypergraphDataset,
        seed: Seed,
    ) -> ProtocolResult:
        raise NotImplementedError
