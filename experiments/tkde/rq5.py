"""RQ5 -- description patterns (DESIGN.md §6).

Which patterns of description exist in a collection, and does the structure
recover known kinds? The evaluation axis is ARI against the Wikidata P31 class,
with NMI beside it and cophenetic correlation for the hierarchy; the geometry
table carries the *licences* (non-Euclidean mass, hubness) that justify PAM over
a centroid method and metric MDS over classical MDS.

Two designs, per DESIGN.md §6:

* **full** -- every member carrying one of the classes with at least
  ``min_class_size`` members. PAM is run from 27 initializations and the
  labelling of *lowest PAM cost* is reported (a label-free criterion: choosing
  by ARI would select on the answer). Its ARI carries a member-level bootstrap
  interval. Imbalance is stated rather than removed.
* **balanced** -- the primary statistical comparison. Per seed, ``per_class``
  members are sampled from each class, giving one score per seed and therefore
  27 paired observations per arm for the Wilcoxon family in ``analyze_rq5``.

Every design reads *submatrices of the cached full-collection matrices*
(``experiments.tkde.matrices``); nothing here recomputes a distance. The member
order is the frozen ``records.jsonl`` order, which is what makes the submatrix
indices meaningful.

Unit of work: one ``(experiment, arm)`` pair for the full design, one
``(experiment, seed)`` for a balanced design -- the split that matches where
the cost is. Units are idempotent: each writes its own row files, so a re-run
after a node loss redoes only what did not finish.
"""

from __future__ import annotations

import argparse
import dataclasses
import logging
import sys
import time
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any

from experiments.tkde import corpora
from experiments.tkde.config import TkdeConfigError, load_yaml, results_root, seeds
from experiments.tkde.io import RunPaths, write_config, write_manifest, write_rows
from experiments.tkde.matrices import (
    MatrixCacheMissingError,
    common_member_ids,
    deploy_stamps,
    load_arm_matrices,
    load_cached_matrix_censored,
    parse_shard,
    resolve_data_root,
    shard_bounds,
)

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray

logger = logging.getLogger(__name__)

RQ_DIR = "RQ5_patterns"
ROWS_SUBDIR = "rows"
RQ_INDEX = 5

#: ``fact_rank_roles`` is absent: it fails the M0 relabelling-invariance check
#: (43/60), so it is not a measurable arm and may not reach a table (T-KBf).
DEFAULT_ARMS: tuple[str, ...] = (
    "fact_rank",
    "isal_ow_struct",
    "isal_ow_rank",
    "isal_ow_rank0",
    "wstar_rank",
    "nauty_cert",
    "nauty_cert_rows",
    "wl_l1",
    "netlsd",
    "hpd_jsd",
    "bipartite_ged_path",
    "bipartite_ged_assign",
    "size_l1",
    "degree_seq_l1",
)
#: The purity control (DESIGN.md §G4). Only the arms its supplementary table
#: reports have cached matrices for this collection.
CONTROL_ARMS: tuple[str, ...] = (
    "fact_rank",
    "isal_ow_struct",
    "isal_ow_rank",
    "isal_ow_rank0",
    "wstar_rank",
    "nauty_cert",
    "wl_l1",
    "size_l1",
    "degree_seq_l1",
)
#: The two naive floors, mandatory on every task table (DESIGN.md G3, L1).
FLOOR_ARMS: tuple[str, ...] = ("size_l1", "degree_seq_l1")

MDS_ARM = "fact_rank"
HUBNESS_K = 10
N_BOOTSTRAP = 1_000

_BASE_COLUMNS: tuple[str, ...] = (
    "rq",
    "experiment",
    "collection",
    "seed",
    "arm",
    "secs",
    "censored",
)

