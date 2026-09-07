"""H2S greedy encoder with bounded backtracking on new-input orderings.

Greedy traversal of an input hypergraph that emits the ``Sigma_HG*`` token
sequence which, under :func:`isalhg.core.string_to_hypergraph`, reproduces
an isomorphic hypergraph. The tie-breaking cascade is mandatory (invariant
5 in ``CLAUDE.md``):

1. minimise total displacement cost ``Sigma |delta_i|``;
2. for the displacement block, emit movement tokens in lex-min order
   (``N[1], N[1], N[2], ..., P[1], ..., P[k]``);
3. prefer ``V`` over ``C`` at equal displacement cost;
4. lex-min on ``(i, j)`` (V) / ``(i,)`` (C);
5. lex-min on edge label ``ell_e``;
6. lex-min on new-node label tuple (V only);
7. lex-min on ``eta(e)``.

Iso-equivariance requires one more refinement: when a ``V`` token is
chosen, the *assignment* of input vertices to the ``j`` new output slots
admits permutations within each label class. The encoder enumerates those
permutations and recurses, taking the lex-min completion. For trivial
vocabularies the branching factor at each ``V`` step is ``j!`` (typically
``<= 6`` for v1 hypergraphs); displacement and edge selection are not
branched, so the worst-case complexity is product of ``j!`` over emissions.

The cascade does NOT make the default single-branch encoder a function of
the abstract hypergraph: distinct edges can tie through the full cascade
key ``(i, j, edge_label, new_node_labels, eta)``, and the residual tie is
broken by raw edge id (insertion order). The greedy string is therefore a
function of the *presentation* (vertex ids + edge insertion order); two
edge orderings of the same hypergraph can produce different strings
(counterexample pinned in ``tests/unit/core/test_canonical.py``).
Passing ``tie_branch=True`` to :func:`_python_greedy_h2s` instead recurses
over *every* cascade-tied candidate and keeps the lex-min completion,
which removes edge ids from observable behaviour and makes the per-seed
output isomorphism-equivariant (Theorem A, metric-space article). The
``canonical`` algorithm variant exposes this mode.

Two hooks alter *which* branches the tie-complete search explores without
altering what it returns or how it decides:

- ``orbit_oracle`` prunes the branch set to one representative per
  stabiliser orbit. Automorphic branches provably return equal completions,
  so the shortlex minimum is unchanged: the emitted tokens are the unpruned
  ones bit for bit. Only honoured together with ``tie_branch=True``.
- ``ranks`` replaces the residual edge-id tie-break by a canonical rank key
  and the label-respecting orderings by the single ``(label, rank)`` order.
  That is a *different* canonical program (``canonical_rank``), not a
  pruning of this one; it is mutually exclusive with ``tie_branch=True``.

Neither hook exists on the C++ path; requesting one there raises rather than
silently running the unhooked search.

Disconnected hypergraphs are rejected by :func:`isalhg.core.canonical.canonical_string`,
not here.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from functools import lru_cache
from itertools import permutations, product
from typing import Any

from isalhg.core.cdll import CircularDoublyLinkedList
from isalhg.core.instructions import (
    Token,
    TokenC,
    TokenN,
    TokenP,
    TokenV,
    sequence_sort_key,
    serialize,
)
from isalhg.core.orbit_oracle import OrbitOracle
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.core.structural_tuples import eta
from isalhg.errors import CanonicalizationTimeoutError, IsalHGError
from isalhg.types import EdgeId, NodeId, TokenSequence


class H2SStuckError(IsalHGError):
    """Raised when the encoder cannot emit a token from a non-terminal state."""


# ---------------------------------------------------------------------------
# Displacement enumeration
# ---------------------------------------------------------------------------


@lru_cache(maxsize=32)
def _enum_displacements(k: int, radius: int) -> tuple[tuple[int, ...], ...]:
    """All ``k``-tuples in ``[-radius, radius]^k`` sorted by ``(sum|d|, |d|, d)``.

    A pure function of ``(k, radius)`` that the encoder calls once per search
    frame, so it is memoised. The result is shared across callers and must be
    treated as read-only; it is only ever iterated. Returning a tuple rather
    than a list makes that immutability structural.

    ``radius`` only ever ranges over ``0..n``, so a cache of 32 covers a whole
    encoding of any hypergraph these corpora contain without thrashing, and
    bounds what is retained to roughly twice the largest table -- the table the
    uncached code would have rebuilt at every frame anyway.
    """
    if radius <= 0:
        return ((0,) * k,)
    rng = range(-radius, radius + 1)
    tuples = list(product(*([rng] * k)))
    tuples.sort(key=lambda t: (sum(abs(d) for d in t), tuple(abs(d) for d in t), t))
    return tuple(tuples)


def _movement_tokens(displacement: tuple[int, ...]) -> list[Token]:
    """Render a displacement vector as a lex-min movement-token block.

    Order: ``N[1]^*, N[2]^*, ..., N[k]^*, P[1]^*, ..., P[k]^*`` -- matches
    ``Token.sort_key()`` ordering (N rank < P rank, then i ascending).
    """
    out: list[Token] = []
    for i, d in enumerate(displacement, start=1):
        if d < 0:
            out.extend([TokenN(i=i)] * (-d))
    for i, d in enumerate(displacement, start=1):
        if d > 0:
            out.extend([TokenP(i=i)] * d)
    return out


def _displaced_slot(cdll: CircularDoublyLinkedList, start: int, delta: int) -> int:
    s = start
    if delta > 0:
        for _ in range(delta):
            s = cdll.next_node(s)
    elif delta < 0:
        for _ in range(-delta):
            s = cdll.prev_node(s)
    return s


# ---------------------------------------------------------------------------
# Encoder state (clonable for backtracking)
# ---------------------------------------------------------------------------


@dataclass
class _State:
    cdll: CircularDoublyLinkedList
    pointers: list[int]  # raw positions, k entries; 0-indexed
    i2o: dict[NodeId, NodeId]
    o2i: dict[NodeId, NodeId]
    consumed_edges: set[EdgeId]
    next_output_id: NodeId

    def clone(self) -> _State:
        return _State(
            cdll=self.cdll.clone(),
            pointers=list(self.pointers),
            i2o=dict(self.i2o),
            o2i=dict(self.o2i),
            consumed_edges=set(self.consumed_edges),
            next_output_id=self.next_output_id,
        )

    def get_ptr(self, i_1based: int) -> int:
        return self.pointers[i_1based - 1]

    def set_ptrs(self, new_slots: tuple[int, ...]) -> None:
        self.pointers[:] = list(new_slots)

    def placed_inputs(self) -> tuple[NodeId, ...]:
        """Return ``dom mu``: placed input ids in creation (output-id) order.

        Output ids are handed out contiguously from ``0`` (the seed), so
        enumerating ``range(next_output_id)`` walks the placement order both
        under clone-on-branch and under the in-place undo log.
        """
        return tuple(self.o2i[o] for o in range(self.next_output_id))


# ---------------------------------------------------------------------------
# Candidate finders
# ---------------------------------------------------------------------------


def _iter_v_candidates(
    H: SparseHypergraph,
    k: int,
    tentative_inputs: list[NodeId],
    state: _State,
) -> Iterator[tuple[tuple[Any, ...], EdgeId, int, int, int, tuple[int, ...], frozenset[NodeId]]]:
    """Yield every applicable V candidate at this displacement.

    Yields ``(key_prefix, edge_id, i, j, edge_label, new_labels,
    new_inputs_set)`` where ``key_prefix = (i, j, edge_label, new_labels,
    eta)`` is the iso-invariant part of the cascade key (invariant 5);
    the edge id is deliberately excluded from it.
    """
    for edge_id, members, edge_label in H.iter_edges():
        if edge_id in state.consumed_edges:
            continue
        arity = len(members)
        if arity < 2 or arity > k:
            continue
        longest_prefix = 0
        seen_prefix: set[NodeId] = set()
        for idx in range(min(k, arity)):
            v = tentative_inputs[idx]
            if v in members and v not in seen_prefix:
                seen_prefix.add(v)
                longest_prefix = idx + 1
            else:
                break
        if longest_prefix < 1:
            continue
        for i_val in range(1, longest_prefix + 1):
            j_val = arity - i_val
            if j_val < 1 or i_val + j_val > k or j_val > k - 1 or i_val > k - 1:
                continue
            pointed = set(tentative_inputs[:i_val])
            new_inputs = members - pointed
            if any(v in state.i2o for v in new_inputs):
                continue
            new_labels = tuple(sorted(H.vertex_label(v) for v in new_inputs))
            edge_eta = eta(H, edge_id)
            key_prefix = (i_val, j_val, edge_label, new_labels, edge_eta)
            yield (
                key_prefix,
                edge_id,
                i_val,
                j_val,
                edge_label,
                new_labels,
                frozenset(new_inputs),
            )


def _rank_tiebreak(
    new_inputs: frozenset[NodeId],
    pointed: tuple[NodeId, ...],
    ranks: Sequence[int],
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Residual V tie-break key from canonical ranks.

    ``(sorted ranks of the unplaced members, sorted ranks of the placed
    members)``. Ranks are a permutation of the vertices, and at a fixed
    displacement two tied candidates share their placed prefix, so distinct
    edges receive distinct keys: the tie set collapses to a singleton.
    """
    return (
        tuple(sorted(ranks[v] for v in new_inputs)),
        tuple(sorted(ranks[v] for v in pointed)),
    )


