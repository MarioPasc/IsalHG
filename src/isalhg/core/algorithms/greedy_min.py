"""Greedy H2S from every max-xi seed; emit lex-min result.

This is the variant the canonical entry point uses.
"""

from __future__ import annotations

from isalhg.core.algorithms.base import H2SAlgorithm
from isalhg.core.sparse_hypergraph import SparseHypergraph


class GreedyMin(H2SAlgorithm):
    """Greedy H2S over every max-xi seed; take the lex-min string."""

    def __init__(self, *, k: int, structural_depth: int = 3) -> None:
        self._k = k
        self._structural_depth = structural_depth

    @property
    def name(self) -> str:
        return "greedy_min"

    def encode(self, H: SparseHypergraph) -> str:
        raise NotImplementedError
