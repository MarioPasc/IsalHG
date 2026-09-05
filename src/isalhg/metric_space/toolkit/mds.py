"""Metric multidimensional scaling over a precomputed dissimilarity matrix.

``sklearn.manifold.MDS`` with ``metric=True`` (SMACOF) is the right solver here
rather than classical MDS: classical MDS assumes the double-centred Gram matrix
is positive semi-definite, which a space with non-Euclidean mass ``nu > 0`` is
not. SMACOF minimises raw stress directly and needs no such assumption.

Stress is recomputed explicitly as Kruskal's stress-1 from the returned
coordinates -- scikit-learn's ``stress_`` attribute has changed normalization
between releases, and every reported number must have one fixed definition.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from isalhg.errors import MetricSpaceError

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray


def metric_mds(
    D: NDArray[np.float64], dim: int = 2, seed: int = 0
) -> tuple[NDArray[np.float64], float]:
    """Embed ``D`` in ``dim`` dimensions by metric MDS and report stress-1.

    Parameters
    ----------
    D : numpy.ndarray
        Symmetric ``(N, N)`` dissimilarity matrix with a zero diagonal,
        ``N >= 2``.
    dim : int, optional
        Target dimension. Default 2 (the map).
    seed : int, optional
        Random state of the SMACOF initializations.

    Returns
    -------
    X : numpy.ndarray
        ``(N, dim)`` coordinates.
    stress1 : float
        Kruskal stress-1 between ``D`` and the Euclidean distances of ``X``,
        computed by :func:`isalhg.metric_space.metrics.embedding.kruskal_stress_1`.
        In ``[0, 1]``; 0 is a perfect fit.

    Raises
    ------
    isalhg.errors.MetricSpaceError
        If ``D`` is not square, has fewer than 2 rows, or ``dim < 1``.
    """
    import numpy as np

    matrix = np.asarray(D, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise MetricSpaceError(f"expected a square distance matrix, got shape {matrix.shape}")
    if matrix.shape[0] < 2:
        raise MetricSpaceError("metric MDS needs at least two items")
    if dim < 1:
        raise MetricSpaceError(f"dim must be >= 1, got {dim}")

    from scipy.spatial.distance import squareform
    from sklearn.manifold import MDS  # type: ignore[import-untyped]

    from isalhg.metric_space.metrics.embedding import kruskal_stress_1

    symmetric = (matrix + matrix.T) / 2.0
    np.fill_diagonal(symmetric, 0.0)

    embedder = MDS(**_mds_kwargs(MDS, dim, seed))
    coordinates = np.asarray(embedder.fit_transform(symmetric), dtype=np.float64)

    from scipy.spatial.distance import pdist

    embedded = squareform(pdist(coordinates))
    return coordinates, float(kruskal_stress_1(symmetric, embedded))


def _mds_kwargs(mds_class: Any, dim: int, seed: int) -> dict[str, Any]:
    """Spell metric SMACOF on precomputed dissimilarities for this scikit-learn.

    scikit-learn 1.9 renamed the two parameters that select this mode:
    ``dissimilarity='precomputed'`` became ``metric='precomputed'``, and the old
    ``metric=True`` became ``metric_mds=True``. Both spellings are still
    accepted in 1.9 but the old one warns, and only one of them exists in 1.10
    or in releases before the rename -- so the signature decides.
    """
    import inspect

    kwargs: dict[str, Any] = {
        "n_components": dim,
        "random_state": seed,
        "normalized_stress": False,
        "n_init": 4,
    }
    if "metric_mds" in inspect.signature(mds_class.__init__).parameters:
        kwargs["metric_mds"] = True
        kwargs["metric"] = "precomputed"
        # Pin the initialization: its default changes to "classical_mds" in
        # scikit-learn 1.10, which would silently move every reported stress.
        kwargs["init"] = "random"
    else:
        kwargs["metric"] = True
        kwargs["dissimilarity"] = "precomputed"
    return kwargs


__all__ = ["metric_mds"]
