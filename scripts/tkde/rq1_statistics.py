"""Confidence intervals and corrected significance tests for the RQ1 tables.

The published RQ1 tables report point estimates on whatever units each arm
happened to complete inside the 60 s budget. Two things are missing and both
change how the numbers may be read.

*Every arm is censored on a different subset*, so the printed tables score arms
on different units. Every comparison here first restricts to the intersection of
the units completed by **all** published arms, and prints that intersection's
size in every table header.

*The rows are not independent.* The edits of one knowledge base share a base
object, the rungs of one ladder share a ladder, and the quarterly members of one
NDC drug class share an entity. Resampling rows would understate every interval,
so every interval is a cluster bootstrap over the natural cluster:

===================  ==================================================
``rows_m1``          the **entity** ``base_id.split("@")[0]``, namespaced
                     by collection -- ndc_classes' 1,381 members are 171
                     independent objects
``rows_m2`` ladder   the **ladder** ``pair_id.split("|")[0]`` -- 1,000
                     ladders of 5 rungs, cross-checked against ``seed``
``rows_m2`` natural  the **entity** ``pair_id.split("@")[0]`` -- 528
                     consecutive-quarter pairs from 61 entities
``rows_m4``          the pair ``pair_id`` (one row per pair per arm)
===================  ==================================================

The cluster keys are structural claims about how the ids are formed, so they are
asserted against the measured inventory rather than trusted; a key that fails to
parse produces one cluster per row, which is exactly the mistake the assertions
exist to catch.

Statistics come from :mod:`experiments.tkde.stats` -- ``bca_ci``,
``wilcoxon_paired``, ``holm`` and ``spearman_ci``. Two estimators that module
does not provide are composed here from its primitives: the cluster bootstrap of
a *ratio* (the within-two-tokens fraction, whose point estimate is pooled over
rows and therefore cannot be an unweighted mean of per-cluster fractions) and
the cluster bootstrap of a *paired difference of Spearman rho*, which must
recompute both correlations on the same resample for the difference to be
paired at all.
"""

from __future__ import annotations

import argparse
import glob
import json
import logging
import math
import sys
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.tkde.stats import (  # noqa: E402 -- needs the repo root on sys.path
    bca_ci,
    holm,
    spearman_ci,
    wilcoxon_paired,
)

logger = logging.getLogger(__name__)


class Rq1StatisticsError(Exception):
    """Base error for this script."""


class ClusterStructureError(Rq1StatisticsError):
    """A cluster key did not parse into the inventory it was measured to have."""


class RestrictionError(Rq1StatisticsError):
    """The common-unit restriction left nothing to score."""


#: The arms of the published D-ART5 table. Every comparison is restricted to the
#: units all of these completed.
PUBLISHED_ARMS: tuple[str, ...] = (
    "wstar_orbit",
    "wstar_rank",
    "isal_ow_struct",
    "isal_ow_rank",
    "isal_ow_rank0",
    "nauty_cert",
    "nauty_cert_rows",
)

#: Every paired comparison is against this arm.
REFERENCE_ARM = "wstar_orbit"

#: M4 correlates every arm against this one.
CERT_ROWS_ARM = "nauty_cert_rows"

DEFAULT_RESAMPLES = 2_000
DEFAULT_SEED = 0
CONFIDENCE = 0.95

#: ``d_instr <= WITHIN_TOKENS`` is the "within two tokens" claim of the M1 table.
WITHIN_TOKENS = 2

M1_UNIT_KEYS: tuple[str, ...] = ("collection", "seed", "base_id", "edit_kind", "edit_idx")
M2_UNIT_KEYS: tuple[str, ...] = ("collection", "seed", "series", "pair_id")
M4_UNIT_KEYS: tuple[str, ...] = ("collection", "seed", "series", "pair_id")

#: Measured M1 inventory per collection: (members, entities). ``ndc_classes``
#: members are ``"<entity>@<quarter>"``; the other two collections have no
#: ``"@"`` and member == entity, so the split is a no-op there.
M1_EXPECTED_INVENTORY: Mapping[str, tuple[int, int]] = {
    "ndc_classes": (1_381, 171),
    "synthetic_rq1": (2_000, 2_000),
    "wd50k66": (3_988, 3_988),
}

#: Collections whose entity key must strictly coarsen the member key. Asserting
#: only "clusters < members" would pass on a key that split wrongly, so the exact
#: count above is the real guard; this is the sibling check that names the cause.
M1_COARSENING_COLLECTIONS: frozenset[str] = frozenset({"ndc_classes"})


@dataclass(frozen=True)
class M2ClusterSpec:
    """How one M2 series' ``pair_id`` decomposes, and the inventory it must have.

    Attributes
    ----------
    separator : str
        Character the cluster id is the prefix of, inside ``pair_id``.
    expected_clusters : int
        Distinct clusters over the whole series.
    expected_rows_per_cluster : int or None
        Exact row count per cluster when the design fixes it (the ladders), else
        ``None``.
    expected_clusters_per_regime : Mapping[int, int]
        Distinct clusters within each ``regime``.
    cross_check_column : str or None
        A column that must induce the identical partition, when one exists.
    """

    separator: str
    expected_clusters: int
    expected_rows_per_cluster: int | None
    expected_clusters_per_regime: Mapping[int, int]
    cross_check_column: str | None


#: Measured M2 inventory. ``ladder`` pair ids read ``"Q1000|t3"``; ``natural``
#: pair ids read ``"3@443|3@444"`` -- ``<entity>@<quarter>`` on both sides, so
#: the cluster is the entity and *not* the pair.
M2_CLUSTER_SPECS: Mapping[str, M2ClusterSpec] = {
    "ladder": M2ClusterSpec(
        separator="|",
        expected_clusters=1_000,
        expected_rows_per_cluster=5,
        expected_clusters_per_regime={1: 1_000},
        cross_check_column="seed",
    ),
    "natural": M2ClusterSpec(
        separator="@",
        expected_clusters=61,
        expected_rows_per_cluster=None,
        expected_clusters_per_regime={0: 50, 1: 39},
        cross_check_column=None,
    ),
}

#: Below this many rows a group is too small for the "one cluster per row means
#: the key did not parse" inference to be safe.
MIN_ROWS_FOR_PARSE_GUARD = 3


# ---------------------------------------------------------------------------
# Loading and censoring
# ---------------------------------------------------------------------------


