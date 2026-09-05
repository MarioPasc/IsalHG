"""``TokenNGram`` -- an order-``n`` token n-gram over words of the fact alphabet.

The model is deliberately plain. RQ6's claim is about the *language*, not about
the model: every sample of any model over the fact alphabet decodes, because
:func:`isalhg.core.fact_word.decode_fact_word` is total on the token
vocabulary. A stronger generator would make the fidelity numbers prettier and
would not change the validity result at all, so a stronger generator would only
obscure what is being demonstrated. The same model class is run over the flat
serialization of :mod:`isalhg.generation.incidence_baseline`, where samples
*are* rejected -- and since the two arms differ in nothing but the
serialization, the difference is attributable to the language.

Smoothing
---------
Interpolated Kneser-Ney with a fixed absolute discount ``D`` (Chen & Goodman,
*An empirical study of smoothing techniques for language modeling*, Computer
Speech & Language 13(4):359-394, 1999). At each order

    ``p_k(w | h) = max(c(h w) - D, 0) / c(h) + D * N_{1+}(h *) / c(h) * p_{k-1}(w | h')``

where ``h'`` drops the oldest token of ``h`` and ``N_{1+}(h *)`` counts the
distinct continuations of ``h``. When ``h`` was never seen the level is skipped
(``p_k = p_{k-1}``), which is the usual convention and keeps the model defined
on unseen contexts.

The recursion bottoms out at the *continuation* distribution -- how many
distinct contexts a token completes, not how often it occurs. That is the part
of Kneser-Ney that matters here: a fact token appearing in many different
knowledge bases should be likelier in a novel context than one appearing many
times inside a single knowledge base. It is add-one smoothed,
``p_0(w) = (N_{1+}(* w) + 1) / (N_{1+}(* *) + |V|)``, so every token of the
vocabulary keeps positive probability, :meth:`logprob` is finite on any word
over that vocabulary, and no sampled continuation is unreachable.

``smoothing="witten_bell"`` is the alternative named in the design: it replaces
the fixed discount with the adaptive mass ``N_{1+}(h *) / (c(h) + N_{1+}(h *))``.

How the distribution is computed
--------------------------------
Written as a recursion, scoring one token costs one pass per order, and
sampling would cost that for every candidate in the vocabulary -- thousands of
Python-level calls per emitted token, which is minutes per thousand samples on
a real collection. The recursion is therefore **expanded once** into a dense
vector instead. Unrolling

    ``p_K = d_K + b_K (d_{K-1} + b_{K-1} (... + b_1 p_0))``

gives ``p = sum_k (prod_{i>k} b_i) d_k + (prod_i b_i) p_0``, so one pass from
the longest matching context down to the shortest accumulates the exact same
distribution into a single numpy array. Sampling and scoring then index that
array. The result is identical to the recursion -- this is an expansion, not an
approximation -- and the per-context vectors are memoised, since a sampler
revisits contexts constantly.

The memo is a **bounded LRU** (``cache_size``). Each entry is one dense
``float64`` vector over the whole vocabulary, so it costs ``8 * |V|`` bytes, and
a long-lived sampler visits a new context far more often than intuition
suggests: one 10,000-sample RQ6 unit over ``wd50k66`` (``|V| = 8,489``, i.e.
67,912 bytes per entry) touched about 10,800 distinct contexts and grew the
unbounded memo by 731 MB, which is how a shard reached 20.4 GB and was killed.
Eviction cannot change a sampled sequence: the memo caches a deterministic
function of the context, so a miss recomputes exactly the vector that was
dropped. ``cache_size=None`` restores the unbounded behaviour.

Tokens
------
Tokens are opaque hashables. The model never inspects them, so it fits fact
words (:func:`isalhg.metric_space.distances.fact_levenshtein.fact_word`) and
flattened incidence lists (:func:`isalhg.generation.incidence_baseline.flatten`)
through the identical code path -- which is what makes the two RQ6 arms a
controlled comparison rather than two separate experiments.

``BOS`` and ``EOS`` are internal sentinels. ``EOS`` is a real vocabulary entry
(the model must learn when to stop) but is never part of a returned word;
``BOS`` only pads contexts. Sampling stops at ``EOS`` or at ``max_len``; a
truncated sample is still a word, and for the fact alphabet still decodes, so
truncation costs fidelity rather than validity.

numpy and the standard library only.
"""

