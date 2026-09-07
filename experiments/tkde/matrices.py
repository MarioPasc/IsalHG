"""Shared ``N x N`` distance-matrix precomputation for the TKDE campaign.

This is the *first* job of the wave and the input of three consumers: RQ2's
false-merge census, RQ4's anomaly screen and RQ5's clustering. All three index
the same matrices, so all three must see the same member order -- the order of
the frozen ``records.jsonl`` and nothing else. That order is the cache key's
order component (:func:`isalhg.metric_space.toolkit.matrix.member_order_sha1`),
so a consumer that reorders members silently misses the cache and recomputes
rather than reading someone else's matrix; the strict reader below turns that
silent miss into an error instead.

Unit of work = one ``(collection, arm)`` pair. Units are idempotent: a unit
whose ``.npy`` and manifest already validate is skipped, so a re-run after a
node loss costs only the units that did not finish.

Output layout under ``--out`` (the results root)::

    matrices/<collection>/<arm>.npy
    matrices/<collection>/<arm>.manifest.json
    matrices/_build_rq45/rows_matrices.csv, config.json, manifest.json

The matrices are a handful of large files (``wd50k66`` is 3,988 members, i.e.
63.6 MB of ``float32``), not the many-small-files pattern that mandates
``$LOCALSCRATCH`` staging, and consumers running on *other* nodes need them at
the shared path. The SLURM worker therefore writes here directly.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import resource
import sys
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any

from experiments.tkde import corpora
from experiments.tkde.config import TkdeConfigError, load_yaml, results_root
from experiments.tkde.io import RunPaths, write_config, write_manifest, write_rows
from isalhg.metric_space.toolkit.matrix import cache_paths, member_order_sha1

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray

logger = logging.getLogger(__name__)

RQ_DIR = "matrices"
BUILD_EXPERIMENT = "_build_rq45"

ROWS_MATRICES_COLUMNS: tuple[str, ...] = (
    "rq",
    "experiment",
    "collection",
    "seed",
    "arm",
    "secs",
    "censored",
    "n_members",
    "n_pairs",
    "peak_rss_mb",
    "cache_hit",
    "order_sha1",
    "matrix_path",
    "n_jobs",
)

#: The Isal instruction words that get an ``N x N`` matrix. ``wstar_orbit`` and
#: ``isalhg_levenshtein`` are deliberately absent: both compute ``w*_c``, whose
#: per-member cost is unbounded without the forked-child budget, and a budget is
#: a per-member notion that a whole-matrix build has nowhere to record. They are
#: measured per member in RQ1 and RQ7 instead.
ISAL_MATRIX_ARMS: tuple[str, ...] = (
    "isal_ow_struct",
    "isal_ow_rank",
    "isal_ow_rank0",
    "wstar_rank",
)

#: Arms per collection, frozen by the wave-3 brief. ``fact_rank_roles`` runs
#: only where roles exist (WD50K); ``wd50k100`` is RQ5's purity control and
#: needs only the arms its supplementary table reports.
DEFAULT_SPECS: dict[str, tuple[str, ...]] = {
    "wd50k66": (
        "fact_rank",
        "fact_rank_roles",
        *ISAL_MATRIX_ARMS,
        "nauty_cert",
        "nauty_cert_rows",
        "wl_l1",
        "netlsd",
        "hpd_jsd",
        "bipartite_ged_path",
        "bipartite_ged_assign",
        "size_l1",
        "degree_seq_l1",
    ),
    "ndc_classes": (
        "fact_rank",
        *ISAL_MATRIX_ARMS,
        "nauty_cert",
        "nauty_cert_rows",
        "wl_l1",
        "netlsd",
        "hpd_jsd",
        "bipartite_ged_path",
        "bipartite_ged_assign",
        "size_l1",
        "degree_seq_l1",
    ),
    "wd50k100": (
        "fact_rank",
        *ISAL_MATRIX_ARMS,
        "nauty_cert",
        "wl_l1",
        "size_l1",
        "degree_seq_l1",
    ),
}

#: A tiny configuration for ``--smoke``: two collections, the fast arms, a
#: handful of members. Must finish well inside five minutes.
SMOKE_SPECS: dict[str, tuple[str, ...]] = {
    "wd50k66": (
        "fact_rank",
        "fact_rank_roles",
        "isal_ow_struct",
        "nauty_cert",
        "wl_l1",
        "size_l1",
    ),
    "ndc_classes": ("fact_rank", "isal_ow_struct", "nauty_cert", "degree_seq_l1"),
}
SMOKE_MEMBERS = 40


class MatrixCacheMissingError(RuntimeError):
    """A consumer asked for a matrix the matrices job has not produced."""


# ---------------------------------------------------------------------------
# Cache addressing -- the contract RQ2 / RQ4 / RQ5 all read through
# ---------------------------------------------------------------------------


def collection_cache_dir(root: Path | str, collection: str, *, smoke: bool = False) -> Path:
    """Return the cache directory of one collection's matrices.

    Parameters
    ----------
    root : Path or str
        Results root.
    collection : str
        Frozen collection name.
    smoke : bool, optional
        Route under the smoke component. A smoke run builds matrices over a
        *subset* of the members under the real arm names; sharing a directory
        with the campaign's would let a consumer's cache lookup meet a matrix
        built from 40 members. The member-order SHA-1 would reject it, but a
        rejection that depends on a hash is a weaker guarantee than never
        writing the file next to the real one.

    Returns
    -------
    Path
        ``<root>/matrices/<collection>``, or ``<root>/matrices/_smoke/<collection>``.
    """
    base = Path(root) / RQ_DIR
    if smoke:
        base = base / SMOKE_COMPONENT
    return base / collection


def _read_matrix_at(cache_dir: Path, arm: str, member_ids: Sequence[str]) -> Any:
    """Validate a cached matrix in an explicit directory (see :func:`load_cached_matrix`)."""
    import numpy as np

    matrix_path, manifest_path = cache_paths(cache_dir, arm)
    if not matrix_path.exists() or not manifest_path.exists():
        raise MatrixCacheMissingError(f"no cached matrix for arm={arm!r} under {cache_dir}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("member_order_sha1") != member_order_sha1(member_ids):
        raise MatrixCacheMissingError(f"member order mismatch for arm={arm!r} under {cache_dir}")
    if int(manifest.get("n", -1)) != len(member_ids):
        raise MatrixCacheMissingError(f"size mismatch for arm={arm!r} under {cache_dir}")
    return np.load(matrix_path)


def load_cached_matrix(
    root: Path | str,
    collection: str,
    arm: str,
    member_ids: Sequence[str],
) -> NDArray[np.float32]:
    """Read one cached matrix, refusing to recompute.

    The consumers run on compute nodes under a wall-clock budget sized for
    reading, not for building; a silent fall-through to recomputation would
    turn a missing dependency into a time-out hours later. This raises
    instead, naming the unit that must be produced first.

    Parameters
    ----------
    root : Path or str
        Results root.
    collection : str
        Frozen collection name.
    arm : str
        Arm name, exactly as the matrices job requested it (aliases and
        canonical names cache separately).
    member_ids : Sequence[str]
        Expected member order; checked against the manifest's SHA-1.

    Returns
    -------
    numpy.ndarray
        ``(N, N)`` ``float32`` matrix.

    Raises
    ------
    MatrixCacheMissingError
        If the matrix, its manifest, or the member-order agreement is absent.
    """
    import numpy as np

    matrix_path, manifest_path = cache_paths(collection_cache_dir(root, collection), arm)
    if not matrix_path.exists() or not manifest_path.exists():
        raise MatrixCacheMissingError(
            f"no cached matrix for collection={collection!r} arm={arm!r} "
            f"under {matrix_path.parent}; "
            "run `python -m experiments.tkde.matrices` first"
        )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_sha = member_order_sha1(member_ids)
    if manifest.get("member_order_sha1") != expected_sha:
        raise MatrixCacheMissingError(
            f"member order mismatch for collection={collection!r} arm={arm!r}: "
            f"manifest {manifest.get('member_order_sha1')!r} != requested {expected_sha!r}. "
            "Every consumer must index the frozen records.jsonl order."
        )
    if int(manifest.get("n", -1)) != len(member_ids):
        raise MatrixCacheMissingError(
            f"size mismatch for collection={collection!r} arm={arm!r}: "
            f"manifest n={manifest.get('n')} != requested {len(member_ids)}"
        )

    matrix = np.load(matrix_path)
    if matrix.shape != (len(member_ids), len(member_ids)):
        raise MatrixCacheMissingError(
            f"shape mismatch for collection={collection!r} arm={arm!r}: {matrix.shape}"
        )
    return matrix


def cached_arms(root: Path | str, collection: str, member_ids: Sequence[str]) -> tuple[str, ...]:
    """Return the arms whose matrices are present and valid for ``collection``.

    Parameters
    ----------
    root : Path or str
        Results root.
    collection : str
        Frozen collection name.
    member_ids : Sequence[str]
        Expected member order.

    Returns
    -------
    tuple[str, ...]
        Arm names, sorted, whose cache validates.
    """
    directory = collection_cache_dir(root, collection)
    if not directory.is_dir():
        return ()
    found: list[str] = []
    for manifest_path in sorted(directory.glob("*.manifest.json")):
        arm = manifest_path.name[: -len(".manifest.json")]
        try:
            load_cached_matrix(root, collection, arm, member_ids)
        except (MatrixCacheMissingError, OSError, ValueError):
            continue
        found.append(arm)
    return tuple(found)


# ---------------------------------------------------------------------------
# Units
# ---------------------------------------------------------------------------


def build_specs(config: Mapping[str, Any], *, smoke: bool) -> dict[str, tuple[str, ...]]:
    """Return the ``collection -> arms`` mapping this run builds.

    Parameters
    ----------
    config : Mapping
        Parsed YAML; ``collections`` is a list of ``{name, arms}`` mappings.
    smoke : bool
        Use the tiny built-in configuration instead.

    Returns
    -------
    dict[str, tuple[str, ...]]
        Ordered mapping.
    """
    if smoke:
        return dict(SMOKE_SPECS)
    entries = config.get("collections")
    if not entries:
        return dict(DEFAULT_SPECS)
    specs: dict[str, tuple[str, ...]] = {}
    for entry in entries:
        name = entry.get("name")
        arms = entry.get("arms")
        if not name or not arms:
            raise TkdeConfigError(f"collections entry needs `name` and `arms`, got {entry!r}")
        specs[str(name)] = tuple(str(a) for a in arms)
    return specs


def enumerate_units(specs: Mapping[str, Sequence[str]]) -> list[tuple[str, str]]:
    """Return the deterministic ``(collection, arm)`` unit list.

    Parameters
    ----------
    specs : Mapping
        ``collection -> arms``.

    Returns
    -------
    list[tuple[str, str]]
        Units in declaration order.
    """
    return [(collection, arm) for collection, arms in specs.items() for arm in arms]


def shard_bounds(n_units: int, index: int, count: int) -> tuple[int, int]:
    """Split ``n_units`` evenly into ``count`` contiguous shards.

    An even split, never fixed blocks with a ragged tail: the short remainder
    task is exactly the sub-two-hour job the bundling rule exists to remove.

    Parameters
    ----------
    n_units : int
        Total units.
    index : int
        Shard index in ``[0, count)``.
    count : int
        Number of shards.

    Returns
    -------
    tuple[int, int]
        Half-open ``[lo, hi)``.

    Raises
    ------
    TkdeConfigError
        If ``count < 1`` or ``index`` is out of range.
    """
    if count < 1:
        raise TkdeConfigError(f"shard count must be >= 1, got {count}")
    if not 0 <= index < count:
        raise TkdeConfigError(f"shard index {index} out of range for {count} shards")
    quotient, remainder = divmod(n_units, count)
    lo = index * quotient + min(index, remainder)
    hi = lo + quotient + (1 if index < remainder else 0)
    return lo, hi


def parse_shard(spec: str) -> tuple[int, int]:
    """Parse a ``"i/N"`` shard specification.

    Parameters
    ----------
    spec : str
        ``"<index>/<count>"``.

    Returns
    -------
    tuple[int, int]
        ``(index, count)``.

    Raises
    ------
    TkdeConfigError
        If the specification is malformed.
    """
    parts = spec.split("/")
    if len(parts) != 2:
        raise TkdeConfigError(f"--shard expects 'i/N', got {spec!r}")
    try:
        index, count = int(parts[0]), int(parts[1])
    except ValueError as exc:
        raise TkdeConfigError(f"--shard expects integers, got {spec!r}") from exc
    return index, count


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------


def resolve_data_root(explicit: Path | str | None = None) -> Path | None:
    """Return the directory that holds ``corpora/``, or None for the default.

    The frozen collections do not live in the same place on both sides.
    Locally they sit under the results root, which is what
    ``experiments.tkde.corpora`` defaults to; on Picasso they are staged on
    FSCRATCH at ``$ISALHG_DATA_ROOT/corpora`` while the results root is on
    HOME, so the default resolves to a directory that does not exist. Rather
    than requiring every caller to know which side it is on, this prefers an
    explicit value, then ``$ISALHG_DATA_ROOT`` *if that is where the corpora
    actually are*, and otherwise falls through to the corpora module's own
    default.

    Parameters
    ----------
    explicit : Path or str or None, optional
        A ``--data-root`` value, or the config's ``data_root``.

    Returns
    -------
    Path or None
        The root to pass to ``corpora.load_collection``; None means "default".
    """
    if explicit is not None:
        return Path(explicit)
    env = os.environ.get("ISALHG_DATA_ROOT")
    if env and (Path(env) / "corpora").is_dir():
        return Path(env)
    return None


#: Path component that marks an artefact as produced by a smoke run. A smoke
#: task runs ONE real unit to prove the deployment, so its rows are addressed by
#: the same unit id the full run uses; written into the real folder they would
#: make the idempotent full run skip that unit and ship the smoke's output as
#: the campaign's. Everything a smoke writes therefore goes under this
#: component, and the analyzers refuse to read any path containing it.
SMOKE_COMPONENT = "_smoke"

#: The canonical checkout whose `src/**` the editable-install finder serves.
#: A private environment installed from another checkout overrides it with
#: ``$ISALHG_SRC_REPO`` (the same override ``rq1.deploy_stamps`` honours).
SRC_DEPLOY_STAMP = (
    Path(
        os.environ.get(
            "ISALHG_SRC_REPO",
            "/mnt/home/users/tic_163_uma/mpascual/fscratch/repos/IsalHG-tkde",
        )
    )
    / ".tkde_deploy"
)


def _read_stamp(path: Path) -> str | None:
    """Return a deploy stamp's contents on one line, or None."""
    try:
        return " ".join(path.read_text(encoding="utf-8").split())
    except OSError:
        return None


