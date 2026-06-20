"""Cohort comparison panels.

Reusable N-panel figure builder for "show how one hypergraph cohort
parameter reshapes the structure" plots — used by the preprint cohort
axes routine (``experiments/preprint/data/visualize_cohort_axes.py``)
and intended as the general entry point for ad-hoc comparison figures.

Concept: each panel is a small hypergraph drawn through any registered
:class:`HypergraphVizBackend`. We compose by reusing the existing
backend-agnostic dispatcher
:func:`isalhg.viz.hypergraph_view.draw_hypergraph`, which already
accepts a caller-supplied ``Axes``; this file only carries the layout,
titling, and per-panel framing logic.

Panel item shape
----------------
Each entry of ``panels`` is a three-tuple ``(label, subtitle, H)``:

- ``label`` — short identifier (rendered bold, title-cased by caller).
- ``subtitle`` — multi-line descriptive text (rendered regular weight
  below the label, e.g. ``"n=12, r=3\\nm=18, ⟨deg⟩=4.5"``).
- ``H`` — the hypergraph drawn through the chosen viz backend.

Why a new module
----------------
``isalhg.viz.composite`` is hard-wired to the three-row CDLL /
instruction / hypergraph layout used by single-trace stepping. The
cohort-comparison concept is different (single-row, no trace context,
parameter-encoded titles), so per the project's "one concept per
module" rule it lives here rather than in ``composite``.
"""

from __future__ import annotations

