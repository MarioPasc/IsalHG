"""K-pointer manager for the IsalHG virtual machine.

Generalises the two-pointer (primary/secondary) IsalGraph machine to
``k`` pointers ``p_1, ..., p_k``. Pointers are stored internally as a
length-``k`` list of CDLL slot indices; the alphabet uses 1-based naming
so the public ``get(i) / advance(i) / retreat(i)`` API takes ``i`` in
``[1, k]``.

Cap: ``k <= 10`` (decision B12).
"""

from __future__ import annotations

from isalhg.core.cdll import CircularDoublyLinkedList
from isalhg.errors import InvalidPointerError
from isalhg.types import PointerIndex

K_MAX: int = 10


class KPointerSet:
    """A vector of ``k`` pointers into a :class:`CircularDoublyLinkedList`.

    Parameters
    ----------
    cdll : CircularDoublyLinkedList
        The underlying CDLL. Must contain at least one slot at construction
        time so all pointers can be initialised to slot ``0``.
    k : int
        Number of pointers; constrained to ``1 <= k <= 10`` (decision B12).
    """

    __slots__ = ("_cdll", "_k", "_positions")

    def __init__(self, cdll: CircularDoublyLinkedList, k: int) -> None:
        if not 1 <= k <= K_MAX:
            raise InvalidPointerError(f"k must be in [1, {K_MAX}], got {k}")
        if len(cdll) == 0:
            raise ValueError("CDLL must contain at least one slot before pointer init")
        self._cdll: CircularDoublyLinkedList = cdll
        self._k: int = k
        self._positions: list[PointerIndex] = [cdll.head()] * k

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def k(self) -> int:
        return self._k

    @property
    def cdll(self) -> CircularDoublyLinkedList:
        return self._cdll

    # ------------------------------------------------------------------
    # 1-based API matching the alphabet
    # ------------------------------------------------------------------

    def _check(self, i: int) -> None:
        if not 1 <= i <= self._k:
            raise InvalidPointerError(f"pointer index i must be in [1, {self._k}], got {i}")

    def get(self, i: int) -> PointerIndex:
        """Return the CDLL slot index of pointer ``p_i``."""
        self._check(i)
        return self._positions[i - 1]

    def set(self, i: int, slot: PointerIndex) -> None:
        """Overwrite ``p_i`` with ``slot`` (used by H2S for direct assignment)."""
        self._check(i)
        self._positions[i - 1] = slot

    def advance(self, i: int) -> None:
        """Apply ``P_i``: ``p_i <- cdll.next_node(p_i)``."""
        self._check(i)
        self._positions[i - 1] = self._cdll.next_node(self._positions[i - 1])

    def retreat(self, i: int) -> None:
        """Apply ``N_i``: ``p_i <- cdll.prev_node(p_i)``."""
        self._check(i)
        self._positions[i - 1] = self._cdll.prev_node(self._positions[i - 1])

    def reset(self) -> None:
        """Reset all pointers to the CDLL head."""
        head = self._cdll.head()
        for j in range(self._k):
            self._positions[j] = head

    def snapshot(self) -> tuple[PointerIndex, ...]:
        """Return the current pointer vector as an immutable tuple."""
        return tuple(self._positions)

    def restore(self, snapshot: tuple[PointerIndex, ...]) -> None:
        """Restore from a :meth:`snapshot` (used for greedy backtracking)."""
        if len(snapshot) != self._k:
            raise InvalidPointerError(f"snapshot has {len(snapshot)} entries, expected {self._k}")
        self._positions[:] = list(snapshot)

    def __repr__(self) -> str:
        return f"KPointerSet(k={self._k}, positions={tuple(self._positions)})"
