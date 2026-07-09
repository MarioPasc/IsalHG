"""Unit tests for the node-labeled ARB/Benson loader.

Anchored on Qin et al. (ICDE 2023) Table I: PS = 242 nodes / 12,704 hyperedges
/ 11 label classes; HS = 327 / 7,818 / 9. Tests are skipped when the local
dataset mirror is absent (external data, not shipped with the repo).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from isalhg.core.sparse_hypergraph import ego_network
from isalhg.datasets.arb_benson import ARBBensonDataset
from isalhg.datasets.registry import get_dataset
from isalhg.datasets.schemas import LabelVocabulary
from isalhg.errors import DatasetIntegrityError

pytestmark = pytest.mark.unit

DATA_ROOT = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/misc/HGED/data")

requires_data = pytest.mark.skipif(
    not DATA_ROOT.is_dir(), reason="ARB/Benson local mirror not mounted"
)


class TestLabelVocabularyFit:
    def test_lexicographic_contiguous_ids(self) -> None:
        vocab = LabelVocabulary.fit([(["b", "a"], ["x"]), (["c", "a"], [])])
        assert vocab.vertex_symbols == ("a", "b", "c")
        assert vocab.edge_symbols == ("x",)

    def test_empty_side_falls_back_to_trivial(self) -> None:
        vocab = LabelVocabulary.fit([(["a"], ())])
        assert vocab.edge_symbols == ("⊥",)
        assert vocab.n_edge_labels == 1


@requires_data
class TestContactPrimarySchool:
    def test_table_i_stats(self) -> None:
        ds = ARBBensonDataset(DATA_ROOT, "contact-primary-school")
        item = next(iter(ds))
        assert item.hypergraph.n_nodes == 242
        assert item.hypergraph.n_edges == 12704
        assert item.extra["m_file"] == 12704
        assert ds.metadata.label_vocabulary.n_vertex_labels == 11
        assert ds.metadata.n_items == 1 and len(ds) == 1

    def test_labels_are_composite_symbols(self) -> None:
        ds = ARBBensonDataset(DATA_ROOT, "contact-primary-school")
        vocab = ds.metadata.label_vocabulary
        # PS labels are single class names; composites degenerate to them.
        assert all("," not in s for s in vocab.vertex_symbols)

    def test_ego_extraction_runs(self) -> None:
        ds = ARBBensonDataset(DATA_ROOT, "contact-primary-school")
        H = next(iter(ds)).hypergraph
        ego = ego_network(H, 0)
        assert 1 <= ego.n_nodes <= H.n_nodes
        assert ego.n_vertex_labels == H.n_vertex_labels


@requires_data
class TestContactHighSchool:
    def test_table_i_stats(self) -> None:
        ds = ARBBensonDataset(DATA_ROOT, "contact-high-school")
        item = next(iter(ds))
        assert item.hypergraph.n_nodes == 327
        assert item.hypergraph.n_edges == 7818
        assert ds.metadata.label_vocabulary.n_vertex_labels == 9


@requires_data
class TestMathoverflow:
    def test_stats_and_composite_labels(self) -> None:
        ds = ARBBensonDataset(DATA_ROOT, "mathoverflow-answers")
        item = next(iter(ds))
        assert item.hypergraph.n_nodes == 73851
        assert item.extra["m_file"] == 5446
        # One duplicate member-set in the file merges under the set semantics.
        assert item.extra["m_loaded"] == 5445
        vocab = ds.metadata.label_vocabulary
        # Multi-tag users produce composite (comma-joined, sorted) symbols.
        assert any("," in s for s in vocab.vertex_symbols)


@requires_data
class TestRegistry:
    def test_get_dataset_by_name(self) -> None:
        ds = get_dataset("arb_benson", {"root": str(DATA_ROOT), "name": "contact-high-school"})
        assert ds.name == "arb_benson:contact-high-school"


class TestErrors:
    def test_missing_directory_raises(self, tmp_path: Path) -> None:
        ds = ARBBensonDataset(tmp_path, "nope")
        with pytest.raises(DatasetIntegrityError):
            _ = ds.metadata
