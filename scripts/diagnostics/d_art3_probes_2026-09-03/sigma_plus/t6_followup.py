"""Coordinator rulings R1 / R2 / R3.

R1 -- the anchor carries the MAXIMUM vertex label, so it wins the first rung of
      the seed cascade by construction. 300 fresh E1-top KBs with vertex labels
      {constants = 0, anchor = 1}.
R2 -- Prop 4(c) emits the j A+ tokens in REVERSE order of V's fresh-vertex list.
      Checked on the 60 trivial-label KBs and on a distinct-label stress set
      (constants in {0,1,2}, anchor = 3), for exact equality (same NodeIds, same
      per-id labels, same edge sets) and, separately, for isomorphism.
R3 -- coverage on the INDEL ball: witnesses built only from token insertions and
      deletions (no substitutions).
"""

from __future__ import annotations

import json
import random
import statistics as st
import time
from collections import Counter, defaultdict
from itertools import combinations

import sigma_plus as SP
from t4_reach import (
    CELLS,
    CENTRES_PER_CELL,
    MASTER_SEED,
    N_COPIES,
    NEL,
    NOISE,
    PKG_ALPHA,
    Profile,
    _match,
    comp_key,
    cost1_deletions,
    make_centre,
    make_copy,
    relabel_vocab,
)

from isalhg.core.canonical import canonical_fingerprint, canonical_string
from isalhg.core.instructions import TokenV
from isalhg.core.sparse_hypergraph import SparseHypergraph

K = 3


def exact_key(H: SparseHypergraph) -> tuple:
    """Identity of the *labelled, id-carrying* object: NodeIds, per-id vertex
    labels, and the labelled edge set. Equality means literally the same object."""
    return (
        H.n_nodes,
        tuple(H.vertex_label(v) for v in range(H.n_nodes)),
        frozenset((ell, m) for _, m, ell in H.iter_edges()),
    )


# ===========================================================================
# R1 -- anchor = seed by construction (anchor carries the max vertex label)
# ===========================================================================
def make_kb_labelled(rng: random.Random, n_vlab: int, anchor_label: int, arity=(2, 3)):
    """E1-top KB. Constants get labels in [0, anchor_label); the anchor gets
    `anchor_label`, the unique maximum, so the seed cascade must select it."""
    nc = rng.randint(8, 12)
    nf = rng.randint(8, 16)
    vlabs = [anchor_label] + [rng.randrange(max(anchor_label, 1)) for _ in range(nc)]
    H = SparseHypergraph(
        n_nodes=nc + 1, n_vertex_labels=n_vlab, n_edge_labels=NEL, vertex_labels=vlabs
    )
    for c in range(1, nc + 1):
        H.add_hyperedge([0, c], label=0)
    tries = 0
    while H.n_edges < nc + nf and tries < 20_000:
        tries += 1
        a = rng.choice(arity) if len(arity) > 1 else arity[0]
        H.add_hyperedge(rng.sample(range(1, nc + 1), a), label=rng.randint(1, NEL - 1))
    return H, anchor_label


def r1(n_kb: int = 300) -> dict:
    rng = random.Random(MASTER_SEED + 501)
    seed_is_anchor = rank0 = 0
    prefix_used = 0
    t0 = time.perf_counter()
    for _ in range(n_kb):
        H, alab = make_kb_labelled(rng, 2, 1)
        lab, w = canonical_fingerprint(H, k=K)
        prefix_used += int(lab == alab)
        H0 = SP.decode_plus(
            SP.parse_plus(w), k=K, n_vertex_labels=2, n_edge_labels=NEL, seed_label=lab
        )
        doms = [set(m) for _, m, ell in H0.iter_edges() if ell == 0]
        anchor = set.intersection(*doms).pop()
        seed_is_anchor += int(H0.vertex_label(anchor) == alab)
        rank0 += int(anchor == 0)
    return dict(
        n_kb=n_kb,
        seed_label_is_anchor_label=prefix_used,
        anchor_is_rank0=rank0,
        anchor_carries_max_label=seed_is_anchor,
        secs=time.perf_counter() - t0,
    )


