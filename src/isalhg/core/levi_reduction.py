"""Levi (incidence) bipartite reduction shared by both package concerns.

The nauty, Traces, and bliss iso backends solve *graph* isomorphism, so they
take a hypergraph ``H = (V, E)`` and operate on its Levi bipartite graph
``B(H) = (V cup E, {{v, e} : v in e})`` with the partition (V, E) preserved
as a colouring. The metric-space representations ``NautyLeviEditDistance`` and
``NetLSDDistance`` need the same reduction, so it lives in ``core`` (stdlib-only,
a pure structural transform) to keep both concerns free of an upward import.

Colouring scheme -- two disjoint colour ranges so a graph-iso engine treats
vertex nodes and hyperedge nodes as separate witness classes regardless of
label overlap:

- vertex-side colour ``= vertex_label_id`` (range ``[0, |Sigma_v|)``);
- edge-side colour ``= |Sigma_v| + edge_label_id`` (range
  ``[|Sigma_v|, |Sigma_v| + |Sigma_e|)``).

Mirrors the SageMath ``IncidenceStructure`` / GAP+FinInG convention for
hypergraph isomorphism via Levi.

Ordered partitions do not carry absolute colour identity
-------------------------------------------------------
nauty and Traces accept the colouring as an *ordered partition*: a sequence of
cells, identified by position. A colour with no nodes contributes no cell, so
the cell at position ``i`` is the ``i``-th *occupied* colour, not colour ``i``.
Two hypergraphs whose occupied colours differ therefore hand the engine the
same ordered partition, and the engine reports them isomorphic even though the
article's definition of isomorphism (Def. 1.3 of the Theorem A proof) demands
absolute label preservation, ``l_V2(phi(v)) == l_V1(v)``.

The repair is :meth:`LeviGraph.color_signature`. Both engines refine the given
ordered partition by *splitting* cells in place, never reordering them, so once
two Levi graphs are known to share the same colour profile -- the iso-invariant
multiset ``{(colour, |class|)}`` -- position and colour agree cell by cell and
the engine's canonical form is exact. Consumers therefore prepend the signature
to the certificate, exactly as ``core.canonical`` prepends the seed label to
``w*`` (T-TAb). The signature also pins the ``(|V|, |E|)`` split of the
bipartition, which a bare certificate does not encode.

bliss is exempt: python-igraph hands bliss the per-node colour *values*, so its
canonical form already distinguishes colours by identity rather than position.

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
        """Return the non-empty colour classes, ordered by colour ID.

        Unoccupied colours contribute no cell, so a cell's position identifies
        its colour only among Levi graphs sharing this graph's
        :meth:`color_profile`. Consumers that hand this partition to nauty or
        Traces must pair the resulting certificate with
        :meth:`color_signature`.

        Returns
        -------
        classes : list[set[NodeId]]
            One set of node IDs per occupied colour, in increasing colour order.
        """
        classes: dict[int, set[NodeId]] = {}
        for node, colour in enumerate(self.colors):
            classes.setdefault(colour, set()).add(node)
        return [classes[c] for c in sorted(classes.keys())]

    def color_profile(self) -> tuple[tuple[int, int], ...]:
        """Return ``((colour, class_size), ...)`` over occupied colours.

        The profile is the label histogram of ``H`` written in Levi colour
        coordinates, hence invariant under every hypergraph isomorphism, and it
        determines the ``(|V|, |E|)`` split of the bipartition.

        Returns
        -------
        profile : tuple[tuple[int, int], ...]
            Pairs in increasing colour order, aligned index-for-index with
            :meth:`color_classes`.
        """
        sizes: dict[int, int] = {}
        for colour in self.colors:
            sizes[colour] = sizes.get(colour, 0) + 1
        return tuple((c, sizes[c]) for c in sorted(sizes.keys()))

    def color_signature(self) -> bytes:
        """Return the byte encoding of :meth:`color_profile`.

        Fixed-width big-endian fields (a 4-byte pair count, then 4 bytes of
        colour and 4 bytes of class size per pair) so the signature is
        self-delimiting and may be concatenated with an arbitrary certificate.

        Returns
        -------
        signature : bytes
            ``4 + 8 * len(color_profile())`` bytes.
        """
        profile = self.color_profile()
        parts = [len(profile).to_bytes(4, "big")]
        parts.extend(c.to_bytes(4, "big") + size.to_bytes(4, "big") for c, size in profile)
        return b"".join(parts)


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
