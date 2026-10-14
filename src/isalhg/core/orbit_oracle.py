"""Stabiliser-orbit oracle protocol for the tie-complete search.

The tie-complete encoder (``tie_branch=True`` in
:mod:`isalhg.core.hypergraph_to_string`) branches over the full residual tie
set and, per tied edge, over every label-respecting ordering of its new
vertices. On symmetric inputs that branch set is dominated by automorphic
duplicates: a star with ``q`` interchangeable leaves is explored ``q!`` times
at the root alone.

Proposition (orbit pruning returns ``w*_c``) licenses removing exactly those
duplicates. Write ``sigma`` for a search state, ``dom mu`` for the placed
input vertices in creation order, and
``G_sigma := {psi in Aut(H) : psi(v) = v for all v in dom mu}``. If two tied
edges lie in the same ``G_sigma``-orbit, the two sub-searches return equal
completions, so the shortlex minimum over the tie set equals the minimum over
one representative per orbit; likewise for the orderings of ``U(e)`` under
``G_{sigma,e} := G_sigma cap Stab_set(e)``, and for the seeds under
``Aut(H)``. The pruned search is therefore *value-preserving*: it returns the
frozen ``w*_c`` bit for bit, which is what distinguishes it from a tie-set
*refinement* (also complete, but a different canonical form -- forbidden by
D-TA2).

The stabiliser must be recomputed at **every** tie: it shrinks as the search
descends and may never be inherited from the root.

This module holds only the interface, because ``core`` is stdlib-only. The
implementation that actually computes the groups -- ``autgrp`` on the Levi
graph with the placed vertices individualised -- lives in
:mod:`isalhg.iso_backends.orbit_oracle`, where ``pynauty`` may be imported.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.types import EdgeId, NodeId


@runtime_checkable
class OrbitOracle(Protocol):
    """Reduce a branch set to one representative per stabiliser orbit.

    Every method receives the candidate sequence the unpruned search would
    branch over and returns a subsequence holding one element per orbit. The
    representative is chosen deterministically as the **first** element of the
    input sequence lying in that orbit, and the returned list preserves the
    input order. Any representative is value-equivalent, so the choice cannot
    affect ``w*_c``; fixing it keeps the pruned search reproducible.

    An implementation is always free to return its input unchanged -- that is
    the unpruned search, which is correct but slow (see
    :class:`TrivialOrbitOracle`).
    """

    def seed_representatives(self, H: SparseHypergraph, seeds: Sequence[NodeId]) -> list[NodeId]:
        """Return one seed per ``Aut(H)``-orbit of ``seeds``.

        Parameters
        ----------
        H : SparseHypergraph
            The hypergraph being encoded.
        seeds : Sequence[NodeId]
            The iso-invariant seed set, in the order the seed loop would visit.

        Returns
        -------
        list[NodeId]
            One representative per orbit, in input order.
        """
        ...

    def edge_representatives(
        self,
        H: SparseHypergraph,
        placed: Sequence[NodeId],
        tied_edges: Sequence[EdgeId],
    ) -> list[EdgeId]:
        """Return one edge per ``G_sigma``-orbit of ``tied_edges``.

        Parameters
        ----------
        H : SparseHypergraph
            The hypergraph being encoded.
        placed : Sequence[NodeId]
            ``dom mu`` -- the input-hypergraph node ids already mapped, in
            creation (output-id) order.
        tied_edges : Sequence[EdgeId]
            The residual tie set ``T(sigma)``, in the order the unpruned
            search would branch over it.

        Returns
        -------
        list[EdgeId]
            One representative per orbit, in input order.
        """
        ...

    def ordering_representatives(
        self,
        H: SparseHypergraph,
        placed: Sequence[NodeId],
        edge: EdgeId,
        orderings: Sequence[tuple[NodeId, ...]],
    ) -> list[tuple[NodeId, ...]]:
        """Return one ordering per ``G_{sigma,e}``-orbit of ``orderings``.

        Parameters
        ----------
        H : SparseHypergraph
            The hypergraph being encoded.
        placed : Sequence[NodeId]
            ``dom mu`` -- the placed input node ids, in creation order.
        edge : EdgeId
            The tied edge already committed to at this branch.
        orderings : Sequence[tuple[NodeId, ...]]
            The label-respecting orderings of the unplaced members ``U(e)``.

        Returns
        -------
        list[tuple[NodeId, ...]]
            One representative per orbit, in input order.
        """
        ...


class TrivialOrbitOracle:
    """The identity oracle: every candidate is its own orbit representative.

    Returns each branch set unchanged, so the search it drives is the unpruned
    tie-complete search. It exists to pin that the oracle *hook* is
    value-neutral -- any difference between the hook-off and
    ``TrivialOrbitOracle`` outputs is a bug in the plumbing, not in the group
    theory.
    """

    def seed_representatives(self, H: SparseHypergraph, seeds: Sequence[NodeId]) -> list[NodeId]:
        """Return ``seeds`` unchanged."""
        return list(seeds)

    def edge_representatives(
        self,
        H: SparseHypergraph,
        placed: Sequence[NodeId],
        tied_edges: Sequence[EdgeId],
    ) -> list[EdgeId]:
        """Return ``tied_edges`` unchanged."""
        return list(tied_edges)

    def ordering_representatives(
        self,
        H: SparseHypergraph,
        placed: Sequence[NodeId],
        edge: EdgeId,
        orderings: Sequence[tuple[NodeId, ...]],
    ) -> list[tuple[NodeId, ...]]:
        """Return ``orderings`` unchanged."""
        return list(orderings)
