"""HIC OD6 secondary exhibit — A1/A2/A3 on IMDB genre datasets (T-M5j).

Runs MDS + geometry table (A1), k-medoids clustering (A2), and kNN
classification (A3) on 6 real HIC IMDB-genre datasets with a w*_c DNF-filter
applied per instance (fork + terminate pattern; 5 s budget). Results are cached
idempotently under the T-M5j results root.

**Why a separate driver (not run_mds_pipeline / run_clustering_pipeline /
run_knn_pipeline from the planted pipelines)?** Those three high-level pipeline
functions are wired to PlantedFamilyDataset — they load the corpus from a config
dict internally and use the planted_families D-cache path layout.  For HIC we
supply pre-filtered hypergraphs directly, so we call the lower-level functions
(``compute_and_cache_d_matrix``, ``cv_dimension_selection``,
``geometry_table_row``, ``run_kmedoids``, ``run_dendrogram``,
``clustering_metrics``, ``run_knn_cv``, ``stratified_fold_indices``) by import.
No new src/ code.

Usage
-----
    python -m experiments.article.analysis.hic_od6 \\
        --hic-root /media/.../data/HIC/data/hypergraph \\
        --output-root /media/.../results/T-M5j

Results land under::

    {output_root}/d_matrix/{hic_name}/{dist_name}/D.npy
    {output_root}/d_matrix/{hic_name}/{dist_name}/meta.json
    {output_root}/censoring_table.csv
    {output_root}/geometry_table_{hic_name}.csv
    {output_root}/clustering_table_{hic_name}.csv
    {output_root}/knn_table_{hic_name}.csv
    {output_root}/figures/{hic_name}/...
    {output_root}/agreement_summary.json
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import json
import logging
import multiprocessing as mp
import os
import tempfile
import time
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HIC_ROOT_DEFAULT = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/data/HIC/data/hypergraph")
RESULTS_ROOT_DEFAULT = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/T-M5j")

#: The 6 IMDB genre datasets for OD6.
IMDB_DATASETS: list[str] = [
    "IMDB-Wri-Genre",
    "IMDB-Dir-Genre",
    "IMDB-Wri-Genre-M",
    "IMDB-Dir-Genre-M",
    "IMDB-Wri-Form",
    "IMDB-Dir-Form",
]

#: Maximum edge arity allowed (D-CONN1 + OD6 scope).
ARITY_CAP: int = 10

#: Per-instance w*_c timeout in seconds.
WSTAR_BUDGET: float = 5.0

#: Main representation set (mirrors T-M5b MAIN_DISTANCES).
MAIN_DISTANCES: list[str] = [
    "isalhg_levenshtein",
    "hypergraph_wl_l1",
    "netlsd_l2",
    "hpd_jsd",
    "nauty_levi_edit",
]

#: Display labels (mirrors T-M5b REPR_LABELS).
REPR_LABELS: dict[str, str] = {
    "isalhg_levenshtein": "IsalHG",
    "hypergraph_wl_l1": "WL-L1",
    "netlsd_l2": "NetLSD",
    "hpd_jsd": "HPD-JSD",
    "nauty_levi_edit": "NautyEdit",
}

#: HyperCOT scale limit: only run on a stratified subsample of at most this size.
#: We omit HyperCOT from the main HIC run and state the scale limit in the table.
HYPERCOT_MAX_N: int = 40


# ---------------------------------------------------------------------------
# w*_c timeout filter
# ---------------------------------------------------------------------------


def _wstar_worker(H: Any, q: mp.Queue[float]) -> None:  # type: ignore[type-arg]
    """Target for the fork subprocess: compute canonical_fingerprint and enqueue elapsed."""
    from isalhg.core.canonical import canonical_fingerprint

    t0 = time.perf_counter()
    canonical_fingerprint(H)
    q.put(time.perf_counter() - t0)


def wstar_ok(H: Any, budget: float = WSTAR_BUDGET) -> bool:
    """Return True if ``canonical_fingerprint(H)`` completes within ``budget`` seconds.

    Uses ``multiprocessing.get_context("fork")`` so the subprocess inherits the
    loaded SparseHypergraph without serialisation overhead. The C++ tie-complete
    encoder ignores SIGALRM, so ``terminate()`` is the only reliable kill.

    Parameters
    ----------
    H : SparseHypergraph
        Input hypergraph.
    budget : float
        Wall-clock timeout in seconds.  Default 5.0.

    Returns
    -------
    bool
        ``True`` if w*_c completed within ``budget``, ``False`` on DNF.
    """
    ctx = mp.get_context("fork")
    q: mp.Queue[float] = ctx.Queue()  # type: ignore[type-arg]
    p = ctx.Process(target=_wstar_worker, args=(H, q))
    p.start()
    p.join(budget)
    if p.is_alive():
        p.terminate()
        p.join()
        return False
    return not q.empty()


# ---------------------------------------------------------------------------
# Censoring filter
# ---------------------------------------------------------------------------


def apply_censoring_filter(
    hypergraphs: list[Any],
    labels: list[int],
    budget: float = WSTAR_BUDGET,
) -> tuple[list[Any], list[int]]:
    """Filter hypergraphs by w*_c completion within ``budget`` seconds.

    Applies ``wstar_ok`` to each instance; drops DNFs.  The returned lists are
    co-indexed: ``survivors[i]`` and ``sur_labels[i]`` correspond to the same
    original item.

    Parameters
    ----------
    hypergraphs : list[SparseHypergraph]
        Arity-capped instances.
    labels : list[int]
        Integer class labels, same length and order as ``hypergraphs``.
    budget : float
        Per-instance timeout in seconds.

    Returns
    -------
    survivors : list[SparseHypergraph]
        Instances that completed w*_c within ``budget``.
    sur_labels : list[int]
        Labels corresponding to survivors.
    """
    survivors: list[Any] = []
    sur_labels: list[int] = []
    for H, lbl in zip(hypergraphs, labels, strict=True):
        if wstar_ok(H, budget=budget):
            survivors.append(H)
            sur_labels.append(lbl)
    return survivors, sur_labels


# ---------------------------------------------------------------------------
# Yield accounting
# ---------------------------------------------------------------------------


def per_class_yield(all_labels: list[int], sur_labels: list[int]) -> dict[int, float]:
    """Compute per-class survival fraction after censoring.

    Parameters
    ----------
    all_labels : list[int]
        Labels of all arity-capped instances (before w*_c filter).
    sur_labels : list[int]
        Labels of surviving instances (after w*_c filter).

    Returns
    -------
    dict[int, float]
        Class → fraction (survivors / total) for every class present in
        ``all_labels``.  Classes with zero survivors have yield 0.0.
    """
    total = Counter(all_labels)
    survived = Counter(sur_labels)
    return {cls: survived.get(cls, 0) / count for cls, count in total.items()}


def make_censoring_table_row(
    hic_name: str,
    n_items: int,
    n_arity_capped: int,
    n_survivors: int,
    per_class_yield_map: dict[int, float],
) -> dict[str, Any]:
    """Construct one row of the OD6 censoring table.

    Parameters
    ----------
    hic_name : str
        Dataset name (e.g. ``"IMDB-Wri-Genre"``).
    n_items : int
        Total items in the dataset.
    n_arity_capped : int
        Items with max edge arity ≤ 10.
    n_survivors : int
        Items that pass the w*_c timeout filter.
    per_class_yield_map : dict[int, float]
        Per-class survival fraction from ``per_class_yield``.

    Returns
    -------
    dict
        Row with keys: hic_name, n_items, n_arity_capped, n_survivors,
        wstar_yield, per_class.
    """
    wstar_yield = n_survivors / n_arity_capped if n_arity_capped > 0 else 0.0
    return {
        "hic_name": hic_name,
        "n_items": n_items,
        "n_arity_capped": n_arity_capped,
        "n_survivors": n_survivors,
        "wstar_yield": wstar_yield,
        "per_class": per_class_yield_map,
    }


# ---------------------------------------------------------------------------
# Stratified subsample (for HyperCOT scale-limited run)
# ---------------------------------------------------------------------------


def stratified_subsample(
    hypergraphs: list[Any],
    labels: list[int],
    max_n: int = HYPERCOT_MAX_N,
    rng_seed: int = 42,
) -> tuple[list[Any], list[int]]:
    """Return a stratified subsample of at most ``max_n`` items.

    Attempts to draw roughly equal counts from each class; class counts are
    clipped so the total does not exceed ``max_n``.

    Parameters
    ----------
    hypergraphs : list
        Full list of hypergraphs.
    labels : list[int]
        Corresponding integer labels, same length.
    max_n : int
        Maximum number of items in the subsample.
    rng_seed : int
        Random seed for reproducibility.

    Returns
    -------
    sub_hgs : list
        Subsampled hypergraphs.
    sub_labels : list[int]
        Corresponding labels.
    """
    rng = np.random.default_rng(rng_seed)
    n = len(hypergraphs)
    if n <= max_n:
        return list(hypergraphs), list(labels)

    classes = sorted(set(labels))
    n_classes = len(classes)
    per_class = max(1, max_n // n_classes)

    # Build per-class index lists.
    class_indices: dict[int, list[int]] = {c: [] for c in classes}
    for i, lbl in enumerate(labels):
        class_indices[lbl].append(i)

    selected: list[int] = []
    for cls in classes:
        idx = class_indices[cls]
        rng.shuffle(idx)  # type: ignore[arg-type]
        selected.extend(idx[:per_class])

    # Shuffle the combined selection for row-order randomness.
    selected_arr = np.array(selected)
    rng.shuffle(selected_arr)
    selected_arr = selected_arr[:max_n]

    sub_hgs = [hypergraphs[i] for i in selected_arr]
    sub_labels = [labels[i] for i in selected_arr]
    return sub_hgs, sub_labels


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------


def _atomic_write_npy(path: Path, arr: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp.npy")
    try:
        os.close(fd)
        np.save(tmp, arr)
        os.replace(tmp, path)
    except Exception:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def _atomic_write_json(path: Path, data: dict[str, Any]) -> None:
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


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# D-matrix helpers
# ---------------------------------------------------------------------------


def _d_matrix_is_done(dist_dir: Path) -> bool:
    meta = dist_dir / "meta.json"
    d_npy = dist_dir / "D.npy"
    if not (meta.exists() and d_npy.exists()):
        return False
    with contextlib.suppress(Exception):
        with meta.open() as f:
            m = json.load(f)
        return m.get("status") == "done"
    return False


def compute_hic_d_matrix(
    hypergraphs: list[Any],
    dist_name: str,
    cell_output_dir: Path,
    corpus_meta: dict[str, Any],
) -> np.ndarray:
    """Compute (or load cached) D matrix for a HIC subset.

    Output mirrors the runner-compatible layout used by mds.py::

        {cell_output_dir}/{dist_name}/D.npy
        {cell_output_dir}/{dist_name}/meta.json

    Parameters
    ----------
    hypergraphs : list[SparseHypergraph]
        Filtered, surviving instances.
    dist_name : str
        Registered distance name.
    cell_output_dir : Path
        Per-dataset cache root (``{results_root}/d_matrix/{hic_name}/``).
    corpus_meta : dict
        Metadata written to meta.json (dataset name, n_survivors, etc.).

    Returns
    -------
    numpy.ndarray
        Symmetric (n, n) distance matrix.
    """
    from isalhg.metric_space.registry import get_distance

    dist_dir = cell_output_dir / dist_name
    d_npy = dist_dir / "D.npy"

    if _d_matrix_is_done(dist_dir):
        logger.info("    %s: cached (loading from disk)", dist_name)
        return np.load(str(d_npy))

    dist = get_distance(dist_name)
    logger.info("    computing %s on %d instances ...", dist_name, len(hypergraphs))
    t0 = time.perf_counter()
    D: np.ndarray = dist.matrix(hypergraphs)
    elapsed = time.perf_counter() - t0
    logger.info("    %s done in %.1fs", dist_name, elapsed)

    meta: dict[str, Any] = {
        "status": "done",
        "distance": dist_name,
        "shape": list(D.shape),
        "wall_clock_s": elapsed,
    }
    meta.update(corpus_meta)

    _atomic_write_npy(d_npy, D)
    _atomic_write_json(dist_dir / "meta.json", meta)
    return D


# ---------------------------------------------------------------------------
# Per-dataset pipeline
# ---------------------------------------------------------------------------


def run_hic_dataset(
    hic_name: str,
    hic_root: Path,
    results_root: Path,
    distance_names: list[str] | None = None,
    wstar_budget: float = WSTAR_BUDGET,
    arity_cap: int = ARITY_CAP,
    knn_k_values: list[int] | None = None,
    knn_n_folds: int = 5,
    knn_rng_seed: int = 42,
) -> dict[str, Any]:
    """Run A1/A2/A3 on one HIC IMDB dataset with w*_c censoring.

    Parameters
    ----------
    hic_name : str
        Dataset name (e.g. ``"IMDB-Wri-Genre"``).
    hic_root : Path
        HIC data root (``{...}/HIC/data/hypergraph``).
    results_root : Path
        T-M5j results root; D matrices and tables are written under here.
    distance_names : list[str] or None
        Representations to evaluate.  Defaults to ``MAIN_DISTANCES``.
    wstar_budget : float
        Per-instance w*_c timeout.  Default 5.0 s.
    arity_cap : int
        Maximum edge arity allowed.  Default 10.
    knn_k_values : list[int] or None
        k values for kNN sweep.  Defaults to ``[1, 3, 5, 7, 9]``.
    knn_n_folds : int
        Stratified CV folds for kNN.  Default 5.
    knn_rng_seed : int
        RNG seed for kNN CV.  Default 42.

    Returns
    -------
    dict
        Summary dict with keys: censoring_row, geometry_rows, clustering_rows,
        knn_rows.
    """
    from isalhg.datasets.hic_atlas import HICAtlasDataset

    if distance_names is None:
        distance_names = MAIN_DISTANCES
    if knn_k_values is None:
        knn_k_values = [1, 3, 5, 7, 9]

    logger.info("=== HIC OD6: %s ===", hic_name)

    # ----------------------------------------------------------------
    # 1. Load dataset
    # ----------------------------------------------------------------
    t0 = time.perf_counter()
    ds = HICAtlasDataset(root=hic_root, hic_name=hic_name)
    all_items = list(ds)
    n_total = len(all_items)
    logger.info("  loaded %d items in %.1fs", n_total, time.perf_counter() - t0)

    # ----------------------------------------------------------------
    # 2. Arity cap
    # ----------------------------------------------------------------
    def _arity(H: Any) -> int:
        return max((len(H.members(e)) for e in H.edges()), default=0)

    capped = [
        (it.hypergraph, int(it.extra.get("class_label", 0)))
        for it in all_items
        if _arity(it.hypergraph) <= arity_cap
    ]
    n_capped = len(capped)
    capped_hgs = [h for h, _ in capped]
    capped_labels_raw = [lbl for _, lbl in capped]
    logger.info("  arity<=10 subset: %d/%d", n_capped, n_total)

    # ----------------------------------------------------------------
    # 3. w*_c censoring filter (with survivor-index cache for reruns)
    # ----------------------------------------------------------------
    cache_dir = results_root / "d_matrix" / hic_name
    cache_dir.mkdir(parents=True, exist_ok=True)
    survivor_cache = cache_dir / "survivor_indices.json"

    if survivor_cache.exists():
        with survivor_cache.open() as _f:
            _cache = json.load(_f)
        if _cache.get("n_capped") == n_capped and _cache.get("wstar_budget_s") == wstar_budget:
            survivor_indices: list[int] = _cache["survivor_indices"]
            survivors = [capped_hgs[i] for i in survivor_indices]
            sur_labels_raw = [capped_labels_raw[i] for i in survivor_indices]
            n_surv = len(survivors)
            logger.info("  w*_c filter: loaded %d survivors from cache.", n_surv)
        else:
            survivor_cache.unlink()
            survivor_indices = []

    if not survivor_cache.exists():
        logger.info("  applying w*_c filter (budget=%.1fs) on %d items...", wstar_budget, n_capped)
        t_filt = time.perf_counter()
        survivors = []
        sur_labels_raw = []
        survivor_indices = []
        for i, (H, lbl) in enumerate(zip(capped_hgs, capped_labels_raw, strict=True)):
            if wstar_ok(H, budget=wstar_budget):
                survivors.append(H)
                sur_labels_raw.append(lbl)
                survivor_indices.append(i)
            if (i + 1) % 50 == 0:
                logger.info("    filtered %d/%d ...", i + 1, n_capped)
        t_filt_elapsed = time.perf_counter() - t_filt
        n_surv = len(survivors)
        logger.info("  survivors: %d/%d in %.1fs", n_surv, n_capped, t_filt_elapsed)
        _atomic_write_json(
            survivor_cache,
            {
                "n_capped": n_capped,
                "wstar_budget_s": wstar_budget,
                "survivor_indices": survivor_indices,
                "n_survivors": n_surv,
                "wall_clock_s": t_filt_elapsed,
            },
        )

    # Record per-class yield.
    class_yield = per_class_yield(capped_labels_raw, sur_labels_raw)
    censoring_row = make_censoring_table_row(
        hic_name=hic_name,
        n_items=n_total,
        n_arity_capped=n_capped,
        n_survivors=n_surv,
        per_class_yield_map=class_yield,
    )

    if n_surv == 0:
        logger.warning("  %s: ALL instances DNF — skipping A1/A2/A3.", hic_name)
        return {
            "censoring_row": censoring_row,
            "geometry_rows": [],
            "clustering_rows": [],
            "knn_rows": [],
        }

    # ----------------------------------------------------------------
    # 4. Remap labels to 0-indexed contiguous integers
    # ----------------------------------------------------------------
    unique_classes = sorted(set(sur_labels_raw))
    n_classes = len(unique_classes)
    cls_map = {c: i for i, c in enumerate(unique_classes)}
    sur_labels = [cls_map[lbl] for lbl in sur_labels_raw]
    k_clust = n_classes  # k-medoids uses the number of genre classes

    logger.info("  n_survivors=%d, n_classes=%d, k_clust=%d", n_surv, n_classes, k_clust)

    # Warn when only one class survived (all metrics will be degenerate).
    if n_classes < 2:
        logger.warning(
            "  %s: only %d class survived censoring; ARI/NMI/AUC undefined.", hic_name, n_classes
        )

    # ----------------------------------------------------------------
    # 5. D-matrix computation and A1/A2/A3 per representation
    # ----------------------------------------------------------------
    cell_output_dir = results_root / "d_matrix" / hic_name
    corpus_meta = {
        "hic_name": hic_name,
        "n_survivors": n_surv,
        "wstar_budget_s": wstar_budget,
        "arity_cap": arity_cap,
    }

    figures_dir = results_root / "figures" / hic_name
    figures_dir.mkdir(parents=True, exist_ok=True)

    geometry_rows: list[dict[str, Any]] = []
    clustering_rows: list[dict[str, Any]] = []
    knn_rows: list[dict[str, Any]] = []

    # Pre-compute shared fold indices for kNN (same folds for all representations).
    from experiments.article.analysis.knn import stratified_fold_indices

    if n_surv <= 50:
        # LOO for small datasets.
        from experiments.article.analysis.knn import loo_fold_indices

        fold_indices = loo_fold_indices(n_surv)
        cv_desc = f"LOO (n={n_surv})"
    else:
        fold_indices = stratified_fold_indices(
            np.array(sur_labels), n_folds=knn_n_folds, rng_seed=knn_rng_seed
        )
        cv_desc = f"StratifiedKFold(n_splits={knn_n_folds}, seed={knn_rng_seed})"
    logger.info("  kNN CV strategy: %s", cv_desc)

    for dist_name in distance_names:
        repr_label = REPR_LABELS.get(dist_name, dist_name)
        logger.info("  --- %s (%s) ---", dist_name, repr_label)

        try:
            D = compute_hic_d_matrix(survivors, dist_name, cell_output_dir, corpus_meta)
        except Exception as exc:
            logger.warning("    %s FAILED: %s; skipping.", dist_name, exc)
            continue

        # A1: CV D̂ + geometry table row.
        try:
            from experiments.article.analysis.mds import (
                cv_dimension_selection,
                geometry_table_row,
                mardia_ratios,
                negative_eigenvalue_floor,
            )
            from isalhg.metric_space.metrics.embedding import classical_mds

            d_hat, cv_errors = cv_dimension_selection(D)
            eigenvalues, _ = classical_mds(D)
            p1, p2 = mardia_ratios(eigenvalues)
            neg_floor = negative_eigenvalue_floor(eigenvalues)

            row = geometry_table_row(
                corpus_name=hic_name,
                representation_name=repr_label,
                D=D,
                d_hat=d_hat,
            )
            row["mardia_p1"] = float(p1)
            row["mardia_p2"] = float(p2)
            row["neg_eigenvalue_floor"] = int(neg_floor)
            geometry_rows.append(row)
            logger.info(
                "    A1: D̂=%d  ν=%.3f  stress=%.3f  hub_skew=%.3f",
                d_hat,
                row["nu"],
                row["stress_at_d_hat"],
                row["hubness_skewness"],
            )
        except Exception as exc:
            logger.warning("    A1 failed for %s: %s", dist_name, exc)

        # A2: clustering.
        if n_classes >= 2:
            try:
                from experiments.article.analysis.clustering import (
                    clustering_metrics,
                    run_dendrogram,
                    run_kmedoids,
                )

                km = run_kmedoids(D, k=k_clust)
                dend = run_dendrogram(D, k=k_clust)
                true_labels_arr = np.array(sur_labels, dtype=np.intp)
                metrics_pam = clustering_metrics(D, km.labels, km.medoids, true_labels_arr)

                clust_row: dict[str, Any] = {
                    "hic_name": hic_name,
                    "representation": repr_label,
                    "n_points": n_surv,
                    "n_classes": n_classes,
                    **{f"pam_{k}": v for k, v in metrics_pam.items()},
                    "cophenetic": float(dend.cophenetic),
                    "dend_silhouette_at_k": float(dend.silhouette_at_k),
                }
                clustering_rows.append(clust_row)
                logger.info(
                    "    A2: ARI=%.3f  NMI=%.3f  sil=%.3f  cophenetic=%.3f",
                    metrics_pam["ari"],
                    metrics_pam["nmi"],
                    metrics_pam["silhouette"],
                    dend.cophenetic,
                )
            except Exception as exc:
                logger.warning("    A2 failed for %s: %s", dist_name, exc)

        # A3: kNN.
        if n_classes >= 2:
            try:
                from experiments.article.analysis.knn import run_knn_cv

                labels_arr = np.array(sur_labels, dtype=np.intp)
                # Clamp k values to at most n_surv - 1.
                k_vals = [k for k in knn_k_values if k < n_surv]
                if not k_vals:
                    logger.warning("    A3: no valid k values for n=%d", n_surv)
                else:
                    knn_results = run_knn_cv(D, labels_arr, k_vals, fold_indices, n_classes)
                    for res in knn_results:
                        knn_rows.append(
                            {
                                "hic_name": hic_name,
                                "representation": repr_label,
                                **res,
                            }
                        )
                    best = max(knn_results, key=lambda r: r["accuracy"])
                    logger.info(
                        "    A3: best acc=%.3f  F1=%.3f  AUC=%.3f at k=%d",
                        best["accuracy"],
                        best["macro_f1"],
                        best["auc_ovr"],
                        best["k"],
                    )
            except Exception as exc:
                logger.warning("    A3 failed for %s: %s", dist_name, exc)

        # Figures.
        try:
            _generate_dataset_figures(D, sur_labels, repr_label, hic_name, figures_dir)
        except Exception as exc:
            logger.debug("    figures failed for %s: %s", dist_name, exc)

    # ----------------------------------------------------------------
    # 6. Write per-dataset tables
    # ----------------------------------------------------------------
    ds_output = results_root / "tables"
    ds_output.mkdir(parents=True, exist_ok=True)

    _write_csv(ds_output / f"geometry_table_{hic_name}.csv", geometry_rows)
    _atomic_write_json(
        ds_output / f"geometry_table_{hic_name}.json",
        {"rows": geometry_rows},
    )
    _write_csv(ds_output / f"clustering_table_{hic_name}.csv", clustering_rows)
    _atomic_write_json(
        ds_output / f"clustering_table_{hic_name}.json",
        {"rows": clustering_rows},
    )
    _write_csv(ds_output / f"knn_table_{hic_name}.csv", knn_rows)
    _atomic_write_json(
        ds_output / f"knn_table_{hic_name}.json",
        {"rows": knn_rows},
    )

    return {
        "censoring_row": censoring_row,
        "geometry_rows": geometry_rows,
        "clustering_rows": clustering_rows,
        "knn_rows": knn_rows,
    }


def _generate_dataset_figures(
    D: np.ndarray,
    labels: list[int],
    repr_label: str,
    hic_name: str,
    figures_dir: Path,
) -> None:
    """Generate MDS scatter and Shepard figure for one (dataset, representation)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from experiments.article.analysis.mds import (
        cv_dimension_selection,
        pairwise_l2,
        plot_mds_scatter,
        plot_shepard,
    )
    from isalhg.metric_space.metrics.embedding import (
        classical_mds,
        embed_classical,
        shepard_data,
    )

    d_hat, _ = cv_dimension_selection(D)
    X = embed_classical(D, n_dims=min(d_hat, D.shape[0] - 1))

    fig = plot_mds_scatter(X, labels, repr_label, hic_name, d_hat)
    path = figures_dir / f"mds_scatter_{repr_label.replace(' ', '_')}.pdf"
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(path), dpi=150, bbox_inches="tight")
    plt.close(fig)

    # Shepard diagram.
    eigenvalues, _ = classical_mds(D)
    D_embed = pairwise_l2(X)
    d_orig_tri, d_embed_tri = shepard_data(D, D_embed)
    fig2 = plot_shepard(d_orig_tri, d_embed_tri, repr_label, d_hat)
    path2 = figures_dir / f"shepard_{repr_label.replace(' ', '_')}.pdf"
    fig2.savefig(str(path2), dpi=150, bbox_inches="tight")
    plt.close(fig2)


