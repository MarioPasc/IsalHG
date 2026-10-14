"""Unit tests for the fact alphabet: encoder, total decoder, vocabulary, goldens."""

from __future__ import annotations

import random

import pytest

from isalhg.core.fact_word import (
    decode_fact_word,
    encode_fact_word,
    fact_key,
    token_vocabulary,
    word_length,
)
from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.errors import FactWordError
from isalhg.iso_backends.canonical_order import canonical_ranks
from isalhg.iso_backends.pynauty_levi import PynautyLeviBackend

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Fixtures local to this module
# ---------------------------------------------------------------------------


def labelled_4() -> SparseHypergraph:
    """The 4-constant labelled knowledge base whose word is pinned below."""
    return SparseHypergraph(
        n_nodes=4,
        hyperedges=[{0, 1, 2}, {1, 2, 3}, {0, 3}],
        n_vertex_labels=2,
        n_edge_labels=2,
        vertex_labels=[0, 1, 1, 0],
        edge_labels=[0, 1, 0],
    )


def chain_3() -> SparseHypergraph:
    """Three constants, two binary facts, trivial vocabulary."""
    return SparseHypergraph(
        n_nodes=3,
        hyperedges=[{0, 1}, {1, 2}],
        n_vertex_labels=1,
        n_edge_labels=1,
        vertex_labels=[0, 0, 0],
        edge_labels=[0, 0],
    )


# ---------------------------------------------------------------------------
# Golden words -- hand-checked once, then frozen
# ---------------------------------------------------------------------------

# rank = (1, 2, 3, 0), so pi^-1 = (3, 0, 1, 2) and the type prefix reads
# type(3), type(0), type(1), type(2) = 0, 0, 1, 1. The facts {0,1,2} (label 0),
# {1,2,3} (label 1) and {0,3} (label 0) address as (1,2,3), (0,2,3) and (0,1),
# then sort by (label, operands).
GOLDEN_LABELLED_4 = (
    ("T", 0),
    ("T", 0),
    ("T", 1),
    ("T", 1),
    ("F", 0, (0, 1)),
    ("F", 0, (1, 2, 3)),
    ("F", 1, (0, 2, 3)),
)

# Fano STS(7): 7 constants on a trivial vocabulary, 7 triples. Every one of the
# C(7,2) = 21 pairs occurs in exactly one fact token, and every constant occurs
# in exactly 3 -- checked by hand against the pinned tuple below.
GOLDEN_FANO = (
    ("T", 0),
    ("T", 0),
    ("T", 0),
    ("T", 0),
    ("T", 0),
    ("T", 0),
    ("T", 0),
    ("F", 0, (0, 1, 2)),
    ("F", 0, (0, 3, 5)),
    ("F", 0, (0, 4, 6)),
    ("F", 0, (1, 3, 4)),
    ("F", 0, (1, 5, 6)),
    ("F", 0, (2, 3, 6)),
    ("F", 0, (2, 4, 5)),
)

# STS(9) = AG(2,3): 9 constants, 12 triples, every one of the C(9,2) = 36 pairs
# in exactly one fact token, every constant in exactly 4.
GOLDEN_STS9 = (
    ("T", 0),
    ("T", 0),
    ("T", 0),
    ("T", 0),
    ("T", 0),
    ("T", 0),
    ("T", 0),
    ("T", 0),
    ("T", 0),
    ("F", 0, (0, 1, 2)),
    ("F", 0, (0, 3, 4)),
    ("F", 0, (0, 5, 8)),
    ("F", 0, (0, 6, 7)),
    ("F", 0, (1, 3, 5)),
    ("F", 0, (1, 4, 7)),
    ("F", 0, (1, 6, 8)),
    ("F", 0, (2, 3, 6)),
    ("F", 0, (2, 4, 8)),
    ("F", 0, (2, 5, 7)),
    ("F", 0, (3, 7, 8)),
    ("F", 0, (4, 5, 6)),
)


