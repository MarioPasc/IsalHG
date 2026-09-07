"""RQ7 runner -- the operating envelope.

Implements ``DESIGN.md`` §8: the parametric sweep over
``m x k x |Sigma_E| x |Sigma_V| x density`` with 27 seeds per cell (plus the
fact-alphabet-only large-``m`` extension), the yield of the real collections by
size bucket, and the ``N``-scaling of the full ``N x N`` matrix on ``wd50k66``.

Two notes on what is persisted:

* **``rows_yield`` is produced by the analyzer, not here.** Its schema is one
  row per ``(collection, bucket, arm)`` carrying a median and a p90 over the
  whole collection, and a shard that sees a slice of the members cannot compute
  either. The runner writes ``rows_yield_members`` (one row per member and arm:
  the bucket, the seconds, the censoring flag) and
  :mod:`experiments.tkde.analyze_rq7` reduces them.
* **The two ``N``-scaling columns measure two different things, on purpose.**
  ``secs_canon_total`` is the summed per-member canonicalization cost -- the
  ``N`` half of H7c's "``N`` canonicalizations plus ``N^2`` string comparisons"
  -- measured by calling the arm's own ``fingerprint``; ``secs_pairs_total`` is
  the wall-clock of the whole ``build_matrix`` call with the cache disabled,
  which is the number a user actually waits for. The second is not the first
  subtracted from anything, and the rows say so.

Timing is a reported quantity here, so every job that runs this module pins
``--constraint=sd`` and exports ``TKDE_THREADS=1``.
"""

from __future__ import annotations

import argparse
import logging
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
from experiments.tkde.rq1 import (
    aut_bucket,
    block_slice,
    corpora_root,
    deploy_stamps,
    member_word,
    parse_shard,
    run_tag,
    table_file,
    word_tokens,
)

logger = logging.getLogger(__name__)

RQ_INDEX = 7
RQ_FOLDER = "RQ7_envelope"
EXPERIMENT = "envelope"

POINTER_ARM = "isalhg_levenshtein"
#: The envelope is swept over the four-cell nauty ablation of D-ART4: ``w*_c``
#: with no nauty at all, ``w*_c`` with the automorphism oracle, the ordered walk
#: (order only) and the greedy walk keyed by rank (both).
DEFAULT_SWEEP_ARMS: tuple[str, ...] = (
    POINTER_ARM,
    "wstar_orbit",
    "isal_ow_struct",
    "wstar_rank",
    "fact_rank",
    "nauty_cert",
)
DEFAULT_YIELD_ARMS: tuple[str, ...] = (POINTER_ARM, "isal_ow_struct", "fact_rank")
FACT_ALPHABET_ARMS: tuple[str, ...] = ("fact_rank", "nauty_cert")

BUCKETS: tuple[tuple[str, int, int], ...] = (
    ("<=8", 0, 8),
    ("9-12", 9, 12),
    ("13-16", 13, 16),
    ("17-20", 17, 20),
    ("21-24", 21, 24),
    (">24", 25, 10**9),
)

UNIVERSAL_COLUMNS: tuple[str, ...] = ("rq", "experiment", "git_sha", "host_cpu")

COLUMNS_SWEEP: tuple[str, ...] = (
    *UNIVERSAL_COLUMNS,
    "collection",
    "cell",
    "m",
    "k",
    "sigma_e",
    "sigma_v",
    "density",
    "seed",
    "n",
    "aut_bucket",
    "arm",
    "secs",
    "censored",
    "tokens_or_bytes",
    "error",
)
COLUMNS_YIELD_MEMBERS: tuple[str, ...] = (
    *UNIVERSAL_COLUMNS,
    "collection",
    "seed",
    "member_id",
    "n",
    "m",
    "k",
    "bucket",
    "arm",
    "secs",
    "censored",
)
COLUMNS_NSCALING: tuple[str, ...] = (
    *UNIVERSAL_COLUMNS,
    "collection",
    "seed",
    "N",
    "arm",
    "rep",
    "secs_canon_total",
    "secs_pairs_total",
    "censored",
    "skipped",
    "error",
)


class Rq7Error(TkdeConfigError):
    """The RQ7 runner was asked for something the design does not define."""


def bucket_of(n: int) -> str:
    """Size bucket of a constant count (``DESIGN.md`` §8's six buckets)."""
    for name, low, high in BUCKETS:
        if low <= n <= high:
            return name
    return ">24"


