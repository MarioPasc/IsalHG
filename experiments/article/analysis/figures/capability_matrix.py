"""Capability matrix — main-text figure for the IsalHG article.

Renders a 7 × 6 grid of ✓ / ✗ / ~ / — symbols comparing six representations
(plus the naive degree-sequence baseline) across six capability dimensions,
per the spec in ``docs/article/REVIEW/CAPABILITY_MATRIX.md``.

All cell values are established facts (proved or measured); no computation is
required here.  The only job of this module is to render and save the figure.

Justification of every cell is in ``docs/article/REVIEW/CAPABILITY_MATRIX.md``
§Column-by-column justification.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

matplotlib.use("Agg")  # non-interactive; safe in HPC / CI

# ---------------------------------------------------------------------------
# Matrix data
# ---------------------------------------------------------------------------

#: Ordered list of representation row labels (display form).
REPRESENTATIONS: list[str] = [
    "IsalHG",
    "WL-hist",
    "NetLSD",
    "HyperCOT",
    "HPD",
    "nauty-edit",
    "Deg-seq L1",
]

#: Ordered list of capability column labels (short display form).
CAPABILITY_COLUMNS: list[str] = [
    "Complete\ninvariant",
    "True\nmetric",
    "Decodable",
    "Navigable\ngeometry",
    "Scales to\nn ≳ 10²",
    "Single metric\nall 4 tasks",
]

#: Allowed cell symbols.
_ALLOWED: frozenset[str] = frozenset({"✓", "✗", "~", "—"})

#: The capability matrix.  Each value is a list of 6 symbols in the same
#: order as ``CAPABILITY_COLUMNS``.
#:
#: Sources (per column):
#:   [0] Complete invariant  — IsalHG: Theorem A (``w*_c`` tie-complete).
#:                              nauty:  canonical form on Levi graph (complete by construction).
#:                              Others: lossy embeddings, non-iso hypergraphs can collide.
#:                              Deg-seq: incompleteness witness ``non_iso_pair_small``
#:                                       (degrees [2,2,1,1], d_DS = 0, non-iso).
#:   [1] True metric          — HPD uses Jensen–Shannon divergence (not a metric;
#:                              its square root is). All others satisfy the triangle ineq.
#:   [2] Decodable            — Only ``w*_c`` has a closed-alphabet inverse (S2H).
#:                              nauty's canonical string decodes to the *graph*, not a
#:                              navigable hypergraph intermediate (avalanche geometry).
#:   [3] Navigable geometry   — IsalHG: measured IQR 2–8 tokens (G2, T-M5g).
#:                              nauty: IQR 10–20, ratio 1.25–9.5×.
#:                              Vector / portrait reps: no natural single-edit notion (—).
#:   [4] Scales to n ≳ 10²   — IsalHG: symmetry-gated (HIC NO-GO, T-DQ3').
#:                              HyperCOT: O(n³)/pair.
#:                              nauty: worst-case exponential, typical sub-second (~).
#:   [5] Single metric 4 tasks— HPD: JSD ≠ metric → MDS/k-medoids/kNN only approximately
#:                              licensed (~). Deg-seq: feeds A1–A3 but A4 intermediates
#:                              are not decodable hypergraphs (still ✓ as a metric for
#:                              the three tasks where it applies; capability captured
#:                              by the Decodable row).
MATRIX_DATA: dict[str, list[str]] = {
    "IsalHG": ["✓", "✓", "✓", "✓", "✗", "✓"],
    "WL-hist": ["✗", "✓", "✗", "—", "✓", "✓"],
    "NetLSD": ["✗", "✓", "✗", "—", "✓", "✓"],
    "HyperCOT": ["✗", "✓", "✗", "—", "✗", "✓"],
    "HPD": ["✗", "✗", "✗", "—", "✓", "~"],
    "nauty-edit": ["✓", "✓", "✗", "✗", "~", "✓"],
    "Deg-seq L1": ["✗", "✓", "✗", "—", "✓", "✓"],
}

# ---------------------------------------------------------------------------
# Colour map for cells
# ---------------------------------------------------------------------------

_CELL_COLORS: dict[str, str] = {
    "✓": "#c8e6c9",  # light green
    "✗": "#ffcdd2",  # light red
    "~": "#fff9c4",  # light yellow
    "—": "#eeeeee",  # light grey
}

# IsalHG row is highlighted (paper's protagonist row).
_ISALHG_ROW_ALPHA = 0.85
_OTHER_ROW_ALPHA = 0.70

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_matrix(data: dict[str, list[str]]) -> None:
    """Validate that every cell in *data* is an allowed symbol.

    Parameters
    ----------
    data :
        Mapping from representation name to list of cell symbols.

    Raises
    ------
    ValueError
        If any cell value is not in ``{"✓", "✗", "~", "—"}``.
    """
    for rep, row in data.items():
        for col_idx, cell in enumerate(row):
            if cell not in _ALLOWED:
                col_name = (
                    CAPABILITY_COLUMNS[col_idx]
                    if col_idx < len(CAPABILITY_COLUMNS)
                    else str(col_idx)
                )
                raise ValueError(
                    f"invalid cell value {cell!r} for {rep}[{col_name}]; "
                    f"allowed: {sorted(_ALLOWED)}"
                )


# ---------------------------------------------------------------------------
# Figure rendering
# ---------------------------------------------------------------------------

_CAPTION = (
    "\\textbf{Fig.\\,CAP}\\enspace Capability matrix for all representations. "
    "IsalHG is the only representation that is simultaneously a "
    "\\emph{complete invariant}, \\emph{decodable} (the closed IsalHG "
    "alphabet allows S2H to recover the hypergraph from any string on an "
    "edit path), and \\emph{geometrically navigable} (single-edit "
    "sensitivity IQR 2–8 tokens; measured in G2). "
    "HPD uses Jensen\\textendash Shannon divergence, which is not a metric "
    "(its square root is); metric-sensitive operations (MDS, PAM, kNN) are "
    "therefore only approximately licensed for HPD. "
    "Place adjacent to the A4 decoded-intermediates figure."
)


def render_capability_matrix(
    output_path: Path | None = None,
    *,
    dpi: int = 150,
) -> Path:
    """Render the capability matrix and write it to *output_path*.

    Parameters
    ----------
    output_path :
        Destination file.  Must end in ``.pdf`` or ``.svg`` (vector formats).
        Defaults to the module directory under ``figures/``.
    dpi :
        Resolution passed to ``savefig`` (relevant only for rasterised formats;
        kept for API consistency even though the default output is PDF).

    Returns
    -------
    Path
        The path of the written file.

    Raises
    ------
    ValueError
        If any cell in ``MATRIX_DATA`` is not a recognised symbol.
    """
    validate_matrix(MATRIX_DATA)

    if output_path is None:
        output_path = Path(__file__).parent / "capability_matrix.pdf"
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    n_rows = len(REPRESENTATIONS)
    n_cols = len(CAPABILITY_COLUMNS)

    # ------------------------------------------------------------------
    # Build the cell-colour array and text array
    # ------------------------------------------------------------------
    cell_text: list[list[str]] = []
    cell_colours: list[list[str]] = []

    for rep in REPRESENTATIONS:
        row_vals = MATRIX_DATA[rep]
        cell_text.append(row_vals)
        cell_colours.append([_CELL_COLORS[v] for v in row_vals])

    # ------------------------------------------------------------------
    # Figure layout
    # ------------------------------------------------------------------
    fig_width = 10.0
    row_height = 0.52
    fig_height = row_height * (n_rows + 1.2)  # +1.2 for column headers

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.set_axis_off()

    tbl = ax.table(
        cellText=cell_text,
        cellColours=cell_colours,
        rowLabels=REPRESENTATIONS,
        colLabels=CAPABILITY_COLUMNS,
        loc="center",
        cellLoc="center",
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(11)
    tbl.scale(1.0, 1.55)

    # ---- Style column headers ----
    for col_idx in range(n_cols):
        hdr = tbl[0, col_idx]
        hdr.set_facecolor("#37474f")
        hdr.set_text_props(color="white", fontweight="bold", fontsize=9.5)
        hdr.set_height(0.18)

    # ---- Style row-label cells ----
    for row_idx, rep in enumerate(REPRESENTATIONS, start=1):
        cell = tbl[row_idx, -1]  # row label is at column index -1
        cell.set_facecolor("#eceff1")
        cell.set_text_props(fontweight="bold" if rep == "IsalHG" else "normal")

    # ---- Highlight IsalHG row ----
    isalhg_idx = REPRESENTATIONS.index("IsalHG") + 1  # +1 for header
    for col_idx in range(n_cols):
        data_cell = tbl[isalhg_idx, col_idx]
        current_fc = data_cell.get_facecolor()
        # Slightly darken the IsalHG cells to make the row stand out.
        r, g, b, a = current_fc
        data_cell.set_facecolor((r * 0.88, g * 0.92, b * 0.88, 1.0))

    # ---- Thicker border for the IsalHG row ----
    for col_idx in range(n_cols):
        tbl[isalhg_idx, col_idx].set_linewidth(1.5)

    # ---- Font sizes for data cells ----
    for row_idx in range(1, n_rows + 1):
        for col_idx in range(n_cols):
            tbl[row_idx, col_idx].set_fontsize(13)

    # ------------------------------------------------------------------
    # Legend strip (below the table)
    # ------------------------------------------------------------------
    legend_elements = [
        mpatches.Patch(facecolor=_CELL_COLORS["✓"], edgecolor="grey", label="✓  holds / measured"),
        mpatches.Patch(facecolor=_CELL_COLORS["✗"], edgecolor="grey", label="✗  does not hold"),
        mpatches.Patch(
            facecolor=_CELL_COLORS["~"], edgecolor="grey", label="~  partial / conditional"
        ),
        mpatches.Patch(facecolor=_CELL_COLORS["—"], edgecolor="grey", label="—  not applicable"),
    ]
    ax.legend(
        handles=legend_elements,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.07),
        ncol=4,
        fontsize=8,
        frameon=False,
    )

    plt.tight_layout(pad=0.3)

    suffix = output_path.suffix.lower()
    if suffix not in {".pdf", ".svg", ".png", ".eps"}:
        suffix = ".pdf"
        output_path = output_path.with_suffix(suffix)

    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)

    return output_path
