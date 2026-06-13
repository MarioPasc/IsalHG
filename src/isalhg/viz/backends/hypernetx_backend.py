"""HyperNetX visualisation backend.

HyperNetX's :func:`hnx.drawing.draw` takes per-node and per-edge colours
via the ``nodes_kwargs={"facecolors": ...}`` / ``edges_kwargs={"edgecolors": ...}``
escape hatches.

The 2.4.0 dict-of-set constructor crashes with
``AttributeError: 'DataFrame' object has no attribute 'misc_properties'``
on this install. The working path is the list-of-set constructor:
``hnx.Hypergraph([{1, 2, 3}, {2, 3, 4}])`` -- edges are auto-numbered by
position, so we feed the colour arrays in that same order.
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


class HyperNetXBackend(HypergraphVizBackend):
    """HyperNetX-backed renderer."""

    @property
    def name(self) -> str:
        return "hypernetx"

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
            import hypernetx as hnx
        except ImportError as exc:  # pragma: no cover -- exercised when hnx is absent
            raise VizBackendUnavailableError(
                "hypernetx is required for HyperNetXBackend; install via `pip install hypernetx`"
            ) from exc

        sorted_edges = sorted(H.edges())
        edge_sets: list[set[int]] = [set(int(v) for v in H.members(e)) for e in sorted_edges]
        # Isolated nodes (degree 0) won't appear from the edge-set constructor;
        # we add them after the fact so colour arrays stay full-coverage.
        hnxH = hnx.Hypergraph(edge_sets)
        for v in H.nodes():
            if int(v) not in set(hnxH.nodes):
                hnxH.add_node(int(v))

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

        # Per-node face colours: dict over node IDs (hnx accepts dict + scalar broadcast).
        node_face: dict[int, str] = {
            int(v): (GRAYED_FACE if v in grayed_nodes else node_colors.get(v, "#888888"))
            for v in H.nodes()
        }
        # Per-edge stroke colours: list aligned with sorted_edges order.
        edge_face_list = [
            (GRAYED_FACE if e in grayed_edges else edge_colors.get(e, "#AAAAAA"))
            for e in sorted_edges
        ]

        hnx.drawing.draw(
            hnxH,
            pos=layout,
            ax=ax,
            nodes_kwargs={"facecolors": node_face, "linewidths": 1.0},
            edges_kwargs={"edgecolors": edge_face_list, "linewidths": 1.0},
            with_node_labels=True,
            with_edge_labels=False,
        )

        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)

        return layout


register_backend("hypernetx", HyperNetXBackend)
