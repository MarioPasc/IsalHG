"""Greedy H2S from a single max-xi seed -- fast heuristic.

Runs the greedy encoder from one max-xi seed (the lexicographically
smallest among the tied max-xi nodes) and returns the result without
aggregating across seeds. This is NOT canonical-invariant on
non-trivially-symmetric hypergraphs: two isomorphic inputs that have
multiple equally-good seeds can land on different greedy trajectories.

Used as a speed-only baseline in the algorithm-comparison study; the
benchmark protocol records ``iso_invariance_ok=False`` for the cells
where the heuristic departs from canonical.
"""

from __future__ import annotations

from isalhg.core.algorithms.base import H2SAlgorithm
from isalhg.core.algorithms.registry import register_algorithm
from isalhg.core.hypergraph_to_string import greedy_h2s
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.core.structural_tuples import DEFAULT_DEPTH, max_xi_nodes
from isalhg.errors import DisconnectedHypergraphError
from isalhg.types import TokenSequence


class GreedySingle(H2SAlgorithm):
    """Greedy H2S from one max-xi seed (smallest-id tiebreak)."""

    def __init__(self, *, k: int, structural_depth: int = DEFAULT_DEPTH) -> None:
        self._k = k
        self._structural_depth = structural_depth

    @property
    def name(self) -> str:
        return "greedy_single"

    @property
    def k(self) -> int:
        return self._k

    @property
    def structural_depth(self) -> int:
        return self._structural_depth

    def encode(self, H: SparseHypergraph) -> TokenSequence:
        if H.n_nodes == 0:
            return ()
        if not H.is_connected():
            raise DisconnectedHypergraphError(
                "GreedySingle requires a connected hypergraph (decision B11)"
            )
        seeds = max_xi_nodes(H, depth=self._structural_depth)
        seed = min(seeds)
        return greedy_h2s(H, seed_node=seed, k=self._k)


register_algorithm(
    "greedy_single",
    lambda k, d: GreedySingle(k=k, structural_depth=d),
)
