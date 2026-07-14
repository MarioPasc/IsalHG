"""Evaluate the Prop-6.0 coherence criterion over the w*_c search (T-TBb, D2).

Analytical T-B3 asks whether the Fano/STS(9)-coherent vs STS(13)/GQ(2,2)-
incoherent classification follows from the stabiliser-transitivity criterion
of ``theorem_a_completeness.tex`` Proposition 6.0 alone, with no appeal to the
T-TAa string-equality measurements. This script computes the criterion
exactly:

1. enumerate ``Aut(H)`` by structure-pruned backtracking (design groups are
   small: Fano 168, STS(9) 432, cyclic-13 39, GQ(2,2) 720);
2. audit the tie-complete search tree, mirroring the step selection of
   ``isalhg.core.hypergraph_to_string._encode_from`` (displacement-cost-first
   cascade), exploring one representative per stabiliser orbit of each tie
   (sound: automorphic branches have isomorphic subtree tie structure, so the
   orbit-pruned tree meets every reachable tie up to ``Aut(H)``);
3. at each V step compute the pointwise stabiliser of ``dom(mu)`` (the
   introduced input vertices) and its orbits on (a) the tied candidate edges
   and (b) the label-respecting orderings of the chosen branch's new inputs.

A tie whose candidates split into more than one stabiliser orbit is
*incoherent* -- Prop. 6.0's hypothesis fails there. The criterion is
sufficient-only: an incoherent tie does NOT imply diverging branch
completions, so the script additionally checks, at the first incoherent edge
tie on the min-id path, whether the per-branch lex-min completions actually
differ (this supplementary check uses string comparison and is reported
separately from the criterion-only classification).
"""

from __future__ import annotations

from typing import Any

from isalhg.core.cdll import CircularDoublyLinkedList
from isalhg.core.hypergraph_to_string import (
    _best_c_for_displacement,
    _best_v_for_displacement,
    _displaced_slot,
    _encode_from,
    _enum_displacements,
    _label_respecting_perms,
    _movement_tokens,
    _State,
    _tied_v_candidates,
)
from isalhg.core.instructions import Token, TokenC, TokenV, sequence_sort_key
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.core.structural_tuples import max_neighbor_degree_nodes
from isalhg.datasets.synthetic import designs
from isalhg.errors import CanonicalizationTimeoutError
from isalhg.types import EdgeId, NodeId

Perm = tuple[int, ...]

AUDIT_BUDGET: int = 200_000
COMPLETION_BUDGET: int = 2_000_000


# ---------------------------------------------------------------------------
# Automorphism enumeration (backtracking, edge-set consistency pruning)
# ---------------------------------------------------------------------------


def automorphisms(H: SparseHypergraph) -> list[Perm]:
    """Enumerate ``Aut(H)`` as vertex permutations (image tuples).

    Backtracking on vertex images with degree and partial-edge pruning.
    Vertices are assigned in a constraint-first order (each next vertex
    maximises the number of its edges fully inside the ordered prefix), so
    edge-consistency prunes as early as possible. Feasible for the design
    fixtures (n <= 15, |Aut| <= 720).
    """
    n = H.n_nodes
    edge_sets = frozenset(frozenset(m) for _, m, _ in H.iter_edges())
    incident: list[list[frozenset[NodeId]]] = [[] for _ in range(n)]
    for _, members, _ in H.iter_edges():
        for v in members:
            incident[v].append(frozenset(members))
    degree = [len(incident[v]) for v in range(n)]

    order: list[int] = []
    placed: set[int] = set()
    while len(order) < n:
        best_v, best_score = -1, (-1, -1)
        for v in range(n):
            if v in placed:
                continue
            complete = sum(1 for mem in incident[v] if all(u in placed or u == v for u in mem))
            score = (complete, degree[v])
            if score > best_score:
                best_v, best_score = v, score
        order.append(best_v)
        placed.add(best_v)

    out: list[Perm] = []
    image: list[int] = [-1] * n
    used = [False] * n

    def consistent(v: int) -> bool:
        for members in incident[v]:
            if (
                all(image[u] >= 0 for u in members)
                and frozenset(image[u] for u in members) not in edge_sets
            ):
                return False
        return True

    def backtrack(d: int) -> None:
        if d == n:
            out.append(tuple(image))
            return
        v = order[d]
        for w in range(n):
            if used[w] or degree[w] != degree[v]:
                continue
            image[v] = w
            used[w] = True
            if consistent(v):
                backtrack(d + 1)
            image[v] = -1
            used[w] = False

    backtrack(0)
    return out


