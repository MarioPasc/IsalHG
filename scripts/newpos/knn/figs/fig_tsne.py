"""fig_s5_tsne (F-a): t-SNE maps of partial copies under four representations.

Fixed rule, decided before looking: WD50K(66), seed 0, the first 12 sources of
that seed (the run's acceptance order); columns: the word, the nauty
certificate rows, the bipartite edit path (symmetric min) and one-round WL;
t-SNE of the precomputed distances with the same perplexity and seed in every
panel. Colour x shape encodes the source.

Top row, Design B (r = 2): the 6 partial copies of each source, read from the
cell's own evaluated-items file. Bottom row, Design D (r = 1): each source's
catalogue record (large marker), its 3 copies (small), up to 5 of its C8
one-edit look-alikes in the catalogue (grey) and any other catalogue record
that is some copy's 1-NN against the whole catalogue (grey ring); a line joins
each copy to that 1-NN: solid green when it is the source, dashed green when
the source shares the nearest tie block, dotted vermillion when it is another
record. The Design-D sources and copies are regenerated from the job's source
seed and checked against its stored source ids.

Each panel prints the cell's 1-NN accuracy (and, in the top row, its ARI): the
mean over the 27 seeds, from ``full_summary.json``.
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
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
import design_c as DC  # noqa: E402, N812
import design_d as DD  # noqa: E402, N812
import knn_lib as K  # noqa: E402, N812
import rect as R  # noqa: E402, N812
import style as S  # noqa: E402, N812

from experiments.tkde import corpora as C  # noqa: E402, N812
from isalhg.datasets.kb.base import KBRecord  # noqa: E402

PANEL_ARMS: tuple[str, ...] = (K.OURS, "nauty_cert_rows", K.PATH_SYM, K.WL_H1)
WIDTH_IN, HEIGHT_IN = 7.0, 2.6


def _tsne(D: np.ndarray, perplexity: float, seed: int) -> np.ndarray:
    from sklearn.manifold import TSNE

    finite = D[np.isfinite(D)]
    D = np.where(np.isfinite(D), D, (finite.max() if finite.size else 1.0) * 2)
    return TSNE(
        n_components=2,
        metric="precomputed",
        init="random",
        perplexity=min(perplexity, (len(D) - 1) / 3),
        random_state=seed,
    ).fit_transform(D)


#: Label corners in placement order: (name, x, y, ha, va) in axes fraction.
CORNERS: tuple[tuple[str, float, float, str, str], ...] = (
    ("lower left", 0.02, 0.02, "left", "bottom"),
    ("lower right", 0.98, 0.02, "right", "bottom"),
    ("upper left", 0.02, 0.98, "left", "top"),
    ("upper right", 0.98, 0.98, "right", "top"),
)
#: Largest marker area drawn in a panel (points^2); a point within its radius of a label counts.
MAX_MARKER_S = 28.0


def _panel(ax: Any, text: str) -> Any:  # noqa: ANN401
    """Frame the panel and print its label (placed later by :func:`place_labels`)."""
    ax.set_xticks([])
    ax.set_yticks([])
    for side in ax.spines.values():
        side.set_color("#b9b8b2")
        side.set_linewidth(0.5)
    name, x, y, ha, va = CORNERS[0]
    return ax.text(
        x,
        y,
        text,
        transform=ax.transAxes,
        ha=ha,
        va=va,
        fontsize=6,
        bbox={
            "boxstyle": "round,pad=0.25",
            "facecolor": S.SURFACE,
            "edgecolor": "none",
            "alpha": 0.85,
        },
        zorder=10,
    )


def _covered(fig: Any, ax: Any, label: Any, points: np.ndarray) -> int:  # noqa: ANN401
    """Points whose marker reaches the label's box, in display coordinates."""
    renderer = fig.canvas.get_renderer()
    # The text extent follows the position at once (the bbox patch only at the next draw);
    # widen it by the rounded box's pad and the largest marker's radius.
    box = label.get_window_extent(renderer)
    pad = (0.25 * label.get_fontsize() + np.sqrt(MAX_MARKER_S) / 2) * fig.dpi / 72
    xy = ax.transData.transform(points)
    inside = (
        (xy[:, 0] >= box.x0 - pad)
        & (xy[:, 0] <= box.x1 + pad)
        & (xy[:, 1] >= box.y0 - pad)
        & (xy[:, 1] <= box.y1 + pad)
    )
    return int(inside.sum())


