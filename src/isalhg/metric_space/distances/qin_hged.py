"""Faithful re-implementation of the Qin et al. (ICDE 2023) HGED -- ``QinHGED``.

Reference: Qin, Li, Yuan, Wang & Dai, *Explainable Hyperlink Prediction: A
Hypergraph Edit Distance-Based Approach* (ICDE 2023, DOI
10.1109/ICDE55515.2023.00386). Qin's empty-shell taxonomy is the article's
**single official HGED cost model** (PI decision 2026-07-08, superseding the
earlier whole-edge variant). This module implements the paper's own
**algorithm** (HGED-BFS) for that metric — the fidelity anchor reproducing the
paper's Example 2 and its Table II regime. The experiments' oracle is the
branch-and-bound solver of the *same metric* in
:class:`~isalhg.metric_space.distances.hged.ExactHGED`, whose LSAP-based
partial-map bounds prune far harder on unlabelled inputs (where this module's
Definition-5 node bound is identically zero); a property test asserts the two
solvers agree exactly on random pairs.

Cost model (Qin Definition 3, all unit cost)
--------------------------------------------
(i) insert/delete a node or hyperedge of cardinality 0; (ii) extend/reduce a
hyperedge by one node; (iii) substitute a node or hyperedge label. Hence
deleting a ``k``-node hyperedge costs ``k + 1`` (``k`` reduces + one empty
shell) and deleting a degree-``h`` node costs ``h + 1`` -- the "empty-shell"
convention.

Equivalently (the paper's EDC formulation, Algorithm 2): pad both hypergraphs
to common node/edge counts with null objects labelled ``⊥`` (matching no real
label); the cost of a complete node+edge correspondence is::

    #node-label mismatches + #edge-label mismatches
    + sum over matched edge pairs (E, E') of |E| + |E'| - 2*|{a in E : f(a) in E'}|
    + sum over deleted edges of |E|      (their incidences)
    + sum over inserted edges of |E'|,

and ``HGED = min`` over correspondences. The paper's Lemma 4.1 (no node
insertion is needed when ``|V| >= |V'|``) justifies orienting the pair so the
source has at least as many nodes; the analogous edge-side restriction (never
delete a real edge *and* insert a real edge when they could be matched, since
matching costs at most ``|E| + |E'| + 1 < (1+|E|) + (1+|E'|)``) fixes the
number of edge deletions to ``max(0, m - m')``.

Algorithm (Qin Algorithm 3, HGED-BFS)
-------------------------------------
FIFO BFS over assignment levels in ReRank order (Strategy 1: all nodes before
all hyperedges; nodes grouped by label with degree-descending groups,
hyperedges by descending cardinality). Node levels add label costs only; edge
levels add label + incidence costs (the node map is complete by then).
Strategy 2 seeds the upper bound ``c̄dc`` from sample greedy mappings (plus the
caller's optional ``upper_bound`` clamp -- the paper sets ``~10`` "in most
situations", which is what makes Table II's random-pair timings feasible: far
pairs exit at the root because the Strategy-3 bound already exceeds the
clamp). Strategy 3 prunes with the admissible remaining-cost bound
``Def 5 + Def 6``:

* Definition 5: ``Ψ(S1, S2) = max(|S1|, |S2|) - |S1 ∩ S2|`` over the label
  multisets of the remaining unmatched nodes plus the remaining unmatched
  hyperedges;
* Definition 6: descending-sorted remaining hyperedge cardinalities, padded
  with zeros, summed ``|Δ|`` -- a lower bound on extend/reduce operations,
  disjoint from the label contributions.

The search is exact: at a complete assignment the accumulated cost equals the
EDC cost of the induced correspondence, and pruning only ever discards states
whose admissible bound cannot beat the incumbent (or exceeds the clamp).

Notes on fidelity. The paper's Example 6 re-ranked order is not reproducible
from its stated rules alone (its published order is neither globally
degree-sorted nor max-degree-group-sorted); ReRank affects speed, never the
returned value, so this implementation uses label groups ordered by descending
maximum degree, degree-descending within a group. ``_dfs_reference`` is the
paper's Algorithm 1+2 enumeration (exact, factorial -- test oracle only).

Everything here is stdlib-only.
"""

from __future__ import annotations

import itertools
import math
import time
from collections import Counter, deque
from collections.abc import Sequence
from dataclasses import dataclass