def _best_v_for_displacement(
    H: SparseHypergraph,
    k: int,
    tentative_inputs: list[NodeId],
    state: _State,
    ranks: Sequence[int] | None = None,
) -> tuple[tuple[Any, ...], EdgeId, int, int, int, tuple[int, ...], frozenset[NodeId]] | None:
    """Return the lex-min V candidate at this displacement, or None.

    Returns ``(cascade_key, edge_id, i, j, edge_label, new_labels, new_inputs_set)``
    where ``cascade_key = key_prefix + (residual,)``. The residual is the raw
    edge id (NOT iso-invariant; see the module docstring) unless ``ranks`` is
    supplied, in which case it is :func:`_rank_tiebreak`.
    The new-input ordering is left to the caller (branching point).
    """
    best: (
        tuple[tuple[Any, ...], EdgeId, int, int, int, tuple[int, ...], frozenset[NodeId]] | None
    ) = None
    for key_prefix, edge_id, i_val, j_val, edge_label, new_labels, new_inputs in _iter_v_candidates(
        H, k, tentative_inputs, state
    ):
        residual: Any = edge_id
        if ranks is not None:
            residual = _rank_tiebreak(new_inputs, tuple(tentative_inputs[:i_val]), ranks)
        key = key_prefix + (residual,)
        if best is None or key < best[0]:
            best = (key, edge_id, i_val, j_val, edge_label, new_labels, new_inputs)
    return best