def deploy_stamps() -> dict[str, str | None]:
    """Return both provenance stamps for the manifest.

    On Picasso ``isalhg.*`` resolves through the PEP 660 editable finder of the
    shared ``IsalHG-tkde`` checkout, while ``experiments.*`` comes from this
    agent's own deployment. The two trees can be at different commits, so a
    single git SHA in the manifest would describe only half of what ran.

    Returns
    -------
    dict[str, str or None]
        ``src_deploy`` (the library half) and ``runner_deploy`` (this half),
        plus ``isalhg_path`` and ``isalhg_git_sha``, which name the tree that
        actually served the library even when no deploy stamp was written.
    """
    from experiments.tkde.rq1 import library_provenance

    runner = os.environ.get("REPO_DIR")
    return {
        "src_deploy": _read_stamp(SRC_DEPLOY_STAMP),
        "runner_deploy": _read_stamp(Path(runner) / ".tkde_deploy") if runner else None,
        **library_provenance(),
    }


def contains_smoke(path: Path | str) -> bool:
    """Return True when any component of ``path`` marks it as smoke output.

    Parameters
    ----------
    path : Path or str

    Returns
    -------
    bool
    """
    return SMOKE_COMPONENT in Path(path).parts


_DERIVED: dict[tuple[int, str], Any] = {}


