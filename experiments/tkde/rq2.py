"""RQ2 runner -- well-posedness, and the measured price of each missing property.

Implements ``DESIGN.md`` §3 steps 0-3 and 5:

0. exactness at zero, both directions, on 100 isomorphic pairs per collection
   and arm (``rows_exact0``);
1. the false-merge census over every arm with a matrix (``rows_census``);
2. bipartite metricity on real members -- asymmetry, triangle violations, and
   the raw assignment reading's false zeros (``rows_bipartite``);
3. the exact oracle's ceiling by ``n`` stratum under a 600 s budget
   (``rows_oracle``), plus the gated HyperCOT timing row
   (``rows_hypercot_timing``).

Step 4 (certificate validity) is produced by the RQ3 runner into
``RQ2_wellposedness/certificate_validity/rows_certificate.csv`` and is read by
:mod:`experiments.tkde.analyze_rq2`, not here. Step 5 (identity timing) is
RQ7's ``rows_yield``.

**Every per-pair computation is bounded at the process level.** The pointer arm
and the oracles do not return to the interpreter on time-out, so a ``SIGALRM``
and the oracles' own ``timeout`` argument do not bound them (measured,
``COMPETITOR_AUDIT.md`` §1). Every arm therefore runs through
:func:`experiments.tkde.budget.run_with_budget_detail`, uniformly: a fork costs
milliseconds and the uniform rule removes the chance of exempting the wrong arm.

**Matrix provenance.** The census reads the cached ``N x N`` matrices under
``<results_root>/matrices/<collection>/<arm>.npy`` for ``wd50k66`` and
``ndc_classes`` -- they are produced once by the shared matrices job, and this
runner never rebuilds them. ``ndc_substances`` is this runner's own and is built
here, into the same cache layout.
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import random
import sys
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from experiments.tkde import corpora as corpora_io
from experiments.tkde.budget import run_with_budget_detail
from experiments.tkde.config import TkdeConfigError, load_yaml, seeds
from experiments.tkde.io import RunPaths, write_config, write_manifest, write_rows
from experiments.tkde.rq1 import corpora_root

logger = logging.getLogger(__name__)

RQ_INDEX = 2
RQ_FOLDER = "RQ2_wellposedness"
EXPERIMENT = "wellposedness"
CERTIFICATE_EXPERIMENT = "certificate_validity"

POINTER_ARM = "isalhg_levenshtein"
ORACLE_ARMS: frozenset[str] = frozenset({"exact_ged", "exact_hged", "qin_hged"})
ZERO_TOLERANCE = 1e-9

UNIVERSAL_COLUMNS: tuple[str, ...] = ("rq", "experiment", "git_sha", "host_cpu")

COLUMNS_EXACT0: tuple[str, ...] = (
    *UNIVERSAL_COLUMNS,
    "collection",
    "seed",
    "arm",
    "pair_id",
    "d",
    "at_zero",
    "secs",
    "censored",
    "error",
)
COLUMNS_CENSUS: tuple[str, ...] = (
    *UNIVERSAL_COLUMNS,
    "collection",
    "seed",
    "arm",
    "n_members",
    "n_pairs",
    "n_noniso_pairs",
    "n_false_merges",
    "n_classes_arm",
    "n_classes_true",
    "tolerance",
    "source",
    "secs",
    "censored",
    "error",
)
COLUMNS_BIPARTITE: tuple[str, ...] = (
    *UNIVERSAL_COLUMNS,
    "collection",
    "seed",
    "arm",
    "kind",
    "ids",
    "d_ab",
    "d_ba",
    "d_bc",
    "d_ac",
    "violation",
    "secs",
    "censored",
)
COLUMNS_ORACLE: tuple[str, ...] = (
    *UNIVERSAL_COLUMNS,
    "collection",
    "seed",
    "arm",
    "stratum",
    "pair_id",
    "n_a",
    "n_b",
    "m_a",
    "m_b",
    "secs",
    "censored",
    "value",
    "error",
)
COLUMNS_HYPERCOT: tuple[str, ...] = (
    *UNIVERSAL_COLUMNS,
    "collection",
    "seed",
    "arm",
    "pair_id",
    "n_a",
    "n_b",
    "secs",
    "censored",
    "value",
    "error",
)

STRATA: tuple[tuple[str, int, int], ...] = (("<=6", 0, 6), ("7-8", 7, 8), ("9-10", 9, 10))


class Rq2Error(TkdeConfigError):
    """The RQ2 runner was asked for something the design does not define."""


# ---------------------------------------------------------------------------
# Units
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Unit:
    """One independently computable, independently resumable piece of work."""

    kind: str
    label: str
    extra: Mapping[str, Any] = field(default_factory=dict)

    @property
    def unit_id(self) -> str:
        """Stable id; part of every row file name this unit writes.

        The stratum labels of ``DESIGN.md`` §3 contain ``<`` and ``>``, which
        are legal in a POSIX file name but hazardous in every shell that later
        touches the results tree, so they are spelled ``le`` / ``gt`` here. The
        rows keep the design's own labels.
        """
        safe = self.label.replace("<=", "le").replace(">=", "ge").replace(">", "gt")
        return f"{self.kind}-{safe}"

    @property
    def tables(self) -> tuple[str, ...]:
        """Row tables this unit is responsible for."""
        return {
            "exact0": ("exact0",),
            "census": ("census",),
            "bipartite": ("bipartite",),
            "oracle": ("oracle",),
            "hypercot": ("hypercot_timing",),
        }[self.kind]


def enumerate_units(config: Mapping[str, Any], kinds: Sequence[str] | None = None) -> list[Unit]:
    """Every unit of this configuration, in a deterministic order.

    Parameters
    ----------
    config : Mapping
        The parsed configuration.
    kinds : Sequence[str] or None, optional
        Restrict to these unit kinds. The census units are the only ones that
        depend on the shared matrices job, so they are submitted as their own
        array under ``--dependency=afterok`` while the rest run immediately;
        this filter is how the two submissions are separated.

    Returns
    -------
    list[Unit]
        The units, filtered.
    """
    units: list[Unit] = []
    for collection in config.get("exact0_collections") or []:
        for arm in config.get("exact0_arms") or []:
            units.append(
                Unit("exact0", f"{collection}-{arm}", extra={"collection": collection, "arm": arm})
            )
    for collection in config.get("census_collections") or []:
        for arm in config.get("census_arms") or []:
            units.append(
                Unit("census", f"{collection}-{arm}", extra={"collection": collection, "arm": arm})
            )
    for collection in config.get("bipartite_collections") or []:
        units.append(Unit("bipartite", collection, extra={"collection": collection}))
    for collection in config.get("oracle_collections") or []:
        for name, _, _ in STRATA:
            units.append(
                Unit(
                    "oracle",
                    f"{collection}-n{name}",
                    extra={"collection": collection, "stratum": name},
                )
            )
    for collection in config.get("hypercot_collections") or []:
        units.append(Unit("hypercot", collection, extra={"collection": collection}))
    if kinds:
        wanted = set(kinds)
        units = [unit for unit in units if unit.kind in wanted]
    return units


# ---------------------------------------------------------------------------
# Bounded pair evaluation
# ---------------------------------------------------------------------------


def arm_budget(arm: str, config: Mapping[str, Any]) -> float:
    """Budget of one arm: 60 s for the pointer, 600 s for an oracle, else the default."""
    if arm == POINTER_ARM:
        return float(config.get("pointer_budget_s", 60.0))
    if arm in ORACLE_ARMS or arm == "hypercot":
        return float(config.get("oracle_budget_s", 600.0))
    return float(config.get("arm_budget_s", 60.0))


def _pairwise(arm: str, H1: Any, H2: Any) -> float:
    from isalhg.metric_space.registry import get_distance

    return float(get_distance(arm).pairwise(H1, H2))


def bounded_pairwise(arm: str, H1: Any, H2: Any, seconds: float) -> tuple[Any, float, bool, str]:
    """``(value, secs, censored, error)`` for one pair, bounded at the process level.

    HyperCOT's cost is a numerical optimum rather than an exact count and has
    been measured returning a small *negative* number on an isomorphic pair
    (-9.9e-16). It is clamped at zero here rather than downstream, so no reader
    has to remember to.
    """
    result = run_with_budget_detail(_pairwise, (arm, H1, H2), seconds)
    value = result.value
    if value is not None and arm == "hypercot":
        value = max(0.0, float(value))
    return value, result.secs, result.censored, result.error or ""


def is_zero(value: Any) -> bool:
    """The design's "distance 0" for a real-valued arm: strictly below 1e-9."""
    return value is not None and abs(float(value)) < ZERO_TOLERANCE


