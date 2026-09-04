"""E-D and E-D1 -- fact addressing by (local key, index within key class).

Follow-on to :mod:`f4_encodings` (E-A pointer, E-B global canonical rank, E-C
depth-3 WL colour). The two failures measured there have opposite causes: E-C's
address is *content* (a refinement colour is a global hash, so one fact edit
moves 92-98 % of the colours), E-B's address is *positional* (a global rank
order renumbers whenever the constant set it orders changes). The missing third
point is an address that is positional **within a locally determined class**.

E-D   local key ``kappa(c) = (type(c), sorted multiset over facts incident to c
      of (predicate label, arity))`` -- strictly depth 0: it reads only ``c``'s
      own incidences, never a neighbour's key.
E-D1  coarse local key ``kappa(c) = (type(c), degree(c))`` -- the granularity
      control. E-B is the degenerate single-class case of the same family.

In both, ``addr(c) = (kappa(c), idx)`` with ``idx`` the position of ``c`` among
the constants sharing ``kappa(c)``, ordered by the same nauty canonical rank
E-B uses. Word layout mirrors E-C exactly: an address-keyed type prefix in
increasing address order, then one ``F[l; addr_1 ... addr_a]`` per fact with
operands sorted by address and the fact tokens sorted lexicographically.

Also here: ``apply_edit_traced`` / ``sample_edits_traced``, byte-for-byte
replays of :func:`f4_corpora.apply_edit` / :func:`f4_corpora.sample_edits` that
additionally return the old-constant -> new-constant correspondence, which the
N3 mechanism measurement needs because ``compact`` renumbers after a deletion.
The replay consumes the RNG identically; ``verify_trace_equivalence`` asserts it.
"""

from __future__ import annotations

import random
from typing import Any, TypeAlias

from f4_corpora import ENV_M_MAX, ENV_M_MIN, ENV_N, K_MAX, apply_edit, is_connected
from f4_encodings import KB, Symbol, Word, canonical_ranks

from isalhg.core.sparse_hypergraph import SparseHypergraph

Key: TypeAlias = tuple[Any, ...]
Address: TypeAlias = tuple[Key, int]


# ---------------------------------------------------------------------------
# The two local keys
# ---------------------------------------------------------------------------


def key_full(H: SparseHypergraph, v: int) -> Key:
    """``(type label, sorted multiset of (predicate label, arity) over v's facts)``."""
    return (
        H.vertex_label(v),
        tuple(sorted((H.edge_label(e), len(H.members(e))) for e in H.incident_edges(v))),
    )


def key_coarse(H: SparseHypergraph, v: int) -> Key:
    """``(type label, degree)`` -- the coarse control."""
    return (H.vertex_label(v), H.degree(v))


KEY_FNS = {"D": key_full, "D1": key_coarse}


def keys_of(H: SparseHypergraph, which: str) -> tuple[Key, ...]:
    fn = KEY_FNS[which]
    return tuple(fn(H, v) for v in range(H.n_nodes))


# ---------------------------------------------------------------------------
# Addressing
# ---------------------------------------------------------------------------


def key_addresses(
    H: SparseHypergraph,
    which: str,
    rank: tuple[int, ...] | None = None,
) -> tuple[Address, ...]:
    """Return ``addr[v] = (kappa(v), index of v among same-kappa constants)``.

    The index orders same-key constants by their nauty canonical rank, so the
    address map is isomorphism-invariant (an iso-invariant key composed with an
    iso-invariant within-class order) and injective by construction.
    """
    if rank is None:
        rank = canonical_ranks(H)
    keys = keys_of(H, which)
    by_key: dict[Key, list[int]] = {}
    for v in range(H.n_nodes):
        by_key.setdefault(keys[v], []).append(v)
    addr: list[Address] = [((), 0)] * H.n_nodes
    for key, members in by_key.items():
        for idx, v in enumerate(sorted(members, key=lambda u: rank[u])):
            addr[v] = (key, idx)
    return tuple(addr)


