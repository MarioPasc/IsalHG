"""Seeded fact-level corruptions of real members (RQ4, supplementary S3).

Four corruption kinds, all pure functions of ``(record, budget, seed)`` and all
verified non-isomorphic to the original before they are returned:

``spurious_fact``
    ``budget`` facts over existing constants that are not in the member.
``missing_fact``
    ``budget`` facts removed; a constant left with no fact leaves the knowledge
    base (the record is compacted).
``wrong_argument``
    ``budget`` times, one argument of one fact replaced by another constant,
    the fact staying distinct from every other.
``iso_twin``
    degree-preserving 2-fact swaps applied until the result is non-isomorphic
    to the original. The twin matches the member on ``n``, ``m``, the arity
    histogram, the degree sequence, the type multiset and the predicate
    multiset -- every statistic an incomplete representation can see. The
    depth-1 refinement-colour histogram equality is recorded as
    ``meta["wl1_equal"]`` and reported, not enforced.
"""

from __future__ import annotations

import random
from collections import Counter
from typing import Any

from isalhg.datasets.kb.base import (
    DEFAULT_ENVELOPE,
    Envelope,
    Fact,
    KBRecord,
    compact,
    iso_fingerprint,
    make_record,
)

CORRUPTION_KINDS: tuple[str, ...] = (
    "spurious_fact",
    "missing_fact",
    "wrong_argument",
    "iso_twin",
)

_ATTEMPTS = 200
_TWIN_SWAPS_MAX = 64


def wl1_histogram(record: KBRecord) -> Counter[tuple[Any, ...]]:
    """Depth-1 refinement-colour histogram of a record.

    The colour of a constant is its type together with the sorted multiset of
    ``(predicate, arity)`` of the facts it occurs in -- one round of the
    hypergraph colour refinement, which is exactly what a depth-1 WL descriptor
    of the labelled knowledge base sees.

    Parameters
    ----------
    record : KBRecord
        The record to colour.

    Returns
    -------
    Counter
        Colour -> number of constants carrying it.
    """
    incident: list[list[tuple[int, int]]] = [[] for _ in range(record.n)]
    for pred, members in record.facts:
        for v in members:
            incident[v].append((pred, len(members)))
    return Counter((record.types[v], tuple(sorted(incident[v]))) for v in range(record.n))


def _arity_pool(record: KBRecord) -> list[int]:
    return sorted({len(members) for _, members in record.facts})


def _spurious(
    record: KBRecord, budget: int, rng: random.Random, envelope: Envelope
) -> list[Fact] | None:
    facts = list(record.facts)
    existing = set(facts)
    added = 0
    for _ in range(_ATTEMPTS):
        if added == budget:
            return facts
        arity = max(2, min(rng.choice(_arity_pool(record)), record.n, envelope.k_max))
        candidate: Fact = (
            rng.randrange(record.n_preds),
            tuple(sorted(rng.sample(range(record.n), arity))),
        )
        if candidate in existing or len(facts) + 1 > envelope.m_max:
            continue
        existing.add(candidate)
        facts.append(candidate)
        added += 1
    return facts if added == budget else None


def _missing(record: KBRecord, budget: int, rng: random.Random) -> list[Fact] | None:
    if record.m - budget < 1:
        return None
    keep = list(record.facts)
    for _ in range(budget):
        keep.pop(rng.randrange(len(keep)))
    return keep


def _wrong_argument(record: KBRecord, budget: int, rng: random.Random) -> list[Fact] | None:
    facts = list(record.facts)
    changed = 0
    for _ in range(_ATTEMPTS):
        if changed == budget:
            return facts
        index = rng.randrange(len(facts))
        pred, members = facts[index]
        outside = [v for v in range(record.n) if v not in members]
        if not outside:
            continue
        leaving = rng.choice(members)
        entrant = rng.choice(outside)
        candidate: Fact = (
            pred,
            tuple(sorted((*(v for v in members if v != leaving), entrant))),
        )
        if any(candidate == f for i, f in enumerate(facts) if i != index):
            continue
        facts[index] = candidate
        changed += 1
    return facts if changed == budget else None


def _one_swap(facts: list[Fact], rng: random.Random) -> bool:
    """Attempt one degree-preserving 2-fact swap in place; report success."""
    if len(facts) < 2:
        return False
    for _ in range(_ATTEMPTS):
        i, j = rng.sample(range(len(facts)), 2)
        (pred_i, members_i), (pred_j, members_j) = facts[i], facts[j]
        only_i = [v for v in members_i if v not in members_j]
        only_j = [v for v in members_j if v not in members_i]
        if not only_i or not only_j:
            continue
        v1, v2 = rng.choice(only_i), rng.choice(only_j)
        new_i: Fact = (pred_i, tuple(sorted((*(v for v in members_i if v != v1), v2))))
        new_j: Fact = (pred_j, tuple(sorted((*(v for v in members_j if v != v2), v1))))
        clash = any(f in (new_i, new_j) for k, f in enumerate(facts) if k not in (i, j))
        if clash:
            continue
        facts[i], facts[j] = new_i, new_j
        return True
    return False