# ===========================================================================
# R2 -- reverse-order re-attachment
# ===========================================================================
def r2_run(n_kb: int, n_vlab: int, anchor_label: int, arity, tag: str, seed: int) -> dict:
    rng = random.Random(seed)
    res: dict[str, Counter] = {o: Counter() for o in ("reverse", "forward")}
    for _ in range(n_kb):
        H, alab = make_kb_labelled(rng, n_vlab, anchor_label, arity)
        lab, w = canonical_fingerprint(H, k=K)
        toks = SP.parse_plus(w)
        it = SP.StringToHypergraphPlus(
            toks, k=K, n_vertex_labels=n_vlab, n_edge_labels=NEL, seed_label=lab
        )
        H0 = it.run(track_creators=True)
        doms = [set(m) for _, m, ell in H0.iter_edges() if ell == 0]
        a_rank = set.intersection(*doms).pop()
        es = SP.edge_set(H0)
        vl = [H0.vertex_label(v) for v in range(H0.n_nodes)]
        for f in [e for e in es if e[0] >= 1]:
            idxs = [i for i, c in enumerate(it.creators) if c == f]
            if not idxs or not isinstance(toks[idxs[0]], TokenV):
                continue
            tok = toks[idxs[0]]
            j = tok.j
            tgt = SparseHypergraph(
                H0.n_nodes, n_vertex_labels=n_vlab, n_edge_labels=NEL, vertex_labels=vl
            )
            for ell, mm in es - {f}:
                tgt.add_hyperedge(mm, label=ell)
            for order in ("reverse", "forward"):
                labs = (
                    list(reversed(tok.new_node_labels))
                    if order == "reverse"
                    else list(tok.new_node_labels)
                )
                repl = [SP.TokenAPlus(0, lam, (a_rank,)) for lam in labs]
                wit = toks[: idxs[0]] + repl + toks[idxs[0] + 1 :]
                got = SP.decode_plus(
                    wit, k=K, n_vertex_labels=n_vlab, n_edge_labels=NEL, seed_label=lab
                )
                c = res[order]
                c[f"j{j}_total"] += 1
                if exact_key(got) == exact_key(tgt):
                    c[f"j{j}_exact"] += 1
                if (
                    got.n_nodes == tgt.n_nodes
                    and got.is_connected()
                    and canonical_fingerprint(got, k=K) == canonical_fingerprint(tgt, k=K)
                ):
                    c[f"j{j}_iso"] += 1
    return {tag: {o: dict(c) for o, c in res.items()}}


# ===========================================================================
# R3 -- indel-only ball coverage
# ===========================================================================
def scan_indel(M: SparseHypergraph, pr: Profile):
    """reach<=1 / reach<=2 with witnesses made only of token INSERTIONS and
    DELETIONS.

    r = 1 enumerates the whole indel ball of radius 1 over Sigma^+:
      - the L single-token deletions of w*_c(M)                     (brute force)
      - the (L+1) * |Sigma_HG(3)| single package-token insertions    (brute force)
      - the A-token insertions: position-independent, so the set of results is
        exactly {S2H(w) + (l,S) : |S| <= 3, l <= 2}; tested as
        `S2H(w) ~ K` or `S2H(w) ~ K - f` for some f in E(K)          (exact)
      - the A+-token insertions: every one yields n+1 vertices (syntactic count
        n = 1 + sum_V j + #A+), and no target has n+1 vertices        (excluded)
      NB no substitution is used anywhere.

    r = 2 enumerates the fact-level indel compositions (each is 2 indel edits):
      (a) two A appends            : exists f1 != f2 in E(K) with K-f1-f2 ~ M
      (b) one A append + one cost-1 token deletion :
                                     exists f' cost-1 in M, f in E(K), K-f ~ M-f'
      (c) two cost-1 token deletions : M-f'1-f'2 ~ K
    """
    dels_c1, _nv, toks, _miss, Hd = cost1_deletions(M)
    L = len(toks)
    tgt_inv = {SP.invariant(Ki) for Ki in pr.copies}
    key_to_i: dict = {}
    for i, kk in enumerate(pr.tgt_key):
        key_to_i.setdefault(kk, []).append(i)
    r1_ = [False] * N_COPIES

    def consider(H):
        if SP.invariant(H) not in tgt_inv:
            return
        for i in key_to_i.get(comp_key(H), []):
            r1_[i] = True

    n_dec = 0
    for p in range(L):  # deletions
        consider(SP.decode_plus(toks[:p] + toks[p + 1 :], k=K, n_edge_labels=NEL))
        n_dec += 1
    for a in PKG_ALPHA:  # package insertions
        for p in range(L + 1):
            consider(SP.decode_plus(toks[:p] + [a] + toks[p:], k=K, n_edge_labels=NEL))
            n_dec += 1
    base = SP.decode_plus(toks, k=K, n_edge_labels=NEL)  # A insertions (exact reduction)
    for i in range(N_COPIES):
        if not r1_[i] and _match(base, pr.T1[i]):
            r1_[i] = True

    r2_ = list(r1_)
    for i in range(N_COPIES):
        if r2_[i]:
            continue
        if _match(M, pr.T2[i]):
            r2_[i] = True
            continue
        for _f, Md in dels_c1:
            if _match(Md, pr.T1[i]):
                r2_[i] = True
                break
        if r2_[i]:
            continue
        for (f1, _), (f2, _) in combinations(dels_c1, 2):
            H = SP.from_edge_set(Hd.n_nodes, SP.edge_set(Hd) - {f1, f2}, n_edge_labels=NEL)
            if SP.invariant(H) == SP.invariant(pr.copies[i]) and comp_key(H) == pr.tgt_key[i]:
                r2_[i] = True
                break
    return r1_, r2_, n_dec


