"""MDS (A1) pipeline — T-M5b.

Classical Torgerson–Gower + SMACOF MDS on pairwise distance matrices for each
representation (ours + four competitors). Computes and caches D.npy files with the
same layout as runner.run_d_matrix_cell so T-M5c/d/e can reuse them directly.

Deliverables
------------
- Per-representation D.npy caches (idempotent; same layout as the runner).
- CV-selected intrinsic dimension D̂ (primary) + Mardia P^(1)/P^(2) (supporting).
- Geometry table: one row per (corpus, representation) with all T-M5f columns.
- Figures: MDS scatter (classical at D̂), Shepard diagram, stress-vs-D curve.

Boundary (docs/article/CODE_DESIGN.md §9)
------------------------------------------
- ``src/`` provides stateless primitives: classical_mds, embed_classical,
  is_psd, neg_eigenvalue_mass, kruskal_stress_1, shepard_data,
  concentration_stats, hubness_skewness.
- CV-MDS, SMACOF, figures, and the geometry table live here in experiments/.
- No new src/ code.

Runner bug note
---------------
experiments/article/runner.py's ``_build_dataset`` fallback calls
``get_dataset(name, **params)`` but the registry signature is
``get_dataset(name, params: dict)``. This fails for planted_families.
This module therefore computes D matrices directly (same cache layout) and
does not call the runner.  A task-handoff has been filed to fix the runner.

Usage
-----
    # Compute D matrices + geometry table + figures (local, all representations):
    python -m experiments.article.analysis.mds \\
        --output-root /media/.../results/T-M5b/ \\
        --corpus planted_main

    # HyperCOT-only small corpus:
    python -m experiments.article.analysis.mds \\
        --output-root /media/.../results/T-M5b/ \\
        --corpus planted_small
"""

from __future__ import annotations

import argparse
import contextlib
import json
import logging
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Corpus configurations
# ---------------------------------------------------------------------------

#: Planted-families corpus configs keyed by label.
#: Each config is forwarded to PlantedFamilyDataset(**cfg).
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

#: Distance names for the main corpus (all representations except HyperCOT).
MAIN_DISTANCES: list[str] = [
    "isalhg_levenshtein",
    "hypergraph_wl_l1",
    "netlsd_l2",
    "hpd_jsd",
    "nauty_levi_edit",
]

#: HyperCOT only runs on the small corpus (O(n³)/pair; scale limit stated).
SMALL_DISTANCES: list[str] = [
    "isalhg_levenshtein",
    "hypercot",
]

#: Display names for the geometry table and figures.
REPR_LABELS: dict[str, str] = {
    "isalhg_levenshtein": "IsalHG",
    "hypergraph_wl_l1": "WL-L1",
    "netlsd_l2": "NetLSD",
    "hpd_jsd": "HPD-JSD",
    "nauty_levi_edit": "NautyEdit",
    "hypercot": "HyperCOT",
}


# ---------------------------------------------------------------------------
# Pure mathematical helpers (tested independently)
# ---------------------------------------------------------------------------


def pairwise_l2(X: np.ndarray) -> np.ndarray:
    """Symmetric pairwise L2 distance matrix from an ``(n, d)`` coordinate array.

    Parameters
    ----------
    X : numpy.ndarray
        Coordinate matrix of shape ``(n, d)``.

    Returns
    -------
    numpy.ndarray
        Symmetric ``(n, n)`` distance matrix with zero diagonal.
    """
    diff = X[:, np.newaxis, :] - X[np.newaxis, :, :]
    D: np.ndarray = np.sqrt(np.sum(diff**2, axis=-1))
    # Ensure exact zero diagonal despite floating-point noise.
    np.fill_diagonal(D, 0.0)
    return D


