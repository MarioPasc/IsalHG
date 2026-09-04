"""Self-contained probe: is the Riesen-Bunke bipartite (Hungarian) graph edit
distance approximation a metric?

Cost model (unit costs, vertex-labelled undirected simple graphs, labels in
{a, b}, unlabelled edges):

  Exact GED. Standard edit-path formulation. A candidate correspondence is a
  partial injective map phi: S1 -> V2 (S1 subset of V1). Vertices in V1 \\ S1
  are deleted, vertices in V2 \\ phi(S1) are inserted. Cost:
    - vertex substitution: 0 if labels match else 1, for i in S1
    - vertex deletion / insertion: 1 each
    - edge cost: for every unordered pair {i,j} in V1, compare presence of
      edge {i,j} in E1 against presence of the corresponding pair in E2
      (via phi, when both endpoints are mapped) -- mismatch costs 1; if
      exactly one of i,j is deleted (or both), a present E1 edge costs 1
      (it cannot survive); plus, symmetrically, every unordered pair in V2
      involving at least one inserted vertex whose edge is present in E2
      costs 1 (pairs already covered by both-endpoints-mapped case above
      are not double-counted).
    Exact GED = min over all partial injective maps phi of this cost.
    Brute-forced for n1, n2 <= 5 (<= 1546 candidate maps).

  Bipartite/Hungarian GED (Riesen & Bunke, IVC 27(7), 2009). Build the
  (n1+n2) x (n1+n2) cost matrix C:
    - top-left  n1 x n2 : c(u_i -> v_j) = label_mismatch(u_i,v_j)
                            + |deg(u_i) - deg(v_j)|
                          (the local edge term is the closed-form optimum of
                          matching the two incident-edge multisets, since
                          edges are unlabelled: min(deg_i,deg_j) edges match
                          at 0 cost, the |deg_i-deg_j| excess costs 1 each)
    - top-right n1 x n1 : diagonal c(u_i -> eps) = 1 + deg(u_i); off-diag BIG
    - bot-left  n2 x n2 : diagonal c(eps -> v_j) = 1 + deg(v_j); off-diag BIG
    - bot-right n2 x n1 : all zero (eps -> eps)
  Solved with scipy.optimize.linear_sum_assignment.
    - "raw" value       = sum of the selected cost-matrix entries.
    - "induced" d_BP     = the node correspondence phi read off the
      assignment (real-to-real entries only) is fed back through the exact
      edit-path cost function above, giving the true cost of the actual
      implied edit path (this is the value normally reported as "the"
      bipartite GED upper bound in the literature).

Reproducibility: single seed SEED below drives every random generator via a
dedicated random.Random instance.
"""

from __future__ import annotations

import itertools
import json
import random
import time
from dataclasses import dataclass

import numpy as np
from scipy.optimize import linear_sum_assignment

SEED = 20260903
BIG = 1.0e6
LABELS = ("a", "b")


@dataclass(frozen=True)
class Graph:
    labels: tuple[str, ...]
    edges: frozenset[frozenset[int]]

    @property
    def n(self) -> int:
        return len(self.labels)

    def degree(self, i: int) -> int:
        return sum(1 for e in self.edges if i in e)

    def edge_list(self) -> list[tuple[int, int]]:
        return sorted(tuple(sorted(e)) for e in self.edges)

    def describe(self) -> str:
        return f"labels={list(self.labels)}, edges={self.edge_list()}"


def random_graph(n: int, p: float, rng: random.Random) -> Graph:
    labels = tuple(rng.choice(LABELS) for _ in range(n))
    edges = set()
    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < p:
                edges.add(frozenset((i, j)))
    return Graph(labels, frozenset(edges))


# ---------------------------------------------------------------------------
# Exact edit-path cost, shared by the brute-force exact GED and the induced
# BP-GED readout.
# ---------------------------------------------------------------------------


def path_cost(g1: Graph, g2: Graph, phi: dict[int, int]) -> int:
    n1, n2 = g1.n, g2.n
    s1 = set(phi.keys())
    mapped2 = set(phi.values())
    deleted1 = set(range(n1)) - s1
    inserted2 = set(range(n2)) - mapped2

    cost = 0
    for i in s1:
        cost += 0 if g1.labels[i] == g2.labels[phi[i]] else 1
    cost += len(deleted1) + len(inserted2)

    for i, j in itertools.combinations(range(n1), 2):
        e1 = frozenset((i, j)) in g1.edges
        if i in s1 and j in s1:
            e2 = frozenset((phi[i], phi[j])) in g2.edges
            cost += 0 if e1 == e2 else 1
        elif e1:
            cost += 1

    for i2, j2 in itertools.combinations(range(n2), 2):
        if i2 in mapped2 and j2 in mapped2:
            continue
        if frozenset((i2, j2)) in g2.edges:
            cost += 1

    return cost


def exact_ged(g1: Graph, g2: Graph) -> int:
    n1, n2 = g1.n, g2.n
    best = None
    for k in range(0, min(n1, n2) + 1):
        for s1 in itertools.combinations(range(n1), k):
            for target in itertools.permutations(range(n2), k):
                phi = dict(zip(s1, target))
                c = path_cost(g1, g2, phi)
                if best is None or c < best:
                    best = c
    return best


