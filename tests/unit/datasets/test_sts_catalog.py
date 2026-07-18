"""Unit tests for the vendored Steiner-triple-system catalog (T-M0c)."""

from __future__ import annotations

import itertools

import pytest

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.datasets.registry import get_dataset
from isalhg.datasets.synthetic.sts_catalog import (
    STS_ORDERS,
    SteinerTripleSystems,
    steiner_triple_system,
    sts_count,
)
from isalhg.errors import DatasetNotFoundError

pytestmark = pytest.mark.unit

_EXPECTED_COUNTS = {3: 1, 7: 1, 9: 1, 13: 2, 15: 80}


def _pair_coverage(H: SparseHypergraph) -> dict[tuple[int, int], int]:
    cover: dict[tuple[int, int], int] = {}
    for _, members, _ in H.iter_edges():
        for p in itertools.combinations(sorted(members), 2):
            cover[p] = cover.get(p, 0) + 1
    return cover


@pytest.mark.parametrize("n", STS_ORDERS)
def test_catalog_counts_match_classification(n: int) -> None:
    assert sts_count(n) == _EXPECTED_COUNTS[n]


@pytest.mark.parametrize("n", STS_ORDERS)
def test_every_catalog_system_is_a_steiner_triple_system(n: int) -> None:
    for i in range(sts_count(n)):
        H = steiner_triple_system(n, i)
        assert (H.n_nodes, H.n_edges) == (n, n * (n - 1) // 6)
        assert all(len(members) == 3 for _, members, _ in H.iter_edges())
        cover = _pair_coverage(H)
        assert len(cover) == n * (n - 1) // 2
        assert set(cover.values()) == {1}


def test_unknown_order_and_index_raise() -> None:
    with pytest.raises(DatasetNotFoundError):
        steiner_triple_system(11)
    with pytest.raises(DatasetNotFoundError):
        steiner_triple_system(13, 2)
    with pytest.raises(DatasetNotFoundError):
        sts_count(19)


def test_builders_return_fresh_objects() -> None:
    a = steiner_triple_system(13, 0)
    b = steiner_triple_system(13, 0)
    assert a is not b
    a.add_node()
    assert b.n_nodes == 13


def test_dataset_iterates_all_85_with_iso_labels() -> None:
    ds = get_dataset("sts_catalog", {})
    items = list(ds)
    assert len(ds) == len(items) == sum(_EXPECTED_COUNTS.values()) == 85
    ids = [item.item_id for item in items]
    assert len(set(ids)) == 85
    iso_classes = [item.iso_class for item in items]
    assert len(set(iso_classes)) == 85
    assert ds.metadata.has_iso_labels is True


def test_dataset_orders_param_restricts() -> None:
    ds = get_dataset("sts_catalog", {"orders": [13]})
    items = list(ds)
    assert [item.item_id for item in items] == ["sts13_1", "sts13_2"]
    with pytest.raises(DatasetNotFoundError):
        SteinerTripleSystems(orders=(11,))


def test_true_sts13_pair_differs_in_edge_count_from_cyclic_orbit() -> None:
    from isalhg.datasets.synthetic.designs import cyclic_triple_orbit_13

    true_sts = steiner_triple_system(13, 0)
    partial = cyclic_triple_orbit_13((0, 1, 3))
    assert true_sts.n_edges == 26
    assert partial.n_edges == 13