import logging
import math
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.types import NodeId
from isalhg.viz.base import Position
from isalhg.viz.hypergraph_view import draw_hypergraph
from isalhg.viz.layout import compact_primal_layout
from isalhg.viz.style import (
    apply_ieee_style,
    build_edge_palette,
    build_vertex_palette,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure
else:
    Figure = Any
    Axes = Any

logger = logging.getLogger(__name__)

LayoutFn = Callable[[SparseHypergraph], dict[NodeId, Position]]


def _default_layout(H: SparseHypergraph) -> dict[NodeId, Position]:
    """Default panel layout: spring layout with stray vertices pulled in."""
    return compact_primal_layout(H, seed=0)


def _add_rounded_frame(
    ax: Axes,
    *,
    color: str = "#666666",
    facecolor: str = "#FAFAFA",
    linewidth: float = 1.0,
    rounding: float = 0.06,
) -> None:
    """Draw a rounded rectangular card behind the axes data area.

    Frame matches the current ``xlim``/``ylim`` exactly. Placed at low
    z-order so the hypergraph draws on top; the rounded corners
    visually isolate each panel.
    """
    from matplotlib.patches import FancyBboxPatch

    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    width = xlim[1] - xlim[0]
    height = ylim[1] - ylim[0]
    rsize = min(width, height) * rounding
    # boxstyle pad inflates the patch; we want the frame inside the axis
    # extents, so pad=0 and dimensions match exactly.
    frame = FancyBboxPatch(
        (xlim[0], ylim[0]),
        width=width,
        height=height,
        boxstyle=f"round,pad=0.0,rounding_size={rsize}",
        linewidth=linewidth,
        edgecolor=color,
        facecolor=facecolor,
        zorder=-100,
        clip_on=False,
    )
    ax.add_patch(frame)


def _add_panel_title(
    ax: Axes,
    *,
    label: str,
    subtitle: str,
    label_fontsize: int,
    subtitle_fontsize: int,
) -> None:
    """Place a bold ``label`` above the frame and a ``subtitle`` below it.

    Polaroid-style: title floats above the rounded frame, the hypergraph
    fills the frame, and the descriptive stats sit below the frame. The
    two text blocks never overlap because they live on opposite sides of
    the axes bounding box.
    """
    ax.set_title(label, fontsize=label_fontsize, fontweight="bold", pad=10.0)
    if subtitle:
        ax.text(
            0.5,
            -0.04,
            subtitle,
            transform=ax.transAxes,
            ha="center",
            va="top",
            fontsize=subtitle_fontsize,
            linespacing=1.25,
        )


def cohort_grid_figure(
    panels: Sequence[tuple[str, str, SparseHypergraph]],
    *,
    backend: str = "xgi",
    n_columns: int | None = None,
    figsize: tuple[float, float] | None = None,
    overall_title: str | None = None,
    apply_style: bool = True,
    label_fontsize: int = 11,
    subtitle_fontsize: int = 8,
    layout_fn: LayoutFn | None = _default_layout,
    axis_margin: float = 0.45,
    frame_color: str = "#666666",
    frame_facecolor: str = "#FAFAFA",
) -> Figure:
    """Draw ``len(panels)`` hypergraphs in a (wrapped) row figure.

    Parameters
    ----------
    panels : Sequence[tuple[str, str, SparseHypergraph]]
        Each entry is ``(label, subtitle, H)``. ``label`` is rendered
        bold; ``subtitle`` is rendered regular-weight below the label;
        ``H`` is drawn through ``backend``.
    backend : str, optional
        Name of a registered :class:`HypergraphVizBackend` (``"xgi"``,
        ``"hypernetx"``, or ``"hypergraphx"``).
    n_columns : int | None, optional
        Number of columns. ``None`` → single-row figure.
    figsize : tuple[float, float] | None, optional
        Forwarded to ``plt.subplots``. ``None`` requests
        ``(3.2 * ncols, 3.6 * nrows)``.
    overall_title : str | None, optional
        Figure-level ``suptitle``; omitted when ``None``.
    apply_style : bool, optional
        Apply :func:`isalhg.viz.style.apply_ieee_style` first.
    label_fontsize, subtitle_fontsize : int, optional
        Font sizes for the bold label and the regular-weight subtitle.
    layout_fn : Callable[[SparseHypergraph], dict[NodeId, Position]] | None
        Per-panel vertex-position provider. Default
        :func:`isalhg.viz.layout.compact_primal_layout` keeps strays
        adjacent to the main cluster. ``None`` defers to the viz
        backend's auto-layout (and skips the per-panel viewport lock).
    axis_margin : float, optional
        Padding around the laid-out points, in normalised axis units.
        The compact layout places strays at ``x = 1 + margin_layout``;
        ``axis_margin`` must exceed that plus the visual blob extent of
        the chosen viz backend (HypergraphX bezier hulls bow ~0.2 past
        their vertices). The default 0.45 accommodates all three
        backends; HypergraphX in particular needs ≥ 0.4 to prevent
        overflow outside the rounded frame.
    frame_color, frame_facecolor : str, optional
        Stroke and fill of the rounded card behind each panel.

    Returns
    -------
    matplotlib.figure.Figure
        Caller saves with :func:`isalhg.viz.style.save_figure`.

    Raises
    ------
    ValueError
        If ``panels`` is empty.
    """
    if not panels:
        raise ValueError("cohort_grid_figure requires at least one panel")

    import matplotlib.pyplot as plt

    if apply_style:
        apply_ieee_style()

    ncols = n_columns or len(panels)
    nrows = math.ceil(len(panels) / ncols)
    fig, axes_obj = plt.subplots(
        nrows,
        ncols,
        figsize=figsize or (3.2 * ncols, 3.6 * nrows),
        squeeze=False,
    )
    axes = axes_obj.ravel()

    for ax, (label, subtitle, H) in zip(axes[: len(panels)], panels, strict=False):
        node_colors = build_vertex_palette(H)
        edge_colors = build_edge_palette(H)
        layout = layout_fn(H) if layout_fn is not None else None
        draw_hypergraph(
            ax,
            H,
            backend=backend,
            node_colors=node_colors,
            edge_colors=edge_colors,
            layout=layout,
        )
        # Lock the viewport: the compact_primal_layout puts strays at
        # x ≈ 1.2; ``axis_margin`` is the buffer beyond that. We set the
        # limits *after* the backend draws (the backend may have called
        # autoscale_view) and disable autoscaling to keep them locked
        # while the rounded frame is added.
        if layout is not None:
            # Layout strip extends to ~1.2; pad symmetrically beyond that.
            ax.set_xlim(-1.0 - axis_margin, 1.2 + axis_margin)
            ax.set_ylim(-1.0 - axis_margin, 1.0 + axis_margin)
            ax.set_autoscale_on(False)
            ax.set_aspect("equal", adjustable="box")
        # The decorative frame sits behind everything.
        _add_rounded_frame(ax, color=frame_color, facecolor=frame_facecolor)
        # Strip the default matplotlib axes spines; the rounded frame is
        # the only border.
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        _add_panel_title(
            ax,
            label=label,
            subtitle=subtitle,
            label_fontsize=label_fontsize,
            subtitle_fontsize=subtitle_fontsize,
        )

    # Blank any spare axes when len(panels) does not fill the grid.
    for ax in axes[len(panels) :]:
        ax.set_axis_off()

    if overall_title:
        fig.suptitle(overall_title, fontsize=12, fontweight="bold")
    # tight_layout collapses panels together; we then expand the inter-axes
    # spacing so the subtitle (below each panel) and the title (above) have
    # breathing room and do not overlap a neighbour.
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.92 if overall_title else 1.0))
    fig.subplots_adjust(
        wspace=0.12,
        hspace=0.40,
        bottom=0.22,
        top=0.88 if overall_title else 0.92,
    )
    logger.debug(
        "cohort_grid_figure: backend=%s panels=%d ncols=%d nrows=%d layout=%s",
        backend,
        len(panels),
        ncols,
        nrows,
        "compact_primal" if layout_fn is _default_layout else "custom/none",
    )
    return fig


__all__ = ["LayoutFn", "cohort_grid_figure"]
