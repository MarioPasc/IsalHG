"""Greedy H2S from every max-xi seed; emit lex-min result.

This is the variant the canonical entry point uses.
"""

from __future__ import annotations

from isalhg.core.algorithms.base import H2SAlgorithm
from isalhg.core.hypergraph_to_string import greedy_h2s
from isalhg.core.instructions import sequence_sort_key
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.core.structural_tuples import DEFAULT_DEPTH, max_xi_nodes
from isalhg.errors import DisconnectedHypergraphError
from isalhg.types import TokenSequence


class GreedyMin(H2SAlgorithm):
    """Greedy H2S over every max-xi seed; take the lex-min token tuple."""

    def __init__(self, *, k: int, structural_depth: int = DEFAULT_DEPTH) -> None:
        self._k = k
        self._structural_depth = structural_depth

    @property
    def name(self) -> str:
        return "greedy_min"

    @property
    def k(self) -> int:
        return self._k

    @property
    def structural_depth(self) -> int:
        return self._structural_depth

    def encode(self, H: SparseHypergraph) -> TokenSequence:
        """Encode ``H`` by running greedy from every max-xi seed and taking lex-min.

        Raises
        ------
        DisconnectedHypergraphError
            If ``H`` is not connected (decision B11).
        """
        if H.n_nodes == 0:
            return ()
        if not H.is_connected():
            raise DisconnectedHypergraphError(
                "GreedyMin requires a connected hypergraph (decision B11)"
            )
        seeds = max_xi_nodes(H, depth=self._structural_depth)
        candidates: list[TokenSequence] = [greedy_h2s(H, seed_node=s, k=self._k) for s in seeds]
        return min(candidates, key=sequence_sort_key)
