"""Exact label-preserving isomorphism oracle + labelled-pair strategy.

An independent oracle, deliberately sharing no machinery with the backends it
checks. For ``n <= 5`` an exhaustive search over the ``n!`` bijections is both
exact and cheap.

Written at T-TAb, when the Levi backends could not serve as the labelled oracle:
``LeviGraph.color_classes`` drops empty colour classes, so the ordered partition
handed to nauty had forgotten which label id each cell carried and a hypergraph
with all vertices labelled ``0`` was reported isomorphic to one with all
vertices labelled ``1``. T-TAe repaired that (the backends now pair the
certificate with ``LeviGraph.color_signature``), and
``tests/property/test_levi_labelled_oracle.py`` holds them to this oracle.
"""

from __future__ import annotations

from itertools import permutations

from hypothesis import strategies as st

from isalhg.core.sparse_hypergraph import SparseHypergraph


def brute_force_iso(H1: SparseHypergraph, H2: SparseHypergraph) -> bool:
    """Return whether a label-preserving bijection ``V1 -> V2`` exists.

    Exhaustive over all ``n!`` bijections; intended for ``n <= 6``.
    """
    if (H1.n_nodes, H1.n_edges) != (H2.n_nodes, H2.n_edges):
        return False
    if (H1.n_vertex_labels, H1.n_edge_labels) != (H2.n_vertex_labels, H2.n_edge_labels):
        return False

    target = {(frozenset(m), ell) for _, m, ell in H2.iter_edges()}
    source = [(frozenset(m), ell) for _, m, ell in H1.iter_edges()]
    labels_1 = [H1.vertex_label(v) for v in range(H1.n_nodes)]
    labels_2 = [H2.vertex_label(v) for v in range(H2.n_nodes)]

    for phi in permutations(range(H2.n_nodes)):
        if any(labels_2[phi[v]] != labels_1[v] for v in range(H1.n_nodes)):
            continue
        if {(frozenset(phi[v] for v in m), ell) for m, ell in source} == target:
            return True
    return False


@st.composite
def _connected_structure(draw, max_n: int, max_arity: int) -> tuple[int, list[frozenset[int]]]:
    """A connected hyperedge list: a random spanning tree plus extra edges."""
    n = draw(st.integers(min_value=2, max_value=max_n))
    perm = draw(st.permutations(list(range(n))))
    edges = [
        frozenset({perm[i], perm[draw(st.integers(min_value=0, max_value=i - 1))]})
        for i in range(1, n)
    ]
    for _ in range(draw(st.integers(min_value=0, max_value=2))):
        arity = draw(st.integers(min_value=2, max_value=min(max_arity, n)))
        members = draw(
            st.sets(st.integers(min_value=0, max_value=n - 1), min_size=arity, max_size=arity)
        )
        edges.append(frozenset(members))
    return n, edges


@st.composite
def labelled_hypergraph_pair(
    draw, max_n: int = 5, max_arity: int = 3
) -> tuple[SparseHypergraph, SparseHypergraph]:
    """Two labellings of one structure over a shared non-trivial vocabulary.

    Sharing the structure concentrates sampling on the regime the seed-label
    deficiency lives in: with the bare canonical string, roughly 5% of such
    pairs are non-isomorphic yet indistinguishable, against roughly 1% when the
    two structures are drawn independently. Structural diversity is covered by
    the unlabelled properties.
    """
    n_labels = draw(st.integers(min_value=2, max_value=3))
    n_nodes, members = draw(_connected_structure(max_n=max_n, max_arity=max_arity))
    labellings = draw(
        st.tuples(
            *(
                st.lists(
                    st.integers(min_value=0, max_value=n_labels - 1),
                    min_size=n_nodes,
                    max_size=n_nodes,
                )
                for _ in range(2)
            )
        )
    )
    return tuple(  # type: ignore[return-value]
        SparseHypergraph(
            n_nodes=n_nodes,
            hyperedges=members,
            n_vertex_labels=n_labels,
            vertex_labels=labels,
        )
        for labels in labellings
    )
