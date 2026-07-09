"""E3 — perturbation-ladder scaling analysis.

Plots d_I(base, H_t) vs edit budget t and per-step increments.
The per-step increments are the T-TBb proxy for R(e)/T_span(e).

Usage::

    from experiments.article.analysis.ladder import analyze_ladder
    result = analyze_ladder(ladder_json_path, output_dir)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


def analyze_ladder(
    ladder_json: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Analyse perturbation-ladder d_I tracking.

    Parameters
    ----------
    ladder_json : Path
        ``ladder.json`` produced by ``run_ladder_cell``.
    output_dir : Path
        Where to write ``ladder_result.json`` and figures.

    Returns
    -------
    dict
        Summary: monotonicity stats, mean increment per op type, T-TBb proxy.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(ladder_json) as f:
        data = json.load(f)

    ladders = data.get("ladders", [])
    if not ladders:
        logger.warning("No ladder data in %s", ladder_json)
        result: dict[str, Any] = {"status": "empty"}
        with open(output_dir / "ladder_result.json", "w") as f:
            json.dump(result, f)
        return result

    # Flatten all steps across ladders
    all_budgets: list[float] = []
    all_d_I: list[float] = []
    all_increments: list[float] = []
    per_op_increments: dict[str, list[float]] = {}
    non_monotone_count = 0

    for ladder in ladders:
        steps = ladder.get("steps", [])
        prev_d = 0.0
        for step in steps:
            b = float(step["budget_from_base"])
            d = float(step["d_I_from_base"])
            inc = float(step["d_I_increment"])
            op = step.get("op", "unknown")

            all_budgets.append(b)
            all_d_I.append(d)
            all_increments.append(inc)
            per_op_increments.setdefault(op, []).append(inc)

            if d < prev_d - 1e-9:
                non_monotone_count += 1
            prev_d = d

    budgets_arr = np.array(all_budgets)
    d_I_arr = np.array(all_d_I)
    incr_arr = np.array(all_increments)

    # T-TBb proxy: distribution of per-step d_I increments
    per_op_mean_incr = {op: float(np.mean(vals)) for op, vals in per_op_increments.items()}

    result = {
        "n_ladders": len(ladders),
        "n_steps_total": len(all_budgets),
        "non_monotone_steps": non_monotone_count,
        "non_monotone_fraction": non_monotone_count / max(len(all_budgets), 1),
        "mean_d_I_increment": float(incr_arr.mean()) if len(incr_arr) > 0 else 0.0,
        "median_d_I_increment": float(np.median(incr_arr)) if len(incr_arr) > 0 else 0.0,
        "max_d_I_increment": float(incr_arr.max()) if len(incr_arr) > 0 else 0.0,
        "per_op_mean_increment": per_op_mean_incr,
        "tbb_proxy_note": (
            "per_op_mean_increment values are the per-edit d_I proxies for "
            "R(e)/T_span(e) in T-TBb (pointer-run amortization analysis)"
        ),
    }

    with open(output_dir / "ladder_result.json", "w") as f:
        json.dump(result, f, indent=2)

    _ladder_figures(ladders, budgets_arr, d_I_arr, incr_arr, result, output_dir)

    logger.info(
        "E3 ladder: n_ladders=%d  mean_incr=%.3f  non_monotone=%.1f%%",
        len(ladders),
        result["mean_d_I_increment"],
        100 * result["non_monotone_fraction"],
    )
    return result


def _ladder_figures(
    ladders: list[dict],
    budgets: np.ndarray,
    d_I: np.ndarray,
    increments: np.ndarray,
    result: dict[str, Any],
    out_dir: Path,
) -> None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        logger.warning("matplotlib not available; skipping ladder figures")
        return

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))

    # Left: d_I(base, H_t) vs budget per ladder
    ax = axes[0]
    colors = plt.cm.Blues(np.linspace(0.4, 0.9, max(len(ladders), 1)))  # type: ignore[attr-defined]
    for i, ladder in enumerate(ladders):
        steps = ladder.get("steps", [])
        if not steps:
            continue
        bud = [0.0] + [s["budget_from_base"] for s in steps]
        d_vals = [0.0] + [s["d_I_from_base"] for s in steps]
        ax.plot(
            bud,
            d_vals,
            "o-",
            color=colors[i],
            linewidth=1.2,
            markersize=4,
            label=f"ladder {ladder['ladder_id']}",
        )

    ax.set_xlabel("Edit budget $t$ (Qin cost upper bound)")
    ax.set_ylabel("$d_I$(base, $H_t$)")
    ax.set_title("E3 — perturbation ladder tracking")
    if len(ladders) <= 6:
        ax.legend(fontsize=7)

    # Right: per-step increment histogram (T-TBb proxy)
    ax2 = axes[1]
    ax2.hist(increments, bins=20, color="#4dac26", alpha=0.85, edgecolor="white", linewidth=0.3)
    ax2.axvline(
        result["median_d_I_increment"],
        color="#d6604d",
        linestyle="--",
        linewidth=1.5,
        label=f"median={result['median_d_I_increment']:.2f}",
    )
    ax2.set_xlabel("Per-step $d_I$ increment ($d_I(H_{t-1}, H_t)$)")
    ax2.set_ylabel("Count")
    ax2.set_title("T-TBb proxy: per-edit $d_I$ increment")
    ax2.legend(fontsize=8)

    fig.tight_layout()
    fig.savefig(out_dir / "ladder.pdf", dpi=150)
    plt.close(fig)
    logger.info("Saved ladder figure to %s", out_dir / "ladder.pdf")
