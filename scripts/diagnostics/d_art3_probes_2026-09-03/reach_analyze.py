"""Aggregate the reach-probe results into the report tables (tolerates partial runs)."""

from __future__ import annotations

import json
import statistics as st
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = json.loads((HERE / "reach_results.json").read_text())
T1, T2 = R["task1"], R["task2"]
PIL = {
    (r["n"], r["m"], r["t"], r["centre_seed"] % 1000): r
    for r in json.loads((HERE / "pilot_consensus_results.json").read_text())["records"]
}
GROUPS = [(8, 10, 1), (8, 10, 2), (10, 12, 1), (10, 12, 2)]
COPIES = [f"K{i}" for i in range(7)]


def sel(tbl, n, m, t):
    return [r for r in tbl if (r["n"], r["m"], r["t"]) == (n, m, t)]


def mean(xs, d=float("nan")):
    return st.mean(xs) if xs else d


def pct(a, b):
    return "n/a" if b == 0 else f"{a}/{b} ({100.0 * a / b:.0f}%)"


print(f"Profiles completed: {len(T1)}/24  wall clock {R['wall_clock']:.0f}s\n")

print("## T1a. Centre -> copy reach (origin = w*_c(M0); 7 targets per profile)\n")
print("| cell | t | profiles | r=1 | r<=2 | r>2 | mean r (capped 3) | mean d_I(M0,K_i) |")
print("|---|---|---|---|---|---|---|---|")
for n, m, t in GROUPS:
    es = sel(T1, n, m, t)
    if not es:
        continue
    r1 = r2 = tot = 0
    rs = []
    for e in es:
        o = e["origins"]["M0"]
        f1, f2 = set(o["r1_found"]), set(o.get("r2_found", []))
        for c in COPIES:
            tot += 1
            if c in f1:
                r1 += 1
                r2 += 1
                rs.append(1)
            elif "r2_found" in o:
                if c in f2:
                    r2 += 1
                    rs.append(2)
                else:
                    rs.append(3)
    dm = mean([PIL[(n, m, t, e["centre"])]["mean_dM0"] for e in es])
    print(
        f"| ({n},{m}) | {t} | {len(es)} | {pct(r1, tot)} | {pct(r2, tot)} | "
        f"{pct(tot - r2, tot)} | {mean(rs):.2f} | {dm:.1f} |"
    )

print("\n## T1b. Reverse (copy -> centre) and copy -> copy reach at r=1\n")
print("| cell | t | copy->centre r=1 | copy->copy r=1 | ordered pairs |")
print("|---|---|---|---|---|")
for n, m, t in GROUPS:
    es = sel(T1, n, m, t)
    if not es:
        continue
    cc = cct = pp = ppt = 0
    for e in es:
        for oid in COPIES:
            f1 = set(e["origins"][oid]["r1_found"])
            cct += 1
            cc += "M0" in f1
            for c in COPIES:
                if c != oid:
                    ppt += 1
                    pp += c in f1
    print(f"| ({n},{m}) | {t} | {pct(cc, cct)} | {pct(pp, ppt)} | {ppt} |")

print("\n## T1c. Radius-2 reach from copy origins (subsampled profiles, t=1)\n")
print("| cell | profiles with copy-origin B_2 | copy->centre r<=2 | copy->copy r<=2 | pairs |")
print("|---|---|---|---|---|")
for n, m in [(8, 10), (10, 12)]:
    es = [e for e in T1 if (e["n"], e["m"]) == (n, m) and "r2_found" in e["origins"]["K0"]]
    cc = cct = pp = ppt = 0
    for e in es:
        for oid in COPIES:
            o = e["origins"][oid]
            if "r2_found" not in o:
                continue
            f = set(o["r1_found"]) | set(o["r2_found"])
            cct += 1
            cc += "M0" in f
            for c in COPIES:
                if c != oid:
                    ppt += 1
                    pp += c in f
    print(f"| ({n},{m}) | {len(es)} | {pct(cc, cct)} | {pct(pp, ppt)} | {ppt} |")