def build_cost_matrix(g1: Graph, g2: Graph) -> np.ndarray:
    n1, n2 = g1.n, g2.n
    size = n1 + n2
    c = np.full((size, size), BIG, dtype=float)
    deg1 = [g1.degree(i) for i in range(n1)]
    deg2 = [g2.degree(j) for j in range(n2)]
    for i in range(n1):
        for j in range(n2):
            lbl = 0 if g1.labels[i] == g2.labels[j] else 1
            c[i, j] = lbl + abs(deg1[i] - deg2[j])
    for i in range(n1):
        c[i, n2 + i] = 1 + deg1[i]
    for j in range(n2):
        c[n1 + j, j] = 1 + deg2[j]
    for i in range(n2):
        for j in range(n1):
            c[n1 + i, n2 + j] = 0.0
    return c


def bp_ged(g1: Graph, g2: Graph) -> tuple[int, int]:
    """Returns (raw_value, induced_d_BP), both rounded to int (integer costs)."""
    n1, n2 = g1.n, g2.n
    c = build_cost_matrix(g1, g2)
    row_ind, col_ind = linear_sum_assignment(c)
    raw = int(round(c[row_ind, col_ind].sum()))
    phi = {i: int(col_ind[i]) for i in range(n1) if col_ind[i] < n2}
    induced = path_cost(g1, g2, phi)
    return raw, induced


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def check_metric_sanity(rng: random.Random, n_triples: int = 300) -> dict:
    """Sanity-check the exact GED implementation: metric on random triples,
    GED(A,A)=0."""
    violations_tri = 0
    violations_sym = 0
    zero_self = 0
    total = 0
    for _ in range(n_triples):
        n = rng.choice([3, 4, 5])
        a = random_graph(n, 0.5, rng)
        b = random_graph(rng.choice([3, 4, 5]), 0.5, rng)
        c = random_graph(rng.choice([3, 4, 5]), 0.5, rng)
        dab = exact_ged(a, b)
        dba = exact_ged(b, a)
        dbc = exact_ged(b, c)
        dac = exact_ged(a, c)
        if dab != dba:
            violations_sym += 1
        if dac > dab + dbc:
            violations_tri += 1
        if exact_ged(a, a) == 0:
            zero_self += 1
        total += 1
    return {
        "n_triples": total,
        "sym_violations": violations_sym,
        "tri_violations": violations_tri,
        "zero_self_ok": zero_self,
    }


def check_upper_bound(rng: random.Random, n_pairs: int = 300) -> dict:
    n_ok = 0
    n_equal = 0
    n_total = 0
    for _ in range(n_pairs):
        na = rng.choice([3, 4, 5])
        nb = rng.choice([3, 4, 5])
        a = random_graph(na, 0.5, rng)
        b = random_graph(nb, 0.5, rng)
        ged = exact_ged(a, b)
        _, dbp = bp_ged(a, b)
        n_total += 1
        if dbp >= ged:
            n_ok += 1
        if dbp == ged:
            n_equal += 1
    return {"n_pairs": n_total, "upper_bound_holds": n_ok, "n_equal": n_equal}


def check_symmetry(rng: random.Random, n_pairs: int = 2000) -> dict:
    n_asym_raw = 0
    n_asym_induced = 0
    for _ in range(n_pairs):
        na = rng.choice([3, 4, 5, 6])
        nb = rng.choice([3, 4, 5, 6])
        a = random_graph(na, 0.5, rng)
        b = random_graph(nb, 0.5, rng)
        raw_ab, ind_ab = bp_ged(a, b)
        raw_ba, ind_ba = bp_ged(b, a)
        if raw_ab != raw_ba:
            n_asym_raw += 1
        if ind_ab != ind_ba:
            n_asym_induced += 1
    return {
        "n_pairs": n_pairs,
        "raw_asymmetric": n_asym_raw,
        "induced_asymmetric": n_asym_induced,
    }


def check_triangle(rng: random.Random, n_triples: int = 5000) -> dict:
    raw_viol = 0
    ind_viol = 0
    small_n_triples = []  # (a,b,c) with all n<=5, for the exact-GED contrast
    counterexample = None  # (total_n, a, b, c, dab, dbc, dac) on induced
    counterexample_raw = None
    for _ in range(n_triples):
        na, nb, nc = (rng.choice([3, 4, 5, 6]) for _ in range(3))
        a = random_graph(na, 0.5, rng)
        b = random_graph(nb, 0.5, rng)
        c = random_graph(nc, 0.5, rng)

        raw_ab, ind_ab = bp_ged(a, b)
        raw_bc, ind_bc = bp_ged(b, c)
        raw_ac, ind_ac = bp_ged(a, c)

        if raw_ac > raw_ab + raw_bc:
            raw_viol += 1
            total_n = na + nb + nc
            if counterexample_raw is None or total_n < counterexample_raw[0]:
                counterexample_raw = (total_n, a, b, c, raw_ab, raw_bc, raw_ac)

        if ind_ac > ind_ab + ind_bc:
            ind_viol += 1
            total_n = na + nb + nc
            if counterexample is None or total_n < counterexample[0]:
                counterexample = (total_n, a, b, c, ind_ab, ind_bc, ind_ac)

        if na <= 5 and nb <= 5 and nc <= 5:
            small_n_triples.append((a, b, c))

    return {
        "n_triples": n_triples,
        "raw_violations": raw_viol,
        "induced_violations": ind_viol,
        "counterexample_induced": counterexample,
        "counterexample_raw": counterexample_raw,
        "small_n_triples": small_n_triples,
    }


