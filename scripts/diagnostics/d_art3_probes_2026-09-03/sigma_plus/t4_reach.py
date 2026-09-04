"""Task 4 -- Proposition 5 / the reach + ball-coverage pilot re-run under Sigma^+.

Substrate: the 12 planted centres of `reach_probe.py`, rebuilt from the *same*
pilot seeds (MASTER_SEED = 20260903, cells (8,10) and (10,12), 6 centres each);
each rebuild is checked against the stored `L0` of `pilot_consensus_results.json`.

Copies are regenerated as *fact-level* variants of the rank-numbered decoded
centre `H_0 = S2H(w*_c(M_0))`:
  family I : t in {1,2} insertions of a random fact (arity 2 or 3, label in
             {0,1,2}) over existing constants;
  family D : t in {1,2} deletions of an existing fact, connectivity preserved;
each followed by a random vertex permutation.  7 copies per (centre, t, family)
=> 48 profiles.

reach(M -> K) <= 1  is decided by the FULL single-token ball B_1^+(w*_c(M)):
  (i)   all package tokens Sigma_HG(3) over 3 edge labels (25 tokens): brute
        force over all deletions / substitutions / insertions;
  (ii)  all A tokens (rank subsets of size <= 3, labels <= 2): handled by an
        exact reduction -- inserting or substituting-in an A token can only
        yield `base + one edge`, so the test is
            exists base B in {w} u {w minus one token} : B ~ K - f  for some f in E(K)
        (or B ~ K, the no-op case).  Enumerated token count is reported.
  (iii) all A+ tokens: a syntactic vertex-count filter (n(w) = 1 + sum_V j +
        #A+) rules out every A+ insertion and every A+ substitution except at a
        V token with j = 1; those are brute-forced.

reach(M -> K) <= 2 enumerates exactly the fact-level two-step witnesses:
  (a) two A appends            : exists f1 != f2 in E(K) with K-f1-f2 ~ M
  (b) one A append + one cost-1 deletion : exists f' cost-1 in M, f in E(K) with K-f ~ M-f'
  (c) two cost-1 deletions     : M-f'1-f'2 ~ K
  plus everything at r <= 1.
`cost-1 deletion` = the fact's creating token in w*_c(M) is a C token, so the
witness is a single token deletion.  On this NON-anchored substrate a V-created
fact has NO bounded-cost deletion witness (the j fresh constants would be lost);
that is exactly the gap the anchored encoding E1-top of Task 3 closes.
"""

from __future__ import annotations

import json
import random
import sys
import time
from itertools import combinations
from pathlib import Path

import sigma_plus as SP

from isalhg.core.canonical import canonical_string
from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.datasets.synthetic._random_hg import random_connected_hypergraph

K = 3
NEL = 3  # edge labels 0..2 (the coordinator's "labels <= 2")
N_COPIES = 7
MASTER_SEED = 20260903
CELLS = [(8, 10), (10, 12)]
CENTRES_PER_CELL = 6
NOISE = (1, 2)
FAMILIES = ("I", "D")
PILOT = Path(
    "/home/mpascual/research/code/IsalHG/scripts/diagnostics/d_art3_probes_2026-09-03/"
    "pilot_consensus_results.json"
)
DEADLINE = time.perf_counter() + float(sys.argv[1] if len(sys.argv) > 1 else 1500.0)

PKG_ALPHA = SP.sigma_hg_alphabet(K, NEL, 1)
_CANON: dict[tuple, str] = {}
N_CANON = [0]


def comp_key(H: SparseHypergraph) -> tuple:
    """Complete iso-invariant for a possibly disconnected hypergraph:
    the sorted multiset of its components' canonical strings."""
    sk = SP.structural_key(H)
    hit = _CANON.get(sk)
    if hit is not None:
        return hit
    # component split on the primal graph, isolated vertices included
    adj = H.primal_graph()
    seen: set[int] = set()
    keys = []
    for v in range(H.n_nodes):
        if v in seen:
            continue
        stack, comp = [v], {v}
        seen.add(v)
        while stack:
            u = stack.pop()
            for x in adj[u]:
                if x not in comp:
                    comp.add(x)
                    seen.add(x)
                    stack.append(x)
        idx = {u: i for i, u in enumerate(sorted(comp))}
        sub = SparseHypergraph(len(comp), n_vertex_labels=1, n_edge_labels=NEL)
        nm = 0
        for _, m, ell in H.iter_edges():
            if next(iter(m)) in comp:
                sub.add_hyperedge([idx[u] for u in m], label=ell)
                nm += 1
        N_CANON[0] += 1
        keys.append((len(comp), nm, canonical_string(sub, k=K) if nm else ""))
    out = tuple(sorted(keys))
    _CANON[sk] = out
    return out


