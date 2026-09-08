"""RQ3 runner --- the representative record, plus RQ2's certificate-validity rows.

Implements DESIGN.md section 4 (Corpus A variant collections over real members,
Corpus B the natural NDC series) and DESIGN.md section 3 procedure step 4, whose
rows are derived from the same matrices and are therefore produced here.

The question is which member of a disagreeing collection is the reference record.
Three families of method answer it: a certified medoid under each of the eight
distance arms (it can only ever return an input), the coverage consensus over the
fact language (it returns a decoded word that need not be any input), and
``majority_merge``, which is allowed to read the constant identities every other
method is denied and therefore serves as a reference, not a competitor.

The single evaluation axis is the exact fact-level distance to the truth,
computed with constant identities: a member's facts are ``(predicate, frozenset
of external constant identities)``, a consensus output's constants are mapped
through :attr:`ConsensusResult.node_map` into its anchor member's identities, and
the score is the size of the symmetric difference against the truth's fact set.
The methods never read identities; only the evaluation does.
"""

from __future__ import annotations

import argparse
import logging
import random
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from experiments.tkde import corpora, io
from experiments.tkde.budget import guarded_budget_call
from experiments.tkde.config import TkdeConfigError, TkdeError, load_yaml, results_root, seeds
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.datasets.kb.base import KBCollection, KBRecord
from isalhg.datasets.kb.ladders import variant_collection
from isalhg.language.consensus import ConsensusResult, coverage_consensus
from isalhg.language.majority import majority_merge
from isalhg.metric_space.toolkit.matrix import build_matrix
from isalhg.metric_space.toolkit.medoid import medoid

logger = logging.getLogger(__name__)

RQ = "RQ3"
RQ_INDEX = 3
RQ_DIR = "RQ3_representative"
EXPERIMENT_A = "corpus_a"
EXPERIMENT_B = "corpus_b"
CERT_RQ_DIR = "RQ2_wellposedness"
CERT_EXPERIMENT = "certificate_validity"
PARTS = "parts"

MEDOID_ARMS: tuple[str, ...] = (
    "fact_rank",
    "isal_ow_struct",
    "wstar_rank",
    "nauty_cert",
    "wl_l1",
    "netlsd",
    "hpd_jsd",
    "bipartite_ged_path",
    "degree_seq_l1",
    "size_l1",
)
ZERO_TOLERANCE = 1e-9

VARIANT_COLUMNS: tuple[str, ...] = (
    "rq",
    "experiment",
    "collection",
    "seed",
    "arm",
    "git_sha",
    "host_cpu",
    "secs",
    "censored",
    "unit",
    "cell",
    "cell_N",
    "cell_t",
    "cell_kind",
    "source_id",
    "collection_id",
    "N",
    "method",
    "radius",
    "fact_dist",
    "exact_recovery",
    "medoid_cost",
    "LB",
    "ratio",
    "n_candidates",
    "n_ties",
)

NATURAL_COLUMNS: tuple[str, ...] = (
    "rq",
    "experiment",
    "collection",
    "seed",
    "arm",
    "git_sha",
    "host_cpu",
    "secs",
    "censored",
    "unit",
    "class_id",
    "run_index",
    "T",
    "regime_preserving",
    "collection_id",
    "N",
    "method",
    "radius",
    "fact_dist",
    "exact_recovery",
    "medoid_cost",
    "LB",
    "ratio",
    "n_candidates",
    "n_ties",
)

CERTIFICATE_COLUMNS: tuple[str, ...] = (
    "rq",
    "experiment",
    "collection",
    "seed",
    "arm",
    "git_sha",
    "host_cpu",
    "secs",
    "censored",
    "unit",
    "collection_id",
    "N",
    "LB",
    "medoid_cost",
    "invalid",
)

IdentityFacts = frozenset[tuple[int, frozenset[str]]]


class RQ3Error(TkdeError):
    """A RQ3 unit could not be built or evaluated as specified."""


# ---------------------------------------------------------------------------
# Provenance for the universal row columns
# ---------------------------------------------------------------------------


SHARED_SRC_REPO = Path("/mnt/home/users/tic_163_uma/mpascual/fscratch/repos/IsalHG-tkde")
DEPLOY_STAMP = ".tkde_deploy"
SMOKE_MARKER = "_smoke"


def _read_stamp(directory: Path) -> str | None:
    """Return the one-line deploy stamp of ``directory``, or ``None``."""
    stamp = directory / DEPLOY_STAMP
    try:
        return stamp.read_text(encoding="utf-8").strip()
    except OSError:
        return None


