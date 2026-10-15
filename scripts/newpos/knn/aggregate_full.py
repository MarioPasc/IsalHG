"""Aggregate the KNN_2026-10-15 full run (LOG.md §8): statistics, tests, a verdict per hypothesis.

Reads the unit directories written by ``full_run.py`` under ``--root`` (default
``<OUT_ROOT>/full``; any path component named ``_smoke`` is skipped) and writes
``FULL_SUMMARY.md``, ``FULL_DETAIL.md`` and ``full_summary.json`` there.

Cells. A cell is one ``(design, condition or stratum, c, collection, r)``; its
series is the per-seed value of every arm on every metric. Per arm and metric:
mean, [min, max] and a 95 % BCa interval over seeds (scipy, 9,999 resamples,
``random_state`` 0). Against each verdict competitor (the cell's recorded
``competitors``: the eleven of §6 with the symmetric-min edit path, LOG.md §7.1
and §8), one-sided Wilcoxon signed-rank tests over the paired seeds
(``zero_method="zsplit"``) in both directions (word > competitor, competitor >
word), each family Holm-corrected over the eleven competitors, with the
rank-biserial correlation. The as-run edit path is a reported row: it is
tested against the word alone (raw p) and enters no family and no verdict.

Verdicts, exactly as registered (§§3, 6, 6.1, 7, 7.1, 8). A claim cell is
killed when any verdict competitor's seed mean is >= the word's on any of the
hypothesis's metrics; an infeasible Design-C cell (fewer than 10 available
blocks at some seed) is reported as infeasible and is not a pass. Cells outside
a claim are reported with their own verdict and no claim.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import aggregate_c as AC  # noqa: E402, N812
import knn_lib as K  # noqa: E402, N812

SEEDS_FULL = 27
ALPHA = 0.05
SHORT: dict[str, str] = {
    "isal_ow_struct": "w°",
    "nauty_cert": "cert",
    "nauty_cert_rows": "cert rows",
    "fact_rank": "fact list",
    "wl_l1": "WL (registry)†",
    "wl_h1": "WL h=1",
    "netlsd": "NetLSD",
    "hpd_jsd": "HPD",
    "bipartite_ged_assign": "bip. assign",
    "bipartite_ged_path_sym": "bip. path (sym-min)",
    "bipartite_ged_path": "bip. path (as run)‡",
    "degree_seq_l1": "degree",
    "size_l1": "size",
}
ARM_ORDER: tuple[str, ...] = (*K.ARMS_FULL,)
COLLECTION_ORDER = {c: i for i, c in enumerate(K.COLLECTIONS)}


@dataclass(frozen=True)
class Hypothesis:
    """One registered hypothesis: which cells it claims and on which metrics."""

    name: str
    title: str
    metrics: tuple[str, ...]
    extra: tuple[str, ...]


HYPOTHESES: dict[str, Hypothesis] = {
    "H-KNN-A": Hypothesis(
        "H-KNN-A", "real NDC lineages (§3)", ("acc1", "ari"), ("acc5", "f1_1", "nmi")
    ),
    "H-KNN-B": Hypothesis(
        "H-KNN-B", "partial copies, pendant removals (§3)", ("acc1", "ari"), ("acc5", "f1_1", "nmi")
    ),
    "H-KNN-mix": Hypothesis(
        "H-KNN-mix", "partial copies, C8 edit mix, WD50K (§3)", ("acc1",), ("ari", "acc5", "nmi")
    ),
    "H-KNN-C": Hypothesis(
        "H-KNN-C",
        "look-alike blocks, C-all, c = 3 (§6, §6.1)",
        ("acc1", "ari"),
        ("acc5", "nmi", "err_within_share"),
    ),
    "H-KNN-C-int": Hypothesis(
        "H-KNN-C-int",
        "look-alike blocks, C-int, c = 3 (§6, §6.1)",
        ("acc1", "ari"),
        ("acc5", "nmi", "err_within_share"),
    ),
    "C-pend": Hypothesis(
        "C-pend", "look-alike blocks, C-pend, c = 3 (no claim)", ("acc1", "ari"), ("acc5", "nmi")
    ),
    "H-KNN-C@c6": Hypothesis(
        "H-KNN-C@c6",
        "C-all at the registered c = 6 (secondary, §6.1)",
        ("acc1", "ari"),
        ("acc5", "nmi", "err_within_share"),
    ),
    "H-KNN-C-int@c6": Hypothesis(
        "H-KNN-C-int@c6",
        "C-int at the registered c = 6 (secondary, §6.1)",
        ("acc1", "ari"),
        ("acc5", "nmi", "err_within_share"),
    ),
    "C-pend@c6": Hypothesis(
        "C-pend@c6", "C-pend at c = 6 (no claim)", ("acc1", "ari"), ("acc5", "nmi")
    ),
    "H-KNN-D": Hypothesis(
        "H-KNN-D",
        "catalogue linkage, pendant copies (§7, §7.1)",
        ("acc1",),
        ("rr", "nn_zero_share"),
    ),
    "H-KNN-D-mix": Hypothesis(
        "H-KNN-D-mix",
        "catalogue linkage, C8 edit mix, WD50K (§7, §7.1)",
        ("acc1",),
        ("rr", "nn_zero_share"),
    ),
}


@dataclass
class Series:
    """The per-seed values of one cell, before aggregation."""

    cell_id: str
    design: str
    condition: str
    c: int | None
    collection: str
    r: int | None
    hypothesis: str
    claim: bool
    competitors: tuple[str, ...]
    seeds: list[int] = field(default_factory=list)
    values: dict[str, dict[str, list[float | None]]] = field(default_factory=dict)
    diag: dict[str, list[Any]] = field(default_factory=lambda: defaultdict(list))
    feasible: bool | None = None
    #: Per arm: per-seed share of queries whose own class is strictly nearer / tied, and the
    #: pooled nearest same-class and other-class distances (memory only; quantiles are kept).
    mech: dict[str, dict[str, list[Any]]] = field(default_factory=dict)
    #: Per arm: the per-seed Prop. 6.1 certificate census of the PAM clusters.
    cert: dict[str, list[dict[str, Any]]] = field(default_factory=dict)

    def add(self, seed: int, arms: dict[str, dict[str, Any]], metrics: Sequence[str]) -> None:
        """Append one seed's arm values (``None`` where an arm lacks a metric)."""
        self.seeds.append(seed)
        n = len(self.seeds)
        for arm, res in arms.items():
            slot = self.values.setdefault(arm, {})
            for m in metrics:
                col = slot.setdefault(m, [None] * (n - 1))
                v = res.get(m)
                col.append(None if v is None else float(v))
            self._add_mech(arm, res)
            if res.get("certified"):
                self.cert.setdefault(arm, []).append(res["certified"])
        for slot in self.values.values():
            for col in slot.values():
                col.extend([None] * (n - len(col)))

    def _add_mech(self, arm: str, res: dict[str, Any]) -> None:
        same = res.get("nn_same", res.get("d_source"))
        other = res.get("nn_other", res.get("d_other"))
        if same is None or other is None:
            return
        a = np.array([np.inf if x is None else x for x in same], dtype=float)
        b = np.array([np.inf if x is None else x for x in other], dtype=float)
        slot = self.mech.setdefault(arm, {"closer": [], "tie": [], "same": [], "other": []})
        slot["closer"].append(float((a < b).mean()) if len(a) else float("nan"))
        slot["tie"].append(float((a == b).mean()) if len(a) else float("nan"))
        slot["same"].append(a[np.isfinite(a)].astype(np.float32))
        slot["other"].append(b[np.isfinite(b)].astype(np.float32))