def make_centre(n: int, m: int, rng: random.Random) -> SparseHypergraph:
    """Byte-identical to `pilot_consensus.make_centre` (same generator, same rng)."""
    for _ in range(500):
        H, _ = random_connected_hypergraph(n_nodes=n, n_edges=m, arity_range=(3, 3), rng=rng)
        seen = set()
        ok = all(len(mm) <= K for _, mm, _ in H.iter_edges())
        for _, mm, ell in H.iter_edges():
            if (mm, ell) in seen:
                ok = False
            seen.add((mm, ell))
        if ok and H.n_edges == m and H.n_nodes == n and H.is_connected():
            return H
    raise RuntimeError("no centre")


def relabel_vocab(H: SparseHypergraph) -> SparseHypergraph:
    """Same object, declared over NEL edge labels (w*_c is unchanged -- preflight)."""
    return SP.from_edge_set(H.n_nodes, SP.edge_set(H), n_edge_labels=NEL)


def make_copy(H0: SparseHypergraph, t: int, family: str, rng: random.Random):
    for _ in range(400):
        cur = H0
        ok = True
        for _ in range(t):
            if family == "I":
                for _ in range(200):
                    a = rng.choice((2, 3))
                    S = frozenset(rng.sample(range(cur.n_nodes), a))
                    ell = rng.randrange(NEL)
                    if (ell, S) not in SP.edge_set(cur):
                        cur = SP.from_edge_set(
                            cur.n_nodes, SP.edge_set(cur) | {(ell, S)}, n_edge_labels=NEL
                        )
                        break
                else:
                    ok = False
            else:
                es = sorted(SP.edge_set(cur), key=lambda x: (x[0], sorted(x[1])))
                rng.shuffle(es)
                for f in es:
                    nxt = SP.from_edge_set(cur.n_nodes, SP.edge_set(cur) - {f}, n_edge_labels=NEL)
                    if nxt.is_connected() and nxt.n_edges >= 1:
                        cur = nxt
                        break
                else:
                    ok = False
            if not ok:
                break
        if not ok:
            continue
        perm = list(range(cur.n_nodes))
        rng.shuffle(perm)
        return permute(cur, perm)
    raise RuntimeError("no copy")


class Profile:
    def __init__(self, H0, copies):
        self.H0 = H0
        self.copies = copies
        self.tgt_key = [comp_key(Ki) for Ki in copies]
        # target-side lazy tables, keyed by invariant
        self.T1 = []  # {K} u {K-f}
        self.T2 = []  # {K-f1-f2}
        for Ki in copies:
            es = sorted(SP.edge_set(Ki), key=lambda x: (x[0], sorted(x[1])))
            t1 = {Ki}
            t1 |= {SP.from_edge_set(Ki.n_nodes, set(es) - {f}, n_edge_labels=NEL) for f in es}
            t2 = {
                SP.from_edge_set(Ki.n_nodes, set(es) - {f1, f2}, n_edge_labels=NEL)
                for f1, f2 in combinations(es, 2)
            }
            self.T1.append(_index(t1))
            self.T2.append(_index(t2))


def _index(hs) -> dict:
    d: dict = {}
    for H in hs:
        d.setdefault(SP.invariant(H), []).append(H)
    return d


def _match(H, table) -> bool:
    """True iff H is isomorphic to some hypergraph in the invariant-indexed table."""
    bucket = table.get(SP.invariant(H))
    if not bucket:
        return False
    kh = comp_key(H)
    return any(comp_key(X) == kh for X in bucket)


