"""Seeded edit generators: single edits, ladders, and variant collections.

Three generators, all pure functions of ``(record, parameters, seed)``:

``single_edits``
    RQ1 M1 -- the five structural edit kinds, applied once, with the
    pre-registered rejection rules (result connected where required, inside the
    envelope, not isomorphic to the base, distinct among themselves).
``constant_preserving_ladder``
    RQ1 M2(b) -- cumulative fact insert / delete walks with the constant set
    held fixed, so ``delta = |F_0 triangle F_t|`` is exact.
``variant_collection``
    RQ3 Corpus A -- ``N`` members, each ``t`` independent fact edits of one
    source, pairwise non-isomorphic and non-isomorphic to the source.  The
    constant set is *not* held fixed: a deletion that takes the last fact
    naming a constant removes the constant, so members of one collection may
    differ in constant count.

Ported from ``scripts/diagnostics/d_art3_probes_2026-09-03/f4_topology/f4_corpora.py``
(``apply_edit``, ``sample_edits``, ``_stable_step``, ``random_walk``).

Envelope semantics for *edit results*: the upper walls (``n_max``, ``m_max``,
``k_max``) are enforced, the fact floor ``m_min`` is not. ``m_min`` is a
corpus-*selection* rule -- the median NDC-classes member holds exactly three
facts, so enforcing it on results would make ``delete_fact`` impossible there
and would not reproduce the probe the RQ1 gate is measured against. An edit
that introduces a constant is allowed to reach ``max(n_max, n + 1)`` for the
same reason.
"""

from __future__ import annotations

import random
from collections.abc import Sequence
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

EDIT_KINDS: tuple[str, ...] = (
    "insert_fact",
    "delete_fact",
    "add_constant",
    "remove_constant",
    "insert_fact_new_constant",
)

VARIANT_KINDS: tuple[str, ...] = ("ins", "del", "mix")

_ATTEMPTS_PER_EDIT = 40
_STEP_ATTEMPTS = 80
_COLLECTION_ATTEMPTS = 50


def _arity_pool(record: KBRecord) -> list[int]:
    return sorted({len(members) for _, members in record.facts})


def _within_upper_walls(record: KBRecord, envelope: Envelope, n_limit: int) -> bool:
    return record.n <= n_limit and record.m <= envelope.m_max and record.max_arity <= envelope.k_max


def _new_constant_id(record: KBRecord) -> str | None:
    if record.constant_ids is None:
        return None
    return f"{record.kb_id}::new{record.n}"


