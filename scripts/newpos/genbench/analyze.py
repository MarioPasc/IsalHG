"""Statistics and tables of the generation benchmark on usable samples.

Reads the evaluator's ``units.csv``, ``arrays/`` and ``collections.json`` and
writes ``tables.md`` and ``stats.json``. Implements the pre-registered tests
(HA1 rejection bias, HA2 relational structure, HA3 yield) with the reviewer
amendment: fidelity is compared at equal numbers of USABLE samples (primary), not
at equal draws, and arms with fewer than ``MIN_USABLE`` usable samples on a seed
enter no fidelity statistic.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import zlib
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from experiments.tkde.stats import bca_ci, holm, wilcoxon_paired  # noqa: E402
from scripts.newpos.genbench import common as gb  # noqa: E402

HA1_METRICS: tuple[str, ...] = ("jsd_n", "jsd_m", "w1_m")
HA2_METRIC = "rel_dev"
FIDELITY_METRICS: tuple[str, ...] = (
    "jsd_n",
    "jsd_m",
    "jsd_arity",
    "jsd_pred",
    "jsd_type",
    "w1_n",
    "w1_m",
    "mean_n",
    "mean_m",
    "star_frac",
    "rel_dev",
    "shared",
)
ALPHA = 0.05
#: Bias direction predicted by the mechanism: sign of (usable mean - collection value).
PREDICTED_SIGN = {"mean_n": -1, "mean_m": -1, "star_frac": +1}


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def _finite(values: Iterable[float] | np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    return arr[np.isfinite(arr)]


def ci(values: Iterable[float] | np.ndarray) -> dict[str, float] | None:
    """BCa 95 % interval of the mean of the finite entries, or ``None`` if there are none."""
    arr = _finite(values)
    if arr.size == 0:
        return None
    interval = bca_ci(arr, stat="mean")
    return {"mean": interval.point, "low": interval.low, "high": interval.high, "n": int(arr.size)}


def fmt(x: float, digits: int = 4) -> str:
    """Compact significant-digit formatting that keeps tiny values readable."""
    if x is None or (isinstance(x, float) and not math.isfinite(x)):
        return "nan"
    if x == 0:
        return "0"
    if abs(x) >= 1000:
        return f"{x:,.0f}"
    return f"{x:.{digits}g}"


def fmt_ci(c: dict[str, float] | None, digits: int = 4) -> str:
    """``mean [low, high]`` of an interval dict."""
    if c is None:
        return "n/a"
    return f"{fmt(c['mean'], digits)} [{fmt(c['low'], digits)}, {fmt(c['high'], digits)}]"


def md_table(header: list[str], rows: list[list[str]]) -> str:
    """Render a Markdown table."""
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    lines += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(lines)


def _rng(*parts: object, rep: int = 0) -> np.random.Generator:
    return np.random.default_rng([zlib.crc32("|".join(map(str, parts)).encode()), rep])


# ---------------------------------------------------------------------------
# Data access
# ---------------------------------------------------------------------------


class Bench:
    """The evaluator's outputs for a set of arms."""

    def __init__(self, eval_dir: Path, collections: list[str], arms: list[str]) -> None:
        self.dir = eval_dir
        self.units = pd.read_csv(eval_dir / "units.csv")
        self.collections = collections
        self.arms = arms
        self.coll_info = json.loads((eval_dir / "collections.json").read_text())
        self._arrays: dict[tuple[str, str, int], gb.SampleSet] = {}
        self._reference: dict[str, gb.SampleSet] = {}

    def rows(self, collection: str, arm: str) -> pd.DataFrame:
        sel = self.units[(self.units.collection == collection) & (self.units.generator == arm)]
        return sel.sort_values("seed").reset_index(drop=True)

    def seeds(self, collection: str, arm: str) -> list[int]:
        return [int(s) for s in self.rows(collection, arm).seed]

    def arrays(self, collection: str, arm: str, seed: int) -> gb.SampleSet:
        key = (collection, arm, seed)
        if key not in self._arrays:
            path = self.dir / "arrays" / f"{gb.unit_stem(collection, arm, seed)}.npz"
            self._arrays[key] = gb.SampleSet.load(path)
        return self._arrays[key]

    def reference(self, collection: str) -> tuple[gb.SampleSet, dict[str, np.ndarray]]:
        """The collection's own sample set, rebuilt from the frozen corpus."""
        if collection not in self._reference:
            from experiments.tkde import corpora

            records = corpora.load_collection(collection, gb.CORPUS_ROOT).records
            self._reference[collection] = gb.SampleSet.from_kbs(
                (r.n, r.types, r.facts) for r in records
            )
        ref = self._reference[collection]
        return ref, ref.profile()


