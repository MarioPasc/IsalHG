"""Information-content analysis: IsalHG bits vs incidence-list bits.

Ports IsalGraph Table 1 methodology:
- Fixed-width code: B_IsalHG = |w| * log2(|Σ_HG(k)|)
- Competitor: B_incidence = incidence-list encoding (n-1 vertex bits + arity
  address bits per edge)
- Compression ratio r = B_incidence / B_IsalHG; r > 1 favours IsalHG.
- One-sided Wilcoxon signed-rank on r - 1 > 0.
- OLS: B_IsalHG = a + β·B_incidence; β < 1 confirms systematic compression.

Usage::

    from experiments.article.analysis.information_content import analyze_info_content
    result = analyze_info_content(info_content_json, output_dir)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


def analyze_info_content(
    info_content_json: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Compute Wilcoxon test, OLS, and compression-ratio summary.

    Parameters
    ----------
    info_content_json : Path
        ``info_content.json`` produced by ``run_info_content_cell``.
    output_dir : Path
        Where to write ``info_content_result.json`` and figure.

    Returns
    -------
    dict
        Keys: median_compression_ratio, fraction_shorter, wilcoxon_statistic,
        wilcoxon_pvalue, ols_beta, ols_intercept, n_items.
    """
    from scipy.stats import wilcoxon

    output_dir.mkdir(parents=True, exist_ok=True)
    with open(info_content_json) as f:
        data = json.load(f)

    records = data.get("records", [])
    if not records:
        logger.warning("No records in %s", info_content_json)
        result: dict[str, Any] = {"status": "empty", "n_items": 0}
        with open(output_dir / "info_content_result.json", "w") as f:
            json.dump(result, f)
        return result

    b_isal = np.array([r["bits_isalhg"] for r in records])
    b_inc = np.array([r["bits_incidence_list"] for r in records])
    ratios = np.array([r["compression_ratio"] for r in records])

    # Wilcoxon signed-rank: one-sided H0: r - 1 <= 0, H1: r - 1 > 0
    try:
        stat, pval = wilcoxon(ratios - 1.0, alternative="greater")
        wilcoxon_stat = float(stat)
        wilcoxon_pval = float(pval)
    except Exception as exc:
        logger.warning("Wilcoxon failed: %s", exc)
        wilcoxon_stat = float("nan")
        wilcoxon_pval = float("nan")

    # OLS: B_IsalHG = alpha + beta * B_incidence
    beta, alpha = _ols(b_inc, b_isal)

    result = {
        "n_items": len(records),
        "median_compression_ratio": float(np.median(ratios)),
        "mean_compression_ratio": float(ratios.mean()),
        "fraction_shorter": float(np.mean(ratios > 1.0)),
        "wilcoxon_statistic": wilcoxon_stat,
        "wilcoxon_pvalue": wilcoxon_pval,
        "wilcoxon_alternative": "greater (r > 1 => IsalHG shorter)",
        "ols_beta": float(beta),
        "ols_intercept": float(alpha),
        "bits_isalhg_median": float(np.median(b_isal)),
        "bits_incidence_median": float(np.median(b_inc)),
        "k": data.get("k"),
        "alphabet_size": data.get("alphabet_size"),
    }

    with open(output_dir / "info_content_result.json", "w") as f:
        json.dump(result, f, indent=2)

    _bits_figure(b_isal, b_inc, ratios, result, output_dir / "info_content.pdf")

    logger.info(
        "Info-content: median_r=%.3f  frac_shorter=%.3f  Wilcoxon_p=%.4g  beta=%.3f",
        result["median_compression_ratio"],
        result["fraction_shorter"],
        wilcoxon_pval,
        beta,
    )
    return result


def _ols(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """Return (slope, intercept) for OLS y = alpha + beta*x."""
    if len(x) < 2:
        return float("nan"), float("nan")
    x_c = x - x.mean()
    denom = x_c.dot(x_c)
    beta = float(x_c.dot(y) / denom) if denom > 0 else float("nan")
    alpha = float(y.mean() - beta * x.mean())
    return beta, alpha


def _bits_figure(
    b_isal: np.ndarray,
    b_inc: np.ndarray,
    ratios: np.ndarray,
    result: dict[str, Any],
    out_path: Path,
) -> None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        logger.warning("matplotlib not available; skipping info-content figure")
        return

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))

    # Left: scatter B_IsalHG vs B_incidence with OLS line
    ax = axes[0]
    ax.scatter(b_inc, b_isal, alpha=0.5, s=10, color="#2166ac", rasterized=True)
    x_line = np.array([b_inc.min(), b_inc.max()])
    beta, alpha = result["ols_beta"], result["ols_intercept"]
    ax.plot(x_line, alpha + beta * x_line, color="#d6604d", linewidth=1.5, label=f"β={beta:.3f}")
    ax.plot(x_line, x_line, "k--", linewidth=0.8, alpha=0.5, label="β=1 (equal)")
    ax.set_xlabel("$B_{\\mathrm{incidence}}$ (bits)")
    ax.set_ylabel("$B_{\\mathrm{IsalHG}}$ (bits)")
    ax.set_title(f"IsalHG compression  (β={beta:.3f} < 1)")
    ax.legend(fontsize=8)

    # Right: compression ratio histogram
    ax2 = axes[1]
    ax2.hist(ratios, bins=25, color="#4dac26", alpha=0.85, edgecolor="white", linewidth=0.3)
    ax2.axvline(1.0, color="k", linestyle="--", linewidth=1.0, label="r=1 (break-even)")
    ax2.axvline(
        result["median_compression_ratio"],
        color="#d6604d",
        linestyle="--",
        linewidth=1.5,
        label=f"median={result['median_compression_ratio']:.2f}",
    )
    ax2.set_xlabel("Compression ratio $r = B_{\\mathrm{incidence}} / B_{\\mathrm{IsalHG}}$")
    ax2.set_ylabel("Count")
    ax2.set_title(
        f"Wilcoxon p={result['wilcoxon_pvalue']:.3g}  "
        f"frac<incidence={result['fraction_shorter']:.3f}"
    )
    ax2.legend(fontsize=8)

    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    logger.info("Saved info-content figure to %s", out_path)