def _apply_edit(
    record: KBRecord,
    kind: str,
    rng: random.Random,
    envelope: Envelope,
    *,
    kb_id: str,
    require_connected: bool,
) -> KBRecord | None:
    """Apply one edit of ``kind``; ``None`` when the attempt is invalid."""
    facts = list(record.facts)
    types = list(record.types)
    ids = None if record.constant_ids is None else list(record.constant_ids)
    existing = set(facts)
    meta: dict[str, Any] = {
        "base_id": record.kb_id,
        "edit_kind": kind,
        "n_types": record.n_types,
        "n_preds": record.n_preds,
    }

    if kind == "insert_fact":
        arity = max(2, min(rng.choice(_arity_pool(record)), record.n, envelope.k_max))
        candidate: Fact = (
            rng.randrange(record.n_preds),
            tuple(sorted(rng.sample(range(record.n), arity))),
        )
        if candidate in existing:
            return None
        meta["edit"] = {"op": "insert_fact", "fact": list(candidate[1]), "pred": candidate[0]}
        return make_record(
            kb_id,
            record.n,
            types,
            [*facts, candidate],
            constant_ids=ids,
            label=record.label,
            meta=meta,
            require_connected=require_connected,
        )

    if kind == "delete_fact":
        if record.m <= 1:
            return None
        index = rng.randrange(record.m)
        meta["edit"] = {"op": "delete_fact", "fact_index": index}
        return compact(
            kb_id,
            types,
            [f for i, f in enumerate(facts) if i != index],
            constant_ids=ids,
            label=record.label,
            meta=meta,
            require_connected=require_connected,
        )

    if kind == "add_constant":
        index = rng.randrange(record.m)
        pred, members = facts[index]
        outside = [v for v in range(record.n) if v not in members]
        if not outside or len(members) >= envelope.k_max:
            return None
        entrant = rng.choice(outside)
        candidate = (pred, tuple(sorted((*members, entrant))))
        if candidate in existing:
            return None
        facts[index] = candidate
        meta["edit"] = {"op": "add_constant", "fact_index": index, "constant": entrant}
        return make_record(
            kb_id,
            record.n,
            types,
            facts,
            constant_ids=ids,
            label=record.label,
            meta=meta,
            require_connected=require_connected,
        )

    if kind == "remove_constant":
        wide = [i for i, (_, members) in enumerate(facts) if len(members) >= 3]
        if not wide:
            return None
        index = rng.choice(wide)
        pred, members = facts[index]
        leaving = rng.choice(members)
        candidate = (pred, tuple(v for v in members if v != leaving))
        if candidate in existing:
            return None
        facts[index] = candidate
        meta["edit"] = {"op": "remove_constant", "fact_index": index, "constant": leaving}
        return compact(
            kb_id,
            types,
            facts,
            constant_ids=ids,
            label=record.label,
            meta=meta,
            require_connected=require_connected,
        )

    if kind == "insert_fact_new_constant":
        arity = max(2, min(rng.choice(_arity_pool(record)), record.n + 1, envelope.k_max))
        entrant = record.n
        others = rng.sample(range(record.n), arity - 1)
        candidate = (rng.randrange(record.n_preds), tuple(sorted((entrant, *others))))
        meta["edit"] = {"op": "insert_fact_new_constant", "constant": entrant}
        new_id = _new_constant_id(record)
        return make_record(
            kb_id,
            record.n + 1,
            [*types, rng.randrange(record.n_types)],
            [*facts, candidate],
            constant_ids=None if ids is None or new_id is None else [*ids, new_id],
            label=record.label,
            meta=meta,
            require_connected=require_connected,
        )

    raise ValueError(f"unknown edit kind {kind!r}")


def _stamp_regime(base: KBRecord, edited: KBRecord) -> KBRecord:
    """Attach the regime flag; no edit kind both drops and adds a constant."""
    preserved = edited.n == base.n
    if base.constant_ids is not None and edited.constant_ids is not None:
        preserved = set(base.constant_ids) == set(edited.constant_ids)
    meta = dict(edited.meta)
    meta["constant_set_preserved"] = preserved
    return KBRecord(
        kb_id=edited.kb_id,
        n=edited.n,
        types=edited.types,
        facts=edited.facts,
        roles=edited.roles,
        constant_ids=edited.constant_ids,
        label=edited.label,
        meta=meta,
    )