class TestGoldenWords:
    def test_labelled_4(self) -> None:
        H = labelled_4()
        assert encode_fact_word(H, canonical_ranks(H)) == GOLDEN_LABELLED_4

    def test_fano(self, fano_plane: SparseHypergraph) -> None:
        assert encode_fact_word(fano_plane, canonical_ranks(fano_plane)) == GOLDEN_FANO

    def test_sts_9(self, sts_9: SparseHypergraph) -> None:
        assert encode_fact_word(sts_9, canonical_ranks(sts_9)) == GOLDEN_STS9

    @pytest.mark.parametrize(
        ("word", "n_pairs", "degree"),
        [(GOLDEN_FANO, 21, 3), (GOLDEN_STS9, 36, 4)],
    )
    def test_golden_is_a_steiner_triple_system(
        self, word: tuple[tuple[object, ...], ...], n_pairs: int, degree: int
    ) -> None:
        """The pinned design words really do describe an STS -- the hand check, automated."""
        facts = [token[2] for token in word if token[0] == "F"]
        constants = [token for token in word if token[0] == "T"]
        pairs = [
            (operands[i], operands[j])
            for operands in facts
            for i in range(len(operands))
            for j in range(i + 1, len(operands))
        ]
        assert len(set(pairs)) == len(pairs) == n_pairs
        for r in range(len(constants)):
            assert sum(1 for operands in facts if r in operands) == degree


# ---------------------------------------------------------------------------
# Encoding
# ---------------------------------------------------------------------------


class TestEncode:
    def test_length_is_n_plus_m(self, fano_plane: SparseHypergraph) -> None:
        word = encode_fact_word(fano_plane, canonical_ranks(fano_plane))
        assert len(word) == word_length(fano_plane) == 7 + 7

    def test_type_prefix_is_indexed_by_rank(self) -> None:
        H = labelled_4()
        rank = canonical_ranks(H)
        word = encode_fact_word(H, rank)
        inverse = {r: v for v, r in enumerate(rank)}
        for r in range(H.n_nodes):
            assert word[r] == ("T", H.vertex_label(inverse[r]))

    def test_fact_tokens_are_sorted(self) -> None:
        H = labelled_4()
        facts = [t for t in encode_fact_word(H, canonical_ranks(H)) if t[0] == "F"]
        assert facts == sorted(facts, key=lambda t: (t[1], t[2]))

    def test_identity_rank_is_accepted(self) -> None:
        H = chain_3()
        assert encode_fact_word(H, (0, 1, 2)) == (
            ("T", 0),
            ("T", 0),
            ("T", 0),
            ("F", 0, (0, 1)),
            ("F", 0, (1, 2)),
        )

    def test_empty_hypergraph_encodes_to_the_empty_word(self) -> None:
        H = SparseHypergraph(n_nodes=0, hyperedges=[])
        assert encode_fact_word(H, ()) == ()

    @pytest.mark.parametrize("bad", [(0, 1), (0, 1, 1), (0, 1, 3), (0, 1, 2, 3)])
    def test_non_permutation_rank_raises(self, bad: tuple[int, ...]) -> None:
        with pytest.raises(FactWordError, match="permutation"):
            encode_fact_word(chain_3(), bad)


class TestEncodeWithRoles:
    def test_operands_are_role_rank_pairs_sorted_by_rank(self) -> None:
        H = chain_3()
        roles = {0: {0: 5, 1: 7}, 1: {1: 5, 2: 7}}
        word = encode_fact_word(H, (0, 1, 2), roles)
        facts = [t for t in word if t[0] == "F"]
        assert facts == [("F", 0, ((5, 0), (7, 1))), ("F", 0, ((5, 1), (7, 2)))]

    def test_missing_fact_raises(self) -> None:
        with pytest.raises(FactWordError, match="no entry for fact"):
            encode_fact_word(chain_3(), (0, 1, 2), {0: {0: 0, 1: 1}})

    def test_missing_incidence_raises(self) -> None:
        with pytest.raises(FactWordError, match="no role for constant"):
            encode_fact_word(chain_3(), (0, 1, 2), {0: {0: 0}, 1: {1: 0, 2: 1}})


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------


