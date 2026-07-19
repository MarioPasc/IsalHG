"""Verify every registered representation on the planted corpus (S2 pass).

Builds the S2 verification corpus — the planted-family corpus (4 families x 3
members, seed 0) plus one permuted copy per family and a Fano/permuted-Fano
pair — and checks, for each competitor distance and for ``d_I``:

* ``matrix()`` runs; the result is symmetric, non-negative, zero-diagonal;
* every planted isomorphic pair maps to distance 0 (spectral NetLSD and
  transport HyperCOT within tolerance);
* the complete invariants (``isalhg_levenshtein``, ``nauty_levi_edit``)
  separate every non-isomorphic pair.

HyperCOT is attempted last and reported as SKIP when its pinned env
(``isalhg-hypercot``, see ``envs/hypercot.yml``) is absent.

First run + reference numbers: the S2 orchestrator session (2026-07-19),
recorded in ``docs/article/DEVELOPMENT/SESSIONS.md``.
"""

from __future__ import annotations

import random
import sys
import time

import numpy as np

from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.datasets.registry import get_dataset
from isalhg.errors import SubprocessRepresentationError
from isalhg.metric_space.registry import get_distance

RNG_SEED = 20260719


def _fano() -> SparseHypergraph:
    edges = [
        [0, 1, 2],
        [0, 3, 4],
        [0, 5, 6],
        [1, 3, 5],
        [1, 4, 6],
        [2, 3, 6],
        [2, 4, 5],
    ]
    return SparseHypergraph(
        n_nodes=7,
        hyperedges=[frozenset(e) for e in edges],
        n_vertex_labels=1,
        n_edge_labels=1,
        vertex_labels=[0] * 7,
        edge_labels=[0] * len(edges),
    )


def build_corpus() -> tuple[list[SparseHypergraph], list[tuple[int, int]], list[str]]:
    """Return (corpus, planted iso-pair index list, item names)."""
    rng = random.Random(RNG_SEED)

    def sigma(n: int) -> list[int]:
        s = list(range(n))
        rng.shuffle(s)
        return s

    items = list(get_dataset("planted_families", {"seed_value": 0}))
    corpus = [it.hypergraph for it in items]
    names = [it.item_id for it in items]
    iso_pairs: list[tuple[int, int]] = []
    for base in (0, 3, 6, 9):
        H = corpus[base]
        corpus.append(permute(H, sigma(H.n_nodes)))
        names.append(f"perm({names[base]})")
        iso_pairs.append((base, len(corpus) - 1))
    fano = _fano()
    corpus.append(fano)
    names.append("fano")
    corpus.append(permute(fano, sigma(7)))
    names.append("perm(fano)")
    iso_pairs.append((len(corpus) - 2, len(corpus) - 1))
    return corpus, iso_pairs, names


def check(
    name: str,
    corpus: list[SparseHypergraph],
    iso_pairs: list[tuple[int, int]],
    names: list[str],
    *,
    atol: float,
    complete: bool,
) -> bool:
    """Run one distance over the corpus and print a one-line verdict."""
    t0 = time.perf_counter()
    D = get_distance(name).matrix(corpus)
    dt = time.perf_counter() - t0
    n = len(corpus)
    iso_vals = [float(D[i, j]) for i, j in iso_pairs]
    iu = np.triu_indices(n, k=1)
    ok = (
        D.shape == (n, n)
        and bool(np.allclose(D, D.T))
        and bool(np.allclose(np.diag(D), 0.0))
        and bool((D >= -1e-12).all())
        and all(v <= atol for v in iso_vals)
    )
    line = (
        f"{name:22} {dt:7.2f}s  iso_max={max(iso_vals):.3g} "
        f"offdiag[min={D[iu].min():.3g} med={np.median(D[iu]):.3g} max={D[iu].max():.3g}]"
    )
    if complete:
        iso_set = set(iso_pairs)
        violations = [
            (names[i], names[j], float(D[i, j]))
            for i, j in zip(*iu, strict=True)
            if (i, j) not in iso_set and D[i, j] <= atol
        ]
        ok = ok and not violations
        line += f" complete_sep={not violations}"
        if violations:
            line += f" VIOLATIONS={violations[:5]}"
    print(line + ("  PASS" if ok else "  FAIL"))
    return ok


def main() -> int:
    corpus, iso_pairs, names = build_corpus()
    print(
        f"corpus: {len(corpus)} hypergraphs "
        f"(n in {sorted({H.n_nodes for H in corpus})}), {len(iso_pairs)} planted iso pairs"
    )
    spec: list[tuple[str, float, bool]] = [
        ("isalhg_levenshtein", 0.0, True),
        ("hypergraph_wl_l1", 0.0, False),
        ("nauty_levi_edit", 0.0, True),
        ("hpd_jsd", 0.0, False),
        ("netlsd_l2", 1e-6, False),
    ]
    ok = all(
        check(name, corpus, iso_pairs, names, atol=atol, complete=complete)
        for name, atol, complete in spec
    )
    try:
        ok = check("hypercot", corpus, iso_pairs, names, atol=1e-8, complete=False) and ok
    except SubprocessRepresentationError as exc:
        print(f"hypercot                SKIP ({exc})")
    print("ALL PASS" if ok else "FAILURES PRESENT")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
