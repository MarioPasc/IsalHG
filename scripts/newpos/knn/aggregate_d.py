"""Aggregate the Design-D job JSONs: seed statistics, tests, verdicts and cost (LOG.md §7).

Reads every ``D_<collection>_<mix>.json`` under ``--inputs`` and writes
``SUMMARY_D.md`` and ``summary_d.json`` there (or under ``--out``).

Per ``(collection, mix, r)`` cell and arm, over seeds: mean, [min, max] and a
95 % BCa interval of the expected 1-NN accuracy and of the source's reciprocal
rank; against each competitor, a one-sided Wilcoxon signed-rank test of
word > competitor over paired seeds, Holm across the eleven competitors, and
the rank-biserial correlation. Verdicts (§7): H-KNN-D (``mix = pendant``) and
H-KNN-D-mix (``mix = empirical``, WD50K only) claim the highest 1-NN accuracy at
``r = 1`` and ``r = 2``; a claim cell is killed when any competitor's seed mean
is >= the word's. ``r = 3`` is reported with its own verdict and no claim.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import aggregate_c as AC  # noqa: E402, N812
import knn_lib as K  # noqa: E402, N812

CLAIM_RS: tuple[int, ...] = (1, 2)
METRICS: tuple[str, ...] = ("acc1", "rr")
HYP = {"pendant": "H-KNN-D", "empirical": "H-KNN-D-mix"}
MIX_COLLECTIONS = {"empirical": ("wd50k66", "wd50k100")}
SHORT = AC.SHORT
S_FULL = 200
SEEDS_FULL = 27


def _values(job: dict[str, Any], r: str, arm: str, metric: str) -> list[float]:
    out = []
    for s in sorted(job["seeds"], key=int):
        cell = job["seeds"][s]["cells"].get(r)
        if cell and arm in cell["arms"]:
            out.append(float(cell["arms"][arm][metric]))
    return out


def aggregate_cell(job: dict[str, Any], r: str) -> dict[str, Any]:
    """Statistics, tests and the verdict of one ``(job, r)`` cell."""
    arms = [a for a in K.ARMS_C if _values(job, r, a, "acc1")]
    per_arm: dict[str, dict[str, Any]] = {}
    for arm in arms:
        per_arm[arm] = {}
        for m in METRICS:
            v = _values(job, r, arm, m)
            lo, hi = AC.bca(v)
            per_arm[arm][m] = {
                "mean": float(np.mean(v)),
                "min": min(v),
                "max": max(v),
                "n": len(v),
                "bca": [lo, hi],
                "values": v,
            }
        per_arm[arm]["nn_zero_share"] = float(np.mean(_values(job, r, arm, "nn_zero_share")))
        per_arm[arm]["secs"] = float(np.mean(_values(job, r, arm, "secs")))
        pps = [
            x
            for x in (
                job["seeds"][s]["cells"][r]["arms"][arm].get("pairs_per_s") for s in job["seeds"]
            )
            if x
        ]
        per_arm[arm]["pairs_per_s"] = float(np.mean(pps)) if pps else None
    tests = {
        m: AC.paired_tests(
            per_arm[K.OURS][m]["values"],
            {a: per_arm[a][m]["values"] for a in arms if a in K.COMPETITORS_C},
        )
        for m in METRICS
    }
    means = {a: {m: v[m]["mean"] for m in METRICS} for a, v in per_arm.items()}
    best = {m: K.best_competitor(means, m, K.COMPETITORS_C) for m in METRICS}
    word = means[K.OURS]
    ahead = bool(word["acc1"] > best["acc1"][1])
    claim = int(r) in CLAIM_RS
    if claim:
        verdict = "word ahead" if ahead else "kill"
    else:
        verdict = "word ahead (no claim)" if ahead else "competitor ahead (no claim)"
    cells = [job["seeds"][s]["cells"][r] for s in sorted(job["seeds"], key=int)]
    shares = [c["copies"]["realized_pendant_share"] for c in cells]
    return {
        "r": int(r),
        "claim": claim,
        "per_arm": per_arm,
        "tests": tests,
        "best_competitor": best,
        "word": word,
        "word_ahead": ahead,
        "verdict": verdict,
        "n_queries": [c["n_queries"] for c in cells],
        "ceiling": [c["exact_arm_ceiling"] for c in cells],
        "n_iso_to_catalogue": [c["n_iso_to_catalogue"] for c in cells],
        "realized_pendant_share": shares,
        "secs": [c["secs"] for c in cells],
    }


def cost(job: dict[str, Any]) -> dict[str, Any]:
    """Measured cost of the job and its extrapolation to ``S = 200`` and 27 seeds."""
    seeds = list(job["seeds"].values())
    per_seed = float(np.mean([s["secs_seed"] for s in seeds]))
    S = job["config"]["S"]
    fit = float(sum(job["secs_fit"].values()))
    # Every per-seed term (source draw, copies, rectangles) grows linearly in the query count.
    full = job["secs_setup"] + SEEDS_FULL * per_seed * S_FULL / S
    bip = [
        c["arms"][a].get("pairs_per_s")
        for s in seeds
        for c in s["cells"].values()
        for a in ("bipartite_ged_path", "bipartite_ged_assign")
        if c["arms"][a].get("pairs_per_s")
    ]
    return {
        "catalogue": job["catalogue"]["n_catalogue"],
        "secs_setup": job["secs_setup"],
        "secs_fit_total": fit,
        "secs_fit_slowest": max(job["secs_fit"].items(), key=lambda kv: kv[1]),
        "secs_per_seed": per_seed,
        "bipartite_pairs_per_s": float(np.mean(bip)) if bip else None,
        "n_jobs": job["config"]["n_jobs"],
        "full_run_minutes": full / 60.0,
    }


def aggregate(jobs: list[dict[str, Any]]) -> dict[str, Any]:
    """Every job's cells, the two hypothesis verdicts and the cost table."""
    rows = []
    for job in jobs:
        rs = sorted({r for s in job["seeds"].values() for r in s["cells"]}, key=int)
        rows.append(
            {
                "collection": job["collection"],
                "mix": job["mix"],
                "seeds": sorted(int(s) for s in job["seeds"]),
                "S": [s["S"] for s in job["seeds"].values()],
                "catalogue": job["catalogue"],
                "q_interior": job["config"]["q_interior"],
                "cells": {r: aggregate_cell(job, r) for r in rs},
                "cost": cost(job),
            }
        )
    hyps = {}
    for mix, name in HYP.items():
        mine = [x for x in rows if x["mix"] == mix]
        if mix in MIX_COLLECTIONS:
            mine = [x for x in mine if x["collection"] in MIX_COLLECTIONS[mix]]
        kills = [
            (x["collection"], c["r"])
            for x in mine
            for c in x["cells"].values()
            if c["claim"] and c["verdict"] == "kill"
        ]
        r3 = [
            (x["collection"], c["verdict"])
            for x in mine
            for c in x["cells"].values()
            if not c["claim"]
        ]
        hyps[mix] = {
            "hypothesis": name,
            "collections": [x["collection"] for x in mine],
            "claim_cells": sum(1 for x in mine for c in x["cells"].values() if c["claim"]),
            "kills": kills,
            "fired": bool(kills),
            "r3": r3,
        }
    return {"rows": rows, "hypotheses": hyps, "generated": time.strftime("%Y-%m-%d %H:%M %Z")}


