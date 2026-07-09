"""Unit tests for :class:`isalhg.metric_space.distances.isalhg_levenshtein`.

``d_I`` must be 0 on isomorphic pairs (``w*`` is iso-invariant) and > 0 on
non-isomorphic pairs, including the hard same-parameter STS(13) pair.
"""

from __future__ import annotations

import pytest

from isalhg.core.canonical import canonical_string, required_k
from isalhg.core.instructions import parse
from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.metric_space import registry
from isalhg.metric_space.distances.isalhg_levenshtein import IsalHGLevenshtein

pytestmark = pytest.mark.unit

# d_I hard-depends on rapidfuzz; skip the whole module if it is absent.
pytest.importorskip("rapidfuzz")


def _path_hypergraph() -> SparseHypergraph:
    return SparseHypergraph(
        n_nodes=4, hyperedges=[frozenset({0, 1}), frozenset({1, 2}), frozenset({2, 3})]
    )


class TestPairwise:
    def test_zero_on_iso_pair(
        self, iso_pair_small: tuple[SparseHypergraph, SparseHypergraph, list[int]]
    ) -> None:
        h1, h2, _ = iso_pair_small
        assert IsalHGLevenshtein().pairwise(h1, h2) == 0.0

    def test_zero_on_permuted_design_fixture(self, fano_plane: SparseHypergraph) -> None:
        d = IsalHGLevenshtein()
        assert d.pairwise(fano_plane, permute(fano_plane, [6, 5, 4, 3, 2, 1, 0])) == 0.0

    def test_self_distance_zero(self, sts_9: SparseHypergraph) -> None:
        assert IsalHGLevenshtein().pairwise(sts_9, sts_9) == 0.0

    def test_positive_on_non_iso(
        self, non_iso_pair_small: tuple[SparseHypergraph, SparseHypergraph]
    ) -> None:
        h1, h2 = non_iso_pair_small
        assert IsalHGLevenshtein().pairwise(h1, h2) > 0.0

    def test_distinguishes_two_sts13(
        self, sts_13_pair: tuple[SparseHypergraph, SparseHypergraph]
    ) -> None:
        # Same parameters, genuinely non-isomorphic — the hard case for w*.
        a, b = sts_13_pair
        assert IsalHGLevenshtein().pairwise(a, b) > 0.0

    def test_symmetry(self, non_iso_pair_small: tuple[SparseHypergraph, SparseHypergraph]) -> None:
        h1, h2 = non_iso_pair_small
        d = IsalHGLevenshtein()
        assert d.pairwise(h1, h2) == d.pairwise(h2, h1)

    def test_normalized_in_unit_interval(
        self, non_iso_pair_small: tuple[SparseHypergraph, SparseHypergraph]
    ) -> None:
        h1, h2 = non_iso_pair_small
        value = IsalHGLevenshtein(normalize=True).pairwise(h1, h2)
        assert 0.0 < value <= 1.0

    def test_name(self) -> None:
        assert IsalHGLevenshtein().name == "isalhg_levenshtein"
        assert IsalHGLevenshtein(normalize=True).name == "isalhg_levenshtein_normalized"


class TestMatrix:
    def _corpus(
        self,
        fano_plane: SparseHypergraph,
        sts_9: SparseHypergraph,
        single_edge_hypergraph: SparseHypergraph,
        iso_pair_small: tuple[SparseHypergraph, SparseHypergraph, list[int]],
        non_iso_pair_small: tuple[SparseHypergraph, SparseHypergraph],
    ) -> list[SparseHypergraph]:
        i1, i2, _ = iso_pair_small
        h1, h2 = non_iso_pair_small
        return [
            fano_plane,
            permute(fano_plane, [1, 2, 3, 4, 5, 6, 0]),
            sts_9,
            permute(sts_9, [1, 2, 3, 4, 5, 6, 7, 8, 0]),
            i1,
            i2,
            h1,
            h2,
            single_edge_hypergraph,
            _path_hypergraph(),
        ]

    def test_matrix_symmetric_zero_diagonal(
        self,
        fano_plane: SparseHypergraph,
        sts_9: SparseHypergraph,
        single_edge_hypergraph: SparseHypergraph,
        iso_pair_small: tuple[SparseHypergraph, SparseHypergraph, list[int]],
        non_iso_pair_small: tuple[SparseHypergraph, SparseHypergraph],
    ) -> None:
        np = pytest.importorskip("numpy")
        corpus = self._corpus(
            fano_plane, sts_9, single_edge_hypergraph, iso_pair_small, non_iso_pair_small
        )
        matrix = IsalHGLevenshtein().matrix(corpus)
        assert matrix.shape == (10, 10)
        assert np.allclose(matrix, matrix.T)
        assert np.allclose(np.diag(matrix), 0.0)
        # Isomorphic members are at distance 0.
        assert matrix[0, 1] == 0.0  # fano vs permuted fano
        assert matrix[2, 3] == 0.0  # sts9 vs permuted sts9
        assert matrix[4, 5] == 0.0  # iso pair
        # Non-isomorphic members are separated.
        assert matrix[6, 7] > 0.0

    def test_empty_corpus(self) -> None:
        pytest.importorskip("numpy")
        matrix = IsalHGLevenshtein().matrix([])
        assert matrix.shape == (0, 0)


