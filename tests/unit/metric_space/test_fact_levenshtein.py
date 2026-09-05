"""Unit tests for ``fact_rank`` and the three displaced-addressing ablation arms."""

from __future__ import annotations

import random

import pytest

from isalhg.core.fact_word import encode_fact_word
from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.errors import DistanceComputationError
from isalhg.iso_backends.canonical_order import canonical_ranks
from isalhg.metric_space.distances.fact_addressing_ablations import (
    ARM_DEGREE_KEY,
    ARM_LOCAL_COLOUR,
    ARM_LOCAL_KEY,
    FactAddressingAblation,
    addressed_word,
    key_addresses,
    key_degree,
    key_local_key,
)
from isalhg.metric_space.distances.fact_levenshtein import (
    FactRankLevenshtein,
    fact_word,
    word_distance,
)
from isalhg.metric_space.registry import get_distance

pytestmark = pytest.mark.unit

pytest.importorskip("pynauty")
pytest.importorskip("rapidfuzz")

ARMS = [ARM_LOCAL_COLOUR, ARM_LOCAL_KEY, ARM_DEGREE_KEY]
REGISTERED = [
    "fact_rank",
    "fact_rank_roles",
    "fact_local_colour",
    "fact_local_key",
    "fact_degree_key",
]


def random_kb(rng: random.Random, *, n_max: int = 8) -> SparseHypergraph:
    """A small labelled knowledge base."""
    n = rng.randint(3, n_max)
    m = rng.randint(2, 6)
    seen: set[tuple[int, frozenset[int]]] = set()
    edges: list[set[int]] = []
    labels: list[int] = []
    for _ in range(m * 4):
        if len(edges) == m:
            break
        members = frozenset(rng.sample(range(n), rng.randint(2, min(4, n))))
        label = rng.randrange(2)
        if (label, members) in seen:
            continue
        seen.add((label, members))
        edges.append(set(members))
        labels.append(label)
    return SparseHypergraph(
        n_nodes=n,
        hyperedges=edges,
        n_vertex_labels=2,
        n_edge_labels=2,
        vertex_labels=[rng.randrange(2) for _ in range(n)],
        edge_labels=labels,
    )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class TestRegistry:
    @pytest.mark.parametrize("name", REGISTERED)
    def test_resolves_and_names_itself(self, name: str) -> None:
        assert get_distance(name).name == name

    def test_all_five_are_listed(self) -> None:
        from isalhg.metric_space.registry import available_distances

        assert set(REGISTERED) <= set(available_distances())

    def test_unknown_arm_is_refused(self) -> None:
        with pytest.raises(DistanceComputationError, match="unknown fact-addressing arm"):
            FactAddressingAblation("nonsense")


# ---------------------------------------------------------------------------
# fact_word and word_distance
# ---------------------------------------------------------------------------


class TestFactWord:
    def test_composes_canonical_ranks_with_the_encoder(self, sts_9: SparseHypergraph) -> None:
        assert fact_word(sts_9) == encode_fact_word(sts_9, canonical_ranks(sts_9))

    def test_carries_roles_through(self) -> None:
        H = SparseHypergraph(
            n_nodes=3,
            hyperedges=[{0, 1}, {1, 2}],
            n_vertex_labels=1,
            n_edge_labels=1,
            vertex_labels=[0, 0, 0],
            edge_labels=[0, 0],
        )
        roles = {0: {0: 4, 1: 9}, 1: {1: 4, 2: 9}}
        facts = [t for t in fact_word(H, roles) if t[0] == "F"]
        assert all(isinstance(operand, tuple) for t in facts for operand in t[2])


class TestWordDistance:
    def test_identity_of_indiscernibles(self, fano_plane: SparseHypergraph) -> None:
        assert word_distance(fact_word(fano_plane), fact_word(fano_plane)) == 0

    def test_symmetry_and_triangle(self) -> None:
        rng = random.Random(5)
        corpus = [fact_word(random_kb(rng, n_max=6)) for _ in range(12)]
        for i, a in enumerate(corpus):
            for j, b in enumerate(corpus):
                assert word_distance(a, b) == word_distance(b, a)
                for c in corpus[max(0, i + j - 3) :]:
                    assert word_distance(a, b) <= word_distance(a, c) + word_distance(c, b)

    def test_counts_tokens_not_characters(self) -> None:
        # Two words differing in one token: a single substitution, whatever the
        # tokens' internal size.
        w1 = (("T", 0), ("F", 0, (0, 1)))
        w2 = (("T", 0), ("F", 0, (0, 1, 2, 3, 4, 5)))
        assert word_distance(w1, w2) == 1

    def test_empty_words(self) -> None:
        assert word_distance((), ()) == 0
        assert word_distance((), (("T", 0),)) == 1


