"""Metric-space toolkit: the shared machinery every TKDE experiment runner calls.

The toolkit sits one layer above :mod:`isalhg.metric_space.distances` and
:mod:`isalhg.metric_space.representations`: it turns a corpus plus an *arm*
(a registered distance name) into a cached ``N x N`` matrix, and then wraps the
maintained libraries that consume such a matrix -- ``kmedoids`` (FasterPAM),
``scipy.cluster.hierarchy``, ``scikit-learn`` (LOF, kNN, metric MDS, ARI/NMI,
AUROC) -- behind the small, frozen surface the runners were written against.

Nothing here reimplements an algorithm a maintained library provides. The only
bespoke pieces are the cache protocol (:mod:`~isalhg.metric_space.toolkit.matrix`),
the certified medoid of Prop 3 (:mod:`~isalhg.metric_space.toolkit.medoid`), and
a documented pure-numpy PAM fallback used only when ``kmedoids`` is absent.

Every heavy dependency (numpy, scipy, scikit-learn, kmedoids, rapidfuzz) is
imported inside function bodies, so importing this package costs nothing and
never fails on a machine missing an optional dependency.
"""

from __future__ import annotations

from isalhg.metric_space.toolkit.clustering import (
    ari,
    average_linkage,
    cut,
    nmi,
    pam,
    per_class_table,
)
from isalhg.metric_space.toolkit.geometry import hubness, non_euclidean_mass
from isalhg.metric_space.toolkit.matrix import build_matrix, cache_paths
from isalhg.metric_space.toolkit.mds import metric_mds
from isalhg.metric_space.toolkit.medoid import MedoidResult, medoid
from isalhg.metric_space.toolkit.outliers import auroc, knn_score, lof_score

__all__ = [
    "MedoidResult",
    "ari",
    "auroc",
    "average_linkage",
    "build_matrix",
    "cache_paths",
    "cut",
    "hubness",
    "knn_score",
    "lof_score",
    "medoid",
    "metric_mds",
    "nmi",
    "non_euclidean_mass",
    "pam",
    "per_class_table",
]
