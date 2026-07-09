"""Exhaustive search over a WL-colour representative set, in-place state.

Speed heuristic. **Not iso-invariant, and not a canonical form.** Picks the
minimum-id vertex of each stable WL colour class as the seed set (rather than
every vertex, like :class:`~isalhg.core.algorithms.exhaustive.Exhaustive`),
runs the in-place greedy encoder from each representative, and returns the
lex-min token sequence.

Presentation dependence. The per-class representative is selected by raw
vertex id, and raw ids are not transported by an isomorphism, so the seed set
is not iso-equivariant and the output is a function of the vertex numbering.
This is the inadmissible pruning key of the completeness proof's
admissible-pruning lemma: a pruning key must be computable from iso-invariant
data of the state. Relabelling the vertices of the triangular prism changes
the emitted string -- pinned in
``test_pruned_exhaustive_is_not_relabel_invariant``.

Exactness condition. The output equals ``exhaustive``'s iff greedy H2S is
constant on every WL colour class. That is strictly stronger than "WL classes
are automorphism orbits": greedy H2S is not constant on an orbit either, since
its residual V-tie-break reads raw edge ids, so two seeds of one orbit can
yield different strings. On the vertex-transitive prism -- a single WL class,
a single orbit -- this variant already disagrees with ``exhaustive``
(``test_pruned_exhaustive_differs_from_exhaustive_on_vertex_transitive``).

Consequently this variant defines no canonical form on isomorphism classes and
must never feed ``d_I``. Use ``canonical`` for any isomorphism or
metric-space claim. Retained as a speed heuristic and as part of the
iso-benchmark preprint's measurement apparatus.
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
    """Exhaustive H2S over min-id WL-class seeds. Speed heuristic, not iso-invariant."""

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