from isalhg.core.sparse_hypergraph import SparseHypergraph, assert_vocab_compatible
from isalhg.errors import HGEDComputationError
from isalhg.metric_space.base import HypergraphDistance
from isalhg.metric_space.registry import register_distance
from isalhg.types import DistanceName

_NULL = -1

# HGED-BFS search state: (f, depth, edc, assign, used_node_mask, node_nulls,
# source-edge image masks (None until the node phase completes), used_edge_mask,
# edge_nulls).
_State = tuple[int, int, int, tuple[int, ...], int, int, tuple[int, ...] | None, int, int]


# ---------------------------------------------------------------------------
# Pair preparation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Pair:
    """Oriented, precomputed view of one ``(source, target)`` hypergraph pair."""

    n1: int
    n2: int
    vl1: tuple[int, ...]
    vl2: tuple[int, ...]
    e1_members: tuple[frozenset[int], ...]
    e1_labels: tuple[int, ...]
    e2_members: tuple[frozenset[int], ...]
    e2_masks: tuple[int, ...]
    e2_labels: tuple[int, ...]
    node_order: tuple[int, ...]
    edge_order: tuple[int, ...]
    node_null_quota: int
    edge_null_quota: int

    @property
    def m1(self) -> int:
        return len(self.e1_members)

    @property
    def m2(self) -> int:
        return len(self.e2_members)


def _rerank_nodes(H: SparseHypergraph) -> tuple[int, ...]:
    """Strategy 1 node order: label groups by max degree desc, then degree desc."""
    groups: dict[int, list[int]] = {}
    for v in range(H.n_nodes):
        groups.setdefault(H.vertex_label(v), []).append(v)
    ordered: list[int] = []
    group_key = sorted(groups.items(), key=lambda kv: (-max(H.degree(v) for v in kv[1]), kv[0]))
    for _, members in group_key:
        ordered.extend(sorted(members, key=lambda v: (-H.degree(v), v)))
    return tuple(ordered)


def _prepare(H1: SparseHypergraph, H2: SparseHypergraph) -> _Pair:
    """Orient (source has >= nodes, Lemma 4.1) and precompute the pair view."""
    if H2.n_nodes > H1.n_nodes:
        H1, H2 = H2, H1
    n1, n2 = H1.n_nodes, H2.n_nodes
    e1 = [(members, ell) for _, members, ell in H1.iter_edges()]
    e2 = [(members, ell) for _, members, ell in H2.iter_edges()]
    edge_order = tuple(sorted(range(len(e1)), key=lambda i: (-len(e1[i][0]), e1[i][1], i)))
    return _Pair(
        n1=n1,
        n2=n2,
        vl1=tuple(H1.vertex_label(v) for v in range(n1)),
        vl2=tuple(H2.vertex_label(v) for v in range(n2)),
        e1_members=tuple(m for m, _ in e1),
        e1_labels=tuple(ell for _, ell in e1),
        e2_members=tuple(m for m, _ in e2),
        e2_masks=tuple(sum(1 << v for v in m) for m, _ in e2),
        e2_labels=tuple(ell for _, ell in e2),
        node_order=_rerank_nodes(H1),
        edge_order=edge_order,
        node_null_quota=n1 - n2,
        edge_null_quota=max(0, len(e1) - len(e2)),
    )


# ---------------------------------------------------------------------------
# Lower bounds (Definitions 5 and 6) and the exact mapping cost (EDC)
# ---------------------------------------------------------------------------


def _psi(c1: Counter[int], c2: Counter[int]) -> int:
    """Qin Definition 5: ``Ψ(S1, S2) = max(|S1|, |S2|) - |S1 ∩ S2|`` on multisets."""
    common = sum(min(c, c2[label]) for label, c in c1.items())
    return max(sum(c1.values()), sum(c2.values())) - common


def _def6(cards1: Sequence[int], cards2: Sequence[int]) -> int:
    """Qin Definition 6: cardinality bound on extend/reduce operations."""
    a = sorted(cards1, reverse=True)
    b = sorted(cards2, reverse=True)
    if len(a) < len(b):
        a += [0] * (len(b) - len(a))
    elif len(b) < len(a):
        b += [0] * (len(a) - len(b))
    return sum(abs(x - y) for x, y in zip(a, b, strict=True))


