"""Greedy H2S from a single max-xi seed.

Out of scope for Phase 1; the canonical entry point uses
:class:`isalhg.core.algorithms.greedy_min.GreedyMin` which iterates over
all max-xi seeds.
"""

from __future__ import annotations

from isalhg.core.algorithms.base import H2SAlgorithm
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.types import TokenSequence


class GreedySingle(H2SAlgorithm):
    """Greedy H2S from one max-xi seed."""

    def __init__(self, *, k: int, structural_depth: int = 3) -> None:
        self._k = k
        self._structural_depth = structural_depth

    @property
    def name(self) -> str:
        return "greedy_single"

    def encode(self, H: SparseHypergraph) -> TokenSequence:
        raise NotImplementedError("GreedySingle is out of scope for Phase 1")
