"""Draft of the Design-D figure (LOG.md §7): linkage of partial exports against a catalogue.

(a) Fixed rule, decided before looking: WD50K(66), pendant copies, seed 0,
r = 1, the first 12 sources of seed 0 (the job's acceptance order). Each panel
embeds, under one representation, every source's catalogue record (large
marker), its 3 copies (small marker, same colour), up to 5 of its C8 one-edit
look-alikes in the catalogue (grey; a uniform sample under a fixed seed when it
has more) and any further catalogue record that is some copy's 1-NN (grey ring).
t-SNE on the precomputed distances, the same perplexity and seed in every
panel. A thin line joins each copy to its 1-NN in the *whole* catalogue: green
when it is the source, red otherwise, dashed when the source shares the nearest
tie block with other records. Titles give the panel's 1-NN accuracy on these 36
copies against the whole catalogue. (b) 1-NN accuracy vs r per collection and
condition (probe seeds: mean and [min, max]); the word and the four strongest
competitors coloured, the rest grey.
"""

from __future__ import annotations

import argparse
import json
import sys
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
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import design_c as DC  # noqa: E402, N812
import design_d as DD  # noqa: E402, N812
import knn_lib as K  # noqa: E402, N812
import rect as R  # noqa: E402, N812

from experiments.tkde import corpora as C  # noqa: E402, N812

