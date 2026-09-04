"""Task 1 (conservativity) and Task 2 (Proposition 2+: totality + connectivity).

T1: 2,000 random Sigma_HG(3) words; S2H+ vs the package S2H, compared by the
    exact structural key and by the canonical key w*_c.
T2: 20,000 random Sigma^+(3) words of length 1..40 whose A / A+ tokens carry
    arbitrary ranks (out-of-range, repeated, unsorted); every word must decode
    without exception to a connected, duplicate-free hypergraph.
"""

from __future__ import annotations

import json
import random
import time

import sigma_plus as SP

from isalhg.core.canonical import canonical_string
from isalhg.core.instructions import serialize
from isalhg.core.string_to_hypergraph import string_to_hypergraph

K = 3
SEED = 20260903


def task1(n_words: int = 2000) -> dict:
    rng = random.Random(SEED + 1)
    alpha = SP.sigma_hg_alphabet(K, 1, 1)
    struct_eq = canon_eq = canon_done = 0
    t0 = time.perf_counter()
    for _ in range(n_words):
        L = rng.randint(0, 40)
        toks = [rng.choice(alpha) for _ in range(L)]
        s = serialize(toks)
        H_pkg = string_to_hypergraph(s, k=K)
        H_plus = SP.decode_plus(toks, k=K)
        struct_eq += int(SP.structural_key(H_pkg) == SP.structural_key(H_plus))
        if H_plus.n_edges >= 1 and H_plus.is_connected():
            canon_done += 1
            canon_eq += int(canonical_string(H_pkg, k=K) == canonical_string(H_plus, k=K))
    return dict(
        n_words=n_words,
        structural_equal=struct_eq,
        canonicalizable=canon_done,
        canonical_equal=canon_eq,
        secs=time.perf_counter() - t0,
    )


def task2(n_words: int = 20000) -> dict:
    rng = random.Random(SEED + 2)
    n_exc = n_disconnected = n_dup = 0
    n_with_A = n_edgeless = 0
    n_clamped = 0
    lens_n: list[int] = []
    lens_m: list[int] = []
    t0 = time.perf_counter()
    for _ in range(n_words):
        L = rng.randint(1, 40)
        toks = SP.random_sigma_plus_word(rng, L, K, n_edge_labels=3, n_vertex_labels=1, rank_max=60)
        has_A = any(isinstance(t, (SP.TokenA, SP.TokenAPlus)) for t in toks)
        n_with_A += int(has_A)
        # round-trip the surface form so the parser is exercised too
        s = SP.serialize_plus(toks)
        toks2 = SP.parse_plus(s)
        assert [t.serialize() for t in toks2] == [t.serialize() for t in toks], "parser round-trip"
        try:
            H = SP.decode_plus(toks2, k=K, n_edge_labels=3, n_vertex_labels=1)
        except Exception:  # noqa: BLE001 -- any exception is a totality failure
            n_exc += 1
            continue
        if not H.is_connected():
            n_disconnected += 1
        keys = {(ell, m) for _, m, ell in H.iter_edges()}
        if len(keys) != H.n_edges:
            n_dup += 1
        n_edgeless += int(H.n_edges == 0)
        # did clamping actually fire anywhere in this word?
        cap = (
            1
            + sum(t.j for t in toks2 if isinstance(t, SP.TokenV))
            + sum(1 for t in toks2 if isinstance(t, SP.TokenAPlus))
        )
        if has_A and any(
            max(t.ranks) >= cap for t in toks2 if isinstance(t, (SP.TokenA, SP.TokenAPlus))
        ):
            n_clamped += 1
        lens_n.append(H.n_nodes)
        lens_m.append(H.n_edges)
    return dict(
        n_words=n_words,
        exceptions=n_exc,
        disconnected=n_disconnected,
        duplicate_edges=n_dup,
        words_with_new_tokens=n_with_A,
        words_where_clamp_certainly_fired=n_clamped,
        edgeless_decodes=n_edgeless,
        mean_n=sum(lens_n) / len(lens_n),
        mean_m=sum(lens_m) / len(lens_m),
        max_n=max(lens_n),
        max_m=max(lens_m),
        secs=time.perf_counter() - t0,
    )


if __name__ == "__main__":
    out = dict(task1=task1(), task2=task2())
    print(json.dumps(out, indent=1))
    with open("results_t1_t2.json", "w") as fh:
        json.dump(out, fh, indent=1)
