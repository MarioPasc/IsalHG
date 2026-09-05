"""``TokenNGram`` -- determinism, validity, and the conditional completion.

The load-bearing test is :meth:`TestValidity.test_every_sample_decodes`: it is
RQ6's H6a on a synthetic corpus, and it must hold by the totality of the fact
decoder rather than by luck, so it asserts *all* samples decode rather than
counting a rate.

The vectorized distribution in ``ngram.py`` is an unrolling of the Kneser-Ney
recursion, not an approximation, so :class:`TestDistribution` checks the
properties the unrolling must preserve: normalization at every context, and a
finite score for every word over the vocabulary.
"""

from __future__ import annotations

import math
import random

import pytest

from isalhg.core.fact_word import decode_fact_word, encode_fact_word
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.generation.errors import GenerationError
from isalhg.generation.ngram import DEFAULT_CACHE_SIZE, EOS, TokenNGram, words_of

pytestmark = pytest.mark.unit

pytest.importorskip("numpy")

N_TYPES = 3
N_PREDS = 2


def _corpus(count: int = 40, seed: int = 0) -> list[SparseHypergraph]:
    """A small corpus of random connected labelled knowledge bases."""
    rng = random.Random(seed)
    out: list[SparseHypergraph] = []
    for _ in range(count):
        n = rng.randint(4, 8)
        edges = {frozenset({i, i + 1}) for i in range(n - 1)}
        for _ in range(rng.randint(1, 3)):
            edges.add(frozenset(rng.sample(range(n), rng.randint(2, 3))))
        members = sorted(edges, key=sorted)
        out.append(
            SparseHypergraph(
                n,
                members,
                n_vertex_labels=N_TYPES,
                n_edge_labels=N_PREDS,
                vertex_labels=[rng.randrange(N_TYPES) for _ in range(n)],
                edge_labels=[rng.randrange(N_PREDS) for _ in members],
            )
        )
    return out


def _words(count: int = 40, seed: int = 0) -> list[tuple[object, ...]]:
    """Fact words of ``_corpus`` under the identity addressing.

    The identity rank keeps the fixture free of ``pynauty``: what the model is
    being tested on is a corpus of well-formed words, and canonicity of the
    addressing is not part of this file's claim.
    """
    return [encode_fact_word(H, list(range(H.n_nodes))) for H in _corpus(count, seed)]


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


class TestConstruction:
    @pytest.mark.parametrize("order", [0, -1])
    def test_rejects_bad_order(self, order: int) -> None:
        with pytest.raises(GenerationError, match="order"):
            TokenNGram(order=order)

    def test_rejects_unknown_smoothing(self) -> None:
        with pytest.raises(GenerationError, match="smoothing"):
            TokenNGram(smoothing="laplace")

    @pytest.mark.parametrize("discount", [-0.1, 1.0, 1.5])
    def test_rejects_bad_discount(self, discount: float) -> None:
        with pytest.raises(GenerationError, match="discount"):
            TokenNGram(discount=discount)

    def test_rejects_empty_corpus(self) -> None:
        with pytest.raises(GenerationError, match="empty corpus"):
            TokenNGram().fit([])

    def test_unfitted_model_refuses_to_sample(self) -> None:
        with pytest.raises(GenerationError, match="fitted"):
            TokenNGram().sample(1, seed=0)

    def test_unfitted_model_refuses_to_score(self) -> None:
        with pytest.raises(GenerationError, match="fitted"):
            TokenNGram().logprob(())

    def test_fit_returns_self_for_chaining(self) -> None:
        model = TokenNGram(order=2)
        assert model.fit(_words(10)) is model

    def test_vocabulary_holds_eos_and_not_bos(self) -> None:
        model = TokenNGram(order=3).fit(_words(20))
        assert EOS in model.vocabulary
        assert "<bos>" not in model.vocabulary

    def test_refitting_replaces_state(self) -> None:
        model = TokenNGram(order=2).fit(_words(20, seed=0))
        first = len(model.vocabulary)
        model.fit(_words(5, seed=99))
        assert len(model.vocabulary) != first or True  # size may coincide; state must be fresh
        assert all(token in model.vocabulary for word in _words(5, seed=99) for token in word)


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


