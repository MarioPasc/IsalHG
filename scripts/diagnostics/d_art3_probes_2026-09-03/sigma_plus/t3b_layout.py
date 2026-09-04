"""Focused diagnostic: does a run of j A+ tokens reproduce the CDLL layout of one
V token with j fresh vertices?  (The coordinator flagged this as the one place
the design may need a correction.)

Part 1 -- direct layout demonstration on a hand-built word.
Part 2 -- deletion witnesses on arity-3-only anchored KBs, which push the share
          of V-created facts (and hence j = 2 witnesses) far above the arity-2/3
          mix of `t3_prop4.py`.
"""

from __future__ import annotations

import json
import random
from collections import Counter

import sigma_plus as SP

from isalhg.core.canonical import canonical_string
from isalhg.core.instructions import TokenV
from isalhg.core.sparse_hypergraph import SparseHypergraph

K = 3
NEL = 3


def part1() -> dict:
    """V[0;1;2;0,0] vs A+[0;0;0] ; A+[0;0;0] executed from the same VM state."""
    wv = [TokenV(edge_label=0, i=1, j=2, new_node_labels=(0, 0))]
    wa = [SP.TokenAPlus(0, 0, (0,)), SP.TokenAPlus(0, 0, (0,))]
    iv = SP.StringToHypergraphPlus(wv, k=K, n_edge_labels=NEL)
    iv.run()
    ia = SP.StringToHypergraphPlus(wa, k=K, n_edge_labels=NEL)
    ia.run()
    return dict(
        V_cdll_order=iv._cdll.values(),
        Aplus_cdll_order=ia._cdll.values(),
        layouts_equal=iv._cdll.values() == ia._cdll.values(),
        note="creation order is 0,1,2 in both; the CDLL block after p_1 is reversed",
    )


def make_kb3(rng: random.Random) -> SparseHypergraph:
    nc = rng.randint(8, 12)
    nf = rng.randint(8, 16)
    H = SparseHypergraph(n_nodes=nc + 1, n_vertex_labels=1, n_edge_labels=NEL)
    for c in range(1, nc + 1):
        H.add_hyperedge([0, c], label=0)
    tries = 0
    while H.n_edges < nc + nf and tries < 20_000:
        tries += 1
        H.add_hyperedge(rng.sample(range(1, nc + 1), 3), label=rng.randint(1, 2))
    return H


def part2(n_kb: int = 40) -> dict:
    rng = random.Random(20260903 + 313)
    ok = tot = 0
    by = Counter()
    fail = Counter()
    for _ in range(n_kb):
        H = make_kb3(rng)
        toks = SP.parse_plus(canonical_string(H, k=K))
        it = SP.StringToHypergraphPlus(toks, k=K, n_edge_labels=NEL)
        H0 = it.run(track_creators=True)
        doms = [set(m) for _, m, ell in H0.iter_edges() if ell == 0]
        a_rank = set.intersection(*doms).pop()
        es = SP.edge_set(H0)
        for f in [e for e in es if e[0] >= 1]:
            idxs = [i for i, c in enumerate(it.creators) if c == f]
            if not idxs:
                continue
            tok = toks[idxs[0]]
            if isinstance(tok, SP.TokenC):
                wit, kind = toks[: idxs[0]] + toks[idxs[0] + 1 :], "C"
            elif isinstance(tok, TokenV):
                repl = [SP.TokenAPlus(0, lam, (a_rank,)) for lam in tok.new_node_labels]
                wit, kind = toks[: idxs[0]] + repl + toks[idxs[0] + 1 :], f"V(j={tok.j})"
            else:
                continue
            tgt = SP.from_edge_set(H0.n_nodes, es - {f}, n_edge_labels=NEL)
            got = SP.decode_plus(wit, k=K, n_edge_labels=NEL)
            good = (
                got.n_nodes == tgt.n_nodes
                and got.is_connected()
                and canonical_string(got, k=K) == canonical_string(tgt, k=K)
            )
            tot += 1
            ok += int(good)
            by[kind] += 1
            if not good:
                fail[kind] += 1
    return dict(
        n_kb=n_kb,
        ok=ok,
        total=tot,
        fraction=ok / max(tot, 1),
        by_creator=dict(by),
        failures=dict(fail),
    )


if __name__ == "__main__":
    out = dict(part1=part1(), part2=part2())
    print(json.dumps(out, indent=1))
    with open("results_t3b.json", "w") as fh:
        json.dump(out, fh, indent=1)
