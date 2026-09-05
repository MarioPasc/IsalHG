"""RQ1 analyzer -- the addressing tables of ``DESIGN.md`` §2.

Reads every ``rows_<table>__<unit>.csv`` under ``<root>/RQ1_addressing/`` and
writes ``summary.json``, ``stats.json`` and ``tables.md`` beside them, plus the
design's aggregate ``rows_m0.csv`` (see :mod:`experiments.tkde.rq1` for why that
one table is reduced here rather than emitted by the runner).

It runs on **partial** rows: the campaign is an array and the tables are wanted
while it is still going. Every figure therefore carries its own ``n``, and a
statistic whose sample is too small is reported as ``null`` with that ``n``
rather than being silently omitted.

Statistics follow G5: medians with a cluster bootstrap over the base member,
proportions with Wilson intervals, Spearman ``rho`` with a clustered percentile
bootstrap, and the arm family with a two-sided paired Wilcoxon under Holm.

This module also carries the loading helpers the RQ2 and RQ7 analyzers import,
so the "which files are rows" rule exists once.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from experiments.tkde.config import TkdeError
from experiments.tkde.io import RunPaths, write_stats, write_summary, write_tables_md
from experiments.tkde.stats import (
    Interval,
    bca_ci,
    paired_family,
    spearman_ci,
    wilson_ci,
)

logger = logging.getLogger(__name__)

RQ_FOLDER = "RQ1_addressing"
EXPERIMENT = "addressing"
SMOKE_DIR = "_smoke"
OURS = "fact_rank"
POINTER_ARM = "isalhg_levenshtein"
CERT_ARM = "nauty_cert"

# DESIGN.md section 2, "Gate and fallback": the pooled normalized median of
# fact_rank must land within +-0.05 of these probe values, in the order the
# section lists the corpora, and the pointer arm within +-0.05 of 0.577 -- the
# probe's own pointer number re-scored with an equality-keyed alphabet. The
# probe's published 0.500 compared tokens by hash, and TokenP(i) == TokenN(i)
# under hashing, so it under-reported the pointer response (DESIGN section 2,
# amendment of 2026-09-06).
GATE_FACT_RANK: dict[str, float] = {
    "synthetic_rq1": 0.188,
    "ndc_classes": 0.211,
    "wd50k66": 0.300,
}
GATE_POINTER = 0.577
GATE_TOLERANCE = 0.05
WITHIN_TOKENS = 2


class AnalysisError(TkdeError):
    """The analyzer was pointed at a tree it cannot read."""


# ---------------------------------------------------------------------------
# Loading (shared with the RQ2 and RQ7 analyzers)
# ---------------------------------------------------------------------------


def load_table(root: Path, rq_folder: str, table: str) -> Any:
    """Concatenate every shard's ``rows_<table>__*.csv`` under one RQ folder.

    Parameters
    ----------
    root : Path
        The results root.
    rq_folder : str
        e.g. ``"RQ1_addressing"``.
    table : str
        Table name without the ``rows_`` prefix.

    Returns
    -------
    pandas.DataFrame
        All rows, or an empty frame when nothing has landed yet. A file that
        fails to parse is logged and skipped: a half-written shard must not
        take the whole analysis down while the campaign is still running.
    """
    import pandas as pd

    base = Path(root) / rq_folder
    frames = []
    for path in sorted(base.rglob(f"rows_{table}__*.csv")):
        # A smoke run measures five members under the real unit ids, so its rows
        # must never reach a table. Two guards, because both failure shapes have
        # occurred: a smoke staged into its own _smoke subtree, and (from the
        # 2026-09-05 cluster smokes, whose output could not be removed) untagged
        # files sitting in the real directory. Only a file whose unit segment
        # carries a run tag is a campaign row.
        if SMOKE_DIR in path.parts or not _is_tagged(path, table):
            logger.debug("skipping non-campaign rows %s", path)
            continue
        try:
            frame = pd.read_csv(path)
        except (OSError, ValueError) as exc:
            logger.warning("unreadable rows file %s: %s", path, exc)
            continue
        if not frame.empty:
            frames.append(frame)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _is_tagged(path: Path, table: str) -> bool:
    """True when ``rows_<table>__<8 hex>-<unit>.csv`` -- i.e. a campaign row file.

    The run tag is written by :func:`experiments.tkde.rq1.run_tag` and identifies
    the parameters a row was produced under. A file without one predates the tag
    and is not part of any campaign.
    """
    import re

    stem = path.name[len(f"rows_{table}__") : -len(".csv")]
    return bool(re.match(r"^[0-9a-f]{8}-", stem))


def as_dict(interval: Interval | None) -> dict[str, Any] | None:
    """JSON form of an interval, or ``None``."""
    return interval.as_dict() if interval is not None else None


def safe_bca(values: Sequence[float], stat: str = "median") -> dict[str, Any] | None:
    """BCa interval, or ``None`` when the sample is empty."""
    import numpy as np

    array = np.asarray([v for v in values if v == v], dtype=float)
    if array.size == 0:
        return None
    return bca_ci(array, stat=stat).as_dict()


def cluster_median_ci(values: Sequence[float], clusters: Sequence[Any]) -> dict[str, Any] | None:
    """Median with a cluster bootstrap over the natural cluster (G5).

    The cluster is the base knowledge base: the four edits of one member are not
    independent observations, and an i.i.d. interval understates the width. The
    per-cluster medians are the resampling unit, and the interval is the BCa
    interval of their median.
    """
    import numpy as np
    import pandas as pd

    frame = pd.DataFrame({"value": list(values), "cluster": list(clusters)}).dropna()
    if frame.empty:
        return None
    per_cluster = frame.groupby("cluster")["value"].median().to_numpy(dtype=float)
    interval = bca_ci(per_cluster, stat="median")
    payload = interval.as_dict()
    payload["method"] = "bca_median_cluster"
    payload["point"] = float(np.median(frame["value"].to_numpy(dtype=float)))
    payload["n_observations"] = int(len(frame))
    payload["n_clusters"] = int(per_cluster.size)
    return payload


def iqr(values: Sequence[float]) -> list[float] | None:
    """``[q1, q3]`` of a sample, or ``None`` when it is empty."""
    import numpy as np

    array = np.asarray([v for v in values if v == v], dtype=float)
    if array.size == 0:
        return None
    return [float(np.percentile(array, 25)), float(np.percentile(array, 75))]


# ---------------------------------------------------------------------------
# M0 -- exactness and invariance
# ---------------------------------------------------------------------------


def reduce_m0(items: Any) -> Any:
    """Reduce the per-member M0 rows to the design's ``rows_m0`` schema.

    A *false merge* is a pair of members one arm gives the same word but nauty
    separates; a *false split* is the converse. Both are counted exactly, from
    the group sizes, without materialising the pair list.
    """
    import pandas as pd

    if items.empty:
        return pd.DataFrame()

    records: list[dict[str, Any]] = []
    for (collection, arm), group in items.groupby(["collection", "arm"], sort=True):
        usable = group[group["censored"] == 0]
        usable = usable[usable["word_hash"].astype(str) != ""]
        merges = _cross_pairs(usable, "word_hash", "nauty_hash")
        splits = _cross_pairs(usable, "nauty_hash", "word_hash")
        violations = int((group["invariance_ok"] == 0).sum())
        records.append(
            {
                "collection": collection,
                "arm": arm,
                "n_members": int(len(group)),
                "n_usable": int(len(usable)),
                "n_classes_arm": int(usable["word_hash"].nunique()),
                "n_classes_nauty": int(usable["nauty_hash"].nunique()),
                "false_merges": merges,
                "false_splits": splits,
                "invariance_violations": violations,
                "n_censored": int((group["censored"] != 0).sum()),
            }
        )
    return pd.DataFrame(records)


def _cross_pairs(frame: Any, group_key: str, split_key: str) -> int:
    """Pairs sharing ``group_key`` but differing in ``split_key``."""
    total = 0
    for _, group in frame.groupby(group_key, sort=False):
        size = len(group)
        counts = group[split_key].value_counts().to_numpy()
        same = int((counts * (counts - 1) // 2).sum())
        total += size * (size - 1) // 2 - same
    return int(total)


# ---------------------------------------------------------------------------
# M1 -- the single-edit response
# ---------------------------------------------------------------------------


def m1_response(m1: Any) -> Any:
    """Add the normalized response and drop censored or failed measurements."""
    import numpy as np
    import pandas as pd

    if m1.empty:
        return pd.DataFrame()
    frame = m1.copy()
    frame["d_abs"] = pd.to_numeric(frame["d_abs"], errors="coerce")
    frame["len_base"] = pd.to_numeric(frame["len_base"], errors="coerce")
    frame = frame[(frame["censored"] == 0) & frame["d_abs"].notna()]
    # d_abs is measured over the seed-prefixed symbol sequence (the fingerprint
    # F = (seed label, w*)), which has len_base + 1 symbols; the denominator must
    # be the length of the same sequence, not of the bare word.
    frame["normalized"] = np.where(
        frame["len_base"] > 0, frame["d_abs"] / (frame["len_base"] + 1), np.nan
    )
    return frame


def m1_tables(frame: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Per corpus x edit kind x regime medians, IQRs and within-two-tokens rates."""
    rows: list[dict[str, Any]] = []
    if frame.empty:
        return rows, {}

    for (collection, kind, regime, arm), group in frame.groupby(
        ["collection", "edit_kind", "regime", "arm"], sort=True
    ):
        absolute = group["d_abs"].to_numpy(dtype=float)
        normalized = group["normalized"].to_numpy(dtype=float)
        within = int((absolute <= WITHIN_TOKENS).sum())
        rows.append(
            {
                "collection": collection,
                "edit_kind": kind,
                "regime": int(regime),
                "arm": arm,
                "n": int(len(group)),
                "n_base_members": int(group["base_id"].nunique()),
                "median_abs": float(group["d_abs"].median()),
                "iqr_abs": iqr(absolute),
                "median_normalized": float(group["normalized"].median()),
                "iqr_normalized": iqr(normalized),
                "median_abs_ci": cluster_median_ci(absolute, group["base_id"]),
                "median_normalized_ci": cluster_median_ci(normalized, group["base_id"]),
                "within_two_tokens": within,
                "within_two_tokens_rate": as_dict(wilson_ci(within, int(len(group)))),
            }
        )
    return rows, {}


