"""Visualisation subsystem for IsalHG.

Three atomic views (CDLL ring, instruction strip, hypergraph) composed
into per-step columns and stacked into roundtrip collages. The hypergraph
drawing is delegated to one of three external libraries via the
:class:`HypergraphVizBackend` ABC and a name-keyed registry.

Dependency rule: this package may import :mod:`isalhg.core` and
:mod:`isalhg.adapters`. External viz libraries (``matplotlib``, ``xgi``,
``hypernetx``, ``hypergraphx``) are imported inside method bodies only.
"""

from isalhg.viz.base import HypergraphVizBackend, Position
from isalhg.viz.cohort_panel import cohort_grid_figure
from isalhg.viz.registry import (
    available_backends,
    get_backend,
    register_backend,
)

__all__ = [
    "HypergraphVizBackend",
    "Position",
    "available_backends",
    "cohort_grid_figure",
    "get_backend",
    "register_backend",
]
