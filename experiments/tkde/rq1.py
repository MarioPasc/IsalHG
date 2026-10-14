"""RQ1 runner -- representation design (addressing).

Implements ``DESIGN.md`` §2 verbatim: M0 (exactness and invariance), M1
(single-edit response), M2 (correlation with the known fact-level difference),
M3 (compactness and cost) and M4 (relation to the certificate), on
``synthetic_rq1``, ``ndc_classes`` and ``wd50k66``, over the six addressing arms
plus ``nauty_cert``.

Two structural decisions worth stating, because they are not in the design:

* **M0 is emitted as per-member rows, not as the aggregate.** The design's
  ``rows_m0`` is one row per ``(collection, arm)`` carrying collection-wide
  counts (false merges, false splits). A collection-wide count cannot be
  computed inside a shard that sees a slice of the members, so the runner
  writes ``rows_m0items`` (one row per member and arm: the word hash, the
  nauty hash, the invariance flag) and :mod:`experiments.tkde.analyze_rq1`
  reduces those to the design's ``rows_m0.csv``. Nothing is lost and the
  reduction is reproducible from the persisted rows (G5's rule).
* **Arm words are computed once per member and compared as symbol sequences.**
  Every RQ1 arm's ``pairwise`` is exactly ``Levenshtein(fingerprint(H1),
  fingerprint(H2))`` (verified in the source of each arm), so fingerprint-once
  is equivalent and avoids recomputing a canonical labelling per pair.

The pointer arm is the only expensive one and the only one that cannot be
bounded from inside Python; every one of its canonicalizations goes through
:func:`experiments.tkde.budget.pointer_word` (forked child, SIGKILL at 60 s).
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
from experiments.tkde.budget import engine_word, pointer_symbols, symbol_distance
from experiments.tkde.config import TkdeConfigError, load_yaml, seeds
from experiments.tkde.io import RunPaths, write_config, write_manifest, write_rows

logger = logging.getLogger(__name__)

RQ_INDEX = 1
RQ_FOLDER = "RQ1_addressing"
EXPERIMENT = "addressing"

POINTER_ARM = "isalhg_levenshtein"
ROLES_ARM = "fact_rank_roles"
CERT_ARM = "nauty_cert"
CERT_ROWS_ARM = "nauty_cert_rows"

#: The Isal instruction word of the ordered walk (Theorem C), one arm per
#: emission policy. Exact, `k`-free and cheap enough to run unbudgeted.
OW_ARMS: tuple[str, ...] = ("isal_ow_struct", "isal_ow_rank", "isal_ow_rank0")

#: Arm -> :func:`experiments.tkde.budget.engine_word` engine, for the arms whose
#: search does not return to the interpreter on time-out and must therefore be
#: bounded by a forked child. ``wstar_rank`` is deliberately absent: its greedy
#: walk terminates in milliseconds, so it goes through ``get_distance`` like the
#: ordered-walk arms and pays no fork.
#: Every Isal engine with a search runs in a forked child under the budget —
#: the rank engine included: since wave 3 it is the C++ engine, and an
#: unbudgeted in-process call on an arity-10 member ran for more than twelve
#: minutes in the 2026-09-07 rank smoke (job 2248491).
BUDGETED_ARMS: dict[str, str] = {
    POINTER_ARM: "cpp",
    "wstar_orbit": "orbit",
    "wstar_rank": "rank",
}

#: ``|Aut|`` strata of the coloured Levi graph. The labels are decade
#: groupings, so the middle bucket is ``[1e3, 1e7)`` and the three are
#: exhaustive.
AUT_BUCKETS: tuple[tuple[float, str], ...] = ((1e3, "<1e3"), (1e7, "1e3-1e6"))
AUT_BUCKET_TOP = ">=1e7"

#: ``ROLES_ARM`` is deliberately absent: it fails the M0 relabelling-invariance
#: gate on wd50k66 (247 false splits, 2,104 violations of 3,988 members), so it
#: is not a measurable arm and must not reach a table (T-KBf). ``member_word``
#: still knows how to compute it, so a config that names it explicitly can, but
#: nothing selects it by default.
DEFAULT_ARMS: tuple[str, ...] = (
    POINTER_ARM,
    "wstar_rank",
    "wstar_orbit",
    *OW_ARMS,
    "fact_rank",
    "fact_local_colour",
    "fact_local_key",
    "fact_degree_key",
    CERT_ARM,
    CERT_ROWS_ARM,
)

UNIVERSAL_COLUMNS: tuple[str, ...] = ("rq", "experiment", "git_sha", "host_cpu")

COLUMNS_M0ITEMS: tuple[str, ...] = (
    *UNIVERSAL_COLUMNS,
    "collection",
    "seed",
    "member_id",
    "arm",
    "word_hash",
    "nauty_hash",
    "invariance_ok",
    "censored",
    "secs",
)
COLUMNS_M1: tuple[str, ...] = (
    *UNIVERSAL_COLUMNS,
    "collection",
    "seed",
    "base_id",
    "edit_kind",
    "edit_idx",
    "regime",
    "zero_shift",
    "aut_bucket",
    "arm",
    "d_abs",
    "d_instr",
    "n_instr",
    "len_base",
    "len_edit",
    "secs_canon",
    "censored",
)
COLUMNS_M2: tuple[str, ...] = (
    *UNIVERSAL_COLUMNS,
    "collection",
    "seed",
    "series",
    "pair_id",
    "delta",
    "regime",
    "arm",
    "d",
    "len_a",
    "len_b",
    "secs",
    "censored",
)
COLUMNS_M3: tuple[str, ...] = (
    *UNIVERSAL_COLUMNS,
    "collection",
    "seed",
    "member_id",
    "n",
    "m",
    "k",
    "aut_bucket",
    "arm",
    "tokens",
    "n_instr",
    "secs",
    "censored",
)
COLUMNS_M4: tuple[str, ...] = (
    *UNIVERSAL_COLUMNS,
    "collection",
    "seed",
    "series",
    "pair_id",
    "arm",
    "d",
    "d_cert",
    "censored",
)


class Rq1Error(TkdeConfigError):
    """The RQ1 runner was asked for something the design does not define."""


# ---------------------------------------------------------------------------
# Units
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Unit:
    """One independently computable, independently resumable piece of work."""

    kind: str
    collection: str
    block: int = 0
    n_blocks: int = 1
    extra: Mapping[str, Any] = field(default_factory=dict)

    @property
    def unit_id(self) -> str:
        """Stable id; part of every row file name this unit writes."""
        return f"{self.kind}-{self.collection}-{self.block:03d}of{self.n_blocks:03d}"

    @property
    def tables(self) -> tuple[str, ...]:
        """Row tables this unit is responsible for."""
        if self.kind == "m3":
            return ("m3", "m0items")
        return (self.kind,)


OPERATIONAL_KEYS: frozenset[str] = frozenset({"n_shards", "smoke"})
RUN_TAG_LENGTH = 8


def run_tag(config: Mapping[str, Any]) -> str:
    """Short hash of the parameters that determine what a unit measures.

    Every row file is named ``rows_<table>__<run_tag>-<unit_id>.csv``, and the
    idempotence check looks for exactly that name. Without the tag, two runs
    whose *unit ids* coincide but whose *parameters* differ are indistinguishable
    on disk, and the second silently inherits the first's rows -- which is not
    hypothetical: a ``--smoke`` run and the campaign share the unit-id namespace
    (``exact0-ndc_classes-fact_rank`` is a unit of both), so five toy members
    would have stood in for the corpus. Changing ``m1_edits_per_kind`` without
    changing a block count has the same shape.

    Keys that describe *how* the work is distributed rather than *what* is
    measured (``n_shards``, ``smoke``) are excluded, so re-sharding a campaign
    resumes it instead of recomputing it.

    Parameters
    ----------
    config : Mapping
        The parsed configuration, after any ``--smoke`` overlay.

    Returns
    -------
    str
        Eight hexadecimal characters.
    """
    import json

    payload = {key: value for key, value in config.items() if key not in OPERATIONAL_KEYS}
    encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha1(encoded, usedforsecurity=False).hexdigest()[:RUN_TAG_LENGTH]


def table_file(tag: str, table: str, unit_id: str) -> str:
    """The ``write_rows`` table name of one unit's row file."""
    return f"{table}__{tag}-{unit_id}"


