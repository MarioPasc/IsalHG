"""Unit tests for :mod:`isalhg.datasets.synthetic.exhaustive_small`."""

from __future__ import annotations

import pytest

from isalhg.datasets.schemas import DatasetItem, LabelVocabulary
from isalhg.datasets.synthetic.exhaustive_small import ExhaustiveSmallHypergraphs
from isalhg.errors import BackendUnavailableError

pytestmark = pytest.mark.unit


class TestInitValidation:
    def test_unknown_dedup_backend_raises_at_init(self) -> None:
        with pytest.raises(BackendUnavailableError):
            ExhaustiveSmallHypergraphs(
                n_range=(3, 3),
                arity_range=(2, 2),
                max_edges=2,
                include_designs=False,
                permutations_per_class=1,
                dedup_backend_name="__never_registered__",
            )


class TestEnumeration:
    def test_n3_arity2_small_universe(self) -> None:
        ds = ExhaustiveSmallHypergraphs(
            n_range=(3, 3),
            arity_range=(2, 2),
            max_edges=3,
            include_designs=False,
            permutations_per_class=1,
        )
        items = list(ds)
        # On 3 nodes with arity-2 edges, connected hypergraphs up to iso are
        # the path P_3 (2 edges) and the triangle (3 edges). Single edges
        # leave one vertex isolated.
        assert len(items) == 2
        iso_classes = {it.iso_class for it in items}
        assert iso_classes == {0, 1}

    def test_permutations_share_iso_class(self) -> None:
        ds = ExhaustiveSmallHypergraphs(
            n_range=(3, 4),
            arity_range=(2, 3),
            max_edges=3,
            include_designs=False,
            permutations_per_class=3,
        )
        items = list(ds)
        from collections import Counter

        counts = Counter(it.iso_class for it in items)
        assert all(v == 3 for v in counts.values()), counts

    def test_deterministic_iteration_under_seed(self) -> None:
        ds1 = ExhaustiveSmallHypergraphs(
            n_range=(3, 4),
            arity_range=(2, 3),
            max_edges=3,
            include_designs=False,
            permutations_per_class=2,
            seed_value=42,
        )
        ds2 = ExhaustiveSmallHypergraphs(
            n_range=(3, 4),
            arity_range=(2, 3),
            max_edges=3,
            include_designs=False,
            permutations_per_class=2,
            seed_value=42,
        )
        items1 = list(ds1)
        items2 = list(ds2)
        assert len(items1) == len(items2)
        for a, b in zip(items1, items2, strict=True):
            assert a.item_id == b.item_id
            assert a.iso_class == b.iso_class

    def test_different_seeds_change_permutation_only(self) -> None:
        ds1 = ExhaustiveSmallHypergraphs(
            n_range=(3, 3),
            arity_range=(2, 2),
            max_edges=3,
            include_designs=False,
            permutations_per_class=2,
            seed_value=0,
        )
        ds2 = ExhaustiveSmallHypergraphs(
            n_range=(3, 3),
            arity_range=(2, 2),
            max_edges=3,
            include_designs=False,
            permutations_per_class=2,
            seed_value=99,
        )
        items1 = list(ds1)
        items2 = list(ds2)
        # Iso classes (and class IDs) are seed-independent; only the
        # permutation-induced extra payloads differ.
        assert [it.iso_class for it in items1] == [it.iso_class for it in items2]

    def test_small_named_designs_are_emitted(self) -> None:
        ds = ExhaustiveSmallHypergraphs(
            n_range=(3, 3),
            arity_range=(2, 2),
            max_edges=2,
            include_designs=True,
            include_large_designs=False,
            permutations_per_class=1,
        )
        items = list(ds)
        named = [it for it in items if it.extra.get("source") == "named_design"]
        names = {it.extra["design_name"] for it in named}
        assert names == {"fano_plane_sts7", "sts_9_ag23"}

    def test_large_designs_require_pynauty_dedup(self) -> None:
        # IsalHG fingerprint on GQ(2,2) currently takes ~3 minutes; the test
        # opts the large designs in but uses pynauty as the dedup oracle to
        # keep the runtime tractable.
        pytest.importorskip("pynauty")
        ds = ExhaustiveSmallHypergraphs(
            n_range=(3, 3),
            arity_range=(2, 2),
            max_edges=2,
            include_designs=True,
            include_large_designs=True,
            dedup_backend_name="pynauty_levi",
            permutations_per_class=1,
        )
        items = list(ds)
        named = [it for it in items if it.extra.get("source") == "named_design"]
        names = {it.extra["design_name"] for it in named}
        assert names == {
            "fano_plane_sts7",
            "sts_9_ag23",
            "cyclic_triple_13_014",
            "cyclic_triple_13_016",
            "gq_2_2_doily",
        }


class TestMetadata:
    def test_trivial_vocabulary(self) -> None:
        ds = ExhaustiveSmallHypergraphs(
            n_range=(3, 3),
            arity_range=(2, 2),
            max_edges=2,
            include_designs=False,
            permutations_per_class=1,
        )
        meta = ds.metadata
        assert meta.has_iso_labels is True
        assert meta.label_vocabulary == LabelVocabulary.trivial()

    def test_n_items_matches_len(self) -> None:
        ds = ExhaustiveSmallHypergraphs(
            n_range=(3, 4),
            arity_range=(2, 3),
            max_edges=3,
            include_designs=False,
            permutations_per_class=2,
        )
        n = len(list(ds))
        assert ds.metadata.n_items == n
        assert len(ds) == n


class TestItemShape:
    def test_every_item_carries_iso_class(self) -> None:
        ds = ExhaustiveSmallHypergraphs(
            n_range=(3, 4),
            arity_range=(2, 3),
            max_edges=3,
            include_designs=True,
            permutations_per_class=2,
        )
        for item in ds:
            assert isinstance(item, DatasetItem)
            assert item.iso_class is not None
            assert item.hypergraph.is_connected()
