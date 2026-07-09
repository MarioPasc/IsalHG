"""Association measures between two distance vectors.

All functions operate on 1-D ``numpy`` arrays of equal length. The typical
caller extracts the upper triangle of two pairwise distance matrices via
:func:`triu_vector`, then passes both vectors here.

Scipy and numpy are imported inside each function body so that importing
this module at the package level never requires them.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray


def triu_vector(D: NDArray[np.float64]) -> NDArray[np.float64]:
    """Return the strict upper-triangle of a square matrix as a flat vector.

    Parameters
    ----------
    D : numpy.ndarray
        Symmetric ``(n, n)`` distance matrix.

    Returns
    -------
    numpy.ndarray
        1-D array of length ``n*(n-1)//2`` containing ``D[i, j]`` for
        all ``i < j``.
    """
    import numpy as np

    D = np.asarray(D, dtype=np.float64)
    n = D.shape[0]
    idx = np.triu_indices(n, k=1)
    return D[idx]


def spearman_r(
    x: NDArray[np.float64],
    y: NDArray[np.float64],
) -> tuple[float, float]:
    """Spearman rank correlation between two distance vectors.

    Parameters
    ----------
    x, y : numpy.ndarray
        1-D arrays of equal length.

    Returns
    -------
    tuple[float, float]
        ``(rho, pvalue)`` — Spearman ρ in ``[-1, 1]`` and the two-sided
        p-value under the null hypothesis of no correlation.
    """
    from scipy.stats import spearmanr

    result = spearmanr(x, y)
    return float(result.statistic), float(result.pvalue)


def pearson_r(
    x: NDArray[np.float64],
    y: NDArray[np.float64],
) -> tuple[float, float]:
    """Pearson product-moment correlation between two distance vectors.

    Parameters
    ----------
    x, y : numpy.ndarray
        1-D arrays of equal length.

    Returns
    -------
    tuple[float, float]
        ``(r, pvalue)`` — Pearson r in ``[-1, 1]`` and the two-sided p-value.
    """
    from scipy.stats import pearsonr

    result = pearsonr(x, y)
    return float(result.statistic), float(result.pvalue)


def mutual_information_binned(
    x: NDArray[np.float64],
    y: NDArray[np.float64],
    n_bins: int = 20,
) -> float:
    """Mutual information I(X; Y) estimated via equal-width 2-D histogram.

    Uses the plug-in estimator on the empirical joint distribution:
    ``I = sum_{ij} p_{ij} * log2(p_{ij} / (p_i * p_j))`` (bits), with
    zero-count bins skipped. This mirrors the fixed-width-code framing in
    ``PROPOSAL.md`` §3 and avoids the k-NN Kraskov estimator's dependence
    on nearest-neighbour distance computations.

    Parameters
    ----------
    x, y : numpy.ndarray
        1-D arrays of equal length containing the two distance vectors.
    n_bins : int, optional
        Number of equal-width bins per axis.  Default 20 is appropriate for
        ``N ~ 100–1000`` pairwise entries.

    Returns
    -------
    float
        Non-negative mutual information in bits.
    """
    import numpy as np

    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)

    joint, _, _ = np.histogram2d(x, y, bins=n_bins)
    joint = joint / joint.sum()

    px = joint.sum(axis=1, keepdims=True)
    py = joint.sum(axis=0, keepdims=True)

    # Avoid log(0): only sum over cells with positive probability.
    mask = joint > 0
    mi = float(np.sum(joint[mask] * np.log2(joint[mask] / (px * py)[mask])))
    return max(mi, 0.0)  # numerical clamp — never negative by definition
