"""E2 — density sweep: ρ(d_I, HGED) vs mean max-degree Δ.

Tests Theorem B's falsifiable Δ-dependence: ρ should decay as density
increases, following the B-cond envelope C(k,Δ) = O(kΔ).

Usage::

    from experiments.article.analysis.density_sweep import analyze_density_sweep
    result = analyze_density_sweep(density_cells, output_dir)

``density_cells`` is a list of dicts::

    [
        {"label": "low", "d_I_dir": Path(...), "hged_dir": Path(...),
         "meta": {mean_max_degree, mean_arity, ...}},
        ...
    ]

where each entry corresponds to one density bin cell.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


def analyze_density_sweep(
    density_cells: list[dict[str, Any]],
    output_dir: Path,
    *,
    k: int = 3,
) -> dict[str, Any]:
    """Plot ρ vs Δ and overlay the Theorem B predicted envelope.

    Parameters
    ----------
    density_cells : list[dict]
        Each entry: ``{label, d_I_dir, hged_dir, meta}``.
        ``meta`` must contain ``mean_max_degree`` and ``mean_arity``.
    output_dir : Path
        Where to write ``density_sweep_result.json`` and the figure.
    k : int
        Max arity used for the C(k,Δ) envelope (default 3 for unlabelled
        corpora; set from corpus max_k when available).

    Returns
    -------
    dict
        Per-bin correlation values and summary statistics.
    """
    from isalhg.metric_space.metrics.association import pearson_r, spearman_r, triu_vector

    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []

    for cell in density_cells:
        d_I_dir = Path(cell["d_I_dir"])
        hged_dir = Path(cell["hged_dir"])
        meta = cell.get("meta", {})
        label = cell.get("label", "")

        D_I = np.load(d_I_dir / "D.npy")
        D_hged = np.load(hged_dir / "D.npy")
        x = triu_vector(D_hged)
        y = triu_vector(D_I)
        mask = (x > 0) & (y > 0)
        x_f, y_f = x[mask], y[mask]

        rho, _ = spearman_r(x_f, y_f) if len(x_f) >= 5 else (float("nan"), 1.0)
        r, _ = pearson_r(x_f, y_f) if len(x_f) >= 5 else (float("nan"), 1.0)

        rows.append(
            {
                "label": label,
                "mean_max_degree": float(meta.get("mean_max_degree", float("nan"))),
                "mean_arity": float(meta.get("mean_arity", float("nan"))),
                "spearman_rho": float(rho),
                "pearson_r": float(r),
                "n_pairs": int(mask.sum()),
            }
        )
        logger.info(
            "density bin %r: Δ_mean=%.2f  rho=%.3f  n=%d",
            label,
            meta.get("mean_max_degree", float("nan")),
            rho,
            mask.sum(),
        )

    result: dict[str, Any] = {"bins": rows}

    # Predicted B-cond envelope: ρ ~ 1/C where C = (1+Δ) + c*kΔ ≈ kΔ
    # Normalised so that at min Δ, predicted ρ = observed ρ.
    deltas = [r["mean_max_degree"] for r in rows if not np.isnan(r["mean_max_degree"])]
    if deltas:
        delta_arr = np.array(deltas)
        # C_rough = 1 + k * delta (B-worst normalised by m≈1 for unlabelled)
        C_vals = 1.0 + k * delta_arr
        # Scale so min C → rho_max
        rho_obs = [r["spearman_rho"] for r in rows if not np.isnan(r["spearman_rho"])]
        if rho_obs:
            rho_max = max(rho_obs)
            envelope = rho_max * (C_vals.min() / C_vals)
            result["envelope"] = {
                "delta": delta_arr.tolist(),
                "predicted_rho": envelope.tolist(),
                "k": k,
                "formula": "rho_max * C_min / C(k,Delta)  where C=1+k*Delta",
            }

    with open(output_dir / "density_sweep_result.json", "w") as f:
        json.dump(result, f, indent=2)

    _sweep_figure(rows, result.get("envelope"), output_dir / "rho_vs_delta.pdf")
    return result


def _sweep_figure(
    rows: list[dict[str, Any]],
    envelope: dict[str, Any] | None,
    out_path: Path,
) -> None:
    """Save ρ-vs-Δ scatter with the Theorem B predicted envelope."""
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        logger.warning("matplotlib not available; skipping density-sweep figure")
        return

    fig, ax = plt.subplots(figsize=(5, 4))
    deltas = [r["mean_max_degree"] for r in rows]
    rhos = [r["spearman_rho"] for r in rows]

    ax.scatter(deltas, rhos, color="#2166ac", zorder=5, label="Observed ρ")
    for row in rows:
        ax.annotate(
            row["label"],
            (row["mean_max_degree"], row["spearman_rho"]),
            fontsize=6,
            xytext=(3, 3),
            textcoords="offset points",
        )

    if envelope is not None:
        env_delta = np.array(envelope["delta"])
        env_rho = np.array(envelope["predicted_rho"])
        order = np.argsort(env_delta)
        ax.plot(
            env_delta[order],
            env_rho[order],
            "--",
            color="#d6604d",
            linewidth=1.5,
            label=f"B-cond envelope (k={envelope['k']})",
        )

    ax.set_xlabel("Mean max-degree $\\Delta$")
    ax.set_ylabel("Spearman $\\rho$($d_I$, HGED)")
    ax.set_ylim(0, 1.05)
    ax.legend(fontsize=8)
    ax.set_title("Density sweep — Theorem B Δ-dependence")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    logger.info("Saved density sweep figure to %s", out_path)