HUES = ("#2a78d6", "#eb6834", "#1baf7a")
SHAPES = ("o", "s", "^", "D")
LINE_SLOTS = ("#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4")
GREY, GOOD, BAD = "#a3a29c", "#0ca30c", "#d03b3b"
INK, INK2, SURFACE = "#0b0b0b", "#52514e", "#fcfcfb"
# The edit path is drawn in its verdict reading, the symmetric min (LOG.md §7.1).
PANEL_ARMS = (K.OURS, "nauty_cert_rows", "bipartite_ged_path_sym", K.WL_H1)
LABELS = {
    "isal_ow_struct": r"Isal word $w^{\circ}$ (ours)",
    "nauty_cert_rows": "nauty certificate, rows",
    "nauty_cert": "nauty certificate, bytes",
    "bipartite_ged_path": "bipartite GED, edit path (as run)",
    "bipartite_ged_path_sym": "bipartite GED, edit path (sym-min)",
    "bipartite_ged_assign": "bipartite GED, assignment",
    "wl_h1": "WL, one round",
    "wl_l1": "WL, registry (degenerate)",
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


def _style(ax: Axes) -> None:
    ax.set_xticks([])
    ax.set_yticks([])
    for side in ax.spines.values():
        side.set_color("#d6d5cf")
        side.set_linewidth(0.6)


def _setup(args: argparse.Namespace) -> dict[str, Any]:
    """Sources, copies, look-alikes and the catalogue for the panel-(a) rule."""
    job = json.loads((args.probe / f"D_{args.collection}_pendant.json").read_text())
    seed_res = job["seeds"][str(args.seed)]
    col = C.load_collection(args.collection)
    keys = K.IsoKeys(col.n_types, col.n_preds)
    cat, _ = DD.build_catalogue(col, keys)
    draw = K.select_sources(
        cat,
        job["config"]["S"],
        DD.RS,
        DD.C_COPIES,
        np.random.default_rng(seed_res["source_seed"]),
        keys,
    )
    if [s.kb_id for s in draw.sources] != seed_res["source_ids"]:
        raise SystemExit("the regenerated sources differ from the job's: refusing to draw")
    shown = draw.sources[: args.n_sources]
    copies = [draw.copies[args.r][i] for i in range(args.n_sources)]
    graph = DC.one_edit_graph(col)
    cls_of = {graph.rep[c]: c for c in graph.rep}
    member_index = col.index()
    cat_index = cat.index()
    rep_kb = {cls: col.records[i].kb_id for cls, i in graph.rep.items()}
    lookalikes: list[list[str]] = []
    for s in shown:
        cls = cls_of.get(member_index[s.kb_id])
        nbrs = sorted(rep_kb[u] for u in graph.adj.get(cls, {})) if cls is not None else []
        nbrs = [kb for kb in nbrs if kb in cat_index]
        if len(nbrs) > args.lookalikes:
            rng = np.random.default_rng(K.cell_seed(args.seed, "fig-d", s.kb_id))
            nbrs = [nbrs[int(i)] for i in sorted(rng.choice(len(nbrs), args.lookalikes, False))]
        lookalikes.append(nbrs)
    return {"col": col, "cat": cat, "shown": shown, "copies": copies, "lookalikes": lookalikes}


def draw_panels(fig: Figure | SubFigure, ctx: dict[str, Any], args: argparse.Namespace) -> dict:
    """Row (a): one embedding per representation with the 1-NN lines."""
    from sklearn.manifold import TSNE

    col, cat = ctx["col"], ctx["cat"]
    cat_recs = list(cat.records)
    cat_index = cat.index()
    cat_hs = K.hypergraphs(cat_recs, col.n_types, col.n_preds)
    queries = [cp for cs in ctx["copies"] for cp in cs]
    q_src = np.array([cat_index[cp.label] for cp in queries])
    q_hs = K.hypergraphs(queries, col.n_types, col.n_preds)
    axes = fig.subplots(1, len(PANEL_ARMS))
    numbers: dict[str, Any] = {"sources": [s.kb_id for s in ctx["shown"]], "arms": {}}
    for ax, arm in zip(axes, PANEL_ARMS, strict=True):
        D = R.make_arm(arm, args.n_jobs).fit(cat_hs).rect(q_hs)
        p1, _ = DD.score_rect(D, q_src)
        targets = []
        for i in range(len(queries)):
            nn = np.flatnonzero(D[i] == D[i].min())
            src_in = q_src[i] in nn
            targets.append((int(q_src[i]) if src_in else int(nn[0]), src_in, len(nn) > 1))
        # The panel's point set: sources, copies, look-alikes, then any other 1-NN record.
        cat_pts = [cat_index[s.kb_id] for s in ctx["shown"]]
        for nbrs in ctx["lookalikes"]:
            cat_pts += [cat_index[kb] for kb in nbrs if cat_index[kb] not in cat_pts]
        n_look = len(cat_pts)
        cat_pts += sorted({t for t, _, _ in targets if t not in cat_pts})
        recs = [cat_recs[i] for i in cat_pts] + queries
        if arm.endswith(R.SYM_SUFFIX):
            pts = K.hypergraphs(recs, col.n_types, col.n_preds)
            Dp = R.make_arm(arm, args.n_jobs).fit(pts).rect(pts)
            np.fill_diagonal(Dp, 0.0)
        else:
            Dp = K.build_matrices(
                recs, [arm], n_types=col.n_types, n_preds=col.n_preds, n_jobs=args.n_jobs
            )[0][arm]
        emb = TSNE(
            n_components=2,
            metric="precomputed",
            init="random",
            perplexity=args.perplexity,
            random_state=args.tsne_seed,
        ).fit_transform(Dp)
        pos = {ci: emb[k] for k, ci in enumerate(cat_pts)}
        qpos = emb[len(cat_pts) :]
        n_src = len(ctx["shown"])
        for k in range(n_src, len(cat_pts)):
            ring = k >= n_look
            ax.scatter(
                *emb[k],
                s=14,
                facecolor="none" if ring else GREY,
                edgecolor=GREY,
                linewidth=0.6,
                zorder=1,
            )
        for i, (t, ok, tie) in enumerate(targets):
            ax.plot(
                [qpos[i, 0], pos[t][0]],
                [qpos[i, 1], pos[t][1]],
                color=GOOD if ok else BAD,
                lw=0.6,
                ls="--" if tie else "-",
                alpha=0.8,
                zorder=2,
            )
        for j in range(n_src):
            hue, mk = HUES[j % 3], SHAPES[j // 3]
            ax.scatter(
                *emb[j], s=46, marker=mk, facecolor=hue, edgecolor=INK, linewidth=0.7, zorder=4
            )
            qs = qpos[j * DD.C_COPIES : (j + 1) * DD.C_COPIES]
            ax.scatter(
                qs[:, 0],
                qs[:, 1],
                s=16,
                marker=mk,
                facecolor=hue,
                edgecolor=SURFACE,
                linewidth=0.5,
                zorder=3,
            )
        acc = float(p1.mean())
        ax.set_title(
            f"{LABELS[arm]}\n1-NN {acc:.2f} on these {len(queries)} copies",
            fontsize=7,
            color=INK,
            pad=3,
        )
        _style(ax)
        numbers["arms"][arm] = {"acc1": acc, "n_points": len(recs)}
    handles = [
        Line2D(
            [],
            [],
            ls="",
            marker="o",
            markerfacecolor=HUES[0],
            markeredgecolor=INK,
            markersize=6,
            label="catalogue record of a source",
        ),
        Line2D(
            [],
            [],
            ls="",
            marker="o",
            markerfacecolor=HUES[0],
            markeredgecolor=SURFACE,
            markersize=4,
            label=f"its {DD.C_COPIES} partial copies (r = {args.r})",
        ),
        Line2D(
            [],
            [],
            ls="",
            marker="o",
            markerfacecolor=GREY,
            markeredgecolor=GREY,
            markersize=4,
            label="one-edit look-alikes in the catalogue",
        ),
        Line2D(
            [],
            [],
            ls="",
            marker="o",
            markerfacecolor="none",
            markeredgecolor=GREY,
            markersize=4,
            label="other catalogue record hit as 1-NN",
        ),
        Line2D([], [], color=GOOD, lw=0.9, label="1-NN = source"),
        Line2D([], [], color=BAD, lw=0.9, label="1-NN = another record"),
        Line2D([], [], color=GOOD, lw=0.9, ls="--", label="source tied with others"),
    ]
    fig.legend(
        handles=handles,
        loc="lower center",
        ncol=4,
        fontsize=5.5,
        frameon=False,
        labelcolor=INK2,
        handletextpad=0.3,
        columnspacing=1.0,
    )
    fig.suptitle(
        f"(a) {COLLECTION_LABELS[args.collection]}: 12 sources (first 12 of seed 0), their copies "
        "and catalogue look-alikes; t-SNE per representation; line = copy to its 1-NN",
        fontsize=7.5,
        x=0.01,
        y=0.995,
        ha="left",
        color=INK,
    )
    return numbers


def draw_curves(fig: Figure | SubFigure, summary: dict[str, Any]) -> None:
    """Row (b): 1-NN vs r per (condition, collection)."""
    rows = [x for x in summary["rows"]]
    panels = [
        (x["mix"], x["collection"])
        for x in sorted(
            rows, key=lambda x: (x["mix"] != "pendant", K.COLLECTIONS.index(x["collection"]))
        )
    ]
    by = {(x["mix"], x["collection"]): x for x in rows}
    totals: dict[str, float] = {}
    for x in rows:
        if x["mix"] != "pendant":
            continue
        for cell in x["cells"].values():
            for a in DD.COMPETITORS_D:
                totals[a] = totals.get(a, 0.0) + cell["per_arm"][a]["acc1"]["mean"]
    strongest = sorted(totals, key=lambda a: -totals[a])[:4]
    highlight = [K.OURS, *strongest]
    colour = {a: LINE_SLOTS[i] for i, a in enumerate(highlight)}
    axes = fig.subplots(1, len(panels), sharey=True)
    for ax, key in zip(np.atleast_1d(axes), panels, strict=True):
        x = by[key]
        rs = sorted(x["cells"], key=int)
        # The verdict arms only: the as-run edit-path orientation is not drawn.
        for arm in sorted((K.OURS, *DD.COMPETITORS_D), key=lambda a: a in highlight):
            ys = [x["cells"][r]["per_arm"][arm]["acc1"]["mean"] for r in rs]
            lo = [x["cells"][r]["per_arm"][arm]["acc1"]["min"] for r in rs]
            hi = [x["cells"][r]["per_arm"][arm]["acc1"]["max"] for r in rs]
            xs = [int(r) for r in rs]
            if arm in highlight:
                ax.fill_between(xs, lo, hi, color=colour[arm], alpha=0.15, lw=0)
                ax.plot(
                    xs,
                    ys,
                    color=colour[arm],
                    lw=1.8 if arm == K.OURS else 1.1,
                    marker="o",
                    ms=2.6,
                    zorder=3,
                )
            else:
                ax.plot(xs, ys, color=GREY, lw=0.6, zorder=1)
        ax.axvspan(2.5, 3.5, color="#f0efec", zorder=0)
        ax.set_title(f"{COLLECTION_LABELS[key[1]]}\n{key[0]}", fontsize=6.3, color=INK, pad=2)
        ax.set_xticks([1, 2, 3])
        ax.set_xlim(0.8, 3.2)
        ax.set_xlabel("r", fontsize=6, color=INK2)
        ax.tick_params(labelsize=5.5, colors=INK2)
        ax.grid(axis="y", color="#ebeae5", lw=0.5)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    np.atleast_1d(axes)[0].set_ylabel("1-NN accuracy", fontsize=6.5, color=INK2)
    handles = [
        Line2D(
            [],
            [],
            color=colour[a],
            lw=1.8 if a == K.OURS else 1.1,
            marker="o",
            ms=2.6,
            label=LABELS[a],
        )
        for a in highlight
    ] + [Line2D([], [], color=GREY, lw=0.6, label="other competitors")]
    fig.legend(
        handles=handles,
        loc="lower center",
        ncol=len(handles),
        fontsize=5.5,
        frameon=False,
        labelcolor=INK2,
    )
    fig.suptitle(
        "(b) 1-NN accuracy against the catalogue vs r (probe: mean over seeds, band = [min, max]; "
        "r = 3, shaded, carries no claim)",
        fontsize=7.5,
        x=0.01,
        ha="left",
        color=INK,
    )


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--probe", type=Path, default=K.OUT_ROOT / "probe_d")
    ap.add_argument("--collection", default="wd50k66")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--r", type=int, default=1)
    ap.add_argument("--n-sources", type=int, default=12)
    ap.add_argument("--lookalikes", type=int, default=5)
    ap.add_argument("--perplexity", type=float, default=15.0)
    ap.add_argument("--tsne-seed", type=int, default=0)
    ap.add_argument("--n-jobs", type=int, default=8)
    args = ap.parse_args()
    plt.rcParams.update({"font.family": "DejaVu Sans", "figure.facecolor": SURFACE})
    fig = plt.figure(figsize=(7.16, 5.4))
    top, bottom = fig.subfigures(2, 1, height_ratios=[1.35, 1.0], hspace=0.03)
    numbers = draw_panels(top, _setup(args), args)
    summary_path = args.probe / "summary_d.json"
    if summary_path.exists():
        draw_curves(bottom, json.loads(summary_path.read_text()))
    top.subplots_adjust(left=0.01, right=0.99, top=0.8, bottom=0.2, wspace=0.05)
    bottom.subplots_adjust(left=0.07, right=0.99, top=0.76, bottom=0.3, wspace=0.08)
    stem = args.probe / f"fig_knn_d_{args.collection}_r{args.r}_s{args.seed}"
    fig.savefig(stem.with_suffix(".png"), dpi=300, facecolor=SURFACE)
    fig.savefig(stem.with_suffix(".pdf"), facecolor=SURFACE)
    numbers.update({k: (str(v) if isinstance(v, Path) else v) for k, v in vars(args).items()})
    K.write_json(stem.with_suffix(".json"), numbers)
    print(f"wrote {stem}.{{png,pdf,json}}")
    for arm, v in numbers["arms"].items():
        print(f"  {arm:20s} 1-NN {v['acc1']:.3f} ({v['n_points']} points)")


if __name__ == "__main__":
    main()
