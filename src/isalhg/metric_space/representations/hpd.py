"""``HPDDistance`` — Hyperedge Portrait Divergence (Agostinelli et al., JCN 2026).

The Hyperedge Portrait Divergence maps each hypergraph to its *hyperedge
portrait* — a 4-D tensor ``B[m, n, l, k]`` counting how many hyperedges of
size ``m`` see ``k`` hyperedges of size ``n`` at line-graph distance ``l``
(see :func:`_hpd_vendor.hyperedge_portrait`) — and returns the Jensen–Shannon
divergence between two such portraits after padding them to the same shape.

The upstream ``hyper_portrait_divergence`` function in the vendored module
returns the Jensen–Shannon *divergence* (JSD) in bits, not its square root.
The square root ``sqrt(JSD)`` is a proper metric on distributions (Endres &
Schindelin 2003; Lin 1991). This class therefore exposes a ``sqrt_js``
constructor kwarg (default ``True``) and defaults to returning the JS
*distance* ``sqrt(JSD)`` so that ``HPDDistance`` satisfies the triangle
inequality and is comparable to the other metric-valued competitors
(HyperCOT, ``IsalHGLevenshtein``). Set ``sqrt_js=False`` to recover the raw
JSD for ablation comparisons.

The functions are vendored verbatim from MIT-licensed upstream code; the
provenance header in :mod:`_hpd_vendor` lists every adaptation.

Dependency guard
----------------
``xgi``, ``networkx``, and ``scipy`` are imported *inside* method bodies.
Importing this module never triggers those imports, and absence raises
:class:`isalhg.errors.RepresentationDependencyMissingError` with an install
hint, following the same pattern as :class:`HypergraphWLDistance`.

COMPETITORS.md classification
------------------------------
*fair metric baseline* — HPD is hyperedge-path-centric and global,
complementing the vertex-neighbourhood-centric WL baseline.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.errors import RepresentationDependencyMissingError
from isalhg.metric_space.base import HypergraphDistance
from isalhg.metric_space.registry import register_distance
from isalhg.types import DistanceName

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray


def _import_deps() -> tuple[Any, Any, Any]:
    """Import optional deps inside callers to stay importable when absent.

    Returns
    -------
    tuple
        ``(xgi_module, _hpd_vendor_module, numpy_module)``

    Raises
    ------
    RepresentationDependencyMissingError
        If any required dependency is not installed.
    """
    try:
        import numpy as np
        import xgi  # noqa: F401  — sentinel; ImportError propagates if absent

        from isalhg.metric_space.representations import _hpd_vendor
    except ImportError as exc:
        raise RepresentationDependencyMissingError(
            "HPDDistance requires xgi, networkx, and scipy; "
            "install via `pip install xgi networkx scipy`"
        ) from exc
    return xgi, _hpd_vendor, np


class HPDDistance(HypergraphDistance):
    """Jensen–Shannon distance (or divergence) between hyperedge portraits.

    Parameters
    ----------
    sqrt_js : bool, optional
        When ``True`` (default) return the Jensen–Shannon *distance*
        ``sqrt(JSD)``, which is a proper metric (satisfies the triangle
        inequality). When ``False`` return the raw Jensen–Shannon *divergence*
        ``JSD`` for ablation comparisons. Both are in ``[0, 1]``.

    Raises
    ------
    RepresentationDependencyMissingError
        At call time if ``xgi``, ``networkx``, or ``scipy`` is not installed.
    """

    def __init__(self, *, sqrt_js: bool = True) -> None:
        self._sqrt_js = sqrt_js

    @property
    def name(self) -> DistanceName:
        return "hpd_jsd"

    def pairwise(self, H1: SparseHypergraph, H2: SparseHypergraph) -> float:
        """Return the HPD distance (or divergence) between ``H1`` and ``H2``.

        Parameters
        ----------
        H1, H2 : SparseHypergraph
            The two hypergraphs to compare. Each must have at least one
            hyperedge (the hyperedge portrait is undefined on edge-less
            hypergraphs).

        Returns
        -------
        float
            ``sqrt(JSD)`` when ``sqrt_js=True`` (default); raw ``JSD`` when
            ``sqrt_js=False``. Returns ``0.0`` for isomorphic pairs.

        Raises
        ------
        RepresentationDependencyMissingError
            If ``xgi``, ``networkx``, or ``scipy`` is not installed.
        """
        _, _hpd_vendor, _ = _import_deps()
        from isalhg.adapters.xgi_adapter import XGIAdapter

        adapter = XGIAdapter()
        b1 = _hpd_vendor.hyperedge_portrait(adapter.to_external(H1))
        b2 = _hpd_vendor.hyperedge_portrait(adapter.to_external(H2))
        jsd = _hpd_vendor.hyper_portrait_divergence(b1, b2)
        return math.sqrt(jsd) if self._sqrt_js else float(jsd)

    def matrix(self, corpus: Sequence[SparseHypergraph]) -> NDArray[np.float64]:
        """Return the dense symmetric HPD distance matrix over ``corpus``.

        Precomputes each hyperedge portrait once (O(N) portrait computations),
        then computes pairwise JSD over the upper triangle (O(N²) calls).
        This is strictly cheaper than calling :meth:`pairwise` independently
        for every pair, which would recompute each portrait O(N) times.

        Parameters
        ----------
        corpus : Sequence[SparseHypergraph]
            Hypergraphs to embed; each must have at least one hyperedge.

        Returns
        -------
        numpy.ndarray
            Symmetric ``(len(corpus), len(corpus))`` ``float64`` matrix,
            zero diagonal.

        Raises
        ------
        RepresentationDependencyMissingError
            If ``xgi``, ``networkx``, or ``scipy`` is not installed.
        """
        _, _hpd_vendor, np = _import_deps()
        from isalhg.adapters.xgi_adapter import XGIAdapter

        adapter = XGIAdapter()
        portraits = [_hpd_vendor.hyperedge_portrait(adapter.to_external(H)) for H in corpus]

        size = len(corpus)
        mat = np.zeros((size, size), dtype=np.float64)
        for i in range(size):
            for j in range(i + 1, size):
                jsd = _hpd_vendor.hyper_portrait_divergence(portraits[i], portraits[j])
                value = math.sqrt(jsd) if self._sqrt_js else float(jsd)
                mat[i, j] = value
                mat[j, i] = value
        return mat  # type: ignore[no-any-return]


register_distance("hpd_jsd", lambda: HPDDistance())
