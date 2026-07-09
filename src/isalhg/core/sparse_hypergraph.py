"""Sparse hypergraph data model.

In-memory representation used by every other module in the package:
contiguous integer node IDs, hyperedges as :class:`frozenset` of node IDs,
no duplicate hyperedges. Generalisation of
``IsalGraph/src/isalgraph/core/sparse_graph.py`` from arity-2 edges to
arbitrary-arity sets.

Labels are dataset-scoped ``int`` IDs in ``[0, |Sigma_v|)`` (vertex side) and
``[0, |Sigma_e|)`` (edge side); the semantic-string layer lives in
``datasets.schemas.LabelVocabulary`` and never reaches ``core/`` (decision I45).
The default trivial vocabulary ``(1, 1)`` means every vertex and edge carries
label ``0`` and the canonical algorithm exercises the same code path as the
labelled case.

Restriction: Python stdlib only.
"""

from __future__ import annotations

import random
from collections import deque
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence

from isalhg.errors import HypergraphEditError, InvalidLabelError, VocabularyMismatchError
from isalhg.types import EdgeId, EdgeLabel, HyperedgeSet, NodeId, VertexLabel


class SparseHypergraph:
    """Incidence-list hypergraph with contiguous integer node and edge IDs.

    Parameters
    ----------
    n_nodes : int
        Number of vertices; the IDs are exactly ``0, 1, ..., n_nodes - 1``.
    hyperedges : Iterable[HyperedgeSet], optional
        Initial hyperedges. Each must be a ``frozenset`` of ``NodeId`` values
        already in ``range(n_nodes)``. Duplicate sets are silently dropped
        (multi-hyperedges are forbidden, invariant 3).
    n_vertex_labels : int, optional
        Vocabulary size ``|Sigma_v|``. Defaults to ``1`` (trivial vocabulary).
    n_edge_labels : int, optional
        Vocabulary size ``|Sigma_e|``. Defaults to ``1`` (trivial vocabulary).
    vertex_labels : Sequence[VertexLabel] or None, optional
        Per-vertex label IDs of length ``n_nodes``. Defaults to all-zero.
    edge_labels : Sequence[EdgeLabel] or None, optional
        Per-edge label IDs aligned with ``hyperedges``. Defaults to all-zero.

    Invariants
    ----------
    1. Node IDs are exactly ``0, 1, ..., n_nodes - 1``; edge IDs are
       ``0, 1, ..., n_edges - 1``.
    2. Every hyperedge satisfies ``|e| >= 1`` and ``e subseteq nodes``.
    3. No two distinct edges share the same ``(label, member-set)`` pair.
    4. ``vertex_labels[v] in range(n_vertex_labels)`` for every ``v``;
       analogously for edges (decision I45).
    """

    __slots__ = (
        "_n_nodes",
        "_vertex_labels",
        "_edge_labels",
        "_edge_to_vertices",
        "_vertex_to_edges",
        "_edge_lookup",
        "_n_vertex_labels",
        "_n_edge_labels",
    )

    def __init__(
        self,
        n_nodes: int,
        hyperedges: Iterable[HyperedgeSet] = (),
        *,
        n_vertex_labels: int = 1,
        n_edge_labels: int = 1,
        vertex_labels: Sequence[VertexLabel] | None = None,
        edge_labels: Sequence[EdgeLabel] | None = None,
    ) -> None:
        if n_nodes < 0:
            raise ValueError(f"n_nodes must be non-negative, got {n_nodes}")
        if n_vertex_labels < 1 or n_edge_labels < 1:
            raise ValueError("label vocabulary sizes must be >= 1")
        self._n_nodes: int = n_nodes
        self._n_vertex_labels: int = n_vertex_labels
        self._n_edge_labels: int = n_edge_labels

        if vertex_labels is None:
            self._vertex_labels: list[VertexLabel] = [0] * n_nodes
        else:
            if len(vertex_labels) != n_nodes:
                raise ValueError(
                    f"vertex_labels has length {len(vertex_labels)}, expected {n_nodes}"
                )
            for v, ell in enumerate(vertex_labels):
                if not 0 <= ell < n_vertex_labels:
                    raise InvalidLabelError(
                        f"vertex_labels[{v}] = {ell} out of [0, {n_vertex_labels})"
                    )
            self._vertex_labels = list(vertex_labels)

        self._edge_to_vertices: list[HyperedgeSet] = []
        self._edge_labels: list[EdgeLabel] = []
        self._vertex_to_edges: list[set[EdgeId]] = [set() for _ in range(n_nodes)]
        self._edge_lookup: dict[tuple[EdgeLabel, HyperedgeSet], EdgeId] = {}

        edges_list = list(hyperedges)
        if edge_labels is None:
            edge_labels_list: list[EdgeLabel] = [0] * len(edges_list)
        else:
            edge_labels_list = list(edge_labels)
            if len(edge_labels_list) != len(edges_list):
                raise ValueError(
                    f"edge_labels has length {len(edge_labels_list)}, expected {len(edges_list)}"
                )
        for members, ell in zip(edges_list, edge_labels_list, strict=True):
            self.add_hyperedge(members, label=ell)

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    @property
    def n_nodes(self) -> int:
        return self._n_nodes

    @property
    def n_edges(self) -> int:
        return len(self._edge_to_vertices)

    @property
    def n_vertex_labels(self) -> int:
        return self._n_vertex_labels

    @property
    def n_edge_labels(self) -> int:
        return self._n_edge_labels

    def nodes(self) -> Iterator[NodeId]:
        return iter(range(self._n_nodes))

    def edges(self) -> Iterator[EdgeId]:
        return iter(range(self.n_edges))

    def hyperedges(self) -> Iterator[HyperedgeSet]:
        return iter(self._edge_to_vertices)

    def iter_edges(self) -> Iterator[tuple[EdgeId, HyperedgeSet, EdgeLabel]]:
        """Yield ``(edge_id, member-set, edge_label)`` for every hyperedge."""
        for e, members in enumerate(self._edge_to_vertices):
            yield e, members, self._edge_labels[e]

    def vertex_label(self, v: NodeId) -> VertexLabel:
        return self._vertex_labels[v]

    def edge_label(self, e: EdgeId) -> EdgeLabel:
        return self._edge_labels[e]

    def members(self, e: EdgeId) -> HyperedgeSet:
        """Return the vertex set of edge ``e``."""
        return self._edge_to_vertices[e]

    def incident_edges(self, v: NodeId) -> set[EdgeId]:
        """Return the set of edge IDs containing vertex ``v``."""
        return self._vertex_to_edges[v]

    def degree(self, v: NodeId) -> int:
        return len(self._vertex_to_edges[v])

    def has_edge(self, members: Iterable[NodeId], label: EdgeLabel = 0) -> bool:
        key = (label, frozenset(members))
        return key in self._edge_lookup

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add_node(self, label: VertexLabel = 0) -> NodeId:
        """Append a new vertex with ``label`` and return its ID."""
        if not 0 <= label < self._n_vertex_labels:
            raise InvalidLabelError(
                f"label {label} out of vertex-vocabulary range [0, {self._n_vertex_labels})"
            )
        new_id: NodeId = self._n_nodes
        self._n_nodes += 1
        self._vertex_labels.append(label)
        self._vertex_to_edges.append(set())
        return new_id

    def add_hyperedge(
        self,
        members: Iterable[NodeId],
        label: EdgeLabel = 0,
    ) -> EdgeId:
        """Insert a hyperedge. Returns the new edge ID, or the existing one
        if a hyperedge with the same ``(label, member-set)`` already exists.

        Raises
        ------
        InvalidLabelError
            If ``label`` is outside ``[0, n_edge_labels)``.
        ValueError
            If ``members`` is empty or references an out-of-range vertex.
        """
        if not 0 <= label < self._n_edge_labels:
            raise InvalidLabelError(
                f"label {label} out of edge-vocabulary range [0, {self._n_edge_labels})"
            )
        member_set: HyperedgeSet = frozenset(members)
        if not member_set:
            raise ValueError("hyperedge must contain at least one vertex")
        for v in member_set:
            if not 0 <= v < self._n_nodes:
                raise ValueError(f"vertex {v} out of range [0, {self._n_nodes})")

        key = (label, member_set)
        existing = self._edge_lookup.get(key)
        if existing is not None:
            return existing

        new_id: EdgeId = len(self._edge_to_vertices)
        self._edge_to_vertices.append(member_set)
        self._edge_labels.append(label)
        for v in member_set:
            self._vertex_to_edges[v].add(new_id)
        self._edge_lookup[key] = new_id
        return new_id

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def neighbors(self, v: NodeId, depth: int = 1) -> set[NodeId]:
        """Vertices within ``depth`` primal-graph hops of ``v``, excluding ``v``.

        Two vertices share a primal edge iff they co-occur in at least one
        hyperedge.
        """
        if depth < 1:
            return set()
        adjacency = self.primal_graph()
        seen: set[NodeId] = {v}
        frontier: set[NodeId] = {v}
        for _ in range(depth):
            nxt: set[NodeId] = set()
            for u in frontier:
                nxt.update(adjacency[u] - seen)
            seen.update(nxt)
            frontier = nxt
            if not frontier:
                break
        seen.discard(v)
        return seen

    def primal_graph(self) -> dict[NodeId, set[NodeId]]:
        """Return ``{v: {u : exists e in E with {u, v} subseteq e}}`` for all ``v``."""
        adj: dict[NodeId, set[NodeId]] = {v: set() for v in range(self._n_nodes)}
        for members in self._edge_to_vertices:
            members_list = tuple(members)
            for i, u in enumerate(members_list):
                for w in members_list[i + 1 :]:
                    adj[u].add(w)
                    adj[w].add(u)
        return adj

    def is_connected(self) -> bool:
        """True iff every vertex is reachable from vertex ``0`` in the primal graph.

        An empty hypergraph (no vertices) is connected by convention.
        Isolated vertices in a multi-vertex hypergraph make it disconnected.
        """
        if self._n_nodes <= 1:
            return True
        adj = self.primal_graph()
        seen: set[NodeId] = {0}
        queue: deque[NodeId] = deque([0])
        while queue:
            u = queue.popleft()
            for w in adj[u] - seen:
                seen.add(w)
                queue.append(w)
        return len(seen) == self._n_nodes

    def bfs_distances(self, source: NodeId) -> dict[NodeId, int]:
        """Return BFS distances from ``source`` in the primal graph (unreachable: absent)."""
        adj = self.primal_graph()
        dist: dict[NodeId, int] = {source: 0}
        queue: deque[NodeId] = deque([source])
        while queue:
            u = queue.popleft()
            for w in adj[u]:
                if w not in dist:
                    dist[w] = dist[u] + 1
                    queue.append(w)
        return dist

    # ------------------------------------------------------------------
    # Equality
    # ------------------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SparseHypergraph):
            return NotImplemented
        if self._n_nodes != other._n_nodes:
            return False
        if self._n_vertex_labels != other._n_vertex_labels:
            return False
        if self._n_edge_labels != other._n_edge_labels:
            return False
        if self._vertex_labels != other._vertex_labels:
            return False
        if len(self._edge_to_vertices) != len(other._edge_to_vertices):
            return False
        # Compare as multisets of (label, member-set) pairs (edge IDs are
        # implementation detail; isomorphism over node IDs is *not* checked here).
        return self._edge_lookup.keys() == other._edge_lookup.keys()

    def __hash__(self) -> int:
        return hash(
            (
                self._n_nodes,
                tuple(self._vertex_labels),
                frozenset(self._edge_lookup.keys()),
            )
        )

    def __repr__(self) -> str:
        return (
            f"SparseHypergraph(n_nodes={self._n_nodes}, n_edges={self.n_edges},"
            f" n_vlabels={self._n_vertex_labels}, n_elabels={self._n_edge_labels})"
        )


