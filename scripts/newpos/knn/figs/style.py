"""Shared style of the Section-S5 figures: palette, fonts, labels, output and printed numbers.

Palette and fonts follow the supplement's contract
(``supplementary/figures/knn/README.md``): Okabe & Ito's colour-blind-safe set
("Color Universal Design", 2008) with the word in the paper's blue
``#0072B2``, the best competitor of a panel in ``#D55E00`` and every other
competitor in ``#8C8C8C``; serif type at 7 pt at print size; no in-plot
titles; every panel readable in grey (markers and line styles carry the same
distinctions as the hues).

Printed numbers. Every number a figure prints is registered with
:class:`Printed`: its value, the string printed and its JSON path in
``full_summary.json``. ``save`` writes them to ``<stem>.numbers.json`` next to
the PDF and PNG, which is what the figure test checks against the summary.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402

WORD, BEST, OTHER = "#0072B2", "#D55E00", "#8C8C8C"
INK, INK2, GRID, SURFACE = "#1f1f1d", "#4a4a46", "#e6e5e0", "#ffffff"
GOOD = "#009E73"
#: Okabe-Ito hues and shapes for categorical sources (colour x shape = one source).
SOURCE_HUES: tuple[str, ...] = ("#E69F00", "#56B4E9", "#009E73", "#CC79A7")
SOURCE_SHAPES: tuple[str, ...] = ("o", "s", "^")
LABELS: dict[str, str] = {
    "isal_ow_struct": r"word $w^{\circ}$",
    "bipartite_ged_path_sym": "bipartite edit path",
    "bipartite_ged_path": "bipartite edit path (cached orientation)",
    "bipartite_ged_assign": "bipartite assignment",
    "wl_h1": "WL, one round",
    "wl_l1": "WL histogram",
    "nauty_cert_rows": "nauty certificate rows",
    "nauty_cert": "nauty certificate bytes",
    "fact_rank": "fact list",
    "netlsd": "NetLSD",
    "hpd_jsd": "HPD",
    "degree_seq_l1": "degree-sequence floor",
    "size_l1": "size floor",
}
COLLECTION_LABELS = {
    "wd50k66": "WD50K(66)",
    "wd50k100": "WD50K(100)",
    "ndc_classes": "NDC-classes",
    "ndc_substances": "NDC-substances",
}
COLLECTIONS: tuple[str, ...] = tuple(COLLECTION_LABELS)


def apply_rc() -> None:
    """Serif type at 7 pt and quiet axes."""
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Nimbus Roman", "TeX Gyre Termes", "DejaVu Serif"],
            "mathtext.fontset": "stix",
            "font.size": 7,
            "axes.titlesize": 7,
            "axes.labelsize": 7,
            "xtick.labelsize": 6.5,
            "ytick.labelsize": 6.5,
            "legend.fontsize": 6.5,
            "axes.edgecolor": "#8a8a85",
            "axes.linewidth": 0.5,
            "xtick.major.width": 0.5,
            "ytick.major.width": 0.5,
            "xtick.major.size": 2.0,
            "ytick.major.size": 2.0,
            "xtick.color": INK2,
            "ytick.color": INK2,
            "axes.labelcolor": INK,
            "text.color": INK,
            "pdf.fonttype": 42,
            "savefig.dpi": 300,
        }
    )


def source_style(j: int) -> tuple[str, str]:
    """Hue and marker of the ``j``-th source."""
    return SOURCE_HUES[j % len(SOURCE_HUES)], SOURCE_SHAPES[(j // len(SOURCE_HUES)) % 3]


def path_str(path: list[Any]) -> str:
    """``cells["B/pendant/wd50k66/r2"].per_arm.isal_ow_struct.acc1.mean`` style."""
    out = ""
    for p in path:
        if isinstance(p, int):
            out += f"[{p}]"
        elif "/" in str(p) or "-" in str(p):
            out += f'["{p}"]'
        else:
            out += ("." if out else "") + str(p)
    return out


def lookup(summary: dict[str, Any], path: list[Any]) -> Any:  # noqa: ANN401
    """The value at ``path`` in the decoded summary."""
    node: Any = summary
    for p in path:
        node = node[p]
    return node


@dataclass
class Printed:
    """The numbers a figure prints, each with its source path."""

    entries: list[dict[str, Any]] = field(default_factory=list)

    def add(
        self, summary: dict[str, Any], path: list[Any], nd: int, where: str, scale: float = 1.0
    ) -> str:
        """Look ``path`` up, scale and format it to ``nd`` decimals, record it, return it."""
        value = float(lookup(summary, path))
        text = f"{value * scale:.{nd}f}"
        self.entries.append(
            {
                "path": path,
                "path_str": path_str(path),
                "value": value,
                "scale": scale,
                "printed": text,
                "nd": nd,
                "where": where,
            }
        )
        return text


def save(fig: Figure, out: Path, stem: str, printed: Printed, meta: dict[str, Any]) -> list[Path]:
    """Vector PDF, a 200-dpi PNG preview and the printed-numbers sidecar."""
    out.mkdir(parents=True, exist_ok=True)
    paths = [out / f"{stem}.pdf", out / f"{stem}.png", out / f"{stem}.numbers.json"]
    fig.savefig(paths[0])
    fig.savefig(paths[1], dpi=200)
    paths[2].write_text(json.dumps({"figure": stem, **meta, "printed": printed.entries}, indent=1))
    plt.close(fig)
    return paths
