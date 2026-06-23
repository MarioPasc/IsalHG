"""Produce algorithm-comparison figures from the aggregator's output.

Reads ``items.parquet`` (or ``items.csv``) written by
``aggregate.py`` and emits PDF figures + summary CSVs into the chosen
output directory.

Figures:

- ``wall_clock_by_algo.pdf`` -- per-algorithm wall-clock distributions
  (boxplot grouped by ``(n, r, c)`` cell).
- ``dnf_rate_vs_n.pdf`` -- DNF rate per algorithm as ``n`` grows.
- ``speedup_inplace.pdf`` -- in-place / clone speedup ratio (matched
  pairs on greedy_min vs greedy_min_inplace).
- ``speedup_wl.pdf`` -- WL seed filter / no-filter speedup ratio
  (matched pairs greedy_min_inplace vs greedy_min_inplace_wl_pruned).
- ``fingerprint_length_by_algo.pdf`` -- canonical fingerprint length
  distribution.
- ``canonical_equivalence_table.csv`` -- per-algorithm cross-equivalence
  rate vs greedy_min.

Designed to fail-soft: when matplotlib or pandas are unavailable,
skips that subset and writes a CSV summary instead.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def _load_items(items_path: Path):
    try:
        import pandas as pd
    except ImportError as exc:
        raise SystemExit(f"figures.py requires pandas: {exc}") from exc
    if items_path.suffix == ".parquet":
        return pd.read_parquet(items_path)
    return pd.read_csv(items_path)


def _save_pdf(fig, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(dest, bbox_inches="tight")
    logger.info("wrote %s", dest)


def _plot_wall_clock_by_algo(df, output_dir: Path) -> None:
    import matplotlib.pyplot as plt

    sub = df[df["dnf"] == False][["algorithm", "median_time_s"]].dropna()  # noqa: E712
    if sub.empty:
        logger.warning("no non-DNF rows for wall-clock plot")
        return
    fig, ax = plt.subplots(figsize=(8, 5))
    algos = sorted(sub["algorithm"].unique())
    data = [sub.loc[sub["algorithm"] == a, "median_time_s"].values for a in algos]
    ax.boxplot(data, tick_labels=algos)
    ax.set_yscale("log")
    ax.set_ylabel("median wall-clock (s)")
    ax.set_xlabel("algorithm")
    ax.set_title("Per-item median wall-clock by algorithm")
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    _save_pdf(fig, output_dir / "wall_clock_by_algo.pdf")
    plt.close(fig)


def _plot_dnf_rate_vs_n(df, output_dir: Path) -> None:
    import matplotlib.pyplot as plt

    grouped = df.groupby(["algorithm", "ds_n"])["dnf"].mean().reset_index(name="dnf_rate")
    fig, ax = plt.subplots(figsize=(8, 5))
    for algo, g in grouped.groupby("algorithm"):
        g_sorted = g.sort_values("ds_n")
        ax.plot(g_sorted["ds_n"], g_sorted["dnf_rate"], marker="o", label=algo)
    ax.set_xscale("log")
    ax.set_xlabel("n (vertices)")
    ax.set_ylabel("DNF rate")
    ax.set_title("DNF rate vs n, per algorithm")
    ax.legend(fontsize=7, loc="best")
    _save_pdf(fig, output_dir / "dnf_rate_vs_n.pdf")
    plt.close(fig)


def _plot_speedup_pair(df, baseline: str, variant: str, dest_name: str, output_dir: Path) -> None:
    import matplotlib.pyplot as plt

    key_cols = ["dataset", "ds_n", "ds_r", "ds_c", "ds_seed", "item_id"]
    base = df[df["algorithm"] == baseline].set_index(key_cols)["median_time_s"]
    var = df[df["algorithm"] == variant].set_index(key_cols)["median_time_s"]
    common = base.index.intersection(var.index)
    if common.empty:
        logger.warning("no matched pairs for %s vs %s", baseline, variant)
        return
    ratio = base.loc[common] / var.loc[common]
    ratio = ratio.dropna().replace([float("inf"), float("-inf")], None).dropna()
    if ratio.empty:
        return
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(ratio.values, bins=30)
    ax.axvline(1.0, color="red", linestyle="--", label="parity")
    ax.set_xscale("log")
    ax.set_xlabel(f"speedup ratio ({baseline} time / {variant} time)")
    ax.set_ylabel("count")
    ax.set_title(f"{variant} speedup over {baseline}")
    ax.legend()
    _save_pdf(fig, output_dir / dest_name)
    plt.close(fig)


def _plot_fingerprint_length(df, output_dir: Path) -> None:
    import matplotlib.pyplot as plt

    sub = df[["algorithm", "fp_bytes_length"]].dropna()
    if sub.empty:
        return
    fig, ax = plt.subplots(figsize=(8, 5))
    algos = sorted(sub["algorithm"].unique())
    data = [sub.loc[sub["algorithm"] == a, "fp_bytes_length"].values for a in algos]
    ax.boxplot(data, tick_labels=algos)
    ax.set_ylabel("fingerprint length (bytes)")
    ax.set_xlabel("algorithm")
    ax.set_title("Canonical fingerprint length by algorithm")
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    _save_pdf(fig, output_dir / "fingerprint_length_by_algo.pdf")
    plt.close(fig)


def _equivalence_table(df, output_dir: Path) -> None:
    if "canonical_equivalent_with_greedy_min" not in df.columns:
        logger.warning("no canonical_equivalent_with_greedy_min column")
        return
    sub = df.dropna(subset=["canonical_equivalent_with_greedy_min"])
    if sub.empty:
        return
    table = (
        sub.groupby("algorithm")["canonical_equivalent_with_greedy_min"]
        .agg(["count", "sum", "mean"])
        .rename(columns={"count": "n_items", "sum": "n_equal", "mean": "rate_equal"})
        .reset_index()
    )
    dest = output_dir / "canonical_equivalence_table.csv"
    dest.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(dest, index=False)
    logger.info("wrote %s", dest)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--items", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"]
    )
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    df = _load_items(args.items)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    try:
        import matplotlib  # noqa: F401
    except ImportError:
        logger.warning("matplotlib not installed; only writing CSV table")
        _equivalence_table(df, args.output_dir)
        return 0

    _plot_wall_clock_by_algo(df, args.output_dir)
    _plot_dnf_rate_vs_n(df, args.output_dir)
    _plot_speedup_pair(
        df,
        baseline="greedy_min",
        variant="greedy_min_inplace",
        dest_name="speedup_inplace.pdf",
        output_dir=args.output_dir,
    )
    _plot_speedup_pair(
        df,
        baseline="greedy_min_inplace",
        variant="greedy_min_inplace_wl_pruned",
        dest_name="speedup_wl.pdf",
        output_dir=args.output_dir,
    )
    _plot_fingerprint_length(df, args.output_dir)
    _equivalence_table(df, args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
