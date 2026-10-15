"""Draft of the Design-C figure (LOG.md §6, §6.1).

(a) Inside one C-int block: t-SNE (precomputed distances; the same perplexity
and seed in every panel) of the copies of its 3–5 look-alike members, coloured
by member, under the word, the certificate rows, the bipartite edit path and
the one-round WL. The block is the largest C-int block of seed 0 at c = 3 on
WD50K(100) or NDC-substances (the C-int-feasible collections). Each title gives
1-NN accuracy (ties at expectation) and k-medoids ARI (k = block size) on the
copies shown. (b) 1-NN accuracy vs r, one small multiple per (stratum,
collection), mean over the probe seeds with the [min, max] band; infeasible
cells are marked.

Reads the job JSONs and ``summary_c.json`` of the probe directory; writes
``fig_knn_c_r<r>.{png,pdf,json}`` there.
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
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import design_c as DC  # noqa: E402, N812
import knn_lib as K  # noqa: E402, N812

from experiments.tkde import corpora as C  # noqa: E402, N812

HUES = ("#2a78d6", "#eb6834", "#1baf7a")
SHAPES = ("o", "s")
LINE_SLOTS = ("#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4")
GREY = "#a3a29c"
INK, INK2, SURFACE = "#0b0b0b", "#52514e", "#fcfcfb"
PANEL_ARMS = (K.OURS, "nauty_cert_rows", "bipartite_ged_path", K.WL_H1)
LABELS = {
    "isal_ow_struct": r"Isal word $w^{\circ}$ (ours)",
    "nauty_cert_rows": "nauty certificate, rows",
    "bipartite_ged_path": "bipartite GED, edit path",
    "bipartite_ged_assign": "bipartite GED, assignment",
    "wl_h1": "WL, one round",
    "degree_seq_l1": "degree-sequence floor",
    "fact_rank": "fact list",
    "nauty_cert": "nauty certificate, bytes",
    "netlsd": "NetLSD",
    "hpd_jsd": "HPD",
    "size_l1": "size floor",
    "wl_l1": "WL, registry (degenerate)",
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


def pick_block(probe: Path, c: int, seed: int) -> tuple[str, dict[str, Any]]:
    """The largest C-int block of ``seed`` on WD50K(100) or NDC-substances (first wins ties)."""
    best: tuple[int, str, dict[str, Any]] | None = None
    for collection in ("wd50k100", "ndc_substances"):
        path = probe / f"C_{collection}_C-int_c{c}.json"
        if not path.exists():
            continue
        blocks = json.loads(path.read_text())["seeds"][str(seed)]["blocks"]
        for block in blocks:
            if best is None or len(block["classes"]) > best[0]:
                best = (len(block["classes"]), collection, block)
    if best is None:
        raise SystemExit("no C-int job JSON found")
    return best[1], best[2]


def draw_block(
    fig: Figure | SubFigure, collection: str, block: dict[str, Any], args: argparse.Namespace
) -> dict[str, Any]:
    """Row (a): the copies of one block under four representations."""
    from sklearn.manifold import TSNE
    from sklearn.metrics import adjusted_rand_score

    col = C.load_collection(collection)
    keys = K.IsoKeys(col.n_types, col.n_preds)
    by_id = C.records_by_id(col)
    recs, codes = [], []
    for j, (cls, kb_id) in enumerate(zip(block["classes"], block["kb_ids"], strict=True)):
        got = DC.member_copies(by_id[kb_id], cls, args.seed, keys, collection, args.c)
        if got is None:
            raise SystemExit(f"copies of {kb_id} fall short; the pool could not have held it")
        recs += got[args.r]
        codes += [j] * args.c
    code_arr = np.array(codes)
    mats, _ = K.build_matrices(recs, PANEL_ARMS, n_types=col.n_types, n_preds=col.n_preds)
    axes = fig.subplots(1, len(PANEL_ARMS))
    numbers: dict[str, Any] = {"collection": collection, "block": block, "arms": {}}
    pam_seed = K.cell_seed(args.seed, "fig-c", args.r, "pam")
    for ax, arm in zip(axes, PANEL_ARMS, strict=True):
        D = mats[arm]
        acc = K.expected_accuracy(K.loo_knn_probs(D, code_arr, 1), code_arr)
        ari = float(
            adjusted_rand_score(code_arr, K.pam(D, len(block["classes"]), pam_seed)["labels"])
        )
        emb = TSNE(
            n_components=2,
            metric="precomputed",
            init="random",
            perplexity=args.perplexity,
            random_state=args.tsne_seed,
        ).fit_transform(D)
        for j in range(len(block["classes"])):
            pts = emb[code_arr == j]
            hue = HUES[j % len(HUES)]
            cx, cy = pts.mean(axis=0)
            for x, y in pts:
                ax.plot([cx, x], [cy, y], color=hue, lw=0.6, alpha=0.5, zorder=1)
            ax.scatter(
                pts[:, 0],
                pts[:, 1],
                s=30,
                marker=SHAPES[j // len(HUES)],
                facecolor=hue,
                edgecolor=SURFACE,
                linewidth=0.7,
                zorder=2,
            )
        ax.set_title(f"{LABELS[arm]}\n1-NN {acc:.2f} · ARI {ari:.2f}", fontsize=7, color=INK, pad=3)
        _style(ax)
        numbers["arms"][arm] = {"acc1": acc, "ari": ari}
    handles = []
    for j, kb_id in enumerate(block["kb_ids"]):
        role = "block seed" if j == 0 else f"{block['kinds_to_seed'][j - 1]} edit from seed"
        handles.append(
            Line2D(
                [],
                [],
                ls="",
                marker=SHAPES[j // len(HUES)],
                markerfacecolor=HUES[j % len(HUES)],
                markeredgecolor=SURFACE,
                markersize=5.5,
                label=f"{kb_id} (n={block['n'][j]}, m={block['m'][j]}; {role})",
            )
        )
    fig.legend(
        handles=handles,
        loc="lower center",
        ncol=3,
        fontsize=5.5,
        frameon=False,
        handletextpad=0.2,
        columnspacing=0.9,
        labelcolor=INK2,
        title=f"block member ({args.c} partial copies each, r = {args.r} pendant removals)",
        title_fontsize=6,
    )
    fig.suptitle(
        f"(a) one C-int block, {COLLECTION_LABELS[collection]}: look-alike records one interior "
        "edit apart (t-SNE; 1-NN, ARI on these copies)",
        fontsize=7.5,
        x=0.01,
        y=0.995,
        ha="left",
        color=INK,
    )
    return numbers


def draw_curves(fig: Figure | SubFigure, summary: dict[str, Any], c: int) -> None:
    """Row (b): 1-NN vs r per (stratum, collection)."""
    entries = {(e["stratum"], e["collection"]): e for e in summary["by_c"][str(c)]}
    strata = [s for s in DC.STRATA if any(k[0] == s for k in entries)]
    cols = [x for x in K.COLLECTIONS if any(k[1] == x for k in entries)]
    axes = np.atleast_2d(fig.subplots(len(strata), len(cols), sharex=True, sharey=True))
    highlight = list(PANEL_ARMS)
    colour = {a: LINE_SLOTS[i] for i, a in enumerate(highlight)}
    for i, stratum in enumerate(strata):
        for j, collection in enumerate(cols):
            ax = axes[i, j]
            e = entries.get((stratum, collection))
            if e is None:
                ax.set_visible(False)
                continue
            rs = sorted(e["cells"], key=int)
            arms = [a for a in K.ARMS_C if a in e["cells"][rs[0]]["per_arm"]]
            for arm in sorted(arms, key=lambda a: a in highlight):
                ys = [e["cells"][r]["per_arm"][arm]["acc1"]["mean"] for r in rs]
                lo = [e["cells"][r]["per_arm"][arm]["acc1"]["min"] for r in rs]
                hi = [e["cells"][r]["per_arm"][arm]["acc1"]["max"] for r in rs]
                x = [int(r) for r in rs]
                if arm in highlight:
                    ax.fill_between(x, lo, hi, color=colour[arm], alpha=0.15, lw=0)
                    ax.plot(
                        x,
                        ys,
                        color=colour[arm],
                        lw=1.8 if arm == K.OURS else 1.2,
                        marker="o",
                        ms=2.8,
                        zorder=3,
                    )
                else:
                    ax.plot(x, ys, color=GREY, lw=0.6, zorder=1)
            if not e["feasible"]:
                ax.set_facecolor("#f0efec")
                ax.text(
                    0.5,
                    0.92,
                    f"infeasible ({e['blocks_available_min']} blocks)",
                    transform=ax.transAxes,
                    ha="center",
                    fontsize=5.5,
                    color=INK2,
                )
            if i == 0:
                ax.set_title(COLLECTION_LABELS[collection], fontsize=6.5, color=INK, pad=2)
            if j == 0:
                ax.set_ylabel(f"{stratum}\n1-NN", fontsize=6, color=INK2)
            if i == len(strata) - 1:
                ax.set_xlabel("removed statements r", fontsize=6, color=INK2)
                ax.set_xticks([1, 2, 3])
            ax.tick_params(labelsize=5.5, colors=INK2)
            ax.grid(axis="y", color="#ebeae5", lw=0.5)
            for side in ("top", "right"):
                ax.spines[side].set_visible(False)
    handles = [
        Line2D(
            [],
            [],
            color=colour[a],
            lw=1.8 if a == K.OURS else 1.2,
            marker="o",
            ms=2.8,
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
        f"(b) 1-NN accuracy vs r by stratum (c = {c}; probe: mean over seeds, band = [min, max])",
        fontsize=7.5,
        x=0.01,
        ha="left",
        color=INK,
    )


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--probe", type=Path, default=K.OUT_ROOT / "probe_c")
    ap.add_argument("--c", type=int, default=DC.C_COPIES)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--r", type=int, default=1)
    ap.add_argument("--perplexity", type=float, default=4.0)
    ap.add_argument("--tsne-seed", type=int, default=0)
    args = ap.parse_args()
    plt.rcParams.update({"font.family": "DejaVu Sans", "figure.facecolor": SURFACE})
    collection, block = pick_block(args.probe, args.c, args.seed)
    fig = plt.figure(figsize=(7.16, 6.6))
    top, bottom = fig.subfigures(2, 1, height_ratios=[1.0, 1.45], hspace=0.03)
    numbers = draw_block(top, collection, block, args)
    summary_path = args.probe / "summary_c.json"
    if summary_path.exists():
        draw_curves(bottom, json.loads(summary_path.read_text()), args.c)
    # Applied after the axes exist: a subfigure's adjust only moves axes already placed.
    top.subplots_adjust(left=0.01, right=0.99, top=0.76, bottom=0.25, wspace=0.06)
    bottom.subplots_adjust(left=0.08, right=0.99, top=0.9, bottom=0.17, wspace=0.08, hspace=0.18)
    stem = args.probe / f"fig_knn_c_r{args.r}"
    fig.savefig(stem.with_suffix(".png"), dpi=300, facecolor=SURFACE)
    fig.savefig(stem.with_suffix(".pdf"), facecolor=SURFACE)
    numbers.update({k: (str(v) if isinstance(v, Path) else v) for k, v in vars(args).items()})
    K.write_json(stem.with_suffix(".json"), numbers)
    print(f"wrote {stem}.{{png,pdf,json}}  block on {collection}: {block['kb_ids']}")
    for arm, v in numbers["arms"].items():
        print(f"  {arm:20s} 1-NN {v['acc1']:.3f}  ARI {v['ari']:.3f}")


if __name__ == "__main__":
    main()
