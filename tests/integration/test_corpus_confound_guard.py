"""Corpus confound guard (T-M4b) — the size confound cannot silently return.

The Stratum A defect: 17 design families occupied only 14 distinct ``(n, m)``
cells, so ``|Δn| + |Δm|`` alone scored A2 ARI 0.442 / A3 AUC 0.932 and the
task tables measured size encoding, not representation quality
(``scripts/diagnostics/size_confound_probe.py``, 2026-08-09).

This guard pins the repaired contract on the production Stratum C cells: every
cell realizes exactly one ``(n, m)`` pair and one degree sequence, and the two
naive baselines are *identically zero* on every pair — the structural floor by
construction, not by argument.
"""

from __future__ import annotations

import numpy as np
import pytest

from experiments.article.analysis.sweep_multi_seed import (
    STRATUM_C_CELLS,
    build_stratum_c_seed_corpus,
)
from isalhg.metric_space.registry import get_distance

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(("n_nodes", "n_edges"), STRATUM_C_CELLS)
def test_stratum_c_cell_has_no_size_or_degree_signal(n_nodes: int, n_edges: int) -> None:
    hypergraphs, labels = build_stratum_c_seed_corpus(n_nodes=n_nodes, n_edges=n_edges, seed=0)
    assert len(hypergraphs) >= 2
    assert len(set(labels)) >= 2

    # One (n, m) cell — the Stratum A defect was 17 families / 14 cells.
    cells = {(H.n_nodes, H.n_edges) for H in hypergraphs}
    assert cells == {(n_nodes, n_edges)}

    # One degree sequence across the whole cell.
    degseqs = {tuple(sorted(H.degree(v) for v in range(H.n_nodes))) for H in hypergraphs}
    assert len(degseqs) == 1

    # Both naive baselines identically zero on every pair.
    for dist_name in ("size_l1", "degree_seq_l1"):
        D = np.asarray(get_distance(dist_name).matrix(hypergraphs), dtype=float)
        assert np.all(D == 0.0), f"{dist_name} is nonzero on cell ({n_nodes}, {n_edges})"
