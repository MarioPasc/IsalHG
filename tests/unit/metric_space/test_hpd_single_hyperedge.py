"""Regression tests for the single-hyperedge defect in the vendored HPD code.

``_hpd_vendor.hyperedge_portrait`` allocated the ``k``-axis of the portrait
tensor with extent ``N`` (the hyperedge count). ``k`` is the number of
hyperedges of a given size at a given line-graph distance from hyperedge
``i``; at distance ``0`` the bin holds ``i`` alone (``k <= 1``) and at
distance ``>= 1`` it excludes ``i`` (``k <= N - 1``), so the attainable
maximum is ``max(1, N - 1)`` and the required extent is ``max(N, 2)``.
Upstream's ``N`` is exact for every ``N >= 2`` and one short at ``N == 1``,
where the lone hyperedge counts itself and writes ``k = 1 = N``.

Two things are pinned here:

1. the crash — the smallest hand-made trigger, and the real corrupted
   ``ndc_classes`` member that surfaced it in the RQ4 anomaly screen;
2. the no-op guarantee — every portrait that upstream *could* compute
   (``N >= 2``) is element-for-element unchanged by the fix. The "before"
   side is :func:`_upstream_hyperedge_portrait`, a frozen copy of the
   upstream body carrying the original ``N`` extent.
"""

from __future__ import annotations

import os
from itertools import combinations
from pathlib import Path

import numpy as np
import pytest

from isalhg.adapters.xgi_adapter import XGIAdapter
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.metric_space.representations import _hpd_vendor
from isalhg.metric_space.representations.hpd import HPDDistance

pytestmark = pytest.mark.unit


# --------------------------------------------------------------------------- #
# frozen pre-fix reference
# --------------------------------------------------------------------------- #


def _upstream_hyperedge_portrait(H):  # noqa: ANN001, ANN202
    """The upstream ``hyperedge_portrait`` body, verbatim, before the fix.

    Kept as a frozen local copy rather than reconstructed from git so the
    comparison is independent of which commit the test runs on. The only
    difference from the shipped function is the ``k``-axis extent: ``N``
    here, ``max(N, 2)`` there.
    """
    import networkx as nx
    import xgi

    G = _hpd_vendor.H_to_G_mapping(H)
    N = G.number_of_nodes()
    sizes_dict = nx.get_node_attributes(G, "size")
    s_max = np.max(xgi.unique_edge_sizes(H))
    CC = [G.subgraph(c).copy() for c in nx.connected_components(G)]

    dist_dict = {}
    lengths = set()
    for Gc in CC:
        for i in Gc.nodes:
            dist_dict[i] = nx.shortest_path_length(Gc, i)
            lengths |= set(dist_dict[i].values())

    dia = max(lengths)
    B = np.zeros((s_max - 1, s_max - 1, dia + 1, N), dtype=int)

    for Gc in CC:
        for i in Gc.nodes:
            m = sizes_dict[i] - 2
            dd_i = dist_dict[i]
            counter = np.zeros((s_max - 1, dia + 1), dtype=int)
            for j in Gc.nodes:
                counter[sizes_dict[j] - 2][dd_i[j]] += 1
            for n in range(s_max - 1):
                for length in range(dia + 1):
                    k = counter[n][length]
                    B[m][n][length][k] += 1

    return B


# --------------------------------------------------------------------------- #
# fixtures
# --------------------------------------------------------------------------- #

#: Smallest hypergraph that triggers the defect: one hyperedge, two nodes.
SMALLEST_TRIGGER = SparseHypergraph(n_nodes=2, hyperedges=[frozenset({0, 1})])

#: The real offender, pinned so this file has teeth without the frozen drive.
#:
#: Collection ``ndc_classes``, member ``kb_id="3@401"``, corruption
#: ``missing_fact`` at ``budget=2``, ``seed=0``. That member carries three
#: facts; dropping two leaves the single fact ``(0, (0, 1, 2, 3, 4, 5))`` over
#: ``n = 6`` constants, i.e. one hyperedge spanning every node.
NDC_CLASSES_OFFENDER_KB_ID = "3@401"
NDC_CLASSES_OFFENDER_CORRUPTION = ("missing_fact", 2, 0)
NDC_CLASSES_OFFENDER = SparseHypergraph(
    n_nodes=6,
    hyperedges=[frozenset({0, 1, 2, 3, 4, 5})],
)