def cv_dimension_selection(
    D: np.ndarray,
    max_dims: int,
    test_fraction: float = 0.2,
    rng_seed: int = 42,
) -> tuple[int, list[float]]:
    """Select D̂ by cross-validated reconstruction error on held-out pairs.

    Procedure: embed the full distance matrix at each candidate dimension ``d``
    using classical (Torgerson–Gower) MDS, evaluate Kruskal RMSE only on a
    random held-out subset of the C(N,2) upper-triangle pairs, and pick the
    dimension that minimises the held-out error.

    This is the "practical CV-MDS" approach: embedding uses all pairs (not just
    training pairs), and the test set provides an unbiased estimate of how well
    the embedding generalises.  True out-of-sample fitting (MDS on partial
    matrices) is numerically ill-posed and not used here.

    Parameters
    ----------
    D : numpy.ndarray
        Symmetric ``(n, n)`` distance matrix.
    max_dims : int
        Maximum dimension to evaluate.  Clipped to ``n - 1``.
    test_fraction : float, optional
        Fraction of C(N,2) pairs held out for evaluation.  Default ``0.2``.
    rng_seed : int, optional
        Seed for the random pair split.  Default ``42``.

    Returns
    -------
    d_hat : int
        1-indexed dimension minimising the held-out RMSE.
    cv_errors : list[float]
        Held-out RMSE for each dimension ``d = 1, …, max_dims``, so
        ``cv_errors[d - 1]`` is the error at dimension ``d``.
    """
    from isalhg.metric_space.metrics.embedding import embed_classical

    n = D.shape[0]
    max_dims = min(max_dims, n - 1)

    # Upper-triangle pair indices (excluding diagonal).
    rows, cols = np.triu_indices(n, k=1)
    n_pairs = len(rows)

    # Random test/train split of pairs.
    rng = np.random.default_rng(rng_seed)
    perm = rng.permutation(n_pairs)
    n_test = max(1, int(n_pairs * test_fraction))
    test_mask = perm[:n_test]

    d_orig_test = D[rows[test_mask], cols[test_mask]]

    cv_errors: list[float] = []
    for d in range(1, max_dims + 1):
        X = embed_classical(D, n_dims=d)
        D_embed = pairwise_l2(X)
        d_embed_test = D_embed[rows[test_mask], cols[test_mask]]
        rmse = float(np.sqrt(np.mean((d_orig_test - d_embed_test) ** 2)))
        cv_errors.append(rmse)

    # Parsimony rule: pick the *smallest* d within a relative tolerance of
    # the global minimum.  Without this, machine-epsilon fluctuations among
    # equally good high-d embeddings cause the argmin to land arbitrarily
    # at large d on near-Euclidean inputs.
    min_err = min(cv_errors)
    # Tolerance = 0.1% of the improvement from d=1 to the minimum, or 1e-8
    # absolute — whichever is larger.  This is tight enough not to collapse
    # a genuine elbow but wide enough to absorb double-precision noise.
    range_err = cv_errors[0] - min_err
    tol_abs = max(1e-8, range_err * 1e-3)

    d_hat = 1
    for d, err in enumerate(cv_errors, 1):
        if err <= min_err + tol_abs:
            d_hat = d
            break

    return d_hat, cv_errors


def mardia_ratios(eigenvalues: np.ndarray) -> tuple[float, float]:
    """Mardia P^(1) and P^(2) from the double-centred Gram eigenspectrum.

    These are the two classic criteria for choosing MDS dimension
    (Mardia et al. 1979; Borg & Groenen 2005 §12).

    ``P^(1) = Σ_{λ_i > 0} λ_i / Σ_i |λ_i|``
    ``P^(2) = Σ_{λ_i > 0} λ_i² / Σ_i λ_i²``

    Parameters
    ----------
    eigenvalues : numpy.ndarray
        1-D eigenvalue array from ``classical_mds`` (descending, may have
        negative entries for non-Euclidean metrics).

    Returns
    -------
    p1, p2 : float
        Both in ``[0, 1]``; values near 1 indicate a compact Euclidean embedding.
    """
    eigenvalues = np.asarray(eigenvalues, dtype=np.float64)
    pos = eigenvalues[eigenvalues > 0]
    if len(pos) == 0:
        return 0.0, 0.0

    sum_pos = float(np.sum(pos))
    sum_abs = float(np.sum(np.abs(eigenvalues)))
    sum_sq_pos = float(np.sum(pos**2))
    sum_sq_all = float(np.sum(eigenvalues**2))

    p1 = sum_pos / sum_abs if sum_abs > 0.0 else 0.0
    p2 = sum_sq_pos / sum_sq_all if sum_sq_all > 0.0 else 0.0
    return float(np.clip(p1, 0.0, 1.0)), float(np.clip(p2, 0.0, 1.0))


