"""Unit tests for ``isalhg.datasets.synthetic.symmetric_designs``."""

from __future__ import annotations

import pytest

from isalhg.datasets.registry import get_dataset
from isalhg.datasets.synthetic.symmetric_designs import SymmetricDesigns

pytestmark = pytest.mark.unit


def test_dataset_has_five_items() -> None:
    ds = SymmetricDesigns()
    items = list(ds)
    assert len(items) == 5
    assert len(ds) == 5


def test_item_ids_are_unique_and_named() -> None:
    items = list(SymmetricDesigns())
    ids = [item.item_id for item in items]
    assert sorted(ids) == sorted(set(ids))
    expected = {
        "fano_sts7",
        "sts9",
        "sts13_cyclic_014",
        "sts13_cyclic_016",
        "gq_2_2_doily",
    }
    assert set(ids) == expected


def test_all_items_are_3_uniform() -> None:
    for item in SymmetricDesigns():
        for e in item.hypergraph.edges():
            assert len(item.hypergraph.members(e)) == 3


def test_iteration_is_deterministic() -> None:
    a = [item.item_id for item in SymmetricDesigns()]
    b = [item.item_id for item in SymmetricDesigns()]
    assert a == b


def test_seed_is_noop() -> None:
    ds = SymmetricDesigns()
    assert ds.seed(123) is ds or ds.seed(123).name == ds.name


def test_metadata_arity_3() -> None:
    meta = SymmetricDesigns().metadata
    assert meta.arity_range == (3, 3)
    assert meta.has_iso_labels is False
    assert meta.n_items == 5


def test_registry_dispatch() -> None:
    ds = get_dataset("symmetric_designs", {})
    assert len(list(ds)) == 5