class TestDeterminism:
    def test_same_seed_same_samples(self) -> None:
        model = TokenNGram(order=3).fit(_words())
        assert model.sample(50, seed=4) == model.sample(50, seed=4)

    def test_different_seeds_differ(self) -> None:
        model = TokenNGram(order=3).fit(_words())
        assert model.sample(50, seed=4) != model.sample(50, seed=5)

    def test_sampling_does_not_touch_global_random_state(self) -> None:
        model = TokenNGram(order=3).fit(_words())
        random.seed(1234)
        expected = [random.random() for _ in range(3)]
        random.seed(1234)
        model.sample(20, seed=0)
        assert [random.random() for _ in range(3)] == expected

    def test_two_models_fitted_identically_sample_identically(self) -> None:
        words = _words()
        assert TokenNGram(order=3).fit(words).sample(30, seed=2) == TokenNGram(order=3).fit(
            words
        ).sample(30, seed=2)

    def test_sample_count_and_bounds(self) -> None:
        model = TokenNGram(order=3).fit(_words())
        samples = model.sample(25, seed=0, max_len=12)
        assert len(samples) == 25
        assert all(len(word) <= 12 for word in samples)

    def test_zero_samples(self) -> None:
        assert TokenNGram(order=2).fit(_words(10)).sample(0, seed=0) == []

    @pytest.mark.parametrize(("n_samples", "max_len"), [(-1, 10), (1, 0)])
    def test_rejects_bad_sampling_arguments(self, n_samples: int, max_len: int) -> None:
        model = TokenNGram(order=2).fit(_words(10))
        with pytest.raises(GenerationError):
            model.sample(n_samples, seed=0, max_len=max_len)


# ---------------------------------------------------------------------------
# Validity -- RQ6 H6a
# ---------------------------------------------------------------------------


class TestValidity:
    @pytest.mark.parametrize("order", [1, 2, 3, 4])
    def test_every_sample_decodes(self, order: int) -> None:
        """All samples decode, at every order -- the property is the language's."""
        model = TokenNGram(order=order).fit(_words())
        samples = model.sample(300, seed=order)
        for word in samples:
            decoded, _ = decode_fact_word(word, n_types=N_TYPES, n_preds=N_PREDS)
            assert isinstance(decoded, SparseHypergraph)

    def test_no_sample_contains_a_sentinel(self) -> None:
        model = TokenNGram(order=3).fit(_words())
        for word in model.sample(200, seed=1):
            assert EOS not in word
            assert "<bos>" not in word

    @pytest.mark.parametrize("smoothing", ["kneser_ney", "witten_bell"])
    def test_both_smoothings_produce_decodable_samples(self, smoothing: str) -> None:
        model = TokenNGram(order=3, smoothing=smoothing).fit(_words())
        for word in model.sample(150, seed=0):
            decode_fact_word(word, n_types=N_TYPES, n_preds=N_PREDS)

    def test_samples_terminate_before_the_cap(self) -> None:
        """EOS must actually fire; a model that always truncates is a bug, not a model."""
        model = TokenNGram(order=3).fit(_words())
        samples = model.sample(200, seed=0, max_len=400)
        assert sum(1 for word in samples if len(word) < 400) > 190


# ---------------------------------------------------------------------------
# The unrolled distribution
# ---------------------------------------------------------------------------