class TestRoundTrip:
    def test_decode_of_encode_equals_permute_by_rank(self) -> None:
        H = labelled_4()
        rank = canonical_ranks(H)
        decoded, roles = decode_fact_word(
            encode_fact_word(H, rank), n_types=H.n_vertex_labels, n_preds=H.n_edge_labels
        )
        assert decoded == permute(H, rank)
        assert roles is None

    @pytest.mark.parametrize("fixture", ["fano_plane", "sts_9"])
    def test_designs_round_trip_to_the_same_fingerprint(
        self, fixture: str, request: pytest.FixtureRequest
    ) -> None:
        H = request.getfixturevalue(fixture)
        rank = canonical_ranks(H)
        decoded, _ = decode_fact_word(
            encode_fact_word(H, rank), n_types=H.n_vertex_labels, n_preds=H.n_edge_labels
        )
        backend = PynautyLeviBackend()
        assert backend.fingerprint(decoded) == backend.fingerprint(H)

    def test_roles_survive_the_round_trip(self) -> None:
        H = chain_3()
        rank = canonical_ranks(H)
        roles = {0: {0: 5, 1: 7}, 1: {1: 5, 2: 7}}
        word = encode_fact_word(H, rank, roles)
        decoded, decoded_roles = decode_fact_word(word, n_types=1, n_preds=1)
        assert decoded_roles is not None
        # Roles come back keyed by the decoded edge ids and the ranks of the
        # constants; translating through rank recovers the input map exactly.
        translated = {
            frozenset((rank[v], role) for v, role in fact_roles.items())
            for fact_roles in roles.values()
        }
        recovered = {
            frozenset((r, role) for r, role in fact_roles.items())
            for fact_roles in decoded_roles.values()
        }
        assert recovered == translated
        assert decoded == permute(H, rank)


# ---------------------------------------------------------------------------
# The decoder is total
# ---------------------------------------------------------------------------


class TestDecoderTotality:
    def test_empty_word(self) -> None:
        H, roles = decode_fact_word((), n_types=2, n_preds=2)
        assert (H.n_nodes, H.n_edges) == (0, 0)
        assert (H.n_vertex_labels, H.n_edge_labels) == (2, 2)
        assert roles is None

    def test_only_type_tokens(self) -> None:
        H, _ = decode_fact_word((("T", 1), ("T", 0)), n_types=2, n_preds=1)
        assert H.n_nodes == 2
        assert [H.vertex_label(v) for v in range(2)] == [1, 0]
        assert H.n_edges == 0

    def test_fact_beyond_the_prefix_appends_untyped_constants(self) -> None:
        H, _ = decode_fact_word((("T", 1), ("F", 0, (0, 3))), n_types=2, n_preds=1)
        assert H.n_nodes == 4
        assert [H.vertex_label(v) for v in range(4)] == [1, 0, 0, 0]
        assert sorted(members for _, members, _ in H.iter_edges()) == [frozenset({0, 3})]

    def test_facts_form_a_set(self) -> None:
        H, _ = decode_fact_word(
            (("F", 0, (0, 1)), ("F", 0, (0, 1)), ("F", 0, (1, 0))), n_types=1, n_preds=1
        )
        assert H.n_edges == 1

    def test_same_members_under_different_predicates_are_two_facts(self) -> None:
        H, _ = decode_fact_word((("F", 0, (0, 1)), ("F", 1, (0, 1))), n_types=1, n_preds=2)
        assert H.n_edges == 2

    def test_duplicate_ranks_collapse(self) -> None:
        H, _ = decode_fact_word((("F", 0, (2, 2, 0)),), n_types=1, n_preds=1)
        assert H.n_nodes == 3
        assert [members for _, members, _ in H.iter_edges()] == [frozenset({0, 2})]

    def test_empty_operand_tuple_is_a_no_op(self) -> None:
        H, _ = decode_fact_word((("T", 0), ("F", 0, ())), n_types=1, n_preds=1)
        assert (H.n_nodes, H.n_edges) == (1, 0)

    def test_disconnected_result_is_legal(self) -> None:
        H, _ = decode_fact_word((("F", 0, (0, 1)), ("F", 0, (2, 3))), n_types=1, n_preds=1)
        assert H.n_nodes == 4
        assert not H.is_connected()

    def test_repeated_fact_keeps_the_first_roles(self) -> None:
        _, roles = decode_fact_word(
            (("F", 0, ((1, 0), (2, 1))), ("F", 0, ((7, 0), (8, 1)))), n_types=1, n_preds=1
        )
        assert roles == {0: {0: 1, 1: 2}}

    def test_duplicate_rank_in_a_role_operand_keeps_the_first_role(self) -> None:
        _, roles = decode_fact_word((("F", 0, ((1, 0), (2, 0), (3, 1))),), n_types=1, n_preds=1)
        assert roles == {0: {0: 1, 1: 3}}

    def test_bare_facts_contribute_no_roles_entry(self) -> None:
        _, roles = decode_fact_word(
            (("F", 0, (0, 1)), ("F", 1, ((4, 0), (5, 1)))), n_types=1, n_preds=2
        )
        assert roles is not None
        assert set(roles) == {1}


