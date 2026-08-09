"""Separability pilot 2: random substrates at fixed (n,m,k)=(15,35,3).

Arm R (regular):   seeds = 300-swap randomizations of rigid STS(15) idx22
                   (7-regular preserved) -> near-symmetry-free but degree-uniform.
Arm I (irregular): base = random connected (15,35,3); seeds = 300-swap
                   randomizations (same irregular degree sequence for ALL items).

Members: t=2 swaps per member, 4 families x 4 members per arm.
Reports within/between d_I, PAM ARI, naive-floor checks, encode wall-clocks.
"""

import itertools
import random
import statistics
import sys
import time

import numpy as np
from kmedoids import fasterpam
from rapidfuzz.distance import Levenshtein
from sklearn.metrics import adjusted_rand_score

from isalhg.core.canonical import canonical_string
from isalhg.datasets.registry import get_dataset
from isalhg.datasets.synthetic._random_hg import random_connected_hypergraph

sys.path.insert(
    0,
    "/tmp/claude-1000/-home-mpascual-research-code-IsalHG/dcde24e9-927a-4da1-9085-3a2b29666db2/scratchpad",
)
from sts15_symmetry_probe import swaps  # noqa: E402


def run_arm(name, base, n_fam=4, members=4, t=2, sep_swaps=300):
    seeds = [swaps(base, sep_swaps, seed=777 + f) for f in range(n_fam)]
    items = [
        (f, swaps(seeds[f], t, seed=1000 * f + j)) for f in range(n_fam) for j in range(members)
    ]
    degs = {tuple(sorted(H.degree(v) for v in range(H.n_nodes))) for _f, H in items}
    sizes = {(H.n_nodes, H.n_edges) for _f, H in items}
    edge_sets = [frozenset(frozenset(m) for _e, m, _l in H.iter_edges()) for _f, H in items]
    seed_shared = [
        len(a & b)
        for a, b in itertools.combinations(
            [frozenset(frozenset(m) for _e, m, _l in s.iter_edges()) for s in seeds], 2
        )
    ]
    print(
        f"[{name}] deg-seqs={len(degs)} (n,m)-cells={len(sizes)} "
        f"seed shared-edges: {sorted(seed_shared)}",
        flush=True,
    )
    t0 = time.perf_counter()
    ws = [canonical_string(H, k=3) for _f, H in items]
    dt = time.perf_counter() - t0
    print(
        f"[{name}] {len(items)} encodings in {dt:.1f}s "
        f"(mean {dt / len(items):.2f}s) |w| range "
        f"{min(map(len, ws))}-{max(map(len, ws))} distinct {len(set(ws))}/16",
        flush=True,
    )
    within, between = [], []
    N = len(items)
    D = np.zeros((N, N))
    for (i, (fi, _)), (j, (fj, _)) in itertools.combinations(enumerate(items), 2):
        d = Levenshtein.distance(ws[i], ws[j])
        D[i, j] = D[j, i] = d
        (within if fi == fj else between).append(d)
    print(
        f"[{name}] within  min={min(within)} med={statistics.median(within)} max={max(within)}",
        flush=True,
    )
    print(
        f"[{name}] between min={min(between)} med={statistics.median(between)} max={max(between)}",
        flush=True,
    )
    labels = [f for f, _ in items]
    aris = [
        adjusted_rand_score(labels, fasterpam(D, 4, random_state=rs).labels) for rs in range(10)
    ]
    print(f"[{name}] PAM ARI: min={min(aris):.3f} max={max(aris):.3f}", flush=True)
    print(
        f"[{name}] edge-set overlap within vs between: "
        f"within med={statistics.median([len(edge_sets[i] & edge_sets[j]) for (i, (fi, _)), (j, (fj, _)) in itertools.combinations(enumerate(items), 2) if fi == fj])} "
        f"between med={statistics.median([len(edge_sets[i] & edge_sets[j]) for (i, (fi, _)), (j, (fj, _)) in itertools.combinations(enumerate(items), 2) if fi != fj])}",
        flush=True,
    )


def main() -> None:
    ds = get_dataset("sts_catalog", {})
    sts15 = [it.hypergraph for it in ds if it.extra.get("order") == 15]
    run_arm("R/regular", sts15[22])
    H0, _att = random_connected_hypergraph(
        n_nodes=15, n_edges=35, arity_range=(3, 3), rng=random.Random(7)
    )
    degseq = sorted(H0.degree(v) for v in range(H0.n_nodes))
    print(f"[I] base degree sequence: {degseq}", flush=True)
    run_arm("I/irregular", H0)


if __name__ == "__main__":
    main()