# ---------------------------------------------------------------------------
# Free functions
# ---------------------------------------------------------------------------


def permute(
    H: SparseHypergraph,
    sigma: Mapping[NodeId, NodeId] | Sequence[NodeId],
) -> SparseHypergraph:
    """Return a copy of ``H`` with vertices renamed by ``sigma``.

    ``sigma`` must be a permutation of ``{0, ..., H.n_nodes - 1}``; either a
    ``Mapping`` or a length-``n`` ``Sequence`` whose entries are the images.
    The returned hypergraph is structurally identical (same labels, same
    hyperedge member-sets up to relabelling) and is the positive iso-pair
    oracle for Tier 1 (decision I44).

    Raises
    ------
    ValueError
        If ``sigma`` is not a permutation of ``range(H.n_nodes)``.
    """
    n = H.n_nodes
    if isinstance(sigma, Mapping):
        sigma_list: list[NodeId] = [sigma[v] for v in range(n)]
    else:
        sigma_list = list(sigma)
    if sorted(sigma_list) != list(range(n)):
        raise ValueError(f"sigma must be a permutation of range({n})")

    new_vertex_labels: list[VertexLabel] = [0] * n
    for old_v, new_v in enumerate(sigma_list):
        new_vertex_labels[new_v] = H.vertex_label(old_v)

    new_edges: list[HyperedgeSet] = []
    new_edge_labels: list[EdgeLabel] = []
    for _, members, ell in H.iter_edges():
        new_edges.append(frozenset(sigma_list[v] for v in members))
        new_edge_labels.append(ell)

    return SparseHypergraph(
        n_nodes=n,
        hyperedges=new_edges,
        n_vertex_labels=H.n_vertex_labels,
        n_edge_labels=H.n_edge_labels,
        vertex_labels=new_vertex_labels,
        edge_labels=new_edge_labels,
    )


