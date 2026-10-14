"""The isomorphism-invariant address map on constants, and two nauty forms.

The fact alphabet (:mod:`isalhg.core.fact_word`) addresses constants by rank
and leaves the choice of rank to its caller.  This module supplies the choice
the article adopts: the total order induced on the constants by nauty's
canonical labelling of the coloured Levi graph.  Because ``canon_label``
returns a permutation there are no residual ties --- the address map is
injective, which is what makes the fact word a *complete* isomorphism
invariant.

Invariance, stated exactly
--------------------------
The rank *vector* is canonical only **up to an automorphism**, and this is
measured, not hypothetical: on 2,000 random labelled knowledge bases with
``n <= 8`` the vector failed strict equivariance in 557 cases.  Write
``gamma`` for the canonical form of the coloured Levi graph and ``pi_H`` for
the labelling nauty returns.  For ``H' = tau(H)`` both ``pi_H`` and
``pi_{H'} . tau`` carry ``H`` onto the same ``gamma``, so they differ by some
``beta`` in ``Aut(gamma)``; restricted to the constant side (colours separate
constants from facts, so ``beta`` cannot mix them) that is a permutation
``rho`` of the ranks with ``rank_{H'} . tau = rho . rank_H``.

The *word* is invariant outright.  ``gamma`` is precisely the ranked structure
--- types by position, facts as position sets --- so ``rho``, being induced by
an automorphism of ``gamma``, leaves the type prefix and the multiset of fact
tokens fixed.  Hence ``fact_word(tau(H)) == fact_word(H)`` for every
isomorphism ``tau``.  Consumers must therefore compare *words*, never rank
vectors; ``canonical_ranks`` output is meaningful only relative to the
hypergraph it was computed from.

Colouring.  ``isalhg.core.levi_reduction.to_levi`` colours a constant node with
its type and a fact node with ``|Sigma_V| + predicate``, so the two witness
ranges are disjoint and no constant can be mapped onto a fact.  The colour
classes handed to nauty are an *ordered partition*, which loses absolute colour
identity; every certificate consumer here therefore prepends
``LeviGraph.color_signature()`` (T-TAe).

Also here are the two nauty tokenizations the experiments compare against the
fact word: the certificate as raw bytes (the existing ``nauty_levi_edit``
form), and the canonical adjacency rows as symbols.

``pynauty`` is imported inside function bodies, so importing this module never
requires it.
"""

from __future__ import annotations

from typing import Any

from isalhg.core.levi_reduction import LeviGraph, to_levi
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.errors import BackendUnavailableError


def _import_pynauty() -> Any:
    """Return the ``pynauty`` module, or raise with an install hint."""
    try:
        import pynauty
    except ImportError as exc:  # pragma: no cover - exercised only without pynauty
        raise BackendUnavailableError(
            "pynauty is required for canonical_order; install via `pip install pynauty`"
        ) from exc
    return pynauty


def _to_pynauty(levi: LeviGraph) -> Any:
    """Build a ``pynauty.Graph`` from ``levi``, mirroring ``pynauty_levi._to_pynauty``."""
    pynauty = _import_pynauty()
    adjacency: dict[int, list[int]] = {node: [] for node in range(levi.n_nodes)}
    for u, v in levi.edges:
        adjacency[u].append(v)
        adjacency[v].append(u)
    return pynauty.Graph(
        number_of_vertices=levi.n_nodes,
        directed=False,
        adjacency_dict=adjacency,
        vertex_coloring=levi.color_classes(),
    )


