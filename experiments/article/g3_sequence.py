"""G3 — One-Factor-At-a-Time (OFAT) sequence generator (T-M7f).

Produces hypergraph sequences H_0..H_T from a Stratum A design base,
varying exactly one structural knob per axis.  Every step records the
accumulated Qin-cost budget so the experiment is HGED-free (the budget
is an upper bound on HGED by construction).

Five axes:
  M1 — vertex growth      V-like op: insert vertex + connecting edge
  M2 — densification      C-like op: insert edge over existing vertices
  M3 — arity increase     add_incidence to one target edge per step
  M4 — incidence edit     alternating add/remove vertex–edge incidences
  M5 — symmetry break     random connectivity-preserving edit on high-symmetry base

Usage::

    import random
    from isalhg.datasets.synthetic.designs import fano_plane
    from experiments.article.g3_sequence import OfatAxis, generate_ofat_sequence

    H0 = fano_plane()
    steps = generate_ofat_sequence(H0, OfatAxis.M2, T=10, rng=random.Random(42))
    for s in steps:
        print(s.step, s.budget_from_base, s.op_name, s.hypergraph.n_nodes)

Invariants (asserted in tests/unit/experiments_article/test_g3_sequence.py):
  - AC1: budget_from_base is non-negative and non-decreasing; step 0 = 0.
  - AC2: every H_t is connected.
  - AC3: M2 holds n fixed across all steps.
  - AC4: M3 changes exactly one edge's arity per step (+1 to total incidence count).
  - AC5: canonical_string(s2h(canonical_string(H_t))) == canonical_string(H_t).
  - AC6: M1 grows n by exactly 1 per step.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from isalhg.core.sparse_hypergraph import (
    SparseHypergraph,
    add_incidence,
    insert_hyperedge,
    insert_vertex,
    qin_edit_cost,
    random_connected_edit,
    remove_incidence,
)

# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


class OfatAxis(StrEnum):
    """The five OFAT move axes."""

    M1 = "M1_vertex_growth"
    M2 = "M2_densification"
    M3 = "M3_arity_increase"
    M4 = "M4_incidence_edit"
    M5 = "M5_symmetry_break"


@dataclass(frozen=True)
class OfatStep:
    """One step in an OFAT sequence.

    Parameters
    ----------
    step : int
        Index (0 = base, t = t-th step).
    hypergraph : SparseHypergraph
        Hypergraph at this step.
    budget_from_base : int
        Accumulated Qin-cost from the base (H_0). HGED(H_0, H_t) <= budget.
    op_name : str
        Name of the operation applied to reach this step (empty for step 0).
    """

    step: int
    hypergraph: SparseHypergraph
    budget_from_base: int
    op_name: str


# ---------------------------------------------------------------------------
# Axis generators
# ---------------------------------------------------------------------------


def _m1_step(H: SparseHypergraph, rng: random.Random) -> tuple[SparseHypergraph, str]:
    """M1 — insert one vertex and one new 2-edge connecting it to an existing vertex.

    This mirrors the V-instruction: a new node is created and immediately
    connected into the structure, preserving connectivity.  The connecting
    edge uses the minimum arity (2) so the k-profile is not changed.

    Returns
    -------
    tuple[SparseHypergraph, str]
        (new hypergraph, op name)
    """
    new_v = H.n_nodes  # id of the soon-to-be-added vertex
    # Pick a random existing vertex to connect to.
    anchor = rng.randrange(H.n_nodes)
    H1 = insert_vertex(H, 0)
    H2 = insert_hyperedge(H1, frozenset({anchor, new_v}))
    return H2, "insert_vertex_and_edge"


def _m2_step(
    H: SparseHypergraph,
    rng: random.Random,
    arity: int | None = None,
    max_tries: int = 200,
) -> tuple[SparseHypergraph, str] | None:
    """M2 — insert one edge over existing vertices.

    The edge arity matches the base's uniform arity when ``arity`` is given;
    otherwise a size in [2, n_nodes] is sampled.

    Returns ``None`` when no valid edge is found within ``max_tries``
    (e.g. the complete hypergraph has been reached for this arity).
    """
    n = H.n_nodes
    if n < 2:
        return None
    k = arity if arity is not None else max(len(H.members(e)) for e in range(H.n_edges))
    k = min(k, n)
    for _ in range(max_tries):
        size = k if k <= n else rng.randint(2, n)
        subset = frozenset(rng.sample(range(n), size))
        label = 0  # trivial vocabulary
        if not H.has_edge(subset, label):
            H2 = insert_hyperedge(H, subset, label)
            return H2, "insert_hyperedge"
    return None


def _m3_step(
    H: SparseHypergraph,
    target_edge: int,
    rng: random.Random,
) -> tuple[SparseHypergraph, int, str] | None:
    """M3 — add one incidence to *target_edge*, growing its arity by 1.

    Returns ``(new_H, new_target, op_name)`` where ``new_target`` is the
    edge id of the grown edge in the new hypergraph (same id since we only
    modify in-place via add_incidence).  Returns ``None`` when the target
    edge already spans all vertices (the sequence terminates early).
    """
    members = H.members(target_edge)
    outside = [v for v in range(H.n_nodes) if v not in members]
    if not outside:
        # Edge spans all vertices; try to find another growable edge.
        for e in range(H.n_edges):
            if e == target_edge:
                continue
            m2 = H.members(e)
            out2 = [v for v in range(H.n_nodes) if v not in m2]
            if out2:
                v = rng.choice(out2)
                label = H.edge_label(e)
                new_set = m2 | {v}
                if not H.has_edge(new_set, label):
                    H2 = add_incidence(H, v, e)
                    return H2, e, "add_incidence"
        return None
    v = rng.choice(outside)
    label = H.edge_label(target_edge)
    new_set = members | {v}
    if H.has_edge(new_set, label):
        # Would duplicate; try another vertex.
        rng.shuffle(outside)
        for u in outside:
            nset = members | {u}
            if not H.has_edge(nset, label):
                H2 = add_incidence(H, u, target_edge)
                return H2, target_edge, "add_incidence"
        return None
    H2 = add_incidence(H, v, target_edge)
    return H2, target_edge, "add_incidence"


def _m4_step(
    H: SparseHypergraph,
    step: int,
    rng: random.Random,
    max_tries: int = 50,
) -> tuple[SparseHypergraph, str] | None:
    """M4 — one vertex–edge incidence edit (add or remove), connectivity-preserving.

    Alternates add/remove for variety; falls back to the other direction if
    the chosen direction fails.  Uses remove_incidence only when the edge
    has arity >= 2 (to avoid emptying edges).
    """
    # Try both directions, preferring alternation.
    for prefer_add in [step % 2 == 0, step % 2 == 1]:
        if prefer_add:
            # add_incidence: pick a random edge and a random vertex not in it.
            for _ in range(max_tries):
                if H.n_edges == 0:
                    break
                e = rng.randrange(H.n_edges)
                members = H.members(e)
                outside = [v for v in range(H.n_nodes) if v not in members]
                if not outside:
                    continue
                v = rng.choice(outside)
                label = H.edge_label(e)
                if not H.has_edge(members | {v}, label):
                    H2 = add_incidence(H, v, e)
                    return H2, "add_incidence"
        else:
            # remove_incidence: pick a random edge with arity >= 2 and a random vertex in it.
            big_edges = [e for e in range(H.n_edges) if len(H.members(e)) >= 2]
            if not big_edges:
                continue
            for _ in range(max_tries):
                e = rng.choice(big_edges)
                members = H.members(e)
                v = rng.choice(tuple(members))
                label = H.edge_label(e)
                if not H.has_edge(members - {v}, label):
                    H2 = remove_incidence(H, v, e)
                    if H2.is_connected():
                        return H2, "remove_incidence"
    return None


def _m5_step(
    H: SparseHypergraph,
    rng: random.Random,
    max_arity: int | None = None,
) -> tuple[SparseHypergraph, str]:
    """M5 — one random connectivity-preserving edit (symmetry break).

    Delegates to random_connected_edit which preserves connectivity and
    optionally bounds the max arity.  On a high-symmetry base (e.g. GQ(2,2))
    this probes the avalanche regime of the canonical encoder.
    """
    return random_connected_edit(H, rng, max_arity=max_arity)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def generate_ofat_sequence(
    H_0: SparseHypergraph,
    axis: OfatAxis,
    T: int,
    rng: random.Random,
    *,
    max_arity: int | None = None,
) -> list[OfatStep]:
    """Generate an OFAT sequence H_0..H_T for the given axis.

    Parameters
    ----------
    H_0 : SparseHypergraph
        Connected base hypergraph (must satisfy H_0.is_connected()).
    axis : OfatAxis
        Which structural axis to vary.
    T : int
        Number of steps (sequence length = T + 1, including the base).
    rng : random.Random
        Seeded RNG.  Caller pins and reports the seed.
    max_arity : int or None
        Maximum hyperedge arity.  When None, no bound is imposed (M1/M2/M5
        use the base's max arity implicitly; M3 terminates when all edges
        are fully grown).

    Returns
    -------
    list[OfatStep]
        Steps indexed 0..min(T, achievable). Step 0 is the base with
        budget_from_base=0. Sequences may terminate before T if the axis
        is exhausted (e.g. M2 reaches the complete graph, M3 fully grows
        all edges).

    Raises
    ------
    ValueError
        If H_0 is not connected or T < 0.
    """
    if not H_0.is_connected():
        raise ValueError("H_0 must be connected")
    if T < 0:
        raise ValueError(f"T must be >= 0, got {T}")

    steps: list[OfatStep] = [OfatStep(0, H_0, 0, "")]

    if axis == OfatAxis.M1:
        _fill_m1(steps, T, rng)
    elif axis == OfatAxis.M2:
        base_k = max_arity or (
            max(len(H_0.members(e)) for e in range(H_0.n_edges)) if H_0.n_edges > 0 else 3
        )
        _fill_m2(steps, T, rng, base_k)
    elif axis == OfatAxis.M3:
        # Target edge: largest arity edge; break ties by smallest edge id.
        target_e = (
            max(
                range(H_0.n_edges),
                key=lambda e: len(H_0.members(e)),
            )
            if H_0.n_edges > 0
            else 0
        )
        _fill_m3(steps, T, rng, target_e)
    elif axis == OfatAxis.M4:
        _fill_m4(steps, T, rng)
    elif axis == OfatAxis.M5:
        base_k = max_arity or (
            max(len(H_0.members(e)) for e in range(H_0.n_edges)) if H_0.n_edges > 0 else 3
        )
        _fill_m5(steps, T, rng, base_k)
    else:
        raise ValueError(f"Unknown axis: {axis}")

    return steps


# ---------------------------------------------------------------------------
# Internal fill routines
# ---------------------------------------------------------------------------


def _fill_m1(
    steps: list[OfatStep],
    T: int,
    rng: random.Random,
) -> None:
    for _ in range(T):
        prev = steps[-1]
        H_new, op = _m1_step(prev.hypergraph, rng)
        budget = prev.budget_from_base + qin_edit_cost(prev.hypergraph, H_new)
        steps.append(OfatStep(len(steps), H_new, budget, op))


def _fill_m2(
    steps: list[OfatStep],
    T: int,
    rng: random.Random,
    base_k: int,
) -> None:
    for _ in range(T):
        prev = steps[-1]
        result = _m2_step(prev.hypergraph, rng, arity=base_k)
        if result is None:
            # Complete graph reached for this arity; sequence terminates.
            break
        H_new, op = result
        budget = prev.budget_from_base + qin_edit_cost(prev.hypergraph, H_new)
        steps.append(OfatStep(len(steps), H_new, budget, op))


def _fill_m3(
    steps: list[OfatStep],
    T: int,
    rng: random.Random,
    target_edge: int,
) -> None:
    current_target = target_edge
    for _ in range(T):
        prev = steps[-1]
        result = _m3_step(prev.hypergraph, current_target, rng)
        if result is None:
            break
        H_new, current_target, op = result
        budget = prev.budget_from_base + qin_edit_cost(prev.hypergraph, H_new)
        steps.append(OfatStep(len(steps), H_new, budget, op))


def _fill_m4(
    steps: list[OfatStep],
    T: int,
    rng: random.Random,
) -> None:
    for i in range(T):
        prev = steps[-1]
        result = _m4_step(prev.hypergraph, i, rng)
        if result is None:
            break
        H_new, op = result
        budget = prev.budget_from_base + qin_edit_cost(prev.hypergraph, H_new)
        steps.append(OfatStep(len(steps), H_new, budget, op))


def _fill_m5(
    steps: list[OfatStep],
    T: int,
    rng: random.Random,
    base_k: int,
) -> None:
    for _ in range(T):
        prev = steps[-1]
        H_new, op = _m5_step(prev.hypergraph, rng, max_arity=base_k)
        budget = prev.budget_from_base + qin_edit_cost(prev.hypergraph, H_new)
        steps.append(OfatStep(len(steps), H_new, budget, op))


# ---------------------------------------------------------------------------
# S2H round-trip utility (used in tests and analysis)
# ---------------------------------------------------------------------------


def verify_s2h_roundtrip(H: SparseHypergraph) -> bool:
    """Return True iff canonical_string(s2h(canonical_string(H))) == canonical_string(H).

    This is the G3 decodability check: the canonical form encodes H as a string,
    S2H decodes that string back to a hypergraph, and re-encoding that hypergraph
    must yield the same canonical string.  Because the alphabet is closed (S2H
    never rejects a valid Sigma_HG* string), this is guaranteed by Theorem A —
    this function makes it measurable per step.

    Parameters
    ----------
    H : SparseHypergraph
        A connected hypergraph with n >= 1.

    Returns
    -------
    bool
        True on round-trip success (always expected; False signals a defect).
    """
    from isalhg.core.canonical import canonical_string
    from isalhg.core.string_to_hypergraph import string_to_hypergraph

    w = canonical_string(H)
    k = max(len(H.members(e)) for e in range(H.n_edges)) if H.n_edges > 0 else 2
    H2 = string_to_hypergraph(w, k=k)
    w2 = canonical_string(H2)
    return w == w2


def sequence_roundtrip_results(steps: list[OfatStep]) -> list[dict[str, Any]]:
    """Return per-step round-trip results for all steps in a sequence.

    Parameters
    ----------
    steps : list[OfatStep]
        Output of :func:`generate_ofat_sequence`.

    Returns
    -------
    list[dict]
        One dict per step with keys: step, ok, n_nodes, n_edges.
    """
    results = []
    for s in steps:
        ok = verify_s2h_roundtrip(s.hypergraph)
        results.append(
            {
                "step": s.step,
                "ok": ok,
                "n_nodes": s.hypergraph.n_nodes,
                "n_edges": s.hypergraph.n_edges,
            }
        )
    return results