def _tied_v_candidates(
    H: SparseHypergraph,
    k: int,
    tentative_inputs: list[NodeId],
    state: _State,
    key_prefix: tuple[Any, ...],
) -> list[tuple[EdgeId, frozenset[NodeId]]]:
    """All ``(edge_id, new_inputs_set)`` whose cascade key-prefix equals ``key_prefix``.

    The returned list is the full residual tie set the default encoder
    resolves by min edge id; the tie-branching mode recurses over every
    element so the result is independent of edge insertion order.
    """
    return sorted(
        (
            (edge_id, new_inputs)
            for kp, edge_id, _, _, _, _, new_inputs in _iter_v_candidates(
                H, k, tentative_inputs, state
            )
            if kp == key_prefix
        ),
        key=lambda t: t[0],
    )


def _best_c_for_displacement(
    H: SparseHypergraph,
    k: int,
    tentative_inputs: list[NodeId],
    state: _State,
) -> tuple[tuple[Any, ...], EdgeId, int, int] | None:
    best: tuple[tuple[Any, ...], EdgeId, int, int] | None = None
    for edge_id, members, edge_label in H.iter_edges():
        if edge_id in state.consumed_edges:
            continue
        arity = len(members)
        if arity > k:
            continue
        if any(v not in state.i2o for v in members):
            continue
        first_arity = tentative_inputs[:arity]
        if set(first_arity) != members or len(set(first_arity)) != arity:
            continue
        edge_eta = eta(H, edge_id)
        key = (arity, edge_label, edge_eta, edge_id)
        if best is None or key < best[0]:
            best = (key, edge_id, arity, edge_label)
    return best