def deploy_stamps() -> dict[str, Any]:
    """Name both trees a cluster run actually used.

    A PEP 660 editable install registers a meta-path finder, which is consulted
    before ``sys.path``, so on Picasso ``isalhg.*`` resolves to whichever
    checkout the environment was installed from --- the shared ``IsalHG-tkde``
    tree --- while ``experiments.*`` comes from the deployed runner tree on
    ``PYTHONPATH``. A manifest that names only one of them misattributes the
    code that ran.

    Returns
    -------
    dict
        ``src_deploy`` (the stamp of the tree ``isalhg`` was imported from),
        ``runner_deploy`` (the stamp of the tree ``experiments`` came from) and
        ``isalhg_path`` (the resolved package file, which settles the question
        even when a stamp is missing).
    """
    import isalhg

    package = Path(isalhg.__file__).resolve()
    src_stamp: str | None = None
    for parent in package.parents:
        found = _read_stamp(parent)
        if found is not None:
            src_stamp = found
            break
    if src_stamp is None:
        src_stamp = _read_stamp(SHARED_SRC_REPO)
    from experiments.tkde.rq1 import library_provenance

    return {
        "src_deploy": src_stamp,
        "runner_deploy": _read_stamp(io.repo_root()),
        **library_provenance(),
    }


def provenance() -> tuple[str, str]:
    """Return ``(git_sha, host_cpu)`` for the universal row columns.

    Delegates to the manifest writer's own helpers so that the value stamped on
    every row is the one ``manifest.json`` reports; a second implementation would
    drift from it silently.

    Returns
    -------
    tuple of str
        The short git SHA (or the deploy stamp's SHA) and the CPU model name.
    """
    return str(io._repo_provenance()["git_sha"] or ""), io._cpu_model()


# ---------------------------------------------------------------------------
# The evaluation axis --- exact fact-level distance under constant identities
# ---------------------------------------------------------------------------


def identity_facts_of_record(record: KBRecord) -> IdentityFacts:
    """Return the fact set of ``record`` addressed by external constant identity.

    Parameters
    ----------
    record : KBRecord
        A record carrying ``constant_ids``.

    Returns
    -------
    frozenset
        ``{(predicate, frozenset of constant identities)}``.

    Raises
    ------
    RQ3Error
        If the record carries no identities, so the axis is undefined.
    """
    ids = record.constant_ids
    if ids is None:
        raise RQ3Error(f"record {record.kb_id!r} carries no constant_ids; the RQ3 axis needs them")
    return frozenset((pred, frozenset(ids[v] for v in members)) for pred, members in record.facts)


def identity_facts_of_hypergraph(
    H: SparseHypergraph,
    ids: Sequence[str],
    node_map: Sequence[int] | None = None,
) -> IdentityFacts:
    """Return the fact set of ``H`` addressed by external constant identity.

    Parameters
    ----------
    H : SparseHypergraph
        A knowledge base expressed in some member's constant space.
    ids : Sequence of str
        That member's ``constant_ids``.
    node_map : Sequence of int or None, optional
        ``node_map[v]`` is the member's constant that constant ``v`` of ``H``
        denotes. ``None`` means the identity.

    Returns
    -------
    frozenset
        ``{(predicate, frozenset of constant identities)}``.
    """
    mapping = tuple(range(H.n_nodes)) if node_map is None else tuple(node_map)
    return frozenset(
        (label, frozenset(ids[mapping[v]] for v in members)) for _, members, label in H.iter_edges()
    )


def fact_distance(a: IdentityFacts, b: IdentityFacts) -> int:
    """Size of the symmetric difference of two identity-addressed fact sets."""
    return len(a ^ b)


# ---------------------------------------------------------------------------
# Process-level budget guard
# ---------------------------------------------------------------------------


def run_guarded(fn: Callable[[], Any], budget_s: float) -> tuple[str, Any]:
    """Run ``fn`` in a forked child, killed after ``budget_s`` seconds.

    A wall-clock guard has to be at the process level: a long computation inside
    a C extension does not return to the interpreter, so a signal-based alarm
    never fires (measured; DESIGN.md section 3 step 1).

    Delegates to :func:`experiments.tkde.budget.guarded_budget_call`, which adds
    the fork-health canary this function lacked: a process that has already
    canonicalized in-process forks children that deadlock on the C++ engine, so
    every call here would return ``("timeout", None)`` without having computed
    anything -- a censoring indistinguishable, in the rows, from a real one.
    RQ3 canonicalizes hundreds of consensus candidates per cell, so it refuses
    instead of writing that fiction.

    Parameters
    ----------
    fn : callable
        A no-argument callable whose return value is picklable.
    budget_s : float
        Wall-clock budget in seconds.

    Returns
    -------
    tuple
        ``("ok", value)``, ``("timeout", None)`` or ``("error", message)``.

    Raises
    ------
    experiments.tkde.budget.TkdeBudgetError
        If the C++ engine has already run in this process.
    """
    result = guarded_budget_call(fn, (), budget_s)
    if result.censored:
        return ("timeout", None)
    if result.error is not None:
        return ("error", result.error)
    return ("ok", result.value)


