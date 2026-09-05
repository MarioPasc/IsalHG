"""Fidelity measures: profile shapes, JSD endpoints, novelty.

The JSD endpoints are the ones that must be exact rather than approximately
right, because the fidelity table is read against them: 0 means "the sample
matches the collection", 1 means "the sample shares nothing with it", and a
number in between is only interpretable if those two anchors are.
"""

from __future__ import annotations

import pytest

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.generation.errors import GenerationError
from isalhg.generation.fidelity import PROFILE_KEYS, fidelity, jsd, novelty, profile

pytestmark = pytest.mark.unit

np = pytest.importorskip("numpy")


def _kb(
    n: int, edges: list[frozenset[int]], types: list[int], preds: list[int]
) -> SparseHypergraph:
    return SparseHypergraph(
        n,
        edges,
        n_vertex_labels=3,
        n_edge_labels=2,
        vertex_labels=types,
        edge_labels=preds,
    )


@pytest.fixture
def sample_kb() -> SparseHypergraph:
    return _kb(4, [frozenset({0, 1, 2}), frozenset({2, 3})], [0, 1, 2, 0], [0, 1])


# ---------------------------------------------------------------------------
# jsd
# ---------------------------------------------------------------------------


class TestJSD:
    def test_identical_distributions_give_zero(self) -> None:
        p = np.array([0.2, 0.5, 0.3])
        assert jsd(p, p) == pytest.approx(0.0, abs=1e-12)

    def test_disjoint_supports_give_one_bit(self) -> None:
        p = np.array([1.0, 0.0])
        q = np.array([0.0, 1.0])
        assert jsd(p, q) == pytest.approx(1.0, abs=1e-12)

    def test_disjoint_supports_of_different_lengths(self) -> None:
        assert jsd(np.array([1.0, 0.0]), np.array([0.0, 0.0, 3.0])) == pytest.approx(1.0)

    def test_symmetric(self) -> None:
        p = np.array([0.1, 0.7, 0.2])
        q = np.array([0.5, 0.25, 0.25])
        assert jsd(p, q) == pytest.approx(jsd(q, p))

    def test_bounded_in_the_unit_interval(self) -> None:
        rng = np.random.default_rng(0)
        for _ in range(50):
            p = rng.random(6)
            q = rng.random(6)
            assert 0.0 <= jsd(p, q) <= 1.0

    def test_unnormalized_counts_are_accepted(self) -> None:
        assert jsd(np.array([2.0, 6.0]), np.array([1.0, 3.0])) == pytest.approx(0.0, abs=1e-12)

    def test_half_overlap_matches_the_closed_form(self) -> None:
        """``p`` on {0}, ``q`` split evenly over {0, 1}: JSD = 1 - 3/4 log2 3 + ... .

        Computed directly from the definition so the test is a check of the
        implementation rather than a restatement of it.
        """
        p = np.array([1.0, 0.0])
        q = np.array([0.5, 0.5])
        mixture = np.array([0.75, 0.25])

        def entropy(v: object) -> float:
            arr = np.asarray(v)
            nz = arr[arr > 0]
            return float(-(nz * np.log2(nz)).sum())

        expected = entropy(mixture) - 0.5 * (entropy(p) + entropy(q))
        assert jsd(p, q) == pytest.approx(expected)

    def test_both_empty_agree_vacuously(self) -> None:
        assert jsd(np.zeros(3), np.zeros(3)) == 0.0

    def test_one_empty_is_maximal(self) -> None:
        assert jsd(np.zeros(3), np.array([1.0, 0.0, 0.0])) == 1.0

    def test_rejects_negative_histograms(self) -> None:
        with pytest.raises(GenerationError, match="non-negative"):
            jsd(np.array([-1.0, 2.0]), np.array([1.0, 1.0]))

    def test_rejects_non_1d_input(self) -> None:
        with pytest.raises(GenerationError, match="1-D"):
            jsd(np.ones((2, 2)), np.ones(4))


# ---------------------------------------------------------------------------
# profile
# ---------------------------------------------------------------------------


