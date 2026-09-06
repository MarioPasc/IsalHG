"""``pynauty``-backed stabiliser-orbit oracle, and the entry points it drives.

The tie-complete search of :mod:`isalhg.core.hypergraph_to_string` explores
automorphic duplicates: on a star with ``q`` interchangeable leaves it visits
``q!`` orderings at the root alone. The orbit-pruning proposition licenses
keeping one branch per stabiliser orbit, and the individualisation lemma says
where the stabiliser comes from: ``Aut`` of the Levi graph ``B(H)`` with the
already-placed constants individualised -- each in its own singleton colour
cell, placed before every other cell -- restricted to the constant side is
exactly ``G_sigma``; individualising the fact node of ``e`` as well gives
``G_{sigma,e}``.

Two consequences drive the implementation:

- the stabiliser is **recomputed at every tie**. It shrinks as the search
  descends and inheriting the root group would prune branches that are not in
  fact equivalent;
- the pruning is **value-preserving**. Every entry point here returns the
  frozen ``w*_c``, bit for bit, and is pinned against it.

Also here is ``canonical_rank``: the family's greedy walk with the residual
tie broken by nauty's canonical rank rather than by raw edge id. That is a
*different* canonical program -- complete and isomorphism-invariant, but not
``w*_c`` -- so it is never used where ``w*_c`` is pinned.

``pynauty`` is imported inside function bodies, so importing this module never
requires it.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any, TypeVar

from isalhg.core.canonical import (
    CANONICAL_ORBIT_ALGORITHM,
    CANONICAL_RANK_ALGORITHM,
    canonical_fingerprint,
    canonical_string,
)
from isalhg.core.levi_reduction import LeviGraph, to_levi
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.errors import BackendUnavailableError
from isalhg.types import EdgeId, NodeId, VertexLabel

# Bound on the per-hypergraph generator caches. The search revisits a placed
# prefix rarely, so the cache is a working set, not a memo table; capping it
# keeps a deep search from retaining a group per visited state.
_CACHE_LIMIT = 4096

_T = TypeVar("_T")


def _import_pynauty() -> Any:
    """Return the ``pynauty`` module, or raise with an install hint."""
    try:
        import pynauty
    except ImportError as exc:  # pragma: no cover - exercised only without pynauty
        raise BackendUnavailableError(
            "pynauty is required for the orbit oracle; install via `pip install pynauty`"
        ) from exc
    return pynauty


class PynautyOrbitOracle:
    """Stabiliser orbits of the tie-complete search, via ``pynauty.autgrp``.

    One instance may serve many hypergraphs; the Levi graph and the adjacency
    dict are cached per hypergraph (keyed by identity, with the hypergraph kept
    alive by the cache so the key cannot be recycled).

    Attributes
    ----------
    autgrp_calls : int
        Number of ``pynauty.autgrp`` invocations made so far. Diagnostic only;
        it does not affect any returned value.
    """

    def __init__(self) -> None:
        self._levi: dict[int, tuple[SparseHypergraph, LeviGraph, dict[int, list[int]]]] = {}
        self._gens: dict[tuple[int, tuple[NodeId, ...]], tuple[tuple[int, ...], ...]] = {}
        self.autgrp_calls: int = 0

    # -- graph construction -------------------------------------------------

    def _levi_of(self, H: SparseHypergraph) -> tuple[LeviGraph, dict[int, list[int]]]:
        key = id(H)
        hit = self._levi.get(key)
        if hit is not None and hit[0] is H:
            return hit[1], hit[2]
        levi = to_levi(H)
        adjacency: dict[int, list[int]] = {node: [] for node in range(levi.n_nodes)}
        for u, v in levi.edges:
            adjacency[u].append(v)
            adjacency[v].append(u)
        if len(self._levi) >= _CACHE_LIMIT:
            self._levi.clear()
        self._levi[key] = (H, levi, adjacency)
        return levi, adjacency

    def _coloring(
        self,
        levi: LeviGraph,
        individualised: Sequence[int],
    ) -> list[set[int]]:
        """Refine the Levi colouring by individualising ``individualised``.

        Each listed node becomes its own cell, in the given order, ahead of the
        residual colour classes. Every node stays in exactly one cell, so the
        refinement is a genuine ordered partition of the Levi graph and the
        automorphism group it selects is the pointwise stabiliser of the listed
        nodes inside the colour-preserving group.
        """
        fixed = set(individualised)
        cells: list[set[int]] = [{node} for node in individualised]
        for cls in levi.color_classes():
            rest = cls - fixed
            if rest:
                cells.append(rest)
        return cells

    def _autgrp(
        self,
        H: SparseHypergraph,
        individualised: Sequence[int],
    ) -> tuple[tuple[tuple[int, ...], ...], list[int]]:
        """Return ``(generators, orbit_representatives)`` of the refined group."""
        pynauty = _import_pynauty()
        levi, adjacency = self._levi_of(H)
        graph = pynauty.Graph(
            number_of_vertices=levi.n_nodes,
            directed=False,
            adjacency_dict=adjacency,
            vertex_coloring=self._coloring(levi, individualised),
        )
        self.autgrp_calls += 1
        generators, _size1, _size2, orbits, _n_orbits = pynauty.autgrp(graph)
        return tuple(tuple(g) for g in generators), list(orbits)

    def _state_generators(
        self, H: SparseHypergraph, placed: Sequence[NodeId]
    ) -> tuple[tuple[int, ...], ...]:
        """Generators of ``G_sigma``, cached per ``(hypergraph, placed prefix)``."""
        key = (id(H), tuple(placed))
        hit = self._gens.get(key)
        if hit is not None:
            return hit
        generators, _ = self._autgrp(H, list(placed))
        if len(self._gens) >= _CACHE_LIMIT:
            self._gens.clear()
        self._gens[key] = generators
        return generators

    # -- the OrbitOracle protocol ------------------------------------------

    def seed_representatives(self, H: SparseHypergraph, seeds: Sequence[NodeId]) -> list[NodeId]:
        """Return one seed per ``Aut(H)``-orbit, in input order.

        Parameters
        ----------
        H : SparseHypergraph
            The hypergraph being encoded.
        seeds : Sequence[NodeId]
            The iso-invariant seed set.

        Returns
        -------
        list[NodeId]
            One representative per orbit, in input order.
        """
        if len(seeds) <= 1:
            return list(seeds)
        _, orbits = self._autgrp(H, ())
        return _first_per_class(seeds, lambda v: orbits[v])

    def edge_representatives(
        self,
        H: SparseHypergraph,
        placed: Sequence[NodeId],
        tied_edges: Sequence[EdgeId],
    ) -> list[EdgeId]:
        """Return one edge per ``G_sigma``-orbit of ``tied_edges``, in input order.

        ``pynauty.autgrp`` already reports the orbit partition of the refined
        group on the Levi nodes, so the fact nodes are classified directly; no
        union--find is needed at this level.

        Parameters
        ----------
        H : SparseHypergraph
            The hypergraph being encoded.
        placed : Sequence[NodeId]
            ``dom mu`` -- placed input node ids in creation order.
        tied_edges : Sequence[EdgeId]
            The residual tie set.

        Returns
        -------
        list[EdgeId]
            One representative per orbit, in input order.
        """
        if len(tied_edges) <= 1:
            return list(tied_edges)
        levi, _ = self._levi_of(H)
        offset = levi.n_vertex_nodes
        _, orbits = self._autgrp(H, list(placed))
        return _first_per_class(tied_edges, lambda e: orbits[offset + e])

    def ordering_representatives(
        self,
        H: SparseHypergraph,
        placed: Sequence[NodeId],
        edge: EdgeId,
        orderings: Sequence[tuple[NodeId, ...]],
    ) -> list[tuple[NodeId, ...]]:
        """Return one ordering per ``G_{sigma,e}``-orbit, in input order.

        The group acts on *tuples*, not on single nodes, so the orbits are
        computed by union--find over the generator images of each candidate
        ordering. A trivial ``G_sigma`` cannot have a non-trivial subgroup, so
        that case short-circuits without a second ``autgrp`` call.

        Parameters
        ----------
        H : SparseHypergraph
            The hypergraph being encoded.
        placed : Sequence[NodeId]
            ``dom mu`` -- placed input node ids in creation order.
        edge : EdgeId
            The tied edge committed to at this branch.
        orderings : Sequence[tuple[NodeId, ...]]
            Label-respecting orderings of the unplaced members of ``edge``.

        Returns
        -------
        list[tuple[NodeId, ...]]
            One representative per orbit, in input order.
        """
        if len(orderings) <= 1:
            return list(orderings)
        if not self._state_generators(H, placed):
            return list(orderings)
        levi, _ = self._levi_of(H)
        individualised = [*placed, levi.n_vertex_nodes + edge]
        generators, _ = self._autgrp(H, individualised)
        if not generators:
            return list(orderings)

        index = {order: i for i, order in enumerate(orderings)}
        parent = list(range(len(orderings)))

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for i, order in enumerate(orderings):
            for g in generators:
                j = index.get(tuple(g[v] for v in order))
                if j is None:
                    continue
                root_i, root_j = find(i), find(j)
                if root_i != root_j:
                    parent[max(root_i, root_j)] = min(root_i, root_j)
        return _first_per_class(orderings, lambda order: find(index[order]))


def _first_per_class(items: Sequence[_T], key: Callable[[_T], Any]) -> list[_T]:
    """Keep the first element of ``items`` in each ``key`` class, in input order."""
    seen: set[Any] = set()
    out: list[_T] = []
    for item in items:
        cls = key(item)
        if cls not in seen:
            seen.add(cls)
            out.append(item)
    return out


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------


def canonical_string_orbit(
    H: SparseHypergraph,
    *,
    k: int | None = None,
    structural_depth: int = 3,
) -> str:
    """Compute ``w*_c(H)`` through the orbit-pruned tie-complete search.

    Parameters
    ----------
    H : SparseHypergraph
        Connected hypergraph.
    k : int or None, optional
        Pointer count; ``None`` uses ``required_k(H)``.
    structural_depth : int, optional
        Structural-tuple depth. Defaults to 3.

    Returns
    -------
    str
        The frozen canonical string ``w*_c``, identical to
        ``canonical_string(H, algorithm="canonical")``.

    Raises
    ------
    isalhg.errors.BackendUnavailableError
        If ``pynauty`` is not installed.
    """
    return canonical_string(
        H,
        k=k,
        structural_depth=structural_depth,
        algorithm=CANONICAL_ORBIT_ALGORITHM,
        backend="python",
        orbit_oracle=PynautyOrbitOracle(),
    )


def canonical_fingerprint_orbit(
    H: SparseHypergraph,
    *,
    k: int | None = None,
    structural_depth: int = 3,
) -> tuple[VertexLabel, str]:
    """Compute ``F(H) = (seed label, w*_c(H))`` through the orbit-pruned search.

    Parameters
    ----------
    H : SparseHypergraph
        Connected hypergraph.
    k : int or None, optional
        Pointer count; ``None`` uses ``required_k(H)``.
    structural_depth : int, optional
        Structural-tuple depth. Defaults to 3.

    Returns
    -------
    tuple[VertexLabel, str]
        Seed vertex label and ``w*_c``.

    Raises
    ------
    isalhg.errors.BackendUnavailableError
        If ``pynauty`` is not installed.
    """
    return canonical_fingerprint(
        H,
        k=k,
        structural_depth=structural_depth,
        algorithm=CANONICAL_ORBIT_ALGORITHM,
        backend="python",
        orbit_oracle=PynautyOrbitOracle(),
    )


def canonical_string_rank(
    H: SparseHypergraph,
    *,
    k: int | None = None,
    structural_depth: int = 3,
) -> str:
    """Compute the rank-tie-broken canonical string of ``H``.

    The family's greedy walk with nauty's canonical rank replacing the raw edge
    id in the residual tie and the ``(label, rank)`` order replacing the
    label-respecting id order. Complete and isomorphism-invariant, but **not**
    ``w*_c``: it is a different canonical program.

    Parameters
    ----------
    H : SparseHypergraph
        Connected hypergraph.
    k : int or None, optional
        Pointer count; ``None`` uses ``required_k(H)``.
    structural_depth : int, optional
        Structural-tuple depth. Defaults to 3.

    Returns
    -------
    str
        The canonical string of the ``canonical_rank`` program.

    Raises
    ------
    isalhg.errors.BackendUnavailableError
        If ``pynauty`` is not installed.
    """
    from isalhg.iso_backends.canonical_order import canonical_ranks

    return canonical_string(
        H,
        k=k,
        structural_depth=structural_depth,
        algorithm=CANONICAL_RANK_ALGORITHM,
        backend="python",
        ranks=canonical_ranks(H),
    )


def canonical_fingerprint_rank(
    H: SparseHypergraph,
    *,
    k: int | None = None,
    structural_depth: int = 3,
) -> tuple[VertexLabel, str]:
    """Compute ``(seed label, canonical_rank string)`` of ``H``.

    Parameters
    ----------
    H : SparseHypergraph
        Connected hypergraph.
    k : int or None, optional
        Pointer count; ``None`` uses ``required_k(H)``.
    structural_depth : int, optional
        Structural-tuple depth. Defaults to 3.

    Returns
    -------
    tuple[VertexLabel, str]
        Seed vertex label and the ``canonical_rank`` string.

    Raises
    ------
    isalhg.errors.BackendUnavailableError
        If ``pynauty`` is not installed.
    """
    from isalhg.iso_backends.canonical_order import canonical_ranks

    return canonical_fingerprint(
        H,
        k=k,
        structural_depth=structural_depth,
        algorithm=CANONICAL_RANK_ALGORITHM,
        backend="python",
        ranks=canonical_ranks(H),
    )
