"""Worked example: one real WD50K entity KB under the three encodings, before and after one edit."""

from __future__ import annotations

import json
import random
import sys

sys.path.insert(0, "/home/mpascual/research/code/IsalHG")

from experiments.tkde import corpora  # noqa: E402
from experiments.tkde.budget import symbol_distance  # noqa: E402
from isalhg.core.canonical import canonical_string  # noqa: E402
from isalhg.core.fact_word import encode_fact_word  # noqa: E402
from isalhg.core.sparse_hypergraph import SparseHypergraph, permute  # noqa: E402
from isalhg.iso_backends.canonical_order import (  # noqa: E402
    canonical_ranks,
    nauty_certificate_bytes,
    nauty_certificate_rows,
)

ROOT = "/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE"
vocab = json.load(open(f"{ROOT}/corpora/wd50k66/vocab.json"))
P = vocab["pred_names"]
coll = corpora.load_collection("wd50k66", ROOT)
rec = next(r for r in coll.records if r.kb_id == "Q1002100")
H = rec.to_hypergraph(n_types=coll.n_types, n_preds=coll.n_preds)


def show_kb(title: str, H: SparseHypergraph, ids: list[str]) -> None:
    print(f"--- {title}: n={H.n_nodes} constants, m={H.n_edges} facts")
    for e, members, label in H.iter_edges():
        print(f"    {P[label]}({', '.join(ids[v] for v in sorted(members))})")


def fact_word(H: SparseHypergraph):
    return encode_fact_word(H, canonical_ranks(H))


def fmt_word(w) -> str:
    out = []
    for t in w:
        if t[0] == "T":
            out.append("T")
        else:
            out.append(f"F[{P[t[1]]};{','.join(map(str, t[2]))}]")
    return " ".join(out)


def pointer_tokens(H: SparseHypergraph) -> list[str]:
    s = canonical_string(H)
    return s.split(";")


def report(name: str, H: SparseHypergraph, ids: list[str]):
    show_kb(name, H, ids)
    ranks = canonical_ranks(H)
    print(
        "    canonical rank of each constant (from nauty):",
        {ids[v]: r for v, r in enumerate(ranks)},
    )
    w = fact_word(H)
    print(f"    fact_rank word ({len(w)} tokens): {fmt_word(w)}")
    cert = nauty_certificate_bytes(H)
    print(f"    nauty certificate: {len(cert)} bytes, hex {cert.hex()[:48]}...")
    rows = nauty_certificate_rows(H)
    print(f"    nauty certificate as adjacency rows: {len(rows)} rows, e.g. {rows[:3]}")
    p = pointer_tokens(H)
    print(f"    pointer word w*_c ({len(p)} tokens): {' '.join(p)}")
    return w, cert, rows, p


ids = list(rec.constant_ids)
w0, c0, r0, p0 = report("ORIGINAL  Q1002100 (a film)", H, ids)

# 1. A random renaming of the constants: every encoding must be unchanged.
rng = random.Random(7)
sigma = list(range(H.n_nodes))
rng.shuffle(sigma)
H_ren = permute(H, sigma)
ids_ren = [None] * H.n_nodes
for v, s in enumerate(sigma):
    ids_ren[s] = ids[v]
print("\n=== 1. RENAME the constants (permutation", sigma, ")")
w1, c1, r1, p1 = report("RENAMED", H_ren, ids_ren)
print(
    "    fact word equal:",
    w1 == w0,
    "| certificate equal:",
    c1 == c0,
    "| pointer word equal:",
    p1 == p0,
)

# 2. Insert ONE fact over existing constants: P161 (cast member) also links the film to Q89284.
edges = [members for _, members, _ in H.iter_edges()]
labels = [label for _, _, label in H.iter_edges()]
edges.append(frozenset({0, 3}))
labels.append(P.index("P161"))
H_ins = SparseHypergraph(
    H.n_nodes,
    edges,
    n_vertex_labels=H.n_vertex_labels,
    n_edge_labels=H.n_edge_labels,
    vertex_labels=[H.vertex_label(v) for v in range(H.n_nodes)],
    edge_labels=labels,
)
print("\n=== 2. INSERT one fact P161(Q1002100, Q652) over existing constants")
w2, c2, r2, p2 = report("EDITED", H_ins, ids)
print(f"    Levenshtein  fact_rank : {symbol_distance(w0, w2)} tokens of {len(w0)}")
print(f"    Levenshtein  nauty cert: {symbol_distance(c0, c2)} bytes  of {len(c0)}")
print(f"    Levenshtein  cert rows : {symbol_distance(r0, r2)} rows   of {len(r0)}")
print(f"    Levenshtein  pointer   : {symbol_distance(p0, p2)} tokens of {len(p0)}")

# 3. Insert a fact that ADDS a constant (the constant set changes).
edges3 = list(edges[:-1]) + [frozenset({0, 6})]
labels3 = list(labels[:-1]) + [P.index("P161")]
H_new = SparseHypergraph(
    H.n_nodes + 1,
    edges3,
    n_vertex_labels=H.n_vertex_labels,
    n_edge_labels=H.n_edge_labels,
    vertex_labels=[0] * (H.n_nodes + 1),
    edge_labels=labels3,
)
print("\n=== 3. INSERT one fact P161(Q1002100, NEW) that adds a constant")
w3, c3, r3, p3 = report("EDITED+CONSTANT", H_new, ids + ["NEW"])
print(f"    Levenshtein  fact_rank : {symbol_distance(w0, w3)} tokens of {len(w0)}")
print(f"    Levenshtein  nauty cert: {symbol_distance(c0, c3)} bytes  of {len(c0)}")
print(f"    Levenshtein  cert rows : {symbol_distance(r0, r3)} rows   of {len(r0)}")
print(f"    Levenshtein  pointer   : {symbol_distance(p0, p3)} tokens of {len(p0)}")
