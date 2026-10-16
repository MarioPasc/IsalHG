"""fig_s5_mechanism (F-d): nearest sibling against nearest copy of another source, per query.

Two Design-B cells (pendant copies), one per row; columns: the word
(Levenshtein, tokens) and the bipartite edit path (symmetric min, edit cost).

- Row 1: the registered mech-cell (default WD50K(66), r = 2, the cell of the
  t-SNE figure's top row).
- Row 2: chosen by a fixed rule, :data:`ROW2_RULE`: the B pendant claim cell
  with the largest symmetric-edit-path lead over the word on 1-NN accuracy
  (seed means). The rule is stored in the figure's numbers.json.

Every query of every seed of a cell: the distance to its nearest sibling
(another copy of the same source; y axis) against the distance to its nearest
copy of another source (x axis). The distances are integers, so each panel is a
two-dimensional histogram (grey scale, logarithmic counts) with the diagonal
drawn; a query below the diagonal has its sibling strictly nearer, i.e. a
certain correct 1-NN decision, and a query on it is a tie. The printed shares
of both (means over seeds) are read from ``full_summary.json``
(``mechanism.<arm>.own_strictly_nearer`` and ``.tie``); the points are read
from the unit cell files under ``<root>``.
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

ARMS: tuple[tuple[str, str], ...] = ((K.OURS, "tokens"), (K.PATH_SYM, "edit cost"))
WIDTH_IN, HEIGHT_IN = 3.4, 3.5
ROW2_RULE = (
    "the B pendant claim cell with the largest symmetric-edit-path lead over the word on "
    "1-NN accuracy (seed means)"
)


def row2_cell(summary: dict[str, Any]) -> tuple[str, float]:
    """The cell :data:`ROW2_RULE` selects, and the edit path's lead there.

    Fixed before drawing so the second row is not picked by eye: among the B
    pendant claim cells, the largest ``mean 1-NN(sym edit path) - mean 1-NN(word)``.
    """
    cands = [
        c
        for c in summary["cells"].values()
        if c["design"] == "B" and c["condition"] == "pendant" and c["claim"]
    ]

    def lead(c: dict[str, Any]) -> float:
        return c["per_arm"][K.PATH_SYM]["acc1"]["mean"] - c["per_arm"][K.OURS]["acc1"]["mean"]

    best = max(cands, key=lead)
    return best["id"], lead(best)


def pooled(root: Path, col: str, r: int, arm: str) -> tuple[np.ndarray, np.ndarray, int]:
    """Nearest-sibling and nearest-other distances of every query of every seed."""
    same: list[float] = []
    other: list[float] = []
    files = sorted((root / f"B_{col}" / "cells").glob(f"B_{col}_r{r}_s*.json"))
    for path in files:
        res = json.loads(path.read_text())["arms"][arm]
        for a, b in zip(res["nn_same"], res["nn_other"], strict=True):
            if a is not None and b is not None:
                same.append(a)
                other.append(b)
    return np.asarray(same), np.asarray(other), len(files)


def _panel(
    ax: Any,  # noqa: ANN401
    root: Path,
    summary: dict[str, Any],
    cid: str,
    arm: str,
    unit: str,
    printed: S.Printed,
) -> dict[str, Any]:
    from matplotlib.colors import LogNorm

    _, _, col, r = cid.split("/")
    same, other, n_seeds = pooled(root, col, int(r.removeprefix("r")), arm)
    meta: dict[str, Any] = {"queries": int(len(same)), "seeds": n_seeds}
    if not len(same):
        ax.text(0.5, 0.5, "no data", ha="center", va="center", transform=ax.transAxes)
        return meta
    hi = float(np.quantile(np.concatenate([same, other]), 0.995))
    step = 1.0 if arm != K.PATH_SYM or hi <= 60 else max(1.0, round(hi / 60))
    edges = np.arange(-0.5, hi + step + 0.5, step)
    ax.hist2d(other, same, bins=[edges, edges], cmap="Greys", norm=LogNorm(), cmin=1)
    ax.plot([0, hi], [0, hi], color=S.WORD if arm == K.OURS else S.BEST, lw=0.8)
    ax.set_xlim(-0.5, hi + 0.5)
    ax.set_ylim(-0.5, hi + 0.5)
    ax.set_aspect("equal")
    ax.set_xlabel(f"nearest other source ({unit})")
    ax.set_ylabel(f"nearest sibling ({unit})")
    base = ["cells", cid, "mechanism", arm]
    near = printed.add(summary, [*base, "own_strictly_nearer", "mean"], 0, f"{cid} {arm}", 100.0)
    tie = printed.add(summary, [*base, "tie", "mean"], 0, f"{cid} {arm} tie", 100.0)
    ax.text(
        0.97,
        0.04,
        f"{S.LABELS[arm]}\nsibling nearer {near} %\ntie {tie} %",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=5.6,
        bbox={"facecolor": S.SURFACE, "edgecolor": "none", "alpha": 0.85, "pad": 1.0},
    )
    return meta


def draw(
    root: Path, summary: dict[str, Any], cid1: str, cid2: str
) -> tuple[Any, S.Printed, dict[str, Any]]:
    """Two rows (cells) by two columns (arms)."""
    import matplotlib.pyplot as plt

    printed = S.Printed()
    meta: dict[str, Any] = {}
    fig, axes = plt.subplots(2, len(ARMS), figsize=(WIDTH_IN, HEIGHT_IN), layout="constrained")
    for i, cid in enumerate((cid1, cid2)):
        _, _, col, r = cid.split("/")
        for j, (arm, unit) in enumerate(ARMS):
            ax = axes[i, j]
            meta[f"{cid}/{arm}"] = _panel(ax, root, summary, cid, arm, unit, printed)
        axes[i, 0].annotate(
            f"{S.COLLECTION_LABELS[col]}, r = {r.removeprefix('r')}",
            xy=(0, 1),
            xycoords="axes fraction",
            xytext=(0, 3),
            textcoords="offset points",
            fontsize=6.5,
            va="bottom",
        )
    return fig, printed, meta


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--root", type=Path, default=K.OUT_ROOT / "full")
    ap.add_argument("--out", type=Path, default=None, help="default <root>/section")
    ap.add_argument("--collection", default="wd50k66")
    ap.add_argument("--r", type=int, default=2)
    args = ap.parse_args()
    S.apply_rc()
    summary = json.loads((args.root / "full_summary.json").read_text())
    cid1 = f"B/pendant/{args.collection}/r{args.r}"
    cid2, lead = row2_cell(summary)
    fig, printed, meta = draw(args.root, summary, cid1, cid2)
    paths = S.save(
        fig,
        args.out or args.root / "section",
        "fig_s5_mechanism",
        printed,
        {
            "root": str(args.root),
            "cell": cid1,
            "cell2": cid2,
            "rule2": ROW2_RULE,
            "rule2_lead_acc1": lead,
            "panels": meta,
        },
    )
    print("\n".join(map(str, paths)))


if __name__ == "__main__":
    main()
