"""Render Figures 1-3 + Tables 1-2 for the preprint.

Reads the CSVs emitted by
:mod:`experiments.preprint.pipeline.analysis.aggregate` and produces:

- ``figures/fig1_wallclock_heatgrid.{pdf,png}``: heat-grid coloured by
  ``log10(T_isalhg / min(T_levi))``. Rows = ``(r, c)`` pairs, cols = ``n``.
  Blue = IsalHG faster; red = Levi faster.
- ``figures/fig2_memory_heatgrid.{pdf,png}``: heat-grid of
  ``max_rss(isalhg) / max_rss(best Levi)``, same axes.
- ``figures/fig3_fp_bytelen_box.{pdf,png}``: per-(n, r, c) box-plot of
  fingerprint byte lengths, grouped by backend.
- ``tables/table1_per_cell_summary.tex``: 18-row LaTeX booktabs table.
- ``tables/table2_correctness.tex``: one-row LaTeX assertion.

Usage
-----
::

    python -m experiments.preprint.pipeline.analysis.figures \\
        --aggregate-dir experiments/preprint/pipeline/analysis_output \\
        --output-dir   experiments/preprint/pipeline/analysis_output
"""

from __future__ import annotations

import argparse
import csv
import logging
import math
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_BACKENDS: tuple[str, ...] = ("isalhg", "pynauty_levi", "bliss_levi", "traces_levi")
_LEVI_BACKENDS: tuple[str, ...] = ("pynauty_levi", "bliss_levi", "traces_levi")


# ---------------------------------------------------------------------------
# CSV reader
# ---------------------------------------------------------------------------
def _read_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(path)
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for raw in reader:
            row: dict[str, Any] = {}
            for k, v in raw.items():
                if v == "" or v is None:
                    row[k] = None
                else:
                    row[k] = _coerce(v)
            rows.append(row)
    return rows


def _coerce(value: str) -> Any:
    if value.lower() in ("true", "false"):
        return value.lower() == "true"
    try:
        if "." in value or "e" in value.lower():
            return float(value)
        return int(value)
    except ValueError:
        return value


def _sorted_nrc(rows: list[dict[str, Any]]) -> list[tuple[int, int, float]]:
    keys = {(int(r["n"]), int(r["r"]), float(r["c"])) for r in rows if r.get("n") is not None}
    return sorted(keys)


# ---------------------------------------------------------------------------
# Figure 1 + 2: heat-grids
# ---------------------------------------------------------------------------
def _heatgrid_matrix(
    per_nrc: list[dict[str, Any]],
    value_fn,
    n_values: list[int],
    rc_pairs: list[tuple[int, float]],
) -> list[list[float | None]]:
    by_key: dict[tuple[int, int, float], dict[str, Any]] = {}
    for row in per_nrc:
        if row.get("n") is None:
            continue
        key = (int(row["n"]), int(row["r"]), float(row["c"]))
        by_key[key] = row

    matrix: list[list[float | None]] = []
    for r, c in rc_pairs:
        row_out: list[float | None] = []
        for n in n_values:
            entry = by_key.get((n, r, c))
            row_out.append(value_fn(entry) if entry else None)
        matrix.append(row_out)
    return matrix


def _draw_heatgrid(
    matrix: list[list[float | None]],
    *,
    n_values: list[int],
    rc_pairs: list[tuple[int, float]],
    title: str,
    cbar_label: str,
    output_basepath: Path,
    cmap_name: str = "RdBu_r",
    vmin: float | None = None,
    vmax: float | None = None,
) -> None:
    import matplotlib.pyplot as plt
    import numpy as np

    from isalhg.viz.style import apply_ieee_style, save_figure

    apply_ieee_style()

    arr = np.array(
        [[np.nan if v is None else float(v) for v in row] for row in matrix],
        dtype=float,
    )

    finite = arr[np.isfinite(arr)]
    auto_bound = float(np.max(np.abs(finite))) if finite.size else 1.0
    if vmin is None:
        vmin = -auto_bound
    if vmax is None:
        vmax = auto_bound
    bound = max(abs(vmin), abs(vmax))

    fig, ax = plt.subplots(figsize=(5.0, 3.4))
    im = ax.imshow(arr, cmap=cmap_name, vmin=vmin, vmax=vmax, aspect="auto")

    ax.set_xticks(range(len(n_values)))
    ax.set_xticklabels([f"n={n}" for n in n_values])
    ax.set_yticks(range(len(rc_pairs)))
    ax.set_yticklabels([f"r={r}, c={c:g}" for r, c in rc_pairs])
    ax.set_title(title)

    # Annotate cells with their value (or DNF).
    for i, row in enumerate(matrix):
        for j, v in enumerate(row):
            label = "DNF" if v is None or (isinstance(v, float) and math.isnan(v)) else f"{v:+.2f}"
            ax.text(
                j,
                i,
                label,
                ha="center",
                va="center",
                fontsize=7,
                color="black" if -bound / 2 <= (v or 0) <= bound / 2 else "white",
            )

    cbar = fig.colorbar(im, ax=ax, shrink=0.85)
    cbar.set_label(cbar_label)

    fig.tight_layout()
    save_figure(fig, output_basepath, formats=("pdf", "png"))
    plt.close(fig)