def assert_vocab_compatible(H1: SparseHypergraph, H2: SparseHypergraph) -> None:
    """Raise :class:`VocabularyMismatchError` if two hypergraphs disagree on label sizes."""
    if H1.n_vertex_labels != H2.n_vertex_labels or H1.n_edge_labels != H2.n_edge_labels:
        raise VocabularyMismatchError(
            f"vocab mismatch: ({H1.n_vertex_labels}, {H1.n_edge_labels})"
            f" vs ({H2.n_vertex_labels}, {H2.n_edge_labels})"
        )


def ego_network(H: SparseHypergraph, v: NodeId) -> SparseHypergraph:
    """Return the ego network ``EGO_H(v)`` of Qin et al. (ICDE 2023), Definition 1.

    ``NEI(v) = {v} ∪ {u : ∃e ∈ E, {u, v} ⊆ e}`` is the closed neighbourhood of
    ``v``; the ego network is the sub-hypergraph *induced* on ``NEI(v)``,
    keeping exactly the hyperedges **fully contained** in ``NEI(v)`` (edges
    partially overlapping the neighbourhood are dropped, not truncated).

    Node IDs are remapped to ``0..|NEI(v)|-1`` preserving ascending original
    order; vertex/edge labels and both vocabulary sizes are preserved. No two
    kept edges can collide under the remap because member-sets are unchanged
    and ``H`` already holds unique ``(label, member-set)`` pairs.

    Parameters
    ----------
    H : SparseHypergraph
        Source hypergraph (unchanged).
    v : NodeId
        Ego centre; must satisfy ``0 <= v < H.n_nodes``.

    Returns
    -------
    SparseHypergraph
        The induced ego network of ``v``.

    Raises
    ------
    ValueError
        If ``v`` is out of range.
    """
    if not 0 <= v < H.n_nodes:
        raise ValueError(f"vertex {v} out of range [0, {H.n_nodes})")
    nei: set[NodeId] = {v}
    for e in H.incident_edges(v):
        nei |= H.members(e)
    keep = sorted(nei)
    remap = {old: new for new, old in enumerate(keep)}
    edges: list[HyperedgeSet] = []
    edge_labels: list[EdgeLabel] = []
    for _, members, ell in H.iter_edges():
        if members <= nei:
            edges.append(frozenset(remap[u] for u in members))
            edge_labels.append(ell)
    return SparseHypergraph(
        n_nodes=len(keep),
        hyperedges=edges,
        n_vertex_labels=H.n_vertex_labels,
        n_edge_labels=H.n_edge_labels,
        vertex_labels=[H.vertex_label(u) for u in keep],
        edge_labels=edge_labels,
    )