def negative_eigenvalue_floor(eigenvalues: np.ndarray) -> int:
    """Index at which eigenvalues first become negative (0-based).

    Parameters
    ----------
    eigenvalues : numpy.ndarray
        Descending eigenvalue array.

    Returns
    -------
    int
        The 0-based index of the first negative eigenvalue, or ``len(eigenvalues)``
        when all are non-negative (Euclidean metric).
    """
    eigenvalues = np.asarray(eigenvalues, dtype=np.float64)
    neg = np.where(eigenvalues < -1e-10)[0]
    return int(neg[0]) if len(neg) > 0 else len(eigenvalues)


def geometry_table_row(
    corpus_name: str,
    representation_name: str,
    D: np.ndarray,
    d_hat: int,
) -> dict[str, Any]:
    """Compute one row of the T-M5f geometry table.

    All columns are computed from ``D`` and ``d_hat``; no other inputs needed.

    Parameters
    ----------
    corpus_name : str
        Label for the corpus (e.g. ``"planted_k3_n10"``).
    representation_name : str
        Label for the representation (e.g. ``"IsalHG"``).
    D : numpy.ndarray
        Symmetric ``(n, n)`` pairwise distance matrix.
    d_hat : int
        Selected intrinsic dimension (from CV or Mardia; passed in, not recomputed).

    Returns
    -------
    dict
        Row with keys: corpus, representation, n_points, psd, nu, d_hat,
        stress_at_d_hat, diameter, median, diameter_to_median, iqr,
        hubness_skewness.
    """
    from isalhg.metric_space.metrics.embedding import (
        classical_mds,
        embed_classical,
        is_psd,
        kruskal_stress_1,
        neg_eigenvalue_mass,
    )
    from isalhg.metric_space.metrics.geometry import concentration_stats, hubness_skewness

    D = np.asarray(D, dtype=np.float64)
    n = D.shape[0]

    eigenvalues, _ = classical_mds(D)

    psd_flag: bool = is_psd(eigenvalues)
    nu: float = neg_eigenvalue_mass(eigenvalues)

    # Stress at d_hat using classical embedding.
    X_hat = embed_classical(D, n_dims=d_hat)
    D_hat = pairwise_l2(X_hat)
    stress: float = kruskal_stress_1(D, D_hat)

    conc = concentration_stats(D)
    hub = hubness_skewness(D, k=min(10, n - 1))

    return {
        "corpus": corpus_name,
        "representation": representation_name,
        "n_points": int(n),
        "psd": bool(psd_flag),
        "nu": float(nu),
        "d_hat": int(d_hat),
        "stress_at_d_hat": float(stress),
        "diameter": float(conc["diameter"]),
        "median": float(conc["median"]),
        "diameter_to_median": float(conc["diameter_to_median"]),
        "iqr": float(conc["iqr"]),
        "hubness_skewness": float(hub),
    }


# ---------------------------------------------------------------------------
# D-matrix caching (runner-compatible layout)
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


def _d_matrix_is_done(dist_dir: Path) -> bool:
    meta_path = dist_dir / "meta.json"
    if not meta_path.exists():
        return False
    try:
        with open(meta_path) as f:
            return json.load(f).get("status") == "done"
    except (json.JSONDecodeError, KeyError):
        return False


def compute_and_cache_d_matrix(
    hypergraphs: list,
    dist_name: str,
    cell_output_dir: Path,
    corpus_meta: dict[str, Any],
) -> np.ndarray:
    """Compute pairwise distance matrix and cache it in runner-compatible layout.

    Output structure mirrors experiments.article.runner.run_d_matrix_cell:
        ``{cell_output_dir}/{dist_name}/D.npy``
        ``{cell_output_dir}/{dist_name}/meta.json`` (status: 'done')

    Parameters
    ----------
    hypergraphs : list[SparseHypergraph]
        Ordered corpus.
    dist_name : str
        Registered distance name (e.g. ``"isalhg_levenshtein"``).
    cell_output_dir : Path
        Cell-level output directory (= ``output_root / cell.output_key()``).
    corpus_meta : dict
        Corpus metadata written into meta.json (for traceability).

    Returns
    -------
    numpy.ndarray
        Symmetric ``(n, n)`` distance matrix.
    """
    dist_dir = cell_output_dir / dist_name
    d_npy = dist_dir / "D.npy"

    if _d_matrix_is_done(dist_dir):
        logger.info("  %s: cached (loading from disk)", dist_name)
        return np.load(d_npy)

    dist = _build_distance(dist_name)
    logger.info("  computing %s...", dist_name)
    t0 = time.perf_counter()
    D: np.ndarray = dist.matrix(hypergraphs)
    elapsed = time.perf_counter() - t0
    logger.info("  %s: %.2fs  shape=%s", dist_name, elapsed, D.shape)

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


