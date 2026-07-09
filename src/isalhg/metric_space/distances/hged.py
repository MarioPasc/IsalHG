"""Hypergraph Edit Distance oracles -- ``ExactHGED`` and ``BipartiteHGED``.

HGED is the ground-truth structural distance the Layer-1 correlation study
regresses ``d_I`` (and every competitor) against. It is **exactly** the
Hypergraph Edit Distance of Qin, Li, Yuan, Wang & Dai, *Explainable Hyperlink
Prediction: A Hypergraph Edit Distance-Based Approach* (ICDE 2023, DOI
10.1109/ICDE55515.2023.00386), the article's single official cost model
(PI decision 2026-07-08, superseding the earlier whole-edge deviation):

    ``HGED(H, H') = min total cost of atomic edits transforming H into a
    hypergraph isomorphic to H'``

over Qin's Definition-3 atomic operations, all unit cost: (i) insert/delete a
cardinality-0 node or hyperedge (an empty shell); (ii) extend/reduce a
hyperedge by one node; (iii) substitute a node or hyperedge label. Deleting or
inserting a whole arity-``a`` hyperedge therefore costs ``a + 1``, and deleting
a degree-``h`` node costs ``h + 1``. On the trivial (unlabelled) vocabulary the
label term is identically zero.

The same metric is computed by two independent solvers: the branch-and-bound
oracle here (fast; the one the experiments use) and the paper-faithful
HGED-BFS in :mod:`isalhg.metric_space.distances.qin_hged` (the fidelity anchor,
validated against the paper's Example 2); a property test asserts their
equality on random pairs.

No public HGED solver exists (a 2026-07-08 search confirmed Qin et al. released
no code, and neither HyperNetX/XGI/Hypergraphx nor any GED library ships one),
so ``ExactHGED`` is bespoke. Following the resolved decision OD4 it is our own
search over the six typed ops on :class:`SparseHypergraph` **directly**, not a
GED on the bipartite Levi graph (whose equality with HGED is unproven and would
owe a correctness argument we decline to carry).

Cost model (the correctness contract)
--------------------------------------
Both oracles evaluate an edit by a pair of correspondences: a vertex bijection
``pi`` (source vertices padded with dummies to ``max(n, n')`` and mapped onto
target vertices padded likewise) and a hyperedge bijection ``mu`` (edges padded
with empty dummy edges). Their cost decomposes with no overlap into

* **vertex cost** -- ``#deletions + #insertions + #label-substitutions`` where a
  deletion is a real source vertex mapped to a dummy, an insertion a dummy
  mapped to a real target vertex;
* **hyperedge cost** -- an assignment between the two edge sets in which a
  matched pair ``(E, E')`` costs the incidence-edit count
  ``|E| + |E'| - 2*|{a in E : pi(a) in E'}|`` (each mismatched membership slot is
  one incidence add or remove) plus a unit label-substitution term, while an
  unmatched source edge is a deletion at cost ``1 + |E|`` (``|E|`` reduces plus
  the empty-shell delete) and an unmatched target edge an insertion at cost
  ``1 + |E'|``, so the assignment freely trades reshaping against
  delete-then-insert (matching is never dearer: ``Hamming + label <=
  |E| + |E'| + 1 < (1+|E|) + (1+|E'|)``).

Relation to the generator ops and the ladder budget
----------------------------------------------------
The six free functions of :mod:`isalhg.core.sparse_hypergraph` remain the
*generators* the perturbation ladder samples, but each is priced by Qin's
taxonomy (:func:`~isalhg.core.sparse_hypergraph.qin_edit_cost`):
``insert/delete_hyperedge`` of arity ``a`` costs ``a + 1``, the others cost 1.
:func:`~isalhg.core.sparse_hypergraph.edit_path` returns the accumulated Qin
cost as its budget, so the ladder guarantee ``budget >= HGED`` holds under
this official cost model.

That this mapping cost equals the minimum sequential unit-edit cost is the
standard graph-edit-distance mapping equivalence (Bunke 1997), specialised to
this generating set; it is validated here empirically against hand-computed edit
counts and the perturbation-ladder budget (``t >= HGED``). The full proof is
theory-track work (T-TA / T-TB), not this module.

Algorithm
---------
Given a fixed vertex bijection ``pi`` the optimal ``mu`` is a linear-sum
assignment over the padded edge-cost matrix, solved with
:func:`scipy.optimize.linear_sum_assignment`. ``ExactHGED`` searches the outer
minimisation over ``pi`` with best-first branch-and-bound (an A* whose structure
ports :func:`networkx.algorithms.similarity.optimize_edit_paths` -- partial
vertex map, admissible LSAP-style lower bound, anytime upper bound -- onto typed
hypergraph ops). The admissible heuristic sums a vertex lower bound
(``|remaining source| - |remaining target|`` forced insertions/deletions) and a
vertex-map-independent edge lower bound (an LSAP over per-edge cardinality-gap
costs), and the incumbent is seeded with the better of a degree-aligned greedy
map and the Riesen-Bunke bipartite map so a tight upper bound prunes early.
HGED is NP-hard (Qin et al. §IV), so the exact oracle is small-to-medium scale;
its ``n``-ceiling on the HPC parallel regime is what T-M2 benchmarks (DQ1).

``BipartiteHGED`` is the optional scalable cross-check (decision DQ2): it fixes a
single ``pi`` from a Riesen & Bunke (2009) bipartite node assignment and returns
the exact cost under that ``pi`` -- a genuine edit, hence an **upper bound**,
``ExactHGED <= BipartiteHGED``.

scipy and numpy are imported inside method bodies (guarded, raising
:class:`RepresentationDependencyMissingError`) so importing this module -- and
the whole ``metric_space`` package -- never requires them at import time.
"""

