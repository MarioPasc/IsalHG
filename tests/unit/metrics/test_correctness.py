"""Unit tests for :mod:`isalhg.metrics.correctness`."""

from __future__ import annotations

import pytest

from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.metrics.correctness import (
    ConfusionCounts,
    confusion_from_partitions,
    verify_bijection_certificate,
)

pytestmark = pytest.mark.unit


class TestConfusionFromPartitions:
    def test_all_within_class_pairs_predicted_iso_yields_tp_only(self) -> None:
        gt = {"a": 0, "b": 0, "c": 0}
        pred = {("a", "b"): True, ("a", "c"): True, ("b", "c"): True}
        counts = confusion_from_partitions(gt, pred)
        assert counts == ConfusionCounts(3, 0, 0, 0)

    def test_two_classes_perfect_prediction(self) -> None:
        gt = {"a": 0, "b": 0, "c": 1, "d": 1}
        pred = {
            ("a", "b"): True,
            ("a", "c"): False,
            ("a", "d"): False,
            ("b", "c"): False,
            ("b", "d"): False,
            ("c", "d"): True,
        }
        counts = confusion_from_partitions(gt, pred)
        # 2 TP (a-b, c-d), 4 TN (cross-class), 0 FP, 0 FN
        assert counts == ConfusionCounts(2, 0, 4, 0)

    def test_false_positive_recorded(self) -> None:
        gt = {"a": 0, "b": 1}
        pred = {("a", "b"): True}  # wrongly says iso
        counts = confusion_from_partitions(gt, pred)
        assert counts.false_positive == 1
        assert counts.true_positive == 0

    def test_false_negative_recorded(self) -> None:
        gt = {"a": 0, "b": 0}
        pred = {("a", "b"): False}  # missed iso
        counts = confusion_from_partitions(gt, pred)
        assert counts.false_negative == 1

    def test_reverse_order_pair_accepted(self) -> None:
        gt = {"a": 0, "b": 0}
        pred = {("b", "a"): True}
        counts = confusion_from_partitions(gt, pred)
        assert counts.true_positive == 1

    def test_missing_pair_raises_keyerror(self) -> None:
        gt = {"a": 0, "b": 0, "c": 0}
        pred = {("a", "b"): True}  # missing (a, c) and (b, c)
        with pytest.raises(KeyError):
            confusion_from_partitions(gt, pred)


class TestVerifyBijectionCertificate:
    def test_identity_certificate_on_self(self) -> None:
        H = SparseHypergraph(
            n_nodes=4,
            hyperedges=[frozenset({0, 1, 2}), frozenset({0, 1, 3})],
        )
        sigma = {v: v for v in range(4)}
        assert verify_bijection_certificate(H, H, sigma) is True

    def test_certificate_matches_known_permutation(self) -> None:
        H1 = SparseHypergraph(
            n_nodes=4,
            hyperedges=[frozenset({0, 1, 2}), frozenset({0, 1, 3})],
        )
        sigma_list = [3, 2, 1, 0]
        H2 = permute(H1, sigma_list)
        sigma = {v: sigma_list[v] for v in range(4)}
        assert verify_bijection_certificate(H1, H2, sigma) is True

    def test_wrong_certificate_returns_false(self) -> None:
        H1 = SparseHypergraph(
            n_nodes=4,
            hyperedges=[frozenset({0, 1, 2}), frozenset({0, 1, 3})],
        )
        H2 = permute(H1, [3, 2, 1, 0])
        sigma = {0: 0, 1: 1, 2: 2, 3: 3}  # not the right permutation
        assert verify_bijection_certificate(H1, H2, sigma) is False

    def test_non_bijection_returns_false(self) -> None:
        H = SparseHypergraph(n_nodes=3, hyperedges=[frozenset({0, 1, 2})])
        bad = {0: 0, 1: 0, 2: 2}  # not injective
        assert verify_bijection_certificate(H, H, bad) is False

    def test_vocab_mismatch_returns_false(self) -> None:
        H1 = SparseHypergraph(n_nodes=2, hyperedges=[frozenset({0, 1})])
        H2 = SparseHypergraph(
            n_nodes=2,
            hyperedges=[frozenset({0, 1})],
            n_vertex_labels=2,
        )
        sigma = {0: 0, 1: 1}
        assert verify_bijection_certificate(H1, H2, sigma) is False
