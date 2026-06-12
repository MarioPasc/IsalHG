"""XGI visualisation backend.

Default backend. XGI's :func:`xgi.draw` accepts both per-node and
per-edge colours via dict mappings, which maps cleanly onto the
:class:`HypergraphVizBackend` contract. Layout is computed via
:func:`xgi.barycenter_spring_layout` and pinned across snapshot
columns by the caller.

External library imports stay inside method bodies so the package
remains importable without XGI.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.errors import VizBackendUnavailableError
from isalhg.types import EdgeId, NodeId
from isalhg.viz.base import HypergraphVizBackend, Position
from isalhg.viz.registry import register_backend
from isalhg.viz.style import GRAYED_FACE

if TYPE_CHECKING:
    from matplotlib.axes import Axes
else:
    Axes = Any


class XGIBackend(HypergraphVizBackend):
    """XGI-backed renderer for :class:`SparseHypergraph`."""

    @property
    def name(self) -> str:
        return "xgi"

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
        try:
            import xgi
        except ImportError as exc:  # pragma: no cover -- exercised when xgi is absent
            raise VizBackendUnavailableError(
                "xgi is required for XGIBackend; install via `pip install xgi`"
            ) from exc

        xH = xgi.Hypergraph()
        xH.add_nodes_from(list(H.nodes()))
        for e in H.edges():
            xH.add_edge(sorted(H.members(e)), id=int(e))

        if layout is None:
            try:
                raw = xgi.barycenter_spring_layout(xH, seed=42)
            except Exception:  # pragma: no cover -- degenerate fallback
                raw = xgi.circular_layout(xH)
            layout = {int(v): (float(p[0]), float(p[1])) for v, p in raw.items()}

        node_fc = {
            v: (GRAYED_FACE if v in grayed_nodes else node_colors.get(v, "#888888"))
            for v in H.nodes()
        }
        edge_fc = {
            int(e): (GRAYED_FACE if e in grayed_edges else edge_colors.get(e, "#AAAAAA"))
            for e in H.edges()
        }

        xgi.draw(
            xH,
            pos=layout,
            ax=ax,
            node_fc=node_fc,
            edge_fc=edge_fc,
            node_size=18,
            node_ec="#222222",
            node_lw=0.6,
            alpha=0.55,
            node_labels=True,
            hyperedge_labels=False,
        )

        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)

        return layout


register_backend("xgi", XGIBackend)