def _build_distance(name: str):  # noqa: ANN202
    """Instantiate a HypergraphDistance by registered name."""
    from isalhg.metric_space.registry import get_distance

    return get_distance(name)


# ---------------------------------------------------------------------------
# Figure generation
# ---------------------------------------------------------------------------


def _save_figure(fig: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    logger.info("  figure saved: %s", path)


def plot_mds_scatter(
    X: np.ndarray,
    labels: list[int] | None,
    repr_label: str,
    corpus_label: str,
    d_hat: int,
) -> Any:
    """MDS scatter plot (first two dimensions of the classical embedding).

    Points are coloured by planted-family label when available.

    Parameters
    ----------
    X : numpy.ndarray
        ``(n, d_hat)`` classical MDS embedding.
    labels : list[int] or None
        Planted-family class labels (``iso_class``), one per point.
    repr_label : str
        Human-readable representation name for the title.
    corpus_label : str
        Corpus name.
    d_hat : int
        Dimension used (for subtitle).

    Returns
    -------
    matplotlib.figure.Figure
    """
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(5, 4))
    xs = X[:, 0] if X.shape[1] > 0 else np.zeros(X.shape[0])
    ys = X[:, 1] if X.shape[1] > 1 else np.zeros(X.shape[0])

    if labels is not None:
        scatter = ax.scatter(xs, ys, c=labels, cmap="tab10", s=30, alpha=0.8)
        plt.colorbar(scatter, ax=ax, label="Family id")
    else:
        ax.scatter(xs, ys, s=30, alpha=0.8)

    ax.set_title(f"MDS ({repr_label}, D={d_hat})\n{corpus_label}", fontsize=9)
    ax.set_xlabel("MDS dim 1")
    ax.set_ylabel("MDS dim 2")
    ax.tick_params(labelsize=7)
    fig.tight_layout()
    return fig


def plot_shepard(
    d_orig: np.ndarray,
    d_embed: np.ndarray,
    repr_label: str,
    d_hat: int,
) -> Any:
    """Shepard diagram: original dissimilarities vs embedding distances.

    Parameters
    ----------
    d_orig : numpy.ndarray
        Upper-triangle entries of the original distance matrix.
    d_embed : numpy.ndarray
        Corresponding entries of the embedding distance matrix.
    repr_label : str
    d_hat : int

    Returns
    -------
    matplotlib.figure.Figure
    """
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(4, 4))
    ax.scatter(d_orig, d_embed, s=5, alpha=0.3, rasterized=True)
    lim_max = max(d_orig.max(), d_embed.max()) * 1.05
    ax.plot([0, lim_max], [0, lim_max], "r--", lw=0.8, label="identity")
    ax.set_xlim(0, lim_max)
    ax.set_ylim(0, lim_max)
    ax.set_xlabel("Original distance")
    ax.set_ylabel("Embedding distance")
    ax.set_title(f"Shepard — {repr_label} (D={d_hat})", fontsize=9)
    ax.legend(fontsize=7)
    fig.tight_layout()
    return fig


def plot_stress_vs_dim(
    cv_errors: list[float],
    d_hat: int,
    repr_label: str,
) -> Any:
    """Stress (CV RMSE) vs embedding dimension curve.

    Parameters
    ----------
    cv_errors : list[float]
        CV reconstruction RMSE for dimensions 1 … len(cv_errors).
    d_hat : int
        Selected dimension (marked with a vertical line).
    repr_label : str

    Returns
    -------
    matplotlib.figure.Figure
    """
    import matplotlib.pyplot as plt

    dims = list(range(1, len(cv_errors) + 1))
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.plot(dims, cv_errors, marker="o", ms=4)
    ax.axvline(x=d_hat, color="r", linestyle="--", lw=1.0, label=f"D̂={d_hat}")
    ax.set_xlabel("Dimension")
    ax.set_ylabel("CV RMSE")
    ax.set_title(f"CV dimension selection — {repr_label}", fontsize=9)
    ax.legend(fontsize=7)
    fig.tight_layout()
    return fig