class TestDecoderRejectsMalformedTokens:
    @pytest.mark.parametrize(
        "token",
        [
            "T",
            ("T",),
            ("T", 0, 0),
            ("F", 0),
            ("X", 0),
            ("F", 0, (0, -1)),
            ("F", 0, (0, "a")),
            ("F", 0, (0, (1, 2))),
            ("F", 0, ((1, 2, 3),)),
            ("F", 0, ((1, -1),)),
            ("F", 0, ((-1, 0),)),
            ("F", 0, 3),
        ],
    )
    def test_malformed_token_raises(self, token: object) -> None:
        with pytest.raises(FactWordError):
            decode_fact_word((token,), n_types=2, n_preds=2)  # type: ignore[arg-type]

    @pytest.mark.parametrize("token", [("T", 5), ("F", 5, (0, 1)), ("T", -1)])
    def test_out_of_vocabulary_id_raises(self, token: tuple[object, ...]) -> None:
        with pytest.raises(FactWordError, match="outside"):
            decode_fact_word((token,), n_types=2, n_preds=2)

    @pytest.mark.parametrize(("n_types", "n_preds"), [(0, 1), (1, 0)])
    def test_empty_vocabulary_raises(self, n_types: int, n_preds: int) -> None:
        with pytest.raises(FactWordError, match="at least 1"):
            decode_fact_word((), n_types=n_types, n_preds=n_preds)


# ---------------------------------------------------------------------------
# Position insensitivity (DESIGN.md G2 lemma)
# ---------------------------------------------------------------------------


class TestPositionInsensitivity:
    """The decoded knowledge base depends on the multiset of F tokens and the
    type prefix, never on where the tokens sit."""

    WORD = (
        ("T", 0),
        ("T", 1),
        ("T", 1),
        ("F", 0, (0, 1)),
        ("F", 0, (1, 2)),
        ("F", 1, (0, 2)),
    )

    def _decode(self, word: tuple[tuple[object, ...], ...]) -> SparseHypergraph:
        H, _ = decode_fact_word(word, n_types=2, n_preds=2)  # type: ignore[arg-type]
        return H

    def test_shuffling_fact_tokens_leaves_the_decode_unchanged(self) -> None:
        reference = self._decode(self.WORD)
        prefix = self.WORD[:3]
        facts = list(self.WORD[3:])
        rng = random.Random(0)
        for _ in range(50):
            rng.shuffle(facts)
            assert self._decode((*prefix, *facts)) == reference

    def test_moving_type_tokens_leaves_the_decode_unchanged(self) -> None:
        reference = self._decode(self.WORD)
        tokens = list(self.WORD)
        rng = random.Random(1)
        for _ in range(50):
            shuffled = tokens[:]
            rng.shuffle(shuffled)
            # The T tokens must keep their relative order: their order *is* the
            # type prefix, and permuting it re-types the constants.
            types = [t for t in shuffled if t[0] == "T"]
            if types != [t for t in tokens if t[0] == "T"]:
                continue
            assert self._decode(tuple(shuffled)) == reference

    def test_permuting_the_type_prefix_may_change_the_class(self) -> None:
        """The prefix order is information; only F-token order is free."""
        a = self._decode((("T", 0), ("T", 1), ("F", 0, (0, 2))))
        b = self._decode((("T", 1), ("T", 0), ("F", 0, (0, 2))))
        backend = PynautyLeviBackend()
        assert backend.fingerprint(a) != backend.fingerprint(b)

    def test_the_two_readings_agree_on_every_canonical_word(
        self, fano_plane: SparseHypergraph, sts_9: SparseHypergraph
    ) -> None:
        """A word whose T tokens precede its F tokens decodes the same either way.

        The positional reading appends a constant where a ``T`` token sits; the
        adopted reading collects the ``T`` tokens first. On a word emitted by
        :func:`encode_fact_word` -- prefix, then facts -- the two coincide, so
        the choice is invisible to every measured number.
        """
        for H in (labelled_4(), chain_3(), fano_plane, sts_9):
            word = encode_fact_word(H, canonical_ranks(H))
            decoded, _ = decode_fact_word(word, n_types=H.n_vertex_labels, n_preds=H.n_edge_labels)
            assert decoded == _decode_positionally(
                word, n_types=H.n_vertex_labels, n_preds=H.n_edge_labels
            )


