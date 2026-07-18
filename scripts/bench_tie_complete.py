"""Wall-clock of the tie-complete canonical string (``greedy_min_complete``).

Compares the C++ tie-complete encoder against the C++ single-branch greedy
default and against the pure-Python tie-complete reference, on the four design
fixtures and a random corpus. Reports whether the greedy string coincides with
the canonical one on each design (the automorphism-coherent-tie regime).

Run: ``python scripts/bench_tie_complete.py [--python-reference]``
"""

from __future__ import annotations

import argparse
import random
import statistics
import time
from collections.abc import Callable

from isalhg.core.canonical import canonical_string, required_k
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.datasets.synthetic.designs import cyclic_triple_orbit_13, fano_plane, gq_2_2_doily, sts_9

GREEDY = "greedy_min_nbrdeg"
COMPLETE = "canonical"


def _random_hypergraph(rng: random.Random, n: int, max_arity: int = 4) -> SparseHypergraph:
    perm = list(range(n))
    rng.shuffle(perm)
    edges = [frozenset({perm[i], perm[rng.randrange(i)]}) for i in range(1, n)]
    for _ in range(rng.randrange(4)):
        arity = rng.randint(2, min(max_arity, n))
        edges.append(frozenset(rng.sample(range(n), arity)))
    return SparseHypergraph(n_nodes=n, hyperedges=list(dict.fromkeys(edges)))


def _time(fn: Callable[[], str]) -> tuple[float, str]:
    start = time.perf_counter()
    value = fn()
    return time.perf_counter() - start, value


def _bench_designs(with_python: bool, python_reference_max_n: int) -> None:
    designs = [
        ("fano", fano_plane()),
        ("sts9", sts_9()),
        ("c13_013", cyclic_triple_orbit_13((0, 1, 3))),
        ("gq22_doily", gq_2_2_doily()),
    ]
    header = f"{'design':<12}{'greedy(C++)':>14}{'complete(C++)':>16}{'ratio':>9}{'w*_g==w*_c':>13}"
    if with_python:
        header += f"{'complete(py)':>16}{'speedup':>10}"
    print(header)
    print("-" * len(header))
    for name, H in designs:
        k = required_k(H)
        t_greedy, w_greedy = _time(lambda H=H, k=k: canonical_string(H, k=k, algorithm=GREEDY))
        t_complete, w_complete = _time(
            lambda H=H, k=k: canonical_string(H, k=k, algorithm=COMPLETE)
        )
        row = (
            f"{name:<12}{t_greedy * 1e3:>12.2f}ms{t_complete * 1e3:>14.2f}ms"
            f"{t_complete / t_greedy:>8.1f}x{str(w_greedy == w_complete):>13}"
        )
        if with_python and H.n_nodes <= python_reference_max_n:
            t_py, w_py = _time(
                lambda H=H, k=k: canonical_string(H, k=k, algorithm=COMPLETE, backend="python")
            )
            assert w_py == w_complete, f"{name}: C++ and Python tie-complete disagree"
            row += f"{t_py * 1e3:>14.1f}ms{t_py / t_complete:>9.0f}x"
        elif with_python:
            row += f"{'skipped':>16}{'-':>10}"
        print(row, flush=True)


def _bench_random_corpus(seed: int) -> None:
    rng = random.Random(seed)
    print(f"\nrandom corpus (seed={seed}), 30 connected instances per n")
    print(f"{'n':<5}{'greedy median':>16}{'complete median':>18}{'complete max':>16}")
    print("-" * 55)
    for n in range(4, 13):
        greedy_times: list[float] = []
        complete_times: list[float] = []
        drawn = 0
        while drawn < 30:
            H = _random_hypergraph(rng, n)
            if not H.is_connected():
                continue
            drawn += 1
            k = required_k(H)
            greedy_times.append(
                _time(lambda H=H, k=k: canonical_string(H, k=k, algorithm=GREEDY))[0]
            )
            complete_times.append(
                _time(lambda H=H, k=k: canonical_string(H, k=k, algorithm=COMPLETE))[0]
            )
        print(
            f"{n:<5}{statistics.median(greedy_times) * 1e3:>14.2f}ms"
            f"{statistics.median(complete_times) * 1e3:>16.2f}ms"
            f"{max(complete_times) * 1e3:>14.2f}ms",
            flush=True,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--python-reference",
        action="store_true",
        help="also time the pure-Python tie-complete reference (minutes on STS(9)+)",
    )
    parser.add_argument(
        "--python-reference-max-n",
        type=int,
        default=9,
        help="skip the Python reference on designs larger than this (it does not terminate)",
    )
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    _bench_designs(args.python_reference, args.python_reference_max_n)
    _bench_random_corpus(args.seed)


if __name__ == "__main__":
    main()
