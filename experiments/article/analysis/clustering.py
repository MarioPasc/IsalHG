"""Clustering + dendrogram (A2) pipeline — T-M5c.

k-medoids (PAM/FasterPAM) + agglomerative dendrogram on each pairwise
distance matrix D_I (ours) and each competitor D_rep.

Deliverables
------------
- Per-representation clustering metric table (CSV + JSON):
  silhouette, Dunn, Davies–Bouldin, ARI, NMI (internal + external).
- Agglomerative dendrogram metrics: cophenetic correlation, silhouette at k-cut.
- Medoid-representative (PAM k=1 degenerate) reported inline.
- Figures: dendrogram per representation, metric comparison bar chart.

Licence (applications.md §A2)
------------------------------
ν (k-medoids/PAM needs only a metric, no Euclidean coordinates) and the
G2 smoothness evidence (near-monotone ladder response, measured at T-M5g).

Data (T-M5b caches)
--------------------
D-matrix cache root:
    /media/.../results/T-M5b/d_matrix/planted_families/{label}/seed{seed}/{dist}/D.npy
Label source:
    PlantedFamilyDataset(**corpus_cfg) → item.extra["family_index"]

Library dependencies
--------------------
- kmedoids: FasterPAM (Schubert & Lenssen 2022, JOSS 7(75)) — PAM-equivalent.
- scipy.cluster.hierarchy: agglomerative linkage + cophenetic.
- sklearn.metrics: silhouette_score (precomputed), ARI, NMI.

Usage
-----
    python -m experiments.article.analysis.clustering \\
        --output-root /media/.../results/T-M5c/ \\
        --d-matrix-root /media/.../results/T-M5b/ \\
        --corpus planted_main
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import json
import logging
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Corpus configurations (same params as mds.py / mds_planted.yaml)
# ---------------------------------------------------------------------------

CORPUS_CONFIGS: dict[str, dict[str, Any]] = {
    "planted_main": {
        "n_families": 5,
        "members_per_family": 12,
        "n_nodes": 10,
        "k": 3,
        "n_edges": 10,
        "seed_value": 42,
        "n_edits": 3,
        "max_retries": 300,
    },
    "planted_small": {
        "n_families": 4,
        "members_per_family": 5,
        "n_nodes": 6,
        "k": 3,
        "n_edges": 5,
        "seed_value": 42,
        "n_edits": 2,
        "max_retries": 200,
    },
}

MAIN_DISTANCES: list[str] = [
    "isalhg_levenshtein",
    "hypergraph_wl_l1",
    "netlsd_l2",
    "hpd_jsd",
    "nauty_levi_edit",
]

SMALL_DISTANCES: list[str] = [
    "isalhg_levenshtein",
    "hypercot",
]

REPR_LABELS: dict[str, str] = {
    "isalhg_levenshtein": "IsalHG",
    "hypergraph_wl_l1": "WL-L1",
    "netlsd_l2": "NetLSD",
    "hpd_jsd": "HPD-JSD",
    "nauty_levi_edit": "NautyEdit",
    "hypercot": "HyperCOT",
}


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------


@dataclass
class KmedoidsResult:
    """Output of run_kmedoids.

    Parameters
    ----------
    medoids : numpy.ndarray
        Row indices of the k chosen medoids in D.
    labels : numpy.ndarray
        0-based cluster assignment for each point (length n).
    loss : float
        Total distance of each point to its assigned medoid (PAM objective).
    best_seed : int
        Random state of the best run among the n_init restarts.
    """

    medoids: np.ndarray
    labels: np.ndarray
    loss: float
    best_seed: int


@dataclass
class DendrogramResult:
    """Output of run_dendrogram.

    Parameters
    ----------
    linkage_matrix : numpy.ndarray
        Scipy linkage array of shape (n-1, 4).
    labels_at_k : numpy.ndarray
        Cluster assignments at the k-cluster cut (0-based).
    cophenetic : float
        Cophenetic correlation coefficient.
    silhouette_at_k : float
        Silhouette score at the k-cluster cut (precomputed D).
    """

    linkage_matrix: np.ndarray
    labels_at_k: np.ndarray
    cophenetic: float
    silhouette_at_k: float


# ---------------------------------------------------------------------------
# Pure mathematical helpers (unit-tested independently)
# ---------------------------------------------------------------------------


def dunn_index(D: np.ndarray, labels: np.ndarray) -> float:
    """Dunn validity index on a precomputed distance matrix.

    Dunn = min_{inter-cluster distance} / max_{intra-cluster diameter}

    The inter-cluster distance between clusters C_i and C_j is:
        delta(C_i, C_j) = min_{x in C_i, y in C_j} D[x, y]

    The intra-cluster diameter of C_i is:
        Delta(C_i) = max_{x, y in C_i} D[x, y]

    When all clusters are singletons, max_intra = 0 and Dunn = inf.

    Parameters
    ----------
    D : numpy.ndarray
        Symmetric (n, n) pairwise distance matrix with zero diagonal.
    labels : numpy.ndarray
        Integer cluster assignment for each point (length n).

    Returns
    -------
    float
        Dunn validity index (higher = better separation).

    References
    ----------
    Dunn 1973; Halkidi et al. 2001 (survey).
    """
    D = np.asarray(D, dtype=np.float64)
    labels = np.asarray(labels)
    unique = np.unique(labels)
    k = len(unique)

    # Intra-cluster diameters.
    max_intra = 0.0
    for c in unique:
        idx = np.where(labels == c)[0]
        if len(idx) < 2:
            continue
        sub = D[np.ix_(idx, idx)]
        diam = float(sub.max())
        if diam > max_intra:
            max_intra = diam

    if max_intra == 0.0:
        # All clusters are singletons (or one point each): Dunn = +inf.
        return float("inf")

    # Minimum inter-cluster distance.
    min_inter = float("inf")
    for i, ci in enumerate(unique):
        idx_i = np.where(labels == ci)[0]
        for cj in unique[i + 1 :]:
            idx_j = np.where(labels == cj)[0]
            sub = D[np.ix_(idx_i, idx_j)]
            d_ij = float(sub.min())
            if d_ij < min_inter:
                min_inter = d_ij

    if k < 2:
        return 0.0

    return min_inter / max_intra


def davies_bouldin_precomputed(
    D: np.ndarray,
    labels: np.ndarray,
    medoids: np.ndarray,
) -> float:
    """Davies–Bouldin index on a precomputed distance matrix using medoids.

    The standard DB index uses centroids as cluster representatives, which
    requires coordinate vectors.  Here we substitute the medoid:

        s_i = (1/|C_i|) sum_{x in C_i} D[x, medoid_i]   (scatter)
        d_ij = D[medoid_i, medoid_j]                       (medoid separation)
        DB = (1/k) sum_i max_{j != i} (s_i + s_j) / d_ij

    Parameters
    ----------
    D : numpy.ndarray
        Symmetric (n, n) pairwise distance matrix.
    labels : numpy.ndarray
        Integer cluster assignment for each point (length n).
    medoids : numpy.ndarray
        Row index of the medoid for each cluster, in label order.
        ``medoids[i]`` is the row index of the medoid for cluster with id
        ``np.unique(labels)[i]``.

    Returns
    -------
    float
        Davies–Bouldin index (lower = better).

    References
    ----------
    Davies & Bouldin 1979 (IEEE TPAMI).
    """
    D = np.asarray(D, dtype=np.float64)
    labels = np.asarray(labels)
    medoids = np.asarray(medoids)
    unique = np.unique(labels)
    k = len(unique)

    # Average scatter per cluster.
    scatter = np.zeros(k)
    for i, c in enumerate(unique):
        idx = np.where(labels == c)[0]
        scatter[i] = float(D[idx, medoids[i]].mean())

    # DB ratio per cluster.
    db_sum = 0.0
    for i in range(k):
        max_ratio = 0.0
        for j in range(k):
            if i == j:
                continue
            sep = D[medoids[i], medoids[j]]
            # Identical medoids (degenerate): treat as infinite ratio.
            ratio = float("inf") if sep < 1e-15 else (scatter[i] + scatter[j]) / sep
            if ratio > max_ratio:
                max_ratio = ratio
        db_sum += max_ratio

    return db_sum / k


def silhouette_precomputed(D: np.ndarray, labels: np.ndarray) -> float:
    """Silhouette score on a precomputed distance matrix.

    Thin wrapper around ``sklearn.metrics.silhouette_score`` with
    ``metric='precomputed'``.

    Parameters
    ----------
    D : numpy.ndarray
        Symmetric (n, n) pairwise distance matrix.
    labels : numpy.ndarray
        Cluster assignment for each point (length n).

    Returns
    -------
    float
        Mean silhouette coefficient in [-1, 1].
    """
    from sklearn.metrics import silhouette_score

    return float(silhouette_score(D, labels, metric="precomputed"))


def cophenetic_from_d(D: np.ndarray, method: str = "average") -> float:
    """Cophenetic correlation from a square distance matrix.

    Parameters
    ----------
    D : numpy.ndarray
        Symmetric (n, n) pairwise distance matrix.
    method : str, optional
        Linkage method for ``scipy.cluster.hierarchy.linkage``.  Default 'average'.

    Returns
    -------
    float
        Cophenetic correlation coefficient in [-1, 1].
    """
    import scipy.cluster.hierarchy as sch
    from scipy.spatial.distance import squareform

    condensed = squareform(D, checks=False)
    Z = sch.linkage(condensed, method=method)
    c, _ = sch.cophenet(Z, condensed)
    return float(c)


# ---------------------------------------------------------------------------
# Clustering runners
# ---------------------------------------------------------------------------


def run_kmedoids(
    D: np.ndarray,
    k: int,
    n_init: int = 10,
    rng_seed: int = 42,
) -> KmedoidsResult:
    """Run FasterPAM k-medoids on a precomputed distance matrix.

    Performs ``n_init`` restarts with different random states and returns the
    result with the lowest PAM objective (total distance to medoids).

    FasterPAM is equivalent to PAM in result quality (same local minimum) but
    runs in O(k) per swap step instead of O(k(n-k)).

    Parameters
    ----------
    D : numpy.ndarray
        Symmetric (n, n) pairwise distance matrix.
    k : int
        Number of medoids / clusters.
    n_init : int, optional
        Number of random-restart initializations.  Default 10.
    rng_seed : int, optional
        Base random state; restart i uses ``rng_seed + i``.  Default 42.

    Returns
    -------
    KmedoidsResult

    References
    ----------
    Schubert & Lenssen 2022 (JOSS 7(75), doi:10.21105/joss.04183).
    """
    import kmedoids

    D = np.asarray(D, dtype=np.float64)
    best: Any = None
    best_seed = rng_seed

    for i in range(n_init):
        seed_i = rng_seed + i
        result = kmedoids.fasterpam(D, k, random_state=seed_i)
        if best is None or result.loss < best.loss:
            best = result
            best_seed = seed_i

    return KmedoidsResult(
        medoids=np.array(best.medoids, dtype=np.intp),
        labels=np.array(best.labels, dtype=np.intp),
        loss=float(best.loss),
        best_seed=best_seed,
    )


def run_dendrogram(
    D: np.ndarray,
    k: int,
    linkage_method: str = "average",
) -> DendrogramResult:
    """Agglomerative dendrogram on a precomputed distance matrix.

    Uses UPGMA (average) linkage by default, which is defined for any
    dissimilarity (no Euclidean assumption).

    Parameters
    ----------
    D : numpy.ndarray
        Symmetric (n, n) pairwise distance matrix.
    k : int
        Number of clusters for the flat cut (used to compute silhouette at k).
    linkage_method : str, optional
        Linkage criterion: 'average', 'single', 'complete', 'ward'.
        'ward' requires Euclidean data; use 'average' for metric-only data.
        Default 'average'.

    Returns
    -------
    DendrogramResult
    """
    import scipy.cluster.hierarchy as sch
    from scipy.spatial.distance import squareform
    from sklearn.metrics import silhouette_score

    D = np.asarray(D, dtype=np.float64)
    condensed = squareform(D, checks=False)
    Z = sch.linkage(condensed, method=linkage_method)

    # Cophenetic correlation.
    c, _ = sch.cophenet(Z, condensed)

    # Flat cut at k clusters (0-based labels).
    labels_1based = sch.fcluster(Z, t=k, criterion="maxclust")
    labels = (labels_1based - 1).astype(np.intp)  # convert to 0-based

    # Silhouette at k-cut.
    n_unique = len(np.unique(labels))
    sil = float("nan") if n_unique < 2 else float(silhouette_score(D, labels, metric="precomputed"))

    return DendrogramResult(
        linkage_matrix=Z,
        labels_at_k=labels,
        cophenetic=float(c),
        silhouette_at_k=sil,
    )


# ---------------------------------------------------------------------------
# Metric bundler
# ---------------------------------------------------------------------------


def clustering_metrics(
    D: np.ndarray,
    pred_labels: np.ndarray,
    medoids: np.ndarray,
    true_labels: np.ndarray,
) -> dict[str, float]:
    """Compute the full A2 internal + external metric set.

    Parameters
    ----------
    D : numpy.ndarray
        Symmetric (n, n) pairwise distance matrix.
    pred_labels : numpy.ndarray
        Predicted cluster assignments (0-based, length n).
    medoids : numpy.ndarray
        Row indices of the k medoids in label order.
    true_labels : numpy.ndarray
        Ground-truth planted-family ids (length n).

    Returns
    -------
    dict
        Keys: silhouette, dunn, davies_bouldin, ari, nmi.
    """
    from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

    sil = silhouette_precomputed(D, pred_labels)
    dunn = dunn_index(D, pred_labels)
    db = davies_bouldin_precomputed(D, pred_labels, medoids)
    ari = float(adjusted_rand_score(true_labels, pred_labels))
    nmi = float(normalized_mutual_info_score(true_labels, pred_labels, average_method="arithmetic"))

    return {
        "silhouette": sil,
        "dunn": dunn,
        "davies_bouldin": db,
        "ari": ari,
        "nmi": nmi,
    }


# ---------------------------------------------------------------------------
# Cache loading
# ---------------------------------------------------------------------------


def load_corpus_and_labels(corpus_cfg: dict[str, Any]) -> tuple[list, list[int]]:
    """Load PlantedFamilyDataset and extract family-index labels.

    Parameters
    ----------
    corpus_cfg : dict
        Keyword arguments forwarded to ``PlantedFamilyDataset``.

    Returns
    -------
    hypergraphs : list[SparseHypergraph]
    labels : list[int]
        ``item.extra["family_index"]`` for each item, in iteration order.
        Aligns 1:1 with the cached D.npy row order.
    """
    from isalhg.datasets.synthetic.planted_families import PlantedFamilyDataset

    dataset = PlantedFamilyDataset(**corpus_cfg)
    items = list(dataset)
    hypergraphs = [item.hypergraph for item in items]
    labels = [int(item.extra.get("family_index", 0)) for item in items]
    return hypergraphs, labels


def load_d_matrix(
    d_matrix_root: Path, corpus_label: str, seed_val: int, dist_name: str
) -> np.ndarray:
    """Load a cached D.npy from T-M5b output layout.

    Path: ``{d_matrix_root}/d_matrix/planted_families/{corpus_label}/seed{seed_val}/
    {dist_name}/D.npy``

    Parameters
    ----------
    d_matrix_root : Path
        Root of T-M5b results (e.g. ``/media/.../results/T-M5b``).
    corpus_label : str
        e.g. ``"planted_main"``.
    seed_val : int
        Dataset seed (42).
    dist_name : str
        Distance name (e.g. ``"isalhg_levenshtein"``).

    Returns
    -------
    numpy.ndarray
        Symmetric (n, n) distance matrix.

    Raises
    ------
    FileNotFoundError
        If the cache file does not exist.
    """
    path = (
        Path(d_matrix_root)
        / "d_matrix"
        / "planted_families"
        / corpus_label
        / f"seed{seed_val}"
        / dist_name
        / "D.npy"
    )
    if not path.exists():
        raise FileNotFoundError(f"D-matrix cache missing: {path}")
    return np.load(str(path))


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------


def _save_figure(fig: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(path), dpi=150, bbox_inches="tight")
    logger.info("  figure saved: %s", path)


def plot_dendrogram_figure(
    Z: np.ndarray,
    labels: list[int] | None,
    repr_label: str,
    corpus_label: str,
    k: int,
) -> Any:
    """Agglomerative dendrogram with colour labels at the k-cut.

    Parameters
    ----------
    Z : numpy.ndarray
        Linkage matrix from ``scipy.cluster.hierarchy.linkage``.
    labels : list[int] or None
        Ground-truth family ids for leaf colouring.
    repr_label : str
        Display name of the representation.
    corpus_label : str
    k : int
        Number of clusters highlighted.

    Returns
    -------
    matplotlib.figure.Figure
    """
    import matplotlib.pyplot as plt
    import scipy.cluster.hierarchy as sch

    n = Z.shape[0] + 1
    fig, ax = plt.subplots(figsize=(max(6, n * 0.18), 4))
    sch.dendrogram(
        Z,
        ax=ax,
        color_threshold=Z[-(k - 1), 2],  # colour the k top clusters
        above_threshold_color="grey",
        leaf_rotation=90.0,
        leaf_font_size=5.0,
        no_labels=(n > 30),
    )
    ax.set_title(f"Dendrogram — {repr_label}\n{corpus_label}  (k={k})", fontsize=9)
    ax.set_xlabel("Sample index", fontsize=7)
    ax.set_ylabel("Distance", fontsize=7)
    ax.tick_params(labelsize=6)
    fig.tight_layout()
    return fig


def plot_metric_comparison(
    rows: list[dict[str, Any]],
    corpus_label: str,
    metrics: list[str] | None = None,
) -> Any:
    """Bar chart comparing clustering metrics across representations.

    Parameters
    ----------
    rows : list[dict]
        Clustering result rows (one per representation).
    corpus_label : str
    metrics : list[str] or None
        Which metric keys to plot.  Defaults to silhouette, ARI, NMI.

    Returns
    -------
    matplotlib.figure.Figure
    """
    import matplotlib.pyplot as plt

    if metrics is None:
        metrics = ["silhouette", "ari", "nmi"]

    reprs = [r["representation"] for r in rows]
    n_reprs = len(reprs)
    n_metrics = len(metrics)
    x = np.arange(n_reprs)
    width = 0.25

    fig, ax = plt.subplots(figsize=(max(5, n_reprs * 1.2), 3.5))
    for i, m in enumerate(metrics):
        vals = [r.get(m, float("nan")) for r in rows]
        ax.bar(x + i * width, vals, width, label=m)

    ax.set_xticks(x + width * (n_metrics - 1) / 2)
    ax.set_xticklabels(reprs, rotation=20, ha="right", fontsize=7)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Metric value", fontsize=8)
    ax.set_title(f"A2 clustering metrics — {corpus_label}", fontsize=9)
    ax.legend(fontsize=7)
    ax.tick_params(labelsize=7)
    fig.tight_layout()
    return fig


def plot_combined_dendrogram(
    dendrograms: dict[str, DendrogramResult],
    corpus_label: str,
    k: int,
) -> Any:
    """Multi-panel dendrogram comparing all representations.

    Parameters
    ----------
    dendrograms : dict[str, DendrogramResult]
        Keyed by representation name.
    corpus_label : str
    k : int
        Number of clusters.

    Returns
    -------
    matplotlib.figure.Figure
    """
    import matplotlib.pyplot as plt
    import scipy.cluster.hierarchy as sch

    n_reprs = len(dendrograms)
    if n_reprs == 0:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
        return fig

    ncols = min(3, n_reprs)
    nrows = (n_reprs + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(5 * ncols, 3.5 * nrows), squeeze=False)

    for idx, (repr_name, dr) in enumerate(dendrograms.items()):
        row, col = divmod(idx, ncols)
        ax = axes[row][col]
        Z = dr.linkage_matrix
        n = Z.shape[0] + 1
        sch.dendrogram(
            Z,
            ax=ax,
            color_threshold=Z[-(k - 1), 2],
            above_threshold_color="grey",
            no_labels=(n > 30),
            leaf_font_size=4.0,
        )
        repr_label = REPR_LABELS.get(repr_name, repr_name)
        ax.set_title(
            f"{repr_label}  (coph={dr.cophenetic:.3f}, sil={dr.silhouette_at_k:.3f})",
            fontsize=7,
        )
        ax.tick_params(labelsize=5)

    for idx in range(n_reprs, nrows * ncols):
        row, col = divmod(idx, ncols)
        axes[row][col].set_visible(False)

    fig.suptitle(f"Agglomerative dendrogram — {corpus_label}", fontsize=10)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------


def _atomic_write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp.json")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, path)
    except Exception:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def _write_clustering_table(
    rows: list[dict[str, Any]],
    csv_path: Path,
    json_path: Path,
) -> None:
    """Write clustering metric table to CSV and JSON."""
    flat_keys = [
        "corpus",
        "representation",
        "n_points",
        "k",
        "linkage_method",
        "silhouette_pam",
        "dunn",
        "davies_bouldin",
        "ari",
        "nmi",
        "silhouette_dendro",
        "cophenetic",
        "medoid_k1_family",
    ]
    _atomic_write_json(json_path, rows)
    logger.info("clustering table JSON: %s", json_path)

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=flat_keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    logger.info("clustering table CSV: %s", csv_path)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def run_clustering_pipeline(
    output_root: Path,
    d_matrix_root: Path,
    corpus_label: str,
    corpus_cfg: dict[str, Any],
    distance_names: list[str],
    linkage_method: str = "average",
    n_init: int = 10,
    rng_seed: int = 42,
) -> list[dict[str, Any]]:
    """Run the full T-M5c A2 clustering pipeline on one corpus.

    Steps
    -----
    1. Load corpus and ground-truth labels.
    2. For each distance representation:
       a. Load cached D.npy from T-M5b output.
       b. k-medoids (FasterPAM): silhouette, Dunn, DB, ARI, NMI.
       c. k=1 degenerate: record medoid's family_index (inline representative).
       d. Agglomerative dendrogram: cophenetic correlation, silhouette at k-cut.
    3. Write metric table (CSV + JSON).
    4. Write figures: combined dendrogram, metric comparison bar chart.

    Parameters
    ----------
    output_root : Path
        Where T-M5c results are written.
    d_matrix_root : Path
        Root of T-M5b D-matrix cache (contains ``d_matrix/`` subdirectory).
    corpus_label : str
        e.g. ``"planted_main"``.
    corpus_cfg : dict
        PlantedFamilyDataset constructor kwargs.
    distance_names : list[str]
        Registered distance names whose caches are available.
    linkage_method : str, optional
        Agglomerative linkage criterion.  Default 'average'.
    n_init : int, optional
        FasterPAM restarts.  Default 10.
    rng_seed : int, optional
        Base RNG seed.  Default 42.

    Returns
    -------
    list[dict]
        One row per (corpus, representation).
    """
    logger.info("=== T-M5c clustering pipeline: %s ===", corpus_label)

    # 1. Corpus labels.
    seed_val = int(corpus_cfg.get("seed_value", 0))
    n_families = int(corpus_cfg["n_families"])
    _, true_labels_list = load_corpus_and_labels(corpus_cfg)
    true_labels = np.array(true_labels_list, dtype=np.intp)
    n = len(true_labels)
    logger.info("  N=%d, k=%d, seed=%d", n, n_families, seed_val)

    figures_dir = output_root / "figures" / corpus_label
    figures_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    dendrograms: dict[str, DendrogramResult] = {}

    for dist_name in distance_names:
        repr_label = REPR_LABELS.get(dist_name, dist_name)
        logger.info("--- %s (%s) ---", dist_name, repr_label)

        # 2a. Load D.
        try:
            D = load_d_matrix(d_matrix_root, corpus_label, seed_val, dist_name)
        except FileNotFoundError as exc:
            logger.warning("  cache missing: %s; skipping.", exc)
            continue

        if D.shape[0] != n:
            logger.error(
                "  D shape mismatch: D.shape[0]=%d vs n_labels=%d; skipping.", D.shape[0], n
            )
            continue

        # 2b. k-medoids at n_families.
        km_result = run_kmedoids(D, k=n_families, n_init=n_init, rng_seed=rng_seed)
        metrics_pam = clustering_metrics(D, km_result.labels, km_result.medoids, true_labels)
        logger.info(
            "  PAM: sil=%.3f Dunn=%.3f DB=%.3f ARI=%.3f NMI=%.3f",
            metrics_pam["silhouette"],
            metrics_pam["dunn"],
            metrics_pam["davies_bouldin"],
            metrics_pam["ari"],
            metrics_pam["nmi"],
        )

        # 2c. k=1 degenerate medoid.
        km1 = run_kmedoids(D, k=1, n_init=1, rng_seed=rng_seed)
        medoid_k1_idx = int(km1.medoids[0])
        medoid_k1_family = int(true_labels[medoid_k1_idx])
        logger.info("  Medoid (k=1): point %d, family %d", medoid_k1_idx, medoid_k1_family)

        # 2d. Dendrogram.
        dend = run_dendrogram(D, k=n_families, linkage_method=linkage_method)
        dendrograms[dist_name] = dend
        logger.info(
            "  Dendro: coph=%.3f sil@k=%.3f",
            dend.cophenetic,
            dend.silhouette_at_k,
        )

        # Per-representation dendrogram figure.
        try:
            import matplotlib

            matplotlib.use("Agg")
            fig_d = plot_dendrogram_figure(
                dend.linkage_matrix, true_labels_list, repr_label, corpus_label, n_families
            )
            _save_figure(fig_d, figures_dir / f"dendrogram_{dist_name}.pdf")
            fig_d.clf()
        except Exception as exc:
            logger.warning("  dendrogram figure failed for %s: %s", dist_name, exc)

        # Row record.
        row: dict[str, Any] = {
            "corpus": corpus_label,
            "representation": repr_label,
            "n_points": int(n),
            "k": int(n_families),
            "linkage_method": linkage_method,
            **{"silhouette_pam": metrics_pam["silhouette"]},
            "dunn": metrics_pam["dunn"],
            "davies_bouldin": metrics_pam["davies_bouldin"],
            "ari": metrics_pam["ari"],
            "nmi": metrics_pam["nmi"],
            "silhouette_dendro": dend.silhouette_at_k,
            "cophenetic": dend.cophenetic,
            "medoid_k1_family": medoid_k1_family,
            # Detailed raw results for JSON (not CSV).
            "pam_loss": km_result.loss,
            "pam_medoids": km_result.medoids.tolist(),
            "pam_best_seed": km_result.best_seed,
        }
        rows.append(row)

    # 3. Write table.
    table_csv = output_root / f"clustering_table_{corpus_label}.csv"
    table_json = output_root / f"clustering_table_{corpus_label}.json"
    _write_clustering_table(rows, table_csv, table_json)

    # 4. Figures.
    try:
        import matplotlib

        matplotlib.use("Agg")
        fig_comb = plot_combined_dendrogram(dendrograms, corpus_label, n_families)
        _save_figure(fig_comb, figures_dir / "dendrogram_combined.pdf")
        fig_comb.clf()

        fig_bar = plot_metric_comparison(rows, corpus_label)
        _save_figure(fig_bar, figures_dir / "metric_comparison.pdf")
        fig_bar.clf()
    except Exception as exc:
        logger.warning("  summary figures failed: %s", exc)

    return rows


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Run the A2 clustering pipeline from the command line.

    Usage
    -----
    python -m experiments.article.analysis.clustering \\
        --output-root /media/.../results/T-M5c/ \\
        --d-matrix-root /media/.../results/T-M5b/ \\
        --corpus planted_main
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )

    parser = argparse.ArgumentParser(description="T-M5c: A2 clustering + dendrogram.")
    parser.add_argument(
        "--output-root",
        required=True,
        type=Path,
        help="Root output directory for T-M5c results.",
    )
    parser.add_argument(
        "--d-matrix-root",
        required=True,
        type=Path,
        help="Root of T-M5b D-matrix cache (contains d_matrix/ subdirectory).",
    )
    parser.add_argument(
        "--corpus",
        required=True,
        choices=list(CORPUS_CONFIGS),
        help="Corpus label.",
    )
    parser.add_argument(
        "--linkage",
        default="average",
        choices=["average", "single", "complete"],
        help="Agglomerative linkage method.  Default: average.",
    )
    parser.add_argument(
        "--n-init",
        type=int,
        default=10,
        help="FasterPAM restarts.  Default: 10.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Base RNG seed.  Default: 42.",
    )
    args = parser.parse_args(argv)

    corpus_label: str = args.corpus
    corpus_cfg = CORPUS_CONFIGS[corpus_label]
    distance_names = MAIN_DISTANCES if corpus_label == "planted_main" else SMALL_DISTANCES

    rows = run_clustering_pipeline(
        output_root=args.output_root,
        d_matrix_root=args.d_matrix_root,
        corpus_label=corpus_label,
        corpus_cfg=corpus_cfg,
        distance_names=distance_names,
        linkage_method=args.linkage,
        n_init=args.n_init,
        rng_seed=args.seed,
    )

    # Print the metric table to stdout for quick inspection.
    print(f"\n=== A2 clustering results: {corpus_label} ===")
    header = (
        f"{'Representation':<14} {'Sil':>6} {'Dunn':>7} {'DB':>7} {'ARI':>6} {'NMI':>6} {'Coph':>6}"
    )
    print(header)
    print("-" * len(header))
    for r in rows:
        dunn_str = (
            f"{r['dunn']:7.3f}"
            if not (isinstance(r["dunn"], float) and r["dunn"] == float("inf"))
            else "    inf"
        )
        print(
            f"{r['representation']:<14}"
            f" {r['silhouette_pam']:6.3f}"
            f" {dunn_str}"
            f" {r['davies_bouldin']:7.3f}"
            f" {r['ari']:6.3f}"
            f" {r['nmi']:6.3f}"
            f" {r['cophenetic']:6.3f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
