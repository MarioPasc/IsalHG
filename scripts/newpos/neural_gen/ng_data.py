"""Serializations, vocabularies, member splits and batching for the NEWPOS GRU experiment.

Stdlib only (no torch): the batching helpers return plain lists so the torch module
owns every tensor.
"""

from __future__ import annotations

import random
from collections.abc import Hashable, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

#: Serialization name -> generator name written into the sample files.
SERIALIZATIONS: tuple[str, ...] = ("ow", "fact", "incidence")
GENERATOR_NAMES: dict[str, str] = {
    "ow": "gru_ow",
    "fact": "gru_fact",
    "incidence": "gru_incidence",
}

PAD = 0
BOS = 1
EOS = 2
N_SPECIAL = 3

TRAIN_FRACTION = 0.8
VAL_FRACTION = 0.1


class NeuralGenError(Exception):
    """Root of the exceptions raised by the NEWPOS GRU experiment."""


class VocabularyError(NeuralGenError):
    """A token or id is outside the vocabulary."""


class SplitError(NeuralGenError):
    """The member split cannot be formed."""


class CollectionLike(Protocol):
    """The attributes of ``rq6.CollectionContext`` this experiment reads."""

    name: str
    hypergraphs: list[Any]
    words: list[Any]
    flat: list[Any]
    ow_words: list[Any]
    ow_roots: list[int]
    n_types: int
    n_preds: int
    k: int


@dataclass(frozen=True)
class Vocabulary:
    """Bijection between the original token objects and contiguous ids.

    Ids ``0, 1, 2`` are PAD, BOS and EOS; token ``i`` of ``tokens`` has id
    ``i + N_SPECIAL``. The original objects are kept so a sampled id maps back to
    exactly the token the decoder expects, not to a re-parsed string.
    """

    tokens: tuple[Hashable, ...]
    index: dict[Hashable, int]

    @classmethod
    def fit(cls, sequences: Sequence[Sequence[Hashable]]) -> Vocabulary:
        """Collect every distinct token in first-appearance order.

        Parameters
        ----------
        sequences : Sequence[Sequence[Hashable]]
            Every sequence of the whole collection (not only the training split).

        Returns
        -------
        Vocabulary
            Deterministic for a fixed member order.
        """
        seen: dict[Hashable, int] = {}
        for sequence in sequences:
            for token in sequence:
                if token not in seen:
                    seen[token] = len(seen) + N_SPECIAL
        return cls(tokens=tuple(seen), index=seen)

    def __len__(self) -> int:
        """Number of ids including the three specials."""
        return len(self.tokens) + N_SPECIAL

    def encode(self, sequence: Sequence[Hashable]) -> list[int]:
        """Map a token sequence to ids.

        Raises
        ------
        VocabularyError
            If a token is not in the vocabulary.
        """
        try:
            return [self.index[token] for token in sequence]
        except KeyError as exc:
            raise VocabularyError(f"token {exc.args[0]!r} is not in the vocabulary") from exc

    def decode(self, ids: Sequence[int]) -> tuple[Hashable, ...]:
        """Map ids (no specials) back to the original token objects.

        Raises
        ------
        VocabularyError
            If an id is a special or out of range.
        """
        out: list[Hashable] = []
        for i in ids:
            if not N_SPECIAL <= i < len(self):
                raise VocabularyError(f"id {i} is not a token id of a {len(self)}-id vocabulary")
            out.append(self.tokens[i - N_SPECIAL])
        return tuple(out)


def serialization_sequences(ctx: CollectionLike, serialization: str) -> list[Any]:
    """Return the per-member token sequences of one serialization, in member order.

    Taken verbatim from the n-gram experiment's collection context so the GRU and
    the n-gram model see the same sequences.

    Raises
    ------
    NeuralGenError
        If ``serialization`` is unknown.
    """
    if serialization == "ow":
        return list(ctx.ow_words)
    if serialization == "fact":
        return list(ctx.words)
    if serialization == "incidence":
        return list(ctx.flat)
    raise NeuralGenError(
        f"unknown serialization {serialization!r}; expected one of {SERIALIZATIONS}"
    )


def split_members(
    n_members: int, collection: str, seed: int
) -> tuple[list[int], list[int], list[int]]:
    """Seeded 80/10/10 split of member indices.

    The split depends on ``(collection, seed)`` only, so the three serializations of
    one seed are trained and tested on the same members.

    Parameters
    ----------
    n_members : int
        Collection size.
    collection : str
        Collection name; part of the RNG key.
    seed : int
        Unit seed.

    Returns
    -------
    tuple[list[int], list[int], list[int]]
        ``(train, val, test)`` index lists, each sorted.

    Raises
    ------
    SplitError
        If a split would be empty.
    """
    n_val = max(1, round(VAL_FRACTION * n_members))
    n_test = max(1, round(VAL_FRACTION * n_members))
    n_train = n_members - n_val - n_test
    if n_train < 1:
        raise SplitError(f"{n_members} members cannot form a non-empty 80/10/10 split")
    order = list(range(n_members))
    random.Random(f"newpos-gru-split|{collection}|{seed}").shuffle(order)
    train = sorted(order[:n_train])
    val = sorted(order[n_train : n_train + n_val])
    test = sorted(order[n_train + n_val :])
    return train, val, test


@dataclass(frozen=True)
class Batch:
    """One right-padded batch; ``inputs`` start with BOS, ``targets`` end with EOS."""

    inputs: list[list[int]]
    targets: list[list[int]]
    lengths: list[int]


def make_batch(id_sequences: Sequence[Sequence[int]]) -> Batch:
    """Right-pad a list of id sequences into an input/target pair.

    Padding positions hold ``PAD`` in both lists; the consumer masks them with
    ``lengths`` (``len(sequence) + 1`` real positions per row, the extra one being
    the EOS target).
    """
    lengths = [len(s) + 1 for s in id_sequences]
    width = max(lengths)
    inputs = [[BOS, *s] + [PAD] * (width - len(s) - 1) for s in id_sequences]
    targets = [[*s, EOS] + [PAD] * (width - len(s) - 1) for s in id_sequences]
    return Batch(inputs=inputs, targets=targets, lengths=lengths)


def epoch_batches(
    id_sequences: Sequence[Sequence[int]],
    batch_size: int,
    rng: random.Random | None,
) -> list[Batch]:
    """Batches of one epoch: shuffled when ``rng`` is given, else length-sorted.

    The length-sorted order is for evaluation, where it only saves padding.
    """
    order = list(range(len(id_sequences)))
    if rng is not None:
        rng.shuffle(order)
    else:
        order.sort(key=lambda i: len(id_sequences[i]))
    return [
        make_batch([id_sequences[i] for i in order[start : start + batch_size]])
        for start in range(0, len(order), batch_size)
    ]