class TestLabelled:
    """``d_I`` must separate hypergraphs that differ only in the seed's label.

    ``w*`` never emits the seed label, so without the seed-label prefix the two
    hypergraphs below share their token sequence and ``d_I`` reads 0 on a
    non-isomorphic pair -- identity of indiscernibles fails (Corollary A).
    """

    @staticmethod
    def _one_edge(labels: list[int]) -> SparseHypergraph:
        return SparseHypergraph(
            n_nodes=2, hyperedges=[frozenset({0, 1})], n_vertex_labels=2, vertex_labels=labels
        )

    def test_positive_on_seed_label_counterexample(self) -> None:
        d = IsalHGLevenshtein()
        assert d.pairwise(self._one_edge([0, 0]), self._one_edge([1, 0])) == 1.0

    def test_zero_on_labelled_iso_pair(self) -> None:
        H = SparseHypergraph(
            n_nodes=4,
            hyperedges=[frozenset({0, 1, 2}), frozenset({2, 3})],
            n_vertex_labels=3,
            vertex_labels=[1, 0, 2, 1],
        )
        assert IsalHGLevenshtein().pairwise(H, permute(H, [2, 0, 3, 1])) == 0.0

    def test_matrix_separates_the_counterexample(self) -> None:
        np = pytest.importorskip("numpy")
        matrix = IsalHGLevenshtein().matrix([self._one_edge([0, 0]), self._one_edge([1, 0])])
        assert np.allclose(np.diag(matrix), 0.0)
        assert matrix[0, 1] == 1.0

    def test_trivial_vocabulary_symbols_carry_no_seed_prefix(
        self, non_iso_pair_small: tuple[SparseHypergraph, SparseHypergraph]
    ) -> None:
        """With one vertex label the sequence is exactly the token sequence."""
        h1, _ = non_iso_pair_small
        assert h1.n_vertex_labels == 1
        k = required_k(h1)
        symbols = IsalHGLevenshtein(k=k).fingerprint(h1)
        assert symbols == tuple(parse(canonical_string(h1, k=k, algorithm="greedy_min_nbrdeg")))


class TestRegistry:
    def test_registered_and_retrievable(self) -> None:
        d = registry.get_distance("isalhg_levenshtein")
        assert isinstance(d, IsalHGLevenshtein)
        assert "isalhg_levenshtein" in registry.available_distances()


# ---------------------------------------------------------------------------
# T-TAg hardenings
# ---------------------------------------------------------------------------


class TestGuard:
    """IsalHGLevenshtein must reject non-canonical algorithms at construction
    time (hardening (a) from T-TAg): the greedy one-sided heuristics do not
    satisfy the metric axioms and must not silently feed into d_I.
    """

    def test_default_algorithm_accepted(self) -> None:
        """Default construction (algorithm='canonical') must not raise."""
        from isalhg.core.canonical import CANONICAL_ALGORITHM

        d = IsalHGLevenshtein()
        assert d._algorithm == CANONICAL_ALGORITHM

    @pytest.mark.parametrize(
        "bad_algo",
        ["greedy_min_nbrdeg", "greedy_min", "greedy_single", "greedy_single_nbrdeg"],
    )
    def test_non_canonical_algorithm_raises(self, bad_algo: str) -> None:
        from isalhg.errors import DistanceComputationError

        with pytest.raises(DistanceComputationError, match="canonical"):
            IsalHGLevenshtein(algorithm=bad_algo)


class TestEdgeOrderInvariance:
    """d_I must be 0.0 on both presentations of the n=4 counterexample
    (hardening (a)/(c) from T-TAg): before T-TAd this was 4.0 because the
    greedy default was edge-order dependent.
    """

    _CE_EDGES: list[frozenset[int]] = [
        frozenset({1, 3}),
        frozenset({0, 1, 3}),
        frozenset({0, 2, 3}),
        frozenset({1, 2}),
    ]
    _CE_ORDER_B: list[int] = [1, 2, 3, 0]

    def _presentation_a(self) -> SparseHypergraph:
        return SparseHypergraph(n_nodes=4, hyperedges=self._CE_EDGES)

    def _presentation_b(self) -> SparseHypergraph:
        return SparseHypergraph(n_nodes=4, hyperedges=[self._CE_EDGES[i] for i in self._CE_ORDER_B])

    def test_d_i_zero_on_both_presentations(self) -> None:
        d = IsalHGLevenshtein()
        assert d.pairwise(self._presentation_a(), self._presentation_b()) == 0.0

    def test_self_distance_zero_on_counterexample(self) -> None:
        H = self._presentation_a()
        assert IsalHGLevenshtein().pairwise(H, H) == 0.0


class TestBudget:
    """CanonicalEncoder(max_expansions=N).encode() must raise
    CanonicalizationTimeoutError on eta-degenerate inputs before hanging
    (hardening (b) from T-TAg).
    """

    def test_budget_raises_on_high_automorphism_design(self) -> None:
        from isalhg.core.algorithms.canonical import CanonicalEncoder
        from isalhg.errors import CanonicalizationTimeoutError

        # Cyclic STS(13) — vertex-transitive, hits large tie sets.
        H = SparseHypergraph(
            n_nodes=13,
            hyperedges=[frozenset({i, (i + 1) % 13, (i + 3) % 13}) for i in range(13)],
        )
        enc = CanonicalEncoder(k=3, max_expansions=5)
        with pytest.raises(CanonicalizationTimeoutError, match="budget"):
            enc.encode(H)

    def test_unlimited_budget_succeeds(self) -> None:
        from isalhg.core.algorithms.canonical import CanonicalEncoder

        H = SparseHypergraph(
            n_nodes=4,
            hyperedges=[
                frozenset({1, 3}),
                frozenset({0, 1, 3}),
                frozenset({0, 2, 3}),
                frozenset({1, 2}),
            ],
        )
        enc = CanonicalEncoder(k=3, max_expansions=None)
        result = enc.encode(H)
        assert len(result) > 0