def _label_respecting_perms(
    new_inputs_set: frozenset[NodeId],
    H: SparseHypergraph,
) -> list[tuple[NodeId, ...]]:
    """All orderings of ``new_inputs_set`` consistent with the sorted label tuple.

    Smaller labels first; within a label class, all permutations are emitted.
    """
    by_label: dict[int, list[NodeId]] = defaultdict(list)
    for v in new_inputs_set:
        by_label[H.vertex_label(v)].append(v)
    sorted_labels = sorted(by_label.keys())
    groups = [by_label[lab] for lab in sorted_labels]
    out: list[tuple[NodeId, ...]] = []
    for prod_perm in product(*[permutations(g) for g in groups]):
        out.append(tuple(v for group in prod_perm for v in group))
    return out


# ---------------------------------------------------------------------------
# Main recursive encoder
# ---------------------------------------------------------------------------


def _encode_from(
    H: SparseHypergraph,
    k: int,
    state: _State,
    *,
    inplace: bool = False,
    tie_branch: bool = False,
    orbit_oracle: OrbitOracle | None = None,
    ranks: Sequence[int] | None = None,
    stats: dict[str, int] | None = None,
    _counter: list[int] | None = None,
    _max_expansions: int | None = None,
) -> TokenSequence | None:
    """Recursive lex-min completion from ``state``. Returns ``None`` if stuck.

    Parameters
    ----------
    inplace : bool, optional
        When ``True`` mutate ``state`` directly at each branch and undo
        on return instead of cloning. Equivalent output; lower per-branch
        cost. Default ``False`` (clone-on-branch, identical to the
        original behaviour).
    tie_branch : bool, optional
        When ``True``, recurse over *every* V candidate tying on the
        iso-invariant cascade key-prefix instead of committing to the
        min-edge-id one, and keep the lex-min completion. Removes the
        edge-insertion-order dependence of the output (module docstring).
        Default ``False`` (single-branch greedy, historical behaviour).
    orbit_oracle : OrbitOracle or None, optional
        When given (and ``tie_branch=True``), reduce the residual tie set to
        one edge per stabiliser orbit and, per tied edge, the label-respecting
        orderings to one per orbit of the stabiliser that also fixes the edge.
        Value-preserving: the completion returned is unchanged.
    ranks : Sequence[int] or None, optional
        Per-vertex canonical ranks. When given, the residual V tie-break is
        :func:`_rank_tiebreak` instead of the raw edge id, and the new-vertex
        ordering is ``(label, rank)`` instead of every label-respecting
        permutation. Both branch sets become singletons.
    stats : dict[str, int] or None, optional
        Mutable counter sink. Keys ``"frames"`` (calls to this function),
        ``"v_branches"`` (V-branch expansions actually explored) and
        ``"oracle_calls"`` (oracle invocations made by the encoder) are
        incremented in place.
    """
    if stats is not None:
        stats["frames"] = stats.get("frames", 0) + 1
    if len(state.i2o) == H.n_nodes and len(state.consumed_edges) == H.n_edges:
        return ()

    radius = max(0, len(state.i2o))
    best_emission_key: tuple[Any, ...] | None = None
    best_kind: str | None = None
    best_new_slots: tuple[int, ...] | None = None
    best_v_info: tuple[Any, ...] | None = None
    best_c_info: tuple[Any, ...] | None = None
    best_move_block: list[Token] | None = None
    best_main_tok: Token | None = None

    for displacement in _enum_displacements(k, radius):
        cost = sum(abs(d) for d in displacement)
        if best_emission_key is not None and cost + 1 > best_emission_key[0]:
            break

        new_slots = tuple(
            _displaced_slot(state.cdll, state.get_ptr(idx + 1), displacement[idx])
            for idx in range(k)
        )
        tentative_inputs = [state.o2i[state.cdll.get_value(s)] for s in new_slots]
        move_block = _movement_tokens(displacement)
        move_keys = tuple(t.sort_key() for t in move_block)

        v_cand = _best_v_for_displacement(H, k, tentative_inputs, state, ranks)
        if v_cand is not None:
            (v_key, edge_id, i_v, j_v, le, new_labels, new_inputs_set) = v_cand
            main_tok: Token = TokenV(edge_label=le, i=i_v, j=j_v, new_node_labels=new_labels)
            ek = (
                len(move_block) + 1,
                move_keys + (main_tok.sort_key(),),
            )
            if best_emission_key is None or ek < best_emission_key:
                best_emission_key = ek
                best_kind = "V"
                best_new_slots = new_slots
                best_v_info = (edge_id, i_v, j_v, le, new_labels, new_inputs_set, v_key[:-1])
                best_c_info = None
                best_move_block = move_block
                best_main_tok = main_tok

        c_cand = _best_c_for_displacement(H, k, tentative_inputs, state)
        if c_cand is not None:
            (_, edge_id_c, i_c, le_c) = c_cand
            main_tok_c: Token = TokenC(edge_label=le_c, i=i_c)
            ek_c = (
                len(move_block) + 1,
                move_keys + (main_tok_c.sort_key(),),
            )
            if best_emission_key is None or ek_c < best_emission_key:
                best_emission_key = ek_c
                best_kind = "C"
                best_new_slots = new_slots
                best_c_info = (edge_id_c, i_c, le_c)
                best_v_info = None
                best_move_block = move_block
                best_main_tok = main_tok_c

    if best_kind is None:
        return None

    assert best_move_block is not None
    assert best_main_tok is not None
    assert best_new_slots is not None
    move_prefix = tuple(best_move_block) + (best_main_tok,)

    if best_kind == "C":
        assert best_c_info is not None
        edge_id_c, _, _ = best_c_info
        if inplace:
            saved_ptrs = tuple(state.pointers)
            state.set_ptrs(best_new_slots)
            state.consumed_edges.add(edge_id_c)
            sub_completion = _encode_from(
                H,
                k,
                state,
                inplace=True,
                tie_branch=tie_branch,
                orbit_oracle=orbit_oracle,
                stats=stats,
                _counter=_counter,
                _max_expansions=_max_expansions,
            )
            state.consumed_edges.discard(edge_id_c)
            state.pointers[:] = list(saved_ptrs)
            if sub_completion is None:
                return None
            return move_prefix + sub_completion
        sub_state = state.clone()
        sub_state.set_ptrs(best_new_slots)
        sub_state.consumed_edges.add(edge_id_c)
        sub_completion = _encode_from(
            H,
            k,
            sub_state,
            inplace=False,
            tie_branch=tie_branch,
            orbit_oracle=orbit_oracle,
            stats=stats,
            _counter=_counter,
            _max_expansions=_max_expansions,
        )
        if sub_completion is None:
            return None
        return move_prefix + sub_completion

    # V branch: enumerate the tied candidate edges (tie_branch mode only;
    # otherwise the single min-edge-id winner) and, per candidate, the
    # label-respecting permutations of its new inputs.
    assert best_v_info is not None
    edge_id_v, _, _, _, _, new_inputs_set, v_key_prefix = best_v_info

    prune = tie_branch and orbit_oracle is not None
    placed: tuple[NodeId, ...] = state.placed_inputs() if prune else ()

    if tie_branch:
        tentative_best = [state.o2i[state.cdll.get_value(s)] for s in best_new_slots]
        tied = _tied_v_candidates(H, k, tentative_best, state, v_key_prefix)
        if prune and len(tied) > 1:
            assert orbit_oracle is not None
            reps = orbit_oracle.edge_representatives(H, placed, [e for e, _ in tied])
            if stats is not None:
                stats["oracle_calls"] = stats.get("oracle_calls", 0) + 1
            keep = set(reps)
            tied = [(e, inputs) for e, inputs in tied if e in keep]
    else:
        tied = [(edge_id_v, new_inputs_set)]

    branches: list[tuple[EdgeId, tuple[NodeId, ...]]] = []
    for edge_id_b, inputs_b in tied:
        if ranks is not None:
            rk: Sequence[int] = ranks
            branches.append(
                (edge_id_b, tuple(sorted(inputs_b, key=lambda v: (H.vertex_label(v), rk[v]))))
            )
            continue
        perms = _label_respecting_perms(inputs_b, H)
        if prune and len(perms) > 1:
            assert orbit_oracle is not None
            perms = orbit_oracle.ordering_representatives(H, placed, edge_id_b, perms)
            if stats is not None:
                stats["oracle_calls"] = stats.get("oracle_calls", 0) + 1
        branches.extend((edge_id_b, seq_b) for seq_b in perms)

    best_completion: TokenSequence | None = None
    best_completion_key: tuple[Any, ...] | None = None
    for edge_id_v, new_input_seq in branches:
        if stats is not None:
            stats["v_branches"] = stats.get("v_branches", 0) + 1
        if _counter is not None:
            if _counter[0] >= _max_expansions:  # type: ignore[operator]
                raise CanonicalizationTimeoutError(
                    f"canonical-string branch budget exceeded ({_max_expansions} expansions)"
                )
            _counter[0] += 1
        if inplace:
            saved_ptrs = tuple(state.pointers)
            saved_next_id = state.next_output_id
            state.set_ptrs(best_new_slots)
            anchor_slot = state.get_ptr(1)
            new_cdll_slots: list[int] = []
            new_o_ids: list[NodeId] = []
            new_i_ids: list[NodeId] = []
            for input_v in new_input_seq:
                out_v_local: NodeId = state.next_output_id
                state.next_output_id += 1
                new_slot = state.cdll.insert_after(anchor_slot, out_v_local)
                state.i2o[input_v] = out_v_local
                state.o2i[out_v_local] = input_v
                new_cdll_slots.append(new_slot)
                new_o_ids.append(out_v_local)
                new_i_ids.append(input_v)
                anchor_slot = new_slot
            state.consumed_edges.add(edge_id_v)
            sub_completion = _encode_from(
                H,
                k,
                state,
                inplace=True,
                tie_branch=tie_branch,
                orbit_oracle=orbit_oracle,
                stats=stats,
                _counter=_counter,
                _max_expansions=_max_expansions,
            )
            state.consumed_edges.discard(edge_id_v)
            for slot in reversed(new_cdll_slots):
                state.cdll.remove(slot)
            for input_v in new_i_ids:
                state.i2o.pop(input_v, None)
            for out_v_local in new_o_ids:
                state.o2i.pop(out_v_local, None)
            state.next_output_id = saved_next_id
            state.pointers[:] = list(saved_ptrs)
        else:
            sub_state = state.clone()
            sub_state.set_ptrs(best_new_slots)
            anchor_slot = sub_state.get_ptr(1)
            for input_v in new_input_seq:
                out_v: NodeId = sub_state.next_output_id
                sub_state.next_output_id += 1
                new_slot = sub_state.cdll.insert_after(anchor_slot, out_v)
                sub_state.i2o[input_v] = out_v
                sub_state.o2i[out_v] = input_v
                anchor_slot = new_slot
            sub_state.consumed_edges.add(edge_id_v)
            sub_completion = _encode_from(
                H,
                k,
                sub_state,
                inplace=False,
                tie_branch=tie_branch,
                orbit_oracle=orbit_oracle,
                stats=stats,
                _counter=_counter,
                _max_expansions=_max_expansions,
            )
        if sub_completion is None:
            continue
        candidate = list(move_prefix) + list(sub_completion)
        cand_key = sequence_sort_key(candidate)
        if best_completion_key is None or cand_key < best_completion_key:
            best_completion = tuple(candidate)
            best_completion_key = cand_key
    return best_completion


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------