def _true_class_ids(graphs: Sequence[Any]) -> list[str]:
    """Isomorphism class of every member, by the pynauty Levi fingerprint."""
    from isalhg.iso_backends.canonical_order import nauty_certificate_bytes

    return [
        hashlib.sha1(nauty_certificate_bytes(H), usedforsecurity=False).hexdigest() for H in graphs
    ]


# ---------------------------------------------------------------------------
# Step 0 -- exactness at zero
# ---------------------------------------------------------------------------


def run_exact0(unit: Unit, ctx: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """100 isomorphic pairs (random relabellings) per collection and arm."""
    from isalhg.core.sparse_hypergraph import permute

    collection = ctx["collection"]
    graphs = ctx["graphs"]
    arm = str(unit.extra["arm"])
    config = ctx["config"]
    count = int(config.get("exact0_pairs", 100))
    seconds = arm_budget(arm, config)
    master = seeds(RQ_INDEX)[0]

    rng = random.Random(master + 7)
    size = len(graphs)
    rows: list[dict[str, Any]] = []
    for index in range(min(count, size)):
        member = rng.randrange(size)
        H = graphs[member]
        order = list(range(collection.records[member].n))
        rng.shuffle(order)
        H_permuted = permute(H, {node: order[node] for node in range(len(order))})
        value, secs, censored, error = bounded_pairwise(arm, H, H_permuted, seconds)
        rows.append(
            {
                **ctx["stamp"],
                "collection": collection.name,
                "seed": master + 7,
                "arm": arm,
                "pair_id": f"{collection.records[member].kb_id}|sigma{index}",
                "d": "" if value is None else value,
                "at_zero": "" if value is None else int(is_zero(value)),
                "secs": round(secs, 6),
                "censored": int(censored),
                "error": error,
            }
        )
    return {"exact0": rows}


# ---------------------------------------------------------------------------
# Step 1 -- the false-merge census
# ---------------------------------------------------------------------------


def matrix_for(
    collection: Any,
    graphs: Sequence[Any],
    arm: str,
    *,
    matrices_root: Path,
    own: bool,
    n_jobs: int,
) -> tuple[Any, str]:
    """Return ``(D, source)`` -- the cached matrix, or one built here.

    ``own`` marks the collections this runner is responsible for computing
    (``ndc_substances``). For the others the matrix is an input produced by the
    shared matrices job; a missing one is an error, never a silent rebuild that
    would double the campaign's cost and produce a second, unversioned copy.
    """
    import json

    import numpy as np

    from isalhg.metric_space.toolkit.matrix import build_matrix, cache_paths, member_order_sha1

    cache_dir = matrices_root / collection.name
    matrix_path, manifest_path = cache_paths(cache_dir, arm)
    member_ids = [record.kb_id for record in collection.records]
    if not own:
        if not matrix_path.is_file():
            raise Rq2Error(
                f"no cached matrix at {matrix_path}; the census depends on the shared "
                f"matrices job (submit with --dependency=afterok:<matrices job id>)"
            )
        # The .npy records nothing about which members its rows are, so a cache
        # whose member order differs from ours would index a correct-looking
        # matrix with the wrong ids and produce a plausible wrong census. The
        # manifest's SHA-1 of the member-id list is what rules that out.
        expected = member_order_sha1(member_ids)
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise Rq2Error(f"unreadable matrix manifest at {manifest_path}: {exc}") from exc
        if manifest.get("member_order_sha1") != expected:
            raise Rq2Error(
                f"{matrix_path} was built over a different member order "
                f"({manifest.get('member_order_sha1')} != {expected}); refusing to index it"
            )
        matrix = np.load(matrix_path)
        if matrix.shape[0] != len(member_ids):
            raise Rq2Error(
                f"{matrix_path} is {matrix.shape[0]}x{matrix.shape[0]} but the collection "
                f"has {len(member_ids)} members"
            )
        return matrix, "cache"
    matrix = build_matrix(
        list(graphs),
        arm,
        member_ids=member_ids,
        roles=corpora_io.roles_maps(collection) if arm.endswith("roles") else None,
        cache_dir=cache_dir,
        n_jobs=n_jobs,
    )
    return matrix, "computed"


def census_counts(matrix: Any, class_ids: Sequence[str]) -> dict[str, int]:
    """False merges and induced classes of one arm on one collection.

    A *false merge* is an unordered pair the arm places at distance 0 whose
    members are not isomorphic by the nauty fingerprint. The *induced classes*
    are the connected components of the zero-distance graph -- the coarsest
    partition the arm's own zero relation can support.
    """
    import numpy as np
    from scipy.sparse import csr_matrix
    from scipy.sparse.csgraph import connected_components

    size = len(class_ids)
    codes = {name: index for index, name in enumerate(sorted(set(class_ids)))}
    labels = np.array([codes[name] for name in class_ids], dtype=np.int64)

    zero = np.abs(np.asarray(matrix, dtype=np.float64)) < ZERO_TOLERANCE
    np.fill_diagonal(zero, False)
    upper = np.triu(zero, k=1)
    rows, cols = np.nonzero(upper)
    false_merges = int(np.count_nonzero(labels[rows] != labels[cols]))

    n_pairs = size * (size - 1) // 2
    _, counts = np.unique(labels, return_counts=True)
    same_class_pairs = int(np.sum(counts * (counts - 1) // 2))
    n_components, _ = connected_components(csr_matrix(zero), directed=False, return_labels=True)
    return {
        "n_members": size,
        "n_pairs": n_pairs,
        "n_noniso_pairs": n_pairs - same_class_pairs,
        "n_false_merges": false_merges,
        "n_classes_arm": int(n_components),
        "n_classes_true": len(codes),
    }


def run_census(unit: Unit, ctx: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """One ``(collection, arm)`` census row."""
    collection = ctx["collection"]
    graphs = ctx["graphs"]
    arm = str(unit.extra["arm"])
    config = ctx["config"]
    own = collection.name in set(config.get("census_own_collections") or ())
    master = seeds(RQ_INDEX)[0]

    base = {
        **ctx["stamp"],
        "collection": collection.name,
        "seed": master,
        "arm": arm,
        "tolerance": ZERO_TOLERANCE,
        "censored": 0,
    }
    started = time.monotonic()
    try:
        matrix, source = matrix_for(
            collection,
            graphs,
            arm,
            matrices_root=ctx["matrices_root"],
            own=own,
            n_jobs=int(config.get("n_jobs", 1)),
        )
    except Exception as exc:  # noqa: BLE001 - a missing input is reported, not raised
        logger.error("census %s/%s failed: %s", collection.name, arm, exc)
        return {
            "census": [
                {
                    **base,
                    "n_members": len(graphs),
                    "n_pairs": "",
                    "n_noniso_pairs": "",
                    "n_false_merges": "",
                    "n_classes_arm": "",
                    "n_classes_true": "",
                    "source": "missing",
                    "secs": round(time.monotonic() - started, 3),
                    "error": f"{type(exc).__name__}: {exc}",
                }
            ]
        }

    counts = census_counts(matrix, ctx["class_ids"])
    return {
        "census": [
            {
                **base,
                **counts,
                "source": source,
                "secs": round(time.monotonic() - started, 3),
                "error": "",
            }
        ]
    }


# ---------------------------------------------------------------------------
# Step 2 -- bipartite metricity
# ---------------------------------------------------------------------------


def run_bipartite(unit: Unit, ctx: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Asymmetry, triangle violations, and the assignment reading's false zeros."""
    collection = ctx["collection"]
    graphs = ctx["graphs"]
    config = ctx["config"]
    path_arm = str(config.get("bipartite_path_arm", "bipartite_ged_path"))
    assign_arm = str(config.get("bipartite_assign_arm", "bipartite_ged_assign"))
    n_pairs = int(config.get("bipartite_pairs", 2000))
    n_triples = int(config.get("bipartite_triples", 5000))
    seconds = arm_budget(path_arm, config)
    master = seeds(RQ_INDEX)[0]
    size = len(graphs)
    ids = [record.kb_id for record in collection.records]
    class_ids = ctx["class_ids"]

    rng = random.Random(master + 13)
    rows: list[dict[str, Any]] = []

    for index in range(n_pairs if size >= 2 else 0):
        a, b = rng.sample(range(size), 2)
        d_ab, secs_ab, cen_ab, _ = bounded_pairwise(path_arm, graphs[a], graphs[b], seconds)
        d_ba, secs_ba, cen_ba, _ = bounded_pairwise(path_arm, graphs[b], graphs[a], seconds)
        violation = ""
        if d_ab is not None and d_ba is not None:
            violation = int(abs(float(d_ab) - float(d_ba)) > ZERO_TOLERANCE)
        rows.append(
            {
                **ctx["stamp"],
                "collection": collection.name,
                "seed": master + 13,
                "arm": path_arm,
                "kind": "pair",
                "ids": f"{ids[a]}|{ids[b]}|{index}",
                "d_ab": "" if d_ab is None else d_ab,
                "d_ba": "" if d_ba is None else d_ba,
                "d_bc": "",
                "d_ac": "",
                "violation": violation,
                "secs": round(secs_ab + secs_ba, 6),
                "censored": int(cen_ab or cen_ba),
            }
        )

    for index in range(n_triples if size >= 3 else 0):
        a, b, c = rng.sample(range(size), 3)
        d_ab, s1, c1, _ = bounded_pairwise(path_arm, graphs[a], graphs[b], seconds)
        d_bc, s2, c2, _ = bounded_pairwise(path_arm, graphs[b], graphs[c], seconds)
        d_ac, s3, c3, _ = bounded_pairwise(path_arm, graphs[a], graphs[c], seconds)
        violation = ""
        if None not in (d_ab, d_bc, d_ac):
            violation = int(float(d_ac) > float(d_ab) + float(d_bc) + ZERO_TOLERANCE)
        rows.append(
            {
                **ctx["stamp"],
                "collection": collection.name,
                "seed": master + 13,
                "arm": path_arm,
                "kind": "triple",
                "ids": f"{ids[a]}|{ids[b]}|{ids[c]}|{index}",
                "d_ab": "" if d_ab is None else d_ab,
                "d_ba": "",
                "d_bc": "" if d_bc is None else d_bc,
                "d_ac": "" if d_ac is None else d_ac,
                "violation": violation,
                "secs": round(s1 + s2 + s3, 6),
                "censored": int(c1 or c2 or c3),
            }
        )

    for index in range(n_pairs if size >= 2 else 0):
        a, b = rng.sample(range(size), 2)
        if class_ids[a] == class_ids[b]:
            continue  # a zero here would be correct, not a false zero
        value, secs, censored, _ = bounded_pairwise(assign_arm, graphs[a], graphs[b], seconds)
        rows.append(
            {
                **ctx["stamp"],
                "collection": collection.name,
                "seed": master + 13,
                "arm": assign_arm,
                "kind": "false_zero",
                "ids": f"{ids[a]}|{ids[b]}|{index}",
                "d_ab": "" if value is None else value,
                "d_ba": "",
                "d_bc": "",
                "d_ac": "",
                "violation": "" if value is None else int(is_zero(value)),
                "secs": round(secs, 6),
                "censored": int(censored),
            }
        )
    return {"bipartite": rows}


# ---------------------------------------------------------------------------
# Step 3 -- the oracle ceiling, and the gated HyperCOT timing row
# ---------------------------------------------------------------------------


def stratum_members(collection: Any, name: str, m_max: int) -> list[int]:
    """Indices of the members inside one ``n`` stratum with ``m <= m_max``."""
    low, high = next((lo, hi) for label, lo, hi in STRATA if label == name)
    return [
        index
        for index, record in enumerate(collection.records)
        if low <= record.n <= high and record.m <= m_max
    ]


def run_oracle(unit: Unit, ctx: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """``exact_ged`` on 30 real pairs of one stratum, 600 s process budget."""
    collection = ctx["collection"]
    graphs = ctx["graphs"]
    config = ctx["config"]
    arm = str(config.get("oracle_arm", "exact_ged"))
    stratum = str(unit.extra["stratum"])
    count = int(config.get("oracle_pairs", 30))
    m_max = int(config.get("oracle_m_max", 8))
    seconds = arm_budget(arm, config)
    master = seeds(RQ_INDEX)[0]

    candidates = stratum_members(collection, stratum, m_max)
    rows: list[dict[str, Any]] = []
    if len(candidates) < 2:
        return {"oracle": rows}

    rng = random.Random(master + 29)
    for index in range(count):
        a, b = rng.sample(candidates, 2)
        value, secs, censored, error = bounded_pairwise(arm, graphs[a], graphs[b], seconds)
        rows.append(
            {
                **ctx["stamp"],
                "collection": collection.name,
                "seed": master + 29,
                "arm": arm,
                "stratum": stratum,
                "pair_id": f"{collection.records[a].kb_id}|{collection.records[b].kb_id}|{index}",
                "n_a": collection.records[a].n,
                "n_b": collection.records[b].n,
                "m_a": collection.records[a].m,
                "m_b": collection.records[b].m,
                "secs": round(secs, 6),
                "censored": int(censored),
                "value": "" if value is None else value,
                "error": error,
            }
        )
    return {"oracle": rows}


def run_hypercot(unit: Unit, ctx: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """The single HyperCOT timing row set, gated at ``N <= 20`` members (L24)."""
    collection = ctx["collection"]
    graphs = ctx["graphs"]
    config = ctx["config"]
    arm = "hypercot"
    count = int(config.get("hypercot_pairs", 20))
    gate = int(config.get("hypercot_member_gate", 20))
    seconds = arm_budget(arm, config)
    master = seeds(RQ_INDEX)[0]

    size = min(gate, len(graphs))
    rows: list[dict[str, Any]] = []
    if size < 2:
        return {"hypercot_timing": rows}

    rng = random.Random(master + 31)
    for index in range(count):
        a, b = rng.sample(range(size), 2)
        value, secs, censored, error = bounded_pairwise(arm, graphs[a], graphs[b], seconds)
        rows.append(
            {
                **ctx["stamp"],
                "collection": collection.name,
                "seed": master + 31,
                "arm": arm,
                "pair_id": f"{collection.records[a].kb_id}|{collection.records[b].kb_id}|{index}",
                "n_a": collection.records[a].n,
                "n_b": collection.records[b].n,
                "secs": round(secs, 6),
                "censored": int(censored),
                "value": "" if value is None else value,
                "error": error,
            }
        )
    return {"hypercot_timing": rows}


RUNNERS = {
    "exact0": run_exact0,
    "census": run_census,
    "bipartite": run_bipartite,
    "oracle": run_oracle,
    "hypercot": run_hypercot,
}
COLUMNS = {
    "exact0": COLUMNS_EXACT0,
    "census": COLUMNS_CENSUS,
    "bipartite": COLUMNS_BIPARTITE,
    "oracle": COLUMNS_ORACLE,
    "hypercot_timing": COLUMNS_HYPERCOT,
}


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def _stamp() -> dict[str, Any]:
    # Private helpers of this package's own io module: the provenance stamped
    # into every row must be the one the manifest reports.
    from experiments.tkde.io import _cpu_model, _repo_provenance

    return {
        "rq": RQ_INDEX,
        "experiment": EXPERIMENT,
        "git_sha": _repo_provenance()["git_sha"],
        "host_cpu": _cpu_model(),
    }


def _unit_context(
    unit: Unit,
    config: Mapping[str, Any],
    results_root: Path,
    data_root: Path | None = None,
) -> dict[str, Any]:
    name = str(unit.extra["collection"])
    root = corpora_root(results_root, name, data_root)
    if root is None:
        raise Rq2Error(
            f"no frozen collection {name!r}: looked under --data-root {data_root}, "
            f"{results_root}/corpora, $ISALHG_RESULTS_ROOT and $ISALHG_DATA_ROOT"
        )
    collection = corpora_io.load_collection(name, root)
    limit = config.get("member_limit")
    if limit:
        collection = corpora_io.subset(
            collection,
            [record.kb_id for record in collection.records[: int(limit)]],
            name=collection.name,
        )
    graphs = corpora_io.hypergraphs(collection)
    context: dict[str, Any] = {
        "collection": collection,
        "graphs": graphs,
        "config": config,
        "stamp": _stamp(),
        "matrices_root": Path(results_root) / "matrices",
    }
    if unit.kind in ("census", "bipartite"):
        context["class_ids"] = _true_class_ids(graphs)
    return context


def unit_is_done(paths: RunPaths, unit: Unit) -> bool:
    """True when every row file this unit owns exists and parses as CSV."""
    import csv

    for table in unit.tables:
        target = paths.dir / f"rows_{table}__{unit.unit_id}.csv"
        if not target.is_file():
            return False
        try:
            with target.open(encoding="utf-8", newline="") as handle:
                next(csv.reader(handle))
        except (OSError, StopIteration, UnicodeDecodeError):
            return False
    return True


def run_unit(
    unit: Unit,
    config: Mapping[str, Any],
    paths: RunPaths,
    data_root: Path | None = None,
) -> dict[str, int]:
    """Compute one unit and write its row files."""
    context = _unit_context(unit, config, Path(paths.root), data_root)
    tables = RUNNERS[unit.kind](unit, context)
    counts: dict[str, int] = {}
    for table, rows in tables.items():
        write_rows(paths, f"{table}__{unit.unit_id}", rows, columns=COLUMNS[table])
        counts[table] = len(rows)
    return counts


def smoke_config(config: dict[str, Any]) -> dict[str, Any]:
    """Shrink a configuration to the ``--smoke`` shape (minutes, not hours)."""
    smoke = dict(config)
    smoke.update(config.get("smoke") or {})
    smoke.pop("smoke", None)
    return smoke


def build_parser() -> argparse.ArgumentParser:
    """The frozen runner CLI."""
    parser = argparse.ArgumentParser(prog="experiments.tkde.rq2", description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument(
        "--data-root",
        type=Path,
        default=None,
        help="Directory holding corpora/ ($ISALHG_DATA_ROOT on Picasso).",
    )
    parser.add_argument("--shard", default=None, help="i/N: run shard i of N")
    parser.add_argument(
        "--kinds",
        default=None,
        help=(
            "Comma-separated unit kinds to run (exact0, census, bipartite, oracle, "
            "hypercot). The census units are the only ones that need the shared "
            "matrices job, so they are submitted separately under "
            "--dependency=afterok while the rest start immediately."
        ),
    )
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--count", action="store_true", help="print the shard count and exit")
    parser.add_argument("--list-units", action="store_true")
    parser.add_argument(
        "--start-cutoff-epoch",
        type=float,
        default=None,
        help="Unix time after which no further unit is started; the first is exempt.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    from experiments.tkde.rq1 import parse_shard

    args = build_parser().parse_args(argv)
    config = load_yaml(args.config)
    if args.smoke:
        config = smoke_config(config)

    kinds = [part for part in (args.kinds or "").split(",") if part] or None
    units = enumerate_units(config, kinds)
    if args.count:
        # With --kinds the shard count is the filtered unit count: the two
        # submissions are separate arrays and must not share a shard numbering.
        print(len(units) if kinds else int(config.get("n_shards", len(units))))
        return 0
    if args.list_units:
        for unit in units:
            print(unit.unit_id)
        return 0

    results_root = Path(args.out) if args.out else corpora_io.results_root()
    paths = RunPaths(root=results_root, rq=RQ_FOLDER, experiment=EXPERIMENT)
    paths.ensure()

    shard, n_shards = parse_shard(args.shard, len(units))
    mine = units[shard::n_shards]
    logger.info("RQ2: shard %d/%d -> %d of %d units", shard, n_shards, len(mine), len(units))

    written: dict[str, int] = {}
    attempted = 0
    for unit in mine:
        if unit_is_done(paths, unit):
            logger.info("skip %s (rows present)", unit.unit_id)
            continue
        if (
            args.start_cutoff_epoch is not None
            and attempted > 0
            and time.time() >= args.start_cutoff_epoch
        ):
            logger.info("DEFERRED: unit %s (past the start cutoff)", unit.unit_id)
            continue
        attempted += 1
        started = time.monotonic()
        counts = run_unit(unit, config, paths, args.data_root)
        logger.info("unit %s done in %.1f s: %s", unit.unit_id, time.monotonic() - started, counts)
        for table, count in counts.items():
            written[table] = written.get(table, 0) + count

    record = {
        "rq": RQ_INDEX,
        "experiment": EXPERIMENT,
        "config_path": str(args.config),
        "config": dict(config),
        "shard": f"{shard}/{n_shards}",
        "kinds": kinds,
        "smoke": bool(args.smoke),
        "results_root": str(results_root),
        "data_root": str(args.data_root) if args.data_root else None,
        "seeds": seeds(RQ_INDEX),
        "units": [unit.unit_id for unit in mine],
    }
    extra = {"shard": f"{shard}/{n_shards}", "rows_written": written}
    write_config(paths, record)
    write_manifest(paths, extra=extra)
    # The kinds tag keeps the two RQ2 arrays (the immediate one and the
    # matrices-dependent census one) from overwriting each other's per-shard
    # provenance, since their shard numberings both start at 0.
    tag = "-".join(kinds) if kinds else "all"
    shard_paths = RunPaths(
        root=results_root, rq=RQ_FOLDER, experiment=f"{EXPERIMENT}/_shards/{tag}-{shard:03d}"
    )
    write_config(shard_paths, record)
    write_manifest(shard_paths, extra=extra)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
