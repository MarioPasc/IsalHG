"""E1' harvest: aggregate (d_I, exact_hged) pairs across available cells.

Scans the standard Picasso output directory for cells that have both
``isalhg_levenshtein`` and ``exact_hged`` D.npy files, extracts
upper-triangle HGED>0 pairs, aggregates across cells, computes Spearman
ρ (and Pearson r for the figure caption), and writes the E1'
scatter/joint-density figure + JSON summary.

The pipeline is idempotent: it always rewrites its outputs, so it can be
re-run when the remaining cells (n9_s1, n10_s0, n10_s1) land.

Usage (standalone)::

    python -m experiments.article.analysis.e1prime_harvest \\
        --e1prime-dir /media/.../results/T-M5a/e1prime \\
        --output-dir  /media/.../results/T-M5a/figures
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Discovery helpers
# ---------------------------------------------------------------------------


def _triu_indices(n: int) -> tuple[np.ndarray, np.ndarray]:
    """Return (row, col) for the strict upper triangle of an n×n matrix."""
    return np.triu_indices(n, k=1)


def _triu_vector(D: np.ndarray) -> np.ndarray:
    """Extract strict upper-triangle values as a 1-D array."""
    r, c = _triu_indices(D.shape[0])
    return D[r, c]


def _cell_root(e1prime_dir: Path) -> Path:
    """Return the root of the per-cell subdirectory tree."""
    return e1prime_dir / "d_matrix" / "perturbation_ladder"


def find_complete_cells(e1prime_dir: Path) -> list[dict[str, Any]]:
    """Return a list of cells where both d_I and exact_hged are present.

    Parameters
    ----------
    e1prime_dir : Path
        Root of the e1prime output tree (contains ``d_matrix/``).

    Returns
    -------
    list of dict
        Each entry has keys: ``label``, ``seed_dir``, ``d_I_dir``, ``hged_dir``.
    """
    root = _cell_root(e1prime_dir)
    if not root.exists():
        logger.warning("E1' root not found: %s", root)
        return []

    cells: list[dict[str, Any]] = []
    for label_dir in sorted(root.iterdir()):
        if not label_dir.is_dir():
            continue
        for seed_dir in sorted(label_dir.iterdir()):
            if not seed_dir.is_dir():
                continue
            d_I_dir = seed_dir / "isalhg_levenshtein"
            hged_dir = seed_dir / "exact_hged"
            d_I_ok = (d_I_dir / "D.npy").exists()
            hged_ok = (hged_dir / "D.npy").exists()
            cells.append(
                {
                    "label": label_dir.name,
                    "seed_dir": str(seed_dir),
                    "d_I_dir": d_I_dir if d_I_ok else None,
                    "hged_dir": hged_dir if hged_ok else None,
                    "complete": d_I_ok and hged_ok,
                }
            )
    return cells


# ---------------------------------------------------------------------------
# Pair extraction
# ---------------------------------------------------------------------------


def extract_pairs(
    d_I_dir: Path,
    hged_dir: Path,
) -> tuple[np.ndarray, np.ndarray]:
    """Load D_I and D_HGED and extract upper-triangle HGED>0 pairs.

    Parameters
    ----------
    d_I_dir : Path
        Directory with ``D.npy`` for isalhg_levenshtein.
    hged_dir : Path
        Directory with ``D.npy`` for exact_hged.

    Returns
    -------
    hged_vec : np.ndarray
        1-D array of HGED values for pairs with HGED > 0.
    d_I_vec : np.ndarray
        1-D array of d_I values for the same pairs.
    """
    D_I = np.load(d_I_dir / "D.npy")
    D_hged = np.load(hged_dir / "D.npy")

    if D_I.shape != D_hged.shape:
        raise ValueError(f"Shape mismatch: D_I={D_I.shape}, D_hged={D_hged.shape} in {d_I_dir}")

    hged_vec = _triu_vector(D_hged)
    d_I_vec = _triu_vector(D_I)

    mask = hged_vec > 0
    return hged_vec[mask], d_I_vec[mask]


# ---------------------------------------------------------------------------
# OLS helper
# ---------------------------------------------------------------------------


def _ols(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """Return (slope beta, intercept alpha) for OLS y = alpha + beta*x."""
    if len(x) < 2:
        return float("nan"), float("nan")
    x_c = x - x.mean()
    denom = x_c.dot(x_c)
    beta = float(x_c.dot(y) / denom) if denom > 0 else float("nan")
    alpha = float(y.mean() - beta * x.mean())
    return beta, alpha


# ---------------------------------------------------------------------------
# Main harvest
# ---------------------------------------------------------------------------


def harvest_e1prime(
    e1prime_dir: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Aggregate E1' pairs, compute ρ, and write figure + JSON summary.

    Parameters
    ----------
    e1prime_dir : Path
        Root of the Picasso output tree (contains ``d_matrix/``).
    output_dir : Path
        Where to write ``e1prime_result.json`` and ``e1prime_figure.pdf``.

    Returns
    -------
    dict
        Keys: consumed_cells, n_cells_complete, n_cells_total,
        n_pairs_per_cell, n_pairs_total, spearman_rho, spearman_pvalue,
        pearson_r, pearson_pvalue, ols_beta, ols_intercept.
    """
    from scipy.stats import pearsonr, spearmanr

    output_dir.mkdir(parents=True, exist_ok=True)

    all_cells = find_complete_cells(e1prime_dir)
    complete = [c for c in all_cells if c["complete"]]
    incomplete = [c["label"] for c in all_cells if not c["complete"]]

    logger.info(
        "E1' harvest: %d/%d cells complete; missing exact_hged: %s",
        len(complete),
        len(all_cells),
        incomplete,
    )

    if not complete:
        result: dict[str, Any] = {
            "status": "no_complete_cells",
            "n_cells_complete": 0,
            "n_cells_total": len(all_cells),
        }
        with open(output_dir / "e1prime_result.json", "w") as f:
            json.dump(result, f, indent=2)
        return result

    # Aggregate pairs across all complete cells
    hged_all: list[np.ndarray] = []
    d_I_all: list[np.ndarray] = []
    per_cell: list[dict[str, Any]] = []

    for cell in complete:
        hged_vec, d_I_vec = extract_pairs(
            Path(cell["d_I_dir"]),
            Path(cell["hged_dir"]),
        )
        hged_all.append(hged_vec)
        d_I_all.append(d_I_vec)

        # Per-cell statistics for the record
        if len(hged_vec) >= 5:
            rho_c, p_c = spearmanr(hged_vec, d_I_vec)
        else:
            rho_c, p_c = float("nan"), float("nan")

        per_cell.append(
            {
                "label": cell["label"],
                "n_pairs": int(len(hged_vec)),
                "spearman_rho": float(rho_c),
                "spearman_pvalue": float(p_c),
            }
        )
        logger.info("  %s: N=%d  rho=%.3f", cell["label"], len(hged_vec), rho_c)

    hged_agg = np.concatenate(hged_all)
    d_I_agg = np.concatenate(d_I_all)

    # Aggregate statistics
    rho, rho_p = spearmanr(hged_agg, d_I_agg)
    r_pear, r_p = pearsonr(hged_agg, d_I_agg)
    beta, alpha = _ols(hged_agg, d_I_agg)

    result = {
        "status": "done",
        "provisonal_note": (
            f"{len(complete)}/{len(all_cells)} cells (missing exact_hged: {incomplete})"
        ),
        "consumed_cells": [c["label"] for c in complete],
        "missing_cells": incomplete,
        "n_cells_complete": len(complete),
        "n_cells_total": len(all_cells),
        "n_pairs_total": int(len(hged_agg)),
        "spearman_rho": float(rho),
        "spearman_pvalue": float(rho_p),
        "pearson_r": float(r_pear),
        "pearson_pvalue": float(r_p),
        "ols_beta": float(beta),
        "ols_intercept": float(alpha),
        "per_cell": per_cell,
    }

    with open(output_dir / "e1prime_result.json", "w") as f:
        json.dump(result, f, indent=2)

    _e1prime_figure(
        hged_agg,
        d_I_agg,
        result,
        output_dir / "e1prime_figure.pdf",
    )

    logger.info(
        "E1' aggregate: N=%d  rho=%.4f  p=%.3g  r=%.4f  beta=%.3f",
        len(hged_agg),
        rho,
        rho_p,
        r_pear,
        beta,
    )
    return result


