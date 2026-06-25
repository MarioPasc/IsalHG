"""Layout helpers shared across the three views.

Pure geometric maths -- no matplotlib at import time. NetworkX is
imported lazily inside :func:`compact_primal_layout`.
"""

from __future__ import annotations

import logging
import math
from typing import Any

from isalhg.types import NodeId
from isalhg.viz.base import Position

logger = logging.getLogger(__name__)


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


def compact_primal_layout(
    H: Any,
    *,
    seed: int = 0,
    margin: float = 0.18,
    spring_iterations: int = 80,
    spring_k: float | None = 0.9,
    fit_fraction: float = 0.78,
) -> dict[NodeId, Position]:
    """Spring layout on the primal graph with stray vertices pulled in.

    Auto-layouts in the three viz backends (XGI, HyperNetX, HypergraphX)
    each call a NetworkX spring/Kamada-Kawai layout internally and let
    disconnected vertices drift to the periphery, which forces the main
    cluster to shrink. This helper produces a single layout that:

    1. Builds the primal (clique-expansion) graph of ``H``.
    2. Spring-layouts the largest connected component, with an optimal
       inter-node distance of ``spring_k`` (larger k → more spread,
       more whitespace between the rendered hyperedge blobs).
    3. Normalises the result into a square of side ``2 * fit_fraction``
       centred at the origin (i.e. the hypergraph occupies the inner
       ``fit_fraction`` of the ``[-1, 1]^2`` canvas, leaving the outer
       band visually empty so adjacent hyperedge blobs do not touch
       the rounded frame).
    4. Places isolated / smaller-component vertices on a vertical strip
       just outside the main component's bounding box, separated by
       ``margin`` and ordered by ``NodeId``. The strip stays inside
       ``[-1.0 - margin, 1.0 + margin]``, so the main component still
       occupies ~80% of the figure rather than ~30% when one vertex
       drifts to the edge.

    Pass the returned dict to
    :func:`isalhg.viz.hypergraph_view.draw_hypergraph` via the
    ``layout`` keyword to override the backend's auto-layout.

    Parameters
    ----------
    H : SparseHypergraph
        Hypergraph to lay out.
    seed : int, optional
        PRNG seed for the spring layout; pinning makes the figure
        reproducible across runs.
    margin : float, optional
        Distance between the main bounding box and the stray-vertex
        strip, in normalised axis units.
    spring_iterations : int, optional
        Number of force iterations; lower values are faster but
        noisier.
    spring_k : float | None, optional
        Optimal inter-vertex distance forwarded to
        ``nx.spring_layout(k=...)``. Larger values push hyperedge
        blobs apart visually. ``None`` reverts to NetworkX's default
        ``1/sqrt(n)``.
    fit_fraction : float, optional
        Fraction of the ``[-1, 1]^2`` canvas the main component is
        scaled to occupy (default ``0.78``). Smaller fractions leave
        more empty margin between hyperedges and the panel frame.

    Returns
    -------
    dict[NodeId, Position]
        ``{node_id: (x, y)}`` for every vertex of ``H``.
    """
    import networkx as nx

    primal = H.primal_graph()
    g = nx.Graph()
    g.add_nodes_from(H.nodes())
    for u, neighbours in primal.items():
        for v in neighbours:
            if u < v:
                g.add_edge(u, v)

    components = sorted(nx.connected_components(g), key=len, reverse=True)
    if not components:
        return {}

    main = components[0]
    main_subgraph = g.subgraph(main)
    if len(main) <= 1:
        # Degenerate: single vertex / no edges. Lay everything out evenly.
        return cdll_ring_positions(tuple(sorted(H.nodes())))

    raw = nx.spring_layout(
        main_subgraph,
        seed=seed,
        iterations=spring_iterations,
        k=spring_k,
    )
    xs = [p[0] for p in raw.values()]
    ys = [p[1] for p in raw.values()]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    span_x = max(xmax - xmin, 1e-6)
    span_y = max(ymax - ymin, 1e-6)
    span = max(span_x, span_y)
    # Centre and rescale: the hypergraph occupies the inner
    # ``[-fit_fraction, fit_fraction]^2`` band; the outer ring of the
    # ``[-1, 1]^2`` canvas is visual padding.
    cx, cy = (xmax + xmin) / 2.0, (ymax + ymin) / 2.0
    scale = 2.0 * fit_fraction
    positions: dict[NodeId, Position] = {}
    for v, (x, y) in raw.items():
        positions[v] = (scale * (x - cx) / span, scale * (y - cy) / span)

    strays: list[NodeId] = sorted(v for comp in components[1:] for v in comp)
    if strays:
        # Vertical strip just to the right of the main bbox at x = 1 + margin.
        n = len(strays)
        strip_top, strip_bot = 0.9, -0.9
        step = (strip_top - strip_bot) / max(1, n)
        strip_x = 1.0 + margin
        for i, v in enumerate(strays):
            y = strip_top - (i + 0.5) * step if n > 1 else 0.0
            positions[v] = (strip_x, y)
        logger.debug(
            "compact_primal_layout: %d main + %d stray vertices over %d component(s)",
            len(main),
            len(strays),
            len(components),
        )

    return positions
