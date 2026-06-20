"""Unit tests for :mod:`isalhg.viz.cohort_panel`."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")  # noqa: E402 - must precede pyplot import

import matplotlib.pyplot as plt
import pytest

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.viz import cohort_grid_figure

pytestmark = pytest.mark.unit


def _tiny_hypergraph(n: int, edges: list[frozenset[int]]) -> SparseHypergraph:
    return SparseHypergraph(n_nodes=n, hyperedges=edges)


def _panels() -> list[tuple[str, str, SparseHypergraph]]:
    return [
        (
            "Panel A",
            "n=6, r=2",
            _tiny_hypergraph(
                6,
                [
                    frozenset({0, 1}),
                    frozenset({1, 2}),
                    frozenset({2, 3}),
                    frozenset({3, 4}),
                    frozenset({4, 5}),
                ],
            ),
        ),
        (
            "Panel B",
            "n=6, r=3",
            _tiny_hypergraph(
                6,
                [
                    frozenset({0, 1, 2}),
                    frozenset({2, 3, 4}),
                    frozenset({4, 5, 0}),
                ],
            ),
        ),
        (
            "Panel C",
            "n=6, r=3 denser",
            _tiny_hypergraph(
                6,
                [
                    frozenset({0, 1, 2}),
                    frozenset({1, 2, 3}),
                    frozenset({2, 3, 4}),
                    frozenset({3, 4, 5}),
                    frozenset({0, 4, 5}),
                ],
            ),
        ),
    ]


class TestCohortGridFigure:
    @pytest.mark.parametrize("backend_name", ["xgi", "hypernetx", "hypergraphx"])
    def test_renders_three_panel_figure(self, backend_name: str) -> None:
        pytest.importorskip(backend_name)
        panels = _panels()
        fig = cohort_grid_figure(panels, backend=backend_name, overall_title="smoke")
        try:
            assert len(fig.axes) >= 3
        finally:
            plt.close(fig)

    def test_empty_panels_raises(self) -> None:
        with pytest.raises(ValueError, match="at least one panel"):
            cohort_grid_figure([], backend="xgi")

    def test_n_columns_wrap(self) -> None:
        pytest.importorskip("xgi")
        panels = _panels()  # 3 panels
        fig = cohort_grid_figure(panels, backend="xgi", n_columns=2)
        try:
            # 3 panels in a 2-col grid -> 2 rows -> 4 axes total
            # (panels[:3] populated, 1 spare blanked).
            assert len(fig.axes) == 4
        finally:
            plt.close(fig)
