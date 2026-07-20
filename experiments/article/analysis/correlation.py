"""E1' — single-cell correlation helper: d_I vs HGED.

Rescoped at D-ART2 (2026-07-18): MI is dropped; the figure reports
Spearman ρ + Pearson r (ours only, no competitor rows, no density sweep).
MI was retired with the HGED head-to-head axis (PROPOSAL §5, OQ-F).

For the multi-cell E1' aggregate (the article figure) use
``experiments.article.analysis.e1prime_harvest.harvest_e1prime``.
This module is the single-cell helper useful for smoke tests and per-cell
diagnostics.

Usage::

    from experiments.article.analysis.correlation import analyze_correlation
    result = analyze_correlation(d_I_dir, hged_dir, output_dir)
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
) -> dict[str, Any]:
    """Compute Spearman ρ and Pearson r between d_I and HGED for one cell.

    MI is not computed (retired at D-ART2; was for the competitor head-to-head
    axis which the v3 scope drops).

    Parameters
    ----------
    d_I_dir : Path
        Directory containing ``D.npy`` for ``isalhg_levenshtein``.
    hged_dir : Path
        Directory containing ``D.npy`` for ``exact_hged``.
    output_dir : Path
        Where to write ``correlation_result.json`` and the scatter figure.

    Returns
    -------
    dict
        Keys: spearman_rho, spearman_pvalue, pearson_r, pearson_pvalue,
        ols_slope_beta, ols_intercept, n_pairs.
    """
    from scipy.stats import pearsonr, spearmanr

    from isalhg.metric_space.metrics.association import triu_vector

    result_path = output_dir / "correlation_result.json"
    output_dir.mkdir(parents=True, exist_ok=True)

    D_I = np.load(d_I_dir / "D.npy")
    D_hged = np.load(hged_dir / "D.npy")

    x = triu_vector(D_hged)
    y = triu_vector(D_I)
    mask = x > 0
    x_filt, y_filt = x[mask], y[mask]

    if len(x_filt) < 5:
        logger.warning("Only %d valid pairs — correlation will be unreliable", len(x_filt))

    rho, rho_pval = spearmanr(x_filt, y_filt)
    r_pear, r_p = pearsonr(x_filt, y_filt)
    beta, alpha = _ols(x_filt, y_filt)

    with open(d_I_dir / "meta.json") as f:
        d_I_meta = json.load(f)

    result: dict[str, Any] = {
        "n_pairs": int(mask.sum()),
        "n_pairs_total": int(len(x)),
        "spearman_rho": float(rho),
        "spearman_pvalue": float(rho_pval),
        "pearson_r": float(r_pear),
        "pearson_pvalue": float(r_p),
        "ols_slope_beta": float(beta),
        "ols_intercept": float(alpha),
        "mean_max_degree": d_I_meta.get("mean_max_degree"),
        "mean_arity": d_I_meta.get("mean_arity"),
    }

    with open(result_path, "w") as f:
        json.dump(result, f, indent=2)

    _scatter_figure(x_filt, y_filt, result, output_dir / "scatter_d_I_vs_hged.pdf")

    logger.info(
        "E1' (single cell): rho=%.3f  r=%.3f  beta=%.3f  n=%d",
        rho,
        r_pear,
        beta,
        mask.sum(),
    )
    return result


def _ols(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """Return (slope beta, intercept alpha) for OLS y = alpha + beta*x."""
    if len(x) < 2:
        return float("nan"), float("nan")
    x_c = x - x.mean()
    denom = x_c.dot(x_c)
    beta = float(x_c.dot(y) / denom) if denom > 0 else float("nan")
    alpha = float(y.mean() - beta * x.mean())
    return beta, alpha


def _scatter_figure(
    x: np.ndarray,
    y: np.ndarray,
    result: dict[str, Any],
    out_path: Path,
) -> None:
    """Scatter of HGED (x-axis) vs d_I (y-axis) with OLS line."""
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        logger.warning("matplotlib not available; skipping scatter figure")
        return

    fig, ax = plt.subplots(figsize=(5, 4))
    ax.scatter(x, y, alpha=0.4, s=8, color="#2166ac", rasterized=True, linewidths=0)

    beta, alpha = result["ols_slope_beta"], result["ols_intercept"]
    x_line = np.array([x.min(), x.max()])
    ax.plot(x_line, alpha + beta * x_line, color="#d6604d", linewidth=1.5, label=f"β={beta:.2f}")

    ax.set_xlabel("HGED (Qin 2023)")
    ax.set_ylabel("$d_I$ (IsalHG Levenshtein)")
    rho = result["spearman_rho"]
    r_pear = result["pearson_r"]
    ax.set_title(
        f"ρ={rho:.3f}  r={r_pear:.3f}  n={result['n_pairs']}",
        fontsize=9,
    )
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    logger.info("Saved scatter figure to %s", out_path)
