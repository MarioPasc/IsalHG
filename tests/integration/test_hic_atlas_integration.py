"""Integration tests for the HIC atlas loader against the real data on disk.

All tests are skipped when the HIC data root is not mounted.
The data root is expected at the path below (Sandisk2TB external drive).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from isalhg.datasets.hic_atlas import HICAtlasDataset

pytestmark = pytest.mark.integration

HIC_ROOT = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/data/HIC/data/hypergraph")

requires_hic = pytest.mark.skipif(
    not HIC_ROOT.is_dir(),
    reason="HIC data not available (Sandisk2TB not mounted)",
)


@requires_hic
class TestIMDBDirGenreLoads:
    """Smoke tests against the IMDB-Dir-Genre dataset (~3393 instances)."""

    def test_len_nonzero(self) -> None:
        ds = HICAtlasDataset(root=HIC_ROOT, hic_name="IMDB-Dir-Genre")
        assert len(ds) > 0

    def test_all_hypergraphs_connected(self) -> None:
        ds = HICAtlasDataset(root=HIC_ROOT, hic_name="IMDB-Dir-Genre")
        disconnected = [item.item_id for item in ds if not item.hypergraph.is_connected()]
        assert disconnected == [], (
            f"{len(disconnected)} hypergraphs are not connected after LCC restriction"
        )

    def test_all_items_have_none_iso_class(self) -> None:
        ds = HICAtlasDataset(root=HIC_ROOT, hic_name="IMDB-Dir-Genre")
        for item in ds:
            assert item.iso_class is None

    def test_class_label_in_extra_for_all_items(self) -> None:
        ds = HICAtlasDataset(root=HIC_ROOT, hic_name="IMDB-Dir-Genre")
        for item in ds:
            assert "class_label" in item.extra
            assert isinstance(item.extra["class_label"], int)

    def test_metadata_consistent(self) -> None:
        ds = HICAtlasDataset(root=HIC_ROOT, hic_name="IMDB-Dir-Genre")
        md = ds.metadata
        assert not md.has_iso_labels  # genre labels are not iso certs
        assert md.n_items == len(ds)
        assert md.arity_range[0] >= 1
        assert md.arity_range[1] >= md.arity_range[0]
        assert md.n_nodes_range[0] >= 1

    def test_retention_report_populated(self) -> None:
        ds = HICAtlasDataset(root=HIC_ROOT, hic_name="IMDB-Dir-Genre")
        report = ds.retention_report
        assert len(report) > 0
        for cl, stats in report.items():
            assert isinstance(cl, int)
            assert stats.n_instances > 0
            assert 0.0 < stats.vertex_fraction <= 1.0
            assert 0.0 <= stats.edge_fraction <= 1.0

    def test_len_matches_iter_count(self) -> None:
        ds = HICAtlasDataset(root=HIC_ROOT, hic_name="IMDB-Dir-Genre")
        assert len(list(ds)) == len(ds)


@requires_hic
class TestRHG3Loads:
    """Smoke test against the small RHG-3 dataset (~1500 instances)."""

    def test_len_and_connectivity(self) -> None:
        ds = HICAtlasDataset(root=HIC_ROOT, hic_name="RHG-3")
        assert len(ds) > 0
        for item in ds:
            assert item.hypergraph.is_connected()

    def test_arity_range_at_least_3(self) -> None:
        # RHG-3 means 3-uniform hypergraphs
        ds = HICAtlasDataset(root=HIC_ROOT, hic_name="RHG-3")
        assert ds.metadata.arity_range[0] >= 3


@requires_hic
class TestAllDatasetsLoadable:
    """Every known HIC dataset name must load without error."""

    @pytest.mark.parametrize("hic_name", HICAtlasDataset.KNOWN_NAMES)
    def test_loads(self, hic_name: str) -> None:
        ds = HICAtlasDataset(root=HIC_ROOT, hic_name=hic_name)
        assert len(ds) > 0

    @pytest.mark.parametrize("hic_name", HICAtlasDataset.KNOWN_NAMES)
    def test_all_connected(self, hic_name: str) -> None:
        ds = HICAtlasDataset(root=HIC_ROOT, hic_name=hic_name)
        for item in ds:
            assert item.hypergraph.is_connected(), (
                f"{hic_name}: item {item.item_id} is disconnected"
            )