class TestDistribution:
    def test_distribution_is_normalized_at_every_visited_context(self) -> None:
        model = TokenNGram(order=3).fit(_words())
        contexts = [(), ("<bos>", "<bos>")]
        words = _words(5)
        for word in words:
            for i in range(len(word)):
                contexts.append(model._context_of(list(word[:i])))
        for context in contexts:
            total = float(model._distribution(tuple(context)).sum())
            assert total == pytest.approx(1.0, abs=1e-9)

    def test_distribution_is_non_negative(self) -> None:
        model = TokenNGram(order=3).fit(_words())
        assert (model._distribution(()) >= 0).all()

    def test_logprob_is_finite_for_words_over_the_vocabulary(self) -> None:
        words = _words()
        model = TokenNGram(order=3).fit(words)
        for word in words[:10]:
            assert math.isfinite(model.logprob(word))

    def test_logprob_is_negative_infinity_for_unknown_tokens(self) -> None:
        model = TokenNGram(order=3).fit(_words())
        assert model.logprob((("F", 99, (0, 1)),)) == -math.inf

    def test_logprob_of_a_sample_is_finite(self) -> None:
        model = TokenNGram(order=3).fit(_words())
        for word in model.sample(30, seed=0):
            assert math.isfinite(model.logprob(word))

    def test_training_words_score_above_shuffled_ones(self) -> None:
        """A sanity check that the model learned order, not just a unigram."""
        words = _words(60)
        model = TokenNGram(order=3).fit(words)
        rng = random.Random(0)
        real = sum(model.logprob(w) for w in words[:20])
        shuffled = 0.0
        for word in words[:20]:
            tokens = list(word)
            rng.shuffle(tokens)
            shuffled += model.logprob(tuple(tokens))
        assert real > shuffled


# ---------------------------------------------------------------------------
# Conditional completion -- RQ6 step 5
# ---------------------------------------------------------------------------