ROWS_CLUSTERING_COLUMNS: tuple[str, ...] = (
    *_BASE_COLUMNS,
    "design",
    "method",
    "k",
    "n_members",
    "ari",
    "nmi",
    "cophenetic",
    "silhouette",
    "ari_boot_low",
    "ari_boot_high",
    "pam_cost",
    "n_init",
    "n_censored_members",
)
ROWS_PER_CLASS_COLUMNS: tuple[str, ...] = (
    *_BASE_COLUMNS,
    "design",
    "method",
    "class",
    "support",
    "recall",
    "precision",
    "cluster",
    "n_censored_class",
    "censor_rate_class",
)
ROWS_GEOMETRY_COLUMNS: tuple[str, ...] = (
    *_BASE_COLUMNS,
    "design",
    "N",
    "nu",
    "n_negative_eigen",
    "largest_negative",
    "hubness_skew_k10",
    "hubness_max_occurrence",
    "diameter_over_median",
    "n_censored_members",
)
ROWS_MDS_COLUMNS: tuple[str, ...] = (
    *_BASE_COLUMNS,
    "design",
    "member_id",
    "label",
    "dim0",
    "dim1",
    "stress1",
)


@dataclasses.dataclass(frozen=True)
class Experiment:
    """One RQ5 experiment: a collection, a design, and the arms it runs."""

    name: str
    collection: str
    design: str
    arms: tuple[str, ...]
    min_class_size: int
    per_class: int
    n_seeds: int
    #: Cap on the full design's member count. ``None`` in production (the whole
    #: collection); set under ``--smoke`` so PAM, the eigendecomposition and the
    #: SMACOF map stay inside the five-minute budget.
    max_members: int | None = None


@dataclasses.dataclass(frozen=True)
class Unit:
    """One idempotent unit of work."""

    index: int
    experiment: Experiment
    arm: str | None
    seed: int | None

    @property
    def unit_id(self) -> str:
        """Return the stable filename stem of this unit."""
        if self.arm is not None:
            return f"{self.experiment.name}__{self.arm}"
        return f"{self.experiment.name}__seed{self.seed}"


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


def build_experiments(config: Mapping[str, Any], *, smoke: bool) -> list[Experiment]:
    """Return the experiments this run executes.

    Parameters
    ----------
    config : Mapping
        Parsed YAML.
    smoke : bool
        Shrink to a configuration that finishes in well under five minutes.

    Returns
    -------
    list[Experiment]
    """
    if smoke:
        return [
            Experiment(
                name="wd50k66_full",
                collection="wd50k66",
                design="full",
                arms=("fact_rank", "isal_ow_struct", "size_l1"),
                min_class_size=20,
                per_class=20,
                n_seeds=3,
                max_members=280,
            ),
            Experiment(
                name="wd50k66_balanced",
                collection="wd50k66",
                design="balanced",
                arms=("fact_rank", "isal_ow_struct", "size_l1", "degree_seq_l1"),
                min_class_size=20,
                per_class=5,
                n_seeds=3,
            ),
        ]

    entries = config.get("experiments")
    if not entries:
        raise TkdeConfigError("rq5 config needs an `experiments` list")
    built: list[Experiment] = []
    for entry in entries:
        built.append(
            Experiment(
                name=str(entry["name"]),
                collection=str(entry["collection"]),
                design=str(entry["design"]),
                arms=tuple(str(a) for a in entry["arms"]),
                min_class_size=int(entry.get("min_class_size", 20)),
                per_class=int(entry.get("per_class", 20)),
                n_seeds=int(entry.get("n_seeds", 27)),
            )
        )
    return built


def enumerate_units(experiments: Sequence[Experiment]) -> list[Unit]:
    """Return the deterministic unit list.

    The full design splits by arm (each arm is a heavy PAM / eigendecomposition
    on the whole collection); a balanced design splits by seed (each seed is a
    280-member submatrix across every arm, and the seed is the replication unit
    the statistics harness pairs on).

    Parameters
    ----------
    experiments : Sequence[Experiment]

    Returns
    -------
    list[Unit]
    """
    units: list[Unit] = []
    for experiment in experiments:
        if experiment.design == "full":
            for arm in experiment.arms:
                units.append(Unit(len(units), experiment, arm, None))
        else:
            for seed in seeds(RQ_INDEX, experiment.n_seeds):
                units.append(Unit(len(units), experiment, None, seed))
    return units