def deploy_stamps(repo_dir: Path | str | None = None) -> dict[str, str]:
    """Both deployment stamps, because two trees are in play on the cluster.

    The editable install is a PEP 660 meta-path finder, so it wins over
    ``PYTHONPATH``: ``isalhg.*`` is imported from the checkout the environment
    was installed from, while ``experiments.tkde.*`` comes from the deployed
    runner tree. Recording only one of the two stamps would attribute a result
    to a tree that did not compute half of it.

    Parameters
    ----------
    repo_dir : Path or str or None, optional
        The runner tree; defaults to ``$REPO_DIR`` or the current directory.

    Returns
    -------
    dict
        ``runner_deploy`` and ``src_deploy``, each the stamp's text or a short
        note saying why it is unavailable, plus ``isalhg_path`` and
        ``isalhg_git_sha`` -- the resolved package file and the head of the tree
        it came out of. The deploy stamps are written by the cluster sync and
        are absent on a local run, where those last two are the whole answer.
    """
    import os

    runner = Path(repo_dir or os.environ.get("REPO_DIR") or Path.cwd())
    installed = Path(
        os.environ.get(
            "ISALHG_SRC_REPO",
            "/mnt/home/users/tic_163_uma/mpascual/fscratch/repos/IsalHG-tkde",
        )
    )
    stamps: dict[str, str] = {}
    for name, directory in (("runner_deploy", runner), ("src_deploy", installed)):
        stamp = directory / ".tkde_deploy"
        try:
            stamps[name] = stamp.read_text(encoding="utf-8").strip()
        except OSError:
            stamps[name] = f"absent at {stamp}"
    stamps.update(library_provenance())
    return stamps


