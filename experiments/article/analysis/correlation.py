"""E1 — correlation analysis: d_I vs HGED.

Ports IsalGraph Table 2 (Spearman ρ / Pearson r) and adds mutual information
(novel second axis not in the sibling paper).

Usage::

    from experiments.article.analysis.correlation import analyze_correlation
    result = analyze_correlation(d_I_dir, hged_dir, output_dir)

The ``d_I_dir`` and ``hged_dir`` paths should point to the per-distance
subdirectories produced by ``run_d_matrix_cell`` (containing ``D.npy`` and
``meta.json``).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


def analyze_correlation(
    d_I_dir: Path,
    hged_dir: Path,
    output_dir: Path,
    *,
    n_bins: int = 20,
) -> dict[str, Any]:
    """Compute Spearman ρ, Pearson r, and MI between d_I and HGED.

    Parameters
    ----------
    d_I_dir : Path
        Directory containing ``D.npy`` for ``isalhg_levenshtein``.
    hged_dir : Path
        Directory containing ``D.npy`` for ``exact_hged``.
    output_dir : Path
        Where to write ``correlation_result.json`` and the scatter figure.
    n_bins : int
        Number of bins for the mutual-information plug-in estimator.

    Returns
    -------
    dict
        Keys: spearman_rho, spearman_pvalue, pearson_r, pearson_pvalue,
        mutual_information_bits, ols_slope_beta, ols_intercept, n_pairs.
    """
    from isalhg.metric_space.metrics.association import (
        mutual_information_binned,
        pearson_r,
        spearman_r,
        triu_vector,
    )

    result_path = output_dir / "correlation_result.json"
    output_dir.mkdir(parents=True, exist_ok=True)

    D_I = np.load(d_I_dir / "D.npy")
    D_hged = np.load(hged_dir / "D.npy")

    # Restrict to pairs where both distances are strictly positive
    x = triu_vector(D_hged)
    y = triu_vector(D_I)
    mask = (x > 0) & (y > 0)
    x_filt, y_filt = x[mask], y[mask]

    if len(x_filt) < 5:
        logger.warning("Only %d valid pairs — correlation will be unreliable", len(x_filt))

    rho, rho_pval = spearman_r(x_filt, y_filt)
    r, r_pval = pearson_r(x_filt, y_filt)
    mi = mutual_information_binned(x_filt, y_filt, n_bins=n_bins)

    # OLS: d_I = a + beta * HGED
    beta, alpha = _ols(x_filt, y_filt)

    with open(d_I_dir / "meta.json") as f:
        d_I_meta = json.load(f)

    result: dict[str, Any] = {
        "n_pairs": int(mask.sum()),
        "n_pairs_total": len(x),
        "spearman_rho": float(rho),
        "spearman_pvalue": float(rho_pval),
        "pearson_r": float(r),
        "pearson_pvalue": float(r_pval),
        "mutual_information_bits": float(mi),
        "ols_slope_beta": float(beta),
        "ols_intercept": float(alpha),
        "mean_max_degree": d_I_meta.get("mean_max_degree"),
        "mean_arity": d_I_meta.get("mean_arity"),
    }

    with open(result_path, "w") as f:
        json.dump(result, f, indent=2)

    _scatter_figure(x_filt, y_filt, result, output_dir / "scatter_d_I_vs_hged.pdf")

    logger.info(
        "E1 correlation: rho=%.3f  r=%.3f  MI=%.3f bits  beta=%.3f  n=%d",
        rho,
        r,
        mi,
        beta,
        mask.sum(),
    )
    return result


def _ols(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """Return (slope, intercept) of OLS regression y = alpha + beta*x."""
    if len(x) < 2:
        return float("nan"), float("nan")
    x_c = x - x.mean()
    beta = float(np.dot(x_c, y) / np.dot(x_c, x_c)) if x_c.dot(x_c) > 0 else float("nan")
    alpha = float(y.mean() - beta * x.mean())
    return beta, alpha


def _scatter_figure(
    x: np.ndarray,
    y: np.ndarray,
    result: dict[str, Any],
    out_path: Path,
) -> None:
    """Save scatter plot of HGED (x) vs d_I (y) with OLS line."""
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        logger.warning("matplotlib not available; skipping scatter figure")
        return

    fig, ax = plt.subplots(figsize=(5, 4))
    ax.scatter(x, y, alpha=0.4, s=8, color="#2166ac", rasterized=True)

    beta, alpha = result["ols_slope_beta"], result["ols_intercept"]
    x_line = np.array([x.min(), x.max()])
    ax.plot(x_line, alpha + beta * x_line, color="#d6604d", linewidth=1.5, label=f"β={beta:.2f}")

    ax.set_xlabel("HGED (Qin 2023)")
    ax.set_ylabel("$d_I$ (IsalHG Levenshtein)")
    rho = result["spearman_rho"]
    ax.set_title(
        f"ρ={rho:.3f}  MI={result['mutual_information_bits']:.2f} bits  n={result['n_pairs']}"
    )
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    logger.info("Saved scatter figure to %s", out_path)