def eligible_classes(labels: Sequence[str | None], min_size: int) -> list[str]:
    """Return the class labels with at least ``min_size`` members.

    Ordered by descending support then label, so the ordering is deterministic
    and independent of dictionary insertion order.

    Parameters
    ----------
    labels : Sequence[str or None]
        Per-member class label.
    min_size : int
        Inclusive lower bound on support.

    Returns
    -------
    list[str]
    """
    counts: dict[str, int] = {}
    for label in labels:
        if label is not None:
            counts[label] = counts.get(label, 0) + 1
    return [
        c
        for c, _ in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
        if counts[c] >= min_size
    ]


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def _pam_cost(D: NDArray[np.float64], labels: NDArray[np.int64]) -> float:
    """Return the PAM objective of ``labels``: the summed distance to medoids.

    The label-free criterion used to pick among the 27 initializations of the
    full design. Selecting by ARI instead would choose the run on the answer.

    Parameters
    ----------
    D : numpy.ndarray
        ``(N, N)`` distance matrix.
    labels : numpy.ndarray
        ``(N,)`` cluster assignment.

    Returns
    -------
    float
        Total cost; ``inf`` if a cluster is empty.
    """
    import numpy as np

    total = 0.0
    for cluster in np.unique(labels):
        members = np.flatnonzero(labels == cluster)
        if members.size == 0:
            return float("inf")
        block = D[np.ix_(members, members)]
        total += float(block.sum(axis=1).min())
    return total


def _silhouette(D: NDArray[np.float64], labels: NDArray[np.int64]) -> float:
    """Return the precomputed-metric silhouette, or NaN when it is undefined."""
    import numpy as np
    from sklearn.metrics import silhouette_score

    if np.unique(labels).size < 2:
        return float("nan")
    try:
        return float(silhouette_score(D, labels, metric="precomputed"))
    except ValueError:
        return float("nan")


def _bootstrap_ari(
    truth: Sequence[str],
    predicted: NDArray[np.int64],
    *,
    seed: int,
    n_resamples: int = N_BOOTSTRAP,
) -> tuple[float, float]:
    """Return a percentile member-level interval for ARI, by subsampling.

    The full design has one value per arm, so its interval comes from
    resampling *members* rather than seeds (DESIGN.md §6 Statistics).

    **Subsampling without replacement, not the ordinary bootstrap.** A
    with-replacement resample duplicates members, and a duplicated member
    agrees with itself in both the true and the predicted partition, so every
    pair-counting index is biased upward. The effect is not academic: measured
    on the smoke configuration, the ordinary bootstrap returned
    ``[0.052, 0.098]`` around a point ARI of ``0.045`` -- an interval that does
    not contain its own point estimate. Drawing ``m = 0.632 n`` *distinct*
    members (the expected number of distinct draws in an ``n``-out-of-``n``
    bootstrap) keeps each resample a genuine sub-partition and removes the
    artefact.

    Parameters
    ----------
    truth : Sequence[str]
        Ground-truth class per member.
    predicted : numpy.ndarray
        Cluster label per member.
    seed : int
        Resampling seed.
    n_resamples : int, optional
        Number of resamples.

    Returns
    -------
    tuple[float, float]
        ``(low, high)`` at 95 %.
    """
    import numpy as np

    from isalhg.metric_space.toolkit import ari

    rng = np.random.default_rng(seed)
    truth_arr = np.asarray(truth, dtype=object)
    n = len(truth_arr)
    m = max(2, int(round(0.632 * n)))
    values: list[float] = []
    for _ in range(n_resamples):
        idx = rng.choice(n, size=m, replace=False)
        values.append(ari(list(truth_arr[idx]), list(predicted[idx])))
    return float(np.percentile(values, 2.5)), float(np.percentile(values, 97.5))


