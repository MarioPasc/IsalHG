"""Property tests for the fact alphabet.

Four properties, at the scale the definition of done asks for:

* **round-trip** --- ``decode(encode(H, canonical_ranks(H)))`` recovers ``H``
  up to the rank relabelling, with and without roles;
* **isomorphism invariance** --- the word of a permuted knowledge base is the
  same word, for the adopted addressing and each of its three displaced arms;
* **completeness** --- word equality partitions a corpus exactly as the nauty
  fingerprint does, with no false merge and no false split;
* **totality** --- the decoder accepts every sequence over the token
  vocabulary and returns a knowledge base that re-encodes consistently.
"""

from __future__ import annotations

import random

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from isalhg.core.fact_word import decode_fact_word, encode_fact_word, token_vocabulary
from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.iso_backends.canonical_order import canonical_ranks
from isalhg.iso_backends.pynauty_levi import PynautyLeviBackend
from isalhg.metric_space.distances.fact_addressing_ablations import (
    ARM_DEGREE_KEY,
    ARM_LOCAL_COLOUR,
    ARM_LOCAL_KEY,
    addressed_word,
)

pytestmark = pytest.mark.property

pytest.importorskip("pynauty")

ARMS = [ARM_LOCAL_COLOUR, ARM_LOCAL_KEY, ARM_DEGREE_KEY]

# Vocabulary bounds for the totality test (definition of done item 4).
VOCAB_N = 8
VOCAB_K = 4
VOCAB_PREDS = 3
VOCAB_TYPES = 3
VOCAB = tuple(token_vocabulary(VOCAB_N, VOCAB_K, VOCAB_PREDS, VOCAB_TYPES))


# ---------------------------------------------------------------------------
# Corpus generation
# ---------------------------------------------------------------------------


def random_kb(
    rng: random.Random,
    *,
    n_lo: int = 3,
    n_hi: int = 12,
    m_lo: int = 2,
    m_hi: int = 8,
    arity_hi: int = 5,
    n_types: int = 2,
    n_preds: int = 2,
) -> SparseHypergraph:
    """A random labelled knowledge base with distinct ``(predicate, members)`` facts."""
    n = rng.randint(n_lo, n_hi)
    m = rng.randint(m_lo, m_hi)
    seen: set[tuple[int, frozenset[int]]] = set()
    edges: list[set[int]] = []
    labels: list[int] = []
    for _ in range(m * 8):
        if len(edges) == m:
            break
        arity = rng.randint(2, min(arity_hi, n))
        members = frozenset(rng.sample(range(n), arity))
        label = rng.randrange(n_preds)
        if (label, members) in seen:
            continue
        seen.add((label, members))
        edges.append(set(members))
        labels.append(label)
    return SparseHypergraph(
        n_nodes=n,
        hyperedges=edges,
        n_vertex_labels=n_types,
        n_edge_labels=n_preds,
        vertex_labels=[rng.randrange(n_types) for _ in range(n)],
        edge_labels=labels,
    )


def random_roles(rng: random.Random, H: SparseHypergraph, n_roles: int = 3) -> dict:
    """A role for every incidence of every fact."""
    return {e: {v: rng.randrange(n_roles) for v in members} for e, members, _ in H.iter_edges()}


# ---------------------------------------------------------------------------
# 1. Round-trip
# ---------------------------------------------------------------------------


class TestRoundTrip:
    N_CASES = 500

    def test_role_free_round_trip(self) -> None:
        rng = random.Random(101)
        for case in range(self.N_CASES):
            H = random_kb(rng)
            rank = canonical_ranks(H)
            decoded, roles = decode_fact_word(
                encode_fact_word(H, rank),
                n_types=H.n_vertex_labels,
                n_preds=H.n_edge_labels,
            )
            assert roles is None
            assert decoded == permute(H, rank), f"case {case}"

    def test_round_trip_preserves_the_isomorphism_class(self) -> None:
        rng = random.Random(102)
        backend = PynautyLeviBackend()
        for case in range(self.N_CASES):
            H = random_kb(rng)
            decoded, _ = decode_fact_word(
                encode_fact_word(H, canonical_ranks(H)),
                n_types=H.n_vertex_labels,
                n_preds=H.n_edge_labels,
            )
            assert backend.fingerprint(decoded) == backend.fingerprint(H), f"case {case}"

    def test_round_trip_with_roles(self) -> None:
        rng = random.Random(103)
        for case in range(self.N_CASES):
            H = random_kb(rng)
            rank = canonical_ranks(H)
            roles = random_roles(rng, H)
            decoded, decoded_roles = decode_fact_word(
                encode_fact_word(H, rank, roles),
                n_types=H.n_vertex_labels,
                n_preds=H.n_edge_labels,
            )
            assert decoded == permute(H, rank), f"case {case}"
            assert decoded_roles is not None
            expected = {
                frozenset((rank[v], role) for v, role in fact_roles.items())
                for fact_roles in roles.values()
            }
            observed = {frozenset(fact_roles.items()) for fact_roles in decoded_roles.values()}
            assert observed == expected, f"case {case}"