# ---------------------------------------------------------------------------
# Matched comparison (primary fidelity test)
# ---------------------------------------------------------------------------


def _averaged(
    sample: gb.SampleSet,
    size: int,
    ref: gb.SampleSet,
    ref_profile: dict[str, np.ndarray],
    key: tuple[Any, ...],
    *,
    replace: bool = False,
) -> dict[str, float]:
    """Mean of the fidelity metrics over ``N_MATCH_REPEATS`` seeded subsamples of ``size``."""
    if size >= len(sample) and not replace:
        return gb.set_metrics(sample, ref, ref_profile)
    runs = []
    for rep in range(gb.N_MATCH_REPEATS):
        rng = _rng(*key, rep=rep)
        idx = (
            rng.integers(0, len(sample), size)
            if replace
            else rng.choice(len(sample), size, replace=False)
        )
        runs.append(gb.set_metrics(sample.take(idx), ref, ref_profile))
    return {k: float(np.mean([r[k] for r in runs])) for k in runs[0]}


def matched_cell(
    bench: Bench, collection: str, ours: str, base: str, mode: str, fact_arm: str = gb.ARM_FACT
) -> dict[str, Any]:
    """Per-seed metrics of ``ours`` and ``base`` at equal numbers of usable samples.

    Parameters
    ----------
    mode : {"u_b", "u_fact", "full"}
        ``u_b``: size is the baseline's usable count, only ``ours`` is subsampled.
        ``u_fact``: size is the fact-list arm's usable count, both arms subsampled
        (the repair arm is always usable). ``full``: both arms at their full usable
        sets (the repair arm at about 10,000).
    """
    ref, ref_profile = bench.reference(collection)
    base_rows, ours_rows = bench.rows(collection, base), bench.rows(collection, ours)
    fact_rows = bench.rows(collection, fact_arm)
    seeds, per_seed = [], []
    for seed in bench.seeds(collection, base):
        b_row = base_rows[base_rows.seed == seed].iloc[0]
        o_row = ours_rows[ours_rows.seed == seed]
        if o_row.empty:
            continue
        if mode == "u_fact":
            f_row = fact_rows[fact_rows.seed == seed]
            size = int(f_row.iloc[0].n_usable) if not f_row.empty else 0
        elif mode == "full":
            size = min(int(b_row.n_usable), int(o_row.iloc[0].n_usable))
        else:
            size = int(b_row.n_usable)
        if size < gb.MIN_USABLE or int(b_row.n_usable) < gb.MIN_USABLE:
            continue
        o_set = bench.arrays(collection, ours, seed)
        b_set = bench.arrays(collection, base, seed)
        key = (collection, seed, base, mode)
        ours_vals = _averaged(o_set, size, ref, ref_profile, (*key, "ours"))
        if mode == "u_b":
            base_vals = gb.set_metrics(b_set, ref, ref_profile)
        else:
            base_vals = _averaged(b_set, size, ref, ref_profile, (*key, "base"))
        ideal = _averaged(ref, size, ref, ref_profile, (*key, "ideal"), replace=True)
        seeds.append(seed)
        per_seed.append({"size": size, "ours": ours_vals, "base": base_vals, "ideal": ideal})
    return {"seeds": seeds, "per_seed": per_seed}


def test_rows(
    collection: str,
    base: str,
    mode: str,
    cell: dict[str, Any],
    metrics: tuple[str, ...],
    n_total: int,
    base_usable_median: float,
) -> list[dict[str, Any]]:
    """One-sided paired Wilcoxon of ``base`` > ``ours`` for each metric of a matched cell.

    ``median_size`` is the baseline's median usable count over all seeds (what a
    reader needs to see when the cell is untestable); ``median_matched_size`` is the
    matched sample size actually used.
    """
    out = []
    for metric in metrics:
        b = np.array([p["base"][metric] for p in cell["per_seed"]], dtype=float)
        o = np.array([p["ours"][metric] for p in cell["per_seed"]], dtype=float)
        ideal = np.array([p["ideal"][metric] for p in cell["per_seed"]], dtype=float)
        keep = np.isfinite(b) & np.isfinite(o)
        row: dict[str, Any] = {
            "collection": collection,
            "baseline": base,
            "mode": mode,
            "metric": metric,
            "n_valid_seeds": int(keep.sum()),
            "n_total_seeds": n_total,
            "testable": bool(keep.sum() >= gb.MIN_VALID_SEEDS),
            "median_size": base_usable_median,
            "median_matched_size": float(np.median([p["size"] for p in cell["per_seed"]]))
            if cell["per_seed"]
            else math.nan,
        }
        if keep.any():
            row.update(
                mean_base=ci(b[keep]),
                mean_ours=ci(o[keep]),
                mean_ideal=ci(ideal[keep]),
                diff=ci(b[keep] - o[keep]),
            )
        if row["testable"]:
            test = wilcoxon_paired(b[keep], o[keep], alternative="greater")
            row.update(
                p_raw=test["p_value"],
                rank_biserial=test["rank_biserial"],
                n_nonzero=test["n"],
            )
        out.append(row)
    return out


