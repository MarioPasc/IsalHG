"""The ordered walk ``OW_pi`` -- a deterministic Isal program along a canonical order.

The family's canonical string ``w*_c`` is the *minimum* of a presentation-dependent
search: discontinuous under edits and exponential on symmetric inputs. The ordered
walk removes the search from the representation. A canonical order on the constants
is injected as a rank vector (nauty's individualisation-refinement on the coloured
Levi graph supplies it -- see :mod:`isalhg.iso_backends.isal_ordered`); the emitter
then walks the knowledge base from a canonically chosen root and writes one Isal
instruction block per fact, with no branching and no lex-min.

The emitter is a simulation of :class:`~isalhg.core.string_to_hypergraph.StringToHypergraph`
run forward: it maintains the same CDLL and pointer vector the decoder will build, so
``S2H(serialize(tokens); k, root_label)`` reproduces the input up to isomorphism
(round trip, Lemma C.3 of ``theorem_c_ordered_walk.tex``). Together with the fact that
the canonically relabelled structure ``H_rho`` is a complete invariant (Lemma C.1), the
pair ``(root label, word)`` is a complete isomorphism invariant (Theorem C).

Two phases
----------
*V-phase.* While some constant is unplaced, select the ``K_V``-minimal fact that
straddles the placed frontier, point ``p_1`` at its anchor (the placed member of least
creation index) and ``p_2..p_i`` at its other placed members in ascending creation
index, and emit ``V[predicate; i; j; types of the new members]``. The decoder chains the
``j`` new constants immediately after ``p_1`` in the listed order; the emitter does the
same to its own CDLL.

*C-phase.* Every fact whose members are all placed by the end of the V-phase closes with
a ``C`` token, swept in ascending ``K_C``. The CDLL no longer changes here, so ``pos`` is
computed once.

*Move rule (no-crossing).* Both phases move pointers in backward-position coordinates
from the root, never wrapping: see :meth:`_Emitter._move`. This is what keeps the word
local -- a run's length counts slots on the root-free arc, and chaining new constants
after ``p_1`` leaves those counts alone.

The rank vector is a parameter, never computed here, so the emitter needs nothing
outside the standard library. Two implementations of it are registered: the pure-Python
one below -- the reference the definition is read off -- and the C++ port in
``isalhg.core._core`` (``src/isalhg/core/_native/src/ordered_walk.cpp``), which returns
the same tokens bit for bit. ``backend=`` picks one; the default is the extension when
it is importable, mirroring :func:`isalhg.core.canonical.canonical_string`.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Literal

from isalhg.core.backends import resolve
from isalhg.core.cdll import CircularDoublyLinkedList
from isalhg.core.hypergraph_to_string import _movement_tokens
from isalhg.core.instructions import (
    Token,
    TokenC,
    TokenN,
    TokenP,
    TokenV,
    TokenW,
    validate,
)
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.errors import (
    DegenerateHypergraphError,
    DisconnectedHypergraphError,
    IsalHGError,
)
from isalhg.types import EdgeId, NodeId, VertexLabel

try:
    from isalhg.core._core import ordered_walk as _core_ordered_walk
except ImportError:  # pragma: no cover - exercised only without a built extension
    _core_ordered_walk = None  # type: ignore[assignment]

# ``(type of u, sorted multiset of (predicate, arity) over the facts containing u)``.
# Isomorphism-invariant, and it changes only when u's own facts change -- which is what
# makes it the locality-preserving component of ``K_V``.
_Signature = tuple[int, tuple[tuple[int, int], ...]]


class OrderedWalkError(IsalHGError):
    """Raised when the ordered walk cannot proceed on well-formed input."""


@dataclass(frozen=True)
class OrderedWalkPolicy:
    """A choice of root rule and ``K_V`` field order.

    Parameters
    ----------
    root_rule : {"hub", "rank0"}
        ``"hub"`` takes the constant maximising ``(deg_E, type)``, ties broken by
        minimum rank -- the entity that appears in most facts. ``"rank0"`` takes the
        constant nauty ranks first, an ablation that hands the whole root choice to
        the canonical labelling.
    rank_first : bool
        ``False`` (the default, ``ow-struct``) puts the new members' ranks last in
        ``K_V``, after their local signatures, so the rank decides only inside a
        signature class. ``True`` (``ow-rank``) moves that component to just after the
        anchor's creation index, ahead of the predicate: the order is then nauty's and
        the structure second.
    """

    root_rule: Literal["hub", "rank0"] = "hub"
    rank_first: bool = False

    @property
    def name(self) -> str:
        """Short identifier: ``"struct"``, ``"rank"``, ``"rank0"``.

        The pre-registered arms are ``struct`` (hub root, structure first), ``rank``
        (hub root, rank first) and ``rank0`` (rank-0 root, structure first). The
        fourth combination is reachable but is not an arm; it is named
        ``"rank0_rank"`` so it can never be mistaken for one of the three.
        """
        if self.root_rule == "rank0":
            return "rank0_rank" if self.rank_first else "rank0"
        return "rank" if self.rank_first else "struct"


#: The default policy ``ow-struct``. A frozen dataclass, so one module-level instance
#: is shared by every default argument (ruff B008 forbids constructing one in place).
DEFAULT_POLICY: OrderedWalkPolicy = OrderedWalkPolicy()


@dataclass(frozen=True)
class OrderedWalkResult:
    """The emitted program and the two facts about it a caller needs.

    Attributes
    ----------
    root : NodeId
        Input id of the constant the walk started from.
    root_label : VertexLabel
        Type of the root. No token carries it -- the decoder receives it as
        ``seed_label`` -- so the fingerprint must carry it alongside the word.
    tokens : tuple[Token, ...]
        The program. ``instructions.serialize(tokens)`` is "the word".
    creation_order : tuple[NodeId, ...]
        Input ids in the order the program creates them, root first. Position ``t``
        is the constant the decoder will create ``t``-th, so this is the round-trip
        isomorphism written out.
    """

    root: NodeId
    root_label: VertexLabel
    tokens: tuple[Token, ...]
    creation_order: tuple[NodeId, ...]


def _signatures(H: SparseHypergraph) -> list[_Signature]:
    """Return the local signature of every constant, indexed by node id."""
    return [
        (
            H.vertex_label(v),
            tuple(sorted((H.edge_label(e), len(H.members(e))) for e in H.incident_edges(v))),
        )
        for v in range(H.n_nodes)
    ]


def _select_root(H: SparseHypergraph, ranks: Sequence[int], policy: OrderedWalkPolicy) -> NodeId:
    """Return the constant the walk starts from under ``policy``."""
    if policy.root_rule == "rank0":
        return ranks.index(0)
    return max(
        range(H.n_nodes),
        key=lambda v: (H.degree(v), H.vertex_label(v), -ranks[v]),
    )


class _Emitter:
    """Mutable state of one ordered walk. Instantiated once per call."""

    __slots__ = (
        "_H",
        "_ranks",
        "_policy",
        "_sig",
        "_n_ptr",
        "_cdll",
        "_slot_of",
        "_ptr",
        "_order",
        "_index_of",
        "_placed",
        "_c",
        "_consumed",
        "_creation",
        "_tokens",
    )

    def __init__(
        self,
        H: SparseHypergraph,
        ranks: Sequence[int],
        policy: OrderedWalkPolicy,
        n_ptr: int,
        root: NodeId,
    ) -> None:
        self._H = H
        self._ranks = ranks
        self._policy = policy
        self._sig = _signatures(H)
        self._n_ptr = n_ptr

        self._cdll = CircularDoublyLinkedList(capacity=H.n_nodes)
        root_slot = self._cdll.insert_after(0, root)
        self._slot_of: dict[NodeId, int] = {root: root_slot}
        self._ptr: list[int] = [root_slot] * n_ptr
        self._order: list[int] = [root_slot]
        self._index_of: dict[int, int] = {root_slot: 0}

        self._placed: set[NodeId] = {root}
        self._c: dict[NodeId, int] = {root: 0}
        self._consumed: set[EdgeId] = set()
        self._creation: list[NodeId] = [root]
        self._tokens: list[Token] = []

    # ------------------------------------------------------------------
    # Movement
    # ------------------------------------------------------------------

    def _pos(self, slot: int) -> int:
        """Backward steps from the root's slot to ``slot``; the root itself is ``0``."""
        size = len(self._order)
        return (size - self._index_of[slot]) % size

    def _move(self, targets: dict[int, int]) -> None:
        """Move the given 1-based pointers to the given slots and emit the block.

        The **no-crossing rule**: every move is computed in backward-position
        coordinates from the root and never wraps. A pointer at ``pos = a`` moving to a
        target at ``pos = b`` retreats ``b - a`` steps when ``b > a`` and advances
        ``a - b`` steps when ``b < a`` -- in both cases a displacement of ``a - b``,
        which ``_movement_tokens`` renders as ``N`` for a negative value and ``P`` for a
        positive one (all ``N`` by ascending pointer index, then all ``P``).

        No move passes over the root's slot, so a run's length is the number of slots
        strictly between the two positions on the root-free arc. That is what makes the
        word local: the decoder chains new constants immediately after ``p_1``, which
        leaves the backward position of every slot beyond ``p_1`` untouched, so an
        insertion elsewhere never changes an existing run. The shorter-direction rule
        this replaces did change them -- a forward-rendered run has length ``size - gap``
        and therefore grows with the constant count.

        Every run is at most ``n - 1`` tokens long, because positions live in
        ``[0, n - 1]``.
        """
        displacement = [0] * self._n_ptr
        for t, target_slot in targets.items():
            displacement[t - 1] = self._pos(self._ptr[t - 1]) - self._pos(target_slot)
            self._ptr[t - 1] = target_slot
        self._tokens.extend(_movement_tokens(tuple(displacement)))

    # ------------------------------------------------------------------
    # V-phase
    # ------------------------------------------------------------------

    def _key_v(self, e: EdgeId) -> tuple[object, ...]:
        """Return ``K_V(e)``; a total order on the candidate facts.

        Creation indices are injective on placed constants and ranks are injective on
        all of them, so the key determines ``e``: no two distinct candidates tie.
        """
        members = self._H.members(e)
        placed_c = sorted(self._c[v] for v in members if v in self._placed)
        fresh = [u for u in members if u not in self._placed]
        structure: tuple[object, ...] = (
            self._H.edge_label(e),
            len(placed_c),
            len(fresh),
            tuple(placed_c),
            tuple(sorted(self._sig[u] for u in fresh)),
        )
        by_rank = tuple(sorted(self._ranks[u] for u in fresh))
        if self._policy.rank_first:
            return (placed_c[0], by_rank, *structure)
        return (placed_c[0], *structure, by_rank)

    def _emit_v(self, e: EdgeId) -> None:
        members = self._H.members(e)
        anchored = sorted((v for v in members if v in self._placed), key=lambda v: self._c[v])
        fresh = sorted(
            (u for u in members if u not in self._placed),
            key=lambda u: (self._H.vertex_label(u), self._ranks[u]),
        )
        self._move({t: self._slot_of[v] for t, v in enumerate(anchored, start=1)})
        self._tokens.append(
            TokenV(
                edge_label=self._H.edge_label(e),
                i=len(anchored),
                j=len(fresh),
                new_node_labels=tuple(self._H.vertex_label(u) for u in fresh),
            )
        )
        self._insert_after_p1(fresh)
        self._consumed.add(e)

    def _insert_after_p1(self, fresh: list[NodeId]) -> None:
        """Chain ``fresh`` into the CDLL right after ``p_1``, mirroring the decoder."""
        anchor_slot = self._ptr[0]
        base = self._index_of[anchor_slot]
        new_slots: list[int] = []
        after = anchor_slot
        for u in fresh:
            slot = self._cdll.insert_after(after, u)
            self._slot_of[u] = slot
            new_slots.append(slot)
            after = slot
            self._c[u] = len(self._creation)
            self._creation.append(u)
            self._placed.add(u)
        self._order[base + 1 : base + 1] = new_slots
        self._index_of = {slot: idx for idx, slot in enumerate(self._order)}

    def _v_phase(self) -> None:
        candidates: set[EdgeId] = set()
        for v in self._creation:
            candidates |= self._H.incident_edges(v)
        while len(self._placed) < self._H.n_nodes:
            candidates = {
                e
                for e in candidates
                if e not in self._consumed and not self._H.members(e) <= self._placed
            }
            if not candidates:
                raise OrderedWalkError(
                    "the V-phase ran out of frontier facts before every constant was "
                    "placed; the input is not connected"
                )
            best = min(candidates, key=self._key_v)
            before = len(self._creation)
            self._emit_v(best)
            for u in self._creation[before:]:
                candidates |= self._H.incident_edges(u)

    # ------------------------------------------------------------------
    # C-phase
    # ------------------------------------------------------------------

    def _c_phase(self) -> None:
        # The CDLL no longer changes, so every ``pos`` is computed once here.
        pos = {self._cdll.get_value(slot): self._pos(slot) for slot in self._order}
        remaining = [e for e in self._H.edges() if e not in self._consumed]
        remaining.sort(
            key=lambda e: (
                tuple(sorted(pos[v] for v in self._H.members(e))),
                self._H.edge_label(e),
            )
        )
        for e in remaining:
            members = sorted(self._H.members(e), key=lambda v: pos[v])
            self._move({t: self._slot_of[v] for t, v in enumerate(members, start=1)})
            self._tokens.append(TokenC(edge_label=self._H.edge_label(e), i=len(members)))
            self._consumed.add(e)

    # ------------------------------------------------------------------
    # Driver
    # ------------------------------------------------------------------

    def run(self) -> tuple[tuple[Token, ...], tuple[NodeId, ...]]:
        self._v_phase()
        self._c_phase()
        return tuple(self._tokens), tuple(self._creation)