from __future__ import annotations

import heapq
import itertools
import time
from typing import Any

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.errors import HGEDComputationError, RepresentationDependencyMissingError
from isalhg.metric_space.base import HypergraphDistance
from isalhg.metric_space.registry import register_distance
from isalhg.types import DistanceName, NodeId


def _import_scipy() -> tuple[Any, Any]:
    """Return ``(linear_sum_assignment, numpy)`` or raise with an install hint."""
    try:
        import numpy as np
        from scipy.optimize import linear_sum_assignment
    except ImportError as exc:  # pragma: no cover - exercised only without scipy/numpy
        raise RepresentationDependencyMissingError(
            "scipy and numpy are required for the HGED oracles; "
            "install via `pip install scipy numpy`"
        ) from exc
    return linear_sum_assignment, np


# ---------------------------------------------------------------------------
# Cost primitives (shared by ExactHGED and BipartiteHGED)
# ---------------------------------------------------------------------------


def _vertex_cost(H1: SparseHypergraph, H2: SparseHypergraph, pi: dict[NodeId, NodeId]) -> int:
    """Vertex-op cost of the correspondence ``pi`` (source vertex -> target vertex).

    Unmatched source vertices are deletions, unmatched target vertices are
    insertions, and each matched pair with differing labels is one substitution.
    """
    matched = len(pi)
    deletions = H1.n_nodes - matched
    insertions = H2.n_nodes - matched
    substitutions = sum(1 for a, b in pi.items() if H1.vertex_label(a) != H2.vertex_label(b))
    return deletions + insertions + substitutions


def _edge_cost(
    H1: SparseHypergraph,
    H2: SparseHypergraph,
    pi: dict[NodeId, NodeId],
    lsa: Any,
    np: Any,
) -> int:
    """Minimum hyperedge-assignment cost given the vertex correspondence ``pi``.

    Solves a Riesen-Bunke-style ``(m1 + m2) x (m1 + m2)`` linear-sum assignment
    with a substitution block (incidence-edit count under ``pi`` + unit label
    term), diagonal delete/insert blocks (Qin cost ``1 + |E|`` each), and a zero
    dummy-dummy block. The assignment therefore trades reshaping a matched pair
    against deleting one edge and inserting the other.
    """
    m1, m2 = H1.n_edges, H2.n_edges
    if m1 == 0 and m2 == 0:
        return 0
    dim = m1 + m2
    forbidden = float(dim + H1.n_nodes + H2.n_nodes + 10) * 4.0

    images = [frozenset(pi[a] for a in H1.members(e) if a in pi) for e in range(m1)]
    e1_sizes = [len(H1.members(e)) for e in range(m1)]
    e2_members = [H2.members(e) for e in range(m2)]
    e1_labels = [H1.edge_label(e) for e in range(m1)]
    e2_labels = [H2.edge_label(e) for e in range(m2)]

    cost = np.full((dim, dim), forbidden, dtype=np.float64)
    for i in range(m1):
        for j in range(m2):
            overlap = len(images[i] & e2_members[j])
            hamming = e1_sizes[i] + len(e2_members[j]) - 2 * overlap
            label = 0 if e1_labels[i] == e2_labels[j] else 1
            cost[i, j] = hamming + label
    for i in range(m1):
        cost[i, m2 + i] = 1.0 + e1_sizes[i]  # delete edge i: |E| reduces + shell
    for j in range(m2):
        cost[m1 + j, j] = 1.0 + len(e2_members[j])  # insert edge j: shell + extends
    for j in range(m2):
        for i in range(m1):
            cost[m1 + j, m2 + i] = 0.0  # dummy-dummy
    rows, cols = lsa(cost)
    return int(round(float(cost[rows, cols].sum())))


