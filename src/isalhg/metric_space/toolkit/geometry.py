"""The two geometric licences the applications cite.

* :func:`non_euclidean_mass` -- Schoenberg's criterion made quantitative. A
  dissimilarity is Euclidean iff the double-centred Gram matrix
  ``B = -1/2 J D^2 J`` is positive semi-definite; ``nu = sum_{lam<0}|lam| /
  sum|lam|`` measures how far from that it sits. ``nu > 0`` licenses PAM over
  centroid methods and metric MDS over classical MDS.
* :func:`hubness` -- the skewness of the ``k``-occurrence distribution
  (Radovanovic et al., JMLR 11, 2010). A high value predicts degraded kNN, so
  it is reported as the precondition of every kNN table.

Both delegate to the already-tested primitives in
:mod:`isalhg.metric_space.metrics`; this module only fixes the calling
convention the runners share.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from isalhg.errors import MetricSpaceError

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray


def non_euclidean_mass(
    D: NDArray[np.float64],
) -> tuple[float, NDArray[np.float64]]:
    """Return the non-Euclidean mass ``nu`` of ``D`` and the Gram spectrum.

    Parameters
    ----------
    D : numpy.ndarray
        Symmetric ``(N, N)`` dissimilarity matrix with a zero diagonal.

    Returns
    -------
    nu : float
        ``sum_{lam < 0} |lam| / sum |lam|`` over the eigenvalues of the
        double-centred Gram matrix; ``0`` exactly for a Euclidean matrix.
    eigenvalues : numpy.ndarray
        The ``(N,)`` spectrum, sorted descending.

    Raises
    ------
    isalhg.errors.MetricSpaceError
        If ``D`` is not a square 2-D array.
    """
    import numpy as np

    matrix = np.asarray(D, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise MetricSpaceError(f"expected a square distance matrix, got shape {matrix.shape}")
    if matrix.shape[0] == 0:
        return 0.0, np.zeros(0, dtype=np.float64)

    from isalhg.metric_space.metrics.embedding import classical_mds, neg_eigenvalue_mass

    symmetric = (matrix + matrix.T) / 2.0
    np.fill_diagonal(symmetric, 0.0)
    eigenvalues, _ = classical_mds(symmetric)
    return float(neg_eigenvalue_mass(eigenvalues)), np.asarray(eigenvalues, dtype=np.float64)


def hubness(D: NDArray[np.float64], k: int = 10) -> tuple[float, int]:
    """Return the ``k``-occurrence skewness of ``D`` and its maximum count.

    Parameters
    ----------
    D : numpy.ndarray
        Symmetric ``(N, N)`` dissimilarity matrix with a zero diagonal.
    k : int, optional
        Neighbourhood size, ``1 <= k <= N - 1``. Default 10.

    Returns
    -------
    skewness : float
        Sample skewness of ``N_k``; above about 1.2 predicts degraded kNN.
    max_occurrence : int
        ``max_i N_k(i)``, the size of the largest hub.

    Raises
    ------
    isalhg.errors.MetricSpaceError
        If ``D`` is not square or ``k`` is out of range.
    """
    import numpy as np

    matrix = np.asarray(D, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise MetricSpaceError(f"expected a square distance matrix, got shape {matrix.shape}")
    size = matrix.shape[0]
    if not 1 <= k <= size - 1:
        raise MetricSpaceError(f"k must satisfy 1 <= k <= {size - 1}, got {k}")

    from isalhg.metric_space.metrics.geometry import hubness_skewness, k_occurrence_counts

    counts = k_occurrence_counts(matrix, k=k)
    return float(hubness_skewness(matrix, k=k)), int(counts.max())


__all__ = ["hubness", "non_euclidean_mass"]