# --------------------------------------------------------------------------- loading


def _skip(path: Path) -> bool:
    return "_smoke" in path.parts


def _cell_metrics(design: str) -> tuple[str, ...]:
    if design == "D":
        return ("acc1", "rr", "nn_zero_share")
    return ("acc1", "acc5", "f1_1", "ari", "nmi", "err_within_share")


def load_ab(root: Path) -> dict[str, Series]:
    """Designs A (seeded and full) and B (pendant and mix) from their cell files."""
    out: dict[str, Series] = {}
    files = sorted(
        p
        for p in root.glob("*/cells/*.json")
        if not _skip(p) and p.parts[-3].startswith(("A_", "B"))
    )
    for path in files:
        p = json.loads(path.read_text())
        design = p["design"]
        if design == "B":
            cond = "pendant" if p["condition"] == "pendant" else "mix"
            cid = f"B/{cond}/{p['collection']}/r{p['r']}"
            hyp = "H-KNN-B" if cond == "pendant" else "H-KNN-mix"
            claim = cond == "pendant" or p["collection"] in ("wd50k66", "wd50k100")
            r = int(p["r"])
        else:
            cond, r = "lineage", None
            cid = f"{design}/lineage/{p['collection']}"
            hyp, claim = ("H-KNN-A", True) if design == "A" else ("Afull", False)
        # Designs A and B were registered with ten competitors: one-round WL is an added,
        # reported row there and stays outside the kill and the Holm family (coordinator
        # ruling, 2026-10-15); C and D registered it.
        comps = tuple(a for a in p["competitors"] if a != K.WL_H1)
        s = out.get(cid) or Series(cid, design, cond, None, p["collection"], r, hyp, claim, comps)
        out[cid] = s
        s.add(int(p["seed"]) if p["seed"] is not None else 0, p["arms"], _cell_metrics(design))
        s.diag["n_items"].append(p["n_items"])
        s.diag["exact_ceiling"].append(p["iso_census"]["exact_arm_acc1_ceiling"])
        s.diag["cross_class_iso"].append(p["iso_census"]["cross_class_iso_fraction"])
        s.diag["key_disagreements"].append(p["iso_census"]["key_disagreements"])
        s.diag["secs"].append(p["secs_cell"])
        s.diag["S"].append(p.get("S"))
        if p.get("copies"):
            s.diag["realized_pendant_share"].append(p["copies"]["realized_pendant_share"])
        cert = p["arms"].get(K.OURS, {}).get("certified")
        if cert:
            s.diag["word_certified"].append(cert)
    return out