def place_labels(fig: Any, labels: list[tuple[str, Any, Any, np.ndarray]]) -> list[dict]:  # noqa: ANN401
    """Keep each label in the lower-left corner unless a point reaches it there.

    Deterministic: after the layout is final, count the points under the label's
    box in every corner (:data:`CORNERS` order) and move it to the corner with
    the fewest, the first in that order on a tie.
    """
    fig.canvas.draw()
    out = []
    for key, ax, label, points in labels:
        counts: dict[str, int] = {}
        for name, x, y, ha, va in CORNERS:
            label.set_position((x, y))
            label.set_ha(ha)
            label.set_va(va)
            counts[name] = _covered(fig, ax, label, points)
        chosen = CORNERS[0][0] if counts[CORNERS[0][0]] == 0 else min(counts, key=counts.get)
        _, x, y, ha, va = next(c for c in CORNERS if c[0] == chosen)
        label.set_position((x, y))
        label.set_ha(ha)
        label.set_va(va)
        out.append({"panel": key, "corner": chosen, "points_under_label": counts})
    return out


def row_b(
    axes: Any,  # noqa: ANN401
    args: argparse.Namespace,
    summary: dict,
    printed: S.Printed,
    labels: list[tuple[str, Any, Any, np.ndarray]],
) -> dict:
    """Copies of the first sources of the Design-B cell, read from its items file."""
    col = C.load_collection(args.collection)
    name = f"B_{args.collection}_r{args.r_b}_s{args.seed}"
    unit = args.root / f"B_{args.collection}"
    cell = json.loads((unit / "cells" / f"{name}.json").read_text())
    rows = (unit / "items" / f"{name}.jsonl").read_text().splitlines()
    c = cell["c"]
    items = [KBRecord.from_json(json.loads(x)) for x in rows][: args.n_sources * c]
    if [it.label for it in items][::c] != cell["source_ids"][: args.n_sources]:
        raise SystemExit("items file and cell source ids disagree: refusing to draw")
    cid = f"B/pendant/{args.collection}/r{args.r_b}"
    mats, _ = K.build_matrices(
        items, list(PANEL_ARMS), n_types=col.n_types, n_preds=col.n_preds, n_jobs=args.n_jobs
    )
    for ax, arm in zip(axes, PANEL_ARMS, strict=True):
        emb = _tsne(mats[arm], args.perplexity, args.tsne_seed)
        for j in range(args.n_sources):
            hue, mk = S.source_style(j)
            pts = emb[j * c : (j + 1) * c]
            ax.scatter(pts[:, 0], pts[:, 1], s=9, marker=mk, color=hue, edgecolor=S.INK, lw=0.3)
        base = ["cells", cid, "per_arm", arm]
        acc = printed.add(summary, [*base, "acc1", "mean"], 3, f"tsne B {arm} acc1")
        ari = printed.add(summary, [*base, "ari", "mean"], 3, f"tsne B {arm} ari")
        labels.append((f"B/{arm}", ax, _panel(ax, f"1-NN {acc}, ARI {ari}"), emb))
        ax.set_title(S.LABELS[arm], pad=2, color=S.WORD if arm == K.OURS else S.INK)
    return {"cell": cid, "items": len(items), "sources": cell["source_ids"][: args.n_sources]}


def _d_setup(args: argparse.Namespace) -> dict[str, Any]:
    unit = args.root / f"D_{args.collection}_pendant"
    job = json.loads((unit / f"D_{args.collection}_pendant.json").read_text())
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
        raise SystemExit("the regenerated Design-D sources differ from the job's: refusing to draw")
    shown = draw.sources[: args.n_sources]
    copies = [draw.copies[args.r_d][i] for i in range(args.n_sources)]
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


