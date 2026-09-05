"""RQ4 -- the data-quality screen (DESIGN.md §5).

Which descriptions are structurally anomalous, and does exactness change the
answer? Five per cent of a collection's members are *replaced* by a corrupted
version of themselves (the anomaly is a bad record, not a duplicate), the
collection is scored by distance-based outlier detection under each
representation, and the axis is AUROC with the anomaly as positive.

The interesting corruption is ``iso_twin``: a degree-preserving swap sequence
that keeps ``n``, ``m``, the arity histogram, the degree sequence and both
label multisets, and is nauty-verified non-isomorphic to its original. An
incomplete representation cannot see it at all, so H4a predicts chance
behaviour there while the exact arms (``fact_rank``, ``nauty_cert``) score
above it wherever the collection has structural repetition.

**Nothing here recomputes a full matrix.** The inlier-inlier block is read from
the cached matrix built by :mod:`experiments.tkde.matrices` -- for a WD50K
per-type sub-collection, the submatrix of the parent ``wd50k66`` matrix at the
sub-collection's member indices. Only the anomaly rows are new, which is
``0.05 N`` rows rather than ``N``, and they are the run's whole cost: at NetLSD's
measured 1.75 ms/pair a single ``Q5`` (human) unit is ~430 core-seconds.

Unit of work: one ``(sub-collection, corruption, budget, seed)``. Units are
enumerated **seed-major**, so any contiguous bundle of 49 units is exactly one
seed's work across every sub-collection and corruption and therefore costs the
same as any other bundle -- the even split the two-hour bundling rule needs in
order not to produce one four-hour task and one four-minute one.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import logging
import os
import sys
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any

from experiments.tkde import corpora
from experiments.tkde.config import TkdeConfigError, load_yaml, results_root, seeds
from experiments.tkde.io import RunPaths, write_config, write_manifest, write_rows
from experiments.tkde.matrices import (
    MatrixCacheMissingError,
    deploy_stamps,
    load_cached_matrix,
    parse_shard,
    resolve_data_root,
    shard_bounds,
)
from isalhg.datasets.kb.corruptions import corrupt

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray

    from isalhg.core.sparse_hypergraph import SparseHypergraph

logger = logging.getLogger(__name__)

RQ_DIR = "RQ4_screen"
ROWS_SUBDIR = "rows"
RQ_INDEX = 4

#: DESIGN.md §5 Scores. ``fact_rank`` and ``nauty_cert`` are the exact arms
#: H4a is about; the last two are the mandatory naive floors.
DEFAULT_ARMS: tuple[str, ...] = (
    "fact_rank",
    "nauty_cert",
    "wl_l1",
    "netlsd",
    "hpd_jsd",
    "bipartite_ged_path",
    "degree_seq_l1",
    "size_l1",
)
EXACT_ARMS: tuple[str, ...] = ("fact_rank", "nauty_cert")
FLOOR_ARMS: tuple[str, ...] = ("degree_seq_l1", "size_l1")

#: ``(corruption, budget)``. ``iso_twin`` ignores its budget -- it applies as
#: many degree-preserving swaps as non-isomorphy needs -- but ``corrupt``
#: requires a positive one, so it is passed 1 and recorded as such.
DEFAULT_CORRUPTIONS: tuple[tuple[str, int], ...] = (
    ("spurious_fact", 1),
    ("spurious_fact", 2),
    ("missing_fact", 1),
    ("missing_fact", 2),
    ("wrong_argument", 1),
    ("wrong_argument", 2),
    ("iso_twin", 1),
)

CONTAMINATION = 0.05
KNN_K = 5
LOF_K = 20
WORD_ARM = "fact_rank"

_BASE_COLUMNS: tuple[str, ...] = (
    "rq",
    "experiment",
    "collection",
    "seed",
    "arm",
    "secs",
    "censored",
)

ROWS_AUC_COLUMNS: tuple[str, ...] = (
    *_BASE_COLUMNS,
    "subcollection",
    "corruption",
    "budget",
    "score",
    "auc",
    "n_inliers",
    "n_anomalies",
    "n_skipped",
)
ROWS_ANOMALIES_COLUMNS: tuple[str, ...] = (
    "rq",
    "experiment",
    "collection",
    "seed",
    "arm",
    "secs",
    "censored",
    "subcollection",
    "member_id",
    "anomaly_id",
    "corruption",
    "budget",
    "twin_wl1_equal",
    "noniso_verified",
    "constant_set_preserved",
    "connected",
    "n_swaps",
    "realised",
)


@dataclasses.dataclass(frozen=True)
class SubCollection:
    """A scoring population: a whole collection, or one WD50K entity type.

    Anomalies must be judged against their own kind, so WD50K is split by the
    Wikidata P31 class rather than screened as one heterogeneous pool
    (DESIGN.md §5 Corpora (b)).
    """

    name: str
    collection: str
    label: str | None
    min_members: int


@dataclasses.dataclass(frozen=True)
class Experiment:
    """One ``(sub-collection, corruption, budget)`` screen."""

    sub: SubCollection
    corruption: str
    budget: int

    @property
    def name(self) -> str:
        """Return the experiment's stable name."""
        return f"{self.sub.name}__{self.corruption}_b{self.budget}"


