"""``SizeL1Distance`` — the two-integer size baseline.

Computes ``d_size(H, H') = |n - n'| + |m - m'|`` from the vertex and
hyperedge counts alone.  It carries **no structural information whatsoever**:
it is the L1 distance between the points ``(n, m)`` and ``(n', m')`` in
``ℝ²``, so non-negativity, symmetry, and the triangle inequality are
immediate, while identity of indiscernibles fails maximally (any two
same-size hypergraphs receive distance 0).

**Role.** The second naive baseline, mandated by the discharge of the
pre-registered contract in ``docs/article/COMPETITORS.md`` §4 (T-M4b): on the
former primary corpus this distance outranked five of seven representations
on A2 ARI and four of seven on A3 AUC, demonstrating that the corpus scored
size encoding rather than representation quality.  It is present in every
comparison surface with the same intervals and tests as every other row: on a
size-controlled corpus it sits at exactly 0 on every pair, pinning the
structural floor; any corpus where it scores above floor is measuring size.

**Fingerprint.** The pair ``(n_nodes, n_edges)``.

**Dependencies.** Pure stdlib for :meth:`pairwise` and :meth:`fingerprint`;
:meth:`matrix` requires numpy (guarded, consistent with the base class).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.errors import RepresentationDependencyMissingError
from isalhg.metric_space.base import HypergraphDistance
from isalhg.metric_space.registry import register_distance
from isalhg.types import DistanceName

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray


class SizeL1Distance(HypergraphDistance):
    """L1 distance between the ``(n_nodes, n_edges)`` pairs of two hypergraphs.

    A pseudometric that is blind to all structure: it separates hypergraphs
    only by how many vertices and hyperedges they have.  See the module
    docstring for its role as the size floor of every comparison surface.
    """

    @property
    def name(self) -> DistanceName:
        return "size_l1"

    def fingerprint(self, H: SparseHypergraph) -> tuple[int, int]:
        """Return the size pair of *H*.

        Parameters
        ----------
        H : SparseHypergraph
            The input hypergraph.

        Returns
        -------
        tuple[int, int]
            ``(n_nodes, n_edges)``.
        """
        return (H.n_nodes, H.n_edges)

    def pairwise(self, H1: SparseHypergraph, H2: SparseHypergraph) -> float:
        """Return ``|n1 - n2| + |m1 - m2|``.

        Parameters
        ----------
        H1, H2 : SparseHypergraph
            The two hypergraphs to compare.

        Returns
        -------
        float
            The L1 distance between the two size pairs; 0 for any two
            hypergraphs of equal size, isomorphic or not.
        """
        return float(abs(H1.n_nodes - H2.n_nodes) + abs(H1.n_edges - H2.n_edges))

    def matrix(self, corpus: Sequence[SparseHypergraph]) -> NDArray[np.float64]:
        """Return the symmetric size-distance matrix over *corpus*.

        Parameters
        ----------
        corpus : Sequence[SparseHypergraph]
            The hypergraphs to compare.

        Returns
        -------
        numpy.ndarray
            Symmetric ``(N, N)`` float64 matrix, zero diagonal.

        Raises
        ------
        RepresentationDependencyMissingError
            If numpy is not installed.
        """
        try:
            import numpy as np
        except ImportError as exc:
            raise RepresentationDependencyMissingError(
                "numpy is required for SizeL1Distance.matrix(); install via `pip install numpy`"
            ) from exc

        size = len(corpus)
        if size == 0:
            return np.zeros((0, 0), dtype=np.float64)

        pairs = [(H.n_nodes, H.n_edges) for H in corpus]
        result = np.zeros((size, size), dtype=np.float64)
        for i in range(size):
            for j in range(i + 1, size):
                d = float(abs(pairs[i][0] - pairs[j][0]) + abs(pairs[i][1] - pairs[j][1]))
                result[i, j] = d
                result[j, i] = d
        return result


register_distance("size_l1", SizeL1Distance)
