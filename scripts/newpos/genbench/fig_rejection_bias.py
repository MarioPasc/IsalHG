"""Figure: what survives the domain filter, and how many draws it takes to get it.

Per collection (rows): (a) the fact-count (m) distribution of the collection against
the usable samples of each arm, averaged over seeds; (b) the star fraction of the
usable samples against the collection's; (c) usable and valid-unique-novel samples
per 10,000 draws on a log axis. Arms with fewer than the minimum usable samples on
too many seeds are named in the legend and not drawn in (a) and (b).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.newpos.genbench import common as gb  # noqa: E402
from scripts.newpos.genbench.analyze import Bench, ci  # noqa: E402

# Okabe-Ito: distinguishable under the common colour-vision deficiencies.
COLORS = {
    "ow_ngram": "#0072B2",
    "fact_ngram": "#D55E00",
    "fact_ngram_lcc": "#E69F00",
    "incidence_ngram": "#009E73",
}
LABELS = {
    "ow_ngram": "ordered walk w° (ours)",
    "fact_ngram": "fact list",
    "fact_ngram_lcc": "fact list + LCC repair",
    "incidence_ngram": "incidence list",
}
M_CAP = 24


def _mean_hist(bench: Bench, collection: str, arm: str, cap: int) -> np.ndarray | None:
    """Seed-averaged normalised m histogram of the usable samples, tail folded into ``cap``."""
    rows = bench.rows(collection, arm)
    rows = rows[rows.fidelity_ok == 1]
    if len(rows) < gb.MIN_VALID_SEEDS:
        return None
    hists = []
    for seed in rows.seed:
        m = np.minimum(bench.arrays(collection, arm, int(seed)).m, cap)
        hists.append(np.bincount(m, minlength=cap + 1)[: cap + 1] / len(m))
    return np.mean(hists, axis=0)


def draw(bench: Bench, arms: list[str], out: Path) -> None:
    """Render the figure to ``out`` (PDF)."""
    collections = bench.collections
    fig, axes = plt.subplots(
        len(collections), 3, figsize=(13.2, 3.9 * len(collections)), squeeze=False
    )
    for r, collection in enumerate(collections):
        ref, _ = bench.reference(collection)
        ax = axes[r][0]
        ref_hist = np.bincount(np.minimum(ref.m, M_CAP), minlength=M_CAP + 1)[: M_CAP + 1] / len(
            ref
        )
        x = np.arange(M_CAP + 1)
        ax.step(x, ref_hist, where="mid", color="black", lw=2.2, label="collection")
        undrawn = []
        for arm in arms:
            hist = _mean_hist(bench, collection, arm, M_CAP)
            if hist is None:
                undrawn.append(arm)
                continue
            ax.step(
                x,
                hist,
                where="mid",
                color=COLORS.get(arm, "gray"),
                lw=1.6,
                label=LABELS.get(arm, arm),
            )
        for arm in undrawn:
            med = int(bench.rows(collection, arm).n_usable.median())
            ax.plot(
                [],
                [],
                color=COLORS.get(arm, "gray"),
                ls=":",
                label=f"{LABELS.get(arm, arm)} (u={med}, not drawn)",
            )
        ax.set_xlim(0.5, M_CAP + 0.5)
        ax.set_xlabel(f"facts per knowledge base m (≥{M_CAP} folded)")
        ax.set_ylabel("fraction of usable samples")
        ax.set_title(f"{collection}: m of usable samples")
        ax.legend(fontsize=7.5, frameon=False)

        ax = axes[r][1]
        info = bench.coll_info[collection]
        ticks, names = [], []
        for pos, arm in enumerate(arms):
            rows = bench.rows(collection, arm)
            ok = rows[rows.fidelity_ok == 1]
            ticks.append(pos)
            names.append(LABELS.get(arm, arm).replace(" (ours)", "\n(ours)").replace(" + ", "\n+ "))
            if len(ok) >= gb.MIN_VALID_SEEDS:
                c = ci(ok.star_frac_use)
                ax.bar(
                    pos,
                    c["mean"],
                    color=COLORS.get(arm, "gray"),
                    width=0.7,
                    yerr=[[c["mean"] - c["low"]], [c["high"] - c["mean"]]],
                    ecolor="black",
                    capsize=3,
                )
            else:
                ax.text(pos, 0.5, "u < 100\n(not drawn)", ha="center", va="center", fontsize=7.5)
        ax.axhline(info["coll_star_frac"], color="black", lw=1.6, ls="--", label="collection")
        ax.set_xticks(ticks, names, fontsize=7.5)
        ax.set_ylabel("star fraction of usable samples")
        ax.set_ylim(0, 1)
        ax.set_title(f"{collection}: star fraction (95% BCa CI)")
        ax.legend(fontsize=8, frameon=False)

        ax = axes[r][2]
        width = 0.38
        for i, arm in enumerate(arms):
            rows = bench.rows(collection, arm)
            usable = ci(rows.n_usable / rows.n_draws * 1e4)
            vun = ci(rows.n_unique_novel_usable / rows.n_draws * 1e4)
            for off, cell, hatch in ((-width / 2, usable, None), (width / 2, vun, "//")):
                h = max(cell["mean"], 1e-2)
                lo, hi = max(cell["low"], 1e-2), max(cell["high"], 1e-2)
                ax.bar(
                    i + off,
                    h,
                    width=width,
                    color=COLORS.get(arm, "gray"),
                    hatch=hatch,
                    yerr=[[max(h - lo, 0)], [max(hi - h, 0)]],
                    ecolor="black",
                    capsize=2,
                )
                if cell["mean"] == 0:
                    ax.text(i + off, 1.5e-2, "0", ha="center", fontsize=8)
        ax.set_yscale("log")
        ax.set_ylim(1e-2, 2e4)
        ax.set_xticks(
            range(len(arms)),
            [LABELS.get(a, a).replace(" (ours)", "\n(ours)").replace(" + ", "\n+ ") for a in arms],
            fontsize=7.5,
        )
        ax.set_ylabel("per 10,000 draws")
        ax.set_title(f"{collection}: usable (solid) and valid-unique-novel (hatched)")
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    """Command-line entry point."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--eval", required=True)
    p.add_argument("--out", required=True, help="output PDF path")
    p.add_argument("--arms", default=",".join([gb.ARM_OURS, *gb.BASELINES]))
    p.add_argument("--collection", action="append")
    args = p.parse_args()
    arms = args.arms.split(",")
    bench = Bench(Path(args.eval), args.collection or list(gb.COLLECTIONS), arms)
    draw(bench, arms, Path(args.out))
    print(f"[fig] wrote {args.out}")


if __name__ == "__main__":
    main()
