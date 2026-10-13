"""Tables, paired tests and verdicts of the description-length experiment.

Reads the files ``measure.py`` wrote and produces ``tables.md``, ``stats.json`` and
two flat CSVs. The verdict rule is the pre-registered one (work log, section 2.1):

* a per-member win is a one-sided paired Wilcoxon ``H1: bits(X) > bits(ours)`` with
  Holm-adjusted ``p < 0.05`` and a positive median paired difference;
* a compressor win is a point ratio below 1 with a 95 % bootstrap CI (paired over
  the shared member resamples) entirely below 1, on the self-contained number;
* the headline is claimed only if ``w_o`` wins against every certificate
  granularity under every coder in every primary collection.
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from experiments.tkde.stats import bca_ci, holm, wilcoxon_paired  # noqa: E402

logger = logging.getLogger("compression.analyze")

PRIMARY_COLLECTIONS = ("wd50k66", "ndc_classes")
CONTROL_COLLECTIONS = ("wd50k100", "ndc_substances")
CODERS: dict[str, str] = {
    "fixed_obs": "bits_fixed_obs",
    "fixed_theo": "bits_fixed_theo",
    "ngram1": "bits_ngram1",
    "ngram2": "bits_ngram2",
    "ngram3": "bits_ngram3",
}
EXTRA_CODERS: dict[str, str] = {
    "ngram1_theo": "bits_ngram1_theo",
    "ngram2_theo": "bits_ngram2_theo",
    "ngram3_theo": "bits_ngram3_theo",
}
COMPRESSORS = ("xz", "zstd", "bzip2")
HB1_COMPETITORS = ("cert_bytes", "cert_u32", "cert_rows", "cert_ints", "cert_ints_ut")
HB1_REQUIRED = ("cert_bytes", "cert_rows", "cert_ints")
HB2_COMPETITORS = ("fact", "incid", "fact_noT", "incid_noT", "fact_flat")
PRIMARY_ARMS = ("w_o", "cert_bytes", "cert_rows", "cert_ints", "fact", "incid")
FLAT_VS: dict[str, tuple[str, ...]] = {
    "HB1": ("cert_ints", "cert_ints_ut"),
    "HB2": ("fact_flat",),
}
MIN_STRATUM = 20
ALPHA = 0.05
BCA_RESAMPLES = 2000


def load_collection_data(res: Path, name: str) -> dict[str, Any]:
    """Load every measure.py output of one collection."""
    data: dict[str, Any] = {
        "perkb": pd.read_csv(res / f"perkb_{name}.csv"),
        "alphabets": json.loads((res / f"alphabets_{name}.json").read_text()),
        "members": json.loads((res / f"members_{name}.json").read_text()),
    }
    for key, fname in (
        ("seeds", f"ngram_seeds_{name}.csv"),
        ("comp", f"compressors_{name}.csv"),
        ("comp_point", f"compressors_point_{name}.csv"),
        ("deltas", f"deltas_{name}.csv"),
    ):
        path = res / fname
        data[key] = pd.read_csv(path) if path.exists() else None
    if data["deltas"] is not None:
        frame = data["deltas"]
        frame["net_patch_bytes"] = frame["patch_bytes"] - frame["self_patch_bytes"]
    if data["comp"] is not None:
        frame = data["comp"]
        shift = frame["bytes_per_kb"] - frame["boot_mean"]
        frame["ci_low_c"] = frame["ci_low"] + shift
        frame["ci_high_c"] = frame["ci_high"] + shift
    boot = res / f"compressors_boot_{name}.npz"
    data["boot"] = dict(np.load(boot)) if boot.exists() else {}
    return data


def wide_by_arm(perkb: pd.DataFrame, column: str) -> dict[str, np.ndarray]:
    """Arm to the per-member vector of ``column`` (all arms share one member order)."""
    out: dict[str, np.ndarray] = {}
    order: list[str] | None = None
    for arm, frame in perkb.groupby("representation", sort=False):
        ids = frame["kb_id"].tolist()
        if order is None:
            order = ids
        assert ids == order, f"member order differs for arm {arm}"
        out[str(arm)] = frame[column].to_numpy(dtype=float)
    return out


def _clean(value: Any) -> Any:  # noqa: ANN401 - JSON tree of mixed types
    """JSON-safe copy (numpy scalars and non-finite floats)."""
    if isinstance(value, dict):
        return {str(k): _clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean(v) for v in value]
    if isinstance(value, (np.floating, float)):
        return float(value) if math.isfinite(float(value)) else None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value


def median_ci(values: np.ndarray) -> tuple[float, float, float]:
    """Median with its BCa 95 % interval."""
    interval = bca_ci(values, stat="median", n_resamples=BCA_RESAMPLES, seed=0)
    return interval.point, interval.low, interval.high


def fmt_ci(point: float, low: float, high: float, digits: int = 1) -> str:
    """``point [low, high]``."""
    return f"{point:.{digits}f} [{low:.{digits}f}, {high:.{digits}f}]"


# ---------------------------------------------------------------------------
# Lengths and bits tables
# ---------------------------------------------------------------------------


def lengths_table(perkb: pd.DataFrame) -> pd.DataFrame:
    """Median and mean token length per arm, overall and per stratum (amendment 3)."""
    rows: list[dict[str, Any]] = []
    groupings: list[tuple[str, str | None]] = [
        ("all", None),
        ("structure", "structure"),
        ("fact_bin", "fact_bin"),
    ]
    for label, column in groupings:
        grouped = (
            perkb.groupby(["representation", column])
            if column
            else perkb.groupby(["representation"])
        )
        for key, frame in grouped:
            arm = key[0] if column else key
            stratum = key[1] if column else "all"
            if isinstance(arm, tuple):
                arm = arm[0]
            rows.append(
                {
                    "grouping": label,
                    "stratum": stratum,
                    "representation": arm,
                    "n_members": int(frame["kb_id"].nunique()),
                    "L_median": float(frame["L"].median()),
                    "L_mean": float(frame["L"].mean()),
                }
            )
    return pd.DataFrame(rows)


def bits_table(perkb: pd.DataFrame, columns: dict[str, str]) -> list[dict[str, Any]]:
    """Median bits per KB (BCa CI) per arm and coder, overall."""
    rows: list[dict[str, Any]] = []
    for arm, frame in perkb.groupby("representation", sort=False):
        row: dict[str, Any] = {"representation": arm, "L_median": float(frame["L"].median())}
        for coder, column in columns.items():
            point, low, high = median_ci(frame[column].to_numpy(dtype=float))
            row[coder] = {
                "median": point,
                "low": low,
                "high": high,
                "mean": float(frame[column].mean()),
            }
        rows.append(row)
    return rows


def stratum_medians(perkb: pd.DataFrame) -> pd.DataFrame:
    """Median learned-code bits per arm, structure and fact-count bin (feeds the figure)."""
    frames = []
    for column in ("structure", "fact_bin"):
        grouped = perkb.groupby(["representation", column])
        summary = grouped[
            ["L", "bits_fixed_obs", "bits_fixed_theo", "bits_ngram1", "bits_ngram2", "bits_ngram3"]
        ].median()
        summary["n_members"] = grouped["kb_id"].nunique()
        summary = summary.reset_index().rename(columns={column: "stratum"})
        summary.insert(0, "grouping", column)
        frames.append(summary)
    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------------------
# Paired per-member tests
# ---------------------------------------------------------------------------


def paired_rows(
    wide: dict[str, dict[str, np.ndarray]],
    ours: str,
    competitors: tuple[str, ...],
    mask: np.ndarray | None = None,
) -> list[dict[str, Any]]:
    """Uncorrected one-sided tests ``bits(X) > bits(ours)`` for every competitor and coder."""
    rows: list[dict[str, Any]] = []
    for competitor in competitors:
        for coder in CODERS:
            if ours not in wide[coder] or competitor not in wide[coder]:
                continue
            a = wide[coder][competitor]
            b = wide[coder][ours]
            if mask is not None:
                a, b = a[mask], b[mask]
            diff = a - b
            test = wilcoxon_paired(a, b, alternative="greater")
            point, low, high = (
                median_ci(diff) if np.ptp(diff) > 0 else (float(np.median(diff)),) * 3
            )
            rows.append(
                {
                    "ours": ours,
                    "competitor": competitor,
                    "coder": coder,
                    "n": int(diff.size),
                    "median_ours": float(np.median(b)),
                    "median_competitor": float(np.median(a)),
                    "median_diff": point,
                    "median_diff_low": low,
                    "median_diff_high": high,
                    "ratio_of_medians": float(np.median(a) / np.median(b))
                    if np.median(b) > 0
                    else float("nan"),
                    "frac_ours_fewer": float(np.mean(diff > 0)),
                    "frac_tied": float(np.mean(diff == 0)),
                    "p_raw": test["p_value"],
                    "rank_biserial": test["rank_biserial"],
                }
            )
    return rows


def apply_holm(rows: list[dict[str, Any]]) -> None:
    """Add ``p_holm`` and ``win`` in place (Holm over the given family)."""
    if not rows:
        return
    corrected = holm([r["p_raw"] for r in rows], alpha=ALPHA)
    for row, adj in zip(rows, corrected, strict=True):
        row["p_holm"] = adj["p_holm"]
        row["win"] = bool(adj["reject"] and row["median_diff"] > 0)


# ---------------------------------------------------------------------------
# Compressor comparisons
# ---------------------------------------------------------------------------


def compressor_rows(
    data: dict[str, Any], ours: str, competitors: tuple[str, ...]
) -> list[dict[str, Any]]:
    """Point ratios with paired bootstrap CIs on both numbers, per competitor and compressor."""
    comp = data["comp"]
    boot = data["boot"]
    if comp is None:
        return []
    rows: list[dict[str, Any]] = []
    n = int(comp["n_members"].iloc[0])
    for competitor in competitors:
        for kind in COMPRESSORS:
            for number in ("self_contained", "spec"):
                sel = comp[(comp.compressor == kind) & (comp.number == number)].set_index("arm")
                if ours not in sel.index or competitor not in sel.index:
                    continue
                a, b = sel.loc[competitor, "bytes_total"], sel.loc[ours, "bytes_total"]
                key_a, key_b = f"{competitor}|{kind}|{number}", f"{ours}|{kind}|{number}"
                low = high = float("nan")
                if key_a in boot and key_b in boot:
                    ratio = boot[key_b] / boot[key_a]
                    low, high = (float(q) for q in np.quantile(ratio, [0.025, 0.975]))
                    shift = float(b) / float(a) - float(ratio.mean())
                    low, high = low + shift, high + shift
                rows.append(
                    {
                        "ours": ours,
                        "competitor": competitor,
                        "compressor": kind,
                        "number": number,
                        "bytes_per_kb_ours": float(b) / n,
                        "bytes_per_kb_competitor": float(a) / n,
                        "ratio_ours_over_competitor": float(b) / float(a),
                        "ratio_ci_low": low,
                        "ratio_ci_high": high,
                        "rendering_ours": sel.loc[ours, "rendering"],
                        "rendering_competitor": sel.loc[competitor, "rendering"],
                        "win": bool(float(b) < float(a) and high < 1.0),
                    }
                )
    return rows


# ---------------------------------------------------------------------------
# Deltas (HB3)
# ---------------------------------------------------------------------------


def delta_rows(
    deltas: pd.DataFrame, ours: str, competitors: tuple[str, ...]
) -> list[dict[str, Any]]:
    """Paired one-sided tests on version deltas, per stratum, both directions."""
    rows: list[dict[str, Any]] = []
    strata = {
        "all": np.ones(len(deltas["pair"].unique()), dtype=bool),
    }
    base = deltas[deltas.arm == ours].sort_values("pair")
    cp = base["constant_preserving"].to_numpy(dtype=bool)
    strata["constant_preserving"] = cp
    strata["constant_changing"] = ~cp
    for competitor in competitors:
        other = deltas[deltas.arm == competitor].sort_values("pair")
        if other.empty:
            continue
        for measure in ("patch_bytes", "net_patch_bytes", "edit_distance"):
            a_all = other[measure].to_numpy(dtype=float)
            b_all = base[measure].to_numpy(dtype=float)
            for stratum, mask in strata.items():
                if mask.sum() < 2:
                    continue
                a, b = a_all[mask], b_all[mask]
                smaller = wilcoxon_paired(a, b, alternative="greater")
                larger = wilcoxon_paired(a, b, alternative="less")
                rows.append(
                    {
                        "ours": ours,
                        "competitor": competitor,
                        "measure": measure,
                        "stratum": stratum,
                        "n_pairs": int(mask.sum()),
                        "median_ours": float(np.median(b)),
                        "mean_ours": float(np.mean(b)),
                        "median_competitor": float(np.median(a)),
                        "mean_competitor": float(np.mean(a)),
                        "frac_ours_smaller": float(np.mean(a > b)),
                        "frac_ours_larger": float(np.mean(a < b)),
                        "p_ours_smaller": smaller["p_value"],
                        "p_ours_larger": larger["p_value"],
                        "rank_biserial": smaller["rank_biserial"],
                    }
                )
    for key in ("p_ours_smaller", "p_ours_larger"):
        corrected = holm([r[key] for r in rows], alpha=ALPHA) if rows else []
        for row, adj in zip(rows, corrected, strict=True):
            row[key.replace("p_", "p_holm_")] = adj["p_holm"]
    for row in rows:
        row["verdict"] = (
            "ours smaller"
            if row["p_holm_ours_smaller"] < ALPHA
            else "ours larger"
            if row["p_holm_ours_larger"] < ALPHA
            else "n.s."
        )
    return rows


def delta_summary(deltas: pd.DataFrame) -> pd.DataFrame:
    """Median/mean delta per arm and stratum, with the self-patch calibration."""
    frame = deltas.copy()
    frame["stratum"] = np.where(
        frame["constant_preserving"], "constant_preserving", "constant_changing"
    )
    parts = []
    for stratum, sub in [("all", frame), *list(frame.groupby("stratum"))]:
        agg = sub.groupby("arm").agg(
            n_pairs=("pair", "nunique"),
            patch_median=("patch_bytes", "median"),
            patch_mean=("patch_bytes", "mean"),
            net_median=("net_patch_bytes", "median"),
            net_mean=("net_patch_bytes", "mean"),
            edit_median=("edit_distance", "median"),
            edit_mean=("edit_distance", "mean"),
            self_patch_median=("self_patch_bytes", "median"),
            len_median=("len_b", "median"),
        )
        agg.insert(0, "stratum", stratum)
        parts.append(agg.reset_index())
    return pd.concat(parts, ignore_index=True)


# ---------------------------------------------------------------------------
# Per-collection analysis
# ---------------------------------------------------------------------------


def analyse_collection(res: Path, name: str) -> dict[str, Any]:
    """All statistics of one collection (uncorrected rows carry ``p_raw``; Holm applied later)."""
    data = load_collection_data(res, name)
    perkb: pd.DataFrame = data["perkb"]
    wide = {coder: wide_by_arm(perkb, col) for coder, col in CODERS.items()}
    members = pd.DataFrame(data["members"])
    out: dict[str, Any] = {
        "collection": name,
        "n_members": len(members),
        "star_fraction": float(members["star"].mean()),
        "fact_bin_counts": members["fact_bin"].value_counts().to_dict(),
        "alphabets": data["alphabets"],
        "lengths": lengths_table(perkb),
        "bits": bits_table(perkb, {**CODERS, **EXTRA_CODERS}),
        "stratum_medians": stratum_medians(perkb),
        "tests": {
            "HB1": paired_rows(wide, "w_o", HB1_COMPETITORS),
            "HB2": paired_rows(wide, "w_o", HB2_COMPETITORS),
        },
        "tests_flat": {h: paired_rows(wide, "w_flat", comps) for h, comps in FLAT_VS.items()},
        "strata_tests": {},
        "compressors": {
            "HB1": compressor_rows(data, "w_o", HB1_COMPETITORS),
            "HB2": compressor_rows(data, "w_o", HB2_COMPETITORS),
            "flat_HB1": compressor_rows(data, "w_flat", FLAT_VS["HB1"]),
            "flat_HB2": compressor_rows(data, "w_flat", FLAT_VS["HB2"]),
        },
        "data_comp": data["comp"],
        "seeds": data["seeds"],
    }
    structure = members["star"].to_numpy(dtype=bool)
    strata: dict[str, np.ndarray] = {"star": structure, "relational": ~structure}
    for label in members["fact_bin"].unique():
        strata[str(label)] = (members["fact_bin"] == label).to_numpy()
    strata_rows: list[dict[str, Any]] = []
    for stratum, mask in strata.items():
        if mask.sum() < MIN_STRATUM:
            continue
        rows = [
            r
            for r in paired_rows(wide, "w_o", HB1_COMPETITORS + HB2_COMPETITORS, mask)
            if r["coder"] in ("fixed_obs", "ngram3")
        ]
        apply_holm(rows)
        for r in rows:
            r["stratum"] = stratum
        strata_rows.extend(rows)
    out["strata_tests"] = strata_rows
    if data["deltas"] is not None:
        out["deltas"] = {
            "summary": delta_summary(data["deltas"]),
            "tests": delta_rows(data["deltas"], "w_o", HB1_COMPETITORS + HB2_COMPETITORS),
        }
    return out


def holm_families(results: dict[str, dict[str, Any]]) -> None:
    """Apply Holm within the pre-registered families (primary and control separately)."""
    for names in (PRIMARY_COLLECTIONS, CONTROL_COLLECTIONS):
        present = [n for n in names if n in results]
        for hypothesis in ("HB1", "HB2"):
            rows = [r for n in present for r in results[n]["tests"][hypothesis]]
            apply_holm(rows)
            flat = [r for n in present for r in results[n]["tests_flat"][hypothesis]]
            apply_holm(flat)
    for name, result in results.items():
        if name not in PRIMARY_COLLECTIONS + CONTROL_COLLECTIONS:
            for hypothesis in ("HB1", "HB2"):
                apply_holm(result["tests"][hypothesis])
                apply_holm(result["tests_flat"][hypothesis])


def _win_matrix(
    result: dict[str, Any], tests_key: str, comp_key: str, hypothesis: str
) -> dict[str, dict[str, bool]]:
    """Competitor to coder to win flag, per-member coders then compressors (self-contained)."""
    matrix: dict[str, dict[str, bool]] = {}
    tests = result[tests_key][hypothesis]
    for row in tests:
        matrix.setdefault(row["competitor"], {})[row["coder"]] = row["win"]
    comp_rows = result["compressors"][f"flat_{hypothesis}" if comp_key == "flat" else hypothesis]
    for row in comp_rows:
        if row["number"] == "self_contained":
            matrix.setdefault(row["competitor"], {})[row["compressor"]] = row["win"]
    return matrix


def _every(mats: dict[str, dict[str, dict[str, bool]]], keep: tuple[str, ...] | None) -> bool:
    flags = [
        win
        for mat in mats.values()
        for competitor, by_coder in mat.items()
        if keep is None or competitor in keep
        for win in by_coder.values()
    ]
    return bool(flags) and all(flags)


def verdicts(results: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Win matrices for every collection; headline flags from the primary collections only."""
    out: dict[str, Any] = {}
    for hypothesis, required in (("HB1", HB1_REQUIRED), ("HB2", ("fact", "incid"))):
        matrices = {n: _win_matrix(r, "tests", "w_o", hypothesis) for n, r in results.items()}
        flat = {n: _win_matrix(r, "tests_flat", "flat", hypothesis) for n, r in results.items()}
        primary = {n: m for n, m in matrices.items() if n in PRIMARY_COLLECTIONS}
        primary_flat = {n: m for n, m in flat.items() if n in PRIMARY_COLLECTIONS}
        out[hypothesis] = {
            "matrices_w_o": matrices,
            "matrices_w_flat": flat,
            "required_set_w_o": _every(primary, required),
            "all_set_w_o": _every(primary, None),
            "all_set_w_flat": _every(primary_flat, None),
            "headline": _every(primary, None) and _every(primary_flat, None),
        }
    return out


