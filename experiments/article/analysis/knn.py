"""kNN classification (A3) — T-M5d.

Implements A3: kNN in (·, d_I) and competitor metrics, leave-one-out /
stratified CV, reporting accuracy / macro-F1 / AUC-OvR vs k.
Scores are interpreted against the G1 concentration + hubness profile from
T-M5b's geometry table (printed alongside).

Acceptance criteria
-------------------
1. load_labels_from_corpus() returns labels in the same row order as D.npy
   (same PlantedFamilyDataset params + seed_value).
2. loo_fold_indices(n) returns n folds; every (train_idx, test_idx) pair is
   disjoint and covers {0..n-1}.
3. stratified_fold_indices uses StratifiedKFold; same seed → same folds.
4. run_knn_cv uses sklearn KNeighborsClassifier(metric='precomputed');
   the caller pre-computes fold_indices once so the same folds are shared
   across all representations on the same corpus (fair head-to-head).
5. Metrics: accuracy_score, f1_score(average='macro'),
   roc_auc_score(multi_class='ovr', average='macro').
6. G1 profile loaded from T-M5b geometry table CSV; printed alongside scores.
7. Results written to output_root / knn_scores_{corpus}.{csv,json}.
8. Figures: accuracy, macro-F1, AUC vs k (one curve per representation).
9. HyperCOT reported on planted_small only (N=20) with LOO.
10. No HGED. No HIC.

Boundary (docs/article/CODE_DESIGN.md §9)
------------------------------------------
No new src/ code.  All imports from src/ use installed isalhg.* primitives.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Corpus configurations (mirrored from mds.py / mds_planted.yaml)
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

# Threshold below which LOO is preferred over stratified k-fold.
_LOO_THRESHOLD = 25

# k values to sweep.
K_VALUES_MAIN: list[int] = [1, 3, 5, 7, 9, 11]
K_VALUES_SMALL: list[int] = [1, 3, 5, 7]


# ---------------------------------------------------------------------------
# Cross-validation fold helpers (testable independently)
# ---------------------------------------------------------------------------


def loo_fold_indices(n: int) -> list[tuple[np.ndarray, np.ndarray]]:
    """Leave-one-out fold indices for n points.

    Parameters
    ----------
    n : int
        Number of points.

    Returns
    -------
    list of (train_idx, test_idx)
        n folds; each test_idx is a length-1 array; train_idx has length n-1.
    """
    all_idx = np.arange(n)
    folds: list[tuple[np.ndarray, np.ndarray]] = []
    for i in range(n):
        test = np.array([i])
        train = np.concatenate([all_idx[:i], all_idx[i + 1 :]])
        folds.append((train, test))
    return folds


def stratified_fold_indices(
    labels: np.ndarray,
    n_folds: int = 5,
    rng_seed: int = 42,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Stratified k-fold indices.

    Generates fold assignments once so that, when called with the same
    arguments, every representation on the same corpus uses identical folds
    (fair head-to-head comparison).

    Parameters
    ----------
    labels : numpy.ndarray
        Integer class labels, shape (n,).
    n_folds : int, optional
        Number of folds.  Default 5.
    rng_seed : int, optional
        Random seed for reproducible stratification.  Default 42.

    Returns
    -------
    list of (train_idx, test_idx)
        n_folds folds; disjoint test sets covering all n indices.
    """
    from sklearn.model_selection import StratifiedKFold

    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=rng_seed)
    dummy = np.zeros(len(labels))
    return [(train, test) for train, test in skf.split(dummy, labels)]


# ---------------------------------------------------------------------------
# kNN CV runner
# ---------------------------------------------------------------------------