def load_rows(exp_dir: Path, table: str) -> pd.DataFrame:
    """Concatenate every ``rows_<table>__*.csv`` shard and drop censored rows.

    Parameters
    ----------
    exp_dir : Path
        The experiment directory, ``<root>/RQ1_addressing/<experiment>``.
    table : str
        Table name, one of ``"m1"``, ``"m2"``, ``"m4"``.

    Returns
    -------
    pandas.DataFrame
        Uncensored rows from every shard.

    Raises
    ------
    Rq1StatisticsError
        If no shard exists for the table.
    """
    paths = sorted(glob.glob(str(exp_dir / f"rows_{table}__*.csv")))
    if not paths:
        raise Rq1StatisticsError(f"no rows_{table} shards under {exp_dir}")
    frame = pd.concat([pd.read_csv(path) for path in paths], ignore_index=True)
    logger.info("rows_%s: %d rows in %d shards", table, len(frame), len(paths))
    return drop_censored(frame)


def drop_censored(frame: pd.DataFrame) -> pd.DataFrame:
    """Drop rows whose ``censored`` flag is set.

    The column is written as ``0``/``1`` by the runner but read back as ``bool``
    when a shard happens to hold only the two literals, so both spellings are
    accepted rather than compared against one of them.
    """
    if "censored" not in frame.columns:
        return frame
    flag = frame["censored"]
    if flag.dtype == bool:
        mask = ~flag.to_numpy(dtype=bool)
    else:
        text = flag.astype(str).str.strip().str.lower()
        mask = ~text.isin({"true", "1", "1.0"}).to_numpy(dtype=bool)
    return frame.loc[mask].reset_index(drop=True)


def _numeric(frame: pd.DataFrame, column: str) -> pd.Series:
    """Coerce a column to float, turning the runner's ``""`` misses into NaN."""
    return pd.to_numeric(frame[column], errors="coerce")


# ---------------------------------------------------------------------------
# Cluster keys
# ---------------------------------------------------------------------------


def entity_of(ids: pd.Series) -> pd.Series:
    """Return the entity prefix of an ``"<entity>@<quarter>"`` id.

    A no-op on ids without ``"@"``, which is what makes the key uniform across
    collections whose member already is the entity.
    """
    return ids.astype(str).str.split("@").str[0]


def m1_cluster_key(frame: pd.DataFrame) -> pd.Series:
    """The M1 cluster: the entity behind ``base_id``, namespaced by collection.

    The M1 cells pool the collections, and entity ids are only unique inside a
    collection (``"3"`` names a drug class in ``ndc_classes`` and could name
    anything elsewhere), so the collection is part of the key.
    """
    return frame["collection"].astype(str) + "::" + entity_of(frame["base_id"])


def m1_member_key(frame: pd.DataFrame) -> pd.Series:
    """The M1 member: ``base_id``, namespaced by collection for the same reason."""
    return frame["collection"].astype(str) + "::" + frame["base_id"].astype(str)


def m2_cluster_key(frame: pd.DataFrame) -> pd.Series:
    """The M2 cluster: the ladder or the entity behind ``pair_id``, per series.

    Raises
    ------
    ClusterStructureError
        If a row carries a series with no declared decomposition.
    """
    series = frame["series"].astype(str)
    unknown = sorted(set(series.unique()) - set(M2_CLUSTER_SPECS))
    if unknown:
        raise ClusterStructureError(f"no cluster key declared for m2 series {unknown}")
    pair = frame["pair_id"].astype(str)
    key = pd.Series(index=frame.index, dtype=object)
    for name, spec in M2_CLUSTER_SPECS.items():
        mask = series == name
        if not mask.any():
            continue
        key.loc[mask] = pair.loc[mask].str.split(spec.separator, regex=False).str[0]
    return frame["collection"].astype(str) + "::" + series + "::" + key.astype(str)


def m4_cluster_key(frame: pd.DataFrame) -> pd.Series:
    """The M4 cluster: the sampled pair itself."""
    return (
        frame["collection"].astype(str)
        + "::"
        + frame["series"].astype(str)
        + "::"
        + frame["pair_id"].astype(str)
    )


# ---------------------------------------------------------------------------
# Structural assertions
# ---------------------------------------------------------------------------


def check_m1_structure(frame: pd.DataFrame, *, strict: bool = True) -> list[str]:
    """Assert the measured member/entity inventory of ``rows_m1``.

    Parameters
    ----------
    frame : pandas.DataFrame
        Uncensored ``rows_m1``, before the common-unit restriction.
    strict : bool, optional
        Raise on a mismatch. When False the mismatch is logged and reported.

    Returns
    -------
    list[str]
        One report line per collection.

    Raises
    ------
    ClusterStructureError
        Under ``strict``, when a collection's entity count is not the measured
        one, or when a collection that must coarsen does not.
    """
    lines: list[str] = []
    problems: list[str] = []
    working = frame.assign(_member=m1_member_key(frame), _cluster=m1_cluster_key(frame))
    for collection, group in working.groupby("collection", sort=True):
        members = int(group["_member"].nunique())
        clusters = int(group["_cluster"].nunique())
        lines.append(f"{collection}: {len(group)} rows, {members} members, {clusters} entities")
        expected = M1_EXPECTED_INVENTORY.get(str(collection))
        if expected is not None and clusters != expected[1]:
            problems.append(
                f"{collection}: entity key gave {clusters} clusters, measured {expected[1]}"
            )
        if str(collection) in M1_COARSENING_COLLECTIONS and clusters == members:
            problems.append(
                f"{collection}: entity key gave one cluster per member "
                f"({clusters}), so the '@' split silently failed"
            )
    lines.append(f"pooled: {int(working['_cluster'].nunique())} clusters")
    _report(problems, strict)
    return lines


