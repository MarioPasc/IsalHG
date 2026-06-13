"""Unit tests for :class:`isalhg.protocols.pairwise_iso.PairwiseIsoProtocol`."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.datasets.base import HypergraphDataset
from isalhg.datasets.schemas import DatasetItem, DatasetMetadata, LabelVocabulary
from isalhg.errors import ProtocolPreconditionError
from isalhg.iso_backends.isalhg_backend import IsalHGBackend
from isalhg.protocols.pairwise_iso import PairwiseIsoProtocol

pytestmark = pytest.mark.unit


class _TwoClassDataset(HypergraphDataset):
    """Two iso-classes, two reps each; total 4 items, 6 unordered pairs.

    Class 0: 3-edge triangle on 3 nodes (and its permutation).
    Class 1: 4-node hypergraph with two 3-edges sharing 2 vertices.
    """

    def __init__(self) -> None:
        h0 = SparseHypergraph(
            n_nodes=3,
            hyperedges=[frozenset({0, 1}), frozenset({1, 2}), frozenset({0, 2})],
        )
        h0p = permute(h0, [2, 0, 1])
        h1 = SparseHypergraph(
            n_nodes=4,
            hyperedges=[frozenset({0, 1, 2}), frozenset({0, 1, 3})],
        )
        h1p = permute(h1, [3, 2, 1, 0])
        self._items = (
            DatasetItem(item_id="c0_r0", hypergraph=h0, iso_class=0),
            DatasetItem(item_id="c0_r1", hypergraph=h0p, iso_class=0),
            DatasetItem(item_id="c1_r0", hypergraph=h1, iso_class=1),
            DatasetItem(item_id="c1_r1", hypergraph=h1p, iso_class=1),
        )

    @property
    def name(self) -> str:
        return "_two_class"

    @property
    def metadata(self) -> DatasetMetadata:
        return DatasetMetadata(
            name=self.name,
            n_items=len(self._items),
            arity_range=(2, 3),
            n_nodes_range=(3, 4),
            has_iso_labels=True,
            source="test fixture",
            label_vocabulary=LabelVocabulary.trivial(),
        )

    def __iter__(self) -> Iterator[DatasetItem]:
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)


class _UnlabelledDataset(_TwoClassDataset):
    @property
    def metadata(self) -> DatasetMetadata:
        m = super().metadata
        return DatasetMetadata(
            name=m.name,
            n_items=m.n_items,
            arity_range=m.arity_range,
            n_nodes_range=m.n_nodes_range,
            has_iso_labels=False,
            source=m.source,
            label_vocabulary=m.label_vocabulary,
        )


def test_isalhg_backend_reports_fp_fn_zero() -> None:
    proto = PairwiseIsoProtocol(check_bijection=False)
    result = proto.measure(IsalHGBackend(), _TwoClassDataset(), seed=0)
    conf = result.measurements["confusion"]
    assert conf["false_positive"] == 0
    assert conf["false_negative"] == 0
    # 2 within-class pairs (c0_r0 vs c0_r1; c1_r0 vs c1_r1).
    assert conf["true_positive"] == 2
    # 4 cross-class pairs (c0 x c1).
    assert conf["true_negative"] == 4


def test_unlabelled_dataset_raises_precondition() -> None:
    proto = PairwiseIsoProtocol()
    with pytest.raises(ProtocolPreconditionError):
        proto.measure(IsalHGBackend(), _UnlabelledDataset(), seed=0)


def test_result_carries_self_describing_identifiers() -> None:
    proto = PairwiseIsoProtocol(check_bijection=False)
    backend = IsalHGBackend()
    dataset = _TwoClassDataset()
    result = proto.measure(backend, dataset, seed=7)
    assert result.protocol == "pairwise_iso"
    assert result.backend == backend.name
    assert result.dataset == dataset.name
    assert result.seed == 7
    assert result.wall_clock_s >= 0.0
    assert result.measurements["n_items"] == 4
    assert result.measurements["n_pairs"] == 6
