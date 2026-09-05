"""Metric-space layer -- hypergraph distances and competing representations.

Every distance implements :class:`isalhg.metric_space.base.HypergraphDistance`
and yields a real-valued dissimilarity between hypergraphs -- the metric-space
analogue of the iso-detection ``IsoBackend``. Concrete distances are registered
in :mod:`isalhg.metric_space.registry` and discovered by name.

This package may import from :mod:`isalhg.core`, :mod:`isalhg.adapters`, and
:mod:`isalhg.metrics`, and may use guarded optional external libraries (numpy,
rapidfuzz, ...). The shared Levi reduction lives in
:mod:`isalhg.core.levi_reduction` so both concerns depend only on ``core``.
One exception is deliberate: the fact-alphabet distances import
:func:`isalhg.iso_backends.canonical_order.canonical_ranks` inside function
bodies, so that the article's addressing has a single source of truth; no other
module of this package may import :mod:`isalhg.iso_backends`, and
:mod:`isalhg.iso_backends` never imports this package (no cycle).
"""

from __future__ import annotations
