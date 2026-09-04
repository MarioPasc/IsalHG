"""Task 3 -- Proposition 4 (fact-level simulation) on anchored knowledge bases.

Encoding E1-top with the *labelled* vocabulary the package supports natively:
trivial vertex vocabulary (|Sigma_V| = 1), edge labels {dom = 0, facts 1..r},
r = 2.  Preflight confirmed canonical_string is edge-label sensitive, that the
declared vocabulary size alone does not change the string, and that the
canonical seed is the anchor in 8/8 pilot KBs (re-measured here on all 60).

Insertion witness :  w*_c(K) . A[l; r_1 ... r_a]                      (1 token)
Deletion witness  :  drop the C token that created the fact           (1 token)
                     or replace the V token that created it, together with its
                     j fresh constants, by j copies of A+[dom; lam; anchor]
                                                                      (j tokens)
"""

from __future__ import annotations

import json
import random
import time
from collections import Counter

import sigma_plus as SP

from isalhg.core.canonical import canonical_string
from isalhg.core.sparse_hypergraph import SparseHypergraph

K = 3
R = 2  # fact labels 1..2; dom = 0
NEL = R + 1
SEED = 20260903
N_KB = 60
N_INSERT_SAMPLES = 20


def make_kb(rng: random.Random) -> SparseHypergraph:
    n_const = rng.randint(8, 12)
    n_facts = rng.randint(8, 16)
    H = SparseHypergraph(n_nodes=n_const + 1, n_vertex_labels=1, n_edge_labels=NEL)
    for c in range(1, n_const + 1):
        H.add_hyperedge([0, c], label=0)
    tries = 0
    while H.n_edges < n_const + n_facts and tries < 20_000:
        tries += 1
        a = rng.choice((2, 3))
        H.add_hyperedge(rng.sample(range(1, n_const + 1), a), label=rng.randint(1, R))
    return H


def canon(H: SparseHypergraph) -> str:
    return canonical_string(H, k=K)


def anchor_of(H: SparseHypergraph) -> int:
    doms = [set(m) for _, m, ell in H.iter_edges() if ell == 0]
    inter = set.intersection(*doms)
    assert len(inter) == 1, f"anchor not unique: {inter}"
    return inter.pop()


def main() -> None:
    rng = random.Random(SEED + 3)
    t_start = time.perf_counter()
    ins_ok = ins_tot = 0
    del_ok = del_tot = 0
    del_by_kind: Counter = Counter()
    del_fail_by_kind: Counter = Counter()
    edit_counts: Counter = Counter()
    seed_is_anchor = 0
    creator_missing = 0
    kb_rows = []

    for kb_idx in range(N_KB):
        H = make_kb(rng)
        w = canon(H)
        toks = SP.parse_plus(w)
        interp = SP.StringToHypergraphPlus(toks, k=K, n_edge_labels=NEL)
        H0 = interp.run(track_creators=True)
        creators = interp.creators
        assert canon(H0) == w, "decode(w*_c) is not canonical-equal to the source KB"
        a_rank = anchor_of(H0)
        seed_is_anchor += int(a_rank == 0)
        base_edges = SP.edge_set(H0)
        facts = sorted(
            ((ell, m) for ell, m in base_edges if ell >= 1), key=lambda x: (x[0], sorted(x[1]))
        )
        consts = [v for v in range(H0.n_nodes) if v != a_rank]

        # ---------------- INSERTIONS ------------------------------------
        cand = []
        for _ in range(400):
            if len(cand) >= N_INSERT_SAMPLES:
                break
            a = rng.choice((2, 3))
            S = frozenset(rng.sample(consts, a))
            ell = rng.randint(1, R)
            if (ell, S) not in base_edges and (ell, S) not in cand:
                cand.append((ell, S))
        for ell, S in cand:
            target = SP.from_edge_set(H0.n_nodes, base_edges | {(ell, S)}, n_edge_labels=NEL)
            witness = [*toks, SP.TokenA(edge_label=ell, ranks=tuple(sorted(S)))]
            got = SP.decode_plus(witness, k=K, n_edge_labels=NEL)
            ins_tot += 1
            ins_ok += int(canon(got) == canon(target))

        # ---------------- DELETIONS -------------------------------------
        for ell, S in facts:
            idxs = [i for i, c in enumerate(creators) if c == (ell, S)]
            if not idxs:
                creator_missing += 1
                del_tot += 1
                continue
            idx = idxs[0]
            tok = toks[idx]
            if isinstance(tok, SP.TokenC):
                witness = toks[:idx] + toks[idx + 1 :]
                n_edits = 1
                kind = "C"
            elif isinstance(tok, SP.TokenV):
                j = tok.j
                repl = [
                    SP.TokenAPlus(edge_label=0, new_label=lam, ranks=(a_rank,))
                    for lam in tok.new_node_labels
                ]
                witness = toks[:idx] + repl + toks[idx + 1 :]
                n_edits = j
                kind = f"V(j={j})"
            else:
                del_tot += 1
                del_fail_by_kind[type(tok).__name__] += 1
                continue
            target = SP.from_edge_set(H0.n_nodes, base_edges - {(ell, S)}, n_edge_labels=NEL)
            got = SP.decode_plus(witness, k=K, n_edge_labels=NEL)
            ok = (
                got.n_nodes == target.n_nodes and got.is_connected() and canon(got) == canon(target)
            )
            del_tot += 1
            del_ok += int(ok)
            del_by_kind[kind] += 1
            edit_counts[n_edits] += 1
            if not ok:
                del_fail_by_kind[kind] += 1

        kb_rows.append(
            dict(n=H0.n_nodes, m=H0.n_edges, n_facts=len(facts), L=len(toks), anchor=a_rank)
        )
        if (kb_idx + 1) % 10 == 0:
            print(
                f"[{kb_idx + 1}/{N_KB}] ins {ins_ok}/{ins_tot}  del {del_ok}/{del_tot}  "
                f"{time.perf_counter() - t_start:.0f}s",
                flush=True,
            )

    out = dict(
        n_kb=N_KB,
        kb_n=[r["n"] for r in kb_rows],
        kb_m=[r["m"] for r in kb_rows],
        kb_L=[r["L"] for r in kb_rows],
        seed_is_anchor=seed_is_anchor,
        insertions=dict(ok=ins_ok, total=ins_tot, fraction=ins_ok / max(ins_tot, 1)),
        deletions=dict(
            ok=del_ok,
            total=del_tot,
            fraction=del_ok / max(del_tot, 1),
            by_creator=dict(del_by_kind),
            failures_by_creator=dict(del_fail_by_kind),
            creator_missing=creator_missing,
        ),
        witness_edit_counts=dict(edit_counts),
        secs=time.perf_counter() - t_start,
    )
    print(json.dumps(out, indent=1))
    with open("results_t3.json", "w") as fh:
        json.dump(out, fh, indent=1)


if __name__ == "__main__":
    main()
