"""fig_s5_mechanism (F-d): nearest sibling against nearest copy of another source, per query.

For one Design-B cell (default: WD50K(66), pendant copies, r = 2, the cell of
the t-SNE figure's top row), every query of every seed: the distance to its
nearest sibling (another copy of the same source; y axis) against the distance
to its nearest copy of another source (x axis), under the word (Levenshtein,
tokens) and under the bipartite edit path (symmetric min, edit cost). The
distances are integers, so each panel is a two-dimensional histogram (grey
scale, logarithmic counts) with the diagonal drawn; a query below the diagonal
has its sibling strictly nearer, i.e. a certain correct 1-NN decision. The
printed share of such queries (mean over seeds) is read from
``full_summary.json`` (``mechanism.<arm>.own_strictly_nearer``); the points are
read from the unit cell files under ``<root>``.
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
WIDTH_IN, HEIGHT_IN = 3.4, 1.85


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


def draw(
    root: Path, summary: dict[str, Any], col: str, r: int
) -> tuple[Any, S.Printed, dict[str, Any]]:
    """Two panels; returns the figure, the printed numbers and the point counts."""
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm

    printed = S.Printed()
    meta: dict[str, Any] = {}
    cid = f"B/pendant/{col}/r{r}"
    fig, axes = plt.subplots(1, len(ARMS), figsize=(WIDTH_IN, HEIGHT_IN), layout="constrained")
    for ax, (arm, unit) in zip(axes, ARMS, strict=True):
        same, other, n_seeds = pooled(root, col, r, arm)
        meta[arm] = {"queries": int(len(same)), "seeds": n_seeds}
        if not len(same):
            ax.text(0.5, 0.5, "no data", ha="center", va="center", transform=ax.transAxes)
            continue
        hi = float(np.quantile(np.concatenate([same, other]), 0.995))
        step = 1.0 if arm != K.PATH_SYM or hi <= 60 else max(1.0, round(hi / 60))
        edges = np.arange(-0.5, hi + step + 0.5, step)
        h = ax.hist2d(other, same, bins=[edges, edges], cmap="Greys", norm=LogNorm(), cmin=1)
        ax.plot([0, hi], [0, hi], color=S.WORD if arm == K.OURS else S.BEST, lw=0.8)
        ax.set_xlim(-0.5, hi + 0.5)
        ax.set_ylim(-0.5, hi + 0.5)
        ax.set_aspect("equal")
        ax.set_xlabel(f"nearest other source ({unit})")
        ax.set_ylabel(f"nearest sibling ({unit})")
        share = printed.add(
            summary,
            ["cells", cid, "mechanism", arm, "own_strictly_nearer", "mean"],
            0,
            f"{cid} {arm}",
            scale=100.0,
        )
        ax.text(
            0.97,
            0.04,
            f"{S.LABELS[arm]}\nsibling nearer: {share} %",
            transform=ax.transAxes,
            ha="right",
            va="bottom",
            fontsize=5.8,
            bbox={"facecolor": S.SURFACE, "edgecolor": "none", "alpha": 0.85, "pad": 1.0},
        )
        meta[arm]["max_count"] = float(np.nanmax(h[0])) if np.isfinite(np.nanmax(h[0])) else 0
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
    fig, printed, meta = draw(args.root, summary, args.collection, args.r)
    paths = S.save(
        fig,
        args.out or args.root / "section",
        "fig_s5_mechanism",
        printed,
        {"root": str(args.root), "cell": f"B/pendant/{args.collection}/r{args.r}", **meta},
    )
    print("\n".join(map(str, paths)))


if __name__ == "__main__":
    main()