def word_key(
    H: SparseHypergraph,
    which: str,
    rank: tuple[int, ...] | None = None,
) -> Word:
    """F4 word addressed by ``(local key, index)``.

    Layout identical to :func:`f4_encodings.word_C`: type prefix
    ``T[addr; type]`` in increasing address order, then ``F[l; addr...]`` per
    fact, operands sorted by address, fact tokens sorted lexicographically.
    """
    addr = key_addresses(H, which, rank)
    order = sorted(range(H.n_nodes), key=lambda v: addr[v])
    prefix: list[Symbol] = [("T", addr[v], H.vertex_label(v)) for v in order]
    facts: list[Symbol] = []
    for _, members, lab in H.iter_edges():
        facts.append(("F", lab, tuple(sorted(addr[v] for v in members))))
    facts.sort(key=lambda t: (t[1], t[2]))
    return (*prefix, *facts)


def word_D(H: SparseHypergraph, rank: tuple[int, ...] | None = None) -> Word:
    return word_key(H, "D", rank)


def word_D1(H: SparseHypergraph, rank: tuple[int, ...] | None = None) -> Word:
    return word_key(H, "D1", rank)


# ---------------------------------------------------------------------------
# Traced edits: the same operators, plus the constant correspondence
# ---------------------------------------------------------------------------


def _compact_traced(
    types: list[int],
    facts: list[tuple[int, frozenset[int]]],
    n_types: int,
    n_preds: int,
) -> tuple[KB | None, dict[int, int]]:
    """:func:`f4_corpora.compact`, additionally returning ``old -> new``."""
    used = sorted({v for _, mem in facts for v in mem})
    if not used or not facts:
        return None, {}
    remap = {v: i for i, v in enumerate(used)}
    new_facts = [(lab, frozenset(remap[v] for v in mem)) for lab, mem in facts]
    if not is_connected(len(used), new_facts):
        return None, {}
    seen: set[tuple[int, frozenset[int]]] = set()
    for f in new_facts:
        if f in seen:
            return None, {}
        seen.add(f)
    kb = KB(
        n=len(used),
        types=tuple(types[v] for v in used),
        facts=tuple(sorted(set(new_facts), key=lambda f: (f[0], sorted(f[1])))),
        n_types=n_types,
        n_preds=n_preds,
    )
    return kb, remap


def _make_traced(
    n: int,
    types: list[int],
    facts: list[tuple[int, frozenset[int]]],
    n_types: int,
    n_preds: int,
) -> tuple[KB | None, dict[int, int]]:
    """:func:`f4_corpora.make_kb`; the correspondence is the identity on ``n``."""
    if n == 0 or not facts or not is_connected(n, facts):
        return None, {}
    kb = KB(
        n=n,
        types=tuple(types),
        facts=tuple(sorted(set(facts), key=lambda f: (f[0], sorted(f[1])))),
        n_types=n_types,
        n_preds=n_preds,
    )
    return kb, {v: v for v in range(n)}


