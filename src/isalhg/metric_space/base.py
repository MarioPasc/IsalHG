"""Abstract base class for hypergraph distances.

``HypergraphDistance`` is the metric-space analogue of
:class:`isalhg.iso_backends.base.IsoBackend`: an ``IsoBackend`` yields an
isomorphism decision / fingerprint, a ``HypergraphDistance`` yields a
real-valued dissimilarity. Our method (``d_I`` = Levenshtein of the canonical
string), the HGED oracle, and every competing representation subclass this one
interface, so the Layer-1 correlation study is uniformly
``corr(D.matrix(corpus), ExactHGED().matrix(corpus))`` for each registered ``D``.

numpy is imported lazily inside :meth:`HypergraphDistance.matrix` (guarded,
raising :class:`RepresentationDependencyMissingError`) so that importing this
module -- and the whole ``metric_space`` package -- never requires numpy at
import time. The matrix return type is annotated under ``TYPE_CHECKING`` only.

Restriction: no external dependency at module import time.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.errors import RepresentationDependencyMissingError
from isalhg.types import DistanceName

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray


class HypergraphDistance(ABC):
    """Abstract real-valued dissimilarity between hypergraphs.

    Concrete subclasses implement :meth:`pairwise` and the :attr:`name`
    property. They may override :meth:`matrix` when a whole-corpus computation
    (a shared embedding, coupling, or fingerprint batch) is cheaper than
    ``O(N^2)`` independent :meth:`pairwise` calls, and :meth:`fingerprint`
    when a per-hypergraph summary can amortize :meth:`matrix`.
    """

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def name(self) -> DistanceName:
        """Short identifier used in registries, configs, and result records."""
        ...

    # ------------------------------------------------------------------
    # Core operation
    # ------------------------------------------------------------------

    @abstractmethod
    def pairwise(self, H1: SparseHypergraph, H2: SparseHypergraph) -> float:
        """Return the dissimilarity between ``H1`` and ``H2``.

        Parameters
        ----------
        H1, H2 : SparseHypergraph
            The two hypergraphs to compare.

        Returns
        -------
        float
            A non-negative dissimilarity; ``0`` iff the representation cannot
            tell the two hypergraphs apart (for an exact invariant, iff they
            are isomorphic).
        """
        ...

    # ------------------------------------------------------------------
    # Corpus operation
    # ------------------------------------------------------------------

    def matrix(self, corpus: Sequence[SparseHypergraph]) -> NDArray[np.float64]:
        """Return the dense symmetric dissimilarity matrix over ``corpus``.

        The default loops :meth:`pairwise` over the upper triangle and mirrors
        it, leaving a zero diagonal. Override when a representation computes a
        whole-corpus embedding / coupling more efficiently.

        Parameters
        ----------
        corpus : Sequence[SparseHypergraph]
            The hypergraphs to embed; row/column ``i`` corresponds to
            ``corpus[i]``.

        Returns
        -------
        numpy.ndarray
            Symmetric ``(len(corpus), len(corpus))`` ``float64`` matrix with a
            zero diagonal.

        Raises
        ------
        RepresentationDependencyMissingError
            If numpy is not installed.
        """
        try:
            import numpy as np
        except ImportError as exc:  # pragma: no cover - exercised only without numpy
            raise RepresentationDependencyMissingError(
                "numpy is required for HypergraphDistance.matrix(); install via `pip install numpy`"
            ) from exc

        size = len(corpus)
        matrix = np.zeros((size, size), dtype=np.float64)
        for i in range(size):
            for j in range(i + 1, size):
                value = float(self.pairwise(corpus[i], corpus[j]))
                matrix[i, j] = value
                matrix[j, i] = value
        return matrix

    # ------------------------------------------------------------------
    # Optional operation
    # ------------------------------------------------------------------

    def fingerprint(self, H: SparseHypergraph) -> Any | None:
        """Return a per-hypergraph summary that amortizes :meth:`matrix`, or ``None``.

        The default returns ``None`` (no amortization). Representations whose
        distance factors through a per-item object -- the canonical string for
        ``d_I``, a WL colour histogram, a spectral signature -- override this
        and a :meth:`matrix` that consumes the cached fingerprints.
        """
        return None

    # ------------------------------------------------------------------
    # Plumbing
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"