def _python_greedy_h2s(
    H: SparseHypergraph,
    *,
    seed_node: NodeId,
    k: int,
    inplace: bool = False,
    tie_branch: bool = False,
    max_expansions: int | None = None,
    orbit_oracle: OrbitOracle | None = None,
    ranks: Sequence[int] | None = None,
    stats: dict[str, int] | None = None,
) -> TokenSequence:
    """Pure-Python reference implementation (kept for differential tests).

    See :func:`greedy_h2s` for the production C++-backed entry point.
    ``tie_branch=True`` selects the tie-complete search (module docstring),
    mirrored bit-for-bit by the C++ twin and exposed as the
    ``canonical`` algorithm variant.

    Parameters
    ----------
    max_expansions : int or None, optional
        Maximum number of V-branch expansions across the entire search tree.
        ``None`` (default) means unlimited. When the budget is exceeded,
        :class:`isalhg.errors.CanonicalizationTimeoutError` is raised.
        Only meaningful when ``tie_branch=True``; single-branch greedy never
        branches so the counter stays at 0.
    orbit_oracle : OrbitOracle or None, optional
        Stabiliser-orbit pruning of the tie-complete branch set. Honoured
        only when ``tie_branch=True``; value-preserving, so the returned
        token sequence is unchanged.
    ranks : Sequence[int] or None, optional
        Per-vertex canonical ranks. When given, the residual V tie and the
        new-vertex ordering are resolved by rank instead of by raw id, which
        collapses both branch sets to a singleton. Mutually exclusive with
        ``tie_branch=True``; it selects a *different* canonical program
        (``canonical_rank``), not ``w*_c``.
    stats : dict[str, int] or None, optional
        Mutable counter sink; see :func:`_encode_from`.
    """
    n = H.n_nodes
    if n == 0:
        return ()
    if not 0 <= seed_node < n:
        raise ValueError(f"seed_node {seed_node} out of [0, {n})")
    if k < 1:
        raise ValueError(f"k must be >= 1, got {k}")

    cdll = CircularDoublyLinkedList(capacity=max(1, n))
    seed_slot = cdll.insert_after(0, 0)
    state = _State(
        cdll=cdll,
        pointers=[seed_slot] * k,
        i2o={seed_node: 0},
        o2i={0: seed_node},
        consumed_edges=set(),
        next_output_id=1,
    )
    _counter: list[int] | None = [0] if max_expansions is not None else None
    result = _encode_from(
        H,
        k,
        state,
        inplace=inplace,
        tie_branch=tie_branch,
        orbit_oracle=orbit_oracle,
        ranks=ranks,
        stats=stats,
        _counter=_counter,
        _max_expansions=max_expansions,
    )
    if result is None:
        raise H2SStuckError(
            f"H2S stuck from seed {seed_node} on hypergraph with {n} nodes, {H.n_edges} edges"
        )
    return result


