"""Pilot: consensus / 1-median of N hypergraphs under d_I (token Levenshtein on w*_c).

Design (fixed, see the report):
  12 planted centres M0 (6 x (n,m)=(8,10), 6 x (10,12)), 3-uniform, connected, trivial labels
  noise levels t in {1,2}; N=7 perturbed copies per (centre, t): t connectivity-preserving
  Qin-style edits (max arity 3) followed by a random vertex permutation
  distance: d_I via isalhg.metric_space.distances.isalhg_levenshtein (token level, k=3 fixed)
  Search A: best-improvement local search in structure space from the medoid
  Search B: best-improvement local search in ambient string space Sigma_HG(3)* from w*_c(medoid),
            each candidate decoded by S2H and re-canonicalized before evaluating C

Writes a JSON record of every profile next to this script.
"""

from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from rapidfuzz.distance import Levenshtein

from isalhg.core.canonical import canonical_string
from isalhg.core.instructions import TokenC, TokenN, TokenP, TokenV, TokenW, parse, serialize
from isalhg.core.sparse_hypergraph import (
    SparseHypergraph,
    permute,
    random_connected_edit,
)
from isalhg.core.string_to_hypergraph import string_to_hypergraph
from isalhg.datasets.synthetic._random_hg import random_connected_hypergraph
from isalhg.metric_space.distances.isalhg_levenshtein import IsalHGLevenshtein

K = 3
N_COPIES = 7
BUDGET = 200
NEIGHBOURS = 40
MASTER_SEED = 20260903
CELLS = [(8, 10), (10, 12)]
CENTRES_PER_CELL = 6
NOISE_LEVELS = (1, 2)
CANON_TIMEOUT_S = 30.0

HERE = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Sigma_HG(3) alphabet (trivial vocabulary: one vertex label, one edge label)
# ---------------------------------------------------------------------------
ALPHABET = [
    TokenW(),
    *[TokenP(i) for i in range(1, K + 1)],
    *[TokenN(i) for i in range(1, K + 1)],
    *[TokenC(0, i) for i in range(1, K + 1)],
    *[TokenV(0, i, j, tuple([0] * j)) for i in range(1, K) for j in range(1, K) if 2 <= i + j <= K],
]

# ---------------------------------------------------------------------------
# Cached canonicalization + distance
# ---------------------------------------------------------------------------
_DIST = IsalHGLevenshtein(k=K)
_VOCAB: dict[object, str] = {}


@dataclass
class Stats:
    n_canon: int = 0
    canon_time: float = 0.0
    max_canon: float = 0.0
    dnf: int = 0
    s2h_fail: int = 0


STATS = Stats()


def _key(H: SparseHypergraph) -> tuple:
    return (
        H.n_nodes,
        tuple(sorted((tuple(sorted(m)), ell) for _, m, ell in H.iter_edges())),
    )


_CACHE: dict[tuple, tuple[str, str]] = {}  # key -> (w*_c, encoded token string)


def encode_hg(H: SparseHypergraph) -> tuple[str, str]:
    """Return (w*_c(H), encoded-token-string) with memoization.

    The encoded string maps each distinct Sigma_HG token to a private code point
    under one process-wide bijection; Levenshtein is invariant under bijective
    symbol relabelling, so distances equal IsalHGLevenshtein.pairwise exactly
    (verified per profile against the module's own matrix()).
    """
    key = _key(H)
    hit = _CACHE.get(key)
    if hit is not None:
        return hit
    t0 = time.perf_counter()
    w = canonical_string(H, k=K)
    dt = time.perf_counter() - t0
    STATS.n_canon += 1
    STATS.canon_time += dt
    STATS.max_canon = max(STATS.max_canon, dt)
    if dt > CANON_TIMEOUT_S:
        STATS.dnf += 1
    buf = []
    for tok in parse(w):
        ch = _VOCAB.get(tok)
        if ch is None:
            ch = chr(0x100 + len(_VOCAB))
            _VOCAB[tok] = ch
        buf.append(ch)
    out = (w, "".join(buf))
    _CACHE[key] = out
    return out


def d_I(H1: SparseHypergraph, H2: SparseHypergraph) -> int:
    return int(Levenshtein.distance(encode_hg(H1)[1], encode_hg(H2)[1]))


def cost(cand: SparseHypergraph, corpus: list[SparseHypergraph]) -> int:
    return sum(d_I(cand, K_i) for K_i in corpus)


