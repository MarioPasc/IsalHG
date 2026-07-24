"""G2 geometry-pillar analysis: sensitivity profiles + ladder response (T-M5g).

Post-processes ``g2_sensitivity.json`` and ``g2_design_sensitivity.json`` outputs
from ``runner.py`` into:

1. **Contrast figure** — side-by-side histograms of ``s_e_isalhg`` vs
   ``s_e_nauty`` per density regime and per design fixture (ours compact +
   structured; nauty avalanche-everywhere).
2. **Three-regime confrontation table** — heavy-tail fraction and IQR per
   regime, confronting the prediction from ``stability.md`` §4.2.
3. **Ladder-response figure** — ``d_I(H_0, H_t)`` vs Qin budget ``t`` per
   corpus (from the existing ``ladder.json`` outputs; reused via
   ``analysis/ladder.py``).

All figures are saved as PDF under ``{output_dir}/``. The analysis module
can also be called programmatically by other scripts; CLI usage is::

    python -m experiments.article.analysis.g2 \\
        --sensitivity-json /path/to/g2_sensitivity.json \\
        --design-json /path/to/g2_design_sensitivity.json \\
        --output-dir /path/to/figs/

"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Regime-prediction record (confronts stability.md §4.2)
# ---------------------------------------------------------------------------

_REGIME_PREDICTION: dict[str, str] = {
    # random sparse/medium/dense corpora
    "sparse": "unimodal",
    "medium": "unimodal",
    "dense": "unimodal",
    # design fixtures (hand-built, T-M5g keys)
    "fano_plane": "unimodal",  # small, coherent ties
    "sts_9": "unimodal",  # medium, coherent ties
    "cyclic_triple_orbit_13": "heavy-tailed",  # incoherent ties (C13)
    "gq_2_2_doily": "heavy-tailed",  # incoherent ties (GQ(2,2))
    # Stratum A catalog designs (T-M7q re-run; key = item_id from DATA_MANIFEST.stratum_a_ids).
    # Reconciled against the T-M7m prune (dropped 3 complete uniforms) and
    # the T-M7o additions (3 longer tight cycles).  17 ids total.
    # arity-3: same regime as T-M5g fixtures
    "sts7": "unimodal",  # Fano plane; max_arity=3, coherent STS(7)
    "sts9": "unimodal",  # coherent STS(9)
    "gq22": "heavy-tailed",  # GQ(2,2); incoherent ties — was falsified at k=3
    "loose_path_k3": "unimodal",  # path-like, low tie diversity
    "tight_path_k3": "unimodal",
    "loose_cycle_k3": "unimodal",
    "tight_cycle_k3": "unimodal",
    # arity-4: all structurally regular — predicted unimodal even at max_arity=4
    # (heavy-tail requires incoherent ties, not just higher arity)
    "loose_path_k4": "unimodal",
    "tight_path_k4": "unimodal",
    "loose_cycle_k4": "unimodal",
    "tight_cycle_k4": "unimodal",
    "tight_cycle_k4_n8": "unimodal",  # n=8 m=8 tight cycle, arity-4 (T-M7o)
    "tight_cycle_k4_n10": "unimodal",  # n=10 m=10 tight cycle, arity-4 (T-M7o)
    # arity-5: same reasoning
    "loose_path_k5": "unimodal",
    "tight_path_k5": "unimodal",
    "tight_cycle_k5": "unimodal",
    "tight_cycle_k5_n8": "unimodal",  # n=8 m=8 tight cycle, arity-5 (T-M7o)
}


def _heavy_tail_frac(values: list[float]) -> float:
    """Fraction of values beyond Q3 + 1.5·IQR (Tukey's fence)."""
    if len(values) < 4:
        return 0.0
    arr = np.array(values, dtype=float)
    q25, q75 = float(np.percentile(arr, 25)), float(np.percentile(arr, 75))
    iqr = q75 - q25
    fence = q75 + 1.5 * iqr
    return float(np.mean(arr > fence))


def _iqr(values: list[float]) -> float:
    if len(values) < 4:
        return 0.0
    arr = np.array(values, dtype=float)
    return float(np.percentile(arr, 75) - np.percentile(arr, 25))


def confront_regime_predictions(
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return per-regime confrontation rows.

    Parameters
    ----------
    records : list[dict]
        Records from either ``g2_sensitivity.json`` or
        ``g2_design_sensitivity.json``.

    Returns
    -------
    list[dict]
        Each row: regime, n_edits, heavy_tail_frac, iqr_isalhg, iqr_nauty,
        prediction, outcome (confirmed | falsified | inconclusive).
    """
    rows = []
    # Group by regime / design_name
    groups: dict[str, list[float]] = {}
    nauty_groups: dict[str, list[float]] = {}
    for rec in records:
        key = rec.get("design_name") or rec.get("regime", "random")
        for edit in rec.get("edits", []):
            groups.setdefault(key, []).append(edit["s_e_isalhg"])
            nauty_groups.setdefault(key, []).append(edit["s_e_nauty"])

    for key, vals in groups.items():
        htf = _heavy_tail_frac(vals)
        prediction = _REGIME_PREDICTION.get(key, "unknown")
        if len(vals) < 4:
            outcome = "inconclusive"
        elif prediction == "unimodal":
            outcome = "confirmed" if htf < 0.2 else "falsified"
        elif prediction == "heavy-tailed":
            outcome = "confirmed" if htf >= 0.15 else "falsified"
        else:
            outcome = "inconclusive"
        rows.append(
            {
                "regime": key,
                "n_edits": len(vals),
                "heavy_tail_frac": round(htf, 4),
                "iqr_isalhg": round(_iqr(vals), 4),
                "iqr_nauty": round(_iqr(nauty_groups.get(key, [])), 4),
                "prediction": prediction,
                "outcome": outcome,
            }
        )
    return rows


# ---------------------------------------------------------------------------
# Figure: contrast histogram (ours vs nauty per regime)
# ---------------------------------------------------------------------------


def plot_contrast_figure(
    records: list[dict[str, Any]],
    output_path: Path,
    title: str = "Sensitivity contrast: IsalHG vs nauty-Levi",
) -> None:
    """Render side-by-side s(e) histograms for IsalHG vs nauty per group.

    Parameters
    ----------
    records : list[dict]
        Records from g2_sensitivity.json or g2_design_sensitivity.json.
    output_path : Path
        Where to write the PDF figure.
    title : str
        Figure suptitle.
    """
    import matplotlib.pyplot as plt

    # Collect s(e) per group
    groups: dict[str, tuple[list[float], list[float]]] = {}
    for rec in records:
        key = rec.get("design_name") or rec.get("regime", "random")
        vals_i: list[float] = []
        vals_n: list[float] = []
        for edit in rec.get("edits", []):
            vals_i.append(edit["s_e_isalhg"])
            vals_n.append(edit["s_e_nauty"])
        if key in groups:
            groups[key][0].extend(vals_i)
            groups[key][1].extend(vals_n)
        else:
            groups[key] = (vals_i, vals_n)

    n_groups = len(groups)
    if n_groups == 0:
        logger.warning("No groups to plot in contrast figure.")
        return

    fig, axes = plt.subplots(
        n_groups,
        2,
        figsize=(10, 2.5 * n_groups),
        squeeze=False,
        sharey="row",
    )
    fig.suptitle(title, fontsize=12)

    for row_idx, (key, (vals_i, vals_n)) in enumerate(groups.items()):
        ax_ours = axes[row_idx, 0]
        ax_nauty = axes[row_idx, 1]

        bins_i = min(30, max(5, len(vals_i) // 5)) if vals_i else 10
        bins_n = min(30, max(5, len(vals_n) // 5)) if vals_n else 10

        ax_ours.hist(vals_i, bins=bins_i, color="#2171b5", alpha=0.8, edgecolor="white")
        ax_ours.set_title(f"{key} — IsalHG d_I", fontsize=9)
        ax_ours.set_xlabel("s(e) = d_I(H, H⊕e)", fontsize=8)
        ax_ours.set_ylabel("count", fontsize=8)

        ax_nauty.hist(vals_n, bins=bins_n, color="#d6604d", alpha=0.8, edgecolor="white")
        ax_nauty.set_title(f"{key} — nauty-Levi edit dist.", fontsize=9)
        ax_nauty.set_xlabel("s_nauty(e)", fontsize=8)

        if vals_i:
            htf = _heavy_tail_frac(vals_i)
            ax_ours.text(
                0.98,
                0.95,
                f"heavy-tail: {htf:.1%}",
                transform=ax_ours.transAxes,
                ha="right",
                va="top",
                fontsize=7,
                color="darkblue",
            )
        if vals_n:
            htf_n = _heavy_tail_frac(vals_n)
            ax_nauty.text(
                0.98,
                0.95,
                f"heavy-tail: {htf_n:.1%}",
                transform=ax_nauty.transAxes,
                ha="right",
                va="top",
                fontsize=7,
                color="darkred",
            )

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    logger.info("Contrast figure saved: %s", output_path)


# ---------------------------------------------------------------------------
# Main analysis entry point
# ---------------------------------------------------------------------------


def analyze_g2(
    sensitivity_json: Path | None,
    design_json: Path | None,
    output_dir: Path,
) -> dict[str, Any]:
    """Run the full G2 post-processing pipeline.

    Parameters
    ----------
    sensitivity_json : Path | None
        Path to ``g2_sensitivity.json``.
    design_json : Path | None
        Path to ``g2_design_sensitivity.json``.
    output_dir : Path
        Directory for output figures and the confrontation JSON.

    Returns
    -------
    dict
        Summary with ``confrontation_rows``, ``n_falsified``, and figure paths.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    all_records: list[dict[str, Any]] = []

    if sensitivity_json and sensitivity_json.exists():
        with open(sensitivity_json) as f:
            sens_data = json.load(f)
        all_records.extend(sens_data.get("records", []))
        plot_contrast_figure(
            sens_data.get("records", []),
            output_dir / "g2_contrast_random.pdf",
            title="Sensitivity contrast (random corpora): IsalHG vs nauty-Levi",
        )

    if design_json and design_json.exists():
        with open(design_json) as f:
            design_data = json.load(f)
        all_records.extend(design_data.get("records", []))
        plot_contrast_figure(
            design_data.get("records", []),
            output_dir / "g2_contrast_designs.pdf",
            title="Sensitivity contrast (design fixtures): IsalHG vs nauty-Levi",
        )

    confrontation_rows = confront_regime_predictions(all_records)
    n_falsified = sum(1 for r in confrontation_rows if r["outcome"] == "falsified")
    n_confirmed = sum(1 for r in confrontation_rows if r["outcome"] == "confirmed")

    summary: dict[str, Any] = {
        "confrontation_rows": confrontation_rows,
        "n_regimes": len(confrontation_rows),
        "n_confirmed": n_confirmed,
        "n_falsified": n_falsified,
        "n_inconclusive": len(confrontation_rows) - n_confirmed - n_falsified,
    }

    # Write the confrontation table as JSON for provenance
    conf_path = output_dir / "g2_regime_confrontation.json"
    with open(conf_path, "w") as f:
        json.dump(summary, f, indent=2)
    logger.info("Confrontation table: %s", conf_path)

    # Print summary to stderr (analysis script output)
    import sys

    print("\n=== G2 Three-regime confrontation ===", file=sys.stderr)
    header = f"{'Regime':<30} {'N':>6} {'HeavyTail':>10} {'IQR_ours':>10} "
    header += f"{'IQR_nauty':>10} {'Predict':>14} {'Outcome':>12}"
    print(header, file=sys.stderr)
    print("-" * len(header), file=sys.stderr)
    for row in confrontation_rows:
        flag = (
            "OK"
            if row["outcome"] == "confirmed"
            else ("!!" if row["outcome"] == "falsified" else "--")
        )
        print(
            f"{row['regime']:<30} {row['n_edits']:>6} {row['heavy_tail_frac']:>10.3f}"
            f" {row['iqr_isalhg']:>10.3f} {row['iqr_nauty']:>10.3f}"
            f" {row['prediction']:>14} {row['outcome']:>10} {flag}",
            file=sys.stderr,
        )
    print(
        f"\nResult: {n_confirmed} confirmed, {n_falsified} falsified, "
        f"{summary['n_inconclusive']} inconclusive.",
        file=sys.stderr,
    )

    return summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _cli() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="G2 sensitivity analysis: contrast figure + regime confrontation."
    )
    parser.add_argument("--sensitivity-json", type=Path, default=None)
    parser.add_argument("--design-json", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    analyze_g2(args.sensitivity_json, args.design_json, args.output_dir)


if __name__ == "__main__":
    _cli()
