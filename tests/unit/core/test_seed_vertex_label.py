"""Unit tests for ``seed_vertex_label`` / ``canonical_fingerprint``.

The canonical string emits the label of every vertex it *creates* and never the
label of its seed. ``seed_vertex_label`` recovers the missing label by removing
the emitted labels from the vertex-label multiset of ``H``. These tests pin the
recovery against the two production seed cascades, which give the answer
independently: the neighbour-degree cascade seeds on a maximal-label vertex,
the ``xi`` cascade on an ``argmax_lex xi`` vertex.
"""

from __future__ import annotations

import pytest

from isalhg.core.canonical import (
    canonical_fingerprint,
    canonical_string,
    seed_vertex_label,
)
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.core.structural_tuples import max_neighbor_degree_nodes, max_xi_nodes
from isalhg.errors import InvalidLabelError

pytestmark = pytest.mark.unit

_NBRDEG_VARIANTS = ("greedy_min_nbrdeg", "greedy_single_nbrdeg", "greedy_min_complete")
_XI_VARIANTS = ("greedy_min", "greedy_single")


def _labelled_path(labels: list[int], n_vertex_labels: int) -> SparseHypergraph:
    n = len(labels)
    return SparseHypergraph(
        n_nodes=n,
        hyperedges=[{i, i + 1} for i in range(n - 1)],
        n_vertex_labels=n_vertex_labels,
        vertex_labels=labels,
    )


def test_trivial_vocabulary_seed_label_is_zero() -> None:
    H = _labelled_path([0, 0, 0], n_vertex_labels=1)
    assert seed_vertex_label(H, canonical_string(H)) == 0


def test_empty_hypergraph_seed_label_is_zero() -> None:
    assert seed_vertex_label(SparseHypergraph(n_nodes=0, hyperedges=[]), "") == 0


def test_single_vertex_seed_label_is_its_own_label() -> None:
    H = SparseHypergraph(n_nodes=1, hyperedges=[], n_vertex_labels=3, vertex_labels=[2])
    assert seed_vertex_label(H, "") == 2


@pytest.mark.parametrize("algorithm", _NBRDEG_VARIANTS)
def test_nbrdeg_seed_label_is_the_maximal_vertex_label(algorithm: str) -> None:
    H = _labelled_path([0, 2, 1, 2], n_vertex_labels=3)
    ell, _ = canonical_fingerprint(H, algorithm=algorithm)
    assert ell == max(H.vertex_label(v) for v in H.nodes())
    assert ell == H.vertex_label(max_neighbor_degree_nodes(H)[0])


@pytest.mark.parametrize("algorithm", _XI_VARIANTS)
def test_xi_seed_label_matches_the_xi_seed_set(algorithm: str) -> None:
    H = _labelled_path([0, 2, 1, 2], n_vertex_labels=3)
    ell, _ = canonical_fingerprint(H, algorithm=algorithm)
    seeds = max_xi_nodes(H, 3)
    assert {H.vertex_label(s) for s in seeds} == {ell}


@pytest.mark.parametrize(
    "algorithm",
    (*_NBRDEG_VARIANTS, *_XI_VARIANTS, "exhaustive", "pruned_exhaustive"),
)
def test_recovered_label_completes_the_emitted_multiset(algorithm: str) -> None:
    """hist(H) == {seed label} + labels emitted by ``w*``, for every variant."""
    from collections import Counter

    from isalhg.core.instructions import TokenV, parse

    H = SparseHypergraph(
        n_nodes=5,
        hyperedges=[{0, 1, 2}, {2, 3}, {3, 4}, {0, 4}],
        n_vertex_labels=3,
        vertex_labels=[1, 0, 2, 2, 1],
    )
    ell, w = canonical_fingerprint(H, algorithm=algorithm)
    emitted: Counter[int] = Counter()
    for token in parse(w):
        if isinstance(token, TokenV):
            emitted.update(token.new_node_labels)
    emitted[ell] += 1
    assert emitted == Counter(H.vertex_label(v) for v in H.nodes())


def test_seed_label_rejects_a_string_that_creates_too_few_vertices() -> None:
    H = _labelled_path([0, 1], n_vertex_labels=2)
    with pytest.raises(InvalidLabelError):
        seed_vertex_label(H, "")


def test_seed_label_rejects_a_string_emitting_a_label_h_does_not_carry() -> None:
    H = _labelled_path([0, 1], n_vertex_labels=3)
    other = _labelled_path([2, 2], n_vertex_labels=3)
    with pytest.raises(InvalidLabelError):
        seed_vertex_label(H, canonical_string(other))