def single_edits(
    record: KBRecord,
    kind: str,
    count: int,
    seed: int,
    *,
    require_connected: bool = True,
    envelope: Envelope = DEFAULT_ENVELOPE,
) -> list[KBRecord]:
    """Sample up to ``count`` distinct single edits of one kind (RQ1 M1).

    Parameters
    ----------
    record : KBRecord
        The base knowledge base. Roles are dropped: an edit changes the operand
        tuple, and there is no principled role for a synthesised operand.
    kind : str
        One of :data:`EDIT_KINDS`.
    count : int
        How many distinct results to return.
    seed : int
        Seed of the local ``random.Random``; the output is a pure function of
        ``(record, kind, count, seed, require_connected, envelope)``.
    require_connected : bool, optional
        Reject a result that is disconnected or leaves a constant isolated.
    envelope : Envelope, optional
        Upper walls the result must respect (see the module docstring for why
        ``m_min`` is not applied to results).

    Returns
    -------
    list[KBRecord]
        Between 0 and ``count`` records, pairwise structurally distinct and
        none isomorphic to ``record``. Each carries ``base_id``, ``edit_kind``,
        ``edit_idx``, ``edit`` and ``constant_set_preserved`` in ``meta``, and
        the base's ``constant_ids`` (restricted or extended by the edit).

    Raises
    ------
    ValueError
        If ``kind`` is not an edit kind.
    """
    if kind not in EDIT_KINDS:
        raise ValueError(f"unknown edit kind {kind!r}; expected one of {EDIT_KINDS}")
    if count <= 0 or record.m == 0:
        return []
    rng = random.Random(seed)
    n_limit = max(envelope.n_max, record.n + 1)
    base_fingerprint = iso_fingerprint(record)
    seen: set[tuple[int, tuple[int, ...], tuple[Fact, ...]]] = set()
    out: list[KBRecord] = []
    for _ in range(_ATTEMPTS_PER_EDIT * count):
        if len(out) >= count:
            break
        candidate = _apply_edit(
            record,
            kind,
            rng,
            envelope,
            kb_id=f"{record.kb_id}#{kind}{len(out)}s{seed}",
            require_connected=require_connected,
        )
        if candidate is None or not _within_upper_walls(candidate, envelope, n_limit):
            continue
        if candidate.key() in seen:
            continue
        if iso_fingerprint(candidate) == base_fingerprint:
            continue
        seen.add(candidate.key())
        meta = dict(candidate.meta)
        meta["edit_idx"] = len(out)
        meta["seed"] = seed
        out.append(
            _stamp_regime(
                record,
                KBRecord(
                    kb_id=f"{record.kb_id}#{kind}{len(out)}s{seed}",
                    n=candidate.n,
                    types=candidate.types,
                    facts=candidate.facts,
                    constant_ids=candidate.constant_ids,
                    label=candidate.label,
                    meta=meta,
                ),
            )
        )
    return out


def _stable_step(
    record: KBRecord, rng: random.Random, envelope: Envelope, *, force: str | None = None
) -> tuple[list[Fact], str] | None:
    """One fact insertion or deletion that leaves the constant set unchanged."""
    facts = list(record.facts)
    insert = force == "ins" or (
        force is None and (rng.random() < 0.5 or record.m <= envelope.m_min)
    )
    if force == "del":
        insert = False
    if insert:
        arity = max(2, min(rng.choice(_arity_pool(record)), record.n, envelope.k_max))
        candidate: Fact = (
            rng.randrange(record.n_preds),
            tuple(sorted(rng.sample(range(record.n), arity))),
        )
        if candidate in set(facts) or record.m + 1 > envelope.m_max:
            return None
        return [*facts, candidate], "ins"
    if record.m <= 1:
        return None
    index = rng.randrange(record.m)
    return [f for i, f in enumerate(facts) if i != index], "del"