# --------------------------------------------------------------------------- markdown


def _order(rows: list[dict[str, Any]], mix: str) -> list[dict[str, Any]]:
    return sorted(
        [x for x in rows if x["mix"] == mix], key=lambda x: K.COLLECTIONS.index(x["collection"])
    )


def _verdict_table(rows: list[dict[str, Any]], mix: str) -> list[str]:
    lines = [
        "| collection | r | queries | `w°` 1-NN | best competitor 1-NN | `w°` RR | best "
        "competitor RR | exact-arm ceiling | verdict |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for x in _order(rows, mix):
        for r, cell in sorted(x["cells"].items(), key=lambda kv: int(kv[0])):
            w = cell["per_arm"][K.OURS]
            b1, b2 = cell["best_competitor"]["acc1"][0], cell["best_competitor"]["rr"][0]
            v = cell["verdict"]
            v = f"**{v}**" if v == "kill" else v
            ceil = cell["ceiling"]
            lines.append(
                f"| {x['collection']} | {r} | {int(np.mean(cell['n_queries']))} | "
                f"{AC._fmt(w['acc1'])} | {SHORT[b1]} {AC._fmt(cell['per_arm'][b1]['acc1'])} | "
                f"{AC._fmt(w['rr'])} | {SHORT[b2]} {AC._fmt(cell['per_arm'][b2]['rr'])} | "
                f"{np.mean(ceil):.3f} [{min(ceil):.3f}, {max(ceil):.3f}] | {v} |"
            )
    return lines


def _detail(rows: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for mix in ("pendant", "empirical"):
        for x in _order(rows, mix):
            for r, cell in sorted(x["cells"].items(), key=lambda kv: int(kv[0])):
                extra = ""
                if mix == "empirical":
                    extra = " — realized pendant share " + ", ".join(
                        f"{s:.3f}" for s in cell["realized_pendant_share"] if s is not None
                    )
                lines += [
                    f"#### {mix} {x['collection']} r={r} ({cell['verdict']}){extra}",
                    "",
                    "| arm | 1-NN (BCa) | RR (BCa) | p_Holm 1-NN (word >) | r_rb 1-NN | 1-NN at "
                    "distance 0 | s per cell |",
                    "|---|---|---|---|---|---|---|",
                ]
                for arm, v in cell["per_arm"].items():
                    t = cell["tests"]["acc1"].get(arm)
                    p = f"{t['p_holm']:.3f}" if t else "(word)"
                    e = f"{t['rank_biserial']:+.2f}" if t else ""
                    lines.append(
                        f"| {SHORT.get(arm, arm)} | {AC._fmt(v['acc1'], True)} | "
                        f"{AC._fmt(v['rr'], True)} | {p} | {e} | {v['nn_zero_share']:.3f} | "
                        f"{v['secs']:.1f} |"
                    )
                lines.append("")
    return lines


def render(summary: dict[str, Any]) -> str:
    """``SUMMARY_D.md``."""
    out = [
        "# KNN_2026-10-15 — Design D (catalogue linkage) summary (generated; do not edit)",
        "",
        "Seed means with [min, max] over seeds; BCa intervals and Holm-corrected one-sided "
        "Wilcoxon p-values over seeds are in the detail tables (descriptive at probe scale: with "
        "3 seeds the smallest one-sided p is 0.125). A claim cell (r = 1, 2) is killed when any "
        "competitor's mean 1-NN accuracy is >= the word's; r = 3 carries no claim. Competitors: "
        "the ten §2 arms plus the one-round WL; † the registry WL refines to the stable "
        "partition of catalogue + queries and is degenerate. Exact-arm ceiling = share of "
        "queries isomorphic to no catalogue record. RR = reciprocal of the source's expected "
        "rank.",
        "",
    ]
    for mix in ("pendant", "empirical"):
        h = summary["hypotheses"][mix]
        out.append(
            f"- **{h['hypothesis']}** ({mix}; {', '.join(h['collections'])}): kill "
            f"{'**FIRED**' if h['fired'] else 'not fired'} in "
            f"{len(h['kills'])} of {h['claim_cells']} claim cells"
            + (f" ({', '.join(f'{a} r={b}' for a, b in h['kills'])})" if h["kills"] else "")
            + "; r = 3: "
            + "; ".join(f"{a}: {v}" for a, v in h["r3"])
            + "."
        )
    out += ["", "## H-KNN-D — pendant copies", ""] + _verdict_table(summary["rows"], "pendant")
    out += ["", "## H-KNN-D-mix — C8 empirical edit mix (claim on WD50K only)", ""]
    out += _verdict_table(summary["rows"], "empirical") + [""]
    out += [
        "## Cost (measured; full run extrapolated linearly in S)",
        "",
        "| collection | mix | catalogue | setup s | catalogue fit s (slowest arm) | s per seed "
        "(S = 60) | bipartite pairs/s | n_jobs | full run (S = 200, 27 seeds), min |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for mix in ("pendant", "empirical"):
        for x in _order(summary["rows"], mix):
            c = x["cost"]
            slow = c["secs_fit_slowest"]
            bp = f"{c['bipartite_pairs_per_s']:,.0f}" if c["bipartite_pairs_per_s"] else "–"
            out.append(
                f"| {x['collection']} | {mix} | {c['catalogue']} | {c['secs_setup']:.0f} | "
                f"{c['secs_fit_total']:.0f} ({slow[0]} {slow[1]:.0f}) | {c['secs_per_seed']:.1f} | "
                f"{bp} | {c['n_jobs']} | {c['full_run_minutes']:.0f} |"
            )
    out += ["", "## Per-arm detail", ""] + _detail(summary["rows"])
    return "\n".join(out) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--inputs", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    out = args.out or args.inputs
    jobs = [json.loads(p.read_text()) for p in sorted(args.inputs.glob("D_*.json"))]
    summary = aggregate(jobs)
    K.write_json(out / "summary_d.json", summary)
    (out / "SUMMARY_D.md").write_text(render(summary))
    print(f"wrote {out / 'SUMMARY_D.md'}")


if __name__ == "__main__":
    main()
