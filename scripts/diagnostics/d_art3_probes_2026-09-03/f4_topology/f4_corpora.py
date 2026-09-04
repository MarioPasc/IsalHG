"""Corpora and edit operators for the F4 topology probe.

Three corpora, matching the probe design:

(i)   300 synthetic labelled KBs, ``n in [6, 16]``, ``m in [6, 20]``, arities
      2-4, 3 constant types, 3 predicates, rejection sampling under a fixed
      seed.
(ii)  NDC-classes quarterly star KBs inside the encodable envelope
      (``3 <= m <= 110``, ``n <= 24``, ``max arity <= 10``) with the FDA class
      type carried as a name suffix as the constant type.
(iii) WD50K(66) subject-ego star KBs inside the same envelope, predicate =
      relation, constants untyped.

Derivations reuse the existing probe libraries rather than reimplementing them:
``arb_temporal/arb_temporal_lib.py`` for (ii) and ``hyperrel/probe_hyperrel.py``
for (iii).
"""

from __future__ import annotations

import os
import random
import sys
from collections import defaultdict
from pathlib import Path

from f4_encodings import KB

_HERE = Path(__file__).resolve().parent
_PROBES = _HERE.parent
sys.path.insert(0, str(_PROBES / "arb_temporal"))
sys.path.insert(0, str(_PROBES / "hyperrel"))

ENV_N = 24
ENV_M_MIN = 3
ENV_M_MAX = 110
K_MAX = 10

NDC_QUARTER_MS = 7_889_238_000
NDC_TYPE_NAMES = ("[epc]", "[moa]", "[pe]", "untyped")
NDC_TYPE_ID = {name: i for i, name in enumerate(sorted(NDC_TYPE_NAMES))}


# ---------------------------------------------------------------------------
# Structural helpers
# ---------------------------------------------------------------------------


def is_connected(n: int, facts: list[tuple[int, frozenset[int]]]) -> bool:
    """True iff the primal graph on the constants used by ``facts`` is connected."""
    used: set[int] = set()
    for _, mem in facts:
        used |= mem
    if len(used) != n or n == 0:
        return False
    adj: dict[int, set[int]] = defaultdict(set)
    for _, mem in facts:
        ms = sorted(mem)
        for a in ms:
            for b in ms:
                if a != b:
                    adj[a].add(b)
    seen = {next(iter(used))}
    stack = [next(iter(used))]
    while stack:
        v = stack.pop()
        for u in adj[v]:
            if u not in seen:
                seen.add(u)
                stack.append(u)
    return len(seen) == n


def compact(
    types: list[int], facts: list[tuple[int, frozenset[int]]], n_types: int, n_preds: int
) -> KB | None:
    """Drop constants that no longer occur in any fact and renumber densely.

    A knowledge base *is* its set of ground facts, so a constant left with no
    fact after a deletion has left the knowledge base. Returns ``None`` if the
    result is empty or disconnected.
    """
    used = sorted({v for _, mem in facts for v in mem})
    if not used or not facts:
        return None
    remap = {v: i for i, v in enumerate(used)}
    new_facts = [(lab, frozenset(remap[v] for v in mem)) for lab, mem in facts]
    if not is_connected(len(used), new_facts):
        return None
    seen: set[tuple[int, frozenset[int]]] = set()
    dedup: list[tuple[int, frozenset[int]]] = []
    for f in new_facts:
        if f in seen:
            return None
        seen.add(f)
        dedup.append(f)
    return KB(
        n=len(used),
        types=tuple(types[v] for v in used),
        facts=tuple(sorted(dedup, key=lambda f: (f[0], sorted(f[1])))),
        n_types=n_types,
        n_preds=n_preds,
    )


def make_kb(
    n: int, types: list[int], facts: list[tuple[int, frozenset[int]]], n_types: int, n_preds: int
) -> KB | None:
    if n == 0 or not facts:
        return None
    if not is_connected(n, facts):
        return None
    return KB(
        n=n,
        types=tuple(types),
        facts=tuple(sorted(set(facts), key=lambda f: (f[0], sorted(f[1])))),
        n_types=n_types,
        n_preds=n_preds,
    )


# ---------------------------------------------------------------------------
# (i) synthetic
# ---------------------------------------------------------------------------


def gen_synthetic(count: int, seed: int) -> list[KB]:
    """Rejection-sample ``count`` connected labelled KBs."""
    rng = random.Random(seed)
    out: list[KB] = []
    tries = 0
    while len(out) < count and tries < 200 * count:
        tries += 1
        n = rng.randint(6, 16)
        m = rng.randint(6, 20)
        types = [rng.randrange(3) for _ in range(n)]
        facts: set[tuple[int, frozenset[int]]] = set()
        guard = 0
        while len(facts) < m and guard < 400:
            guard += 1
            a = rng.randint(2, 4)
            mem = frozenset(rng.sample(range(n), a))
            facts.add((rng.randrange(3), mem))
        if len(facts) != m:
            continue
        kb = make_kb(n, types, sorted(facts, key=lambda f: (f[0], sorted(f[1]))), 3, 3)
        if kb is not None:
            out.append(kb)
    return out


