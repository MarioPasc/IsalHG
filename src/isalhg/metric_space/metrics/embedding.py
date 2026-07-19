"""Classical MDS solve, Kruskal stress-1, and PSD check.

Implements the deterministic Torgerson–Gower double-centering + eigendecomposition
pipeline (PROPOSAL.md §5).  numpy and scipy are imported lazily inside each
function body; this module is importable with no optional dependencies installed.

Because ``d_I`` is a string-edit metric it is **not** guaranteed Euclidean, so
the Gram matrix ``B`` will generically have negative eigenvalues (Schoenberg's
theorem).  :func:`is_psd` and :func:`classical_mds` return the full eigenspectrum
so callers can check and report PSD status per corpus.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray


def classical_mds(
    D: NDArray[np.float64],
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Torgerson–Gower classical MDS eigendecomposition.

    Double-centres the squared distance matrix to obtain the Gram matrix ``B``
    and returns its full eigendecomposition sorted **largest eigenvalue first**.

    ``B = -½ · J · D² · J``   where  ``J = I − (1/n) · 11ᵀ`` .

    Parameters
    ----------
    D : numpy.ndarray
        Symmetric ``(n, n)`` non-negative distance matrix with zero diagonal.

    Returns
    -------
    eigenvalues : numpy.ndarray
        1-D array of length ``n``, sorted **descending** (largest first).
    eigenvectors : numpy.ndarray
        ``(n, n)`` matrix whose ``k``-th *column* is the eigenvector for
        ``eigenvalues[k]``.

    Notes
    -----
    Negative eigenvalues indicate that ``d`` is not Euclidean.
    :func:`is_psd` tests whether all are non-negative within a tolerance.
    """
    import numpy as np
    from scipy.linalg import eigh

    D = np.asarray(D, dtype=np.float64)
    n = D.shape[0]

    D_sq = D**2
    # Double-centering: B = -0.5 * J @ D_sq @ J
    ones = np.ones((n, n), dtype=np.float64)
    J = np.eye(n) - ones / n
    B = -0.5 * J @ D_sq @ J

    # eigh returns eigenvalues in ascending order.
    vals, vecs = eigh(B)

    # Reverse to descending order.
    vals = vals[::-1].copy()
    vecs = vecs[:, ::-1].copy()

    return vals, vecs


def is_psd(
    eigenvalues: NDArray[np.float64],
    tol: float = 1e-10,
) -> bool:
    """Return True iff all eigenvalues are >= -tol (Gram matrix is PSD).

    Parameters
    ----------
    eigenvalues : numpy.ndarray
        Eigenvalue array from :func:`classical_mds` (or any symmetric matrix).
    tol : float, optional
        Absolute tolerance for the negativity check.  Numerical noise on a
        true Euclidean metric can produce eigenvalues of order ``-1e-14``.

    Returns
    -------
    bool
        ``True`` if the smallest eigenvalue is ``>= -tol``.
    """
    import numpy as np

    eigenvalues = np.asarray(eigenvalues, dtype=np.float64)
    return bool(float(eigenvalues.min()) >= -tol)


def embed_classical(
    D: NDArray[np.float64],
    n_dims: int,
) -> NDArray[np.float64]:
    """Return a classical MDS embedding in ``n_dims`` dimensions.

    Clips negative eigenvalues to zero before taking the square root, which
    produces the best-fitting Euclidean embedding when ``B`` is indefinite.

    Parameters
    ----------
    D : numpy.ndarray
        Symmetric ``(n, n)`` distance matrix.
    n_dims : int
        Target embedding dimensionality.  If ``n_dims`` exceeds the number of
        positive eigenvalues, the trailing columns are zero.

    Returns
    -------
    numpy.ndarray
        ``(n, n_dims)`` coordinate matrix ``X`` such that
        ``||X[i] - X[j]||₂`` approximates ``D[i, j]``.
    """
    import numpy as np

    D = np.asarray(D, dtype=np.float64)
    n = D.shape[0]
    n_dims = min(n_dims, n)

    vals, vecs = classical_mds(D)

    # Take the top n_dims eigenvalues; clip negatives to avoid complex sqrt.
    top_vals = np.maximum(vals[:n_dims], 0.0)
    top_vecs = vecs[:, :n_dims]

    X: NDArray[np.float64] = top_vecs * np.sqrt(top_vals)[np.newaxis, :]
    return X


