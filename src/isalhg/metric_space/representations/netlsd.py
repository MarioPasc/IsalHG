"""``NetLSDDistance`` -- optional spectral fifth competitor.

Computes the L2 distance between the NetLSD heat-trace signatures of the
Levi bipartite expansions of two hypergraphs.

**Method.** For a hypergraph ``H``, build its Levi bipartite graph
``B(H)`` via :func:`isalhg.core.levi_reduction.to_levi`, convert the
edge list to a scipy sparse adjacency matrix, and call
``netlsd.heat(adjacency)`` to obtain a heat-trace signature vector
``phi(H) in R^{250}`` (default timescale grid). The distance is
``||phi(H1) - phi(H2)||_2``.

**Spectral invariance property.** NetLSD is a spectral invariant: the
heat-trace signature depends only on the Laplacian spectrum of ``B(H)``,
which is preserved by graph isomorphism.  Consequently, isomorphic
hypergraphs ``H1 ~ H2`` yield signatures that are equal **up to
floating-point noise** (on the Fano plane, the empirical L2 distance
between an iso-pair is ~3e-15). This means the distance is ``~0`` for
iso-pairs, **not exactly 0** -- unlike the exact-invariant baselines
(``d_I``, nauty-edit) which return exact 0. Assert iso-pair equality
with ``numpy.testing.assert_allclose(atol=1e-6)``, never with ``==``.

**Optional dependency.** ``netlsd`` is not part of the package's core
requirements; it is installed separately via ``pip install netlsd``.
Both ``netlsd`` and ``numpy`` are imported lazily inside method bodies.
Importing this module therefore never fails due to a missing ``netlsd``
or ``numpy``.

**Citation.** Tsitsulin, A., Mottin, D., Karras, P., Bronstein, A., &
Muller, E. (2018). NetLSD: Hearing the Shape of a Graph. *KDD 2018*.
Package: https://github.com/xgfs/netlsd (MIT licence).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, cast

from isalhg.core.levi_reduction import to_levi
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.errors import RepresentationDependencyMissingError
from isalhg.metric_space.base import HypergraphDistance
from isalhg.metric_space.registry import register_distance
from isalhg.types import DistanceName

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray


def _levi_to_scipy_adj(H: SparseHypergraph) -> Any:
    """Build a symmetric scipy sparse adjacency matrix for the Levi graph of H.

    Parameters
    ----------
    H : SparseHypergraph
        The source hypergraph.

    Returns
    -------
    scipy.sparse.csr_matrix
        Symmetric ``(n_v + n_e, n_v + n_e)`` float64 adjacency matrix.
    """
    try:
        import numpy as np
        from scipy.sparse import csr_matrix
    except ImportError as exc:
        raise RepresentationDependencyMissingError(
            "numpy and scipy are required for NetLSDDistance; install via `pip install netlsd`"
        ) from exc

    levi = to_levi(H)
    n = levi.n_nodes
    if n == 0 or not levi.edges:
        import scipy.sparse as sp

        return sp.csr_matrix((n, n), dtype=np.float64)

    rows: list[int] = []
    cols: list[int] = []
    for v, e in levi.edges:
        rows.extend([v, e])
        cols.extend([e, v])
    data = np.ones(len(rows), dtype=np.float64)
    return csr_matrix((data, (rows, cols)), shape=(n, n))


class NetLSDDistance(HypergraphDistance):
    """L2 distance between NetLSD heat-trace signatures of Levi expansions.

    The Levi bipartite graph ``B(H)`` of a hypergraph ``H`` is built via
    :func:`isalhg.core.levi_reduction.to_levi`; its adjacency matrix is
    passed to ``netlsd.heat()`` to obtain a 250-dimensional signature
    vector.  The pairwise distance is the Euclidean norm between two
    signature vectors.

    Because NetLSD is a spectral invariant, isomorphic hypergraphs yield
    signatures that agree to floating-point precision (~1e-14 gap on
    the Fano plane) -- not exactly zero.  Compare with
    ``numpy.testing.assert_allclose(atol=1e-6)``.

    Parameters
    ----------
    timescales : numpy.ndarray or None, optional
        Timescale grid passed to ``netlsd.heat``.  ``None`` uses the
        default grid (``np.logspace(-2, 2, 250)``).

    Raises
    ------
    RepresentationDependencyMissingError
        When ``netlsd`` or ``numpy``/``scipy`` is not installed.
    """

    def __init__(self, *, timescales: Any | None = None) -> None:
        self._timescales = timescales

    @property
    def name(self) -> DistanceName:
        return "netlsd_l2"

    def fingerprint(self, H: SparseHypergraph) -> NDArray[np.float64]:
        """Return the NetLSD heat-trace signature vector for ``H``.

        Amortizes :meth:`matrix` when signatures are cached externally.

        Parameters
        ----------
        H : SparseHypergraph
            Input hypergraph.

        Returns
        -------
        numpy.ndarray
            Shape ``(250,)`` float64 signature vector (default timescales).

        Raises
        ------
        RepresentationDependencyMissingError
            When ``netlsd`` or ``scipy`` is not installed.
        """
        try:
            import netlsd
        except ImportError as exc:
            raise RepresentationDependencyMissingError(
                "netlsd is required for NetLSDDistance; install via `pip install netlsd`"
            ) from exc

        adj = _levi_to_scipy_adj(H)
        # netlsd is untyped; cast informs mypy that heat() returns a float64 array.
        if self._timescales is None:
            return cast("NDArray[np.float64]", netlsd.heat(adj))
        return cast("NDArray[np.float64]", netlsd.heat(adj, timescales=self._timescales))

    def pairwise(self, H1: SparseHypergraph, H2: SparseHypergraph) -> float:
        """Return the L2 distance between the NetLSD signatures of ``H1`` and ``H2``.

        Parameters
        ----------
        H1, H2 : SparseHypergraph
            The two hypergraphs to compare.

        Returns
        -------
        float
            L2 norm ``||phi(H1) - phi(H2)||_2``.  Approximately 0 for
            isomorphic pairs (not exactly 0 due to floating-point noise).

        Raises
        ------
        RepresentationDependencyMissingError
            When ``netlsd`` or ``scipy`` is not installed.
        """
        try:
            import numpy as np
        except ImportError as exc:
            raise RepresentationDependencyMissingError(
                "numpy is required for NetLSDDistance.pairwise(); install via `pip install netlsd`"
            ) from exc

        sig1 = self.fingerprint(H1)
        sig2 = self.fingerprint(H2)
        return float(np.linalg.norm(sig1 - sig2))

    def matrix(self, corpus: Sequence[SparseHypergraph]) -> NDArray[np.float64]:
        """Return the symmetric L2-distance matrix over ``corpus``.

        Computes all signatures in one pass, then fills the upper triangle.
        This is cheaper than ``O(N^2)`` independent :meth:`pairwise` calls
        because each Levi adjacency and eigendecomposition is computed once.

        Parameters
        ----------
        corpus : Sequence[SparseHypergraph]
            The hypergraphs to embed.

        Returns
        -------
        numpy.ndarray
            Symmetric ``(N, N)`` float64 matrix, zero diagonal.

        Raises
        ------
        RepresentationDependencyMissingError
            When ``netlsd`` or ``scipy`` is not installed.
        """
        try:
            import numpy as np
        except ImportError as exc:
            raise RepresentationDependencyMissingError(
                "numpy is required for NetLSDDistance.matrix(); install via `pip install netlsd`"
            ) from exc

        size = len(corpus)
        if size == 0:
            return np.zeros((0, 0), dtype=np.float64)

        signatures = [self.fingerprint(H) for H in corpus]
        result = np.zeros((size, size), dtype=np.float64)
        for i in range(size):
            for j in range(i + 1, size):
                d = float(np.linalg.norm(signatures[i] - signatures[j]))
                result[i, j] = d
                result[j, i] = d
        return result


register_distance("netlsd_l2", NetLSDDistance)