def _value_log_ratio_time(row: dict[str, Any]) -> float | None:
    t_isalhg = row.get("median_time_s_isalhg")
    levi_times = [row.get(f"median_time_s_{b}") for b in _LEVI_BACKENDS]
    levi_clean = [v for v in levi_times if v is not None and v > 0]
    if not (t_isalhg and t_isalhg > 0 and levi_clean):
        return None
    return math.log10(t_isalhg / min(levi_clean))


def _value_log_ratio_rss(row: dict[str, Any]) -> float | None:
    rss_isalhg = row.get("max_peak_rss_bytes_isalhg")
    levi_rss = [row.get(f"max_peak_rss_bytes_{b}") for b in _LEVI_BACKENDS]
    levi_clean = [v for v in levi_rss if v is not None and v > 0]
    if not (rss_isalhg and rss_isalhg > 0 and levi_clean):
        return None
    return math.log10(rss_isalhg / min(levi_clean))


def _axes_orderings(per_nrc: list[dict[str, Any]]) -> tuple[list[int], list[tuple[int, float]]]:
    nrc = _sorted_nrc(per_nrc)
    n_values = sorted({n for n, _, _ in nrc})
    rc_pairs = sorted({(r, c) for _, r, c in nrc})
    return n_values, rc_pairs