def m1_paired(frame: Any) -> list[dict[str, Any]]:
    """Ours against every other arm on the same instances, per corpus and regime.

    The pairing key is the instance ``(base_id, edit_kind, edit_idx)``: the
    design applies identical edits to every arm precisely so this pairing is
    exact rather than a matched-sample approximation.
    """
    import pandas as pd

    if frame.empty:
        return []

    results: list[dict[str, Any]] = []
    for (collection, regime), group in frame.groupby(["collection", "regime"], sort=True):
        wide = group.pivot_table(
            index=["base_id", "edit_kind", "edit_idx"],
            columns="arm",
            values="normalized",
            aggfunc="first",
        )
        if OURS not in wide.columns:
            continue
        others = [arm for arm in wide.columns if arm != OURS]
        complete = wide[[OURS, *others]].dropna()
        if complete.empty or not others:
            continue
        table = paired_family(
            complete[OURS].to_numpy(dtype=float),
            {arm: complete[arm].to_numpy(dtype=float) for arm in others},
        )
        for row in table:
            results.append(
                {
                    "collection": collection,
                    "regime": int(regime),
                    "n_instances": int(len(complete)),
                    **row,
                }
            )
    if not results:
        return []
    return pd.DataFrame(results).to_dict("records")


def gate_check(frame: Any) -> list[dict[str, Any]]:
    """The design's reproduction gate, evaluated and printed with the tables."""
    rows: list[dict[str, Any]] = []
    if frame.empty:
        return rows
    for collection, group in frame.groupby("collection", sort=True):
        for arm, target in ((OURS, GATE_FACT_RANK.get(collection)), (POINTER_ARM, GATE_POINTER)):
            subset = group[group["arm"] == arm]
            if subset.empty or target is None:
                rows.append(
                    {
                        "collection": collection,
                        "arm": arm,
                        "target": target,
                        "measured": None,
                        "n": int(len(subset)),
                        "within_tolerance": None,
                    }
                )
                continue
            measured = float(subset["normalized"].median())
            rows.append(
                {
                    "collection": collection,
                    "arm": arm,
                    "target": target,
                    "measured": measured,
                    "delta": measured - target,
                    "n": int(len(subset)),
                    "tolerance": GATE_TOLERANCE,
                    "within_tolerance": bool(abs(measured - target) <= GATE_TOLERANCE),
                }
            )
    return rows