from __future__ import annotations

import math
import random
from collections import OrderedDict
from collections.abc import Hashable, Iterable, Sequence
from typing import TYPE_CHECKING, Any

from isalhg.core.fact_word import Word
from isalhg.generation.errors import GenerationError

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray

# Bare strings, deliberately: every token of both serializations is a tuple, so
# a string sentinel cannot collide with real data no matter what a collection
# contains.
BOS: str = "<bos>"
EOS: str = "<eos>"

SMOOTHINGS: tuple[str, ...] = ("kneser_ney", "witten_bell")

# Entries in the per-context distribution memo. One entry is 8 * |V| bytes.
# Sized against the largest frozen TKDE vocabulary, wd50k66_full's fact words
# at |V| = 21,263: 21,263 * 8 = 170,104 B ~ 166 KiB per entry, so
# 1024 * 170,104 = 174,186,496 B ~ 166 MiB, inside a 256 MiB budget. On the
# collection that ran out of memory, wd50k66 at |V| = 8,489, the same 1024
# entries cost 69.5 MB against the 731 MB the unbounded memo accumulated in one
# 10,000-sample unit.
DEFAULT_CACHE_SIZE: int = 1024

# Per-context level record: (continuation indices, discounted probabilities,
# backoff mass). Precomputed at fit time, consumed by _distribution.
_Level = tuple["NDArray[np.int64]", "NDArray[np.float64]", float]


def _import_numpy() -> Any:
    try:
        import numpy as np
    except ImportError as exc:  # pragma: no cover - exercised only without numpy
        raise GenerationError(
            "numpy is required for TokenNGram; install via `pip install numpy`"
        ) from exc
    return np