def load_c(root: Path) -> dict[str, Series]:
    """Design C from its job files (feasibility = minimum over seeds of available blocks)."""
    out: dict[str, Series] = {}
    for path in sorted(root.glob("C*_*/C_*_c*.json")):
        if _skip(path):
            continue
        job = json.loads(path.read_text())
        c = int(job["c"])
        stratum = job["stratum"]
        seeds = sorted(job["seeds"], key=int)
        avail = [job["seeds"][s]["n_blocks_available"] for s in seeds]
        feasible = bool(avail) and min(avail) >= job["config"]["min_feasible_blocks"]
        base = {"C-all": "H-KNN-C", "C-int": "H-KNN-C-int", "C-pend": "C-pend"}[stratum]
        hyp = base if c == 3 else f"{base}@c6"
        claim = stratum != "C-pend"
        for s in seeds:
            seed = job["seeds"][s]
            for r, cell in seed["cells"].items():
                cid = f"C/{stratum}/c{c}/{job['collection']}/r{r}"
                ser = out.get(cid) or Series(
                    cid,
                    "C",
                    stratum,
                    c,
                    job["collection"],
                    int(r),
                    hyp,
                    claim,
                    tuple(job["config"]["competitors"]),
                    feasible=feasible,
                )
                out[cid] = ser
                ser.add(int(s), cell["arms"], _cell_metrics("C"))
                ser.diag["n_items"].append(cell["n_items"])
                ser.diag["S"].append(cell["S"])
                ser.diag["exact_ceiling"].append(cell["iso_census"]["exact_arm_acc1_ceiling"])
                ser.diag["cross_class_iso"].append(cell["iso_census"]["cross_class_iso_fraction"])
                ser.diag["key_disagreements"].append(cell["iso_census"]["key_disagreements"])
                ser.diag["secs"].append(cell["secs"])
                ser.diag["blocks_available"].append(seed["n_blocks_available"])
                ser.diag["pool_blocks"].append(seed["n_blocks"])
                cert = cell["arms"].get(K.OURS, {}).get("certified")
                if cert:
                    ser.diag["word_certified"].append(cert)
        # A stratum whose pool never reached two blocks has no cells; keep it visible.
        if not any(seed["cells"] for seed in job["seeds"].values()):
            cid = f"C/{stratum}/c{c}/{job['collection']}/none"
            out[cid] = Series(
                cid,
                "C",
                stratum,
                c,
                job["collection"],
                None,
                hyp,
                claim,
                tuple(job["config"]["competitors"]),
                feasible=feasible,
            )
            out[cid].diag["blocks_available"] = avail
    return out


def load_d(root: Path) -> dict[str, Series]:
    """Design D from its job files."""
    out: dict[str, Series] = {}
    for path in sorted(root.glob("D_*/D_*.json")):
        if _skip(path):
            continue
        job = json.loads(path.read_text())
        mix = job["mix"]
        hyp = "H-KNN-D" if mix == "pendant" else "H-KNN-D-mix"
        for s in sorted(job["seeds"], key=int):
            seed = job["seeds"][s]
            for r, cell in seed["cells"].items():
                cid = f"D/{mix}/{job['collection']}/r{r}"
                ser = out.get(cid) or Series(
                    cid,
                    "D",
                    mix,
                    3,
                    job["collection"],
                    int(r),
                    hyp,
                    int(r) in (1, 2),
                    tuple(job["config"]["competitors"]),
                )
                out[cid] = ser
                ser.add(int(s), cell["arms"], _cell_metrics("D"))
                ser.diag["n_items"].append(cell["n_queries"])
                ser.diag["S"].append(seed["S"])
                ser.diag["exact_ceiling"].append(cell["exact_arm_ceiling"])
                ser.diag["n_iso_to_catalogue"].append(cell["n_iso_to_catalogue"])
                ser.diag["realized_pendant_share"].append(cell["copies"]["realized_pendant_share"])
                ser.diag["secs"].append(cell.get("secs"))
                ser.diag["catalogue"].append(job["catalogue"]["n_catalogue"])
    return out


# --------------------------------------------------------------------------- statistics


def _stat(values: Sequence[float | None], with_ci: bool) -> dict[str, Any] | None:
    v = [x for x in values if x is not None]
    if not v:
        return None
    lo, hi = AC.bca(v) if with_ci else (None, None)
    return {
        "mean": float(np.mean(v)),
        "min": float(min(v)),
        "max": float(max(v)),
        "n": len(v),
        "bca": [lo, hi],
        "values": [None if x is None else round(x, 6) for x in values],
    }


def _paired(a: Sequence[float | None], b: Sequence[float | None]) -> tuple[np.ndarray, np.ndarray]:
    keep = [i for i, (x, y) in enumerate(zip(a, b, strict=True)) if x is not None and y is not None]
    return np.array([a[i] for i in keep], float), np.array([b[i] for i in keep], float)


def _one_sided(x: np.ndarray, y: np.ndarray) -> float:
    """p of the one-sided Wilcoxon x > y (``zsplit``); 1 when every difference is 0."""
    import warnings

    from scipy.stats import wilcoxon

    if len(x) == 0 or np.all(x == y):
        return 1.0
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return float(wilcoxon(x, y, alternative="greater", zero_method="zsplit").pvalue)


def tests_for(
    word: Sequence[float | None], comps: dict[str, Sequence[float | None]]
) -> dict[str, dict[str, float]]:
    """Both one-sided Holm families and the rank-biserial correlation, per competitor."""
    from neardup import holm, rank_biserial

    fwd: dict[str, float] = {}
    rev: dict[str, float] = {}
    eff: dict[str, float] = {}
    for arm, vals in comps.items():
        x, y = _paired(word, vals)
        fwd[arm] = _one_sided(x, y)
        rev[arm] = _one_sided(y, x)
        eff[arm] = rank_biserial(x, y) if len(x) else 0.0
    hf, hr = holm(fwd), holm(rev)
    return {
        a: {
            "p_raw": fwd[a],
            "p_holm": hf[a],
            "p_raw_rev": rev[a],
            "p_holm_rev": hr[a],
            "rank_biserial": eff[a],
        }
        for a in comps
    }


