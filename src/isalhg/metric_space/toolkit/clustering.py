"""Clustering over a precomputed dissimilarity matrix.

Thin wrappers over maintained code: ``kmedoids.fasterpam`` (Schubert & Lenssen,
JOSS 7(75), 2022) for PAM, ``scipy.cluster.hierarchy`` for the average-linkage
hierarchy and its cophenetic correlation, and ``scikit-learn`` for ARI / NMI.

PAM rather than a centroid method is what the geometry licenses: a medoid needs
only a dissimilarity, whereas a centroid needs an inner-product space, which a
matrix with non-Euclidean mass ``nu > 0`` does not provide.

The only hand-written algorithm here is :func:`_pam_numpy`, a BUILD + SWAP PAM
used solely when ``kmedoids`` is not installed. It is a fallback for
importability, not the measurement path.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from isalhg.errors import MetricSpaceError

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray

logger = logging.getLogger(__name__)


def pam(D: NDArray[np.float64], k: int, seed: int) -> NDArray[np.int64]:
    """Partition ``D`` into ``k`` clusters with FasterPAM.

    Parameters
    ----------
    D : numpy.ndarray
        Symmetric ``(N, N)`` dissimilarity matrix with a zero diagonal.
    k : int
        Number of clusters, ``1 <= k <= N``.
    seed : int
        Random state of the initialization; the result is deterministic in it.

    Returns
    -------
    numpy.ndarray
        ``(N,)`` integer cluster labels in ``[0, k)``.

    Raises
    ------
    isalhg.errors.MetricSpaceError
        If ``D`` is not square or ``k`` is out of range.
    """
    import numpy as np

    matrix = _as_square(D)
    size = matrix.shape[0]
    if not 1 <= k <= size:
        raise MetricSpaceError(f"k must satisfy 1 <= k <= {size}, got {k}")

    try:
        import kmedoids  # type: ignore[import-untyped]
    except ImportError:
        logger.warning("kmedoids not installed; using the pure-numpy PAM fallback")
        return _pam_numpy(matrix, k, seed)

    result = kmedoids.fasterpam(matrix, k, random_state=seed)
    return np.asarray(result.labels, dtype=np.int64)


def average_linkage(D: NDArray[np.float64]) -> tuple[NDArray[np.float64], float]:
    """Average-linkage hierarchy of ``D`` and its cophenetic correlation.

    Parameters
    ----------
    D : numpy.ndarray
        Symmetric ``(N, N)`` dissimilarity matrix with a zero diagonal,
        ``N >= 2``.

    Returns
    -------
    Z : numpy.ndarray
        The ``(N - 1, 4)`` scipy linkage matrix.
    cophenetic : float
        Pearson correlation between the cophenetic distances of ``Z`` and the
        condensed ``D``; in ``[-1, 1]``, higher means the hierarchy preserves
        the metric better.

    Raises
    ------
    isalhg.errors.MetricSpaceError
        If ``D`` is not square or has fewer than 2 rows.
    """
    import numpy as np

    matrix = _as_square(D)
    if matrix.shape[0] < 2:
        raise MetricSpaceError("average linkage needs at least two items")

    from scipy.cluster.hierarchy import cophenet, linkage
    from scipy.spatial.distance import squareform

    condensed = squareform(_symmetrize(matrix), checks=False)
    linkage_matrix = linkage(condensed, method="average")
    correlation, _ = cophenet(linkage_matrix, condensed)
    return np.asarray(linkage_matrix, dtype=np.float64), float(correlation)


def cut(Z: NDArray[np.float64], k: int) -> NDArray[np.int64]:
    """Cut a linkage matrix into ``k`` flat clusters.

    Parameters
    ----------
    Z : numpy.ndarray
        A scipy linkage matrix.
    k : int
        Requested number of clusters.

    Returns
    -------
    numpy.ndarray
        ``(N,)`` integer labels, **0-based** (scipy's ``fcluster`` is 1-based;
        the shift keeps the label convention identical to :func:`pam`).
    """
    import numpy as np
    from scipy.cluster.hierarchy import fcluster

    labels = fcluster(np.asarray(Z, dtype=np.float64), t=k, criterion="maxclust")
    return np.asarray(labels, dtype=np.int64) - 1


def ari(a: Sequence[Any], b: Sequence[Any]) -> float:
    """Adjusted Rand index between two labellings (``sklearn``)."""
    from sklearn.metrics import adjusted_rand_score  # type: ignore[import-untyped]

    return float(adjusted_rand_score(list(a), list(b)))


def nmi(a: Sequence[Any], b: Sequence[Any]) -> float:
    """Normalized mutual information between two labellings (``sklearn``)."""
    from sklearn.metrics import normalized_mutual_info_score

    return float(normalized_mutual_info_score(list(a), list(b)))


def per_class_table(labels_true: Sequence[str], labels_pred: Sequence[int]) -> list[dict[str, Any]]:
    """Per-class recall and precision against the best-matching cluster.

    Classes are matched to clusters by a Hungarian assignment maximising the
    total contingency count (``scipy.optimize.linear_sum_assignment``), so each
    class is credited to at most one cluster and each cluster to at most one
    class. A class left unmatched (more classes than clusters) reports zero
    recall and zero precision.

    Parameters
    ----------
    labels_true : Sequence[str]
        Ground-truth class of each item.
    labels_pred : Sequence[int]
        Cluster index of each item.

    Returns
    -------
    list[dict]
        One row per class, sorted by class name, with keys ``class``,
        ``support``, ``recall``, ``precision`` and ``cluster`` (the matched
        cluster index, or ``None``).

    Raises
    ------
    isalhg.errors.MetricSpaceError
        If the two labellings differ in length.
    """
    import numpy as np

    if len(labels_true) != len(labels_pred):
        raise MetricSpaceError(
            f"labels_true has {len(labels_true)} entries, labels_pred {len(labels_pred)}"
        )
    if not labels_true:
        return []

    from scipy.optimize import linear_sum_assignment

    classes = sorted({str(label) for label in labels_true})
    clusters = sorted({int(label) for label in labels_pred})
    class_index = {name: i for i, name in enumerate(classes)}
    cluster_index = {value: j for j, value in enumerate(clusters)}

    contingency = np.zeros((len(classes), len(clusters)), dtype=np.int64)
    for true_label, pred_label in zip(labels_true, labels_pred, strict=True):
        contingency[class_index[str(true_label)], cluster_index[int(pred_label)]] += 1

    rows_idx, cols_idx = linear_sum_assignment(-contingency)
    matched = dict(zip(rows_idx.tolist(), cols_idx.tolist(), strict=True))

    support = contingency.sum(axis=1)
    cluster_size = contingency.sum(axis=0)

    table: list[dict[str, Any]] = []
    for i, name in enumerate(classes):
        j = matched.get(i)
        if j is None:
            table.append(
                {
                    "class": name,
                    "support": int(support[i]),
                    "recall": 0.0,
                    "precision": 0.0,
                    "cluster": None,
                }
            )
            continue
        hits = int(contingency[i, j])
        table.append(
            {
                "class": name,
                "support": int(support[i]),
                "recall": hits / int(support[i]) if support[i] else 0.0,
                "precision": hits / int(cluster_size[j]) if cluster_size[j] else 0.0,
                "cluster": clusters[j],
            }
        )
    return table


# ---------------------------------------------------------------------------
# Fallback PAM
# ---------------------------------------------------------------------------


def _pam_numpy(D: NDArray[np.float64], k: int, seed: int) -> NDArray[np.int64]:
    """BUILD + SWAP PAM (Kaufman & Rousseeuw 1990) in pure numpy.

    Used only when ``kmedoids`` is unavailable. The BUILD phase is greedy on
    total cost; the SWAP phase applies the first improving swap and repeats
    until no swap improves the cost or ``100`` iterations elapse. Deterministic
    given ``seed`` (which only breaks the initial ties).
    """
    import numpy as np

    size = D.shape[0]
    rng = np.random.default_rng(seed)

    medoids: list[int] = [int(np.argmin(D.sum(axis=1)))]
    while len(medoids) < k:
        nearest = D[:, medoids].min(axis=1)
        gains = np.array(
            [
                -np.inf if c in medoids else float(np.minimum(nearest, D[:, c]).sum())
                for c in range(size)
            ]
        )
        gains[np.isneginf(gains)] = np.inf
        best = int(np.argmin(gains + rng.random(size) * 1e-12))
        medoids.append(best)

    def cost(current: list[int]) -> float:
        return float(D[:, current].min(axis=1).sum())

    best_cost = cost(medoids)
    for _ in range(100):
        improved = False
        for slot in range(k):
            for candidate in range(size):
                if candidate in medoids:
                    continue
                trial = list(medoids)
                trial[slot] = candidate
                trial_cost = cost(trial)
                if trial_cost < best_cost - 1e-12:
                    medoids, best_cost, improved = trial, trial_cost, True
                    break
            if improved:
                break
        if not improved:
            break

    return np.asarray(np.argmin(D[:, medoids], axis=1), dtype=np.int64)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _symmetrize(D: NDArray[np.float64]) -> NDArray[np.float64]:
    """Return an exactly symmetric copy with a zero diagonal.

    ``scipy.spatial.distance.squareform`` reads the upper triangle only, but a
    matrix assembled in float32 and cast up can be off by an ULP; forcing
    symmetry here keeps the linkage input well defined.
    """
    import numpy as np

    symmetric = (D + D.T) / 2.0
    np.fill_diagonal(symmetric, 0.0)
    return symmetric


def _as_square(D: NDArray[np.float64]) -> NDArray[np.float64]:
    import numpy as np

    matrix = np.asarray(D, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise MetricSpaceError(f"expected a square distance matrix, got shape {matrix.shape}")
    return matrix


__all__ = ["ari", "average_linkage", "cut", "nmi", "pam", "per_class_table"]