# ---------------------------------------------------------------------------
# The single-fact insertion -- the property the article rests on
# ---------------------------------------------------------------------------


class TestSingleFactInsertion:
    """One fact added over existing constants costs exactly one edit.

    Found by a fixed-seed search over random labelled knowledge bases for a
    candidate whose addition leaves ``canonical_ranks`` untouched, then frozen
    here. The rank map being unchanged is what makes the two words share their
    type prefix and all previous fact tokens, so the second word is the first
    with one token inserted.
    """

    N = 7
    EDGES = [{1, 3, 6}, {3, 5, 6}, {0, 6}, {0, 4, 6}, {2, 4, 5}]
    EDGE_LABELS = [1, 0, 1, 1, 1]
    VERTEX_LABELS = [0, 1, 1, 0, 0, 0, 0]
    NEW_FACT = (0, {1, 2})
    EXPECTED_RANKS = (2, 6, 5, 4, 1, 3, 0)

    def _build(self, *, with_new_fact: bool) -> SparseHypergraph:
        edges = [set(e) for e in self.EDGES]
        labels = list(self.EDGE_LABELS)
        if with_new_fact:
            label, members = self.NEW_FACT
            edges.append(set(members))
            labels.append(label)
        return SparseHypergraph(
            n_nodes=self.N,
            hyperedges=edges,
            n_vertex_labels=2,
            n_edge_labels=2,
            vertex_labels=list(self.VERTEX_LABELS),
            edge_labels=labels,
        )

    def test_the_fixture_is_connected(self) -> None:
        assert self._build(with_new_fact=False).is_connected()
        assert self._build(with_new_fact=True).is_connected()

    def test_the_canonical_order_is_unchanged(self) -> None:
        before = self._build(with_new_fact=False)
        after = self._build(with_new_fact=True)
        assert canonical_ranks(before) == self.EXPECTED_RANKS
        assert canonical_ranks(after) == self.EXPECTED_RANKS

    def test_distance_is_exactly_one(self) -> None:
        before, after = self._build(with_new_fact=False), self._build(with_new_fact=True)
        assert word_distance(fact_word(before), fact_word(after)) == 1
        assert FactRankLevenshtein().pairwise(before, after) == 1.0

    def test_the_edit_is_a_single_insertion(self) -> None:
        w1, w2 = (
            fact_word(self._build(with_new_fact=False)),
            fact_word(self._build(with_new_fact=True)),
        )
        assert len(w2) == len(w1) + 1
        inserted = [t for t in w2 if t not in w1]
        assert len(inserted) == 1
        label, members = self.NEW_FACT
        ranks = self.EXPECTED_RANKS
        assert inserted[0] == ("F", label, tuple(sorted(ranks[v] for v in members)))


# ---------------------------------------------------------------------------
# The distance object
# ---------------------------------------------------------------------------


class TestFactRankLevenshtein:
    def test_zero_iff_isomorphic(
        self,
        iso_pair_small: tuple[SparseHypergraph, SparseHypergraph, list[int]],
        non_iso_pair_small: tuple[SparseHypergraph, SparseHypergraph],
    ) -> None:
        H1, H2, _ = iso_pair_small
        distance = FactRankLevenshtein()
        assert distance.pairwise(H1, H2) == 0.0
        A, B = non_iso_pair_small
        assert distance.pairwise(A, B) > 0.0

    def test_invariant_under_random_permutations(self) -> None:
        rng = random.Random(17)
        distance = FactRankLevenshtein()
        for _ in range(40):
            H = random_kb(rng)
            sigma = list(range(H.n_nodes))
            rng.shuffle(sigma)
            assert distance.pairwise(H, permute(H, sigma)) == 0.0

    def test_matrix_agrees_with_pairwise(self) -> None:
        rng = random.Random(19)
        corpus = [random_kb(rng, n_max=6) for _ in range(8)]
        distance = FactRankLevenshtein()
        matrix = distance.matrix(corpus)
        assert matrix.shape == (8, 8)
        for i in range(8):
            assert matrix[i, i] == 0.0
            for j in range(i + 1, 8):
                assert matrix[i, j] == matrix[j, i] == distance.pairwise(corpus[i], corpus[j])

    def test_empty_corpus(self) -> None:
        assert FactRankLevenshtein().matrix([]).shape == (0, 0)

    def test_fingerprint_is_the_word(self, sts_9: SparseHypergraph) -> None:
        assert FactRankLevenshtein().fingerprint(sts_9) == fact_word(sts_9)