def canonical_ranks(H: SparseHypergraph) -> tuple[int, ...]:
    """Return the isomorphism-invariant total order ``pi`` on the constants of ``H``.

    ``pynauty.canon_label(g)`` returns ``pi`` with ``pi[i]`` the *original* Levi
    node sitting at canonical position ``i``.  Filtering that sequence to the
    constant-side nodes (ids below ``n_vertex_nodes``) and keeping the order
    yields a total order on the constants alone.

    The returned vector is canonical **up to an automorphism** of the canonical
    form, so it is meaningful only relative to ``H``: two isomorphic knowledge
    bases may receive rank vectors that do not correspond under the
    isomorphism.  What is invariant is the word these ranks induce --- see the
    module docstring for the statement and its proof sketch.  Never compare
    rank vectors across knowledge bases; compare
    :func:`isalhg.metric_space.distances.fact_levenshtein.fact_word` output.

    Parameters
    ----------
    H : SparseHypergraph
        The knowledge base.  ``n_nodes == 0`` is accepted and yields ``()``.

    Returns
    -------
    tuple[int, ...]
        ``rank[v]`` is the canonical rank of constant ``v``, a permutation of
        ``range(H.n_nodes)``.

    Raises
    ------
    isalhg.errors.BackendUnavailableError
        If ``pynauty`` is not installed.
    """
    if H.n_nodes == 0:
        return ()
    pynauty = _import_pynauty()
    levi = to_levi(H)
    pi = pynauty.canon_label(_to_pynauty(levi))
    rank: list[int] = [-1] * levi.n_vertex_nodes
    position = 0
    for node in pi:
        if node < levi.n_vertex_nodes:
            rank[node] = position
            position += 1
    return tuple(rank)


def nauty_certificate_bytes(H: SparseHypergraph) -> bytes:
    """Return ``color_signature ++ pynauty.certificate`` for the Levi graph of ``H``.

    Byte-for-byte the fingerprint of
    :class:`isalhg.iso_backends.pynauty_levi.PynautyLeviBackend` and of the
    ``nauty_levi_edit`` representation, so a distance built on it agrees with
    both on isomorphism.

    Parameters
    ----------
    H : SparseHypergraph
        The knowledge base.

    Returns
    -------
    bytes
        ``b""`` for the empty hypergraph; otherwise the colour signature
        followed by the nauty certificate.

    Raises
    ------
    isalhg.errors.BackendUnavailableError
        If ``pynauty`` is not installed.
    """
    if H.n_nodes == 0:
        return b""
    pynauty = _import_pynauty()
    levi = to_levi(H)
    return levi.color_signature() + bytes(pynauty.certificate(_to_pynauty(levi)))


def nauty_certificate_rows(H: SparseHypergraph) -> tuple[tuple[int, ...], ...]:
    """Return the canonical Levi adjacency rows of ``H``, one symbol per node.

    Row ``i`` is ``(colour of the node at canonical position i, *sorted
    canonical positions of its neighbours)``.  This is the second tokenization
    of the same nauty canonical form: ``nauty_certificate_bytes`` spends one
    symbol per byte, this spends one symbol per Levi node.

    Carrying the colour inside the row is what keeps the arm exact at zero.
    The rows alone determine the *uncoloured* canonical graph, but the ordered
    partition handed to nauty records only the relative order of the colour
    classes, so two Levi graphs with different absolute colours --- different
    types, different predicates --- could share their rows.  With the colour in
    the row the whole coloured graph is determined, hence equal row sequences
    imply isomorphic knowledge bases.

    Parameters
    ----------
    H : SparseHypergraph
        The knowledge base.

    Returns
    -------
    tuple[tuple[int, ...], ...]
        One row per Levi node --- constants and facts alike --- in canonical
        order.  ``()`` for the empty hypergraph.

    Raises
    ------
    isalhg.errors.BackendUnavailableError
        If ``pynauty`` is not installed.
    """
    if H.n_nodes == 0:
        return ()
    pynauty = _import_pynauty()
    levi = to_levi(H)
    pi = pynauty.canon_label(_to_pynauty(levi))

    position: list[int] = [0] * levi.n_nodes
    for i, node in enumerate(pi):
        position[node] = i

    neighbours: list[list[int]] = [[] for _ in range(levi.n_nodes)]
    for u, v in levi.edges:
        neighbours[position[u]].append(position[v])
        neighbours[position[v]].append(position[u])

    return tuple((levi.colors[pi[i]], *sorted(neighbours[i])) for i in range(levi.n_nodes))


__all__ = [
    "canonical_ranks",
    "nauty_certificate_bytes",
    "nauty_certificate_rows",
]