# ---------------------------------------------------------------------------
# Structural edit operations (the six unit ops of the HGED, Qin et al. 2023)
# ---------------------------------------------------------------------------
#
# These are pure free functions (like ``permute``): each returns a *new*
# hypergraph and never mutates its argument. They are the generating set the
# exact HGED oracle searches over and the perturbation-ladder / planted-family
# generators sample from. Each is a single **unit-cost** operation, so a chain
# of ``t`` of them upper-bounds the HGED of the result by ``t`` (Qin et al.
# 2023 unit-cost specialization; the ladder's known budget).
#
# ``delete_vertex`` deletes an **isolated** vertex only: with ``remove_incidence``
# a separate atomic op, deleting a vertex that still sits in hyperedges is a
# compound edit, not a unit one. This keeps every op unit-cost. To delete a
# vertex in the interior, remove its incidences first (each a unit op).
#
# The ops preserve neither connectivity nor arity bounds -- ``insert_vertex``
# yields an isolated vertex, ``insert_hyperedge`` admits any arity. Corpus
# generators that require connectivity or ``arity <= k`` filter downstream;
# that constraint is theirs, not the operations'.


def _snapshot(
    H: SparseHypergraph,
) -> tuple[list[HyperedgeSet], list[EdgeLabel], list[VertexLabel]]:
    """Return mutable ``(edges, edge_labels, vertex_labels)`` copies in ID order."""
    edges: list[HyperedgeSet] = []
    edge_labels: list[EdgeLabel] = []
    for _, members, ell in H.iter_edges():
        edges.append(members)
        edge_labels.append(ell)
    vertex_labels: list[VertexLabel] = [H.vertex_label(v) for v in range(H.n_nodes)]
    return edges, edge_labels, vertex_labels


def _assemble(
    H: SparseHypergraph,
    n_nodes: int,
    edges: list[HyperedgeSet],
    edge_labels: list[EdgeLabel],
    vertex_labels: list[VertexLabel],
) -> SparseHypergraph:
    """Build a new hypergraph carrying ``H``'s label-vocabulary sizes."""
    return SparseHypergraph(
        n_nodes=n_nodes,
        hyperedges=edges,
        n_vertex_labels=H.n_vertex_labels,
        n_edge_labels=H.n_edge_labels,
        vertex_labels=vertex_labels,
        edge_labels=edge_labels,
    )


