"""Unit tests for the size-controlled swap-planted corpus (T-M4b).

The cell contract: every item shares one ``(n_nodes, n_edges)``, one uniform
arity ``k``, and one exact degree sequence, so ``size_l1`` and
``degree_seq_l1`` are identically zero on every pair by construction.
"""

from __future__ import annotations

import pytest

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.datasets.registry import get_dataset
from isalhg.datasets.synthetic.planted_families import PlantedFamilyDataset
from isalhg.datasets.synthetic.size_controlled_corpus import SizeControlledCellDataset

pytestmark = pytest.mark.unit

_SMALL = {
    "n_nodes": 8,
    "n_edges": 10,
    "k": 3,
    "n_families": 3,
    "members_per_family": 3,
    "t_swaps": 1,
    "sep_swaps": 20,
    "dedup_backend": "isalhg",
}


def _degseq(H: SparseHypergraph) -> tuple[int, ...]:
    return tuple(sorted(H.degree(v) for v in range(H.n_nodes)))


def _edge_sets(ds: SizeControlledCellDataset) -> list[tuple[str, frozenset[frozenset[int]]]]:
    return [
        (it.item_id, frozenset(members for _e, members, _l in it.hypergraph.iter_edges()))
        for it in ds
    ]


@pytest.fixture(scope="module")
def small_corpus() -> SizeControlledCellDataset:
    return SizeControlledCellDataset(seed_value=0, **_SMALL)


class TestCellContract:
    def test_single_size_cell(self, small_corpus: SizeControlledCellDataset) -> None:
        cells = {(it.hypergraph.n_nodes, it.hypergraph.n_edges) for it in small_corpus}
        assert cells == {(8, 10)}

    def test_single_degree_sequence(self, small_corpus: SizeControlledCellDataset) -> None:
        degseqs = {_degseq(it.hypergraph) for it in small_corpus}
        assert len(degseqs) == 1

    def test_k_uniform(self, small_corpus: SizeControlledCellDataset) -> None:
        arities = {
            len(members) for it in small_corpus for _e, members, _l in it.hypergraph.iter_edges()
        }
        assert arities == {3}

    def test_all_connected(self, small_corpus: SizeControlledCellDataset) -> None:
        assert all(it.hypergraph.is_connected() for it in small_corpus)

    def test_family_labels(self, small_corpus: SizeControlledCellDataset) -> None:
        labels = [it.extra["class_label"] for it in small_corpus]
        assert set(labels) == {0, 1, 2}

    def test_globally_non_isomorphic(self, small_corpus: SizeControlledCellDataset) -> None:
        from isalhg.iso_backends.registry import get_backend

        backend = get_backend("isalhg")
        fps = [backend.fingerprint(it.hypergraph) for it in small_corpus]
        assert len(set(fps)) == len(fps)


class TestDeterminism:
    def test_same_seed_same_corpus(self, small_corpus: SizeControlledCellDataset) -> None:
        again = SizeControlledCellDataset(seed_value=0, **_SMALL)
        assert _edge_sets(small_corpus) == _edge_sets(again)

    def test_seed_rebuilds_everything(self, small_corpus: SizeControlledCellDataset) -> None:
        reseeded = small_corpus.seed(5)
        fresh = SizeControlledCellDataset(seed_value=5, **_SMALL)
        assert _edge_sets(reseeded) == _edge_sets(fresh)
        # a different master seed redraws the base itself
        assert _edge_sets(reseeded) != _edge_sets(small_corpus)

    def test_registry_roundtrip(self) -> None:
        ds = get_dataset("size_controlled_corpus", {"seed_value": 0, **_SMALL})
        assert isinstance(ds, SizeControlledCellDataset)
        assert len(ds) == len(list(ds))


class TestSwapEditKind:
    def test_swap_members_share_seed_degree_sequence(self) -> None:
        ds = SizeControlledCellDataset(seed_value=1, **_SMALL)
        seeds_deg = {_degseq(it.hypergraph) for it in ds if it.extra["is_seed"]}
        members_deg = {_degseq(it.hypergraph) for it in ds if not it.extra["is_seed"]}
        assert members_deg <= seeds_deg

    def test_edit_kind_recorded_in_source(self) -> None:
        ds = PlantedFamilyDataset(
            n_families=2,
            n_nodes=6,
            n_edges=5,
            members_per_family=2,
            edit_kind="swap",
            dedup_backend="isalhg",
            allow_partial=True,
        )
        assert "edit_kind='swap'" in ds.metadata.source
        assert "edit_kind='swap'" in ds.seed(3).metadata.source

    def test_invalid_edit_kind_raises(self) -> None:
        with pytest.raises(ValueError):
            PlantedFamilyDataset(edit_kind="teleport")
