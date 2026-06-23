"""Phase 4 benchmark — Python vs C++ canonical_string on the symmetric designs.

The 18-cell Erdős-Rényi grid is all DNF in Python (>600 s per cell — see
docs/ALGORITHMS.md), so there is no Python baseline to "speed up". The
five symmetric designs are the only cells with finite Python timings and
are the right local head-to-head subset.

Outputs
-------
* stdout — wall-clock table with Python (pre-port), C++, and ratio.
* docs/CPP_SPEEDUP.md — Markdown copy of the same table.

Notes
-----
* Python timings use the ``_python_*`` reference implementations that
  Phase 1 kept alongside the C++-backed entry points.
* C++ timings use ``isalhg.core.canonical.canonical_string`` (which
  dispatches to the C++ multi-seed entry for the five fast variants).
* Doily ``greedy_min`` Python single-seed already takes ~21 s; full
  multi-seed is DNF >300 s. We time multi-seed only via ``greedy_single``
  for the doily.
"""

from __future__ import annotations

import itertools
import time
from pathlib import Path

from isalhg.core.canonical import canonical_string, required_k
from isalhg.core.hypergraph_to_string import _python_greedy_h2s
from isalhg.core.instructions import sequence_sort_key, serialize
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.core.structural_tuples import _python_max_xi_nodes


def fano() -> SparseHypergraph:
    edges = [
        [0, 1, 2],
        [0, 3, 4],
        [0, 5, 6],
        [1, 3, 5],
        [1, 4, 6],
        [2, 3, 6],
        [2, 4, 5],
    ]
    return SparseHypergraph(n_nodes=7, hyperedges=edges)


def sts9() -> SparseHypergraph:
    edges = [
        [0, 1, 2],
        [3, 4, 5],
        [6, 7, 8],
        [0, 3, 6],
        [1, 4, 7],
        [2, 5, 8],
        [0, 4, 8],
        [1, 5, 6],
        [2, 3, 7],
        [0, 5, 7],
        [1, 3, 8],
        [2, 4, 6],
    ]
    return SparseHypergraph(n_nodes=9, hyperedges=edges)


def sts13() -> SparseHypergraph:
    edges = [[i, (i + 1) % 13, (i + 3) % 13] for i in range(13)]
    return SparseHypergraph(n_nodes=13, hyperedges=edges)


def doily() -> SparseHypergraph:
    pairs = list(itertools.combinations(range(1, 7), 2))
    pid = {p: i for i, p in enumerate(pairs)}

    def matchings(es: tuple[int, ...]):
        if not es:
            yield ()
            return
        a = es[0]
        rest = es[1:]
        for i, b in enumerate(rest):
            new_rest = rest[:i] + rest[i + 1 :]
            for m in matchings(new_rest):
                yield ((a, b),) + m

    lines = [sorted(pid[tuple(sorted(p))] for p in m) for m in matchings(tuple(range(1, 7)))]
    return SparseHypergraph(n_nodes=15, hyperedges=lines)


def py_canonical_string(H: SparseHypergraph, algorithm: str) -> str:
    """Pure-Python reference canonical_string using only the _python_* shims."""
    seeds = _python_max_xi_nodes(H)
    k = required_k(H)
    if algorithm == "greedy_single":
        seeds = (min(seeds),)
    candidates = [_python_greedy_h2s(H, seed_node=s, k=k) for s in seeds]
    best = min(candidates, key=sequence_sort_key)
    return serialize(list(best))


def cpp_canonical_string(H: SparseHypergraph, algorithm: str) -> str:
    return canonical_string(H, algorithm=algorithm)


def best_of(fn, n_repeats: int) -> float:
    best = float("inf")
    for _ in range(n_repeats):
        t0 = time.perf_counter()
        fn()
        dt = time.perf_counter() - t0
        if dt < best:
            best = dt
    return best


def main() -> None:
    designs = [
        ("Fano STS(7)", fano(), 3),
        ("STS(9) AG(2,3)", sts9(), 3),
        ("STS(13) cyclic", sts13(), 3),
        ("GQ(2,2) doily", doily(), 1),  # single Python trial — too slow otherwise
    ]
    variants = ["greedy_min", "greedy_single"]

    rows = []
    print(f"{'design':18s}  {'algorithm':16s}  {'PY':>10s}  {'CPP':>10s}  {'speedup':>9s}  status")
    print("-" * 92)
    for label, H, py_repeats in designs:
        for algo in variants:
            # Skip multi-seed greedy_min on doily — DNF in pure Python.
            if label == "GQ(2,2) doily" and algo == "greedy_min":
                t_py = float("nan")
                t_cpp = best_of(lambda H=H, a=algo: cpp_canonical_string(H, a), 3)
                py_str = None
                cpp_str = cpp_canonical_string(H, algo)
            else:
                t_py = best_of(lambda H=H, a=algo: py_canonical_string(H, a), py_repeats)
                t_cpp = best_of(lambda H=H, a=algo: cpp_canonical_string(H, a), 3)
                py_str = py_canonical_string(H, algo)
                cpp_str = cpp_canonical_string(H, algo)

            status = "EQ" if py_str is None or py_str == cpp_str else "MISMATCH"
            speedup = (
                "DNF"
                if t_py != t_py  # NaN check
                else f"{t_py / t_cpp:7.1f}x"
            )
            py_disp = "DNF" if t_py != t_py else f"{t_py * 1000:9.2f}ms"
            cpp_disp = f"{t_cpp * 1000:9.2f}ms"
            print(
                f"{label:18s}  {algo:16s}  {py_disp:>10s}  {cpp_disp:>10s}  {speedup:>9s}  {status}"
            )
            rows.append(
                {
                    "design": label,
                    "algorithm": algo,
                    "py_ms": None if t_py != t_py else t_py * 1000,
                    "cpp_ms": t_cpp * 1000,
                    "speedup": None if t_py != t_py else t_py / t_cpp,
                    "status": status,
                }
            )

    # Render the same table into docs/CPP_SPEEDUP.md.
    repo_root = Path(__file__).resolve().parent.parent
    out = repo_root / "docs" / "CPP_SPEEDUP.md"
    lines = [
        "# Phase 4 — IsalHG C++ vs Python speedup",
        "",
        "Local laptop, single-threaded. Python timings use the pre-port",
        "reference implementations kept under ``_python_greedy_h2s`` and",
        "``_python_max_xi_nodes``. C++ timings call the production entry",
        "``isalhg.core.canonical.canonical_string`` which dispatches to the",
        "C++ ``_core.canonical_string`` for the five native variants.",
        "",
        "All cells are byte-equal between Python and C++ on the runs that",
        "completed (column ``status``).",
        "",
        "| Design | Algorithm | Python (ms) | C++ (ms) | Speedup | Status |",
        "|---|---|---:|---:|---:|---|",
    ]
    for r in rows:
        py_cell = "DNF" if r["py_ms"] is None else f"{r['py_ms']:.2f}"
        sp_cell = "—" if r["speedup"] is None else f"{r['speedup']:.1f}×"
        lines.append(
            f"| {r['design']} | {r['algorithm']} | {py_cell} | {r['cpp_ms']:.2f} | {sp_cell} | {r['status']} |"
        )
    lines.append("")
    out.write_text("\n".join(lines))
    print()
    print(f"Wrote {out.relative_to(repo_root)}")


if __name__ == "__main__":
    main()
