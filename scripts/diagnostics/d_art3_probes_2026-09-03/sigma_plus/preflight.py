"""Preflight: edge-label support in canonical_string, anchored-KB timing, seed identity."""

from __future__ import annotations

import random
import time

import sigma_plus as SP

from isalhg.core.canonical import canonical_string
from isalhg.core.sparse_hypergraph import SparseHypergraph, permute

K = 3


def make_kb(rng: random.Random, n_const: int, n_facts: int, r: int = 2):
    """Anchored KB (encoding E1-top): vertex 0 = anchor, dom = edge label 0,
    fact labels 1..r, fact arity 2..3. Trivial vertex vocabulary."""
    H = SparseHypergraph(n_nodes=n_const + 1, n_vertex_labels=1, n_edge_labels=r + 1)
    for c in range(1, n_const + 1):
        H.add_hyperedge([0, c], label=0)
    tries = 0
    while H.n_edges < n_const + n_facts and tries < 10_000:
        tries += 1
        a = rng.choice((2, 3))
        S = rng.sample(range(1, n_const + 1), a)
        H.add_hyperedge(S, label=rng.randint(1, r))
    return H


def main() -> None:
    rng = random.Random(20260903)
    # 1. does canonical_string honour edge labels?
    H1 = SparseHypergraph(3, [(0, 1), (1, 2)], n_edge_labels=3)
    H2 = SparseHypergraph(3, [(0, 1), (1, 2)], n_edge_labels=3, edge_labels=[0, 1])
    w1, w2 = canonical_string(H1, k=K), canonical_string(H2, k=K)
    print("edge-label sensitivity:", w1 != w2, "|", w1, "|", w2)
    # does declared vocabulary size alone change the string?
    H3 = SparseHypergraph(3, [(0, 1), (1, 2)], n_edge_labels=1)
    print("vocab-size invariance:", canonical_string(H3, k=K) == w1)
    # iso-invariance with labels
    H2p = permute(H2, [2, 0, 1])
    print("label iso-invariance:", canonical_string(H2p, k=K) == w2)

    # 2. anchored-KB canonicalization timing + seed identity + n/m
    times = []
    seed_is_anchor = 0
    for _ in range(8):
        nc = rng.randint(8, 12)
        nf = rng.randint(8, 16)
        H = make_kb(rng, nc, nf)
        t0 = time.perf_counter()
        w = canonical_string(H, k=K)
        times.append(time.perf_counter() - t0)
        H0 = SP.decode_plus(SP.parse_plus(w), k=K, n_edge_labels=3)
        # anchor of H0 = the vertex in every label-0 edge
        doms = [m for _, m, ell in H0.iter_edges() if ell == 0]
        anchor = set.intersection(*[set(d) for d in doms])
        seed_is_anchor += int(anchor == {0})
        print(
            f"  nc={nc} nf={nf} n={H.n_nodes} m={H.n_edges} |w|={len(SP.parse_plus(w))} "
            f"t={times[-1]:.3f}s anchor_rank={sorted(anchor)} decoded n={H0.n_nodes} m={H0.n_edges}"
        )
    print(
        f"canon: max={max(times):.3f}s mean={sum(times) / len(times):.3f}s "
        f"seed_is_anchor={seed_is_anchor}/8"
    )


if __name__ == "__main__":
    main()
