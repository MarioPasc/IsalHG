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

from collections import deque
from collections.abc import Iterable, Iterator, Mapping, Sequence

from isalhg.errors import InvalidLabelError, VocabularyMismatchError
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
