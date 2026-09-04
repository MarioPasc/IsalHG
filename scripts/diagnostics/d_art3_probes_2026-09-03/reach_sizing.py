"""Sizing: cost of enumerating B_1 / B_2 token-Levenshtein balls over Sigma_HG(3)."""

from __future__ import annotations

import random
import time

import pilot_consensus as P

from isalhg.core.instructions import serialize
from isalhg.core.string_to_hypergraph import string_to_hypergraph

ALPHA = tuple(P.ALPHABET)


def ball1(w: tuple) -> set[tuple]:
    """All token words at token-Levenshtein distance <= 1 from ``w``."""
    out = {w}
    L = len(w)
    for i in range(L):
        out.add(w[:i] + w[i + 1 :])
    for i in range(L):
        pre, post = w[:i], w[i + 1 :]
        for a in ALPHA:
            out.add(pre + (a,) + post)
    for i in range(L + 1):
        pre, post = w[:i], w[i:]
        for a in ALPHA:
            out.add(pre + (a,) + post)
    return out


for n, m in [(8, 10), (10, 12)]:
    M0 = P.make_centre(n, m, random.Random(P.MASTER_SEED + (0 if n == 8 else 1000)))
    w0 = tuple(P.parse(P.encode_hg(M0)[0]))
    print(f"\n({n},{m}) |w*_c|={len(w0)}")

    t0 = time.perf_counter()
    B1 = ball1(w0)
    t_gen1 = time.perf_counter() - t0
    print(f"  |B_1|={len(B1)} gen={t_gen1:.3f}s")

    # decode cost
    t0 = time.perf_counter()
    keys = {}
    for w in B1:
        H = string_to_hypergraph(serialize(w), k=3)
        if H.n_edges == 0:
            continue
        keys.setdefault(P._key(H), H)
    t_dec = time.perf_counter() - t0
    print(f"  decode+labelled-dedup: {t_dec:.3f}s -> {len(keys)} distinct labelled")

    t0 = time.perf_counter()
    iso = {P.encode_hg(H)[0] for H in keys.values()}
    print(f"  canonicalize distinct: {time.perf_counter() - t0:.3f}s -> {len(iso)} iso-classes")

    # B_2
    t0 = time.perf_counter()
    B2: set[tuple] = set()
    for w in B1:
        B2 |= ball1(w)
    t_gen2 = time.perf_counter() - t0
    print(f"  |B_2|={len(B2)} gen={t_gen2:.1f}s")

    t0 = time.perf_counter()
    keys2 = set()
    cnt = 0
    for w in B2:
        H = string_to_hypergraph(serialize(w), k=3)
        cnt += 1
        if H.n_edges == 0:
            continue
        keys2.add(P._key(H))
    t_dec2 = time.perf_counter() - t0
    print(f"  decode B_2: {t_dec2:.1f}s ({cnt} words) -> {len(keys2)} distinct labelled")
    print(f"  per-word decode = {1e6 * t_dec2 / cnt:.1f} us")