class TestProfile:
    def test_keys_and_normalization(self, sample_kb: SparseHypergraph) -> None:
        result = profile([sample_kb])
        assert set(result) == set(PROFILE_KEYS)
        for key, vector in result.items():
            assert vector.ndim == 1, key
            assert vector.sum() == pytest.approx(1.0), key

    def test_shapes_are_indexed_by_value(self, sample_kb: SparseHypergraph) -> None:
        """``n`` and ``m`` histograms are indexed by count, so length = max + 1."""
        result = profile([sample_kb])
        assert len(result["n"]) == sample_kb.n_nodes + 1
        assert len(result["m"]) == sample_kb.n_edges + 1
        assert len(result["arity"]) == 4  # max arity 3
        assert len(result["pred"]) == sample_kb.n_edge_labels
        assert len(result["type"]) == sample_kb.n_vertex_labels

    def test_counts_land_in_the_right_bins(self, sample_kb: SparseHypergraph) -> None:
        result = profile([sample_kb])
        assert result["n"][4] == pytest.approx(1.0)
        assert result["m"][2] == pytest.approx(1.0)
        # arities 3 and 2, one each
        assert result["arity"][3] == pytest.approx(0.5)
        assert result["arity"][2] == pytest.approx(0.5)
        # types [0, 1, 2, 0] -> two 0s, one 1, one 2
        assert result["type"][0] == pytest.approx(0.5)
        assert result["type"][1] == pytest.approx(0.25)

    def test_empty_population(self) -> None:
        result = profile([])
        for key in PROFILE_KEYS:
            assert result[key].sum() == 0.0

    def test_edgeless_member_leaves_arity_and_pred_empty(self) -> None:
        H = _kb(2, [], [0, 0], [])
        result = profile([H])
        assert result["arity"].sum() == 0.0
        assert result["pred"].sum() == 0.0
        assert result["n"].sum() == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# fidelity
# ---------------------------------------------------------------------------


class TestFidelity:
    def test_a_collection_against_itself_is_zero_everywhere(
        self, sample_kb: SparseHypergraph
    ) -> None:
        collection = [sample_kb, _kb(3, [frozenset({0, 1, 2})], [0, 0, 1], [1])]
        result = fidelity(collection, collection)
        assert set(result) == {f"jsd_{key}" for key in PROFILE_KEYS}
        for key, value in result.items():
            assert value == pytest.approx(0.0, abs=1e-12), key

    def test_disjoint_collections_diverge(self) -> None:
        small = [_kb(2, [frozenset({0, 1})], [0, 0], [0])]
        large = [_kb(6, [frozenset({0, 1, 2, 3, 4, 5})], [1] * 6, [1])]
        result = fidelity(small, large)
        assert result["jsd_n"] == pytest.approx(1.0)
        assert result["jsd_arity"] == pytest.approx(1.0)
        assert result["jsd_pred"] == pytest.approx(1.0)
        assert result["jsd_type"] == pytest.approx(1.0)

    def test_all_values_are_in_the_unit_interval(self, sample_kb: SparseHypergraph) -> None:
        other = _kb(5, [frozenset({0, 1}), frozenset({1, 2, 3})], [2, 2, 0, 1, 1], [0, 0])
        for value in fidelity([sample_kb], [other]).values():
            assert 0.0 <= value <= 1.0


# ---------------------------------------------------------------------------
# novelty
# ---------------------------------------------------------------------------


class TestNovelty:
    def test_all_new(self) -> None:
        assert novelty([("a",), ("b",)], [("c",)]) == pytest.approx(1.0)

    def test_none_new(self) -> None:
        assert novelty([("a",), ("b",)], [("a",), ("b",)]) == pytest.approx(0.0)

    def test_half_new(self) -> None:
        assert novelty([("a",), ("z",)], [("a",)]) == pytest.approx(0.5)

    def test_duplicated_samples_count_once_each(self) -> None:
        """Novelty is a fraction of samples, not of distinct samples."""
        assert novelty([("z",), ("z",), ("a",)], [("a",)]) == pytest.approx(2 / 3)

    def test_empty_sample_set(self) -> None:
        assert novelty([], [("a",)]) == 0.0

    def test_empty_collection_makes_everything_novel(self) -> None:
        assert novelty([("a",)], []) == pytest.approx(1.0)
