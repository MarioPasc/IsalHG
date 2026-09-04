"""E-C-roles -- E-C with argument roles carried inside the fact token.

Optional fourth arm, WD50K(66) only (the only corpus whose statements have a
subject / object / qualifier structure). Identical to E-C except a fact token
lists ``(role, address)`` pairs sorted by ``(role, address)`` instead of bare
addresses.

A role-annotated knowledge base is kept as its own value type because roles
live on *incidences*, not on constants: the same constant can be the subject of
one fact and a qualifier value of another.
"""

from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass

from f4_corpora import ENV_M_MAX, ENV_M_MIN, ENV_N, K_MAX, is_connected
from f4_encodings import KB, Word, local_addresses

ROLE_SUBJECT, ROLE_OBJECT, ROLE_QUALIFIER = 0, 1, 2
ROLE_NAMES = ("subject", "object", "qualifier")

RFact = tuple[int, tuple[tuple[int, int], ...]]  # (predicate, sorted (constant, role) pairs)


@dataclass(frozen=True)
class RKB:
    """Role-annotated knowledge base."""

    n: int
    types: tuple[int, ...]
    rfacts: tuple[RFact, ...]
    n_types: int
    n_preds: int

    @property
    def m(self) -> int:
        return len(self.rfacts)

    def to_kb(self) -> KB:
        facts = tuple(
            sorted(
                {(lab, frozenset(c for c, _ in pairs)) for lab, pairs in self.rfacts},
                key=lambda f: (f[0], sorted(f[1])),
            )
        )
        return KB(
            n=self.n, types=self.types, facts=facts, n_types=self.n_types, n_preds=self.n_preds
        )

    def role_of(self) -> dict[tuple[int, frozenset[int]], dict[int, int]]:
        out: dict[tuple[int, frozenset[int]], dict[int, int]] = {}
        for lab, pairs in self.rfacts:
            key = (lab, frozenset(c for c, _ in pairs))
            cur = out.setdefault(key, {})
            for c, r in pairs:
                cur[c] = min(cur.get(c, r), r)
        return out


def _normalise(
    n: int, types: list[int], rfacts: list[RFact], n_types: int, n_preds: int
) -> RKB | None:
    """Deduplicate on ``(predicate, member set)``, drop unused constants, check connectivity."""
    seen: dict[tuple[int, frozenset[int]], RFact] = {}
    for lab, pairs in rfacts:
        key = (lab, frozenset(c for c, _ in pairs))
        if key not in seen:
            seen[key] = (lab, tuple(sorted(pairs)))
    used = sorted({c for lab, pairs in seen.values() for c, _ in pairs})
    if not used or not seen:
        return None
    remap = {c: i for i, c in enumerate(used)}
    out: list[RFact] = [
        (lab, tuple(sorted((remap[c], r) for c, r in pairs))) for lab, pairs in seen.values()
    ]
    plain = [(lab, frozenset(c for c, _ in pairs)) for lab, pairs in out]
    if not is_connected(len(used), plain):
        return None
    return RKB(
        n=len(used),
        types=tuple(types[c] for c in used),
        rfacts=tuple(sorted(out)),
        n_types=n_types,
        n_preds=n_preds,
    )


# ---------------------------------------------------------------------------
# Corpus
# ---------------------------------------------------------------------------


def load_wd50k66_roles() -> list[RKB]:
    """WD50K(66) subject-ego star KBs with subject / object / qualifier roles."""
    import os
    from pathlib import Path

    import probe_hyperrel as ph

    root = os.environ.get("F4_DATA_ROOT")
    if root:
        ph.DATA_ROOT = Path(root)
    stmts = ph.load("wd50k_66", "csv", ("train.txt", "valid.txt", "test.txt"))
    rels = sorted({s.relation for s in stmts})
    rel_id = {r: i for i, r in enumerate(rels)}
    by_subject: dict[str, list] = defaultdict(list)
    for s in stmts:
        by_subject[s.subject].append(s)

    out: list[RKB] = []
    for ent in sorted(by_subject):
        group = by_subject[ent]
        if len(group) < 3:
            continue
        verts = sorted({v for s in group for v in s.vertices})
        if len(verts) > ENV_N:
            continue
        remap = {v: i for i, v in enumerate(verts)}
        rfacts: list[RFact] = []
        for s in group:
            role: dict[int, int] = {}
            for v, r in [(s.subject, ROLE_SUBJECT), (s.obj, ROLE_OBJECT)] + [
                (q, ROLE_QUALIFIER) for q in s.qual_values
            ]:
                c = remap[v]
                role[c] = min(role.get(c, r), r)
            rfacts.append((rel_id[s.relation], tuple(sorted(role.items()))))
        rkb = _normalise(len(verts), [0] * len(verts), rfacts, 1, len(rels))
        if rkb is None:
            continue
        if not (ENV_M_MIN <= rkb.m <= ENV_M_MAX):
            continue
        if max(len(p) for _, p in rkb.rfacts) > K_MAX:
            continue
        out.append(rkb)
    return out