# ---------------------------------------------------------------------------
# M2 / M3 / M4
# ---------------------------------------------------------------------------


def m2_correlation(m2: Any) -> list[dict[str, Any]]:
    """Spearman ``rho(delta, d)`` per collection, series, regime and arm."""
    import pandas as pd

    if m2.empty:
        return []
    frame = m2.copy()
    frame["d"] = pd.to_numeric(frame["d"], errors="coerce")
    frame["delta"] = pd.to_numeric(frame["delta"], errors="coerce")
    frame = frame[(frame["censored"] == 0) & frame["d"].notna() & frame["delta"].notna()]

    rows: list[dict[str, Any]] = []
    for (collection, series, regime, arm), group in frame.groupby(
        ["collection", "series", "regime", "arm"], sort=True
    ):
        clusters = group["pair_id"].astype(str).str.split("|").str[0]
        interval = None
        if len(group) >= 3 and group["delta"].nunique() > 1 and group["d"].nunique() > 1:
            interval = spearman_ci(
                group["delta"].to_numpy(dtype=float),
                group["d"].to_numpy(dtype=float),
                clusters=list(clusters),
            ).as_dict()
        rows.append(
            {
                "collection": collection,
                "series": series,
                "regime": int(regime),
                "arm": arm,
                "n": int(len(group)),
                "median_d": float(group["d"].median()),
                "spearman": interval,
            }
        )
    return rows