def _diff(word: Sequence[float | None], other: Sequence[float | None]) -> dict[str, Any] | None:
    x, y = _paired(word, other)
    if not len(x):
        return None
    d = x - y
    lo, hi = AC.bca(d.tolist())
    return {"mean": float(d.mean()), "bca": [lo, hi], "n": int(len(d))}


def aggregate_series(s: Series) -> dict[str, Any]:
    """Statistics, tests and the verdict of one cell."""
    hyp = HYPOTHESES.get(s.hypothesis, Hypothesis(s.hypothesis, "", ("acc1",), ("acc5",)))
    metrics = hyp.metrics
    arms = sorted(s.values, key=lambda a: ARM_ORDER.index(a) if a in ARM_ORDER else 99)
    per_arm = {
        a: {
            m: st
            for m in (*metrics, *hyp.extra)
            if (st := _stat(s.values[a].get(m, []), with_ci=m in (*metrics, "rr", "ari", "acc1")))
        }
        for a in arms
    }
    tests: dict[str, Any] = {}
    best: dict[str, Any] = {}
    best_any: dict[str, Any] = {}
    diffs: dict[str, Any] = {}
    # Reported rows outside the family and the verdict: the as-run edit path everywhere,
    # one-round WL in Designs A and B.
    added = [a for a in (K.PATH_ASRUN, K.WL_H1) if a in s.values and a not in s.competitors]
    added_rows: dict[str, dict[str, Any]] = {a: {} for a in added}
    word_vals = s.values.get(K.OURS, {})
    for m in metrics:
        comps = {a: s.values[a][m] for a in s.competitors if a in s.values and m in s.values[a]}
        if K.OURS not in s.values or not comps:
            continue
        tests[m] = tests_for(word_vals[m], comps)
        means = {a: per_arm[a][m]["mean"] for a in comps if m in per_arm[a]}
        name = max(means, key=lambda a: means[a])
        best[m] = {"arm": name, "mean": means[name]}
        verdict_arms = {**means, K.OURS: per_arm[K.OURS][m]["mean"]}
        top = max(verdict_arms, key=lambda a: verdict_arms[a])
        best_any[m] = {"arm": top, "mean": verdict_arms[top]}
        diffs[m] = _diff(word_vals[m], s.values[name][m])
        for a in added:
            if m not in s.values[a] or m not in per_arm[a]:
                continue
            x, y = _paired(word_vals[m], s.values[a][m])
            added_rows[a][m] = {
                "mean": per_arm[a][m]["mean"],
                "p_raw_word_greater": _one_sided(x, y),
                "ge_word": bool(per_arm[a][m]["mean"] >= per_arm[K.OURS][m]["mean"]),
            }
    word_mean = {m: per_arm[K.OURS][m]["mean"] for m in metrics if m in per_arm.get(K.OURS, {})}
    killers = {
        m: sorted(
            a
            for a in s.competitors
            if m in per_arm.get(a, {}) and per_arm[a][m]["mean"] >= word_mean.get(m, np.inf)
        )
        for m in metrics
    }
    ahead = {m: not killers[m] for m in metrics}
    significant = {
        m: bool(tests.get(m)) and all(t["p_holm"] < ALPHA for t in tests[m].values())
        for m in metrics
    }
    if s.feasible is False:
        verdict = "infeasible"
    elif not word_mean:
        verdict = "no data"
    elif s.claim:
        verdict = "word ahead" if all(ahead.values()) else "kill"
    else:
        verdict = "word ahead (no claim)" if all(ahead.values()) else "competitor ahead (no claim)"
    diag = {k: list(v) for k, v in s.diag.items()}
    mechanism = {arm: _mechanism(slot) for arm, slot in s.mech.items()}
    certified = {arm: _certified(rows) for arm, rows in s.cert.items()}
    return {
        "id": s.cell_id,
        "design": s.design,
        "condition": s.condition,
        "c": s.c,
        "collection": s.collection,
        "r": s.r,
        "hypothesis": s.hypothesis,
        "claim": s.claim,
        "feasible": s.feasible,
        "competitors": list(s.competitors),
        "seeds": s.seeds,
        "n_seeds": len(s.seeds),
        # An infeasible Design-C cell can hold fewer seeds: a seed whose pool held fewer than
        # two blocks has no cell. It carries no verdict either way.
        "complete": len(s.seeds) >= SEEDS_FULL or s.design == "Afull" or s.feasible is False,
        "metrics": list(metrics),
        "per_arm": per_arm,
        "tests": tests,
        "best_competitor": best,
        "best_arm_overall": best_any,
        "diff_word_minus_best": diffs,
        "added_rows": added_rows,
        "as_run_path": added_rows.get(K.PATH_ASRUN, {}),
        "word": word_mean,
        "killers": killers,
        "word_ahead": ahead,
        "word_significant_vs_all": significant,
        "verdict": verdict,
        "diag": diag,
        "mechanism": mechanism,
        "certified": certified,
    }