# ---------------------------------------------------------------------------
# Corpus construction
# ---------------------------------------------------------------------------
def is_valid(H: SparseHypergraph) -> bool:
    seen = set()
    for _, members, ell in H.iter_edges():
        if len(members) > K:
            return False
        key = (members, ell)
        if key in seen:
            return False
        seen.add(key)
    return H.n_nodes >= 1 and H.n_edges >= 1 and H.is_connected()


def make_centre(n: int, m: int, rng: random.Random) -> SparseHypergraph:
    for _ in range(500):
        H, _att = random_connected_hypergraph(n_nodes=n, n_edges=m, arity_range=(3, 3), rng=rng)
        if is_valid(H) and H.n_edges == m and H.n_nodes == n:
            return H
    raise RuntimeError(f"no valid 3-uniform connected centre at ({n},{m})")


def make_copy(M0: SparseHypergraph, t: int, rng: random.Random) -> SparseHypergraph:
    for _ in range(200):
        cur = M0
        ok = True
        for _ in range(t):
            cur, _op = random_connected_edit(cur, rng, max_arity=K)
            if not is_valid(cur):
                ok = False
                break
        if not ok:
            continue
        perm = list(range(cur.n_nodes))
        rng.shuffle(perm)
        return permute(cur, perm)
    raise RuntimeError("could not build a valid perturbed copy")


# ---------------------------------------------------------------------------
# Search A -- structure space
# ---------------------------------------------------------------------------
def search_A(start: SparseHypergraph, corpus: list[SparseHypergraph], rng: random.Random):
    t0 = time.perf_counter()
    cur, cur_c = start, cost(start, corpus)
    evals = 0
    steps = 0
    while evals < BUDGET:
        seen: dict[str, SparseHypergraph] = {}
        for _ in range(NEIGHBOURS * 3):
            if len(seen) >= NEIGHBOURS:
                break
            cand, _op = random_connected_edit(cur, rng, max_arity=K)
            if not is_valid(cand):
                continue
            w, _ = encode_hg(cand)
            seen.setdefault(w, cand)
        best, best_c = None, cur_c
        for cand in seen.values():
            if evals >= BUDGET:
                break
            c = cost(cand, corpus)
            evals += 1
            if c < best_c:
                best, best_c = cand, c
        if best is None:
            break
        cur, cur_c = best, best_c
        steps += 1
    return cur, cur_c, evals, steps, time.perf_counter() - t0


# ---------------------------------------------------------------------------
# Search B -- ambient string space
# ---------------------------------------------------------------------------
def mutate_string(tokens: list, rng: random.Random) -> list | None:
    op = rng.choice(("ins", "del", "sub"))
    toks = list(tokens)
    if op == "ins":
        pos = rng.randrange(len(toks) + 1)
        toks.insert(pos, rng.choice(ALPHABET))
    elif op == "del":
        if len(toks) <= 1:
            return None
        toks.pop(rng.randrange(len(toks)))
    else:
        if not toks:
            return None
        toks[rng.randrange(len(toks))] = rng.choice(ALPHABET)
    return toks