def m3_cost(m3: Any) -> list[dict[str, Any]]:
    """Tokens and canonicalization wall-clock per collection, arm and ``n`` stratum."""
    import pandas as pd

    if m3.empty:
        return []
    frame = m3.copy()
    frame["secs"] = pd.to_numeric(frame["secs"], errors="coerce")
    frame["tokens"] = pd.to_numeric(frame["tokens"], errors="coerce")
    frame["n_stratum"] = pd.cut(
        frame["n"],
        bins=[0, 8, 12, 16, 20, 24, 10**9],
        labels=["<=8", "9-12", "13-16", "17-20", "21-24", ">24"],
    )

    rows: list[dict[str, Any]] = []
    for (collection, arm, stratum), group in frame.groupby(
        ["collection", "arm", "n_stratum"], observed=True, sort=True
    ):
        finished = group[group["censored"] == 0]
        rows.append(
            {
                "collection": collection,
                "arm": arm,
                "n_stratum": str(stratum),
                "n_members": int(len(group)),
                "n_censored": int((group["censored"] != 0).sum()),
                "censored_fraction": as_dict(
                    wilson_ci(int((group["censored"] != 0).sum()), int(len(group)))
                ),
                "median_tokens": (
                    float(finished["tokens"].median()) if not finished.empty else None
                ),
                "median_secs": float(finished["secs"].median()) if not finished.empty else None,
                "p90_secs": (float(finished["secs"].quantile(0.9)) if not finished.empty else None),
                "median_secs_ci": safe_bca(finished["secs"].to_numpy(dtype=float)),
            }
        )
    return rows


