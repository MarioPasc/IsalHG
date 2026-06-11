"""Array-backed Circular Doubly-Linked List of hypergraph node IDs.

Port template: ``IsalGraph/src/isalgraph/core/cdll.py``. The structure is
k-independent; arity generalisation lives entirely in :mod:`isalhg.core.pointers`
and :mod:`isalhg.core.string_to_hypergraph`.

The CDLL stores **hypergraph node IDs** as payloads, addressed by **slot
indices**. Slot indices are what the VM pointers ``p_1, ..., p_k`` carry.
Translating a pointer to a hypergraph node requires :meth:`get_value`; this
distinction is invariant 1 of the project (see ``CLAUDE.md``).
"""

from __future__ import annotations

from isalhg.errors import CapacityError
from isalhg.types import NodeId, PointerIndex


class CircularDoublyLinkedList:
    """Array-backed circular doubly-linked list with integer node-ID payloads.

    Parameters
    ----------
    capacity : int
        Maximum number of active nodes. Pre-allocates parallel ``_next``,
        ``_prev``, ``_data`` arrays of this length plus a free-stack.

    Notes
    -----
    The free-list is a stack initialised to ``range(capacity-1, -1, -1)`` so
    the first allocation yields slot ``0``. This determinism is relied upon
    by :class:`StringToHypergraph` and :class:`HypergraphToString`, which both
    assume the seed node lives at slot ``0``.
    """

    __slots__ = ("_next", "_prev", "_data", "_free", "_size", "_capacity")

    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError(f"capacity must be positive, got {capacity}")
        self._capacity: int = capacity
        self._next: list[int] = [-1] * capacity
        self._prev: list[int] = [-1] * capacity
        self._data: list[int] = [0] * capacity
        self._free: list[int] = list(range(capacity - 1, -1, -1))
        self._size: int = 0

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    def size(self) -> int:
        """Return the number of active slots."""
        return self._size

    def capacity(self) -> int:
        """Return the pre-allocated capacity."""
        return self._capacity

    def get_value(self, p: PointerIndex) -> NodeId:
        """Return the node-ID payload stored at slot ``p``."""
        return self._data[p]

    def set_value(self, p: PointerIndex, value: NodeId) -> None:
        """Overwrite the payload stored at slot ``p``."""
        self._data[p] = value

    def next_node(self, p: PointerIndex) -> PointerIndex:
        """Return the successor slot of ``p`` (wraps to head)."""
        return self._next[p]

    def prev_node(self, p: PointerIndex) -> PointerIndex:
        """Return the predecessor slot of ``p`` (wraps to tail)."""
        return self._prev[p]

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def insert_after(self, p: PointerIndex, value: NodeId) -> PointerIndex:
        """Insert a new slot with payload ``value`` after slot ``p``.

        When the list is empty the ``p`` argument is ignored and the new
        slot becomes the sole element pointing to itself.

        Returns
        -------
        PointerIndex
            The slot index assigned to the new element.

        Raises
        ------
        CapacityError
            When the free-list is exhausted.
        """
        new_slot: int = self._allocate_slot()
        self._data[new_slot] = value

        if self._size == 0:
            self._next[new_slot] = new_slot
            self._prev[new_slot] = new_slot
        else:
            next_of_p: int = self._next[p]
            self._next[p] = new_slot
            self._prev[new_slot] = p
            self._next[new_slot] = next_of_p
            self._prev[next_of_p] = new_slot

        self._size += 1
        return new_slot

    def remove(self, p: PointerIndex) -> None:
        """Remove slot ``p`` and return its index to the free-list."""
        if self._size == 0:
            return
        if self._size == 1:
            self._free_slot(p)
            self._size = 0
            return
        prev_of_p: int = self._prev[p]
        next_of_p: int = self._next[p]
        self._next[prev_of_p] = next_of_p
        self._prev[next_of_p] = prev_of_p
        self._free_slot(p)
        self._size -= 1

    # ------------------------------------------------------------------
    # Iteration helpers
    # ------------------------------------------------------------------

    def head(self) -> PointerIndex:
        """Return slot ``0`` (the seed slot, always head after the first insert)."""
        if self._size == 0:
            raise IndexError("CDLL is empty")
        return 0

    def iter_slots(self, start: PointerIndex | None = None) -> list[PointerIndex]:
        """Return slot indices in forward circular order, starting at ``start``."""
        if self._size == 0:
            return []
        s = self.head() if start is None else start
        out: list[PointerIndex] = [s]
        cur = self._next[s]
        while cur != s:
            out.append(cur)
            cur = self._next[cur]
        return out

    def values(self, start: PointerIndex | None = None) -> list[NodeId]:
        """Return node-ID payloads in forward circular order."""
        return [self._data[s] for s in self.iter_slots(start)]

    # ------------------------------------------------------------------
    # Cloning
    # ------------------------------------------------------------------

    def clone(self) -> CircularDoublyLinkedList:
        """Return a deep copy of this CDLL (independent arrays + free-list)."""
        new = CircularDoublyLinkedList(capacity=self._capacity)
        new._next[:] = self._next
        new._prev[:] = self._prev
        new._data[:] = self._data
        new._free[:] = self._free
        new._size = self._size
        return new

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _allocate_slot(self) -> int:
        if not self._free:
            raise CapacityError("CircularDoublyLinkedList is full")
        return self._free.pop()

    def _free_slot(self, index: int) -> None:
        self._free.append(index)

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return self._size

    def __repr__(self) -> str:
        return f"{type(self).__name__}(capacity={self._capacity}, size={self._size})"