# ---------------------------------------------------------------------------
# Encoder
# ---------------------------------------------------------------------------


def word_C_roles(rkb: RKB) -> Word:
    """E-C word with ``(role, address)`` operands."""
    kb = rkb.to_kb()
    H = kb.to_hypergraph()
    addr = local_addresses(H)
    role = rkb.role_of()
    order = sorted(range(H.n_nodes), key=lambda v: addr[v])
    prefix = [("T", addr[v], H.vertex_label(v)) for v in order]
    facts = []
    for _, members, lab in H.iter_edges():
        rmap = role[(lab, members)]
        facts.append(("F", lab, tuple(sorted((rmap[v], addr[v]) for v in members))))
    facts.sort(key=lambda t: (t[1], t[2]))
    return (*prefix, *facts)


# ---------------------------------------------------------------------------
# Role-aware edits (same five kinds as the core probe)
# ---------------------------------------------------------------------------


def _assign_roles(members: list[int], rng: random.Random) -> tuple[tuple[int, int], ...]:
    ms = list(members)
    rng.shuffle(ms)
    role = {ms[0]: ROLE_SUBJECT, ms[1]: ROLE_OBJECT}
    for c in ms[2:]:
        role[c] = ROLE_QUALIFIER
    return tuple(sorted(role.items()))


def apply_edit_roles(rkb: RKB, kind: str, rng: random.Random) -> RKB | None:
    rfacts = list(rkb.rfacts)
    types = list(rkb.types)
    existing = {(lab, frozenset(c for c, _ in p)) for lab, p in rfacts}

    if kind == "insert_fact":
        pool = sorted({len(p) for _, p in rfacts})
        a = max(2, min(rng.choice(pool), rkb.n, K_MAX))
        mem = rng.sample(range(rkb.n), a)
        lab = rng.randrange(rkb.n_preds)
        if (lab, frozenset(mem)) in existing or rkb.m + 1 > ENV_M_MAX:
            return None
        return _normalise(
            rkb.n, types, [*rfacts, (lab, _assign_roles(mem, rng))], rkb.n_types, rkb.n_preds
        )

    if kind == "delete_fact":
        if rkb.m <= 1:
            return None
        e = rng.randrange(rkb.m)
        return _normalise(
            rkb.n, types, [f for i, f in enumerate(rfacts) if i != e], rkb.n_types, rkb.n_preds
        )

    if kind == "add_constant":
        e = rng.randrange(rkb.m)
        lab, pairs = rfacts[e]
        mem = {c for c, _ in pairs}
        outside = [v for v in range(rkb.n) if v not in mem]
        if not outside or len(pairs) >= K_MAX:
            return None
        new_c = rng.choice(outside)
        if (lab, frozenset(mem | {new_c})) in existing:
            return None
        rfacts[e] = (lab, tuple(sorted([*pairs, (new_c, ROLE_QUALIFIER)])))
        return _normalise(rkb.n, types, rfacts, rkb.n_types, rkb.n_preds)

    if kind == "remove_constant":
        cands = [i for i, (_, p) in enumerate(rfacts) if len(p) >= 3]
        if not cands:
            return None
        e = rng.choice(cands)
        lab, pairs = rfacts[e]
        drop = rng.choice(pairs)
        mem = {c for c, _ in pairs} - {drop[0]}
        if (lab, frozenset(mem)) in existing:
            return None
        rfacts[e] = (lab, tuple(p for p in pairs if p != drop))
        return _normalise(rkb.n, types, rfacts, rkb.n_types, rkb.n_preds)

    if kind == "insert_fact_new_constant":
        pool = sorted({len(p) for _, p in rfacts})
        a = max(2, min(rng.choice(pool), rkb.n + 1, K_MAX))
        new_v = rkb.n
        mem = [new_v, *rng.sample(range(rkb.n), a - 1)]
        lab = rng.randrange(rkb.n_preds)
        return _normalise(
            rkb.n + 1,
            [*types, 0],
            [*rfacts, (lab, _assign_roles(mem, rng))],
            rkb.n_types,
            rkb.n_preds,
        )

    raise ValueError(f"unknown edit kind {kind!r}")


def sample_edits_roles(
    rkb: RKB, kind: str, count: int, rng: random.Random, tries: int = 40
) -> list[RKB]:
    seen: set[tuple] = set()
    out: list[RKB] = []
    for _ in range(tries * count):
        if len(out) >= count:
            break
        cand = apply_edit_roles(rkb, kind, rng)
        if cand is None:
            continue
        key = (cand.n, cand.types, cand.rfacts)
        if key in seen:
            continue
        seen.add(key)
        out.append(cand)
    return out