def insert_vertex(H: SparseHypergraph, label: VertexLabel = 0) -> SparseHypergraph:
    """Return a copy of ``H`` with one new isolated vertex appended.

    The new vertex gets ID ``H.n_nodes`` and participates in no hyperedge.

    Parameters
    ----------
    H : SparseHypergraph
        Source hypergraph (unchanged).
    label : VertexLabel, optional
        Label of the new vertex; must lie in ``[0, H.n_vertex_labels)``.

    Returns
    -------
    SparseHypergraph
        Copy with ``n_nodes + 1`` vertices.

    Raises
    ------
    InvalidLabelError
        If ``label`` is outside the vertex vocabulary range.
    """
    edges, edge_labels, vertex_labels = _snapshot(H)
    vertex_labels.append(label)
    return _assemble(H, H.n_nodes + 1, edges, edge_labels, vertex_labels)


def delete_vertex(H: SparseHypergraph, v: NodeId) -> SparseHypergraph:
    """Return a copy of ``H`` with the isolated vertex ``v`` removed.

    Vertices after ``v`` shift down by one to keep IDs contiguous. Only an
    isolated vertex (degree 0) may be deleted; remove its incidences first
    otherwise (each ``remove_incidence`` a unit op).

    Parameters
    ----------
    H : SparseHypergraph
        Source hypergraph (unchanged).
    v : NodeId
        Vertex to delete; must satisfy ``0 <= v < H.n_nodes`` and ``degree(v) == 0``.

    Returns
    -------
    SparseHypergraph
        Copy with ``n_nodes - 1`` vertices.

    Raises
    ------
    HypergraphEditError
        If ``v`` is out of range or not isolated.
    """
    if not 0 <= v < H.n_nodes:
        raise HypergraphEditError(f"vertex {v} out of range [0, {H.n_nodes})")
    if H.degree(v) != 0:
        raise HypergraphEditError(
            f"vertex {v} is not isolated (degree {H.degree(v)}); "
            "remove its incidences before deleting it"
        )
    edges: list[HyperedgeSet] = []
    edge_labels: list[EdgeLabel] = []
    for _, members, ell in H.iter_edges():
        edges.append(frozenset(u if u < v else u - 1 for u in members))
        edge_labels.append(ell)
    vertex_labels = [H.vertex_label(u) for u in range(H.n_nodes) if u != v]
    return _assemble(H, H.n_nodes - 1, edges, edge_labels, vertex_labels)


def insert_hyperedge(
    H: SparseHypergraph,
    members: Iterable[NodeId],
    label: EdgeLabel = 0,
) -> SparseHypergraph:
    """Return a copy of ``H`` with a new hyperedge over ``members``.

    Parameters
    ----------
    H : SparseHypergraph
        Source hypergraph (unchanged).
    members : Iterable[NodeId]
        Non-empty set of existing vertices spanned by the new hyperedge.
    label : EdgeLabel, optional
        Label of the new hyperedge; must lie in ``[0, H.n_edge_labels)``.

    Returns
    -------
    SparseHypergraph
        Copy with ``n_edges + 1`` hyperedges.

    Raises
    ------
    HypergraphEditError
        If ``members`` is empty, references an out-of-range vertex, the label
        is out of range, or the ``(label, member-set)`` already exists (which
        would silently merge two hyperedges, breaking the unit-cost model).
    """
    member_set: HyperedgeSet = frozenset(members)
    if not member_set:
        raise HypergraphEditError("hyperedge must contain at least one vertex")
    for u in member_set:
        if not 0 <= u < H.n_nodes:
            raise HypergraphEditError(f"vertex {u} out of range [0, {H.n_nodes})")
    if not 0 <= label < H.n_edge_labels:
        raise HypergraphEditError(f"edge label {label} out of range [0, {H.n_edge_labels})")
    if H.has_edge(member_set, label):
        raise HypergraphEditError(f"hyperedge (label={label}, {set(member_set)}) already exists")
    edges, edge_labels, vertex_labels = _snapshot(H)
    edges.append(member_set)
    edge_labels.append(label)
    return _assemble(H, H.n_nodes, edges, edge_labels, vertex_labels)


def delete_hyperedge(H: SparseHypergraph, e: EdgeId) -> SparseHypergraph:
    """Return a copy of ``H`` with hyperedge ``e`` removed.

    Edges after ``e`` shift down by one to keep IDs contiguous. Vertices are
    untouched (a vertex may become isolated).

    Parameters
    ----------
    H : SparseHypergraph
        Source hypergraph (unchanged).
    e : EdgeId
        Hyperedge to delete; must satisfy ``0 <= e < H.n_edges``.

    Returns
    -------
    SparseHypergraph
        Copy with ``n_edges - 1`` hyperedges.

    Raises
    ------
    HypergraphEditError
        If ``e`` is out of range.
    """
    if not 0 <= e < H.n_edges:
        raise HypergraphEditError(f"edge {e} out of range [0, {H.n_edges})")
    edges: list[HyperedgeSet] = []
    edge_labels: list[EdgeLabel] = []
    for e_id, members, ell in H.iter_edges():
        if e_id == e:
            continue
        edges.append(members)
        edge_labels.append(ell)
    _, _, vertex_labels = _snapshot(H)
    return _assemble(H, H.n_nodes, edges, edge_labels, vertex_labels)