def _mapping_cost(pair: _Pair, node_map: Sequence[int], edge_map: Sequence[int]) -> int:
    """Exact EDC cost of a complete correspondence (Qin Algorithm 2 semantics).

    ``node_map[u]`` is the target node matched to source node ``u`` (``-1`` =
    deletion); ``edge_map[i]`` likewise for source edge ``i``. Unmatched real
    target nodes/edges are insertions.
    """
    cost = 0
    used_nodes = set()
    for u, t in enumerate(node_map):
        if t == _NULL:
            cost += 1
        else:
            used_nodes.add(t)
            if pair.vl1[u] != pair.vl2[t]:
                cost += 1
    cost += pair.n2 - len(used_nodes)  # inserted target nodes

    used_edges = set()
    for i, j in enumerate(edge_map):
        members = pair.e1_members[i]
        if j == _NULL:
            cost += 1 + len(members)
        else:
            used_edges.add(j)
            if pair.e1_labels[i] != pair.e2_labels[j]:
                cost += 1
            image = {node_map[a] for a in members if node_map[a] != _NULL}
            overlap = len(image & pair.e2_members[j])
            cost += len(members) + len(pair.e2_members[j]) - 2 * overlap
    for j in range(pair.m2):
        if j not in used_edges:
            cost += 1 + len(pair.e2_members[j])
    return cost


# ---------------------------------------------------------------------------
# Strategy 2 -- sample-mapping upper bounds
# ---------------------------------------------------------------------------


def _greedy_maps(pair: _Pair) -> list[tuple[list[int], list[int]]]:
    """Complete correspondences seeding the incumbent (degree/label greedy + identity)."""
    seeds: list[tuple[list[int], list[int]]] = []
    deg1 = [0] * pair.n1
    for members in pair.e1_members:
        for v in members:
            deg1[v] += 1
    deg2 = [0] * pair.n2
    for members in pair.e2_members:
        for v in members:
            deg2[v] += 1

    node_map = [_NULL] * pair.n1
    unused = set(range(pair.n2))
    for u in pair.node_order:
        if not unused:
            break
        t = min(
            unused,
            key=lambda t: (pair.vl1[u] != pair.vl2[t], abs(deg1[u] - deg2[t]), t),
        )
        node_map[u] = t
        unused.discard(t)

    def greedy_edges(nmap: list[int]) -> list[int]:
        edge_map = [_NULL] * pair.m1
        free = set(range(pair.m2))
        for i in pair.edge_order:
            members = pair.e1_members[i]
            image = {nmap[a] for a in members if nmap[a] != _NULL}
            null_cost = 1 + len(members)
            best_j, best_c = _NULL, null_cost
            for j in free:
                c = (pair.e1_labels[i] != pair.e2_labels[j]) + (
                    len(members) + len(pair.e2_members[j]) - 2 * len(image & pair.e2_members[j])
                )
                if c < best_c:
                    best_j, best_c = j, c
            if best_j != _NULL:
                edge_map[i] = best_j
                free.discard(best_j)
        return edge_map

    seeds.append((node_map, greedy_edges(node_map)))
    if pair.n1 == pair.n2:
        ident = list(range(pair.n1))
        seeds.append((ident, greedy_edges(ident)))
    return seeds


# ---------------------------------------------------------------------------
# Algorithm 1 + 2 -- exhaustive DFS reference (test oracle, tiny inputs only)
# ---------------------------------------------------------------------------


def _dfs_reference(H1: SparseHypergraph, H2: SparseHypergraph) -> int:
    """Exact HGED by full enumeration (factorial; oracle for unit tests)."""
    pair = _prepare(H1, H2)
    padded_targets = list(range(pair.n2)) + [_NULL] * pair.node_null_quota
    best = math.inf
    for node_perm in set(itertools.permutations(padded_targets)):
        node_map = list(node_perm)
        for edge_choice in itertools.permutations(range(pair.m2 + pair.m1), pair.m1):
            edge_map = [j if j < pair.m2 else _NULL for j in edge_choice]
            best = min(best, _mapping_cost(pair, node_map, edge_map))
    return int(best)


# ---------------------------------------------------------------------------
# Algorithm 3 -- HGED-BFS
# ---------------------------------------------------------------------------


