"""Numeric probe for the pointer-run amortization analysis (T-TBb, D1).

Measures, on pinned-seed random connected hypergraphs, the two quantities the
layout-locality analysis of ``proofs/stability/pointer_run_amortization.tex``
predicts:

1. **Total pointer movement** ``M(H)`` = number of ``P``/``N`` tokens in
   ``w*_c(H)``, as a function of ``(n, m)`` at fixed arity range.  The
   averaging identity gives ``E_s[T_span] = M(H)/n`` over uniform insertion
   slots, so super-linear growth of ``M`` in ``m`` (at fixed density) means
   the average spanning count outgrows any ``O(k*Delta)`` budget.

2. **Per-edit sensitivity** ``s(e) = d_Lev(w*_c(H), w*_c(H+e))`` for random
   connectivity-preserving Qin edits (``random_connected_edit``), grouped by
   edit type, as ``n`` grows at fixed density.  Layout-locality (iv)-(v)
   generic would predict a plateau at ``O(k*Delta)``; growth with ``n``
   supports the refutation.

This probe is deliberately small (local, seconds-to-minutes, n <= 96); it is
NOT experiment E2b / T-M5a (the HPC single-edit histogram), only a sanity
check on the scaling direction of the theory. Distances are token-level
Levenshtein via rapidfuzz on serialized token lists.
"""

from __future__ import annotations

import random
import statistics
from collections import defaultdict

from rapidfuzz.distance import Levenshtein

from isalhg.core.canonical import canonical_string
from isalhg.core.instructions import TokenN, TokenP, TokenV, parse
from isalhg.core.sparse_hypergraph import SparseHypergraph, random_connected_edit
from isalhg.datasets.synthetic._random_hg import random_connected_hypergraph
from isalhg.errors import CanonicalizationTimeoutError

ARITY_RANGE: tuple[int, int] = (2, 3)
K: int = 3
N_INSTANCES: int = 5
N_EDITS: int = 12
MASTER_SEED: int = 20260714


BRANCH_BUDGET: int = 50_000


def _wstar(H: SparseHypergraph) -> str | None:
    """``w*_c`` with a branch budget; ``None`` when a tie-degenerate draw explodes."""
    try:
        return canonical_string(H, k=K, max_expansions=BRANCH_BUDGET)
    except CanonicalizationTimeoutError:
        return None


def _tokens(H: SparseHypergraph) -> list[str] | None:
    w = _wstar(H)
    return None if w is None else [t.serialize() for t in parse(w)]


def _pointer_token_count(tokens: list[str]) -> int:
    parsed = parse(";".join(tokens))
    return sum(isinstance(t, (TokenP, TokenN)) for t in parsed)


def boundary_crossings(w: str, k: int) -> dict[str, int]:
    """Replay ``w`` through a CDLL simulation; count crossings per boundary.

    Boundaries are named by the vertex on their left ("after x"); a ``P_l``
    step from cell ``x`` crosses "after x", an ``N_l`` step into cell ``y``
    crosses "after y". Insertion after ``p_1`` (V semantics: new nodes chained
    after the anchor) creates fresh boundaries and never crosses one.
    Returns the crossing count per boundary; ``sum(values()) == M(H)`` and
    ``max(values())`` upper-bounds ``T_span`` for an insertion at the
    worst-case slot.
    """
    succ: dict[int, int] = {0: 0}
    pred: dict[int, int] = {0: 0}
    pos = [0] * k
    next_id = 1
    crossings: dict[int, int] = {}
    for tok in parse(w):
        if isinstance(tok, TokenP):
            x = pos[tok.i - 1]
            crossings[x] = crossings.get(x, 0) + 1
            pos[tok.i - 1] = succ[x]
        elif isinstance(tok, TokenN):
            y = pred[pos[tok.i - 1]]
            crossings[y] = crossings.get(y, 0) + 1
            pos[tok.i - 1] = y
        elif isinstance(tok, TokenV):
            anchor = pos[0]
            for _ in range(tok.j):
                v = next_id
                next_id += 1
                nxt = succ[anchor]
                succ[anchor], pred[v] = v, anchor
                succ[v], pred[nxt] = nxt, v
                anchor = v
    return {f"after {x}": c for x, c in crossings.items()}


def _crossing_stats(H: SparseHypergraph) -> tuple[int, int, float] | None:
    """Return ``(M, max_b X(b), mean_b X(b))`` for ``w*_c(H)``, or None on budget."""
    w = _wstar(H)
    if w is None:
        return None
    cross = boundary_crossings(w, K)
    if not cross:
        return 0, 0, 0.0
    total = sum(cross.values())
    return total, max(cross.values()), total / max(H.n_nodes, 1)


def balanced_tree(depth: int, branching: int = 2) -> SparseHypergraph:
    """Complete ``branching``-ary tree as a 2-uniform hypergraph."""
    edges: list[frozenset[int]] = []
    n = 1
    frontier = [0]
    for _ in range(depth):
        nxt: list[int] = []
        for parent in frontier:
            for _ in range(branching):
                edges.append(frozenset({parent, n}))
                nxt.append(n)
                n += 1
        frontier = nxt
    return SparseHypergraph(n_nodes=n, hyperedges=edges)