def add_incidence(H: SparseHypergraph, v: NodeId, e: EdgeId) -> SparseHypergraph:
    """Return a copy of ``H`` with vertex ``v`` added to hyperedge ``e``.

    Grows the arity of ``e`` by one.

    Parameters
    ----------
    H : SparseHypergraph
        Source hypergraph (unchanged).
    v : NodeId
        Vertex to add; must be in range and not already incident to ``e``.
    e : EdgeId
        Hyperedge to grow; must be in range.

    Returns
    -------
    SparseHypergraph
        Copy in which ``members(e)`` gains ``v``.

    Raises
    ------
    HypergraphEditError
        If ``v`` or ``e`` is out of range, ``v`` is already incident to ``e``,
        or the grown edge would duplicate an existing ``(label, member-set)``.
    """
    if not 0 <= v < H.n_nodes:
        raise HypergraphEditError(f"vertex {v} out of range [0, {H.n_nodes})")
    if not 0 <= e < H.n_edges:
        raise HypergraphEditError(f"edge {e} out of range [0, {H.n_edges})")
    old = H.members(e)
    if v in old:
        raise HypergraphEditError(f"vertex {v} is already incident to edge {e}")
    label = H.edge_label(e)
    new_set: HyperedgeSet = old | {v}
    if H.has_edge(new_set, label):
        raise HypergraphEditError(
            f"adding vertex {v} to edge {e} would duplicate an existing hyperedge"
        )
    edges, edge_labels, vertex_labels = _snapshot(H)
    edges[e] = new_set
    return _assemble(H, H.n_nodes, edges, edge_labels, vertex_labels)


def remove_incidence(H: SparseHypergraph, v: NodeId, e: EdgeId) -> SparseHypergraph:
    """Return a copy of ``H`` with vertex ``v`` removed from hyperedge ``e``.

    Shrinks the arity of ``e`` by one. Removing the *last* incidence is
    forbidden (a hyperedge must keep ``arity >= 1``); use
    :func:`delete_hyperedge` for that.

    Parameters
    ----------
    H : SparseHypergraph
        Source hypergraph (unchanged).
    v : NodeId
        Vertex to remove; must be incident to ``e``.
    e : EdgeId
        Hyperedge to shrink; must be in range with ``arity >= 2``.

    Returns
    -------
    SparseHypergraph
        Copy in which ``members(e)`` loses ``v``.

    Raises
    ------
    HypergraphEditError
        If ``v`` or ``e`` is out of range, ``v`` is not incident to ``e``, the
        removal would empty ``e``, or the shrunk edge would duplicate an
        existing ``(label, member-set)``.
    """
    if not 0 <= v < H.n_nodes:
        raise HypergraphEditError(f"vertex {v} out of range [0, {H.n_nodes})")
    if not 0 <= e < H.n_edges:
        raise HypergraphEditError(f"edge {e} out of range [0, {H.n_edges})")
    old = H.members(e)
    if v not in old:
        raise HypergraphEditError(f"vertex {v} is not incident to edge {e}")
    if len(old) <= 1:
        raise HypergraphEditError(
            f"removing the last incidence of edge {e} would empty it; use delete_hyperedge instead"
        )
    label = H.edge_label(e)
    new_set: HyperedgeSet = old - {v}
    if H.has_edge(new_set, label):
        raise HypergraphEditError(
            f"removing vertex {v} from edge {e} would duplicate an existing hyperedge"
        )
    edges, edge_labels, vertex_labels = _snapshot(H)
    edges[e] = new_set
    return _assemble(H, H.n_nodes, edges, edge_labels, vertex_labels)


# ---------------------------------------------------------------------------
# Random edits and perturbation paths
# ---------------------------------------------------------------------------


def _sample_new_hyperedge(
    H: SparseHypergraph, rng: random.Random, tries: int = 8
) -> tuple[HyperedgeSet, EdgeLabel] | None:
    """Sample a fresh (non-duplicate) hyperedge, or ``None`` if none is found."""
    n = H.n_nodes
    if n == 0:
        return None
    for _ in range(tries):
        size = rng.randint(1, n)
        members: HyperedgeSet = frozenset(rng.sample(range(n), size))
        label = rng.randrange(H.n_edge_labels)
        if not H.has_edge(members, label):
            return members, label
    return None


