"""``HypergraphVizBackend`` -- abstract drawing interface.

Concrete backends wrap one external visualisation library (XGI,
HyperNetX, HyperGraphX). Each backend implements a single :meth:`draw`
method that paints ``H`` onto a user-supplied matplotlib ``Axes`` with
caller-specified per-vertex and per-edge colours and a ``grayed`` mask
for elements that should be rendered as ghosts.

The draw method returns the node-position mapping it used so the next
snapshot column can pin layout for visual continuity across the step
strip.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, TypeAlias

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.types import EdgeId, NodeId

if TYPE_CHECKING:
    from matplotlib.axes import Axes
else:
    Axes = Any

Position: TypeAlias = tuple[float, float]


class HypergraphVizBackend(ABC):
    """Abstract base class for hypergraph visualisation backends."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier for this backend (matches the registry key)."""
        ...

    @abstractmethod
    def draw(
        self,
        H: SparseHypergraph,
        ax: Axes,
        *,
        node_colors: dict[NodeId, str],
        edge_colors: dict[EdgeId, str],
        grayed_nodes: frozenset[NodeId] = frozenset(),
        grayed_edges: frozenset[EdgeId] = frozenset(),
        layout: dict[NodeId, Position] | None = None,
    ) -> dict[NodeId, Position]:
        """Draw ``H`` on ``ax`` and return the layout used.

        Parameters
        ----------
        H : SparseHypergraph
            The hypergraph to draw.
        ax : matplotlib.axes.Axes
            Target axes.
        node_colors : dict[NodeId, str]
            Per-vertex colour (hex or named). Every active vertex must
            have an entry.
        edge_colors : dict[EdgeId, str]
            Per-hyperedge colour. Every active edge must have an entry.
        grayed_nodes : frozenset[NodeId], optional
            Vertices to render at reduced opacity (ghost mode).
        grayed_edges : frozenset[EdgeId], optional
            Hyperedges to render at reduced opacity (ghost mode).
        layout : dict[NodeId, Position] or None, optional
            If provided, the backend must reuse this layout instead of
            computing its own. Otherwise, the backend computes a layout
            and returns it.

        Returns
        -------
        dict[NodeId, Position]
            Node positions used (so the caller can pin them for the next
            snapshot column).
        """
        ...

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={self.name!r})"