def apply_holm(rows: list[dict[str, Any]], family: str) -> None:
    """Holm-correct the testable rows of one family in place."""
    testable = [r for r in rows if r.get("testable")]
    for r in rows:
        r["family"] = family
    if not testable:
        return
    for r, corr in zip(testable, holm([r["p_raw"] for r in testable], alpha=ALPHA), strict=True):
        r["p_holm"], r["reject"], r["family_size"] = corr["p_holm"], corr["reject"], len(testable)


# ---------------------------------------------------------------------------
# Unmatched tests and yield
# ---------------------------------------------------------------------------


def unmatched_rows(
    bench: Bench, collection: str, ours: str, base: str, metrics: tuple[str, ...]
) -> list[dict[str, Any]]:
    """The same tests on the full usable sets (secondary), seeds with ``fidelity_ok`` in both."""
    b_rows, o_rows = bench.rows(collection, base), bench.rows(collection, ours)
    merged = b_rows.merge(o_rows, on="seed", suffixes=("_b", "_o"))
    merged = merged[(merged.fidelity_ok_b == 1) & (merged.fidelity_ok_o == 1)]
    out = []
    for metric in metrics:
        b, o = merged[f"{metric}_use_b"].to_numpy(float), merged[f"{metric}_use_o"].to_numpy(float)
        keep = np.isfinite(b) & np.isfinite(o)
        row: dict[str, Any] = {
            "collection": collection,
            "baseline": base,
            "mode": "unmatched",
            "metric": metric,
            "n_valid_seeds": int(keep.sum()),
            "n_total_seeds": len(b_rows),
            "testable": bool(keep.sum() >= gb.MIN_VALID_SEEDS),
            "median_size": float(b_rows.n_usable.median()),
        }
        if keep.any():
            row.update(mean_base=ci(b[keep]), mean_ours=ci(o[keep]), diff=ci(b[keep] - o[keep]))
        if row["testable"]:
            test = wilcoxon_paired(b[keep], o[keep], alternative="greater")
            row.update(
                p_raw=test["p_value"],
                rank_biserial=test["rank_biserial"],
                n_nonzero=test["n"],
            )
        out.append(row)
    return out


def yield_rows(bench: Bench, collection: str, ours: str, base: str, column: str) -> dict[str, Any]:
    """HA3: ``ours`` > ``base`` on a per-draw yield column, all paired seeds."""
    merged = bench.rows(collection, ours).merge(
        bench.rows(collection, base), on="seed", suffixes=("_o", "_b")
    )
    o, b = merged[f"{column}_o"].to_numpy(float), merged[f"{column}_b"].to_numpy(float)
    test = wilcoxon_paired(o, b, alternative="greater")
    return {
        "collection": collection,
        "baseline": base,
        "metric": column,
        "n_valid_seeds": len(o),
        "testable": True,
        "mean_ours": ci(o),
        "mean_base": ci(b),
        "diff": ci(o - b),
        "p_raw": test["p_value"],
        "rank_biserial": test["rank_biserial"],
        "n_nonzero": test["n"],
    }


# ---------------------------------------------------------------------------
# Direction of the rejection bias (amendment 3)
# ---------------------------------------------------------------------------


def direction(bench: Bench, collection: str, arm: str) -> dict[str, Any]:
    """Seed-level deviation of the usable mean n, mean m and star fraction from the collection's."""
    rows = bench.rows(collection, arm)
    rows = rows[rows.fidelity_ok == 1]
    out: dict[str, Any] = {"collection": collection, "arm": arm, "n_valid_seeds": len(rows)}
    for metric, coll_col in (
        ("mean_n", "coll_mean_n"),
        ("mean_m", "coll_mean_m"),
        ("star_frac", "coll_star_frac"),
    ):
        if len(rows) < gb.MIN_VALID_SEEDS:
            out[metric] = None
            continue
        dev = rows[f"{metric}_use"].to_numpy(float) - rows[coll_col].to_numpy(float)
        c = ci(dev)
        sign = PREDICTED_SIGN[metric]
        out[metric] = {
            "deviation": c,
            "predicted_sign": sign,
            "seeds_in_predicted_direction": int(np.sum(np.sign(dev) == sign)),
            "ci_on_predicted_side": bool(
                c is not None and (c["high"] < 0 if sign < 0 else c["low"] > 0)
            ),
            "ci_on_opposite_side": bool(
                c is not None and (c["low"] > 0 if sign < 0 else c["high"] < 0)
            ),
        }
    return out