# ---------------------------------------------------------------------------
# Units
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Unit:
    """One independently computable, independently resumable piece of work."""

    kind: str
    label: str
    block: int = 0
    n_blocks: int = 1
    extra: Mapping[str, Any] = field(default_factory=dict)

    @property
    def unit_id(self) -> str:
        """Stable id; part of every row file name this unit writes."""
        return f"{self.kind}-{self.label}-{self.block:03d}of{self.n_blocks:03d}"

    @property
    def tables(self) -> tuple[str, ...]:
        """Row tables this unit is responsible for."""
        return {"sweep": ("sweep",), "yield": ("yield_members",), "nscaling": ("nscaling",)}[
            self.kind
        ]


def _cell_label(cell: Mapping[str, Any]) -> str:
    return (
        f"m{cell['m']}k{cell['k']}e{cell['n_edge_labels']}"
        f"v{cell['n_vertex_labels']}{cell['density']}"
    )


def sweep_cells(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    """The feasible cells of the RQ7 grid, in the generator's order.

    An infeasible cell is not a unit: at ``k = 2`` the sparse density asks for
    more constants than ``m`` facts of arity at most 2 can connect, so the cell
    is structurally impossible rather than merely expensive (measured by the
    corpus generator, 2026-09-05).
    """
    from isalhg.datasets.kb.envelope_sweep import grid

    include = bool(config.get("include_extension", True))
    cells = [cell for cell in grid(include_extension=include) if cell["feasible"]]
    limit = config.get("cell_limit")
    return cells[: int(limit)] if limit else cells


def enumerate_units(config: Mapping[str, Any]) -> list[Unit]:
    """Every unit of this configuration, in a deterministic order."""
    units: list[Unit] = []
    for cell in sweep_cells(config):
        units.append(Unit("sweep", _cell_label(cell), extra={"cell": dict(cell)}))
    for collection in config.get("yield_collections") or []:
        total = max(1, int((config.get("yield_blocks") or {}).get(collection, 1)))
        units.extend(Unit("yield", collection, block=b, n_blocks=total) for b in range(total))
    for arm in config.get("nscaling_arms") or []:
        for size in config.get("nscaling_N") or []:
            units.append(Unit("nscaling", f"{arm}-N{size}", extra={"arm": arm, "N": int(size)}))
    return units


# ---------------------------------------------------------------------------
# Measurements
# ---------------------------------------------------------------------------


def run_sweep(unit: Unit, ctx: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """One grid cell: 27 seeded instances, three arms, wall-clock and tokens."""
    from isalhg.datasets.kb.envelope_sweep import random_kb

    cell = dict(unit.extra["cell"])
    config = ctx["config"]
    budget = float(config.get("pointer_budget_s", 60.0))
    arms = (
        list(FACT_ALPHABET_ARMS)
        if cell.get("fact_alphabet_only")
        else list(config.get("sweep_arms") or DEFAULT_SWEEP_ARMS)
    )
    seed_list = seeds(RQ_INDEX, int(config.get("sweep_seeds", 27)))

    rows: list[dict[str, Any]] = []
    for seed in seed_list:
        record = random_kb(
            cell["m"],
            cell["k"],
            cell["n_edge_labels"],
            cell["n_vertex_labels"],
            cell["density"],
            seed,
        )
        H = record.to_hypergraph()
        # One autgrp call per instance, shared by every arm's row: symmetry is
        # what censors the tie-complete engines, so the envelope is tabulated
        # over (m, k, |Aut|) rather than over (m, k) alone.
        symmetry = aut_bucket(H)
        for arm in arms:
            # The pointer arm is encoded at the CELL's k, not at the instance's
            # required_k: the envelope statement is about the alphabet the user
            # declares, not about the arity a sample happened to realise.
            word, secs, censored = member_word(arm, H, None, k=int(cell["k"]), budget=budget)
            rows.append(
                {
                    **ctx["stamp"],
                    "collection": "envelope_sweep",
                    "cell": unit.label,
                    "m": cell["m"],
                    "k": cell["k"],
                    "sigma_e": cell["n_edge_labels"],
                    "sigma_v": cell["n_vertex_labels"],
                    "density": cell["density"],
                    "seed": seed,
                    "n": record.n,
                    "aut_bucket": symmetry,
                    "arm": arm,
                    "secs": round(secs, 6),
                    "censored": int(censored),
                    "tokens_or_bytes": word_tokens(arm, word),
                    "error": "" if word is not None or censored else "failed",
                }
            )
    return {"sweep": rows}


def run_yield(unit: Unit, ctx: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Per-member canonicalization time of one real collection (the yield inputs)."""
    from isalhg.core.canonical import required_k

    collection = ctx["collection"]
    graphs = ctx["graphs"]
    roles = ctx["roles"]
    config = ctx["config"]
    budget = float(config.get("pointer_budget_s", 60.0))
    fact_only = set(config.get("yield_fact_alphabet_only") or ())
    arms = (
        ["fact_rank"]
        if unit.label in fact_only
        else list(config.get("yield_arms") or DEFAULT_YIELD_ARMS)
    )
    master = seeds(RQ_INDEX)[0]

    rows: list[dict[str, Any]] = []
    for index in block_slice(len(collection.records), unit.block, unit.n_blocks):
        record = collection.records[index]
        H = graphs[index]
        k = required_k(H)
        for arm in arms:
            word, secs, censored = member_word(arm, H, roles[index], k=k, budget=budget)
            rows.append(
                {
                    **ctx["stamp"],
                    "collection": collection.name,
                    "seed": master,
                    "member_id": record.kb_id,
                    "n": record.n,
                    "m": record.m,
                    "k": k,
                    "bucket": bucket_of(record.n),
                    "arm": arm,
                    "secs": round(secs, 6),
                    "censored": int(censored or word is None),
                }
            )
    return {"yield_members": rows}


def _matrix_timing(items: Sequence[Any], ids: Sequence[str], arm: str) -> tuple[float, float]:
    """``(canonicalization seconds, whole-matrix seconds)`` for one arm at one ``N``."""
    from isalhg.metric_space.registry import get_distance
    from isalhg.metric_space.toolkit.matrix import build_matrix

    canon = 0.0
    if arm in ("fact_rank", "fact_rank_roles"):
        from isalhg.metric_space.distances.fact_levenshtein import fact_word

        start = time.perf_counter()
        for H in items:
            fact_word(H)
        canon = time.perf_counter() - start
    else:
        distance = get_distance(arm)
        start = time.perf_counter()
        probe = distance.fingerprint(items[0]) if items else None
        if probe is not None:
            for H in items:
                distance.fingerprint(H)
            canon = time.perf_counter() - start
        else:
            canon = float("nan")

    start = time.perf_counter()
    build_matrix(items, arm, member_ids=list(ids), cache_dir=None, n_jobs=1)
    return canon, time.perf_counter() - start


def run_nscaling(unit: Unit, ctx: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """``N``-scaling of one arm at one ``N``, three repetitions under a budget."""
    collection = ctx["collection"]
    graphs = ctx["graphs"]
    config = ctx["config"]
    arm = str(unit.extra["arm"])
    size = min(int(unit.extra["N"]), len(collection.records))
    reps = int(config.get("nscaling_reps", 3))
    budget = float(config.get("nscaling_budget_s", 3600.0))
    master = seeds(RQ_INDEX)[0]

    items = graphs[:size]
    ids = [record.kb_id for record in collection.records[:size]]

    rows: list[dict[str, Any]] = []
    censored_once = False
    for rep in range(1, reps + 1):
        if censored_once:
            # An arm that blew the budget once at this N is recorded as skipped
            # for the remaining repetitions rather than run again: the design
            # asks for the arms that finish under one hour, and re-measuring a
            # known overrun buys nothing but queue time.
            rows.append(_nscaling_row(ctx, collection.name, master, size, arm, rep, skipped=True))
            continue
        result = run_with_budget_detail(_matrix_timing, (items, ids, arm), budget)
        if result.censored:
            censored_once = True
            rows.append(
                _nscaling_row(
                    ctx, collection.name, master, size, arm, rep, censored=True, secs_pairs=budget
                )
            )
            continue
        if result.error is not None:
            rows.append(
                _nscaling_row(ctx, collection.name, master, size, arm, rep, error=result.error)
            )
            continue
        canon, pairs = result.value
        rows.append(
            _nscaling_row(
                ctx, collection.name, master, size, arm, rep, secs_canon=canon, secs_pairs=pairs
            )
        )
    return {"nscaling": rows}


def _nscaling_row(
    ctx: dict[str, Any],
    collection: str,
    seed: int,
    size: int,
    arm: str,
    rep: int,
    *,
    secs_canon: float | None = None,
    secs_pairs: float | None = None,
    censored: bool = False,
    skipped: bool = False,
    error: str = "",
) -> dict[str, Any]:
    return {
        **ctx["stamp"],
        "collection": collection,
        "seed": seed,
        "N": size,
        "arm": arm,
        "rep": rep,
        "secs_canon_total": "" if secs_canon is None else round(float(secs_canon), 6),
        "secs_pairs_total": "" if secs_pairs is None else round(float(secs_pairs), 6),
        "censored": int(censored),
        "skipped": int(skipped),
        "error": error,
    }


RUNNERS = {"sweep": run_sweep, "yield": run_yield, "nscaling": run_nscaling}
COLUMNS = {
    "sweep": COLUMNS_SWEEP,
    "yield_members": COLUMNS_YIELD_MEMBERS,
    "nscaling": COLUMNS_NSCALING,
}


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def _stamp() -> dict[str, Any]:
    # Private helpers of this package's own io module: the manifest's provenance
    # fields must be identical to the ones stamped into every row.
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
    context: dict[str, Any] = {"config": config, "stamp": _stamp()}
    name = ""
    if unit.kind == "yield":
        name = unit.label
    elif unit.kind == "nscaling":
        name = str(config.get("nscaling_collection", "wd50k66"))
    if not name:
        return context

    root = corpora_root(results_root, name, data_root)
    if root is None:
        raise Rq7Error(
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
    context["collection"] = collection
    context["graphs"] = corpora_io.hypergraphs(collection)
    context["roles"] = corpora_io.roles_maps(collection)
    return context


def unit_is_done(paths: RunPaths, unit: Unit, tag: str) -> bool:
    """True when every row file this unit owns exists and parses as CSV."""
    import csv

    for table in unit.tables:
        target = paths.dir / f"rows_{table_file(tag, table, unit.unit_id)}.csv"
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
    tag: str | None = None,
) -> dict[str, int]:
    """Compute one unit and write its row files."""
    stamp = tag or run_tag(config)
    context = _unit_context(unit, config, Path(paths.root), data_root)
    tables = RUNNERS[unit.kind](unit, context)
    counts: dict[str, int] = {}
    for table, rows in tables.items():
        write_rows(paths, table_file(stamp, table, unit.unit_id), rows, columns=COLUMNS[table])
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
    parser = argparse.ArgumentParser(prog="experiments.tkde.rq7", description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument(
        "--data-root",
        type=Path,
        default=None,
        help="Directory holding corpora/ ($ISALHG_DATA_ROOT on Picasso).",
    )
    parser.add_argument("--shard", default=None, help="i/N: run shard i of N")
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

    args = build_parser().parse_args(argv)
    config = load_yaml(args.config)
    if args.smoke:
        config = smoke_config(config)

    units = enumerate_units(config)
    if args.count:
        print(int(config.get("n_shards", len(units))))
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
    tag = run_tag(config)
    logger.info(
        "RQ7: shard %d/%d -> %d of %d units (run tag %s)",
        shard,
        n_shards,
        len(mine),
        len(units),
        tag,
    )

    written: dict[str, int] = {}
    attempted = 0
    for unit in mine:
        if unit_is_done(paths, unit, tag):
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
        counts = run_unit(unit, config, paths, args.data_root, tag)
        logger.info("unit %s done in %.1f s: %s", unit.unit_id, time.monotonic() - started, counts)
        for table, count in counts.items():
            written[table] = written.get(table, 0) + count

    record = {
        "rq": RQ_INDEX,
        "experiment": EXPERIMENT,
        "config_path": str(args.config),
        "config": dict(config),
        "run_tag": tag,
        "shard": f"{shard}/{n_shards}",
        "smoke": bool(args.smoke),
        "results_root": str(results_root),
        "data_root": str(args.data_root) if args.data_root else None,
        "seeds": seeds(RQ_INDEX),
        "units": [unit.unit_id for unit in mine],
    }
    extra = {
        "shard": f"{shard}/{n_shards}",
        "run_tag": tag,
        "rows_written": written,
        **deploy_stamps(),
    }
    write_config(paths, record)
    write_manifest(paths, extra=extra)
    shard_paths = RunPaths(
        root=results_root, rq=RQ_FOLDER, experiment=f"{EXPERIMENT}/_shards/{shard:03d}"
    )
    write_config(shard_paths, record)
    write_manifest(shard_paths, extra=extra)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