def _hged_bfs(
    pair: _Pair,
    *,
    upper_bound: int | None,
    timeout: float | None,
    max_expansions: int | None,
) -> float:
    """Exact HGED (or ``inf`` when a clamp proves ``HGED > upper_bound``)."""
    n1, n2, m1, m2 = pair.n1, pair.n2, pair.m1, pair.m2

    root_lb = (
        _psi(Counter(pair.vl1), Counter(pair.vl2))
        + _psi(Counter(pair.e1_labels), Counter(pair.e2_labels))
        + _def6([len(m) for m in pair.e1_members], [len(m) for m in pair.e2_members])
    )
    if upper_bound is not None and root_lb > upper_bound:
        return math.inf

    best = math.inf
    for node_map, edge_map in _greedy_maps(pair):
        best = min(best, _mapping_cost(pair, node_map, edge_map))
    if upper_bound is not None and best > upper_bound:
        best = math.inf
    if best <= root_lb:
        return best

    def limit() -> float:
        # Deepest admissible f: strict improvement on an achieved incumbent,
        # or the clamp while nothing at or below it has been achieved yet.
        if best is not math.inf:
            return min(best - 1, upper_bound if upper_bound is not None else math.inf)
        return upper_bound if upper_bound is not None else math.inf

    e1_cards = [len(m) for m in pair.e1_members]
    e2_cards = [len(m) for m in pair.e2_members]
    edge_lb_all = _psi(Counter(pair.e1_labels), Counter(pair.e2_labels)) + _def6(e1_cards, e2_cards)

    # State: (f, depth, edc, assign, used_node_mask, node_nulls,
    #         img_masks, used_edge_mask, edge_nulls); ``f`` is the push-time
    #         admissible bound, re-checked at pop against the current incumbent.
    root: _State = (root_lb, 0, 0, (), 0, 0, None, 0, 0)
    queue: deque[_State] = deque([root])
    started = time.perf_counter()
    expansions = 0

    while queue:
        f, depth, edc, assign, used_n, nulls_n, imgs, used_e, nulls_e = queue.popleft()
        if f > limit():
            continue
        if best <= root_lb:
            break

        expansions += 1
        if max_expansions is not None and expansions > max_expansions:
            raise HGEDComputationError(
                f"Qin HGED-BFS exceeded {max_expansions} expansions (n={n1}/{n2}, m={m1}/{m2})"
            )
        if timeout is not None and (time.perf_counter() - started) > timeout:
            raise HGEDComputationError(
                f"Qin HGED-BFS exceeded {timeout:g}s (n={n1}/{n2}, m={m1}/{m2})"
            )

        if depth < n1:
            # ----- node phase -----
            u = pair.node_order[depth]
            lu = pair.vl1[u]
            rem_src = Counter(pair.vl1[v] for v in pair.node_order[depth + 1 :])
            rem_tgt = Counter(pair.vl2[t] for t in range(n2) if not (used_n >> t) & 1)
            base_common = sum(min(c, rem_tgt[label]) for label, c in rem_src.items())
            s_total = n1 - depth - 1
            t_total = n2 - (depth - nulls_n)

            children: list[tuple[int, _State]] = []
            for t in range(n2):
                if (used_n >> t) & 1:
                    continue
                c = 0 if lu == pair.vl2[t] else 1
                lt = pair.vl2[t]
                common = base_common - (1 if 0 < rem_tgt[lt] <= rem_src.get(lt, 0) else 0)
                psi_nodes = max(s_total, t_total - 1) - common
                f_child = edc + c + psi_nodes + edge_lb_all
                if f_child <= limit():
                    children.append(
                        (
                            c,
                            (
                                f_child,
                                depth + 1,
                                edc + c,
                                assign + (t,),
                                used_n | (1 << t),
                                nulls_n,
                                None,
                                0,
                                0,
                            ),
                        )
                    )
            if nulls_n < pair.node_null_quota:
                psi_nodes = max(s_total, t_total) - base_common
                f_child = edc + 1 + psi_nodes + edge_lb_all
                if f_child <= limit():
                    children.append(
                        (
                            1,
                            (
                                f_child,
                                depth + 1,
                                edc + 1,
                                assign + (_NULL,),
                                used_n,
                                nulls_n + 1,
                                None,
                                0,
                                0,
                            ),
                        )
                    )
            children.sort(key=lambda pair_: pair_[0])
            for _, child in children:
                queue.append(child)
            continue

        # ----- transition: node phase complete, compute source-edge images -----
        if imgs is None:
            node_map = [0] * n1
            for k, u in enumerate(pair.node_order):
                node_map[u] = assign[k]
            imgs = tuple(
                sum(1 << node_map[a] for a in members if node_map[a] != _NULL)
                for members in pair.e1_members
            )

        j_level = depth - n1
        if j_level == m1:
            total = edc + sum(1 + e2_cards[j] for j in range(m2) if not (used_e >> j) & 1)
            if total < best and (upper_bound is None or total <= upper_bound):
                best = total
                if best <= root_lb:
                    break
            continue

        # ----- edge phase -----
        i = pair.edge_order[j_level]
        card_i = e1_cards[i]
        li = pair.e1_labels[i]
        img = imgs[i]

        rem_src_lab = Counter(pair.e1_labels[pair.edge_order[k]] for k in range(j_level + 1, m1))
        rem_tgt_idx = [j for j in range(m2) if not (used_e >> j) & 1]
        rem_tgt_lab = Counter(pair.e2_labels[j] for j in rem_tgt_idx)
        base_common = sum(min(c, rem_tgt_lab[label]) for label, c in rem_src_lab.items())
        s_total = m1 - j_level - 1
        rem_src_cards = [e1_cards[pair.edge_order[k]] for k in range(j_level + 1, m1)]

        children = []
        for j in rem_tgt_idx:
            c = (li != pair.e2_labels[j]) + (
                card_i + e2_cards[j] - 2 * ((img & pair.e2_masks[j]).bit_count())
            )
            if edc + c > limit():
                continue
            lj = pair.e2_labels[j]
            common = base_common - (1 if 0 < rem_tgt_lab[lj] <= rem_src_lab.get(lj, 0) else 0)
            psi_edges = max(s_total, len(rem_tgt_idx) - 1) - common
            def6 = _def6(rem_src_cards, [e2_cards[q] for q in rem_tgt_idx if q != j])
            f_child = edc + c + psi_edges + def6
            if f_child <= limit():
                children.append(
                    (
                        c,
                        (
                            f_child,
                            depth + 1,
                            edc + c,
                            assign,
                            used_n,
                            nulls_n,
                            imgs,
                            used_e | (1 << j),
                            nulls_e,
                        ),
                    )
                )
        if nulls_e < pair.edge_null_quota:
            c = 1 + card_i
            psi_edges = max(s_total, len(rem_tgt_idx)) - base_common
            def6 = _def6(rem_src_cards, [e2_cards[q] for q in rem_tgt_idx])
            f_child = edc + c + psi_edges + def6
            if f_child <= limit():
                children.append(
                    (
                        c,
                        (
                            f_child,
                            depth + 1,
                            edc + c,
                            assign,
                            used_n,
                            nulls_n,
                            imgs,
                            used_e,
                            nulls_e + 1,
                        ),
                    )
                )
        children.sort(key=lambda pair_: pair_[0])
        for _, child in children:
            queue.append(child)

    return best


