"""Unit tests for :class:`isalhg.metric_space.distances.isalhg_levenshtein`.

``d_I`` must be 0 on isomorphic pairs (``w*`` is iso-invariant) and > 0 on
non-isomorphic pairs, including the hard same-parameter cyclic C13 pair.
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

    def test_distinguishes_cyclic_triple_13_pair(
        self, cyclic_triple_13_pair: tuple[SparseHypergraph, SparseHypergraph]
    ) -> None:
        # Same parameters, genuinely non-isomorphic — the hard case for w*.
        a, b = cyclic_triple_13_pair
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
    """canonical_string(max_expansions=N) must raise CanonicalizationTimeoutError
    on high-automorphism inputs before hanging — for both the cpp and python backends.
    """

    # Cyclic triple orbit C13(0,1,3): vertex-transitive, hits large V tie-sets.
    _C13 = [frozenset({i, (i + 1) % 13, (i + 3) % 13}) for i in range(13)]

    @pytest.mark.parametrize("backend", ["cpp", "python"])
    def test_budget_raises_on_high_automorphism_design(self, backend: str) -> None:
        from isalhg.errors import CanonicalizationTimeoutError

        H = SparseHypergraph(n_nodes=13, hyperedges=self._C13)
        with pytest.raises(CanonicalizationTimeoutError, match="budget"):
            canonical_string(H, max_expansions=5, backend=backend)

    @pytest.mark.parametrize("backend", ["cpp", "python"])
    def test_unlimited_budget_succeeds(self, backend: str) -> None:
        H = SparseHypergraph(
            n_nodes=4,
            hyperedges=[
                frozenset({1, 3}),
                frozenset({0, 1, 3}),
                frozenset({0, 2, 3}),
                frozenset({1, 2}),
            ],
        )
        result = canonical_string(H, max_expansions=None, backend=backend)
        assert len(result) > 0

    def test_budget_raises_via_encoder_python_path(self) -> None:
        """CanonicalEncoder(max_expansions=N).encode() — legacy direct-encoder path."""
        from isalhg.core.algorithms.canonical import CanonicalEncoder
        from isalhg.errors import CanonicalizationTimeoutError

        H = SparseHypergraph(n_nodes=13, hyperedges=self._C13)
        enc = CanonicalEncoder(k=3, max_expansions=5)
        with pytest.raises(CanonicalizationTimeoutError, match="budget"):
            enc.encode(H)


# ---------------------------------------------------------------------------
# (a) Degenerate-domain guard (T-M1c)
# ---------------------------------------------------------------------------


class TestDegenerateDomain:
    """The empty hypergraph (n=0) must be excluded from the d_I domain.

    ``w*(∅) = ""`` and ``w*(•) = ""``, so without a guard ``d_I(∅, •) = 0``
    on a non-isomorphic pair -- identity of indiscernibles fails.  The fix:
    raise ``DegenerateHypergraphError`` for ``n = 0`` inputs and return False
    for ``are_isomorphic(∅, •)``.
    """

    @staticmethod
    def _empty() -> SparseHypergraph:
        return SparseHypergraph(n_nodes=0, hyperedges=[])

    @staticmethod
    def _single_vertex() -> SparseHypergraph:
        return SparseHypergraph(n_nodes=1, hyperedges=[])

    def test_pairwise_raises_on_empty_left(self) -> None:
        from isalhg.errors import DegenerateHypergraphError

        with pytest.raises(DegenerateHypergraphError):
            IsalHGLevenshtein().pairwise(self._empty(), self._single_vertex())

    def test_pairwise_raises_on_empty_right(self) -> None:
        from isalhg.errors import DegenerateHypergraphError

        with pytest.raises(DegenerateHypergraphError):
            IsalHGLevenshtein().pairwise(self._single_vertex(), self._empty())

    def test_are_isomorphic_empty_vs_single_is_false(self) -> None:
        from isalhg.iso_backends.isalhg_backend import IsalHGBackend

        assert not IsalHGBackend().are_isomorphic(self._empty(), self._single_vertex())

    def test_are_isomorphic_empty_vs_empty_is_true(self) -> None:
        from isalhg.iso_backends.isalhg_backend import IsalHGBackend

        assert IsalHGBackend().are_isomorphic(self._empty(), self._empty())

    def test_canonical_string_raises_on_empty(self) -> None:
        from isalhg.errors import DegenerateHypergraphError

        with pytest.raises(DegenerateHypergraphError):
            canonical_string(self._empty())


# ---------------------------------------------------------------------------
# (c) Pinned witness: normalize=True violates triangle inequality (T-M1c)
# ---------------------------------------------------------------------------


class TestNormalizedNonMetric:
    """Pinned witness: rapidfuzz normalized_distance is NOT a metric.

    Marzal & Vidal (IEEE TPAMI 15(9), 1993) prove that the naive
    length-normalized edit distance NED(s,t) = edit(s,t) / max(|s|,|t|)
    violates the triangle inequality.

    Witness token sequences (private-use characters as stand-ins for tokens):
        s1 = (A, B)       — length 2
        s2 = (A, B, C)    — length 3  (s1 with one token appended)
        s3 = (B, C)       — length 2  (last two tokens of s2)

    Distances (edit = Levenshtein on character strings):
        NED(s1, s2) = 1 / max(2,3) = 1/3
        NED(s2, s3) = 1 / max(3,2) = 1/3
        NED(s1, s3) = 2 / max(2,2) = 1

    Triangle inequality violated: NED(s1, s3) = 1 > 1/3 + 1/3 = 2/3.

    Since IsalHGLevenshtein(normalize=True) routes through rapidfuzz's
    ``Levenshtein.normalized_distance`` on the same encoded token sequences,
    the same violation applies to any three hypergraphs whose canonical string
    encodings reproduce this length pattern.
    """

    # Private-use code points (>= U+0100), identical to those _encode() uses.
    _S1 = "Āā"
    _S2 = "ĀāĂ"
    _S3 = "āĂ"

    def test_triangle_violation_at_token_level(self) -> None:
        """rapidfuzz.normalized_distance directly violates triangle inequality."""
        from rapidfuzz.distance import Levenshtein

        d12 = Levenshtein.normalized_distance(self._S1, self._S2)
        d23 = Levenshtein.normalized_distance(self._S2, self._S3)
        d13 = Levenshtein.normalized_distance(self._S1, self._S3)

        assert abs(d12 - 1 / 3) < 1e-9, f"d12={d12}"
        assert abs(d23 - 1 / 3) < 1e-9, f"d23={d23}"
        assert abs(d13 - 1.0) < 1e-9, f"d13={d13}"
        # Triangle inequality violated: d(s1, s3) > d(s1, s2) + d(s2, s3)
        assert d13 > d12 + d23

    def test_normalize_true_uses_same_kernel(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """IsalHGLevenshtein(normalize=True) routes through the same non-metric kernel.

        Monkeypatches _symbols to inject the witness sequences, then checks
        that pairwise() reproduces the triangle-inequality violation.
        """
        import isalhg.metric_space.distances.isalhg_levenshtein as mod

        # Dummy hypergraphs — structure doesn't matter once _symbols is patched.
        H1 = SparseHypergraph(n_nodes=2, hyperedges=[frozenset({0, 1})])
        H2 = SparseHypergraph(n_nodes=3, hyperedges=[frozenset({0, 1}), frozenset({1, 2})])
        H3 = SparseHypergraph(n_nodes=2, hyperedges=[frozenset({0, 1})])

        # Map each hypergraph id to its injected token sequence.
        _sequences: dict[int, tuple[str, ...]] = {
            id(H1): tuple(self._S1),
            id(H2): tuple(self._S2),
            id(H3): tuple(self._S3),
        }

        def _patched_symbols(
            self_inner: object,
            H: SparseHypergraph,
            k: int,
            *,
            augment: bool,
        ) -> tuple[str, ...]:
            return _sequences[id(H)]

        monkeypatch.setattr(mod.IsalHGLevenshtein, "_symbols", _patched_symbols)
        d = mod.IsalHGLevenshtein(normalize=True)

        d12 = d.pairwise(H1, H2)
        d23 = d.pairwise(H2, H3)
        d13 = d.pairwise(H1, H3)

        # Same violation as at the token level.
        assert d13 > d12 + d23
