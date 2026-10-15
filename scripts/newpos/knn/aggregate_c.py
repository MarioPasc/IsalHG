"""Aggregate the Design-C job JSONs: seed statistics, tests, verdicts (LOG.md §6, §6.1).

Reads every ``C_<collection>_<stratum>_c<c>.json`` under ``--inputs`` and writes
``SUMMARY_C.md`` and ``summary_c.json`` there (or under ``--out``).

Per ``(c, collection, stratum, r)`` cell and arm, over seeds: mean, [min, max]
and a 95 % BCa interval (scipy, 9,999 resamples, ``random_state`` 0) of 1-NN
accuracy and ARI; against each competitor, a one-sided Wilcoxon signed-rank
test of word > competitor over the paired seeds (``zero_method="zsplit"``), Holm
across the eleven competitors, and the rank-biserial correlation. Verdicts
follow §6: a feasible cell (at least 10 available blocks, minimum over seeds)
is killed when any competitor's seed mean is >= the word's on either metric;
an infeasible cell is reported as such and is not a pass. c = 3 is the primary
(§6.1); the registered c = 6 is reported after it with its own verdicts.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
import warnings
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import knn_lib as K  # noqa: E402, N812
from neardup import holm, rank_biserial  # noqa: E402

PRIMARY_C = 3
METRICS: tuple[str, ...] = ("acc1", "ari")
EXTRA: tuple[str, ...] = ("acc5", "nmi", "f1_1", "err_within_share")
STRATUM_ORDER: tuple[str, ...] = ("C-all", "C-int", "C-pend")
HYPOTHESIS = {"C-all": "H-KNN-C", "C-int": "H-KNN-C-int", "C-pend": "(no claim)"}
SHORT = {
    "isal_ow_struct": "w°",
    "nauty_cert": "cert",
    "nauty_cert_rows": "cert rows",
    "fact_rank": "fact list",
    "wl_l1": "WL (registry)†",
    "wl_h1": "WL h=1",
    "netlsd": "NetLSD",
    "hpd_jsd": "HPD",
    "bipartite_ged_assign": "bip. assign",
    "bipartite_ged_path": "bip. path",
    "degree_seq_l1": "degree",
    "size_l1": "size",
}


def bca(values: Sequence[float]) -> tuple[float | None, float | None]:
    """95 % BCa interval of the mean; degenerate samples return the point twice."""
    from scipy.stats import bootstrap

    x = np.asarray(values, dtype=np.float64)
    if len(x) == 0:
        return None, None
    if np.allclose(x, x[0]):
        return float(x[0]), float(x[0])
    if len(x) < 3:
        return None, None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            res = bootstrap(
                (x,),
                np.mean,
                method="BCa",
                n_resamples=9999,
                random_state=0,
                confidence_level=0.95,
            )
        except Exception:  # noqa: BLE001 - a degenerate jackknife is reported as missing
            return None, None
    lo, hi = float(res.confidence_interval.low), float(res.confidence_interval.high)
    return (lo if math.isfinite(lo) else None), (hi if math.isfinite(hi) else None)


def paired_tests(
    word: Sequence[float], competitors: dict[str, Sequence[float]]
) -> dict[str, dict[str, float]]:
    """One-sided Wilcoxon word > competitor over seeds, Holm-corrected, with rank-biserial."""
    from scipy.stats import wilcoxon

    x = np.asarray(word, dtype=np.float64)
    raw: dict[str, float] = {}
    eff: dict[str, float] = {}
    for arm, vals in competitors.items():
        y = np.asarray(vals, dtype=np.float64)
        d = x - y
        if np.all(d == 0):
            raw[arm] = 1.0
        else:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                raw[arm] = float(wilcoxon(x, y, alternative="greater", zero_method="zsplit").pvalue)
        eff[arm] = rank_biserial(x, y)
    adj = holm(raw)
    return {a: {"p_raw": raw[a], "p_holm": adj[a], "rank_biserial": eff[a]} for a in raw}


def load_jobs(inputs: Path) -> list[dict[str, Any]]:
    """Every Design-C job JSON under ``inputs``."""
    return [json.loads(p.read_text()) for p in sorted(inputs.glob("C_*_c*.json"))]


def _seed_values(job: dict[str, Any], r: str, arm: str, metric: str) -> list[float]:
    out = []
    for s in sorted(job["seeds"], key=int):
        cell = job["seeds"][s]["cells"].get(r)
        if cell and arm in cell["arms"] and cell["arms"][arm].get(metric) is not None:
            out.append(float(cell["arms"][arm][metric]))
    return out


def aggregate_cell(job: dict[str, Any], r: str, feasible: bool) -> dict[str, Any]:
    """Statistics, tests and the verdict of one ``(job, r)`` cell."""
    arms = [a for a in K.ARMS_C if _seed_values(job, r, a, "acc1")]
    per_arm: dict[str, dict[str, Any]] = {}
    for arm in arms:
        entry: dict[str, Any] = {}
        for m in (*METRICS, *EXTRA):
            v = _seed_values(job, r, arm, m)
            if not v:
                continue
            lo, hi = bca(v) if m in METRICS else (None, None)
            entry[m] = {
                "mean": float(np.mean(v)),
                "min": min(v),
                "max": max(v),
                "n": len(v),
                "bca": [lo, hi],
                "values": v,
            }
        per_arm[arm] = entry
    tests = {}
    for m in METRICS:
        word = per_arm[K.OURS][m]["values"]
        comps = {
            a: per_arm[a][m]["values"] for a in arms if a in K.COMPETITORS_C and m in per_arm[a]
        }
        tests[m] = paired_tests(word, comps)
    best = {
        m: K.best_competitor(
            {a: {mm: v[mm]["mean"] for mm in v} for a, v in per_arm.items()}, m, K.COMPETITORS_C
        )
        for m in METRICS
    }
    word_mean = {m: per_arm[K.OURS][m]["mean"] for m in METRICS}
    ahead = {m: bool(word_mean[m] > best[m][1]) for m in METRICS}
    verdict = "infeasible" if not feasible else ("pass" if all(ahead.values()) else "kill")
    seeds = [
        job["seeds"][s] for s in sorted(job["seeds"], key=int) if r in job["seeds"][s]["cells"]
    ]
    cells = [s["cells"][r] for s in seeds]
    return {
        "r": int(r),
        "per_arm": per_arm,
        "tests": tests,
        "best_competitor": best,
        "word": word_mean,
        "word_ahead": ahead,
        "verdict": verdict,
        "n_items": [c["n_items"] for c in cells],
        "exact_ceiling": [c["iso_census"]["exact_arm_acc1_ceiling"] for c in cells],
        "cross_source_iso": [c["iso_census"]["cross_class_iso_fraction"] for c in cells],
        "key_disagreements": [c["iso_census"]["key_disagreements"] for c in cells],
        "arms_ge_0.9": [c["ceiling"].get("n_arms_acc1_ge_0.9") for c in cells],
        "word_certified": [c["arms"][K.OURS].get("certified", {}) for c in cells],
        "secs": [c["secs"] for c in cells],
    }


def aggregate(jobs: list[dict[str, Any]]) -> dict[str, Any]:
    """Feasibility, cells and hypothesis verdicts for every ``c``."""
    out: dict[str, Any] = {"by_c": {}}
    for job in jobs:
        c = int(job.get("c", job["config"]["c"]))
        seeds = [job["seeds"][s] for s in sorted(job["seeds"], key=int)]
        avail = [s["n_blocks_available"] for s in seeds]
        feasible = bool(avail) and min(avail) >= job["config"]["min_feasible_blocks"]
        entry = {
            "collection": job["collection"],
            "stratum": job["stratum"],
            "c": c,
            "seeds": [s["seed"] for s in seeds],
            "eligible": job["eligibility"]["n_eligible"],
            "classes_in_graph": job["eligibility"]["n_classes_in_graph"],
            "candidate_block_seeds": job["n_candidate_block_seeds"],
            "blocks_available": avail,
            "blocks_available_min": min(avail) if avail else None,
            "blocks_available_mean": float(np.mean(avail)) if avail else None,
            "feasible": feasible,
            "pool_blocks": [s["n_blocks"] for s in seeds],
            "S": [s["S"] for s in seeds],
            "discarded_blocks": [s["discarded_blocks"] for s in seeds],
            "dropped_members": [len(s["dropped_members"]) for s in seeds],
            "secs_seed": [s["secs_seed"] for s in seeds],
            "secs_setup": job.get("secs_setup"),
            "cells": {},
        }
        rs = sorted({r for s in seeds for r in s["cells"]}, key=int)
        for r in rs:
            entry["cells"][r] = aggregate_cell(job, r, feasible)
        out["by_c"].setdefault(str(c), []).append(entry)
    for c, entries in out["by_c"].items():
        hyps = {}
        for stratum, name in HYPOTHESIS.items():
            rows = [e for e in entries if e["stratum"] == stratum]
            feas = [e for e in rows if e["feasible"]]
            kills = [
                (e["collection"], r)
                for e in feas
                for r, cell in e["cells"].items()
                if cell["verdict"] == "kill"
            ]
            hyps[stratum] = {
                "hypothesis": name,
                "feasible_collections": [e["collection"] for e in feas],
                "infeasible_collections": [e["collection"] for e in rows if not e["feasible"]],
                "kills": kills,
                "fired": bool(kills) if stratum != "C-pend" else None,
            }
        out[f"hypotheses_c{c}"] = hyps
    out["generated"] = time.strftime("%Y-%m-%d %H:%M %Z")
    return out


# --------------------------------------------------------------------------- markdown


def _fmt(v: dict[str, Any] | None, ci: bool = False) -> str:
    if not v:
        return "–"
    s = f"{v['mean']:.3f} [{v['min']:.3f}, {v['max']:.3f}]"
    if ci and v.get("bca") and v["bca"][0] is not None:
        s += f" (BCa {v['bca'][0]:.3f}–{v['bca'][1]:.3f})"
    return s


def _order(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        entries,
        key=lambda e: (STRATUM_ORDER.index(e["stratum"]), K.COLLECTIONS.index(e["collection"])),
    )


def _feasibility_table(entries: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| stratum | collection | eligible / classes | candidate seeds | available blocks min / "
        "mean (per seed) | feasible | pool blocks | realised S | discarded / dropped |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for e in _order(entries):
        lines.append(
            f"| {e['stratum']} | {e['collection']} | {e['eligible']} / {e['classes_in_graph']} | "
            f"{e['candidate_block_seeds']} | {e['blocks_available_min']} / "
            f"{e['blocks_available_mean']:.1f} ({', '.join(map(str, e['blocks_available']))}) | "
            f"{'yes' if e['feasible'] else '**no**'} | {', '.join(map(str, e['pool_blocks']))} | "
            f"{', '.join(map(str, e['S']))} | {sum(e['discarded_blocks'])} / "
            f"{sum(e['dropped_members'])} |"
        )
    return lines


def _verdict_table(entries: list[dict[str, Any]], stratum: str) -> list[str]:
    lines = [
        "| collection | r | N | `w°` 1-NN | best competitor 1-NN | `w°` ARI | best competitor ARI "
        "| verdict |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for e in _order([x for x in entries if x["stratum"] == stratum]):
        for r, cell in sorted(e["cells"].items(), key=lambda kv: int(kv[0])):
            w = cell["per_arm"][K.OURS]
            cols = []
            for m in METRICS:
                name, _ = cell["best_competitor"][m]
                cols += [
                    _fmt(w.get(m)),
                    f"{SHORT.get(name, name)} {_fmt(cell['per_arm'][name].get(m))}",
                ]
            verdict = {"pass": "word ahead", "kill": "**kill**", "infeasible": "infeasible"}[
                cell["verdict"]
            ]
            lines.append(
                f"| {e['collection']} | {r} | {int(np.mean(cell['n_items']))} | "
                + " | ".join(cols)
                + f" | {verdict} |"
            )
    return lines


def _error_table(entries: list[dict[str, Any]]) -> list[str]:
    show = (K.OURS, "bipartite_ged_path", "wl_h1", "nauty_cert_rows")
    lines = [
        "| stratum | collection | r | "
        + " | ".join(f"{SHORT[a]}: 1-NN err / within-block share" for a in show)
        + " |",
        "|---|---|---|" + "---|" * len(show),
    ]
    for e in _order(entries):
        for r, cell in sorted(e["cells"].items(), key=lambda kv: int(kv[0])):
            cols = []
            for a in show:
                v = cell["per_arm"].get(a, {})
                err = 1 - v["acc1"]["mean"] if "acc1" in v else float("nan")
                share = (
                    v.get("err_within_share", {}).get("mean") if v.get("err_within_share") else None
                )
                cols.append(f"{err:.3f} / {share:.2f}" if share is not None else f"{err:.3f} / –")
            lines.append(f"| {e['stratum']} | {e['collection']} | {r} | " + " | ".join(cols) + " |")
    return lines


def _diag_table(entries: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| stratum | collection | r | exact-arm ceiling | cross-source iso | arms >= 0.9 | "
        "`w°` cert. ratio median / max / over | seconds per seed |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for e in _order(entries):
        for r, cell in sorted(e["cells"].items(), key=lambda kv: int(kv[0])):
            certs = [c for c in cell["word_certified"] if c and c.get("ratio_median") is not None]
            cert = (
                f"{np.mean([c['ratio_median'] for c in certs]):.2f} / "
                f"{max(c['ratio_max'] for c in certs):.2f} / "
                f"{sum(c['n_over_bound'] for c in certs)} of {sum(c['n_certified'] for c in certs)}"
                if certs
                else "–"
            )
            lines.append(
                f"| {e['stratum']} | {e['collection']} | {r} | "
                f"{np.mean(cell['exact_ceiling']):.3f} | {np.mean(cell['cross_source_iso']):.3f} | "
                f"{', '.join(str(x) for x in cell['arms_ge_0.9'])} | {cert} | "
                f"{np.mean(cell['secs']):.1f} |"
            )
    return lines


def _detail(entries: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for e in _order(entries):
        for r, cell in sorted(e["cells"].items(), key=lambda kv: int(kv[0])):
            lines += [
                f"#### {e['stratum']} {e['collection']} r={r} ({cell['verdict']})",
                "",
                "| arm | 1-NN | ARI | p_Holm 1-NN / ARI (word >) | r_rb 1-NN / ARI | within-block "
                "err share |",
                "|---|---|---|---|---|---|",
            ]
            for arm, v in cell["per_arm"].items():
                t1 = cell["tests"]["acc1"].get(arm)
                t2 = cell["tests"]["ari"].get(arm)
                ptxt = f"{t1['p_holm']:.3f} / {t2['p_holm']:.3f}" if t1 and t2 else "(word)"
                rtxt = (
                    f"{t1['rank_biserial']:+.2f} / {t2['rank_biserial']:+.2f}" if t1 and t2 else ""
                )
                share = v.get("err_within_share")
                stxt = f"{share['mean']:.2f}" if share else "–"
                lines.append(
                    f"| {SHORT.get(arm, arm)} | {_fmt(v.get('acc1'), True)} | "
                    f"{_fmt(v.get('ari'), True)} | {ptxt} | {rtxt} | {stxt} |"
                )
            lines.append("")
    return lines


def render(summary: dict[str, Any]) -> str:
    """``SUMMARY_C.md``: primary c = 3 first, then the registered c = 6."""
    out = [
        "# KNN_2026-10-15 — Design C (look-alike blocks) summary (generated; do not edit)",
        "",
        "Seed means with [min, max] over seeds; BCa intervals and Holm-corrected one-sided "
        "Wilcoxon p-values over seeds are in the detail tables (at probe scale, 3 seeds, they are "
        "descriptive: the smallest one-sided Wilcoxon p with 3 pairs is 0.125). A feasible cell is "
        "killed when any competitor's mean is >= the word's on 1-NN or ARI. Competitors: the ten "
        "§2 arms plus the one-round WL; † the registry WL refines to the stable partition of the "
        "pool and is degenerate here (distance n_i + n_j).",
        "",
    ]
    cs = sorted(summary["by_c"], key=lambda c: (int(c) != PRIMARY_C, int(c)))
    for c in cs:
        entries = summary["by_c"][c]
        role = "primary (LOG.md §6.1)" if int(c) == PRIMARY_C else "secondary (registered c = 6)"
        out += [f"## c = {c} — {role}", ""]
        hyps = summary[f"hypotheses_c{c}"]
        for stratum in STRATUM_ORDER:
            h = hyps.get(stratum)
            if not h:
                continue
            fired = {True: "**FIRED**", False: "not fired", None: "—"}[h["fired"]]
            out.append(
                f"- **{h['hypothesis']}** ({stratum}): kill {fired}; feasible: "
                f"{', '.join(h['feasible_collections']) or 'none'}; infeasible: "
                f"{', '.join(h['infeasible_collections']) or 'none'}; killed cells: "
                f"{', '.join(f'{a} r={b}' for a, b in h['kills']) or 'none'}."
            )
        out += [
            "",
            "### Feasibility (available blocks = disjoint blocks of the exhaustive draw)",
            "",
        ]
        out += _feasibility_table(entries) + [""]
        for stratum in STRATUM_ORDER:
            out += [f"### {HYPOTHESIS[stratum]} — {stratum}", ""]
            out += _verdict_table(entries, stratum) + [""]
        out += ["### Where the 1-NN errors land (share inside the query's own block)", ""]
        out += _error_table(entries) + [""]
        out += ["### Diagnostics", ""] + _diag_table(entries) + [""]
        out += ["### Per-arm detail", ""] + _detail(entries)
    return "\n".join(out) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--inputs", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    out = args.out or args.inputs
    summary = aggregate(load_jobs(args.inputs))
    K.write_json(out / "summary_c.json", summary)
    (out / "SUMMARY_C.md").write_text(render(summary))
    print(f"wrote {out / 'SUMMARY_C.md'}")


if __name__ == "__main__":
    main()