def plot_combined_mds_scatter(
    embeddings: dict[str, np.ndarray],
    labels: list[int] | None,
    corpus_label: str,
    d_hats: dict[str, int],
) -> Any:
    """Multi-panel MDS scatter comparing all representations.

    Parameters
    ----------
    embeddings : dict[str, np.ndarray]
        ``{repr_name: X}`` where X is ``(n, d_hat)`` classical MDS embedding.
    labels : list[int] or None
        Planted-family class labels.
    corpus_label : str
    d_hats : dict[str, int]
        Selected dimension per representation.

    Returns
    -------
    matplotlib.figure.Figure
    """
    import matplotlib.pyplot as plt

    n_reprs = len(embeddings)
    if n_reprs == 0:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No embeddings", ha="center", va="center")
        return fig

    ncols = min(3, n_reprs)
    nrows = (n_reprs + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(4 * ncols, 3.5 * nrows), squeeze=False)

    for idx, (repr_name, X) in enumerate(embeddings.items()):
        row, col = divmod(idx, ncols)
        ax = axes[row][col]
        xs = X[:, 0] if X.shape[1] > 0 else np.zeros(X.shape[0])
        ys = X[:, 1] if X.shape[1] > 1 else np.zeros(X.shape[0])
        if labels is not None:
            ax.scatter(xs, ys, c=labels, cmap="tab10", s=20, alpha=0.8)
        else:
            ax.scatter(xs, ys, s=20, alpha=0.8)
        ax.set_title(
            f"{REPR_LABELS.get(repr_name, repr_name)} (D̂={d_hats.get(repr_name, '?')})",
            fontsize=8,
        )
        ax.set_xlabel("MDS 1", fontsize=7)
        ax.set_ylabel("MDS 2", fontsize=7)
        ax.tick_params(labelsize=6)

    # Hide empty subplots.
    for idx in range(n_reprs, nrows * ncols):
        row, col = divmod(idx, ncols)
        axes[row][col].set_visible(False)

    fig.suptitle(f"Classical MDS — {corpus_label}", fontsize=10)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# SMACOF stress helper
# ---------------------------------------------------------------------------


def smacof_stress_at_dim(D: np.ndarray, n_dims: int, rng_seed: int = 42) -> float:
    """Run SMACOF MDS and return the final stress.

    Parameters
    ----------
    D : numpy.ndarray
        ``(n, n)`` distance matrix.
    n_dims : int
        Target dimensionality.
    rng_seed : int
        Random state for sklearn's SMACOF initialisation.

    Returns
    -------
    float
        Kruskal stress-1 after SMACOF convergence (sklearn's ``stress_``
        is not normalised the same way, so we recompute via our primitive).
    """
    from sklearn.manifold import MDS

    from isalhg.metric_space.metrics.embedding import kruskal_stress_1

    mds = MDS(
        n_components=n_dims,
        metric=True,
        dissimilarity="precomputed",
        random_state=rng_seed,
        normalized_stress=False,
        n_init=4,
        max_iter=300,
    )
    X_smacof = mds.fit_transform(D)
    D_smacof = pairwise_l2(X_smacof)
    return float(kruskal_stress_1(D, D_smacof))


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def _corpus_meta(cfg: dict[str, Any], n_items: int) -> dict[str, Any]:
    return {
        "dataset": "planted_families",
        "dataset_params": cfg,
        "n_items": n_items,
    }