def ha1_verdict(rows: list[dict[str, Any]], dirn: dict[str, Any] | None) -> str:
    """Pre-registered HA1 verdict of one (collection, baseline) cell."""
    if (
        not rows
        or not all(r["testable"] for r in rows)
        or dirn is None
        or dirn["n_valid_seeds"] < gb.MIN_VALID_SEEDS
    ):
        return "INSUFFICIENT"
    if not all(r.get("reject") for r in rows):
        return "NOT SUPPORTED"
    on_side = all(dirn[m]["ci_on_predicted_side"] for m in PREDICTED_SIGN)
    return "SUPPORTED" if on_side else "WRONG-DIRECTION"


# ---------------------------------------------------------------------------
# RQ6 reproduction
# ---------------------------------------------------------------------------


def reproduction(bench: Bench, rq6_rows: Path, arms: list[str]) -> list[dict[str, Any]]:
    """Compare the all-decoded columns with RQ6's published per-seed rows."""
    ref = pd.read_csv(rq6_rows)
    out = []
    for collection in bench.collections:
        for arm in arms:
            mine, theirs = (
                bench.rows(collection, arm),
                ref[(ref.collection == collection) & (ref.model == arm)],
            )
            merged = mine.merge(theirs, on="seed", suffixes=("", "_rq6"))
            if merged.empty:
                continue
            row: dict[str, Any] = {"collection": collection, "arm": arm, "n_seeds": len(merged)}
            row["n_valid_equal"] = bool((merged.n_decoded == merged.n_valid).all())
            row["n_connected_equal"] = bool((merged.n_connected == merged.n_connected_rq6).all())
            worst = 0.0
            for key in gb.PROFILE_KEYS:
                a, b = (
                    merged[f"jsd_{key}_all"].to_numpy(float),
                    merged[f"jsd_{key}"].to_numpy(float),
                )
                scale = np.maximum(np.abs(b), 1e-12)
                rel = np.where(np.abs(b) < 1e-12, np.abs(a - b), np.abs(a - b) / scale)
                row[f"max_rel_diff_jsd_{key}"] = float(np.nanmax(rel))
                worst = max(worst, row[f"max_rel_diff_jsd_{key}"])
            row["agree_3sf"] = bool(
                row["n_valid_equal"] and row["n_connected_equal"] and worst < 5e-4
            )
            out.append(row)
    return out


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------


def yield_table(bench: Bench) -> tuple[str, dict[str, Any]]:
    """Per collection and arm: validity, connectivity, usable rate, VUN."""
    stats: dict[str, Any] = {}
    rows = []
    columns = ("validity", "connectivity", "usable_rate", "vun_per_draw", "vun_singleton_per_draw")
    for collection in bench.collections:
        for arm in bench.arms:
            frame = bench.rows(collection, arm)
            if frame.empty:
                continue
            cells = {c: ci(frame[c]) for c in columns}
            per10k = ci(frame.n_usable / frame.n_draws * 1e4)
            stats[f"{collection}|{arm}"] = {
                **cells,
                "usable_per_10k": per10k,
                "n_seeds": len(frame),
                "total_draws": int(frame.n_draws.sum()),
                "total_usable": int(frame.n_usable.sum()),
            }
            rows.append(
                [
                    collection,
                    arm,
                    str(len(frame)),
                    fmt_ci(cells["validity"]),
                    fmt_ci(cells["connectivity"]),
                    fmt_ci(per10k, 5),
                    fmt_ci(ci(frame.n_unique_novel_usable / frame.n_draws * 1e4), 5),
                    fmt_ci(cells["vun_per_draw"]),
                    fmt_ci(cells["vun_singleton_per_draw"]),
                ]
            )
    header = [
        "collection",
        "arm",
        "seeds",
        "decoded / draws",
        "connected / decoded",
        "usable per 10,000 draws",
        "valid-unique-novel per 10,000",
        "VUN per draw",
        "VUN per draw (singleton reading)",
    ]
    return md_table(header, rows), stats


