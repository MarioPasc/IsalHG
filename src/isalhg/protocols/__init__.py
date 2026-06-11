"""Benchmark protocols.

A :class:`isalhg.protocols.base.BenchmarkProtocol` describes *what* to measure
when a backend meets a dataset. Each PROPOSAL tier corresponds to one
protocol subclass:

- :class:`PairwiseIsoProtocol` -- Tiers 1 and 3.
- :class:`FingerprintTimingProtocol` -- Tier 2.
- :class:`PartitionAgreementProtocol` -- Tier 5.
- :class:`StructuralCalibrationProtocol` -- Tier 4 (no backend invocation).

The orchestrator drives the experiment matrix
``Protocol x Backend x Dataset``.

This package may import from :mod:`isalhg.core`, :mod:`isalhg.iso_backends`,
:mod:`isalhg.datasets`, and :mod:`isalhg.metrics` but not from
:mod:`isalhg.adapters` (data-format interop is not a protocol concern).
"""

from __future__ import annotations