def pointwise_stabilizer(group: list[Perm], fixed: set[int]) -> list[Perm]:
    return [g for g in group if all(g[v] == v for v in fixed)]


def edge_orbit_reps(
    group: list[Perm],
    tied: list[tuple[EdgeId, frozenset[NodeId]]],
    members_of: dict[EdgeId, frozenset[NodeId]],
) -> list[list[tuple[EdgeId, frozenset[NodeId]]]]:
    """Partition tied candidates into stabiliser orbits (by member set)."""
    remaining = list(tied)
    orbits: list[list[tuple[EdgeId, frozenset[NodeId]]]] = []
    while remaining:
        eid0, ni0 = remaining[0]
        images = {frozenset(g[v] for v in members_of[eid0]) for g in group}
        this_orbit = [(e, ni) for (e, ni) in remaining if members_of[e] in images]
        remaining = [(e, ni) for (e, ni) in remaining if members_of[e] not in images]
        orbits.append(this_orbit)
    return orbits


def ordering_orbit_reps(
    group: list[Perm], orderings: list[tuple[NodeId, ...]]
) -> list[list[tuple[NodeId, ...]]]:
    remaining = list(orderings)
    orbits: list[list[tuple[NodeId, ...]]] = []
    while remaining:
        first = remaining[0]
        images = {tuple(g[v] for v in first) for g in group}
        orbits.append([o for o in remaining if o in images])
        remaining = [o for o in remaining if o not in images]
    return orbits


# ---------------------------------------------------------------------------
# Emission selection (mirrors _encode_from's per-state choice)
# ---------------------------------------------------------------------------


def select_emission(H: SparseHypergraph, k: int, state: _State) -> dict[str, Any] | None:
    """Return the winning emission at ``state`` (displacement-cost-first key)."""
    radius = max(0, len(state.i2o))
    best_key: tuple[Any, ...] | None = None
    best: dict[str, Any] | None = None
    for displacement in _enum_displacements(k, radius):
        cost = sum(abs(d) for d in displacement)
        if best_key is not None and cost + 1 > best_key[0]:
            break
        new_slots = tuple(
            _displaced_slot(state.cdll, state.get_ptr(i + 1), displacement[i]) for i in range(k)
        )
        tentative = [state.o2i[state.cdll.get_value(s)] for s in new_slots]
        move_block = _movement_tokens(displacement)
        move_keys = tuple(t.sort_key() for t in move_block)
        v_cand = _best_v_for_displacement(H, k, tentative, state)
        if v_cand is not None:
            (v_key, edge_id, i_v, j_v, le, new_labels, new_inputs) = v_cand
            tok: Token = TokenV(edge_label=le, i=i_v, j=j_v, new_node_labels=new_labels)
            ek = (len(move_block) + 1, move_keys + (tok.sort_key(),))
            if best_key is None or ek < best_key:
                best_key = ek
                best = {
                    "kind": "V",
                    "new_slots": new_slots,
                    "tentative": tentative,
                    "edge_id": edge_id,
                    "new_inputs": new_inputs,
                    "key_prefix": v_key[:-1],
                }
        c_cand = _best_c_for_displacement(H, k, tentative, state)
        if c_cand is not None:
            (_, edge_id_c, i_c, le_c) = c_cand
            tok_c: Token = TokenC(edge_label=le_c, i=i_c)
            ek_c = (len(move_block) + 1, move_keys + (tok_c.sort_key(),))
            if best_key is None or ek_c < best_key:
                best_key = ek_c
                best = {"kind": "C", "new_slots": new_slots, "edge_id": edge_id_c}
    return best


def apply_v_branch(
    state: _State, new_slots: tuple[int, ...], ordering: tuple[NodeId, ...], edge_id: EdgeId
) -> _State:
    """Clone ``state`` and apply the V emission with the given ordering."""
    sub = state.clone()
    sub.set_ptrs(new_slots)
    anchor = sub.get_ptr(1)
    for input_v in ordering:
        out_v = sub.next_output_id
        sub.next_output_id += 1
        anchor = sub.cdll.insert_after(anchor, out_v)
        sub.i2o[input_v] = out_v
        sub.o2i[out_v] = input_v
    sub.consumed_edges.add(edge_id)
    return sub