def run_mds_pipeline(
    output_root: Path,
    corpus_label: str,
    corpus_cfg: dict[str, Any],
    distance_names: list[str],
    max_dims: int = 10,
    cv_rng_seed: int = 42,
) -> list[dict[str, Any]]:
    """Run the full T-M5b MDS pipeline on one corpus.

    Steps
    -----
    1. Load planted_families corpus.
    2. For each distance: compute/load D.npy (idempotent caching).
    3. For each D: CV-D̂ selection + Mardia ratios + geometry table row.
    4. Generate figures (scatter, Shepard, stress-vs-D).
    5. Write geometry table to ``{output_root}/geometry_table_{corpus_label}.csv/json``.

    Parameters
    ----------
    output_root : Path
        Root output directory (outside the git tree).
    corpus_label : str
        Human label (e.g. ``"planted_main"``), used in paths and table rows.
    corpus_cfg : dict
        PlantedFamilyDataset constructor kwargs.
    distance_names : list[str]
        Registered distance names to run.
    max_dims : int, optional
        Maximum CV dimension to evaluate.  Default ``10``.
    cv_rng_seed : int, optional
        RNG seed for CV pair split.  Default ``42``.

    Returns
    -------
    list[dict]
        List of geometry table rows (one per distance).
    """
    from isalhg.datasets.synthetic.planted_families import PlantedFamilyDataset
    from isalhg.metric_space.metrics.embedding import (
        classical_mds,
        embed_classical,
        shepard_data,
    )

    logger.info("=== corpus: %s ===", corpus_label)

    # 1. Load corpus.
    t0 = time.perf_counter()
    dataset = PlantedFamilyDataset(**corpus_cfg)
    items = list(dataset)
    hypergraphs = [item.hypergraph for item in items]
    # planted_families stores the class label in extra["family_index"];
    # iso_class is None (family membership is the class, not an iso-fingerprint).
    labels = [int(item.extra.get("family_index", 0)) for item in items]
    n = len(hypergraphs)
    corpus_meta = _corpus_meta(corpus_cfg, n)
    logger.info("  corpus loaded: N=%d in %.2fs", n, time.perf_counter() - t0)

    # Cell output directory mirrors runner layout:
    # {output_root}/d_matrix/planted_families/{corpus_label}/seed{seed}/
    seed_val = int(corpus_cfg.get("seed_value", 0))
    cell_output_dir = (
        output_root / "d_matrix" / "planted_families" / corpus_label / f"seed{seed_val}"
    )

    figures_dir = output_root / "figures" / corpus_label
    figures_dir.mkdir(parents=True, exist_ok=True)

    # 2–3. Per-distance: D matrix + geometry.
    geometry_rows: list[dict[str, Any]] = []
    embeddings_for_combined: dict[str, np.ndarray] = {}
    d_hats_for_combined: dict[str, int] = {}

    for dist_name in distance_names:
        repr_label = REPR_LABELS.get(dist_name, dist_name)
        logger.info("--- %s (%s) ---", dist_name, repr_label)

        # 2. D matrix (cached).
        try:
            D = compute_and_cache_d_matrix(hypergraphs, dist_name, cell_output_dir, corpus_meta)
        except Exception as exc:
            logger.warning("  %s FAILED: %s; skipping.", dist_name, exc)
            continue

        # 3a. Classical MDS eigendecomposition.
        eigenvalues, _ = classical_mds(D)

        # 3b. CV D̂ selection.
        d_hat, cv_errors = cv_dimension_selection(D, max_dims=max_dims, rng_seed=cv_rng_seed)
        logger.info("  CV D̂=%d (CV RMSE at D̂=%.4f)", d_hat, cv_errors[d_hat - 1])

        # 3c. Mardia ratios (supporting evidence).
        p1, p2 = mardia_ratios(eigenvalues)
        neg_floor = negative_eigenvalue_floor(eigenvalues)
        logger.info("  Mardia P^(1)=%.3f P^(2)=%.3f neg_floor=%d", p1, p2, neg_floor)

        # 3d. Geometry table row.
        row = geometry_table_row(
            corpus_name=corpus_label,
            representation_name=repr_label,
            D=D,
            d_hat=d_hat,
        )
        row["mardia_p1"] = float(p1)
        row["mardia_p2"] = float(p2)
        row["neg_eigenvalue_floor"] = int(neg_floor)
        row["cv_errors"] = cv_errors
        geometry_rows.append(row)

        # 3e. Classical embedding for scatter.
        X_hat = embed_classical(D, n_dims=d_hat)
        embeddings_for_combined[dist_name] = X_hat
        d_hats_for_combined[dist_name] = d_hat

        # 4. Figures.
        try:
            import matplotlib

            matplotlib.use("Agg")

            # MDS scatter (first 2 dims).
            fig_scatter = plot_mds_scatter(X_hat, labels, repr_label, corpus_label, d_hat)
            _save_figure(fig_scatter, figures_dir / f"mds_scatter_{dist_name}.pdf")
            fig_scatter.clf()

            # Shepard diagram.
            d_orig_tri, d_embed_tri = shepard_data(D, pairwise_l2(X_hat))
            fig_shepard = plot_shepard(d_orig_tri, d_embed_tri, repr_label, d_hat)
            _save_figure(fig_shepard, figures_dir / f"shepard_{dist_name}.pdf")
            fig_shepard.clf()

            # Stress-vs-dim.
            fig_stress = plot_stress_vs_dim(cv_errors, d_hat, repr_label)
            _save_figure(fig_stress, figures_dir / f"stress_vs_dim_{dist_name}.pdf")
            fig_stress.clf()

        except Exception as exc:
            logger.warning("  figure generation failed for %s: %s", dist_name, exc)

    # 4b. Combined scatter.
    try:
        import matplotlib

        matplotlib.use("Agg")

        fig_combined = plot_combined_mds_scatter(
            embeddings_for_combined, labels, corpus_label, d_hats_for_combined
        )
        _save_figure(fig_combined, figures_dir / "mds_combined.pdf")
        fig_combined.clf()
    except Exception as exc:
        logger.warning("  combined scatter failed: %s", exc)

    # 5. Write geometry table.
    table_csv = output_root / f"geometry_table_{corpus_label}.csv"
    table_json = output_root / f"geometry_table_{corpus_label}.json"
    _write_geometry_table(geometry_rows, table_csv, table_json)

    return geometry_rows


