"""Exhaustive H2S over every node as seed; lex-min over results.

Brute-force baseline: ignores the max-xi seed-selection heuristic and
runs greedy H2S from every vertex of ``H``. Canonical by construction
(any seed strategy is a subset of "all seeds"), but the lex-min over
``n`` greedy runs is expensive on large or symmetric hypergraphs.
"""

from __future__ import annotations

from isalhg.core.algorithms.base import H2SAlgorithm
from isalhg.core.algorithms.registry import register_algorithm
from isalhg.core.hypergraph_to_string import greedy_h2s
from isalhg.core.instructions import sequence_sort_key
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.core.structural_tuples import DEFAULT_DEPTH
from isalhg.errors import DisconnectedHypergraphError
from isalhg.types import TokenSequence


class Exhaustive(H2SAlgorithm):
    """Greedy H2S over every node as seed; take the lex-min token tuple."""

    def __init__(self, *, k: int, structural_depth: int = DEFAULT_DEPTH) -> None:
        self._k = k
        self._structural_depth = structural_depth

    @property
    def name(self) -> str:
        return "exhaustive"

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
                "Exhaustive requires a connected hypergraph (decision B11)"
            )
        candidates: list[TokenSequence] = [greedy_h2s(H, seed_node=v, k=self._k) for v in H.nodes()]
        return min(candidates, key=sequence_sort_key)


register_algorithm(
    "exhaustive",
    lambda k, d: Exhaustive(k=k, structural_depth=d),
)