# ---------------------------------------------------------------------------
# Exact oracle
# ---------------------------------------------------------------------------


def _greedy_upper_bound(
    H1: SparseHypergraph,
    H2: SparseHypergraph,
    order: list[NodeId],
    lsa: Any,
    np: Any,
) -> int:
    """Cost of a degree-aligned complete correspondence -- an initial upper bound."""
    n2 = H2.n_nodes
    target_order = sorted(range(n2), key=lambda v: H2.degree(v), reverse=True)
    pi = {order[k]: target_order[k] for k in range(min(len(order), n2))}
    return _vertex_cost(H1, H2, pi) + _edge_cost(H1, H2, pi, lsa, np)


def _partial_edge_lb(
    H1: SparseHypergraph,
    H2: SparseHypergraph,
    mapped: dict[NodeId, NodeId],
    deleted: set[NodeId],
    lsa: Any,
    np: Any,
) -> int:
    """Admissible lower bound on the edge-assignment cost given a *partial* map.

    ``mapped`` (source vertex -> committed target) and ``deleted`` (source
    vertices committed to deletion) fix part of the correspondence; unassigned
    vertices are treated optimistically. The LSAP cell for matching ``E`` to
    ``E'`` is ``max(cardinality-gap, forced incidence edits) + [labels differ]``,
    where the *forced* edits are the incidences the committed map already
    determines: a committed member of ``E`` whose image is absent from ``E'`` (a
    forced removal) and a committed image in ``E'`` whose preimage is absent from
    ``E`` (a forced addition). An edge delete/insert costs ``1 + |E|`` (Qin
    empty-shell convention); dummy-dummy is
    free. Each cell underestimates the true match cost, so the assignment is a
    valid lower bound. At a *complete* map every incidence is forced, so this
    returns the exact edge cost -- the terminal cost and the heuristic are one
    function.
    """
    m1, m2 = H1.n_edges, H2.n_edges
    if m1 == 0 and m2 == 0:
        return 0
    dim = m1 + m2
    # The big-M must dominate every legitimate cell, whose ceiling scales with
    # the vertex counts (Hamming <= |E| + |E'| <= 2n, delete/insert = 1 + |E|),
    # not just with the edge counts.
    forbidden = float(dim + H1.n_nodes + H2.n_nodes + 10) * 4.0
    committed = mapped.keys() | deleted
    reverse = {v: u for u, v in mapped.items()}
    used = reverse.keys()
    e1_members = [H1.members(e) for e in range(m1)]
    e2_members = [H2.members(e) for e in range(m2)]
    e1_labels = [H1.edge_label(e) for e in range(m1)]
    e2_labels = [H2.edge_label(e) for e in range(m2)]

    cost = np.full((dim, dim), forbidden, dtype=np.float64)
    for i in range(m1):
        members_i = e1_members[i]
        for j in range(m2):
            members_j = e2_members[j]
            forced_removals = sum(
                1
                for a in members_i
                if a in committed and (a in deleted or mapped.get(a) not in members_j)
            )
            forced_additions = sum(
                1 for b in members_j if b in used and reverse[b] not in members_i
            )
            gap = abs(len(members_i) - len(members_j))
            label = 0 if e1_labels[i] == e2_labels[j] else 1
            cost[i, j] = float(max(gap, forced_removals + forced_additions) + label)
    for i in range(m1):
        cost[i, m2 + i] = 1.0 + len(e1_members[i])
    for j in range(m2):
        cost[m1 + j, j] = 1.0 + len(e2_members[j])
    for j in range(m2):
        for i in range(m1):
            cost[m1 + j, m2 + i] = 0.0
    rows, cols = lsa(cost)
    return int(round(float(cost[rows, cols].sum())))