# ---------------------------------------------------------------------------
# Figure
# ---------------------------------------------------------------------------


def _e1prime_figure(
    hged: np.ndarray,
    d_I: np.ndarray,
    result: dict[str, Any],
    out_path: Path,
) -> None:
    """E1' scatter/joint-density figure (scatter + marginal histograms)."""
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.gridspec import GridSpec
    except ImportError:
        logger.warning("matplotlib not available; skipping E1' figure")
        return

    rho = result["spearman_rho"]
    r_pear = result["pearson_r"]
    n = result["n_pairs_total"]
    beta = result["ols_beta"]
    alpha_ols = result["ols_intercept"]

    fig = plt.figure(figsize=(5.5, 5.5), layout="constrained")
    gs = GridSpec(
        2,
        2,
        figure=fig,
        width_ratios=[4, 1],
        height_ratios=[1, 4],
        hspace=0.05,
        wspace=0.05,
    )

    ax_scatter = fig.add_subplot(gs[1, 0])
    ax_hist_x = fig.add_subplot(gs[0, 0], sharex=ax_scatter)
    ax_hist_y = fig.add_subplot(gs[1, 1], sharey=ax_scatter)

    # Scatter
    ax_scatter.scatter(
        hged,
        d_I,
        alpha=0.25,
        s=6,
        color="#2166ac",
        rasterized=True,
        linewidths=0,
    )
    # OLS line
    x_line = np.array([hged.min(), hged.max()])
    ax_scatter.plot(
        x_line,
        alpha_ols + beta * x_line,
        color="#d6604d",
        linewidth=1.5,
        label=f"β={beta:.2f}",
    )
    ax_scatter.set_xlabel("HGED (Qin 2023)")
    ax_scatter.set_ylabel("$d_I$ (IsalHG Levenshtein)")
    ax_scatter.legend(fontsize=7, loc="upper left")

    title_str = f"Spearman ρ={rho:.3f}   Pearson r={r_pear:.3f}   N={n:,}"
    ax_scatter.set_title(title_str, fontsize=8)

    # Marginal histograms — integer-valued axes, use integer bins
    hged_bins = np.arange(hged.min(), hged.max() + 2) - 0.5
    d_I_bins = np.arange(d_I.min(), d_I.max() + 2) - 0.5

    ax_hist_x.hist(hged, bins=hged_bins, color="#2166ac", alpha=0.7, linewidth=0)
    ax_hist_x.set_ylabel("Count")
    plt.setp(ax_hist_x.get_xticklabels(), visible=False)
    ax_hist_x.tick_params(axis="x", which="both", bottom=False)

    ax_hist_y.hist(
        d_I,
        bins=d_I_bins,
        color="#2166ac",
        alpha=0.7,
        linewidth=0,
        orientation="horizontal",
    )
    ax_hist_y.set_xlabel("Count")
    plt.setp(ax_hist_y.get_yticklabels(), visible=False)
    ax_hist_y.tick_params(axis="y", which="both", left=False)

    fig.suptitle(
        result.get("provisonal_note", ""),
        fontsize=7,
    )
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved E1' figure to %s", out_path)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry point for standalone execution."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--e1prime-dir",
        type=Path,
        required=True,
        help="Root of the e1prime output tree (contains d_matrix/).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory where e1prime_result.json and figure are written.",
    )
    args = parser.parse_args()

    result = harvest_e1prime(args.e1prime_dir, args.output_dir)

    # Print summary to stdout
    print(f"\nE1' harvest summary ({result['n_cells_complete']}/{result['n_cells_total']} cells)")
    print(f"  Consumed cells : {result.get('consumed_cells', [])}")
    print(f"  Missing cells  : {result.get('missing_cells', [])}")
    print(f"  N pairs        : {result.get('n_pairs_total', 'N/A')}")
    print(f"  Spearman rho   : {result.get('spearman_rho', 'N/A'):.4f}")
    print(f"  p-value        : {result.get('spearman_pvalue', 'N/A'):.3g}")
    print(f"  Pearson r      : {result.get('pearson_r', 'N/A'):.4f}")
    print(f"  OLS beta       : {result.get('ols_beta', 'N/A'):.4f}")
    print(f"  Results written to {args.output_dir}")


if __name__ == "__main__":
    main()
