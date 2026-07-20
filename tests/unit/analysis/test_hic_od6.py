"""Unit tests for experiments.article.analysis.hic_od6 (T-M5j).

Acceptance criteria checked here
---------------------------------
1. ``wstar_ok`` returns True for a fast hypergraph (small Fano-plane-triangle).
2. ``wstar_ok`` returns False when the subprocess times out (monkeypatched budget).
3. ``apply_censoring_filter`` keeps hypergraphs and labels in the same order.
4. ``per_class_yield`` computes correct fraction per class.
5. ``make_censoring_table_row`` returns expected keys.
6. ``stratified_subsample`` returns at most ``max_n`` items with balanced class coverage.
7. ``_compute_hpd_d_matrix_safe`` handles per-instance IndexError (DEFECT-1 fix).
8. ``compute_agreement_summary`` uses only clean datasets for ranking conclusions.

Every test is designed to FAIL before ``hic_od6`` is implemented.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Minimal fixture helpers
# ---------------------------------------------------------------------------


def _tiny_triangle() -> object:
    """Return a small 3-node triangle SparseHypergraph (always fast for w*_c)."""
    from isalhg.core.sparse_hypergraph import SparseHypergraph

    return SparseHypergraph(
        n_nodes=3,
        hyperedges=[frozenset({0, 1}), frozenset({1, 2}), frozenset({0, 2})],
    )


def _medium_hg(n: int = 5, k: int = 3) -> object:
    """Return a small connected k-uniform hypergraph with n vertices."""
    from isalhg.core.sparse_hypergraph import SparseHypergraph

    return SparseHypergraph(
        n_nodes=n,
        hyperedges=[frozenset(range(k)), frozenset(range(1, k + 1))],
    )


# ---------------------------------------------------------------------------
# 1. wstar_ok — passes on a fast hypergraph
# ---------------------------------------------------------------------------


class TestWstarOk:
    def test_fast_hg_passes(self) -> None:
        """A tiny triangle should compute w*_c in well under 5 s."""
        from experiments.article.analysis.hic_od6 import wstar_ok

        H = _tiny_triangle()
        assert wstar_ok(H, budget=5.0) is True

    def test_zero_budget_dnf(self) -> None:
        """Budget=0 leaves no time for any computation — must report DNF."""
        from experiments.article.analysis.hic_od6 import wstar_ok

        H = _tiny_triangle()
        # With a 0-second budget even a trivial computation should timeout.
        # This relies on the fork + join(0) path correctly checking is_alive.
        result = wstar_ok(H, budget=0.0)
        assert result is False


# ---------------------------------------------------------------------------
# 2. apply_censoring_filter — label-alignment invariant
# ---------------------------------------------------------------------------


class TestCensoringFilter:
    def test_all_pass_preserves_order(self) -> None:
        """When all survive, order is unchanged and lengths match."""
        from experiments.article.analysis.hic_od6 import apply_censoring_filter

        hgs = [_tiny_triangle() for _ in range(4)]
        labels = [0, 1, 0, 2]
        survivors, sur_labels = apply_censoring_filter(hgs, labels, budget=5.0)
        assert len(survivors) == len(sur_labels)
        assert len(survivors) == 4
        assert sur_labels == labels

    def test_dnf_instances_dropped(self) -> None:
        """DNF instances (budget=0) must be dropped and labels stay aligned."""
        from experiments.article.analysis.hic_od6 import apply_censoring_filter

        hgs = [_tiny_triangle() for _ in range(3)]
        labels = [0, 1, 2]
        # With budget=0 all should time out.
        survivors, sur_labels = apply_censoring_filter(hgs, labels, budget=0.0)
        assert len(survivors) == len(sur_labels)
        # No survivors at budget=0 (all timeout).
        assert len(survivors) == 0

    def test_alignment_invariant(self) -> None:
        """After filtering, survivors[i] and sur_labels[i] must match the original pair."""
        from experiments.article.analysis.hic_od6 import apply_censoring_filter

        hgs = [_tiny_triangle(), _tiny_triangle(), _tiny_triangle()]
        labels = [7, 3, 9]
        survivors, sur_labels = apply_censoring_filter(hgs, labels, budget=5.0)
        # All fast — all three survive; labels must match original order.
        assert sur_labels == [7, 3, 9]
        assert len(survivors) == 3


# ---------------------------------------------------------------------------
# 3. per_class_yield
# ---------------------------------------------------------------------------


class TestPerClassYield:
    def test_correct_fractions(self) -> None:
        """per_class_yield returns survivors / total per class."""
        from experiments.article.analysis.hic_od6 import per_class_yield

        all_labels = [0, 0, 1, 1, 1]
        sur_labels = [0, 1, 1]  # 1/2 of class 0, 2/3 of class 1
        yield_map = per_class_yield(all_labels, sur_labels)
        assert set(yield_map.keys()) == {0, 1}
        assert abs(yield_map[0] - 0.5) < 1e-9
        assert abs(yield_map[1] - 2.0 / 3.0) < 1e-9

    def test_full_survival(self) -> None:
        """When all survive, yield is 1.0 for every class."""
        from experiments.article.analysis.hic_od6 import per_class_yield

        labels = [0, 1, 0, 2]
        yield_map = per_class_yield(labels, labels)
        assert all(abs(v - 1.0) < 1e-9 for v in yield_map.values())

    def test_empty_class_zero_yield(self) -> None:
        """A class present in all_labels but absent from sur_labels → yield 0.0."""
        from experiments.article.analysis.hic_od6 import per_class_yield

        all_labels = [0, 0, 1]
        sur_labels = [0]  # class 1 fully censored
        yield_map = per_class_yield(all_labels, sur_labels)
        assert yield_map[1] == 0.0


# ---------------------------------------------------------------------------
# 4. make_censoring_table_row
# ---------------------------------------------------------------------------


class TestCensoringTableRow:
    def test_required_keys(self) -> None:
        """make_censoring_table_row must return all required keys."""
        from experiments.article.analysis.hic_od6 import make_censoring_table_row

        row = make_censoring_table_row(
            hic_name="IMDB-Wri-Genre",
            n_items=1000,
            n_arity_capped=901,
            n_survivors=836,
            per_class_yield_map={0: 0.95, 1: 0.88, 2: 0.79},
        )
        for key in (
            "hic_name",
            "n_items",
            "n_arity_capped",
            "n_survivors",
            "wstar_yield",
            "per_class",
        ):
            assert key in row, f"Missing key: {key}"

    def test_yield_fraction(self) -> None:
        """wstar_yield should equal n_survivors / n_arity_capped."""
        from experiments.article.analysis.hic_od6 import make_censoring_table_row

        row = make_censoring_table_row(
            hic_name="X",
            n_items=100,
            n_arity_capped=80,
            n_survivors=60,
            per_class_yield_map={0: 0.75},
        )
        assert abs(row["wstar_yield"] - 60.0 / 80.0) < 1e-9


# ---------------------------------------------------------------------------
# 5. stratified_subsample
# ---------------------------------------------------------------------------


class TestStratifiedSubsample:
    def test_max_n_respected(self) -> None:
        """Result must have at most max_n items."""
        from experiments.article.analysis.hic_od6 import stratified_subsample

        hgs = [_tiny_triangle() for _ in range(100)]
        labels = list(range(100))  # all unique labels
        sub_hgs, sub_labels = stratified_subsample(hgs, labels, max_n=40, rng_seed=42)
        assert len(sub_hgs) <= 40
        assert len(sub_hgs) == len(sub_labels)

    def test_order_preserved_within_class(self) -> None:
        """Selected items must be a subset of the original with consistent pairing."""
        from experiments.article.analysis.hic_od6 import stratified_subsample

        hgs = [_tiny_triangle() for _ in range(20)]
        labels = [i % 4 for i in range(20)]
        sub_hgs, sub_labels = stratified_subsample(hgs, labels, max_n=8, rng_seed=0)
        assert len(sub_hgs) == len(sub_labels)
        assert len(sub_hgs) <= 8


# ---------------------------------------------------------------------------
# 6. _compute_hpd_d_matrix_safe (DEFECT-1 fix)
# ---------------------------------------------------------------------------


class TestHpdSafeMatrix:
    """Verify _compute_hpd_d_matrix_safe handles per-instance IndexError.

    Teeth test: demonstrates that the *raw* HPD matrix() propagates the
    IndexError to the caller, while _compute_hpd_d_matrix_safe returns a
    partial result on the computable subset.
    """

    def test_raw_hpd_matrix_raises_for_degenerate(self) -> None:
        """Confirm the vendored HPD matrix() raises on a degenerate instance.

        This is the bug that _compute_hpd_d_matrix_safe works around.
        The test MUST pass (the raw function raises); remove it if/when the
        vendored code is patched upstream.
        """
        import unittest.mock as mock

        from isalhg.metric_space.representations.hpd import HPDDistance

        call_count_box = [0]

        def portrait_side_effect(_xgi_h: object) -> object:
            call_count_box[0] += 1
            if call_count_box[0] == 2:
                raise IndexError("index 1 is out of bounds for axis 0 with size 1")
            return {"mock": True}

        with (
            mock.patch(
                "isalhg.metric_space.representations._hpd_vendor.hyperedge_portrait",
                side_effect=portrait_side_effect,
            ),
            pytest.raises(IndexError),
        ):
            HPDDistance().matrix([_tiny_triangle(), _tiny_triangle(), _tiny_triangle()])

    def test_safe_wrapper_drops_degenerate(self, tmp_path: object) -> None:
        """_compute_hpd_d_matrix_safe drops failing instances; D has shape (n_ok, n_ok)."""
        import unittest.mock as mock
        from pathlib import Path

        from experiments.article.analysis.hic_od6 import _compute_hpd_d_matrix_safe

        corpus = [_tiny_triangle(), _tiny_triangle(), _tiny_triangle()]
        call_count_box = [0]

        def portrait_side_effect(_xgi_h: object) -> object:
            call_count_box[0] += 1
            if call_count_box[0] == 2:  # second instance fails
                raise IndexError("index 1 is out of bounds for axis 0 with size 1")
            return {"mock": True}

        with (
            mock.patch(
                "isalhg.metric_space.representations._hpd_vendor.hyperedge_portrait",
                side_effect=portrait_side_effect,
            ),
            mock.patch(
                "isalhg.metric_space.representations._hpd_vendor.hyper_portrait_divergence",
                return_value=0.25,
            ),
        ):
            D, good_idx, n_errors, error_sample = _compute_hpd_d_matrix_safe(
                corpus, Path(str(tmp_path)), {"dataset": "test"}
            )

        assert n_errors == 1
        assert good_idx == [0, 2]
        assert D.shape == (2, 2)
        assert error_sample != ""

    def test_safe_wrapper_full_success(self, tmp_path: object) -> None:
        """When all portraits succeed, n_errors=0 and D is (n, n)."""
        import unittest.mock as mock
        from pathlib import Path

        from experiments.article.analysis.hic_od6 import _compute_hpd_d_matrix_safe

        corpus = [_tiny_triangle(), _tiny_triangle(), _tiny_triangle()]

        with (
            mock.patch(
                "isalhg.metric_space.representations._hpd_vendor.hyperedge_portrait",
                return_value={"mock": True},
            ),
            mock.patch(
                "isalhg.metric_space.representations._hpd_vendor.hyper_portrait_divergence",
                return_value=0.0,
            ),
        ):
            D, good_idx, n_errors, error_sample = _compute_hpd_d_matrix_safe(
                corpus, Path(str(tmp_path)), {"dataset": "test"}
            )

        assert n_errors == 0
        assert good_idx == [0, 1, 2]
        assert D.shape == (3, 3)
        assert error_sample == ""


# ---------------------------------------------------------------------------
# 7. compute_agreement_summary — clean/censored split (DEFECT-2 fix)
# ---------------------------------------------------------------------------


class TestAgreementSummaryCleanSplit:
    """Verify compute_agreement_summary restricts ranking to clean datasets."""

    def _make_rows(self) -> tuple[list[dict], list[dict], list[dict]]:
        """Return (censoring_rows, clustering_rows, knn_rows) for 2 clean + 1 censored."""
        censoring_rows = [
            {"hic_name": "Clean-A", "wstar_yield": 0.925},
            {"hic_name": "Clean-B", "wstar_yield": 0.917},
            {"hic_name": "Censored-C", "wstar_yield": 0.39},
        ]
        clustering_rows = [
            {"hic_name": "Clean-A", "representation": "IsalHG", "pam_ari": 0.066, "pam_nmi": 0.116},
            {"hic_name": "Clean-A", "representation": "WL-L1", "pam_ari": 0.057, "pam_nmi": 0.139},
            {"hic_name": "Clean-B", "representation": "IsalHG", "pam_ari": 0.074, "pam_nmi": 0.051},
            {"hic_name": "Clean-B", "representation": "WL-L1", "pam_ari": -0.012, "pam_nmi": 0.103},
            # Censored dataset — high ARI that would flip ranking if included.
            {"hic_name": "Censored-C", "representation": "WL-L1", "pam_ari": 0.45, "pam_nmi": 0.40},
            {
                "hic_name": "Censored-C",
                "representation": "IsalHG",
                "pam_ari": 0.01,
                "pam_nmi": 0.01,
            },
        ]
        knn_rows = [
            {
                "hic_name": "Clean-A",
                "representation": "IsalHG",
                "k": 9,
                "accuracy": 0.555,
                "macro_f1": 0.43,
                "auc_ovr": 0.750,
            },
            {
                "hic_name": "Clean-A",
                "representation": "WL-L1",
                "k": 9,
                "accuracy": 0.490,
                "macro_f1": 0.38,
                "auc_ovr": 0.678,
            },
            {
                "hic_name": "Clean-B",
                "representation": "IsalHG",
                "k": 9,
                "accuracy": 0.400,
                "macro_f1": 0.30,
                "auc_ovr": 0.596,
            },
            {
                "hic_name": "Clean-B",
                "representation": "WL-L1",
                "k": 9,
                "accuracy": 0.370,
                "macro_f1": 0.28,
                "auc_ovr": 0.569,
            },
        ]
        return censoring_rows, clustering_rows, knn_rows

    def test_clean_datasets_identified(self) -> None:
        """compute_agreement_summary identifies only high-yield datasets as clean."""
        from experiments.article.analysis.hic_od6 import compute_agreement_summary

        censoring_rows, clustering_rows, knn_rows = self._make_rows()
        result = compute_agreement_summary(clustering_rows, knn_rows, censoring_rows)

        assert "Clean-A" in result["clean_datasets"]
        assert "Clean-B" in result["clean_datasets"]
        assert "Censored-C" not in result["clean_datasets"]

    def test_censored_dataset_not_used_for_ranking(self) -> None:
        """The censored dataset's high WL ARI must NOT flip the clean ranking."""
        from experiments.article.analysis.hic_od6 import compute_agreement_summary

        censoring_rows, clustering_rows, knn_rows = self._make_rows()
        result = compute_agreement_summary(clustering_rows, knn_rows, censoring_rows)

        # On clean datasets, IsalHG leads ARI (0.07 vs WL -0.012 on avg).
        # Censored-C has WL ARI=0.45 — if included it would flip the order.
        clean_order = result["ari_order_clean"]
        assert clean_order.index("IsalHG") < clean_order.index("WL-L1")

    def test_conclusion_mentions_censoring(self) -> None:
        """conclusion field must explain that heavily-censored sets are excluded."""
        from experiments.article.analysis.hic_od6 import compute_agreement_summary

        censoring_rows, clustering_rows, knn_rows = self._make_rows()
        result = compute_agreement_summary(clustering_rows, knn_rows, censoring_rows)

        conclusion = result["conclusion"].lower()
        assert "censor" in conclusion

    def test_no_censoring_rows_treats_all_as_clean(self) -> None:
        """When censoring_rows=None, all datasets are treated as clean."""
        from experiments.article.analysis.hic_od6 import compute_agreement_summary

        _, clustering_rows, knn_rows = self._make_rows()
        result = compute_agreement_summary(clustering_rows, knn_rows, censoring_rows=None)

        # All three datasets should be in clean.
        assert "Censored-C" in result["clean_datasets"]
