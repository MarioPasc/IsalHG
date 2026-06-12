"""Composite figure builders.

Atomic unit: a three-row column showing one snapshot's
``(CDLL ring, instruction strip, hypergraph)`` views. Higher-level
figures stack columns horizontally (``steps_figure``) or stack two
direction blocks vertically (``roundtrip_figure``).

Layout is computed once from the **final** hypergraph and re-used for
every snapshot column so the nodes do not jump between frames.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from isalhg.core.instructions import Token
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.core.trace import StepSnapshot
from isalhg.types import EdgeId, NodeId
from isalhg.viz.base import Position
from isalhg.viz.cdll_view import draw_cdll_ring
from isalhg.viz.hypergraph_view import draw_hypergraph
from isalhg.viz.instruction_view import (
    assign_edge_ids_to_tokens,
    draw_instruction_strip,
)
from isalhg.viz.style import build_edge_palette, build_vertex_palette

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure
    from matplotlib.gridspec import GridSpec, SubplotSpec
else:
    Axes = Any
    Figure = Any
    GridSpec = Any
    SubplotSpec = Any


_ROW_RATIOS: tuple[float, float, float] = (1.3, 1.0, 1.6)


def _column_axes(
    fig: Figure,
    spec: SubplotSpec,
) -> tuple[Axes, Axes, Axes]:
    """Carve a 3-row sub-gridspec out of ``spec`` and return the three axes."""
    sub = spec.subgridspec(3, 1, height_ratios=list(_ROW_RATIOS), hspace=0.05)
    ax_cdll = fig.add_subplot(sub[0])
    ax_strip = fig.add_subplot(sub[1])
    ax_h = fig.add_subplot(sub[2])
    return ax_cdll, ax_strip, ax_h


def draw_column(
    fig: Figure,
    spec: SubplotSpec,
    snapshot: StepSnapshot,
    full_H: SparseHypergraph,
    full_tokens: tuple[Token, ...],
    *,
    backend: str,
    vertex_palette: dict[NodeId, str],
    edge_palette: dict[EdgeId, str],
    hypergraph_layout: dict[NodeId, Position] | None,
    column_title: str | None = None,
    direction: str = "s2h",
    column_inches: float | None = None,
) -> dict[NodeId, Position]:
    """Draw one snapshot column into ``fig`` at ``spec``.

    Active vs grayed semantics depend on ``direction``:

    - ``"s2h"``: the algorithm builds ``H`` from the string. A vertex /
      hyperedge is rendered in full colour once it has been built
      (``snapshot.active_*``); the rest is grayed (ghost of the target).
      The hypergraph view starts fully grayed and ends fully coloured.
    - ``"h2s"``: the algorithm consumes ``H`` and emits the string. A
      vertex / hyperedge is rendered in full colour while it has not yet
      been emitted; the already-emitted parts are grayed (the algorithm
      has "captured" them in the partial string). The hypergraph view
      starts fully coloured and ends fully grayed.

    The instruction strip and the CDLL ring are identical in both
    directions: tokens fill left-to-right and the CDLL grows monotonically
    in both framings.

    Returns
    -------
    dict[NodeId, Position]
        The hypergraph layout (so subsequent columns can pin it).
    """
    ax_cdll, ax_strip, ax_h = _column_axes(fig, spec)

    if column_title is not None:
        ax_cdll.set_title(column_title, fontsize=8, pad=4)

    draw_cdll_ring(
        ax_cdll,
        snapshot,
        vertex_colors=vertex_palette,
    )

    edge_id_per_tok = assign_edge_ids_to_tokens(full_tokens)
    draw_instruction_strip(
        ax_strip,
        full_tokens,
        current_idx=snapshot.step_idx,
        edge_palette=edge_palette,
        edge_id_per_token=edge_id_per_tok,
        axis_width_inches=column_inches,
        direction=direction,
    )

    active_nodes = set(snapshot.active_nodes)
    active_edges = set(snapshot.active_edges)
    if direction == "h2s":
        # In H2S framing, already-emitted (= "active") elements are ghosts;
        # the colored hypergraph is what the algorithm has yet to encode.
        grayed_nodes = frozenset(active_nodes)
        grayed_edges = frozenset(active_edges)
    else:
        grayed_nodes = frozenset(v for v in full_H.nodes() if v not in active_nodes)
        grayed_edges = frozenset(e for e in full_H.edges() if e not in active_edges)

    layout_used = draw_hypergraph(
        ax_h,
        full_H,
        backend=backend,
        node_colors=vertex_palette,
        edge_colors=edge_palette,
        grayed_nodes=grayed_nodes,
        grayed_edges=grayed_edges,
        layout=hypergraph_layout,
    )
    return layout_used


def _sample_indices(n: int, k: int) -> list[int]:
    """Return ``k`` evenly spaced indices in ``[0, n)``.

    When ``n <= k`` returns ``list(range(n))`` so every available
    snapshot is rendered.
    """
    if n <= 0:
        return []
    if n <= k:
        return list(range(n))
    # Endpoints included; midpoints uniformly spaced.
    step = (n - 1) / (k - 1)
    return sorted({round(i * step) for i in range(k)})


def single_card_figure(
    snapshot: StepSnapshot,
    full_H: SparseHypergraph,
    full_tokens: tuple[Token, ...],
    *,
    backend: str,
    title: str | None = None,
    direction: str = "s2h",
) -> Figure:
    """Build a one-column figure for the start or end snapshot."""
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec

    fig = plt.figure(figsize=(3.6, 6.5))
    gs = GridSpec(1, 1, figure=fig)
    vertex_palette = build_vertex_palette(full_H)
    edge_palette = build_edge_palette(full_H)
    draw_column(
        fig,
        gs[0, 0],
        snapshot,
        full_H,
        full_tokens,
        backend=backend,
        vertex_palette=vertex_palette,
        edge_palette=edge_palette,
        hypergraph_layout=None,
        column_title=title,
        direction=direction,
        column_inches=3.0,
    )
    return fig


def steps_figure(
    snapshots: tuple[StepSnapshot, ...],
    full_H: SparseHypergraph,
    full_tokens: tuple[Token, ...],
    *,
    backend: str,
    direction: str,
    n_columns: int = 7,
    overall_title: str | None = None,
) -> Figure:
    """Build the ``3 x n_columns`` step figure.

    ``snapshots`` may be larger than ``n_columns``; we sample
    ``n_columns`` evenly spaced indices (or use all if fewer are
    available).
    """
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec

    indices = _sample_indices(len(snapshots), n_columns)
    ncols = len(indices)
    fig = plt.figure(figsize=(2.8 * ncols, 6.5))
    gs = GridSpec(1, ncols, figure=fig, wspace=0.12)
    vertex_palette = build_vertex_palette(full_H)
    edge_palette = build_edge_palette(full_H)
    pinned: dict[NodeId, Position] | None = None
    for col, idx in enumerate(indices):
        snap = snapshots[idx]
        pinned = draw_column(
            fig,
            gs[0, col],
            snap,
            full_H,
            full_tokens,
            backend=backend,
            vertex_palette=vertex_palette,
            edge_palette=edge_palette,
            hypergraph_layout=pinned,
            column_title=f"Step {snap.step_idx}",
            direction=direction,
            column_inches=2.4,
        )
    if overall_title is not None:
        fig.suptitle(overall_title, fontsize=10)
    return fig


def roundtrip_figure(
    s2h_snapshots: tuple[StepSnapshot, ...],
    h2s_snapshots: tuple[StepSnapshot, ...],
    full_H: SparseHypergraph,
    full_tokens: tuple[Token, ...],
    *,
    backend: str,
    n_columns: int = 7,
    overall_title: str | None = None,
) -> Figure:
    """Build the roundtrip collage.

    Top half: ``h2s_snapshots`` (algorithm producing the string).
    Bottom half: ``s2h_snapshots`` (algorithm consuming the string).
    The same column indices are sampled from both sequences so the
    columns line up.
    """
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec

    n = min(len(s2h_snapshots), len(h2s_snapshots))
    indices = _sample_indices(n, n_columns)
    ncols = len(indices)
    fig = plt.figure(figsize=(2.8 * ncols, 13.0))
    gs = GridSpec(
        2,
        ncols,
        figure=fig,
        wspace=0.12,
        hspace=0.15,
        height_ratios=[1.0, 1.0],
    )
    vertex_palette = build_vertex_palette(full_H)
    edge_palette = build_edge_palette(full_H)
    pinned_top: dict[NodeId, Position] | None = None
    pinned_bot: dict[NodeId, Position] | None = None
    for col, idx in enumerate(indices):
        h2s_snap = h2s_snapshots[idx]
        s2h_snap = s2h_snapshots[idx]
        pinned_top = draw_column(
            fig,
            gs[0, col],
            h2s_snap,
            full_H,
            full_tokens,
            backend=backend,
            vertex_palette=vertex_palette,
            edge_palette=edge_palette,
            hypergraph_layout=pinned_top,
            column_title=f"Step {h2s_snap.step_idx}",
            direction="h2s",
            column_inches=2.4,
        )
        pinned_bot = draw_column(
            fig,
            gs[1, col],
            s2h_snap,
            full_H,
            full_tokens,
            backend=backend,
            vertex_palette=vertex_palette,
            edge_palette=edge_palette,
            hypergraph_layout=pinned_bot,
            column_title=f"Step {s2h_snap.step_idx}",
            direction="s2h",
            column_inches=2.4,
        )
    if overall_title is not None:
        fig.suptitle(overall_title, fontsize=10)
    return fig
