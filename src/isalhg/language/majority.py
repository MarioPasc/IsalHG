"""Majority merge over constant identities --- the RQ3 reference method.

Every other method in this package sees a bare labelled hypergraph.  This one
is handed the constant *identities* as well, so it can decide a fact by name:
keep ``(predicate, {identity, ...})`` when strictly more than half the members
assert it.  With identities the representative problem is a vote; without them
it is a search over decoded words, which is what
:func:`isalhg.language.consensus.coverage_consensus` does.  `DESIGN.md` RQ3
hypothesis H3c asks whether the search comes within five points of the vote,
so this function exists to be the number the search is measured against, and it
is the *only* place in the package that reads identities.

The merged knowledge base carries the union of the members' constants, ordered
by identity, so its constant space is not any member's.  The identity tuple is
returned beside it because the caller needs it to score the merge against a
truth whose constants are named the same way.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.language.reach import LanguageError
from isalhg.types import EdgeLabel, VertexLabel

Identity = str
IdentifiedFact = tuple[EdgeLabel, frozenset[Identity]]


class MajorityMergeError(LanguageError):
    """Raised when a majority merge is given inconsistent members and identities."""


def _validate(
    members: Sequence[SparseHypergraph], identities: Sequence[Sequence[Identity]]
) -> None:
    """Raise :class:`MajorityMergeError` unless the identities align with the members."""
    if not members:
        raise MajorityMergeError("majority_merge needs at least one member")
    if len(members) != len(identities):
        raise MajorityMergeError(f"got {len(members)} members but {len(identities)} identity rows")
    for index, (H, names) in enumerate(zip(members, identities, strict=True)):
        if len(names) != H.n_nodes:
            raise MajorityMergeError(
                f"member {index} has {H.n_nodes} constants but {len(names)} identities"
            )
        if len(set(names)) != len(names):
            raise MajorityMergeError(f"member {index} repeats a constant identity")


def _majority_types(
    members: Sequence[SparseHypergraph], identities: Sequence[Sequence[Identity]]
) -> dict[Identity, VertexLabel]:
    """Return the majority type of every identity, ties broken by smallest type id."""
    votes: dict[Identity, Counter[VertexLabel]] = {}
    for H, names in zip(members, identities, strict=True):
        for v, name in enumerate(names):
            votes.setdefault(name, Counter())[H.vertex_label(v)] += 1
    return {
        name: min(counter.items(), key=lambda item: (-item[1], item[0]))[0]
        for name, counter in votes.items()
    }


def majority_merge(
    members: Sequence[SparseHypergraph],
    identities: Sequence[Sequence[Identity]],
) -> tuple[SparseHypergraph, tuple[Identity, ...]]:
    """Merge members by majority vote over identified facts.

    Parameters
    ----------
    members : Sequence[SparseHypergraph]
        The knowledge bases to merge; at least one.
    identities : Sequence[Sequence[str]]
        ``identities[i][v]`` names constant ``v`` of ``members[i]``.  Names are
        the shared vocabulary the vote is taken in, and must be distinct inside
        one member.

    Returns
    -------
    H : SparseHypergraph
        Constants are the union of the identities, ordered by
        ``sorted(identities)``; a constant's type is the majority type among the
        members that carry it, ties broken by the smallest type id.  A fact
        ``(predicate, {identity, ...})`` is present iff strictly more than half
        the members assert it.  Facts are added in
        ``(predicate, constant indices)`` order.
    names : tuple[str, ...]
        The identity of each constant of ``H``, aligned with its node ids.

    Raises
    ------
    MajorityMergeError
        If ``members`` is empty, the two sequences disagree in length, an
        identity row does not match its member's constant count, or a member
        repeats an identity.
    """
    _validate(members, identities)
    total = len(members)

    counts: Counter[IdentifiedFact] = Counter()
    for H, names in zip(members, identities, strict=True):
        for _, node_set, label in H.iter_edges():
            counts[(label, frozenset(names[v] for v in node_set))] += 1

    types = _majority_types(members, identities)
    ordered = tuple(sorted(types))
    position = {name: index for index, name in enumerate(ordered)}

    kept: list[tuple[EdgeLabel, tuple[int, ...]]] = sorted(
        (label, tuple(sorted(position[name] for name in names)))
        for (label, names), count in counts.items()
        if 2 * count > total
    )

    return (
        SparseHypergraph(
            len(ordered),
            [frozenset(nodes) for _, nodes in kept],
            n_vertex_labels=max(H.n_vertex_labels for H in members),
            n_edge_labels=max(H.n_edge_labels for H in members),
            vertex_labels=[types[name] for name in ordered],
            edge_labels=[label for label, _ in kept],
        ),
        ordered,
    )


__all__ = [
    "Identity",
    "IdentifiedFact",
    "MajorityMergeError",
    "majority_merge",
]
