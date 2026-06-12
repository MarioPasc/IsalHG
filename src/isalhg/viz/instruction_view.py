"""Render the instruction-string strip.

The strip is a horizontal row of token cells. Cells for tokens already
emitted (``i < current_idx``) are at full opacity in their semantic
colour; remaining cells are greyed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from isalhg.core.instructions import Token, TokenC, TokenV
from isalhg.types import EdgeId
from isalhg.viz.style import (
    ACTIVE_ALPHA,
    GRAYED_ALPHA,
    GRAYED_FACE,
    color_for_token,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes
else:
    Axes = Any


def assign_edge_ids_to_tokens(tokens: tuple[Token, ...]) -> tuple[int | None, ...]:
    """Map each ``V`` or ``C`` token to the edge ID it constructs.

    The S2H interpreter assigns edge IDs in order of construction
    (skipping duplicates, since ``add_hyperedge`` is idempotent). For
    plotting we assume the canonical sequence does not produce
    duplicates -- this holds for greedy_min on simple hypergraphs and
    matches the assumption made by the Phase 1 tests.

    Returns a tuple aligned with ``tokens``: ``edge_id`` for ``V`` / ``C``
    tokens, ``None`` for ``W`` / ``P`` / ``N`` / unknown.
    """
    out: list[int | None] = []
    next_edge_id = 0
    for tok in tokens:
        if isinstance(tok, (TokenV, TokenC)):
            out.append(next_edge_id)
            next_edge_id += 1
        else:
            out.append(None)
    return tuple(out)


def _kind_of(tok: Token) -> str:
    return type(tok).__name__.removeprefix("Token")


def _auto_fontsize(n_tokens: int, axis_width_inches: float) -> float:
    """Pick a label fontsize that does not overflow the cell.

    Heuristic: per-cell width in points is ``axis_width_inches * 72 /
    n_tokens``. A rotated label needs roughly one character height
    (``= fontsize`` points) of horizontal room, plus 25 % margin. The
    result is clamped to ``[3.0, 7.5]``.
    """
    if n_tokens <= 0:
        return 7.5
    per_cell_pts = axis_width_inches * 72.0 / n_tokens
    return max(3.0, min(7.5, per_cell_pts * 0.80))


def draw_instruction_strip(
    ax: Axes,
    tokens: tuple[Token, ...],
    *,
    current_idx: int,
    edge_palette: dict[EdgeId, str],
    edge_id_per_token: tuple[int | None, ...] | None = None,
    cell_width: float = 1.05,
    cell_height: float = 1.1,
    show_labels: bool = True,
    label_rotation: float = 90.0,
    axis_width_inches: float | None = None,
    label_fontsize: float | None = None,
) -> None:
    """Draw the strip.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axes.
    tokens : tuple[Token, ...]
        Full token sequence.
    current_idx : int
        Number of tokens already emitted; cells ``[0, current_idx)`` are
        rendered at full opacity, ``[current_idx, len(tokens))`` greyed.
    edge_palette : dict[EdgeId, str]
        Colour per hyperedge ID; ``V`` and ``C`` cells inherit from here.
    edge_id_per_token : tuple[int | None, ...] | None, optional
        Pre-computed mapping from token index to edge ID. When ``None``,
        :func:`assign_edge_ids_to_tokens` is called.
    cell_width, cell_height : float, optional
        Cell geometry in axis units.
    show_labels : bool, optional
        Render the serialised token text on top of each cell.
    """
    from matplotlib.patches import FancyBboxPatch

    if edge_id_per_token is None:
        edge_id_per_token = assign_edge_ids_to_tokens(tokens)

    n = len(tokens)
    if label_fontsize is None:
        label_fontsize = 7.0 if axis_width_inches is None else _auto_fontsize(n, axis_width_inches)
    if n == 0:
        ax.text(
            0.5,
            0.5,
            "(empty)",
            ha="center",
            va="center",
            transform=ax.transAxes,
            color="#888888",
            fontsize=7,
        )
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        return

    for i, tok in enumerate(tokens):
        x = i * cell_width
        kind = _kind_of(tok)
        is_active = i < current_idx
        face = (
            color_for_token(
                kind,
                tok.serialize(),
                edge_palette=edge_palette,
                edge_id_for_token=edge_id_per_token[i],
            )
            if is_active
            else GRAYED_FACE
        )
        alpha = ACTIVE_ALPHA if is_active else GRAYED_ALPHA
        patch = FancyBboxPatch(
            (x + 0.05, 0.05),
            cell_width - 0.10,
            cell_height - 0.10,
            boxstyle="round,pad=0.02,rounding_size=0.08",
            facecolor=face,
            edgecolor="#333333",
            lw=0.6,
            alpha=alpha,
        )
        ax.add_patch(patch)
        if show_labels:
            ax.text(
                x + cell_width / 2,
                cell_height / 2,
                tok.serialize(),
                ha="center",
                va="center",
                fontsize=label_fontsize,
                color="#111111" if is_active else "#666666",
                rotation=label_rotation,
            )

    ax.set_xlim(-0.1, n * cell_width + 0.1)
    ax.set_ylim(-0.05, cell_height + 0.05)
    ax.set_aspect("auto")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