def kruskal_stress_1(
    D_original: NDArray[np.float64],
    D_embedded: NDArray[np.float64],
) -> float:
    """Kruskal stress-1 between original dissimilarities and embedded distances.

    ``S₁ = sqrt( Σᵢⱼ (dᵢⱼ − δᵢⱼ)² / Σᵢⱼ dᵢⱼ² )``

    where ``d`` = original and ``δ`` = embedded distances (upper triangle only,
    excluding the zero diagonal).

    Parameters
    ----------
    D_original : numpy.ndarray
        Symmetric ``(n, n)`` original distance matrix.
    D_embedded : numpy.ndarray
        Symmetric ``(n, n)`` distance matrix computed from the embedding.

    Returns
    -------
    float
        Kruskal stress-1, a non-negative value where 0 means perfect fit.
    """
    import numpy as np

    D_o = np.asarray(D_original, dtype=np.float64)
    D_e = np.asarray(D_embedded, dtype=np.float64)

    n = D_o.shape[0]
    idx = np.triu_indices(n, k=1)
    d = D_o[idx]
    delta = D_e[idx]

    numerator = float(np.sum((d - delta) ** 2))
    denominator = float(np.sum(d**2))
    if denominator == 0.0:
        return 0.0
    return float(np.sqrt(numerator / denominator))


def neg_eigenvalue_mass(
    eigenvalues: NDArray[np.float64],
    tol: float = 1e-10,
) -> float:
    """Non-Euclidean mass ν of the Gram spectrum.

    Measures the proportion of the total eigenvalue magnitude carried by
    strictly negative eigenvalues (those below ``-tol``).  A value of 0
    means the metric is Euclidean; values near 1 indicate strong
    non-Euclideanness.

    ``ν = Σ_{λ < -tol} |λ| / Σ_i |λ_i|``

    Parameters
    ----------
    eigenvalues : numpy.ndarray
        1-D array of eigenvalues from :func:`classical_mds` (or any symmetric
        matrix), in **any** order.
    tol : float, optional
        Eigenvalues in ``(-tol, 0)`` are treated as numerical zero and do not
        contribute to the numerator.  Matches the tolerance in :func:`is_psd`.

    Returns
    -------
    float
        ``ν ∈ [0, 1)``; returns 0.0 when all eigenvalues are zero.
    """
    import numpy as np

    eigenvalues = np.asarray(eigenvalues, dtype=np.float64)
    total = float(np.sum(np.abs(eigenvalues)))
    if total == 0.0:
        return 0.0
    neg_sum = float(np.sum(np.abs(eigenvalues[eigenvalues < -tol])))
    return neg_sum / total


def shepard_data(
    D_original: NDArray[np.float64],
    D_embedded: NDArray[np.float64],
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Extract upper-triangle pairs (d_ij, δ_ij) for a Shepard diagram.

    A Shepard diagram plots original dissimilarities against embedding
    distances as a scatter plot.  Proximity to the identity line indicates
    low distortion.

    Parameters
    ----------
    D_original : numpy.ndarray
        Symmetric ``(n, n)`` original distance matrix.
    D_embedded : numpy.ndarray
        Symmetric ``(n, n)`` distance matrix computed from the embedding
        (e.g. from :func:`embed_classical`).

    Returns
    -------
    d_original : numpy.ndarray
        1-D array of ``n*(n-1)/2`` upper-triangle entries from ``D_original``.
    d_embedded : numpy.ndarray
        1-D array of ``n*(n-1)/2`` upper-triangle entries from ``D_embedded``,
        aligned with ``d_original``.
    """
    import numpy as np

    D_o = np.asarray(D_original, dtype=np.float64)
    D_e = np.asarray(D_embedded, dtype=np.float64)
    n = D_o.shape[0]
    idx = np.triu_indices(n, k=1)
    return D_o[idx], D_e[idx]