class TokenNGram:
    """Order-``order`` n-gram over sequences of hashable tokens.

    Parameters
    ----------
    order : int, optional
        Context length plus one: ``order=3`` conditions each token on the two
        before it. Must be at least 1. Defaults to 3 (the RQ6 setting).
    smoothing : {"kneser_ney", "witten_bell"}, optional
        Interpolation scheme. Defaults to ``"kneser_ney"``.
    discount : float, optional
        The absolute discount ``D`` of Kneser-Ney, in ``[0, 1)``. Ignored by
        ``"witten_bell"``. Defaults to 0.75.
    cache_size : int or None, optional
        How many per-context distributions the memo retains, least-recently-used
        evicted first. Each entry is one dense ``float64`` vector over the
        vocabulary, so it costs ``8 * |V|`` bytes: at the largest frozen TKDE
        vocabulary (``wd50k66_full`` fact words, ``|V| = 21,263``) that is
        ``21,263 * 8 = 170,104`` bytes, and the default 1024 entries therefore
        bound the memo at ``1024 * 170,104 = 174,186,496`` bytes, about 166 MiB
        -- inside a 256 MiB budget, and 69.5 MB on ``wd50k66``
        (``|V| = 8,489``), whose unbounded memo grew 731 MB in a single
        10,000-sample unit. ``None`` leaves the memo unbounded, which is the
        historical behaviour and is safe only for short-lived models. Must be at
        least 1 when given, so the vector just computed is always retained.
        Defaults to :data:`DEFAULT_CACHE_SIZE`.

    Raises
    ------
    isalhg.generation.errors.GenerationError
        If ``order`` is below 1, ``smoothing`` is unknown, ``discount`` is
        outside ``[0, 1)``, or ``cache_size`` is below 1.
    """

    def __init__(
        self,
        order: int = 3,
        smoothing: str = "kneser_ney",
        discount: float = 0.75,
        cache_size: int | None = DEFAULT_CACHE_SIZE,
    ) -> None:
        if order < 1:
            raise GenerationError(f"order must be at least 1; got {order}")
        if smoothing not in SMOOTHINGS:
            raise GenerationError(f"smoothing must be one of {SMOOTHINGS}; got {smoothing!r}")
        if not 0.0 <= discount < 1.0:
            raise GenerationError(f"discount must lie in [0, 1); got {discount}")
        if cache_size is not None and cache_size < 1:
            raise GenerationError(f"cache_size must be at least 1 or None; got {cache_size}")

        self.order = order
        self.smoothing = smoothing
        self.discount = discount
        self.cache_size = cache_size

        self._levels: list[dict[tuple[Hashable, ...], _Level]] = []
        self._vocabulary: tuple[Hashable, ...] = ()
        self._index: dict[Hashable, int] = {}
        self._p0: Any = None
        self._cache: OrderedDict[tuple[Hashable, ...], Any] = OrderedDict()
        self._fitted = False

    # ------------------------------------------------------------------
    # Fitting
    # ------------------------------------------------------------------

    def fit(self, words: Sequence[Word]) -> TokenNGram:
        """Accumulate n-gram statistics from ``words``.

        Refitting replaces any previous state, so one instance is one model.

        Parameters
        ----------
        words : Sequence[Word]
            Training words. Tokens must be hashable; an empty word contributes
            only the ``BOS -> EOS`` transition. An empty corpus is rejected --
            a model with no vocabulary cannot sample.

        Returns
        -------
        TokenNGram
            ``self``, so the call chains.

        Raises
        ------
        isalhg.generation.errors.GenerationError
            If ``words`` is empty or numpy is missing.
        """
        np = _import_numpy()
        if len(words) == 0:
            raise GenerationError("cannot fit a TokenNGram on an empty corpus")

        counts: list[dict[tuple[Hashable, ...], dict[Hashable, int]]] = [
            {} for _ in range(self.order)
        ]
        continuation_pairs: set[tuple[tuple[Hashable, ...], Hashable]] = set()
        vocabulary: set[Hashable] = set()

        for word in words:
            padded = (*(BOS,) * (self.order - 1), *word, EOS)
            for position in range(self.order - 1, len(padded)):
                token = padded[position]
                vocabulary.add(token)
                for k in range(self.order):
                    context = padded[position - k : position]
                    bucket = counts[k].setdefault(context, {})
                    bucket[token] = bucket.get(token, 0) + 1
                    if k == 1:
                        continuation_pairs.add((context, token))

        vocabulary.discard(BOS)
        self._vocabulary = tuple(sorted(vocabulary, key=repr))
        self._index = {token: i for i, token in enumerate(self._vocabulary)}
        size = len(self._vocabulary)

        # Lowest order: add-one-smoothed continuation counts. For order 1 there
        # is no context to count distinct occurrences over, so the unigram
        # counts stand in.
        raw = np.zeros(size, dtype=np.float64)
        if self.order >= 2:
            for _, continued in continuation_pairs:
                index = self._index.get(continued)
                if index is not None:
                    raw[index] += 1.0
        else:
            for unigram, count in counts[0].get((), {}).items():
                index = self._index.get(unigram)
                if index is not None:
                    raw[index] += float(count)
        self._p0 = (raw + 1.0) / (raw.sum() + max(size, 1))

        self._levels = [self._build_level(counts[k], np) for k in range(self.order)]
        self.reset_cache()
        self._fitted = True
        return self

    def _build_level(
        self, buckets: dict[tuple[Hashable, ...], dict[Hashable, int]], np: Any
    ) -> dict[tuple[Hashable, ...], _Level]:
        """Turn raw counts at one order into ``(indices, discounted, backoff)`` records."""
        level: dict[tuple[Hashable, ...], _Level] = {}
        for context, bucket in buckets.items():
            pairs = [
                (self._index[token], count)
                for token, count in bucket.items()
                if token in self._index
            ]
            if not pairs:
                continue
            indices = np.fromiter((i for i, _ in pairs), dtype=np.int64, count=len(pairs))
            counts = np.fromiter((c for _, c in pairs), dtype=np.float64, count=len(pairs))
            total = float(counts.sum())
            distinct = float(len(pairs))
            if self.smoothing == "kneser_ney":
                discounted = np.maximum(counts - self.discount, 0.0) / total
                backoff = self.discount * distinct / total
            else:  # witten_bell
                denominator = total + distinct
                discounted = counts / denominator
                backoff = distinct / denominator
            level[context] = (indices, discounted, float(backoff))
        return level

    # ------------------------------------------------------------------
    # Distribution
    # ------------------------------------------------------------------

    def _require_fit(self) -> None:
        if not self._fitted:
            raise GenerationError("TokenNGram must be fitted before use; call fit(words) first")

    def reset_cache(self) -> None:
        """Empty the per-context distribution memo.

        The memo holds a deterministic function of the context, so dropping it
        costs recomputation and changes no sampled or scored value. Useful when
        one fitted model is reused across many sampling passes and the resident
        set matters more than the recomputation.
        """
        self._cache = OrderedDict()

    def _distribution(self, context: tuple[Hashable, ...]) -> NDArray[np.float64]:
        """Dense conditional distribution over the vocabulary given ``context``.

        The unrolled interpolation described in the module docstring: one pass
        from the longest matching context down to the shortest, accumulating
        each level's discounted mass scaled by the backoff masses above it, and
        finishing with the continuation distribution. Memoised per context in a
        bounded LRU; eviction only costs a recomputation of the same vector.
        """
        cached = self._cache.get(context)
        if cached is not None:
            self._cache.move_to_end(context)
            return cached  # type: ignore[no-any-return]

        np = _import_numpy()
        dense = np.zeros(len(self._vocabulary), dtype=np.float64)
        weight = 1.0
        for k in range(len(context), 0, -1):
            record = self._levels[k].get(context[len(context) - k :])
            if record is None:
                continue  # unseen context at this order: fall straight through
            indices, discounted, backoff = record
            dense[indices] += weight * discounted
            weight *= backoff
        dense += weight * self._p0

        total = dense.sum()
        if total > 0:
            dense /= total
        self._cache[context] = dense
        if self.cache_size is not None:
            while len(self._cache) > self.cache_size:
                self._cache.popitem(last=False)
        return dense  # type: ignore[no-any-return]

    def _context_of(self, history: Sequence[Hashable]) -> tuple[Hashable, ...]:
        """The ``order - 1`` tokens preceding the next position, ``BOS``-padded."""
        if self.order == 1:
            return ()
        padded = (*(BOS,) * (self.order - 1), *history)
        return tuple(padded[len(padded) - (self.order - 1) :])

    def logprob(self, word: Word) -> float:
        """Return the natural log-probability of ``word`` under the model.

        The word is scored as the model generates it: every token conditioned on
        the ``order - 1`` before it, then a final ``EOS``. Words of all lengths
        therefore share one distribution and their scores are comparable.

        Parameters
        ----------
        word : Word
            The word to score. A token outside the fitted vocabulary makes the
            whole word unreachable, so the score is ``-inf`` rather than an
            error -- that is the honest value, and callers filtering by
            likelihood want it to sort last.

        Returns
        -------
        float
            Natural log-probability; ``-inf`` iff ``word`` uses an unknown token.

        Raises
        ------
        isalhg.generation.errors.GenerationError
            If the model has not been fitted.
        """
        self._require_fit()
        history: list[Hashable] = []
        total = 0.0
        for token in (*word, EOS):
            index = self._index.get(token)
            if index is None:
                return -math.inf
            probability = float(self._distribution(self._context_of(history))[index])
            if probability <= 0.0:
                return -math.inf
            total += math.log(probability)
            history.append(token)
        return total

    # ------------------------------------------------------------------
    # Sampling
    # ------------------------------------------------------------------

    def _sample_one(self, rng: random.Random, prefix: Word, max_len: int) -> Word:
        """Continue ``prefix`` autoregressively until ``EOS`` or ``max_len``."""
        np = _import_numpy()
        out: list[Any] = list(prefix)
        while len(out) < max_len:
            dense = self._distribution(self._context_of(out))
            # Inverse-CDF draw off one uniform: the sampler must be reproducible
            # from a seeded random.Random, and numpy's Generator would be a
            # second, separately seeded source of randomness.
            cumulative = np.cumsum(dense)
            position = int(np.searchsorted(cumulative, rng.random() * float(cumulative[-1])))
            token = self._vocabulary[min(position, len(self._vocabulary) - 1)]
            if token == EOS:
                break
            out.append(token)
        return tuple(out)

    def sample(self, n_samples: int, *, seed: int, max_len: int = 200) -> list[Word]:
        """Draw ``n_samples`` words from the model.

        Deterministic in ``seed``: the same ``(model, n_samples, seed,
        max_len)`` yields the same list, which is what makes RQ6's 27-seed
        replication reproducible.

        Parameters
        ----------
        n_samples : int
            How many words to draw. Must be non-negative.
        seed : int
            Seed of a private :class:`random.Random`; no global state is
            touched.
        max_len : int, optional
            Hard cap on the tokens per sample. Defaults to 200.

        Returns
        -------
        list[Word]
            The sampled words, each a tuple of tokens, none containing ``EOS``.

        Raises
        ------
        isalhg.generation.errors.GenerationError
            If the model is unfitted, ``n_samples`` is negative, or ``max_len``
            is not positive.
        """
        self._require_fit()
        if n_samples < 0:
            raise GenerationError(f"n_samples must be non-negative; got {n_samples}")
        if max_len < 1:
            raise GenerationError(f"max_len must be positive; got {max_len}")

        rng = random.Random(seed)
        return [self._sample_one(rng, (), max_len) for _ in range(n_samples)]

    def complete(self, prefix: Word, *, seed: int, max_len: int = 200) -> Word:
        """Extend ``prefix`` autoregressively and return the whole word.

        The result starts with ``prefix`` verbatim -- RQ6's conditional exhibit
        asks what the model would write after a truncated knowledge base, so the
        given part must survive intact.

        Parameters
        ----------
        prefix : Word
            The tokens to condition on. May be empty, in which case this is one
            unconditional sample.
        seed : int
            Seed of a private :class:`random.Random`.
        max_len : int, optional
            Cap on the *total* length, prefix included. A prefix already at or
            beyond the cap is returned unchanged.

        Returns
        -------
        Word
            ``prefix`` followed by the sampled continuation.

        Raises
        ------
        isalhg.generation.errors.GenerationError
            If the model is unfitted or ``max_len`` is not positive.
        """
        self._require_fit()
        if max_len < 1:
            raise GenerationError(f"max_len must be positive; got {max_len}")
        return self._sample_one(random.Random(seed), tuple(prefix), max_len)

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def vocabulary(self) -> tuple[Hashable, ...]:
        """The distinct tokens seen during :meth:`fit`, ``EOS`` included, ``BOS`` excluded."""
        return self._vocabulary

    def __repr__(self) -> str:
        state = f"|V|={len(self._vocabulary)}" if self._fitted else "unfitted"
        return f"TokenNGram(order={self.order}, smoothing={self.smoothing!r}, {state})"


def words_of(hypergraphs: Iterable[Any], roles: Iterable[Any] | None = None) -> list[Word]:
    """Fact words of ``hypergraphs``, optionally under their roles maps.

    A convenience for the RQ6 runner so the fitting corpus is built the same way
    in every arm.

    Parameters
    ----------
    hypergraphs : Iterable[SparseHypergraph]
        The collection members.
    roles : Iterable[RolesMap or None] or None, optional
        Aligned roles maps. ``None`` (default) encodes every member role-free.

    Returns
    -------
    list[Word]
        One word per member, in the order given.
    """
    from isalhg.metric_space.distances.fact_levenshtein import fact_word

    members = list(hypergraphs)
    if roles is None:
        return [fact_word(H) for H in members]
    return [fact_word(H, r) for H, r in zip(members, list(roles), strict=True)]


__all__ = ["BOS", "DEFAULT_CACHE_SIZE", "EOS", "SMOOTHINGS", "TokenNGram", "words_of"]
