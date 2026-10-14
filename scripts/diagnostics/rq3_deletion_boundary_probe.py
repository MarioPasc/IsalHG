"""Probe the RQ3 deletion t=2 boundary: information loss vs candidate-generation loss."""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, "/home/mpascual/research/code/IsalHG")

from experiments.tkde import corpora  # noqa: E402
from experiments.tkde.rq3 import (  # noqa: E402
    cell_source_window,
    eligible_sources,
    fact_distance,
    identity_facts_of_hypergraph,
    identity_facts_of_record,
    identity_ids,
)
from isalhg.datasets.kb.ladders import variant_collection  # noqa: E402
from isalhg.language.consensus import _Scorer, coverage_consensus  # noqa: E402
from isalhg.language.majority import majority_merge  # noqa: E402
from isalhg.language.reach import fact_key_of  # noqa: E402

ROOT = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE")
WINDOW = {"n_min": 4, "n_max": 12, "m_min": 4, "m_max": 12, "max_arity": 6}


def main(name: str, N: int, t: int, n_sources: int, seeds: int) -> None:
    coll = corpora.load_collection(name, ROOT)
    pool = eligible_sources(coll, cell_source_window(WINDOW, "del", N))
    print(f"{name}: pool={len(pool)} (m>= {N + 1})")
    stats = Counter()
    by_m: dict[int, Counter] = {}
    for seed in range(seeds):
        for idx, source in enumerate(pool[:n_sources]):
            members = variant_collection(source, N, t, "del", seed * 1000 + idx)
            if members is None:
                stats["dropped"] += 1
                continue
            H = [r.to_hypergraph(n_types=coll.n_types, n_preds=coll.n_preds) for r in members]
            ids = [identity_ids(r) for r in members]
            truth = identity_facts_of_record(source)
            src_H = source.to_hypergraph(n_types=coll.n_types, n_preds=coll.n_preds)
            src_key = fact_key_of(src_H)

            res = coverage_consensus(H, 2)
            out = identity_facts_of_hypergraph(res.kb, ids[res.anchor], res.node_map)
            cons_ok = fact_distance(out, truth) == 0

            in_pool = any(c.word == src_key for c in res.candidates)
            scorer = _Scorer(H, 2)
            cov, sr = scorer.score(src_H)
            would_win = (cov, sr) <= (res.coverage, res.sum_reach) and cov >= res.coverage

            union = frozenset().union(*(identity_facts_of_record(r) for r in members))
            union_ok = union == truth

            merged, merged_ids = majority_merge(H, ids)
            maj_ok = fact_distance(identity_facts_of_hypergraph(merged, merged_ids), truth) == 0

            win_sub = out <= truth
            win_m = len(out)
            stats["winner_subset_of_source"] += int(win_sub and not cons_ok)
            stats["winner_m_minus_src_m_sum"] += (win_m - len(truth)) if not cons_ok else 0
            stats["winner_cov"] += res.coverage; stats["winner_sum"] += res.sum_reach
            stats["src_cov"] += cov; stats["src_sum"] += sr
            m = source.m
            c = by_m.setdefault(m, Counter())
            c["n"] += 1
            for k, v in (
                ("consensus_exact", cons_ok),
                ("source_in_pool", in_pool),
                ("source_would_win", would_win and cov == N),
                ("union_exact", union_ok),
                ("majority_exact", maj_ok),
                ("in_pool_but_lost", in_pool and not cons_ok),
            ):
                c[k] += int(v)
                stats[k] += int(v)
            stats["n"] += 1
    n = stats["n"]
    print(f"collections={n} dropped={stats['dropped']}")
    for k in (
        "consensus_exact",
        "source_in_pool",
        "source_would_win",
        "in_pool_but_lost",
        "union_exact",
        "majority_exact",
    ):
        print(f"  {k:18s} {stats[k]:4d} / {n}  = {stats[k] / max(n, 1):.3f}")
    miss = n - stats["consensus_exact"]
    print(f"  misses={miss}: winner is strict subset of source in {stats['winner_subset_of_source']}; mean(winner_m - source_m)={stats['winner_m_minus_src_m_sum']/max(miss,1):.2f}")
    print(f"  mean winner (cov,sum)=({stats['winner_cov']/n:.2f},{stats['winner_sum']/n:.2f}) vs source ({stats['src_cov']/n:.2f},{stats['src_sum']/n:.2f})")
    print("by source size m:")
    for m in sorted(by_m):
        c = by_m[m]
        print(
            f"  m={m:2d} n={c['n']:3d} consensus={c['consensus_exact'] / c['n']:.2f} "
            f"in_pool={c['source_in_pool'] / c['n']:.2f} would_win={c['source_would_win'] / c['n']:.2f} "
            f"union={c['union_exact'] / c['n']:.2f} majority={c['majority_exact'] / c['n']:.2f}"
        )


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "ndc_classes"
    N = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    main(name, N, 2, n_sources=int(sys.argv[3]) if len(sys.argv) > 3 else 40, seeds=2)