def m4_against_certificate(m4: Any, m1: Any) -> list[dict[str, Any]]:
    """Spearman of each arm against ``nauty_cert``, on random pairs and on M1 pairs."""
    import pandas as pd

    rows: list[dict[str, Any]] = []

    if not m4.empty:
        frame = m4.copy()
        frame["d"] = pd.to_numeric(frame["d"], errors="coerce")
        frame["d_cert"] = pd.to_numeric(frame["d_cert"], errors="coerce")
        frame = frame[frame["d"].notna() & frame["d_cert"].notna()]
        for (collection, arm), group in frame.groupby(["collection", "arm"], sort=True):
            rows.append(_rho_row(collection, "random", arm, group["d"], group["d_cert"], None))

    if not m1.empty:
        frame = m1_response(m1)
        wide = frame.pivot_table(
            index=["collection", "base_id", "edit_kind", "edit_idx"],
            columns="arm",
            values="d_abs",
            aggfunc="first",
        ).reset_index()
        if CERT_ARM in wide.columns:
            for collection, group in wide.groupby("collection", sort=True):
                for arm in group.columns:
                    if arm in ("collection", "base_id", "edit_kind", "edit_idx", CERT_ARM):
                        continue
                    pair = group[[arm, CERT_ARM, "base_id"]].dropna()
                    if pair.empty:
                        continue
                    rows.append(
                        _rho_row(
                            collection,
                            "m1_pairs",
                            arm,
                            pair[arm],
                            pair[CERT_ARM],
                            list(pair["base_id"]),
                        )
                    )
    return rows


def _rho_row(
    collection: str, series: str, arm: str, x: Any, y: Any, clusters: list[Any] | None
) -> dict[str, Any]:
    interval = None
    if len(x) >= 3 and x.nunique() > 1 and y.nunique() > 1:
        interval = spearman_ci(
            x.to_numpy(dtype=float), y.to_numpy(dtype=float), clusters=clusters
        ).as_dict()
    return {
        "collection": collection,
        "series": series,
        "arm": arm,
        "n": int(len(x)),
        "spearman_vs_nauty_cert": interval,
    }


# ---------------------------------------------------------------------------
# Tables and driver
# ---------------------------------------------------------------------------


def _frame(records: Sequence[Mapping[str, Any]], columns: Sequence[str]) -> Any:
    import pandas as pd

    if not records:
        return pd.DataFrame(columns=list(columns))
    frame = pd.DataFrame(list(records))
    keep = [column for column in columns if column in frame.columns]
    return frame[keep]


def _point(value: Any) -> Any:
    return None if not isinstance(value, Mapping) else value.get("point")