# ---------------------------------------------------------------------------
# 2. Isomorphism invariance
# ---------------------------------------------------------------------------


class TestIsomorphismInvariance:
    N_CASES = 500

    def test_arm_b_fact_rank(self) -> None:
        rng = random.Random(201)
        for case in range(self.N_CASES):
            H = random_kb(rng)
            sigma = list(range(H.n_nodes))
            rng.shuffle(sigma)
            H2 = permute(H, sigma)
            assert encode_fact_word(H, canonical_ranks(H)) == encode_fact_word(
                H2, canonical_ranks(H2)
            ), f"case {case}"

    @pytest.mark.parametrize("arm", ARMS)
    def test_displaced_arms(self, arm: str) -> None:
        rng = random.Random(202)
        for case in range(self.N_CASES):
            H = random_kb(rng)
            sigma = list(range(H.n_nodes))
            rng.shuffle(sigma)
            assert addressed_word(H, arm) == addressed_word(permute(H, sigma), arm), (
                f"arm {arm} case {case}"
            )


# ---------------------------------------------------------------------------
# 3. Completeness against the nauty fingerprint
# ---------------------------------------------------------------------------


class TestCompleteness:
    """Word equality must partition a corpus exactly as nauty does.

    The corpus is built small on purpose so that isomorphic duplicates really
    occur; the test asserts that they do, otherwise "no false merge" would be
    vacuous.
    """

    N_CASES = 1000

    @staticmethod
    def _corpus(seed: int) -> list[SparseHypergraph]:
        rng = random.Random(seed)
        return [
            random_kb(rng, n_lo=3, n_hi=5, m_lo=2, m_hi=4, arity_hi=3)
            for _ in range(TestCompleteness.N_CASES)
        ]

    def _check(self, words: list[object], corpus: list[SparseHypergraph], arm: str) -> None:
        backend = PynautyLeviBackend()
        certificates = [backend.fingerprint(H) for H in corpus]

        by_word: dict[object, set[bytes]] = {}
        for word, cert in zip(words, certificates, strict=True):
            by_word.setdefault(word, set()).add(cert)
        false_merges = sum(len(group) - 1 for group in by_word.values() if len(group) > 1)

        by_cert: dict[bytes, set[object]] = {}
        for word, cert in zip(words, certificates, strict=True):
            by_cert.setdefault(cert, set()).add(word)
        false_splits = sum(len(group) - 1 for group in by_cert.values() if len(group) > 1)

        assert false_merges == 0, f"arm {arm}: {false_merges} false merges"
        assert false_splits == 0, f"arm {arm}: {false_splits} false splits"
        # The corpus must actually contain repeated isomorphism classes.
        assert len(by_cert) < len(corpus), "corpus has no isomorphic duplicates"

    def test_arm_b_fact_rank(self) -> None:
        corpus = self._corpus(301)
        words = [encode_fact_word(H, canonical_ranks(H)) for H in corpus]
        self._check(words, corpus, "fact_rank")

    @pytest.mark.parametrize("arm", ARMS)
    def test_displaced_arms(self, arm: str) -> None:
        corpus = self._corpus(301)
        words = [addressed_word(H, arm) for H in corpus]
        self._check(words, corpus, arm)


# ---------------------------------------------------------------------------
# 4. Totality of the decoder
# ---------------------------------------------------------------------------


@st.composite
def token_sequences(draw: st.DrawFn) -> tuple[tuple, ...]:
    """Any sequence of 0-40 tokens drawn from the vocabulary, in any order."""
    return tuple(draw(st.lists(st.sampled_from(VOCAB), min_size=0, max_size=40)))