# ---------------------------------------------------------------------------
# Method outcomes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ConsensusOutcome:
    """What one coverage-consensus call contributes to a row."""

    fact_dist: int
    coverage: int
    sum_reach: int
    n_candidates: int
    n_ties: int


def consensus_outcome(
    members: Sequence[SparseHypergraph],
    identities: Sequence[Sequence[str]],
    truth_facts: IdentityFacts,
    r: int,
    *,
    alignment_budget: str = "triangle",
) -> ConsensusOutcome:
    """Compute the coverage consensus and score it against the truth.

    Parameters
    ----------
    members : Sequence of SparseHypergraph
        The collection, in the order its identities are given.
    identities : Sequence of Sequence of str
        Per member, its external constant identities (evaluation only).
    truth_facts : frozenset
        The truth's identity-addressed fact set.
    r : int
        Consensus radius.
    alignment_budget : str, optional
        Candidate-generation budget; the frozen default is ``"triangle"``.

    Returns
    -------
    ConsensusOutcome
        The score and the candidate-set statistics the rows carry.
    """
    result: ConsensusResult = coverage_consensus(members, r, alignment_budget=alignment_budget)
    out = identity_facts_of_hypergraph(result.kb, identities[result.anchor], result.node_map)
    return ConsensusOutcome(
        fact_dist=fact_distance(out, truth_facts),
        coverage=result.coverage,
        sum_reach=result.sum_reach,
        n_candidates=result.n_candidates,
        n_ties=result.n_ties,
    )


def majority_outcome(
    members: Sequence[SparseHypergraph],
    identities: Sequence[Sequence[str]],
    truth_facts: IdentityFacts,
) -> int:
    """Merge by majority over identified facts and score against the truth."""
    merged, merged_ids = majority_merge(members, identities)
    out = identity_facts_of_hypergraph(merged, merged_ids)
    return fact_distance(out, truth_facts)


# ---------------------------------------------------------------------------
# One collection: every method, every arm
# ---------------------------------------------------------------------------


