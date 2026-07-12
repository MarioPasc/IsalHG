"""Head-to-head wall-clock: IsalHG canonical (``w*_c``) vs Levi + nauty / bliss.

Spans an easy -> hard difficulty spectrum so the comparison is neither cherry-
picked to IsalHG's worst case (the vertex-transitive designs, where the
tie-complete search hits its ``(j!)^E`` branching ceiling) nor to its best
(tiny sparse instances). Reports ``fingerprint(H)`` best-of-N milliseconds for
each backend.

Tiers
-----
easy   : small sparse random hypergraphs (n<=10, arity<=3)
medium : larger sparse random hypergraphs (n in {20,35,50}, arity<=3)
hard   : the vertex-transitive design fixtures (Fano, STS(9), cyclic STS(13),
         GQ(2,2) doily) -- IsalHG's structural worst case.

Run: ``python scripts/bench_canonical_vs_competitors.py [--reps N] [--seed S]``
"""

from __future__ import annotations

import argparse
import random
import time
from collections.abc import Callable

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.datasets.synthetic.designs import cyclic_sts_13, fano_plane, gq_2_2_doily, sts_9
from isalhg.iso_backends.registry import get_backend

CANONICAL = "isalhg_canonical"
COMPETITORS = ("pynauty_levi", "bliss_levi", "traces_levi")


def _random_hypergraph(rng: random.Random, n: int, max_arity: int) -> SparseHypergraph:
    perm = list(range(n))
    rng.shuffle(perm)
    edges = [frozenset({perm[i], perm[rng.randrange(i)]}) for i in range(1, n)]
    extra = rng.randint(n // 3, n)
    for _ in range(extra):
        arity = rng.randint(2, min(max_arity, n))
        edges.append(frozenset(rng.sample(range(n), arity)))
    return SparseHypergraph(n_nodes=n, hyperedges=list(dict.fromkeys(edges)))


def _best_ms(fn: Callable[[], object], reps: int, warmup: int = 2) -> float:
    for _ in range(warmup):
        fn()
    best = float("inf")
    for _ in range(reps):
        start = time.perf_counter()
        fn()
        best = min(best, time.perf_counter() - start)
    return best * 1e3


def _load_backends() -> dict[str, object]:
    backends: dict[str, object] = {"isalhg_canonical": get_backend(CANONICAL)}
    for name in COMPETITORS:
        try:
            b = get_backend(name)
            b.fingerprint(fano_plane())  # trigger binary discovery
            backends[name] = b
        except Exception as exc:  # noqa: BLE001 - report and skip unavailable backends
            print(f"# skipping {name}: {type(exc).__name__}: {str(exc)[:70]}")
    return backends


def _row(label: str, H: SparseHypergraph, backends: dict[str, object], reps: int) -> None:
    cells = []
    for backend in backends.values():
        ms = _best_ms(lambda b=backend, H=H: b.fingerprint(H), reps)
        cells.append(f"{ms:>11.3f}")
    print(f"{label:<26}{''.join(cells)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reps", type=int, default=7)
    parser.add_argument("--seed", type=int, default=20260712)
    args = parser.parse_args()

    backends = _load_backends()
    header = f"{'instance':<26}" + "".join(f"{n[:11]:>11}" for n in backends)
    print(header)
    print("-" * len(header))

    rng = random.Random(args.seed)

    print("# --- easy: small sparse random (median of 5 instances) ---")
    for n in (6, 8, 10):
        # Report the median instance by IsalHG time to avoid a lucky/unlucky draw.
        instances = []
        while len(instances) < 5:
            H = _random_hypergraph(rng, n, 3)
            if H.is_connected():
                instances.append(H)
        # pick the median-by-edge-count instance for a representative single row
        instances.sort(key=lambda H: H.n_edges)
        _row(f"easy n={n} m~{instances[2].n_edges}", instances[2], backends, args.reps)

    print("# --- medium: larger sparse random ---")
    for n in (20, 35, 50):
        H = None
        while H is None or not H.is_connected():
            H = _random_hypergraph(rng, n, 3)
        _row(f"medium n={n} m={H.n_edges}", H, backends, args.reps)

    print("# --- hard: vertex-transitive designs (IsalHG worst case) ---")
    for label, H in (
        ("hard fano STS(7)", fano_plane()),
        ("hard STS(9)", sts_9()),
        ("hard cyclic STS(13)", cyclic_sts_13((0, 1, 3))),
        ("hard GQ(2,2) doily", gq_2_2_doily()),
    ):
        _row(label, H, backends, args.reps)


if __name__ == "__main__":
    main()