def _sample_add_incidence(
    H: SparseHypergraph, rng: random.Random, tries: int = 8
) -> tuple[NodeId, EdgeId] | None:
    """Sample a valid ``(vertex, edge)`` for :func:`add_incidence`, or ``None``."""
    m = H.n_edges
    if m == 0:
        return None
    for _ in range(tries):
        e = rng.randrange(m)
        old = H.members(e)
        outside = [v for v in range(H.n_nodes) if v not in old]
        if not outside:
            continue
        v = rng.choice(outside)
        if not H.has_edge(old | {v}, H.edge_label(e)):
            return v, e
    return None


def _sample_remove_incidence(
    H: SparseHypergraph, rng: random.Random, tries: int = 8
) -> tuple[NodeId, EdgeId] | None:
    """Sample a valid ``(vertex, edge)`` for :func:`remove_incidence`, or ``None``."""
    big = [e for e in range(H.n_edges) if len(H.members(e)) >= 2]
    if not big:
        return None
    for _ in range(tries):
        e = rng.choice(big)
        old = H.members(e)
        v = rng.choice(tuple(old))
        if not H.has_edge(old - {v}, H.edge_label(e)):
            return v, e
    return None


def random_edit(H: SparseHypergraph, rng: random.Random) -> tuple[SparseHypergraph, str]:
    """Apply one uniformly-chosen applicable unit edit to ``H``.

    The operation type is chosen uniformly among those with at least one valid
    operand under the current state; ``insert_vertex`` is always applicable, so
    a result is always produced. The chosen operand is pre-validated, so the
    returned edit never raises.

    Parameters
    ----------
    H : SparseHypergraph
        Source hypergraph (unchanged).
    rng : random.Random
        Seeded stdlib RNG; the caller pins and reports the seed.

    Returns
    -------
    tuple[SparseHypergraph, str]
        The perturbed hypergraph and the name of the applied operation.
    """
    candidates: list[tuple[str, Callable[[], SparseHypergraph]]] = []

    vlabel = rng.randrange(H.n_vertex_labels)
    candidates.append(("insert_vertex", lambda: insert_vertex(H, vlabel)))

    isolated = [v for v in range(H.n_nodes) if H.degree(v) == 0]
    if isolated:
        dead = rng.choice(isolated)
        candidates.append(("delete_vertex", lambda: delete_vertex(H, dead)))

    if H.n_edges >= 1:
        victim = rng.randrange(H.n_edges)
        candidates.append(("delete_hyperedge", lambda: delete_hyperedge(H, victim)))

    fresh = _sample_new_hyperedge(H, rng)
    if fresh is not None:
        members, elabel = fresh
        candidates.append(("insert_hyperedge", lambda: insert_hyperedge(H, members, elabel)))

    grow = _sample_add_incidence(H, rng)
    if grow is not None:
        gv, ge = grow
        candidates.append(("add_incidence", lambda: add_incidence(H, gv, ge)))

    shrink = _sample_remove_incidence(H, rng)
    if shrink is not None:
        sv, se = shrink
        candidates.append(("remove_incidence", lambda: remove_incidence(H, sv, se)))

    name, make = rng.choice(candidates)
    return make(), name


def qin_edit_cost(before: SparseHypergraph, after: SparseHypergraph) -> int:
    """Qin-taxonomy cost of one generator edit, from its before/after pair.

    Under the Qin et al. (ICDE 2023) atomic operations — the article's official
    HGED cost model — a generator op costs ``|Δn| + |Δm| + |Δ total incidences|``:
    ``insert_vertex``/``delete_vertex``/``add_incidence``/``remove_incidence``
    cost 1, while ``insert_hyperedge``/``delete_hyperedge`` of an arity-``a``
    edge cost ``a + 1`` (``a`` incidence ops plus one empty-shell op).

    Exact for a single generator op; for arbitrary pairs it is only a lower
    bound on their true edit cost (deltas can cancel).

    Parameters
    ----------
    before, after : SparseHypergraph
        The hypergraphs on either side of one generator edit.

    Returns
    -------
    int
        The Qin-taxonomy cost of that edit.
    """
    inc_before = sum(len(members) for members in before.hyperedges())
    inc_after = sum(len(members) for members in after.hyperedges())
    return (
        abs(before.n_nodes - after.n_nodes)
        + abs(before.n_edges - after.n_edges)
        + abs(inc_before - inc_after)
    )