# ---------------------------------------------------------------------------
# (ii) NDC-classes quarterly star KBs + their natural variant series
# ---------------------------------------------------------------------------


def _ndc_types(corpus) -> dict[int, int]:  # noqa: ANN001
    """Map ARB node id -> constant-type id from the FDA class-type suffix."""
    out: dict[int, int] = {}
    for nid, name in corpus.node_names.items():
        suffix = "untyped"
        for cand in ("[epc]", "[moa]", "[pe]"):
            if name.rstrip().endswith(cand):
                suffix = cand
                break
        out[nid] = NDC_TYPE_ID[suffix]
    return out


def _kb_from_simplices(
    simplices: list[list[int]], type_of: dict[int, int]
) -> tuple[KB | None, frozenset[int]]:
    verts = sorted({v for s in simplices for v in s})
    remap = {v: i for i, v in enumerate(verts)}
    facts = [(0, frozenset(remap[v] for v in s)) for s in simplices]
    kb = make_kb(len(verts), [type_of.get(v, NDC_TYPE_ID["untyped"]) for v in verts], facts, 4, 1)
    return kb, frozenset(verts)


def load_ndc() -> tuple[list[KB], list[dict]]:
    """Return (in-envelope quarterly star KBs, consecutive-window pair records).

    Each pair record carries ``delta`` = ``|S_t(v) triangle S_{t+1}(v)|`` on the
    named ARB canonical simplex ids -- exact fact-level ground truth.
    """
    import arb_temporal_lib as atl

    root = os.environ.get("F4_DATA_ROOT")
    if root:
        atl.ROOT = str(Path(root) / "arb_benson" / "temporal")
    corpus = atl.load("NDC-classes")
    groups = atl.build_groups(corpus, NDC_QUARTER_MS, with_full=True)
    type_of = _ndc_types(corpus)

    ok: dict[tuple[int, int], int] = {}
    for gi in range(len(groups.key)):
        if not (ENV_M_MIN <= groups.m[gi] <= ENV_M_MAX):
            continue
        if groups.n[gi] > ENV_N or groups.max_arity[gi] > K_MAX:
            continue
        ok[(int(groups.node[gi]), int(groups.window[gi]))] = gi

    def sids(gi: int) -> frozenset[int]:
        s = groups.gstart[gi]
        e = groups.gstart[gi + 1] if gi + 1 < len(groups.gstart) else len(groups.usid)
        return frozenset(int(x) for x in groups.usid[s:e])

    kbs: list[KB] = []
    index: dict[tuple[int, int], int] = {}
    for key, gi in sorted(ok.items()):
        kb, _ = _kb_from_simplices(atl.kb_edges(corpus, groups, gi), type_of)
        if kb is None:
            continue
        index[key] = len(kbs)
        kbs.append(kb)

    pairs: list[dict] = []
    for (node, win), gi in sorted(ok.items()):
        nxt = (node, win + 1)
        if nxt not in ok or key_missing(index, (node, win)) or key_missing(index, nxt):
            continue
        a, b = sids(gi), sids(ok[nxt])
        pairs.append(
            {
                "node": node,
                "window": win,
                "i": index[(node, win)],
                "j": index[nxt],
                "delta": len(a ^ b),
            }
        )
    return kbs, pairs


def key_missing(index: dict, key) -> bool:  # noqa: ANN001
    return key not in index


# ---------------------------------------------------------------------------
# (iii) WD50K(66) subject-ego star KBs
# ---------------------------------------------------------------------------


def load_wd50k66() -> list[KB]:
    """Return in-envelope subject-ego star KBs of WD50K(66), predicate=relation."""
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

    out: list[KB] = []
    for ent in sorted(by_subject):
        group = by_subject[ent]
        if len(group) < 3:
            continue
        verts = sorted({v for s in group for v in s.vertices})
        if len(verts) > ENV_N:
            continue
        remap = {v: i for i, v in enumerate(verts)}
        facts = {(rel_id[s.relation], frozenset(remap[v] for v in s.vertices)) for s in group}
        if not (ENV_M_MIN <= len(facts) <= ENV_M_MAX):
            continue
        if max(len(mem) for _, mem in facts) > K_MAX:
            continue
        kb = make_kb(
            len(verts),
            [0] * len(verts),
            sorted(facts, key=lambda f: (f[0], sorted(f[1]))),
            1,
            len(rels),
        )
        if kb is not None:
            out.append(kb)
    return out


# ---------------------------------------------------------------------------
# Edit operators (five kinds; all preserve connectivity and the envelope)
# ---------------------------------------------------------------------------