def run_knn_cv(
    D: np.ndarray,
    labels: np.ndarray,
    k_values: list[int],
    fold_indices: list[tuple[np.ndarray, np.ndarray]],
    n_classes: int,
) -> list[dict[str, float]]:
    """Run kNN CV for each k in k_values on a precomputed distance matrix.

    For each fold, fits KNeighborsClassifier on the train submatrix
    D[np.ix_(train_idx, train_idx)] and predicts on the test block
    D[np.ix_(test_idx, train_idx)].  Probability estimates (vote
    proportions) are accumulated across folds, then accuracy / macro-F1 /
    AUC-OvR are computed over all n points jointly.

    Parameters
    ----------
    D : numpy.ndarray
        Symmetric (n, n) precomputed distance matrix with zero diagonal.
    labels : numpy.ndarray
        Integer class labels, shape (n,), 0-indexed.
    k_values : list of int
        k values to evaluate.
    fold_indices : list of (train_idx, test_idx)
        Pre-computed fold assignments — pass the same list for all
        representations on the same corpus to ensure a fair comparison.
    n_classes : int
        Number of distinct classes.  Used to allocate the probability
        accumulation array; must equal ``len(np.unique(labels))``.

    Returns
    -------
    list of dict
        One dict per k with keys ``{k, accuracy, macro_f1, auc_ovr}``.
    """
    from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
    from sklearn.neighbors import KNeighborsClassifier

    n = len(labels)
    results: list[dict[str, float]] = []

    for k in k_values:
        all_proba = np.zeros((n, n_classes), dtype=float)

        for train_idx, test_idx in fold_indices:
            D_train = D[np.ix_(train_idx, train_idx)]
            D_test = D[np.ix_(test_idx, train_idx)]
            y_train = labels[train_idx]

            knn = KNeighborsClassifier(n_neighbors=k, metric="precomputed")
            knn.fit(D_train, y_train)
            proba = knn.predict_proba(D_test)  # (n_test, n_present_classes)

            # knn.classes_ gives the sorted unique labels seen in y_train.
            # Fill into the full n_classes columns so we don't mix up ordering
            # when some class is absent from a training fold.
            for col_idx, cls in enumerate(knn.classes_):
                all_proba[test_idx, int(cls)] = proba[:, col_idx]

        y_pred = all_proba.argmax(axis=1)
        acc = float(accuracy_score(labels, y_pred))
        f1 = float(f1_score(labels, y_pred, average="macro", zero_division=0))
        try:
            auc = float(roc_auc_score(labels, all_proba, multi_class="ovr", average="macro"))
        except ValueError:
            auc = float("nan")

        results.append({"k": k, "accuracy": acc, "macro_f1": f1, "auc_ovr": auc})

    return results


# ---------------------------------------------------------------------------
# G1 profile loader
# ---------------------------------------------------------------------------


