"""R2 decisive, j = 2, distinct labels -- structural comparison only (no
canonicalization, which is what made `t6b` slow on random 4-label words).

The three properties that decide everything downstream:
  exact            : final hypergraph identical to the ground truth (NodeIds,
                     per-id vertex labels, labelled edge set)
  cdll_label_order : the CDLL label sequence matches -- what every later pointer
                     walk sees, hence whether later edges land on the right
                     vertices
  rank_label_map   : NodeId -> label matches -- whether the rank numbering agrees
"""

from __future__ import annotations

import json
import random
from collections import Counter

import sigma_plus as SP
from t6_followup import exact_key
from t6b_r2_direct import (
    ANCHOR_LABEL,
    NEL,
    NVL,
    K,
    cdll_label_seq,
    ground_truth,
    id_label_map,
    witness,
)

from isalhg.core.instructions import TokenV


def main(n_words: int = 2000) -> None:
    rng = random.Random(20260903 + 701)
    alpha = SP.sigma_hg_alphabet(K, NEL, NVL) + [
        TokenV(edge_label=le, i=1, j=2, new_node_labels=(l1, l2))
        for le in range(NEL)
        for l1 in range(NVL)
        for l2 in range(NVL)
        if l1 != l2
    ]
    res = {o: Counter() for o in ("forward", "reverse")}
    done = 0
    while done < n_words:
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
        done += 1
        itT = ground_truth(toks, p, 0, ANCHOR_LABEL)
        for order in ("forward", "reverse"):
            itG = witness(toks, p, 0, ANCHOR_LABEL, order)
            c = res[order]
            c["total"] += 1
            c["exact"] += int(exact_key(itG._H) == exact_key(itT._H))
            c["cdll_label_order_ok"] += int(cdll_label_seq(itG) == cdll_label_seq(itT))
            c["rank_label_map_ok"] += int(id_label_map(itG._H) == id_label_map(itT._H))
    out = {o: dict(c) for o, c in res.items()}
    print(json.dumps(out, indent=1))
    with open("results_t6c.json", "w") as fh:
        json.dump(out, fh, indent=1)


if __name__ == "__main__":
    main()
