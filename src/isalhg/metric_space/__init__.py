"""Metric-space layer -- hypergraph distances and competing representations.

Every distance implements :class:`isalhg.metric_space.base.HypergraphDistance`
and yields a real-valued dissimilarity between hypergraphs -- the metric-space
analogue of the iso-detection ``IsoBackend``. Concrete distances are registered
in :mod:`isalhg.metric_space.registry` and discovered by name.

This package may import from :mod:`isalhg.core`, :mod:`isalhg.adapters`, and
:mod:`isalhg.metrics`, and may use guarded optional external libraries (numpy,
rapidfuzz, ...). It MUST NOT import :mod:`isalhg.iso_backends`: the shared Levi
reduction lives in :mod:`isalhg.core.levi_reduction` so both concerns depend
only on ``core``.
"""

from __future__ import annotations
