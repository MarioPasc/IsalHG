"""Layout helpers shared across the three views.

Pure geometric maths -- no matplotlib at import time.
"""

from __future__ import annotations

import math

from isalhg.types import NodeId
from isalhg.viz.base import Position


def cdll_ring_positions(
    node_order: tuple[NodeId, ...],
    *,
    radius: float = 1.0,
    start_angle: float = math.pi / 2,
    clockwise: bool = True,
) -> dict[NodeId, Position]:
    """Place ``node_order`` evenly on a circle of radius ``radius``.

    Parameters
    ----------
    node_order : tuple[NodeId, ...]
        Node IDs in the order they appear on the CDLL ring (forward
        circular order starting at the head slot).
    radius : float, optional
        Ring radius in axis units.
    start_angle : float, optional
        Angle of the first node, in radians. Defaults to ``pi / 2``
        (top of the circle).
    clockwise : bool, optional
        When ``True`` (default) the ring is laid out clockwise, matching
        the IsalSR convention.

    Returns
    -------
    dict[NodeId, Position]
        ``{node_id: (x, y)}`` mapping.
    """
    n = len(node_order)
    if n == 0:
        return {}
    if n == 1:
        return {node_order[0]: (0.0, 0.0)}
    direction = -1.0 if clockwise else 1.0
    positions: dict[NodeId, Position] = {}
    for i, v in enumerate(node_order):
        theta = start_angle + direction * (2.0 * math.pi * i / n)
        positions[v] = (radius * math.cos(theta), radius * math.sin(theta))
    return positions
