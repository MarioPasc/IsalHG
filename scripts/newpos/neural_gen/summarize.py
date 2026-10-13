# ruff: noqa: E501
"""Aggregate the per-unit summaries of the GRU experiment into tables and the HC1/HC2 checks.

Reads ``*.summary.json`` from the results directory; writes ``units.csv``,
``stats.json`` and ``summary.md`` beside them.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parents[2]
for _path in (str(_HERE), str(_REPO_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import numpy as np  # noqa: E402
from ng_data import SERIALIZATIONS  # noqa: E402

DEFAULT_RESULTS_DIR = Path(
    "/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/NEWPOS_2026-10-13/neural_gen"
)
FULL_SEED_COUNT = 27
BCA_MIN_SEEDS = 10
BASELINES: tuple[str, ...] = ("fact", "incidence")
HC2_METRICS: tuple[str, ...] = ("usable_per_draw", "vun_per_draw")

UNIT_COLUMNS: tuple[str, ...] = (
    "collection",
    "serialization",
    "seed",
    "n_train",
    "vocab_tokens",
    "max_len",
    "epochs_run",
    "best_epoch",
    "train_secs",
    "wall_secs",
    "peak_gpu_mb",
    "test_bits_per_kb",
    "test_bits_per_token",
    "test_root_bits_per_kb",
    "n_draws",
    "n_decoded",
    "n_connected",
    "n_usable",
    "n_zero_fact_usable",
    "n_unique_usable",
    "n_novel_usable",
    "n_vun",
    "n_capped",
    "n_copy_train",
    "n_copy_heldout",
    "validity",
    "connectivity_given_decoded",
    "usable_per_draw",
    "residual_ood_rate",
    "uniqueness",
    "novelty",
    "vun_per_draw",
)


def load_units(results_dir: Path) -> list[dict[str, Any]]:
    """Every per-unit summary found in ``results_dir``, sorted by key."""
    units = [json.loads(p.read_text(encoding="utf-8")) for p in results_dir.glob("*.summary.json")]
    return sorted(units, key=lambda u: (u["collection"], u["serialization"], u["seed"]))


def group(
    units: Sequence[Mapping[str, Any]],
) -> dict[tuple[str, str], list[Mapping[str, Any]]]:
    """Units keyed by ``(collection, serialization)``, each list sorted by seed."""
    out: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
    for unit in units:
        out.setdefault((unit["collection"], unit["serialization"]), []).append(unit)
    for rows in out.values():
        rows.sort(key=lambda u: u["seed"])
    return out


def ci95(values: Sequence[float]) -> dict[str, Any]:
    """95 % interval of the mean over seeds.

    BCa bootstrap from 10 seeds (the project convention for 27 seeds);
    below that a Student-t interval, labelled, because BCa is meaningless on three
    points.
    """
    data = np.asarray(values, dtype=float)
    n = int(data.size)
    mean = float(data.mean())
    if n < 2 or float(data.std()) == 0.0:
        return {"mean": mean, "low": mean, "high": mean, "method": "degenerate", "n": n}
    if n >= BCA_MIN_SEEDS:
        from experiments.tkde.stats import bca_ci

        interval = bca_ci(data.tolist(), stat="mean")
        return {
            "mean": interval.point,
            "low": interval.low,
            "high": interval.high,
            "method": interval.method,
            "n": n,
        }
    from scipy.stats import t

    half = float(t.ppf(0.975, n - 1) * data.std(ddof=1) / math.sqrt(n))
    return {"mean": mean, "low": mean - half, "high": mean + half, "method": "student_t", "n": n}


def _vector(rows: Sequence[Mapping[str, Any]], key: str) -> list[float]:
    return [float(r[key]) for r in rows if r.get(key) is not None]


def describe(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, Any]:
    """Mean, sd and 95 % interval of one column over seeds."""
    values = _vector(rows, key)
    if not values:
        return {"mean": None, "sd": None, "low": None, "high": None, "method": None, "n": 0}
    interval = ci95(values)
    return {
        "mean": interval["mean"],
        "sd": float(np.std(values, ddof=1)) if len(values) > 1 else 0.0,
        "low": interval["low"],
        "high": interval["high"],
        "method": interval["method"],
        "n": len(values),
    }


def hc1_check(units: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """HC1: every ``w°`` unit has validity = connectivity = 1 exactly."""
    ow = [u for u in units if u["serialization"] == "ow"]
    violations = [
        {
            "unit": f"{u['collection']}__gru_ow__s{u['seed']}",
            "n_rejected": u["n_rejected"],
            "n_decoded": u["n_decoded"],
            "n_connected": u["n_connected"],
        }
        for u in ow
        if u["n_decoded"] != u["n_draws"] or u["n_connected"] != u["n_decoded"]
    ]
    return {
        "n_ow_units": len(ow),
        "n_draws_total": int(sum(u["n_draws"] for u in ow)),
        "n_decoded_total": int(sum(u["n_decoded"] for u in ow)),
        "n_connected_total": int(sum(u["n_connected"] for u in ow)),
        "violations": violations,
        "holds": not violations and bool(ow),
    }


def hc2_tests(units: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """HC2: one-sided paired Wilcoxon (ours > baseline) over seeds, Holm across the family."""
    from experiments.tkde.stats import holm, wilcoxon_paired

    grouped = group(units)
    collections = sorted({c for c, _ in grouped})
    rows: list[dict[str, Any]] = []
    for collection in collections:
        ours = {u["seed"]: u for u in grouped.get((collection, "ow"), [])}
        for baseline in BASELINES:
            theirs = {u["seed"]: u for u in grouped.get((collection, baseline), [])}
            seeds = sorted(set(ours) & set(theirs))
            if not seeds:
                continue
            for metric in HC2_METRICS:
                a = [float(ours[s][metric]) for s in seeds]
                b = [float(theirs[s][metric]) for s in seeds]
                test = wilcoxon_paired(a, b, alternative="greater")
                rows.append(
                    {
                        "collection": collection,
                        "baseline": baseline,
                        "metric": metric,
                        "n_seeds": len(seeds),
                        "mean_ow": float(np.mean(a)),
                        "mean_baseline": float(np.mean(b)),
                        "mean_diff": float(np.mean(np.subtract(a, b))),
                        "p_raw": test["p_value"],
                        "rank_biserial": test["rank_biserial"],
                        "n_nonzero_pairs": test["n"],
                        "ow_greater_in_all_seeds": bool(
                            all(x > y for x, y in zip(a, b, strict=True))
                        ),
                    }
                )
    if rows:
        for row, fix in zip(rows, holm([r["p_raw"] for r in rows]), strict=True):
            row["p_holm"] = fix["p_holm"]
            row["reject_holm_0.05"] = fix["reject"]
    return rows


def aggregate(units: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """All aggregated quantities in one JSON-ready mapping."""
    grouped = group(units)
    cells: dict[str, Any] = {}
    for (collection, serialization), rows in grouped.items():
        cells[f"{collection}|{serialization}"] = {
            "n_seeds": len(rows),
            "seeds": [r["seed"] for r in rows],
            **{
                key: describe(rows, key)
                for key in (
                    "validity",
                    "connectivity_given_decoded",
                    "usable_per_draw",
                    "residual_ood_rate",
                    "uniqueness",
                    "novelty",
                    "vun_per_draw",
                    "test_bits_per_kb",
                    "test_bits_per_token",
                    "test_root_bits_per_kb",
                    "epochs_run",
                    "best_epoch",
                    "train_secs",
                    "wall_secs",
                    "n_capped",
                    "vocab_tokens",
                    "peak_gpu_mb",
                    "n_copy_train",
                    "n_copy_heldout",
                )
            },
        }
    n_seeds = max((c["n_seeds"] for c in cells.values()), default=0)
    return {
        "n_units": len(units),
        "n_seeds_max": n_seeds,
        "descriptive_only": n_seeds < FULL_SEED_COUNT,
        "cells": cells,
        "hc1": hc1_check(units),
        "hc2": hc2_tests(units),
    }


def _fmt(d: Mapping[str, Any], digits: int = 4, *, with_sd: bool = True) -> str:
    if d["mean"] is None:
        return "-"
    text = f"{d['mean']:.{digits}f}"
    if with_sd:
        text += f" ± {d['sd']:.{digits}f}"
    return text


def _fmt_ci(d: Mapping[str, Any], digits: int = 4) -> str:
    if d["mean"] is None:
        return "-"
    return f"{d['mean']:.{digits}f} [{d['low']:.{digits}f}, {d['high']:.{digits}f}]"


def render_markdown(stats: Mapping[str, Any]) -> str:
    """Human-readable tables."""
    cells = stats["cells"]
    collections = sorted({k.split("|")[0] for k in cells})
    lines: list[str] = [
        "# GRU generator over three serializations",
        "",
        f"{stats['n_units']} units; up to {stats['n_seeds_max']} seeds per cell. "
        + (
            "Fewer than 27 seeds: every test below is descriptive."
            if stats["descriptive_only"]
            else "27 seeds: the HC2 tests are confirmatory."
        ),
        "Mean ± sd over seeds. Intervals: 95 % of the mean over seeds "
        "(Student-t below 10 seeds, BCa from 10).",
        "",
    ]
    for collection in collections:
        lines += [f"## {collection}", ""]
        lines += [
            "| serialization | n | validity | conn. (of decoded) | usable/draw | residual r = 1 - usable/draw [95 % CI] "
            "| uniqueness | novelty | VUN/draw |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
        for ser in SERIALIZATIONS:
            c = cells.get(f"{collection}|{ser}")
            if c is None:
                continue
            lines.append(
                f"| {ser} | {c['n_seeds']} | {_fmt(c['validity'])} | {_fmt(c['connectivity_given_decoded'])} "
                f"| {_fmt(c['usable_per_draw'])} | {_fmt_ci(c['residual_ood_rate'])} "
                f"| {_fmt(c['uniqueness'])} | {_fmt(c['novelty'])} | {_fmt(c['vun_per_draw'])} |"
            )
        lines += [
            "",
            "| serialization | test bits/KB | bits/token | root bits/KB (ow) | epochs run | best epoch "
            "| train s | wall s | vocab | capped/10k | train copies | held-out copies |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|",
        ]
        for ser in SERIALIZATIONS:
            c = cells.get(f"{collection}|{ser}")
            if c is None:
                continue
            lines.append(
                f"| {ser} | {_fmt(c['test_bits_per_kb'], 2)} | {_fmt(c['test_bits_per_token'], 3)} "
                f"| {_fmt(c['test_root_bits_per_kb'], 2, with_sd=False)} | {_fmt(c['epochs_run'], 1)} "
                f"| {_fmt(c['best_epoch'], 1)} | {_fmt(c['train_secs'], 1)} | {_fmt(c['wall_secs'], 1)} "
                f"| {c['vocab_tokens']['mean']:.0f} | {_fmt(c['n_capped'], 1)} "
                f"| {_fmt(c['n_copy_train'], 0)} | {_fmt(c['n_copy_heldout'], 1)} |"
            )
        lines.append("")
    hc1 = stats["hc1"]
    lines += [
        "## HC1 (theorem check on `w°`)",
        "",
        f"{hc1['n_ow_units']} `gru_ow` units, {hc1['n_draws_total']} draws: "
        f"{hc1['n_decoded_total']} decoded, {hc1['n_connected_total']} connected. "
        f"HC1 {'holds' if hc1['holds'] else 'FAILS'}; violations: {len(hc1['violations'])}.",
        "",
        "## HC2 (one-sided paired Wilcoxon, ours > baseline; Holm over the family)",
        "",
        "| collection | baseline | metric | n | mean ow | mean baseline | p raw | p Holm | reject | ow > baseline in all seeds |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in stats["hc2"]:
        lines.append(
            f"| {row['collection']} | {row['baseline']} | {row['metric']} | {row['n_seeds']} "
            f"| {row['mean_ow']:.4f} | {row['mean_baseline']:.4f} | {row['p_raw']:.3g} "
            f"| {row['p_holm']:.3g} | {row['reject_holm_0.05']} | {row['ow_greater_in_all_seeds']} |"
        )
    lines.append("")
    return "\n".join(lines)


def write_units_csv(units: Sequence[Mapping[str, Any]], path: Path) -> None:
    """One row per unit with the scalar columns."""
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(UNIT_COLUMNS)
        for unit in units:
            writer.writerow([unit.get(col, "") for col in UNIT_COLUMNS])


def render_sensitivity(
    frozen: Sequence[Mapping[str, Any]], sensitivity: Sequence[Mapping[str, Any]]
) -> str:
    """Side-by-side table of the frozen recipe and a sensitivity recipe on the same seeds."""
    seeds = {u["seed"] for u in sensitivity}
    frozen_cells = group([u for u in frozen if u["seed"] in seeds])
    sens_cells = group(sensitivity)
    cfg = next(iter(sensitivity))["config"]
    lines = [
        "# Sensitivity recipe against the frozen shared recipe (same seeds)",
        "",
        f"Sensitivity: lr {cfg['lr']}, patience {cfg['patience']}, max epochs {cfg['max_epochs']}; "
        f"seeds {sorted(seeds)}. Mean over seeds. `capped` = units that ran all max epochs "
        "without early stopping.",
        "",
        "| collection | serialization | recipe | n | usable/draw | residual r | VUN/draw | test bits/KB | best epoch | epochs run | capped |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for (collection, serialization), rows in sorted(sens_cells.items()):
        for label, cell in (
            ("frozen", frozen_cells.get((collection, serialization), [])),
            ("sensitivity", rows),
        ):
            if not cell:
                continue
            mean = {
                key: float(np.mean(_vector(cell, key)))
                for key in (
                    "usable_per_draw",
                    "residual_ood_rate",
                    "vun_per_draw",
                    "test_bits_per_kb",
                    "best_epoch",
                    "epochs_run",
                )
            }
            capped = sum(1 for u in cell if not u["stopped_early"])
            lines.append(
                f"| {collection} | {serialization} | {label} | {len(cell)} "
                f"| {mean['usable_per_draw']:.4f} | {mean['residual_ood_rate']:.4f} "
                f"| {mean['vun_per_draw']:.4f} | {mean['test_bits_per_kb']:.2f} "
                f"| {mean['best_epoch']:.1f} | {mean['epochs_run']:.1f} | {capped}/{len(cell)} |"
            )
    lines.append("")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> None:
    """Command line entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument(
        "--frozen-dir",
        type=Path,
        default=None,
        help="with --results-dir pointing at a sensitivity directory: also write the comparison "
        "against this frozen-recipe directory",
    )
    args = parser.parse_args(argv)
    units = load_units(args.results_dir)
    if not units:
        raise SystemExit(f"no *.summary.json in {args.results_dir}")
    if args.frozen_dir is not None:
        comparison = render_sensitivity(load_units(args.frozen_dir), units)
        (args.results_dir / "comparison_vs_frozen.md").write_text(comparison, encoding="utf-8")
        print(comparison)
    stats = aggregate(units)
    write_units_csv(units, args.results_dir / "units.csv")
    (args.results_dir / "stats.json").write_text(
        json.dumps(stats, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )
    markdown = render_markdown(stats)
    (args.results_dir / "summary.md").write_text(markdown, encoding="utf-8")
    print(markdown)


if __name__ == "__main__":
    main()
