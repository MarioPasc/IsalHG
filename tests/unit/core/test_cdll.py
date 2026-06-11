"""Unit tests for :class:`isalhg.core.cdll.CircularDoublyLinkedList`."""

from __future__ import annotations

import pytest

from isalhg.core.cdll import CircularDoublyLinkedList
from isalhg.errors import CapacityError

pytestmark = pytest.mark.unit


class TestConstruction:
    def test_zero_capacity_rejected(self) -> None:
        with pytest.raises(ValueError):
            CircularDoublyLinkedList(capacity=0)

    def test_negative_capacity_rejected(self) -> None:
        with pytest.raises(ValueError):
            CircularDoublyLinkedList(capacity=-1)

    def test_empty_initially(self) -> None:
        cdll = CircularDoublyLinkedList(capacity=5)
        assert cdll.size() == 0
        assert cdll.capacity() == 5
        assert len(cdll) == 0


class TestInsertAfter:
    def test_first_insert_self_links(self) -> None:
        cdll = CircularDoublyLinkedList(capacity=3)
        slot = cdll.insert_after(0, 42)
        assert slot == 0
        assert cdll.next_node(slot) == slot
        assert cdll.prev_node(slot) == slot
        assert cdll.get_value(slot) == 42
        assert len(cdll) == 1

    def test_second_insert_links_back(self) -> None:
        cdll = CircularDoublyLinkedList(capacity=3)
        s0 = cdll.insert_after(0, 10)
        s1 = cdll.insert_after(s0, 20)
        assert cdll.next_node(s0) == s1
        assert cdll.prev_node(s0) == s1
        assert cdll.next_node(s1) == s0
        assert cdll.prev_node(s1) == s0
        assert cdll.get_value(s1) == 20

    def test_three_node_insertion_ordering(self) -> None:
        cdll = CircularDoublyLinkedList(capacity=5)
        s0 = cdll.insert_after(0, 0)
        s1 = cdll.insert_after(s0, 1)
        s2 = cdll.insert_after(s0, 2)
        # Inserted after s0 in order 1, then 2: CDLL = s0, s2, s1.
        assert cdll.next_node(s0) == s2
        assert cdll.next_node(s2) == s1
        assert cdll.next_node(s1) == s0

    def test_capacity_exhausted_raises(self) -> None:
        cdll = CircularDoublyLinkedList(capacity=2)
        s0 = cdll.insert_after(0, 0)
        s1 = cdll.insert_after(s0, 1)
        with pytest.raises(CapacityError):
            cdll.insert_after(s1, 2)


class TestRemove:
    def test_remove_singleton(self) -> None:
        cdll = CircularDoublyLinkedList(capacity=3)
        s0 = cdll.insert_after(0, 42)
        cdll.remove(s0)
        assert len(cdll) == 0
        s_new = cdll.insert_after(0, 99)
        assert s_new == s0

    def test_remove_middle(self) -> None:
        cdll = CircularDoublyLinkedList(capacity=4)
        s0 = cdll.insert_after(0, 0)
        s1 = cdll.insert_after(s0, 1)
        s2 = cdll.insert_after(s1, 2)
        cdll.remove(s1)
        assert cdll.next_node(s0) == s2
        assert cdll.prev_node(s2) == s0
        assert len(cdll) == 2


class TestIteration:
    def test_iter_slots(self) -> None:
        cdll = CircularDoublyLinkedList(capacity=4)
        s0 = cdll.insert_after(0, 0)
        s1 = cdll.insert_after(s0, 1)
        s2 = cdll.insert_after(s1, 2)
        assert cdll.iter_slots() == [s0, s1, s2]
        assert cdll.values() == [0, 1, 2]

    def test_empty_iter(self) -> None:
        cdll = CircularDoublyLinkedList(capacity=2)
        assert cdll.iter_slots() == []
        assert cdll.values() == []
