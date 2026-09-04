"""Addendum: per-member sensitivity of the objective to one structural edit of the medoid."""

from __future__ import annotations

import json
import random
import statistics as st
from pathlib import Path

import numpy as np
import pilot_consensus as P

HERE = Path(__file__).resolve().parent
records = json.loads((HERE / "pilot_consensus_results.json").read_text())["records"]

print(
    "mean C_med/C_0 =",
    f"{st.mean([r['C_med'] / r['C_0'] for r in records]):.3f}",
    " profiles with C_med <= C_0:",
    sum(1 for r in records if r["C_med"] <= r["C_0"]),
    "/",
    len(records),
)
print(
    "mean C_med/LB =",
    f"{st.mean([r['C_med'] / r['LB'] for r in records]):.3f}",
    " => medoid is at worst a",
    f"{max(r['C_med'] / r['LB'] for r in records):.2f}",
    "x-approximation of OPT on every profile (OPT >= LB)",
)
print("mean C_0/LB =", f"{st.mean([r['C_0'] / r['LB'] for r in records]):.3f}")
print()

print(
    "| cell | t | mean |d(cand,K_i)-d(med,K_i)| | frac members closer | frac nbrs with >=4 members closer |"
)
print("|---|---|---|---|---|")
for n, m, t in [(8, 10, 1), (8, 10, 2), (10, 12, 1), (10, 12, 2)]:
    abs_ch, closer, maj = [], [], []
    for r in [x for x in records if (x["n"], x["m"], x["t"]) == (n, m, t)]:
        M0 = P.make_centre(n, m, random.Random(r["centre_seed"]))
        crng = random.Random(r["profile_seed"])
        corpus = [P.make_copy(M0, t, crng) for _ in range(P.N_COPIES)]
        D = np.array([[float(P.d_I(a, b)) for b in corpus] for a in corpus])
        medoid = corpus[int(np.argmin(D.sum(axis=1)))]
        base = np.array([P.d_I(medoid, K_i) for K_i in corpus], dtype=float)
        rng = random.Random(r["profile_seed"] + 999)
        seen = {}
        for _ in range(1200):
            cand, _op = P.random_connected_edit(medoid, rng, max_arity=P.K)
            if P.is_valid(cand):
                seen.setdefault(P.encode_hg(cand)[0], cand)
        for c in seen.values():
            v = np.array([P.d_I(c, K_i) for K_i in corpus], dtype=float)
            abs_ch.append(float(np.abs(v - base).mean()))
            closer.append(float((v < base).mean()))
            maj.append(1.0 if (v < base).sum() >= 4 else 0.0)
    print(
        f"| ({n},{m}) | {t} | {st.mean(abs_ch):.2f} | {st.mean(closer):.3f} | {st.mean(maj):.3f} |"
    )
