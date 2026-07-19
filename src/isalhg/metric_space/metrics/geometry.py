"""Concentration and hubness diagnostics for a pairwise dissimilarity space.

Stateless primitives consumed by the per-corpus geometry table (T-M5b) and
the kNN precondition report (A3, ``empirical/applications.md``).  numpy and
scipy are imported lazily inside each function body so this module is
importable without optional dependencies.

All functions operate on upper-triangle pairs of a symmetric ``(n, n)``
distance matrix, excluding the zero diagonal.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray


def concentration_stats(
    D: NDArray[np.float64],
) -> dict[str, float]:
    """Concentration diagnostics from a pairwise distance matrix.

    Summarises the upper-triangle pairwise distances with the metrics used
    to characterise the spread and concentration of the embedding
    (``geometry.md`` §5).

    Parameters
    ----------
    D : numpy.ndarray
        Symmetric ``(n, n)`` non-negative distance matrix with zero diagonal.

    Returns
    -------
    dict
        Keys:

        - ``"diameter"``: maximum pairwise distance.
        - ``"median"``: median pairwise distance.
        - ``"q25"`` / ``"q75"``: 25th and 75th percentiles.
        - ``"iqr"``: inter-quartile range (``q75 - q25``).
        - ``"diameter_to_median"``: diameter / median; large values suggest
          the space is not concentrated.
    """
    import numpy as np

    D = np.asarray(D, dtype=np.float64)
    n = D.shape[0]
    idx = np.triu_indices(n, k=1)
    pairs = D[idx]

    diameter = float(np.max(pairs))
    median = float(np.median(pairs))
    q25 = float(np.percentile(pairs, 25))
    q75 = float(np.percentile(pairs, 75))
    iqr = q75 - q25
    diameter_to_median = diameter / median if median > 0.0 else 0.0

    return {
        "diameter": diameter,
        "median": median,
        "q25": q25,
        "q75": q75,
        "iqr": iqr,
        "diameter_to_median": diameter_to_median,
    }


def length_difference_floor(
    lengths: Sequence[int],
) -> NDArray[np.float64]:
    """Lower-bound matrix from string lengths.

    For any Levenshtein-type distance, ``d(s, t) ≥ ||s| - |t||`` by the
    triangle inequality.  This matrix encodes that floor for a corpus.

    Parameters
    ----------
    lengths : sequence of int
        String lengths ``[|w*_c(H_0)|, |w*_c(H_1)|, …]`` for the corpus.

    Returns
    -------
    numpy.ndarray
        Symmetric ``(n, n)`` matrix where entry ``[i, j]`` equals
        ``|lengths[i] - lengths[j]|``.  Zero diagonal.
    """
    import numpy as np

    L = np.asarray(lengths, dtype=np.float64)
    return np.abs(L[:, None] - L[None, :])


def k_occurrence_counts(
    D: NDArray[np.float64],
    k: int,
) -> NDArray[np.int64]:
    """k-occurrence counts (N_k) for each point.

    For each point ``x``, ``N_k(x)`` counts how many other points include
    ``x`` among their ``k`` nearest neighbours.  High skewness of this
    distribution signals the presence of *hubs* — points that appear
    disproportionately often as nearest neighbours of others
    (Radovanović et al., JMLR 11, 2010).

    Ties in distance are broken by index order (``numpy.argsort`` stable
    sort), matching the convention used in experiments.

    Parameters
    ----------
    D : numpy.ndarray
        Symmetric ``(n, n)`` non-negative distance matrix with zero diagonal.
    k : int
        Number of nearest neighbours to consider (``1 ≤ k < n``).

    Returns
    -------
    numpy.ndarray
        Integer array of shape ``(n,)`` where entry ``i`` is ``N_k(i)``.
        The sum of all entries equals ``n * k``.
    """
    import numpy as np

    D = np.asarray(D, dtype=np.float64)
    n = D.shape[0]
    counts = np.zeros(n, dtype=np.int64)

    for i in range(n):
        row = D[i].copy()
        row[i] = np.inf  # exclude self from NN search
        nn_indices = np.argsort(row, kind="stable")[:k]
        for j in nn_indices:
            counts[j] += 1

    return counts


def hubness_skewness(
    D: NDArray[np.float64],
    k: int,
) -> float:
    """Skewness of the k-occurrence distribution (hubness diagnostic).

    A positive skewness indicates the presence of hubs; high values (>1.2
    by the Radovanović et al. 2010 threshold) predict degraded kNN
    performance.  Returns 0.0 when the distribution is constant (zero
    variance), which happens when every point appears exactly the same
    number of times as a nearest neighbour.

    Parameters
    ----------
    D : numpy.ndarray
        Symmetric ``(n, n)`` non-negative distance matrix with zero diagonal.
    k : int
        Number of nearest neighbours (matches the kNN application's ``k``).

    Returns
    -------
    float
        Sample skewness (``scipy.stats.skew`` with ``bias=True``); 0.0 when
        the distribution is constant.
    """
    import math

    from scipy.stats import skew

    counts = k_occurrence_counts(D, k=k)
    s = float(skew(counts, bias=True))
    if math.isnan(s):
        return 0.0
    return s
