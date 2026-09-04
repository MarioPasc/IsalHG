"""Aggregate the pilot records and run a supplementary neighbourhood-landscape probe.

The probe is NOT part of the fixed design: it samples the same move operators far
more densely than the 40-candidate local search does, so that "the search stopped"
can be separated from "the search under-sampled".
"""

from __future__ import annotations

import json
import random
import statistics as st
from pathlib import Path

import numpy as np
import pilot_consensus as P

HERE = Path(__file__).resolve().parent
REC = json.loads((HERE / "pilot_consensus_results.json").read_text())
records = REC["records"]

GROUPS = [(8, 10, 1), (8, 10, 2), (10, 12, 1), (10, 12, 2)]


def sel(n, m, t):
    return [r for r in records if r["n"] == n and r["m"] == m and r["t"] == t]


def mr(vals):
    return f"{st.mean(vals):.3f} [{min(vals):.3f}, {max(vals):.3f}]"


print("## Ratios to the pairwise lower bound LB\n")
print("| cell | t | C_med/LB | C_0/LB | C_A/LB | C_B/LB |")
print("|---|---|---|---|---|---|")
for n, m, t in GROUPS:
    rs = sel(n, m, t)
    print(
        f"| ({n},{m}) | {t} | "
        + " | ".join(mr([r[k] / r["LB"] for r in rs]) for k in ("C_med", "C_0", "C_A", "C_B"))
        + " |"
    )

print("\n## Search outcomes\n")
print(
    "| cell | t | A beats medoid | B beats medoid | A recovers M0 | B recovers M0 | "
    "medoid recovers M0 | A beats C_0 | B beats C_0 | C_med<=C_0 |"
)
print("|---|---|---|---|---|---|---|---|---|---|")
for n, m, t in GROUPS:
    rs = sel(n, m, t)
    N = len(rs)
    f = lambda p: f"{sum(1 for r in rs if p(r))}/{N}"
    print(
        f"| ({n},{m}) | {t} | "
        + " | ".join(
            [
                f(lambda r: r["C_A"] < r["C_med"]),
                f(lambda r: r["C_B"] < r["C_med"]),
                f(lambda r: r["d_A_M0"] == 0),
                f(lambda r: r["d_B_M0"] == 0),
                f(lambda r: r["d_medoid_M0"] == 0),
                f(lambda r: r["C_A"] < r["C_0"]),
                f(lambda r: r["C_B"] < r["C_0"]),
                f(lambda r: r["C_med"] <= r["C_0"]),
            ]
        )
        + " |"
    )

print("\n## Improvement magnitude (tokens) and search cost\n")
print(
    "| cell | t | C_med-C_A | C_med-C_B | evals A | evals B | steps A | steps B | secs A | secs B |"
)
print("|---|---|---|---|---|---|---|---|---|---|")
for n, m, t in GROUPS:
    rs = sel(n, m, t)
    g = lambda k: f"{st.mean([r[k] for r in rs]):.1f}"
    print(
        f"| ({n},{m}) | {t} | "
        f"{st.mean([r['C_med'] - r['C_A'] for r in rs]):.1f} | "
        f"{st.mean([r['C_med'] - r['C_B'] for r in rs]):.1f} | "
        + " | ".join(g(k) for k in ("evals_A", "evals_B", "steps_A", "steps_B"))
        + f" | {st.mean([r['secs_A'] for r in rs]):.2f} | {st.mean([r['secs_B'] for r in rs]):.2f} |"
    )

print("\n## Avalanche and degeneracy\n")
print(
    "| cell | t | |w*_c(M0)| | mean d_I(M0,K_i) | avalanche frac | d_I(medoid,M0) | zero-pairs frac |"
)
print("|---|---|---|---|---|---|---|")
for n, m, t in GROUPS:
    rs = sel(n, m, t)
    print(
        f"| ({n},{m}) | {t} | {mr([float(r['L0']) for r in rs])} | "
        f"{mr([r['mean_dM0'] for r in rs])} | {mr([r['avalanche'] for r in rs])} | "
        f"{mr([float(r['d_medoid_M0']) for r in rs])} | {mr([r['zero_pairs'] for r in rs])} |"
    )

# ---------------------------------------------------------------------------
# Supplementary: dense neighbourhood probe around the medoid
# ---------------------------------------------------------------------------
DENSE = 1500
print(f"\n## Supplementary landscape probe ({DENSE} sampled neighbours per profile)\n")
print(
    "| cell | t | struct: distinct nbrs | dC min | dC q25 | dC med | dC q75 | frac dC<0 | "
    "string: distinct | dC min | frac dC<0 |"
)
print("|---|---|---|---|---|---|---|---|---|---|---|")

rows = []
for n, m, t in GROUPS:
    agg = {k: [] for k in ("sd", "smin", "q25", "q50", "q75", "sneg", "bd", "bmin", "bneg")}
    for r in sel(n, m, t):
        rng = random.Random(r["profile_seed"] + 77)
        M0 = P.make_centre(r["n"], r["m"], random.Random(r["centre_seed"]))
        crng = random.Random(r["profile_seed"])
        corpus = [P.make_copy(M0, r["t"], crng) for _ in range(P.N_COPIES)]
        D = np.array([[float(P.d_I(a, b)) for b in corpus] for a in corpus])
        medoid = corpus[int(np.argmin(D.sum(axis=1)))]
        c0 = P.cost(medoid, corpus)
        assert c0 == r["C_med"], (c0, r["C_med"])

        # structure-space neighbours
        seen = {}
        for _ in range(DENSE):
            cand, _op = P.random_connected_edit(medoid, rng, max_arity=P.K)
            if not P.is_valid(cand):
                continue
            seen.setdefault(P.encode_hg(cand)[0], cand)
        dC = sorted(P.cost(c, corpus) - c0 for c in seen.values())
        agg["sd"].append(len(dC))
        agg["smin"].append(dC[0])
        agg["q25"].append(dC[len(dC) // 4])
        agg["q50"].append(dC[len(dC) // 2])
        agg["q75"].append(dC[3 * len(dC) // 4])
        agg["sneg"].append(sum(1 for d in dC if d < 0) / len(dC))

        # string-space neighbours
        toks0 = P.parse(P.encode_hg(medoid)[0])
        seenb = {}
        for _ in range(DENSE):
            tk = P.mutate_string(toks0, rng)
            if tk is None:
                continue
            try:
                dec = P.string_to_hypergraph(P.serialize(tk), k=P.K)
            except Exception:
                continue
            if dec.n_nodes < 1 or dec.n_edges < 1 or not dec.is_connected():
                continue
            seenb.setdefault(P.encode_hg(dec)[0], dec)
        dB = sorted(P.cost(c, corpus) - c0 for c in seenb.values())
        agg["bd"].append(len(dB))
        agg["bmin"].append(dB[0])
        agg["bneg"].append(sum(1 for d in dB if d < 0) / len(dB))
    rows.append((n, m, t, agg))
    a = agg
    print(
        f"| ({n},{m}) | {t} | {st.mean(a['sd']):.0f} | {st.mean(a['smin']):.1f} | "
        f"{st.mean(a['q25']):.1f} | {st.mean(a['q50']):.1f} | {st.mean(a['q75']):.1f} | "
        f"{st.mean(a['sneg']):.3f} | {st.mean(a['bd']):.0f} | {st.mean(a['bmin']):.1f} | "
        f"{st.mean(a['bneg']):.3f} |"
    )

print("\n## Global stats")
print(json.dumps(REC["stats"]), "wall_clock=%.1fs" % REC["wall_clock"])
