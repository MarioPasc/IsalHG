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
from experiments.tkde.budget import (
    CPP_ENGINE_ARMS,
    arm_fingerprint_screen,
    guarded_budget_call,
)
from experiments.tkde.config import TkdeConfigError, TkdeError, load_yaml, results_root
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
    "n_requested",
    "n_censored",
    "censored_ids",
    "n_members",
    "n_pairs",
    "peak_rss_mb",
    "cache_hit",
    "order_sha1",
    "matrix_path",
    "n_jobs",
)

#: Arms whose per-member representation is unbounded, so a whole-matrix build
#: over them needs the per-member budget of
#: :func:`experiments.tkde.budget.arm_fingerprint_screen`. ``wstar_rank`` is one
#: since wave 3 (an arity-10 member ran twelve minutes in-process, job 2248491);
#: the two ``w*_c`` arms were kept out of the matrices entirely for want of this
#: mechanism and become buildable with it. The ordered-walk arms are absent
#: because their emitter terminates.
BUDGETED_MATRIX_ARMS: tuple[str, ...] = CPP_ENGINE_ARMS

#: Wall-clock ceiling of one budgeted unit. This is process isolation, not a
#: deadline: the unit runs in a forked child so that the in-process
#: canonicalizations of the build cannot poison the parent's later screens
#: (measured 2026-09-08 -- ``wstar_rank``'s C++ entry point poisons forks
#: exactly as ``canonical_string(backend="cpp")`` does).
DEFAULT_UNIT_BUDGET_S = 86_400.0

#: The Isal instruction words that get an ``N x N`` matrix. ``wstar_orbit`` is
#: the paper's representation under D-ART5 and therefore needs one: the earlier
#: exclusion of both ``w*_c`` engines ("a budget is a per-member notion that a
#: whole-matrix build has nowhere to record") stopped being true at wave 6, when
#: :data:`BUDGETED_MATRIX_ARMS` gained them, ``arm_fingerprint_screen`` supplied
#: the per-member screen and ``<arm>.censored.json`` became the place to record
#: it. ``isalhg_levenshtein`` stays absent: it is the no-nauty cost cell of RQ1,
#: not an arm of any RQ2-RQ7 table, and its censoring drifts run to run.
#:
#: ``isal_ow_struct`` is built but published nowhere outside RQ7. Under D-ART5
#: exactly one Isal row reaches a table, and the ordered walk is not it; the
#: matrix is kept because it is the uncensored Isal reference against which a
#: censored ``wstar_orbit`` subset can be checked in the supplement, it costs
#: only its pairwise pass (its emitter is 0.54 ms/member), and a matrix is a
#: cached artefact rather than a published row. Rebuilding one later is a
#: multi-hour queue wait; the asymmetry favours having it.
ISAL_MATRIX_ARMS: tuple[str, ...] = (
    "wstar_orbit",
    "isal_ow_struct",
)

