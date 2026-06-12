"""Hypergraph drawing dispatch.

Thin wrapper around :func:`isalhg.viz.registry.get_backend`. Resolves a
backend name to a :class:`HypergraphVizBackend` instance and forwards
the draw call. Lives as its own module so callers do not have to know
about the registry directly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.types import EdgeId, NodeId
from isalhg.viz.base import Position
from isalhg.viz.registry import get_backend

if TYPE_CHECKING:
    from matplotlib.axes import Axes
else:
    Axes = Any


def draw_hypergraph(
    ax: Axes,
    H: SparseHypergraph,
    *,
    backend: str,
    node_colors: dict[NodeId, str],
    edge_colors: dict[EdgeId, str],
    grayed_nodes: frozenset[NodeId] = frozenset(),
    grayed_edges: frozenset[EdgeId] = frozenset(),
    layout: dict[NodeId, Position] | None = None,
) -> dict[NodeId, Position]:
    """Draw ``H`` on ``ax`` via the backend named ``backend``."""
    b = get_backend(backend)
    return b.draw(
        H,
        ax,
        node_colors=node_colors,
        edge_colors=edge_colors,
        grayed_nodes=grayed_nodes,
        grayed_edges=grayed_edges,
        layout=layout,
    )