def _certified(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Prop. 6.1 census over seeds: per-seed median ratios, the largest ratio, the counts."""
    med = [r["ratio_median"] for r in rows if r.get("ratio_median") is not None]
    mx = [r["ratio_max"] for r in rows if r.get("ratio_max") is not None]
    return {
        "ratio_median_per_seed": med,
        "ratio_median_mean": float(np.mean(med)) if med else None,
        "ratio_median_min": float(min(med)) if med else None,
        "ratio_median_max": float(max(med)) if med else None,
        "ratio_max": float(max(mx)) if mx else None,
        "n_over_bound": int(sum(r.get("n_over_bound", 0) for r in rows)),
        "n_1medoid_over_bound": int(sum(r.get("n_1medoid_over_bound", 0) for r in rows)),
        "n_certified": int(sum(r.get("n_certified", 0) for r in rows)),
        "n_lb_zero": int(sum(r.get("n_lb_zero", 0) for r in rows)),
        "n_singletons": int(sum(r.get("n_singletons", 0) for r in rows)),
    }


def _mechanism(slot: dict[str, list[Any]]) -> dict[str, Any]:
    """Own-class-strictly-nearer share over seeds and the pooled distance quantiles.

    For A / B / C the own class is the query's siblings (nearest same-class
    candidate vs nearest other-class candidate); for D it is the source record
    (distance to the source vs the nearest other catalogue record).
    """
    same = np.concatenate(slot["same"]) if slot["same"] else np.zeros(0)
    other = np.concatenate(slot["other"]) if slot["other"] else np.zeros(0)

    def q(x: np.ndarray) -> list[float] | None:
        return [float(v) for v in np.quantile(x, (0.25, 0.5, 0.75))] if len(x) else None

    return {
        "own_strictly_nearer": _stat(slot["closer"], with_ci=True),
        "tie": _stat(slot["tie"], with_ci=False),
        "own_quartiles": q(same),
        "other_quartiles": q(other),
        "n_queries": int(len(same)),
    }


def hypothesis_verdicts(cells: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Per hypothesis: claim cells, kills (with the killing competitors) and the verdict."""
    out: dict[str, Any] = {}
    for name, hyp in HYPOTHESES.items():
        mine = [c for c in cells.values() if c["hypothesis"] == name]
        claim = [c for c in mine if c["claim"] and c["verdict"] in ("word ahead", "kill")]
        kills = [
            {"cell": c["id"], "killers": {m: k for m, k in c["killers"].items() if k}}
            for c in claim
            if c["verdict"] == "kill"
        ]
        infeasible = sorted({c["collection"] for c in mine if c["verdict"] == "infeasible"})
        nonclaim = [{"cell": c["id"], "verdict": c["verdict"]} for c in mine if not c["claim"]]
        if name in ("C-pend", "C-pend@c6"):
            fired: bool | None = None
        else:
            fired = bool(kills) if claim else None
        out[name] = {
            "title": hyp.title,
            "metrics": list(hyp.metrics),
            "n_cells": len(mine),
            "n_claim_cells": len(claim),
            "n_kills": len(kills),
            "kills": kills,
            "infeasible_collections": infeasible,
            "non_claim_cells": nonclaim,
            "fired": fired,
            "complete": all(c["complete"] for c in mine),
            "verdict": (
                "no claim"
                if fired is None and name.startswith("C-pend")
                else "untestable"
                if fired is None
                else "killed"
                if fired
                else "survives"
            ),
        }
    return out


# --------------------------------------------------------------------------- markdown


def _f(x: float | None, nd: int = 3) -> str:
    return "–" if x is None else f"{x:.{nd}f}"


def _ci(st: dict[str, Any] | None) -> str:
    if not st:
        return "–"
    lo, hi = st["bca"]
    ci = f" [{_f(lo)}, {_f(hi)}]" if lo is not None else ""
    return f"{st['mean']:.3f}{ci}"


def _p(p: float | None) -> str:
    if p is None:
        return "–"
    return f"{p:.1e}" if p < 1e-3 else f"{p:.3f}"


def _order_key(c: dict[str, Any]) -> tuple[Any, ...]:
    return (
        COLLECTION_ORDER.get(c["collection"], 9),
        c["c"] or 0,
        c["r"] if c["r"] is not None else 0,
    )