def _exact_hged(
    H1: SparseHypergraph,
    H2: SparseHypergraph,
    *,
    timeout: float | None,
    max_expansions: int | None,
) -> int:
    """Return the exact HGED via best-first branch-and-bound over vertex maps.

    Raises
    ------
    HGEDComputationError
        If the search exceeds ``timeout`` seconds or ``max_expansions`` node
        expansions before proving optimality.
    """
    lsa, np = _import_scipy()

    # Orient so the target has no more vertices than the source: HGED is
    # symmetric and the smaller target shrinks the branching factor (Qin's
    # Lemma 4.1 -- with |V_source| >= |V_target| an optimal map needs no vertex
    # insertion).
    if H2.n_nodes > H1.n_nodes:
        H1, H2 = H2, H1
    n1, n2 = H1.n_nodes, H2.n_nodes
    m1, m2 = H1.n_edges, H2.n_edges

    order = sorted(range(n1), key=lambda v: H1.degree(v), reverse=True)

    # Seed the incumbent with the better of a degree-aligned greedy map and the
    # Riesen-Bunke bipartite map; a tight upper bound is what prunes the search.
    bp_pi = _bipartite_matching(H1, H2, lsa, np)
    best = min(
        _greedy_upper_bound(H1, H2, order, lsa, np),
        _vertex_cost(H1, H2, bp_pi) + _edge_cost(H1, H2, bp_pi, lsa, np),
    )
    if best <= 0:
        return 0

    # The empty-map edge bound seeds the root and, carried down the tree, orders
    # a node's children (a parent's bound never exceeds a child's true cost).
    root_edge_lb = _partial_edge_lb(H1, H2, {}, set(), lsa, np)

    counter = itertools.count()
    # State: (f, tiebreak, depth, committed_vertex_cost, assignment, used_targets).
    # assignment[k] is the target matched to order[k], or -1 for a deletion. ``f``
    # is the push-time (looser) bound; it gives a cheap prune before the tighter
    # partial-map bound is recomputed at pop.
    heap: list[tuple[int, int, int, int, tuple[int, ...], frozenset[int]]] = [
        (abs(n1 - n2) + root_edge_lb, next(counter), 0, 0, (), frozenset())
    ]
    started = time.perf_counter()
    expansions = 0

    while heap:
        f, _, depth, g, assignment, used = heapq.heappop(heap)
        if f >= best:
            continue  # incumbent improved since this node was pushed
        mapped = {order[k]: assignment[k] for k in range(depth) if assignment[k] != -1}
        deleted = {order[k] for k in range(depth) if assignment[k] == -1}
        # Recompute the tight partial-map edge bound at pop; at full depth it is
        # the exact edge cost, so ``tight`` is then the exact total edit cost.
        edge_lb = _partial_edge_lb(H1, H2, mapped, deleted, lsa, np)
        v_lb = abs((n1 - depth) - (n2 - len(used)))
        tight = g + v_lb + edge_lb
        if tight >= best:
            continue  # a stronger bound than at push time proves this node hopeless
        if depth == n1:
            best = tight  # tight == exact total here and beats the incumbent
            if best <= 0:
                return 0
            continue

        expansions += 1
        if max_expansions is not None and expansions > max_expansions:
            raise HGEDComputationError(
                f"exact HGED exceeded {max_expansions} node expansions "
                f"(n={n1}, m={m1} vs n={n2}, m={m2})"
            )
        if timeout is not None and (time.perf_counter() - started) > timeout:
            raise HGEDComputationError(
                f"exact HGED exceeded {timeout:g}s (n={n1}, m={m1} vs n={n2}, m={m2})"
            )

        v = order[depth]
        remaining_source = n1 - (depth + 1)
        for b in range(n2):
            if b in used:
                continue
            g_new = g + (0 if H1.vertex_label(v) == H2.vertex_label(b) else 1)
            used_new = used | {b}
            f_new = g_new + abs(remaining_source - (n2 - len(used_new))) + edge_lb
            if f_new < best:
                heapq.heappush(
                    heap,
                    (f_new, next(counter), depth + 1, g_new, assignment + (b,), used_new),
                )
        # deletion branch (source vertex v -> dummy)
        g_del = g + 1
        f_del = g_del + abs(remaining_source - (n2 - len(used))) + edge_lb
        if f_del < best:
            heapq.heappush(heap, (f_del, next(counter), depth + 1, g_del, assignment + (-1,), used))

    return best