@dataclasses.dataclass(frozen=True)
class Unit:
    """One idempotent unit: an experiment at one seed."""

    index: int
    experiment: Experiment
    seed: int

    @property
    def unit_id(self) -> str:
        """Return the stable filename stem of this unit."""
        return f"{self.experiment.name}__seed{self.seed}"


# ---------------------------------------------------------------------------
# Configuration and units
# ---------------------------------------------------------------------------


def build_subcollections(config: Mapping[str, Any], *, smoke: bool) -> list[SubCollection]:
    """Return the scoring populations.

    Parameters
    ----------
    config : Mapping
        Parsed YAML with a ``subcollections`` list.
    smoke : bool
        Use a tiny built-in configuration.

    Returns
    -------
    list[SubCollection]
    """
    if smoke:
        return [SubCollection("ndc_classes", "ndc_classes", None, 0)]
    entries = config.get("subcollections")
    if not entries:
        raise TkdeConfigError("rq4 config needs a `subcollections` list")
    return [
        SubCollection(
            name=str(e["name"]),
            collection=str(e["collection"]),
            label=(str(e["label"]) if e.get("label") is not None else None),
            min_members=int(e.get("min_members", 0)),
        )
        for e in entries
    ]


def build_corruptions(config: Mapping[str, Any], *, smoke: bool) -> list[tuple[str, int]]:
    """Return the ``(corruption, budget)`` pairs this run screens."""
    if smoke:
        return [("spurious_fact", 1), ("iso_twin", 1)]
    entries = config.get("corruptions")
    if not entries:
        return list(DEFAULT_CORRUPTIONS)
    return [(str(e["kind"]), int(e["budget"])) for e in entries]


def enumerate_units(
    subs: Sequence[SubCollection],
    corruptions: Sequence[tuple[str, int]],
    n_seeds: int,
) -> list[Unit]:
    """Return the deterministic, **seed-major** unit list.

    Seed-major is not cosmetic: unit cost is driven by the sub-collection's
    size (a 1,830-member population costs ~30x a 47-member one), so a
    collection-major order would make one contiguous bundle hours long and the
    next one seconds long. With the seed outermost, every block of
    ``len(subs) x len(corruptions)`` consecutive units contains each
    sub-collection exactly once and all bundles cost the same.

    Parameters
    ----------
    subs : Sequence[SubCollection]
    corruptions : Sequence[tuple[str, int]]
    n_seeds : int

    Returns
    -------
    list[Unit]
    """
    units: list[Unit] = []
    for seed in seeds(RQ_INDEX, n_seeds):
        for sub in subs:
            for kind, budget in corruptions:
                units.append(Unit(len(units), Experiment(sub, kind, budget), seed))
    return units


def subcollection_indices(collection: Any, sub: SubCollection) -> list[int]:
    """Return the parent-collection indices this sub-collection scores.

    Parameters
    ----------
    collection : KBCollection
        The parent, in frozen ``records.jsonl`` order.
    sub : SubCollection

    Returns
    -------
    list[int]
        Ascending indices; the whole collection when ``sub.label`` is None.
    """
    if sub.label is None:
        return list(range(len(collection.records)))
    return [i for i, label in enumerate(corpora.labels(collection)) if label == sub.label]


# ---------------------------------------------------------------------------
# Fresh anomaly rows (the only distances this module computes)
# ---------------------------------------------------------------------------

_POOL_STATE: dict[str, Any] = {}


