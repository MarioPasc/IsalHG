"""Distance-based anomaly scores over a precomputed dissimilarity matrix.

Two scores, both reading the same ``N x N`` matrix, both oriented so that a
**larger** value means *more anomalous*:

* :func:`knn_score` -- the mean distance to the ``k`` nearest other members
  (RQ4's primary score);
* :func:`lof_score` -- the local outlier factor of Breunig et al. (SIGMOD 2000),
  via ``sklearn.neighbors.LocalOutlierFactor(metric='precomputed')``, sign-
  flipped from scikit-learn's convention (where more negative is more
  anomalous).

:func:`auroc` scores either against the injected ground truth.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from isalhg.errors import MetricSpaceError

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray


def knn_score(D: NDArray[np.float64], k: int) -> NDArray[np.float64]:
    """Mean distance to the ``k`` nearest *other* members.

    Parameters
    ----------
    D : numpy.ndarray
        Symmetric ``(N, N)`` dissimilarity matrix with a zero diagonal.
    k : int
        Neighbourhood size, ``1 <= k <= N - 1``. The item itself is excluded,
        so its zero self-distance never enters the mean.

    Returns
    -------
    numpy.ndarray
        ``(N,)`` float score; larger means more anomalous.

    Raises
    ------
    isalhg.errors.MetricSpaceError
        If ``D`` is not square or ``k`` is out of range.
    """
    import numpy as np

    matrix = _as_square(D)
    size = matrix.shape[0]
    if not 1 <= k <= size - 1:
        raise MetricSpaceError(f"k must satisfy 1 <= k <= {size - 1}, got {k}")

    masked = matrix.copy()
    np.fill_diagonal(masked, np.inf)
    nearest = np.sort(masked, axis=1)[:, :k]
    return np.asarray(nearest.mean(axis=1), dtype=np.float64)


def lof_score(D: NDArray[np.float64], k: int) -> NDArray[np.float64]:
    """Local outlier factor from a precomputed matrix, higher = more anomalous.

    Parameters
    ----------
    D : numpy.ndarray
        Symmetric ``(N, N)`` dissimilarity matrix with a zero diagonal.
    k : int
        ``n_neighbors``, ``1 <= k <= N - 1``.

    Returns
    -------
    numpy.ndarray
        ``(N,)`` float score, ``-negative_outlier_factor_``: about 1 for an
        inlier, larger for an outlier.

    Raises
    ------
    isalhg.errors.MetricSpaceError
        If ``D`` is not square or ``k`` is out of range.
    """
    import numpy as np

    matrix = _as_square(D)
    size = matrix.shape[0]
    if not 1 <= k <= size - 1:
        raise MetricSpaceError(f"k must satisfy 1 <= k <= {size - 1}, got {k}")

    from sklearn.neighbors import LocalOutlierFactor  # type: ignore[import-untyped]

    estimator = LocalOutlierFactor(n_neighbors=k, metric="precomputed")
    estimator.fit(matrix)
    return np.asarray(-estimator.negative_outlier_factor_, dtype=np.float64)


def auroc(scores: NDArray[np.float64], is_anomaly: NDArray[np.bool_]) -> float:
    """Area under the ROC curve with the anomaly as the positive class.

    Parameters
    ----------
    scores : numpy.ndarray
        ``(N,)`` anomaly scores, larger = more anomalous.
    is_anomaly : numpy.ndarray
        ``(N,)`` boolean ground truth.

    Returns
    -------
    float
        AUROC in ``[0, 1]``; ``0.5`` is chance.

    Raises
    ------
    isalhg.errors.MetricSpaceError
        If the lengths differ, or if the ground truth has only one class (AUROC
        is undefined there).
    """
    import numpy as np

    score_array = np.asarray(scores, dtype=np.float64).ravel()
    truth = np.asarray(is_anomaly).astype(bool).ravel()
    if score_array.shape != truth.shape:
        raise MetricSpaceError(f"scores has shape {score_array.shape}, is_anomaly {truth.shape}")
    if truth.all() or not truth.any():
        raise MetricSpaceError("AUROC needs both classes present in is_anomaly")

    from sklearn.metrics import roc_auc_score  # type: ignore[import-untyped]

    return float(roc_auc_score(truth.astype(int), score_array))


def _as_square(D: NDArray[np.float64]) -> NDArray[np.float64]:
    import numpy as np

    matrix = np.asarray(D, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise MetricSpaceError(f"expected a square distance matrix, got shape {matrix.shape}")
    return matrix


__all__ = ["auroc", "knn_score", "lof_score"]
