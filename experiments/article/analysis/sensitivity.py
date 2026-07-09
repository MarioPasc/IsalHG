"""E2b — single-edit sensitivity histogram.

Tests the Proposition 6.0 coherence characterization (stability.md §3):
- Generic sparse: near-unimodal histogram, O(kΔ) peak.
- Coherent-tie symmetric designs (Fano, STS(9)): near-unimodal O(kΔ).
- Incoherent-tie designs (STS(13), GQ(2,2)): heavy-tailed or bimodal.

Usage::

    from experiments.article.analysis.sensitivity import analyze_sensitivity
    result = analyze_sensitivity(sensitivity_json_path, output_dir)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


def analyze_sensitivity(
    sensitivity_json: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Analyse single-edit sensitivity values from a runner sensitivity cell.

    Parameters
    ----------
    sensitivity_json : Path
        ``sensitivity.json`` produced by ``run_sensitivity_cell``.
    output_dir : Path
        Where to write ``sensitivity_result.json`` and histogram figure.

    Returns
    -------
    dict
        Summary: per-op mean/median, distribution shape stats, heavy-tail
        indicator.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(sensitivity_json) as f:
        data = json.load(f)

    all_s_e = np.array(data.get("all_s_e", []), dtype=float)
    per_op = data.get("per_op_mean", {})

    if len(all_s_e) == 0:
        logger.warning("No s(e) values found in %s", sensitivity_json)
        result: dict[str, Any] = {"status": "empty", "n_edits": 0}
        with open(output_dir / "sensitivity_result.json", "w") as f:
            json.dump(result, f)
        return result

    # Basic distribution statistics
    q75, q25 = np.percentile(all_s_e, [75, 25])
    iqr = q75 - q25
    heavy_tail_fraction = float(np.mean(all_s_e > (q75 + 1.5 * iqr)))

    result = {
        "n_edits": len(all_s_e),
        "mean_sensitivity": float(all_s_e.mean()),
        "median_sensitivity": float(np.median(all_s_e)),
        "std_sensitivity": float(all_s_e.std()),
        "iqr_sensitivity": float(iqr),
        "max_sensitivity": float(all_s_e.max()),
        "heavy_tail_fraction": heavy_tail_fraction,
        "per_op_mean": per_op,
        "per_op_count": data.get("per_op_count", {}),
    }

    with open(output_dir / "sensitivity_result.json", "w") as f:
        json.dump(result, f, indent=2)

    _histogram_figure(all_s_e, per_op, result, output_dir / "sensitivity_histogram.pdf")

    logger.info(
        "E2b sensitivity: n=%d  median=%.2f  heavy_tail=%.3f",
        len(all_s_e),
        result["median_sensitivity"],
        heavy_tail_fraction,
    )
    return result


def _histogram_figure(
    all_s_e: np.ndarray,
    per_op: dict[str, float],
    result: dict[str, Any],
    out_path: Path,
) -> None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        logger.warning("matplotlib not available; skipping sensitivity figure")
        return

    fig, axes = plt.subplots(1, 2, figsize=(9, 4))

    # Left: overall histogram
    ax = axes[0]
    ax.hist(all_s_e, bins=30, color="#2166ac", alpha=0.8, edgecolor="white", linewidth=0.3)
    ax.axvline(
        result["median_sensitivity"],
        color="#d6604d",
        linestyle="--",
        linewidth=1.5,
        label=f"median={result['median_sensitivity']:.2f}",
    )
    ax.set_xlabel("$s(e) = d_I(H, H \\oplus e)$")
    ax.set_ylabel("Count")
    ax.set_title(f"Single-edit sensitivity (n={result['n_edits']})")
    ax.legend(fontsize=8)

    # Right: per-op mean bar chart
    ax2 = axes[1]
    if per_op:
        ops = list(per_op.keys())
        means = [per_op[op] for op in ops]
        ax2.bar(range(len(ops)), means, color="#4dac26", alpha=0.85)
        ax2.set_xticks(range(len(ops)))
        ax2.set_xticklabels(ops, rotation=30, ha="right", fontsize=8)
        ax2.set_ylabel("Mean $s(e)$")
        ax2.set_title("Per-op type mean sensitivity")

    fig.suptitle(
        f"heavy-tail fraction={result['heavy_tail_fraction']:.3f}  "
        f"IQR={result['iqr_sensitivity']:.2f}",
        fontsize=9,
    )
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    logger.info("Saved sensitivity figure to %s", out_path)
