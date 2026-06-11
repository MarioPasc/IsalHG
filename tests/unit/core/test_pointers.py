"""Unit tests for :class:`isalhg.core.pointers.KPointerSet`."""

from __future__ import annotations

import pytest

from isalhg.core.cdll import CircularDoublyLinkedList
from isalhg.core.pointers import K_MAX, KPointerSet
from isalhg.errors import InvalidPointerError

pytestmark = pytest.mark.unit


def _three_node_cdll() -> CircularDoublyLinkedList:
    cdll = CircularDoublyLinkedList(capacity=5)
    s0 = cdll.insert_after(0, 0)
    s1 = cdll.insert_after(s0, 1)
    cdll.insert_after(s1, 2)
    return cdll


class TestConstruction:
    @pytest.mark.parametrize("k", list(range(1, K_MAX + 1)))
    def test_valid_k(self, k: int) -> None:
        cdll = _three_node_cdll()
        ptr = KPointerSet(cdll, k=k)
        assert ptr.k == k
        assert ptr.snapshot() == (0,) * k

    @pytest.mark.parametrize("k", [0, -1, K_MAX + 1, 100])
    def test_invalid_k_rejected(self, k: int) -> None:
        cdll = _three_node_cdll()
        with pytest.raises(InvalidPointerError):
            KPointerSet(cdll, k=k)

    def test_empty_cdll_rejected(self) -> None:
        cdll = CircularDoublyLinkedList(capacity=3)
        with pytest.raises(ValueError):
            KPointerSet(cdll, k=2)


class TestPointerMoves:
    def test_advance_pointer_1(self) -> None:
        cdll = _three_node_cdll()
        ptr = KPointerSet(cdll, k=3)
        ptr.advance(1)
        assert ptr.get(1) == cdll.next_node(0)
        assert ptr.get(2) == 0
        assert ptr.get(3) == 0

    def test_retreat_then_advance(self) -> None:
        cdll = _three_node_cdll()
        ptr = KPointerSet(cdll, k=2)
        ptr.retreat(2)
        assert ptr.get(2) == cdll.prev_node(0)
        ptr.advance(2)
        assert ptr.get(2) == 0

    def test_out_of_range_pointer_index(self) -> None:
        cdll = _three_node_cdll()
        ptr = KPointerSet(cdll, k=2)
        for bad in (0, -1, 3):
            with pytest.raises(InvalidPointerError):
                ptr.advance(bad)
            with pytest.raises(InvalidPointerError):
                ptr.get(bad)


class TestSnapshotRestore:
    def test_snapshot_restore_round_trip(self) -> None:
        cdll = _three_node_cdll()
        ptr = KPointerSet(cdll, k=3)
        ptr.advance(1)
        ptr.advance(2)
        ptr.advance(2)
        snap = ptr.snapshot()
        ptr.reset()
        assert ptr.snapshot() == (0, 0, 0)
        ptr.restore(snap)
        assert ptr.snapshot() == snap

    def test_restore_wrong_length(self) -> None:
        cdll = _three_node_cdll()
        ptr = KPointerSet(cdll, k=3)
        with pytest.raises(InvalidPointerError):
            ptr.restore((0, 0))
