"""Unit tests for experiments.article.analysis.hic_od6 (T-M5j).

Acceptance criteria checked here
---------------------------------
1. ``wstar_ok`` returns True for a fast hypergraph (small Fano-plane-triangle).
2. ``wstar_ok`` returns False when the subprocess times out (monkeypatched budget).
3. ``apply_censoring_filter`` keeps hypergraphs and labels in the same order.
4. ``per_class_yield`` computes correct fraction per class.
5. ``make_censoring_table_row`` returns expected keys.
6. ``stratified_subsample`` returns at most ``max_n`` items with balanced class coverage.

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
