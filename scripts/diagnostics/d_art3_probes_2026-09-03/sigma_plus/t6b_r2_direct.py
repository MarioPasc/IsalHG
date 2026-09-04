"""R2, decisive form: forward vs reverse A+ emission against the exact ground truth.

`w*_c` almost never V-creates a *fact* (V tokens sort by edge label, and dom = 0
beats every fact label), so the labelled KB run of `t6_followup.py` yielded no
j = 2 instances. This test therefore drives the comparison directly.

Ground truth `T` for the Prop 4(c) witness at position p (a V token with j fresh
vertices): run w[:p]; then create the j vertices EXACTLY as V does -- appended in
order (ranks r, r+1, ..., r+j-1 carrying labels lam_1..lam_j) and chained into
the CDLL after p_1 -- but attach each to the anchor by a dom edge instead of
adding the fact edge; then run w[p+1:]. `T` is what "H_0 - f with its constants
kept" means on the nose.

Candidates: the forward emission A+[dom;lam_1;a] ... A+[dom;lam_j;a] and the
reverse emission A+[dom;lam_j;a] ... A+[dom;lam_1;a].
"""

from __future__ import annotations

import json
import random
from collections import Counter

import sigma_plus as SP
from t6_followup import exact_key

from isalhg.core.canonical import canonical_fingerprint
from isalhg.core.instructions import TokenV

K, NVL, NEL = 3, 4, 3
ANCHOR_LABEL = 3


def cdll_label_seq(it) -> list[int]:
    """Vertex labels in CDLL order -- what every later pointer walk sees."""
    return [it._H.vertex_label(v) for v in it._cdll.values()]


def id_label_map(H) -> list[int]:
    """Vertex labels by NodeId -- what the rank numbering assigns."""
    return [H.vertex_label(v) for v in range(H.n_nodes)]


def ground_truth(toks, p: int, a_rank: int, seed_label: int):
    """Execute `toks` with token p replaced by V-style vertex creation + dom edges."""
    tok = toks[p]
    it = SP.StringToHypergraphPlus(
        toks, k=K, n_vertex_labels=NVL, n_edge_labels=NEL, seed_label=seed_label
    )
    for t in toks[:p]:
        it._step(t)
    slot = it._pointers.get(1)
    for lam in tok.new_node_labels:  # V's own order and V's own chaining
        v = it._H.add_node(label=lam)
        slot = it._cdll.insert_after(slot, v)
        it._H.add_hyperedge([a_rank, v], label=0)
    for t in toks[p + 1 :]:
        it._step(t)
    return it


def witness(toks, p: int, a_rank: int, seed_label: int, order: str):
    tok = toks[p]
    labs = list(tok.new_node_labels)
    if order == "reverse":
        labs = labs[::-1]
    repl = [SP.TokenAPlus(0, lam, (a_rank,)) for lam in labs]
    it = SP.StringToHypergraphPlus(
        toks[:p] + repl + toks[p + 1 :],
        k=K,
        n_vertex_labels=NVL,
        n_edge_labels=NEL,
        seed_label=seed_label,
    )
    it.run()
    return it


def main() -> None:
    rng = random.Random(20260903 + 601)
    alpha = SP.sigma_hg_alphabet(K, NEL, NVL)
    # sigma_hg_alphabet emits V tokens whose j fresh labels are all equal; add the
    # distinct-label j = 2 tokens, which are exactly the case R2 is about.
    alpha = alpha + [
        TokenV(edge_label=le, i=1, j=2, new_node_labels=(l1, l2))
        for le in range(NEL)
        for l1 in range(NVL)
        for l2 in range(NVL)
        if l1 != l2
    ]
    res = {o: Counter() for o in ("forward", "reverse")}
    n_words = 0
    while n_words < 1500:
        L = rng.randint(6, 24)
        toks = [rng.choice(alpha) for _ in range(L)]
        cands = [
            i
            for i, t in enumerate(toks)
            if isinstance(t, TokenV) and t.j == 2 and len(set(t.new_node_labels)) == 2
        ]
        if not cands:
            continue
        p = rng.choice(cands)
        n_words += 1
        j = toks[p].j
        itT = ground_truth(toks, p, 0, ANCHOR_LABEL)  # anchor = seed = rank 0 (R1)
        T = itT._H
        kT = canonical_fingerprint(T, k=K) if T.n_edges and T.is_connected() else None
        for order in ("forward", "reverse"):
            itG = witness(toks, p, 0, ANCHOR_LABEL, order)
            G = itG._H
            c = res[order]
            c[f"j{j}_total"] += 1
            c[f"j{j}_exact"] += int(exact_key(G) == exact_key(T))
            # the two separable failure modes
            c[f"j{j}_cdll_label_order_ok"] += int(cdll_label_seq(itG) == cdll_label_seq(itT))
            c[f"j{j}_rank_label_map_ok"] += int(id_label_map(G) == id_label_map(T))
            if kT is not None and G.n_edges and G.is_connected():
                c[f"j{j}_iso"] += int(canonical_fingerprint(G, k=K) == kT)
    out = {o: dict(c) for o, c in res.items()}
    print(json.dumps(out, indent=1))
    with open("results_t6b.json", "w") as fh:
        json.dump(out, fh, indent=1)


if __name__ == "__main__":
    main()