class TestRolesArmRefusesHypergraphOnlyCalls:
    """The roles arm must not silently degrade into the primary arm."""

    @pytest.mark.parametrize("call", ["pairwise", "matrix", "fingerprint"])
    def test_refuses(self, call: str, fano_plane: SparseHypergraph) -> None:
        distance = FactRankLevenshtein(roles=True)
        with pytest.raises(DistanceComputationError, match="roles live"):
            if call == "pairwise":
                distance.pairwise(fano_plane, fano_plane)
            elif call == "matrix":
                distance.matrix([fano_plane])
            else:
                distance.fingerprint(fano_plane)

    def test_the_roles_word_differs_from_the_role_free_one(self) -> None:
        H = SparseHypergraph(
            n_nodes=3,
            hyperedges=[{0, 1}, {1, 2}],
            n_vertex_labels=1,
            n_edge_labels=1,
            vertex_labels=[0, 0, 0],
            edge_labels=[0, 0],
        )
        roles = {0: {0: 0, 1: 1}, 1: {1: 0, 2: 1}}
        assert fact_word(H, roles) != fact_word(H)


# ---------------------------------------------------------------------------
# The displaced addressings
# ---------------------------------------------------------------------------


class TestAddressingArms:
    def test_keys_read_only_local_structure(self) -> None:
        H = SparseHypergraph(
            n_nodes=4,
            hyperedges=[{0, 1, 2}, {0, 3}],
            n_vertex_labels=2,
            n_edge_labels=2,
            vertex_labels=[1, 0, 0, 0],
            edge_labels=[0, 1],
        )
        assert key_degree(H, 0) == (1, 2)
        assert key_local_key(H, 0) == (1, ((0, 3), (1, 2)))
        assert key_local_key(H, 3) == (0, ((1, 2),))

    @pytest.mark.parametrize("arm", ARMS)
    def test_addresses_are_injective(self, arm: str, sts_9: SparseHypergraph) -> None:
        addresses = key_addresses(sts_9, arm)
        assert len(set(addresses)) == sts_9.n_nodes

    @pytest.mark.parametrize("arm", ARMS)
    def test_word_shape(self, arm: str) -> None:
        H = random_kb(random.Random(23))
        word = addressed_word(H, arm)
        assert len(word) == H.n_nodes + H.n_edges
        prefix, facts = word[: H.n_nodes], word[H.n_nodes :]
        assert all(len(t) == 3 and t[0] == "T" for t in prefix)
        assert [t[1] for t in prefix] == sorted(t[1] for t in prefix)
        assert all(t[0] == "F" for t in facts)
        assert list(facts) == sorted(facts, key=lambda t: (t[1], t[2]))

    @pytest.mark.parametrize("arm", ARMS)
    def test_word_is_invariant_under_permutation(self, arm: str) -> None:
        rng = random.Random(29)
        for _ in range(40):
            H = random_kb(rng)
            sigma = list(range(H.n_nodes))
            rng.shuffle(sigma)
            assert addressed_word(H, arm) == addressed_word(permute(H, sigma), arm)

    @pytest.mark.parametrize("arm", ARMS)
    def test_distance_is_zero_iff_isomorphic(
        self,
        arm: str,
        iso_pair_small: tuple[SparseHypergraph, SparseHypergraph, list[int]],
        non_iso_pair_small: tuple[SparseHypergraph, SparseHypergraph],
    ) -> None:
        distance = FactAddressingAblation(arm)
        H1, H2, _ = iso_pair_small
        assert distance.pairwise(H1, H2) == 0.0
        A, B = non_iso_pair_small
        assert distance.pairwise(A, B) > 0.0

    @pytest.mark.parametrize("arm", ARMS)
    def test_matrix_agrees_with_pairwise(self, arm: str) -> None:
        rng = random.Random(31)
        corpus = [random_kb(rng, n_max=6) for _ in range(6)]
        distance = FactAddressingAblation(arm)
        matrix = distance.matrix(corpus)
        for i in range(6):
            for j in range(i + 1, 6):
                assert matrix[i, j] == distance.pairwise(corpus[i], corpus[j])

    def test_arms_disagree_with_each_other(self) -> None:
        """The arms are genuinely different addressings, not aliases."""
        rng = random.Random(37)
        corpus = [random_kb(rng, n_max=6) for _ in range(30)]
        words = {arm: [addressed_word(H, arm) for H in corpus] for arm in ARMS}
        for a, b in [(ARM_LOCAL_COLOUR, ARM_LOCAL_KEY), (ARM_LOCAL_KEY, ARM_DEGREE_KEY)]:
            assert words[a] != words[b]
