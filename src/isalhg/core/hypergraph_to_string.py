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

Disconnected hypergraphs are rejected by :func:`isalhg.core.canonical.canonical_string`,
not here.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
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
)
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.core.structural_tuples import eta
from isalhg.errors import IsalHGError
from isalhg.types import EdgeId, NodeId, TokenSequence


class H2SStuckError(IsalHGError):
    """Raised when the encoder cannot emit a token from a non-terminal state."""


# ---------------------------------------------------------------------------
# Displacement enumeration
# ---------------------------------------------------------------------------


def _enum_displacements(k: int, radius: int) -> list[tuple[int, ...]]:
    """All ``k``-tuples in ``[-radius, radius]^k`` sorted by ``(sum|d|, |d|, d)``."""
    if radius <= 0:
        return [(0,) * k]
    rng = range(-radius, radius + 1)
    tuples = list(product(*([rng] * k)))
    tuples.sort(key=lambda t: (sum(abs(d) for d in t), tuple(abs(d) for d in t), t))
    return tuples


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


# ---------------------------------------------------------------------------
# Candidate finders
# ---------------------------------------------------------------------------


def _best_v_for_displacement(
    H: SparseHypergraph,
    k: int,
    tentative_inputs: list[NodeId],
    state: _State,
) -> tuple[tuple[Any, ...], EdgeId, int, int, int, tuple[int, ...], frozenset[NodeId]] | None:
    """Return the lex-min V candidate at this displacement, or None.

    Returns ``(cascade_key, edge_id, i, j, edge_label, new_labels, new_inputs_set)``.
    The new-input ordering is left to the caller (branching point).
    """
    best: (
        tuple[tuple[Any, ...], EdgeId, int, int, int, tuple[int, ...], frozenset[NodeId]] | None
    ) = None
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
            key = (i_val, j_val, edge_label, new_labels, edge_eta, edge_id)
            if best is None or key < best[0]:
                best = (
                    key,
                    edge_id,
                    i_val,
                    j_val,
                    edge_label,
                    new_labels,
                    frozenset(new_inputs),
                )
    return best


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
    wl_colors: list[int] | None = None,
) -> list[tuple[NodeId, ...]]:
    """Yield all orderings of ``new_inputs_set`` consistent with the sorted
    label tuple (smaller labels first; within a label class, all permutations).

    When ``wl_colors`` is provided, prune permutations that swap two
    WL-equivalent vertices within the same label class: in any such
    swap the resulting completion is isomorphic, so the lex-min is
    unaffected if we require WL-equivalent vertices to appear in
    ascending ID order. This collapses the ``j!`` branching factor on
    inputs whose WL orbit has size > 1.
    """
    by_label: dict[int, list[NodeId]] = defaultdict(list)
    for v in new_inputs_set:
        by_label[H.vertex_label(v)].append(v)
    sorted_labels = sorted(by_label.keys())
    groups = [by_label[lab] for lab in sorted_labels]
    out: list[tuple[NodeId, ...]] = []
    for prod_perm in product(*[permutations(g) for g in groups]):
        if wl_colors is not None and not _wl_orbit_canonical(prod_perm, wl_colors):
            continue
        out.append(tuple(v for group in prod_perm for v in group))
    return out


def _wl_orbit_canonical(
    prod_perm: tuple[tuple[NodeId, ...], ...],
    wl_colors: list[int],
) -> bool:
    """True iff WL-equivalent vertices within each label group appear in ascending ID order."""
    for grp in prod_perm:
        last_id_at_color: dict[int, NodeId] = {}
        for v in grp:
            colour = wl_colors[v]
            if colour in last_id_at_color and last_id_at_color[colour] >= v:
                return False
            last_id_at_color[colour] = v
    return True


# ---------------------------------------------------------------------------
# Main recursive encoder
# ---------------------------------------------------------------------------


