"""The 600 s re-run of the 60 s censored tail -- characterisation, never a row.

D-ART5 decision 2 keeps the published budget at 60 s and defines the 600 s pass
as "a re-run *of the censored tail*, i.e. characterisation by definition, never
a row". This runner is that pass, and nothing else: it takes the members a 60 s
run censored, re-runs each one through the *same* forked-child budget model at a
larger budget, and writes its rows under a results folder that no RQ analyzer
globs (:data:`RQ_FOLDER`), every row carrying ``kind="tail_characterisation"``.

What it answers is pre-stated in ``T-KBe`` §"Pre-stated expectation for the
600 s re-run" and scored by :mod:`experiments.tkde.analyze_tail600`:

* ``wstar_orbit``'s tail sits just above a dense near-boundary population, so a
  material fraction of it should complete;
* ``wstar_rank``'s tail has no near-boundary mass at all, so most of it should
  stay censored -- its members are arity-10 displacement enumerations,
  exponential in the arity, rather than slow instances of a feasible search.

**Where the censored ids come from.** Two sources, because they are not the same
measurement and only one of them can answer the pre-stated expectation.

``"m3"`` (the default) reads the RQ1 M3 census -- ``rows_m3__*.csv`` under
``<results>/RQ1_*/<census_experiment>/``. This is the source T-KBe's 77 / 53 and
D-ART5's "the 77 orbit-censored members" were counted from, it carries
``n``/``m``/``k``/``aut_bucket`` per member so the tail row is directly paired
with its 60 s row, and it is the only source that carries ``wstar_rank`` at all.

``"sidecar"`` reads the matrix-build sidecars
``<results>/matrices/<collection>/<arm>.censored.json``. Those record a
*different* population -- the members a distance-matrix build dropped -- and
exist for ``wstar_orbit`` only. Kept because it is a legitimate second tail and
costs one function to support, but it is not the pre-stated expectation's
population and the analyzer says so.
"""

from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import json
import logging
import time
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from experiments.tkde import corpora as corpora_io
from experiments.tkde.config import TkdeConfigError, load_yaml
from experiments.tkde.io import RunPaths, write_config, write_manifest, write_rows, write_summary

logger = logging.getLogger(__name__)

#: Results folder. Deliberately not ``RQ<n>_*``: every analyzer and merge tool of
#: the campaign globs ``RQ*``/``RQ1_*``, so a name outside that namespace is what
#: makes "never a row" a property of the filesystem rather than of a convention.
RQ_FOLDER = "TAIL600_characterisation"
EXPERIMENT = "tail_600s"
SMOKE_COMPONENT = "_smoke"

#: Stamped on every row. A row that is copied out of :data:`RQ_FOLDER` still says
#: what it is.
KIND = "tail_characterisation"

#: The published budget the tail was censored at (D-ART5 decision 2).
BASELINE_BUDGET_S = 60.0
DEFAULT_BUDGET_S = 600.0

#: The two arms the pre-stated expectation is about. ``isalhg_levenshtein`` (the
#: unpruned engine, 356 censored) is measurable by naming it in ``--arms``, but
#: it is not the published representation and it costs about 59 h of budget
#: against the default pair's 22 h, so it is not a default.
DEFAULT_ARMS: tuple[str, ...] = ("wstar_orbit", "wstar_rank")

#: Where the RQ1 census is read from, relative to the results root.
CENSUS_GLOB = "RQ1_*/{experiment}/rows_m3__*.csv"
DEFAULT_CENSUS_EXPERIMENT = "merged"

#: Keys describing how the work is distributed rather than what is measured.
OPERATIONAL_KEYS: frozenset[str] = frozenset({"n_shards", "smoke", "max_items"})
RUN_TAG_LENGTH = 8

COLUMNS_TAIL: tuple[str, ...] = (
    "rq",
    "experiment",
    "git_sha",
    "host_cpu",
    "kind",
    "source",
    "collection",
    "member_id",
    "n",
    "m",
    "k",
    "aut_bucket",
    "arm",
    "budget_s",
    "baseline_budget_s",
    "baseline_secs",
    "tokens",
    "secs",
    "censored",
    "error",
)


class Tail600Error(TkdeConfigError):
    """The tail runner was asked for something it does not define."""