EDIT_KINDS = (
    "insert_fact",
    "delete_fact",
    "add_constant",
    "remove_constant",
    "insert_fact_new_constant",
)


def _arity_pool(kb: KB) -> list[int]:
    return sorted({len(mem) for _, mem in kb.facts})


def apply_edit(kb: KB, kind: str, rng: random.Random) -> KB | None:
    """Apply one edit of ``kind``; return ``None`` if the attempt is invalid."""
    facts = list(kb.facts)
    types = list(kb.types)
    existing = set(facts)

    if kind == "insert_fact":
        pool = _arity_pool(kb)
        a = rng.choice(pool)
        a = max(2, min(a, kb.n, K_MAX))
        cand = (rng.randrange(kb.n_preds), frozenset(rng.sample(range(kb.n), a)))
        if cand in existing:
            return None
        return make_kb(kb.n, types, [*facts, cand], kb.n_types, kb.n_preds)

    if kind == "delete_fact":
        if kb.m <= 1:
            return None
        e = rng.randrange(kb.m)
        return compact(types, [f for i, f in enumerate(facts) if i != e], kb.n_types, kb.n_preds)

    if kind == "add_constant":
        e = rng.randrange(kb.m)
        lab, mem = facts[e]
        outside = [v for v in range(kb.n) if v not in mem]
        if not outside or len(mem) >= K_MAX:
            return None
        cand = (lab, mem | {rng.choice(outside)})
        if cand in existing:
            return None
        facts[e] = cand
        return make_kb(kb.n, types, facts, kb.n_types, kb.n_preds)

    if kind == "remove_constant":
        cands = [i for i, (_, mem) in enumerate(facts) if len(mem) >= 3]
        if not cands:
            return None
        e = rng.choice(cands)
        lab, mem = facts[e]
        cand = (lab, mem - {rng.choice(sorted(mem))})
        if cand in existing:
            return None
        facts[e] = cand
        return compact(types, facts, kb.n_types, kb.n_preds)

    if kind == "insert_fact_new_constant":
        if kb.n + 1 > ENV_N + 8:
            return None
        pool = _arity_pool(kb)
        a = max(2, min(rng.choice(pool), kb.n + 1, K_MAX))
        new_v = kb.n
        others = rng.sample(range(kb.n), a - 1)
        cand = (rng.randrange(kb.n_preds), frozenset([new_v, *others]))
        return make_kb(
            kb.n + 1,
            [*types, rng.randrange(kb.n_types)],
            [*facts, cand],
            kb.n_types,
            kb.n_preds,
        )

    raise ValueError(f"unknown edit kind {kind!r}")


def sample_edits(kb: KB, kind: str, count: int, rng: random.Random, tries: int = 40) -> list[KB]:
    """Sample up to ``count`` distinct results of one edit kind."""
    seen: set[tuple] = set()
    out: list[KB] = []
    for _ in range(tries * count):
        if len(out) >= count:
            break
        cand = apply_edit(kb, kind, rng)
        if cand is None:
            continue
        key = (cand.n, cand.types, cand.facts)
        if key in seen:
            continue
        seen.add(key)
        out.append(cand)
    return out


def _stable_step(kb: KB, rng: random.Random) -> KB | None:
    """One fact insertion or deletion that leaves the constant set unchanged.

    Keeping the constant ids fixed is what makes the fact-level difference
    ``|F_0 triangle F_t|`` exact on a synthetic ladder, the same way the
    NDC named node ids make it exact on the natural series.
    """
    facts = list(kb.facts)
    if rng.random() < 0.5 or kb.m <= ENV_M_MIN:
        pool = _arity_pool(kb)
        a = max(2, min(rng.choice(pool), kb.n, K_MAX))
        cand = (rng.randrange(kb.n_preds), frozenset(rng.sample(range(kb.n), a)))
        if cand in set(facts) or kb.m + 1 > ENV_M_MAX:
            return None
        new_facts = [*facts, cand]
    else:
        e = rng.randrange(kb.m)
        new_facts = [f for i, f in enumerate(facts) if i != e]
    if not is_connected(kb.n, new_facts):
        return None
    return KB(
        n=kb.n,
        types=kb.types,
        facts=tuple(sorted(set(new_facts), key=lambda f: (f[0], sorted(f[1])))),
        n_types=kb.n_types,
        n_preds=kb.n_preds,
    )


def random_walk(kb: KB, steps: int, rng: random.Random) -> KB | None:
    """Apply ``steps`` constant-set-preserving fact edits; ``None`` if stuck."""
    cur = kb
    for _ in range(steps):
        nxt = None
        for _ in range(80):
            nxt = _stable_step(cur, rng)
            if nxt is not None and nxt.facts != cur.facts:
                break
            nxt = None
        if nxt is None:
            return None
        cur = nxt
    return cur