# ---------------------------------------------------------------------------
# Backend-aware public entry. Both implementations live in this module: the
# pure-Python reference above and the C++-backed wrapper below. The
# dispatcher selects between them via the ``backend=`` kwarg.
# ---------------------------------------------------------------------------

from isalhg.core._core import greedy_h2s as _core_greedy_h2s  # noqa: E402
from isalhg.core.backends import DEFAULT_BACKEND, Backend, resolve  # noqa: E402
from isalhg.core.instructions import parse as _parse_tokens  # noqa: E402


def _cpp_greedy_h2s(
    H: SparseHypergraph,
    *,
    seed_node: NodeId,
    k: int,
    inplace: bool = False,  # noqa: ARG001  # accepted for API parity with _python
    tie_branch: bool = False,
) -> TokenSequence:
    """C++-backed implementation of :func:`greedy_h2s`.

    Delegates to ``isalhg.core._core.greedy_h2s`` and parses the
    serialised result back into Python ``Token`` dataclasses so the
    public return type matches the Python reference.
    """
    raw = _core_greedy_h2s(H, seed_node, k, tie_branch)
    return tuple(_parse_tokens(raw))


_GREEDY_H2S_BACKENDS: dict[str, object] = {
    "python": _python_greedy_h2s,
    "cpp": _cpp_greedy_h2s,
}