class Tail600SourceError(Tail600Error):
    """A censoring source is present but does not carry the census it must."""


@dataclass(frozen=True)
class TailMember:
    """One ``(member, arm)`` the 60 s run censored.

    Attributes
    ----------
    collection : str
        Frozen collection name.
    member_id : str
        ``kb_id`` inside that collection.
    arm : str
        The arm whose 60 s call was censored.
    n : int
        Constants, ``-1`` when the source does not carry it.
    m : int
        Facts, ``-1`` when the source does not carry it.
    k : int
        Pointer count the 60 s call used, ``-1`` when the source does not carry
        it (then it is recomputed from the member).
    aut_bucket : str
        ``|Aut|`` stratum from the 60 s run; ``""`` when the source does not
        carry it.
    baseline_secs : float
        Wall-clock the 60 s call recorded -- the budget itself on a censored
        call. ``-1.0`` when unknown.
    """

    collection: str
    member_id: str
    arm: str
    n: int = -1
    m: int = -1
    k: int = -1
    aut_bucket: str = ""
    baseline_secs: float = -1.0

    @property
    def key(self) -> tuple[str, str, str]:
        """Deduplication key: ``(collection, member_id, arm)``."""
        return (self.collection, self.member_id, self.arm)


# ---------------------------------------------------------------------------
# Source 1 -- the RQ1 M3 census
# ---------------------------------------------------------------------------


def census_paths(root: Path | str, experiment: str = DEFAULT_CENSUS_EXPERIMENT) -> list[Path]:
    """The RQ1 M3 row files the census is read from, sorted.

    Parameters
    ----------
    root : Path or str
        Results root.
    experiment : str, optional
        RQ1 experiment folder. Default ``"merged"`` -- the per-arm merge, which
        is the only tree carrying every arm at its adopted source (T-KBe: taking
        ``wstar_orbit`` from ``addressing`` rather than ``addressing_cpp`` reads
        406 censored instead of 77).

    Returns
    -------
    list[Path]
        Matching files; empty when the census is not deployed here.
    """
    pattern = str(Path(root) / CENSUS_GLOB.format(experiment=experiment))
    return sorted(Path(p) for p in glob.glob(pattern))


def read_m3_census(
    root: Path | str,
    arms: Sequence[str],
    *,
    experiment: str = DEFAULT_CENSUS_EXPERIMENT,
) -> list[TailMember]:
    """Censored ``(member, arm)`` entries of the RQ1 M3 census.

    Parameters
    ----------
    root : Path or str
        Results root.
    arms : Sequence[str]
        Arms to collect. An arm absent from the census yields no entries; the
        caller reports which arms are measurable.
    experiment : str, optional
        RQ1 experiment folder.

    Returns
    -------
    list[TailMember]
        One entry per censored ``(collection, member_id, arm)``, deduplicated
        across shard files, in :func:`worklist` order.

    Raises
    ------
    Tail600SourceError
        If no census file is present, or a file lacks the columns the census is
        defined by.
    """
    paths = census_paths(root, experiment)
    if not paths:
        raise Tail600SourceError(
            f"no RQ1 M3 census under {Path(root) / CENSUS_GLOB.format(experiment=experiment)}; "
            "deploy the merged RQ1 rows, or run with --source sidecar"
        )
    wanted = set(arms)
    required = {"collection", "member_id", "arm", "censored"}
    found: dict[tuple[str, str, str], TailMember] = {}
    for path in paths:
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            missing = required - set(reader.fieldnames or ())
            if missing:
                raise Tail600SourceError(
                    f"{path} is not an M3 census: missing columns {sorted(missing)}"
                )
            for row in reader:
                if row["arm"] not in wanted or row["censored"] != "1":
                    continue
                member = TailMember(
                    collection=row["collection"],
                    member_id=row["member_id"],
                    arm=row["arm"],
                    n=_as_int(row.get("n")),
                    m=_as_int(row.get("m")),
                    k=_as_int(row.get("k")),
                    aut_bucket=str(row.get("aut_bucket") or ""),
                    baseline_secs=_as_float(row.get("secs")),
                )
                found.setdefault(member.key, member)
    return worklist(found.values())


