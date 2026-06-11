"""Sparse hypergraph data model.

In-memory representation used by every other module in the package:
contiguous integer node IDs, hyperedges as :class:`frozenset` of node IDs,
no duplicate hyperedges. Generalisation of
``IsalGraph/src/isalgraph/core/sparse_graph.py`` from arity-2 edges to
arbitrary-arity sets.

Restriction: Python stdlib only.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator

from isalhg.types import EdgeId, HyperedgeSet, NodeId


class SparseHypergraph:
    """Adjacency-set hypergraph with contiguous integer node IDs.

    Invariants
    ----------
    1. Node IDs are exactly ``0, 1, ..., n_nodes - 1``.
    2. Every hyperedge ``e in self.hyperedges`` satisfies ``|e| >= 1`` and
       ``e subseteq {0, ..., n_nodes - 1}``.
    3. No two hyperedges share the same vertex set (multi-hyperedges are
       forbidden).
    """

    def __init__(
        self,
        n_nodes: int,
        hyperedges: Iterable[HyperedgeSet] = (),
    ) -> None:
        """Construct a hypergraph with ``n_nodes`` isolated nodes plus ``hyperedges``."""
        self._n_nodes = n_nodes
        self._hyperedges: tuple[HyperedgeSet, ...] = tuple(hyperedges)

    # ------------------------------------------------------------------
    # Basic accessors
    # ------------------------------------------------------------------

    @property
    def n_nodes(self) -> int:
        raise NotImplementedError

    @property
    def n_edges(self) -> int:
        raise NotImplementedError

    def nodes(self) -> Iterator[NodeId]:
        raise NotImplementedError

    def hyperedges(self) -> Iterator[HyperedgeSet]:
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Mutation (used by the S2H interpreter)
    # ------------------------------------------------------------------

    def add_node(self) -> NodeId:
        """Append a new node with ID ``self.n_nodes`` and return it."""
        raise NotImplementedError

    def add_hyperedge(self, members: Iterable[NodeId]) -> EdgeId:
        """Insert a new hyperedge. No-op if a hyperedge with the same set exists."""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def neighbors(self, v: NodeId, depth: int = 1) -> set[NodeId]:
        """Set of nodes within ``depth`` hops of ``v``, excluding ``v`` itself."""
        raise NotImplementedError

    def degree(self, v: NodeId) -> int:
        """Number of hyperedges incident to ``v``."""
        raise NotImplementedError
