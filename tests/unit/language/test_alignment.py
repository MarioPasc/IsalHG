"""Alignments carry honest isomorphisms, and edit paths have decodable interiors.

Two independent claims live here.

*The node map is real.*  ``Alignment.node_map`` is checked by applying it: the
second remainder permuted by the map must equal the first, as objects.  This is
run on 200 random near-neighbour pairs and on a hand-built case whose remainder
is symmetric, where the naive shortcut --- composing the canonical ranks of
``K`` and ``K2`` themselves --- provably gives a non-isomorphism.  That case is
the regression pin for `DESIGN.md` G1: a rank vector is canonical only up to an
automorphism, so ranks may be composed across two objects only when those
objects are isomorphic, which the remainders are and the originals are not.

*The interior is a sequence of knowledge bases.*  ``alignment_path`` returns the
words strictly between two endpoints of one optimal Levenshtein alignment; the
tests check the length, the one-edit-per-step property, that the reconstruction
lands on the second endpoint, and that every interior word decodes.
"""

from __future__ import annotations

import random

import pytest

from isalhg.core.fact_word import decode_fact_word
from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.language.alignment import alignment_path
from isalhg.language.reach import (
    ReachError,
    alignments,
    fact_key_of,
    node_map_from_ranks,
    reach,
    remove_facts,
)
from isalhg.metric_space.distances.fact_levenshtein import fact_word, word_distance
from tests.unit.language._builders import (
    DEFAULT_PREDS,
    DEFAULT_TYPES,
    random_kb,
    with_inserted_fact,
    with_substituted_fact,
)

pytestmark = pytest.mark.unit

pytest.importorskip("pynauty")
pytest.importorskip("rapidfuzz")


def symmetric_path_kb() -> SparseHypergraph:
    """A 4-constant path whose two end facts are exchanged by an automorphism.

    Facts ``{0,1}``, ``{1,2}``, ``{2,3}`` over four constants of one type.
    Deleting the first leaves ``1-2-3`` with ``0`` isolated; deleting the last
    leaves ``0-1-2`` with ``3`` isolated.  The two remainders are isomorphic but
    not equal, so the identity --- which is exactly what composing the two
    objects' own canonical ranks gives here, the object being the same one ---
    is not an isomorphism between them.
    """
    return SparseHypergraph(
        n_nodes=4,
        hyperedges=[frozenset({0, 1}), frozenset({1, 2}), frozenset({2, 3})],
        n_vertex_labels=1,
        n_edge_labels=1,
        vertex_labels=[0, 0, 0, 0],
        edge_labels=[0, 0, 0],
    )


