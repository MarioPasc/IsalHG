"""Integration tests: end-to-end rendering of fixtures across backends."""

from __future__ import annotations

from pathlib import Path

import pytest

from isalhg.core.algorithms.greedy_min import GreedyMin
from isalhg.core.canonical import required_k
from isalhg.core.sparse_hypergraph import SparseHypergraph

pytestmark = pytest.mark.integration

matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg")


def _fano() -> SparseHypergraph:
    return SparseHypergraph(
        n_nodes=7,
        hyperedges=[
            frozenset({0, 1, 2}),
            frozenset({0, 3, 4}),
            frozenset({0, 5, 6}),
            frozenset({1, 3, 5}),
            frozenset({1, 4, 6}),
            frozenset({2, 3, 6}),
            frozenset({2, 4, 5}),
        ],
    )


def _sts9() -> SparseHypergraph:
    blocks = [
        frozenset({0, 1, 2}),
        frozenset({3, 4, 5}),
        frozenset({6, 7, 8}),
        frozenset({0, 3, 6}),
        frozenset({1, 4, 7}),
        frozenset({2, 5, 8}),
        frozenset({0, 4, 8}),
        frozenset({1, 5, 6}),
        frozenset({2, 3, 7}),
        frozenset({0, 5, 7}),
        frozenset({1, 3, 8}),
        frozenset({2, 4, 6}),
    ]
    return SparseHypergraph(n_nodes=9, hyperedges=blocks)


@pytest.mark.parametrize("backend_name", ["xgi", "hypernetx", "hypergraphx"])
@pytest.mark.parametrize("fixture_name", ["fano", "sts_9"])
def test_single_card_renders(tmp_path: Path, backend_name: str, fixture_name: str) -> None:
    # Skip if the optional backend dependency is missing.
    pytest.importorskip(backend_name)

    import matplotlib.pyplot as plt

    from isalhg.viz.composite import single_card_figure
    from isalhg.viz.style import save_figure

    H = _fano() if fixture_name == "fano" else _sts9()
    algo = GreedyMin(k=required_k(H))
    tokens, trace = algo.encode_with_trace(H)
    fig = single_card_figure(
        trace.snapshots[-1],
        H,
        tuple(tokens),
        backend=backend_name,
    )
    paths = save_figure(fig, tmp_path / f"{fixture_name}_{backend_name}_end", formats=("png",))
    plt.close(fig)
    assert len(paths) == 1
    assert paths[0].exists()
    assert paths[0].stat().st_size > 1000


@pytest.mark.parametrize("backend_name", ["xgi"])
def test_roundtrip_figure_renders(tmp_path: Path, backend_name: str) -> None:
    pytest.importorskip(backend_name)

    import matplotlib.pyplot as plt

    from isalhg.core.string_to_hypergraph import StringToHypergraph
    from isalhg.viz.composite import roundtrip_figure
    from isalhg.viz.style import save_figure

    H = _fano()
    k = required_k(H)
    algo = GreedyMin(k=k)
    tokens, h2s_trace = algo.encode_with_trace(H)
    interpreter = StringToHypergraph(tokens, k=k)
    _, s2h_trace = interpreter.run_with_trace(direction="s2h")
    fig = roundtrip_figure(
        s2h_trace.snapshots,
        h2s_trace.snapshots,
        H,
        tuple(tokens),
        backend=backend_name,
        n_columns=4,
    )
    paths = save_figure(fig, tmp_path / f"fano_{backend_name}_roundtrip", formats=("png",))
    plt.close(fig)
    assert paths[0].exists()
    assert paths[0].stat().st_size > 5000