def _mark(flag: bool | None) -> str:
    """W, L or - for a win flag."""
    return "-" if flag is None else ("W" if flag else "L")


def render_verdicts(verdict: dict[str, Any]) -> str:
    """Markdown matrices: W where the ours-arm wins under the coder, L otherwise."""
    coders = [*CODERS, *COMPRESSORS]
    lines: list[str] = []
    for hypothesis, flags in verdict.items():
        for label, key in (("w_o", "matrices_w_o"), ("w_flat", "matrices_w_flat")):
            lines += [f"### {hypothesis} win matrix, ours = {label} (W = win, L = no win)", ""]
            rows = []
            for name, matrix in flags[key].items():
                for competitor, by_coder in matrix.items():
                    cells = [by_coder.get(c) for c in coders]
                    rows.append(
                        [name, competitor, *[_mark(c) for c in cells]]
                    )
            lines.append(md_table(["collection", "X", *coders], rows))
            lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------


def md_table(header: list[str], rows: list[list[str]]) -> str:
    """GitHub-flavoured Markdown table."""
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    lines.extend("| " + " | ".join(r) + " |" for r in rows)
    return "\n".join(lines)


def render_collection(result: dict[str, Any]) -> str:
    """Markdown section of one collection."""
    name = result["collection"]
    lines = [
        f"## {name} (N = {result['n_members']}, star fraction {result['star_fraction']:.3f})",
        "",
    ]
    lines.append(
        "Fact-count bins: "
        + ", ".join(f"{k}: {v}" for k, v in sorted(result["fact_bin_counts"].items()))
    )
    lines.append("")
    arms = [a for a in result["alphabets"]["observed"]]
    alph = result["alphabets"]
    lines += ["### Alphabets", ""]
    rows = []
    for arm in arms:
        obs = sum(alph["observed"][arm].values())
        theo_total = sum(int(v) for v in alph["theoretical"][arm].values())
        rows.append(
            [
                arm,
                f"{obs:,}",
                f"{math.log2(obs + 1):.2f}",
                f"{theo_total:.3e}" if theo_total > 10**12 else f"{theo_total:,}",
                f"{math.log2(theo_total + 1):.2f}",
            ]
        )
    lines.append(
        md_table(["arm", "|A_obs|", "log2(|A_obs|+1)", "|A_theo|", "log2(|A_theo|+1)"], rows)
    )
    lines += ["", "### Raw token length L (median / mean)", ""]
    lt: pd.DataFrame = result["lengths"]
    overall = lt[lt.grouping == "all"].set_index("representation")
    star = lt[(lt.grouping == "structure")]
    bins = lt[(lt.grouping == "fact_bin")]
    strata_cols = sorted(set(star["stratum"])) + sorted(set(bins["stratum"]))
    rows = []
    for arm in arms:
        row = [arm, f"{overall.loc[arm, 'L_median']:.0f} / {overall.loc[arm, 'L_mean']:.1f}"]
        for stratum in strata_cols:
            sub = lt[(lt.representation == arm) & (lt.stratum == stratum) & (lt.grouping != "all")]
            row.append(
                f"{sub['L_median'].iloc[0]:.0f} / {sub['L_mean'].iloc[0]:.1f}" if len(sub) else "-"
            )
        rows.append(row)
    lines.append(md_table(["arm", "all", *strata_cols], rows))
    lines += ["", "### Median bits per KB [BCa 95 % CI]", ""]
    header = ["arm", "L med", *CODERS.keys(), "ngram3 (theo escape)"]
    rows = []
    for row in result["bits"]:
        cells = [row["representation"], f"{row['L_median']:.0f}"]
        cells += [fmt_ci(row[c]["median"], row[c]["low"], row[c]["high"]) for c in CODERS]
        cells.append(
            fmt_ci(
                row["ngram3_theo"]["median"], row["ngram3_theo"]["low"], row["ngram3_theo"]["high"]
            )
        )
        rows.append(cells)
    lines.append(md_table(header, rows))
    seeds: pd.DataFrame | None = result["seeds"]
    if seeds is not None:
        lines += [
            "",
            "### CV spread of the order-3 median (seeds 0-4, observed-alphabet escape)",
            "",
        ]
        spread = (
            seeds[seeds.order == 3].groupby("representation")["median_bits_obs"].agg(["min", "max"])
        )
        unseen = seeds[(seeds.order == 3) & (seeds.seed == 0)].set_index("representation")[
            "unseen_fraction"
        ]
        rows = [
            [
                arm,
                f"{spread.loc[arm, 'min']:.2f}",
                f"{spread.loc[arm, 'max']:.2f}",
                f"{unseen.loc[arm]:.4f}",
            ]
            for arm in arms
            if arm in spread.index
        ]
        lines.append(md_table(["arm", "min", "max", "unseen-event fraction (seed 0)"], rows))
    for hypothesis in ("HB1", "HB2"):
        lines += [
            "",
            f"### {hypothesis}: ours = w_o, one-sided paired Wilcoxon (X - w_o > 0), "
            "Holm within family",
            "",
        ]
        rows = []
        for r in result["tests"][hypothesis]:
            rows.append(
                [
                    r["competitor"],
                    r["coder"],
                    f"{r['median_competitor']:.1f}",
                    f"{r['median_ours']:.1f}",
                    f"{r['median_diff']:.1f}",
                    f"{r['frac_ours_fewer']:.3f}",
                    f"{r['rank_biserial']:.3f}",
                    f"{r['p_holm']:.2e}",
                    "WIN" if r["win"] else "no",
                ]
            )
        lines.append(
            md_table(
                [
                    "X",
                    "coder",
                    "med X",
                    "med w_o",
                    "med diff",
                    "P(w_o fewer)",
                    "rank-biserial",
                    "p_holm",
                    "w_o wins",
                ],
                rows,
            )
        )
        lines += ["", f"{hypothesis} equal-granularity check: ours = w_flat", ""]
        rows = [
            [
                r["competitor"],
                r["coder"],
                f"{r['median_competitor']:.1f}",
                f"{r['median_ours']:.1f}",
                f"{r['median_diff']:.1f}",
                f"{r['rank_biserial']:.3f}",
                f"{r['p_holm']:.2e}",
                "WIN" if r["win"] else "no",
            ]
            for r in result["tests_flat"][hypothesis]
        ]
        lines.append(
            md_table(
                [
                    "X",
                    "coder",
                    "med X",
                    "med w_flat",
                    "med diff",
                    "rank-biserial",
                    "p_holm",
                    "w_flat wins",
                ],
                rows,
            )
        )
    comp: pd.DataFrame | None = result["data_comp"]
    if comp is not None:
        lines += [
            "",
            "### Generic compressors: bytes per KB (self-contained | spec), rendering",
            "",
        ]
        rows = []
        for arm in arms:
            cells = [arm]
            for kind in COMPRESSORS:
                sc = comp[
                    (comp.arm == arm)
                    & (comp.compressor == kind)
                    & (comp.number == "self_contained")
                ]
                sp = comp[(comp.arm == arm) & (comp.compressor == kind) & (comp.number == "spec")]
                if sc.empty:
                    cells.append("-")
                    continue
                sc, sp = sc.iloc[0], sp.iloc[0]
                cells.append(
                    f"{sc['bytes_per_kb']:.2f} [{sc['ci_low_c']:.2f}, {sc['ci_high_c']:.2f}] "
                    f"{sc['rendering']} | {sp['bytes_per_kb']:.2f} {sp['rendering']}"
                )
            rows.append(cells)
        lines.append(md_table(["arm", *COMPRESSORS], rows))
        lines += [
            "",
            "Compressor wins of w_o (self-contained number; point ratio < 1 and the 95 % "
            "paired distinct-member-bootstrap interval, translated to the full-collection point, "
            "below 1):",
            "",
        ]
        rows = []
        for hypothesis in ("HB1", "HB2"):
            for r in result["compressors"][hypothesis]:
                if r["number"] == "self_contained":
                    rows.append(
                        [
                            hypothesis,
                            r["competitor"],
                            r["compressor"],
                            f"{r['ratio_ours_over_competitor']:.3f}",
                            f"[{r['ratio_ci_low']:.3f}, {r['ratio_ci_high']:.3f}]",
                            "WIN" if r["win"] else "no",
                        ]
                    )
        lines.append(md_table(["hyp", "X", "compressor", "w_o / X", "95 % CI", "w_o wins"], rows))
    if "deltas" in result:
        lines += ["", "### HB3: version deltas (zstd --patch-from bytes, token edit distance)", ""]
        summ: pd.DataFrame = result["deltas"]["summary"]
        rows = [
            [
                r.stratum,
                r.arm,
                str(int(r.n_pairs)),
                f"{r.patch_median:.1f} / {r.patch_mean:.1f}",
                f"{r.self_patch_median:.1f}",
                f"{r.net_median:.1f} / {r.net_mean:.2f}",
                f"{r.edit_median:.1f} / {r.edit_mean:.1f}",
            ]
            for r in summ.itertuples()
        ]
        lines.append(
            md_table(
                [
                    "stratum",
                    "arm",
                    "pairs",
                    "patch bytes med / mean",
                    "self-patch bytes (calibration)",
                    "net patch bytes med / mean",
                    "edit distance med / mean",
                ],
                rows,
            )
        )
        lines += ["", "Paired one-sided tests vs w_o (Holm over this table):", ""]
        rows = [
            [
                r["competitor"],
                r["measure"],
                r["stratum"],
                str(r["n_pairs"]),
                f"{r['median_competitor']:.1f}",
                f"{r['median_ours']:.1f}",
                f"{r['frac_ours_smaller']:.3f}",
                f"{r['p_holm_ours_smaller']:.2e}",
                f"{r['p_holm_ours_larger']:.2e}",
                r["verdict"],
            ]
            for r in result["deltas"]["tests"]
        ]
        lines.append(
            md_table(
                [
                    "X",
                    "measure",
                    "stratum",
                    "pairs",
                    "med X",
                    "med w_o",
                    "P(w_o smaller)",
                    "p_holm(w_o smaller)",
                    "p_holm(w_o larger)",
                    "verdict",
                ],
                rows,
            )
        )
    st = result["strata_tests"]
    if st:
        lines += [
            "",
            "### Stratified tests (exploratory; Holm within stratum; coders fixed_obs and ngram3)",
            "",
        ]
        rows = [
            [
                r["stratum"],
                r["competitor"],
                r["coder"],
                str(r["n"]),
                f"{r['median_competitor']:.1f}",
                f"{r['median_ours']:.1f}",
                f"{r['p_holm']:.1e}",
                "WIN" if r["win"] else "no",
            ]
            for r in st
            if r["competitor"] in HB1_REQUIRED + ("fact", "incid")
        ]
        lines.append(
            md_table(["stratum", "X", "coder", "n", "med X", "med w_o", "p_holm", "w_o wins"], rows)
        )
    lines.append("")
    return "\n".join(lines)