def random_connected_edit(H: SparseHypergraph, rng: random.Random) -> tuple[SparseHypergraph, str]:
    """Apply one randomly-chosen connectivity-preserving unit edit to ``H``.

    Like :func:`random_edit` but guarantees that the returned hypergraph is
    connected, given that ``H`` is connected on entry:

    - ``insert_vertex`` is always paired with an immediately following
      ``insert_hyperedge`` that includes the new vertex and a random existing
      vertex, so no isolated vertex ever materialises.  The pair is treated as
      one logical step and named ``"insert_vertex_and_edge"``; its Qin cost is
      correctly measured by :func:`qin_edit_cost` as the sum of both atomic
      costs (1 + 1 + arity).
    - ``insert_hyperedge`` over existing vertices and ``add_incidence`` only add
      connections and are therefore always connectivity-preserving.
    - ``delete_hyperedge`` and ``remove_incidence`` are included only when the
      result is connected (checked via :meth:`SparseHypergraph.is_connected`).
    - ``delete_vertex`` is never offered: a connected hypergraph with
      ``n_nodes >= 2`` has no isolated vertices.

    Parameters
    ----------
    H : SparseHypergraph
        Source hypergraph; must be connected and have ``n_nodes >= 1``.
    rng : random.Random
        Seeded stdlib RNG.

    Returns
    -------
    tuple[SparseHypergraph, str]
        The perturbed (connected) hypergraph and the name of the applied
        operation.
    """
    candidates: list[tuple[str, SparseHypergraph]] = []

    vlabel = rng.randrange(H.n_vertex_labels)
    # Paired insert: new vertex + edge connecting it to a random existing vertex.
    # Always applicable when n_nodes >= 1 and always connectivity-preserving.
    if H.n_nodes >= 1:
        existing = rng.randrange(H.n_nodes)
        v_new = H.n_nodes
        elabel_new = rng.randrange(H.n_edge_labels)
        H1 = insert_vertex(H, vlabel)
        candidates.append(
            ("insert_vertex_and_edge", insert_hyperedge(H1, [existing, v_new], elabel_new))
        )

    # insert_hyperedge over existing vertices: only adds connections, always safe.
    fresh = _sample_new_hyperedge(H, rng)
    if fresh is not None:
        members, elabel = fresh
        candidates.append(("insert_hyperedge", insert_hyperedge(H, members, elabel)))

    # add_incidence: only adds a vertex to an existing edge, always safe.
    grow = _sample_add_incidence(H, rng)
    if grow is not None:
        gv, ge = grow
        candidates.append(("add_incidence", add_incidence(H, gv, ge)))

    # delete_hyperedge: only when the result remains connected.
    if H.n_edges >= 1:
        victim = rng.randrange(H.n_edges)
        after_del = delete_hyperedge(H, victim)
        if after_del.is_connected():
            candidates.append(("delete_hyperedge", after_del))

    # remove_incidence: only when the result remains connected.
    shrink = _sample_remove_incidence(H, rng)
    if shrink is not None:
        sv, se = shrink
        after_rem = remove_incidence(H, sv, se)
        if after_rem.is_connected():
            candidates.append(("remove_incidence", after_rem))

    # The paired insert is always in candidates when n_nodes >= 1, so this
    # branch is only reachable for n_nodes == 0 (which never occurs in the
    # article's corpus generators).
    if not candidates:
        H1 = insert_vertex(H, 0)
        candidates.append(("insert_vertex", H1))

    name, result = rng.choice(candidates)
    return result, name


def edit_path(H: SparseHypergraph, t: int, rng: random.Random) -> tuple[SparseHypergraph, int]:
    """Apply ``t`` successive random edits and return the result with its budget.

    The returned budget is the **Qin-taxonomy cost** of the applied path —
    the sum of :func:`qin_edit_cost` over the ``t`` generator ops — and is a
    known **upper bound** on ``HGED(H, result)`` under the article's official
    (Qin et al. 2023, empty-shell) cost model: the path realises an actual
    edit sequence of exactly that total cost, while edits may cancel or
    compose (the true HGED can be smaller). This is the perturbation ladder's
    guarantee. Note ``budget >= t``, with equality iff no whole-hyperedge
    insert/delete of arity ``> 0`` occurred.

    Parameters
    ----------
    H : SparseHypergraph
        Source hypergraph (unchanged).
    t : int
        Number of generator edits to apply (``>= 0``).
    rng : random.Random
        Seeded stdlib RNG.

    Returns
    -------
    tuple[SparseHypergraph, int]
        The perturbed hypergraph and the Qin-cost budget (its upper-bound HGED).

    Raises
    ------
    HypergraphEditError
        If ``t`` is negative.
    """
    if t < 0:
        raise HypergraphEditError(f"edit budget t must be non-negative, got {t}")
    current = H
    budget = 0
    for _ in range(t):
        nxt, _ = random_edit(current, rng)
        budget += qin_edit_cost(current, nxt)
        current = nxt
    return current, budget