# ---------------------------------------------------------------------------
# Public distance
# ---------------------------------------------------------------------------


class QinHGED(HypergraphDistance):
    """Qin et al. (ICDE 2023) Hypergraph Edit Distance -- ``qin_hged``.

    The article's official HGED (Qin's empty-shell taxonomy: deleting a
    ``k``-node hyperedge costs ``k + 1``), computed exactly by the paper's own
    HGED-BFS algorithm. Same metric as :class:`ExactHGED` (the experiments'
    branch-and-bound oracle) -- this class is the paper-fidelity anchor and the
    thresholded-query solver; the two agree exactly wherever both terminate.

    Parameters
    ----------
    upper_bound : int or None, optional
        Strategy-2 clamp ``c̄dc``. When set, :meth:`pairwise` returns the exact
        HGED if it is ``<= upper_bound`` and ``math.inf`` otherwise -- the
        thresholded semantics of the paper's HEP use and its Table II regime.
        ``None`` (default) runs to unclamped optimality (sample-mapping seeds).
    timeout : float or None, optional
        Wall-clock budget per :meth:`pairwise` call; exceeding it raises
        :class:`HGEDComputationError`.
    max_expansions : int or None, optional
        Cap on BFS state expansions per call; exceeding it raises
        :class:`HGEDComputationError`.
    """

    def __init__(
        self,
        *,
        upper_bound: int | None = None,
        timeout: float | None = None,
        max_expansions: int | None = None,
    ) -> None:
        self._upper_bound = upper_bound
        self._timeout = timeout
        self._max_expansions = max_expansions

    @property
    def name(self) -> DistanceName:
        return "qin_hged"

    def pairwise(self, H1: SparseHypergraph, H2: SparseHypergraph) -> float:
        assert_vocab_compatible(H1, H2)
        return float(
            _hged_bfs(
                _prepare(H1, H2),
                upper_bound=self._upper_bound,
                timeout=self._timeout,
                max_expansions=self._max_expansions,
            )
        )


register_distance("qin_hged", QinHGED)