class ExactHGED(HypergraphDistance):
    """Exact Hypergraph Edit Distance (ground-truth oracle) -- ``exact_hged``.

    Parameters
    ----------
    timeout : float or None, optional
        Wall-clock budget in seconds for a single :meth:`pairwise` call. ``None``
        (default) runs to optimality. On timeout, raises
        :class:`HGEDComputationError` -- the benchmark uses this to locate the
        exact ``n``-ceiling (DQ1).
    max_expansions : int or None, optional
        Cap on branch-and-bound node expansions per call; ``None`` (default) is
        unbounded. A complementary, deterministic ceiling knob.
    """

    def __init__(self, *, timeout: float | None = None, max_expansions: int | None = None) -> None:
        self._timeout = timeout
        self._max_expansions = max_expansions

    @property
    def name(self) -> DistanceName:
        return "exact_hged"

    def pairwise(self, H1: SparseHypergraph, H2: SparseHypergraph) -> float:
        return float(
            _exact_hged(H1, H2, timeout=self._timeout, max_expansions=self._max_expansions)
        )


# ---------------------------------------------------------------------------
# Bipartite approximation (optional scalable cross-check)
# ---------------------------------------------------------------------------


def _bipartite_matching(
    H1: SparseHypergraph, H2: SparseHypergraph, lsa: Any, np: Any
) -> dict[NodeId, NodeId]:
    """Riesen & Bunke (2009) node assignment -> a single vertex correspondence.

    Builds the ``(n1+n2) x (n1+n2)`` LSAP with a substitution block (label + a
    local degree-difference proxy for structure), diagonal deletion/insertion
    blocks, and a zero dummy-dummy block, then reads off the real-to-real matches.
    """
    n1, n2 = H1.n_nodes, H2.n_nodes
    if n1 == 0 or n2 == 0:
        return {}
    dim = n1 + n2
    forbidden = float(dim + H1.n_edges + H2.n_edges + 10) * 4.0
    deg1 = [H1.degree(v) for v in range(n1)]
    deg2 = [H2.degree(v) for v in range(n2)]

    cost = np.full((dim, dim), forbidden, dtype=np.float64)
    for u in range(n1):
        for v in range(n2):
            label = 0.0 if H1.vertex_label(u) == H2.vertex_label(v) else 1.0
            cost[u, v] = label + abs(deg1[u] - deg2[v])
    for u in range(n1):
        cost[u, n2 + u] = 1.0 + deg1[u]  # delete source vertex u
    for v in range(n2):
        cost[n1 + v, v] = 1.0 + deg2[v]  # insert target vertex v
    for u in range(n1):
        for v in range(n2):
            cost[n1 + v, n2 + u] = 0.0  # dummy-dummy

    rows, cols = lsa(cost)
    pi: dict[NodeId, NodeId] = {}
    for i, j in zip(rows, cols, strict=True):
        if i < n1 and j < n2:
            pi[int(i)] = int(j)
    return pi


class BipartiteHGED(HypergraphDistance):
    """BP-HGED -- an upper bound via Riesen-Bunke bipartite matching (``bipartite_hged``).

    Fixes one vertex correspondence from a linear-sum assignment and returns the
    exact edit cost under it. That cost realises an actual edit sequence, so it
    upper-bounds the exact oracle: ``ExactHGED(H, H') <= BipartiteHGED(H, H')``.
    Optional scalable cross-check (decision DQ2), not load-bearing.
    """

    @property
    def name(self) -> DistanceName:
        return "bipartite_hged"

    def pairwise(self, H1: SparseHypergraph, H2: SparseHypergraph) -> float:
        lsa, np = _import_scipy()
        candidates = [_bipartite_matching(H1, H2, lsa, np)]
        if H1.n_nodes == H2.n_nodes:
            # The identity correspondence is always a valid edit; including it
            # keeps the heuristic's self-distance at 0 on symmetric inputs, where
            # the single LSAP node match need not be an automorphism.
            candidates.append({v: v for v in range(H1.n_nodes)})
        return float(
            min(_vertex_cost(H1, H2, pi) + _edge_cost(H1, H2, pi, lsa, np) for pi in candidates)
        )


register_distance("exact_hged", ExactHGED)
register_distance("bipartite_hged", BipartiteHGED)