def constant_preserving_ladder(
    record: KBRecord,
    t_max: int,
    seed: int,
    *,
    envelope: Envelope = DEFAULT_ENVELOPE,
) -> list[KBRecord]:
    """Cumulative constant-preserving fact edits, one record per rung (RQ1 M2b).

    The constant set is held fixed and every rung stays connected, so the
    fact-level difference to the base is exact: ``delta = |F_0 triangle F_t|``,
    reported in each rung's ``meta``.

    Parameters
    ----------
    record : KBRecord
        The base of the ladder.
    t_max : int
        Number of rungs to attempt; ``t = 1 .. t_max``.
    seed : int
        Seed of the local ``random.Random``.
    envelope : Envelope, optional
        Upper walls the rungs must respect.

    Returns
    -------
    list[KBRecord]
        The rungs reached, in increasing ``t``; shorter than ``t_max`` (possibly
        empty) when the walk gets stuck. Each rung's ``meta`` carries ``t``,
        ``delta``, ``base_id``, ``seed`` and ``constant_set_preserved = True``.
    """
    if t_max <= 0 or record.m == 0:
        return []
    rng = random.Random(seed)
    base_facts = record.fact_set()
    current = record
    rungs: list[KBRecord] = []
    for t in range(1, t_max + 1):
        nxt: KBRecord | None = None
        for _ in range(_STEP_ATTEMPTS):
            step = _stable_step(current, rng, envelope)
            if step is None:
                continue
            facts, op = step
            candidate = make_record(
                f"{record.kb_id}#t{t}s{seed}",
                record.n,
                record.types,
                facts,
                constant_ids=record.constant_ids,
                label=record.label,
                meta={
                    "base_id": record.kb_id,
                    "t": t,
                    "seed": seed,
                    "last_op": op,
                    "constant_set_preserved": True,
                    "n_types": record.n_types,
                    "n_preds": record.n_preds,
                },
                require_connected=True,
            )
            if candidate is None or candidate.facts == current.facts:
                continue
            nxt = candidate
            break
        if nxt is None:
            break
        meta = dict(nxt.meta)
        meta["delta"] = len(base_facts ^ nxt.fact_set())
        current = KBRecord(
            kb_id=nxt.kb_id,
            n=nxt.n,
            types=nxt.types,
            facts=nxt.facts,
            constant_ids=nxt.constant_ids,
            label=nxt.label,
            meta=meta,
        )
        rungs.append(current)
    return rungs


def _identity_facts(record: KBRecord) -> frozenset[tuple[int, frozenset[str]]] | None:
    """Return ``record``'s facts addressed by external identity, or ``None`` without ids.

    Constant *numbers* are not stable across a compaction, so a fact-level delta
    between a source and one of its variants has to be read off the identities.

    Parameters
    ----------
    record : KBRecord
        The record.

    Returns
    -------
    frozenset or None
        ``{(predicate, frozenset of identities)}``, or ``None`` when the record
        carries no ``constant_ids``.
    """
    ids = record.constant_ids
    if ids is None:
        return None
    return frozenset((pred, frozenset(ids[v] for v in members)) for pred, members in record.facts)


def _variant_delta(source: KBRecord, member: KBRecord) -> int:
    """Fact-level difference between a source and one of its variants."""
    left = _identity_facts(source)
    right = _identity_facts(member)
    if left is None or right is None:
        return len(source.fact_set() ^ member.fact_set())
    return len(left ^ right)


def _variant_member(
    source: KBRecord,
    t: int,
    kind: str,
    rng: random.Random,
    envelope: Envelope,
    kb_id: str,
) -> KBRecord | None:
    """``t`` independent fact edits of ``source``; a stranded constant leaves with its facts.

    The constant set is *not* pinned: a knowledge base is its set of facts, so a
    deletion that takes the last fact naming a constant removes the constant
    too, and the member then carries fewer constants than the source.  Every
    rung stays connected.
    """
    facts = list(source.facts)
    working = source
    ops: list[str] = []
    for _ in range(t):
        force = kind if kind in ("ins", "del") else ("ins" if rng.random() < 0.5 else "del")
        step = _stable_step(working, rng, envelope, force=force)
        if step is None:
            return None
        facts, op = step
        ops.append(op)
        candidate = compact(
            kb_id,
            working.types,
            facts,
            constant_ids=working.constant_ids,
            label=working.label,
            meta={"n_types": source.n_types, "n_preds": source.n_preds},
        )
        if candidate is None:
            return None
        working = candidate
    if working.max_arity > envelope.k_max:
        return None
    if working.n == source.n and working.facts == source.facts:
        return None
    return KBRecord(
        kb_id=kb_id,
        n=working.n,
        types=working.types,
        facts=working.facts,
        constant_ids=working.constant_ids,
        label=source.label,
        meta={
            "source_id": source.kb_id,
            "t": t,
            "kind": kind,
            "ops": ops,
            "delta": _variant_delta(source, working),
            "constant_set_preserved": working.n == source.n,
            "n_types": source.n_types,
            "n_preds": source.n_preds,
        },
    )


