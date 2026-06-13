"""HyperGraphX visualisation backend.

HyperGraphX's :func:`draw_hypergraph` only exposes
``hyperedge_color_by_order`` (one colour per edge cardinality), not
per-edge colouring. To recover per-edge colours we call
:func:`draw_hypergraph` once per hyperedge with a single-edge
sub-hypergraph and the desired colour, then draw the nodes once at the
end via matplotlib. All calls share the same pre-computed layout so
positions align.
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


class HypergraphxBackend(HypergraphVizBackend):
    """HyperGraphX-backed renderer with per-edge colour support."""

    @property
    def name(self) -> str:
        return "hypergraphx"

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
            import hypergraphx as hgx
            from hypergraphx.viz.draw_hypergraph import draw_hypergraph as hgx_draw
        except ImportError as exc:  # pragma: no cover -- exercised when hgx is absent
            raise VizBackendUnavailableError(
                "hypergraphx is required for HypergraphxBackend;"
                " install via `pip install hypergraphx`"
            ) from exc

        sorted_edges = sorted(H.edges())
        edge_lists_by_id: dict[int, list[int]] = {
            int(e): sorted(int(v) for v in H.members(e)) for e in sorted_edges
        }

        if layout is None:
            try:
                import networkx as nx

                G = nx.Graph()
                G.add_nodes_from(list(H.nodes()))
                for e in H.edges():
                    members = list(H.members(e))
                    for i, u in enumerate(members):
                        for v in members[i + 1 :]:
                            G.add_edge(u, v)
                raw = nx.spring_layout(G, seed=42)
                layout = {int(v): (float(p[0]), float(p[1])) for v, p in raw.items()}
            except Exception:  # pragma: no cover -- degenerate fallback
                import math

                n = max(1, H.n_nodes)
                layout = {
                    int(v): (math.cos(2 * math.pi * v / n), math.sin(2 * math.pi * v / n))
                    for v in H.nodes()
                }

        # hypergraphx 1.8 has a bug: its draw_hypergraph calls
        # ``ax.fill(..., c=color, edgecolor=facecolor)`` instead of
        # ``color=color``. matplotlib silently ignores ``c`` and falls
        # back to a default fill colour. We work around this by drawing
        # one hyperedge per call and recolouring the new polygon patches
        # immediately after each call. We also skip the per-call node
        # markers (``node_size=0``) and draw nodes once at the end with
        # full vertex-level colour control.
        for e in sorted_edges:
            members = edge_lists_by_id[int(e)]
            sub = hgx.Hypergraph([members])
            color = GRAYED_FACE if e in grayed_edges else edge_colors.get(e, "#AAAAAA")
            order = len(members)
            before = len(ax.patches)
            hgx_draw(
                sub,
                ax=ax,
                pos=layout,
                hyperedge_color_by_order={order: color},
                hyperedge_facecolor_by_order={order: color},
                node_size=0,
                hyperedge_alpha=0.40,
                with_node_labels=False,
            )
            for patch in ax.patches[before:]:
                patch.set_facecolor(color)
                patch.set_edgecolor(color)
                patch.set_alpha(0.40)

        for v in H.nodes():
            x, y = layout[int(v)]
            face = GRAYED_FACE if v in grayed_nodes else node_colors.get(v, "#888888")
            ax.scatter(
                [x],
                [y],
                s=215,
                c=[face],
                edgecolors="#222222",
                linewidths=0.9,
                zorder=5,
            )
            ax.text(
                x,
                y,
                str(int(v)),
                ha="center",
                va="center",
                fontsize=8,
                color="#111111",
                zorder=6,
            )

        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)

        return layout


register_backend("hypergraphx", HypergraphxBackend)