def evaluate_collection(
    *,
    members: Sequence[KBRecord],
    truth: KBRecord,
    collection: KBCollection,
    radii: Sequence[tuple[str, int]],
    arms: Sequence[str],
    base_row: Mapping[str, Any],
    collection_id: str,
    unit: str,
    alignment_budget: str,
    consensus_budget_s: float | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Run every method on one collection and return ``(method rows, certificate rows)``.

    Parameters
    ----------
    members : Sequence of KBRecord
        The disagreeing descriptions; every one carries ``constant_ids``.
    truth : KBRecord
        The reference record the axis measures against.
    collection : KBCollection
        The parent collection, for vocabulary scoping.
    radii : Sequence of (str, int)
        Consensus radii to report, as ``(label, r)``; duplicates by ``r`` share
        one computation and emit one row each.
    arms : Sequence of str
        Registered distance arms the medoid is taken under.
    base_row : Mapping
        Columns shared by every row of this unit.
    collection_id : str
        Identifier of this particular collection.
    unit : str
        Identifier of the enumerated unit the collection belongs to.
    alignment_budget : str
        Candidate-generation budget passed to the consensus.
    consensus_budget_s : float or None
        Wall-clock budget per consensus call; ``None`` runs it unguarded.

    Returns
    -------
    tuple of list of dict
        The method rows and the RQ2 certificate rows.
    """
    n_types, n_preds = collection.n_types, collection.n_preds
    members_H = [r.to_hypergraph(n_types=n_types, n_preds=n_preds) for r in members]
    member_ids = [r.kb_id for r in members]
    identities = [identity_ids(r) for r in members]
    truth_facts = identity_facts_of_record(truth)
    shared = {
        **base_row,
        "unit": unit,
        "collection_id": collection_id,
        "N": len(members),
    }

    rows: list[dict[str, Any]] = []
    certificate_rows: list[dict[str, Any]] = []

    for arm in arms:
        started = time.perf_counter()
        try:
            D = np.asarray(
                build_matrix(members_H, arm, member_ids=member_ids, cache_dir=None),
                dtype=np.float64,
            )
            result = medoid(D)
            secs = time.perf_counter() - started
            distance = fact_distance(identity_facts_of_record(members[result.index]), truth_facts)
            rows.append(
                {
                    **shared,
                    "arm": arm,
                    "method": "medoid",
                    "radius": "",
                    "secs": secs,
                    "censored": 0,
                    "fact_dist": distance,
                    "exact_recovery": int(distance == 0),
                    "medoid_cost": result.cost,
                    "LB": result.lower_bound,
                    "ratio": result.ratio,
                    "n_candidates": "",
                    "n_ties": "",
                }
            )
            certificate_rows.append(
                {
                    **{k: v for k, v in shared.items() if k in CERTIFICATE_COLUMNS},
                    "rq": "RQ2",
                    "experiment": CERT_EXPERIMENT,
                    "collection": base_row["collection"],
                    "seed": base_row["seed"],
                    "git_sha": base_row["git_sha"],
                    "host_cpu": base_row["host_cpu"],
                    "arm": arm,
                    "secs": secs,
                    "censored": 0,
                    "LB": result.lower_bound,
                    "medoid_cost": result.cost,
                    "invalid": int(result.lower_bound > result.cost + ZERO_TOLERANCE),
                }
            )
        except Exception as exc:  # noqa: BLE001 - one dead arm must not kill the unit
            logger.warning("arm %s failed on %s: %s", arm, collection_id, exc)
            secs = time.perf_counter() - started
            rows.append(
                {
                    **shared,
                    "arm": arm,
                    "method": "medoid",
                    "radius": "",
                    "secs": secs,
                    "censored": 1,
                    "fact_dist": "",
                    "exact_recovery": "",
                    "medoid_cost": "",
                    "LB": "",
                    "ratio": "",
                    "n_candidates": "",
                    "n_ties": "",
                }
            )

    computed: dict[int, tuple[ConsensusOutcome | None, float]] = {}
    for label, r in radii:
        if r not in computed:
            started = time.perf_counter()
            if consensus_budget_s is None:
                try:
                    outcome: ConsensusOutcome | None = consensus_outcome(
                        members_H,
                        identities,
                        truth_facts,
                        r,
                        alignment_budget=alignment_budget,
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning("consensus r=%d failed on %s: %s", r, collection_id, exc)
                    outcome = None
            else:
                status, value = run_guarded(
                    lambda r=r: consensus_outcome(  # type: ignore[misc]
                        members_H,
                        identities,
                        truth_facts,
                        r,
                        alignment_budget=alignment_budget,
                    ),
                    consensus_budget_s,
                )
                if status == "ok":
                    outcome = value
                else:
                    logger.warning("consensus r=%d %s on %s: %s", r, status, collection_id, value)
                    outcome = None
            computed[r] = (outcome, time.perf_counter() - started)
        outcome, secs = computed[r]
        if outcome is None:
            rows.append(
                {
                    **shared,
                    "arm": "fact_rank",
                    "method": "coverage",
                    "radius": label,
                    "secs": secs,
                    "censored": 1,
                    "fact_dist": "",
                    "exact_recovery": "",
                    "medoid_cost": "",
                    "LB": "",
                    "ratio": "",
                    "n_candidates": "",
                    "n_ties": "",
                }
            )
            continue
        rows.append(
            {
                **shared,
                "arm": "fact_rank",
                "method": "coverage",
                "radius": label,
                "secs": secs,
                "censored": 0,
                "fact_dist": outcome.fact_dist,
                "exact_recovery": int(outcome.fact_dist == 0),
                "medoid_cost": "",
                "LB": "",
                "ratio": "",
                "n_candidates": outcome.n_candidates,
                "n_ties": outcome.n_ties,
            }
        )

    started = time.perf_counter()
    try:
        distance = majority_outcome(members_H, identities, truth_facts)
        rows.append(
            {
                **shared,
                "arm": "identities",
                "method": "majority_merge",
                "radius": "",
                "secs": time.perf_counter() - started,
                "censored": 0,
                "fact_dist": distance,
                "exact_recovery": int(distance == 0),
                "medoid_cost": "",
                "LB": "",
                "ratio": "",
                "n_candidates": "",
                "n_ties": "",
            }
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("majority_merge failed on %s: %s", collection_id, exc)
        rows.append(
            {
                **shared,
                "arm": "identities",
                "method": "majority_merge",
                "radius": "",
                "secs": time.perf_counter() - started,
                "censored": 1,
                "fact_dist": "",
                "exact_recovery": "",
                "medoid_cost": "",
                "LB": "",
                "ratio": "",
                "n_candidates": "",
                "n_ties": "",
            }
        )
    return rows, certificate_rows


def identity_ids(record: KBRecord) -> tuple[str, ...]:
    """Return a record's external constant identities, or raise if it has none."""
    if record.constant_ids is None:
        raise RQ3Error(f"record {record.kb_id!r} carries no constant_ids")
    return tuple(record.constant_ids)


# ---------------------------------------------------------------------------
# Unit enumeration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class UnitA:
    """One Corpus A unit: a cell and a seed, holding ``sources_per_cell`` collections."""

    collection: str
    n_members: int
    t: int
    kind: str
    seed: int

    @property
    def cell(self) -> str:
        return f"N{self.n_members}_t{self.t}_{self.kind}"

    @property
    def key(self) -> str:
        return f"A|{self.collection}|{self.cell}|s{self.seed}"


@dataclass(frozen=True)
class UnitB:
    """One Corpus B unit: one maximal run of consecutive encodable quarters."""

    collection: str
    class_id: str
    run_index: int
    kb_ids: tuple[str, ...]

    @property
    def key(self) -> str:
        return f"B|{self.collection}|{self.class_id}|r{self.run_index}"


def enumerate_units_a(config: Mapping[str, Any]) -> list[UnitA]:
    """Enumerate every Corpus A unit in a fixed order."""
    block = config["corpus_a"]
    schedule = seeds(RQ_INDEX, int(config.get("seed_count", 27)))
    units: list[UnitA] = []
    for collection in block["collections"]:
        for n_members in block["n_values"]:
            for t in block["t_values"]:
                for kind in block["kinds"]:
                    for seed in schedule:
                        units.append(UnitA(collection, int(n_members), int(t), str(kind), seed))
    return units


def enumerate_units_b(config: Mapping[str, Any], root: Path | None) -> list[UnitB]:
    """Enumerate every Corpus B unit --- one per maximal run of length ``>= T_min``."""
    block = config["corpus_b"]
    name = str(block["collection"])
    collection = corpora.load_collection(name, root)
    units: list[UnitB] = []
    per_class: dict[str, int] = {}
    for run in corpora.consecutive_runs(collection, int(block.get("min_run_length", 4))):
        class_id = str(run.get("class_id"))
        index = per_class.get(class_id, 0)
        per_class[class_id] = index + 1
        units.append(UnitB(name, class_id, index, tuple(run["kb_ids"])))
    return units


def eligible_sources(collection: KBCollection, window: Mapping[str, Any]) -> list[KBRecord]:
    """Members inside the Corpus A source window, in collection order."""
    return [
        record
        for record in collection.records
        if window["n_min"] <= record.n <= window["n_max"]
        and window["m_min"] <= record.m <= window["m_max"]
        and record.max_arity <= window["max_arity"]
        and record.constant_ids is not None
    ]


def cell_source_window(window: Mapping[str, Any], kind: str, n_members: int) -> dict[str, Any]:
    """Tighten the source window for the cell that needs it.

    A source with ``m`` facts has exactly ``m`` single-fact deletions and fewer
    than that up to isomorphism, so a deletion-only cell asking for ``N``
    pairwise non-isomorphic members is structurally impossible below
    ``m = N``. The floor is set at ``N + 1`` to leave the resampler a margin;
    ``ins`` and ``mix`` keep the frozen window, since an insertion can always
    reach a fact that is not there.

    Parameters
    ----------
    window : Mapping
        The frozen Corpus A window.
    kind : {"ins", "del", "mix"}
        The cell's edit policy.
    n_members : int
        The cell's member count ``N``.

    Returns
    -------
    dict
        The effective window for this cell.
    """
    effective = dict(window)
    if kind == "del":
        effective["m_min"] = max(int(window["m_min"]), n_members + 1)
    return effective


def pool_status(size: int, requested: int) -> str:
    """Name a source pool: ``ok``, ``pool_limited`` or ``infeasible``."""
    if size == 0:
        return "infeasible"
    return "ok" if size >= requested else "pool_limited"


# ---------------------------------------------------------------------------
# Unit execution
# ---------------------------------------------------------------------------


def run_unit_a(
    unit: UnitA,
    config: Mapping[str, Any],
    collection: KBCollection,
    pool: Sequence[KBRecord],
    base: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    """Run one Corpus A unit; return ``(rows, certificate rows, dropped)``."""
    block = config["corpus_a"]
    arms = tuple(config.get("medoid_arms", MEDOID_ARMS))
    sources_per_cell = int(block["sources_per_cell"])
    rng = random.Random(f"{unit.collection}|{unit.cell}|{unit.seed}")
    if not pool:
        logger.warning("cell %s has an empty source pool; nothing to run", unit.key)
        return [], [], 0
    chosen = rng.sample(range(len(pool)), min(sources_per_cell, len(pool)))
    radii: list[tuple[str, int]] = [("2", int(block.get("radius_default", 2))), ("t", unit.t)]

    rows: list[dict[str, Any]] = []
    certificate_rows: list[dict[str, Any]] = []
    dropped = 0
    for index, source_index in enumerate(chosen):
        source = pool[source_index]
        members = variant_collection(
            source, unit.n_members, unit.t, unit.kind, unit.seed * 1_000 + index
        )
        if members is None:
            dropped += 1
            logger.info("dropped collection: %s source=%s", unit.key, source.kb_id)
            continue
        collection_id = f"{unit.cell}|s{unit.seed}|{source.kb_id}"
        unit_rows, unit_certificates = evaluate_collection(
            members=members,
            truth=source,
            collection=collection,
            radii=radii,
            arms=arms,
            base_row={
                **base,
                "rq": RQ,
                "experiment": EXPERIMENT_A,
                "collection": unit.collection,
                "seed": unit.seed,
                "cell": unit.cell,
                "cell_N": unit.n_members,
                "cell_t": unit.t,
                "cell_kind": unit.kind,
                "source_id": source.kb_id,
            },
            collection_id=collection_id,
            unit=unit.key,
            alignment_budget=str(block.get("alignment_budget", "triangle")),
            consensus_budget_s=_budget(block.get("consensus_budget_s")),
        )
        rows.extend(unit_rows)
        certificate_rows.extend(unit_certificates)
    return rows, certificate_rows, dropped


def run_unit_b(
    unit: UnitB,
    config: Mapping[str, Any],
    collection: KBCollection,
    preserving: Mapping[tuple[str, str], bool],
    base: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Run one Corpus B unit and return its ``rows_natural`` rows."""
    block = config["corpus_b"]
    arms = tuple(config.get("medoid_arms", MEDOID_ARMS))
    by_id = corpora.records_by_id(collection)
    records = [by_id[kb_id] for kb_id in unit.kb_ids]
    members, truth = records[:-1], records[-1]
    regime = all(
        preserving.get((a, b), False) for a, b in zip(unit.kb_ids, unit.kb_ids[1:], strict=False)
    )
    rows, _ = evaluate_collection(
        members=members,
        truth=truth,
        collection=collection,
        radii=[("2", int(block.get("radius", 2)))],
        arms=arms,
        base_row={
            **base,
            "rq": RQ,
            "experiment": EXPERIMENT_B,
            "collection": unit.collection,
            "seed": 0,
            "class_id": unit.class_id,
            "run_index": unit.run_index,
            "T": len(records),
            "regime_preserving": int(regime),
        },
        collection_id=f"{unit.class_id}|run{unit.run_index}",
        unit=unit.key,
        alignment_budget=str(block.get("alignment_budget", "triangle")),
        consensus_budget_s=_budget(block.get("consensus_budget_s", 1800)),
    )
    return rows


def _budget(value: Any) -> float | None:
    """Read a wall-clock budget from the config: ``None`` or a positive float."""
    if value is None:
        return None
    budget = float(value)
    return budget if budget > 0 else None


# ---------------------------------------------------------------------------
# Shard driver
# ---------------------------------------------------------------------------


def _shard_paths(out: Path, rq_dir: str, experiment: str, index: int, count: int) -> io.RunPaths:
    return io.RunPaths(root=out, rq=rq_dir, experiment=f"{experiment}/{PARTS}/{_tag(index, count)}")


def _tag(index: int, count: int) -> str:
    return f"shard_{index:03d}of{count:03d}"


def _done_units(path: Path) -> set[str]:
    """Unit keys already present in a shard's rows file (the resume authority)."""
    if not path.is_file():
        return set()
    import csv

    with path.open(encoding="utf-8", newline="") as handle:
        return {row["unit"] for row in csv.DictReader(handle) if row.get("unit")}


def _read_rows(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    import csv

    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def run_shard(
    config: Mapping[str, Any],
    out: Path,
    shard: tuple[int, int],
    *,
    data_root: Path | None,
    start_cutoff_s: float | None,
) -> dict[str, Any]:
    """Execute one shard of the RQ3 unit list.

    Parameters
    ----------
    config : Mapping
        The parsed configuration.
    out : Path
        Results root the six files are written under.
    shard : tuple of int
        ``(index, count)``, one-based index.
    data_root : Path or None
        Corpora root override.
    start_cutoff_s : float or None
        Refuse to *start* a unit after this many seconds have elapsed (the first
        unit of the shard is exempt, or the shard livelocks).

    Returns
    -------
    dict
        The shard's summary: counts, drops and deferrals.
    """
    index, count = shard
    started = time.perf_counter()
    git_sha, host_cpu = provenance()
    base = {"git_sha": git_sha, "host_cpu": host_cpu}
    stamps = deploy_stamps()

    units_a = enumerate_units_a(config)
    units_b = enumerate_units_b(config, data_root)
    mine_a = [u for i, u in enumerate(units_a) if i % count == index - 1]
    mine_b = [u for i, u in enumerate(units_b) if (len(units_a) + i) % count == index - 1]

    paths_a = _shard_paths(out, RQ_DIR, EXPERIMENT_A, index, count)
    paths_b = _shard_paths(out, RQ_DIR, EXPERIMENT_B, index, count)
    paths_c = _shard_paths(out, CERT_RQ_DIR, CERT_EXPERIMENT, index, count)

    rows_a = _read_rows(paths_a.dir / "rows_variants.csv")
    rows_b = _read_rows(paths_b.dir / "rows_natural.csv")
    rows_c = _read_rows(paths_c.dir / "rows_certificate.csv")
    done = _done_units(paths_a.dir / "rows_variants.csv") | _done_units(
        paths_b.dir / "rows_natural.csv"
    )

    collections: dict[str, KBCollection] = {}
    pools: dict[tuple[str, str, int], list[KBRecord]] = {}
    window = config["corpus_a"]["source_window"]
    sources_per_cell = int(config["corpus_a"]["sources_per_cell"])

    def load(name: str) -> KBCollection:
        if name not in collections:
            collections[name] = corpora.load_collection(name, data_root)
        return collections[name]

    summary: dict[str, Any] = {
        "shard": _tag(index, count),
        "n_units_a": len(mine_a),
        "n_units_b": len(mine_b),
        "dropped_total": 0,
        "dropped_by_cell": {},
        "source_pools": {},
        "deferred": [],
        "resumed": len(done),
    }

    # The pools are built for every configured cell, not only this shard's, so
    # config.json and summary.json describe the whole design whichever shard
    # wrote them.
    if mine_a:
        block = config["corpus_a"]
        for name in block["collections"]:
            for kind in block["kinds"]:
                for n_members in (int(value) for value in block["n_values"]):
                    key = (str(name), str(kind), n_members)
                    effective = cell_source_window(window, key[1], n_members)
                    pools[key] = eligible_sources(load(key[0]), effective)
                    status = pool_status(len(pools[key]), sources_per_cell)
                    record: dict[str, Any] = {
                        "collection": key[0],
                        "kind": key[1],
                        "N": n_members,
                        "m_min": effective["m_min"],
                        "m_max": effective["m_max"],
                        "n_pool": len(pools[key]),
                        "status": status,
                    }
                    if status == "infeasible":
                        record["reason"] = (
                            f"no member of {key[0]} has {effective['m_min']} <= m <= "
                            f"{effective['m_max']} inside the source window, so {n_members} "
                            "pairwise non-isomorphic deletion variants cannot exist"
                        )
                    elif status == "pool_limited":
                        record["reason"] = (
                            f"only {len(pools[key])} of the {sources_per_cell} requested "
                            "sources satisfy the cell's window"
                        )
                    summary["source_pools"][f"{key[0]}|{key[1]}|N{n_members}"] = record
                    logger.info(
                        "source pool %s|%s|N%d: %d members (%s)",
                        key[0],
                        key[1],
                        n_members,
                        len(pools[key]),
                        status,
                    )

    def pool_of(unit: UnitA) -> list[KBRecord]:
        """The cell's source pool, tightened for deletion-only cells."""
        return pools[(unit.collection, unit.kind, unit.n_members)]

    executed = 0
    for unit in mine_a:
        if unit.key in done:
            continue
        if executed and start_cutoff_s and time.perf_counter() - started >= start_cutoff_s:
            summary["deferred"].append(unit.key)
            continue
        collection = load(unit.collection)
        unit_rows, unit_certificates, dropped = run_unit_a(
            unit, config, collection, pool_of(unit), base
        )
        rows_a.extend(unit_rows)
        rows_c.extend(unit_certificates)
        summary["dropped_total"] += dropped
        if dropped:
            key = f"{unit.collection}|{unit.cell}"
            summary["dropped_by_cell"][key] = summary["dropped_by_cell"].get(key, 0) + dropped
        io.write_rows(paths_c, "certificate", rows_c, columns=CERTIFICATE_COLUMNS)
        io.write_rows(paths_a, "variants", rows_a, columns=VARIANT_COLUMNS)
        executed += 1
        logger.info("unit done: %s (%d rows)", unit.key, len(unit_rows))

    for unit in mine_b:
        if unit.key in done:
            continue
        if executed and start_cutoff_s and time.perf_counter() - started >= start_cutoff_s:
            summary["deferred"].append(unit.key)
            continue
        collection = load(unit.collection)
        preserving = {
            (str(pair["a"]), str(pair["b"])): bool(pair.get("constant_preserving"))
            for pair in corpora.consecutive_pairs(collection)
        }
        rows_b.extend(run_unit_b(unit, config, collection, preserving, base))
        io.write_rows(paths_b, "natural", rows_b, columns=NATURAL_COLUMNS)
        executed += 1
        logger.info("unit done: %s", unit.key)

    summary["secs"] = time.perf_counter() - started
    summary["n_rows_variants"] = len(rows_a)
    summary["n_rows_natural"] = len(rows_b)
    summary["n_rows_certificate"] = len(rows_c)
    summary["n_units_executed"] = executed

    # The effective per-cell source windows are a parameter of the run, not an
    # outcome, so they belong in config.json as well as in the summary.
    written_config = {
        **dict(config),
        "derived": {
            "shard": _tag(index, count),
            "source_pools": summary["source_pools"],
            "n_units_a_total": len(units_a),
            "n_units_b_total": len(units_b),
        },
    }

    if mine_a or rows_a:
        io.write_rows(paths_a, "variants", rows_a, columns=VARIANT_COLUMNS)
        io.write_config(paths_a, written_config)
        io.write_summary(paths_a, summary)
        io.write_manifest(
            paths_a,
            extra={"complete": not summary["deferred"], "shard": shard, **stamps},
        )
    if mine_b or rows_b:
        io.write_rows(paths_b, "natural", rows_b, columns=NATURAL_COLUMNS)
        io.write_config(paths_b, written_config)
        io.write_summary(paths_b, summary)
        io.write_manifest(
            paths_b,
            extra={"complete": not summary["deferred"], "shard": shard, **stamps},
        )
    if mine_a or rows_c:
        io.write_rows(paths_c, "certificate", rows_c, columns=CERTIFICATE_COLUMNS)
        io.write_config(paths_c, written_config)
        io.write_manifest(
            paths_c,
            extra={"complete": not summary["deferred"], "shard": shard, **stamps},
        )
    return summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_shard(text: str) -> tuple[int, int]:
    try:
        left, right = text.split("/")
        index, count = int(left), int(right)
    except ValueError as exc:
        raise TkdeConfigError(f"--shard expects 'i/N', got {text!r}") from exc
    if not 1 <= index <= count:
        raise TkdeConfigError(f"--shard index out of range: {text!r}")
    return index, count


def _apply_smoke(config: dict[str, Any]) -> dict[str, Any]:
    """Shrink the configuration to the pre-registered smoke cell."""
    smoke = config.get("smoke") or {}
    merged = dict(config)
    merged["seed_count"] = int(smoke.get("seed_count", 1))
    merged["corpus_a"] = {**config["corpus_a"], **(smoke.get("corpus_a") or {})}
    merged["corpus_b"] = {**config["corpus_b"], **(smoke.get("corpus_b") or {})}
    if "medoid_arms" in smoke:
        merged["medoid_arms"] = smoke["medoid_arms"]
    merged["smoke"] = True
    return merged


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point of ``python -m experiments.tkde.rq3``."""
    parser = argparse.ArgumentParser(description="RQ3 --- the representative record")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--shard", default="1/1")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--count", action="store_true", help="print the unit count and exit")
    parser.add_argument("--data-root", type=Path, default=None)
    parser.add_argument("--start-cutoff-s", type=float, default=None)
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, str(args.log_level).upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    config = load_yaml(args.config)
    if args.smoke:
        config = _apply_smoke(config)

    if args.count:
        total = len(enumerate_units_a(config)) + len(enumerate_units_b(config, args.data_root))
        print(total)
        return 0

    out = Path(args.out) if args.out is not None else results_root()
    summary = run_shard(
        config,
        out,
        _parse_shard(args.shard),
        data_root=args.data_root,
        start_cutoff_s=args.start_cutoff_s,
    )
    logger.info(
        "shard %s: %d variant rows, %d natural rows, %d certificate rows, %d dropped, %.1f s",
        summary["shard"],
        summary["n_rows_variants"],
        summary["n_rows_natural"],
        summary["n_rows_certificate"],
        summary["dropped_total"],
        summary["secs"],
    )
    if summary["deferred"]:
        logger.warning("deferred %d units at the start cutoff", len(summary["deferred"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