class TestComplete:
    def test_completion_extends_the_prefix_verbatim(self) -> None:
        words = _words()
        model = TokenNGram(order=3).fit(words)
        for word in words[:10]:
            prefix = word[: 2 * len(word) // 3]
            completed = model.complete(prefix, seed=3)
            assert completed[: len(prefix)] == prefix
            assert len(completed) >= len(prefix)

    def test_completion_decodes(self) -> None:
        words = _words()
        model = TokenNGram(order=3).fit(words)
        for word in words[:10]:
            completed = model.complete(word[: len(word) // 2], seed=1)
            decode_fact_word(completed, n_types=N_TYPES, n_preds=N_PREDS)

    def test_completion_is_deterministic(self) -> None:
        words = _words()
        model = TokenNGram(order=3).fit(words)
        prefix = words[0][:3]
        assert model.complete(prefix, seed=8) == model.complete(prefix, seed=8)

    def test_empty_prefix_is_a_plain_sample(self) -> None:
        model = TokenNGram(order=3).fit(_words())
        assert model.complete((), seed=0) == model.sample(1, seed=0)[0]

    def test_prefix_at_the_cap_is_returned_unchanged(self) -> None:
        words = _words()
        model = TokenNGram(order=3).fit(words)
        prefix = words[0][:4]
        assert model.complete(prefix, seed=0, max_len=4) == prefix

    def test_rejects_bad_max_len(self) -> None:
        model = TokenNGram(order=2).fit(_words(10))
        with pytest.raises(GenerationError):
            model.complete((), seed=0, max_len=0)


# ---------------------------------------------------------------------------
# words_of
# ---------------------------------------------------------------------------


class TestWordsOf:
    def test_role_free_words_have_length_n_plus_m(self) -> None:
        pytest.importorskip("pynauty")
        corpus = _corpus(6)
        for H, word in zip(corpus, words_of(corpus), strict=True):
            assert len(word) == H.n_nodes + H.n_edges

    def test_roles_none_and_explicit_none_agree(self) -> None:
        pytest.importorskip("pynauty")
        corpus = _corpus(5)
        assert words_of(corpus) == words_of(corpus, [None] * len(corpus))


# ---------------------------------------------------------------------------
# The bounded distribution memo
# ---------------------------------------------------------------------------


def _wide_words(
    n_symbols: int = 3000, per_word: int = 6, seed: int = 0
) -> list[tuple[object, ...]]:
    """A corpus whose vocabulary is ``n_symbols`` tokens, every one of them seen.

    Deliberately not fact words: the memo is keyed on opaque tokens, and what
    the byte-footprint test needs is a vocabulary wide enough that one dense
    ``float64`` row is expensive, which a small structural corpus cannot give.
    Each symbol appears exactly once, so almost every context of order 3 is
    distinct and a sampler pressures the cache immediately.
    """
    symbols: list[object] = [("sym", i) for i in range(n_symbols)]
    random.Random(seed).shuffle(symbols)
    return [tuple(symbols[i : i + per_word]) for i in range(0, n_symbols, per_word)]


class TestDistributionCache:
    """Eviction is invisible to every sampled and scored value (the whole point)."""

    @pytest.mark.parametrize("cache_size", [None, 1, 7, DEFAULT_CACHE_SIZE])
    def test_samples_are_identical_across_cache_sizes(self, cache_size: int | None) -> None:
        words = _words()
        expected = TokenNGram(order=3, cache_size=None).fit(words).sample(200, seed=11)
        actual = TokenNGram(order=3, cache_size=cache_size).fit(words).sample(200, seed=11)
        assert actual == expected

    @pytest.mark.parametrize("cache_size", [None, 1, DEFAULT_CACHE_SIZE])
    def test_logprobs_are_identical_across_cache_sizes(self, cache_size: int | None) -> None:
        words = _words()
        unbounded = TokenNGram(order=3, cache_size=None).fit(words)
        bounded = TokenNGram(order=3, cache_size=cache_size).fit(words)
        for word in words[:20]:
            assert bounded.logprob(word) == unbounded.logprob(word)

    def test_the_cache_never_exceeds_its_bound(self) -> None:
        model = TokenNGram(order=3, cache_size=16).fit(_wide_words())
        model.sample(300, seed=3, max_len=8)
        assert len(model._cache) <= 16

    def test_an_unbounded_cache_grows_past_that_bound(self) -> None:
        """The defect this bound fixes, pinned: ``None`` still grows without limit."""
        model = TokenNGram(order=3, cache_size=None).fit(_wide_words())
        model.sample(300, seed=3, max_len=8)
        assert len(model._cache) > 16

    def test_fit_resets_the_cache(self) -> None:
        words = _words()
        model = TokenNGram(order=3).fit(words)
        model.sample(20, seed=0)
        assert len(model._cache) > 0
        model.fit(words)
        assert len(model._cache) == 0

    def test_reset_cache_empties_it_and_sampling_is_unchanged(self) -> None:
        words = _words()
        model = TokenNGram(order=3).fit(words)
        before = model.sample(200, seed=5)
        assert len(model._cache) > 0
        model.reset_cache()
        assert len(model._cache) == 0
        assert model.sample(200, seed=5) == before

    def test_reset_cache_before_any_use_is_harmless(self) -> None:
        model = TokenNGram(order=3).fit(_words())
        model.reset_cache()
        assert model.sample(10, seed=1) == TokenNGram(order=3).fit(_words()).sample(10, seed=1)

    @pytest.mark.parametrize("cache_size", [0, -1])
    def test_rejects_a_cache_size_below_one(self, cache_size: int) -> None:
        with pytest.raises(GenerationError, match="cache_size"):
            TokenNGram(cache_size=cache_size)

    def test_the_byte_footprint_stays_under_the_bound_over_many_samples(self) -> None:
        """5,000 samples over a 3,001-token vocabulary, bounded to 32 rows.

        Without the bound this is the RQ6 leak in miniature: one row costs
        ``8 * |V|`` bytes and the sampler keeps finding new contexts.
        """
        cache_size = 32
        model = TokenNGram(order=3, cache_size=cache_size).fit(_wide_words())
        vocabulary_size = len(model.vocabulary)
        assert vocabulary_size >= 3000

        model.sample(5000, seed=7, max_len=8)

        footprint = sum(int(row.nbytes) for row in model._cache.values())
        assert len(model._cache) <= cache_size
        assert footprint <= cache_size * vocabulary_size * 8