def initial_state(H: SparseHypergraph, k: int, seed_node: NodeId) -> _State:
    cdll = CircularDoublyLinkedList(capacity=max(1, H.n_nodes))
    seed_slot = cdll.insert_after(0, 0)
    return _State(
        cdll=cdll,
        pointers=[seed_slot] * k,
        i2o={seed_node: 0},
        o2i={0: seed_node},
        consumed_edges=set(),
        next_output_id=1,
    )


# ---------------------------------------------------------------------------
# Orbit-pruned full-tree audit
# ---------------------------------------------------------------------------


def audit_tree(H: SparseHypergraph, k: int, seed_node: NodeId, group: list[Perm]) -> dict[str, Any]:
    """Audit every reachable tie of the tie-complete search, up to Aut(H).

    Explores one representative per stabiliser orbit of every edge tie and of
    every ordering set (sound because automorphic branches have isomorphic
    subtrees). Records incoherent ties by depth; stops expanding a branch when
    the state budget is exhausted (reported as ``truncated``).
    """
    members_of = {eid: frozenset(m) for eid, m, _ in H.iter_edges()}
    stats: dict[str, Any] = {
        "states": 0,
        "truncated": False,
        "edge_incoherent_depths": {},
        "ordering_incoherent_depths": {},
    }

    def recurse(state: _State, depth: int) -> None:
        if len(state.consumed_edges) == H.n_edges:
            return
        if stats["states"] >= AUDIT_BUDGET:
            stats["truncated"] = True
            return
        stats["states"] += 1
        best = select_emission(H, k, state)
        if best is None:
            return
        if best["kind"] == "C":
            sub = state.clone()
            sub.set_ptrs(best["new_slots"])
            sub.consumed_edges.add(best["edge_id"])
            recurse(sub, depth + 1)
            return
        stab = pointwise_stabilizer(group, set(state.i2o))
        tied = _tied_v_candidates(H, k, best["tentative"], state, best["key_prefix"])
        e_orbits = edge_orbit_reps(stab, tied, members_of)
        if len(e_orbits) > 1:
            d = stats["edge_incoherent_depths"]
            d[depth + 1] = d.get(depth + 1, 0) + 1
        for orbit in e_orbits:
            eid, new_inputs = orbit[0]
            orderings = _label_respecting_perms(new_inputs, H)
            stab_edge = [
                g for g in stab if frozenset(g[v] for v in members_of[eid]) == members_of[eid]
            ]
            o_orbits = ordering_orbit_reps(stab_edge, orderings)
            if len(o_orbits) > 1:
                d = stats["ordering_incoherent_depths"]
                d[depth + 1] = d.get(depth + 1, 0) + 1
            for o_orbit in o_orbits:
                sub = apply_v_branch(state, best["new_slots"], o_orbit[0], eid)
                recurse(sub, depth + 1)

    recurse(initial_state(H, k, seed_node), 0)
    return stats


# ---------------------------------------------------------------------------
# Completion-divergence check at the first incoherent edge tie (min-id path)
# ---------------------------------------------------------------------------