def fidelity_unmatched_table(bench: Bench) -> tuple[str, dict[str, Any]]:
    """Seed-level means of every fidelity quantity on the usable samples (descriptive)."""
    stats: dict[str, Any] = {}
    out = []
    for collection in bench.collections:
        info = bench.coll_info[collection]
        header = ["arm", "usable u (median)", *FIDELITY_METRICS]
        rows = []
        for arm in bench.arms:
            frame = bench.rows(collection, arm)
            if frame.empty:
                continue
            ok = frame[frame.fidelity_ok == 1]
            if len(ok) < gb.MIN_VALID_SEEDS:
                msg = (
                    f"insufficient usable samples (u = {int(frame.n_usable.median())} median, "
                    f"max {int(frame.n_usable.max())}; "
                    f"{len(ok)}/{len(frame)} seeds >= {gb.MIN_USABLE})"
                )
                rows.append(
                    [
                        arm,
                        str(int(frame.n_usable.median())),
                        msg,
                        *[""] * (len(FIDELITY_METRICS) - 1),
                    ]
                )
                stats[f"{collection}|{arm}"] = {"insufficient": True, "n_seeds_ok": len(ok)}
                continue
            cells = {m: ci(ok[f"{m}_use"]) for m in FIDELITY_METRICS}
            stats[f"{collection}|{arm}"] = {"n_seeds_ok": len(ok), **cells}
            rows.append(
                [
                    arm,
                    str(int(frame.n_usable.median())),
                    *[fmt_ci(cells[m]) for m in FIDELITY_METRICS],
                ]
            )
        own = {
            "mean_n": info["coll_mean_n"],
            "mean_m": info["coll_mean_m"],
            "star_frac": info["coll_star_frac"],
            "shared": info["coll_shared"],
        }
        rows.append(
            [
                "collection (own)",
                str(info["n_members"]),
                *[fmt(own[m]) if m in own else "0" for m in FIDELITY_METRICS],
            ]
        )
        for label, key in (
            ("split-half floor (27 splits)", "split_half"),
            ("ideal resampler, 10,000 draws", "resample"),
        ):
            rows.append([label, "-", *[fmt(info[key][m]) for m in FIDELITY_METRICS]])
        stats[f"{collection}|floors"] = {
            "split_half": info["split_half"],
            "resample": info["resample"],
            "own": own,
        }
        out.append(f"#### {collection}\n\n" + md_table(header, rows))
    return "\n\n".join(out), stats


def structure_table(bench: Bench) -> str:
    """Star fraction, mean n and mean m of each arm's usable samples next to the collection's."""
    rows = []
    for collection in bench.collections:
        info = bench.coll_info[collection]
        rows.append(
            [
                collection,
                "collection (own)",
                str(info["n_members"]),
                fmt(info["coll_star_frac"]),
                "-",
                fmt(info["coll_mean_n"]),
                fmt(info["coll_mean_m"]),
            ]
        )
        for arm in bench.arms:
            frame = bench.rows(collection, arm)
            ok = frame[frame.fidelity_ok == 1]
            if frame.empty:
                continue
            if len(ok) < gb.MIN_VALID_SEEDS:
                rows.append(
                    [
                        collection,
                        arm,
                        str(int(frame.n_usable.median())),
                        "insufficient usable samples",
                        "",
                        "",
                        "",
                    ]
                )
                continue
            dev = ok.star_frac_use.to_numpy(float) - ok.coll_star_frac.to_numpy(float)
            rows.append(
                [
                    collection,
                    arm,
                    str(int(frame.n_usable.median())),
                    fmt_ci(ci(ok.star_frac_use)),
                    fmt_ci(ci(dev)),
                    fmt_ci(ci(ok.mean_n_use)),
                    fmt_ci(ci(ok.mean_m_use)),
                ]
            )
    return md_table(
        [
            "collection",
            "arm",
            "usable u (median)",
            "star fraction of usable samples",
            "star fraction - collection's",
            "mean n of usable",
            "mean m of usable",
        ],
        rows,
    )


def posthoc_envelope_table(bench: Bench) -> str:
    """POST-HOC diagnostic: usable samples that also lie in the collections' size envelope."""
    rows = []
    for collection in bench.collections:
        for arm in bench.arms:
            frame = bench.rows(collection, arm)
            if frame.empty:
                continue
            frac = ci(frame.n_usable_inenv / frame.n_usable.clip(lower=1))
            per10k = ci(frame.n_usable_inenv / frame.n_draws * 1e4)
            vun10k = ci(frame.n_unique_novel_inenv / frame.n_draws * 1e4)
            ok = frame[frame.jsd_m_inenv.notna()]
            cells = [
                fmt_ci(ci(ok[c])) if len(ok) >= gb.MIN_VALID_SEEDS else "n/a"
                for c in ("jsd_n_inenv", "jsd_m_inenv", "w1_m_inenv", "mean_m_inenv")
            ]
            rows.append(
                [collection, arm, fmt_ci(frac), fmt_ci(per10k, 5), fmt_ci(vun10k, 5), *cells]
            )
    header = [
        "collection",
        "arm",
        "fraction of usable in envelope",
        "usable in envelope per 10,000",
        "VUN in envelope per 10,000",
        "jsd_n (in-envelope)",
        "jsd_m (in-envelope)",
        "w1_m (in-envelope)",
        "mean m (in-envelope)",
    ]
    return md_table(header, rows)