# ---------------------------------------------------------------------------
# Source 2 -- the matrix-build censoring sidecars
# ---------------------------------------------------------------------------


def read_sidecar_census(
    root: Path | str,
    arms: Sequence[str],
    collections: Sequence[str] | None = None,
) -> tuple[list[TailMember], dict[str, list[str]]]:
    """Censored entries of the matrix-build sidecars, and which arms carry one.

    Parameters
    ----------
    root : Path or str
        Results root; sidecars live under ``<root>/matrices/<collection>/``.
    arms : Sequence[str]
        Arms to look for.
    collections : Sequence[str] or None, optional
        Collections to scan. Default: every directory under ``<root>/matrices``
        that is not a build or smoke component.

    Returns
    -------
    tuple
        ``(members, present)`` where ``present`` maps each arm to the
        collections whose sidecar was found -- an arm mapping to ``[]`` has no
        sidecar anywhere and is *not measurable from this source*.

    Raises
    ------
    Tail600SourceError
        If a sidecar exists and parses as JSON but does not carry a list of
        string ``censored_ids``. A file that is present and wrong is a defect;
        a file that is absent is data.
    """
    from experiments.tkde.matrices import censoring_path

    base = Path(root) / "matrices"
    names = list(collections) if collections is not None else _matrix_collections(base)
    present: dict[str, list[str]] = {arm: [] for arm in arms}
    found: dict[tuple[str, str, str], TailMember] = {}
    for name in names:
        for arm in arms:
            path = censoring_path(base / name, arm)
            if not path.is_file():
                continue
            ids = _sidecar_ids(path)
            present[arm].append(name)
            for member_id in ids:
                member = TailMember(collection=name, member_id=member_id, arm=arm)
                found.setdefault(member.key, member)
    return worklist(found.values()), present


def _matrix_collections(base: Path) -> list[str]:
    """Collection directories under ``matrices/``, excluding build/smoke components."""
    if not base.is_dir():
        return []
    return sorted(p.name for p in base.iterdir() if p.is_dir() and not p.name.startswith("_"))