class TestNodeMapIsAnIsomorphism:
    N_CASES = 200

    def test_applying_the_map_reproduces_the_remainder(self) -> None:
        rng = random.Random(41)
        checked = 0
        verified = 0
        with_deletions = 0
        while checked < self.N_CASES:
            K = random_kb(rng, n_lo=4, n_hi=7, m_lo=3, m_hi=5, arity_hi=3)
            other: SparseHypergraph | None
            choice = rng.randrange(3)
            if choice == 0:
                other = with_inserted_fact(rng, K, arity_hi=3)
            elif choice == 1:
                other = with_substituted_fact(rng, K, arity_hi=3)
            else:
                sigma = list(range(K.n_nodes))
                rng.shuffle(sigma)
                other = permute(K, sigma)
            if other is None:
                continue
            checked += 1
            for alignment in alignments(K, other, 2):
                left = remove_facts(K, alignment.deleted_from_k)
                right = remove_facts(other, alignment.deleted_from_k2)
                assert permute(right, alignment.node_map) == left
                verified += 1
                if alignment.deleted_from_k or alignment.deleted_from_k2:
                    with_deletions += 1
        assert verified >= self.N_CASES
        assert with_deletions >= self.N_CASES // 4

    def test_naive_rank_transport_fails_on_a_symmetric_remainder(self) -> None:
        K = symmetric_path_kb()
        found = [
            alignment
            for alignment in alignments(K, K, 2)
            if alignment.deleted_from_k == (0,) and alignment.deleted_from_k2 == (2,)
        ]
        assert len(found) == 1
        alignment = found[0]

        left = remove_facts(K, (0,))
        right = remove_facts(K, (2,))
        assert left != right
        assert fact_key_of(left) == fact_key_of(right)

        naive = node_map_from_ranks(_ranks(K), _ranks(K))
        assert naive == tuple(range(K.n_nodes))
        assert permute(right, naive) != left

        assert alignment.node_map != naive
        assert permute(right, alignment.node_map) == left

    def test_alignment_at_radius_zero_is_isomorphism_only(self) -> None:
        rng = random.Random(43)
        K = random_kb(rng)
        sigma = list(range(K.n_nodes))
        rng.shuffle(sigma)
        found = alignments(K, permute(K, sigma), 0)
        assert len(found) == 1
        assert found[0].deleted_from_k == ()
        assert found[0].deleted_from_k2 == ()

    def test_incompatible_pair_has_no_alignment(self) -> None:
        rng = random.Random(47)
        K = random_kb(rng, n_lo=5, n_hi=5)
        wider = random_kb(rng, n_lo=6, n_hi=6)
        assert alignments(K, wider, 2) == []

    def test_result_is_sorted_and_deterministic(self) -> None:
        rng = random.Random(53)
        K = random_kb(rng, n_lo=5, n_hi=5, m_lo=4, m_hi=4)
        grown = with_inserted_fact(rng, K)
        assert grown is not None
        first = alignments(K, grown, 2)
        assert first == alignments(K, grown, 2)
        keys = [(a.deleted_from_k, a.deleted_from_k2) for a in first]
        assert keys == sorted(keys)

    def test_per_side_budget_widens_the_family(self) -> None:
        """Two siblings two insertions from a shared source are invisible to a total budget.

        This is the case the consensus depends on: ``K_i`` and ``K_j`` are each
        ``t = 2`` insertions from the source, so their reach is 4 and no
        alignment survives ``|A| + |B| <= 2``, while the per-side family
        ``|A| <= 2, |B| <= 2`` contains the pair that exposes the source.
        """
        rng = random.Random(59)
        source = random_kb(rng, n_lo=6, n_hi=6, m_lo=4, m_hi=4)
        siblings: list[SparseHypergraph] = []
        for _ in range(2):
            grown: SparseHypergraph | None = source
            for _ in range(2):
                assert grown is not None
                grown = with_inserted_fact(rng, grown)
            assert grown is not None
            siblings.append(grown)
        left, right = siblings
        if reach(left, right, r_max=2) is not None:
            pytest.skip("the two siblings landed within radius 2 of each other")
        assert alignments(left, right, 2) == []
        widened = alignments(left, right, 4, max_per_side=2)
        assert any(len(a.deleted_from_k) == 2 and len(a.deleted_from_k2) == 2 for a in widened)
        for alignment in widened:
            assert permute(
                remove_facts(right, alignment.deleted_from_k2), alignment.node_map
            ) == remove_facts(left, alignment.deleted_from_k)

    def test_negative_budgets_raise(self) -> None:
        rng = random.Random(61)
        K = random_kb(rng)
        with pytest.raises(ReachError):
            alignments(K, K, -1)
        with pytest.raises(ReachError):
            alignments(K, K, 2, max_per_side=-1)


def _ranks(H: SparseHypergraph) -> tuple[int, ...]:
    from isalhg.iso_backends.canonical_order import canonical_ranks

    return canonical_ranks(H)


class TestAlignmentPath:
    def test_length_matches_the_distance(self) -> None:
        rng = random.Random(67)
        for _ in range(40):
            first = fact_word(random_kb(rng, n_lo=4, n_hi=7, m_lo=2, m_hi=5))
            second = fact_word(random_kb(rng, n_lo=4, n_hi=7, m_lo=2, m_hi=5))
            distance = word_distance(first, second)
            interior = alignment_path(first, second)
            assert len(interior) == max(distance - 1, 0)

    def test_each_step_is_one_edit_and_ends_at_the_target(self) -> None:
        rng = random.Random(71)
        for _ in range(40):
            first = fact_word(random_kb(rng, n_lo=4, n_hi=7, m_lo=2, m_hi=5))
            second = fact_word(random_kb(rng, n_lo=4, n_hi=7, m_lo=2, m_hi=5))
            chain = [first, *alignment_path(first, second), second]
            for before, after in zip(chain, chain[1:], strict=False):
                assert word_distance(before, after) == 1

    def test_every_interior_word_decodes(self) -> None:
        rng = random.Random(73)
        decoded_total = 0
        for _ in range(40):
            left = random_kb(rng, n_lo=4, n_hi=7, m_lo=2, m_hi=5)
            right = random_kb(rng, n_lo=4, n_hi=7, m_lo=2, m_hi=5)
            for word in alignment_path(fact_word(left), fact_word(right)):
                decoded, _ = decode_fact_word(word, n_types=DEFAULT_TYPES, n_preds=DEFAULT_PREDS)
                assert isinstance(decoded, SparseHypergraph)
                decoded_total += 1
        assert decoded_total > 0

    def test_equal_and_adjacent_words_have_empty_interiors(self) -> None:
        rng = random.Random(79)
        H = random_kb(rng)
        word = fact_word(H)
        assert alignment_path(word, word) == []
        assert alignment_path(word, word[:-1]) == []