# ---------------------------------------------------------------------------
# Backends
# ---------------------------------------------------------------------------


def _python_ordered_walk(
    H: SparseHypergraph, ranks: Sequence[int], policy: OrderedWalkPolicy
) -> OrderedWalkResult:
    """Pure-Python ordered walk -- the reference implementation of Definition 3.2."""
    max_arity = max((len(H.members(e)) for e in H.edges()), default=2)
    root = _select_root(H, ranks, policy)
    tokens, creation = _Emitter(H, ranks, policy, max(2, max_arity), root).run()
    return OrderedWalkResult(
        root=root,
        root_label=H.vertex_label(root),
        tokens=tokens,
        creation_order=creation,
    )


def _token_from_tuple(raw: tuple[Any, ...]) -> Token:
    """Re-hydrate one ``(kind, *fields)`` tuple from the extension into a ``Token``."""
    kind = raw[0]
    if kind == "N":
        return TokenN(i=raw[1])
    if kind == "P":
        return TokenP(i=raw[1])
    if kind == "V":
        return TokenV(edge_label=raw[1], i=raw[2], j=raw[3], new_node_labels=raw[4])
    if kind == "C":
        return TokenC(edge_label=raw[1], i=raw[2])
    return TokenW()


def _cpp_ordered_walk(
    H: SparseHypergraph, ranks: Sequence[int], policy: OrderedWalkPolicy
) -> OrderedWalkResult:
    """C++-backed ordered walk; token-for-token equal to :func:`_python_ordered_walk`."""
    root, root_label, raw_tokens, creation = _core_ordered_walk(
        H,
        list(ranks),
        1 if policy.root_rule == "rank0" else 0,
        policy.rank_first,
    )
    return OrderedWalkResult(
        root=root,
        root_label=root_label,
        tokens=tuple(_token_from_tuple(raw) for raw in raw_tokens),
        creation_order=tuple(creation),
    )