def search_B(start: SparseHypergraph, corpus: list[SparseHypergraph], rng: random.Random):
    t0 = time.perf_counter()
    cur_str = parse(encode_hg(start)[0])
    cur_obj, cur_c = start, cost(start, corpus)
    evals = 0
    steps = 0
    while evals < BUDGET:
        cands: list[tuple[list, SparseHypergraph]] = []
        seen_w: set[str] = set()
        for _ in range(NEIGHBOURS * 3):
            if len(cands) >= NEIGHBOURS:
                break
            toks = mutate_string(cur_str, rng)
            if toks is None:
                continue
            s = serialize(toks)
            try:
                dec = string_to_hypergraph(s, k=K)
            except Exception:
                STATS.s2h_fail += 1
                continue
            if dec.n_nodes < 1 or dec.n_edges < 1 or not dec.is_connected():
                # S2H is total; a decode with no edge has no canonical string
                continue
            w, _ = encode_hg(dec)
            if w in seen_w:
                continue
            seen_w.add(w)
            cands.append((toks, dec))
        best = None
        best_c = cur_c
        for toks, dec in cands:
            if evals >= BUDGET:
                break
            c = cost(dec, corpus)
            evals += 1
            if c < best_c:
                best, best_c = (toks, dec), c
        if best is None:
            break
        cur_str, cur_obj = best[0], best[1]
        cur_c = best_c
        steps += 1
    return cur_obj, cur_c, evals, steps, time.perf_counter() - t0


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
def main() -> None:
    records = []
    t_start = time.perf_counter()
    for cell_idx, (n, m) in enumerate(CELLS):
        for c_idx in range(CENTRES_PER_CELL):
            centre_seed = MASTER_SEED + 1000 * cell_idx + c_idx
            M0 = make_centre(n, m, random.Random(centre_seed))
            w0 = encode_hg(M0)[0]
            L0 = len(parse(w0))
            for t in NOISE_LEVELS:
                prof_seed = centre_seed * 10 + t
                rng = random.Random(prof_seed)
                corpus = [make_copy(M0, t, rng) for _ in range(N_COPIES)]

                # 7x7 matrix -- cached path, cross-checked against the module API
                D = np.array([[float(d_I(a, b)) for b in corpus] for a in corpus], dtype=np.float64)
                D_mod = _DIST.matrix(corpus)
                assert np.allclose(D, D_mod), "cached distance != IsalHGLevenshtein.matrix"

                col = D.sum(axis=1)
                j_med = int(np.argmin(col))
                C_med = float(col[j_med])
                medoid = corpus[j_med]
                iu = np.triu_indices(N_COPIES, 1)
                LB = float(D[iu].sum() / (N_COPIES - 1))
                d0 = [d_I(M0, K_i) for K_i in corpus]
                C_0 = float(sum(d0))
                zero_pairs = float((D[iu] == 0).mean())

                A_obj, C_A, evA, stA, tA = search_A(medoid, corpus, random.Random(prof_seed + 1))
                B_obj, C_B, evB, stB, tB = search_B(medoid, corpus, random.Random(prof_seed + 2))

                records.append(
                    dict(
                        n=n,
                        m=m,
                        t=t,
                        centre_seed=centre_seed,
                        profile_seed=prof_seed,
                        L0=L0,
                        C_med=C_med,
                        C_0=C_0,
                        LB=LB,
                        C_A=C_A,
                        C_B=C_B,
                        d_medoid_M0=d_I(medoid, M0),
                        d_A_M0=d_I(A_obj, M0),
                        d_B_M0=d_I(B_obj, M0),
                        mean_dM0=float(np.mean(d0)),
                        d0=d0,
                        avalanche=float(np.mean(d0)) / L0,
                        zero_pairs=zero_pairs,
                        evals_A=evA,
                        steps_A=stA,
                        secs_A=tA,
                        evals_B=evB,
                        steps_B=stB,
                        secs_B=tB,
                        A_n=A_obj.n_nodes,
                        A_m=A_obj.n_edges,
                        B_n=B_obj.n_nodes,
                        B_m=B_obj.n_edges,
                        M0_n=M0.n_nodes,
                        M0_m=M0.n_edges,
                    )
                )
                print(
                    f"({n},{m}) t={t} c={c_idx}: L0={L0} LB={LB:.1f} C_med={C_med:.0f} "
                    f"C_0={C_0:.0f} C_A={C_A:.0f} C_B={C_B:.0f} "
                    f"d(med,M0)={records[-1]['d_medoid_M0']} "
                    f"evA={evA} evB={evB} tA={tA:.1f}s tB={tB:.1f}s",
                    flush=True,
                )

    out = HERE / "pilot_consensus_results.json"
    out.write_text(
        json.dumps(
            dict(
                records=records,
                stats=dict(
                    n_canon=STATS.n_canon,
                    canon_time=STATS.canon_time,
                    max_canon=STATS.max_canon,
                    dnf=STATS.dnf,
                    s2h_fail=STATS.s2h_fail,
                ),
                wall_clock=time.perf_counter() - t_start,
                config=dict(
                    K=K,
                    N_COPIES=N_COPIES,
                    BUDGET=BUDGET,
                    NEIGHBOURS=NEIGHBOURS,
                    MASTER_SEED=MASTER_SEED,
                    CELLS=CELLS,
                    CENTRES_PER_CELL=CENTRES_PER_CELL,
                    NOISE_LEVELS=list(NOISE_LEVELS),
                ),
            ),
            indent=1,
        )
    )
    print(f"\nwrote {out}")
    print(
        f"canonicalizations={STATS.n_canon} total={STATS.canon_time:.1f}s "
        f"max={STATS.max_canon:.3f}s DNF(>30s)={STATS.dnf} S2H_failures={STATS.s2h_fail}"
    )
    print(f"total wall clock {time.perf_counter() - t_start:.1f}s")


if __name__ == "__main__":
    main()