def apply_edit_traced(kb: KB, kind: str, rng: random.Random) -> tuple[KB | None, dict[int, int]]:
    """Replay of :func:`f4_corpora.apply_edit` returning ``(result, old->new)``.

    The RNG is consumed in exactly the same order and quantity, so replaying a
    sampling loop with this function reproduces the untraced job list verbatim
    (asserted by :func:`verify_trace_equivalence`). For
    ``insert_fact_new_constant`` the correspondence is the identity on the old
    constants and the new one is ``kb.n``.
    """
    facts = list(kb.facts)
    types = list(kb.types)
    existing = set(facts)

    if kind == "insert_fact":
        pool = sorted({len(mem) for _, mem in kb.facts})
        a = rng.choice(pool)
        a = max(2, min(a, kb.n, K_MAX))
        cand = (rng.randrange(kb.n_preds), frozenset(rng.sample(range(kb.n), a)))
        if cand in existing:
            return None, {}
        return _make_traced(kb.n, types, [*facts, cand], kb.n_types, kb.n_preds)

    if kind == "delete_fact":
        if kb.m <= 1:
            return None, {}
        e = rng.randrange(kb.m)
        return _compact_traced(
            types, [f for i, f in enumerate(facts) if i != e], kb.n_types, kb.n_preds
        )

    if kind == "add_constant":
        e = rng.randrange(kb.m)
        lab, mem = facts[e]
        outside = [v for v in range(kb.n) if v not in mem]
        if not outside or len(mem) >= K_MAX:
            return None, {}
        cand = (lab, mem | {rng.choice(outside)})
        if cand in existing:
            return None, {}
        facts[e] = cand
        return _make_traced(kb.n, types, facts, kb.n_types, kb.n_preds)

    if kind == "remove_constant":
        cands = [i for i, (_, mem) in enumerate(facts) if len(mem) >= 3]
        if not cands:
            return None, {}
        e = rng.choice(cands)
        lab, mem = facts[e]
        cand = (lab, mem - {rng.choice(sorted(mem))})
        if cand in existing:
            return None, {}
        facts[e] = cand
        return _compact_traced(types, facts, kb.n_types, kb.n_preds)

    if kind == "insert_fact_new_constant":
        if kb.n + 1 > ENV_N + 8:
            return None, {}
        pool = sorted({len(mem) for _, mem in kb.facts})
        a = max(2, min(rng.choice(pool), kb.n + 1, K_MAX))
        new_v = kb.n
        others = rng.sample(range(kb.n), a - 1)
        cand = (rng.randrange(kb.n_preds), frozenset([new_v, *others]))
        out, _ = _make_traced(
            kb.n + 1,
            [*types, rng.randrange(kb.n_types)],
            [*facts, cand],
            kb.n_types,
            kb.n_preds,
        )
        return out, ({v: v for v in range(kb.n)} if out is not None else {})

    raise ValueError(f"unknown edit kind {kind!r}")


def sample_edits_traced(
    kb: KB, kind: str, count: int, rng: random.Random, tries: int = 40
) -> list[tuple[KB, dict[int, int]]]:
    """Replay of :func:`f4_corpora.sample_edits` carrying the correspondence."""
    seen: set[tuple] = set()
    out: list[tuple[KB, dict[int, int]]] = []
    for _ in range(tries * count):
        if len(out) >= count:
            break
        cand, corr = apply_edit_traced(kb, kind, rng)
        if cand is None:
            continue
        key = (cand.n, cand.types, cand.facts)
        if key in seen:
            continue
        seen.add(key)
        out.append((cand, corr))
    return out


def verify_trace_equivalence(kbs: list[KB], kinds: tuple[str, ...], seed: int) -> dict:
    """Assert the traced replay is RNG- and result-identical to the original."""
    r1 = random.Random(seed)
    r2 = random.Random(seed)
    checked = 0
    mismatch = 0
    for kb in kbs:
        for kind in kinds:
            a = apply_edit(kb, kind, r1)
            b, corr = apply_edit_traced(kb, kind, r2)
            checked += 1
            if (a is None) != (b is None):
                mismatch += 1
                continue
            if (
                a is not None
                and b is not None
                and (
                    (a.n, a.types, a.facts) != (b.n, b.types, b.facts)
                    or len(corr) != len(set(corr.values()))
                    or any(v >= b.n for v in corr.values())
                )
            ):
                mismatch += 1
    return {
        "checked": checked,
        "mismatches": mismatch,
        "rng_states_equal": r1.getstate() == r2.getstate(),
    }


__all__ = [
    "ENV_M_MAX",
    "ENV_M_MIN",
    "Address",
    "Key",
    "apply_edit_traced",
    "key_addresses",
    "key_coarse",
    "key_full",
    "keys_of",
    "sample_edits_traced",
    "verify_trace_equivalence",
    "word_D",
    "word_D1",
    "word_key",
]