def all_decoded_table(bench: Bench) -> str:
    """The five JSDs over ALL decoded samples (the RQ6 view)."""
    parts = []
    for collection in bench.collections:
        rows = []
        for arm in bench.arms:
            frame = bench.rows(collection, arm)
            if frame.empty:
                continue
            rows.append([arm, *[fmt_ci(ci(frame[f"jsd_{k}_all"])) for k in gb.PROFILE_KEYS]])
        parts.append(
            f"#### {collection}\n\n"
            + md_table(["arm", *[f"jsd_{k}" for k in gb.PROFILE_KEYS]], rows)
        )
    return "\n\n".join(parts)


def tests_table(rows: list[dict[str, Any]]) -> str:
    """Render test rows (any family) as a Markdown table."""
    body = []
    for r in rows:
        if not r["testable"]:
            note = (
                f"insufficient usable samples (u = {fmt(r['median_size'])} median; "
                f"{r['n_valid_seeds']}/{r['n_total_seeds']} seeds >= {gb.MIN_USABLE})"
            )
            has = "mean_base" in r
            body.append(
                [
                    r["collection"],
                    r["baseline"],
                    r["metric"],
                    note,
                    fmt_ci(r["mean_base"]) if has else "",
                    fmt_ci(r["mean_ours"]) if has else "",
                    fmt_ci(r["mean_ideal"]) if r.get("mean_ideal") else "",
                    fmt_ci(r["diff"]) if has else "",
                    "untested",
                    "",
                    "",
                ]
            )
            continue
        body.append(
            [
                r["collection"],
                r["baseline"],
                r["metric"],
                str(r["n_valid_seeds"]),
                fmt_ci(r["mean_base"]),
                fmt_ci(r["mean_ours"]),
                fmt_ci(r["mean_ideal"]) if r.get("mean_ideal") else "",
                fmt_ci(r["diff"]),
                f"{r['p_raw']:.3g}",
                f"{r.get('p_holm', math.nan):.3g}",
                ("**yes**" if r.get("reject") else "no") + f" (rb {r['rank_biserial']:+.2f})",
            ]
        )
    header = [
        "collection",
        "baseline",
        "metric",
        "seeds",
        "baseline mean [95% CI]",
        "ours mean [95% CI]",
        "ideal resampler at same size",
        "baseline - ours [95% CI]",
        "p raw",
        "p Holm",
        "reject (rank-biserial)",
    ]
    return md_table(header, body)


