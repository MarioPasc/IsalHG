"""Unit tests for the HIC atlas loader.

These tests exercise the loader without the real HIC data on disk by writing
a synthetic three-hypergraph file to a temporary directory and monkeypatching
``_HIC_FILE_MAP`` to include the test entry.

Baseline (pre-implementation): the stub raises ``NotImplementedError`` from
``__iter__``, ``__len__``, and ``metadata``.  All tests that call those
methods therefore fail before the implementation exists.  The helper functions
``_parse_hic_file`` and ``_largest_connected_component`` do not exist in the
stub, so tests that import them fail with ``ImportError``.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

import isalhg.datasets.hic_atlas as hic_module
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.datasets.hic_atlas import (
    ClassRetentionStats,
    HICAtlasDataset,
    _largest_connected_component,
    _parse_hic_file,
)

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Synthetic HIC file content.
#
# Three hypergraphs:
#  [0] n=5, m=3, class=0 — connected (via shared vertices across edges)
#  [1] n=4, m=2, class=0 — connected
#  [2] n=5, m=3, class=1 — DISCONNECTED: {0,1,2} and {3,4}
#      LCC = {0,1,2} (size 3 > size 2); keeps edges {0,1,2} and {0,1}
# ---------------------------------------------------------------------------

_HIC_CONTENT = textwrap.dedent("""\
    3
    5 3 0
    0 0 0 0 0
    0 1 2
    1 2 3
    2 3 4
    4 2 0
    0 0 0 0
    0 1 2
    1 2 3
    5 3 1
    0 0 0 0 0
    0 1 2
    0 1
    3 4
""")


@pytest.fixture()
def hic_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Synthetic HIC data root with a ``TEST`` dataset and patched file map."""
    ds_dir = tmp_path / "TEST"
    ds_dir.mkdir(parents=True)
    (ds_dir / "test.txt").write_text(_HIC_CONTENT)
    monkeypatch.setitem(hic_module._HIC_FILE_MAP, "TEST", "TEST/test.txt")
    return tmp_path


# ---------------------------------------------------------------------------
# _parse_hic_file
# ---------------------------------------------------------------------------


class TestParseHICFile:
    def test_returns_three_records(self, tmp_path: Path) -> None:
        p = tmp_path / "test.txt"
        p.write_text(_HIC_CONTENT)
        records = _parse_hic_file(p)
        assert len(records) == 3

    def test_first_record_header(self, tmp_path: Path) -> None:
        p = tmp_path / "test.txt"
        p.write_text(_HIC_CONTENT)
        records = _parse_hic_file(p)
        rec = records[0]
        assert rec.n_nodes == 5
        assert rec.class_label == 0
        assert len(rec.hyperedges) == 3

    def test_third_record_class_label(self, tmp_path: Path) -> None:
        p = tmp_path / "test.txt"
        p.write_text(_HIC_CONTENT)
        records = _parse_hic_file(p)
        assert records[2].class_label == 1

    def test_vertex_labels_length_matches_n_nodes(self, tmp_path: Path) -> None:
        p = tmp_path / "test.txt"
        p.write_text(_HIC_CONTENT)
        records = _parse_hic_file(p)
        for rec in records:
            assert len(rec.vertex_labels) == rec.n_nodes

    def test_hyperedge_nodes_are_frozensets(self, tmp_path: Path) -> None:
        p = tmp_path / "test.txt"
        p.write_text(_HIC_CONTENT)
        records = _parse_hic_file(p)
        for rec in records:
            for e in rec.hyperedges:
                assert isinstance(e, frozenset)


# ---------------------------------------------------------------------------
# _largest_connected_component
# ---------------------------------------------------------------------------