def r3() -> list[dict]:
    rows = []
    t0 = time.perf_counter()
    for ci, (n, m) in enumerate(CELLS):
        for c in range(CENTRES_PER_CELL):
            cseed = MASTER_SEED + 1000 * ci + c
            M0 = relabel_vocab(make_centre(n, m, random.Random(cseed)))
            H0 = SP.decode_plus(SP.parse_plus(canonical_string(M0, k=K)), k=K, n_edge_labels=NEL)
            for t in NOISE:
                for fam in ("I", "D"):
                    rng = random.Random(cseed * 100 + t * 10 + (0 if fam == "I" else 1))
                    copies = [make_copy(H0, t, fam, rng) for _ in range(N_COPIES)]
                    pr = Profile(H0, copies)
                    cands = {"H0": H0, **{f"K{i}": copies[i] for i in range(N_COPIES)}}
                    cov1, cov2 = {}, {}
                    c2c1 = c2c2 = 0
                    for cid, M in cands.items():
                        a1, a2, _ = scan_indel(M, pr)
                        si = None if cid == "H0" else int(cid[1:])
                        cov1[cid] = sum(1 for i, b in enumerate(a1) if b and i != si)
                        cov2[cid] = sum(1 for i, b in enumerate(a2) if b and i != si)
                        if si is not None:
                            c2c1 += cov1[cid]
                            c2c2 += cov2[cid]
                    b1 = max(cov1[f"K{i}"] for i in range(N_COPIES))
                    b2 = max(cov2[f"K{i}"] for i in range(N_COPIES))
                    rows.append(
                        dict(
                            n=n,
                            m=m,
                            t=t,
                            family=fam,
                            centre=cseed % 1000,
                            cov1_H0=cov1["H0"],
                            cov2_H0=cov2["H0"],
                            cov1_best_copy=b1,
                            cov2_best_copy=b2,
                            uniq1=cov1["H0"] > b1,
                            uniq2=cov2["H0"] > b2,
                            c2c_r1=c2c1 / (N_COPIES * (N_COPIES - 1)),
                            c2c_r2=c2c2 / (N_COPIES * (N_COPIES - 1)),
                        )
                    )
                    print(
                        f"[{len(rows)}/48] ({n},{m}) t={t} {fam}: cov1 H0={cov1['H0']} "
                        f"best={b1} | cov2 H0={cov2['H0']} best={b2} | "
                        f"c2c r1={rows[-1]['c2c_r1']:.2f} r2={rows[-1]['c2c_r2']:.2f} "
                        f"{time.perf_counter() - t0:.0f}s",
                        flush=True,
                    )
    return rows


if __name__ == "__main__":
    out = {}
    out["R1"] = r1()
    print("R1:", json.dumps(out["R1"]), flush=True)
    out["R2"] = {}
    out["R2"].update(r2_run(60, 1, 0, (2, 3), "trivial_labels_60kb", MASTER_SEED + 502))
    print("R2 trivial:", json.dumps(out["R2"]), flush=True)
    out["R2"].update(r2_run(40, 4, 3, (3,), "distinct_labels_40kb", MASTER_SEED + 503))
    print("R2 distinct:", json.dumps(out["R2"]["distinct_labels_40kb"]), flush=True)
    out["R3"] = r3()
    with open("results_t6.json", "w") as fh:
        json.dump(out, fh, indent=1)

    g = defaultdict(list)
    for r in out["R3"]:
        g[(r["n"], r["m"], r["t"], r["family"])].append(r)
    print(
        "\n| cell | t | fam | cov1^indel(H0)/7 | best copy/6 | uniq r1 | "
        "cov2^indel(H0)/7 | best copy/6 | uniq r2 | c2c r1 | c2c r2 |"
    )
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for kk in sorted(g):
        rs = g[kk]
        print(
            f"| ({kk[0]},{kk[1]}) | {kk[2]} | {kk[3]} | "
            f"{st.mean(r['cov1_H0'] for r in rs):.2f} | "
            f"{st.mean(r['cov1_best_copy'] for r in rs):.2f} | "
            f"{sum(r['uniq1'] for r in rs)}/{len(rs)} | "
            f"{st.mean(r['cov2_H0'] for r in rs):.2f} | "
            f"{st.mean(r['cov2_best_copy'] for r in rs):.2f} | "
            f"{sum(r['uniq2'] for r in rs)}/{len(rs)} | "
            f"{st.mean(r['c2c_r1'] for r in rs):.2f} | "
            f"{st.mean(r['c2c_r2'] for r in rs):.2f} |"
        )