def divergence_check(
    H: SparseHypergraph, k: int, seed_node: NodeId, group: list[Perm]
) -> dict[str, Any] | None:
    """Find the first incoherent edge tie on a representative path; compare branches.

    The path takes the min-id candidate at every tie and the first
    label-respecting ordering at every V emission; every state on it belongs
    to the tie-complete search tree (which branches over all orderings), so
    the tie found is reachable by construction. For one representative edge
    per stabiliser orbit the function computes the lex-min completion over its
    orderings (full tie-complete recursion) and reports whether the
    completions differ. This is the supplementary string-level check of
    Prop 6.0's converse -- NOT part of the criterion classification. Note the
    path is generally NOT the greedy encoder's trajectory: greedy's downstream
    min-edge-id tie-breaks are not automorphism-invariant, so its trajectory
    is id-dependent even across coherent ordering ties.
    """
    members_of = {eid: frozenset(m) for eid, m, _ in H.iter_edges()}
    state = initial_state(H, k, seed_node)
    depth = 0
    while len(state.consumed_edges) < H.n_edges:
        best = select_emission(H, k, state)
        if best is None:
            return None
        depth += 1
        if best["kind"] == "C":
            state.set_ptrs(best["new_slots"])
            state.consumed_edges.add(best["edge_id"])
            continue
        stab = pointwise_stabilizer(group, set(state.i2o))
        tied = _tied_v_candidates(H, k, best["tentative"], state, best["key_prefix"])
        e_orbits = edge_orbit_reps(stab, tied, members_of)
        if len(e_orbits) > 1:
            completions: list[tuple[Any, ...] | None] = []
            for orbit in e_orbits:
                eid, new_inputs = orbit[0]
                best_key = None
                for ordering in _label_respecting_perms(new_inputs, H):
                    sub = apply_v_branch(state, best["new_slots"], ordering, eid)
                    try:
                        comp = _encode_from(
                            H,
                            k,
                            sub,
                            tie_branch=True,
                            _counter=[0],
                            _max_expansions=COMPLETION_BUDGET,
                        )
                    except CanonicalizationTimeoutError:
                        comp = None
                    if comp is None:
                        continue
                    key = sequence_sort_key(list(comp))
                    if best_key is None or key < best_key:
                        best_key = key
                completions.append(best_key)
            distinct = len({c for c in completions if c is not None})
            return {
                "depth": depth,
                "n_orbits": len(e_orbits),
                "budget_exhausted": any(c is None for c in completions),
                "branches_diverge": distinct > 1,
            }
        # follow min-id representative; coherent tie => any representative
        eid, new_inputs = tied[0]
        ordering = _label_respecting_perms(new_inputs, H)[0]
        state = apply_v_branch(state, best["new_slots"], ordering, eid)
    return None


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def greedy_equality_robustness(
    H: SparseHypergraph, k: int, n_presentations: int, rng_base: int = 1000
) -> tuple[int, int]:
    """Count (presentation, seed) pairs where per-seed greedy != complete.

    Supplementary to the criterion audit: an incoherent tie with divergent
    branch completions exposes the greedy/complete comparison to the edge
    numbering, so robust equality across shuffled presentations indicates a
    mechanism beyond Prop 6.0's coherence (observed on STS(9), T-TBb).
    """
    import random

    from isalhg.core.hypergraph_to_string import _python_greedy_h2s

    edges = [m for _, m, _ in H.iter_edges()]
    n_pairs = 0
    n_diff = 0
    for trial in range(n_presentations):
        rng = random.Random(rng_base + trial)
        perm = edges[:]
        rng.shuffle(perm)
        H2 = SparseHypergraph(n_nodes=H.n_nodes, hyperedges=perm)
        for s in range(H.n_nodes):
            g = _python_greedy_h2s(H2, seed_node=s, k=k, tie_branch=False)
            c = _python_greedy_h2s(H2, seed_node=s, k=k, tie_branch=True)
            n_pairs += 1
            if g != c:
                n_diff += 1
    return n_diff, n_pairs


def main() -> None:
    cases: list[tuple[str, SparseHypergraph, int]] = [
        ("Fano plane", designs.fano_plane(), 3),
        ("STS(9)", designs.sts_9(), 3),
        ("cyclic-13 {0,1,4}", designs.cyclic_sts_13((0, 1, 4)), 3),
        ("GQ(2,2) doily", designs.gq_2_2_doily(), 3),
    ]
    for name, H, k in cases:
        group = automorphisms(H)
        seeds = max_neighbor_degree_nodes(H)
        seed = min(seeds)
        stats = audit_tree(H, k, seed, group)
        ei = stats["edge_incoherent_depths"]
        oi = stats["ordering_incoherent_depths"]
        print(
            f"{name}: |Aut|={len(group)} |S(H)|={len(seeds)} m={H.n_edges} "
            f"audited_states={stats['states']}"
            f"{' (TRUNCATED)' if stats['truncated'] else ''}",
            flush=True,
        )
        print(
            f"    edge-incoherent ties by depth:     {ei if ei else 'none'}",
            flush=True,
        )
        print(
            f"    ordering-incoherent ties by depth: {oi if oi else 'none'}",
            flush=True,
        )
        div = divergence_check(H, k, seed, group)
        if div is None:
            print(
                "    divergence check: no incoherent edge tie on the representative path",
                flush=True,
            )
        else:
            print(
                f"    divergence check @ depth {div['depth']}: "
                f"{div['n_orbits']} orbits, branches_diverge={div['branches_diverge']}"
                f"{' (budget exhausted)' if div['budget_exhausted'] else ''}",
                flush=True,
            )
        if name == "STS(9)":
            n_diff, n_pairs = greedy_equality_robustness(H, k, n_presentations=8)
            print(
                f"    greedy-equality robustness: per-seed greedy != complete on "
                f"{n_diff}/{n_pairs} (presentation, seed) pairs",
                flush=True,
            )


if __name__ == "__main__":
    main()