def _sidecar_ids(path: Path) -> list[str]:
    """Validated ``censored_ids`` of one sidecar.

    Raises
    ------
    Tail600SourceError
        If the file is unreadable, is not JSON, is not a mapping, or its
        ``censored_ids`` is absent or not a list of strings.
    """
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Tail600SourceError(f"{path} is present but unreadable: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise Tail600SourceError(f"{path} must hold a mapping, got {type(payload).__name__}")
    ids = payload.get("censored_ids")
    if not isinstance(ids, list) or any(not isinstance(i, str) for i in ids):
        raise Tail600SourceError(f"{path} carries no list of string 'censored_ids'")
    return list(ids)


# ---------------------------------------------------------------------------
# Work list and sharding
# ---------------------------------------------------------------------------


def worklist(members: Iterable[TailMember]) -> list[TailMember]:
    """Deterministic order of the work: by collection, then arm, then member id.

    Grouping by collection first is not cosmetic: a shard loads each collection
    it touches once, and a stride shard over a collection-major list touches the
    same small number of collections every task.
    """
    return sorted(members, key=lambda member: member.key)


def shard_slice(items: Sequence[Any], shard: int, n_shards: int) -> list[Any]:
    """Stride slice ``items[shard::n_shards]``, the campaign's sharding rule.

    A stride rather than a block, matching RQ7: the work list is collection- and
    arm-major, so a block shard would hand one task every member of one arm and
    another none, while a stride spreads both evenly.

    Parameters
    ----------
    items : Sequence
        The work list.
    shard : int
        ``0 <= shard < n_shards``.
    n_shards : int
        Number of shards.

    Returns
    -------
    list
        This shard's items.

    Raises
    ------
    Tail600Error
        If the shard index is out of range.
    """
    if n_shards < 1 or not 0 <= shard < n_shards:
        raise Tail600Error(f"shard {shard}/{n_shards} is out of range")
    return list(items[shard::n_shards])


def parse_shard(spec: str | None, n_items: int) -> tuple[int, int]:
    """Parse ``i/N``; the default is the single shard ``0/1``.

    Raises
    ------
    Tail600Error
        If ``spec`` is not ``i/N`` or the index is out of range.
    """
    if not spec:
        return 0, 1
    try:
        index, total = (int(part) for part in spec.split("/", 1))
    except ValueError as exc:
        raise Tail600Error(f"--shard must look like i/N, got {spec!r}") from exc
    if total < 1 or not 0 <= index < total:
        raise Tail600Error(f"--shard {spec!r} is out of range for {n_items} items")
    return index, total


# ---------------------------------------------------------------------------
# The measurement
# ---------------------------------------------------------------------------


def measure_member(member: TailMember, H: Any, budget: float) -> dict[str, Any]:
    """Re-run one censored ``(member, arm)`` at ``budget`` seconds.

    The only difference from the 60 s call is the budget: the same
    :func:`experiments.tkde.budget.engine_word`, the same engine per arm, the
    same forked child under the same fork-health canary. A tail row is
    comparable with its 60 s row precisely because nothing else moved.

    Parameters
    ----------
    member : TailMember
        The censored entry, carrying the ``k`` its 60 s call used when the
        source knows it.
    H : SparseHypergraph
        The member.
    budget : float
        Wall-clock budget in seconds.

    Returns
    -------
    dict
        ``{"secs", "censored", "tokens", "error", "k"}``.

    Raises
    ------
    Tail600Error
        If ``member.arm`` is not a budgeted engine arm.
    """
    from experiments.tkde.budget import engine_word
    from experiments.tkde.rq1 import BUDGETED_ARMS, word_tokens
    from isalhg.core.canonical import required_k

    engine = BUDGETED_ARMS.get(member.arm)
    if engine is None:
        raise Tail600Error(
            f"arm {member.arm!r} is not a budgeted engine arm; "
            f"the tail is defined only for {sorted(BUDGETED_ARMS)}"
        )
    k = member.k if member.k > 0 else required_k(H)
    result = engine_word(H, k, budget, engine=engine)
    return {
        "secs": round(result.secs, 6),
        "censored": int(result.censored),
        "tokens": word_tokens(member.arm, result.value),
        "error": result.error or "",
        "k": k,
    }


def measure_shard(
    members: Sequence[TailMember],
    *,
    budget: float,
    stamp: Mapping[str, Any],
    source: str,
    results_root: Path,
    data_root: Path | str | None = None,
    start_cutoff_epoch: float | None = None,
) -> list[dict[str, Any]]:
    """Rows for one shard's work, loading each collection at most once.

    Parameters
    ----------
    members : Sequence[TailMember]
        This shard's work, in :func:`worklist` order.
    budget : float
        Wall-clock budget per call.
    stamp : Mapping
        Universal columns (``rq``/``experiment``/``git_sha``/``host_cpu``).
    source : str
        ``"m3"`` or ``"sidecar"``; recorded on every row.
    results_root : Path
        Root used to find the frozen corpora when ``data_root`` does not hold
        them.
    data_root : Path or str or None, optional
        Directory holding ``corpora/``.
    start_cutoff_epoch : float or None, optional
        Unix time after which no further member is started; the first is exempt,
        so a shard always makes progress.

    Returns
    -------
    list[dict]
        One row per member, in input order.

    Raises
    ------
    Tail600Error
        If a collection cannot be found, or a member id is not in it.
    """
    rows: list[dict[str, Any]] = []
    for name, group in _by_collection(members):
        collection = _load_collection(name, results_root, data_root)
        index = {record.kb_id: record for record in collection.records}
        for member in group:
            if start_cutoff_epoch is not None and rows and time.time() >= start_cutoff_epoch:
                logger.info("DEFERRED: %s/%s (start cutoff reached)", name, member.member_id)
                continue
            record = index.get(member.member_id)
            if record is None:
                raise Tail600Error(f"{name}: no member {member.member_id!r} in the frozen corpus")
            outcome = measure_member(member, record.to_hypergraph(), budget)
            logger.info(
                "%s/%s %s: %.1fs censored=%d",
                name,
                member.member_id,
                member.arm,
                outcome["secs"],
                outcome["censored"],
            )
            rows.append(
                {
                    **stamp,
                    "kind": KIND,
                    "source": source,
                    "collection": name,
                    "member_id": member.member_id,
                    "n": record.n,
                    "m": record.m,
                    "k": outcome["k"],
                    "aut_bucket": member.aut_bucket,
                    "arm": member.arm,
                    "budget_s": budget,
                    "baseline_budget_s": BASELINE_BUDGET_S,
                    "baseline_secs": member.baseline_secs,
                    "tokens": outcome["tokens"],
                    "secs": outcome["secs"],
                    "censored": outcome["censored"],
                    "error": outcome["error"],
                }
            )
    return rows


def _by_collection(members: Sequence[TailMember]) -> Iterator[tuple[str, list[TailMember]]]:
    """Group a work list by collection, preserving order."""
    grouped: dict[str, list[TailMember]] = {}
    for member in members:
        grouped.setdefault(member.collection, []).append(member)
    yield from grouped.items()


def _load_collection(name: str, results_root: Path, data_root: Path | str | None) -> Any:
    from experiments.tkde.rq1 import corpora_root

    root = corpora_root(results_root, name, data_root)
    if root is None:
        raise Tail600Error(
            f"no frozen collection {name!r}: looked under --data-root {data_root}, "
            f"{results_root}/corpora, $ISALHG_RESULTS_ROOT and $ISALHG_DATA_ROOT"
        )
    return corpora_io.load_collection(name, root)


# ---------------------------------------------------------------------------
# Configuration and paths
# ---------------------------------------------------------------------------


def run_tag(config: Mapping[str, Any]) -> str:
    """Short hash of the parameters that decide what is measured.

    Same rule as RQ1: the shard count and the smoke overlay describe how the
    work is spread, not what it says, so re-sharding resumes rather than
    recomputes -- but a different budget or arm set is a different measurement
    and gets a different file name.
    """
    payload = {key: value for key, value in config.items() if key not in OPERATIONAL_KEYS}
    encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha1(encoded, usedforsecurity=False).hexdigest()[:RUN_TAG_LENGTH]


def table_file(tag: str, shard: int, n_shards: int) -> str:
    """The ``write_rows`` table name of one shard's row file."""
    return f"tail600__{tag}-{shard:03d}of{n_shards:03d}"


def smoke_config(config: dict[str, Any]) -> dict[str, Any]:
    """Shrink a configuration to the ``--smoke`` shape (seconds, not hours)."""
    smoke = dict(config)
    smoke.update(config.get("smoke") or {})
    smoke.pop("smoke", None)
    return smoke


def resolve_paths(results_root: Path, *, smoke: bool) -> RunPaths:
    """Where the rows go; a smoke run gets its own subtree.

    A smoke shares the shard-id namespace with the real run, so a smoke row file
    beside the real ones would make the real run skip that shard as already
    done.
    """
    experiment = f"{SMOKE_COMPONENT}/{EXPERIMENT}" if smoke else EXPERIMENT
    return RunPaths(root=results_root, rq=RQ_FOLDER, experiment=experiment)


def _stamp(experiment: str = EXPERIMENT) -> dict[str, Any]:
    from experiments.tkde.io import _cpu_model, _repo_provenance

    return {
        "rq": KIND,
        "experiment": experiment,
        "git_sha": _repo_provenance()["git_sha"],
        "host_cpu": _cpu_model(),
    }


def collect_work(
    config: Mapping[str, Any], results_root: Path
) -> tuple[list[TailMember], dict[str, Any]]:
    """The work list and a report of which arms the chosen source can measure.

    Parameters
    ----------
    config : Mapping
        Parsed configuration.
    results_root : Path
        Results root holding the census.

    Returns
    -------
    tuple
        ``(members, report)``; ``report`` names the source, the requested arms,
        the measurable ones and, for the sidecar source, the arms with no
        sidecar anywhere.

    Raises
    ------
    Tail600Error
        If ``source`` is not one of the two.
    """
    arms = tuple(config.get("arms") or DEFAULT_ARMS)
    source = str(config.get("source") or "m3")
    if source == "m3":
        experiment = str(config.get("census_experiment") or DEFAULT_CENSUS_EXPERIMENT)
        members = read_m3_census(results_root, arms, experiment=experiment)
        report: dict[str, Any] = {"source": source, "census_experiment": experiment}
    elif source == "sidecar":
        members, present = read_sidecar_census(results_root, arms)
        report = {"source": source, "sidecars_present": present}
    else:
        raise Tail600Error(f"unknown source {source!r}; expected 'm3' or 'sidecar'")

    measured = sorted({member.arm for member in members})
    report.update(
        {
            "arms_requested": list(arms),
            "arms_measurable": measured,
            "arms_unmeasurable": sorted(set(arms) - set(measured)),
            "n_members": len(members),
        }
    )
    for arm in report["arms_unmeasurable"]:
        logger.warning(
            "arm %r has no censored members in source %r; it is not measurable", arm, source
        )
    limit = config.get("max_items")
    if limit is not None:
        members = members[: int(limit)]
        report["n_members"] = len(members)
    return members, report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """The runner CLI."""
    parser = argparse.ArgumentParser(prog="experiments.tkde.tail600", description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument(
        "--data-root",
        type=Path,
        default=None,
        help="Directory holding corpora/ ($ISALHG_DATA_ROOT on Picasso).",
    )
    parser.add_argument(
        "--census-root",
        type=Path,
        default=None,
        help="Root holding the census (RQ1_*/ or matrices/); defaults to $ISALHG_RESULTS_ROOT.",
    )
    parser.add_argument("--shard", default=None, help="i/N: run shard i of N")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--count", action="store_true", help="print the shard count and exit")
    parser.add_argument("--list-work", action="store_true", help="print the work list and exit")
    parser.add_argument(
        "--start-cutoff-epoch",
        type=float,
        default=None,
        help="Unix time after which no further member is started; the first is exempt.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = build_parser().parse_args(argv)
    config = load_yaml(args.config)
    if args.smoke:
        config = smoke_config(config)

    if args.count:
        print(int(config.get("n_shards", 1)))
        return 0

    results_root = Path(args.out) if args.out else corpora_io.results_root()
    census_root = Path(args.census_root) if args.census_root else corpora_io.results_root()
    members, report = collect_work(config, census_root)

    if args.list_work:
        for member in members:
            print(f"{member.collection}\t{member.arm}\t{member.member_id}")
        return 0

    budget = float(config.get("budget_s", DEFAULT_BUDGET_S))
    shard, n_shards = parse_shard(args.shard, len(members))
    mine = shard_slice(members, shard, n_shards)
    tag = run_tag(config)
    paths = resolve_paths(results_root, smoke=bool(args.smoke))
    paths.ensure()

    logger.info(
        "tail600: source=%s budget=%.0fs shard %d/%d -> %d of %d (%s) tag=%s",
        report["source"],
        budget,
        shard,
        n_shards,
        len(mine),
        len(members),
        ", ".join(report["arms_measurable"]) or "nothing measurable",
        tag,
    )

    table = table_file(tag, shard, n_shards)
    target = paths.dir / f"rows_{table}.csv"
    if _rows_present(target):
        logger.info("skip shard %d/%d (rows present at %s)", shard, n_shards, target)
        return 0

    rows = measure_shard(
        mine,
        budget=budget,
        stamp=_stamp(),
        source=report["source"],
        results_root=results_root,
        data_root=args.data_root,
        start_cutoff_epoch=args.start_cutoff_epoch,
    )
    write_rows(paths, table, rows, columns=COLUMNS_TAIL)
    write_config(paths, {**config, "shard": shard, "n_shards": n_shards, "run_tag": tag})
    write_summary(
        paths,
        {
            "kind": KIND,
            "budget_s": budget,
            "baseline_budget_s": BASELINE_BUDGET_S,
            "shard": shard,
            "n_shards": n_shards,
            "n_rows": len(rows),
            "n_completed": sum(1 for row in rows if not row["censored"]),
            **report,
        },
    )
    write_manifest(paths, extra={"kind": KIND, "run_tag": tag, "shard": f"{shard}/{n_shards}"})
    logger.info("wrote %d rows to %s", len(rows), target)
    return 0


def _rows_present(target: Path) -> bool:
    """True when a shard's row file exists and its header parses."""
    if not target.is_file():
        return False
    try:
        with target.open(encoding="utf-8", newline="") as handle:
            next(csv.reader(handle))
    except (OSError, StopIteration, UnicodeDecodeError):
        return False
    return True


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return -1


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return -1.0


if __name__ == "__main__":  # pragma: no cover - entry point
    raise SystemExit(main())
