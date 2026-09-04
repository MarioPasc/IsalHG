"""Render the stats_*.json files as the report's markdown tables (tasks 1-4).

Tables that would otherwise double in length report only the granularity used
for the timing sample (`timing_granularity`); T1 and T2 keep both granularities,
since task 1 asks for two.
"""

from __future__ import annotations

import glob
import json
import os

import arb_temporal_lib as L

S = {}
for p in glob.glob(os.path.join(L.OUT, "stats_*.json")):
    with open(p) as fh:
        d = json.load(fh)
    S[d["dataset"]] = d
names = [n for n in L.PRIORITY if n in S]
PRIM = {n: S[n]["timing_granularity"] for n in names}


def f(x):
    if x is None:
        return "-"
    return f"{x:.0f}" if isinstance(x, float) else str(x)


def sh(x):
    return "/".join(f(x[k]) for k in ("min", "p25", "med", "p75", "p90", "max"))


print("## 1. Corpus facts and window granularity (task 1)")
print()
print("`cands` gives the median `m` of non-empty star KBs at every candidate window.")
print()
print(
    "| dataset | unit | simplices | distinct | nodes | arity | node-label file | cands (gran:med m) | chosen |"
)
print("|---|---|---|---|---|---|---|---|---|")
for n in names:
    d = S[n]
    lab = f"names ({d['n_node_labels']})" if d["has_node_labels"] else "none"
    cands = ", ".join(f"{r['granularity']}:{r['med_m']:.0f}" for r in d["granularity_scan"])
    print(
        f"| {n} | {d['unit']} | {d['n_simplices']:,} | {d['n_distinct_simplices']:,} | "
        f"{d['n_nodes_used']:,} | {d['arity_range'][0]}-{d['arity_range'][1]} | {lab} | "
        f"{cands} | {', '.join(d['chosen'])} |"
    )

print()
print("## 2. Sizes, arity, envelope yield (task 2)")
print()
print("Percentiles are min/p25/med/p75/p90/max over all non-empty `(v, t)`.")
print()
print(
    "| dataset | gran | #KB | n | m | max arity | KB arity>=3 | env (n<=24, m<=110) | env frac | env arity>=3 | env arity<=10 |"
)
print("|---|---|---|---|---|---|---|---|---|---|---|")
for n in names:
    for g, st in S[n]["per_granularity"].items():
        print(
            f"| {n} | {g} | {st['n_kbs']:,} | {sh(st['n_dist'])} | {sh(st['m_dist'])} | "
            f"{sh(st['maxarity_dist'])} | {st['frac_kb_with_arity_ge3']:.3f} | "
            f"{st['envelope_count']:,} | {st['envelope_frac']:.3f} | "
            f"{st['frac_env_kb_with_arity_ge3']:.3f} | {st['frac_env_maxarity_le10']:.3f} |"
        )

print()
print("Arity histogram over (KB, distinct edge) incidences, in-envelope KBs, chosen granularity:")
print()
print("| dataset | gran | a=1 | a=2 | a=3 | a=4 | a=5 | a=6-10 | a>10 | share a>=3 |")
print("|---|---|---|---|---|---|---|---|---|---|")
for n in names:
    st = S[n]["per_granularity"][PRIM[n]]
    h = {int(k): v for k, v in st["arity_hist_env"].items()}
    tot = sum(h.values()) or 1
    mid = sum(v for k, v in h.items() if 6 <= k <= 10)
    hi = sum(v for k, v in h.items() if k > 10)
    pc3 = 100 * sum(v for k, v in h.items() if k >= 3) / tot
    print(
        f"| {n} | {PRIM[n]} | {h.get(1, 0):,} | {h.get(2, 0):,} | {h.get(3, 0):,} | "
        f"{h.get(4, 0):,} | {h.get(5, 0):,} | {mid:,} | {hi:,} | {pc3:.1f}% |"
    )

print()
print("## 3. Variants: Delta over consecutive windows (task 3)")
print()
print("Both KBs of the pair inside the envelope; chosen granularity.")
print()
print(
    "| dataset | gran | pairs non-empty | pairs in env | d=0 | d=1 | d=2 | d=3-5 | d>5 | nodes run>=3 | nodes run>=5 | nodes >=3 one-edit |"
)
print("|---|---|---|---|---|---|---|---|---|---|---|---|")
for n in names:
    st = S[n]["per_granularity"][PRIM[n]]
    dd = st["delta"]

    def cell(k, dd=dd):
        return f"{dd[k]['count']:,} ({dd[k]['frac']:.3f})"

    print(
        f"| {n} | {PRIM[n]} | {dd['n_pairs_both_nonempty']:,} | {dd['n_pairs_both_in_env']:,} | "
        f"{cell('d0')} | {cell('d1')} | {cell('d2')} | {cell('d3_5')} | {cell('d_gt5')} | "
        f"{st['n_nodes_run3_in_env']:,} | {st['n_nodes_run5_in_env']:,} | "
        f"{st['n_nodes_ge3_one_edit_pairs']:,} |"
    )

print()
print("Same, restricted to the **encodable** envelope (`n<=24`, `3<=m<=110`, max arity `<=10`):")
print()
print(
    "| dataset | gran | #KB encodable | pairs encodable | d=0 | d=1 | d=2 | d=3-5 | d>5 | nodes run>=3 | nodes run>=5 | nodes >=3 one-edit |"
)
print("|---|---|---|---|---|---|---|---|---|---|---|---|")
for n in names:
    st = S[n]["per_granularity"][PRIM[n]]
    dd = st["enc_delta"]

    def cell(k, dd=dd):
        return f"{dd[k]['count']:,} ({dd[k]['frac']:.3f})"

    print(
        f"| {n} | {PRIM[n]} | {st['enc_count']:,} | {dd['n_pairs_both_in_env']:,} | "
        f"{cell('d0')} | {cell('d1')} | {cell('d2')} | {cell('d3_5')} | {cell('d_gt5')} | "
        f"{st['enc_run3']:,} | {st['enc_run5']:,} | {dd['n_nodes_ge3_one_edit_pairs']:,} |"
    )

print()
print("## 4. Isomorphism census over in-envelope KBs (task 4)")
print()
print("pynauty-Levi; sample of at most 1,500 in-envelope KBs, seed 20260903. Every")
print("dataset finished well inside the one-minute cap (worst case 0.1 s).")
print()
print(
    "| dataset | gran | in envelope | census N | sampled | distinct unlabelled | distinct identity-labelled | distinct fact sets | secs |"
)
print("|---|---|---|---|---|---|---|---|---|")
for n in names:
    st = S[n]["per_granularity"][PRIM[n]]
    cs = st["census"]
    print(
        f"| {n} | {PRIM[n]} | {cs['n_in_envelope']:,} | {cs['n_census']:,} | "
        f"{'yes' if cs['sampled'] else 'no'} | {cs['distinct_unlabelled']:,} | "
        f"{cs['distinct_identity_labelled']:,} | {cs['distinct_fact_sets']:,} | {cs['secs']} |"
    )
