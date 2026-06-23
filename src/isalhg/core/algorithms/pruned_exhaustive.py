"""Exhaustive search over a WL-orbit representative set, in-place state.

Picks one vertex per stable WL colour class as the seed set (rather
than every vertex, like :class:`~isalhg.core.algorithms.exhaustive.Exhaustive`),
then runs the in-place greedy encoder from each representative and
returns the lex-min token sequence.

Canonicality. WL colour-refinement is an upper bound on automorphism
orbits: vertices in the same automorphism orbit always share a WL
colour, but the converse may fail (two vertices with the same WL
colour can lie in distinct orbits). When the converse holds for ``H``
the output equals ``exhaustive``'s output (full canonical); when it
fails the algorithm may miss the orbit whose representative would have
produced the lex-min completion. Iso-invariance is preserved
regardless, because the seed set transforms consistently under any
isomorphism (the orbits and the per-orbit "min vertex ID" choice are
iso-equivariant when composed with the same isomorphism on the output
side).

The ``algorithm_benchmark`` protocol's cross-equality with
``greedy_min`` is the empirical test of WL-as-orbits on the cohort.
"""

from __future__ import annotations

from isalhg.core.algorithms.base import H2SAlgorithm
from isalhg.core.algorithms.registry import register_algorithm
from isalhg.core.hypergraph_to_string import greedy_h2s
from isalhg.core.hypergraph_wl import wl_hash
from isalhg.core.instructions import sequence_sort_key
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.core.structural_tuples import DEFAULT_DEPTH
from isalhg.errors import DisconnectedHypergraphError
from isalhg.types import TokenSequence


class PrunedExhaustive(H2SAlgorithm):
    """Exhaustive H2S over WL-min seeds with WL-pruned V-branch permutations."""

    def __init__(self, *, k: int, structural_depth: int = DEFAULT_DEPTH) -> None:
        self._k = k
        self._structural_depth = structural_depth

    @property
    def name(self) -> str:
        return "pruned_exhaustive"

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
                "PrunedExhaustive requires a connected hypergraph (decision B11)"
            )
        colours = wl_hash(H)
        seen_orbits: dict[int, int] = {}
        for v in H.nodes():
            c = colours[v]
            if c not in seen_orbits:
                seen_orbits[c] = v
        seeds = list(seen_orbits.values())
        candidates: list[TokenSequence] = [
            greedy_h2s(H, seed_node=v, k=self._k, inplace=True) for v in seeds
        ]
        return min(candidates, key=sequence_sort_key)


register_algorithm(
    "pruned_exhaustive",
    lambda k, d: PrunedExhaustive(k=k, structural_depth=d),
)
