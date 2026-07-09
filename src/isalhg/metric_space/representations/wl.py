"""``HypergraphWLDistance`` -- the fair WL colour-histogram baseline.

Wraps :func:`isalhg.core.hypergraph_wl.wl_hash` (hypergraph 1-WL colour
refinement on the incidence relation). The fingerprint of ``H`` is the multiset
(histogram) of its stable WL colours; the distance is the ``L1`` (default) or
symmetric ``chi2`` distance between two histograms (Feng et al., TPAMI 2024,
HG-WL subtree convention).

Cross-graph colour comparability. ``wl_hash`` stops as soon as a graph's own
partition stabilises, so two graphs run in isolation may read their colours at
different rounds -- making raw colour values incomparable across graphs. To keep
the baseline fair (not a strawman), WL is run **once on the disjoint union** of
the corpus: every component then reads out at the same global round, so a
structural role shared by two graphs receives the same colour. Colours depend on
the vertex label and incidence structure only, never on vertex id, so the union
offsets do not perturb them. Isomorphic hypergraphs yield identical colour
multisets and hence distance ``0`` regardless of this alignment.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from typing import TYPE_CHECKING

from isalhg.core.backends import Backend
from isalhg.core.hypergraph_wl import wl_hash
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.errors import RepresentationDependencyMissingError
from isalhg.metric_space.base import HypergraphDistance
from isalhg.metric_space.registry import register_distance
from isalhg.types import DistanceName, EdgeLabel, HyperedgeSet, VertexLabel

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray

_VALID_METRICS: tuple[str, ...] = ("l1", "chi2")


def _disjoint_union(
    corpus: Sequence[SparseHypergraph],
) -> tuple[SparseHypergraph, list[int]]:
    """Return the disjoint union of ``corpus`` and the per-graph vertex offsets.

    Member-sets of distinct graphs land in disjoint id ranges, so no hyperedge
    collides across graphs and none is silently merged.
    """
    n_vertex_labels = max((H.n_vertex_labels for H in corpus), default=1)
    n_edge_labels = max((H.n_edge_labels for H in corpus), default=1)
    vertex_labels: list[VertexLabel] = []
    edges: list[HyperedgeSet] = []
    edge_labels: list[EdgeLabel] = []
    offsets: list[int] = []
    offset = 0
    for H in corpus:
        offsets.append(offset)
        vertex_labels.extend(H.vertex_label(v) for v in range(H.n_nodes))
        for _, members, ell in H.iter_edges():
            edges.append(frozenset(offset + u for u in members))
            edge_labels.append(ell)
        offset += H.n_nodes
    union = SparseHypergraph(
        n_nodes=offset,
        hyperedges=edges,
        n_vertex_labels=n_vertex_labels,
        n_edge_labels=n_edge_labels,
        vertex_labels=vertex_labels,
        edge_labels=edge_labels,
    )
    return union, offsets


def _histogram_distance(h1: Counter[int], h2: Counter[int], metric: str) -> float:
    """L1 or symmetric chi2 distance between two colour-count histograms."""
    keys = set(h1) | set(h2)
    if metric == "l1":
        return float(sum(abs(h1.get(key, 0) - h2.get(key, 0)) for key in keys))
    # symmetric chi2: 0.5 * sum (a - b)^2 / (a + b)
    total = 0.0
    for key in keys:
        a = h1.get(key, 0)
        b = h2.get(key, 0)
        denominator = a + b
        if denominator > 0:
            total += (a - b) ** 2 / denominator
    return 0.5 * total


class HypergraphWLDistance(HypergraphDistance):
    """Distance between hypergraph-WL colour histograms.

    Parameters
    ----------
    metric : {"l1", "chi2"}, optional
        Histogram distance. Defaults to ``"l1"``.
    max_rounds : int or None, optional
        WL refinement-round cap. ``None`` (default) uses :func:`wl_hash`'s
        convergence default (run until the union partition stabilises).
    backend : {"cpp", "python"} or None, optional
        WL implementation. ``None`` uses the package default.

    Raises
    ------
    ValueError
        If ``metric`` is not one of ``"l1"`` / ``"chi2"``.
    """

    def __init__(
        self,
        *,
        metric: str = "l1",
        max_rounds: int | None = None,
        backend: Backend | None = None,
    ) -> None:
        if metric not in _VALID_METRICS:
            raise ValueError(f"metric must be one of {_VALID_METRICS}, got {metric!r}")
        self._metric = metric
        self._max_rounds = max_rounds
        self._backend = backend

    @property
    def name(self) -> DistanceName:
        return f"hypergraph_wl_{self._metric}"

    def _histograms(self, corpus: Sequence[SparseHypergraph]) -> list[Counter[int]]:
        if not corpus:
            return []
        union, offsets = _disjoint_union(corpus)
        if self._max_rounds is None:
            colours = wl_hash(union, backend=self._backend)
        else:
            colours = wl_hash(union, max_rounds=self._max_rounds, backend=self._backend)
        histograms: list[Counter[int]] = []
        for i, H in enumerate(corpus):
            start = offsets[i]
            histograms.append(Counter(colours[start : start + H.n_nodes]))
        return histograms

    def pairwise(self, H1: SparseHypergraph, H2: SparseHypergraph) -> float:
        histograms = self._histograms([H1, H2])
        return _histogram_distance(histograms[0], histograms[1], self._metric)

    def matrix(self, corpus: Sequence[SparseHypergraph]) -> NDArray[np.float64]:
        try:
            import numpy as np
        except ImportError as exc:  # pragma: no cover - exercised only without numpy
            raise RepresentationDependencyMissingError(
                "numpy is required for HypergraphWLDistance.matrix(); "
                "install via `pip install numpy`"
            ) from exc
        histograms = self._histograms(corpus)
        size = len(corpus)
        matrix = np.zeros((size, size), dtype=np.float64)
        for i in range(size):
            for j in range(i + 1, size):
                value = _histogram_distance(histograms[i], histograms[j], self._metric)
                matrix[i, j] = value
                matrix[j, i] = value
        return matrix


register_distance("hypergraph_wl_l1", lambda: HypergraphWLDistance(metric="l1"))
register_distance("hypergraph_wl_chi2", lambda: HypergraphWLDistance(metric="chi2"))