def direction_table(dirs: list[dict[str, Any]]) -> str:
    """Bias-direction table (amendment 3)."""
    body = []
    for d in dirs:
        if d["n_valid_seeds"] < gb.MIN_VALID_SEEDS:
            body.append(
                [
                    d["collection"],
                    d["arm"],
                    f"insufficient usable samples ({d['n_valid_seeds']} seeds)",
                    "",
                    "",
                ]
            )
            continue
        cells = []
        for metric in ("mean_n", "mean_m", "star_frac"):
            x = d[metric]
            tag = (
                "predicted side"
                if x["ci_on_predicted_side"]
                else ("OPPOSITE side" if x["ci_on_opposite_side"] else "CI spans 0")
            )
            cells.append(
                f"{fmt_ci(x['deviation'])} ({tag}; "
                f"{x['seeds_in_predicted_direction']}/{d['n_valid_seeds']} seeds)"
            )
        body.append([d["collection"], d["arm"], *cells])
    return md_table(
        [
            "collection",
            "arm",
            "mean n - collection's (pred. < 0)",
            "mean m - collection's (pred. < 0)",
            "star fraction - collection's (pred. > 0)",
        ],
        body,
    )


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def run(args: argparse.Namespace) -> None:
    """Compute every table and test, write ``tables.md`` and ``stats.json``."""
    gb.MIN_VALID_SEEDS = int(args.min_valid_seeds)
    ours = args.ours
    baselines = args.baselines.split(",")
    collections = args.collection or list(gb.COLLECTIONS)
    arms = [ours, *baselines]
    bench = Bench(Path(args.eval), collections, arms)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    yield_md, yield_stats = yield_table(bench)
    fid_md, fid_stats = fidelity_unmatched_table(bench)

    primary: list[dict[str, Any]] = []
    robustness: list[dict[str, Any]] = []
    unmatched: list[dict[str, Any]] = []
    matched_cells: dict[str, Any] = {}
    for collection in collections:
        for base in baselines:
            n_total = len(bench.rows(collection, base))
            u_med = float(bench.rows(collection, base).n_usable.median())
            mode = "u_fact" if base == gb.ARM_LCC else "u_b"
            cell = matched_cell(bench, collection, ours, base, mode)
            matched_cells[f"{collection}|{base}|{mode}"] = {
                "seeds": cell["seeds"],
                "sizes": [p["size"] for p in cell["per_seed"]],
            }
            primary += test_rows(
                collection, base, mode, cell, (*HA1_METRICS, HA2_METRIC), n_total, u_med
            )
            if base == gb.ARM_LCC:
                full = matched_cell(bench, collection, ours, base, "full")
                robustness += test_rows(
                    collection, base, "full", full, (*HA1_METRICS, HA2_METRIC), n_total, u_med
                )
            unmatched += unmatched_rows(bench, collection, ours, base, (*HA1_METRICS, HA2_METRIC))
    ha1_primary = [r for r in primary if r["metric"] in HA1_METRICS]
    ha2_primary = [r for r in primary if r["metric"] == HA2_METRIC]
    apply_holm(ha1_primary, "HA1 matched (primary)")
    apply_holm(ha2_primary, "HA2 matched (primary)")
    apply_holm(
        [r for r in robustness if r["metric"] in HA1_METRICS],
        "HA1 lcc at full usable sets (robustness)",
    )
    apply_holm(
        [r for r in robustness if r["metric"] == HA2_METRIC],
        "HA2 lcc at full usable sets (robustness)",
    )
    apply_holm([r for r in unmatched if r["metric"] in HA1_METRICS], "HA1 unmatched (secondary)")
    apply_holm([r for r in unmatched if r["metric"] == HA2_METRIC], "HA2 unmatched (secondary)")

    ha3 = [yield_rows(bench, c, ours, b, "vun_per_draw") for c in collections for b in baselines]
    ha3_single = [
        yield_rows(bench, c, ours, b, "vun_singleton_per_draw")
        for c in collections
        for b in baselines
    ]
    apply_holm(ha3, "HA3 VUN per draw (distinct classes)")
    apply_holm(ha3_single, "HA3 VUN per draw (singleton reading)")

    dirs = [direction(bench, c, a) for c in collections for a in arms]
    verdicts = []
    for collection in collections:
        for base in baselines:
            rows = [
                r for r in ha1_primary if r["collection"] == collection and r["baseline"] == base
            ]
            dirn = next(d for d in dirs if d["collection"] == collection and d["arm"] == base)
            h2 = next(
                r for r in ha2_primary if r["collection"] == collection and r["baseline"] == base
            )
            h3 = next(r for r in ha3 if r["collection"] == collection and r["baseline"] == base)
            verdicts.append(
                {
                    "collection": collection,
                    "baseline": base,
                    "HA1": ha1_verdict(rows, dirn),
                    "HA2": (
                        "INSUFFICIENT"
                        if not h2["testable"]
                        else "SUPPORTED"
                        if h2.get("reject")
                        else "NOT SUPPORTED"
                    ),
                    "HA3": "SUPPORTED" if h3.get("reject") else "NOT SUPPORTED",
                }
            )

    repro = (
        reproduction(bench, Path(args.rq6_rows), [a for a in arms if a in gb.NGRAM_ARMS])
        if args.rq6_rows
        else []
    )
    stats = {
        "yield": yield_stats,
        "fidelity_unmatched": fid_stats,
        "matched_cells": matched_cells,
        "HA1_matched_primary": ha1_primary,
        "HA2_matched_primary": ha2_primary,
        "robustness_lcc_full": robustness,
        "unmatched_secondary": unmatched,
        "HA3": ha3,
        "HA3_singleton": ha3_single,
        "direction": dirs,
        "verdicts": verdicts,
        "reproduction_rq6": repro,
        "floors": {
            c: {k: bench.coll_info[c][k] for k in ("split_half", "resample")} for c in collections
        },
        "config": {
            "ours": ours,
            "baselines": baselines,
            "min_usable": gb.MIN_USABLE,
            "min_valid_seeds": gb.MIN_VALID_SEEDS,
            "match_repeats": gb.N_MATCH_REPEATS,
            "alpha": ALPHA,
        },
    }
    (out / "stats.json").write_text(json.dumps(stats, indent=1, default=_json_default))

    sections = [
        "# Generation benchmark on usable samples\n",
        f"Arms: ours = `{ours}`; baselines = {', '.join(f'`{b}`' for b in baselines)}. "
        "Seeds per cell are in the tables. Usable = decoded, connected, at least one fact. "
        f"Fidelity statistics need u >= {gb.MIN_USABLE} usable samples on a seed; "
        f"a cell is tested iff >= {gb.MIN_VALID_SEEDS} seeds qualify.\n",
        "## Verdicts (pre-registered rules)\n",
        md_table(
            [
                "collection",
                "baseline",
                "HA1 (rejection bias, matched, direction-checked)",
                "HA2 (relational fraction)",
                "HA3 (yield)",
            ],
            [[v["collection"], v["baseline"], v["HA1"], v["HA2"], v["HA3"]] for v in verdicts],
        ),
        "\n## Yield\n",
        yield_md,
        "\n## Star fraction and size of the usable samples next to the collection's\n",
        structure_table(bench),
        "\n## Fidelity of usable samples, unmatched (descriptive; seed-level mean, BCa 95 % CI)\n",
        fid_md,
        "\n## Fidelity over ALL decoded samples (the RQ6 view)\n",
        all_decoded_table(bench),
        "\n## Bias direction of the usable samples (amendment 3)\n",
        direction_table(dirs),
        "\n## Post-hoc diagnostic (NOT pre-registered): usable samples inside the collections' "
        "size envelope (n <= 24, 3 <= m <= 110, arity <= 10)\n",
        posthoc_envelope_table(bench),
        "\n## HA1 - rejection bias, MATCHED usable counts (primary; one-sided baseline > ours)\n",
        tests_table(ha1_primary),
        "\n## HA2 - relational-fraction deviation, MATCHED (primary)\n",
        tests_table(ha2_primary),
        "\n## Robustness: `fact_ngram_lcc` vs ours at the full usable sets (about 10,000 each)\n",
        tests_table(robustness),
        "\n## Secondary: the same tests UNMATCHED (all usable samples of each arm)\n",
        tests_table(unmatched),
        "\n## HA3 - valid-unique-novel per draw (ours > baseline)\n",
        ha3_table(ha3),
        "\n## HA3, singleton reading of uniqueness\n",
        ha3_table(ha3_single),
    ]
    if repro:
        sections += [
            "\n## Reproduction of RQ6 (all-decoded columns, matching seeds)\n",
            repro_table(repro),
        ]
    (out / "tables.md").write_text("\n".join(sections) + "\n")
    print(f"[analyze] wrote {out / 'tables.md'} and {out / 'stats.json'}")


