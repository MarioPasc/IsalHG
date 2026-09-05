"""The certified medoid and its pairwise lower-bound certificate.

For a collection ``K_1..K_N`` and a dissimilarity ``d``,

* ``M = argmin_i sum_j d(K_i, K_j)`` is the medoid;
* ``LB = sum_{i<j} d(K_i, K_j) / (N - 1)`` lower-bounds the optimal cost;
* ``ratio = cost(M) / LB``, which is ``<= 2 - 2/N`` **in any metric** (Prop 3).

The ratio is the certificate. Under a dissimilarity that is not a metric the
derivation of ``LB`` fails, and ``LB > cost(M)`` can be observed -- the
certificate then lies. Measuring that event is the point of RQ2's
certificate-validity row, so this module computes the three numbers and states
them, and never clamps or repairs the ratio.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

from isalhg.errors import MetricSpaceError

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray


@dataclass(frozen=True)
class MedoidResult:
    """One medoid and its lower-bound certificate.

    Attributes
    ----------
    index : int
        Row index of the medoid; the lowest index wins a tie.
    cost : float
        ``sum_j D[index, j]``.
    lower_bound : float
        ``sum_{i<j} D[i, j] / (N - 1)``.
    ratio : float
        ``cost / lower_bound``; ``inf`` when the bound is zero and the cost is
        not, ``1.0`` when both are zero. A value above ``2 - 2/N`` witnesses a
        violated metric assumption, not a bug.
    """

    index: int
    cost: float
    lower_bound: float
    ratio: float


def medoid(D: NDArray[np.float64]) -> MedoidResult:
    """Return the medoid of a pairwise dissimilarity matrix and its certificate.

    Parameters
    ----------
    D : numpy.ndarray
        Symmetric ``(N, N)`` non-negative dissimilarity matrix with a zero
        diagonal, ``N >= 1``.

    Returns
    -------
    MedoidResult
        Index, cost, lower bound and ratio.

    Raises
    ------
    isalhg.errors.MetricSpaceError
        If ``D`` is not a square 2-D array, or is empty.
    """
    import numpy as np

    matrix = np.asarray(D, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise MetricSpaceError(f"expected a square distance matrix, got shape {matrix.shape}")
    if matrix.shape[0] == 0:
        raise MetricSpaceError("the medoid of an empty collection is undefined")
    size = matrix.shape[0]

    costs = matrix.sum(axis=1)
    index = int(np.argmin(costs))
    cost = float(costs[index])

    if size == 1:
        return MedoidResult(index=0, cost=0.0, lower_bound=0.0, ratio=1.0)

    total = float(np.triu(matrix, k=1).sum())
    lower_bound = total / (size - 1)
    ratio = cost / lower_bound if lower_bound != 0.0 else (1.0 if cost == 0.0 else math.inf)

    return MedoidResult(index=index, cost=cost, lower_bound=lower_bound, ratio=ratio)


__all__ = ["MedoidResult", "medoid"]