def variant_collection(
    source: KBRecord,
    N: int,
    t: int,
    kind: str,
    seed: int,
    *,
    envelope: Envelope = DEFAULT_ENVELOPE,
) -> list[KBRecord] | None:
    """Build one RQ3 Corpus A variant collection over a real member.

    Every member is ``t`` independent fact edits of ``source`` (``mix``: each
    edit insert or delete with probability 1/2), stays connected, and the
    members are pairwise non-isomorphic and non-isomorphic to the source. A
    deletion that strands a constant removes it, so members may carry fewer
    constants than the source and may differ from each other in constant count;
    ``meta["constant_set_preserved"]`` records which members kept the source's.

    Parameters
    ----------
    source : KBRecord
        The truth the collection is built around; its identities are carried
        into every member for evaluation.
    N : int
        Number of members.
    t : int
        Edits per member.
    kind : {"ins", "del", "mix"}
        Edit policy.
    seed : int
        Seed of the local ``random.Random``.
    envelope : Envelope, optional
        Upper walls the members must respect.

    Returns
    -------
    list[KBRecord] or None
        The ``N`` members, or ``None`` when 50 attempts failed to produce a
        legal collection (the caller counts the drop).

    Raises
    ------
    ValueError
        If ``kind`` is not a variant kind.
    """
    if kind not in VARIANT_KINDS:
        raise ValueError(f"unknown variant kind {kind!r}; expected one of {VARIANT_KINDS}")
    if N <= 0 or t <= 0 or source.m == 0:
        return None
    rng = random.Random(seed)
    source_fingerprint = iso_fingerprint(source)
    for attempt in range(_COLLECTION_ATTEMPTS):
        members: list[KBRecord] = []
        fingerprints: set[bytes] = {source_fingerprint}
        for index in range(N):
            member: KBRecord | None = None
            for _ in range(_COLLECTION_ATTEMPTS):
                candidate = _variant_member(
                    source,
                    t,
                    kind,
                    rng,
                    envelope,
                    f"{source.kb_id}#v{index}t{t}{kind}s{seed}",
                )
                if candidate is None:
                    continue
                fingerprint = iso_fingerprint(candidate)
                if fingerprint in fingerprints:
                    continue
                fingerprints.add(fingerprint)
                member = candidate
                break
            if member is None:
                break
            members.append(member)
        if len(members) == N:
            return [_with_cell(m, N, t, kind, seed, attempt) for m in members]
    return None


def _with_cell(record: KBRecord, N: int, t: int, kind: str, seed: int, attempt: int) -> KBRecord:
    meta = dict(record.meta)
    meta.update({"cell_N": N, "cell_t": t, "cell_kind": kind, "seed": seed, "attempt": attempt})
    return KBRecord(
        kb_id=record.kb_id,
        n=record.n,
        types=record.types,
        facts=record.facts,
        roles=record.roles,
        constant_ids=record.constant_ids,
        label=record.label,
        meta=meta,
    )


def fact_distance(a: KBRecord, b: KBRecord) -> int:
    """Exact fact-level distance ``|F(a) triangle F(b)|`` in a shared constant space.

    Evaluation helper for RQ3: it is meaningful only when both records address
    the same constants (a source and its variants, or two consecutive quarters
    of one real series).

    Parameters
    ----------
    a, b : KBRecord
        Records in the same constant numbering.

    Returns
    -------
    int
        Size of the symmetric difference of the two fact sets.
    """
    return len(a.fact_set() ^ b.fact_set())


def edit_kinds() -> Sequence[str]:
    """The five structural edit kinds of RQ1 M1."""
    return EDIT_KINDS
