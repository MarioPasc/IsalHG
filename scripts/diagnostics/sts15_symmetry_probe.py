"""STS(15) symmetry ranking + w*_c feasibility probe (T-M4b diagnostics).

1. |Aut| of all 80 STS(15) via pynauty on the bipartition-coloured Levi graph.
2. Pairwise shared-triple separation of the 80; greedy max-min subset of 12.
3. Degree/size-preserving incidence-swap perturbations (prototype of the
   generator edit for the size-controlled corpus).
4. Subprocess-timed canonical_string (k=3) on selected pristine/perturbed
   instances, 900 s timeout each.

Writes JSON candidates + prints everything; no repo files touched.
"""

import json
import os
import random
import subprocess
import sys
import time

import pynauty

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.datasets.registry import get_dataset

SCRATCH = os.path.dirname(os.path.abspath(__file__))  # probe artifacts land beside the script
TIMEOUT = 900


def levi_aut_order(H: SparseHypergraph) -> float:
    n, m = H.n_nodes, H.n_edges
    adj: dict[int, list[int]] = {v: [] for v in range(n + m)}
    for e_id, members, _label in H.iter_edges():
        for v in members:
            adj[v].append(n + e_id)
    g = pynauty.Graph(
        n + m,
        directed=False,
        adjacency_dict=adj,
        vertex_coloring=[set(range(n)), set(range(n, n + m))],
    )
    _gens, sz1, sz2, _orb, _norb = pynauty.autgrp(g)
    return sz1 * (10**sz2)


def swap_once(H: SparseHypergraph, rng: random.Random) -> SparseHypergraph | None:
    """One degree/size-preserving incidence swap; None if no valid move found."""
    edges = [set(members) for _eid, members, _l in H.iter_edges()]
    edge_set = {frozenset(e) for e in edges}
    m = len(edges)
    for _ in range(200):
        i, j = rng.randrange(m), rng.randrange(m)
        if i == j:
            continue
        e1, e2 = edges[i], edges[j]
        only1, only2 = list(e1 - e2), list(e2 - e1)
        if not only1 or not only2:
            continue
        v1, v2 = rng.choice(only1), rng.choice(only2)
        new1 = frozenset((e1 - {v1}) | {v2})
        new2 = frozenset((e2 - {v2}) | {v1})
        if new1 == new2 or new1 in edge_set or new2 in edge_set:
            continue
        new_edges = list(edges)
        new_edges[i], new_edges[j] = set(new1), set(new2)
        H2 = SparseHypergraph(H.n_nodes, [frozenset(e) for e in new_edges])
        if H2.n_edges != m or not H2.is_connected():
            continue
        return H2
    return None


def swaps(H: SparseHypergraph, t: int, seed: int) -> SparseHypergraph:
    rng = random.Random(seed)
    cur = H
    for _ in range(t):
        nxt = swap_once(cur, rng)
        if nxt is None:
            raise RuntimeError("no valid swap found")
        cur = nxt
    return cur


def dump(H: SparseHypergraph, label: str) -> str:
    path = os.path.join(SCRATCH, f"cand_{label}.json")
    with open(path, "w") as f:
        json.dump(
            {
                "label": label,
                "n": H.n_nodes,
                "edges": [sorted(mem) for _e, mem, _l in H.iter_edges()],
            },
            f,
        )
    return path


def main() -> None:
    ds = get_dataset("sts_catalog", {})
    sts15 = [it for it in ds if it.extra.get("order") == 15]
    print(f"loaded {len(sts15)} STS(15) instances", flush=True)

    # --- 1. |Aut| ranking -------------------------------------------------
    t0 = time.perf_counter()
    aut = [(int(levi_aut_order(it.hypergraph)), idx) for idx, it in enumerate(sts15)]
    print(f"|Aut| for all 80 in {time.perf_counter() - t0:.1f}s", flush=True)
    from collections import Counter

    dist = Counter(a for a, _ in aut)
    print("|Aut| distribution (order: count):", dict(sorted(dist.items())), flush=True)
    aut_sorted = sorted(aut)
    print("5 most rigid  :", aut_sorted[:5], flush=True)
    print("5 most symmetric:", aut_sorted[-5:], flush=True)
    print("index0 |Aut| =", next(a for a, i in aut if i == 0), flush=True)

    # --- 2. pairwise shared triples --------------------------------------
    tri = [frozenset(frozenset(mem) for _e, mem, _l in it.hypergraph.iter_edges()) for it in sts15]
    import statistics

    shared = []
    for i in range(80):
        for j in range(i + 1, 80):
            shared.append(len(tri[i] & tri[j]))
    print(
        f"shared triples over 3160 pairs: min={min(shared)} "
        f"median={statistics.median(shared)} max={max(shared)}",
        flush=True,
    )

    # greedy max-min separation subset of 12 among rigid instances
    rigid = [i for a, i in aut_sorted if a == aut_sorted[0][0]]
    print(f"instances at minimal |Aut|={aut_sorted[0][0]}: {len(rigid)}", flush=True)

    # --- 3+4. timing candidates ------------------------------------------
    idx_rigid = aut_sorted[0][1]
    idx_rigid2 = aut_sorted[1][1]
    idx_median = aut_sorted[40][1]
    H0 = sts15[0].hypergraph
    Hr = sts15[idx_rigid].hypergraph
    Hm = sts15[idx_median].hypergraph
    cands = [
        dump(H0, "sts15_idx0_pristine"),
        dump(Hr, f"sts15_idx{idx_rigid}_rigid_pristine"),
        dump(sts15[idx_rigid2].hypergraph, f"sts15_idx{idx_rigid2}_rigid2_pristine"),
        dump(Hm, f"sts15_idx{idx_median}_median_pristine"),
        dump(swaps(H0, 1, 42), "sts15_idx0_swap1"),
        dump(swaps(Hr, 1, 42), f"sts15_idx{idx_rigid}_rigid_swap1"),
        dump(swaps(Hr, 2, 42), f"sts15_idx{idx_rigid}_rigid_swap2"),
        dump(swaps(Hr, 200, 42), f"sts15_idx{idx_rigid}_rigid_swap200"),
    ]
    py = sys.executable
    timer = os.path.join(SCRATCH, "time_wstar.py")
    for path in cands:
        label = os.path.basename(path)[5:-5]
        t0 = time.perf_counter()
        try:
            r = subprocess.run(
                [py, timer, path], capture_output=True, text=True, timeout=TIMEOUT, env=os.environ
            )
            out = (r.stdout + r.stderr).strip()
            print(out if out else f"TIMING {label} EXIT={r.returncode} (no output)", flush=True)
        except subprocess.TimeoutExpired:
            print(
                f"TIMING {label} TIMEOUT>{TIMEOUT}s (wall {time.perf_counter() - t0:.0f}s)",
                flush=True,
            )


if __name__ == "__main__":
    main()