def probe_boundary_crossings() -> None:
    print()
    print("=== X(b): boundary-crossing profile of w*_c (T_span upper bound) ===")
    print(f"{'instance':<28} {'n':>5} {'m':>5} {'Delta':>5} {'M':>7} {'maxX':>6} {'M/n':>7}")
    for depth in (3, 4, 5, 6, 7, 8):
        H = balanced_tree(depth)
        stats = _crossing_stats(H)
        if stats is None:
            print(f"{'binary tree d=' + str(depth):<28} branch budget exceeded, skipped")
            continue
        M, mx, mean = stats
        d = max(H.degree(v) for v in H.nodes())
        print(
            f"{'binary tree d=' + str(depth):<28} {H.n_nodes:>5} {H.n_edges:>5} "
            f"{d:>5} {M:>7} {mx:>6} {mean:>7.2f}"
        )
    for n in (16, 32, 48):
        for density in (1.0, 1.5, 2.0):
            m_target = round(n * density)
            rows = []
            for inst in range(N_INSTANCES):
                rng = random.Random(MASTER_SEED * 3_000_017 + n * 10_000 + m_target * 100 + inst)
                H, _ = random_connected_hypergraph(
                    n_nodes=n, n_edges=m_target, arity_range=ARITY_RANGE, rng=rng
                )
                stats = _crossing_stats(H)
                if stats is None:
                    continue
                M, mx, mean = stats
                d = max(H.degree(v) for v in H.nodes())
                rows.append((H.n_nodes, H.n_edges, d, M, mx, mean))
            if not rows:
                continue
            med = [statistics.median(c) for c in zip(*rows, strict=True)]
            print(
                f"{'random d=' + f'{density:.1f}':<28} {med[0]:>5.0f} {med[1]:>5.0f} "
                f"{med[2]:>5.0f} {med[3]:>7.0f} {med[4]:>6.0f} {med[5]:>7.2f}"
            )


def probe_total_movement() -> None:
    print("=== M(H): total pointer movement in w*_c ===")
    print(
        f"{'n':>4} {'density':>8} {'m_med':>6} {'Delta_med':>9} "
        f"{'M_med':>8} {'M/n':>8} {'M/(k*m)':>8}"
    )
    for n in (12, 16, 24, 32, 48):
        for density in (1.0, 1.5, 2.0):
            m_target = round(n * density)
            Ms: list[float] = []
            ms: list[int] = []
            deltas: list[int] = []
            for inst in range(N_INSTANCES):
                rng = random.Random(MASTER_SEED * 1_000_003 + n * 10_000 + m_target * 100 + inst)
                H, _ = random_connected_hypergraph(
                    n_nodes=n, n_edges=m_target, arity_range=ARITY_RANGE, rng=rng
                )
                toks = _tokens(H)
                if toks is None:
                    continue
                Ms.append(_pointer_token_count(toks))
                ms.append(H.n_edges)
                deltas.append(max(H.degree(v) for v in H.nodes()))
            if not Ms:
                continue
            m_med = statistics.median(ms)
            M_med = statistics.median(Ms)
            print(
                f"{n:>4} {density:>8.1f} {m_med:>6.0f} "
                f"{statistics.median(deltas):>9.0f} {M_med:>8.0f} "
                f"{M_med / n:>8.2f} {M_med / (K * max(m_med, 1)):>8.2f}"
            )


def probe_single_edit_sensitivity() -> None:
    print()
    print("=== s(e) = d_Lev(w*_c(H), w*_c(H+e)) by edit type ===")
    print(
        f"{'n':>4} {'edit type':<24} {'count':>5} {'median':>7} "
        f"{'p90':>6} {'max':>5} {'k*Delta_med':>11}"
    )
    for n in (12, 16, 24, 32):
        by_type: dict[str, list[int]] = defaultdict(list)
        kdelta: list[int] = []
        for inst in range(N_INSTANCES):
            rng = random.Random(MASTER_SEED * 2_000_003 + n * 10_000 + inst)
            H, _ = random_connected_hypergraph(
                n_nodes=n,
                n_edges=round(1.5 * n),
                arity_range=ARITY_RANGE,
                rng=rng,
            )
            base = _tokens(H)
            if base is None:
                continue
            delta = max(H.degree(v) for v in H.nodes())
            kdelta.append(K * delta)
            for _ in range(N_EDITS):
                H2, kind = random_connected_edit(H, rng, max_arity=ARITY_RANGE[1])
                edited = _tokens(H2)
                if edited is None:
                    continue
                s = Levenshtein.distance(base, edited)
                by_type[kind].append(s)
        for kind in sorted(by_type):
            vals = by_type[kind]
            qs = statistics.quantiles(vals, n=10) if len(vals) >= 10 else vals
            print(
                f"{n:>4} {kind:<24} {len(vals):>5} "
                f"{statistics.median(vals):>7.1f} "
                f"{qs[-1] if len(vals) >= 10 else max(vals):>6.1f} "
                f"{max(vals):>5} {statistics.median(kdelta):>11.0f}"
            )


def main() -> None:
    print(
        f"probe_pointer_runs: k={K}, arity={ARITY_RANGE}, "
        f"{N_INSTANCES} instances/cell, {N_EDITS} edits/instance, "
        f"master seed {MASTER_SEED}"
    )
    probe_total_movement()
    probe_boundary_crossings()
    probe_single_edit_sensitivity()


if __name__ == "__main__":
    main()
