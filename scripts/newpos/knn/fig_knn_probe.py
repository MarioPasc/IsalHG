"""Draft of the PI's KNN figure from one Design-B probe replicate on WD50K(66).

(a) t-SNE embeddings (precomputed distances, the same perplexity and seed in
every panel) of the partial copies of 12 sources under the word ``w°`` and three
competitors, coloured by source; each title gives the panel's 1-NN accuracy
(ties at expectation) and k-medoids ARI on the copies shown. (b) 1-NN accuracy
against the number of removed statements ``r``, one small multiple per
collection, mean over the probe seeds with the [min, max] range; the word, the
three panel-(a) competitors and the best competitor are coloured, every other
competitor is a thin grey line.

Reads the items the probe wrote (``<probe>/items/B_wd50k66_r<r>_s<seed>.jsonl``)
and ``<probe>/summary.json``; writes ``fig_knn_probe_r<r>_s<seed>.{png,pdf,json}``.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure, SubFigure  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import knn_lib as K  # noqa: E402, N812

from experiments.tkde import corpora as C  # noqa: E402, N812
from isalhg.datasets.kb.base import KBRecord  # noqa: E402

# Validated categorical slots (dataviz reference palette, light mode). Twelve
# sources on a scatter exceed what hue alone can separate (only slots 1-3 pass
# the all-pairs gates), so a source is a (hue, marker) pair: 3 hues x 4 shapes.
HUES = ("#2a78d6", "#eb6834", "#1baf7a")
SHAPES = ("o", "s", "^", "D")
LINE_SLOTS = ("#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4")
GREY = "#a3a29c"
INK, INK2, SURFACE = "#0b0b0b", "#52514e", "#fcfcfb"

LABELS = {
    "isal_ow_struct": r"Isal word $w^{\circ}$ (ours)",
    "nauty_cert_rows": "nauty certificate, rows",
    "nauty_cert": "nauty certificate, bytes",
    "fact_rank": "fact list (canonical rank)",
    "wl_l1": "WL histogram",
    "netlsd": "NetLSD",
    "hpd_jsd": "HPD",
    "bipartite_ged_path": "bipartite GED, edit path",
    "bipartite_ged_assign": "bipartite GED, assignment",
    "degree_seq_l1": "degree-sequence floor",
    "size_l1": "size floor",
}
COLLECTION_LABELS = {
    "wd50k66": "WD50K(66)",
    "wd50k100": "WD50K(100)",
    "ndc_classes": "NDC-classes",
    "ndc_substances": "NDC-substances",
}


def _read_items(path: Path) -> list[KBRecord]:
    return [KBRecord.from_json(json.loads(line)) for line in path.read_text().splitlines() if line]


def _panel_scores(D: np.ndarray, codes: np.ndarray, seed: int) -> tuple[float, float]:
    from sklearn.metrics import adjusted_rand_score

    P = K.loo_knn_probs(D, codes, 1)
    cl = K.pam(D, int(codes.max()) + 1, seed)
    return K.expected_accuracy(P, codes), float(adjusted_rand_score(codes, cl["labels"]))


def _style(ax: Axes) -> None:
    ax.set_xticks([])
    ax.set_yticks([])
    for side in ax.spines.values():
        side.set_color("#d6d5cf")
        side.set_linewidth(0.6)


def draw_embeddings(
    fig: Figure | SubFigure, items: list[KBRecord], arms: list[str], args: argparse.Namespace
) -> dict[str, Any]:
    """Row (a): one t-SNE panel per arm; returns the numbers printed in the titles."""
    from sklearn.manifold import TSNE

    col = C.load_collection("wd50k66")
    by_src: dict[str, list[KBRecord]] = defaultdict(list)
    for it in items:
        by_src[str(it.label)].append(it)
    sources = sorted(by_src)
    rng = np.random.default_rng(K.cell_seed(args.seed, "fig", args.r))
    shown = [
        sources[int(i)] for i in sorted(rng.choice(len(sources), args.n_sources, replace=False))
    ]
    recs = [cp for s in shown for cp in by_src[s]]
    codes = np.array([shown.index(str(cp.label)) for cp in recs])
    mats, _ = K.build_matrices(recs, arms, n_types=col.n_types, n_preds=col.n_preds, n_jobs=4)
    src_rec = C.records_by_id(col)
    axes = fig.subplots(1, len(arms))
    numbers: dict[str, Any] = {"sources": shown, "arms": {}}
    pam_seed = K.cell_seed(args.seed, "fig", args.r, "pam")
    for ax, arm in zip(axes, arms, strict=True):
        D = mats[arm]
        acc, ari = _panel_scores(D, codes, pam_seed)
        emb = TSNE(
            n_components=2,
            metric="precomputed",
            init="random",
            perplexity=args.perplexity,
            random_state=args.tsne_seed,
        ).fit_transform(D)
        for j in range(len(shown)):
            pts = emb[codes == j]
            hue = HUES[j % len(HUES)]
            cx, cy = pts.mean(axis=0)
            for x, y in pts:
                ax.plot([cx, x], [cy, y], color=hue, lw=0.5, alpha=0.45, zorder=1)
            ax.scatter(
                pts[:, 0],
                pts[:, 1],
                s=22,
                marker=SHAPES[j // len(HUES)],
                facecolor=hue,
                edgecolor=SURFACE,
                linewidth=0.6,
                zorder=2,
            )
        ax.set_title(f"{LABELS[arm]}\n1-NN {acc:.2f} · ARI {ari:.2f}", fontsize=7, color=INK, pad=3)
        _style(ax)
        numbers["arms"][arm] = {"acc1": acc, "ari": ari}
    handles = []
    for j, s in enumerate(shown):
        rec = src_rec[s]
        handles.append(
            Line2D(
                [],
                [],
                ls="",
                marker=SHAPES[j // len(HUES)],
                markerfacecolor=HUES[j % len(HUES)],
                markeredgecolor=SURFACE,
                markersize=5,
                label=f"{s} (n={rec.n}, m={rec.m})",
            )
        )
    fig.legend(
        handles=handles,
        loc="lower center",
        ncol=6,
        fontsize=5.5,
        frameon=False,
        handletextpad=0.2,
        columnspacing=0.8,
        title=f"source (each with {args.c} partial copies, r = {args.r} pendant removals)",
        title_fontsize=6,
        labelcolor=INK2,
    )
    fig.suptitle(
        "(a) partial copies of 12 WD50K(66) sources, t-SNE of each representation's distances",
        fontsize=7.5,
        x=0.01,
        ha="left",
        color=INK,
    )
    return numbers


def draw_curves(fig: Figure | SubFigure, summary: dict[str, Any], panel_arms: list[str]) -> None:
    """Row (b): 1-NN accuracy vs r per collection (probe seeds: mean and range)."""
    rows = [r for r in summary["rows"] if r["design"] == "B" and r["condition"] == "pendant"]
    by_col: dict[str, dict[int, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        by_col[row["collection"]][int(row["r"])] = row["per_arm"]
    cols = [c for c in K.COLLECTIONS if c in by_col]
    if not cols:
        return
    mean_acc: dict[str, float] = defaultdict(float)
    for c in cols:
        for per in by_col[c].values():
            for arm, v in per.items():
                if arm in K.COMPETITORS:
                    mean_acc[arm] += v["acc1"]["mean"]
    best = max(mean_acc, key=lambda a: mean_acc[a])
    highlight = [K.OURS, *[a for a in panel_arms if a != K.OURS]]
    if best not in highlight:
        highlight.append(best)
    colour = {a: LINE_SLOTS[i] for i, a in enumerate(highlight)}
    axes = fig.subplots(1, len(cols), sharey=True)
    for ax, c in zip(np.atleast_1d(axes), cols, strict=True):
        rs = sorted(by_col[c])
        arms = list(by_col[c][rs[0]])
        for arm in sorted(arms, key=lambda a: a in highlight):
            if arm == K.ABLATION:
                continue
            ys = np.array([by_col[c][r][arm]["acc1"]["mean"] for r in rs])
            lo = np.array([by_col[c][r][arm]["acc1"]["min"] for r in rs])
            hi = np.array([by_col[c][r][arm]["acc1"]["max"] for r in rs])
            if arm in highlight:
                ax.fill_between(rs, lo, hi, color=colour[arm], alpha=0.15, lw=0)
                ax.plot(
                    rs,
                    ys,
                    color=colour[arm],
                    lw=2 if arm == K.OURS else 1.4,
                    marker="o",
                    ms=3.5,
                    zorder=3,
                    label=LABELS[arm],
                )
            else:
                ax.plot(rs, ys, color=GREY, lw=0.7, zorder=1)
        ax.set_title(COLLECTION_LABELS[c], fontsize=7, color=INK, pad=3)
        ax.set_xticks(rs)
        ax.set_xlabel("removed statements r", fontsize=6.5, color=INK2)
        ax.tick_params(labelsize=6, colors=INK2)
        ax.grid(axis="y", color="#ebeae5", lw=0.6)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    np.atleast_1d(axes)[0].set_ylabel("1-NN accuracy", fontsize=6.5, color=INK2)
    handles = [
        Line2D(
            [],
            [],
            color=colour[a],
            lw=2 if a == K.OURS else 1.4,
            marker="o",
            ms=3.5,
            label=LABELS[a],
        )
        for a in highlight
    ] + [Line2D([], [], color=GREY, lw=0.7, label="other competitors")]
    fig.legend(
        handles=handles,
        loc="lower center",
        ncol=len(handles),
        fontsize=5.5,
        frameon=False,
        labelcolor=INK2,
    )
    fig.suptitle(
        "(b) 1-NN accuracy vs r (probe: mean over seeds, band = [min, max]; descriptive)",
        fontsize=7.5,
        x=0.01,
        ha="left",
        color=INK,
    )


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--probe", type=Path, default=K.OUT_ROOT / "probe")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--r", type=int, default=2)
    ap.add_argument("--c", type=int, default=6)
    ap.add_argument("--n-sources", type=int, default=12)
    ap.add_argument("--perplexity", type=float, default=8.0)
    ap.add_argument("--tsne-seed", type=int, default=0)
    # The registry WL runs to the stable partition of the union of the items; on a set
    # of near-identical copies that partition separates every copy, so its distance
    # collapses to n_i + n_j. NetLSD is therefore the default fourth panel.
    ap.add_argument("--third", default="fact_rank", choices=["fact_rank", "bipartite_ged_path"])
    ap.add_argument("--fourth", default="netlsd", choices=["wl_l1", "netlsd"])
    args = ap.parse_args()
    plt.rcParams.update({"font.family": "DejaVu Sans", "figure.facecolor": SURFACE})
    items = _read_items(args.probe / "items" / f"B_wd50k66_r{args.r}_s{args.seed}.jsonl")
    panel_arms = [K.OURS, "nauty_cert_rows", args.third, args.fourth]
    fig = plt.figure(figsize=(7.16, 5.0))
    top, bottom = fig.subfigures(2, 1, height_ratios=[1.3, 1.0], hspace=0.04)
    top.subplots_adjust(left=0.01, right=0.99, top=0.83, bottom=0.2, wspace=0.06)
    bottom.subplots_adjust(left=0.07, right=0.99, top=0.84, bottom=0.3, wspace=0.08)
    numbers = draw_embeddings(top, items, panel_arms, args)
    summary_path = args.probe / "summary.json"
    if summary_path.exists():
        draw_curves(bottom, json.loads(summary_path.read_text()), panel_arms)
    variant = "" if args.third == "fact_rank" else "_editpath"
    stem = args.probe / f"fig_knn_probe_r{args.r}_s{args.seed}{variant}"
    fig.savefig(stem.with_suffix(".png"), dpi=300, facecolor=SURFACE)
    fig.savefig(stem.with_suffix(".pdf"), facecolor=SURFACE)
    numbers.update({k: (str(v) if isinstance(v, Path) else v) for k, v in vars(args).items()})
    K.write_json(stem.with_suffix(".json"), numbers)
    print(f"wrote {stem}.{{png,pdf,json}}")
    for arm, v in numbers["arms"].items():
        print(f"  {arm:18s} 1-NN {v['acc1']:.3f}  ARI {v['ari']:.3f}")


if __name__ == "__main__":
    main()
