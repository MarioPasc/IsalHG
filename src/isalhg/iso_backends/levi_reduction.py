"""Levi (incidence) bipartite reduction shared by the graph-iso backends.

The nauty, Traces, and bliss backends solve graph isomorphism, so they take a
hypergraph ``H = (V, E)`` and operate on its Levi bipartite graph ``B(H) = (V
cup E, {{v, e} : v in e})`` with the partition (V, E) preserved as a
2-colouring. Each backend may post-process the resulting canonical labelling,
but the reduction itself is shared.

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
    """

    n_vertex_nodes: int
    n_edge_nodes: int
    edges: tuple[tuple[int, int], ...]

    @property
    def n_nodes(self) -> int:
        """Total bipartite-graph order."""
        return self.n_vertex_nodes + self.n_edge_nodes

    def vertex_partition(self) -> tuple[tuple[NodeId, ...], tuple[NodeId, ...]]:
        """Return ``(vertex_side_ids, edge_side_ids)`` as the canonical 2-colouring."""
        raise NotImplementedError


def to_levi(H: SparseHypergraph) -> LeviGraph:
    """Construct the Levi bipartite graph of ``H``.

    Parameters
    ----------
    H : SparseHypergraph
        Source hypergraph. Hyperedges of arity 1 are excluded; arity 0 is
        forbidden upstream.

    Returns
    -------
    LeviGraph
        Bipartite-graph representation suitable for graph-iso backends.
    """
    raise NotImplementedError