# ---------------------------------------------------------------------------
# Agreement check vs planted findings
# ---------------------------------------------------------------------------

_PLANTED_ORDERING: dict[str, list[str]] = {
    # From T-M5c/d closing notes: HPD-JSD leads A2/A3 on planted corpus;
    # IsalHG mid-pack; WL degraded by hubness; NautyEdit weak.
    "ari_nmi": ["HPD-JSD", "NetLSD", "IsalHG", "WL-L1", "NautyEdit"],
    "acc_f1": ["HPD-JSD", "NetLSD", "IsalHG", "WL-L1", "NautyEdit"],
}


def compute_agreement_summary(
    all_clustering_rows: list[dict[str, Any]],
    all_knn_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute fallback-vs-HIC ordering agreement.

    Checks whether the across-representation ARI/NMI/AUC orderings on real HIC
    data agree with the planted findings (HPD-JSD leads; IsalHG mid-pack; WL
    degraded; NautyEdit weak).  OD6's acceptance test: does censoring flip any
    conclusion?

    Parameters
    ----------
    all_clustering_rows : list[dict]
        Clustering table rows from all datasets combined.
    all_knn_rows : list[dict]
        kNN table rows from all datasets combined.

    Returns
    -------
    dict
        Contains 'ari_order', 'acc_order', 'agreement_notes', 'conclusion'.
    """
    # Aggregate ARI/NMI per representation across datasets.
    ari_by_repr: dict[str, list[float]] = {}
    nmi_by_repr: dict[str, list[float]] = {}
    for row in all_clustering_rows:
        r = row["representation"]
        ari = row.get("pam_ari", float("nan"))
        nmi = row.get("pam_nmi", float("nan"))
        ari_by_repr.setdefault(r, []).append(ari)
        nmi_by_repr.setdefault(r, []).append(nmi)

    ari_mean = {r: float(np.nanmean(v)) for r, v in ari_by_repr.items()}
    nmi_mean = {r: float(np.nanmean(v)) for r, v in nmi_by_repr.items()}

    ari_order = sorted(ari_mean, key=lambda r: ari_mean[r], reverse=True)
    nmi_order = sorted(nmi_mean, key=lambda r: nmi_mean[r], reverse=True)

    # Aggregate best-k accuracy per representation.
    acc_by_repr: dict[str, list[float]] = {}
    for row in all_knn_rows:
        r = row["representation"]
        acc = row.get("accuracy", float("nan"))
        acc_by_repr.setdefault(r, []).append(acc)

    # Only keep peak accuracy per repr (per dataset).
    peak_acc: dict[str, list[float]] = {}
    seen: set[tuple[str, str]] = set()
    for row in all_knn_rows:
        r = row["representation"]
        ds = row["hic_name"]
        acc = row.get("accuracy", float("nan"))
        key = (r, ds)
        if key not in seen or acc > peak_acc.get(r, [float("-inf")])[0]:
            peak_acc.setdefault(r, []).append(acc)
        seen.add(key)

    peak_mean = {r: float(np.nanmean(v)) for r, v in peak_acc.items()}
    acc_order = sorted(peak_mean, key=lambda r: peak_mean[r], reverse=True)

    # Agreement notes.
    planted_top_a2 = "HPD-JSD"
    planted_top_a3 = "HPD-JSD"
    notes: list[str] = []

    if ari_order and ari_order[0] == planted_top_a2:
        notes.append(f"ARI ordering agrees: {planted_top_a2} leads on HIC (as in planted).")
    elif ari_order:
        notes.append(
            f"ARI ordering differs: {ari_order[0]} leads on HIC vs {planted_top_a2} in planted."
        )

    if acc_order and acc_order[0] == planted_top_a3:
        notes.append(f"kNN acc ordering agrees: {planted_top_a3} leads on HIC (as in planted).")
    elif acc_order:
        notes.append(
            f"kNN acc ordering differs: {acc_order[0]} leads on HIC vs {planted_top_a3} in planted."
        )

    # IsalHG position.
    if "IsalHG" in ari_order:
        pos = ari_order.index("IsalHG") + 1
        notes.append(f"IsalHG position in ARI order: {pos}/{len(ari_order)} (planted: mid-pack).")

    # Conclusion: does censoring flip any conclusion?
    flipped = any("differs" in n for n in notes)
    if flipped:
        conclusion = (
            "HIC orderings differ from planted in at least one metric. "
            "Censoring may correlate with label-class difficulty. "
            "Report per-class yield table and interpret with caution."
        )
    else:
        conclusion = (
            "HIC orderings broadly agree with planted findings. "
            "Censoring does not appear to flip the across-representation conclusions."
        )

    return {
        "ari_order": ari_order,
        "nmi_order": nmi_order,
        "acc_order": acc_order,
        "ari_mean": ari_mean,
        "nmi_mean": nmi_mean,
        "acc_mean_peak": peak_mean,
        "agreement_notes": notes,
        "conclusion": conclusion,
    }


# ---------------------------------------------------------------------------
# Full pipeline driver
# ---------------------------------------------------------------------------


def run_full_pipeline(
    hic_root: Path = HIC_ROOT_DEFAULT,
    results_root: Path = RESULTS_ROOT_DEFAULT,
    datasets: list[str] | None = None,
    distance_names: list[str] | None = None,
    wstar_budget: float = WSTAR_BUDGET,
) -> None:
    """Run the HIC OD6 exhibit pipeline across all 6 IMDB datasets.

    Parameters
    ----------
    hic_root : Path
        HIC data root directory.
    results_root : Path
        Output root for T-M5j results.
    datasets : list[str] or None
        Dataset names to process.  Defaults to ``IMDB_DATASETS``.
    distance_names : list[str] or None
        Representations to evaluate.  Defaults to ``MAIN_DISTANCES``.
    wstar_budget : float
        Per-instance w*_c timeout.
    """
    if datasets is None:
        datasets = IMDB_DATASETS
    if distance_names is None:
        distance_names = MAIN_DISTANCES

    results_root.mkdir(parents=True, exist_ok=True)

    all_censoring: list[dict[str, Any]] = []
    all_clustering: list[dict[str, Any]] = []
    all_knn: list[dict[str, Any]] = []

    for hic_name in datasets:
        summary = run_hic_dataset(
            hic_name=hic_name,
            hic_root=hic_root,
            results_root=results_root,
            distance_names=distance_names,
            wstar_budget=wstar_budget,
        )
        all_censoring.append(summary["censoring_row"])
        all_clustering.extend(summary["clustering_rows"])
        all_knn.extend(summary["knn_rows"])

    # Write combined censoring table.
    tables_dir = results_root / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(tables_dir / "censoring_table.csv", all_censoring)
    _atomic_write_json(tables_dir / "censoring_table.json", {"rows": all_censoring})

    # Agreement summary.
    agreement = compute_agreement_summary(all_clustering, all_knn)
    _atomic_write_json(tables_dir / "agreement_summary.json", agreement)

    # Print censoring table to stdout.
    print("\n=== OD6 Censoring Table ===")
    header = f"{'Dataset':<22} {'N_total':>8} {'Arity≤10':>9} {'Survivors':>10} {'Yield%':>7}"
    print(header)
    print("-" * len(header))
    for row in all_censoring:
        print(
            f"{row['hic_name']:<22} {row['n_items']:>8d} {row['n_arity_capped']:>9d} "
            f"{row['n_survivors']:>10d} {100 * row['wstar_yield']:>6.1f}%"
        )
        per_cls_str = ", ".join(
            f"{cls}:{100 * frac:.0f}%" for cls, frac in sorted(row["per_class"].items())
        )
        print(f"  per-class: {per_cls_str}")

    print("\n=== Fallback-vs-HIC Agreement ===")
    for note in agreement["agreement_notes"]:
        print(f"  {note}")
    print(f"  Conclusion: {agreement['conclusion']}")

    print(f"\nResults written to: {results_root}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="HIC OD6 real-data exhibit: A1/A2/A3 on IMDB genre datasets (T-M5j)."
    )
    p.add_argument("--hic-root", type=Path, default=HIC_ROOT_DEFAULT)
    p.add_argument("--output-root", type=Path, default=RESULTS_ROOT_DEFAULT)
    p.add_argument(
        "--datasets",
        nargs="+",
        default=IMDB_DATASETS,
        help="HIC dataset names to process (default: all 6 IMDB genre variants).",
    )
    p.add_argument(
        "--distances",
        nargs="+",
        default=MAIN_DISTANCES,
        help="Distance representations to evaluate.",
    )
    p.add_argument(
        "--wstar-budget",
        type=float,
        default=WSTAR_BUDGET,
        help="Per-instance w*_c timeout in seconds (default: 5.0).",
    )
    p.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    run_full_pipeline(
        hic_root=args.hic_root,
        results_root=args.output_root,
        datasets=args.datasets,
        distance_names=args.distances,
        wstar_budget=args.wstar_budget,
    )