def _row_worker(task: tuple[int, str]) -> tuple[int, str, list[float] | None]:
    """Compute one anomaly's distance row under one arm, inside a fork child.

    Returns ``None`` for the row when the representation raises. A competitor
    that cannot score one corrupted hypergraph must censor that arm, not end
    the task: an exception crossing back out of ``imap_unordered`` kills the
    whole process and takes every completed unit of the shard with it
    (measured -- ``_hpd_vendor.hyperedge_portrait`` raises IndexError on some
    corrupted NDC records, and job 2215163 lost all three tasks to it).
    """
    from isalhg.metric_space.registry import get_distance

    position, arm = task
    items: Sequence[SparseHypergraph] = _POOL_STATE["items"]
    anomaly = items[position]
    try:
        distance = _POOL_STATE["distances"].setdefault(arm, get_distance(arm))
        return position, arm, [float(distance.pairwise(anomaly, other)) for other in items]
    except Exception as exc:  # noqa: BLE001 -- a competitor's failure is data, not a crash
        logger.warning("arm %s failed on anomaly at position %d: %r", arm, position, exc)
        return position, arm, None


def anomaly_rows(
    items: Sequence[SparseHypergraph],
    words: Sequence[Any] | None,
    positions: Sequence[int],
    arms: Sequence[str],
    *,
    n_jobs: int,
) -> dict[tuple[int, str], list[float]]:
    """Return ``d(anomaly, x)`` for every anomaly, every arm, every member.

    The rows include anomaly-to-anomaly distances: an anomaly's neighbours in
    the *modified* collection are what the screen actually sees, and pretending
    the other anomalies are still their originals would score a collection that
    was never assembled.

    ``fact_rank`` is served from precomputed words (one encoding per member,
    then token Levenshtein) rather than through ``pairwise``, which would
    re-derive the canonical labelling on both sides of every call.

    Parameters
    ----------
    items : Sequence[SparseHypergraph]
        The modified collection, anomalies already substituted.
    words : Sequence or None
        Fact words aligned with ``items``, or None to skip the words path.
    positions : Sequence[int]
        Local indices of the anomalies.
    arms : Sequence[str]
        Arm names.
    n_jobs : int
        Worker processes for the ``pairwise`` arms.

    Returns
    -------
    dict[tuple[int, str], list[float]]
        Keyed by ``(position, arm)``. A key is ABSENT when that arm raised on
        that anomaly; the caller censors the arm rather than scoring a matrix
        with a stale row in it.
    """
    from isalhg.metric_space.distances.fact_levenshtein import word_distance

    result: dict[tuple[int, str], list[float]] = {}

    if words is not None and WORD_ARM in arms:
        for position in positions:
            anomaly_word = words[position]
            try:
                result[(position, WORD_ARM)] = [
                    float(word_distance(anomaly_word, other)) for other in words
                ]
            except Exception as exc:  # noqa: BLE001 -- censor the arm, do not end the shard
                logger.warning(
                    "arm %s failed on anomaly at position %d: %r", WORD_ARM, position, exc
                )

    pairwise_arms = [a for a in arms if not (words is not None and a == WORD_ARM)]
    tasks = [(position, arm) for arm in pairwise_arms for position in positions]
    if not tasks:
        return result

    if n_jobs <= 1:
        _POOL_STATE["items"] = items
        _POOL_STATE["distances"] = {}
        for task in tasks:
            position, arm, row = _row_worker(task)
            if row is not None:
                result[(position, arm)] = row
        return result

    import multiprocessing as mp

    _POOL_STATE["items"] = items
    _POOL_STATE["distances"] = {}
    context = mp.get_context("fork")
    with context.Pool(processes=n_jobs) as pool:
        for position, arm, row in pool.imap_unordered(_row_worker, tasks, chunksize=1):
            if row is not None:
                result[(position, arm)] = row
    return result


# ---------------------------------------------------------------------------
# The unit
# ---------------------------------------------------------------------------


def _score_matrix(
    base: NDArray[np.float64],
    rows: Mapping[tuple[int, str], list[float]],
    positions: Sequence[int],
    arm: str,
) -> NDArray[np.float64] | None:
    """Return the modified collection's matrix: cached block plus fresh rows.

    Returns ``None`` when any anomaly row is missing for ``arm``. Substituting
    the cached row of the *pristine* member would score a collection in which
    that anomaly was never injected, which is a wrong number rather than an
    absent one.
    """
    import numpy as np

    if any((position, arm) not in rows for position in positions):
        return None

    D = np.array(base, dtype=np.float64, copy=True)
    for position in positions:
        row = np.asarray(rows[(position, arm)], dtype=np.float64)
        D[position, :] = row
        D[:, position] = row
    np.fill_diagonal(D, 0.0)
    return D


