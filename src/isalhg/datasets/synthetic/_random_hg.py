"""Deterministic stdlib random-hypergraph builder shared by the T-M2 corpora.

Both HGED corpora -- the exact-HGED correlation corpus and the perturbation
ladder -- need small random hypergraphs drawn from a seeded stdlib
:class:`random.Random` (no numpy / XGI in the generation path, unlike
``erdos_renyi.py`` which delegates to XGI).

:func:`random_hypergraph` is the unconstrained builder (isolated vertices
allowed). :func:`random_connected_hypergraph` rejection-samples until
connected and falls back to a backbone constructor if sampling exhausts its
budget; callers receive the number of attempts so they can report the
acceptance rate (T-M2c, D-CONN1: the article's domain is connected
hypergraphs, conditioning on connectivity changes the ensemble and the
acceptance rate documents the bias, as required for the paper).

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


def _backbone_connected_hypergraph(
    *,
    n_nodes: int,
    n_edges: int,
    arity_range: tuple[int, int],
    rng: random.Random,
    n_vertex_labels: int = 1,
    n_edge_labels: int = 1,
) -> SparseHypergraph:
    """Build a connected hypergraph via a spanning star plus random edges.

    Used as the fallback when :func:`random_connected_hypergraph` exhausts its
    rejection-sampling budget. Wires a star from vertex 0 to every other
    vertex via a 2-edge (guaranteeing connectivity), then adds up to
    ``n_edges`` additional random hyperedges (duplicates silently dropped).

    Parameters
    ----------
    n_nodes : int
        Number of vertices (``>= 1``).
    n_edges : int
        Number of additional random hyperedge insertion attempts after the
        star backbone.
    arity_range : tuple[int, int]
        ``(min_arity, max_arity)`` for the random hyperedges.
    rng : random.Random
        Seeded stdlib RNG.
    n_vertex_labels, n_edge_labels : int, optional
        Label-vocabulary sizes. Default ``1``.

    Returns
    -------
    SparseHypergraph
        A connected hypergraph (guaranteed).
    """
    vertex_labels = [rng.randrange(n_vertex_labels) for _ in range(n_nodes)]
    H = SparseHypergraph(
        n_nodes,
        n_vertex_labels=n_vertex_labels,
        n_edge_labels=n_edge_labels,
        vertex_labels=vertex_labels,
    )
    # Spanning star centred at vertex 0.
    for v in range(1, n_nodes):
        elabel = rng.randrange(n_edge_labels)
        H.add_hyperedge([0, v], label=elabel)
    lo = max(1, arity_range[0])
    hi = min(arity_range[1], n_nodes)
    if hi >= lo:
        for _ in range(n_edges):
            size = rng.randint(lo, hi)
            members = rng.sample(range(n_nodes), size)
            label = rng.randrange(n_edge_labels)
            H.add_hyperedge(members, label=label)
    return H


def random_connected_hypergraph(
    *,
    n_nodes: int,
    n_edges: int,
    arity_range: tuple[int, int],
    rng: random.Random,
    n_vertex_labels: int = 1,
    n_edge_labels: int = 1,
    max_attempts: int = 200,
) -> tuple[SparseHypergraph, int]:
    """Rejection-sample a connected random hypergraph.

    Draws from :func:`random_hypergraph` until the result satisfies
    :meth:`SparseHypergraph.is_connected`. If ``max_attempts`` is exhausted,
    falls back to :func:`_backbone_connected_hypergraph`, which guarantees
    connectivity by construction (spanning star).

    The caller may accumulate ``n_attempts`` across a corpus to estimate the
    *acceptance rate* and report it; conditioning on connectivity changes the
    ensemble, particularly at low ``m/n`` (T-M2c, D-CONN1: the paper must say
    "connected ER" and report the acceptance rate).

    Parameters
    ----------
    n_nodes : int
        Number of vertices (``>= 1``).
    n_edges : int
        Number of hyperedge insertion attempts (``>= 0``).
    arity_range : tuple[int, int]
        ``(min_arity, max_arity)`` for drawn hyperedges.
    rng : random.Random
        Seeded stdlib RNG.
    n_vertex_labels, n_edge_labels : int, optional
        Label-vocabulary sizes. Default ``1``.
    max_attempts : int, optional
        Maximum rejection-sampling draws before the backbone fallback.
        Default ``200``.

    Returns
    -------
    tuple[SparseHypergraph, int]
        ``(H, n_attempts)`` where ``H`` is always connected.
        ``n_attempts <= max_attempts`` means pure rejection succeeded;
        ``n_attempts == max_attempts + 1`` means the backbone was used.

    Raises
    ------
    ValueError
        If ``n_nodes < 1`` or the arity range is empty after clamping.
    """
    if n_nodes == 1:
        # A single-vertex hypergraph is connected regardless of edge count.
        return (
            random_hypergraph(
                n_nodes=1,
                n_edges=n_edges,
                arity_range=arity_range,
                rng=rng,
                n_vertex_labels=n_vertex_labels,
                n_edge_labels=n_edge_labels,
            ),
            1,
        )
    for attempt in range(1, max_attempts + 1):
        H = random_hypergraph(
            n_nodes=n_nodes,
            n_edges=n_edges,
            arity_range=arity_range,
            rng=rng,
            n_vertex_labels=n_vertex_labels,
            n_edge_labels=n_edge_labels,
        )
        if H.is_connected():
            return H, attempt
    H = _backbone_connected_hypergraph(
        n_nodes=n_nodes,
        n_edges=n_edges,
        arity_range=arity_range,
        rng=rng,
        n_vertex_labels=n_vertex_labels,
        n_edge_labels=n_edge_labels,
    )
    return H, max_attempts + 1