print("\n## T1d. Ball sizes, decoded iso-classes and cost (origin = M0)\n")
print(
    "| cell | mean |w*_c(M0)| | |B_1| words | B_1 iso-classes | B_1 s | |B_2| words | "
    "B_2 iso-classes | B_2 s |"
)
print("|---|---|---|---|---|---|---|---|")
for n, m in [(8, 10), (10, 12)]:
    es = [e for e in T1 if (e["n"], e["m"]) == (n, m)]
    if not es:
        continue
    o = [e["origins"]["M0"] for e in es]
    L = mean([PIL[(n, m, e["t"], e["centre"])]["L0"] for e in es])
    b2i = [x["B2_iso"] for x in o if x.get("B2_iso") is not None]
    print(
        f"| ({n},{m}) | {L:.1f} | {mean([x['B1_words'] for x in o]):.0f} | "
        f"{mean([x['B1_iso'] for x in o]):.0f} | {mean([x['B1_secs'] for x in o]):.2f} | "
        f"{mean([x['B2_words'] for x in o if 'B2_words' in x]):.0f} | "
        f"{('%.0f' % mean(b2i)) if b2i else 'not censused'} | "
        f"{mean([x['B2_secs'] for x in o if 'B2_secs' in x]):.1f} |"
    )

print("\n## T2. Ball-coverage consensus at r=1 (7 copies to cover)\n")
print(
    "| cell | t | cov1 M0 | cov1 medoid | cov1 medoid (self excl.) | cov1 best non-oracle "
    "(self excl.) | M0 is max | M0 unique max | mean ties | candidates |"
)
print("|---|---|---|---|---|---|---|---|---|---|")
for n, m, t in GROUPS:
    rs = sel(T2, n, m, t)
    if not rs:
        continue
    N = len(rs)

    def adj(r, k):
        """Remove the trivial self-coverage a copy gets from w in B_1(w)."""
        return r["cov1"][k] - (1 if k in COPIES else 0)

    best_adj = [max(adj(r, k) for k in r["cov1"] if k != "M0") for r in rs]
    print(
        f"| ({n},{m}) | {t} | {mean([r['cov1_M0'] for r in rs]):.2f} | "
        f"{mean([r['cov1_med'] for r in rs]):.2f} | "
        f"{mean([adj(r, r['medoid_id']) for r in rs]):.2f} | {mean(best_adj):.2f} | "
        f"{sum(r['M0_is_max'] for r in rs)}/{N} | {sum(r['unique_max'] for r in rs)}/{N} | "
        f"{mean([r['n_ties'] for r in rs]):.1f} | {mean([r['n_candidates'] for r in rs]):.0f} |"
    )

print("\n## T2b. Radius-2 coverage and truncated objective sum_i min(r_i,3)\n")
print(
    "| cell | t | profiles | cov2 M0 | cov2 medoid | cov2 best of top-5 | trunc M0 | "
    "trunc medoid | trunc best top-5 |"
)
print("|---|---|---|---|---|---|---|---|---|")
for n, m, t in GROUPS:
    rs = [r for r in sel(T2, n, m, t) if r["cov2"]]
    if not rs:
        continue

    def others(r, field):
        return [v for k, v in r[field].items() if k not in ("M0", r["medoid_id"])]

    print(
        f"| ({n},{m}) | {t} | {len(rs)} | "
        f"{mean([r['cov2'].get('M0', 0) for r in rs]):.2f} | "
        f"{mean([r['cov2'].get(r['medoid_id'], 0) for r in rs]):.2f} | "
        f"{mean([max(others(r, 'cov2'), default=0) for r in rs]):.2f} | "
        f"{mean([r['trunc'].get('M0', 21) for r in rs]):.2f} | "
        f"{mean([r['trunc'].get(r['medoid_id'], 21) for r in rs]):.2f} | "
        f"{mean([min(others(r, 'trunc'), default=21) for r in rs]):.2f} |"
    )

print("\n## Global")
print(json.dumps(R["stats"]))
