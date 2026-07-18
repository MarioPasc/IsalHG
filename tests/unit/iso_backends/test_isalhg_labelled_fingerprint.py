"""Regression: the IsalHG fingerprint separates labelled non-isomorphic pairs.

Counterexample 4.3 of the Theorem A proof: with ``|Sigma_V| = 2``, the two
2-vertex one-edge hypergraphs with labels ``(0, 0)`` and ``(1, 0)`` share the
canonical string ``V[0;1;1;0]`` under every variant -- the seed's own label is
never emitted -- so the pre-T-TAb backend answered ``are_isomorphic == True``.
The augmented fingerprint ``(seed label, w*)`` separates them.

The trivial-vocabulary format is pinned too: with one vertex label the seed
label carries no information and the fingerprint stays byte-identical to the
bare canonical string, so no preprint artefact is invalidated.
"""

from __future__ import annotations

import pytest

from isalhg.core.canonical import canonical_string
from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.iso_backends.isalhg_backend import IsalHGBackend

pytestmark = pytest.mark.unit

_VARIANTS = (
    "greedy_min",
    "greedy_min_nbrdeg",
    "canonical",
    "exhaustive",
)


def _one_edge(labels: list[int]) -> SparseHypergraph:
    return SparseHypergraph(
        n_nodes=2,
        hyperedges=[{0, 1}],
        n_vertex_labels=2,
        vertex_labels=labels,
    )


@pytest.mark.parametrize("algorithm", _VARIANTS)
def test_seed_label_counterexample_no_longer_collides(algorithm: str) -> None:
    H_a, H_b = _one_edge([0, 0]), _one_edge([1, 0])
    backend = IsalHGBackend(algorithm=algorithm)

    # The bare canonical string is the same -- that is the whole defect.
    assert canonical_string(H_a, algorithm=algorithm) == canonical_string(H_b, algorithm=algorithm)
    assert backend.fingerprint(H_a) != backend.fingerprint(H_b)
    assert not backend.are_isomorphic(H_a, H_b)


@pytest.mark.parametrize("algorithm", _VARIANTS)
def test_labelled_fingerprint_invariant_under_permutation(algorithm: str) -> None:
    H = SparseHypergraph(
        n_nodes=4,
        hyperedges=[{0, 1, 2}, {2, 3}],
        n_vertex_labels=3,
        vertex_labels=[1, 0, 2, 1],
    )
    backend = IsalHGBackend(algorithm=algorithm)
    assert backend.fingerprint(H) == backend.fingerprint(permute(H, [2, 0, 3, 1]))
    assert backend.are_isomorphic(H, permute(H, [2, 0, 3, 1]))


def test_labelled_fingerprint_carries_the_seed_label_prefix() -> None:
    H_b = _one_edge([1, 0])
    assert IsalHGBackend().fingerprint(H_b) == b"1|V[0;1;1;0]"


def test_trivial_vocabulary_fingerprint_is_the_bare_canonical_string() -> None:
    H = SparseHypergraph(n_nodes=3, hyperedges=[{0, 1}, {1, 2}])
    assert H.n_vertex_labels == 1
    backend = IsalHGBackend()
    assert backend.fingerprint(H) == canonical_string(H, algorithm="greedy_min_nbrdeg").encode(
        "utf-8"
    )


def test_empty_hypergraph_fingerprint_raises() -> None:
    """fingerprint(∅) must raise DegenerateHypergraphError, not return b''.

    Before T-M1c the fingerprint of the empty hypergraph was b'' — identical
    to the single-vertex hypergraph — so are_isomorphic(∅, •) returned True
    and d_I(∅, •) = 0 on a non-isomorphic pair (identity of indiscernibles
    violated).  The fix restricts the domain to n ≥ 1.
    """
    from isalhg.errors import DegenerateHypergraphError

    with pytest.raises(DegenerateHypergraphError):
        IsalHGBackend().fingerprint(SparseHypergraph(n_nodes=0, hyperedges=[]))
