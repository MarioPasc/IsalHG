"""Visual style and colour helpers.

Single source of truth for rcParams, colormaps, and colour lookup so
the instruction-strip token colour and the hypergraph drawing share a
mechanical correspondence by edge label / edge ID.

Port reference: IsalSR ``experiments/plotting_styles.py`` (Paul Tol
colour-blind palette, IEEE single-column dimensions, ``save_figure``
emitting pdf + svg + png).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.types import EdgeId, NodeId

if TYPE_CHECKING:
    from matplotlib.colors import Colormap
    from matplotlib.figure import Figure
else:
    Colormap = Any
    Figure = Any


# Paul-Tol bright qualitative palette (colourblind-safe), useful for
# small categorical sets (vocabulary size <= 8).
PAUL_TOL_BRIGHT: tuple[str, ...] = (
    "#4477AA",  # blue
    "#EE6677",  # red
    "#228833",  # green
    "#CCBB44",  # yellow
    "#66CCEE",  # cyan
    "#AA3377",  # purple
    "#BBBBBB",  # grey (reserved for W tokens / ghosts)
    "#EE7733",  # orange
)


INSTRUCTION_TOKEN_PALETTE: dict[str, str] = {
    "W": "#BBBBBB",
    "P": "#004488",
    "N": "#882200",
    # V and C inherit from the per-edge palette; placeholder entries
    # are still emitted so the strip key has a row for them.
    "V": "#228833",
    "C": "#EE7733",
}

GRAYED_FACE: str = "#DDDDDD"
GRAYED_EDGE: str = "#999999"
GRAYED_ALPHA: float = 0.25
ACTIVE_ALPHA: float = 0.85

POINTER_PALETTE: tuple[str, ...] = (
    "#EE6677",  # p_1 red
    "#4477AA",  # p_2 blue
    "#228833",  # p_3 green
    "#CCBB44",  # p_4 yellow
    "#AA3377",  # p_5 purple
    "#66CCEE",  # p_6 cyan
    "#EE7733",  # p_7 orange
    "#332288",  # p_8 indigo
    "#999933",  # p_9 olive
    "#882255",  # p_10 wine
)


# Default rcParams. Trade-off vs IsalSR: we keep "tab20" / "tab20c"
# defaults for >8 categorical sets and Paul-Tol for <=8.
_BASE_RCPARAMS: dict[str, Any] = {
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
    "font.family": "serif",
    "font.size": 9.0,
    "axes.titlesize": 9.0,
    "axes.labelsize": 8.0,
    "axes.linewidth": 0.7,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.labelsize": 7.0,
    "ytick.labelsize": 7.0,
    "legend.fontsize": 7.0,
    "lines.linewidth": 1.0,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
}


def apply_ieee_style() -> None:
    """Apply IEEE-ish single-column rcParams to the active matplotlib session."""
    import matplotlib.pyplot as plt  # local import: matplotlib stays optional

    plt.rcParams.update(_BASE_RCPARAMS)


def _get_cmap(name: str) -> Colormap:
    import matplotlib.pyplot as plt

    return plt.get_cmap(name)


def _hexify(rgba: tuple[float, float, float, float]) -> str:
    r, g, b = rgba[:3]
    return f"#{int(r * 255):02X}{int(g * 255):02X}{int(b * 255):02X}"


def color_for_vertex(v: NodeId, H: SparseHypergraph) -> str:
    """Return a hex colour for vertex ``v``.

    Strategy: when ``H.n_vertex_labels > 1`` -- partition the
    ``"tab20c"`` colormap into ``n_vertex_labels`` equal slices and
    index by ``H.vertex_label(v)``. When the vocabulary is trivial
    (single label class), fall back to ID-based colouring across
    ``"tab20"``.
    """
    if H.n_vertex_labels > 1:
        cmap = _get_cmap("tab20c")
        t = H.vertex_label(v) / max(1, H.n_vertex_labels - 1)
        return _hexify(cmap(t))
    # ID-based fallback
    n = max(1, H.n_nodes - 1)
    cmap = _get_cmap("tab20c")
    return _hexify(cmap(v / n))


def color_for_edge(e: EdgeId, H: SparseHypergraph) -> str:
    """Return a hex colour for hyperedge ``e``.

    Same strategy as :func:`color_for_vertex`: label-driven when the
    vocabulary is non-trivial, ID-driven otherwise. Uses ``"tab20"``
    (rather than ``"tab20c"``) so vertex and edge palettes do not
    collide.
    """
    if H.n_edge_labels > 1:
        cmap = _get_cmap("tab20")
        t = H.edge_label(e) / max(1, H.n_edge_labels - 1)
        return _hexify(cmap(t))
    n = max(1, H.n_edges - 1)
    cmap = _get_cmap("tab20")
    return _hexify(cmap(e / n))


def build_vertex_palette(H: SparseHypergraph) -> dict[NodeId, str]:
    """Return a ``{node_id: hex}`` mapping covering every vertex of ``H``."""
    return {v: color_for_vertex(v, H) for v in H.nodes()}


def build_edge_palette(H: SparseHypergraph) -> dict[EdgeId, str]:
    """Return a ``{edge_id: hex}`` mapping covering every hyperedge of ``H``."""
    return {e: color_for_edge(e, H) for e in H.edges()}


def color_for_token(
    token_kind: str,
    token_serialised: str | None,
    *,
    edge_palette: dict[EdgeId, str] | None = None,
    edge_id_for_token: int | None = None,
) -> str:
    """Return the colour for one rendered token cell.

    ``V`` and ``C`` tokens inherit the colour of the edge they construct
    (resolved via ``edge_id_for_token``); ``W / P / N`` use the static
    palette in :data:`INSTRUCTION_TOKEN_PALETTE`.
    """
    if (
        token_kind in ("V", "C")
        and edge_palette is not None
        and edge_id_for_token is not None
        and edge_id_for_token in edge_palette
    ):
        return edge_palette[edge_id_for_token]
    if token_kind is None:
        return GRAYED_FACE
    return INSTRUCTION_TOKEN_PALETTE.get(token_kind, GRAYED_FACE)


def save_figure(
    fig: Figure,
    basepath: str | Path,
    *,
    formats: tuple[str, ...] = ("pdf", "svg", "png"),
    dpi: int = 300,
) -> list[Path]:
    """Save ``fig`` to ``basepath.{fmt}`` for every ``fmt`` in ``formats``.

    The directory containing ``basepath`` is created if it does not exist.
    Returns the list of written paths.
    """
    bp = Path(basepath)
    bp.parent.mkdir(parents=True, exist_ok=True)
    out: list[Path] = []
    for fmt in formats:
        p = bp.with_suffix(f".{fmt}")
        fig.savefig(p, dpi=dpi)
        out.append(p)
    return out
