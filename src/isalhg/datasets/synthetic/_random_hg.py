"""Deterministic stdlib random-hypergraph builder shared by the T-M2 corpora.

Both HGED corpora -- the exact-HGED correlation corpus and the perturbation
ladder -- need small random hypergraphs drawn from a seeded stdlib
:class:`random.Random` (no numpy / XGI in the generation path, unlike
``erdos_renyi.py`` which delegates to XGI). Isolated vertices are allowed; a
caller that needs connectivity or an ``arity <= k`` cap filters downstream, as
the edit-op docstring in :mod:`isalhg.core.sparse_hypergraph` notes.

Restriction: Python stdlib + ``isalhg.core`` only.
"""

from __future__ import annotations

import random

from isalhg.core.sparse_hypergraph import SparseHypergraph


def random_hypergraph(
    *,
    n_nodes: int,
    n_edges: int,
    arity_range: tuple[int, int],
    rng: random.Random,
    n_vertex_labels: int = 1,
    n_edge_labels: int = 1,
) -> SparseHypergraph:
    """Return a random hypergraph over ``n_nodes`` vertices with up to ``n_edges`` edges.

    Each hyperedge spans a uniformly random vertex subset whose size is drawn
    uniformly from ``arity_range`` (clamped to ``[1, n_nodes]``). Duplicate
    ``(label, member-set)`` pairs are silently dropped by
    :meth:`SparseHypergraph.add_hyperedge`, so the realised edge count may be
    below ``n_edges``. Vertex and edge labels are drawn uniformly from their
    vocabularies (all-zero under the trivial vocabulary).

    Parameters
    ----------
    n_nodes : int
        Number of vertices (``>= 1``).
    n_edges : int
        Number of hyperedge insertion attempts (``>= 0``).
    arity_range : tuple[int, int]
        ``(min_arity, max_arity)`` for the drawn hyperedges.
    rng : random.Random
        Seeded stdlib RNG; the caller pins and reports the seed.
    n_vertex_labels, n_edge_labels : int, optional
        Label-vocabulary sizes. Default ``1`` (trivial, all-zero labels).

    Returns
    -------
    SparseHypergraph
        The generated hypergraph.

    Raises
    ------
    ValueError
        If ``n_nodes < 1`` or the arity range is empty after clamping.
    """
    if n_nodes < 1:
        raise ValueError(f"n_nodes must be >= 1, got {n_nodes}")
    lo = max(1, arity_range[0])
    hi = min(arity_range[1], n_nodes)
    if hi < lo:
        raise ValueError(f"empty arity range {arity_range} after clamping to n_nodes={n_nodes}")
    vertex_labels = [rng.randrange(n_vertex_labels) for _ in range(n_nodes)]
    H = SparseHypergraph(
        n_nodes,
        n_vertex_labels=n_vertex_labels,
        n_edge_labels=n_edge_labels,
        vertex_labels=vertex_labels,
    )
    for _ in range(n_edges):
        size = rng.randint(lo, hi)
        members = rng.sample(range(n_nodes), size)
        label = rng.randrange(n_edge_labels)
        H.add_hyperedge(members, label=label)
    return H