def _derived(collection_obj: Any, key: str, factory: Any) -> Any:
    """Memoize one derived view of a collection for the life of the process."""
    cache_key = (id(collection_obj), key)
    if cache_key not in _DERIVED:
        _DERIVED[cache_key] = factory(collection_obj)
    return _DERIVED[cache_key]


def _peak_rss_mb() -> float:
    """Return peak RSS of this process and its reaped children, in MiB."""
    self_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    child_kb = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    return max(self_kb, child_kb) / 1024.0


def _load(
    collection: str,
    root: Path | str | None,
    *,
    smoke: bool,
    cache: dict[str, Any],
) -> Any:
    """Load (and memoize) one frozen collection, truncated under ``--smoke``."""
    if collection in cache:
        return cache[collection]
    loaded = corpora.load_collection(collection, root)
    if smoke:
        ids = corpora.member_ids(loaded)[:SMOKE_MEMBERS]
        loaded = corpora.subset(loaded, ids, name=loaded.name)
    cache[collection] = loaded
    return loaded


def run_unit(
    collection_obj: Any,
    collection: str,
    arm: str,
    *,
    out_root: Path,
    n_jobs: int,
    smoke: bool = False,
) -> dict[str, Any]:
    """Build (or confirm) one ``(collection, arm)`` matrix and return its row.

    Parameters
    ----------
    collection_obj : KBCollection
        The loaded collection.
    collection : str
        Its name (the cache subdirectory).
    arm : str
        Arm name, used verbatim as the cache key.
    out_root : Path
        Results root.
    n_jobs : int
        Worker processes for the pairwise path.

    Returns
    -------
    dict[str, Any]
        One ``rows_matrices`` row.
    """
    from isalhg.metric_space.toolkit.matrix import build_matrix

    ids = corpora.member_ids(collection_obj)
    # `corpora.hypergraphs` rebuilds the whole collection on every call, and a
    # collection is used by up to eleven arms in one process.
    items = _derived(collection_obj, "items", corpora.hypergraphs)
    roles = (
        _derived(collection_obj, "roles", corpora.roles_maps) if arm.endswith("_roles") else None
    )
    cache_dir = collection_cache_dir(out_root, collection, smoke=smoke)
    cache_dir.mkdir(parents=True, exist_ok=True)

    try:
        _read_matrix_at(cache_dir, arm, ids)
        cache_hit = True
        secs = 0.0
    except MatrixCacheMissingError:
        cache_hit = False
        started = time.perf_counter()
        build_matrix(
            items,
            arm,
            member_ids=ids,
            roles=roles,
            cache_dir=cache_dir,
            n_jobs=n_jobs,
        )
        secs = time.perf_counter() - started

    matrix_path, _ = cache_paths(cache_dir, arm)
    n = len(ids)
    return {
        "rq": "matrices",
        "experiment": BUILD_EXPERIMENT,
        "collection": collection,
        "seed": 0,
        "arm": arm,
        "secs": round(secs, 4),
        "censored": 0,
        "n_members": n,
        "n_pairs": n * (n - 1) // 2,
        "peak_rss_mb": round(_peak_rss_mb(), 1),
        "cache_hit": int(cache_hit),
        "order_sha1": member_order_sha1(ids),
        "matrix_path": str(matrix_path),
        "n_jobs": n_jobs,
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Command-line entry point.

    Parameters
    ----------
    argv : Sequence[str] or None
        Argument vector; ``None`` reads ``sys.argv``.

    Returns
    -------
    int
        Process exit status.
    """
    parser = argparse.ArgumentParser(description="Build the shared TKDE distance matrices.")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None, help="results root")
    parser.add_argument("--shard", type=str, default=None, help="i/N")
    parser.add_argument("--unit", type=int, default=None, help="run exactly one unit")
    parser.add_argument("--count", action="store_true", help="print the unit count and exit")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--n-jobs", type=int, default=None)
    parser.add_argument(
        "--data-root",
        type=Path,
        default=None,
        help="directory holding corpora/ (Picasso: $ISALHG_DATA_ROOT)",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

    config = load_yaml(args.config) if args.config else {}
    specs = build_specs(config, smoke=args.smoke)
    units = enumerate_units(specs)

    if args.count:
        print(len(units))
        return 0

    out_root = Path(args.out) if args.out else results_root()
    data_root = resolve_data_root(args.data_root or config.get("data_root"))
    n_jobs = args.n_jobs or int(config.get("n_jobs") or os.environ.get("SLURM_CPUS_PER_TASK", 1))

    if args.unit is not None:
        selected = [args.unit]
    elif args.shard:
        index, count = parse_shard(args.shard)
        lo, hi = shard_bounds(len(units), index, count)
        selected = list(range(lo, hi))
    else:
        selected = list(range(len(units)))

    logger.info(
        "matrices: %d unit(s) of %d, out=%s n_jobs=%d smoke=%s",
        len(selected),
        len(units),
        out_root,
        n_jobs,
        args.smoke,
    )

    loaded: dict[str, Any] = {}
    rows: list[dict[str, Any]] = []
    for unit_index in selected:
        collection, arm = units[unit_index]
        collection_obj = _load(collection, data_root, smoke=args.smoke, cache=loaded)
        logger.info("unit %d: %s / %s", unit_index, collection, arm)
        row = run_unit(
            collection_obj,
            collection,
            arm,
            out_root=out_root,
            n_jobs=n_jobs,
            smoke=args.smoke,
        )
        row["experiment"] = BUILD_EXPERIMENT
        rows.append(row)
        logger.info(
            "unit %d done: secs=%.1f cache_hit=%d rss=%.0f MiB",
            unit_index,
            row["secs"],
            row["cache_hit"],
            row["peak_rss_mb"],
        )

    # A smoke run measures 40-member subsets under the real arm names, so its
    # timing rows are shaped like the campaign's; they go under the same smoke
    # component the .npy caches use rather than beside the real rows.
    experiment = f"{SMOKE_COMPONENT}/{BUILD_EXPERIMENT}" if args.smoke else BUILD_EXPERIMENT
    paths = RunPaths(root=out_root, rq=RQ_DIR, experiment=experiment)
    paths.ensure()
    tag = f"shard{args.shard.replace('/', '_')}" if args.shard else "all"
    if args.unit is not None:
        tag = f"unit{args.unit:04d}"
    write_rows(paths, f"matrices__{tag}", rows, columns=ROWS_MATRICES_COLUMNS)
    write_config(
        paths,
        {
            "specs": {k: list(v) for k, v in specs.items()},
            "n_units": len(units),
            "selected": selected,
            "n_jobs": n_jobs,
            "smoke": args.smoke,
            "out_root": str(out_root),
            "data_root": str(data_root) if data_root else None,
        },
    )
    write_manifest(paths, extra={"n_rows": len(rows), "tag": tag, **deploy_stamps()})
    return 0


if __name__ == "__main__":
    sys.exit(main())