CORPORA_ROOT = Path(
    os.environ.get(
        "ISALHG_CORPORA_ROOT",
        "/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE/corpora",
    )
)
COLLECTIONS = (
    "ndc_classes",
    "ndc_substances",
    "synthetic_rq1",
    "wd50k100",
    "wd50k66",
    "wd50k66_full",
)

requires_corpora = pytest.mark.skipif(
    not CORPORA_ROOT.is_dir(),
    reason=f"frozen TKDE corpora not mounted at {CORPORA_ROOT}",
)


def _to_xgi(H: SparseHypergraph):  # noqa: ANN202
    return XGIAdapter().to_external(H)


def _synthetic_corpus() -> list[SparseHypergraph]:
    """Connected and disconnected hypergraphs with ``N >= 2`` hyperedges.

    Deterministic: every subset-of-a-small-ground-set combination, not a
    random draw, so the no-op comparison is reproducible without a seed.
    """
    nodes = range(7)
    candidates = [frozenset(c) for size in (2, 3, 4) for c in combinations(nodes, size)]
    corpus: list[SparseHypergraph] = []
    for count in (2, 3, 5):
        for start in range(0, 40, 7):
            edges = candidates[start : start + count]
            if len(edges) == count:
                corpus.append(SparseHypergraph(n_nodes=7, hyperedges=edges))
    return corpus


# --------------------------------------------------------------------------- #
# 1. the crash, before and after
# --------------------------------------------------------------------------- #


class TestSingleHyperedgeCrash:
    """The defect reproduces on the pre-fix body and is gone from the shipped one."""

    @pytest.mark.parametrize(
        ("label", "hypergraph"),
        [
            ("smallest_trigger", SMALLEST_TRIGGER),
            ("ndc_classes_3@401_missing_fact_b2_s0", NDC_CLASSES_OFFENDER),
            ("single_edge_arity_3", SparseHypergraph(n_nodes=3, hyperedges=[frozenset({0, 1, 2})])),
        ],
    )
    def test_pre_fix_body_raises_index_error(
        self, label: str, hypergraph: SparseHypergraph
    ) -> None:
        with pytest.raises(IndexError, match=r"index 1 is out of bounds for axis 0 with size 1"):
            _upstream_hyperedge_portrait(_to_xgi(hypergraph))

    @pytest.mark.parametrize(
        ("label", "hypergraph"),
        [
            ("smallest_trigger", SMALLEST_TRIGGER),
            ("ndc_classes_3@401_missing_fact_b2_s0", NDC_CLASSES_OFFENDER),
            ("single_edge_arity_3", SparseHypergraph(n_nodes=3, hyperedges=[frozenset({0, 1, 2})])),
        ],
    )
    def test_fixed_body_returns_a_portrait(self, label: str, hypergraph: SparseHypergraph) -> None:
        arity = len(next(hypergraph.hyperedges()))
        B = _hpd_vendor.hyperedge_portrait(_to_xgi(hypergraph))

        assert B.shape == (arity - 1, arity - 1, 1, 2), "the k-axis must admit k = 1 at N = 1"
        # One hyperedge, of size ``arity``, at line-graph distance 0 from
        # itself: it lands in bin (m, m, 0, 1) and in (m, n, 0, 0) for the
        # other ``arity - 2`` sizes the portrait tracks.
        m = arity - 2
        assert B[m][m][0][1] == 1, "the lone hyperedge sees itself at distance 0"
        assert B.sum() == arity - 1
        assert B[m].sum() == arity - 1, "only the size-m slice is populated"

    def test_distance_against_a_normal_hypergraph_is_finite(self) -> None:
        """The padded JSD path survives an ``N = 1`` portrait on either side."""
        other = SparseHypergraph(n_nodes=5, hyperedges=[frozenset({0, 1, 2}), frozenset({2, 3, 4})])
        d = HPDDistance()
        forward = d.pairwise(NDC_CLASSES_OFFENDER, other)
        backward = d.pairwise(other, NDC_CLASSES_OFFENDER)
        assert np.isfinite(forward)
        assert forward == pytest.approx(backward)
        assert d.pairwise(NDC_CLASSES_OFFENDER, NDC_CLASSES_OFFENDER) == pytest.approx(0.0)

    def test_matrix_over_a_corpus_containing_a_single_edge_member(self) -> None:
        corpus = [
            NDC_CLASSES_OFFENDER,
            SMALLEST_TRIGGER,
            SparseHypergraph(n_nodes=5, hyperedges=[frozenset({0, 1, 2}), frozenset({2, 3, 4})]),
        ]
        mat = HPDDistance().matrix(corpus)
        assert mat.shape == (3, 3)
        assert np.all(np.isfinite(mat))
        np.testing.assert_allclose(mat, mat.T)
        np.testing.assert_allclose(np.diag(mat), 0.0)


