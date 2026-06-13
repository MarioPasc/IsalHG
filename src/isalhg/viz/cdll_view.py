"""Render the CDLL ring with its ``k`` pointers.

Pure matplotlib drawing. Nodes are evenly spaced circles whose payload
text is the underlying ``NodeId``. Pointers are arrow annotations from
an outer radius into each node's circumference. Colours are supplied by
the caller (so the same per-vertex palette can drive the ring and the
hypergraph view in lockstep).
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from isalhg.core.trace import StepSnapshot
from isalhg.types import NodeId
from isalhg.viz.layout import cdll_ring_positions
from isalhg.viz.style import (
    ACTIVE_ALPHA,
    GRAYED_ALPHA,
    GRAYED_FACE,
    POINTER_PALETTE,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes
else:
    Axes = Any


def draw_cdll_ring(
    ax: Axes,
    snapshot: StepSnapshot,
    *,
    vertex_colors: dict[NodeId, str],
    grayed_vertices: frozenset[NodeId] = frozenset(),
    node_radius: float = 0.22,
    ring_radius: float = 1.0,
    pointer_offset: float = 0.55,
    pointer_gap: float = 0.12,
    label_extra: float = 0.30,
) -> None:
    """Draw the CDLL ring for ``snapshot`` onto ``ax``.

    The ring is laid out clockwise starting at the top (12 o'clock).
    Each pointer ``p_i`` is rendered as an arrow from an outer radius
    toward the node it currently points to; pointers stacked on the same
    node fan out angularly so they remain distinguishable.
    """
    from matplotlib.patches import Circle, FancyArrowPatch

    node_order = snapshot.cdll_node_order
    positions = cdll_ring_positions(node_order, radius=ring_radius)

    # Draw the ring backbone (light grey connecting line between
    # consecutive slots, including the wrap-around segment).
    if len(node_order) >= 2:
        for i in range(len(node_order)):
            a = positions[node_order[i]]
            b = positions[node_order[(i + 1) % len(node_order)]]
            ax.plot([a[0], b[0]], [a[1], b[1]], color="#CCCCCC", lw=1.4, zorder=1)

    # Draw the node disks.
    for v in node_order:
        x, y = positions[v]
        is_grayed = v in grayed_vertices
        face = GRAYED_FACE if is_grayed else vertex_colors.get(v, "#888888")
        alpha = GRAYED_ALPHA if is_grayed else ACTIVE_ALPHA
        circ = Circle(
            (x, y),
            node_radius,
            facecolor=face,
            edgecolor="#333333",
            lw=1.2,
            alpha=alpha,
            zorder=2,
        )
        ax.add_patch(circ)
        ax.text(
            x,
            y,
            str(v),
            ha="center",
            va="center",
            fontsize=11,
            color="#111111",
            zorder=3,
        )

    # Map node -> indices of pointers that target it (1-based).
    pointers_on_node: dict[NodeId, list[int]] = {}
    for i_one_based, v in enumerate(snapshot.pointer_node_values, start=1):
        pointers_on_node.setdefault(v, []).append(i_one_based)

    arrow_outer = ring_radius + pointer_offset
    for v, indices in pointers_on_node.items():
        if v not in positions:
            continue
        x, y = positions[v]
        # Angle from origin to node.
        base_theta = math.pi / 2 if (x == 0.0 and y == 0.0) else math.atan2(y, x)
        fan_step = 0.18  # radians between stacked pointer arrows
        for j, i_one_based in enumerate(indices):
            offset = (j - (len(indices) - 1) / 2.0) * fan_step
            theta = base_theta + offset
            sx = arrow_outer * math.cos(theta)
            sy = arrow_outer * math.sin(theta)
            # Leave a visible gap between the arrow tip and the node disk
            # so the pointer reads as "pointing at" the node, not "touching" it.
            dx = x - sx
            dy = y - sy
            d = math.hypot(dx, dy)
            stop_radius = node_radius + pointer_gap
            tx = x - (dx / d) * stop_radius if d > 0 else x
            ty = y - (dy / d) * stop_radius if d > 0 else y
            color = POINTER_PALETTE[(i_one_based - 1) % len(POINTER_PALETTE)]
            arrow = FancyArrowPatch(
                (sx, sy),
                (tx, ty),
                arrowstyle="-|>",
                mutation_scale=14,
                color=color,
                lw=1.8,
                zorder=4,
            )
            ax.add_patch(arrow)
            # Place the pointer label outside the arrow tail, away from
            # the node, so it does not collide with the node text.
            lx = (arrow_outer + label_extra) * math.cos(theta)
            ly = (arrow_outer + label_extra) * math.sin(theta)
            ax.text(
                lx,
                ly,
                f"p{i_one_based}",
                ha="center",
                va="center",
                fontsize=9,
                color=color,
                zorder=5,
            )

    # Axis cosmetics.
    extent = ring_radius + pointer_offset + label_extra + 0.25
    ax.set_xlim(-extent, extent)
    ax.set_ylim(-extent, extent)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