def check_m2_structure(frame: pd.DataFrame, *, strict: bool = True) -> list[str]:
    """Assert the measured ladder/entity inventory of ``rows_m2``.

    The counts are per *unit* -- the arm dimension is dropped first, because the
    inventory is a property of the corpus and not of which arm completed it.

    Raises
    ------
    ClusterStructureError
        Under ``strict``, on any inventory mismatch.
    """
    lines: list[str] = []
    problems: list[str] = []
    working = frame.assign(_cluster=m2_cluster_key(frame))
    units = working.drop_duplicates(subset=[*M2_UNIT_KEYS])
    for name, spec in M2_CLUSTER_SPECS.items():
        group = units[units["series"].astype(str) == name]
        if group.empty:
            lines.append(f"{name}: absent")
            continue
        clusters = int(group["_cluster"].nunique())
        lines.append(f"{name}: {len(group)} units, {clusters} clusters")
        if clusters != spec.expected_clusters:
            problems.append(
                f"m2/{name}: cluster key gave {clusters} clusters, "
                f"measured {spec.expected_clusters}"
            )
        if spec.expected_rows_per_cluster is not None:
            sizes = group.groupby("_cluster").size()
            if not bool((sizes == spec.expected_rows_per_cluster).all()):
                problems.append(
                    f"m2/{name}: cluster sizes {sorted(set(sizes.tolist()))}, "
                    f"measured a constant {spec.expected_rows_per_cluster}"
                )
        for regime, expected in spec.expected_clusters_per_regime.items():
            observed = int(group[_numeric(group, "regime") == regime]["_cluster"].nunique())
            lines.append(f"{name}: regime {regime} -> {observed} clusters")
            if observed != expected:
                problems.append(
                    f"m2/{name}: regime {regime} gave {observed} clusters, measured {expected}"
                )
        column = spec.cross_check_column
        if column is not None:
            forward = int(group.groupby("_cluster")[column].nunique().max())
            backward = int(group.groupby(column)["_cluster"].nunique().max())
            lines.append(f"{name}: {column} cross-check {forward}/{backward} (both must be 1)")
            if forward != 1 or backward != 1:
                problems.append(
                    f"m2/{name}: the cluster key and {column} induce different partitions "
                    f"(max {forward} {column} per cluster, {backward} clusters per {column})"
                )
    _report(problems, strict)
    return lines


def _report(problems: Sequence[str], strict: bool) -> None:
    """Raise on ``problems`` under ``strict``, otherwise log each one."""
    if not problems:
        return
    message = "; ".join(problems)
    if strict:
        raise ClusterStructureError(message)
    logger.warning("cluster-structure mismatch (not strict): %s", message)


def guard_parse_failure(n_rows: int, n_clusters: int, label: str) -> None:
    """Raise when a cluster key produced exactly one cluster per row.

    A key that failed to parse degenerates to the row identity, and the resulting
    bootstrap silently treats dependent rows as independent. Groups below
    :data:`MIN_ROWS_FOR_PARSE_GUARD` rows are exempt: there the coincidence
    carries no information.

    Raises
    ------
    ClusterStructureError
        When the degenerate partition is observed on a large enough group.
    """
    if n_rows >= MIN_ROWS_FOR_PARSE_GUARD and n_clusters == n_rows:
        raise ClusterStructureError(
            f"{label}: {n_clusters} clusters for {n_rows} rows -- the cluster key did not parse"
        )


# ---------------------------------------------------------------------------
# The restriction that makes arms comparable
# ---------------------------------------------------------------------------