def ha3_table(rows: list[dict[str, Any]]) -> str:
    """Render the yield tests."""
    body = [
        [
            r["collection"],
            r["baseline"],
            str(r["n_valid_seeds"]),
            fmt_ci(r["mean_ours"]),
            fmt_ci(r["mean_base"]),
            fmt_ci(r["diff"]),
            f"{r['p_raw']:.3g}",
            f"{r['p_holm']:.3g}",
            ("**yes**" if r["reject"] else "no") + f" (rb {r['rank_biserial']:+.2f})",
        ]
        for r in rows
    ]
    return md_table(
        [
            "collection",
            "baseline",
            "seeds",
            "ours mean [95% CI]",
            "baseline mean [95% CI]",
            "ours - baseline [95% CI]",
            "p raw",
            "p Holm",
            "reject (rank-biserial)",
        ],
        body,
    )


def repro_table(rows: list[dict[str, Any]]) -> str:
    """Render the RQ6 reproduction check."""
    body = [
        [
            r["collection"],
            r["arm"],
            str(r["n_seeds"]),
            str(r["n_valid_equal"]),
            str(r["n_connected_equal"]),
            *[fmt(r[f"max_rel_diff_jsd_{k}"], 2) for k in gb.PROFILE_KEYS],
            str(r["agree_3sf"]),
        ]
        for r in rows
    ]
    return md_table(
        [
            "collection",
            "arm",
            "seeds",
            "n_valid equal",
            "n_connected equal",
            *[f"max rel diff jsd_{k}" for k in gb.PROFILE_KEYS],
            "agree to 3 s.f.",
        ],
        body,
    )


def _json_default(obj: object) -> object:
    if isinstance(obj, np.generic):
        return obj.item()
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(type(obj))


def build_parser() -> argparse.ArgumentParser:
    """Command-line interface."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--eval", required=True, help="evaluator output directory")
    p.add_argument("--out", required=True, help="directory for tables.md and stats.json")
    p.add_argument("--ours", default=gb.ARM_OURS)
    p.add_argument("--baselines", default=",".join(gb.BASELINES))
    p.add_argument("--collection", action="append")
    p.add_argument(
        "--min-valid-seeds",
        type=int,
        default=gb.MIN_VALID_SEEDS,
        help="seeds clearing MIN_USABLE a cell needs (pre-registered 10; lower only for a pilot)",
    )
    p.add_argument(
        "--rq6-rows",
        default=str(gb.RQ6_ROWS),
        help="RQ6 rows_samples.csv for the reproduction check ('' to skip)",
    )
    return p


if __name__ == "__main__":
    run(build_parser().parse_args())