def run_unit(
    unit: Unit,
    *,
    matrices_root: Path,
    corpora_root: Path | str | None,
    arms: Sequence[str],
    n_jobs: int,
    collection_cache: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    """Execute one unit and return its rows, keyed by table name.

    Parameters
    ----------
    unit : Unit
    matrices_root : Path
        Results root holding ``matrices/``. On the cluster this is the shared
        HOME results root, NOT the node-local ``--out`` staging tree: the
        matrices job wrote them once, on another node, and this task only
        reads them.
    corpora_root : Path or str or None
    arms : Sequence[str]
        Representations to score.
    n_jobs : int
        Worker processes.
    collection_cache : dict
        Per-process memo of loaded collections and their derived words.

    Returns
    -------
    dict[str, list[dict]]
        Tables ``auc`` and ``anomalies``.
    """
    import numpy as np

    from isalhg.metric_space.distances.fact_levenshtein import fact_word
    from isalhg.metric_space.toolkit import auroc, knn_score, lof_score

    experiment = unit.experiment
    sub = experiment.sub
    if sub.collection not in collection_cache:
        collection_cache[sub.collection] = corpora.load_collection(sub.collection, corpora_root)
    collection = collection_cache[sub.collection]

    parent_ids = corpora.member_ids(collection)
    # `corpora.hypergraphs` rebuilds the whole collection on every call, so it
    # is memoized here: calling it once per member index turned a linear pass
    # into an O(N^2) one (measured: 24 s per ndc_classes unit against 2 s).
    parent_items_key = f"items::{sub.collection}"
    if parent_items_key not in collection_cache:
        collection_cache[parent_items_key] = corpora.hypergraphs(collection)
    parent_items = collection_cache[parent_items_key]

    indices = subcollection_indices(collection, sub)
    n = len(indices)
    records = [collection.records[i] for i in indices]
    items = [parent_items[i] for i in indices]

    tables: dict[str, list[dict[str, Any]]] = {"auc": [], "anomalies": []}

    n_anomalies_target = max(1, int(round(CONTAMINATION * n)))
    rng = np.random.default_rng(unit.seed)
    chosen = sorted(int(p) for p in rng.choice(n, size=min(n_anomalies_target, n), replace=False))

    # --- realise the corruptions; a member the corruption cannot touch is
    # --- skipped and counted, never silently left as an inlier positive.
    modified = list(items)
    realised: list[int] = []
    n_skipped = 0
    for position in chosen:
        record = records[position]
        anomaly = corrupt(record, experiment.corruption, experiment.budget, unit.seed + position)
        row = {
            "rq": "RQ4",
            "experiment": experiment.name,
            "collection": sub.collection,
            "seed": unit.seed,
            "arm": "",
            "secs": 0.0,
            "censored": 0,
            "subcollection": sub.name,
            "member_id": record.kb_id,
            "anomaly_id": anomaly.kb_id if anomaly is not None else "",
            "corruption": experiment.corruption,
            "budget": experiment.budget,
            "twin_wl1_equal": int(bool(anomaly.meta.get("wl1_equal")))
            if anomaly is not None and experiment.corruption == "iso_twin"
            else "",
            "noniso_verified": int(bool(anomaly.meta.get("noniso_verified")))
            if anomaly is not None
            else 0,
            "constant_set_preserved": int(bool(anomaly.meta.get("constant_set_preserved")))
            if anomaly is not None
            else "",
            "connected": int(bool(anomaly.meta.get("connected"))) if anomaly is not None else "",
            "n_swaps": int(anomaly.meta.get("n_swaps", 0)) if anomaly is not None else "",
            "realised": int(anomaly is not None),
        }
        tables["anomalies"].append(row)
        if anomaly is None:
            n_skipped += 1
            continue
        modified[position] = anomaly.to_hypergraph(
            n_types=collection.n_types, n_preds=collection.n_preds
        )
        realised.append(position)

    if not realised:
        logger.warning("unit %d (%s): no corruption realised", unit.index, unit.unit_id)
        return tables

    is_anomaly = np.zeros(n, dtype=bool)
    is_anomaly[realised] = True

    words = None
    if WORD_ARM in arms:
        key = f"words::{sub.name}"
        if key not in collection_cache:
            collection_cache[key] = [fact_word(h) for h in items]
        words = list(collection_cache[key])
        for position in realised:
            words[position] = fact_word(modified[position])

    started = time.perf_counter()
    rows = anomaly_rows(modified, words, realised, arms, n_jobs=n_jobs)
    secs_rows = time.perf_counter() - started

    for arm in arms:
        arm_started = time.perf_counter()
        try:
            # Memoized: every unit of every seed reads the same matrices, and
            # the wd50k66 parent is 64 MB per arm.
            matrix_key = f"matrix::{sub.collection}::{arm}"
            if matrix_key not in collection_cache:
                collection_cache[matrix_key] = load_cached_matrix(
                    matrices_root, sub.collection, arm, parent_ids
                )
            full = collection_cache[matrix_key]
        except MatrixCacheMissingError as exc:
            logger.error("unit %d arm %s: %s", unit.index, arm, exc)
            for score in ("knn", "lof"):
                tables["auc"].append(
                    _auc_row(unit, arm, score, float("nan"), n, len(realised), n_skipped, 0.0, 1)
                )
            continue

        base = np.asarray(full[np.ix_(indices, indices)], dtype=np.float64)
        D = _score_matrix(base, rows, realised, arm)
        if D is None:
            logger.error("unit %d arm %s: anomaly rows incomplete; censored", unit.index, arm)
            for score in ("knn", "lof"):
                tables["auc"].append(
                    _auc_row(unit, arm, score, float("nan"), n, len(realised), n_skipped, 0.0, 1)
                )
            continue

        for score, k, fn in (("knn", KNN_K, knn_score), ("lof", LOF_K, lof_score)):
            if n <= k + 1:
                # Too few members for this neighbourhood size; censor rather
                # than report a score computed on a degenerate neighbourhood.
                tables["auc"].append(
                    _auc_row(unit, arm, score, float("nan"), n, len(realised), n_skipped, 0.0, 1)
                )
                continue
            values = fn(D, k)
            tables["auc"].append(
                _auc_row(
                    unit,
                    arm,
                    score,
                    float(auroc(values, is_anomaly)),
                    n,
                    len(realised),
                    n_skipped,
                    time.perf_counter() - arm_started + secs_rows / max(1, len(arms)),
                    0,
                )
            )
    return tables


def _auc_row(
    unit: Unit,
    arm: str,
    score: str,
    auc: float,
    n: int,
    n_anomalies: int,
    n_skipped: int,
    secs: float,
    censored: int,
) -> dict[str, Any]:
    """Return one ``rows_auc`` row."""
    return {
        "rq": "RQ4",
        "experiment": unit.experiment.name,
        "collection": unit.experiment.sub.collection,
        "seed": unit.seed,
        "arm": arm,
        "secs": round(secs, 4),
        "censored": censored,
        "subcollection": unit.experiment.sub.name,
        "corruption": unit.experiment.corruption,
        "budget": unit.experiment.budget,
        "score": score,
        "auc": auc,
        "n_inliers": n - n_anomalies,
        "n_anomalies": n_anomalies,
        "n_skipped": n_skipped,
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

_TABLES: dict[str, tuple[str, ...]] = {
    "auc": ROWS_AUC_COLUMNS,
    "anomalies": ROWS_ANOMALIES_COLUMNS,
}


def ensure_smoke_matrices(
    subs: Sequence[SubCollection],
    arms: Sequence[str],
    *,
    matrices_root: Path,
    corpora_root: Path | str | None,
    n_jobs: int = 4,
) -> None:
    """Build the matrices the smoke configuration needs but does not have.

    Production depends on the matrices job and fails loudly without it; the
    local smoke has no such job in front of it.

    Parameters
    ----------
    subs : Sequence[SubCollection]
    arms : Sequence[str]
    matrices_root : Path
    corpora_root : Path or str or None
    n_jobs : int, optional
    """
    from experiments.tkde.matrices import collection_cache_dir
    from isalhg.metric_space.toolkit.matrix import build_matrix

    for name in dict.fromkeys(sub.collection for sub in subs):
        collection = corpora.load_collection(name, corpora_root)
        ids = corpora.member_ids(collection)
        items = corpora.hypergraphs(collection)
        cache_dir = collection_cache_dir(matrices_root, name)
        cache_dir.mkdir(parents=True, exist_ok=True)
        for arm in arms:
            try:
                load_cached_matrix(matrices_root, name, arm, ids)
                continue
            except MatrixCacheMissingError:
                pass
            logger.info("smoke: building %s / %s (%d members)", name, arm, len(ids))
            build_matrix(items, arm, member_ids=ids, cache_dir=cache_dir, n_jobs=n_jobs)


# ---------------------------------------------------------------------------
# Refill of a censored arm
# ---------------------------------------------------------------------------
# A competitor that raised on some corrupted records leaves `censored=1` AUC
# rows behind (see `_row_worker`). Once the library defect is fixed, that arm
# has to be re-scored WITHOUT recomputing the seven arms that succeeded --
# 48 core-hours of work whose numbers are already frozen on disk.
#
# The anomaly set is reproducible exactly: the positions come from
# `np.random.default_rng(unit.seed).choice(n, ...)` over the frozen
# sub-collection order, and each anomaly from
# `corrupt(record, kind, budget, unit.seed + position)`. Both are pure
# functions of the unit, so a refill re-derives the identical collection. It is
# still CHECKED rather than trusted: the re-derived `anomaly_id`s are asserted
# equal to the ones the original run persisted in `rows_anomalies`, and a unit
# whose set does not match is refused rather than rewritten.


class RefillMismatchError(RuntimeError):
    """The re-derived anomaly set differs from the one the original run wrote."""


def _censored_arm_rows(path: Path, arm: str) -> bool:
    """Return True when this unit's AUC file holds a censored row for ``arm``."""
    import csv

    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("arm") == arm and str(row.get("censored")) == "1":
                return True
    return False


def _persisted_anomaly_ids(path: Path) -> list[str]:
    """Return the ``anomaly_id`` column of a persisted rows_anomalies file."""
    import csv

    with path.open(encoding="utf-8", newline="") as handle:
        return [row.get("anomaly_id", "") for row in csv.DictReader(handle)]


def refill_unit(
    unit: Unit,
    arm: str,
    rows_paths: RunPaths,
    *,
    matrices_root: Path,
    corpora_root: Path | str | None,
    n_jobs: int,
    collection_cache: dict[str, Any],
) -> bool:
    """Re-score one arm of one unit in place, leaving every other arm untouched.

    Parameters
    ----------
    unit : Unit
    arm : str
        The arm to re-score.
    rows_paths : RunPaths
        Where this unit's row files live.
    matrices_root : Path
    corpora_root : Path or str or None
    n_jobs : int
    collection_cache : dict

    Returns
    -------
    bool
        True when the unit was rewritten; False when it had no censored row for
        ``arm`` and was therefore left alone.

    Raises
    ------
    RefillMismatchError
        When the re-derived anomaly set differs from the persisted one.
    """
    import csv

    auc_path = rows_paths.dir / f"rows_auc__{unit.unit_id}.csv"
    if not auc_path.exists() or not _censored_arm_rows(auc_path, arm):
        return False

    tables = run_unit(
        unit,
        matrices_root=matrices_root,
        corpora_root=corpora_root,
        arms=[arm],
        n_jobs=n_jobs,
        collection_cache=collection_cache,
    )

    anomalies_path = rows_paths.dir / f"rows_anomalies__{unit.unit_id}.csv"
    if anomalies_path.exists():
        before = _persisted_anomaly_ids(anomalies_path)
        after = [str(row["anomaly_id"]) for row in tables["anomalies"]]
        if before != after:
            raise RefillMismatchError(
                f"unit {unit.unit_id}: re-derived anomaly set differs from the "
                f"persisted one ({len(before)} vs {len(after)} rows); refusing to rewrite"
            )

    with auc_path.open(encoding="utf-8", newline="") as handle:
        kept = [row for row in csv.DictReader(handle) if row.get("arm") != arm]
    merged = [*kept, *tables["auc"]]
    write_rows(rows_paths, f"auc__{unit.unit_id}", merged, columns=ROWS_AUC_COLUMNS)
    return True


def _shard_manifest_stamp(out_root: Path, prefix: str, shard_tag: str) -> str | None:
    """Return the ``src_deploy`` stamp of the shard manifest a refill overwrites.

    A refilled table has two provenances: the arm just re-scored comes from the
    current deployment, every other arm from the run that wrote the shard. The
    manifest records the second one so a reader is not left assuming a single
    library commit produced the whole file.
    """
    path = out_root / RQ_DIR / f"{prefix}shard_{shard_tag}" / "manifest.json"
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("src_deploy")
    except (OSError, ValueError):
        return None


def _unit_done(rows_paths: RunPaths, unit: Unit) -> bool:
    """Return True when this unit's AUC rows already exist."""
    return (rows_paths.dir / f"rows_auc__{unit.unit_id}.csv").exists()


def main(argv: Sequence[str] | None = None) -> int:
    """Command-line entry point.

    Parameters
    ----------
    argv : Sequence[str] or None

    Returns
    -------
    int
        Process exit status.
    """
    parser = argparse.ArgumentParser(description="RQ4 -- the data-quality screen.")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None, help="results root")
    parser.add_argument("--shard", type=str, default=None, help="i/N")
    parser.add_argument("--unit", type=int, default=None)
    parser.add_argument("--count", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--n-jobs", type=int, default=None)
    parser.add_argument(
        "--refill-censored-arm",
        type=str,
        default="",
        help=(
            "re-score ONLY this arm, and only in units whose rows_auc holds a "
            "censored=1 row for it. Everything else on disk is left byte-identical. "
            "Use after a library defect that censored one competitor is fixed."
        ),
    )
    parser.add_argument(
        "--matrices-root",
        type=Path,
        default=None,
        help=(
            "results root holding matrices/ (default: --out). On the cluster the "
            "matrices job wrote them once to the shared HOME results root, while "
            "--out is this task's node-local staging tree, so the two differ."
        ),
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=None,
        help="directory holding corpora/ (Picasso: $ISALHG_DATA_ROOT)",
    )
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--tag",
        type=str,
        default="",
        help=(
            "path component under the RQ folder. A cluster smoke task runs a REAL "
            "unit to prove the deployment, so its rows carry the same unit id the "
            "full run uses; written into the real folder they would make the "
            "idempotent full run skip that unit. Smoke tasks pass `_smoke`."
        ),
    )
    parser.add_argument(
        "--deadline",
        type=float,
        default=None,
        help="epoch seconds; refuse to START a unit whose budget no longer fits",
    )
    parser.add_argument("--unit-budget", type=float, default=0.0)
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

    config = load_yaml(args.config) if args.config else {}
    subs = build_subcollections(config, smoke=args.smoke)
    corruptions = build_corruptions(config, smoke=args.smoke)
    n_seeds = 2 if args.smoke else int(config.get("n_seeds", 27))
    arms = (
        ("fact_rank", "nauty_cert", "size_l1")
        if args.smoke
        else tuple(str(a) for a in config.get("arms", DEFAULT_ARMS))
    )
    units = enumerate_units(subs, corruptions, n_seeds)

    if args.count:
        print(len(units))
        return 0

    out_root = Path(args.out) if args.out else results_root()
    data_root = resolve_data_root(args.data_root or config.get("data_root"))
    # Reads come from the shared root the matrices job wrote to; writes go to
    # --out. Defaulting to out_root keeps the single-root local runs working.
    matrices_root = Path(args.matrices_root) if args.matrices_root else out_root
    n_jobs = args.n_jobs or int(config.get("n_jobs") or os.environ.get("SLURM_CPUS_PER_TASK", 1))

    if args.unit is not None:
        selected = [args.unit]
    elif args.shard:
        index, count = parse_shard(args.shard)
        lo, hi = shard_bounds(len(units), index, count)
        selected = list(range(lo, hi))
    else:
        selected = list(range(len(units)))

    prefix = f"{args.tag}/" if args.tag else ""
    rows_paths = RunPaths(root=out_root, rq=RQ_DIR, experiment=f"{prefix}{ROWS_SUBDIR}")
    rows_paths.ensure()

    if args.smoke:
        ensure_smoke_matrices(subs, arms, matrices_root=matrices_root, corpora_root=data_root)

    logger.info(
        "rq4: %d unit(s) of %d, arms=%s n_jobs=%d out=%s",
        len(selected),
        len(units),
        ",".join(arms),
        n_jobs,
        out_root,
    )

    collection_cache: dict[str, Any] = {}

    if args.refill_censored_arm:
        arm = args.refill_censored_arm
        if arm not in arms:
            logger.error("--refill-censored-arm %s is not one of the configured arms", arm)
            return 2
        n_refilled = 0
        for unit_index in selected:
            if refill_unit(
                units[unit_index],
                arm,
                rows_paths,
                matrices_root=matrices_root,
                corpora_root=data_root,
                n_jobs=n_jobs,
                collection_cache=collection_cache,
            ):
                n_refilled += 1
                logger.info(
                    "refilled unit %d (%s) arm %s", unit_index, units[unit_index].unit_id, arm
                )
        shard_tag = args.shard.replace("/", "_") if args.shard else "all"
        refill_paths = RunPaths(
            root=out_root, rq=RQ_DIR, experiment=f"{prefix}refill_{arm}_{shard_tag}"
        )
        refill_paths.ensure()
        # The provenance the refill has to carry is the stamp of the tree that
        # produced the rows it did NOT touch, so a reader can see the two halves
        # of a refilled table came from different library commits.
        original = _shard_manifest_stamp(out_root, prefix, shard_tag)
        write_manifest(
            refill_paths,
            extra={
                "refilled_arm": arm,
                "n_units_refilled": n_refilled,
                "n_units_examined": len(selected),
                "refilled_from": original,
                "matrices_root": str(matrices_root),
                **deploy_stamps(),
            },
        )
        logger.info("refill: %d unit(s) of %d rewritten for arm %s", n_refilled, len(selected), arm)
        return 0

    deferred: list[int] = []
    n_written = 0
    for unit_index in selected:
        unit = units[unit_index]
        if not args.force and _unit_done(rows_paths, unit):
            logger.info("unit %d (%s) already done; skipping", unit_index, unit.unit_id)
            continue
        # Start-cutoff. Refuse to START a unit whose full budget no longer fits
        # inside the wall, and NEVER trim its budget to make it fit: a unit that
        # got a fraction of its time is not comparable with its paired units.
        # The FIRST unit actually run is exempt -- without that exemption a task
        # whose start-up alone exceeds the cutoff defers its whole chunk, the
        # resume pass re-derives the same chunk and defers it again, and the
        # array livelocks, burning a full wall per pass and completing nothing.
        if (
            args.deadline is not None
            and n_written > 0
            and time.time() + args.unit_budget > args.deadline
        ):
            logger.warning("DEFERRED: unit %d (%s) -- start-cutoff", unit_index, unit.unit_id)
            deferred.append(unit_index)
            continue
        logger.info("unit %d: %s", unit_index, unit.unit_id)
        started = time.perf_counter()
        tables = run_unit(
            unit,
            matrices_root=matrices_root,
            corpora_root=data_root,
            arms=arms,
            n_jobs=n_jobs,
            collection_cache=collection_cache,
        )
        for table, columns in _TABLES.items():
            if tables[table]:
                write_rows(rows_paths, f"{table}__{unit.unit_id}", tables[table], columns=columns)
        n_written += 1
        logger.info("unit %d done in %.1f s", unit_index, time.perf_counter() - started)

    shard_tag = args.shard.replace("/", "_") if args.shard else "all"
    shard_paths = RunPaths(root=out_root, rq=RQ_DIR, experiment=f"{prefix}shard_{shard_tag}")
    shard_paths.ensure()
    write_config(
        shard_paths,
        {
            "subcollections": [dataclasses.asdict(s) for s in subs],
            "corruptions": [{"kind": k, "budget": b} for k, b in corruptions],
            "arms": list(arms),
            "n_seeds": n_seeds,
            "contamination": CONTAMINATION,
            "knn_k": KNN_K,
            "lof_k": LOF_K,
            "n_units": len(units),
            "selected": selected,
            "n_jobs": n_jobs,
            "smoke": args.smoke,
        },
    )
    write_manifest(
        shard_paths,
        extra={
            "n_units_written": n_written,
            "n_deferred": len(deferred),
            "deferred": deferred,
            "tag": args.tag,
            "matrices_root": str(matrices_root),
            **deploy_stamps(),
        },
    )
    if deferred:
        logger.warning("%d unit(s) deferred by the start-cutoff: %s", len(deferred), deferred)
    return 0


if __name__ == "__main__":
    sys.exit(main())
