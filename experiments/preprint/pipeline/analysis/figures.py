"""Render Figures 1-3 + Tables 1-2 for the preprint (Jun-25-final format).

All three figures share the same layout:

- **Hierarchical categorical x-axis.** A single ``r = 3`` group covers
  five ``n``-groups (``n ∈ {8, 12, 16, 20, 25}``), each of which is
  split into three ``c``-cells (``c ∈ {1.0, 1.5, 2.0}``) for a total
  of 15 x positions. The grouping is drawn with rounded boxes below
  the data axes; only the ``c`` value is printed on the data row.
- **One scatter + line per backend** (4 backends).
- **Power-law fit per backend.** For each backend the median per cell
  is regressed against ``n`` on a log-log scale, ``log10(y) = α + β
  · log10(n)``. The fitted exponent ``β`` is the headline scaling
  claim of the figure; the prefactor ``A = 10^α`` is reported in the
  legend for reproducibility but is the less interesting parameter.
- **Legend below the figure**, outside the data axes, with renamed
  entries (``isalhg → IsalHG``, ``pynauty_levi → Levi (Nauty)``, …)
  and the fitted ``β`` value appended to each entry.
- **No plot title** — the metric and units appear on the y-axis label
  and in the file name.

Fig 1: median wall-clock (ms) per cell, per backend.
Fig 2: max peak RSS (MB) per cell, per backend.
Fig 3: median fingerprint byte length per cell, per backend.

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
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_BACKENDS: tuple[str, ...] = ("isalhg", "pynauty_levi", "bliss_levi", "traces_levi")
_LEVI_BACKENDS: tuple[str, ...] = ("pynauty_levi", "bliss_levi", "traces_levi")

_BACKEND_DISPLAY: dict[str, str] = {
    "isalhg": "IsalHG",
    "pynauty_levi": "Levi (Nauty)",
    "bliss_levi": "Levi (Bliss)",
    "traces_levi": "Levi (Traces)",
}

# Paul Tol bright-qualitative palette (colour-blind safe).
_BACKEND_COLOR: dict[str, str] = {
    "isalhg": "#332288",
    "pynauty_levi": "#117733",
    "bliss_levi": "#0077BB",
    "traces_levi": "#CC3311",
}

_BACKEND_MARKER: dict[str, str] = {
    "isalhg": "o",
    "pynauty_levi": "s",
    "bliss_levi": "^",
    "traces_levi": "D",
}


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


# ---------------------------------------------------------------------------
# Grid + value extraction
# ---------------------------------------------------------------------------
def _grid_axes(per_nrc: list[dict[str, Any]]) -> tuple[list[int], list[float]]:
    n_vals = sorted({int(r["n"]) for r in per_nrc if r.get("n") is not None})
    c_vals = sorted({float(r["c"]) for r in per_nrc if r.get("c") is not None})
    return n_vals, c_vals


def _cell_index(n_vals: list[int], c_vals: list[float], n: int, c: float) -> int:
    """Position in the hierarchical x-axis: (n, c) pair → 0..N*C-1."""
    return n_vals.index(int(n)) * len(c_vals) + c_vals.index(float(c))


def _backend_series(
    per_nrc: list[dict[str, Any]],
    per_nrc_backend: list[dict[str, Any]],
    backend: str,
    metric: str,
) -> tuple[list[float], list[float]]:
    """Return ``(x_positions, y_values)`` for one backend over the 15 (n, c) cells.

    Both lists are sorted by ``x_position`` so the connecting line
    between scatter points respects the cell ordering. Without the
    sort, ``per_nrc.csv``'s row order leaks into the polyline and
    matplotlib draws zigzag artefacts across the figure.

    ``metric`` ∈ {"time_ms", "rss_mb", "fp_bytes"}. Y is the
    backend-specific median pulled from either ``per_nrc.csv`` (time,
    rss) or ``per_nrc_backend.csv`` (fp_bytes).
    """
    n_vals, c_vals = _grid_axes(per_nrc)
    items: list[tuple[float, float]] = []
    if metric == "fp_bytes":
        # per_nrc_backend.csv: rows keyed by (backend, n, r, c).
        for row in per_nrc_backend:
            if row.get("backend") != backend:
                continue
            n = row.get("n")
            c = row.get("c")
            v = row.get("median_fp_bytes_length")
            if n is None or c is None or v is None or float(v) <= 0:
                continue
            items.append((_cell_index(n_vals, c_vals, n, c), float(v)))
    else:
        key = {
            "time_ms": f"median_time_s_{backend}",
            "rss_mb": f"max_peak_rss_bytes_{backend}",
        }[metric]
        for row in per_nrc:
            n = row.get("n")
            c = row.get("c")
            v = row.get(key)
            if n is None or c is None or v is None:
                continue
            v = float(v)
            if v <= 0:
                continue
            if metric == "time_ms":
                v *= 1_000.0
            elif metric == "rss_mb":
                v /= 1_048_576.0
            items.append((_cell_index(n_vals, c_vals, n, c), v))
    items.sort(key=lambda kv: kv[0])
    pos = [kv[0] for kv in items]
    val = [kv[1] for kv in items]
    return pos, val


def _per_seed_box_data(
    per_cell: list[dict[str, Any]],
    n_vals: list[int],
    c_vals: list[float],
    backend: str,
    metric: str,
) -> tuple[list[float], list[list[float]]]:
    """Return ``(positions, distributions)`` for a backend's per-seed box plot.

    For each (n, c) cell, collect the 10 seed-level measurements from
    ``per_cell.csv`` (one row per seed). Empty/None cells (legacy
    DNFs) are omitted. The returned ``positions`` align with the same
    integer cell index used by the scatter/line plots.
    """
    key = {
        "time_ms": "median_time_s",
        "rss_mb": "peak_rss_bytes",
        "fp_bytes": "fp_bytes_length",
    }[metric]
    buckets: dict[tuple[int, float], list[float]] = {}
    for row in per_cell:
        if row.get("backend") != backend:
            continue
        n = row.get("n")
        c = row.get("c")
        v = row.get(key)
        if n is None or c is None or v is None:
            continue
        try:
            v = float(v)
        except (TypeError, ValueError):
            continue
        if v <= 0:
            continue
        if metric == "time_ms":
            v *= 1_000.0
        elif metric == "rss_mb":
            v /= 1_048_576.0
        buckets.setdefault((int(n), float(c)), []).append(v)

    positions: list[float] = []
    distributions: list[list[float]] = []
    for (n, c), values in sorted(buckets.items()):
        if n not in n_vals or c not in c_vals:
            continue
        positions.append(_cell_index(n_vals, c_vals, n, c))
        distributions.append(values)
    return positions, distributions


# ---------------------------------------------------------------------------
# Power-law fit
# ---------------------------------------------------------------------------
def _power_law_fit(
    n_per_cell: list[int],
    y_per_cell: list[float],
) -> tuple[float, float] | None:
    """Fit ``log10(y) = α + β · log10(n)``. Returns ``(α, β)`` or None.

    Treats each cell as one (n, y) sample — c is collapsed into the
    residual. This gives a single complexity exponent ``β`` per
    backend that ties the figure to a power-law in vertex count.
    """
    import numpy as np

    if len(n_per_cell) < 2:
        return None
    arr_n = np.asarray(n_per_cell, dtype=float)
    arr_y = np.asarray(y_per_cell, dtype=float)
    mask = (arr_n > 0) & (arr_y > 0) & np.isfinite(arr_y)
    if mask.sum() < 2:
        return None
    lx = np.log10(arr_n[mask])
    ly = np.log10(arr_y[mask])
    beta, alpha = np.polyfit(lx, ly, 1)
    return float(alpha), float(beta)


def _legend_label(
    backend: str,
    fit: tuple[float, float] | None,
) -> str:
    """Format ``Display Name — y ≈ A · n^β``."""
    name = _BACKEND_DISPLAY.get(backend, backend)
    if fit is None:
        return name
    alpha, beta = fit
    a_coef = 10**alpha
    # Use scientific notation when A is very small or very large.
    if a_coef == 0:
        a_str = "0"
    elif abs(a_coef) >= 1e4 or abs(a_coef) < 1e-2:
        a_str = f"{a_coef:.2e}"
    else:
        a_str = f"{a_coef:.3g}"
    return f"{name}  ($y \\approx {a_str} \\cdot n^{{{beta:.2f}}}$)"


# ---------------------------------------------------------------------------
# Hierarchical x-axis decoration
# ---------------------------------------------------------------------------
def _draw_hierarchical_xaxis(
    ax,
    *,
    n_vals: list[int],
    c_vals: list[float],
    r_value: int,
) -> None:
    """Draw two-level group boxes under the data axes (r → n → c).

    The data axes already show one tick per (n, c) cell at integer
    positions ``0 .. N*C - 1``. This helper:
      1. Replaces the default tick labels with the ``c`` value.
      2. Draws a row of ``n``-group rounded boxes immediately below
         the c-labels.
      3. Draws a single ``r``-group rounded box below the n-row.
    All boxes use ``ax.get_xaxis_transform()`` so x is in data units
    and y is in axes-fraction units (negative → below the data area).
    """
    from matplotlib.patches import FancyBboxPatch

    n_count = len(n_vals)
    c_count = len(c_vals)
    total = n_count * c_count
    positions = list(range(total))

    # ---- c row: the per-cell value goes on the default xtick ----
    ax.set_xticks(positions)
    ax.set_xticklabels(
        [f"{c_vals[i % c_count]:g}" for i in positions],
        fontsize=7,
    )
    ax.tick_params(axis="x", which="both", length=0, pad=2)

    # Vertical layout (axes-fraction units, all negative = below data).
    # Tightened pass: the n and r rows sit immediately under the c
    # labels so the hierarchy reads as a single banded block rather
    # than three disjoint strips.
    y_c_label = -0.045  # implied by xticklabels above; documented here.
    y_n_top, y_n_bot = -0.09, -0.14
    y_r_top, y_r_bot = -0.16, -0.21
    _ = y_c_label  # marker variable; xticklabels already placed.

    box_kwargs = dict(
        boxstyle="round,pad=0.02,rounding_size=0.04",
        linewidth=0.8,
        edgecolor="#444444",
        facecolor="#F0F0F0",
        clip_on=False,
        transform=ax.get_xaxis_transform(),
        zorder=10,
    )

    # ---- n row: one box per n value, spanning its c group ----
    half = 0.45  # half-width past the leftmost/rightmost member position.
    for i, n in enumerate(n_vals):
        x_lo = i * c_count - half
        x_hi = (i + 1) * c_count - 1 + half
        ax.add_patch(
            FancyBboxPatch(
                (x_lo, y_n_bot),
                width=(x_hi - x_lo),
                height=(y_n_top - y_n_bot),
                **box_kwargs,
            )
        )
        ax.text(
            (x_lo + x_hi) / 2.0,
            (y_n_bot + y_n_top) / 2.0,
            f"$n = {n}$",
            ha="center",
            va="center",
            fontsize=8,
            transform=ax.get_xaxis_transform(),
            clip_on=False,
            zorder=11,
        )

    # ---- r row: a single box spanning everything ----
    x_lo = 0 - half
    x_hi = (total - 1) + half
    ax.add_patch(
        FancyBboxPatch(
            (x_lo, y_r_bot),
            width=(x_hi - x_lo),
            height=(y_r_top - y_r_bot),
            **box_kwargs,
        )
    )
    ax.text(
        (x_lo + x_hi) / 2.0,
        (y_r_bot + y_r_top) / 2.0,
        f"$r = {r_value}$",
        ha="center",
        va="center",
        fontsize=8.5,
        fontweight="bold",
        transform=ax.get_xaxis_transform(),
        clip_on=False,
        zorder=11,
    )

    # ---- Lift x-limits a smidge so the boxes don't hug the data ----
    ax.set_xlim(-half - 0.15, total - 1 + half + 0.15)

    # ---- Move the inner ``c`` label closer to the data axis ----
    # Smooth axis line breath: no extra spine adjustments needed since
    # the boxes float below in axes-fraction space.


# ---------------------------------------------------------------------------
# Figure drawing — shared
# ---------------------------------------------------------------------------
def _draw_metric_figure(
    per_nrc: list[dict[str, Any]],
    per_nrc_backend: list[dict[str, Any]],
    per_cell: list[dict[str, Any]],
    *,
    metric: str,
    y_label: str,
    output_basepath: Path,
) -> None:
    """One scatter + boxplot + fitted line per backend, hierarchical x-axis."""
    import matplotlib.pyplot as plt
    import numpy as np

    from isalhg.viz.style import apply_ieee_style, save_figure

    apply_ieee_style()

    n_vals, c_vals = _grid_axes(per_nrc)
    r_value = int(per_nrc[0].get("r", 3)) if per_nrc else 3

    fig, ax = plt.subplots(figsize=(7.0, 4.6))

    legend_handles = []
    legend_labels = []

    # Box-plot geometry: four backends side-by-side within each cell.
    n_backends = len(_BACKENDS)
    box_step = 0.16  # horizontal stride between adjacent backend boxes
    box_offsets = [(i - (n_backends - 1) / 2.0) * box_step for i in range(n_backends)]
    box_width = box_step * 0.85

    for b_idx, backend in enumerate(_BACKENDS):
        x, y = _backend_series(per_nrc, per_nrc_backend, backend, metric)
        if not x:
            continue

        # Power-law fit uses the n value implied by each cell, not its
        # x-axis position. Recover n from the index ordering.
        n_per_cell = [n_vals[int(p) // len(c_vals)] for p in x]
        fit = _power_law_fit(n_per_cell, y)

        color = _BACKEND_COLOR[backend]
        marker = _BACKEND_MARKER[backend]
        x_offset = box_offsets[b_idx]

        # Boxplot showing the 10-seed spread per cell (one box per
        # (n, c) cell, four backends side by side).
        box_positions, box_data = _per_seed_box_data(per_cell, n_vals, c_vals, backend, metric)
        if box_data:
            bp = ax.boxplot(
                box_data,
                positions=[p + x_offset for p in box_positions],
                widths=box_width,
                patch_artist=True,
                showfliers=False,
                medianprops={"color": color, "linewidth": 1.2},
                boxprops={
                    "facecolor": color,
                    "edgecolor": color,
                    "alpha": 0.20,
                    "linewidth": 0.8,
                },
                whiskerprops={"color": color, "linewidth": 0.7, "alpha": 0.65},
                capprops={"color": color, "linewidth": 0.7, "alpha": 0.65},
                zorder=2,
            )
            del bp  # not used; styling applied via patch_artist props.

        # Scatter the per-cell median over the box, at the same offset.
        x_off = [p + x_offset for p in x]
        ax.scatter(
            x_off,
            y,
            color=color,
            marker=marker,
            s=22,
            edgecolor="white",
            linewidth=0.6,
            zorder=4,
            label=None,
        )

        # Connect adjacent cells with a faint line that traces the
        # per-cell median trend. ``x`` and ``y`` are sorted by cell
        # index (see ``_backend_series``), so the polyline now hugs
        # the boxes from left to right without zigzag artefacts.
        ax.plot(
            x_off,
            y,
            color=color,
            linewidth=0.7,
            alpha=0.35,
            zorder=3,
            label=None,
        )

        # Overlay the fitted power law as a smooth curve in n.
        if fit is not None:
            alpha_log, beta = fit
            # Evaluate at every cell's n; show the curve as a stepped
            # line so it does not visually contradict the categorical
            # x-axis. Use a denser grid in log-space for smoothness.
            n_dense = np.linspace(min(n_vals), max(n_vals), 80)
            y_dense = (10**alpha_log) * n_dense**beta
            # Map dense n back onto fractional cell positions: cell i
            # of n-group j sits at position 3j + i; we drop the fit
            # onto the centre of each n-group (position 3j + 1).
            x_dense = np.interp(
                n_dense,
                n_vals,
                [j * len(c_vals) + (len(c_vals) - 1) / 2.0 for j in range(len(n_vals))],
            )
            ax.plot(
                x_dense,
                y_dense,
                color=color,
                linewidth=1.4,
                linestyle="--",
                alpha=0.85,
                zorder=4,
                label=None,
            )

        # One legend entry per backend, with the fitted parameters.
        h = plt.Line2D(
            [0],
            [0],
            color=color,
            marker=marker,
            markersize=6,
            markeredgecolor="white",
            markeredgewidth=0.6,
            linewidth=1.4,
            linestyle="--",
        )
        legend_handles.append(h)
        legend_labels.append(_legend_label(backend, fit))

    # ---- y-axis: log scale, label, grid ----
    ax.set_yscale("log")
    ax.set_ylabel(y_label, fontsize=10)
    ax.grid(True, axis="y", which="both", linewidth=0.4, alpha=0.35)

    # ---- x-axis: hierarchical group boxes ----
    _draw_hierarchical_xaxis(ax, n_vals=n_vals, c_vals=c_vals, r_value=r_value)

    # ---- spine cleanup ----
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)

    # ---- legend below the figure, outside the data axes ----
    fig.legend(
        legend_handles,
        legend_labels,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.0),
        ncol=2,
        frameon=False,
        fontsize=8.5,
        handlelength=2.6,
        columnspacing=1.4,
        handletextpad=0.5,
    )

    # Reserve enough vertical space for the three hierarchy rows + the
    # legend below them. Bottom: 0.30 axes for hierarchy + legend.
    fig.subplots_adjust(left=0.10, right=0.97, top=0.96, bottom=0.32)

    save_figure(fig, output_basepath, formats=("pdf", "png"))
    plt.close(fig)
    logger.info("wrote %s", output_basepath)


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
        r"$T_{\text{IsalHG}}$ (ms) & $T_{\text{Nauty}}$ (ms) & $T_{\text{Bliss}}$ (ms) & "
        r"$T_{\text{Traces}}$ (ms) & speedup & DNF$_{\text{IsalHG}}$ & DNF$_{\text{best Levi}}$ \\"
    )
    lines.append(r"\midrule")
    for row in sorted(per_nrc, key=lambda r: (int(r["n"]), int(r["r"]), float(r["c"]))):
        speedup = row.get("geomean_isalhg_over_best_levi")
        speedup_str = "DNF" if speedup is None else f"{speedup:.2f}"
        levi_dnfs = [int(row.get(f"dnf_count_{b}") or 0) for b in _LEVI_BACKENDS]
        lines.append(
            f"{row['n']} & {row['r']} & {row['c']} & "
            f"{_fmt_ms(row.get('median_time_s_isalhg'))} & "
            f"{_fmt_ms(row.get('median_time_s_pynauty_levi'))} & "
            f"{_fmt_ms(row.get('median_time_s_bliss_levi'))} & "
            f"{_fmt_ms(row.get('median_time_s_traces_levi'))} & "
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
        r"cells & pairs checked & pass rate & failures (IsalHG) & failures (Levi total) \\",
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


def _fmt_ms(value: Any) -> str:
    """Render seconds → milliseconds with sensible precision."""
    if value is None:
        return "--"
    try:
        v = float(value) * 1_000.0
    except (TypeError, ValueError):
        return str(value)
    if v == 0:
        return "0"
    if v >= 100:
        return f"{v:.0f}"
    if v >= 10:
        return f"{v:.1f}"
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
    per_nrc_backend = _read_csv(args.aggregate_dir / "per_nrc_backend.csv")
    correctness = _read_csv(args.aggregate_dir / "correctness.csv")

    figures_dir = args.output_dir / "figures"
    tables_dir = args.output_dir / "tables"
    figures_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)

    _draw_metric_figure(
        per_nrc,
        per_nrc_backend,
        per_cell,
        metric="time_ms",
        y_label=r"median wall-clock per fingerprint (ms, log scale)",
        output_basepath=figures_dir / "fig1_wallclock",
    )
    _draw_metric_figure(
        per_nrc,
        per_nrc_backend,
        per_cell,
        metric="rss_mb",
        y_label=r"max peak RSS (MiB, log scale)",
        output_basepath=figures_dir / "fig2_memory",
    )
    _draw_metric_figure(
        per_nrc,
        per_nrc_backend,
        per_cell,
        metric="fp_bytes",
        y_label=r"median fingerprint length (bytes, log scale)",
        output_basepath=figures_dir / "fig3_fp_bytelen",
    )

    _table1(per_nrc, tables_dir / "table1_per_cell_summary.tex")
    _table2(correctness, tables_dir / "table2_correctness.tex")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
