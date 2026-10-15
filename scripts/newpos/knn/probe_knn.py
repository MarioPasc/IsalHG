"""Run the KNN_2026-10-15 cells (Designs A and B, the mix condition) and tabulate them.

One JSON per cell under ``<out>/cells/``, the evaluated items as JSON lines
under ``<out>/items/``, and ``SUMMARY.md`` + ``summary.json`` aggregated over
the seeds found on disk. Cells already on disk are skipped (``--force``
recomputes them), so the same command resumes an interrupted run.

Cells
-----
``B``    partial copies, pendant removals: ``(collection, r, seed)``.
``mix``  partial copies, C8's pendant/interior mix: ``(collection, r, seed)``.
``A``    real NDC lineages, a seeded lineage sample: ``(collection, seed)``.
``Afull`` every NDC lineage with >= 3 versions (deterministic kNN reference).
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import knn_lib as K  # noqa: E402, N812

from experiments.tkde import corpora as C  # noqa: E402, N812
from isalhg.datasets.kb.base import KBCollection, KBRecord  # noqa: E402

logger = logging.getLogger("probe_knn")

METRICS: tuple[str, ...] = ("acc1", "acc5", "f1_1", "f1_5", "ari", "nmi")


# --------------------------------------------------------------------------- helpers


def _cell_name(design: str, collection: str, seed: int | None, r: int | None = None) -> str:
    parts = [design, collection]
    if r is not None:
        parts.append(f"r{r}")
    if seed is not None:
        parts.append(f"s{seed}")
    return "_".join(parts)


def _evaluate_items(
    items: Sequence[KBRecord],
    codes: np.ndarray,
    col: KBCollection,
    keys: K.IsoKeys,
    args: argparse.Namespace,
    pam_seed: int,
    candidate_mask: np.ndarray | None = None,
    cluster: bool = True,
) -> dict[str, Any]:
    """Matrices of every arm on ``items`` and their kNN / k-medoids scores."""
    iso_class, disagreements = K.iso_classes(items, keys)
    out: dict[str, Any] = {
        "n_items": len(items),
        "n_classes": int(len(np.unique(codes))),
        "iso_census": {
            "n_iso_classes": int(len(np.unique(iso_class))),
            "key_disagreements": disagreements,
            **K.cross_class_iso(iso_class, codes),
            "exact_arm_acc1_ceiling": K.exact_arm_ceiling(iso_class, codes, candidate_mask),
        },
        "pam_seed": pam_seed,
        "arms": {},
    }
    mats, secs = K.build_matrices(
        items, args.arms, n_types=col.n_types, n_preds=col.n_preds, n_jobs=args.n_jobs
    )
    if args.ablation:
        M, n_cens, s = K.build_ablation_matrix(
            items, n_types=col.n_types, n_preds=col.n_preds, budget_s=args.ablation_budget
        )
        mats[K.ABLATION], secs[K.ABLATION] = M, s
        out["ablation_censored"] = n_cens
    k_clusters = out["n_classes"]
    p_correct: dict[str, np.ndarray] = {}
    for arm, M in mats.items():
        res = K.evaluate_arm(
            M,
            codes,
            k_clusters=k_clusters,
            pam_seed=pam_seed,
            iso_class=iso_class,
            candidate_mask=candidate_mask,
            cluster=cluster,
        )
        res["secs_matrix"] = secs[arm]
        res["medoid_ids"] = [items[i].kb_id for i in res.pop("medoid_ids_idx", [])]
        p_correct[arm] = res.pop("_p_correct1")
        res.pop("_p_correct5")
        # Kept per query so later diagnostics (and query-level paired tests) need no rerun.
        res["p_correct1"] = [round(float(x), 6) for x in p_correct[arm]]
        out["arms"][arm] = res
        if args.save_matrices:
            dest = args.out / "matrices" / args.current_cell
            dest.mkdir(parents=True, exist_ok=True)
            np.save(dest / f"{arm}.npy", M.astype(np.float32))
    out["ceiling"] = K.ceiling_census(p_correct)
    return out


def _availability(col: KBCollection, out: Path) -> dict[str, Any]:
    """Interior-removal availability of a collection, cached on disk."""
    path = out / "calibration" / f"availability_{col.name}.json"
    if path.exists():
        return json.loads(path.read_text())
    t0 = time.perf_counter()
    info = K.interior_availability(col)
    info["secs"] = time.perf_counter() - t0
    K.write_json(path, info)
    return info


# --------------------------------------------------------------------------- Design B / mix


CONDITION_PREFIX = {"pendant": "B", "mix": "Bmix"}


def run_copies(collection: str, condition: str, seed: int, args: argparse.Namespace) -> None:
    """All ``r`` cells of one Design-B replicate (pendant or mix), paired over ``r``."""
    prefix = CONDITION_PREFIX[condition]
    names = {r: _cell_name(prefix, collection, seed, r) for r in args.r}
    todo = [
        r for r in args.r if args.force or not (args.out / "cells" / f"{names[r]}.json").exists()
    ]
    if not todo:
        logger.info("skip %s %s s%d (on disk)", condition, collection, seed)
        return
    t_cell = time.perf_counter()
    col = C.load_collection(collection)
    keys = K.IsoKeys(col.n_types, col.n_preds)
    q, calib = 0.0, None
    if condition == "mix":
        calib = _availability(col, args.out)
        q = K.mix_q(K.PENDANT_SHARE[collection], calib["availability"])
    source_seed = K.cell_seed(seed, condition, collection, "sources")
    rng = np.random.default_rng(source_seed)
    draw = K.select_sources(col, args.S, args.r, args.c, rng, keys, q_interior=q)
    logger.info(
        "%s %s s%d: %d sources (tried %d, ineligible %d, iso-skipped %d) in %.1f s",
        condition,
        collection,
        seed,
        len(draw.sources),
        draw.n_tried,
        draw.n_ineligible,
        draw.n_skipped_iso_source,
        draw.secs,
    )
    for r in args.r:
        args.current_cell = names[r]
        t0 = time.perf_counter()
        items = [cp for per_source in draw.copies[r] for cp in per_source]
        codes = np.repeat(np.arange(len(draw.sources)), args.c)
        st = draw.stats[r]
        steps = st.steps_pendant + st.steps_interior
        payload: dict[str, Any] = {
            "design": "B",
            "condition": condition,
            "collection": collection,
            "seed": seed,
            "source_seed": source_seed,
            "r": r,
            "S_requested": args.S,
            "S": len(draw.sources),
            "c": args.c,
            "source_ids": [s.kb_id for s in draw.sources],
            "eligibility": {
                "n_tried": draw.n_tried,
                "n_ineligible": draw.n_ineligible,
                "n_skipped_iso_source": draw.n_skipped_iso_source,
                "shortfall": draw.shortfall,
                "secs_select": draw.secs,
            },
            "copies": {
                "draws": st.draws,
                "dead_ends": st.dead_ends,
                "iso_rejected_within_source": st.iso_rejected,
                "key_disagreements": st.key_disagreements,
                "steps_pendant": st.steps_pendant,
                "steps_interior": st.steps_interior,
                "steps_fallback": st.steps_fallback,
                "realized_pendant_share": st.steps_pendant / steps if steps else None,
                "items_iso_to_source": int(
                    sum(
                        keys(cp)[0] == keys(s)[0]
                        for s, cs in zip(draw.sources, draw.copies[r], strict=True)
                        for cp in cs
                    )
                ),
                "n_mean": float(np.mean([cp.n for cp in items])),
                "m_mean": float(np.mean([cp.m for cp in items])),
                "source_n_mean": float(np.mean([s.n for s in draw.sources])),
                "source_m_mean": float(np.mean([s.m for s in draw.sources])),
            },
            "mix": None
            if condition != "mix"
            else {
                "target_pendant_share": K.PENDANT_SHARE[collection],
                "availability": calib,
                "q_interior": q,
            },
        }
        payload.update(
            _evaluate_items(
                items, codes, col, keys, args, K.cell_seed(seed, condition, collection, r, "pam")
            )
        )
        payload["secs_cell"] = time.perf_counter() - t0
        payload["secs_replicate_total"] = time.perf_counter() - t_cell
        K.write_records(args.out / "items" / f"{names[r]}.jsonl", items)
        K.write_json(args.out / "cells" / f"{names[r]}.json", payload)
        _log_cell(names[r], payload)


# --------------------------------------------------------------------------- Design A


def run_lineages(collection: str, seed: int | None, args: argparse.Namespace) -> None:
    """One Design-A cell: a seeded lineage sample (``seed``) or every lineage (``None``)."""
    design = "A" if seed is not None else "Afull"
    name = _cell_name(design, collection, seed)
    if not args.force and (args.out / "cells" / f"{name}.json").exists():
        logger.info("skip %s (on disk)", name)
        return
    args.current_cell = name
    t0 = time.perf_counter()
    col = C.load_collection(collection)
    keys = K.IsoKeys(col.n_types, col.n_preds)
    lin = K.lineages(col, min_versions=3)
    sample_seed = K.cell_seed(seed if seed is not None else 0, "A", collection, "lineages")
    if seed is None:
        chosen = sorted(lin, key=int)
    else:
        chosen = K.sample_lineages(lin, args.lineages, np.random.default_rng(sample_seed))
    idx = [i for node in chosen for i in lin[node]]
    items = [col.records[i] for i in idx]
    codes = np.array([chosen.index(str(col.records[i].meta["class_id"])) for i in idx])
    windows = np.array([int(col.records[i].meta["window"]) for i in idx])
    mask = windows[:, None] != windows[None, :]
    payload: dict[str, Any] = {
        "design": design,
        "condition": "lineage",
        "collection": collection,
        "seed": seed,
        "sample_seed": sample_seed if seed is not None else None,
        "n_lineages_available": len(lin),
        "lineages": chosen,
        "versions_per_lineage": [len(lin[n]) for n in chosen],
        "n_windows": int(len(np.unique(windows))),
        "candidates_per_query_mean": float(mask.sum(axis=1).mean()),
        "same_lineage_candidates_mean": float(
            (mask & (codes[:, None] == codes[None, :])).sum(axis=1).mean()
        ),
    }
    payload.update(
        _evaluate_items(
            items,
            codes,
            col,
            keys,
            args,
            K.cell_seed(seed if seed is not None else 0, design, collection, "pam"),
            candidate_mask=mask,
            cluster=seed is not None,
        )
    )
    payload["secs_cell"] = time.perf_counter() - t0
    K.write_json(args.out / "cells" / f"{name}.json", payload)
    _log_cell(name, payload)


# --------------------------------------------------------------------------- summary


def _log_cell(name: str, payload: dict[str, Any]) -> None:
    arms = payload["arms"]
    w = arms.get(K.OURS, {})
    b_acc = K.best_competitor(arms, "acc1")
    b_ari = K.best_competitor(arms, "ari")
    logger.info(
        "%s: N=%d  w° acc1 %.3f ari %.3f | best acc1 %s %.3f | best ari %s %.3f | %.1f s",
        name,
        payload["n_items"],
        w.get("acc1", float("nan")),
        w.get("ari", float("nan")),
        *b_acc,
        *b_ari,
        payload["secs_cell"],
    )


def _group_key(p: dict[str, Any]) -> tuple[str, str, str, int | None]:
    return (p["design"], p["condition"], p["collection"], p.get("r"))


def summarize(out: Path) -> dict[str, Any]:
    """Aggregate every cell JSON on disk over seeds and write ``SUMMARY.md``."""
    groups: dict[tuple[str, str, str, int | None], list[dict[str, Any]]] = defaultdict(list)
    for path in sorted((out / "cells").glob("*.json")):
        p = json.loads(path.read_text())
        groups[_group_key(p)].append(p)
    rows: list[dict[str, Any]] = []
    for key, cells in sorted(groups.items(), key=lambda kv: tuple(str(x) for x in kv[0])):
        design, condition, collection, r = key
        arms = sorted({a for c in cells for a in c["arms"]}, key=lambda a: (a != K.OURS, a))
        per_arm: dict[str, dict[str, Any]] = {}
        for arm in arms:
            vals = {
                m: [c["arms"][arm][m] for c in cells if m in c["arms"].get(arm, {})]
                for m in METRICS
            }
            per_arm[arm] = {m: K.seed_spread(v) for m, v in vals.items() if v}
            per_arm[arm]["secs_matrix"] = K.seed_spread(
                [c["arms"][arm]["secs_matrix"] for c in cells if arm in c["arms"]]
            )
            per_arm[arm]["false_zeros"] = K.seed_spread(
                [c["arms"][arm]["false_zeros"] for c in cells if arm in c["arms"]]
            )
            certs = [
                c["arms"][arm]["certified"]
                for c in cells
                if "certified" in c["arms"].get(arm, {})
                and c["arms"][arm]["certified"]["ratio_median"] is not None
            ]
            if certs:
                per_arm[arm]["certified"] = {
                    "ratio_median": K.seed_spread([x["ratio_median"] for x in certs]),
                    "ratio_max": max(x["ratio_max"] for x in certs),
                    "n_over_bound": sum(x["n_over_bound"] for x in certs),
                    "n_1medoid_over_bound": sum(x["n_1medoid_over_bound"] for x in certs),
                    "n_certified": sum(x["n_certified"] for x in certs),
                    "n_lb_zero": sum(x["n_lb_zero"] for x in certs),
                    "n_singletons": sum(x["n_singletons"] for x in certs),
                }
        means = {a: {m: v[m]["mean"] for m in METRICS if m in v} for a, v in per_arm.items()}
        best = {m: K.best_competitor(means, m) for m in ("acc1", "ari", "acc5", "nmi")}
        word = means.get(K.OURS, {})
        rows.append(
            {
                "design": design,
                "condition": condition,
                "collection": collection,
                "r": r,
                "seeds": sorted(c["seed"] for c in cells if c["seed"] is not None),
                "n_items": [c["n_items"] for c in cells],
                "S": [c.get("S") for c in cells],
                "per_arm": per_arm,
                "best_competitor": best,
                "word": word,
                "word_wins": {m: bool(word.get(m, -1) > best[m][1]) for m in best},
                "realized_pendant_share": [
                    c["copies"]["realized_pendant_share"] for c in cells if "copies" in c
                ],
                "iso": [c["iso_census"] for c in cells],
                "ceiling": [c.get("ceiling", {}) for c in cells],
                "copies": [c.get("copies") for c in cells],
                "secs_cell": [c["secs_cell"] for c in cells],
            }
        )
    summary = {"rows": rows, "generated": time.strftime("%Y-%m-%d %H:%M %Z")}
    K.write_json(out / "summary.json", summary)
    (out / "SUMMARY.md").write_text(render_markdown(rows))
    return summary


def _fmt(spread: dict[str, float] | None) -> str:
    if not spread:
        return "–"
    return f"{spread['mean']:.3f} [{spread['min']:.3f}, {spread['max']:.3f}]"


def _hyp_table(rows: list[dict[str, Any]], metrics: Sequence[str]) -> list[str]:
    head = (
        "| collection | r | N | "
        + " | ".join(f"`w°` {m} | best competitor {m}" for m in metrics)
        + " | word ahead on all |"
    )
    lines = [head, "|" + "---|" * (3 + 2 * len(metrics) + 1)]
    for row in rows:
        cells = [
            row["collection"],
            str(row["r"] if row["r"] is not None else "–"),
            str(int(np.mean(row["n_items"]))),
        ]
        for m in metrics:
            cells.append(_fmt(row["per_arm"][K.OURS].get(m)))
            name, _ = row["best_competitor"][m]
            cells.append(f"{name} {_fmt(row['per_arm'][name].get(m))}")
        ahead = all(row["word_wins"][m] for m in metrics)
        cells.append("yes" if ahead else "**no (kill)**")
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def _spread_of(rows_vals: Sequence[float | None]) -> str:
    vals = [v for v in rows_vals if v is not None]
    return _fmt(K.seed_spread(vals)) if vals else "–"


def _diagnostics_table(rows: list[dict[str, Any]]) -> list[str]:
    """Ceiling and isomorphism diagnostics per cell (descriptive, not hypotheses)."""
    lines = [
        "## Diagnostics — ceiling and isomorphism (descriptive)",
        "",
        "`all correct` = share of queries every main arm (word + 10 competitors) gets right "
        "with certainty at 1-NN; `all non-floor` = the same without the two floors (whose "
        "ties make certainty rare); `w vs best` = expected shares of queries the word gets "
        "right and the best competitor (by 1-NN) wrong / the reverse; `arms >= 0.9` = arms "
        "with 1-NN accuracy >= 0.9, per seed; `x-class iso` = share of items whose "
        "isomorphism class also holds an item of another class; `exact ceiling` = highest "
        "1-NN accuracy any complete invariant can reach (a query with isomorphic candidates "
        "draws its neighbour among them).",
        "",
        "| cell | collection | r | all correct | all non-floor | w vs best (best) | "
        "arms >= 0.9 | x-class iso | exact ceiling |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        ce = row["ceiling"]
        bests = sorted({c.get("best_competitor", "-") for c in ce})
        lines.append(
            f"| {row['design']}/{row['condition']} | {row['collection']} | "
            f"{row['r'] if row['r'] is not None else '–'} | "
            f"{_spread_of([c.get('all_arms_correct') for c in ce])} | "
            f"{_spread_of([c.get('all_nonfloor_correct') for c in ce])} | "
            f"{_spread_of([c.get('word_only_vs_best') for c in ce])} / "
            f"{_spread_of([c.get('best_only_vs_best') for c in ce])} ({', '.join(bests)}) | "
            f"{', '.join(str(c.get('n_arms_acc1_ge_0.9', '–')) for c in ce)} | "
            f"{_spread_of([i.get('cross_class_iso_fraction') for i in row['iso']])} | "
            f"{_spread_of([i.get('exact_arm_acc1_ceiling') for i in row['iso']])} |"
        )
    return lines + [""]


def _certified_table(rows: list[dict[str, Any]]) -> list[str]:
    """Prop. 6.1 certified ratio of the PAM medoids per cell (descriptive)."""
    lines = [
        "## Certified representative — cost(M)/LB of the PAM medoids (Prop. 6.1, descriptive)",
        "",
        "Per cluster with >= 2 members: `LB = sum_{i<j} d / (N-1)`, ratio = `cost(M)/LB` of the "
        "PAM medoid; the bound `2 - 2/N` holds for a metric's in-cluster 1-medoid. `median` = "
        "mean over seeds of the per-cell median; `max` = max over seeds and clusters; `over` = "
        "PAM medoids above `2 - 2/N` (summed over seeds) of the certified clusters. The last "
        "column lists arms whose in-cluster 1-medoid exceeds the bound somewhere (possible "
        "only for a non-metric).",
        "",
        "| cell | collection | r | `w°` median | `w°` max | `w°` over | arms with a 1-medoid over "
        "the bound |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        w = row["per_arm"].get(K.OURS, {}).get("certified")
        if not w:
            continue
        viol = [
            f"{a} ({v['certified']['n_1medoid_over_bound']})"
            for a, v in row["per_arm"].items()
            if v.get("certified") and v["certified"]["n_1medoid_over_bound"]
        ]
        lines.append(
            f"| {row['design']}/{row['condition']} | {row['collection']} | "
            f"{row['r'] if row['r'] is not None else '–'} | {_fmt(w['ratio_median'])} | "
            f"{w['ratio_max']:.3f} | {w['n_over_bound']} of {w['n_certified']} | "
            f"{', '.join(viol) if viol else 'none'} |"
        )
    return lines + [""]


def render_markdown(rows: list[dict[str, Any]]) -> str:
    """The probe's markdown report: hypothesis tables, per-arm detail, costs."""
    by = defaultdict(list)
    for row in rows:
        by[(row["design"], row["condition"])].append(row)
    out = [
        "# KNN_2026-10-15 probe — summary (generated; do not edit)",
        "",
        "Point estimates are means over seeds, with [min, max] over seeds. Descriptive only;",
        "no significance is claimed at probe scale. 'best competitor' excludes the word and the",
        "`wstar_orbit` ablation. A kill is a competitor mean >= the word mean on a hypothesis",
        "metric.",
        "",
    ]
    sections = (
        (("B", "pendant"), "H-KNN-B — partial copies, pendant removals", ("acc1", "ari")),
        (("A", "lineage"), "H-KNN-A — real NDC lineages (seeded lineage sample)", ("acc1", "ari")),
        (
            ("Afull", "lineage"),
            "Design A reference — kNN over every lineage with >= 3 versions (no clustering)",
            ("acc1", "acc5"),
        ),
        (("B", "mix"), "H-KNN-mix — partial copies, C8 edit mix (claim on WD50K only)", ("acc1",)),
    )
    for key, title, metrics in sections:
        if key not in by:
            continue
        out += [f"## {title}", ""] + _hyp_table(by[key], metrics) + [""]
        if key == ("B", "mix"):
            out.append(
                "Realized pendant share of the removal steps, per seed: "
                + "; ".join(
                    f"{r['collection']} r={r['r']}: "
                    + ", ".join(f"{x:.3f}" for x in r["realized_pendant_share"])
                    for r in by[key]
                )
            )
            out.append("")
    out += _diagnostics_table(rows)
    out += _certified_table(rows)
    out += ["## Per-arm detail (mean [min, max] over seeds)", ""]
    for row in rows:
        tag = f"{row['design']}/{row['condition']} {row['collection']}" + (
            f" r={row['r']}" if row["r"] is not None else ""
        )
        out += [f"### {tag} — seeds {row['seeds']}, N {row['n_items']}", ""]
        out.append(
            "| arm | 1-NN acc | 5-NN acc | macro-F1 (1-NN) | ARI | NMI | false zeros | "
            "cert. ratio median / max / over bound | matrix s |"
        )
        out.append("|---|---|---|---|---|---|---|---|---|")
        for arm, v in row["per_arm"].items():
            scores = " | ".join(_fmt(v.get(m)) for m in ("acc1", "acc5", "f1_1", "ari", "nmi"))
            ce = v.get("certified")
            cert = (
                f"{ce['ratio_median']['mean']:.3f} / {ce['ratio_max']:.3f} / "
                f"{ce['n_over_bound']} of {ce['n_certified']}"
                if ce
                else "–"
            )
            out.append(
                f"| {arm} | {scores} | {v['false_zeros']['mean']:.0f} | {cert} | "
                f"{v['secs_matrix']['mean']:.2f} |"
            )
        iso = row["iso"]
        out.append("")
        out.append(
            "Iso census per seed (items in a cross-class isomorphism class / same-class iso "
            "pairs / key disagreements): "
            + "; ".join(
                f"{i['items_in_cross_class_iso']}/{i['same_class_iso_pairs']}/"
                f"{i['key_disagreements']}"
                for i in iso
            )
        )
        cps = [c for c in row["copies"] if c]
        if cps:
            out.append(
                "Copies per seed (within-source iso draws rejected / dead ends / draws): "
                + "; ".join(
                    f"{c['iso_rejected_within_source']}/{c['dead_ends']}/{c['draws']}" for c in cps
                )
            )
        out.append(
            f"Cell wall-clock (s) per seed: {', '.join(f'{s:.1f}' for s in row['secs_cell'])}"
        )
        out.append("")
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------- main


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--designs",
        nargs="+",
        default=["B", "mix", "A", "Afull"],
        choices=["B", "mix", "A", "Afull"],
    )
    ap.add_argument("--collections", nargs="+", default=list(K.COLLECTIONS))
    ap.add_argument("--mix-collections", nargs="+", default=["wd50k66", "wd50k100"])
    ap.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    ap.add_argument("--S", type=int, default=60)
    ap.add_argument("--c", type=int, default=6)
    ap.add_argument("--r", nargs="+", type=int, default=[1, 2, 3])
    ap.add_argument("--lineages", type=int, default=30)
    ap.add_argument("--arms", nargs="+", default=list(K.ARMS))
    ap.add_argument("--ablation", action="store_true", help="also build wstar_orbit (slow)")
    ap.add_argument("--ablation-budget", type=float, default=60.0)
    ap.add_argument("--n-jobs", type=int, default=16)
    ap.add_argument("--out", type=Path, default=K.OUT_ROOT / "probe")
    ap.add_argument("--save-matrices", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--summary-only", action="store_true")
    args = ap.parse_args()
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(name)s %(message)s", datefmt="%H:%M:%S"
    )
    for noisy in ("isalhg", "experiments"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    args.out.mkdir(parents=True, exist_ok=True)
    args.current_cell = ""
    if not args.summary_only:
        K.write_json(
            args.out / "runs" / f"run_{time.strftime('%Y%m%dT%H%M%S')}.json",
            {"argv": sys.argv, **{k: str(v) for k, v in vars(args).items()}},
        )
        for seed in args.seeds:
            if "B" in args.designs:
                for collection in args.collections:
                    run_copies(collection, "pendant", seed, args)
            if "mix" in args.designs:
                for collection in args.mix_collections:
                    run_copies(collection, "mix", seed, args)
            if "A" in args.designs:
                for collection in K.LINEAGE_COLLECTIONS:
                    if collection in args.collections:
                        run_lineages(collection, seed, args)
        if "Afull" in args.designs:
            for collection in K.LINEAGE_COLLECTIONS:
                if collection in args.collections:
                    run_lineages(collection, None, args)
    summarize(args.out)
    print((args.out / "SUMMARY.md").read_text())


if __name__ == "__main__":
    main()
