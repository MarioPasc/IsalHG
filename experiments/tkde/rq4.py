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
from collections.abc import Collection, Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any

from experiments.tkde import corpora
from experiments.tkde.budget import (
    CPP_ENGINE_ARMS,
    encode_symbols,
    engine_word,
    guarded_budget_call,
    pointer_symbols,
)
from experiments.tkde.config import TkdeConfigError, load_yaml, results_root, seeds
from experiments.tkde.io import RunPaths, write_config, write_manifest, write_rows
from experiments.tkde.matrices import (
    MatrixCacheMissingError,
    deploy_stamps,
    load_arm_matrices,
    load_cached_matrix_censored,
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

#: DESIGN.md §5 Scores. The exact arms H4a is about are ``fact_rank``,
#: ``nauty_cert`` and the two Isal instruction words (both complete invariants:
#: Theorem C for the ordered walk, the tie-complete argument for ``wstar_rank``);
#: the last two are the mandatory naive floors.
DEFAULT_ARMS: tuple[str, ...] = (
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
EXACT_ARMS: tuple[str, ...] = ("fact_rank", "isal_ow_struct", "wstar_rank", "nauty_cert")
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

#: Arms whose distance is a token-level Levenshtein over a per-member word.
#: These are served from precomputed representations, never through
#: ``pairwise``: every ``pairwise`` call re-derives the canonical labelling on
#: BOTH sides, so one anomaly row costs ``2 N`` canonicalizations where ``N + 1``
#: suffice. On ``wstar_orbit`` -- p99 43 s per ndc_classes member -- that is the
#: difference between a unit that finishes and one that runs past its wall
#: (measured: job 2265368, 30 min on a single 1,311-member unit).
WORD_ARMS: tuple[str, ...] = ("fact_rank", "isal_ow_struct", "wstar_rank", "wstar_orbit")

#: ``arm -> engine selector of experiments.tkde.budget.engine_word``. These are
#: the Isal instruction-word arms, and the members of :data:`WORD_ARMS` whose
#: representation is unbounded from inside Python.
ENGINE_ARMS: dict[str, str] = {"wstar_rank": "rank", "wstar_orbit": "orbit"}

#: Per-member wall-clock budget for one word-arm representation. Matches the
#: matrices job's ``fingerprint_budget_s``, so a member this run censors is a
#: member that run would have censored too.
DEFAULT_MEMBER_BUDGET_S = 60.0

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
    "n_censored_members",
    "n_censored_anomaly",
    "n_censored_clean",
    "censor_rate_anomaly",
    "censor_rate_clean",
    "n_censored_word_anomaly",
    "n_censored_word_clean",
    "word_censored_arms",
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
# Precomputed word representations (the word arms' fast path)
# ---------------------------------------------------------------------------


def _plain_word(arm: str, H: SparseHypergraph) -> tuple[Any, ...]:
    """Return the token word of a word arm that is not an Isal engine arm.

    Parameters
    ----------
    arm : str
        A member of :data:`WORD_ARMS` outside :data:`ENGINE_ARMS`.
    H : SparseHypergraph

    Returns
    -------
    tuple
        The token sequence the arm's ``pairwise`` measures.
    """
    if arm == "fact_rank":
        from isalhg.metric_space.distances.fact_levenshtein import fact_word

        return tuple(fact_word(H))
    from isalhg.metric_space.registry import get_distance

    word = get_distance(arm).fingerprint(H)
    if word is None:
        raise TkdeConfigError(f"arm {arm!r} has no standalone fingerprint; it is not a word arm")
    return tuple(word)


def member_word(
    arm: str,
    H: SparseHypergraph,
    *,
    augment: bool,
    budget_s: float,
) -> tuple[Any, ...] | None:
    """Return one member's word for ``arm``, or None when it does not finish.

    The word is computed in a forked child under ``budget_s``, exactly as the
    matrices job screens its members: neither engine returns to the interpreter
    on time-out, so a budget enforced from inside Python does not bound them.
    ``cpp_engine`` is set from :data:`experiments.tkde.budget.CPP_ENGINE_ARMS`
    because it declares what the child does -- reaching the C++ canonicalizer
    from a poisoned parent hangs, and reporting that hang as a censoring would
    be a fiction; the fact-word and ordered-walk children are unaffected and
    must not be guarded, or work that would have succeeded is refused.

    ``k`` is the member's own ``required_k``. Neither Isal engine word changes
    with ``k`` above the widest edge -- the walk never names a pointer index it
    does not need -- so this is the same value the pair maximum ``pairwise``
    resolves would produce.

    Parameters
    ----------
    arm : str
        A member of :data:`WORD_ARMS`.
    H : SparseHypergraph
        A connected knowledge base.
    augment : bool
        Whether the corpus vertex vocabulary is non-trivial, which is when the
        ``("seed", label)`` prefix is part of the fingerprint (Corollary A).
        Constant across a knowledge-base collection, since ``n_vertex_labels``
        is the collection's declared type alphabet.
    budget_s : float
        Per-member wall-clock budget.

    Returns
    -------
    tuple or None
        The token sequence, or None when the child was censored or raised.
    """
    if arm in ENGINE_ARMS:
        from isalhg.core.canonical import required_k

        result = engine_word(H, required_k(H), budget_s, engine=ENGINE_ARMS[arm])
        if not result.ok:
            return None
        word, seed_label = result.value
        return pointer_symbols(word, seed_label, augment=augment)

    result = guarded_budget_call(_plain_word, (arm, H), budget_s, cpp_engine=arm in CPP_ENGINE_ARMS)
    return None if not result.ok else tuple(result.value)


def member_words(
    arm: str,
    items: Sequence[SparseHypergraph],
    *,
    augment: bool,
    budget_s: float,
    memo: dict[str, tuple[Any, ...] | None] | None = None,
    keys: Sequence[str] | None = None,
) -> list[tuple[Any, ...] | None]:
    """Return one word per item, memoised by member id when one is supplied.

    Parameters
    ----------
    arm : str
        A member of :data:`WORD_ARMS`.
    items : Sequence[SparseHypergraph]
    augment : bool
        See :func:`member_word`.
    budget_s : float
        Per-member wall-clock budget.
    memo : dict or None, optional
        ``{member id: word or None}``, filled in place. Pristine members are
        the same objects in every unit of a sub-collection, so their words are
        computed once per process rather than once per unit.
    keys : Sequence[str] or None, optional
        Memo key per item; required when ``memo`` is given.

    Returns
    -------
    list
        One entry per item; ``None`` where the word did not finish.

    Raises
    ------
    TkdeConfigError
        If ``memo`` is given without ``keys``, or ``keys`` does not align.
    """
    if memo is not None and (keys is None or len(keys) != len(items)):
        raise TkdeConfigError("member_words: `memo` requires a `keys` aligned with `items`")

    words: list[tuple[Any, ...] | None] = []
    for index, H in enumerate(items):
        if memo is None:
            words.append(member_word(arm, H, augment=augment, budget_s=budget_s))
            continue
        key = keys[index]  # type: ignore[index]
        if key not in memo:
            memo[key] = member_word(arm, H, augment=augment, budget_s=budget_s)
        words.append(memo[key])
    return words


def word_rows(
    words: Sequence[tuple[Any, ...]],
    positions: Sequence[int],
    *,
    n_jobs: int,
) -> list[list[float]]:
    """Return ``d(word[p], word[x])`` for every ``p`` in ``positions``.

    One shared private alphabet for the whole population, then a single
    ``rapidfuzz.process.cdist`` call -- the encode-once pattern every
    amortizing arm's own ``matrix`` uses. Levenshtein is invariant under any
    bijective relabelling of the symbols, so the shared alphabet returns
    exactly the per-pair values ``pairwise`` returns.

    Parameters
    ----------
    words : Sequence[tuple]
        One token sequence per member, in population order.
    positions : Sequence[int]
        Local indices of the anomalies.
    n_jobs : int
        ``workers`` for the ``cdist`` call.

    Returns
    -------
    list[list[float]]
        One row per position, each of length ``len(words)``.
    """
    import numpy as np
    from rapidfuzz import process
    from rapidfuzz.distance import Levenshtein

    encoded = encode_symbols(words)
    queries = [encoded[position] for position in positions]
    matrix = process.cdist(
        queries, encoded, scorer=Levenshtein.distance, workers=n_jobs, dtype=np.float64
    )
    return [[float(value) for value in row] for row in np.asarray(matrix)]


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
    words: Mapping[str, Sequence[tuple[Any, ...]]] | None,
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

    Every :data:`WORD_ARMS` arm is served from precomputed words -- one
    encoding per member, then one token-Levenshtein pass -- rather than through
    ``pairwise``, which re-derives the canonical labelling on both sides of
    every call. The values are identical; the cost is ``N + 1``
    canonicalizations per row instead of ``2 N``.

    Parameters
    ----------
    items : Sequence[SparseHypergraph]
        The modified collection, anomalies already substituted.
    words : Mapping or None
        ``{arm: words aligned with items}`` for the word arms, or None to route
        every arm through ``pairwise``. Every entry must be complete: a member
        whose word did not finish is dropped from the population upstream, not
        carried here as a hole.
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
    result: dict[tuple[int, str], list[float]] = {}
    served = {arm: words[arm] for arm in arms if words is not None and arm in words}

    for arm, arm_words in served.items():
        try:
            served_rows = word_rows(arm_words, positions, n_jobs=n_jobs)
        except Exception as exc:  # noqa: BLE001 -- censor the arm, do not end the shard
            logger.warning("arm %s failed on the word path: %r", arm, exc)
            continue
        for position, served_row in zip(positions, served_rows, strict=True):
            result[(position, arm)] = served_row

    pairwise_arms = [arm for arm in arms if arm not in served]
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


@dataclasses.dataclass(frozen=True)
class Census:
    """The members one unit lost to the matrices job's per-member budget.

    L15's third clause bites here: a corrupted member carries one more fact
    than its clean original, so it is marginally likelier to censor, and an AUC
    computed on a set whose positives were preferentially removed is not the
    AUC claimed. The rate is therefore reported split by label -- the members
    the seed selected for corruption against the ones it left clean -- and the
    corruption type is already a column of every row, so the analyzer can group
    by it without further plumbing.

    A member can also be lost *here*, to the per-member word budget of a
    :data:`WORD_ARMS` arm. The corpus members were screened once by the
    matrices job, but an anomaly is a hypergraph that job never saw, so its
    canonicalization can overrun where its clean original did not -- and L15's
    third clause bites again, in the same direction. Those losses are counted
    separately in ``n_censored_word_*`` (and rolled into the totals) so a reader
    can tell an upstream censoring from one this run made; the arms that caused
    them are named in ``word_censored_arms``.
    """

    kept: tuple[int, ...]
    n_censored: int
    n_censored_anomaly: int
    n_censored_clean: int
    rate_anomaly: float | str
    rate_clean: float | str
    n_censored_word_anomaly: int = 0
    n_censored_word_clean: int = 0
    word_censored_arms: str = ""


def common_positions(
    member_ids: Sequence[str],
    loaded: Mapping[str, tuple[Any, Mapping[str, int]]],
    anomaly_positions: Collection[int],
) -> Census:
    """Restrict a subcollection to the members every loaded arm completed.

    This is the RQ1 ``restrict_to_common_units`` rule one level down: the unit
    is the member, and a cross-arm statistic computed on different member sets
    is not answering the same question for each arm. Arms with no matrix at all
    are already absent from ``loaded`` and so drop out of the requirement rather
    than emptying the intersection.

    Parameters
    ----------
    member_ids : Sequence[str]
        The subcollection's members, in local order.
    loaded : Mapping
        ``arm -> (matrix, {member_id: row})`` as returned by :func:`arm_matrices`.
    anomaly_positions : Collection[int]
        Local positions the seed selected for corruption, for the label split.

    Returns
    -------
    Census
        The surviving local positions and the censoring counts.
    """
    kept = tuple(
        position
        for position, kb_id in enumerate(member_ids)
        if all(kb_id in rows for _, rows in loaded.values())
    )
    survivors = set(kept)
    censored = [position for position in range(len(member_ids)) if position not in survivors]
    chosen = set(anomaly_positions)
    n_anomaly = sum(1 for position in censored if position in chosen)
    n_clean = len(censored) - n_anomaly
    n_chosen = len(chosen)
    n_unchosen = len(member_ids) - n_chosen
    return Census(
        kept=kept,
        n_censored=len(censored),
        n_censored_anomaly=n_anomaly,
        n_censored_clean=n_clean,
        rate_anomaly=round(n_anomaly / n_chosen, 6) if n_chosen else "",
        rate_clean=round(n_clean / n_unchosen, 6) if n_unchosen else "",
    )


def fold_word_census(
    census: Census,
    lost: Collection[int],
    anomaly_positions: Collection[int],
    arms: Collection[str],
    *,
    n_chosen: int,
    n_members: int,
) -> Census:
    """Return ``census`` with the members lost to the word budget folded in.

    A member whose word does not finish is dropped from the population for
    **every** arm, not only for the arm that lost it: this is the same
    common-member rule :func:`common_positions` enforces one level up, and a
    cross-arm AUC computed on different member sets is not answering the same
    question for each arm.

    Parameters
    ----------
    census : Census
        The matrix-censoring census, whose ``kept`` is in the parent's local
        indexing.
    lost : Collection[int]
        Positions *within* ``census.kept`` whose word did not finish.
    anomaly_positions : Collection[int]
        Parent-local positions the seed selected for corruption.
    arms : Collection[str]
        The word arms that lost at least one member.
    n_chosen : int
        Selected-for-corruption members of the whole sub-collection, the
        denominator of ``rate_anomaly``.
    n_members : int
        Members of the whole sub-collection.

    Returns
    -------
    Census
        A new census restricted to the survivors, with the totals updated.
    """
    dropped = set(lost)
    if not dropped:
        return census
    chosen = set(anomaly_positions)
    kept = tuple(position for local, position in enumerate(census.kept) if local not in dropped)
    lost_positions = [position for local, position in enumerate(census.kept) if local in dropped]
    n_anomaly = sum(1 for position in lost_positions if position in chosen)
    n_clean = len(lost_positions) - n_anomaly
    total_anomaly = census.n_censored_anomaly + n_anomaly
    total_clean = census.n_censored_clean + n_clean
    n_unchosen = n_members - n_chosen
    return dataclasses.replace(
        census,
        kept=kept,
        n_censored=census.n_censored + len(lost_positions),
        n_censored_anomaly=total_anomaly,
        n_censored_clean=total_clean,
        rate_anomaly=round(total_anomaly / n_chosen, 6) if n_chosen else "",
        rate_clean=round(total_clean / n_unchosen, 6) if n_unchosen else "",
        n_censored_word_anomaly=census.n_censored_word_anomaly + n_anomaly,
        n_censored_word_clean=census.n_censored_word_clean + n_clean,
        word_censored_arms=",".join(sorted(arms)),
    )


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


def _restrict(
    records: Sequence[Any],
    modified: Sequence[SparseHypergraph],
    realised: Sequence[int],
    keep: Sequence[int],
) -> tuple[list[Any], list[SparseHypergraph], list[int]]:
    """Restrict a unit's population to ``keep``, remapping the anomaly indices."""
    remap = {position: local for local, position in enumerate(keep)}
    return (
        [records[position] for position in keep],
        [modified[position] for position in keep],
        [remap[position] for position in realised if position in remap],
    )


def _restrict_words(
    columns: Mapping[str, Sequence[tuple[Any, ...] | None]],
    keep: Sequence[int],
) -> dict[str, list[tuple[Any, ...]]]:
    """Restrict each arm's word column to ``keep``, refusing to drop a hole.

    A hole that survived into the scored population would shorten one column
    and silently misalign it with the hypergraphs, so it is an error rather
    than a filter: every kept member has a word under every word arm.

    Raises
    ------
    TkdeConfigError
        If a kept position carries no word.
    """
    restricted: dict[str, list[tuple[Any, ...]]] = {}
    for arm, column in columns.items():
        words: list[tuple[Any, ...]] = []
        for local in keep:
            word = column[local]
            if word is None:
                raise TkdeConfigError(
                    f"arm {arm!r}: member at position {local} has no word but was kept"
                )
            words.append(word)
        restricted[arm] = words
    return restricted


def unit_words(
    arms: Sequence[str],
    modified: Sequence[SparseHypergraph],
    member_ids: Sequence[str],
    realised: Sequence[int],
    *,
    budget_s: float,
    cache: dict[str, Any],
    cache_scope: str,
) -> tuple[dict[str, list[tuple[Any, ...] | None]], list[int], set[str]]:
    """Return each word arm's per-member words, and the members none finished.

    Pristine members are the same hypergraphs in every unit of a
    sub-collection, so their words are memoised per process and the budgeted
    fork is paid once each. The corrupted members are new objects the matrices
    job never saw, so their words are computed fresh every unit and are the
    place an anomaly can be lost.

    Parameters
    ----------
    arms : Sequence[str]
        The :data:`WORD_ARMS` members this unit scores.
    modified : Sequence[SparseHypergraph]
        The population, anomalies already substituted.
    member_ids : Sequence[str]
        Member id per position, the memo key for the pristine members.
    realised : Sequence[int]
        Positions holding a corrupted member.
    budget_s : float
        Per-member wall-clock budget.
    cache : dict
        The runner's per-process cache.
    cache_scope : str
        Sub-collection name, so two sub-collections of one parent do not share
        a memo keyed only by member id.

    Returns
    -------
    tuple
        ``(words, lost, lost_arms)``: ``words`` maps arm to one token sequence
        per position, ``None`` where the word did not finish; ``lost`` are the
        positions holding such a hole under any arm; ``lost_arms`` names those
        arms.
    """
    augment = any(H.n_vertex_labels > 1 for H in modified)
    corrupted = set(realised)
    words: dict[str, list[tuple[Any, ...] | None]] = {}
    lost: set[int] = set()
    lost_arms: set[str] = set()

    for arm in arms:
        memo: dict[str, tuple[Any, ...] | None] = cache.setdefault(
            f"words::{arm}::{cache_scope}", {}
        )
        column: list[tuple[Any, ...] | None] = []
        for position, H in enumerate(modified):
            if position in corrupted:
                column.append(member_word(arm, H, augment=augment, budget_s=budget_s))
                continue
            key = member_ids[position]
            if key not in memo:
                memo[key] = member_word(arm, H, augment=augment, budget_s=budget_s)
            column.append(memo[key])
        missing = {position for position, word in enumerate(column) if word is None}
        if missing:
            lost |= missing
            lost_arms.add(arm)
        words[arm] = column

    # The columns are handed back at full length, holes included, so the caller
    # restricts words, records and hypergraphs in one pass and they stay
    # aligned; after that restriction no hole remains.
    return words, sorted(lost), lost_arms


def run_unit(
    unit: Unit,
    *,
    matrices_root: Path,
    corpora_root: Path | str | None,
    arms: Sequence[str],
    n_jobs: int,
    collection_cache: dict[str, Any],
    member_budget_s: float = DEFAULT_MEMBER_BUDGET_S,
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
    member_budget_s : float, optional
        Per-member wall-clock budget for the :data:`WORD_ARMS` representations.
        A member whose word overruns it is dropped and counted (L15), never
        scored against a stale or zero row.

    Returns
    -------
    dict[str, list[dict]]
        Tables ``auc`` and ``anomalies``.
    """
    import numpy as np

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

    loaded = load_arm_matrices(
        matrices_root, sub.collection, arms, parent_ids, cache=collection_cache
    )
    # An arm with no cached matrix is censored whatever its rows say, so its
    # rows are never computed: on wstar_orbit that is 2 N canonicalizations per
    # anomaly spent on a number that is discarded.
    scored_arms = [arm for arm in arms if arm in loaded]

    census = common_positions([r.kb_id for r in records], loaded, chosen)
    if census.n_censored:
        # Every cross-arm number is computed on the members all the loaded arms
        # completed, so the arms are answering the same question.
        records, modified, realised = _restrict(records, modified, realised, census.kept)
        n = len(census.kept)
        logger.warning(
            "unit %d (%s): %d members censored (%d selected for corruption, %d clean); "
            "scoring the %d that every arm completed",
            unit.index,
            unit.unit_id,
            census.n_censored,
            census.n_censored_anomaly,
            census.n_censored_clean,
            n,
        )

    columns, lost, lost_arms = unit_words(
        [arm for arm in scored_arms if arm in WORD_ARMS],
        modified,
        [record.kb_id for record in records],
        realised,
        budget_s=member_budget_s,
        cache=collection_cache,
        cache_scope=sub.name,
    )
    keep = list(range(n))
    if lost:
        census = fold_word_census(
            census, lost, chosen, lost_arms, n_chosen=len(chosen), n_members=len(indices)
        )
        dropped = set(lost)
        keep = [local for local in keep if local not in dropped]
        records, modified, realised = _restrict(records, modified, realised, keep)
        n = len(keep)
        logger.warning(
            "unit %d (%s): %d member(s) lost to the %.0f s word budget of %s "
            "(%d selected for corruption, %d clean); scoring the remaining %d",
            unit.index,
            unit.unit_id,
            len(lost),
            member_budget_s,
            ",".join(sorted(lost_arms)),
            census.n_censored_word_anomaly,
            census.n_censored_word_clean,
            n,
        )

    words = _restrict_words(columns, keep)

    is_anomaly = np.zeros(n, dtype=bool)
    is_anomaly[realised] = True

    if not realised:
        logger.warning(
            "unit %d (%s): every corrupted member was censored; no AUC",
            unit.index,
            unit.unit_id,
        )
        for arm in arms:
            for score in ("knn", "lof"):
                tables["auc"].append(
                    _auc_row(unit, arm, score, float("nan"), n, 0, n_skipped, 0.0, 1, census=census)
                )
        return tables

    kept_ids = [record.kb_id for record in records]

    started = time.perf_counter()
    rows = anomaly_rows(modified, words, realised, scored_arms, n_jobs=n_jobs)
    secs_rows = time.perf_counter() - started

    for arm in arms:
        arm_started = time.perf_counter()
        if arm not in loaded:
            for score in ("knn", "lof"):
                tables["auc"].append(
                    _auc_row(
                        unit,
                        arm,
                        score,
                        float("nan"),
                        n,
                        len(realised),
                        n_skipped,
                        0.0,
                        1,
                        census=census,
                    )
                )
            continue
        full, row_of = loaded[arm]
        # Align by member id: a censored arm's rows are its survivors, not the
        # frozen order, so the parent positions would index the wrong members.
        arm_rows = [row_of[kb_id] for kb_id in kept_ids]
        base = np.asarray(full[np.ix_(arm_rows, arm_rows)], dtype=np.float64)
        D = _score_matrix(base, rows, realised, arm)
        if D is None:
            logger.error("unit %d arm %s: anomaly rows incomplete; censored", unit.index, arm)
            for score in ("knn", "lof"):
                tables["auc"].append(
                    _auc_row(
                        unit,
                        arm,
                        score,
                        float("nan"),
                        n,
                        len(realised),
                        n_skipped,
                        0.0,
                        1,
                        census=census,
                    )
                )
            continue

        for score, k, fn in (("knn", KNN_K, knn_score), ("lof", LOF_K, lof_score)):
            if n <= k + 1:
                # Too few members for this neighbourhood size; censor rather
                # than report a score computed on a degenerate neighbourhood.
                tables["auc"].append(
                    _auc_row(
                        unit,
                        arm,
                        score,
                        float("nan"),
                        n,
                        len(realised),
                        n_skipped,
                        0.0,
                        1,
                        census=census,
                    )
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
                    census=census,
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
    *,
    census: Census | None = None,
) -> dict[str, Any]:
    """Return one ``rows_auc`` row, carrying this unit's censoring census (L15)."""
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
        "n_censored_members": 0 if census is None else census.n_censored,
        "n_censored_anomaly": 0 if census is None else census.n_censored_anomaly,
        "n_censored_clean": 0 if census is None else census.n_censored_clean,
        "censor_rate_anomaly": "" if census is None else census.rate_anomaly,
        "censor_rate_clean": "" if census is None else census.rate_clean,
        "n_censored_word_anomaly": 0 if census is None else census.n_censored_word_anomaly,
        "n_censored_word_clean": 0 if census is None else census.n_censored_word_clean,
        "word_censored_arms": "" if census is None else census.word_censored_arms,
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
                load_cached_matrix_censored(matrices_root, name, arm, ids)
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
    member_budget_s: float = DEFAULT_MEMBER_BUDGET_S,
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
    member_budget_s : float, optional
        Per-member word budget, passed through to :func:`run_unit`.

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
        member_budget_s=member_budget_s,
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
        ("fact_rank", "isal_ow_struct", "nauty_cert", "size_l1")
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
    member_budget_s = float(config.get("member_budget_s") or DEFAULT_MEMBER_BUDGET_S)

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
                member_budget_s=member_budget_s,
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
            member_budget_s=member_budget_s,
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
            "member_budget_s": member_budget_s,
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
