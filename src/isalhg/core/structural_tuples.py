"""Structural tuples ``xi`` (per-node) and ``eta`` (per-edge).

``xi_h(v)`` = number of neighbours of ``v`` at distance ``h``.
``eta_h(e)`` = sum over ``v in e`` of ``xi_h(v)``.

Used both for seed selection (max-lex ``xi`` over nodes) and for tie-breaking
during greedy H2S (max-lex ``eta`` over edges). Default depth 3 (inherited
from IsalGraph). Any deviation requires re-validating the canonical
completeness conjecture.
"""

from __future__ import annotations

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.types import EdgeId, NodeId

#: Default tuple depth; PI's seed proposal.
DEFAULT_DEPTH: int = 3


def xi(H: SparseHypergraph, v: NodeId, depth: int = DEFAULT_DEPTH) -> tuple[int, ...]:
    """Return ``(xi_1(v), ..., xi_depth(v))``."""
    raise NotImplementedError


def eta(H: SparseHypergraph, e: EdgeId, depth: int = DEFAULT_DEPTH) -> tuple[int, ...]:
    """Return ``(eta_1(e), ..., eta_depth(e))``."""
    raise NotImplementedError


def max_xi_nodes(H: SparseHypergraph, depth: int = DEFAULT_DEPTH) -> tuple[NodeId, ...]:
    """Return all nodes attaining the lexicographic maximum of ``xi``."""
    raise NotImplementedError
