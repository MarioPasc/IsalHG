"""Separability pilot: 4 rigid STS(15) seeds x 4 swap-members (t=2).

Answers: does d_I separate perturbation families of distinct rigid Steiner
seeds, while size/degree distances are identically zero by construction?
"""

import itertools
import statistics
import sys
import time

from rapidfuzz.distance import Levenshtein

from isalhg.core.canonical import canonical_string
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.datasets.registry import get_dataset

sys.path.insert(
    0,
    "/tmp/claude-1000/-home-mpascual-research-code-IsalHG/dcde24e9-927a-4da1-9085-3a2b29666db2/scratchpad",
)
from sts15_symmetry_probe import levi_aut_order, swaps  # noqa: E402

T_SWAPS = 2
MEMBERS = 4


def main() -> None:
    ds = get_dataset("sts_catalog", {})
    sts15 = [it.hypergraph for it in ds if it.extra.get("order") == 15]
    rigid = [i for i, H in enumerate(sts15) if levi_aut_order(H) == 1]
    tri = {i: frozenset(frozenset(m) for _e, m, _l in sts15[i].iter_edges()) for i in rigid}

    # greedy max-min shared-triple separation, 4 seeds
    chosen = [rigid[0]]
    while len(chosen) < 4:
        best, best_val = None, -1
        for c in rigid:
            if c in chosen:
                continue
            val = min(35 - len(tri[c] & tri[s]) for s in chosen)
            if val > best_val:
                best, best_val = c, val
        chosen.append(best)
    seps = [35 - len(tri[a] & tri[b]) for a, b in itertools.combinations(chosen, 2)]
    print(f"seeds {chosen}, pairwise differing triples: {sorted(seps)}", flush=True)

    items: list[tuple[int, SparseHypergraph]] = []
    for fam, idx in enumerate(chosen):
        for j in range(MEMBERS):
            H = swaps(sts15[idx], T_SWAPS, seed=1000 * fam + j)
            items.append((fam, H))

    # degree/size floor by construction
    degs = {tuple(sorted(H.degree(v) for v in range(H.n_nodes))) for _f, H in items}
    sizes = {(H.n_nodes, H.n_edges) for _f, H in items}
    print(f"distinct degree sequences: {len(degs)}, distinct (n,m): {len(sizes)}", flush=True)

    # pairwise non-iso check (pynauty certificates would be better; use w*_c)
    t0 = time.perf_counter()
    ws = []
    for fam, H in items:
        t1 = time.perf_counter()
        w = canonical_string(H, k=3)
        ws.append(w)
        print(f"  fam{fam} |w|={len(w)} t={time.perf_counter() - t1:.1f}s", flush=True)
    print(f"16 encodings in {time.perf_counter() - t0:.0f}s", flush=True)
    print(f"distinct w*_c: {len(set(ws))}/16", flush=True)

    within, between = [], []
    for (i, (fi, _)), (j, (fj, _)) in itertools.combinations(enumerate(items), 2):
        d = Levenshtein.distance(ws[i], ws[j])
        (within if fi == fj else between).append(d)
    print(
        f"within  n={len(within)}: min={min(within)} med={statistics.median(within)} "
        f"max={max(within)}",
        flush=True,
    )
    print(
        f"between n={len(between)}: min={min(between)} med={statistics.median(between)} "
        f"max={max(between)}",
        flush=True,
    )

    # quick PAM ARI at k=4
    import numpy as np
    from kmedoids import fasterpam
    from sklearn.metrics import adjusted_rand_score

    N = len(items)
    D = np.zeros((N, N))
    for (i, _), (j, _) in itertools.combinations(enumerate(items), 2):
        D[i, j] = D[j, i] = Levenshtein.distance(ws[i], ws[j])
    labels = [f for f, _ in items]
    aris = []
    for rs in range(10):
        km = fasterpam(D, 4, random_state=rs)
        aris.append(adjusted_rand_score(labels, km.labels))
    print(f"PAM ARI over 10 restarts: min={min(aris):.3f} max={max(aris):.3f}", flush=True)


if __name__ == "__main__":
    main()