def build_tables(summary: Mapping[str, Any]) -> dict[str, Any]:
    """The human-readable tables written to ``tables.md``."""
    import pandas as pd

    m1_rows = []
    for row in summary["m1_response"]:
        m1_rows.append(
            {
                "collection": row["collection"],
                "edit_kind": row["edit_kind"],
                "regime": row["regime"],
                "arm": row["arm"],
                "n": row["n"],
                "median_abs": row["median_abs"],
                "median_norm": row["median_normalized"],
                "within<=2": row["within_two_tokens_rate"]
                and row["within_two_tokens_rate"]["point"],
            }
        )
    tables = {
        "M0 -- exactness and invariance": _frame(
            summary["m0"],
            [
                "collection",
                "arm",
                "n_members",
                "n_classes_arm",
                "n_classes_nauty",
                "false_merges",
                "false_splits",
                "invariance_violations",
                "n_censored",
            ],
        ),
        "M1 -- single-edit response": pd.DataFrame(m1_rows),
        "M1 -- ours vs each arm (Wilcoxon, Holm)": _frame(
            summary["m1_paired"],
            [
                "collection",
                "regime",
                "name",
                "n",
                "mean_ours",
                "mean_other",
                "p_raw",
                "p_holm",
                "reject",
                "rank_biserial",
            ],
        ),
        "Gate (DESIGN.md section 2)": _frame(
            summary["gate"],
            ["collection", "arm", "target", "measured", "delta", "n", "within_tolerance"],
        ),
        "M2 -- rho(delta, d)": pd.DataFrame(
            [
                {
                    "collection": row["collection"],
                    "series": row["series"],
                    "regime": row["regime"],
                    "arm": row["arm"],
                    "n": row["n"],
                    "median_d": row["median_d"],
                    "rho": _point(row["spearman"]),
                }
                for row in summary["m2_correlation"]
            ]
        ),
        "M3 -- tokens and cost": pd.DataFrame(
            [
                {
                    "collection": row["collection"],
                    "arm": row["arm"],
                    "n_stratum": row["n_stratum"],
                    "n_members": row["n_members"],
                    "censored": row["n_censored"],
                    "median_tokens": row["median_tokens"],
                    "median_secs": row["median_secs"],
                    "p90_secs": row["p90_secs"],
                }
                for row in summary["m3_cost"]
            ]
        ),
        "M4 -- rho against nauty_cert": pd.DataFrame(
            [
                {
                    "collection": row["collection"],
                    "series": row["series"],
                    "arm": row["arm"],
                    "n": row["n"],
                    "rho": _point(row["spearman_vs_nauty_cert"]),
                }
                for row in summary["m4"]
            ]
        ),
    }
    return tables


def analyze(root: Path) -> dict[str, Any]:
    """Read the RQ1 rows under ``root`` and write the three analysis files."""
    m0items = load_table(root, RQ_FOLDER, "m0items")
    m1 = load_table(root, RQ_FOLDER, "m1")
    m2 = load_table(root, RQ_FOLDER, "m2")
    m3 = load_table(root, RQ_FOLDER, "m3")
    m4 = load_table(root, RQ_FOLDER, "m4")

    paths = RunPaths(root=root, rq=RQ_FOLDER, experiment=EXPERIMENT)
    paths.ensure()

    m0 = reduce_m0(m0items)
    if not m0.empty:
        m0.to_csv(paths.dir / "rows_m0.csv", index=False)

    response = m1_response(m1)
    response_rows, _ = m1_tables(response)
    summary = {
        "rq": 1,
        "experiment": EXPERIMENT,
        "row_counts": {
            "m0items": int(len(m0items)),
            "m1": int(len(m1)),
            "m2": int(len(m2)),
            "m3": int(len(m3)),
            "m4": int(len(m4)),
        },
        "m0": m0.to_dict("records") if not m0.empty else [],
        "m1_response": response_rows,
        "m1_paired": m1_paired(response),
        "gate": gate_check(response),
        "m2_correlation": m2_correlation(m2),
        "m3_cost": m3_cost(m3),
        "m4": m4_against_certificate(m4, m1),
    }
    stats = {
        "confidence": 0.95,
        "wilcoxon_holm": summary["m1_paired"],
        "gate": summary["gate"],
        "spearman_m2": summary["m2_correlation"],
        "spearman_m4": summary["m4"],
        "within_two_tokens": [
            {
                "collection": row["collection"],
                "edit_kind": row["edit_kind"],
                "regime": row["regime"],
                "arm": row["arm"],
                "wilson": row["within_two_tokens_rate"],
            }
            for row in response_rows
        ],
    }
    write_summary(paths, summary)
    write_stats(paths, stats)
    write_tables_md(paths, build_tables(summary))
    return summary


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(prog="experiments.tkde.analyze_rq1", description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args(argv)
    summary = analyze(args.root)
    print(json.dumps(summary["row_counts"], indent=2))
    for row in summary["gate"]:
        print(
            f"gate {row['collection']:>14} {row['arm']:>22}: "
            f"measured={row['measured']} target={row['target']} "
            f"within={row['within_tolerance']} (n={row['n']})"
        )
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