def geometry_row(D: NDArray[np.float64]) -> dict[str, Any]:
    """Return the geometry invariants of one distance matrix.

    Parameters
    ----------
    D : numpy.ndarray
        ``(N, N)`` distance matrix.

    Returns
    -------
    dict[str, Any]
        ``nu``, negative-eigenvalue count and extreme, hubness, and the
        diameter-over-median concentration ratio.
    """
    import numpy as np

    from isalhg.metric_space.toolkit import hubness, non_euclidean_mass

    nu, eigenvalues = non_euclidean_mass(D)
    tolerance = 1e-9 * float(np.abs(eigenvalues).max() or 1.0)
    negative = eigenvalues[eigenvalues < -tolerance]
    skew, max_occurrence = hubness(D, HUBNESS_K)

    off = D[~np.eye(D.shape[0], dtype=bool)]
    median = float(np.median(off))
    return {
        "N": int(D.shape[0]),
        "nu": float(nu),
        "n_negative_eigen": int(negative.size),
        "largest_negative": float(negative.min()) if negative.size else 0.0,
        "hubness_skew_k10": float(skew),
        "hubness_max_occurrence": int(max_occurrence),
        "diameter_over_median": float(off.max() / median) if median > 0 else float("nan"),
    }


# ---------------------------------------------------------------------------
# Units
# ---------------------------------------------------------------------------


