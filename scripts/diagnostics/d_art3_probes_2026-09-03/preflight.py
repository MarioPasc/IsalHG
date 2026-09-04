"""Preflight: time w*_c on the pilot substrates and verify the cached-distance path."""

from __future__ import annotations

import random
import time

from isalhg.core.canonical import canonical_string
from isalhg.core.instructions import parse
from isalhg.core.sparse_hypergraph import random_connected_edit
from isalhg.datasets.synthetic._random_hg import random_connected_hypergraph
from isalhg.metric_space.distances.isalhg_levenshtein import IsalHGLevenshtein, _encode

K = 3
dist = IsalHGLevenshtein(k=K)

for n, m in [(8, 10), (10, 12)]:
    ts = []
    lens = []
    rng = random.Random(1000 + n)
    Hs = []
    for s in range(6):
        H, _ = random_connected_hypergraph(n_nodes=n, n_edges=m, arity_range=(3, 3), rng=rng)
        t0 = time.perf_counter()
        w = canonical_string(H, k=K)
        ts.append(time.perf_counter() - t0)
        lens.append(len(parse(w)))
        Hs.append(H)
    ts.sort()
    print(
        f"(n={n},m={m}) w*_c secs: min={ts[0]:.4f} med={ts[len(ts) // 2]:.4f} max={ts[-1]:.4f}"
        f" | |w*_c| tokens: {sorted(lens)}"
    )

    # perturbed copies (t=2 edits + permutation) — the real workload
    ts2 = []
    for H in Hs[:3]:
        cur = H
        for _ in range(2):
            cur, _op = random_connected_edit(cur, rng, max_arity=K)
        perm = list(range(cur.n_nodes))
        rng.shuffle(perm)
        from isalhg.core.sparse_hypergraph import permute

        cur = permute(cur, perm)
        t0 = time.perf_counter()
        canonical_string(cur, k=K)
        ts2.append(time.perf_counter() - t0)
    print(f"   perturbed w*_c secs: {['%.4f' % t for t in sorted(ts2)]}")

# consistency: cached-encode path vs module pairwise
rng = random.Random(7)
A, _ = random_connected_hypergraph(n_nodes=8, n_edges=10, arity_range=(3, 3), rng=rng)
B, _ = random_connected_hypergraph(n_nodes=8, n_edges=10, arity_range=(3, 3), rng=rng)
from rapidfuzz.distance import Levenshtein

symA = tuple(parse(canonical_string(A, k=K)))
symB = tuple(parse(canonical_string(B, k=K)))
ea, eb = _encode([symA, symB])
print("cached path:", Levenshtein.distance(ea, eb), "module pairwise:", dist.pairwise(A, B))

# S2H decode of a canonical string
from isalhg.core.string_to_hypergraph import string_to_hypergraph

w = canonical_string(A, k=K)
D = string_to_hypergraph(w, k=K)
print(
    "S2H roundtrip connected:",
    D.is_connected(),
    "n=",
    D.n_nodes,
    "m=",
    D.n_edges,
    "orig n,m=",
    A.n_nodes,
    A.n_edges,
    "wstar equal:",
    canonical_string(D, k=K) == w,
)