class TestLargestConnectedComponent:
    def test_connected_returns_same_object(self) -> None:
        H = SparseHypergraph(n_nodes=4, hyperedges=[frozenset({0, 1, 2}), frozenset({1, 2, 3})])
        H_lcc, v_after, e_after = _largest_connected_component(H)
        assert H_lcc is H  # no copy needed
        assert v_after == 4
        assert e_after == 2

    def test_disconnected_retains_lcc(self) -> None:
        # {0,1,2} component + {3,4} component; LCC = {0,1,2}
        H = SparseHypergraph(
            n_nodes=5,
            hyperedges=[frozenset({0, 1, 2}), frozenset({0, 1}), frozenset({3, 4})],
        )
        H_lcc, v_after, e_after = _largest_connected_component(H)
        assert H_lcc.n_nodes == 3
        assert H_lcc.n_edges == 2
        assert v_after == 3
        assert e_after == 2

    def test_disconnected_lcc_is_connected(self) -> None:
        H = SparseHypergraph(
            n_nodes=5,
            hyperedges=[frozenset({0, 1, 2}), frozenset({0, 1}), frozenset({3, 4})],
        )
        H_lcc, _, _ = _largest_connected_component(H)
        assert H_lcc.is_connected()

    def test_lcc_vertex_ids_are_contiguous(self) -> None:
        # After remap, vertex IDs must be 0..n-1
        H = SparseHypergraph(
            n_nodes=5,
            hyperedges=[frozenset({0, 1, 2}), frozenset({0, 1}), frozenset({3, 4})],
        )
        H_lcc, _, _ = _largest_connected_component(H)
        assert set(range(H_lcc.n_nodes)) == set(H_lcc.nodes())

    def test_vertex_labels_preserved_in_lcc(self) -> None:
        # Nodes 0,1,2 have labels 1,2,3; nodes 3,4 have labels 0,0
        # n_vertex_labels must be 4 (labels 0,1,2,3)
        H = SparseHypergraph(
            n_nodes=5,
            hyperedges=[frozenset({0, 1, 2}), frozenset({3, 4})],
            n_vertex_labels=4,
            vertex_labels=[1, 2, 3, 0, 0],
        )
        H_lcc, _, _ = _largest_connected_component(H)
        # LCC = {0,1,2} remapped to {0,1,2}, labels preserved
        assert [H_lcc.vertex_label(v) for v in range(H_lcc.n_nodes)] == [1, 2, 3]

    def test_single_vertex_hypergraph(self) -> None:
        H = SparseHypergraph(n_nodes=1, hyperedges=[])
        H_lcc, v_after, e_after = _largest_connected_component(H)
        assert H_lcc.n_nodes == 1
        assert e_after == 0


# ---------------------------------------------------------------------------
# HICAtlasDataset — full class
# ---------------------------------------------------------------------------