def _select_indices(
    experiment: Experiment,
    labels: Sequence[str | None],
    classes: Sequence[str],
    seed: int | None,
) -> list[int]:
    """Return the member indices this unit clusters.

    Full design: every member of an eligible class, in collection order.
    Balanced design: ``per_class`` members sampled per class under ``seed``.

    Parameters
    ----------
    experiment : Experiment
    labels : Sequence[str or None]
        Per-member class label, in collection order.
    classes : Sequence[str]
        Eligible classes.
    seed : int or None
        Sampling seed for the balanced design.

    Returns
    -------
    list[int]
    """
    import numpy as np

    eligible = set(classes)
    by_class: dict[str, list[int]] = {c: [] for c in classes}
    for index, label in enumerate(labels):
        if label in eligible:
            by_class[label].append(index)

    if experiment.design == "full":
        chosen_full = sorted(i for members in by_class.values() for i in members)
        if experiment.max_members is not None:
            # Deterministic stratified thinning, so every class survives the cap.
            rng = np.random.default_rng(RQ_INDEX)
            per = max(2, experiment.max_members // max(1, len(classes)))
            capped: list[int] = []
            for cls in classes:
                members = np.asarray(by_class[cls])
                take = min(per, members.size)
                capped.extend(int(i) for i in rng.choice(members, size=take, replace=False))
            return sorted(capped)
        return chosen_full

    rng = np.random.default_rng(seed)
    chosen: list[int] = []
    for cls in classes:
        members = np.asarray(by_class[cls])
        take = min(experiment.per_class, members.size)
        chosen.extend(int(i) for i in rng.choice(members, size=take, replace=False))
    return sorted(chosen)


def run_unit(
    unit: Unit,
    *,
    matrices_root: Path,
    corpora_root: Path | str | None,
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
        Corpora root override.
    collection_cache : dict
        Per-process memo of loaded collections.

    Returns
    -------
    dict[str, list[dict]]
        Tables ``clustering``, ``per_class``, ``geometry``, ``mds``.
    """
    import numpy as np

    from isalhg.metric_space.toolkit import (
        ari,
        average_linkage,
        cut,
        metric_mds,
        nmi,
        pam,
        per_class_table,
    )

    experiment = unit.experiment
    name = experiment.collection
    if name not in collection_cache:
        collection_cache[name] = corpora.load_collection(name, corpora_root)
    collection = collection_cache[name]

    ids = corpora.member_ids(collection)
    labels_all = corpora.labels(collection)
    classes = eligible_classes(labels_all, experiment.min_class_size)
    k = len(classes)

    tables: dict[str, list[dict[str, Any]]] = {
        "clustering": [],
        "per_class": [],
        "geometry": [],
        "mds": [],
    }

    arms = (unit.arm,) if unit.arm is not None else experiment.arms
    selected_all = _select_indices(experiment, labels_all, classes, unit.seed)
    selected_labels = [labels_all[i] for i in selected_all]

    # Memoized: a balanced design reads the same matrices at every one of its 27
    # seeds, and wd50k66 is 64 MB per arm -- 19 GB of repeat I/O without this.
    loaded = load_arm_matrices(matrices_root, name, arms, ids, cache=collection_cache)
    survivors = set(common_member_ids([ids[i] for i in selected_all], loaded))
    selected = [i for i in selected_all if ids[i] in survivors]
    truth = [labels_all[i] for i in selected]
    n_censored = len(selected_all) - len(selected)
    class_census = censored_by_class(selected_labels, truth)
    if n_censored:
        logger.warning(
            "unit %d (%s): %d of %d selected members censored; clustering the rest",
            unit.index,
            unit.unit_id,
            n_censored,
            len(selected_all),
        )

    n_init = experiment.n_seeds if experiment.design == "full" else 1
    init_seeds = seeds(RQ_INDEX, n_init) if experiment.design == "full" else [unit.seed or 0]

    for arm in arms:
        started = time.perf_counter()
        if arm not in loaded or len(selected) < k:
            if arm in loaded:
                logger.error(
                    "unit %d arm %s: %d members survive for %d classes; censored",
                    unit.index,
                    arm,
                    len(selected),
                    k,
                )
            tables["clustering"].append(
                _base_row(unit, arm, 0.0, censored=1)
                | {
                    "design": experiment.design,
                    "method": "pam",
                    "k": k,
                    "n_members": 0,
                    "ari": float("nan"),
                    "nmi": float("nan"),
                    "cophenetic": float("nan"),
                    "silhouette": float("nan"),
                    "ari_boot_low": float("nan"),
                    "ari_boot_high": float("nan"),
                    "pam_cost": float("nan"),
                    "n_init": n_init,
                    "n_censored_members": n_censored,
                }
            )
            continue

        full, row_of = loaded[arm]
        # Align by member id: a censored arm's rows are its survivors, not the
        # frozen order, so the frozen positions would index the wrong members.
        arm_rows = [row_of[ids[i]] for i in selected]
        D = np.asarray(full[np.ix_(arm_rows, arm_rows)], dtype=np.float64)
        np.fill_diagonal(D, 0.0)

        # --- PAM: 27 initializations on the full design, one on a balanced seed
        best_labels: NDArray[np.int64] | None = None
        best_cost = float("inf")
        for init in init_seeds:
            candidate = pam(D, k, int(init) % (2**31 - 1))
            cost = _pam_cost(D, candidate)
            if cost < best_cost:
                best_cost, best_labels = cost, candidate
        assert best_labels is not None

        boot_low, boot_high = (float("nan"), float("nan"))
        if experiment.design == "full":
            boot_low, boot_high = _bootstrap_ari(truth, best_labels, seed=RQ_INDEX)

        tables["clustering"].append(
            _base_row(unit, arm, time.perf_counter() - started)
            | {
                "design": experiment.design,
                "method": "pam",
                "k": k,
                "n_members": len(selected),
                "ari": ari(truth, list(best_labels)),
                "nmi": nmi(truth, list(best_labels)),
                "cophenetic": float("nan"),
                "silhouette": _silhouette(D, best_labels),
                "ari_boot_low": boot_low,
                "ari_boot_high": boot_high,
                "pam_cost": best_cost,
                "n_init": n_init,
                "n_censored_members": n_censored,
            }
        )
        tables["per_class"].extend(
            _base_row(unit, arm, 0.0)
            | {"design": experiment.design, "method": "pam", **row}
            | _class_census_columns(class_census, row)
            for row in per_class_table(truth, list(best_labels))
        )

        # --- average-linkage hierarchy cut at k, with cophenetic correlation
        agglo_started = time.perf_counter()
        linkage, cophenetic = average_linkage(D)
        agglo_labels = cut(linkage, k)
        tables["clustering"].append(
            _base_row(unit, arm, time.perf_counter() - agglo_started)
            | {
                "design": experiment.design,
                "method": "agglo",
                "k": k,
                "n_members": len(selected),
                "ari": ari(truth, list(agglo_labels)),
                "nmi": nmi(truth, list(agglo_labels)),
                "cophenetic": float(cophenetic),
                "silhouette": _silhouette(D, agglo_labels),
                "ari_boot_low": float("nan"),
                "ari_boot_high": float("nan"),
                "pam_cost": float("nan"),
                "n_init": 1,
                "n_censored_members": n_censored,
            }
        )
        tables["per_class"].extend(
            _base_row(unit, arm, 0.0)
            | {"design": experiment.design, "method": "agglo", **row}
            | _class_census_columns(class_census, row)
            for row in per_class_table(truth, list(agglo_labels))
        )

        # --- geometry licences, measured on the whole collection matrix
        if experiment.design == "full":
            geometry_started = time.perf_counter()
            tables["geometry"].append(
                _base_row(unit, arm, time.perf_counter() - geometry_started)
                | {
                    "design": experiment.design,
                    **geometry_row(D),
                    "n_censored_members": n_censored,
                }
            )

        # --- the MDS map: a figure input, not an evaluation
        if experiment.design == "full" and arm == MDS_ARM:
            mds_started = time.perf_counter()
            coords, stress1 = metric_mds(D, 2, RQ_INDEX)
            secs = time.perf_counter() - mds_started
            tables["mds"].extend(
                _base_row(unit, arm, secs)
                | {
                    "design": experiment.design,
                    "member_id": ids[member],
                    "label": truth[position],
                    "dim0": float(coords[position, 0]),
                    "dim1": float(coords[position, 1]),
                    "stress1": float(stress1),
                }
                for position, member in enumerate(selected)
            )

    return tables


def _class_census_columns(
    census: Mapping[str, tuple[int, float]],
    row: Mapping[str, Any],
) -> dict[str, Any]:
    """Project one class's censoring counts onto its ``rows_per_class`` row."""
    lost, rate = census.get(str(row.get("class")), (0, 0.0))
    return {"n_censored_class": lost, "censor_rate_class": rate}


def censored_by_class(
    selected_labels: Sequence[str],
    kept_labels: Sequence[str],
) -> dict[str, tuple[int, float]]:
    """Return ``label -> (censored count, censored rate)`` for one selection.

    L15's label-correlated clause, in RQ5's currency: arity-heavy Wikidata types
    censor more, so a clustering scored after censoring is scored on a class
    distribution the corpus never had. The rate is reported per type rather than
    pooled, since pooling is exactly what would hide it.

    Parameters
    ----------
    selected_labels : Sequence[str]
        Labels of the members the design selected, before restriction.
    kept_labels : Sequence[str]
        Labels of the members that survived every arm's screen.

    Returns
    -------
    dict
        Per label, the number of selected members lost and the fraction of that
        label's selection they were.
    """
    selected_counts = Counter(selected_labels)
    kept_counts = Counter(kept_labels)
    return {
        label: (
            selected_counts[label] - kept_counts[label],
            round((selected_counts[label] - kept_counts[label]) / selected_counts[label], 6),
        )
        for label in selected_counts
    }


def _base_row(unit: Unit, arm: str, secs: float, *, censored: int = 0) -> dict[str, Any]:
    """Return the columns every TKDE row carries."""
    return {
        "rq": "RQ5",
        "experiment": unit.experiment.name,
        "collection": unit.experiment.collection,
        "seed": unit.seed if unit.seed is not None else 0,
        "arm": arm,
        "secs": round(secs, 4),
        "censored": censored,
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

_TABLES: dict[str, tuple[str, ...]] = {
    "clustering": ROWS_CLUSTERING_COLUMNS,
    "per_class": ROWS_PER_CLASS_COLUMNS,
    "geometry": ROWS_GEOMETRY_COLUMNS,
    "mds": ROWS_MDS_COLUMNS,
}


def ensure_smoke_matrices(
    experiments: Sequence[Experiment],
    *,
    matrices_root: Path,
    corpora_root: Path | str | None,
    n_jobs: int = 4,
) -> None:
    """Build any matrix the smoke configuration needs but does not have.

    Production runs depend on the matrices job and must fail loudly when it has
    not run (:class:`MatrixCacheMissingError`); the local smoke has no such job in
    front of it, so it builds its own -- only the cheap arms, and only into the
    scratch root the smoke was pointed at.

    Parameters
    ----------
    experiments : Sequence[Experiment]
    matrices_root : Path
        Smoke results root.
    corpora_root : Path or str or None
    n_jobs : int, optional
        Worker processes.
    """
    from experiments.tkde.matrices import collection_cache_dir
    from isalhg.metric_space.toolkit.matrix import build_matrix

    wanted: dict[str, set[str]] = {}
    for experiment in experiments:
        wanted.setdefault(experiment.collection, set()).update(experiment.arms)

    for name, arms in wanted.items():
        collection = corpora.load_collection(name, corpora_root)
        ids = corpora.member_ids(collection)
        items = corpora.hypergraphs(collection)
        cache_dir = collection_cache_dir(matrices_root, name)
        cache_dir.mkdir(parents=True, exist_ok=True)
        for arm in sorted(arms):
            try:
                load_cached_matrix_censored(matrices_root, name, arm, ids)
                continue
            except MatrixCacheMissingError:
                pass
            logger.info("smoke: building %s / %s (%d members)", name, arm, len(ids))
            build_matrix(
                items,
                arm,
                member_ids=ids,
                roles=corpora.roles_maps(collection) if arm.endswith("_roles") else None,
                cache_dir=cache_dir,
                n_jobs=n_jobs,
            )


def _unit_done(rows_paths: RunPaths, unit: Unit) -> bool:
    """Return True when this unit's clustering rows already exist."""
    return (rows_paths.dir / f"rows_clustering__{unit.unit_id}.csv").exists()


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
    parser = argparse.ArgumentParser(description="RQ5 -- description patterns.")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None, help="results root")
    parser.add_argument("--shard", type=str, default=None, help="i/N")
    parser.add_argument("--unit", type=int, default=None)
    parser.add_argument("--count", action="store_true")
    parser.add_argument("--smoke", action="store_true")
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
    parser.add_argument("--force", action="store_true", help="recompute finished units")
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
    experiments = build_experiments(config, smoke=args.smoke)
    units = enumerate_units(experiments)

    if args.count:
        print(len(units))
        return 0

    out_root = Path(args.out) if args.out else results_root()
    data_root = resolve_data_root(args.data_root or config.get("data_root"))
    # Reads come from the shared root the matrices job wrote to; writes go to
    # --out. Defaulting to out_root keeps the single-root local runs working.
    matrices_root = Path(args.matrices_root) if args.matrices_root else out_root

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
        ensure_smoke_matrices(experiments, matrices_root=matrices_root, corpora_root=data_root)

    logger.info("rq5: %d unit(s) of %d, out=%s", len(selected), len(units), out_root)

    collection_cache: dict[str, Any] = {}
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
            "experiments": [dataclasses.asdict(e) for e in experiments],
            "n_units": len(units),
            "selected": selected,
            "smoke": args.smoke,
            "hubness_k": HUBNESS_K,
            "mds_arm": MDS_ARM,
            "floor_arms": list(FLOOR_ARMS),
            "n_bootstrap": N_BOOTSTRAP,
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