def _iso_twin(
    record: KBRecord, rng: random.Random, base_fingerprint: bytes
) -> tuple[list[Fact], int] | None:
    facts = list(record.facts)
    for swaps in range(1, _TWIN_SWAPS_MAX + 1):
        if not _one_swap(facts, rng):
            return None
        candidate = make_record(
            "probe",
            record.n,
            record.types,
            facts,
            meta={"n_types": record.n_types, "n_preds": record.n_preds},
            require_connected=False,
        )
        if candidate is None:
            return None
        if iso_fingerprint(candidate) != base_fingerprint:
            return list(candidate.facts), swaps
    return None


def corrupt(
    record: KBRecord,
    kind: str,
    budget: int,
    seed: int,
    *,
    envelope: Envelope = DEFAULT_ENVELOPE,
) -> KBRecord | None:
    """Inject one corruption of ``kind`` at ``budget`` into ``record``.

    Parameters
    ----------
    record : KBRecord
        The real member to corrupt. Roles are dropped: a corruption changes
        operand tuples and there is no principled role for a synthesised one.
    kind : str
        One of :data:`CORRUPTION_KINDS`.
    budget : int
        Number of elementary corruptions (1 or 2 in the design). Ignored by
        ``iso_twin``, which applies as many swaps as non-isomorphy needs and
        records how many it took.
    seed : int
        Seed of the local ``random.Random``.
    envelope : Envelope, optional
        Upper walls the result must respect.

    Returns
    -------
    KBRecord or None
        The corrupted member, carrying the original's identities and label and
        a ``meta`` with ``base_id``, ``corruption``, ``budget``, ``seed``,
        ``noniso_verified``, ``constant_set_preserved`` and ``connected``
        (plus ``wl1_equal`` and ``n_swaps`` for ``iso_twin``). ``None`` when
        the corruption could not be realised -- the caller counts the drop.

    Raises
    ------
    ValueError
        If ``kind`` is not a corruption kind, or ``budget`` is not positive.
    """
    if kind not in CORRUPTION_KINDS:
        raise ValueError(f"unknown corruption kind {kind!r}; expected one of {CORRUPTION_KINDS}")
    if budget < 1:
        raise ValueError(f"budget must be >= 1, got {budget}")
    if record.m == 0:
        return None
    rng = random.Random(seed)
    base_fingerprint = iso_fingerprint(record)
    meta: dict[str, Any] = {
        "base_id": record.kb_id,
        "corruption": kind,
        "budget": budget,
        "seed": seed,
        "n_types": record.n_types,
        "n_preds": record.n_preds,
    }
    kb_id = f"{record.kb_id}#{kind}b{budget}s{seed}"

    n_swaps = 0
    if kind == "spurious_fact":
        facts = _spurious(record, budget, rng, envelope)
    elif kind == "missing_fact":
        facts = _missing(record, budget, rng)
    elif kind == "wrong_argument":
        facts = _wrong_argument(record, budget, rng)
    else:
        twin = _iso_twin(record, rng, base_fingerprint)
        if twin is None:
            return None
        facts, n_swaps = twin
    if facts is None:
        return None

    result = compact(
        kb_id,
        record.types,
        facts,
        constant_ids=record.constant_ids,
        label=record.label,
        meta=meta,
        require_connected=False,
    )
    if result is None or result.n > envelope.n_max or result.max_arity > envelope.k_max:
        return None
    if iso_fingerprint(result) == base_fingerprint:
        return None

    final = dict(result.meta)
    final["noniso_verified"] = True
    final["constant_set_preserved"] = result.n == record.n
    final["connected"] = result.is_connected()
    if kind == "iso_twin":
        final["n_swaps"] = n_swaps
        final["wl1_equal"] = wl1_histogram(result) == wl1_histogram(record)
        final["invariants_preserved"] = (
            result.n == record.n
            and result.m == record.m
            and result.arity_histogram() == record.arity_histogram()
            and result.degree_sequence() == record.degree_sequence()
            and Counter(result.types) == Counter(record.types)
            and Counter(p for p, _ in result.facts) == Counter(p for p, _ in record.facts)
        )
    return KBRecord(
        kb_id=result.kb_id,
        n=result.n,
        types=result.types,
        facts=result.facts,
        constant_ids=result.constant_ids,
        label=result.label,
        meta=final,
    )
