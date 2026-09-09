"""Builders shared by the language-layer unit tests.

Small, deterministic constructors only: a random labelled knowledge base, the
two structural edits the reach definition is written in terms of (insert one
fact, substitute one fact), and an independent isomorphism oracle that does not
go through the fact word, so the delete-and-match implementation can be checked
against something it does not share code with.
"""

from __future__ import annotations

import random

from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.iso_backends.canonical_order import nauty_certificate_bytes
from isalhg.language.reach import compact_constants, remove_facts

DEFAULT_TYPES = 3
DEFAULT_PREDS = 2


def random_kb(
    rng: random.Random,
    *,
    n_lo: int = 5,
    n_hi: int = 9,
    m_lo: int = 4,
    m_hi: int = 8,
    arity_hi: int = 4,
    n_types: int = DEFAULT_TYPES,
    n_preds: int = DEFAULT_PREDS,
) -> SparseHypergraph:
    """Return a random labelled knowledge base with distinct ``(predicate, members)`` facts."""
    n = rng.randint(n_lo, n_hi)
    m = rng.randint(m_lo, m_hi)
    seen: set[tuple[int, frozenset[int]]] = set()
    edges: list[frozenset[int]] = []
    labels: list[int] = []
    for _ in range(m * 12):
        if len(edges) == m:
            break
        arity = rng.randint(2, min(arity_hi, n))
        members = frozenset(rng.sample(range(n), arity))
        label = rng.randrange(n_preds)
        if (label, members) in seen:
            continue
        seen.add((label, members))
        edges.append(members)
        labels.append(label)
    return SparseHypergraph(
        n_nodes=n,
        hyperedges=edges,
        n_vertex_labels=n_types,
        n_edge_labels=n_preds,
        vertex_labels=[rng.randrange(n_types) for _ in range(n)],
        edge_labels=labels,
    )


def rebuild(
    H: SparseHypergraph,
    facts: list[tuple[int, frozenset[int]]],
) -> SparseHypergraph:
    """Return a copy of ``H`` carrying exactly ``facts``, constants untouched."""
    return SparseHypergraph(
        n_nodes=H.n_nodes,
        hyperedges=[members for _, members in facts],
        n_vertex_labels=H.n_vertex_labels,
        n_edge_labels=H.n_edge_labels,
        vertex_labels=[H.vertex_label(v) for v in range(H.n_nodes)],
        edge_labels=[label for label, _ in facts],
    )


def facts_of(H: SparseHypergraph) -> list[tuple[int, frozenset[int]]]:
    """Return ``H``'s facts as ``(predicate, member set)`` pairs in edge order."""
    return [(label, members) for _, members, label in H.iter_edges()]


def new_fact(
    rng: random.Random, H: SparseHypergraph, arity_hi: int = 4
) -> tuple[int, frozenset[int]] | None:
    """Return a fact over ``H``'s constants that ``H`` does not already carry."""
    present = set(facts_of(H))
    for _ in range(200):
        arity = rng.randint(2, min(arity_hi, H.n_nodes))
        candidate = (rng.randrange(H.n_edge_labels), frozenset(rng.sample(range(H.n_nodes), arity)))
        if candidate not in present:
            return candidate
    return None


def with_inserted_fact(
    rng: random.Random, H: SparseHypergraph, arity_hi: int = 4
) -> SparseHypergraph | None:
    """Return ``H`` plus one new fact, or ``None`` when no new fact fits."""
    fact = new_fact(rng, H, arity_hi)
    if fact is None:
        return None
    return rebuild(H, [*facts_of(H), fact])


def with_substituted_fact(
    rng: random.Random, H: SparseHypergraph, arity_hi: int = 4
) -> SparseHypergraph | None:
    """Return ``H`` with one fact swapped for a new one, or ``None`` when impossible."""
    if H.n_edges == 0:
        return None
    fact = new_fact(rng, H, arity_hi)
    if fact is None:
        return None
    kept = facts_of(H)
    del kept[rng.randrange(len(kept))]
    return rebuild(H, [*kept, fact])


def transported_remainder(
    K: SparseHypergraph,
    deleted_from_k: tuple[int, ...],
    K2: SparseHypergraph,
    deleted_from_k2: tuple[int, ...],
    node_map: tuple[int | None, ...],
) -> tuple[SparseHypergraph, SparseHypergraph]:
    """Return ``(compact(K2 - B) carried over by node_map, compact(K - A))``.

    ``node_map`` is stated over ``K2``'s constants and is partial, so it is
    re-expressed as a permutation of the compacted remainder before
    :func:`isalhg.core.sparse_hypergraph.permute` can apply it.  The two results
    are equal exactly when the alignment's map is a genuine isomorphism.
    """
    left, left_survivors = compact_constants(remove_facts(K, deleted_from_k))
    right, right_survivors = compact_constants(remove_facts(K2, deleted_from_k2))
    position = {v: u for u, v in enumerate(left_survivors)}
    sigma = [position[node_map[v]] for v in right_survivors]
    return permute(right, sigma), left


def nauty_iso(H1: SparseHypergraph, H2: SparseHypergraph) -> bool:
    """Return whether ``H1`` and ``H2`` are isomorphic, judged without the fact word.

    The reach implementation compares canonical *words*; this compares nauty
    certificates of the coloured Levi graphs, so a brute-force reference built
    on it shares no code with the thing it checks.
    """
    return nauty_certificate_bytes(H1) == nauty_certificate_bytes(H2)