def greedy_h2s(
    H: SparseHypergraph,
    *,
    seed_node: NodeId,
    k: int,
    inplace: bool = False,
    tie_branch: bool = False,
    backend: Backend | None = None,
    orbit_oracle: OrbitOracle | None = None,
    ranks: Sequence[int] | None = None,
) -> TokenSequence:
    """Greedy single-seed H2S encoder.

    Parameters
    ----------
    H : SparseHypergraph
        Connected hypergraph to encode.
    seed_node : NodeId
        First node placed at slot 0 of the CDLL.
    k : int
        Pointer count of the VM. Must satisfy ``k >= max arity of H``.
    inplace : bool, optional
        Accepted for API compatibility. The C++ backend always runs
        inplace with stack-allocated undo records; the Python backend
        honours the flag (clone vs undo log) at no observable cost.
    tie_branch : bool, optional
        When ``True``, branch over every V candidate tying on the
        iso-invariant cascade key-prefix instead of committing to the
        min-edge-id one (module docstring). Both backends implement it.
        Default ``False``.
    backend : {"cpp", "python"}, optional
        Implementation to use. Defaults to ``"cpp"`` (see
        :data:`isalhg.core.backends.DEFAULT_BACKEND`).
    orbit_oracle : OrbitOracle or None, optional
        Stabiliser-orbit pruning of the tie-complete branch set. Python path
        with ``tie_branch=True`` only. Value-preserving: the emitted tokens
        are the unpruned ones, bit for bit.
    ranks : Sequence[int] or None, optional
        Per-vertex canonical ranks selecting the ``canonical_rank`` program
        (rank tie-break + ``(label, rank)`` ordering). Python path only, and
        mutually exclusive with ``tie_branch=True``.

    Returns
    -------
    tuple[Token, ...]
        Emitted token sequence.

    Raises
    ------
    H2SStuckError
        If the encoder cannot make progress from a non-terminal state.
    ValueError
        If ``seed_node`` is out of range, ``k < 1``, ``backend`` is unknown,
        or ``orbit_oracle`` / ``ranks`` is combined with a backend or a
        ``tie_branch`` setting that cannot honour it. The oracle and the
        ranks never fall back silently: an unhonourable request is an error.
    """
    n = H.n_nodes
    if n == 0:
        return ()
    if not 0 <= seed_node < n:
        raise ValueError(f"seed_node {seed_node} out of [0, {n})")
    if k < 1:
        raise ValueError(f"k must be >= 1, got {k}")
    chosen: str = DEFAULT_BACKEND if backend is None else backend
    if orbit_oracle is not None:
        if chosen != "python":
            raise ValueError(
                f"orbit_oracle requires backend='python'; the {chosen!r} backend has no "
                "oracle hook and would silently run the unpruned search"
            )
        if not tie_branch:
            raise ValueError("orbit_oracle requires tie_branch=True (it prunes the tie set)")
    if ranks is not None:
        if chosen != "python":
            raise ValueError(f"ranks requires backend='python'; got {chosen!r}")
        if tie_branch:
            raise ValueError(
                "ranks and tie_branch=True are mutually exclusive: ranks collapse the tie "
                "set to a singleton, which is a different canonical program from w*_c"
            )
    impl = resolve(backend, _GREEDY_H2S_BACKENDS)
    extra: dict[str, Any] = {}
    if orbit_oracle is not None:
        extra["orbit_oracle"] = orbit_oracle
    if ranks is not None:
        extra["ranks"] = ranks
    return impl(
        H,
        seed_node=seed_node,
        k=k,
        inplace=inplace,
        tie_branch=tie_branch,
        **extra,
    )


def hypergraph_to_string(
    H: SparseHypergraph,
    *,
    seed_node: NodeId,
    k: int,
    backend: Backend | None = None,
) -> str:
    """Greedy single-seed encoder returning the serialised string form."""
    tokens = greedy_h2s(H, seed_node=seed_node, k=k, backend=backend)
    return serialize(list(tokens))
