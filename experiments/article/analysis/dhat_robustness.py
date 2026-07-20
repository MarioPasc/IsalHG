"""D̂ robustness analysis — T-M5l.

Three HGED-free deliverables that strengthen the D̂ = 21 estimate from T-M5b:

1. Horn parallel analysis  (``parallel_analysis`` — added to mds.py, imported here).
2. N-scaling D̂ sweep: planted corpus at N ∈ {60,120,240,480} + HIC cross-check
   (N=266, N=833, loaded from T-M5j caches, NOT recomputed).
3. Budget-coloured Shepard panel on the perturbation-ladder corpus (HGED-free;
   budget = known Qin cost, HGED ≤ budget by construction).

Results → /media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/T-M5l/
  dhat_sweep_table.{csv,json}
  figures/horn_scree_planted_N{60,120,240,480}.pdf
  figures/dhat_sweep_bar.pdf
  figures/budget_shepard.pdf

Usage
-----
    python -m experiments.article.analysis.dhat_robustness \\
        --output-root /media/.../results/T-M5l/

    # Separate modes:
    python -m experiments.article.analysis.dhat_robustness --mode sweep
    python -m experiments.article.analysis.dhat_robustness --mode shepard
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import json
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Per-instance params shared across all planted corpora in the sweep.
# Must match planted_main (mds.py CORPUS_CONFIGS) so that N is the only variable.
# ---------------------------------------------------------------------------

_PLANTED_BASE_PARAMS: dict[str, Any] = {
    "n_nodes": 10,
    "k": 3,
    "n_edges": 10,
    "n_edits": 3,
    "seed_value": 42,
    "max_retries": 300,
}

# members_per_family is kept constant so n_families scales linearly with N.
_MEMBERS_PER_FAMILY = 12

# N values for the planted sweep.
_PLANTED_N_LIST: list[int] = [60, 120, 240, 480]

# HIC dataset names and their T-M5j D.npy cache root.
_HIC_DATASETS: list[str] = ["IMDB-Wri-Genre-M", "IMDB-Wri-Genre"]

# Default T-M5j cache location.
_DEFAULT_HIC_ROOT = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/T-M5j/d_matrix")

# Horn permutations: use fewer for large N to keep run-time practical.
# For N ≤ 240 the full eigh is < 50 ms/call; for N ≈ 480 it is ~100 ms;
# for N ≈ 833 it is ~1 s. The thresholds below keep the total under ~10 min.
_N_PERM_FULL: int = 500
_N_PERM_MEDIUM: int = 200
_N_PERM_SMALL: int = 100
_N_MEDIUM_THRESHOLD: int = 300
_N_SMALL_THRESHOLD: int = 500


def _n_permutations_for(n: int, override: int | None = None) -> int:
    if override is not None:
        return override
    if n >= _N_SMALL_THRESHOLD:
        return _N_PERM_SMALL
    if n >= _N_MEDIUM_THRESHOLD:
        return _N_PERM_MEDIUM
    return _N_PERM_FULL


# ---------------------------------------------------------------------------
# Shared I/O helpers
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


def _save_figure(fig: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    logger.info("  figure: %s", path)


# ---------------------------------------------------------------------------
# Figure: Horn scree (observed eigenvalues vs null threshold band)
# ---------------------------------------------------------------------------


def plot_horn_scree(
    obs_eigs: np.ndarray,
    null_thresh: np.ndarray,
    d_hat_horn: int,
    d_hat_cv: int,
    title: str = "",
    max_rank: int = 50,
) -> Any:
    """Scree plot: observed eigenvalues vs the Horn null percentile threshold.

    Parameters
    ----------
    obs_eigs : numpy.ndarray
        Observed eigenvalues, descending, shape (n,).
    null_thresh : numpy.ndarray
        Null threshold curve, descending, shape (n,).
    d_hat_horn : int
        Horn D̂ estimate (vertical line).
    d_hat_cv : int
        CV D̂ estimate (vertical line, dashed).
    title : str
        Figure title.
    max_rank : int
        Number of leading ranks to display.

    Returns
    -------
    matplotlib.figure.Figure
    """
    import matplotlib.pyplot as plt

    k = min(max_rank, len(obs_eigs))
    ranks = np.arange(1, k + 1)
    obs_k = obs_eigs[:k]
    thr_k = null_thresh[:k]

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(ranks, obs_k, marker="o", ms=4, color="steelblue", label="Observed")
    ax.plot(ranks, thr_k, color="tomato", linestyle="--", lw=1.5, label="Null 95th pct")
    ax.axvline(x=d_hat_horn, color="tomato", lw=1.0, alpha=0.7, label=f"D̂_Horn={d_hat_horn}")
    ax.axvline(
        x=d_hat_cv, color="steelblue", lw=1.0, linestyle=":", alpha=0.7, label=f"D̂_CV={d_hat_cv}"
    )
    ax.axhline(y=0, color="black", lw=0.5, linestyle="--")
    ax.set_xlabel("Rank")
    ax.set_ylabel("Eigenvalue")
    ax.set_title(title or "Horn Parallel Analysis — Scree", fontsize=9)
    ax.legend(fontsize=7)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Figure: budget-coloured Shepard panel (2 panels)
# ---------------------------------------------------------------------------


def plot_budget_shepard(
    budgets: np.ndarray,
    d_i: np.ndarray,
    embed_dists: np.ndarray,
    rho_d_i: float,
    rho_embed: float,
    corpus_label: str = "perturbation_ladder",
) -> Any:
    """Two-panel Shepard plot coloured by Qin budget.

    Left panel : x = budget_t, y = native d_I.
    Right panel: x = budget_t, y = embedding Euclidean distance.

    Parameters
    ----------
    budgets : numpy.ndarray
        Accumulated Qin budget for each (base, snapshot) pair.
    d_i : numpy.ndarray
        Native d_I distances.
    embed_dists : numpy.ndarray
        MDS embedding Euclidean distances.
    rho_d_i : float
        Spearman ρ(budget, d_I).
    rho_embed : float
        Spearman ρ(budget, embed_dist).
    corpus_label : str

    Returns
    -------
    matplotlib.figure.Figure
    """
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(9, 4))

    sc0 = axes[0].scatter(budgets, d_i, c=budgets, cmap="viridis", s=18, alpha=0.7)
    axes[0].set_xlabel("Qin budget t (HGED upper bound)")
    axes[0].set_ylabel("d_I (Levenshtein)")
    axes[0].set_title(f"d_I vs budget\nSpearman ρ = {rho_d_i:.3f}", fontsize=9)
    plt.colorbar(sc0, ax=axes[0], label="budget t")

    sc1 = axes[1].scatter(budgets, embed_dists, c=budgets, cmap="viridis", s=18, alpha=0.7)
    axes[1].set_xlabel("Qin budget t (HGED upper bound)")
    axes[1].set_ylabel("Embedding distance (classical MDS)")
    axes[1].set_title(f"Embedding dist vs budget\nSpearman ρ = {rho_embed:.3f}", fontsize=9)
    plt.colorbar(sc1, ax=axes[1], label="budget t")

    fig.suptitle(f"Budget-coloured Shepard — {corpus_label}", fontsize=10)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Figure: D̂ vs N bar summary
# ---------------------------------------------------------------------------


def plot_dhat_vs_n(
    rows: list[dict[str, Any]],
) -> Any:
    """Bar chart showing D̂_CV and D̂_Horn side-by-side for each corpus.

    Parameters
    ----------
    rows : list[dict]
        Table rows from ``dhat_n_sweep``.

    Returns
    -------
    matplotlib.figure.Figure
    """
    import matplotlib.pyplot as plt

    labels = [r["corpus"] for r in rows]
    d_cv = [r["d_hat_cv"] for r in rows]
    d_horn = [r["d_hat_horn"] for r in rows]

    x = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(max(6, len(labels) * 1.2), 4))
    ax.bar(x - width / 2, d_cv, width, label="D̂_CV", color="steelblue", alpha=0.85)
    ax.bar(x + width / 2, d_horn, width, label="D̂_Horn", color="tomato", alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("D̂")
    ax.set_title("Intrinsic dimension D̂ vs corpus size", fontsize=9)
    ax.legend(fontsize=8)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Core sweep logic
# ---------------------------------------------------------------------------


def _geometry_row_from_d(
    corpus_label: str,
    D: np.ndarray,
    d_hat_cv: int,
    d_hat_horn: int,
    obs_eigs: np.ndarray,
    n_permutations_used: int,
) -> dict[str, Any]:
    """Build a sweep table row from a distance matrix and pre-computed estimates."""
    from experiments.article.analysis.mds import mardia_ratios, negative_eigenvalue_floor
    from isalhg.metric_space.metrics.embedding import (
        classical_mds,
        neg_eigenvalue_mass,
    )

    n = D.shape[0]
    eigenvalues, _ = classical_mds(D)
    nu = float(neg_eigenvalue_mass(eigenvalues))
    _, p2 = mardia_ratios(eigenvalues)
    floor = negative_eigenvalue_floor(eigenvalues)

    return {
        "N": int(n),
        "corpus": corpus_label,
        "nu": float(nu),
        "d_hat_cv": int(d_hat_cv),
        "d_hat_horn": int(d_hat_horn),
        "mardia_p2": float(p2),
        "neg_eigenvalue_floor": int(floor),
        "n_permutations": int(n_permutations_used),
    }


def dhat_n_sweep(
    output_root: Path,
    n_list: list[int] | None = None,
    hic_datasets: list[str] | None = None,
    hic_root: Path = _DEFAULT_HIC_ROOT,
    n_permutations_override: int | None = None,
    rng_seed: int = 42,
    figures: bool = True,
) -> list[dict[str, Any]]:
    """N-scaling D̂ sweep: planted corpus at multiple N + HIC cross-check.

    Planted corpora use the *same* per-instance parameters as ``planted_main``
    (n_nodes=10, k=3, n_edges=10, n_edits=3, seed_value=42); only
    ``n_families`` scales to hit each target ``N`` (with ``members_per_family=12``
    fixed for balanced families).

    HIC corpora are loaded from pre-computed T-M5j ``D.npy`` caches; NOT
    recomputed.  The scientific question: is D̂ ≈ 21 stable as N grows?

    Parameters
    ----------
    output_root : Path
        Root output directory (outside git tree).
    n_list : list[int] or None
        Planted-corpus sizes to sweep.  Defaults to [60, 120, 240, 480].
    hic_datasets : list[str] or None
        HIC dataset names to cross-check.  Defaults to both IMDB-Wri-Genre
        variants.
    hic_root : Path
        Root directory containing T-M5j d_matrix caches.
    n_permutations_override : int or None
        Override for all permutation counts (useful for testing / speed).
    rng_seed : int
        Base RNG seed for Horn analysis.
    figures : bool
        Whether to emit scree figures.

    Returns
    -------
    list[dict]
        Sweep table rows.
    """
    from experiments.article.analysis.mds import cv_dimension_selection, parallel_analysis
    from isalhg.datasets.synthetic.planted_families import PlantedFamilyDataset
    from isalhg.metric_space.registry import get_distance

    if n_list is None:
        n_list = _PLANTED_N_LIST
    if hic_datasets is None:
        hic_datasets = _HIC_DATASETS

    figures_dir = output_root / "figures"
    d_matrix_dir = output_root / "d_matrix"
    rows: list[dict[str, Any]] = []

    # ---- Planted-families sweep ----
    dist = get_distance("isalhg_levenshtein")

    for n_target in n_list:
        n_families = n_target // _MEMBERS_PER_FAMILY
        if n_families * _MEMBERS_PER_FAMILY != n_target:
            logger.warning(
                "N=%d not divisible by members_per_family=%d; skipping.",
                n_target,
                _MEMBERS_PER_FAMILY,
            )
            continue

        corpus_label = f"planted_N{n_target}"
        logger.info("=== %s (N=%d, n_families=%d) ===", corpus_label, n_target, n_families)

        cfg = {
            **_PLANTED_BASE_PARAMS,
            "n_families": n_families,
            "members_per_family": _MEMBERS_PER_FAMILY,
        }
        dataset = PlantedFamilyDataset(**cfg)
        items = list(dataset)
        hypergraphs = [it.hypergraph for it in items]
        assert len(hypergraphs) == n_target, f"Expected {n_target} items, got {len(hypergraphs)}"

        # D matrix: load cache or compute.
        d_npy = d_matrix_dir / corpus_label / "isalhg_levenshtein" / "D.npy"
        meta_json = d_npy.parent / "meta.json"
        if d_npy.exists() and meta_json.exists():
            logger.info("  Loading cached D.npy")
            D = np.load(d_npy)
        else:
            logger.info("  Computing isalhg_levenshtein D...")
            t0 = time.perf_counter()
            D = dist.matrix(hypergraphs)
            elapsed = time.perf_counter() - t0
            logger.info("  Done in %.2fs", elapsed)
            _atomic_write_npy(d_npy, D)
            _atomic_write_json(
                meta_json,
                {"status": "done", "shape": list(D.shape), "wall_clock_s": elapsed, **cfg},
            )

        n = D.shape[0]

        # CV D̂.
        logger.info("  Running CV dimension selection...")
        t_cv = time.perf_counter()
        d_hat_cv, _ = cv_dimension_selection(D, max_dims=min(n - 1, 50), rng_seed=rng_seed)
        logger.info("  CV D̂=%d (%.2fs)", d_hat_cv, time.perf_counter() - t_cv)

        # Horn D̂.
        n_perm = _n_permutations_for(n, n_permutations_override)
        logger.info("  Running Horn PA (n_permutations=%d)...", n_perm)
        t_horn = time.perf_counter()
        d_hat_horn, obs_eigs, null_thresh = parallel_analysis(
            D, n_permutations=n_perm, percentile=95, rng_seed=rng_seed
        )
        logger.info("  Horn D̂=%d (%.2fs)", d_hat_horn, time.perf_counter() - t_horn)

        row = _geometry_row_from_d(corpus_label, D, d_hat_cv, d_hat_horn, obs_eigs, n_perm)
        rows.append(row)

        # Scree figure.
        if figures:
            try:
                import matplotlib

                matplotlib.use("Agg")
                fig = plot_horn_scree(
                    obs_eigs,
                    null_thresh,
                    d_hat_horn,
                    d_hat_cv,
                    title=f"Horn Scree — {corpus_label}",
                )
                _save_figure(fig, figures_dir / f"horn_scree_{corpus_label}.pdf")
                fig.clf()
            except Exception as exc:
                logger.warning("  Scree figure failed: %s", exc)

    # ---- HIC cross-check (load cached D.npy, do NOT recompute) ----
    for ds_name in hic_datasets:
        d_npy = hic_root / ds_name / "isalhg_levenshtein" / "D.npy"
        if not d_npy.exists():
            logger.warning("HIC cache not found: %s — skipping.", d_npy)
            continue

        logger.info("=== HIC: %s (loading cache) ===", ds_name)
        D = np.load(d_npy)
        n = D.shape[0]
        corpus_label = ds_name

        # CV D̂ (max_dims capped for efficiency; N=833 → max_dims=50).
        logger.info("  Running CV dimension selection (N=%d)...", n)
        t_cv = time.perf_counter()
        d_hat_cv, _ = cv_dimension_selection(D, max_dims=min(n - 1, 50), rng_seed=rng_seed)
        logger.info("  CV D̂=%d (%.2fs)", d_hat_cv, time.perf_counter() - t_cv)

        # Horn D̂ (fewer permutations for large N).
        n_perm = _n_permutations_for(n, n_permutations_override)
        logger.info("  Running Horn PA (N=%d, n_permutations=%d)...", n, n_perm)
        t_horn = time.perf_counter()
        d_hat_horn, obs_eigs, null_thresh = parallel_analysis(
            D, n_permutations=n_perm, percentile=95, rng_seed=rng_seed
        )
        logger.info("  Horn D̂=%d (%.2fs)", d_hat_horn, time.perf_counter() - t_horn)

        row = _geometry_row_from_d(corpus_label, D, d_hat_cv, d_hat_horn, obs_eigs, n_perm)
        rows.append(row)

        # Scree figure for HIC.
        if figures:
            try:
                import matplotlib

                matplotlib.use("Agg")
                fig = plot_horn_scree(
                    obs_eigs,
                    null_thresh,
                    d_hat_horn,
                    d_hat_cv,
                    title=f"Horn Scree — {ds_name}",
                )
                _save_figure(fig, figures_dir / f"horn_scree_{ds_name}.pdf")
                fig.clf()
            except Exception as exc:
                logger.warning("  Scree figure failed: %s", exc)

    # ---- Summary D̂-vs-N bar figure ----
    if figures and rows:
        try:
            import matplotlib

            matplotlib.use("Agg")
            fig_bar = plot_dhat_vs_n(rows)
            _save_figure(fig_bar, figures_dir / "dhat_sweep_bar.pdf")
            fig_bar.clf()
        except Exception as exc:
            logger.warning("  D̂-vs-N bar figure failed: %s", exc)

    return rows


# ---------------------------------------------------------------------------
# Budget-coloured Shepard panel
# ---------------------------------------------------------------------------


def budget_shepard_panel(
    output_root: Path,
    ladder_params: dict[str, Any] | None = None,
    n_permutations_cv: int | None = None,
    rng_seed: int = 42,
    figures: bool = True,
) -> dict[str, float]:
    """Compute and emit the budget-coloured Shepard panel.

    Uses the ``perturbation_ladder`` corpus with known Qin-budget upper bounds.
    No HGED oracle is called: the budget is known by construction (each edit is
    priced by ``qin_edit_cost``).

    The classical MDS embedding at D̂ (from ``cv_dimension_selection``) is
    computed on the full corpus; then for each (base, snapshot_t, budget_t)
    pair from ``PerturbationLadderHypergraphs.ladder_pairs()``:

      - x = budget_t
      - y_native = d_I(base, snapshot_t)         [from D matrix]
      - y_embed  = ||embed(base) - embed(snap)||  [Euclidean in MDS coords]

    Spearman ρ is reported for both (t, y_native) and (t, y_embed).

    Parameters
    ----------
    output_root : Path
        Root output directory for figures.
    ladder_params : dict or None
        PerturbationLadderHypergraphs constructor kwargs.  Defaults to
        ``{n_nodes=8, n_edges=6, arity_range=(2,3), max_t=10, n_ladders=15,
           seed=42}``.
    n_permutations_cv : int or None
        Unused (kept for API uniformity); CV does not use permutations.
    rng_seed : int
        RNG seed for CV fold assignment.
    figures : bool
        Whether to emit the figure.

    Returns
    -------
    dict
        ``{'rho_d_i': float, 'rho_embed': float, 'd_hat_cv': int, 'n_pairs': int}``
    """
    from scipy.stats import spearmanr

    from experiments.article.analysis.mds import cv_dimension_selection
    from isalhg.datasets.synthetic.perturbation_ladder import PerturbationLadderHypergraphs
    from isalhg.metric_space.metrics.embedding import embed_classical
    from isalhg.metric_space.registry import get_distance

    if ladder_params is None:
        ladder_params = {
            "n_nodes": 8,
            "n_edges": 6,
            "arity_range": (2, 3),
            "max_t": 10,
            "n_ladders": 15,
            "seed": 42,
        }

    logger.info("=== Budget-Shepard panel ===")
    logger.info("  Ladder params: %s", ladder_params)

    dataset = PerturbationLadderHypergraphs(**ladder_params)
    items = list(dataset)
    hypergraphs = [it.hypergraph for it in items]
    n = len(hypergraphs)
    logger.info("  Corpus: %d items", n)

    # Index: (ladder_id, step) → item index.
    idx_map: dict[tuple[int, int], int] = {}
    for i, it in enumerate(items):
        idx_map[(int(it.extra["ladder"]), int(it.extra["step"]))] = i

    # Pairwise d_I matrix.
    logger.info("  Computing isalhg_levenshtein D (%d×%d)...", n, n)
    t0 = time.perf_counter()
    dist = get_distance("isalhg_levenshtein")
    D = dist.matrix(hypergraphs)
    logger.info("  D computed in %.2fs", time.perf_counter() - t0)

    # CV D̂.
    logger.info("  Running CV dimension selection...")
    d_hat_cv, _ = cv_dimension_selection(D, max_dims=min(n - 1, 40), rng_seed=rng_seed)
    logger.info("  CV D̂=%d", d_hat_cv)

    # Classical MDS embedding at D̂.
    X = embed_classical(D, n_dims=d_hat_cv)  # (n, d_hat_cv)

    # Collect (budget, d_I, embed_dist) for all base→snapshot pairs.
    budgets_list: list[int] = []
    d_i_list: list[float] = []
    embed_dists_list: list[float] = []

    for it in items:
        if it.extra["step"] == 0:
            continue  # bases not used as snapshots
        ladder_id = int(it.extra["ladder"])
        step = int(it.extra["step"])
        budget = int(it.extra["budget_from_base"])
        i_base = idx_map[(ladder_id, 0)]
        i_snap = idx_map[(ladder_id, step)]
        d_i_val = float(D[i_base, i_snap])
        embed_dist_val = float(np.sqrt(np.sum((X[i_base] - X[i_snap]) ** 2)))
        budgets_list.append(budget)
        d_i_list.append(d_i_val)
        embed_dists_list.append(embed_dist_val)

    budgets = np.array(budgets_list, dtype=np.float64)
    d_i_arr = np.array(d_i_list, dtype=np.float64)
    embed_arr = np.array(embed_dists_list, dtype=np.float64)
    n_pairs = len(budgets)
    logger.info("  Pairs collected: %d", n_pairs)

    # Spearman ρ.
    rho_d_i = float(spearmanr(budgets, d_i_arr).statistic)
    rho_embed = float(spearmanr(budgets, embed_arr).statistic)
    logger.info("  ρ(budget, d_I)     = %.4f", rho_d_i)
    logger.info("  ρ(budget, embed)   = %.4f", rho_embed)

    # Figure.
    if figures:
        try:
            import matplotlib

            matplotlib.use("Agg")
            fig = plot_budget_shepard(
                budgets,
                d_i_arr,
                embed_arr,
                rho_d_i,
                rho_embed,
                corpus_label="perturbation_ladder",
            )
            _save_figure(fig, output_root / "figures" / "budget_shepard.pdf")
            fig.clf()
        except Exception as exc:
            logger.warning("  Budget-Shepard figure failed: %s", exc)

    return {
        "rho_d_i": rho_d_i,
        "rho_embed": rho_embed,
        "d_hat_cv": d_hat_cv,
        "n_pairs": n_pairs,
    }


# ---------------------------------------------------------------------------
# Table I/O
# ---------------------------------------------------------------------------


def _write_sweep_table(rows: list[dict[str, Any]], output_root: Path) -> None:
    """Write sweep table to CSV and JSON."""
    flat_keys = [
        "N",
        "corpus",
        "nu",
        "d_hat_cv",
        "d_hat_horn",
        "mardia_p2",
        "neg_eigenvalue_floor",
        "n_permutations",
    ]

    csv_path = output_root / "dhat_sweep_table.csv"
    json_path = output_root / "dhat_sweep_table.json"

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=flat_keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    logger.info("Sweep table CSV: %s", csv_path)

    _atomic_write_json(json_path, rows)
    logger.info("Sweep table JSON: %s", json_path)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _print_sweep_table(rows: list[dict[str, Any]]) -> None:
    header = (
        f"{'Corpus':<22} {'N':>5} {'ν':>7} {'D̂_CV':>6} {'D̂_Horn':>7} "
        f"{'P^(2)':>7} {'floor':>6} {'n_perm':>7}"
    )
    print(f"\n{'=' * len(header)}")
    print("D̂ robustness sweep — T-M5l")
    print(f"{'=' * len(header)}")
    print(header)
    print("-" * len(header))
    for r in rows:
        print(
            f"{r['corpus']:<22} "
            f"{r['N']:>5} "
            f"{r['nu']:>7.3f} "
            f"{r['d_hat_cv']:>6} "
            f"{r['d_hat_horn']:>7} "
            f"{r['mardia_p2']:>7.3f} "
            f"{r['neg_eigenvalue_floor']:>6} "
            f"{r['n_permutations']:>7}"
        )


def main() -> None:
    """CLI entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    parser = argparse.ArgumentParser(
        description="T-M5l D̂ robustness analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/T-M5l"),
        help="Root output directory (outside git tree)",
    )
    parser.add_argument(
        "--mode",
        choices=["sweep", "shepard", "all"],
        default="all",
        help="Which deliverable to run (default: all)",
    )
    parser.add_argument(
        "--n-permutations",
        type=int,
        default=None,
        help="Override Horn permutation count (default: adaptive by N)",
    )
    parser.add_argument(
        "--hic-root",
        type=Path,
        default=_DEFAULT_HIC_ROOT,
        help="Root directory for T-M5j HIC D.npy caches",
    )
    parser.add_argument(
        "--no-figures",
        action="store_true",
        help="Skip figure generation",
    )
    args = parser.parse_args()

    output_root: Path = args.output_root
    output_root.mkdir(parents=True, exist_ok=True)
    emit_figures = not args.no_figures

    if args.mode in ("sweep", "all"):
        rows = dhat_n_sweep(
            output_root=output_root,
            hic_root=args.hic_root,
            n_permutations_override=args.n_permutations,
            figures=emit_figures,
        )
        _write_sweep_table(rows, output_root)
        _print_sweep_table(rows)

    if args.mode in ("shepard", "all"):
        result = budget_shepard_panel(
            output_root=output_root,
            figures=emit_figures,
        )
        print(
            f"\nBudget-Shepard panel:"
            f"\n  ρ(budget, d_I)   = {result['rho_d_i']:.4f}"
            f"\n  ρ(budget, embed) = {result['rho_embed']:.4f}"
            f"\n  D̂_CV (ladder)   = {result['d_hat_cv']}"
            f"\n  n_pairs          = {result['n_pairs']}"
        )


if __name__ == "__main__":
    main()
