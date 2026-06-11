"""Levi (incidence) bipartite reduction shared by the graph-iso backends.

The nauty, Traces, and bliss backends solve graph isomorphism, so they take a
hypergraph ``H = (V, E)`` and operate on its Levi bipartite graph
``B(H) = (V cup E, {{v, e} : v in e})`` with the partition (V, E) preserved
as a colouring.

Colouring scheme (CODE_DESIGN.md Section 6 module table). Two disjoint
colour ranges:

- vertex-side colour ``= vertex_label_id`` (range ``[0, |Sigma_v|)``).
- edge-side colour ``= |Sigma_v| + edge_label_id`` (range
  ``[|Sigma_v|, |Sigma_v| + |Sigma_e|)``).

The ranges are disjoint, so the underlying graph-iso engine treats vertex
nodes and hyperedge nodes as separate witness classes regardless of label
overlap. Mirrors the SageMath ``IncidenceStructure`` / GAP+FinInG
convention for hypergraph isomorphism via Levi.

Restriction: Python stdlib only.
"""

from __future__ import annotations

from dataclasses import dataclass

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.types import NodeId


@dataclass(frozen=True)
class LeviGraph:
    """Bipartite graph encoding the incidence relation of a hypergraph.

    Attributes
    ----------
    n_vertex_nodes : int
        Number of nodes on the "original vertices" side. These keep the
        contiguous IDs ``0..n_vertex_nodes-1`` from the source hypergraph.
    n_edge_nodes : int
        Number of nodes on the "hyperedges" side. They receive IDs
        ``n_vertex_nodes..n_vertex_nodes + n_edge_nodes - 1``.
    edges : tuple[tuple[int, int], ...]
        Undirected edges of the bipartite graph as ``(vertex_node,
        edge_node)`` pairs.
    colors : tuple[int, ...]
        Per-node colour. Length ``n_vertex_nodes + n_edge_nodes``. Vertex
        side carries ``vertex_label`` IDs; edge side carries
        ``n_vertex_labels + edge_label`` IDs.
    n_vertex_labels : int
        Source ``|Sigma_v|``; used to recover label ranges.
    n_edge_labels : int
        Source ``|Sigma_e|``.
    """

    n_vertex_nodes: int
    n_edge_nodes: int
    edges: tuple[tuple[int, int], ...]
    colors: tuple[int, ...]
    n_vertex_labels: int
    n_edge_labels: int

    @property
    def n_nodes(self) -> int:
        return self.n_vertex_nodes + self.n_edge_nodes

    def vertex_partition(self) -> tuple[tuple[NodeId, ...], tuple[NodeId, ...]]:
        """Return ``(vertex_side_ids, edge_side_ids)`` as the 2-colouring."""
        vertex_side = tuple(range(self.n_vertex_nodes))
        edge_side = tuple(range(self.n_vertex_nodes, self.n_nodes))
        return vertex_side, edge_side

    def color_classes(self) -> list[set[NodeId]]:
        """Return colour classes (sets of node IDs) ordered by colour ID."""
        classes: dict[int, set[NodeId]] = {}
        for node, colour in enumerate(self.colors):
            classes.setdefault(colour, set()).add(node)
        return [classes[c] for c in sorted(classes.keys())]


def to_levi(H: SparseHypergraph) -> LeviGraph:
    """Construct the Levi bipartite graph of ``H``.

    Hyperedges of arity 1 are admitted (they appear as bipartite leaves).
    The empty hypergraph yields an empty Levi graph.
    """
    n_v = H.n_nodes
    n_e = H.n_edges
    edges: list[tuple[int, int]] = []
    for e_id, members, _ in H.iter_edges():
        edge_node = n_v + e_id
        for v in sorted(members):
            edges.append((v, edge_node))

    colours: list[int] = []
    for v in range(n_v):
        colours.append(H.vertex_label(v))
    for e_id in range(n_e):
        colours.append(H.n_vertex_labels + H.edge_label(e_id))

    return LeviGraph(
        n_vertex_nodes=n_v,
        n_edge_nodes=n_e,
        edges=tuple(edges),
        colors=tuple(colours),
        n_vertex_labels=H.n_vertex_labels,
        n_edge_labels=H.n_edge_labels,
    )