def _write_geometry_table(
    rows: list[dict[str, Any]],
    csv_path: Path,
    json_path: Path,
) -> None:
    """Write geometry table rows to CSV and JSON."""
    import csv

    # JSON (full, including cv_errors list).
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w") as f:
        json.dump(rows, f, indent=2)
    logger.info("geometry table JSON: %s", json_path)

    # CSV (flat, excluding cv_errors which is a list).
    flat_keys = [
        "corpus",
        "representation",
        "n_points",
        "psd",
        "nu",
        "d_hat",
        "stress_at_d_hat",
        "diameter",
        "median",
        "diameter_to_median",
        "iqr",
        "hubness_skewness",
        "mardia_p1",
        "mardia_p2",
        "neg_eigenvalue_floor",
    ]
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=flat_keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    logger.info("geometry table CSV: %s", csv_path)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry point for ``python -m experiments.article.analysis.mds``."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    parser = argparse.ArgumentParser(
        description="T-M5b MDS pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/T-M5b"),
        help="Root output directory (outside git tree)",
    )
    parser.add_argument(
        "--corpus",
        choices=list(CORPUS_CONFIGS),
        default="planted_main",
        help="Corpus to process (default: planted_main)",
    )
    parser.add_argument(
        "--max-dims",
        type=int,
        default=10,
        help="Maximum CV dimension to evaluate (default: 10)",
    )
    parser.add_argument(
        "--cv-seed",
        type=int,
        default=42,
        help="RNG seed for CV pair split (default: 42)",
    )
    args = parser.parse_args()

    corpus_label = args.corpus
    corpus_cfg = CORPUS_CONFIGS[corpus_label]

    distance_names = SMALL_DISTANCES if corpus_label == "planted_small" else MAIN_DISTANCES

    logger.info("output_root: %s", args.output_root)
    logger.info("corpus: %s", corpus_label)
    logger.info("distances: %s", distance_names)

    rows = run_mds_pipeline(
        output_root=args.output_root,
        corpus_label=corpus_label,
        corpus_cfg=corpus_cfg,
        distance_names=distance_names,
        max_dims=args.max_dims,
        cv_rng_seed=args.cv_seed,
    )

    # Print geometry table to stdout.
    print(f"\n{'=' * 70}")
    print(f"Geometry table — {corpus_label}")
    print(f"{'=' * 70}")
    header = (
        f"{'Repr':<12} {'N':>5} {'PSD':>5} {'ν':>6} {'D̂':>4} "
        f"{'S@D̂':>8} {'diam':>8} {'med':>8} {'D/M':>6} {'IQR':>8} {'hub':>7}"
    )
    print(header)
    print("-" * len(header))
    for row in rows:
        print(
            f"{row['representation']:<12} "
            f"{row['n_points']:>5} "
            f"{'T' if row['psd'] else 'F':>5} "
            f"{row['nu']:>6.3f} "
            f"{row['d_hat']:>4} "
            f"{row['stress_at_d_hat']:>8.4f} "
            f"{row['diameter']:>8.2f} "
            f"{row['median']:>8.2f} "
            f"{row['diameter_to_median']:>6.2f} "
            f"{row['iqr']:>8.2f} "
            f"{row['hubness_skewness']:>7.3f}"
        )
    print(f"\nGeometry table written to: {args.output_root}")
    sys.exit(0)


if __name__ == "__main__":
    main()
