"""Task 5 -- ball cost: |B_1^+(w)| vs |B_1(w)| on the 12 pilot centres, plus a
timed full B_1^+ decode (+ sampled canonicalization) for 3 of them.

|B_1(w)| over an alphabet of size S and a word of length L is counted exactly:
    1  (w itself)
  + R  (deletions; deleting any position inside a maximal run of equal tokens
        gives the same word, so R = number of maximal runs)
  + L (S - 1)                       (substitutions, all distinct)
  + (L + 1) S - L                   (insertions; inserting w[i] at i and at i+1
                                     coincide, one duplicate per position)
Lengths L-1 / L / L+1 keep the four groups disjoint.  The formula is checked
against brute-force enumeration on short words before it is used.
"""

from __future__ import annotations

import json
import random
import time

import sigma_plus as SP
from t4_reach import CELLS, CENTRES_PER_CELL, MASTER_SEED, NEL, make_centre, relabel_vocab

from isalhg.core.canonical import canonical_string

K = 3
SAMPLE_CANON = 300
TIMED_CENTRES = 3


def ball_size(w, alphabet_size: int) -> int:
    L = len(w)
    runs = 1 + sum(1 for i in range(1, L) if w[i] != w[i - 1]) if L else 0
    return 1 + runs + L * (alphabet_size - 1) + ((L + 1) * alphabet_size - L)


def brute_ball(w, alphabet) -> set:
    out = {tuple(w)}
    L = len(w)
    for i in range(L):
        out.add(tuple(w[:i] + w[i + 1 :]))
        for a in alphabet:
            out.add(tuple(w[:i] + [a] + w[i + 1 :]))
    for i in range(L + 1):
        for a in alphabet:
            out.add(tuple(w[:i] + [a] + w[i:]))
    return out


def enumerate_ball(w, alphabet):
    yield tuple(w)
    L = len(w)
    seen_del = set()
    for i in range(L):
        d = tuple(w[:i] + w[i + 1 :])
        if d not in seen_del:
            seen_del.add(d)
            yield d
        for a in alphabet:
            if a != w[i]:
                yield tuple(w[:i] + [a] + w[i + 1 :])
    for i in range(L + 1):
        for a in alphabet:
            if i < L and a == w[i]:
                continue  # the duplicate of the (i+1, a) insertion
            yield tuple(w[:i] + [a] + w[i:])


def main() -> None:
    # --- formula check against brute force -------------------------------
    rng = random.Random(20260903)
    small = SP.sigma_hg_alphabet(2, 1, 1)
    checks = []
    for _ in range(30):
        w = [rng.choice(small) for _ in range(rng.randint(0, 6))]
        checks.append(len(brute_ball(w, small)) == ball_size(w, len(small)))
        checks.append(len(set(enumerate_ball(w, small))) == len(brute_ball(w, small)))
    assert all(checks), "ball-size formula / enumerator disagrees with brute force"
    print(f"formula check: {sum(checks)}/{len(checks)} exact")

    rows = []
    timed = []
    idx = 0
    for ci, (n, m) in enumerate(CELLS):
        for c in range(CENTRES_PER_CELL):
            cseed = MASTER_SEED + 1000 * ci + c
            M0 = relabel_vocab(make_centre(n, m, random.Random(cseed)))
            w = SP.parse_plus(canonical_string(M0, k=K))
            nn = M0.n_nodes
            nA = len(SP.a_tokens(nn, K, NEL))
            nAp = len(SP.aplus_tokens(nn, K, NEL, 1))
            s_triv = len(SP.sigma_hg_alphabet(K, 1, 1))  # 13, the 2026-09-03 probe's alphabet
            s_pkg = len(SP.sigma_hg_alphabet(K, NEL, 1))  # 25, 3 edge labels
            s_plus = s_pkg + nA + nAp
            rows.append(
                dict(
                    cell=f"({n},{m})",
                    centre=cseed % 1000,
                    n=nn,
                    L=len(w),
                    sigma_trivial=s_triv,
                    sigma_pkg=s_pkg,
                    n_A=nA,
                    n_Aplus=nAp,
                    sigma_plus=s_plus,
                    B1_trivial=ball_size(w, s_triv),
                    B1_pkg=ball_size(w, s_pkg),
                    B1_plus=ball_size(w, s_plus),
                    ratio_plus_over_trivial=ball_size(w, s_plus) / ball_size(w, s_triv),
                )
            )
            # --- timed full decode + sampled canonicalization -------------
            if idx < TIMED_CENTRES or (idx == CENTRES_PER_CELL and len(timed) < TIMED_CENTRES + 1):
                if len(timed) < TIMED_CENTRES:
                    alpha = (
                        SP.sigma_hg_alphabet(K, NEL, 1)
                        + SP.a_tokens(nn, K, NEL)
                        + SP.aplus_tokens(nn, K, NEL, 1)
                    )
                    t0 = time.perf_counter()
                    keys, nw, n_conn = set(), 0, 0
                    for wd in enumerate_ball(list(w), alpha):
                        H = SP.decode_plus(wd, k=K, n_edge_labels=NEL)
                        nw += 1
                        if H.n_edges and H.is_connected():
                            n_conn += 1
                            keys.add(SP.structural_key(H))
                    t_dec = time.perf_counter() - t0
                    ks = sorted(keys, key=lambda x: (x[0], len(x[2])))
                    smp = random.Random(7).sample(ks, min(SAMPLE_CANON, len(ks)))
                    t1 = time.perf_counter()
                    for sk in smp:
                        Hs = SP.from_edge_set(
                            sk[0], [(ell, frozenset(mm)) for mm, ell in sk[2]], n_edge_labels=NEL
                        )
                        canonical_string(Hs, k=K)
                    t_can = time.perf_counter() - t1
                    timed.append(
                        dict(
                            cell=f"({n},{m})",
                            centre=cseed % 1000,
                            L=len(w),
                            words=nw,
                            decode_secs=t_dec,
                            decode_us_per_word=1e6 * t_dec / nw,
                            connected_nonempty=n_conn,
                            distinct_structures=len(ks),
                            canon_sample=len(smp),
                            canon_secs=t_can,
                            canon_ms_each=1e3 * t_can / max(len(smp), 1),
                            projected_full_canon_secs=t_can / max(len(smp), 1) * len(ks),
                        )
                    )
                    print(f"timed {timed[-1]}", flush=True)
            idx += 1
    out = dict(rows=rows, timed=timed)
    with open("results_t5.json", "w") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
