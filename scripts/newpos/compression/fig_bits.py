"""Figure: bits per knowledge base by fact-count bin, and collection-level compressor bytes.

Top row, one panel per collection: median held-out order-3 code length (bits) of each
representation against the fact-count bin, with a bootstrap 95 % interval of the
median; bins under 20 members are drawn hollow. Bottom row: bytes per knowledge base
under xz, zstd and bzip2 (self-contained number: best of dictionary-charged integer or
code-point renderings and the literal text), with the member-bootstrap 95 % interval.
Colour follows the representation, never its rank; markers and line styles repeat the
identity so the figure survives greyscale and colour-vision deficiency.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.newpos.compression.serialize import FACT_BINS  # noqa: E402

COLLECTIONS = ("wd50k66", "ndc_classes", "wd50k100", "ndc_substances")
BINS = [label for label, _, _ in FACT_BINS]
COMPRESSORS = ("xz", "zstd", "bzip2")
MIN_BIN = 20

# Fixed entity order -> categorical slots 1..7 of the reference palette (light mode).
STYLE: dict[str, dict[str, object]] = {
    "w_o": {"color": "#2a78d6", "marker": "o", "ls": "-", "lw": 2.0, "label": "w_o (ordered walk)"},
    "cert_bytes": {
        "color": "#eb6834",
        "marker": "s",
        "ls": "-",
        "lw": 1.4,
        "label": "certificate, bytes",
    },
    "cert_rows": {
        "color": "#1baf7a",
        "marker": "^",
        "ls": "-",
        "lw": 1.4,
        "label": "certificate, rows",
    },
    "cert_ints": {
        "color": "#eda100",
        "marker": "D",
        "ls": "-",
        "lw": 1.4,
        "label": "certificate, integers",
    },
    "cert_ints_ut": {
        "color": "#6250d6",
        "marker": "v",
        "ls": "--",
        "lw": 1.4,
        "label": "certificate, upper-triangle integers",
    },
    "fact": {
        "color": "#e87ba4",
        "marker": "P",
        "ls": "-",
        "lw": 1.4,
        "label": "canonical-rank fact list",
    },
    "incid": {"color": "#008300", "marker": "X", "ls": "-", "lw": 1.4, "label": "incidence list"},
}
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"


def bin_median_ci(
    values: np.ndarray, reps: int = 1000, seed: int = 0
) -> tuple[float, float, float]:
    """Median with a percentile bootstrap 95 % interval."""
    rng = np.random.default_rng(seed)
    draws = rng.choice(values, size=(reps, values.size), replace=True)
    medians = np.median(draws, axis=1)
    low, high = np.quantile(medians, [0.025, 0.975])
    return float(np.median(values)), float(low), float(high)


def draw_bits_panel(ax: plt.Axes, perkb: pd.DataFrame, title: str) -> None:
    """One collection: median order-3 bits against the fact-count bin."""
    counts = perkb[perkb.representation == "w_o"].groupby("fact_bin")["kb_id"].nunique()
    for arm, style in STYLE.items():
        frame = perkb[perkb.representation == arm]
        xs, ys, lows, highs, solid = [], [], [], [], []
        for i, label in enumerate(BINS):
            values = frame[frame.fact_bin == label]["bits_ngram3"].to_numpy(dtype=float)
            if values.size == 0:
                continue
            point, low, high = bin_median_ci(values)
            xs.append(i)
            ys.append(point)
            lows.append(low)
            highs.append(high)
            solid.append(values.size >= MIN_BIN)
        ax.plot(xs, ys, color=style["color"], ls=style["ls"], lw=style["lw"], zorder=3)
        ax.vlines(xs, lows, highs, color=style["color"], lw=0.8, zorder=3)
        for x, y, ok in zip(xs, ys, solid, strict=True):
            ax.plot(
                [x],
                [y],
                marker=style["marker"],
                ms=7,
                mfc=style["color"] if ok else "white",
                mec=style["color"],
                mew=1.2,
                ls="none",
                zorder=4,
            )
    ax.set_yscale("log")
    ax.set_xticks(range(len(BINS)))
    ax.set_xticklabels([f"{b}\n(n={int(counts.get(b, 0))})" for b in BINS], fontsize=7.5)
    ax.set_title(title, fontsize=10, color=INK, loc="left")
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.tick_params(colors=INK_2, labelsize=8)


def draw_compressor_panel(ax: plt.Axes, comp: pd.DataFrame, title: str) -> None:
    """One collection: bytes per knowledge base per compressor, one bar per representation."""
    arms = list(STYLE)
    width = 0.8 / len(arms)
    sel = comp[comp.number == "self_contained"]
    for j, arm in enumerate(arms):
        values, lows, highs = [], [], []
        for kind in COMPRESSORS:
            row = sel[(sel.arm == arm) & (sel.compressor == kind)]
            if row.empty:
                values.append(np.nan)
                lows.append(np.nan)
                highs.append(np.nan)
                continue
            r = row.iloc[0]
            values.append(r["bytes_per_kb"])
            shift = r["bytes_per_kb"] - r["boot_mean"]
            lows.append(r["ci_low"] + shift)
            highs.append(r["ci_high"] + shift)
        x = np.arange(len(COMPRESSORS)) + (j - (len(arms) - 1) / 2) * width
        ax.bar(
            x,
            values,
            width=width * 0.86,
            color=STYLE[arm]["color"],
            edgecolor="white",
            linewidth=0.8,
            zorder=3,
        )
        ax.vlines(x, lows, highs, color=INK_2, lw=0.7, zorder=4)
    ax.set_xticks(range(len(COMPRESSORS)))
    ax.set_xticklabels(COMPRESSORS, fontsize=8)
    ax.set_title(title, fontsize=10, color=INK, loc="left")
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.tick_params(colors=INK_2, labelsize=8)


def main(argv: list[str] | None = None) -> None:
    """Command-line entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--res", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=None, help="default <res>/fig_bits.pdf")
    args = ap.parse_args(argv)
    present = [c for c in COLLECTIONS if (args.res / f"perkb_{c}.csv").exists()]
    fig, axes = plt.subplots(2, len(present), figsize=(3.6 * len(present), 6.4), squeeze=False)
    for col, name in enumerate(present):
        perkb = pd.read_csv(args.res / f"perkb_{name}.csv")
        n_members = perkb["kb_id"].nunique()
        draw_bits_panel(axes[0, col], perkb, f"{name} (N = {n_members:,})")
        comp_path = args.res / f"compressors_{name}.csv"
        if comp_path.exists():
            draw_compressor_panel(axes[1, col], pd.read_csv(comp_path), f"{name}: whole collection")
    axes[0, 0].set_ylabel("median bits per KB\n(held-out 3-gram, log scale)", fontsize=9, color=INK)
    axes[1, 0].set_ylabel("bytes per KB\n(self-contained)", fontsize=9, color=INK)
    handles = [
        plt.Line2D(
            [0],
            [0],
            color=s["color"],
            marker=s["marker"],
            ls=s["ls"],
            lw=s["lw"],
            ms=7,
            label=s["label"],
        )
        for s in STYLE.values()
    ]
    fig.legend(
        handles=handles,
        loc="lower center",
        ncol=4,
        frameon=False,
        fontsize=8.5,
        bbox_to_anchor=(0.5, 0.0),
    )
    fig.text(
        0.5,
        0.095,
        "Top: lines are bootstrap 95 % intervals of the median; hollow markers have fewer than "
        f"{MIN_BIN} members.\nBottom: bars are the full-collection point; lines are the 95 % "
        "replicate interval (distinct-member bootstrap, about 63 % of the members each),\n"
        "translated to the point.",
        ha="center",
        fontsize=7.5,
        color=INK_2,
    )
    fig.tight_layout(rect=(0, 0.14, 1, 1))
    out = args.out or args.res / "fig_bits.pdf"
    fig.savefig(out)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