#: Arms per collection, frozen by the wave-3 brief. ``fact_rank_roles`` is not
#: among them: it fails the M0 relabelling-invariance check (43/60), so it is
#: not a measurable arm and may not reach a table (T-KBf). ``wd50k100`` is RQ5's
#: purity control and needs only the arms its supplementary table reports.
DEFAULT_SPECS: dict[str, tuple[str, ...]] = {
    "wd50k66": (
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


class MatrixCensoringError(TkdeError):
    """A censoring sidecar does not partition the frozen member order.

    Distinct from :class:`MatrixCacheMissingError` on purpose, and rooted
    outside it: a cache miss is a unit that has yet to run and callers such as
    :func:`cached_arms` swallow it, whereas a sidecar that names members the
    frozen order does not contain -- or omits members it does contain -- is a
    corrupted artefact whose matrix would be indexed under the wrong ids.
    """


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


def censoring_path(cache_dir: Path | str, arm: str) -> Path:
    """Return the sidecar recording which members a budgeted build dropped.

    The ``.npy`` and its manifest describe the matrix that was built, i.e. the
    surviving sub-corpus; this file is what tells a consumer which members those
    are, so that a censored arm can be read against the frozen order instead of
    looking like a cache miss.
    """
    return Path(cache_dir) / f"{arm}.censored.json"


def read_censoring(cache_dir: Path | str, arm: str) -> dict[str, Any] | None:
    """Return the censoring sidecar of one arm, or ``None`` when unscreened."""
    path = censoring_path(cache_dir, arm)
    if not path.is_file():
        return None
    try:
        payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        logger.warning("unreadable censoring sidecar %s; treating the arm as unscreened", path)
        return None
    return payload


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


def load_cached_matrix_censored(
    root: Path | str,
    collection: str,
    arm: str,
    member_ids: Sequence[str],
) -> tuple[NDArray[np.float32], tuple[str, ...], tuple[str, ...]]:
    """Read one cached matrix, tolerating a budgeted build's short member order.

    A budgeted unit writes its manifest over the *survivors*
    (:func:`_write_censoring`), so :func:`load_cached_matrix` -- which validates
    against the full frozen order -- reads a censored arm as a cache miss. This
    reader consults the ``<arm>.censored.json`` sidecar first and validates
    against whichever order actually describes the matrix, returning the
    survivor and censored id lists so that the caller can align by member id
    and report the census (L15).

    An absent sidecar means the arm was never screened, and the call is
    :func:`load_cached_matrix` with the full order as the survivor list.

    Parameters
    ----------
    root : Path or str
        Results root.
    collection : str
        Frozen collection name.
    arm : str
        Arm name, exactly as the matrices job requested it.
    member_ids : Sequence[str]
        The full frozen member order the sidecar must partition.

    Returns
    -------
    tuple
        ``(matrix, kept_ids, censored_ids)``. ``matrix`` is
        ``(len(kept_ids), len(kept_ids))`` and its rows are ``kept_ids`` in
        order; ``censored_ids`` is empty for an unscreened arm.

    Raises
    ------
    MatrixCacheMissingError
        If the matrix, its manifest, or the member-order agreement is absent.
    MatrixCensoringError
        If the sidecar's ``member_ids`` and ``censored_ids`` do not partition
        ``member_ids``.
    """
    frozen = tuple(str(member) for member in member_ids)
    cache_dir = collection_cache_dir(root, collection)
    sidecar = read_censoring(cache_dir, arm)
    if sidecar is None:
        return load_cached_matrix(root, collection, arm, frozen), frozen, ()

    kept_ids = tuple(str(member) for member in sidecar.get("member_ids", ()))
    censored_ids = tuple(str(member) for member in sidecar.get("censored_ids", ()))

    # A sidecar is a partition of the frozen order, not merely a subset of it:
    # equal sets alone would admit an id repeated on both sides, which would
    # index two matrix rows under one member.
    covered = set(kept_ids) | set(censored_ids)
    if covered != set(frozen) or len(kept_ids) + len(censored_ids) != len(frozen):
        raise MatrixCensoringError(
            f"censoring sidecar for collection={collection!r} arm={arm!r} does not partition "
            f"the frozen order: {len(kept_ids)} kept + {len(censored_ids)} censored over "
            f"{len(frozen)} frozen members; "
            f"unknown={sorted(covered - set(frozen))[:5]} "
            f"missing={sorted(set(frozen) - covered)[:5]}"
        )

    matrix = _read_matrix_at(cache_dir, arm, kept_ids)
    if matrix.shape != (len(kept_ids), len(kept_ids)):
        raise MatrixCacheMissingError(
            f"shape mismatch for collection={collection!r} arm={arm!r}: {matrix.shape} "
            f"for {len(kept_ids)} surviving members"
        )
    return matrix, kept_ids, censored_ids


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


def _build_censored_child(
    items: Sequence[Any],
    ids: Sequence[str],
    roles: Sequence[Any] | None,
    arm: str,
    cache_dir: Path,
    n_jobs: int,
    budget_s: float,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Screen, build and cache one arm's matrix; return ``(kept ids, censored ids)``.

    Runs as the body of a forked child: the screen forks a grandchild per member
    under ``budget_s``, and the build that follows canonicalizes in *this*
    process, which is why it must not be the runner's. Only the two id tuples
    cross the pipe; the matrix itself is persisted to ``cache_dir``.
    """
    from isalhg.metric_space.toolkit.matrix import build_matrix_censored

    _matrix, censoring = build_matrix_censored(
        items,
        arm,
        member_ids=list(ids),
        fingerprint_screen=arm_fingerprint_screen(arm, budget_s),
        roles=None if roles is None else list(roles),
        cache_dir=cache_dir,
        n_jobs=n_jobs,
    )
    return censoring.member_ids, censoring.censored_ids


def run_unit(
    collection_obj: Any,
    collection: str,
    arm: str,
    *,
    out_root: Path,
    n_jobs: int,
    smoke: bool = False,
    fingerprint_budget_s: float | None = None,
    unit_budget_s: float = DEFAULT_UNIT_BUDGET_S,
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
    smoke : bool, optional
        Route the cache under the smoke component.
    fingerprint_budget_s : float or None, optional
        Per-member wall-clock budget for the arms of
        :data:`BUDGETED_MATRIX_ARMS`. ``None`` (the default) builds every arm
        unscreened, which is what the campaign's cheap arms want and what an
        unbounded arm must not be given.
    unit_budget_s : float, optional
        Ceiling on the forked child a budgeted unit runs in.

    Returns
    -------
    dict[str, Any]
        One ``rows_matrices`` row, carrying the censored count and ids.
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
    screened = fingerprint_budget_s is not None and arm in BUDGETED_MATRIX_ARMS

    sidecar = read_censoring(cache_dir, arm)
    kept_ids: Sequence[str] = list(sidecar["member_ids"]) if sidecar else ids
    censored_ids: tuple[str, ...] = tuple(sidecar["censored_ids"]) if sidecar else ()

    try:
        _read_matrix_at(cache_dir, arm, kept_ids)
        cache_hit = True
        secs = 0.0
    except MatrixCacheMissingError:
        cache_hit = False
        started = time.perf_counter()
        if screened:
            # The build canonicalizes in-process and would poison this process
            # for every later screen, so it is run in a child that then dies.
            result = guarded_budget_call(
                _build_censored_child,
                (items, ids, roles, arm, cache_dir, n_jobs, float(fingerprint_budget_s or 0.0)),
                unit_budget_s,
            )
            if not result.ok:
                raise TkdeConfigError(
                    f"budgeted matrix unit {collection}/{arm} did not produce a matrix: "
                    f"{'censored at the unit budget' if result.censored else result.error}"
                ) from None
            kept_ids, censored_ids = result.value
            _write_censoring(cache_dir, arm, kept_ids, censored_ids, len(ids))
        else:
            build_matrix(
                items,
                arm,
                member_ids=ids,
                roles=roles,
                cache_dir=cache_dir,
                n_jobs=n_jobs,
            )
            # A rebuild without a screen supersedes whatever a previous
            # budgeted build recorded, so a stale sidecar must not be reported.
            kept_ids, censored_ids = ids, ()
        secs = time.perf_counter() - started

    matrix_path, _ = cache_paths(cache_dir, arm)
    n = len(kept_ids)
    return {
        "rq": "matrices",
        "experiment": BUILD_EXPERIMENT,
        "collection": collection,
        "seed": 0,
        "arm": arm,
        "secs": round(secs, 4),
        "censored": int(bool(censored_ids)),
        "n_requested": len(ids),
        "n_censored": len(censored_ids),
        "censored_ids": " ".join(censored_ids),
        "n_members": n,
        "n_pairs": n * (n - 1) // 2,
        "peak_rss_mb": round(_peak_rss_mb(), 1),
        "cache_hit": int(cache_hit),
        "order_sha1": member_order_sha1(kept_ids),
        "matrix_path": str(matrix_path),
        "n_jobs": n_jobs,
    }


def _write_censoring(
    cache_dir: Path,
    arm: str,
    kept_ids: Sequence[str],
    censored_ids: Sequence[str],
    n_requested: int,
) -> None:
    """Persist the sidecar beside the matrix (atomic rename)."""
    payload = {
        "arm": arm,
        "n_requested": int(n_requested),
        "n_censored": len(censored_ids),
        "member_ids": list(kept_ids),
        "censored_ids": list(censored_ids),
        "member_order_sha1": member_order_sha1(kept_ids),
    }
    path = censoring_path(cache_dir, arm)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


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
        "--fingerprint-budget-s",
        type=float,
        default=None,
        help=(
            "per-member wall-clock budget for the unbounded arms "
            f"({', '.join(BUDGETED_MATRIX_ARMS)}); members that overrun are dropped "
            "from the matrix and reported"
        ),
    )
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

    budget_value = (
        args.fingerprint_budget_s
        if args.fingerprint_budget_s is not None
        else config.get("fingerprint_budget_s")
    )
    fingerprint_budget_s = None if budget_value is None else float(budget_value)
    unit_budget_s = float(config.get("unit_budget_s") or DEFAULT_UNIT_BUDGET_S)

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
            fingerprint_budget_s=fingerprint_budget_s,
            unit_budget_s=unit_budget_s,
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