def check_exact_triangle(small_n_triples: list[tuple[Graph, Graph, Graph]]) -> dict:
    viol = 0
    for a, b, c in small_n_triples:
        dab = exact_ged(a, b)
        dbc = exact_ged(b, c)
        dac = exact_ged(a, c)
        if dac > dab + dbc:
            viol += 1
    return {"n_checked": len(small_n_triples), "violations": viol}


def fmt_graph(g: Graph, name: str) -> str:
    return f"{name}: n={g.n}, labels={list(g.labels)}, edges={g.edge_list()}"


def main() -> None:
    rng = random.Random(SEED)
    t0 = time.time()

    sanity = check_metric_sanity(rng, 300)
    t1 = time.time()

    ub = check_upper_bound(rng, 300)
    t2 = time.time()

    sym = check_symmetry(rng, 2000)
    t3 = time.time()

    tri = check_triangle(rng, 5000)
    t4 = time.time()

    exact_tri = check_exact_triangle(tri["small_n_triples"])
    t5 = time.time()

    results = {
        "seed": SEED,
        "timings_s": {
            "sanity": t1 - t0,
            "upper_bound": t2 - t1,
            "symmetry": t3 - t2,
            "triangle": t4 - t3,
            "exact_triangle": t5 - t4,
        },
        "sanity": sanity,
        "upper_bound": ub,
        "symmetry": sym,
        "triangle": {
            "n_triples": tri["n_triples"],
            "raw_violations": tri["raw_violations"],
            "induced_violations": tri["induced_violations"],
        },
        "exact_triangle": exact_tri,
    }

    print(json.dumps(results, indent=2))

    ce = tri["counterexample_induced"]
    if ce is not None:
        total_n, a, b, c, dab, dbc, dac = ce
        print("\n=== Smallest triangle-inequality counterexample (induced d_BP) ===")
        print(f"total vertices = {total_n}")
        print(fmt_graph(a, "A"))
        print(fmt_graph(b, "B"))
        print(fmt_graph(c, "C"))
        print(f"d_BP(A,B) = {dab}")
        print(f"d_BP(B,C) = {dbc}")
        print(f"d_BP(A,C) = {dac}  (> {dab}+{dbc} = {dab + dbc})")

    ce_raw = tri["counterexample_raw"]
    if ce_raw is not None:
        total_n, a, b, c, dab, dbc, dac = ce_raw
        print("\n=== Smallest triangle-inequality counterexample (raw assignment value) ===")
        print(f"total vertices = {total_n}")
        print(fmt_graph(a, "A"))
        print(fmt_graph(b, "B"))
        print(fmt_graph(c, "C"))
        print(f"raw(A,B) = {dab}")
        print(f"raw(B,C) = {dbc}")
        print(f"raw(A,C) = {dac}  (> {dab}+{dbc} = {dab + dbc})")

    with open("probe_bpged_metric_results.json", "w") as f:
        json.dump(
            {
                "seed": SEED,
                "sanity": sanity,
                "upper_bound": ub,
                "symmetry": sym,
                "triangle": {
                    "n_triples": tri["n_triples"],
                    "raw_violations": tri["raw_violations"],
                    "induced_violations": tri["induced_violations"],
                },
                "exact_triangle": exact_tri,
                "counterexample_induced": None
                if ce is None
                else {
                    "total_n": ce[0],
                    "A": {"labels": list(ce[1].labels), "edges": ce[1].edge_list()},
                    "B": {"labels": list(ce[2].labels), "edges": ce[2].edge_list()},
                    "C": {"labels": list(ce[3].labels), "edges": ce[3].edge_list()},
                    "d_AB": ce[4],
                    "d_BC": ce[5],
                    "d_AC": ce[6],
                },
                "counterexample_raw": None
                if ce_raw is None
                else {
                    "total_n": ce_raw[0],
                    "A": {"labels": list(ce_raw[1].labels), "edges": ce_raw[1].edge_list()},
                    "B": {"labels": list(ce_raw[2].labels), "edges": ce_raw[2].edge_list()},
                    "C": {"labels": list(ce_raw[3].labels), "edges": ce_raw[3].edge_list()},
                    "d_AB": ce_raw[4],
                    "d_BC": ce_raw[5],
                    "d_AC": ce_raw[6],
                },
            },
            f,
            indent=2,
        )


if __name__ == "__main__":
    main()