def _encode_from(
    H: SparseHypergraph,
    k: int,
    state: _State,
    *,
    inplace: bool = False,
    wl_colors: list[int] | None = None,
) -> TokenSequence | None:
    """Recursive lex-min completion from ``state``. Returns ``None`` if stuck.

    Parameters
    ----------
    inplace : bool, optional
        When ``True`` mutate ``state`` directly at each branch and undo
        on return instead of cloning. Equivalent output; lower per-branch
        cost. Default ``False`` (clone-on-branch, identical to the
        original behaviour).
    wl_colors : list[int] or None, optional
        Per-vertex WL hashes for orbit-aware pruning of the V-branch
        permutation set. ``None`` disables pruning (default).
    """
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

        v_cand = _best_v_for_displacement(H, k, tentative_inputs, state)
        if v_cand is not None:
            (_, edge_id, i_v, j_v, le, new_labels, new_inputs_set) = v_cand
            main_tok: Token = TokenV(edge_label=le, i=i_v, j=j_v, new_node_labels=new_labels)
            ek = (
                len(move_block) + 1,
                move_keys + (main_tok.sort_key(),),
            )
            if best_emission_key is None or ek < best_emission_key:
                best_emission_key = ek
                best_kind = "V"
                best_new_slots = new_slots
                best_v_info = (edge_id, i_v, j_v, le, new_labels, new_inputs_set)
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
            sub_completion = _encode_from(H, k, state, inplace=True, wl_colors=wl_colors)
            state.consumed_edges.discard(edge_id_c)
            state.pointers[:] = list(saved_ptrs)
            if sub_completion is None:
                return None
            return move_prefix + sub_completion
        sub_state = state.clone()
        sub_state.set_ptrs(best_new_slots)
        sub_state.consumed_edges.add(edge_id_c)
        sub_completion = _encode_from(H, k, sub_state, inplace=False, wl_colors=wl_colors)
        if sub_completion is None:
            return None
        return move_prefix + sub_completion

    # V branch: enumerate label-respecting permutations of new_inputs.
    assert best_v_info is not None
    edge_id_v, _, _, _, _, new_inputs_set = best_v_info

    best_completion: TokenSequence | None = None
    best_completion_key: tuple[Any, ...] | None = None
    for new_input_seq in _label_respecting_perms(new_inputs_set, H, wl_colors=wl_colors):
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
            sub_completion = _encode_from(H, k, state, inplace=True, wl_colors=wl_colors)
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
            sub_completion = _encode_from(H, k, sub_state, inplace=False, wl_colors=wl_colors)
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
    wl_colors: list[int] | None = None,
) -> TokenSequence:
    """Pure-Python reference implementation (kept for differential tests).

    See :func:`greedy_h2s` for the production C++-backed entry point.
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
    result = _encode_from(H, k, state, inplace=inplace, wl_colors=wl_colors)
    if result is None:
        raise H2SStuckError(
            f"H2S stuck from seed {seed_node} on hypergraph with {n} nodes, {H.n_edges} edges"
        )
    return result


# ---------------------------------------------------------------------------
# C++ fast path. The shim parses the serialised string returned by the C++
# encoder back into the Python ``Token`` dataclasses so the public surface
# matches the pre-port API.
# ---------------------------------------------------------------------------

from isalhg._core import greedy_h2s as _cpp_greedy_h2s  # noqa: E402
from isalhg.core.instructions import parse as _parse_tokens  # noqa: E402


def greedy_h2s(
    H: SparseHypergraph,
    *,
    seed_node: NodeId,
    k: int,
    inplace: bool = False,  # noqa: ARG001  # accepted for API compatibility
    wl_colors: list[int] | None = None,
) -> TokenSequence:
    """Greedy single-seed H2S encoder (C++ implementation).

    Parameters
    ----------
    H : SparseHypergraph
        Connected hypergraph to encode.
    seed_node : NodeId
        First node placed at slot 0 of the CDLL.
    k : int
        Pointer count of the VM. Must satisfy ``k >= max arity of H``.
    inplace : bool, optional
        Accepted for API compatibility; the C++ implementation always
        uses inplace mutation with stack-allocated undo records, so this
        flag has no observable effect.
    wl_colors : list[int] or None, optional
        Per-vertex stable WL colours used to prune the V-branch
        permutation set. Default ``None`` (no pruning).

    Returns
    -------
    tuple[Token, ...]
        Emitted token sequence (parsed back from the C++ string output).

    Raises
    ------
    H2SStuckError
        If the encoder cannot make progress from a non-terminal state.
    ValueError
        If ``seed_node`` is out of range or ``k < 1``.
    """
    n = H.n_nodes
    if n == 0:
        return ()
    if not 0 <= seed_node < n:
        raise ValueError(f"seed_node {seed_node} out of [0, {n})")
    if k < 1:
        raise ValueError(f"k must be >= 1, got {k}")
    raw = _cpp_greedy_h2s(H, seed_node, k, wl_colors)
    return tuple(_parse_tokens(raw))


def hypergraph_to_string(
    H: SparseHypergraph,
    *,
    seed_node: NodeId,
    k: int,
) -> str:
    """Greedy single-seed encoder returning the serialised string form."""
    n = H.n_nodes
    if n == 0:
        return ""
    if not 0 <= seed_node < n:
        raise ValueError(f"seed_node {seed_node} out of [0, {n})")
    if k < 1:
        raise ValueError(f"k must be >= 1, got {k}")
    return _cpp_greedy_h2s(H, seed_node, k, None)
