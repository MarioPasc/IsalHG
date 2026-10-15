"""fig_s5_gap (F-c): the word's 1-NN accuracy minus that of the best competitor, every cell.

A row is a design and stratum, a column a (collection, r); Design A has no r
and spans its collection's three columns. A square is coloured by the mean
over seeds of the paired difference between the word and the cell's best
verdict competitor (diverging scale centred at 0: blue favours the word,
vermillion the competitor). A dot marks a Holm-corrected one-sided p < 0.05
for the word (one-sided paired Wilcoxon of word > best competitor over seeds,
Holm over the design's verdict competitors). Hatched: an infeasible Design-C
cell. Blank: no such cell (the edit mix runs on the WD50K collections only).
Cells outside a claim (C-pend, Design D at r = 3) are drawn like the others.
Reads ``<root>/full_summary.json``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import knn_lib as K  # noqa: E402, N812
import style as S  # noqa: E402, N812

ROWS: tuple[tuple[str, str], ...] = (
    ("A/lineage/{col}", "A"),
    ("B/pendant/{col}/r{r}", "B"),
    ("B/mix/{col}/r{r}", "B, edit mix"),
    ("C/C-all/c3/{col}/r{r}", "C-all, c = 3"),
    ("C/C-int/c3/{col}/r{r}", "C-int, c = 3"),
    ("C/C-pend/c3/{col}/r{r}", "C-pend, c = 3"),
    ("C/C-all/c6/{col}/r{r}", "C-all, c = 6"),
    ("D/pendant/{col}/r{r}", "D"),
    ("D/empirical/{col}/r{r}", "D, edit mix"),
)
RS = (1, 2, 3)
ALPHA = 0.05
WIDTH_IN, HEIGHT_IN = 3.4, 2.75
SHORT_COLL = {
    "wd50k66": "WD66",
    "wd50k100": "WD100",
    "ndc_classes": "NDCc",
    "ndc_substances": "NDCs",
}


def _cmap() -> Any:  # noqa: ANN401
    from matplotlib.colors import LinearSegmentedColormap

    return LinearSegmentedColormap.from_list("word_vs_best", [S.BEST, "#f7f7f5", S.WORD])


def _cell_ids(cells: dict[str, Any], pattern: str, col: str) -> list[tuple[str, float, float]]:
    """``(cell id, x, width)`` of the squares of one row and collection."""
    j = S.COLLECTIONS.index(col)
    if "{r}" not in pattern:
        return [(pattern.format(col=col), j * 3, 3)]
    return [(pattern.format(col=col, r=r), j * 3 + k, 1) for k, r in enumerate(RS)]


def _infeasible(cells: dict[str, Any], cid: str) -> bool:
    if cid in cells:
        return cells[cid].get("feasible") is False
    # A Design-C job whose pool never held two blocks has no per-r cell.
    stem = cid.rsplit("/", 1)[0]
    none = cells.get(f"{stem}/none")
    return bool(none) and none.get("feasible") is False


def draw(summary: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
    """The matrix; returns the figure and the colour limit and marks used."""
    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize
    from matplotlib.patches import Rectangle

    cells = summary["cells"]
    vals = [
        abs(c["diff_word_minus_best"]["acc1"]["mean"])
        for c in cells.values()
        if c["diff_word_minus_best"].get("acc1")
    ]
    lim = max(0.05, float(np.ceil(max(vals, default=0.1) * 20) / 20))
    norm = Normalize(-lim, lim)
    fig, ax = plt.subplots(figsize=(WIDTH_IN, HEIGHT_IN), layout="constrained")
    marks: dict[str, bool] = {}
    for i, (pattern, _) in enumerate(ROWS):
        y = len(ROWS) - 1 - i
        for col in S.COLLECTIONS:
            for cid, x, w in _cell_ids(cells, pattern, col):
                if _infeasible(cells, cid):
                    ax.add_patch(
                        Rectangle(
                            (x, y),
                            w,
                            1,
                            facecolor="#ecebe6",
                            edgecolor=S.SURFACE,
                            hatch="/////",
                            lw=0.6,
                        )
                    )
                    continue
                c = cells.get(cid)
                d = c["diff_word_minus_best"].get("acc1") if c else None
                if not d:
                    continue
                ax.add_patch(
                    Rectangle(
                        (x, y),
                        w,
                        1,
                        facecolor=_cmap()(norm(d["mean"])),
                        edgecolor=S.SURFACE,
                        lw=0.6,
                    )
                )
                best = c["best_competitor"]["acc1"]["arm"]
                sig = c["tests"]["acc1"][best]["p_holm"] < ALPHA
                marks[cid] = sig
                if sig:
                    ax.plot(x + w / 2, y + 0.5, "o", ms=2.2, color=S.INK, mec=S.SURFACE, mew=0.3)
    ncol = len(S.COLLECTIONS) * len(RS)
    ax.set_xlim(0, ncol)
    ax.set_ylim(0, len(ROWS))
    ax.set_xticks([k + 0.5 for k in range(ncol)])
    ax.set_xticklabels([str(r) for _ in S.COLLECTIONS for r in RS], fontsize=5.5)
    ax.set_xlabel("r", labelpad=1)
    for j, col in enumerate(S.COLLECTIONS):
        ax.text(j * 3 + 1.5, len(ROWS) + 0.2, SHORT_COLL[col], ha="center", va="bottom", fontsize=6)
        if j:
            ax.axvline(j * 3, color=S.INK2, lw=0.5)
    ax.set_yticks([len(ROWS) - 1 - i + 0.5 for i in range(len(ROWS))])
    ax.set_yticklabels([lbl for _, lbl in ROWS], fontsize=6)
    ax.tick_params(length=0, pad=1.5)
    for side in ax.spines.values():
        side.set_visible(False)
    sm = plt.cm.ScalarMappable(norm=norm, cmap=_cmap())
    cb = fig.colorbar(sm, ax=ax, orientation="horizontal", fraction=0.06, aspect=40, pad=0.02)
    cb.set_label("word − best competitor, 1-NN accuracy", fontsize=6)
    cb.ax.tick_params(labelsize=5.5, length=1.5)
    return fig, {"limit": lim, "holm_word_greater_p_lt_0.05": marks}


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--root", type=Path, default=K.OUT_ROOT / "full")
    ap.add_argument("--out", type=Path, default=None, help="default <root>/section")
    args = ap.parse_args()
    S.apply_rc()
    summary = json.loads((args.root / "full_summary.json").read_text())
    fig, meta = draw(summary)
    paths = S.save(
        fig,
        args.out or args.root / "section",
        "fig_s5_gap",
        S.Printed(),
        {"root": str(args.root), "alpha": ALPHA, **meta},
    )
    print("\n".join(map(str, paths)))


if __name__ == "__main__":
    main()
