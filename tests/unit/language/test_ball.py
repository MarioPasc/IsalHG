"""The string ball, its decoded interior, and the Prop 4 inclusion.

`DESIGN.md` G2 says the decoder is total, so a Levenshtein ball of a word is a
set of knowledge bases.  Prop 4 is the sharper statement the article uses: the
*fact-level* ball sits inside the string ball --- adding one fact to ``K`` over
constants ``K`` already has produces a class reachable by inserting one token
into ``w(K)``.  The main test measures that on 100 random ``(K, f)`` pairs by
decoding the whole radius-1 ball and looking for the class of ``K + f``, which
is the definition-of-done wording rather than a witness check.

Decoding a few thousand words per case is affordable because the decoded class
depends only on the type prefix and the fact-token *set*, so
:func:`decoded_classes` canonicalizes once per signature.  That lemma is pinned
here too, since the saving is only sound if it holds.
"""

from __future__ import annotations

import random

import pytest

from isalhg.core.fact_word import token_vocabulary
from isalhg.language.ball import BallError, decoded_classes, string_ball
from isalhg.language.reach import fact_key_of
from isalhg.metric_space.distances.fact_levenshtein import fact_word, word_distance
from tests.unit.language._builders import (
    random_kb,
    with_inserted_fact,
)

pytestmark = pytest.mark.unit

pytest.importorskip("pynauty")
pytest.importorskip("rapidfuzz")

BALL_TYPES = 2
BALL_PREDS = 2
BALL_ARITY = 3


class TestStringBall:
    def test_radius_zero_is_the_centre(self) -> None:
        rng = random.Random(101)
        word = fact_word(random_kb(rng))
        assert list(string_ball(word, 0, [])) == [word]

    def test_shell_sizes_and_deduplication(self) -> None:
        word = (("T", 0), ("T", 1))
        vocab = [("T", 0), ("T", 1)]
        ball = list(string_ball(word, 1, vocab))
        assert len(ball) == len(set(ball))
        assert ball[0] == word
        assert all(word_distance(word, other) <= 1 for other in ball)

    def test_every_word_within_radius_is_present(self) -> None:
        """The default ball is exactly the indel ball; with substitutions, the Levenshtein one."""
        from rapidfuzz.distance import Indel

        word = (("T", 0), ("T", 1))
        alphabet: list[tuple[object, ...]] = [("T", 0), ("T", 1)]
        universe = [
            tuple(candidate) for length in range(5) for candidate in _all_words(alphabet, length)
        ]
        codes = {token: chr(0x100 + index) for index, token in enumerate(alphabet)}

        def encode(w: tuple[tuple[object, ...], ...]) -> str:
            return "".join(codes[token] for token in w)

        indel_ball = set(string_ball(word, 2, alphabet))
        expected_indel = {
            candidate
            for candidate in universe
            if Indel.distance(encode(word), encode(candidate)) <= 2
        }
        assert expected_indel <= indel_ball
        assert all(Indel.distance(encode(word), encode(other)) <= 2 for other in indel_ball)

        lev_ball = set(string_ball(word, 2, alphabet, substitutions=True))
        expected_lev = {candidate for candidate in universe if word_distance(word, candidate) <= 2}
        assert expected_lev <= lev_ball

    def test_substitutions_are_opt_in(self) -> None:
        word = (("T", 0),)
        vocab = [("T", 0), ("T", 1)]
        indel = set(string_ball(word, 1, vocab))
        with_subst = set(string_ball(word, 1, vocab, substitutions=True))
        assert (("T", 1),) in with_subst
        assert (("T", 1),) not in indel
        assert indel < with_subst

    def test_negative_radius_raises(self) -> None:
        with pytest.raises(BallError):
            list(string_ball((), -1, []))


def _all_words(alphabet: list[tuple[object, ...]], length: int) -> list[list[tuple[object, ...]]]:
    """Every word of exactly ``length`` tokens over ``alphabet``."""
    if length == 0:
        return [[]]
    return [[token, *rest] for token in alphabet for rest in _all_words(alphabet, length - 1)]


class TestDecodedClasses:
    def test_position_independence_of_the_decoded_class(self) -> None:
        rng = random.Random(103)
        for _ in range(50):
            H = random_kb(rng, n_lo=4, n_hi=6, m_lo=2, m_hi=4, arity_hi=BALL_ARITY)
            word = fact_word(H)
            shuffled = list(word)
            rng.shuffle(shuffled)
            classes = decoded_classes(
                [word, tuple(shuffled)], n_types=H.n_vertex_labels, n_preds=H.n_edge_labels
            )
            prefix_intact = [token for token in shuffled if token[0] == "T"] == [
                token for token in word if token[0] == "T"
            ]
            if prefix_intact:
                assert len(classes) == 1

    def test_keys_are_canonical_keys(self) -> None:
        rng = random.Random(107)
        H = random_kb(rng, n_lo=5, n_hi=5, m_lo=3, m_hi=3, arity_hi=BALL_ARITY)
        classes = decoded_classes(
            [fact_word(H)], n_types=H.n_vertex_labels, n_preds=H.n_edge_labels
        )
        for key, decoded in classes.items():
            assert fact_key_of(decoded) == key
        assert fact_key_of(H) in classes


class TestPropFourInclusion:
    """The fact-level ball of radius 1 sits inside the decoded string ball."""

    N_CASES = 100

    def test_one_fact_insertion_is_one_token_insertion(self) -> None:
        rng = random.Random(109)
        checked = 0
        while checked < self.N_CASES:
            H = random_kb(
                rng,
                n_lo=4,
                n_hi=6,
                m_lo=2,
                m_hi=4,
                arity_hi=BALL_ARITY,
                n_types=BALL_TYPES,
                n_preds=BALL_PREDS,
            )
            grown = with_inserted_fact(rng, H, arity_hi=BALL_ARITY)
            if grown is None:
                continue
            checked += 1
            vocab = tuple(token_vocabulary(H.n_nodes, BALL_ARITY, BALL_PREDS, BALL_TYPES))
            classes = decoded_classes(
                string_ball(fact_word(H), 1, vocab),
                n_types=BALL_TYPES,
                n_preds=BALL_PREDS,
            )
            assert fact_key_of(grown) in classes, (H.n_nodes, H.n_edges)
            assert fact_key_of(H) in classes
