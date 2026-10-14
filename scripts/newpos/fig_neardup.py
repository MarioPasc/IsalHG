"""Figure for C8: near-neighbour retrieval of structural near-duplicates.

Three panels, one dot per (representation, collection) with its 95 % cluster
bootstrap interval: MRR of the nearest true neighbour for (a) pendant one-edit
neighbours, (b) interior one-edit neighbours, (c) all two-edit neighbours.
Reads ``neardup_<collection>.json`` and ``neardup_r2_<collection>.json``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/NEWPOS_2026-10-13/neardup")
COLLECTIONS = (
    ("wd50k66", "WD50K(66)", "#2a78d6", "o"),
    ("wd50k100", "WD50K(100)", "#eb6834", "s"),
    ("ndc_classes", "NDC-classes", "#1baf7a", "^"),
    ("ndc_substances", "NDC-substances", "#eda100", "D"),
)
ARMS = (
    ("isal_ow_struct", r"Isal word $w^{\circ}$ (ours)"),
    ("fact_rank", "fact list (canonical rank)"),
    ("nauty_cert", "nauty certificate, bytes"),
    ("nauty_cert_rows", "nauty certificate, rows"),
    ("bipartite_ged_path", "bipartite GED, edit path"),
    ("bipartite_ged_assign", "bipartite GED, assignment"),
    ("wl_l1", "WL histogram"),
    ("netlsd", "NetLSD"),
    ("hpd_jsd", "HPD"),
    ("degree_seq_l1", "degree-sequence floor"),
    ("size_l1", "size floor"),
)
PANELS = (
    ("r1", "MRR_pendant", "(a) one edit apart, pendant edit"),
    ("r1", "MRR_interior", "(b) one edit apart, interior edit"),
    ("r2", "all", "(c) two edits apart, all"),
)


def point(data: dict, panel: tuple[str, str, str], arm: str) -> tuple[float, float, float] | None:
    kind, key, _ = panel
    if kind == "r1":
        r = data["arms"].get(arm, {})
        if key not in r:
            return None
        lo, hi = data["tests"][key]["ci"][arm]
        return r[key], lo, hi
    r = data["arms"].get(arm, {})
    if f"MRR_{key}" not in r:
        return None
    lo, hi = data["tests"][key]["ci"][arm]
    return r[f"MRR_{key}"], lo, hi


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--out", type=Path, default=ROOT / "fig_neardup_retrieval.pdf")
    args = ap.parse_args()
    r1 = {c: json.loads((args.root / f"neardup_{c}.json").read_text()) for c, *_ in COLLECTIONS}
    r2 = {c: json.loads((args.root / f"neardup_r2_{c}.json").read_text()) for c, *_ in COLLECTIONS}
    plt.rcParams.update(
        {
            "font.size": 7,
            "axes.titlesize": 7,
            "axes.labelsize": 7,
            "xtick.labelsize": 6.5,
            "ytick.labelsize": 6.5,
            "legend.fontsize": 6.5,
            "axes.edgecolor": "#8a8a85",
            "axes.linewidth": 0.6,
            "xtick.color": "#4a4a46",
            "ytick.color": "#1f1f1d",
            "pdf.fonttype": 42,
        }
    )
    fig, axes = plt.subplots(1, 3, figsize=(7.16, 2.75), sharey=True)
    offsets = (-0.27, -0.09, 0.09, 0.27)
    ys = list(range(len(ARMS)))[::-1]
    for ax, panel in zip(axes, PANELS):
        source = r1 if panel[0] == "r1" else r2
        for (c, label, color, marker), off in zip(COLLECTIONS, offsets):
            for (arm, _), y in zip(ARMS, ys):
                p = point(source[c], panel, arm)
                if p is None:
                    continue
                v, lo, hi = p
                ax.plot(
                    [lo, hi],
                    [y + off, y + off],
                    color=color,
                    lw=0.8,
                    solid_capstyle="round",
                    zorder=2,
                )
                ax.plot(
                    v,
                    y + off,
                    marker=marker,
                    ms=3.6,
                    color=color,
                    mec="white",
                    mew=0.5,
                    ls="none",
                    zorder=3,
                    label=label if arm == "isal_ow_struct" else None,
                )
        ax.axhspan(ys[0] - 0.45, ys[0] + 0.45, color="#ecebe6", zorder=0)
        ax.set_xlim(0, 1)
        ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
        ax.grid(axis="x", color="#e2e1dc", lw=0.5, zorder=1)
        ax.set_title(panel[2], loc="left")
        ax.set_xlabel("MRR of the nearest true neighbour")
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        ax.tick_params(axis="y", length=0)
    axes[0].set_yticks(ys)
    axes[0].set_yticklabels([name for _, name in ARMS])
    axes[0].get_yticklabels()[0].set_fontweight("bold")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles, labels, loc="upper center", ncol=4, frameon=False, bbox_to_anchor=(0.62, 1.02)
    )
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out)
    fig.savefig(args.out.with_suffix(".png"), dpi=220)
    print(f"wrote {args.out} and .png")


if __name__ == "__main__":
    main()
