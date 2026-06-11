"""K-pointer manager for the IsalHG virtual machine.

Generalises IsalSR's two-pointer machine. Pointer ``p_i`` is a slot index into
the CDLL; advance / retreat semantics correspond to the ``P_i`` and ``N_i``
instructions.
"""

from __future__ import annotations

from isalhg.core.cdll import CircularDoublyLinkedList
from isalhg.types import PointerIndex


class KPointerSet:
    """Set of ``k`` pointers into a :class:`CircularDoublyLinkedList`."""

    def __init__(self, cdll: CircularDoublyLinkedList, k: int) -> None:
        self._cdll = cdll
        self._k = k
        self._positions: list[PointerIndex] = [0] * k

    @property
    def k(self) -> int:
        return self._k

    def get(self, i: int) -> PointerIndex:
        """Return slot index for ``p_i`` (1-based as in the alphabet, internally 0-based)."""
        raise NotImplementedError

    def advance(self, i: int) -> None:
        """Apply ``P_i``: ``p_i <- cdll.next(p_i)``."""
        raise NotImplementedError

    def retreat(self, i: int) -> None:
        """Apply ``N_i``: ``p_i <- cdll.prev(p_i)``."""
        raise NotImplementedError

    def reset(self) -> None:
        """Reset all pointers to slot 0."""
        raise NotImplementedError