class TestHICAtlasDataset:
    def test_len(self, hic_root: Path) -> None:
        ds = HICAtlasDataset(root=hic_root, hic_name="TEST")
        assert len(ds) == 3

    def test_len_matches_iter_count(self, hic_root: Path) -> None:
        ds = HICAtlasDataset(root=hic_root, hic_name="TEST")
        assert len(ds) == sum(1 for _ in ds)

    def test_all_hypergraphs_are_connected(self, hic_root: Path) -> None:
        ds = HICAtlasDataset(root=hic_root, hic_name="TEST")
        for item in ds:
            assert item.hypergraph.is_connected(), f"item {item.item_id!r} is not connected"

    def test_iso_class_is_none_for_all_items(self, hic_root: Path) -> None:
        # HIC class labels are semantic classification targets (genre, category),
        # not isomorphism certificates.  iso_class must be None so pairwise_iso
        # protocols cannot misinterpret same-class as same-isomorphism-class.
        ds = HICAtlasDataset(root=hic_root, hic_name="TEST")
        for item in ds:
            assert item.iso_class is None, (
                f"item {item.item_id!r} has iso_class={item.iso_class!r}; "
                "expected None (HIC labels are classification targets, not iso certs)"
            )

    def test_class_label_in_extra(self, hic_root: Path) -> None:
        ds = HICAtlasDataset(root=hic_root, hic_name="TEST")
        items = list(ds)
        assert items[0].extra["class_label"] == 0
        assert items[1].extra["class_label"] == 0
        assert items[2].extra["class_label"] == 1

    def test_metadata_has_iso_labels_false(self, hic_root: Path) -> None:
        # has_iso_labels=False because iso_class is None for every item.
        ds = HICAtlasDataset(root=hic_root, hic_name="TEST")
        assert not ds.metadata.has_iso_labels

    def test_metadata_n_items_matches_len(self, hic_root: Path) -> None:
        ds = HICAtlasDataset(root=hic_root, hic_name="TEST")
        assert ds.metadata.n_items == len(ds)

    def test_name_property(self, hic_root: Path) -> None:
        ds = HICAtlasDataset(root=hic_root, hic_name="TEST")
        assert ds.name == "hic:TEST"

    def test_disconnected_instance_is_restricted_to_lcc(self, hic_root: Path) -> None:
        ds = HICAtlasDataset(root=hic_root, hic_name="TEST")
        items = list(ds)
        # Item 2 (index 2) was originally 5 nodes, 3 edges; LCC is {0,1,2}
        item = items[2]
        assert item.hypergraph.n_nodes == 3
        assert item.hypergraph.n_edges == 2

    def test_retention_report_has_both_classes(self, hic_root: Path) -> None:
        ds = HICAtlasDataset(root=hic_root, hic_name="TEST")
        report = ds.retention_report
        assert 0 in report
        assert 1 in report

    def test_retention_connected_class_is_100_percent(self, hic_root: Path) -> None:
        ds = HICAtlasDataset(root=hic_root, hic_name="TEST")
        # Class 0: both instances are connected → full retention
        stats = ds.retention_report[0]
        assert stats.vertex_fraction == pytest.approx(1.0)
        assert stats.edge_fraction == pytest.approx(1.0)

    def test_retention_disconnected_class_is_partial(self, hic_root: Path) -> None:
        ds = HICAtlasDataset(root=hic_root, hic_name="TEST")
        # Class 1: 5 vertices → 3 after LCC; 3 edges → 2 after
        stats = ds.retention_report[1]
        assert stats.vertices_before == 5
        assert stats.vertices_after == 3
        assert stats.edges_before == 3
        assert stats.edges_after == 2
        assert stats.vertex_fraction == pytest.approx(3 / 5)
        assert stats.edge_fraction == pytest.approx(2 / 3)

    def test_trivial_vocabulary_for_all_zero_labels(self, hic_root: Path) -> None:
        ds = HICAtlasDataset(root=hic_root, hic_name="TEST")
        vocab = ds.metadata.label_vocabulary
        # All vertex labels are 0 in the synthetic file → trivial vocabulary
        assert vocab.n_vertex_labels == 1
        assert vocab.vertex_symbols == ("⊥",)

    def test_invalid_hic_name_raises(self, hic_root: Path) -> None:
        with pytest.raises(ValueError, match="Unknown HIC dataset"):
            HICAtlasDataset(root=hic_root, hic_name="NONEXISTENT")

    def test_repr(self, hic_root: Path) -> None:
        ds = HICAtlasDataset(root=hic_root, hic_name="TEST")
        r = repr(ds)
        assert "HICAtlasDataset" in r
        assert "n_items=3" in r


# ---------------------------------------------------------------------------
# ClassRetentionStats
# ---------------------------------------------------------------------------


class TestClassRetentionStats:
    def test_full_retention(self) -> None:
        s = ClassRetentionStats(
            class_label=0,
            n_instances=2,
            vertices_before=10,
            vertices_after=10,
            edges_before=6,
            edges_after=6,
        )
        assert s.vertex_fraction == pytest.approx(1.0)
        assert s.edge_fraction == pytest.approx(1.0)

    def test_partial_retention(self) -> None:
        s = ClassRetentionStats(
            class_label=1,
            n_instances=1,
            vertices_before=5,
            vertices_after=3,
            edges_before=3,
            edges_after=2,
        )
        assert s.vertex_fraction == pytest.approx(0.6)
        assert s.edge_fraction == pytest.approx(2 / 3)

    def test_zero_before_gives_one(self) -> None:
        s = ClassRetentionStats(
            class_label=0,
            n_instances=0,
            vertices_before=0,
            vertices_after=0,
            edges_before=0,
            edges_after=0,
        )
        assert s.vertex_fraction == pytest.approx(1.0)
        assert s.edge_fraction == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Registry integration
# ---------------------------------------------------------------------------


class TestRegistry:
    def test_hic_atlas_is_in_lazy_modules(self) -> None:
        from isalhg.datasets.registry import _LAZY_MODULES

        assert "hic_atlas" in _LAZY_MODULES

    def test_hic_atlas_module_path_correct(self) -> None:
        from isalhg.datasets.registry import _LAZY_MODULES

        assert _LAZY_MODULES["hic_atlas"] == "isalhg.datasets.hic_atlas"

    def test_get_dataset_dispatches(self, hic_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from isalhg.datasets.registry import get_dataset

        ds = get_dataset("hic_atlas", {"root": str(hic_root), "hic_name": "TEST"})
        assert ds.name == "hic:TEST"
        assert len(ds) == 3