def cost1_deletions(M: SparseHypergraph):
    """Facts whose creating token in ``w*_c(M)`` is a ``C`` token, hence deletable
    by a single token deletion. Works in the *decoded* (rank) numbering, which is
    the numbering the creator trace speaks; downstream comparisons are all
    canonical-key comparisons, so the numbering is immaterial."""
    toks = SP.parse_plus(canonical_string(M, k=K))
    it = SP.StringToHypergraphPlus(toks, k=K, n_edge_labels=NEL)
    Hd = it.run(track_creators=True)
    es = SP.edge_set(Hd)
    out, n_v, n_missing = [], 0, 0
    for f in es:
        idxs = [i for i, c in enumerate(it.creators) if c == f]
        if not idxs:
            n_missing += 1
            continue
        if isinstance(toks[idxs[0]], SP.TokenC):
            out.append((f, SP.from_edge_set(Hd.n_nodes, es - {f}, n_edge_labels=NEL)))
        else:
            n_v += 1
    return out, n_v, toks, n_missing, Hd


def scan(M: SparseHypergraph, pr: Profile) -> tuple[list[bool], list[bool], dict]:
    """Return (reach<=1 per target, reach<=2 per target, enumeration counts)."""
    dels_c1, n_v_created, toks, n_missing, Hd = cost1_deletions(M)
    L = len(toks)
    n_M = M.n_nodes
    tgt_inv = {SP.invariant(Ki) for Ki in pr.copies}
    key_to_i = {}
    for i, kk in enumerate(pr.tgt_key):
        key_to_i.setdefault(kk, []).append(i)
    r1 = [False] * N_COPIES

    def consider(H):
        if SP.invariant(H) not in tgt_inv:
            return
        for i in key_to_i.get(comp_key(H), []):
            r1[i] = True

    # ---- (i) package part: full brute force -----------------------------
    bases = []
    n_dec = 0
    for p in range(L):
        w = toks[:p] + toks[p + 1 :]
        H = SP.decode_plus(w, k=K, n_edge_labels=NEL)
        n_dec += 1
        bases.append(H)
        consider(H)
    bases.append(SP.decode_plus(toks, k=K, n_edge_labels=NEL))
    for a in PKG_ALPHA:
        for p in range(L):
            H = SP.decode_plus(toks[:p] + [a] + toks[p + 1 :], k=K, n_edge_labels=NEL)
            n_dec += 1
            consider(H)
        for p in range(L + 1):
            H = SP.decode_plus(toks[:p] + [a] + toks[p:], k=K, n_edge_labels=NEL)
            n_dec += 1
            consider(H)

    # ---- (ii) A part: exact base + one-edge reduction --------------------
    for B in bases:
        for i in range(N_COPIES):
            if not r1[i] and _match(B, pr.T1[i]):
                r1[i] = True

    # ---- (iii) A+ part: syntactic vertex-count filter, then brute force ---
    ap = SP.aplus_tokens(n_M, K, NEL, 1)
    n_ap_dec = 0
    for p in range(L):
        if not (isinstance(toks[p], SP.TokenV) and toks[p].j == 1):
            continue  # any other position changes n; no target has n +- 1
        for a in ap:
            H = SP.decode_plus(toks[:p] + [a] + toks[p + 1 :], k=K, n_edge_labels=NEL)
            n_ap_dec += 1
            consider(H)

    # ---- r <= 2, fact-level only ----------------------------------------
    r2 = list(r1)
    for i in range(N_COPIES):
        if r2[i]:
            continue
        if _match(M, pr.T2[i]):  # (a) two A appends
            r2[i] = True
            continue
        for _f, Md in dels_c1:  # (b) one append + one cost-1 deletion
            if _match(Md, pr.T1[i]):
                r2[i] = True
                break
        if r2[i]:
            continue
        for (f1, _), (f2, _) in combinations(dels_c1, 2):  # (c) two cost-1 deletions
            H = SP.from_edge_set(Hd.n_nodes, SP.edge_set(Hd) - {f1, f2}, n_edge_labels=NEL)
            if SP.invariant(H) == SP.invariant(pr.copies[i]) and comp_key(H) == pr.tgt_key[i]:
                r2[i] = True
                break

    n_A = len(SP.a_tokens(n_M, K, NEL))
    return (
        r1,
        r2,
        dict(
            L=L,
            n_package_decodes=n_dec,
            n_aplus_decodes=n_ap_dec,
            n_A_tokens=n_A,
            n_Aplus_tokens=len(ap),
            n_sigma_plus=len(PKG_ALPHA) + n_A + len(ap),
            n_cost1_facts=len(dels_c1),
            n_Vcreated_facts=n_v_created,
            n_creator_missing=n_missing,
            n_edges=Hd.n_edges,
        ),
    )