# ---------------------------------------------------------------------------
# Figure 3: fingerprint byte length box-plot
# ---------------------------------------------------------------------------
def _draw_fp_bytelen_box(
    per_cell: list[dict[str, Any]],
    output_basepath: Path,
) -> None:
    import matplotlib.pyplot as plt

    from isalhg.viz.style import apply_ieee_style, save_figure

    apply_ieee_style()

    nrc_keys = _sorted_nrc(per_cell)
    n_groups = len(nrc_keys)
    fig, ax = plt.subplots(figsize=(7.0, 4.0))

    width = 0.18
    backend_palette = {
        "isalhg": "#332288",
        "pynauty_levi": "#117733",
        "bliss_levi": "#88CCEE",
        "traces_levi": "#CC6677",
    }

    for b_idx, backend in enumerate(_BACKENDS):
        per_group: list[list[float]] = []
        for n, r, c in nrc_keys:
            vals = [
                float(row["fp_bytes_length"])
                for row in per_cell
                if row.get("backend") == backend
                and row.get("n") == n
                and row.get("r") == r
                and float(row.get("c") or 0) == c
                and row.get("fp_bytes_length") is not None
            ]
            per_group.append(vals)
        positions = [i + (b_idx - 1.5) * width for i in range(n_groups)]
        bp = ax.boxplot(
            per_group,
            positions=positions,
            widths=width * 0.9,
            patch_artist=True,
            showfliers=False,
        )
        for patch in bp["boxes"]:
            patch.set_facecolor(backend_palette[backend])
            patch.set_alpha(0.75)
        ax.plot([], [], color=backend_palette[backend], label=backend, linewidth=4)

    ax.set_yscale("log")
    ax.set_xticks(range(n_groups))
    ax.set_xticklabels([f"n={n} r={r} c={c:g}" for n, r, c in nrc_keys], rotation=60, ha="right")
    ax.set_ylabel("Fingerprint length (bytes)")
    ax.set_title("Fingerprint byte length per backend, per (n, r, c) cell")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, axis="y", alpha=0.3)

    fig.tight_layout()
    save_figure(fig, output_basepath, formats=("pdf", "png"))
    plt.close(fig)


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------
def _table1(per_nrc: list[dict[str, Any]], dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append(r"\begin{tabular}{rrrrrrrrrr}")
    lines.append(r"\toprule")
    lines.append(
        r"$n$ & $r$ & $c$ & "
        r"$T_{\text{isalhg}}$ (s) & $T_{\text{pynauty}}$ (s) & $T_{\text{bliss}}$ (s) & "
        r"$T_{\text{traces}}$ (s) & speedup & DNF$_{\text{isalhg}}$ & DNF$_{\text{best Levi}}$ \\"
    )
    lines.append(r"\midrule")
    for row in sorted(per_nrc, key=lambda r: (int(r["n"]), int(r["r"]), float(r["c"]))):
        speedup = row.get("geomean_isalhg_over_best_levi")
        speedup_str = "DNF" if speedup is None else f"{speedup:.2f}"
        levi_dnfs = [int(row.get(f"dnf_count_{b}") or 0) for b in _LEVI_BACKENDS]
        lines.append(
            f"{row['n']} & {row['r']} & {row['c']} & "
            f"{_fmt(row.get('median_time_s_isalhg'))} & "
            f"{_fmt(row.get('median_time_s_pynauty_levi'))} & "
            f"{_fmt(row.get('median_time_s_bliss_levi'))} & "
            f"{_fmt(row.get('median_time_s_traces_levi'))} & "
            f"{speedup_str} & "
            f"{int(row.get('dnf_count_isalhg') or 0)} & "
            f"{min(levi_dnfs) if levi_dnfs else 0} \\\\"
        )
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("wrote %s", dest)


def _table2(correctness: list[dict[str, Any]], dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not correctness:
        dest.write_text("", encoding="utf-8")
        return
    row = correctness[0]
    lines = [
        r"\begin{tabular}{lrrrr}",
        r"\toprule",
        r"cells & pairs checked & pass rate & failures (isalhg) & failures (Levi total) \\",
        r"\midrule",
        (
            f"{int(row.get('n_cells') or 0)} & "
            f"{int(row.get('positive_pair_checked_total') or 0)} & "
            f"{_fmt(row.get('positive_pair_pass_rate'))} & "
            f"{int(row.get('failures_isalhg') or 0)} & "
            + str(sum(int(row.get(f"failures_{b}") or 0) for b in _LEVI_BACKENDS))
            + r" \\"
        ),
        r"\bottomrule",
        r"\end{tabular}",
    ]
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("wrote %s", dest)


def _fmt(value: Any) -> str:
    if value is None:
        return "--"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return str(value)
    if v == 0:
        return "0"
    if v >= 1:
        return f"{v:.2f}"
    return f"{v:.3g}"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aggregate-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--log-level", default="INFO", choices=("DEBUG", "INFO", "WARNING", "ERROR")
    )
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    per_cell = _read_csv(args.aggregate_dir / "per_cell.csv")
    per_nrc = _read_csv(args.aggregate_dir / "per_nrc.csv")
    correctness = _read_csv(args.aggregate_dir / "correctness.csv")

    figures_dir = args.output_dir / "figures"
    tables_dir = args.output_dir / "tables"
    figures_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)

    n_values, rc_pairs = _axes_orderings(per_nrc)

    wallclock_matrix = _heatgrid_matrix(per_nrc, _value_log_ratio_time, n_values, rc_pairs)
    _draw_heatgrid(
        wallclock_matrix,
        n_values=n_values,
        rc_pairs=rc_pairs,
        title="Wall-clock characterisation (log10 ratio)",
        cbar_label=r"$\log_{10}(T_{\rm isalhg}\,/\,\min T_{\rm Levi})$",
        output_basepath=figures_dir / "fig1_wallclock_heatgrid",
    )

    memory_matrix = _heatgrid_matrix(per_nrc, _value_log_ratio_rss, n_values, rc_pairs)
    _draw_heatgrid(
        memory_matrix,
        n_values=n_values,
        rc_pairs=rc_pairs,
        title="Memory characterisation (log10 ratio)",
        cbar_label=r"$\log_{10}({\rm RSS}_{\rm isalhg}\,/\,\min {\rm RSS}_{\rm Levi})$",
        output_basepath=figures_dir / "fig2_memory_heatgrid",
    )

    _draw_fp_bytelen_box(per_cell, figures_dir / "fig3_fp_bytelen_box")

    _table1(per_nrc, tables_dir / "table1_per_cell_summary.tex")
    _table2(correctness, tables_dir / "table2_correctness.tex")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