def library_provenance() -> dict[str, str]:
    """Name the tree that actually served ``isalhg``, and its git head.

    The PEP 660 editable finder is consulted before ``sys.path``, so the
    library half of a run comes from whichever checkout the environment was
    installed from -- which on a worktree-per-agent layout is *not* the tree the
    runner was read from. ``isalhg.__file__`` settles it without depending on a
    deploy stamp existing.

    Returns
    -------
    dict
        ``isalhg_path`` and ``isalhg_git_sha`` (``"unknown"`` when the tree is
        not a git checkout or git is unavailable).
    """
    import subprocess

    import isalhg

    package = Path(isalhg.__file__).resolve()
    sha = "unknown"
    try:
        sha = subprocess.run(
            ["git", "-C", str(package.parent), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        logger.debug("no git head for %s", package.parent)
    return {"isalhg_path": str(package), "isalhg_git_sha": sha}


def _blocks_for(config: Mapping[str, Any], key: str, collection: str) -> int:
    blocks = dict(config.get(key, {}) or {})
    return max(1, int(blocks.get(collection, 1)))


def enumerate_units(config: Mapping[str, Any]) -> list[Unit]:
    """Every unit of this configuration, in a deterministic order.

    Parameters
    ----------
    config : Mapping
        The parsed configuration.

    Returns
    -------
    list[Unit]
        ``m3`` units (per-member cost, tokens and the M0 ingredients), ``m1``
        units (single-edit response), one ``m2`` unit per series and one ``m4``
        unit per collection.
    """
    collections = list(config.get("collections") or [])
    units: list[Unit] = []
    for collection in collections:
        total = _blocks_for(config, "m3_blocks", collection)
        units.extend(Unit("m3", collection, block=b, n_blocks=total) for b in range(total))
    for collection in collections:
        total = _blocks_for(config, "m1_blocks", collection)
        units.extend(Unit("m1", collection, block=b, n_blocks=total) for b in range(total))
    for collection in collections:
        series = _m2_series(config, collection)
        if not series:
            continue
        total = _blocks_for(config, "m2_blocks", collection)
        units.extend(
            Unit("m2", collection, block=b, n_blocks=total, extra={"series": series})
            for b in range(total)
        )
    for collection in collections:
        total = _blocks_for(config, "m4_blocks", collection)
        units.extend(Unit("m4", collection, block=b, n_blocks=total) for b in range(total))
    return units


def _m2_series(config: Mapping[str, Any], collection: str) -> str:
    """Which M2 series a collection contributes: natural pairs, or ladders."""
    natural = set(config.get("m2_natural") or ())
    ladders = set(config.get("m2_ladders") or ())
    if collection in natural:
        return "natural"
    if collection in ladders:
        return "ladder"
    return ""


# ---------------------------------------------------------------------------
# Arm words
# ---------------------------------------------------------------------------


def arm_is_available(arm: str) -> tuple[bool, str]:
    """Whether an arm can be computed in this tree, and why not when it cannot.

    Asked once per run rather than once per call: an arm whose engine has not
    landed would otherwise fork, raise and be recorded for every one of the
    thousands of words a unit computes, filling the rows with empty distances
    and the log with the same traceback.

    Parameters
    ----------
    arm : str
        Registered arm name.

    Returns
    -------
    tuple
        ``(available, reason)``; ``reason`` is ``""`` when available.
    """
    if arm == ROLES_ARM:
        return True, ""
    try:
        from isalhg.metric_space.registry import get_distance

        distance = get_distance(arm)
    except Exception as exc:  # noqa: BLE001 - an absent arm is data, not a crash
        return False, f"{type(exc).__name__}: {exc}"
    entry_point = getattr(distance, "_entry_point", None)
    if entry_point is None:
        return True, ""
    try:
        entry_point()
    except Exception as exc:  # noqa: BLE001 - same
        return False, f"{type(exc).__name__}: {exc}"
    return True, ""


def available_arms(arms: Sequence[str], *, context: str) -> list[str]:
    """Drop the arms this tree cannot compute, warning once per arm.

    Shared by every runner that resolves an arm list up front, so a partial
    deployment produces a smaller table rather than one exception per word.

    Parameters
    ----------
    arms : Sequence[str]
        Requested arm names.
    context : str
        What the list is for (a collection, a grid cell); named in the warning.

    Returns
    -------
    list[str]
        The subset that resolves.
    """
    kept: list[str] = []
    for arm in arms:
        available, reason = arm_is_available(arm)
        if available:
            kept.append(arm)
        else:
            logger.warning("%s: dropping arm %s (%s)", context, arm, reason)
    return kept


def arms_for(collection: str, arms: Sequence[str], k_max_roles: bool) -> list[str]:
    """The arms that apply to one collection.

    ``fact_rank_roles`` exists only where the corpus carries roles (WD50K); it
    is dropped elsewhere rather than silently degenerating into the primary arm.
    """
    wanted = list(arms) if k_max_roles else [arm for arm in arms if arm != ROLES_ARM]
    return available_arms(wanted, context=f"collection {collection}")


def member_word(
    arm: str,
    H: Any,
    roles: Any,
    *,
    k: int,
    budget: float,
) -> tuple[Any, float, bool]:
    """Return ``(word, secs, censored)`` of one member under one arm.

    Parameters
    ----------
    arm : str
        Registered arm name.
    H : SparseHypergraph
        The member.
    roles : RolesMap or None
        Consumed only by ``fact_rank_roles``.
    k : int
        Pointer count for the budgeted engines (ignored by every other arm).
    budget : float
        Process-level budget for the budgeted engines.

    Returns
    -------
    tuple
        The word (``None`` when censored or failed), the wall-clock seconds and
        the censoring flag. A budgeted engine's word is ``(word, seed_label)``;
        every other arm's is whatever its ``fingerprint`` returns -- for the
        ordered-walk and ``wstar_rank`` arms, the seed-prefixed symbol tuple.
    """
    if arm in BUDGETED_ARMS:
        result = engine_word(H, k, budget, engine=BUDGETED_ARMS[arm])
        return (result.value, result.secs, result.censored)

    start = time.perf_counter()
    if arm == ROLES_ARM:
        from isalhg.metric_space.distances.fact_levenshtein import fact_word

        word: Any = fact_word(H, roles)
    else:
        from isalhg.metric_space.registry import get_distance

        word = get_distance(arm).fingerprint(H)
    return (word, time.perf_counter() - start, False)


def word_tokens(arm: str, word: Any) -> int:
    """Token count of an arm word (bytes for the certificate, per ``DESIGN.md`` §8)."""
    if word is None:
        return 0
    if arm in BUDGETED_ARMS:
        from isalhg.core.instructions import parse

        return len(tuple(parse(word[0])))
    return len(word)


def instruction_symbols(arm: str, word: Any, *, augment: bool) -> tuple[Any, ...] | None:
    """The word at **instruction** granularity -- the tokenisation ``d_instr`` uses.

    One symbol per unit of the arm's own language, so the response of two arms
    is read on the same scale: one ``Sigma_HG`` token for the Isal words
    (budgeted engines are parsed out of their string form and carry the
    ``("seed", label)`` prefix; the ordered-walk and ``wstar_rank`` arms already
    hand back exactly that sequence), one row per Levi node for
    ``nauty_cert_rows``, one fact token for the fact arms.

    ``nauty_cert`` is the one arm whose own word is finer than an instruction --
    it is a byte string -- and it keeps that granularity here, because its
    instruction-granular reading is a *different arm* (``nauty_cert_rows``),
    which the design puts on the table beside it precisely so the comparison is
    at matched tokenisation.

    Parameters
    ----------
    arm : str
        Registered arm name.
    word : Any
        What :func:`member_word` returned, or ``None``.
    augment : bool
        Whether the seed label is part of the compared sequence (true when
        either member of the comparison has more than one vertex label).

    Returns
    -------
    tuple or None
        The symbol sequence, or ``None`` when the word is missing.
    """
    if word is None:
        return None
    if arm in BUDGETED_ARMS:
        return pointer_symbols(word[0], word[1], augment=augment)
    return tuple(word)


def arm_distance(arm: str, wa: Any, wb: Any, *, augment: bool) -> int | None:
    """Distance between two arm words, or ``None`` when either is missing."""
    if wa is None or wb is None:
        return None
    if arm in BUDGETED_ARMS:
        left = pointer_symbols(wa[0], wa[1], augment=augment)
        right = pointer_symbols(wb[0], wb[1], augment=augment)
        return symbol_distance(left, right)
    return symbol_distance(wa, wb)


def _word_hash(arm: str, word: Any) -> str:
    if word is None:
        return ""
    payload = repr(word).encode("utf-8")
    return hashlib.sha1(payload, usedforsecurity=False).hexdigest()[:16]


def _nauty_hash(H: Any) -> str:
    from isalhg.iso_backends.canonical_order import nauty_certificate_bytes

    return hashlib.sha1(nauty_certificate_bytes(H), usedforsecurity=False).hexdigest()[:16]


def aut_order(H: Any) -> float:
    """``|Aut(H)|`` as the automorphism-group order of the coloured Levi graph.

    pynauty returns the order factored as ``grpsize1 * 10 ** grpsize2`` because
    it can overflow a C double; the product is taken as a float, which is exact
    up to the bucket boundaries this is used for.
    """
    import pynauty

    from isalhg.core.levi_reduction import to_levi
    from isalhg.iso_backends.canonical_order import _to_pynauty

    _gens, size1, size2, _orbits, _n_orbits = pynauty.autgrp(_to_pynauty(to_levi(H)))
    return float(size1) * (10.0**size2)


def aut_bucket(H: Any) -> str:
    """The ``|Aut|`` stratum of one member, or ``""`` when pynauty is unavailable.

    Symmetry, not size, is what censors the tie-complete engines (the 2026-09-05
    time-out probe), so every censoring figure is reported inside a stratum of
    this rather than pooled.
    """
    try:
        order = aut_order(H)
    except Exception as exc:  # noqa: BLE001 - a missing stratum is data, not a crash
        logger.debug("aut_order failed: %s", exc)
        return ""
    for bound, label in AUT_BUCKETS:
        if order < bound:
            return label
    return AUT_BUCKET_TOP


def _cached_aut_bucket(ctx: Mapping[str, Any], index: int, H: Any) -> str:
    """``aut_bucket(H)`` computed at most once per member and run."""
    cache: dict[int, str] = ctx["aut_cache"]
    if index not in cache:
        cache[index] = aut_bucket(H)
    return cache[index]


def _pair_k(H1: Any, H2: Any) -> int:
    from isalhg.core.canonical import required_k

    return max(required_k(H1), required_k(H2))


def _augment(H1: Any, H2: Any) -> bool:
    return max(H1.n_vertex_labels, H2.n_vertex_labels) > 1


# ---------------------------------------------------------------------------
# Measurements
# ---------------------------------------------------------------------------


def block_slice(size: int, block: int, n_blocks: int) -> range:
    """Even split of ``size`` items into ``n_blocks``; the index range of one block.

    Even, never fixed blocks with a ragged tail: the short remainder unit is
    exactly what bundling to the two-hour floor is meant to eliminate.

    Parameters
    ----------
    size : int
        Number of items.
    block : int
        Which block, ``0 <= block < n_blocks``.
    n_blocks : int
        How many blocks.

    Returns
    -------
    range
        The half-open index range of this block.
    """
    quotient, remainder = divmod(size, n_blocks)
    low = block * quotient + min(block, remainder)
    high = low + quotient + (1 if block < remainder else 0)
    return range(low, high)


def run_m3(unit: Unit, ctx: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """M3 (tokens and canonicalization time) plus the M0 per-member ingredients."""
    from isalhg.core.canonical import required_k
    from isalhg.core.sparse_hypergraph import permute

    collection = ctx["collection"]
    records = collection.records
    graphs = ctx["graphs"]
    roles = ctx["roles"]
    arms = ctx["arms"]
    budget = ctx["budget"]
    master = ctx["seed"]

    m3_rows: list[dict[str, Any]] = []
    m0_rows: list[dict[str, Any]] = []
    for index in block_slice(len(records), unit.block, unit.n_blocks):
        record = records[index]
        H = graphs[index]
        k = required_k(H)
        nauty = _nauty_hash(H)
        bucket = _cached_aut_bucket(ctx, index, H)
        rng = random.Random(master + index)
        order = list(range(record.n))
        rng.shuffle(order)
        sigma = {node: order[node] for node in range(record.n)}
        H_permuted = permute(H, sigma)
        roles_permuted = _permute_roles(roles[index], sigma)

        augment = H.n_vertex_labels > 1
        for arm in arms:
            word, secs, censored = member_word(arm, H, roles[index], k=k, budget=budget)
            other, _, censored_other = member_word(
                arm, H_permuted, roles_permuted, k=k, budget=budget
            )
            invariance_ok = ""
            if not censored and not censored_other and word is not None:
                invariance_ok = int(_word_hash(arm, word) == _word_hash(arm, other))
            instructions = instruction_symbols(arm, word, augment=augment)
            m3_rows.append(
                {
                    **ctx["stamp"],
                    "collection": collection.name,
                    "seed": master + index,
                    "member_id": record.kb_id,
                    "n": record.n,
                    "m": record.m,
                    "k": k,
                    "aut_bucket": bucket,
                    "arm": arm,
                    "tokens": word_tokens(arm, word),
                    "n_instr": 0 if instructions is None else len(instructions),
                    "secs": round(secs, 6),
                    "censored": int(censored),
                }
            )
            m0_rows.append(
                {
                    **ctx["stamp"],
                    "collection": collection.name,
                    "seed": master + index,
                    "member_id": record.kb_id,
                    "arm": arm,
                    "word_hash": _word_hash(arm, word),
                    "nauty_hash": nauty,
                    "invariance_ok": invariance_ok,
                    "censored": int(censored or censored_other),
                    "secs": round(secs, 6),
                }
            )
    return {"m3": m3_rows, "m0items": m0_rows}


def _permute_roles(roles: Any, sigma: Mapping[int, int]) -> Any:
    """Carry a roles map through a vertex permutation (edge ids are preserved)."""
    if roles is None:
        return None
    return {
        edge: {sigma[node]: role for node, role in mapping.items()}
        for edge, mapping in roles.items()
    }


def run_m1(unit: Unit, ctx: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """M1 -- the single-edit response of every arm on identical instances."""
    from isalhg.datasets.kb.ladders import EDIT_KINDS, single_edits

    collection = ctx["collection"]
    records = collection.records
    graphs = ctx["graphs"]
    roles = ctx["roles"]
    arms = ctx["arms"]
    budget = ctx["budget"]
    master = ctx["seed"]
    per_kind = int(ctx["config"].get("m1_edits_per_kind", 4))
    kinds = tuple(ctx["config"].get("m1_edit_kinds") or EDIT_KINDS)

    rows: list[dict[str, Any]] = []
    for index in block_slice(len(records), unit.block, unit.n_blocks):
        base = records[index]
        H_base = graphs[index]
        base_words: dict[tuple[str, int], tuple[Any, float, bool]] = {}
        base_ranks = _safe_ranks(H_base)
        bucket = _cached_aut_bucket(ctx, index, H_base)

        for kind in kinds:
            edited = single_edits(base, kind, per_kind, master + index, require_connected=True)
            for edit_idx, variant in enumerate(edited):
                H_edit = variant.to_hypergraph()
                k = _pair_k(H_base, H_edit)
                augment = _augment(H_base, H_edit)
                regime = int(bool(variant.meta.get("constant_set_preserved", False)))
                shift = _zero_shift(base, base_ranks, variant, H_edit)

                for arm in arms:
                    key = (arm, k)
                    if key not in base_words:
                        base_words[key] = member_word(arm, H_base, roles[index], k=k, budget=budget)
                    word_base, secs_base, censored_base = base_words[key]
                    word_edit, secs_edit, censored_edit = member_word(
                        arm, H_edit, None, k=k, budget=budget
                    )
                    censored = censored_base or censored_edit
                    distance = arm_distance(arm, word_base, word_edit, augment=augment)
                    instr_base = instruction_symbols(arm, word_base, augment=augment)
                    instr_edit = instruction_symbols(arm, word_edit, augment=augment)
                    d_instr = (
                        ""
                        if instr_base is None or instr_edit is None
                        else symbol_distance(instr_base, instr_edit)
                    )
                    rows.append(
                        {
                            **ctx["stamp"],
                            "collection": collection.name,
                            "seed": master + index,
                            "base_id": base.kb_id,
                            "edit_kind": kind,
                            "edit_idx": edit_idx,
                            "regime": regime,
                            "zero_shift": shift,
                            "aut_bucket": bucket,
                            "arm": arm,
                            "d_abs": "" if distance is None else distance,
                            "d_instr": d_instr,
                            "n_instr": 0 if instr_base is None else len(instr_base),
                            "len_base": word_tokens(arm, word_base),
                            "len_edit": word_tokens(arm, word_edit),
                            "secs_canon": round(secs_base + secs_edit, 6),
                            "censored": int(censored),
                        }
                    )
    return {"m1": rows}


def _safe_ranks(H: Any) -> tuple[int, ...] | None:
    from isalhg.iso_backends.canonical_order import canonical_ranks

    try:
        return canonical_ranks(H)
    except Exception as exc:  # noqa: BLE001 - a missing rank is data, not a crash
        logger.debug("canonical_ranks failed: %s", exc)
        return None


def _zero_shift(
    base: Any, base_ranks: tuple[int, ...] | None, edited: Any, H_edit: Any
) -> int | str:
    """1 when the canonical order of the surviving constants is unchanged.

    Empty when the record carries no external identities, since without them
    "the same constant" is not defined across the edit.
    """
    if base_ranks is None or base.constant_ids is None or edited.constant_ids is None:
        return ""
    edit_ranks = _safe_ranks(H_edit)
    if edit_ranks is None:
        return ""
    base_index = {identity: i for i, identity in enumerate(base.constant_ids)}
    edit_index = {identity: i for i, identity in enumerate(edited.constant_ids)}
    common = [identity for identity in base.constant_ids if identity in edit_index]
    if len(common) < 2:
        return 1
    ordered_base = sorted(common, key=lambda i: base_ranks[base_index[i]])
    ordered_edit = sorted(common, key=lambda i: edit_ranks[edit_index[i]])
    return int(ordered_base == ordered_edit)


def run_m2(unit: Unit, ctx: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """M2 -- distance against a known fact-level difference."""
    series = str(unit.extra.get("series", ""))
    if series == "natural":
        return {"m2": _m2_natural(unit, ctx)}
    return {"m2": _m2_ladders(unit, ctx)}


def _m2_natural(unit: Unit, ctx: dict[str, Any]) -> list[dict[str, Any]]:
    collection = ctx["collection"]
    index = {record.kb_id: i for i, record in enumerate(collection.records)}
    graphs = ctx["graphs"]
    roles = ctx["roles"]
    arms = ctx["arms"]
    budget = ctx["budget"]
    pairs = corpora_io.consecutive_pairs(collection)
    limit = ctx["config"].get("m2_natural_limit")
    if limit:
        pairs = pairs[: int(limit)]
    pairs = [pairs[i] for i in block_slice(len(pairs), unit.block, unit.n_blocks)]

    rows: list[dict[str, Any]] = []
    for pair in pairs:
        a_id, b_id = str(pair["a"]), str(pair["b"])
        if a_id not in index or b_id not in index:
            continue
        ia, ib = index[a_id], index[b_id]
        Ha, Hb = graphs[ia], graphs[ib]
        k = _pair_k(Ha, Hb)
        augment = _augment(Ha, Hb)
        for arm in arms:
            wa, secs_a, cen_a = member_word(arm, Ha, roles[ia], k=k, budget=budget)
            wb, secs_b, cen_b = member_word(arm, Hb, roles[ib], k=k, budget=budget)
            distance = arm_distance(arm, wa, wb, augment=augment)
            rows.append(
                {
                    **ctx["stamp"],
                    "collection": collection.name,
                    "seed": ctx["seed"],
                    "series": "natural",
                    "pair_id": f"{a_id}|{b_id}",
                    "delta": int(pair.get("delta", 0)),
                    "regime": int(bool(pair.get("constant_preserving", False))),
                    "arm": arm,
                    "d": "" if distance is None else distance,
                    "len_a": word_tokens(arm, wa),
                    "len_b": word_tokens(arm, wb),
                    "secs": round(secs_a + secs_b, 6),
                    "censored": int(cen_a or cen_b),
                }
            )
    return rows


def _m2_ladders(unit: Unit, ctx: dict[str, Any]) -> list[dict[str, Any]]:
    from isalhg.datasets.kb.ladders import constant_preserving_ladder, fact_distance

    collection = ctx["collection"]
    records = collection.records
    graphs = ctx["graphs"]
    roles = ctx["roles"]
    arms = ctx["arms"]
    budget = ctx["budget"]
    master = ctx["seed"]
    count = int(ctx["config"].get("m2_ladders_count", 1000))
    t_max = int(ctx["config"].get("m2_ladder_t_max", 5))

    rng = random.Random(master)
    chosen = sorted(rng.sample(range(len(records)), min(count, len(records))))
    chosen = [chosen[i] for i in block_slice(len(chosen), unit.block, unit.n_blocks)]

    rows: list[dict[str, Any]] = []
    for index in chosen:
        base = records[index]
        H_base = graphs[index]
        rungs = constant_preserving_ladder(base, t_max, master + index)
        base_words: dict[tuple[str, int], tuple[Any, float, bool]] = {}
        for rung in rungs:
            H_rung = rung.to_hypergraph()
            k = _pair_k(H_base, H_rung)
            augment = _augment(H_base, H_rung)
            delta = int(rung.meta.get("delta", fact_distance(base, rung)))
            for arm in arms:
                key = (arm, k)
                if key not in base_words:
                    base_words[key] = member_word(arm, H_base, roles[index], k=k, budget=budget)
                wa, secs_a, cen_a = base_words[key]
                wb, secs_b, cen_b = member_word(arm, H_rung, None, k=k, budget=budget)
                distance = arm_distance(arm, wa, wb, augment=augment)
                rows.append(
                    {
                        **ctx["stamp"],
                        "collection": collection.name,
                        "seed": master + index,
                        "series": "ladder",
                        "pair_id": f"{base.kb_id}|t{rung.meta.get('t', '')}",
                        "delta": delta,
                        "regime": 1,
                        "arm": arm,
                        "d": "" if distance is None else distance,
                        "len_a": word_tokens(arm, wa),
                        "len_b": word_tokens(arm, wb),
                        "secs": round(secs_a + secs_b, 6),
                        "censored": int(cen_a or cen_b),
                    }
                )
    return rows


def run_m4(unit: Unit, ctx: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """M4 -- each arm against ``nauty_cert`` on random pairs.

    The M1 half of M4 is not recomputed: ``rows_m1`` already carries
    ``nauty_cert`` as an arm on exactly those pairs, so the analyzer reads the
    correlation off it. This unit measures only the random-pair half.
    """
    collection = ctx["collection"]
    records = collection.records
    graphs = ctx["graphs"]
    roles = ctx["roles"]
    arms = ctx["arms"]
    budget = ctx["budget"]
    master = ctx["seed"]
    count = int(ctx["config"].get("m4_random_pairs", 1000))

    rng = random.Random(master + 991)
    size = len(records)
    if size < 2:
        return {"m4": []}
    sampled = [tuple(rng.sample(range(size), 2)) for _ in range(count)]
    block = block_slice(len(sampled), unit.block, unit.n_blocks)

    rows: list[dict[str, Any]] = []
    for pair_index in block:
        ia, ib = sampled[pair_index]
        Ha, Hb = graphs[ia], graphs[ib]
        k = _pair_k(Ha, Hb)
        augment = _augment(Ha, Hb)
        distances: dict[str, Any] = {}
        censored_flags: dict[str, bool] = {}
        for arm in arms:
            wa, _, cen_a = member_word(arm, Ha, roles[ia], k=k, budget=budget)
            wb, _, cen_b = member_word(arm, Hb, roles[ib], k=k, budget=budget)
            distances[arm] = arm_distance(arm, wa, wb, augment=augment)
            censored_flags[arm] = cen_a or cen_b
        reference = distances.get(CERT_ARM)
        for arm in arms:
            rows.append(
                {
                    **ctx["stamp"],
                    "collection": collection.name,
                    "seed": master + 991,
                    "series": "random",
                    "pair_id": f"{records[ia].kb_id}|{records[ib].kb_id}|{pair_index}",
                    "arm": arm,
                    "d": "" if distances[arm] is None else distances[arm],
                    "d_cert": "" if reference is None else reference,
                    "censored": int(censored_flags[arm]),
                }
            )
    return {"m4": rows}


RUNNERS = {"m3": run_m3, "m1": run_m1, "m2": run_m2, "m4": run_m4}
COLUMNS = {
    "m0items": COLUMNS_M0ITEMS,
    "m1": COLUMNS_M1,
    "m2": COLUMNS_M2,
    "m3": COLUMNS_M3,
    "m4": COLUMNS_M4,
}


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def corpora_root(
    results_root: Path, collection: str, data_root: Path | str | None = None
) -> Path | None:
    """Where the frozen collection lives -- the one rule, used by RQ1, RQ2 and RQ7.

    ``experiments.tkde.corpora`` reads ``<root>/corpora/<name>``, and its default
    root is the *results* root. That default is wrong on Picasso: the corpora are
    staged under ``$ISALHG_DATA_ROOT`` on FSCRATCH while results are written to
    HOME, and ``--out`` may point at a scratch directory holding no corpora at
    all. ``--data-root`` therefore names the directory that holds ``corpora/``
    explicitly; the remaining candidates are a convenience for local runs.

    Parameters
    ----------
    results_root : Path
        The run's ``--out`` root.
    collection : str
        Collection directory name.
    data_root : Path or str or None, optional
        Explicit root, tried first. This is what the workers pass.

    Returns
    -------
    Path or None
        A root such that ``<root>/corpora/<collection>/records.jsonl`` exists,
        or ``None`` when the collection is nowhere to be found.
    """
    import os

    candidates = (
        data_root,
        results_root,
        os.environ.get("ISALHG_RESULTS_ROOT"),
        os.environ.get("ISALHG_DATA_ROOT"),
        corpora_io.DEFAULT_RESULTS_ROOT,
    )
    for candidate in candidates:
        if candidate is None:
            continue
        root = Path(candidate)
        if (root / "corpora" / collection / "records.jsonl").is_file():
            return root
    return None


def experiment_name(config: Mapping[str, Any]) -> str:
    """The experiment this run belongs to: the config's ``experiment`` key, else the default."""
    return str(config.get("experiment") or EXPERIMENT)


def _stamp(experiment: str = EXPERIMENT) -> dict[str, Any]:
    from experiments.tkde.io import _cpu_model, _repo_provenance

    return {
        "rq": RQ_INDEX,
        "experiment": experiment,
        "git_sha": _repo_provenance()["git_sha"],
        "host_cpu": _cpu_model(),
    }


def _unit_context(
    unit: Unit,
    config: Mapping[str, Any],
    results_root: Path,
    data_root: Path | None = None,
) -> dict[str, Any]:
    root = corpora_root(results_root, unit.collection, data_root)
    if root is None:
        raise Rq1Error(
            f"no frozen collection {unit.collection!r}: looked under --data-root "
            f"{data_root}, {results_root}/corpora, $ISALHG_RESULTS_ROOT and "
            f"$ISALHG_DATA_ROOT"
        )
    collection = corpora_io.load_collection(unit.collection, root)
    limit = config.get("member_limit")
    if limit:
        collection = corpora_io.subset(
            collection,
            [record.kb_id for record in collection.records[: int(limit)]],
            name=collection.name,
        )
    roles = corpora_io.roles_maps(collection)
    has_roles = any(entry is not None for entry in roles)
    return {
        "collection": collection,
        "graphs": corpora_io.hypergraphs(collection),
        "roles": roles,
        "arms": arms_for(unit.collection, config.get("arms") or DEFAULT_ARMS, has_roles),
        "budget": float(config.get("pointer_budget_s", 60.0)),
        # G7's schedule, indexed: the campaign runs replication 0, and a local
        # or exploratory run selects another of the 27 without inventing a seed
        # outside the schedule. The index is part of the run tag, so two
        # replications never share a row file.
        "seed": seeds(RQ_INDEX)[int(config.get("seed_index", 0))],
        "config": config,
        "stamp": _stamp(experiment_name(config)),
        "aut_cache": {},
    }


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
    parser = argparse.ArgumentParser(prog="experiments.tkde.rq1", description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument(
        "--data-root",
        type=Path,
        default=None,
        help=(
            "Directory holding corpora/. On Picasso this is $ISALHG_DATA_ROOT "
            "(FSCRATCH); locally it is $ISALHG_RESULTS_ROOT, where corpora/ sits "
            "beside the results."
        ),
    )
    parser.add_argument("--shard", default=None, help="i/N: run shard i of N")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--count", action="store_true", help="print the shard count and exit")
    parser.add_argument("--list-units", action="store_true")
    parser.add_argument(
        "--start-cutoff-epoch",
        type=float,
        default=None,
        help=(
            "Unix time after which no further unit is STARTED. The first unit of "
            "a shard is exempt: without that exemption a shard whose start-up "
            "alone exceeds the cutoff defers its whole chunk, a resume pass "
            "re-derives the same chunk and defers it again, and the array "
            "livelocks. A deferred unit is never given a shortened budget."
        ),
    )
    return parser


def parse_shard(spec: str | None, n_units: int) -> tuple[int, int]:
    """Parse ``i/N``; the default is the single shard ``0/1``."""
    if not spec:
        return 0, 1
    try:
        index, total = (int(part) for part in spec.split("/", 1))
    except ValueError as exc:
        raise Rq1Error(f"--shard must look like i/N, got {spec!r}") from exc
    if total < 1 or not 0 <= index < total:
        raise Rq1Error(f"--shard {spec!r} is out of range for {n_units} units")
    return index, total


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
    # The experiment name is the config's: a second RQ1 experiment on the same
    # units (e.g. configs/rq1_rank.yaml, "addressing_rank") must land in its
    # own <RQ>/<experiment> directory — the one the SLURM worker stages and
    # copies back. With the constant, the 2026-09-07 rank run wrote its rows to
    # an unlinked "addressing" directory on node scratch and lost them.
    experiment = experiment_name(config)
    paths = RunPaths(root=results_root, rq=RQ_FOLDER, experiment=experiment)
    paths.ensure()

    shard, n_shards = parse_shard(args.shard, len(units))
    mine = units[shard::n_shards]
    tag = run_tag(config)
    logger.info(
        "RQ1: shard %d/%d -> %d of %d units (run tag %s)",
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
        "experiment": experiment,
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
    # Two writes on purpose. The experiment directory keeps the G6 six files
    # (last shard wins; every write is atomic, so a concurrent shard can never
    # leave a half file), and each shard also keeps its own copy under
    # _shards/<i>/ so no task's SLURM ids or unit list is overwritten by
    # another's.
    write_config(paths, record)
    write_manifest(paths, extra=extra)
    shard_paths = RunPaths(
        root=results_root, rq=RQ_FOLDER, experiment=f"{experiment}/_shards/{shard:03d}"
    )
    write_config(shard_paths, record)
    write_manifest(shard_paths, extra=extra)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
