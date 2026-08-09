"""Pilot 3: cell sweep — swap-sensitivity + planted-family separability vs (n,m).

Irregular fixed-degree substrate at k=3. Per cell:
  - single-swap sensitivity of d_I (token-level, repo distance)
  - 4 families x 4 members at t=2 swaps; D matrices from the repo's registered
    distances (isalhg, WL, NetLSD, degree-seq) + size floor check
  - within/between medians + PAM ARI per representation
"""

import itertools
import random
import statistics
import sys
import time

import numpy as np
from kmedoids import fasterpam
from sklearn.metrics import adjusted_rand_score

from isalhg.datasets.synthetic._random_hg import random_connected_hypergraph
from isalhg.metric_space.registry import get_distance

sys.path.insert(
    0,
    "/tmp/claude-1000/-home-mpascual-research-code-IsalHG/dcde24e9-927a-4da1-9085-3a2b29666db2/scratchpad",
)
from sts15_symmetry_probe import swaps  # noqa: E402

CELLS = [(9, 12), (10, 15), (12, 20), (15, 35)]
REPS = ["isalhg_levenshtein", "hypergraph_wl_l1", "netlsd_l2", "degree_seq_l1"]
N_FAM, MEMBERS, T = 4, 4, 2


def wb_stats(D, labels):
    within, between = [], []
    for i, j in itertools.combinations(range(len(labels)), 2):
        (within if labels[i] == labels[j] else between).append(D[i, j])
    return statistics.median(within), statistics.median(between)


def main() -> None:
    for n, m in CELLS:
        base, _ = random_connected_hypergraph(
            n_nodes=n, n_edges=m, arity_range=(3, 3), rng=random.Random(7)
        )
        degseq = sorted(base.degree(v) for v in range(n))
        d_iso = get_distance("isalhg_levenshtein")
        # single-swap vs single-Qin-edit sensitivity (token-level d_I)
        t0 = time.perf_counter()
        sens = [d_iso.pairwise(base, swaps(base, 1, seed=100 + i)) for i in range(10)]
        from isalhg.core.sparse_hypergraph import random_connected_edit

        qins = []
        for i in range(10):
            Hq, _op = random_connected_edit(base, random.Random(200 + i), max_arity=3)
            qins.append(d_iso.pairwise(base, Hq))
        print(f"[{n},{m}] degseq={degseq}", flush=True)
        print(
            f"[{n},{m}] swap1 sensitivity: min={min(sens):.0f} "
            f"med={statistics.median(sens):.0f} max={max(sens):.0f} | "
            f"qin1: min={min(qins):.0f} med={statistics.median(qins):.0f} "
            f"max={max(qins):.0f} ({time.perf_counter() - t0:.0f}s)",
            flush=True,
        )
        # planted families
        sep = 10 * m
        seeds = [swaps(base, sep, seed=777 + f) for f in range(N_FAM)]
        items, labels = [], []
        for f in range(N_FAM):
            for j in range(MEMBERS):
                items.append(swaps(seeds[f], T, seed=1000 * f + j))
                labels.append(f)
        assert len({tuple(sorted(H.degree(v) for v in range(n))) for H in items}) == 1
        assert len({(H.n_nodes, H.n_edges) for H in items}) == 1
        for rep in REPS:
            t0 = time.perf_counter()
            D = np.asarray(get_distance(rep).matrix(items), dtype=float)
            wmed, bmed = wb_stats(D, labels)
            aris = [
                adjusted_rand_score(labels, fasterpam(D, N_FAM, random_state=rs).labels)
                for rs in range(10)
            ]
            print(
                f"[{n},{m}] {rep:<22} within_med={wmed:.3g} between_med={bmed:.3g} "
                f"ratio={bmed / wmed if wmed else float('inf'):.2f} "
                f"ARI[{min(aris):.2f},{max(aris):.2f}] "
                f"({time.perf_counter() - t0:.0f}s)",
                flush=True,
            )


if __name__ == "__main__":
    main()