def _verdict_table(cells: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| collection | r | N items | metric | `w°` mean [BCa] | best competitor mean [BCa] | "
        "Δ `w°` − best [BCa] | p_Holm `w°` > best / best > `w°` | r_rb | max p_Holm over the "
        "family | added rows (outside the verdict) | verdict |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for c in sorted(cells, key=_order_key):
        if c["verdict"] in ("infeasible", "no data") and not c["word"]:
            lines.append(
                f"| {c['collection']} | – | – | – | – | – | – | – | – | – | – | {c['verdict']} |"
            )
            continue
        for m in c["metrics"]:
            if m not in c["best_competitor"]:
                continue
            b = c["best_competitor"][m]["arm"]
            t = c["tests"][m][b]
            d = c["diff_word_minus_best"].get(m)
            added = "; ".join(
                f"{SHORT.get(a, a)} {_f(row[m]['mean'])}{' (≥ w°)' if row[m]['ge_word'] else ''}"
                for a, row in c["added_rows"].items()
                if m in row
            )
            pmax = max(x["p_holm"] for x in c["tests"][m].values())
            verdict = c["verdict"]
            if verdict == "kill":
                verdict = f"**kill** ({', '.join(SHORT.get(a, a) for a in c['killers'][m]) or '–'})"
            n_items = int(np.mean(c["diag"]["n_items"])) if c["diag"].get("n_items") else 0
            lines.append(
                f"| {c['collection']} | {c['r'] if c['r'] is not None else '–'} | {n_items} | "
                f"{m} | {_ci(c['per_arm'][K.OURS].get(m))} | {SHORT.get(b, b)} "
                f"{_ci(c['per_arm'][b].get(m))} | {_ci(d) if d else '–'} | "
                f"{_p(t['p_holm'])} / {_p(t['p_holm_rev'])} | {t['rank_biserial']:+.2f} | "
                f"{_p(pmax)} | {added or '–'} | {verdict} |"
            )
    return lines


def _summary_table(hyps: dict[str, Any]) -> list[str]:
    lines = [
        "| hypothesis | cells | claim cells | kills | infeasible | verdict | complete (27 seeds) |",
        "|---|---|---|---|---|---|---|",
    ]
    for name, h in hyps.items():
        if not h["n_cells"]:
            continue
        lines.append(
            f"| {name} — {h['title']} | {h['n_cells']} | {h['n_claim_cells']} | {h['n_kills']} | "
            f"{', '.join(h['infeasible_collections']) or '–'} | **{h['verdict']}** | "
            f"{'yes' if h['complete'] else '**no**'} |"
        )
    return lines


def _diag_table(cells: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| cell | seeds | N items | exact-arm ceiling | x-class iso | realised pendant share | "
        "blocks available min (C) | catalogue (D) | s per seed-cell |",
        "|---|---|---|---|---|---|---|---|---|",
    ]

    def mean(xs: list[Any], nd: int = 3) -> str:
        v = [x for x in xs if x is not None]
        return _f(float(np.mean(v)), nd) if v else "–"

    for c in cells:
        d = c["diag"]
        blocks = d.get("blocks_available")
        lines.append(
            f"| `{c['id']}` | {c['n_seeds']} | {mean(d.get('n_items', []), 0)} | "
            f"{mean(d.get('exact_ceiling', []))} | {mean(d.get('cross_class_iso', []))} | "
            f"{mean(d.get('realized_pendant_share', []))} | {min(blocks) if blocks else '–'} | "
            f"{d['catalogue'][0] if d.get('catalogue') else '–'} | {mean(d.get('secs', []), 1)} |"
        )
    return lines


def render(summary: dict[str, Any]) -> str:
    """FULL_SUMMARY.md: the verdict overview, one verdict table per hypothesis, diagnostics."""
    cells = summary["cells"]
    hyps = summary["hypotheses"]
    out = [
        "# KNN_2026-10-15 full run — summary (generated by `aggregate_full.py`; do not edit)",
        "",
        f"Generated {summary['generated']}. Root: `{summary['root']}`. Seeds 0–26 per cell "
        "(Afull is deterministic: one evaluation). Design parameters as registered (LOG.md §8): "
        "A L = 30; B S = 200, c = 6, r ∈ {1, 2, 3}; mix on WD50K; C c = 3 (primary) and c = 6 "
        "(secondary), S target 60; D S = 200, c = 3.",
        "",
        "**Reading.** Point values are means over seeds with 95 % BCa intervals (9,999 "
        "resamples). The bipartite edit path is read as the symmetric min min(d(a, b), d(b, a)), "
        "the orientation-free symmetrization of the raw cost (§7.1, §8). The verdict "
        "competitors are each design's registered ones: the ten of §2 for Designs A and B (and "
        "the mix condition), those ten plus one-round WL for Designs C and D (§6, §7). A claim "
        "cell is **killed** when any verdict competitor's seed mean is ≥ the word's on any of "
        "the hypothesis's metrics (the registered kill; the tests do not change it). p_Holm: "
        "one-sided paired Wilcoxon over seeds (zsplit), Holm over the design's verdict "
        "competitors, in each direction; r_rb: rank-biserial of `w°` − best. Added rows, "
        "outside every family and verdict: ‡ the as-run edit-path orientation (every design) "
        "and § one-round WL in Designs A and B; '(≥ w°)' marks a cell where that row alone "
        "would have reached the word. † the registry WL refines to the union's stable partition "
        "and is degenerate on copy sets (LOG.md §5.1).",
        "",
        "## Verdicts",
        "",
        *_summary_table(hyps),
        "",
        *_added_row_flags(cells),
    ]
    for name, h in hyps.items():
        mine = [c for c in cells.values() if c["hypothesis"] == name]
        if not mine:
            continue
        out += [f"## {name} — {h['title']}", ""]
        if h["kills"]:
            out.append(
                "Killed in: "
                + "; ".join(
                    f"`{k['cell']}` by "
                    + ", ".join(
                        f"{m}: {', '.join(SHORT.get(a, a) for a in arms)}"
                        for m, arms in k["killers"].items()
                    )
                    for k in h["kills"]
                )
                + "."
            )
            out.append("")
        out += _verdict_table(mine) + [""]
    ref = [c for c in cells.values() if c["design"] == "Afull"]
    if ref:
        out += ["## Design A reference — every lineage with >= 3 versions (no clustering)", ""]
        out += _verdict_table(ref) + [""]
    out += ["## Diagnostics (means over seeds)", "", *_diag_table(list(cells.values())), ""]
    out += _mechanism_section(list(cells.values()))
    out += _repro_section(summary.get("reproducibility"))
    out += _crosscheck_section(summary.get("crosscheck_seed0"), cells)
    if summary.get("sacct"):
        out += [
            "## Cost on Picasso (`sacct`, every step; MaxRSS of the batch step)",
            "",
            "```",
            summary["sacct"].rstrip(),
            "```",
            "",
        ]
    return "\n".join(out) + "\n"


def added_row_flags(cells: dict[str, Any] | list[dict[str, Any]]) -> dict[str, Any]:
    """Per added row and hypothesis: the claim cells where it reaches the word."""
    rows = cells.values() if isinstance(cells, dict) else cells
    out: dict[str, Any] = {}
    for c in rows:
        if not c["claim"] or c["verdict"] not in ("word ahead", "kill"):
            continue
        for arm, row in c["added_rows"].items():
            slot = out.setdefault(arm, {}).setdefault(
                c["hypothesis"], {"cells": 0, "reaches_word": []}
            )
            slot["cells"] += 1
            hit = [m for m in c["metrics"] if m in row and row[m]["ge_word"]]
            if hit:
                slot["reaches_word"].append({"cell": c["id"], "metrics": hit})
    return out


def _added_row_flags(cells: dict[str, Any]) -> list[str]:
    flags = added_row_flags(cells)
    if not flags:
        return []
    lines = [
        "**Added rows (outside every family and verdict).** Claim cells in which the row's "
        "seed mean reaches the word's on a hypothesis metric:",
        "",
    ]
    for arm, by_h in flags.items():
        for h, slot in by_h.items():
            hits = ", ".join(
                f"`{x['cell']}` ({'/'.join(x['metrics'])})" for x in slot["reaches_word"]
            )
            lines.append(
                f"- {SHORT.get(arm, arm)}, {h}: {len(slot['reaches_word'])} of {slot['cells']}"
                + (f" — {hits}" if hits else "")
            )
    return [*lines, ""]


MECH_ARMS: tuple[str, ...] = (K.OURS, K.PATH_SYM, K.WL_H1)


def _q(v: list[float] | None, nd: int = 2) -> str:
    return "–" if not v else f"{v[1]:.{nd}f} ({v[0]:.{nd}f}–{v[2]:.{nd}f})"


def _mechanism_section(cells: list[dict[str, Any]]) -> list[str]:
    """Own class strictly nearer than every other class, per cell (word, edit path, WL h=1)."""
    lines = [
        "## Mechanism — is the own class strictly nearer? (pooled over seeds)",
        "",
        "A query's 1-NN is right with certainty iff its nearest own-class candidate is strictly "
        "nearer than its nearest other-class candidate (A / B / C: siblings; D: the source "
        "record against every other catalogue record). `own nearer` = share of queries where it "
        "is, mean over seeds [BCa]; `tie` = share where the two distances are equal; distances "
        "are medians (IQR) over every query of every seed, in the arm's own unit (word: tokens; "
        "edit path: edit cost).",
        "",
        "| cell | arm | own nearer [BCa] | tie | own-class distance | other-class distance |",
        "|---|---|---|---|---|---|",
    ]
    for c in cells:
        for arm in MECH_ARMS:
            m = c.get("mechanism", {}).get(arm)
            if not m or not m["own_strictly_nearer"]:
                continue
            lines.append(
                f"| `{c['id']}` | {SHORT.get(arm, arm)} | {_ci(m['own_strictly_nearer'])} | "
                f"{_f(m['tie']['mean']) if m['tie'] else '–'} | {_q(m['own_quartiles'])} | "
                f"{_q(m['other_quartiles'])} |"
            )
    return lines + [""]


def platform_sensitive_cells(cells: dict[str, Any], gap: float, arms: set[str]) -> list[dict]:
    """Cells whose registered verdict an arm's cross-machine 1-NN gap could reach.

    An arm whose seed-0 1-NN accuracy differed between Picasso and the
    workstation by up to ``gap`` could change a verdict only where its mean
    lies within ``gap`` of the word's and it decides the verdict alone: in a
    surviving cell, by crossing the word; in a killed cell, by being the only
    competitor at or above the word on 1-NN while nothing kills on another
    metric. ``gap`` is a seed-level difference, used as a heuristic bound.
    """
    out = []
    for c in cells.values():
        if not c["claim"] or c["verdict"] not in ("word ahead", "kill"):
            continue
        w = c["per_arm"].get(K.OURS, {}).get("acc1")
        for arm in arms & set(c["competitors"]):
            st = c["per_arm"].get(arm, {}).get("acc1")
            if not st or not w or abs(st["mean"] - w["mean"]) > gap:
                continue
            others = [k for m, ks in c["killers"].items() for k in ks if (m, k) != ("acc1", arm)]
            if c["verdict"] == "word ahead" or not others:
                out.append({"cell": c["id"], "arm": arm, "arm_mean": st["mean"], "word": w["mean"]})
    return out


def _crosscheck_section(cc: dict[str, Any] | None, cells: dict[str, Any]) -> list[str]:
    """Seed-0 cells computed on the workstation against the Picasso cells."""
    if not cc:
        return []
    differing = {a: n for a, n in cc.get("diff_by_arm", {}).items() if n}
    lines = [
        "## Cross-check: Picasso cells against the same cells computed locally (seed 0)",
        "",
        f"`crosscheck_seed0.py` on {cc['generated']}: {len(cc['cells'])} cells, "
        f"{cc['n_values']:,} values compared (wall-clock, throughput and worker-count keys "
        f"skipped). Exactly equal: {cc['n_exact']:,}; within rtol {cc['rtol']:g}: "
        f"{cc['n_close']:,}; different: {cc['n_diff']:,}. Keys dropped where the local cell "
        f"predates them: {', '.join(cc['ignored_keys']) or 'none'}. Differing values by arm: "
        + (", ".join(f"{a} {n}" for a, n in sorted(differing.items())) or "none")
        + ".",
        "",
    ]
    gap = cc.get("max_metric_gap")
    if gap:
        arms = {g["arm"] for g in cc["metric_gaps"]}
        lines.append(
            f"Hypothesis metrics that differ: {len(cc['metric_gaps'])} (arm, cell, metric) "
            f"values, all in {', '.join(sorted(arms))}; the largest is {gap['arm']} "
            f"{gap['metric']} on `{gap['cell']}`: {gap['picasso']:.4f} on Picasso against "
            f"{gap['local']:.4f} locally (|Δ| = {gap['abs_diff']:.4f}). Every other arm is "
            "bitwise identical across the two machines."
        )
        sens = platform_sensitive_cells(cells, gap["abs_diff"], arms)
        lines.append(
            "Claim cells where such an arm's mean 1-NN lies within that gap of the word's (so "
            "the platform could decide the verdict): "
            + (
                "; ".join(
                    f"`{s['cell']}` ({s['arm']} {s['arm_mean']:.3f} vs word {s['word']:.3f})"
                    for s in sens
                )
                if sens
                else "none"
            )
            + "."
        )
        lines.append("")
    lines += [*[f"- `{c}`" for c in cc["cells"]], ""]
    return lines


def _repro_section(repro: dict[str, Any] | None) -> list[str]:
    """The cross-machine check (Picasso vs the local replica), when ``compare_runs.py`` ran."""
    if not repro:
        return []
    lines = [
        "## Cross-machine reproducibility (Picasso vs the local replica)",
        "",
        f"Compared `{repro['a']}` with `{repro['b']}` by `compare_runs.py` on "
        f"{repro['generated']}: {repro['n_files']} result files, {repro['n_values']:,} numeric "
        "values (every metric and per-query list; wall-clock, throughput and run logs "
        f"excluded). Exactly equal: {repro['n_exact']:,}; within rtol {repro['rtol']:g}: "
        f"{repro['n_close']:,}; different: {repro['n_diff']:,}; files present on one side only: "
        f"{repro['n_missing']}.",
        "",
    ]
    if repro.get("examples"):
        lines += ["First differences:", ""]
        lines += [f"- `{e}`" for e in repro["examples"][:20]]
        lines.append("")
    return lines


def render_detail(summary: dict[str, Any]) -> str:
    """FULL_DETAIL.md: every arm of every cell."""
    out = ["# KNN_2026-10-15 full run — per-arm detail (generated; do not edit)", ""]
    for c in summary["cells"].values():
        out += [f"## `{c['id']}` — {c['hypothesis']}, {c['verdict']}, {c['n_seeds']} seeds", ""]
        mets = [m for m in (*c["metrics"], "rr", "acc5", "nmi", "err_within_share") if True]
        mets = list(dict.fromkeys(m for m in mets if any(m in v for v in c["per_arm"].values())))
        out.append("| arm | " + " | ".join(mets) + " | p_Holm (w° >) " + c["metrics"][0] + " |")
        out.append("|---|" + "---|" * (len(mets) + 1))
        for arm, v in c["per_arm"].items():
            t = c["tests"].get(c["metrics"][0], {}).get(arm)
            out.append(
                f"| {SHORT.get(arm, arm)} | "
                + " | ".join(_ci(v.get(m)) for m in mets)
                + f" | {_p(t['p_holm']) if t else '–'} |"
            )
        out.append("")
    return "\n".join(out) + "\n"


def aggregate(root: Path) -> dict[str, Any]:
    """Load every unit under ``root`` and aggregate every cell and hypothesis."""
    series = {**load_ab(root), **load_c(root), **load_d(root)}
    cells = {
        cid: aggregate_series(s)
        for cid, s in sorted(
            series.items(),
            key=lambda kv: (
                kv[1].design,
                kv[1].condition,
                kv[1].c or 0,
                COLLECTION_ORDER.get(kv[1].collection, 9),
                kv[1].r or 0,
            ),
        )
    }
    repro_path = root / "REPRO_CHECK.json"
    sacct_path = root / "sacct.txt"
    cc_path = root / "CROSSCHECK_SEED0.json"
    return {
        "crosscheck_seed0": json.loads(cc_path.read_text()) if cc_path.exists() else None,
        "sacct": sacct_path.read_text() if sacct_path.exists() else None,
        "root": str(root),
        "generated": time.strftime("%Y-%m-%d %H:%M %Z"),
        "alpha": ALPHA,
        "seeds_expected": SEEDS_FULL,
        "cells": cells,
        "hypotheses": hypothesis_verdicts(cells),
        "added_row_flags": added_row_flags(cells),
        "reproducibility": json.loads(repro_path.read_text()) if repro_path.exists() else None,
    }


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--root", type=Path, default=K.OUT_ROOT / "full")
    args = ap.parse_args()
    summary = aggregate(args.root)
    K.write_json(args.root / "full_summary.json", summary)
    (args.root / "FULL_SUMMARY.md").write_text(render(summary))
    (args.root / "FULL_DETAIL.md").write_text(render_detail(summary))
    print((args.root / "FULL_SUMMARY.md").read_text())


if __name__ == "__main__":
    main()