# --------------------------------------------------------------------------- #
# 2. the fix is a no-op wherever upstream could already compute
# --------------------------------------------------------------------------- #


class TestPortraitUnchangedForComputableInputs:
    """Every ``N >= 2`` portrait is identical before and after the fix."""

    def test_synthetic_corpus(self) -> None:
        corpus = _synthetic_corpus()
        assert len(corpus) >= 15, "guard against an accidentally empty sweep"
        for H in corpus:
            assert H.n_edges >= 2
            xgi_H = _to_xgi(H)
            before = _upstream_hyperedge_portrait(xgi_H)
            after = _hpd_vendor.hyperedge_portrait(xgi_H)
            assert after.shape == before.shape
            assert after.dtype == before.dtype
            assert np.array_equal(after, before)

    @requires_corpora
    def test_every_ndc_classes_member(self) -> None:
        from isalhg.datasets.kb.io import read_jsonl

        records = list(read_jsonl(CORPORA_ROOT / "ndc_classes").records)
        assert len(records) > 0
        for record in records:
            xgi_H = _to_xgi(record.to_hypergraph())
            before = _upstream_hyperedge_portrait(xgi_H)
            after = _hpd_vendor.hyperedge_portrait(xgi_H)
            assert after.shape == before.shape
            assert np.array_equal(after, before), f"portrait changed for {record.kb_id}"

    @requires_corpora
    @pytest.mark.parametrize("collection", COLLECTIONS)
    def test_first_50_members_of_each_frozen_collection(self, collection: str) -> None:
        from isalhg.datasets.kb.io import read_jsonl

        directory = CORPORA_ROOT / collection
        if not (directory / "records.jsonl").is_file():
            pytest.skip(f"collection {collection} not frozen at {directory}")
        for record in list(read_jsonl(directory).records)[:50]:
            xgi_H = _to_xgi(record.to_hypergraph())
            before = _upstream_hyperedge_portrait(xgi_H)
            after = _hpd_vendor.hyperedge_portrait(xgi_H)
            assert after.shape == before.shape
            assert np.array_equal(after, before), f"portrait changed for {record.kb_id}"


# --------------------------------------------------------------------------- #
# 3. the real record, reconstructed from the frozen corpus
# --------------------------------------------------------------------------- #


@requires_corpora
def test_pinned_offender_matches_the_frozen_corpus() -> None:
    """The inline fixture is the record the RQ4 screen actually produced."""
    from isalhg.datasets.kb.corruptions import corrupt
    from isalhg.datasets.kb.io import read_jsonl

    kind, budget, seed = NDC_CLASSES_OFFENDER_CORRUPTION
    records = list(read_jsonl(CORPORA_ROOT / "ndc_classes").records)
    base = next(r for r in records if r.kb_id == NDC_CLASSES_OFFENDER_KB_ID)
    anomaly = corrupt(base, kind, budget, seed)
    assert anomaly is not None

    H = anomaly.to_hypergraph()
    assert H.n_edges == 1, "the corruption must still collapse this member to one fact"
    assert H.n_nodes == NDC_CLASSES_OFFENDER.n_nodes
    assert set(H.hyperedges()) == set(NDC_CLASSES_OFFENDER.hyperedges())

    np.testing.assert_array_equal(
        _hpd_vendor.hyperedge_portrait(_to_xgi(H)),
        _hpd_vendor.hyperedge_portrait(_to_xgi(NDC_CLASSES_OFFENDER)),
    )