def to_serialisable(result: dict[str, Any]) -> dict[str, Any]:
    """Drop DataFrames; keep everything JSON can carry."""
    keep: dict[str, Any] = {}
    for key, value in result.items():
        if isinstance(value, pd.DataFrame) or key in ("data_comp", "seeds") and value is not None:
            keep[key] = value.to_dict(orient="records")
        elif key == "deltas":
            keep[key] = {
                "summary": value["summary"].to_dict(orient="records"),
                "tests": value["tests"],
            }
        elif key in ("data_comp", "seeds"):
            keep[key] = None
        else:
            keep[key] = value
    return keep


def main(argv: list[str] | None = None) -> None:
    """Command-line entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--res", type=Path, required=True, help="directory with measure.py outputs")
    ap.add_argument("--collections", default="wd50k66,ndc_classes,wd50k100,ndc_substances")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    results: dict[str, dict[str, Any]] = {}
    for name in args.collections.split(","):
        if not (args.res / f"perkb_{name}.csv").exists():
            logger.warning("no data for %s", name)
            continue
        logger.info("analysing %s", name)
        results[name] = analyse_collection(args.res, name)
    holm_families(results)
    verdict = verdicts(results)
    sections = [
        "# Description length of a knowledge base: w_o vs the nauty certificate and baselines",
        "",
    ]
    sections.append("Verdict flags (pre-registered rule):")
    sections.append("")
    for hypothesis, flags in verdict.items():
        sections.append(
            f"- {hypothesis}: required-set(w_o) = {flags['required_set_w_o']}, "
            f"all-set(w_o) = {flags['all_set_w_o']}, "
            f"all-set(w_flat) = {flags['all_set_w_flat']}, HEADLINE = {flags['headline']}"
        )
    sections.append("")
    sections.append(render_verdicts(verdict))
    for result in results.values():
        sections.append(render_collection(result))
    (args.res / "tables.md").write_text("\n".join(sections))
    stats = {
        "verdicts": verdict,
        "collections": {n: to_serialisable(r) for n, r in results.items()},
    }
    (args.res / "stats.json").write_text(json.dumps(_clean(stats), indent=1))
    flat_rows = [
        {"collection": n, "hypothesis": h, **row}
        for n, r in results.items()
        for h in ("HB1", "HB2")
        for row in r["tests"][h]
    ]
    pd.DataFrame(flat_rows).to_csv(args.res / "tests_per_kb.csv", index=False)
    logger.info("wrote tables.md, stats.json, tests_per_kb.csv to %s", args.res)


if __name__ == "__main__":
    main()