def main() -> None:
    recs = {r["centre_seed"]: r for r in json.loads(PILOT.read_text())["records"]}
    rows = []
    t0 = time.perf_counter()
    done = 0
    for ci, (n, m) in enumerate(CELLS):
        for c in range(CENTRES_PER_CELL):
            cseed = MASTER_SEED + 1000 * ci + c
            M0 = relabel_vocab(make_centre(n, m, random.Random(cseed)))
            w0 = canonical_string(M0, k=K)
            assert len(SP.parse_plus(w0)) == recs[cseed]["L0"], "centre did not reproduce"
            H0 = SP.decode_plus(SP.parse_plus(w0), k=K, n_edge_labels=NEL)
            for t in NOISE:
                for fam in FAMILIES:
                    if time.perf_counter() > DEADLINE:
                        print("DEADLINE -- stopping", flush=True)
                        _write(rows, t0, done)
                        return
                    rng = random.Random(cseed * 100 + t * 10 + (0 if fam == "I" else 1))
                    copies = [make_copy(H0, t, fam, rng) for _ in range(N_COPIES)]
                    pr = Profile(H0, copies)
                    cands = {"H0": H0, **{f"K{i}": copies[i] for i in range(N_COPIES)}}
                    cov1, cov2, enum = {}, {}, None
                    c2c = 0
                    for cid, M in cands.items():
                        a1, a2, enum = scan(M, pr)
                        self_i = None if cid == "H0" else int(cid[1:])
                        cov1[cid] = sum(1 for i, b in enumerate(a1) if b and i != self_i)
                        cov2[cid] = sum(1 for i, b in enumerate(a2) if b and i != self_i)
                        if self_i is not None:
                            c2c += cov1[cid]
                    best_copy1 = max(cov1[f"K{i}"] for i in range(N_COPIES))
                    best_copy2 = max(cov2[f"K{i}"] for i in range(N_COPIES))
                    rows.append(
                        dict(
                            n=n,
                            m=m,
                            t=t,
                            family=fam,
                            centre_seed=cseed,
                            cov1=cov1,
                            cov2=cov2,
                            cov1_H0=cov1["H0"],
                            cov2_H0=cov2["H0"],
                            cov1_best_copy=best_copy1,
                            cov2_best_copy=best_copy2,
                            H0_unique_max1=cov1["H0"] > best_copy1,
                            H0_unique_max2=cov2["H0"] > best_copy2,
                            copy_to_copy_r1=c2c / (N_COPIES * (N_COPIES - 1)),
                            enum=enum,
                            secs=time.perf_counter() - t0,
                        )
                    )
                    done += 1
                    print(
                        f"[{done}/48] ({n},{m}) t={t} {fam} c={cseed % 1000}: "
                        f"cov1 H0={cov1['H0']}/7 best_copy={best_copy1}/6 | "
                        f"cov2 H0={cov2['H0']}/7 best={best_copy2}/6 | "
                        f"c2c={rows[-1]['copy_to_copy_r1']:.2f} | "
                        f"|S+|={enum['n_sigma_plus']} L={enum['L']} "
                        f"C-facts={enum['n_cost1_facts']}/{enum['n_edges']} miss={enum['n_creator_missing']} "
                        f"{time.perf_counter() - t0:.0f}s",
                        flush=True,
                    )
    _write(rows, t0, done)


def _write(rows, t0, done):
    with open("results_t4.json", "w") as fh:
        json.dump(
            dict(rows=rows, profiles_done=done, wall=time.perf_counter() - t0, n_canon=N_CANON[0]),
            fh,
            indent=1,
        )
    print(
        f"wrote results_t4.json: {done} profiles, {time.perf_counter() - t0:.0f}s, "
        f"{N_CANON[0]} component canonicalizations"
    )


if __name__ == "__main__":
    main()