def restrict_to_common_units(
    frame: pd.DataFrame,
    unit_keys: Sequence[str],
    arms: Sequence[str],
    value_column: str,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Keep only the units every requested arm completed.

    "Completed" means the arm has a row for that unit and a finite value in
    ``value_column``; censored rows are already gone. Arms absent from the frame
    entirely are dropped from the requirement and named in the report, because
    requiring an arm that was never run would empty the intersection.

    Parameters
    ----------
    frame : pandas.DataFrame
        Uncensored rows of one table.
    unit_keys : Sequence[str]
        Columns that identify one unit.
    arms : Sequence[str]
        Arms that must all have completed the unit.
    value_column : str
        The response whose finiteness defines completion.

    Returns
    -------
    tuple
        The restricted frame (with ``value_column`` coerced to float) and a
        report holding the requested arms, the arms actually used, the per-arm
        unit counts before restriction, and the intersection size.

    Raises
    ------
    RestrictionError
        If the intersection is empty.
    """
    keys = list(unit_keys)
    working = frame.copy()
    working[value_column] = _numeric(working, value_column)
    working = working[working[value_column].notna()]

    available = set(working["arm"].astype(str).unique())
    used = [arm for arm in arms if arm in available]
    missing = [arm for arm in arms if arm not in available]
    if not used:
        raise RestrictionError(f"none of the requested arms {list(arms)} appear in the frame")

    working = working[working["arm"].astype(str).isin(used)]
    before = {
        str(arm): int(group.drop_duplicates(subset=keys).shape[0])
        for arm, group in working.groupby("arm", sort=True)
    }
    units = working.drop_duplicates(subset=[*keys, "arm"])
    counts = units.groupby(keys, sort=False)["arm"].nunique()
    kept = counts[counts == len(used)].index
    if len(kept) == 0:
        raise RestrictionError(f"no unit was completed by all of {used}")

    # An inner merge rather than ``.loc`` on a reconstructed MultiIndex: the real
    # tree holds ~137k rows and the index route is quadratic-ish on that shape.
    restricted = working.merge(kept.to_frame(index=False), on=keys, how="inner")
    report = {
        "arms_requested": list(arms),
        "arms_used": used,
        "arms_missing": missing,
        "units_per_arm_before": before,
        "units_after": int(len(kept)),
    }
    logger.info(
        "restriction on %s: %d units survive for %d arms", value_column, len(kept), len(used)
    )
    return restricted, report


# ---------------------------------------------------------------------------
# Cluster bootstrap primitives
# ---------------------------------------------------------------------------


def _cluster_layout(labels: Sequence[Any]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Group row positions by cluster.

    Returns
    -------
    tuple
        ``(flat, starts, sizes)`` where ``flat`` lists every row position sorted
        by cluster, ``starts[g]`` indexes ``flat`` where cluster ``g`` begins and
        ``sizes[g]`` is its length.
    """
    codes = np.asarray(pd.factorize(pd.Series(list(labels)).astype(str), sort=True)[0])
    flat = np.argsort(codes, kind="stable")
    sizes = np.bincount(codes[flat])
    starts = np.concatenate(([0], np.cumsum(sizes)[:-1]))
    return flat, starts, sizes


def _draw_cluster_sample(
    rng: np.random.Generator,
    flat: np.ndarray,
    starts: np.ndarray,
    sizes: np.ndarray,
) -> np.ndarray:
    """One cluster-bootstrap resample, built without a per-cluster Python loop."""
    n_groups = sizes.size
    drawn = rng.integers(0, n_groups, size=n_groups)
    counts = sizes[drawn]
    total = int(counts.sum())
    offsets = np.concatenate(([0], np.cumsum(counts)[:-1]))
    positions = np.arange(total) - np.repeat(offsets, counts) + np.repeat(starts[drawn], counts)
    return np.asarray(flat[positions])


def _bca_bounds(
    point: float,
    replicates: np.ndarray,
    jackknife: np.ndarray,
    *,
    confidence: float = CONFIDENCE,
) -> tuple[float, float, str]:
    """BCa bounds from precomputed replicates and leave-one-cluster-out values.

    Bias correction comes from the replicate distribution, acceleration from the
    jackknife skewness; if either is degenerate the percentile interval is
    returned and the method string says so. The bounds are widened to contain the
    point estimate, which only ever binds on a near-degenerate discrete
    statistic.
    """
    from scipy.stats import norm

    finite = replicates[np.isfinite(replicates)]
    if finite.size == 0:
        return point, point, "degenerate"

    alpha = (1.0 - confidence) / 2.0
    below = float(np.mean(finite < point))
    if 0.0 < below < 1.0:
        z0 = float(norm.ppf(below))
        jack = jackknife[np.isfinite(jackknife)]
        centred = float(np.mean(jack)) - jack if jack.size else np.zeros(0)
        squared = float(np.sum(centred**2))
        acceleration = float(np.sum(centred**3)) / (6.0 * squared**1.5) if squared > 0.0 else 0.0
        adjusted: list[float] = []
        for z in (float(norm.ppf(alpha)), float(norm.ppf(1.0 - alpha))):
            denominator = 1.0 - acceleration * (z0 + z)
            adjusted.append(
                float(norm.cdf(z0 + (z0 + z) / denominator)) if denominator != 0.0 else math.nan
            )
        low_q, high_q = adjusted
        if all(math.isfinite(q) for q in adjusted) and 0.0 < low_q < high_q < 1.0:
            low, high = np.percentile(finite, [100.0 * low_q, 100.0 * high_q])
            return min(float(low), point), max(float(high), point), "bca_cluster"

    low, high = np.percentile(finite, [100.0 * alpha, 100.0 * (1.0 - alpha)])
    return min(float(low), point), max(float(high), point), "percentile_cluster"


def cluster_fraction_ci(
    indicator: Sequence[float],
    clusters: Sequence[Any],
    *,
    n_resamples: int = DEFAULT_RESAMPLES,
    seed: int = DEFAULT_SEED,
) -> dict[str, Any] | None:
    """Cluster bootstrap of a pooled proportion, resampling whole clusters.

    The point estimate is the pooled fraction over rows, so the bootstrap has to
    be of that same ratio: each replicate draws clusters with replacement and
    recomputes ``sum(successes) / sum(rows)`` over the drawn clusters. Bounding
    the unweighted mean of per-cluster fractions instead would bound a different
    estimand whenever cluster sizes differ, which on ``ndc_classes`` they do by a
    factor of 47.

    Parameters
    ----------
    indicator : Sequence[float]
        0/1 per row.
    clusters : Sequence[Any]
        Cluster id per row.
    n_resamples : int, optional
        Bootstrap replicates.
    seed : int, optional
        Bootstrap RNG seed.

    Returns
    -------
    dict or None
        ``point``, ``low``, ``high``, ``method``, ``n``, ``n_clusters``; ``None``
        on empty input.
    """
    values = np.asarray(list(indicator), dtype=float)
    if values.size == 0:
        return None
    codes = pd.factorize(pd.Series(list(clusters)).astype(str), sort=True)[0]
    successes = np.bincount(codes, weights=values)
    totals = np.bincount(codes).astype(float)
    point = float(successes.sum() / totals.sum())
    n_clusters = int(totals.size)

    if n_clusters == 1:
        return {
            "point": point,
            "low": point,
            "high": point,
            "method": "degenerate_single_cluster",
            "n": int(values.size),
            "n_clusters": n_clusters,
        }

    rng = np.random.default_rng(seed)
    replicates = np.empty(n_resamples, dtype=float)
    written = 0
    for draws in _chunk_sizes(n_resamples, n_clusters):
        drawn = rng.integers(0, n_clusters, size=(draws, n_clusters))
        numerator = successes[drawn].sum(axis=1)
        denominator = totals[drawn].sum(axis=1)
        replicates[written : written + draws] = np.divide(
            numerator, denominator, out=np.full(draws, np.nan), where=denominator > 0
        )
        written += draws

    jackknife = (successes.sum() - successes) / np.where(
        totals.sum() - totals > 0, totals.sum() - totals, np.nan
    )
    low, high, method = _bca_bounds(point, replicates, jackknife)
    return {
        "point": point,
        "low": max(0.0, low),
        "high": min(1.0, high),
        "method": f"{method}_ratio",
        "n": int(values.size),
        "n_clusters": n_clusters,
    }


def _chunk_sizes(total: int, width: int) -> Iterator[int]:
    """Yield replicate-batch sizes keeping each ``(batch, width)`` draw modest."""
    per_chunk = max(1, min(total, 2_000_000 // max(width, 1)))
    remaining = total
    while remaining > 0:
        size = min(per_chunk, remaining)
        yield size
        remaining -= size


def cluster_median_ci(
    pooled_values: Sequence[float],
    cluster_values: Sequence[float],
    *,
    n_resamples: int = DEFAULT_RESAMPLES,
    seed: int = DEFAULT_SEED,
) -> dict[str, Any] | None:
    """Pooled median with a BCa interval over the per-cluster values.

    Follows ``experiments.tkde.analyze_rq1.cluster_median_ci``: the point is the
    pooled median over rows (the number the published table prints) and the
    interval is the BCa interval of the median of the per-cluster values. The two
    are not the same functional when clusters differ in size; the method string
    names what the interval is, and the bounds are widened to contain the point.
    """
    pooled = np.asarray(list(pooled_values), dtype=float)
    per_cluster = np.asarray(list(cluster_values), dtype=float)
    pooled = pooled[np.isfinite(pooled)]
    per_cluster = per_cluster[np.isfinite(per_cluster)]
    if pooled.size == 0 or per_cluster.size == 0:
        return None
    point = float(np.median(pooled))
    interval = bca_ci(per_cluster, stat="median", n_resamples=n_resamples, seed=seed)
    return {
        "point": point,
        "low": min(float(interval.low), point),
        "high": max(float(interval.high), point),
        "method": f"{interval.method}_cluster",
        "n": int(pooled.size),
        "n_clusters": int(per_cluster.size),
    }


def spearman_rho(x: np.ndarray, y: np.ndarray) -> float:
    """Spearman rho as Pearson on midrank-transformed data.

    Written out rather than called through ``scipy.stats.spearmanr`` because the
    paired-difference bootstrap evaluates it four thousand times per arm and the
    p-value machinery is dead weight there. Returns NaN when either side is
    constant, which is where rho is undefined.
    """
    from scipy.stats import rankdata

    if x.size < MIN_ROWS_FOR_PARSE_GUARD:
        return math.nan
    rx = rankdata(x)
    ry = rankdata(y)
    rx = rx - rx.mean()
    ry = ry - ry.mean()
    denominator = math.sqrt(float(rx @ rx) * float(ry @ ry))
    if denominator == 0.0:
        return math.nan
    return float(rx @ ry) / denominator


def paired_rho_difference(
    x: Sequence[float],
    y_reference: Sequence[float],
    y_other: Sequence[float],
    clusters: Sequence[Any],
    *,
    n_resamples: int = DEFAULT_RESAMPLES,
    seed: int = DEFAULT_SEED,
) -> dict[str, Any] | None:
    """Cluster bootstrap of ``rho(x, y_reference) - rho(x, y_other)``.

    Both correlations are recomputed on the *same* resampled clusters, which is
    what makes the difference paired: an interval built from two independently
    bootstrapped rho would carry the between-replicate variance twice and
    understate how tightly the two arms move together.

    Returns
    -------
    dict or None
        ``point``, ``low``, ``high``, ``p_raw``, ``method``, ``n``,
        ``n_clusters``, ``n_replicates``. ``None`` when either correlation is
        undefined on the observed data.
    """
    predictor = np.asarray(list(x), dtype=float)
    reference = np.asarray(list(y_reference), dtype=float)
    other = np.asarray(list(y_other), dtype=float)
    rho_reference = spearman_rho(predictor, reference)
    rho_other = spearman_rho(predictor, other)
    if not (math.isfinite(rho_reference) and math.isfinite(rho_other)):
        return None

    point = rho_reference - rho_other
    flat, starts, sizes = _cluster_layout(clusters)
    rng = np.random.default_rng(seed)
    replicates: list[float] = []
    for _ in range(n_resamples):
        picked = _draw_cluster_sample(rng, flat, starts, sizes)
        first = spearman_rho(predictor[picked], reference[picked])
        second = spearman_rho(predictor[picked], other[picked])
        if math.isfinite(first) and math.isfinite(second):
            replicates.append(first - second)

    if not replicates:
        return {
            "point": point,
            "low": point,
            "high": point,
            "p_raw": 1.0,
            "method": "degenerate",
            "n": int(predictor.size),
            "n_clusters": int(sizes.size),
            "n_replicates": 0,
        }

    values = np.asarray(replicates, dtype=float)
    alpha = (1.0 - CONFIDENCE) / 2.0
    low, high = np.percentile(values, [100.0 * alpha, 100.0 * (1.0 - alpha)])
    below = int(np.sum(values <= 0.0))
    above = int(np.sum(values >= 0.0))
    p_raw = min(1.0, 2.0 * (min(below, above) + 1) / (values.size + 1))
    return {
        "point": point,
        "low": min(float(low), point),
        "high": max(float(high), point),
        "p_raw": p_raw,
        "method": "percentile_cluster_paired_rho",
        "n": int(predictor.size),
        "n_clusters": int(sizes.size),
        "n_replicates": int(values.size),
    }


def paired_cluster_family(
    reference: np.ndarray,
    others: Mapping[str, np.ndarray],
    *,
    n_resamples: int = DEFAULT_RESAMPLES,
    seed: int = DEFAULT_SEED,
) -> list[dict[str, Any]]:
    """Wilcoxon of the reference against each arm on the same clusters, Holm-corrected.

    Composes ``wilcoxon_paired``, ``bca_ci`` and ``holm`` the way
    ``experiments.tkde.stats.paired_family`` does, but honours this script's
    ``--resamples`` and ``--seed`` instead of that function's fixed 10,000.
    """
    rows: list[dict[str, Any]] = []
    for name, values in others.items():
        test = wilcoxon_paired(reference.tolist(), values.tolist())
        difference = bca_ci(reference - values, stat="mean", n_resamples=n_resamples, seed=seed)
        rows.append(
            {
                "arm": name,
                "n_clusters": int(reference.size),
                "reference_mean": float(np.mean(reference)),
                "arm_mean": float(np.mean(values)),
                "difference_ci": difference.as_dict(),
                "p_raw": float(test["p_value"]),
                "rank_biserial": float(test["rank_biserial"]),
                "n_nonzero": int(test["n"]),
                "n_ties": int(test["n_ties"]),
            }
        )
    for row, correction in zip(rows, holm([r["p_raw"] for r in rows]), strict=True):
        row["p_holm"] = correction["p_holm"]
        row["reject"] = correction["reject"]
    return rows


# ---------------------------------------------------------------------------
# M1
# ---------------------------------------------------------------------------


def analyze_m1(
    frame: pd.DataFrame,
    arms: Sequence[str],
    reference: str,
    *,
    n_resamples: int = DEFAULT_RESAMPLES,
    seed: int = DEFAULT_SEED,
    strict: bool = True,
) -> dict[str, Any]:
    """Per ``(regime, edit_kind)`` descriptives and paired tests on the common set.

    The response is aggregated in two steps before any resampling: rows to
    ``(member, edit_kind)`` (median ``d_instr``; fraction within two tokens), then
    members to entities (median of the member values). Entities are the resampling
    unit and the pairing key.
    """
    structure = check_m1_structure(frame, strict=strict)
    restricted, restriction = restrict_to_common_units(frame, M1_UNIT_KEYS, arms, "d_instr")
    used = [arm for arm in restriction["arms_used"]]
    if reference not in used:
        raise Rq1StatisticsError(f"reference arm {reference!r} is not among {used}")

    restricted = restricted.assign(
        _cluster=m1_cluster_key(restricted),
        _member=m1_member_key(restricted),
        _within=(restricted["d_instr"] <= WITHIN_TOKENS).astype(float),
        _regime=_numeric(restricted, "regime").astype("Int64"),
    )

    cells: list[dict[str, Any]] = []
    for (regime, kind), group in restricted.groupby(["_regime", "edit_kind"], sort=True):
        cells.append(
            _m1_cell(
                group,
                int(regime),
                str(kind),
                used,
                reference,
                n_resamples=n_resamples,
                seed=seed,
            )
        )
    cells.sort(key=lambda cell: (cell["regime"], cell["edit_kind"]))
    return {"structure": structure, "restriction": restriction, "cells": cells}


def _m1_cell(
    group: pd.DataFrame,
    regime: int,
    kind: str,
    arms: Sequence[str],
    reference: str,
    *,
    n_resamples: int,
    seed: int,
) -> dict[str, Any]:
    """Descriptives and both paired families for one ``(regime, edit_kind)`` cell."""
    label = f"m1 regime={regime} kind={kind}"
    per_arm = int(len(group) / max(len(arms), 1))
    guard_parse_failure(per_arm, int(group["_cluster"].nunique()), label)

    member = (
        group.groupby(["arm", "_cluster", "_member"], sort=True)
        .agg(response=("d_instr", "median"), within=("_within", "mean"))
        .reset_index()
    )
    entity = (
        member.groupby(["arm", "_cluster"], sort=True)
        .agg(response=("response", "median"), within=("within", "median"))
        .reset_index()
    )

    descriptives: list[dict[str, Any]] = []
    for arm in arms:
        rows = group[group["arm"] == arm]
        entities = entity[entity["arm"] == arm]
        descriptives.append(
            {
                "arm": arm,
                "n": int(len(rows)),
                "n_members": int(rows["_member"].nunique()),
                "n_clusters": int(rows["_cluster"].nunique()),
                "median_d_instr": cluster_median_ci(
                    rows["d_instr"].to_numpy(dtype=float),
                    entities["response"].to_numpy(dtype=float),
                    n_resamples=n_resamples,
                    seed=seed,
                ),
                "within_two": cluster_fraction_ci(
                    rows["_within"].to_numpy(dtype=float),
                    rows["_cluster"].tolist(),
                    n_resamples=n_resamples,
                    seed=seed,
                ),
            }
        )

    comparisons: dict[str, list[dict[str, Any]]] = {}
    for statistic in ("response", "within"):
        wide = entity.pivot_table(index="_cluster", columns="arm", values=statistic).dropna()
        if wide.empty or reference not in wide.columns:
            comparisons[statistic] = []
            continue
        others = {
            arm: wide[arm].to_numpy(dtype=float)
            for arm in arms
            if arm != reference and arm in wide.columns
        }
        comparisons[statistic] = paired_cluster_family(
            wide[reference].to_numpy(dtype=float),
            others,
            n_resamples=n_resamples,
            seed=seed,
        )

    first = descriptives[0] if descriptives else {"n": 0, "n_members": 0, "n_clusters": 0}
    return {
        "regime": regime,
        "edit_kind": kind,
        "n": int(first["n"]),
        "n_members": int(first["n_members"]),
        "n_clusters": int(first["n_clusters"]),
        "arms": descriptives,
        "comparisons": comparisons,
    }


# ---------------------------------------------------------------------------
# M2
# ---------------------------------------------------------------------------


def analyze_m2(
    frame: pd.DataFrame,
    arms: Sequence[str],
    reference: str,
    *,
    n_resamples: int = DEFAULT_RESAMPLES,
    seed: int = DEFAULT_SEED,
    strict: bool = True,
) -> dict[str, Any]:
    """Per ``(collection, series, regime)`` clustered rho and paired rho differences."""
    structure = check_m2_structure(frame, strict=strict)
    restricted, restriction = restrict_to_common_units(frame, M2_UNIT_KEYS, arms, "d")
    used = list(restriction["arms_used"])
    if reference not in used:
        raise Rq1StatisticsError(f"reference arm {reference!r} is not among {used}")

    restricted = restricted.assign(
        _cluster=m2_cluster_key(restricted),
        _delta=_numeric(restricted, "delta"),
        _regime=_numeric(restricted, "regime").astype("Int64"),
    )

    groups: list[dict[str, Any]] = []
    for (collection, series, regime), group in restricted.groupby(
        ["collection", "series", "_regime"], sort=True
    ):
        groups.append(
            _m2_group(
                group,
                str(collection),
                str(series),
                int(regime),
                used,
                reference,
                n_resamples=n_resamples,
                seed=seed,
            )
        )
    return {"structure": structure, "restriction": restriction, "groups": groups}


def _m2_group(
    group: pd.DataFrame,
    collection: str,
    series: str,
    regime: int,
    arms: Sequence[str],
    reference: str,
    *,
    n_resamples: int,
    seed: int,
) -> dict[str, Any]:
    """Rho per arm and the reference-minus-arm difference for one M2 group."""
    label = f"m2 {collection}/{series}/regime={regime}"
    wide = group.pivot_table(index=["_cluster", *M2_UNIT_KEYS], columns="arm", values="d").dropna()
    deltas = (
        group.drop_duplicates(subset=[*M2_UNIT_KEYS])
        .set_index(list(M2_UNIT_KEYS))["_delta"]
        .reindex(wide.index.droplevel("_cluster"))
        .to_numpy(dtype=float)
    )
    clusters = wide.index.get_level_values("_cluster").tolist()
    n_rows = int(len(wide))
    n_clusters = int(pd.Series(clusters).nunique())
    guard_parse_failure(n_rows, n_clusters, label)

    per_arm: list[dict[str, Any]] = []
    for arm in arms:
        if arm not in wide.columns:
            per_arm.append({"arm": arm, "rho": None})
            continue
        values = wide[arm].to_numpy(dtype=float)
        per_arm.append(
            {"arm": arm, "rho": _rho_interval(deltas, values, clusters, n_resamples, seed)}
        )

    differences: list[dict[str, Any]] = []
    if reference in wide.columns:
        reference_values = wide[reference].to_numpy(dtype=float)
        for arm in arms:
            if arm == reference or arm not in wide.columns:
                continue
            differences.append(
                {
                    "arm": arm,
                    "difference": paired_rho_difference(
                        deltas,
                        reference_values,
                        wide[arm].to_numpy(dtype=float),
                        clusters,
                        n_resamples=n_resamples,
                        seed=seed,
                    ),
                }
            )
    _apply_holm(differences, "difference")
    return {
        "collection": collection,
        "series": series,
        "regime": regime,
        "n": n_rows,
        "n_clusters": n_clusters,
        "arms": per_arm,
        "differences": differences,
    }


def _rho_interval(
    x: np.ndarray,
    y: np.ndarray,
    clusters: Sequence[Any],
    n_resamples: int,
    seed: int,
) -> dict[str, Any] | None:
    """Clustered ``spearman_ci``, or ``None`` on a degenerate group."""
    finite = np.isfinite(x) & np.isfinite(y)
    if int(finite.sum()) < MIN_ROWS_FOR_PARSE_GUARD:
        return None
    x_used, y_used = x[finite], y[finite]
    if np.unique(x_used).size < 2 or np.unique(y_used).size < 2:
        return None
    labels = [c for c, keep in zip(clusters, finite.tolist(), strict=True) if keep]
    interval = spearman_ci(x_used, y_used, clusters=labels, n_resamples=n_resamples, seed=seed)
    payload = interval.as_dict()
    payload["n_clusters"] = int(pd.Series(labels).nunique())
    return payload


def _apply_holm(rows: list[dict[str, Any]], key: str) -> None:
    """Holm-correct the family of ``p_raw`` values carried under ``rows[i][key]``."""
    testable = [row for row in rows if row.get(key) is not None]
    if not testable:
        return
    corrections = holm([float(row[key]["p_raw"]) for row in testable])
    for row, correction in zip(testable, corrections, strict=True):
        row[key]["p_holm"] = correction["p_holm"]
        row[key]["reject"] = correction["reject"]


# ---------------------------------------------------------------------------
# M4
# ---------------------------------------------------------------------------


def analyze_m4(
    frame: pd.DataFrame,
    arms: Sequence[str],
    *,
    n_resamples: int = DEFAULT_RESAMPLES,
    seed: int = DEFAULT_SEED,
) -> dict[str, Any]:
    """Per-collection rho of each arm's distance against ``nauty_cert_rows``."""
    restricted, restriction = restrict_to_common_units(frame, M4_UNIT_KEYS, arms, "d")
    used = list(restriction["arms_used"])
    if CERT_ROWS_ARM not in used:
        raise Rq1StatisticsError(f"{CERT_ROWS_ARM} is required by M4 but is not among {used}")

    restricted = restricted.assign(_cluster=m4_cluster_key(restricted))
    collections: list[dict[str, Any]] = []
    for collection, group in restricted.groupby("collection", sort=True):
        wide = group.pivot_table(
            index=["_cluster", *M4_UNIT_KEYS], columns="arm", values="d"
        ).dropna()
        clusters = wide.index.get_level_values("_cluster").tolist()
        certificate = wide[CERT_ROWS_ARM].to_numpy(dtype=float)
        rows: list[dict[str, Any]] = []
        for arm in used:
            rows.append(
                {
                    "arm": arm,
                    "rho": _rho_interval(
                        wide[arm].to_numpy(dtype=float),
                        certificate,
                        clusters,
                        n_resamples,
                        seed,
                    ),
                }
            )
        collections.append(
            {
                "collection": str(collection),
                "n": int(len(wide)),
                "n_clusters": int(pd.Series(clusters).nunique()),
                "arms": rows,
            }
        )
    return {"restriction": restriction, "collections": collections}


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

UNIT_SENTENCE = (
    "Units are the Isal engine's completed set at the 60 s budget: the "
    "intersection of the units every published arm completed uncensored."
)


def _fmt(value: float | None, digits: int = 3) -> str:
    """Format a float for a Markdown cell, or ``--`` when it is missing."""
    if value is None or (isinstance(value, float) and not math.isfinite(value)):
        return "--"
    return f"{value:.{digits}f}"


def _fmt_interval(payload: Mapping[str, Any] | None, digits: int = 3) -> str:
    """``point [low, high]`` for an interval payload, or ``--``."""
    if payload is None:
        return "--"
    return (
        f"{_fmt(payload.get('point'), digits)} "
        f"[{_fmt(payload.get('low'), digits)}, {_fmt(payload.get('high'), digits)}]"
    )


def _fmt_p(value: float | None) -> str:
    """A p-value rendered so that very small ones stay readable."""
    if value is None or not math.isfinite(value):
        return "--"
    return f"{value:.3g}" if value >= 1e-4 else f"{value:.1e}"


def _table(header: Sequence[str], rows: Sequence[Sequence[str]]) -> list[str]:
    """A Markdown table, or a placeholder line when there are no rows."""
    if not rows:
        return ["_no rows_", ""]
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join(["---"] * len(header)) + "|"]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    lines.append("")
    return lines


def render_markdown(payload: Mapping[str, Any]) -> str:
    """Render the whole report."""
    run = payload["run"]
    lines = [
        "# RQ1 -- intervals and corrected tests",
        "",
        f"- experiment directory: `{run['exp_dir']}`",
        f"- published arms: {', '.join(run['arms'])}",
        f"- reference arm: `{run['reference']}`",
        f"- bootstrap: {run['n_resamples']} resamples, seed {run['seed']}, "
        f"{int(run['confidence'] * 100)} % intervals",
        "",
        UNIT_SENTENCE,
        "",
    ]
    if "m1" in payload:
        lines += _render_m1(payload["m1"])
    if "m2" in payload:
        lines += _render_m2(payload["m2"])
    if "m4" in payload:
        lines += _render_m4(payload["m4"])
    return "\n".join(lines) + "\n"


def _render_restriction(section: Mapping[str, Any]) -> list[str]:
    """The per-arm unit counts before and after the restriction."""
    restriction = section["restriction"]
    rows = [[arm, str(count)] for arm, count in sorted(restriction["units_per_arm_before"].items())]
    lines = ["**Restriction.** Units completed per arm before the intersection:", ""]
    lines += _table(["arm", "units"], rows)
    lines.append(f"Intersection: **{restriction['units_after']}** units.")
    if restriction["arms_missing"]:
        lines.append(
            f"Arms absent from the rows and therefore not required: "
            f"{', '.join(restriction['arms_missing'])}."
        )
    lines.append("")
    return lines


def _render_m1(section: Mapping[str, Any]) -> list[str]:
    """M1: one subsection per ``(regime, edit_kind)`` cell, pendant first."""
    lines = ["## M1 -- edit response", "", "**Cluster inventory.**", ""]
    lines += [f"- {line}" for line in section["structure"]]
    lines.append("")
    lines += _render_restriction(section)
    for cell in section["cells"]:
        regime = "pendant" if cell["regime"] == 0 else "interior"
        lines += [
            f"### regime {cell['regime']} ({regime}) -- `{cell['edit_kind']}` "
            f"(n = {cell['n']} rows, {cell['n_members']} members, "
            f"{cell['n_clusters']} clusters)",
            "",
        ]
        rows = [
            [
                arm["arm"],
                str(arm["n"]),
                str(arm["n_clusters"]),
                _fmt_interval(arm["median_d_instr"], 2),
                _fmt_interval(arm["within_two"], 4),
            ]
            for arm in cell["arms"]
        ]
        lines += _table(
            ["arm", "n", "n_clusters", "median d_instr [95 % CI]", "within <= 2 [95 % CI]"],
            rows,
        )
        lines.append(UNIT_SENTENCE)
        lines.append("")
        for statistic, title in (
            ("response", "per-entity median `d_instr`"),
            ("within", "per-entity within <= 2 fraction"),
        ):
            lines.append(f"Paired against `{REFERENCE_ARM}` on {title}:")
            lines.append("")
            rows = [
                [
                    row["arm"],
                    str(row["n_clusters"]),
                    _fmt(row["reference_mean"], 4),
                    _fmt(row["arm_mean"], 4),
                    _fmt_interval(row["difference_ci"], 4),
                    _fmt(row["rank_biserial"], 3),
                    _fmt_p(row["p_raw"]),
                    _fmt_p(row.get("p_holm")),
                    "yes" if row.get("reject") else "no",
                ]
                for row in cell["comparisons"].get(statistic, [])
            ]
            lines += _table(
                [
                    "arm",
                    "n_clusters",
                    "reference",
                    "arm",
                    "difference [95 % CI]",
                    "rank-biserial",
                    "p",
                    "p Holm",
                    "reject",
                ],
                rows,
            )
    return lines


def _render_m2(section: Mapping[str, Any]) -> list[str]:
    """M2: rho against the known edit budget, per group."""
    lines = ["## M2 -- response to a known edit budget", "", "**Cluster inventory.**", ""]
    lines += [f"- {line}" for line in section["structure"]]
    lines.append("")
    lines += _render_restriction(section)
    for group in section["groups"]:
        lines += [
            f"### {group['collection']} / {group['series']} / regime {group['regime']} "
            f"(n = {group['n']} pairs, {group['n_clusters']} clusters)",
            "",
        ]
        rows = [
            [entry["arm"], _fmt_interval(entry["rho"], 4), str((entry["rho"] or {}).get("n", "--"))]
            for entry in group["arms"]
        ]
        lines += _table(["arm", "rho(delta, d) [95 % CI]", "n"], rows)
        lines.append(UNIT_SENTENCE)
        lines.append("")
        lines.append(f"Paired difference `{REFERENCE_ARM}` minus arm, same resampled clusters:")
        lines.append("")
        rows = [
            [
                entry["arm"],
                _fmt_interval(entry["difference"], 4),
                _fmt_p((entry["difference"] or {}).get("p_raw")),
                _fmt_p((entry["difference"] or {}).get("p_holm")),
                "yes" if (entry["difference"] or {}).get("reject") else "no",
            ]
            for entry in group["differences"]
        ]
        lines += _table(["arm", "delta rho [95 % CI]", "p", "p Holm", "reject"], rows)
    return lines


def _render_m4(section: Mapping[str, Any]) -> list[str]:
    """M4: rho against the row-granular nauty certificate."""
    lines = [f"## M4 -- agreement with `{CERT_ROWS_ARM}`", ""]
    lines += _render_restriction(section)
    for collection in section["collections"]:
        lines += [
            f"### {collection['collection']} "
            f"(n = {collection['n']} pairs, {collection['n_clusters']} clusters)",
            "",
        ]
        rows = [[entry["arm"], _fmt_interval(entry["rho"], 4)] for entry in collection["arms"]]
        lines += _table(["arm", f"rho vs {CERT_ROWS_ARM} [95 % CI]"], rows)
        lines.append(UNIT_SENTENCE)
        lines.append("")
    return lines


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """The command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path, help="results root")
    parser.add_argument("--experiment", default="addressing")
    parser.add_argument("--out", required=True, type=Path, help="Markdown output path")
    parser.add_argument("--json", type=Path, default=None, help="machine-readable output path")
    parser.add_argument(
        "--measures",
        nargs="*",
        default=["m1", "m2", "m4"],
        choices=["m1", "m2", "m4"],
        help="which measures to compute",
    )
    parser.add_argument("--arms", nargs="*", default=list(PUBLISHED_ARMS))
    parser.add_argument("--reference", default=REFERENCE_ARM)
    parser.add_argument("--resamples", type=int, default=DEFAULT_RESAMPLES)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument(
        "--no-strict-cluster-structure",
        dest="strict",
        action="store_false",
        help="log rather than raise when the measured cluster inventory does not match",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Compute the RQ1 intervals and write the report."""
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    exp_dir = args.root / "RQ1_addressing" / args.experiment

    payload: dict[str, Any] = {
        "run": {
            "exp_dir": str(exp_dir),
            "arms": list(args.arms),
            "reference": args.reference,
            "n_resamples": int(args.resamples),
            "seed": int(args.seed),
            "confidence": CONFIDENCE,
            "strict_cluster_structure": bool(args.strict),
        }
    }
    if "m1" in args.measures:
        payload["m1"] = analyze_m1(
            load_rows(exp_dir, "m1"),
            args.arms,
            args.reference,
            n_resamples=args.resamples,
            seed=args.seed,
            strict=args.strict,
        )
    if "m2" in args.measures:
        payload["m2"] = analyze_m2(
            load_rows(exp_dir, "m2"),
            args.arms,
            args.reference,
            n_resamples=args.resamples,
            seed=args.seed,
            strict=args.strict,
        )
    if "m4" in args.measures:
        payload["m4"] = analyze_m4(
            load_rows(exp_dir, "m4"),
            args.arms,
            n_resamples=args.resamples,
            seed=args.seed,
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render_markdown(payload), encoding="utf-8")
    logger.info("wrote %s", args.out)
    if args.json is not None:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        logger.info("wrote %s", args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
