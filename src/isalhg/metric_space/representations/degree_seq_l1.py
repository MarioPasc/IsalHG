"""``DegreeSequenceL1Distance`` — the naive structural floor baseline.

Computes the L1 distance between the sorted (descending) primal-degree
sequences of two hypergraphs, zero-padded to equal length.

**Definition.** For a hypergraph *H* with *n* vertices, let ``deg(H)`` be
the tuple of vertex degrees sorted in non-increasing order.  The distance is

    d_DS(H, H') = ||deg(H) - deg(H')||_1

where both sequences are first zero-padded to the same length
``max(|V(H)|, |V(H')|)``.  This is a proper metric: non-negativity and
symmetry are immediate; the triangle inequality is inherited from L1 on
``ℝ^{max(n,n')}``.

**Completeness.** The distance is explicitly *not* a complete invariant.
Non-isomorphic hypergraphs that share a degree multiset receive distance 0.
The canonical incompleteness witness is any pair where arity profiles differ
but vertex degrees agree — e.g. ``non_iso_pair_small`` (``tests/conftest.py``):
H1 (two 3-edges sharing a vertex pair) and H2 (three 2-edges forming a
path) both have degree sequence ``[2, 2, 1, 1]``, so ``d_DS = 0`` despite
non-isomorphism.

**Role.** This is the naive structural floor, added at T-M7c to anchor every
comparison surface (geometry table, A2/A3/A4, HIC exhibit).  The
interpretation contract — which outcome to expect and how to report it — is
pre-registered in ``docs/article/COMPETITORS.md`` §4 before any result is
seen.

**Fingerprint.** The per-hypergraph summary is the degree sequence itself
(a ``list[int]``).  :meth:`matrix` is overridden to compute one fingerprint
per corpus member and then fill the upper triangle, avoiding re-sorting per
pair.

**Dependencies.** Pure stdlib for :meth:`pairwise` and :meth:`fingerprint`.
Only :meth:`matrix` requires numpy (guarded, consistent with the base class).
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


def _degree_sequence(H: SparseHypergraph) -> list[int]:
    """Return the sorted-descending primal degree sequence of *H*.

    Parameters
    ----------
    H : SparseHypergraph
        The input hypergraph.

    Returns
    -------
    list[int]
        Degree of each vertex, sorted in non-increasing order.
        Length equals ``H.n_nodes``.
    """
    return sorted((H.degree(v) for v in range(H.n_nodes)), reverse=True)


def _l1_padded(seq1: list[int], seq2: list[int]) -> float:
    """L1 distance between two integer sequences, zero-padded to equal length.

    Parameters
    ----------
    seq1, seq2 : list[int]
        Sorted degree sequences (need not have the same length).

    Returns
    -------
    float
        ``sum(|a - b|)`` after zero-padding the shorter sequence.
    """
    n = max(len(seq1), len(seq2))
    total = 0
    for i in range(n):
        a = seq1[i] if i < len(seq1) else 0
        b = seq2[i] if i < len(seq2) else 0
        total += abs(a - b)
    return float(total)


class DegreeSequenceL1Distance(HypergraphDistance):
    """L1 distance between sorted primal-degree sequences.

    The fingerprint of *H* is its non-increasing degree sequence.  The
    pairwise distance zero-pads the two sequences to equal length and
    returns their L1 norm.

    This is a proper metric (non-negativity, symmetry, triangle inequality)
    but is **not** a complete invariant: non-isomorphic hypergraphs with the
    same degree multiset receive distance 0.  See the module docstring for the
    pinned incompleteness witness and the pre-registered interpretation
    contract in ``docs/article/COMPETITORS.md`` §4.
    """

    @property
    def name(self) -> DistanceName:
        return "degree_seq_l1"

    def fingerprint(self, H: SparseHypergraph) -> list[int]:
        """Return the non-increasing degree sequence of *H*.

        Parameters
        ----------
        H : SparseHypergraph
            The input hypergraph.

        Returns
        -------
        list[int]
            Vertex degrees in non-increasing order; length ``H.n_nodes``.
        """
        return _degree_sequence(H)

    def pairwise(self, H1: SparseHypergraph, H2: SparseHypergraph) -> float:
        """Return the L1 distance between degree sequences of *H1* and *H2*.

        Parameters
        ----------
        H1, H2 : SparseHypergraph
            The two hypergraphs to compare.

        Returns
        -------
        float
            ``||deg(H1) - deg(H2)||_1`` (zero-padded to equal length).
            Returns 0 for isomorphic pairs; may return 0 for non-isomorphic
            pairs with the same degree multiset (see module docstring).
        """
        return _l1_padded(_degree_sequence(H1), _degree_sequence(H2))

    def matrix(self, corpus: Sequence[SparseHypergraph]) -> NDArray[np.float64]:
        """Return the symmetric L1-degree-sequence distance matrix over *corpus*.

        Computes one fingerprint per corpus member, then fills the upper
        triangle.  This is cheaper than ``O(N^2)`` independent
        :meth:`pairwise` calls because each degree sequence is sorted once.

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
                "numpy is required for DegreeSequenceL1Distance.matrix(); "
                "install via `pip install numpy`"
            ) from exc

        size = len(corpus)
        if size == 0:
            return np.zeros((0, 0), dtype=np.float64)

        fingerprints = [_degree_sequence(H) for H in corpus]
        result = np.zeros((size, size), dtype=np.float64)
        for i in range(size):
            for j in range(i + 1, size):
                d = _l1_padded(fingerprints[i], fingerprints[j])
                result[i, j] = d
                result[j, i] = d
        return result


register_distance("degree_seq_l1", DegreeSequenceL1Distance)