def load_g1_profile(
    geometry_table_csv: Path,
    corpus_label: str,
) -> dict[str, dict[str, float]]:
    """Load G1 concentration + hubness columns from a T-M5b geometry table CSV.

    Parameters
    ----------
    geometry_table_csv : Path
        Path to a ``geometry_table_{corpus}.csv`` produced by mds.py.
    corpus_label : str
        Filter rows to this corpus name (the ``corpus`` column).

    Returns
    -------
    dict
        Mapping representation display name →
        ``{diameter_to_median: float, hubness_skewness: float}``.
    """
    profile: dict[str, dict[str, float]] = {}
    with open(geometry_table_csv, newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if row["corpus"] != corpus_label:
                continue
            profile[row["representation"]] = {
                "diameter_to_median": float(row["diameter_to_median"]),
                "hubness_skewness": float(row["hubness_skewness"]),
            }
    return profile


# ---------------------------------------------------------------------------
# Label loader
# ---------------------------------------------------------------------------


def load_labels_from_corpus(corpus_cfg: dict[str, Any]) -> np.ndarray:
    """Instantiate PlantedFamilyDataset and extract class labels.

    The iteration order matches the D.npy row order produced by
    experiments/article/analysis/mds.py for the same corpus_cfg.

    Parameters
    ----------
    corpus_cfg : dict
        PlantedFamilyDataset constructor kwargs (same as in mds_planted.yaml).

    Returns
    -------
    numpy.ndarray
        Integer class labels of shape (n,), 0-indexed family ids.
    """
    from isalhg.datasets.synthetic.planted_families import PlantedFamilyDataset

    dataset = PlantedFamilyDataset(**corpus_cfg)
    items = list(dataset)
    return np.array([int(item.extra.get("family_index", 0)) for item in items])


# ---------------------------------------------------------------------------
# D-matrix loader (idempotent — reads cached files from T-M5b)
# ---------------------------------------------------------------------------


def load_d_matrix(
    cache_root: Path,
    corpus_label: str,
    seed_val: int,
    dist_name: str,
) -> np.ndarray:
    """Load a cached D.npy produced by the T-M5b MDS pipeline.

    Parameters
    ----------
    cache_root : Path
        Root output directory (``{output_root}/d_matrix/planted_families/``).
    corpus_label : str
        Corpus label (``"planted_main"`` or ``"planted_small"``).
    seed_val : int
        Seed value used when computing D (printed in meta.json).
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
    d_path = cache_root / corpus_label / f"seed{seed_val}" / dist_name / "D.npy"
    if not d_path.exists():
        raise FileNotFoundError(f"Cached D.npy not found: {d_path}")
    return np.load(d_path)


# ---------------------------------------------------------------------------
# Figure helpers
# ---------------------------------------------------------------------------


def _plot_knn_metric(
    all_results: dict[str, list[dict[str, float]]],
    metric_key: str,
    metric_label: str,
    corpus_label: str,
    g1_profile: dict[str, dict[str, float]],
) -> matplotlib.figure.Figure:  # type: ignore[name-defined]  # noqa: F821
    """Plot one kNN metric (accuracy / macro-F1 / AUC-OvR) vs k.

    Parameters
    ----------
    all_results : dict
        Mapping repr display name → list of run_knn_cv dicts.
    metric_key : str
        Dict key to plot (``"accuracy"``, ``"macro_f1"``, or ``"auc_ovr"``).
    metric_label : str
        Human label for the y-axis.
    corpus_label : str
        Used in the title.
    g1_profile : dict
        G1 profile from load_g1_profile; shown in the legend.
    """
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7, 4))
    for repr_name, rows in all_results.items():
        k_vals = [r["k"] for r in rows]
        metric_vals = [r[metric_key] for r in rows]
        g1 = g1_profile.get(repr_name, {})
        hub = g1.get("hubness_skewness", float("nan"))
        conc = g1.get("diameter_to_median", float("nan"))
        label = f"{repr_name} (hub={hub:.2f}, conc={conc:.2f})"
        ax.plot(k_vals, metric_vals, marker="o", label=label)

    ax.set_xlabel("k")
    ax.set_ylabel(metric_label)
    ax.set_title(f"A3 kNN — {metric_label} ({corpus_label})")
    ax.legend(fontsize=7)
    ax.set_ylim(0.0, 1.05)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


def _save_figure(fig: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight")
    logger.info("  figure saved: %s", path)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def run_knn_pipeline(
    output_root: Path,
    corpus_label: str,
    corpus_cfg: dict[str, Any],
    distance_names: list[str],
    k_values: list[int],
    t5b_root: Path,
    cv_strategy: str = "auto",
    n_folds: int = 5,
    rng_seed: int = 42,
) -> list[dict[str, Any]]:
    """Run the full T-M5d kNN pipeline on one corpus.

    Steps
    -----
    1. Load labels from PlantedFamilyDataset (same order as cached D.npy).
    2. Compute fold indices once (shared across all representations).
    3. For each distance representation: load D.npy (cached), run kNN CV.
    4. Load G1 profile from T-M5b geometry table; print alongside scores.
    5. Write score tables to output_root/knn_scores_{corpus_label}.{csv,json}.
    6. Save figures.

    Parameters
    ----------
    output_root : Path
        Root output directory for T-M5d results (outside the git tree).
    corpus_label : str
        Human label (``"planted_main"`` or ``"planted_small"``).
    corpus_cfg : dict
        PlantedFamilyDataset constructor kwargs.
    distance_names : list of str
        Distance representations to evaluate.
    k_values : list of int
        k values to sweep.
    t5b_root : Path
        Root output directory of the T-M5b MDS pipeline (for D.npy cache and
        geometry table).
    cv_strategy : str, optional
        ``"loo"`` — leave-one-out; ``"stratified"`` — StratifiedKFold;
        ``"auto"`` — LOO if n <= ``_LOO_THRESHOLD``, else stratified.
        Default ``"auto"``.
    n_folds : int, optional
        Number of folds for ``"stratified"`` strategy.  Default 5.
    rng_seed : int, optional
        Random seed (passed to stratified fold assignment).  Default 42.

    Returns
    -------
    list of dict
        Flat list of score rows (one per representation × k combination).
    """
    logger.info("=== A3 kNN pipeline: %s ===", corpus_label)

    # 1. Load labels.
    t0 = time.perf_counter()
    labels = load_labels_from_corpus(corpus_cfg)
    n = len(labels)
    n_classes = int(np.max(labels)) + 1
    seed_val = int(corpus_cfg.get("seed_value", 0))
    logger.info(
        "  labels loaded: N=%d, %d classes in %.2fs", n, n_classes, time.perf_counter() - t0
    )

    # Verify N matches expected corpus size.
    expected_n = int(corpus_cfg["n_families"]) * int(corpus_cfg["members_per_family"])
    if n != expected_n:
        raise ValueError(
            f"N mismatch: loaded {n} labels but expected {expected_n} for corpus '{corpus_label}'"
        )

    # 2. Pre-compute fold indices (shared across all representations).
    effective_strategy = cv_strategy
    if cv_strategy == "auto":
        effective_strategy = "loo" if n <= _LOO_THRESHOLD else "stratified"

    if effective_strategy == "loo":
        fold_indices = loo_fold_indices(n)
        cv_desc = f"LOO (n={n})"
    else:
        fold_indices = stratified_fold_indices(labels, n_folds=n_folds, rng_seed=rng_seed)
        cv_desc = f"StratifiedKFold(n_splits={n_folds}, seed={rng_seed})"
    logger.info("  CV strategy: %s", cv_desc)

    # 3. Load G1 profile.
    g1_csv = t5b_root / f"geometry_table_{corpus_label}.csv"
    if g1_csv.exists():
        g1_profile = load_g1_profile(g1_csv, corpus_label)
        logger.info("  G1 profile loaded for %d representations", len(g1_profile))
    else:
        g1_profile = {}
        logger.warning("  G1 profile CSV not found: %s", g1_csv)

    # 4. D-matrix cache root.
    d_cache_root = t5b_root / "d_matrix" / "planted_families"

    # 5. Per-representation kNN CV.
    all_results: dict[str, list[dict[str, float]]] = {}
    flat_rows: list[dict[str, Any]] = []

    for dist_name in distance_names:
        repr_label = REPR_LABELS.get(dist_name, dist_name)
        logger.info("--- %s (%s) ---", dist_name, repr_label)

        try:
            D = load_d_matrix(d_cache_root, corpus_label, seed_val, dist_name)
        except FileNotFoundError as exc:
            logger.warning("  D.npy missing — skipping: %s", exc)
            continue

        if D.shape != (n, n):
            logger.warning("  D.shape=%s does not match N=%d — skipping.", D.shape, n)
            continue

        t1 = time.perf_counter()
        knn_rows = run_knn_cv(
            D, labels, k_values=k_values, fold_indices=fold_indices, n_classes=n_classes
        )
        logger.info("  kNN CV done in %.2fs", time.perf_counter() - t1)

        all_results[repr_label] = knn_rows

        g1 = g1_profile.get(repr_label, {})
        hub = g1.get("hubness_skewness", float("nan"))
        conc = g1.get("diameter_to_median", float("nan"))

        # Print score table with G1 profile header.
        print(f"\n  [{repr_label}]  G1: hubness_skew={hub:.3f}, conc(diam/med)={conc:.3f}")
        print(f"  {'k':>4}  {'acc':>7}  {'F1':>7}  {'AUC':>7}")
        for row in knn_rows:
            print(
                f"  {row['k']:>4}  {row['accuracy']:>7.4f}  {row['macro_f1']:>7.4f}"
                f"  {row['auc_ovr']:>7.4f}"
            )
        # Interpretation note: high hubness → k-occurrence skew → degraded kNN.
        if not np.isnan(hub) and hub > 1.0:
            print(f"  NOTE: hubness_skew={hub:.3f} > 1 — strong hubness; expect degraded kNN.")
        elif not np.isnan(hub) and hub < 0.2:
            print(f"  NOTE: hubness_skew={hub:.3f} < 0.2 — low hubness; kNN should work well.")

        for row in knn_rows:
            flat_rows.append(
                {
                    "corpus": corpus_label,
                    "representation": repr_label,
                    "dist_name": dist_name,
                    "cv_strategy": cv_desc,
                    "n": n,
                    "n_classes": n_classes,
                    "seed": rng_seed,
                    "hubness_skewness": hub,
                    "diameter_to_median": conc,
                    **row,
                }
            )

    # 6. Write score tables.
    out_dir = output_root
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"knn_scores_{corpus_label}.csv"
    json_path = out_dir / f"knn_scores_{corpus_label}.json"

    if flat_rows:
        with open(csv_path, "w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(flat_rows[0].keys()))
            writer.writeheader()
            writer.writerows(flat_rows)
        with open(json_path, "w") as fh:
            json.dump(flat_rows, fh, indent=2)
        logger.info("  wrote: %s", csv_path)
        logger.info("  wrote: %s", json_path)

    # 7. Figures.
    if all_results:
        fig_dir = output_root / "figures" / corpus_label
        try:
            import matplotlib

            matplotlib.use("Agg")

            for metric_key, metric_label in [
                ("accuracy", "Accuracy"),
                ("macro_f1", "Macro F1"),
                ("auc_ovr", "AUC-OvR (macro)"),
            ]:
                fig = _plot_knn_metric(
                    all_results, metric_key, metric_label, corpus_label, g1_profile
                )
                fname = metric_key.replace("_", "-")
                _save_figure(fig, fig_dir / f"knn_{fname}.pdf")
                fig.clf()
        except Exception as exc:
            logger.warning("  figure generation failed: %s", exc)

    return flat_rows


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="A3 kNN classification pipeline (T-M5d).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "--output-root",
        type=Path,
        required=True,
        help="Root output directory for T-M5d results.",
    )
    p.add_argument(
        "--t5b-root",
        type=Path,
        default=Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/T-M5b"),
        help="T-M5b output root (for cached D.npy and geometry table).",
    )
    p.add_argument(
        "--corpus",
        choices=["planted_main", "planted_small", "all"],
        default="all",
        help="Which corpus to run.",
    )
    p.add_argument(
        "--cv-strategy",
        choices=["auto", "loo", "stratified"],
        default="auto",
        help="CV strategy ('auto' = LOO for N≤25, stratified otherwise).",
    )
    p.add_argument(
        "--n-folds",
        type=int,
        default=5,
        help="Number of folds for stratified CV.",
    )
    p.add_argument(
        "--rng-seed",
        type=int,
        default=42,
        help="Random seed for stratified fold assignment.",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        stream=sys.stdout,
    )
    args = _build_parser().parse_args(argv)

    corpora_to_run = ["planted_main", "planted_small"] if args.corpus == "all" else [args.corpus]

    for corpus_label in corpora_to_run:
        corpus_cfg = CORPUS_CONFIGS[corpus_label]
        distance_names = MAIN_DISTANCES if corpus_label == "planted_main" else SMALL_DISTANCES
        k_values = K_VALUES_MAIN if corpus_label == "planted_main" else K_VALUES_SMALL

        run_knn_pipeline(
            output_root=args.output_root,
            corpus_label=corpus_label,
            corpus_cfg=corpus_cfg,
            distance_names=distance_names,
            k_values=k_values,
            t5b_root=args.t5b_root,
            cv_strategy=args.cv_strategy,
            n_folds=args.n_folds,
            rng_seed=args.rng_seed,
        )


if __name__ == "__main__":
    main()
