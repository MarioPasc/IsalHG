"""``N x N`` distance-matrix builder with an on-disk cache.

One entry point, :func:`build_matrix`, serves every arm of the TKDE design.

Two computation paths, chosen by the arm name:

* ``"fact_rank"`` / ``"fact_rank_roles"`` -- **words first**. The fact word of
  each member is computed once (roles attached only on the roles arm), and the
  whole matrix comes from a single ``rapidfuzz.process.cdist`` call. This is the
  only way the roles arm is computable at all: a roles map cannot travel through
  ``HypergraphDistance.pairwise(H1, H2)``, which sees hypergraphs and nothing
  else.
* any arm whose distance object amortizes -- i.e. whose ``fingerprint(H)``
  returns a value rather than ``None`` -- **fingerprint first**, through that
  object's own :meth:`HypergraphDistance.matrix`. The pairwise loop would
  recompute each member's representation ``N - 1`` times; the Isal instruction
  words (``isal_ow_*``, ``wstar_rank``, ``wstar_orbit``) and the certificate and
  vector arms all amortize, so the loop is quadratic work for a linear
  quantity. ``isalhg_levenshtein`` deliberately reports ``fingerprint(H) is
  None`` unless ``k`` is pinned, because ``w*_c`` is a family indexed by ``k``
  and the corpus maximum is not known to a per-member call; it therefore stays
  on the pairwise path, where the campaign's per-pair budget applies.
* every remaining arm -- ``get_distance(arm).pairwise`` over the upper triangle,
  in a ``fork`` multiprocessing pool when ``n_jobs > 1``.

The cache is ``<cache_dir>/<arm>.npy`` plus ``<cache_dir>/<arm>.manifest.json``.
A cached matrix is reused only when the arm, the parameters, the member count
and the SHA-1 of the member order all match; anything else recomputes. Member
order is part of the key because the matrix is indexed by it and nothing in the
``.npy`` records it.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import platform
import socket
import time
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from isalhg.core.fact_word import RolesMap
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.errors import MetricSpaceError, RepresentationDependencyMissingError

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray

logger = logging.getLogger(__name__)

WORD_ARMS: tuple[str, ...] = ("fact_rank", "fact_rank_roles")
ROLES_ARM_SUFFIX = "roles"
MATRIX_DTYPE = "float32"

_WORKER_STATE: dict[str, Any] = {}


def member_order_sha1(member_ids: Sequence[str]) -> str:
    """Return the SHA-1 of the newline-joined member ids.

    Parameters
    ----------
    member_ids : Sequence[str]
        Member ids in matrix-row order.

    Returns
    -------
    str
        Hexadecimal SHA-1 digest, the cache key's order component.
    """
    payload = "\n".join(member_ids).encode("utf-8")
    return hashlib.sha1(payload, usedforsecurity=False).hexdigest()


def cache_paths(cache_dir: Path | str, arm: str) -> tuple[Path, Path]:
    """Return ``(matrix_path, manifest_path)`` for one arm under ``cache_dir``.

    Parameters
    ----------
    cache_dir : Path or str
        Directory holding one collection's cached matrices.
    arm : str
        Arm name; the file stem.

    Returns
    -------
    tuple[Path, Path]
        ``<cache_dir>/<arm>.npy`` and ``<cache_dir>/<arm>.manifest.json``.
    """
    base = Path(cache_dir)
    return base / f"{arm}.npy", base / f"{arm}.manifest.json"


def build_matrix(
    items: Sequence[SparseHypergraph],
    arm: str,
    *,
    member_ids: Sequence[str],
    roles: Sequence[RolesMap | None] | None = None,
    cache_dir: Path | str | None = None,
    n_jobs: int = 1,
    params: Mapping[str, Any] | None = None,
) -> NDArray[np.float32]:
    """Return the symmetric ``N x N`` distance matrix of ``items`` under ``arm``.

    Parameters
    ----------
    items : Sequence[SparseHypergraph]
        The corpus, in member order.
    arm : str
        Registered distance name (see :func:`isalhg.metric_space.registry.get_distance`),
        or one of :data:`WORD_ARMS` for the words-first path.
    member_ids : Sequence[str]
        Member id per row, same length and order as ``items``. Part of the cache
        key: a matrix computed under a different order is not reused.
    roles : Sequence[RolesMap | None] or None, optional
        Roles map per member. Consumed only by ``"fact_rank_roles"``; ignored
        (with a debug log) by every other arm.
    cache_dir : Path or str or None, optional
        Cache directory. ``None`` disables both the read and the write.
    n_jobs : int, optional
        Worker processes for the ``pairwise`` path (``1`` runs serially, in
        process). The words-first path passes it to ``rapidfuzz`` as ``workers``.
    params : Mapping or None, optional
        Arm parameters. Recorded in the manifest and part of the cache key.
        The distance registry exposes zero-argument factories, so a non-empty
        mapping cannot be applied and raises.

    Returns
    -------
    numpy.ndarray
        ``(N, N)`` ``float32`` matrix, symmetric with a zero diagonal.

    Raises
    ------
    isalhg.errors.MetricSpaceError
        If ``member_ids`` or ``roles`` do not match ``items`` in length, if
        ``n_jobs < 1``, or if ``params`` is non-empty.
    isalhg.errors.RepresentationDependencyMissingError
        If rapidfuzz is missing on the words-first path.
    """
    import numpy as np

    size = len(items)
    if len(member_ids) != size:
        raise MetricSpaceError(
            f"member_ids has {len(member_ids)} entries for {size} items; they must correspond"
        )
    if roles is not None and len(roles) != size:
        raise MetricSpaceError(
            f"roles has {len(roles)} entries for {size} items; they must correspond"
        )
    if n_jobs < 1:
        raise MetricSpaceError(f"n_jobs must be >= 1, got {n_jobs}")

    normalized_params = dict(params or {})
    order_sha = member_order_sha1(member_ids)

    cached = _read_cache(cache_dir, arm, size, order_sha, normalized_params)
    if cached is not None:
        logger.info("cache hit: arm=%s n=%d order=%s dir=%s", arm, size, order_sha[:12], cache_dir)
        return cached
    if cache_dir is not None:
        logger.info("cache miss: arm=%s n=%d order=%s dir=%s", arm, size, order_sha[:12], cache_dir)

    started = time.perf_counter()
    if arm in WORD_ARMS:
        matrix = _build_from_words(items, arm, roles, n_jobs)
    elif _amortizes(arm, items, normalized_params):
        matrix = _build_from_fingerprints(items, arm, normalized_params)
    else:
        matrix = _build_from_pairwise(items, arm, n_jobs, normalized_params)
    secs_total = time.perf_counter() - started

    matrix = np.asarray(matrix, dtype=np.float32)
    np.fill_diagonal(matrix, 0.0)
    logger.info("computed: arm=%s n=%d secs=%.3f", arm, size, secs_total)

    _write_cache(
        cache_dir,
        arm,
        matrix,
        order_sha,
        normalized_params,
        secs_total,
        _arm_metadata(arm, normalized_params),
    )
    return matrix


# ---------------------------------------------------------------------------
# Computation paths
# ---------------------------------------------------------------------------


def _build_from_words(
    items: Sequence[SparseHypergraph],
    arm: str,
    roles: Sequence[RolesMap | None] | None,
    n_jobs: int,
) -> NDArray[np.float32]:
    """Words-first path: encode each member once, then one ``cdist`` call."""
    import numpy as np

    if not items:
        return np.zeros((0, 0), dtype=np.float32)

    from isalhg.metric_space.distances.fact_levenshtein import fact_word

    use_roles = arm.endswith(ROLES_ARM_SUFFIX)
    if use_roles and roles is None:
        logger.warning("arm %s requested without roles maps; encoding without roles", arm)
    per_member_roles: Sequence[RolesMap | None] = (
        roles if use_roles and roles is not None else [None] * len(items)
    )

    words = [fact_word(H, r) for H, r in zip(items, per_member_roles, strict=True)]

    levenshtein, process = _import_rapidfuzz()
    result = process.cdist(
        words, words, scorer=levenshtein.distance, workers=n_jobs, dtype=np.float32
    )
    return np.asarray(result, dtype=np.float32)


def _amortizes(arm: str, items: Sequence[SparseHypergraph], params: Mapping[str, Any]) -> bool:
    """True when this arm's representation can be computed once per member.

    Decided by asking the distance object itself: ``fingerprint`` is the ABC's
    declaration that a member has a standalone representation, and returning
    ``None`` is how a distance declares it has none (or, for
    ``isalhg_levenshtein``, that the representation depends on a corpus-level
    ``k`` this call cannot know). The probe uses the first member, so an arm
    that raises on a particular input degrades to the pairwise path rather than
    aborting the build.
    """
    if not items:
        return False
    try:
        distance = _make_distance(arm, params)
        return distance.fingerprint(items[0]) is not None
    except Exception as exc:  # noqa: BLE001 - an unavailable probe is not a build failure
        logger.debug("arm %s does not amortize (%s); using the pairwise path", arm, exc)
        return False


def _build_from_fingerprints(
    items: Sequence[SparseHypergraph],
    arm: str,
    params: Mapping[str, Any],
) -> NDArray[np.float32]:
    """Fingerprint-first path: the distance object's own ``matrix``.

    Every amortizing distance in the registry implements ``matrix`` as "encode
    each member once, then one vectorised pass", so the work is linear in the
    corpus instead of quadratic. It is single-process by construction; the
    ``n_jobs`` the caller asked for prices the pairwise loop this path replaces,
    not this one.
    """
    import numpy as np

    if not items:
        return np.zeros((0, 0), dtype=np.float32)
    distance = _make_distance(arm, params)
    return np.asarray(distance.matrix(items), dtype=np.float32)


def _build_from_pairwise(
    items: Sequence[SparseHypergraph],
    arm: str,
    n_jobs: int,
    params: Mapping[str, Any],
) -> NDArray[np.float32]:
    """Generic path: ``HypergraphDistance.pairwise`` over the upper triangle."""
    import numpy as np

    size = len(items)
    matrix = np.zeros((size, size), dtype=np.float32)
    if size < 2:
        return matrix

    pairs = [(i, j) for i in range(size) for j in range(i + 1, size)]

    if n_jobs == 1:
        distance = _make_distance(arm, params)
        for i, j in pairs:
            value = float(distance.pairwise(items[i], items[j]))
            matrix[i, j] = value
            matrix[j, i] = value
        return matrix

    import multiprocessing as mp

    context = mp.get_context("fork")
    chunk_size = max(1, len(pairs) // (n_jobs * 8))
    chunks = [pairs[start : start + chunk_size] for start in range(0, len(pairs), chunk_size)]
    # Publish the corpus before forking: the children inherit it copy-on-write,
    # so it is never pickled. Passing it through initargs sent one full copy of
    # the collection down a pipe per worker.
    _WORKER_STATE["items"] = items
    try:
        with context.Pool(
            processes=n_jobs,
            initializer=_init_worker,
            initargs=(arm, dict(params)),
        ) as pool:
            for chunk_result in pool.imap_unordered(_pair_chunk, chunks):
                for i, j, value in chunk_result:
                    matrix[i, j] = value
                    matrix[j, i] = value
    finally:
        _WORKER_STATE.pop("items", None)
    return matrix


def _init_worker(arm: str, params: dict[str, Any]) -> None:
    """Pool initializer: instantiate the distance once per worker process.

    The corpus is already present in ``_WORKER_STATE`` through the fork; only
    the distance object, which may hold un-picklable handles, is built here.
    """
    _WORKER_STATE["distance"] = _make_distance(arm, params)


def _pair_chunk(chunk: Sequence[tuple[int, int]]) -> list[tuple[int, int, float]]:
    """Evaluate one chunk of ``(i, j)`` pairs in a worker process."""
    items = _WORKER_STATE["items"]
    distance = _WORKER_STATE["distance"]
    return [(i, j, float(distance.pairwise(items[i], items[j]))) for i, j in chunk]


def _make_distance(arm: str, params: Mapping[str, Any]) -> Any:
    """Instantiate the registered distance named ``arm``.

    Raises
    ------
    isalhg.errors.MetricSpaceError
        If ``params`` is non-empty. The registry stores zero-argument factories,
        so a parameterised variant must be registered under its own name (as
        ``fact_rank_roles`` is) rather than configured here.
    """
    if params:
        raise MetricSpaceError(
            f"arm {arm!r}: the distance registry holds zero-argument factories, so "
            f"params={dict(params)!r} cannot be applied; register a parameterised "
            "name instead"
        )
    from isalhg.metric_space.registry import get_distance

    return get_distance(arm)


def _arm_metadata(arm: str, params: Mapping[str, Any]) -> dict[str, Any]:
    """Descriptive (never key-bearing) manifest fields read off the distance object.

    An arm may be registered under an alias whose class reports a different
    ``.name``; recording both lets a reader reconcile the cache file name (the
    requested arm, always) with the class that produced it. ``labels_used``
    reports whether the representation honoured vertex/edge labels, when the
    class exposes it.
    """
    metadata: dict[str, Any] = {"canonical_name": None, "labels_used": None}
    try:
        distance = _make_distance(arm, params)
    except Exception as exc:  # noqa: BLE001 - metadata is best effort, never fatal
        logger.debug("no distance metadata for arm %s: %s", arm, exc)
        return metadata
    metadata["canonical_name"] = str(distance.name)
    labels_used = getattr(distance, "labels_used", None)
    if labels_used is not None:
        # The ABC declares this as a frozenset, which json cannot serialise.
        metadata["labels_used"] = sorted(str(kind) for kind in labels_used)
    return metadata


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------


def _read_cache(
    cache_dir: Path | str | None,
    arm: str,
    size: int,
    order_sha: str,
    params: Mapping[str, Any],
) -> NDArray[np.float32] | None:
    """Return the cached matrix when the manifest matches, else ``None``."""
    if cache_dir is None:
        return None
    matrix_path, manifest_path = cache_paths(cache_dir, arm)
    if not (matrix_path.is_file() and manifest_path.is_file()):
        return None
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        logger.warning("unreadable cache manifest %s; recomputing", manifest_path)
        return None

    mismatches = [
        field
        for field, expected in (
            ("arm", arm),
            ("n", size),
            ("member_order_sha1", order_sha),
            ("params", dict(params)),
        )
        if manifest.get(field) != expected
    ]
    if mismatches:
        logger.info("cache manifest mismatch on %s; recomputing", ", ".join(mismatches))
        return None

    import numpy as np

    try:
        matrix = np.load(matrix_path)
    except (OSError, ValueError):
        logger.warning("unreadable cache matrix %s; recomputing", matrix_path)
        return None
    if matrix.shape != (size, size):
        logger.warning(
            "cached matrix %s has shape %s, expected %s; recomputing",
            matrix_path,
            matrix.shape,
            (size, size),
        )
        return None
    return np.asarray(matrix, dtype=np.float32)


def _write_cache(
    cache_dir: Path | str | None,
    arm: str,
    matrix: NDArray[np.float32],
    order_sha: str,
    params: Mapping[str, Any],
    secs_total: float,
    metadata: Mapping[str, Any] | None = None,
) -> None:
    """Persist ``matrix`` and its manifest under ``cache_dir`` (atomic rename)."""
    if cache_dir is None:
        return
    import numpy as np

    matrix_path, manifest_path = cache_paths(cache_dir, arm)
    matrix_path.parent.mkdir(parents=True, exist_ok=True)

    tmp_matrix = matrix_path.with_suffix(".npy.tmp")
    # np.save appends ".npy" to a path that does not already end in it, so the
    # temporary file must be written through an open handle to keep its name.
    with tmp_matrix.open("wb") as handle:
        np.save(handle, matrix)
    os.replace(tmp_matrix, matrix_path)

    manifest = {
        "arm": arm,
        "params": dict(params),
        "n": int(matrix.shape[0]),
        "member_order_sha1": order_sha,
        "secs_total": float(secs_total),
        "host": socket.gethostname(),
        "created_iso": datetime.now(UTC).isoformat(),
        "dtype": MATRIX_DTYPE,
        "platform": platform.platform(),
    }
    manifest.update(dict(metadata or {}))
    tmp_manifest = manifest_path.with_suffix(".json.tmp")
    tmp_manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp_manifest, manifest_path)


# ---------------------------------------------------------------------------
# Guarded imports
# ---------------------------------------------------------------------------


def _import_rapidfuzz() -> tuple[Any, Any]:
    try:
        from rapidfuzz import process
        from rapidfuzz.distance import Levenshtein
    except ImportError as exc:  # pragma: no cover - exercised only without rapidfuzz
        raise RepresentationDependencyMissingError(
            "rapidfuzz is required for the words-first matrix path; "
            "install via `pip install rapidfuzz`"
        ) from exc
    return Levenshtein, process


__all__ = ["WORD_ARMS", "build_matrix", "cache_paths", "member_order_sha1"]