_ORDERED_WALK_BACKENDS: dict[str, Callable[..., OrderedWalkResult]] = {
    "python": _python_ordered_walk,
}
if _core_ordered_walk is not None:
    _ORDERED_WALK_BACKENDS["cpp"] = _cpp_ordered_walk


def ordered_walk(
    H: SparseHypergraph,
    ranks: Sequence[int],
    *,
    policy: OrderedWalkPolicy = DEFAULT_POLICY,
    k: int | None = None,
    backend: str | None = None,
) -> OrderedWalkResult:
    """Emit the ordered-walk program of ``H`` under ``ranks`` and ``policy``.

    The emitted tokens are independent of ``k``: the walk points at most
    ``max(2, max arity)`` pointers and never names a higher index, so the same program
    is produced for every admissible ``k``. ``k`` is needed only to validate the
    program or to decode it.

    Parameters
    ----------
    H : SparseHypergraph
        A connected labelled hypergraph.
    ranks : Sequence[int]
        ``ranks[v]`` is the canonical rank of constant ``v``; a permutation of
        ``range(H.n_nodes)``. :func:`isalhg.iso_backends.canonical_order.canonical_ranks`
        supplies the one the article adopts.
    policy : OrderedWalkPolicy, optional
        Root rule and ``K_V`` field order. Defaults to ``ow-struct``.
    k : int or None, optional
        When given, the emitted program is checked against
        :func:`isalhg.core.instructions.validate` at this pointer count before it is
        returned. ``None`` (the default) skips the check.
    backend : {"cpp", "python"} or None, optional
        Implementation to run. ``None`` takes the C++ extension when it is importable
        and the Python reference otherwise. Both return the same tokens and the same
        creation order; the choice is a speed decision, never a semantic one.

    Returns
    -------
    OrderedWalkResult
        Root, root type, program, and creation order.

    Raises
    ------
    isalhg.errors.DegenerateHypergraphError
        If ``H`` has no constants.
    isalhg.errors.DisconnectedHypergraphError
        If ``H`` is not connected.
    OrderedWalkError
        If ``ranks`` is not a permutation of ``range(H.n_nodes)``.
    isalhg.errors.InvalidInstructionError
        If ``k`` is given and the program does not validate at that pointer count.
    ValueError
        If ``backend`` is neither ``"cpp"`` nor ``"python"``.
    """
    if H.n_nodes == 0:
        raise DegenerateHypergraphError("the ordered walk requires at least one constant")
    if sorted(ranks) != list(range(H.n_nodes)):
        raise OrderedWalkError(
            f"ranks must be a permutation of range({H.n_nodes}); got {len(ranks)} entries"
        )
    if not H.is_connected():
        raise DisconnectedHypergraphError(
            "the ordered walk requires a connected hypergraph (decision B11)"
        )

    chosen = backend
    if chosen is None and "cpp" not in _ORDERED_WALK_BACKENDS:
        chosen = "python"
    result = resolve(chosen, _ORDERED_WALK_BACKENDS)(H, ranks, policy)

    if k is not None:
        validate(
            list(result.tokens),
            k=k,
            n_vertex_labels=H.n_vertex_labels,
            n_edge_labels=H.n_edge_labels,
        )

    return result


__all__ = [
    "DEFAULT_POLICY",
    "OrderedWalkError",
    "OrderedWalkPolicy",
    "OrderedWalkResult",
    "ordered_walk",
]
