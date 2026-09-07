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
from dataclasses import dataclass
from typing import Any, TypeVar

from isalhg.core.backends import Backend
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


@dataclass
class _HypergraphCache:
    """Everything :class:`PynautyOrbitOracle` memoises for one hypergraph.

    Holding the hypergraph itself keeps the ``id()`` key from being recycled,
    and bundling the generator sets here means they are dropped together with
    the entry rather than outliving the object they describe.
    """

    hypergraph: SparseHypergraph
    levi: LeviGraph
    adjacency: dict[int, list[int]]
    groups: dict[tuple[NodeId, ...], tuple[tuple[tuple[int, ...], ...], list[int]]]


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

    One instance may serve many hypergraphs. Everything cached for a hypergraph
    -- its Levi graph, the adjacency dict, and the per-state generator sets --
    hangs off a single :class:`_HypergraphCache` entry that also holds a
    reference to the hypergraph itself. Two properties follow, and both matter:
    the ``id()`` key cannot be recycled while the entry lives, and evicting the
    entry drops its generator sets with it, so a state's group can never be
    served from a different hypergraph that happened to reuse the address.

    Attributes
    ----------
    autgrp_calls : int
        Number of ``pynauty.autgrp`` invocations made so far. Diagnostic only;
        it does not affect any returned value.
    """

    def __init__(self) -> None:
        self._cache: dict[int, _HypergraphCache] = {}
        self.autgrp_calls: int = 0

    # -- graph construction -------------------------------------------------

    def _entry(self, H: SparseHypergraph) -> _HypergraphCache:
        key = id(H)
        hit = self._cache.get(key)
        if hit is not None and hit.hypergraph is H:
            return hit
        levi = to_levi(H)
        adjacency: dict[int, list[int]] = {node: [] for node in range(levi.n_nodes)}
        for u, v in levi.edges:
            adjacency[u].append(v)
            adjacency[v].append(u)
        if len(self._cache) >= _CACHE_LIMIT:
            self._cache.clear()
        entry = _HypergraphCache(hypergraph=H, levi=levi, adjacency=adjacency, groups={})
        self._cache[key] = entry
        return entry

    def _levi_of(self, H: SparseHypergraph) -> tuple[LeviGraph, dict[int, list[int]]]:
        entry = self._entry(H)
        return entry.levi, entry.adjacency

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

    def _state_group(
        self, H: SparseHypergraph, placed: Sequence[NodeId]
    ) -> tuple[tuple[tuple[int, ...], ...], list[int]]:
        """``(generators, orbits)`` of ``G_sigma``, memoised per placed prefix.

        Both consumers at a state -- the tie-set orbits and the short-circuit
        that skips the ordering oracle when ``G_sigma`` is trivial -- need the
        same group, so it is computed once per state rather than once per
        consumer.

        This memoises identical *states*; it never inherits a group from an
        ancestor state. The proof's recursion remark is explicit that ``G_sigma``
        shrinks as the search descends, so a coarser ancestor group would prune
        branches that are not automorphic duplicates.
        """
        entry = self._entry(H)
        key = tuple(placed)
        hit = entry.groups.get(key)
        if hit is not None:
            return hit
        group = self._autgrp(H, list(placed))
        if len(entry.groups) >= _CACHE_LIMIT:
            entry.groups.clear()
        entry.groups[key] = group
        return group

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
        _generators, orbits = self._state_group(H, ())
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
        offset = self._entry(H).levi.n_vertex_nodes
        _generators, orbits = self._state_group(H, placed)
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
        state_generators, _orbits = self._state_group(H, placed)
        if not state_generators:
            return list(orderings)
        levi = self._entry(H).levi
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
    backend: Backend | None = None,
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
    backend : {"cpp", "python"} or None, optional
        Engine running the pruned search. ``None`` (the default) resolves to
        :data:`isalhg.core.backends.DEFAULT_BACKEND`, i.e. ``"cpp"`` when the
        extension is importable. The two backends return the identical
        string; the oracle itself stays in Python either way.

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
        backend=backend,
        orbit_oracle=PynautyOrbitOracle(),
    )


def canonical_fingerprint_orbit(
    H: SparseHypergraph,
    *,
    k: int | None = None,
    structural_depth: int = 3,
    backend: Backend | None = None,
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
    backend : {"cpp", "python"} or None, optional
        Engine running the pruned search; ``None`` resolves to
        :data:`isalhg.core.backends.DEFAULT_BACKEND`.

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
        backend=backend,
        orbit_oracle=PynautyOrbitOracle(),
    )


def canonical_string_rank(
    H: SparseHypergraph,
    *,
    k: int | None = None,
    structural_depth: int = 3,
    backend: Backend | None = None,
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
    backend : {"cpp", "python"} or None, optional
        Implementation to use. ``None`` (default) takes
        :data:`isalhg.core.backends.DEFAULT_BACKEND`, i.e. ``"cpp"`` when the
        extension is importable. The two backends return the identical string;
        only ``"cpp"`` is feasible above arity 4.

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
        backend=backend,
        ranks=canonical_ranks(H),
    )


def canonical_fingerprint_rank(
    H: SparseHypergraph,
    *,
    k: int | None = None,
    structural_depth: int = 3,
    backend: Backend | None = None,
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
    backend : {"cpp", "python"} or None, optional
        Implementation to use; ``None`` (default) takes
        :data:`isalhg.core.backends.DEFAULT_BACKEND`.

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
        backend=backend,
        ranks=canonical_ranks(H),
    )
