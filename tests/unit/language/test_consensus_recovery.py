"""Measured source-recovery rates of the coverage consensus (`DESIGN.md` RQ3, H3a).

The grid is the definition of done: 40 random labelled sources
(``n in [6,10]``, ``m in [6,10]``, arity 2-4, 3 types, 2 predicates), variant
collections built by :func:`isalhg.datasets.kb.ladders.variant_collection` with
``N in {5, 9}``, ``t in {1, 2}`` and both radii (``r = t``, the known budget,
and ``r = 2``, the unknown one), for each of the three edit kinds.  Recovery is
exact: the winner's canonical key must equal the source's.

Thresholds: insertion-only 100 %, deletion-only 95 %, mixed 80 %.  They are
assertions, not targets to tune towards --- the objective is frozen, so a miss
is reported, not fixed.  The module is marked ``slow`` (about ten minutes) and
is therefore outside the ``-m unit`` sweep; ``majority_merge`` is measured on
the same collections so H3c has both numbers from one run.
"""

from __future__ import annotations

import random

import pytest

from isalhg.language.consensus import coverage_consensus
from isalhg.language.majority import majority_merge
from isalhg.language.reach import fact_key_of

pytestmark = pytest.mark.slow

pytest.importorskip("pynauty")

N_SOURCES = 40
KINDS = ("ins", "del", "mix")
MEMBER_COUNTS = (5, 9)
BUDGETS = (1, 2)
THRESHOLD = {"ins": 1.0, "del": 0.95, "mix": 0.80}


def random_source(rng: random.Random, kb_id: str):
    """A random connected labelled knowledge-base record, or ``None``."""
    from isalhg.datasets.kb.base import make_record

    n = rng.randint(6, 10)
    m = rng.randint(6, 10)
    facts: set[tuple[int, tuple[int, ...]]] = set()
    for _ in range(m * 20):
        if len(facts) == m:
            break
        arity = rng.randint(2, 4)
        facts.add((rng.randrange(2), tuple(sorted(rng.sample(range(n), arity)))))
    return make_record(
        kb_id,
        n,
        [rng.randrange(3) for _ in range(n)],
        sorted(facts),
        constant_ids=[f"c{v}" for v in range(n)],
        meta={"n_types": 3, "n_preds": 2},
        require_connected=True,
    )


def sources(rng: random.Random, count: int) -> list:
    """Return ``count`` random sources."""
    out = []
    attempt = 0
    while len(out) < count and attempt < count * 20:
        record = random_source(rng, f"src{len(out)}")
        attempt += 1
        if record is not None:
            out.append(record)
    return out


@pytest.mark.parametrize("kind", KINDS)
def test_recovery_rate(kind: str) -> None:
    from isalhg.datasets.kb.ladders import variant_collection

    rng = random.Random(9000 + KINDS.index(kind))
    corpus = sources(rng, N_SOURCES)
    assert len(corpus) == N_SOURCES

    hits = 0
    runs = 0
    dropped = 0
    ties_total = 0
    majority_hits = 0
    majority_runs = 0
    per_cell: dict[tuple[int, int, int], tuple[int, int]] = {}

    for index, record in enumerate(corpus):
        truth = fact_key_of(record.to_hypergraph(n_types=3, n_preds=2))
        for n_members in MEMBER_COUNTS:
            for t in BUDGETS:
                members = variant_collection(record, n_members, t, kind, seed=7000 + 13 * index + t)
                if members is None:
                    dropped += 1
                    continue
                graphs = [m.to_hypergraph(n_types=3, n_preds=2) for m in members]
                identities = [list(m.constant_ids or ()) for m in members]
                merged, _ = majority_merge(graphs, identities)
                majority_runs += 1
                majority_hits += int(fact_key_of(merged) == truth)
                for r in sorted({t, 2}):
                    result = coverage_consensus(graphs, r=r)
                    runs += 1
                    hit = int(result.word == truth)
                    hits += hit
                    ties_total += result.n_ties
                    cell = (n_members, t, r)
                    won, total = per_cell.get(cell, (0, 0))
                    per_cell[cell] = (won + hit, total + 1)

    rate = hits / runs
    print(
        f"\nkind={kind}: recovery {hits}/{runs} = {rate:.3f} "
        f"(dropped collections {dropped}, total ties {ties_total}, "
        f"majority_merge {majority_hits}/{majority_runs} = "
        f"{majority_hits / majority_runs:.3f})"
    )
    for cell in sorted(per_cell):
        won, total = per_cell[cell]
        print(f"  N={cell[0]} t={cell[1]} r={cell[2]}: {won}/{total} = {won / total:.3f}")

    assert runs >= N_SOURCES * 4
    assert rate >= THRESHOLD[kind], f"{kind}: {rate:.3f} < {THRESHOLD[kind]}"
