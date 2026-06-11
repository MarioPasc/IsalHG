"""Circular doubly-linked list of node IDs.

Port template: ``IsalGraph/src/isalgraph/core/cdll.py``. Array-backed to keep
pointer arithmetic O(1).
"""

from __future__ import annotations

from isalhg.types import NodeId, PointerIndex


class CircularDoublyLinkedList:
    """Array-backed circular doubly-linked list of :data:`NodeId` values."""

    def __init__(self, initial: NodeId = 0) -> None:
        self._values: list[NodeId] = [initial]
        self._next: list[int] = [0]
        self._prev: list[int] = [0]

    def __len__(self) -> int:
        raise NotImplementedError

    def get_value(self, p: PointerIndex) -> NodeId:
        """Resolve a CDLL slot index to its node ID."""
        raise NotImplementedError

    def insert_after(self, p: PointerIndex, value: NodeId) -> PointerIndex:
        """Insert ``value`` immediately after slot ``p`` and return its slot index."""
        raise NotImplementedError

    def next(self, p: PointerIndex) -> PointerIndex:
        """Return the slot index following ``p`` (wraps to head)."""
        raise NotImplementedError

    def prev(self, p: PointerIndex) -> PointerIndex:
        """Return the slot index preceding ``p`` (wraps to tail)."""
        raise NotImplementedError
