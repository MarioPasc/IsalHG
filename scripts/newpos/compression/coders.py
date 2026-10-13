"""Per-member coders: the learned n-gram code with one escape scheme, and CV folds.

The fixed-width coder lives next to the alphabets (``serialize.fixed_width_bits``).
This module holds the held-out cross-entropy coder. ``TokenNGram`` (Kneser-Ney,
absolute discount 0.75) puts probability only on tokens seen in training, so a
held-out token outside the training vocabulary needs an escape. The scheme is the
same for every arm:

* ``eps = (n1 + 1) / (N + 1)``, with ``N`` the coded events (tokens plus one end
  event per word) of the training folds and ``n1`` the token types that occurred
  exactly once: a Good-Turing estimate of the missing mass with an add-one floor;
* a seen token costs ``-log2((1 - eps) q(t | h))`` with ``q`` the library's own
  conditional distribution;
* an unseen token costs ``-log2(eps) + log2(U)`` with ``U = max(|A| - |V_train|, 1)``,
  uniform over the alphabet tokens the training folds never produced, where ``|A|``
  is the whole-collection alphabet (observed, or theoretical for the second column)
  that the fixed-width coder is also told.

Model parameters are not charged: the code length is held-out cross-entropy.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Hashable, Sequence
from dataclasses import dataclass

import numpy as np

from isalhg.generation.ngram import EOS, TokenNGram

Symbol = Hashable


@dataclass(frozen=True)
class ScoredWord:
    """Components of the code length of one held-out word.

    Attributes
    ----------
    core_bits : float
        ``-sum log2 q(t | h)`` over the seen tokens and the end event.
    n_seen, n_unseen : int
        Coded events inside / outside the training vocabulary.
    bits_obs, bits_theo : float
        Total bits with the escape priced against the observed / theoretical alphabet.
    """

    core_bits: float
    n_seen: int
    n_unseen: int
    bits_obs: float
    bits_theo: float


def kfold_assignment(n_items: int, n_folds: int, seed: int) -> list[np.ndarray]:
    """Seeded partition of ``range(n_items)`` into ``n_folds`` near-equal folds."""
    order = np.random.default_rng(seed).permutation(n_items)
    return [np.sort(fold) for fold in np.array_split(order, n_folds)]


def _cache_size(vocab_size: int) -> int:
    """LRU entries for the per-context memo, bounded near 150 MB."""
    return int(min(100_000, max(128, 1.5e8 / (8 * max(vocab_size, 1)))))


class EscapedNGram:
    """A fitted ``TokenNGram`` plus the escape scheme above.

    Parameters
    ----------
    order : int
        N-gram order (context length plus one).
    alphabet_obs, alphabet_theo : int
        Whole-collection alphabet sizes used for the uniform escape.
    """

    def __init__(self, order: int, alphabet_obs: int, alphabet_theo: int) -> None:
        self.order = order
        self.alphabet_obs = alphabet_obs
        self.alphabet_theo = alphabet_theo
        self.model: TokenNGram | None = None
        self.eps = 0.0
        self.n_train_tokens = 0

    def fit(self, words: Sequence[Sequence[Symbol]]) -> EscapedNGram:
        """Fit the n-gram and the escape probability on the training words."""
        tuples = [tuple(w) for w in words]
        counts: Counter[Symbol] = Counter()
        for w in tuples:
            counts.update(w)
        events = sum(len(w) + 1 for w in tuples)
        n1 = sum(1 for c in counts.values() if c == 1)
        self.eps = (n1 + 1) / (events + 1)
        vocab = len(counts) + 1
        self.model = TokenNGram(order=self.order, cache_size=_cache_size(vocab)).fit(tuples)
        self.n_train_tokens = len(counts)
        return self

    def score(self, word: Sequence[Symbol]) -> ScoredWord:
        """Code length of ``word`` (end event included) under the escaped model."""
        model = self.model
        if model is None:
            raise RuntimeError("EscapedNGram.score called before fit")
        index = model._index  # noqa: SLF001 - the library exposes no per-token probability
        history: list[Symbol] = []
        core = 0.0
        n_seen = n_unseen = 0
        for token in (*word, EOS):
            position = index.get(token)
            if position is None:
                n_unseen += 1
            else:
                dist = model._distribution(model._context_of(history))  # noqa: SLF001
                core -= math.log2(float(dist[position]))
                n_seen += 1
            history.append(token)
        seen_cost = -math.log2(1.0 - self.eps)
        escape = -math.log2(self.eps)
        u_obs = max(self.alphabet_obs - self.n_train_tokens, 1)
        u_theo = max(self.alphabet_theo - self.n_train_tokens, 1)
        base = core + n_seen * seen_cost + n_unseen * escape
        return ScoredWord(
            core_bits=core,
            n_seen=n_seen,
            n_unseen=n_unseen,
            bits_obs=base + n_unseen * math.log2(u_obs),
            bits_theo=base + n_unseen * math.log2(u_theo),
        )


def cross_validated_bits(
    sequences: Sequence[Sequence[Symbol]],
    *,
    order: int,
    seed: int,
    alphabet_obs: int,
    alphabet_theo: int,
    n_folds: int = 5,
) -> list[ScoredWord]:
    """Held-out code length of every sequence under a ``n_folds``-fold CV.

    Parameters
    ----------
    sequences : Sequence[Sequence[Hashable]]
        One symbol sequence per member.
    order : int
        N-gram order.
    seed : int
        Fold-assignment seed.
    alphabet_obs, alphabet_theo : int
        Whole-collection alphabet sizes for the escape.
    n_folds : int, optional
        Number of folds; each member is coded by a model that never saw it.

    Returns
    -------
    list[ScoredWord]
        One score per member, in member order.
    """
    folds = kfold_assignment(len(sequences), n_folds, seed)
    scored: list[ScoredWord | None] = [None] * len(sequences)
    for held_out in folds:
        held = set(int(i) for i in held_out)
        train = [sequences[i] for i in range(len(sequences)) if i not in held]
        coder = EscapedNGram(order, alphabet_obs, alphabet_theo).fit(train)
        for i in held_out:
            scored[int(i)] = coder.score(sequences[int(i)])
    return [s for s in scored if s is not None]
