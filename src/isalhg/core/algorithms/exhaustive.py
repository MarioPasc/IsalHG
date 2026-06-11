"""Exhaustive H2S over every node as a candidate seed.

Brute-force baseline for completeness ablations: ignores the max-xi seeding
heuristic and runs greedy H2S from every node. Out of scope for Phase 1.
"""

from __future__ import annotations

from isalhg.core.algorithms.base import H2SAlgorithm
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.types import TokenSequence


class Exhaustive(H2SAlgorithm):
    """Greedy H2S over every node; take the lex-min string."""

    def __init__(self, *, k: int) -> None:
        self._k = k

    @property
    def name(self) -> str:
        return "exhaustive"

    def encode(self, H: SparseHypergraph) -> TokenSequence:
        raise NotImplementedError("Exhaustive is out of scope for Phase 1")