def row_d(
    axes: Any,  # noqa: ANN401
    args: argparse.Namespace,
    summary: dict,
    printed: S.Printed,
    labels: list[tuple[str, Any, Any, np.ndarray]],
) -> dict:
    """Sources, copies, look-alikes and 1-NN lines against the whole catalogue."""
    ctx = _d_setup(args)
    col, cat = ctx["col"], ctx["cat"]
    cat_recs = list(cat.records)
    cat_index = cat.index()
    cat_hs = K.hypergraphs(cat_recs, col.n_types, col.n_preds)
    queries = [cp for cs in ctx["copies"] for cp in cs]
    q_src = np.array([cat_index[cp.label] for cp in queries])
    q_hs = K.hypergraphs(queries, col.n_types, col.n_preds)
    cid = f"D/pendant/{args.collection}/r{args.r_d}"
    n_src = len(ctx["shown"])
    for ax, arm in zip(axes, PANEL_ARMS, strict=True):
        Dq = R.make_arm(arm, args.n_jobs).fit(cat_hs).rect(q_hs)
        targets = []
        for i in range(len(queries)):
            nn = np.flatnonzero(Dq[i] == Dq[i].min())
            src_in = q_src[i] in nn
            targets.append((int(q_src[i]) if src_in else int(nn[0]), src_in, len(nn) > 1))
        cat_pts = [cat_index[s.kb_id] for s in ctx["shown"]]
        for nbrs in ctx["lookalikes"]:
            cat_pts += [cat_index[kb] for kb in nbrs if cat_index[kb] not in cat_pts]
        n_look = len(cat_pts)
        cat_pts += sorted({t for t, _, _ in targets if t not in cat_pts})
        recs = [cat_recs[i] for i in cat_pts] + queries
        Dp = K.build_matrices(
            recs, [arm], n_types=col.n_types, n_preds=col.n_preds, n_jobs=args.n_jobs
        )[0][arm]
        emb = _tsne(Dp, args.perplexity, args.tsne_seed)
        pos = {ci: emb[k] for k, ci in enumerate(cat_pts)}
        qpos = emb[len(cat_pts) :]
        for k in range(n_src, len(cat_pts)):
            ring = k >= n_look
            ax.scatter(
                *emb[k], s=7, facecolor="none" if ring else S.OTHER, edgecolor=S.OTHER, lw=0.5
            )
        for i, (t, ok, tie) in enumerate(targets):
            style = ("--" if tie else "-") if ok else ":"
            ax.plot(
                [qpos[i, 0], pos[t][0]],
                [qpos[i, 1], pos[t][1]],
                color=S.GOOD if ok else S.BEST,
                lw=0.6,
                ls=style,
                zorder=2,
            )
        for j in range(n_src):
            hue, mk = S.source_style(j)
            ax.scatter(*emb[j], s=28, marker=mk, color=hue, edgecolor=S.INK, lw=0.6, zorder=4)
            qs = qpos[j * DD.C_COPIES : (j + 1) * DD.C_COPIES]
            ax.scatter(
                qs[:, 0], qs[:, 1], s=8, marker=mk, color=hue, edgecolor=S.INK, lw=0.25, zorder=3
            )
        acc = printed.add(
            summary, ["cells", cid, "per_arm", arm, "acc1", "mean"], 3, f"tsne D {arm}"
        )
        labels.append((f"D/{arm}", ax, _panel(ax, f"1-NN {acc}"), emb))
    return {"cell": cid, "queries": len(queries), "sources": [s.kb_id for s in ctx["shown"]]}


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--root", type=Path, default=K.OUT_ROOT / "full")
    ap.add_argument("--out", type=Path, default=None, help="default <root>/section")
    ap.add_argument("--collection", default="wd50k66")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--r-b", type=int, default=2)
    ap.add_argument("--r-d", type=int, default=1)
    ap.add_argument("--n-sources", type=int, default=12)
    ap.add_argument("--lookalikes", type=int, default=5)
    ap.add_argument("--perplexity", type=float, default=15.0)
    ap.add_argument("--tsne-seed", type=int, default=0)
    ap.add_argument("--n-jobs", type=int, default=16)
    args = ap.parse_args()
    import matplotlib.pyplot as plt

    S.apply_rc()
    summary = json.loads((args.root / "full_summary.json").read_text())
    printed = S.Printed()
    fig, axes = plt.subplots(
        2, len(PANEL_ARMS), figsize=(WIDTH_IN, HEIGHT_IN), layout="constrained"
    )
    labels: list[tuple[str, Any, Any, np.ndarray]] = []
    meta_b = row_b(axes[0], args, summary, printed, labels)
    meta_d = row_d(axes[1], args, summary, printed, labels)
    axes[0, 0].set_ylabel(f"B, r = {args.r_b}")
    axes[1, 0].set_ylabel(f"D, r = {args.r_d}")
    label_positions = place_labels(fig, labels)
    paths = S.save(
        fig,
        args.out or args.root / "section",
        "fig_s5_tsne",
        printed,
        {
            "root": str(args.root),
            "row_b": meta_b,
            "row_d": meta_d,
            "perplexity": args.perplexity,
            "tsne_seed": args.tsne_seed,
            "panel_arms": list(PANEL_ARMS),
            "label_positions": label_positions,
        },
    )
    print("\n".join(map(str, paths)))


if __name__ == "__main__":
    main()