def _decode_positionally(
    tokens: tuple[tuple[object, ...], ...], *, n_types: int, n_preds: int
) -> SparseHypergraph:
    """The rejected sequential reading, for the agreement test only."""
    labels: list[int] = []
    facts: list[tuple[int, tuple[int, ...]]] = []
    for token in tokens:
        if token[0] == "T":
            labels.append(int(token[1]))  # type: ignore[arg-type]
        else:
            ranks = tuple(sorted(set(token[2])))  # type: ignore[arg-type]
            while ranks and len(labels) <= ranks[-1]:
                labels.append(0)
            facts.append((int(token[1]), ranks))  # type: ignore[arg-type]
    H = SparseHypergraph(
        n_nodes=len(labels),
        hyperedges=[],
        n_vertex_labels=n_types,
        n_edge_labels=n_preds,
        vertex_labels=labels,
        edge_labels=[],
    )
    for pred, ranks in facts:
        if ranks:
            H.add_hyperedge(ranks, label=pred)
    return H


# ---------------------------------------------------------------------------
# Derived helpers
# ---------------------------------------------------------------------------


class TestFactKey:
    def test_is_the_identity(self, fano_plane: SparseHypergraph) -> None:
        word = encode_fact_word(fano_plane, canonical_ranks(fano_plane))
        assert fact_key(word) is word

    def test_key_is_hashable(self, fano_plane: SparseHypergraph) -> None:
        word = encode_fact_word(fano_plane, canonical_ranks(fano_plane))
        assert len({fact_key(word), fact_key(word)}) == 1


class TestWordLength:
    @pytest.mark.parametrize(
        ("build", "expected"),
        [(labelled_4, 7), (chain_3, 5), (lambda: SparseHypergraph(n_nodes=0, hyperedges=[]), 0)],
    )
    def test_n_plus_m(self, build: object, expected: int) -> None:
        assert word_length(build()) == expected  # type: ignore[operator]

    def test_independent_of_the_address_map(self) -> None:
        H = labelled_4()
        assert word_length(H) == len(encode_fact_word(H, (3, 2, 1, 0)))


class TestTokenVocabulary:
    def test_counts(self) -> None:
        tokens = list(token_vocabulary(4, 3, 2, 3))
        # 3 type tokens; per predicate, C(4,2) + C(4,3) = 6 + 4 = 10 fact tokens.
        assert len(tokens) == 3 + 2 * 10
        assert len(set(tokens)) == len(tokens)

    def test_shapes_and_bounds(self) -> None:
        for token in token_vocabulary(5, 4, 2, 2):
            if token[0] == "T":
                assert 0 <= token[1] < 2
            else:
                assert 0 <= token[1] < 2
                assert 2 <= len(token[2]) <= 4
                assert all(0 <= r < 5 for r in token[2])
                assert list(token[2]) == sorted(set(token[2]))

    def test_is_deterministic(self) -> None:
        assert list(token_vocabulary(4, 3, 2, 2)) == list(token_vocabulary(4, 3, 2, 2))

    @pytest.mark.parametrize(("n", "k"), [(5, 1), (5, 0), (1, 4), (0, 4)])
    def test_degenerate_arguments_yield_only_type_tokens(self, n: int, k: int) -> None:
        assert all(t[0] == "T" for t in token_vocabulary(n, k, 2, 2))

    def test_every_token_decodes(self) -> None:
        for token in token_vocabulary(4, 3, 2, 2):
            decode_fact_word((token,), n_types=2, n_preds=2)

    def test_negative_argument_raises(self) -> None:
        with pytest.raises(FactWordError, match="non-negative"):
            list(token_vocabulary(-1, 3, 2, 2))