class TestTotality:
    @settings(
        max_examples=400,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    @given(tokens=token_sequences())
    def test_decoder_never_raises_and_re_encodes_consistently(
        self, tokens: tuple[tuple, ...]
    ) -> None:
        H, _ = decode_fact_word(tokens, n_types=VOCAB_TYPES, n_preds=VOCAB_PREDS)
        assert H.n_vertex_labels == VOCAB_TYPES
        assert H.n_edge_labels == VOCAB_PREDS
        assert H.n_nodes >= 0

        re_encoded = encode_fact_word(H, canonical_ranks(H))
        again, _ = decode_fact_word(re_encoded, n_types=VOCAB_TYPES, n_preds=VOCAB_PREDS)
        backend = PynautyLeviBackend()
        assert backend.fingerprint(again) == backend.fingerprint(H)

    def test_the_generated_sequences_cover_the_awkward_shapes(self) -> None:
        """Totality is only interesting if the draws hit the hard cases."""
        rng = random.Random(401)
        type_after_fact = 0
        rank_beyond_prefix = 0
        repeated_fact = 0
        for _ in range(2000):
            tokens = [rng.choice(VOCAB) for _ in range(rng.randint(0, 40))]
            tags = [t[0] for t in tokens]
            if (
                "F" in tags
                and "T" in tags
                and tags.index("F") < len(tags) - 1 - tags[::-1].index("T")
            ):
                type_after_fact += 1
            n_types_seen = tags.count("T")
            max_rank = max((max(t[2]) for t in tokens if t[0] == "F"), default=-1)
            if max_rank >= n_types_seen:
                rank_beyond_prefix += 1
            facts = [t for t in tokens if t[0] == "F"]
            if len(facts) != len({(t[1], t[2]) for t in facts}):
                repeated_fact += 1
            decode_fact_word(tuple(tokens), n_types=VOCAB_TYPES, n_preds=VOCAB_PREDS)
        assert type_after_fact > 100
        assert rank_beyond_prefix > 100
        assert repeated_fact > 10

    def test_every_prefix_of_a_word_decodes(self) -> None:
        rng = random.Random(402)
        for _ in range(50):
            H = random_kb(rng, n_hi=8, m_hi=6)
            word = encode_fact_word(H, canonical_ranks(H))
            for cut in range(len(word) + 1):
                decode_fact_word(word[:cut], n_types=H.n_vertex_labels, n_preds=H.n_edge_labels)

    def test_every_single_token_edit_of_a_word_decodes(self) -> None:
        rng = random.Random(403)
        for _ in range(20):
            H = random_kb(rng, n_hi=6, m_hi=4, n_types=VOCAB_TYPES, n_preds=VOCAB_PREDS)
            word = list(encode_fact_word(H, canonical_ranks(H)))
            for position in range(len(word) + 1):
                token = rng.choice(VOCAB)
                for edited in (
                    word[:position] + [token] + word[position:],
                    word[:position] + word[position + 1 :],
                ):
                    decode_fact_word(tuple(edited), n_types=VOCAB_TYPES, n_preds=VOCAB_PREDS)


# ---------------------------------------------------------------------------
# 5. Position insensitivity, at scale
# ---------------------------------------------------------------------------


class TestPositionInsensitivityAtScale:
    def test_shuffling_a_word_leaves_the_decoded_class_alone(self) -> None:
        """Any reordering keeping the T tokens' relative order decodes identically."""
        rng = random.Random(501)
        for case in range(300):
            tokens = [rng.choice(VOCAB) for _ in range(rng.randint(0, 25))]
            reference, _ = decode_fact_word(tuple(tokens), n_types=VOCAB_TYPES, n_preds=VOCAB_PREDS)
            shuffled = tokens[:]
            rng.shuffle(shuffled)
            # Restore the T tokens' relative order; their order is the type prefix.
            types = [t for t in tokens if t[0] == "T"]
            iterator = iter(types)
            shuffled = [next(iterator) if t[0] == "T" else t for t in shuffled]
            decoded, _ = decode_fact_word(tuple(shuffled), n_types=VOCAB_TYPES, n_preds=VOCAB_PREDS)
            assert decoded == reference, f"case {case}"
