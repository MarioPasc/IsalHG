"""fig_s5_accuracy (F-b): 1-NN accuracy against r, seed means with 95 % BCa bands.

Rows: Design B (pendant copies), Design C (C-all, c = 3), Design D (pendant
copies against the catalogue). Columns: the four collections. In each panel
the word is blue (solid, circles), the panel's best verdict competitor (the
highest mean 1-NN over r among the design's registered competitors) is
vermillion (solid, squares) with its name printed, the exact-arm ceiling is a
dashed black line, and every other arm of the run, the added rows included,
is a thin grey line. An infeasible Design-C panel (fewer than 10 blocks at
some seed) is shaded and labelled. Reads ``<root>/full_summary.json``.
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
    ("B/pendant/{col}/r{r}", "B"),
    ("C/C-all/c3/{col}/r{r}", "C (C-all, c = 3)"),
    ("D/pendant/{col}/r{r}", "D"),
)
RS = (1, 2, 3)
WIDTH_IN, HEIGHT_IN = 7.0, 3.0


def _series(cells: dict[str, Any], pattern: str, col: str, arm: str) -> tuple[list[float], ...]:
    mean, lo, hi = [], [], []
    for r in RS:
        c = cells.get(pattern.format(col=col, r=r))
        st = c["per_arm"].get(arm, {}).get("acc1") if c else None
        if st is None:
            mean.append(np.nan)
            lo.append(np.nan)
            hi.append(np.nan)
            continue
        b0, b1 = st["bca"]
        mean.append(st["mean"])
        lo.append(st["mean"] if b0 is None else b0)
        hi.append(st["mean"] if b1 is None else b1)
    return mean, lo, hi


def _ceiling(cells: dict[str, Any], pattern: str, col: str) -> list[float]:
    out = []
    for r in RS:
        c = cells.get(pattern.format(col=col, r=r))
        vals = c["diag"].get("exact_ceiling") if c else None
        out.append(float(np.mean(vals)) if vals else np.nan)
    return out


def best_competitor(cells: dict[str, Any], pattern: str, col: str) -> str | None:
    """The design's verdict competitor with the highest mean 1-NN over r in this panel."""
    first = cells.get(pattern.format(col=col, r=1))
    if first is None:
        return None
    comps = [a for a in first["competitors"] if a in first["per_arm"]]
    return max(comps, key=lambda a: np.nanmean(_series(cells, pattern, col, a)[0]))


def draw(summary: dict[str, Any]) -> tuple[Any, dict[str, str]]:
    """The grid; returns the figure and the best competitor of every panel."""
    import matplotlib.pyplot as plt

    cells = summary["cells"]
    fig, axes = plt.subplots(
        len(ROWS),
        len(S.COLLECTIONS),
        figsize=(WIDTH_IN, HEIGHT_IN),
        sharex=True,
        sharey=True,
        layout="constrained",
    )
    bests: dict[str, str] = {}
    for i, (pattern, row_label) in enumerate(ROWS):
        for j, col in enumerate(S.COLLECTIONS):
            ax = axes[i, j]
            first = cells.get(pattern.format(col=col, r=1))
            ax.grid(True, color=S.GRID, lw=0.4)
            ax.set_xticks(RS)
            # Headroom above 1 holds the best competitor's name clear of the lines.
            ax.set_ylim(-0.02, 1.2)
            ax.set_yticks((0.0, 0.5, 1.0))
            ax.set_xlim(0.8, 3.2)
            if i == 0:
                ax.set_title(S.COLLECTION_LABELS[col], pad=2)
            if j == 0:
                ax.set_ylabel(f"{row_label}\n1-NN accuracy")
            if i == len(ROWS) - 1:
                ax.set_xlabel("pendant removals r")
            if first is None:
                ax.text(0.5, 0.5, "no data", ha="center", va="center", transform=ax.transAxes)
                continue
            best = best_competitor(cells, pattern, col)
            bests[pattern.format(col=col, r="*")] = best or ""
            for arm in first["per_arm"]:
                if arm in (K.OURS, best):
                    continue
                ax.plot(RS, _series(cells, pattern, col, arm)[0], color=S.OTHER, lw=0.45, zorder=1)
            ax.plot(RS, _ceiling(cells, pattern, col), color=S.INK, lw=0.7, ls="--", zorder=2)
            for arm, colour, marker, lw, z in (
                (best, S.BEST, "s", 1.0, 3),
                (K.OURS, S.WORD, "o", 1.4, 4),
            ):
                if arm is None:
                    continue
                m, lo, hi = _series(cells, pattern, col, arm)
                ax.fill_between(RS, lo, hi, color=colour, alpha=0.2, lw=0, zorder=z - 1)
                ax.plot(RS, m, color=colour, marker=marker, ms=2.8, lw=lw, zorder=z)
            ax.text(
                3.15,
                1.18,
                f"best: {S.LABELS[best]}" if best else "",
                ha="right",
                va="top",
                fontsize=5.5,
                color=S.BEST,
            )
            if first.get("feasible") is False:
                ax.set_facecolor("#f1f0eb")
                ax.text(0.03, 0.04, "infeasible", transform=ax.transAxes, fontsize=5.5)
    from matplotlib.lines import Line2D

    handles = [
        Line2D([], [], color=S.WORD, marker="o", ms=3, lw=1.4, label=S.LABELS[K.OURS]),
        Line2D([], [], color=S.BEST, marker="s", ms=3, lw=1.0, label="best competitor"),
        Line2D([], [], color=S.INK, lw=0.7, ls="--", label="exact-arm ceiling"),
        Line2D([], [], color=S.OTHER, lw=0.45, label="other arms"),
    ]
    fig.legend(handles=handles, loc="outside lower center", ncol=4, frameon=False)
    return fig, bests


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--root", type=Path, default=K.OUT_ROOT / "full")
    ap.add_argument("--out", type=Path, default=None, help="default <root>/section")
    args = ap.parse_args()
    S.apply_rc()
    summary = json.loads((args.root / "full_summary.json").read_text())
    fig, bests = draw(summary)
    paths = S.save(
        fig,
        args.out or args.root / "section",
        "fig_s5_accuracy",
        S.Printed(),
        {"root": str(args.root), "rows": [r[0] for r in ROWS], "best_competitor": bests},
    )
    print("\n".join(map(str, paths)))


if __name__ == "__main__":
    main()
