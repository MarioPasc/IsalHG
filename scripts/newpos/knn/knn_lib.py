"""Classification (kNN) and clustering (k-medoids) of KBs by distance: the KNN_2026-10-15 library.

Pre-registration: ``docs/article/D_ART3/experiments/KNN_2026-10-15/LOG.md`` (binding).

Design B (partial copies). A class is one real member, the *source*, which never
enters the evaluated set. Its members are ``c`` partial copies, each obtained by
``r`` successive single down-edits that are *pendant*: delete a fact holding a
constant found in no other fact, or remove a constant from the only fact it
occurs in. Every intermediate and final copy is connected and keeps at least
three facts. Copies of one source are pairwise non-isomorphic; a draw that is
isomorphic to an accepted copy is rejected and counted, and only when the nauty
certificate *and* the ordered-walk fingerprint (the two exact keys) agree. In the
empirical-mix condition a step is interior with a calibrated probability, so that
the share of pendant steps tracks C8's measured share of pendant one-edit pairs.

Design A (real lineages). A class is one NDC node; its members are the node's
KBs in different quarterly windows (every lineage with at least three versions).
In leave-one-out kNN a version's candidates are the versions of *other windows*
only.

Scoring. kNN ties are resolved by expectation: the ``k`` nearest neighbours are
the members strictly closer than the ``k``-th distance plus a uniformly random
subset of the tie block at that distance, and a vote tie is broken uniformly at
random. The probability of every predicted label is computed exactly, which
gives the expected accuracy and the expected confusion matrix (macro-F1 is read
off the expected confusion). k-medoids is PAM (BUILD + SWAP) from the
``kmedoids`` package on a seeded random permutation of the items, so that
index-order tie-breaking is never aligned with the classes; it is scored by ARI
and NMI against the classes.
"""

from __future__ import annotations

import json
import logging
import math
import time
import zlib
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypeAlias

import numpy as np
from numpy.typing import NDArray

from isalhg.datasets.kb.base import Fact, KBCollection, KBRecord, compact

logger = logging.getLogger(__name__)

D_ROOT = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE")
OUT_ROOT = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/KNN_2026-10-15")

OURS = "isal_ow_struct"
COMPETITORS: tuple[str, ...] = (
    "nauty_cert",
    "nauty_cert_rows",
    "fact_rank",
    "wl_l1",
    "netlsd",
    "hpd_jsd",
    "bipartite_ged_assign",
    "bipartite_ged_path",
    "degree_seq_l1",
    "size_l1",
)
ARMS: tuple[str, ...] = (OURS, *COMPETITORS)
ABLATION = "wstar_orbit"
COLLECTIONS: tuple[str, ...] = ("wd50k66", "wd50k100", "ndc_classes", "ndc_substances")
LINEAGE_COLLECTIONS: tuple[str, ...] = ("ndc_classes", "ndc_substances")

#: C8's measured share of pendant one-edit pairs per collection (LOG.md §2, Design B).
PENDANT_SHARE: dict[str, float] = {
    "wd50k66": 0.90,
    "wd50k100": 0.75,
    "ndc_classes": 0.74,
    "ndc_substances": 0.56,
}

M_MIN = 3
KNN_KS: tuple[int, ...] = (1, 5)
FLOORS: tuple[str, ...] = ("degree_seq_l1", "size_l1")

FloatMatrix: TypeAlias = NDArray[np.float64]


class KnnExperimentError(Exception):
    """Root of the failures of this experiment library."""


class CopyGenerationError(KnnExperimentError):
    """A source cannot yield the requested copies."""


# --------------------------------------------------------------------------- seeds


def cell_seed(base_seed: int, *parts: object) -> int:
    """A stable 63-bit seed derived from ``base_seed`` and the cell's name parts.

    Parameters
    ----------
    base_seed : int
        The replicate seed (0, 1, 2, ... in the seed loop).
    *parts : object
        Cell coordinates, e.g. ``("B", "wd50k66", "pendant")``; their ``str``
        forms enter a CRC32, so the derivation does not depend on Python's
        randomised ``hash``.

    Returns
    -------
    int
        The seed, reproducible across processes and machines.
    """
    tag = zlib.crc32("|".join(str(p) for p in parts).encode())
    ss = np.random.SeedSequence([int(base_seed), int(tag)])
    return int(ss.generate_state(1, dtype=np.uint64)[0] >> np.uint64(1))


# --------------------------------------------------------------------------- edits


@dataclass(frozen=True)
class Removal:
    """One valid single down-edit and the compacted record it produces.

    Attributes
    ----------
    kind : str
        ``"delete_fact"`` or ``"remove_constant"``.
    pendant : bool
        True iff the edit changes the constant inventory (a constant leaves).
    fact_index : int
        Index of the edited fact in the parent's ``facts``.
    constant : int or None
        The removed constant (parent numbering) for ``remove_constant``.
    result : KBRecord
        The compacted, connected result with at least ``M_MIN`` facts.
    """

    kind: str
    pendant: bool
    fact_index: int
    constant: int | None
    result: KBRecord


def _candidate_edits(
    facts: Sequence[Fact],
) -> Iterable[tuple[str, bool, int, int | None, list[Fact]]]:
    """Yield ``(kind, pendant, fact index, constant, facts after)`` before validation."""
    count = Counter(a for _, args in facts for a in args)
    fact_set = set(facts)
    for i, (_, args) in enumerate(facts):
        if len(facts) - 1 >= M_MIN:
            pendant = any(count[a] == 1 for a in args)
            yield "delete_fact", pendant, i, None, list(facts[:i]) + list(facts[i + 1 :])
    for i, (pred, args) in enumerate(facts):
        if len(args) < 3:
            continue
        for a in args:
            new: Fact = (pred, tuple(x for x in args if x != a))
            if new in fact_set:
                # Equal to deleting fact i, which is enumerated above.
                continue
            yield (
                "remove_constant",
                count[a] == 1,
                i,
                a,
                list(facts[:i]) + [new] + list(facts[i + 1 :]),
            )


def removals(record: KBRecord) -> list[Removal]:
    """Every valid single down-edit of ``record``.

    Valid means: the result, after dropping constants left in no fact, is
    connected, keeps at least ``M_MIN`` facts, has only facts of arity >= 2 and
    no duplicate fact. Roles are not carried (no arm reads them).

    Parameters
    ----------
    record : KBRecord
        The record to edit.

    Returns
    -------
    list[Removal]
        Pendant and interior removals, in enumeration order.

    Raises
    ------
    KnnExperimentError
        If the pendant flag disagrees with the compacted constant count.
    """
    meta = {"n_types": record.n_types, "n_preds": record.n_preds}
    out: list[Removal] = []
    for kind, pendant, i, const, facts in _candidate_edits(list(record.facts)):
        rec = compact(f"{record.kb_id}-", list(record.types), facts, meta=meta)
        if rec is None or rec.m < M_MIN or rec.m != len(facts):
            continue
        if pendant != (rec.n < record.n):
            raise KnnExperimentError(
                f"{record.kb_id}: pendant flag {pendant} but n {record.n} -> {rec.n}"
            )
        out.append(Removal(kind, pendant, i, const, rec))
    return out


def has_interior_removal(record: KBRecord) -> bool:
    """True iff ``record`` admits at least one valid interior removal."""
    return any(not rem.pendant for rem in removals(record))


def has_pendant_removal(record: KBRecord) -> bool:
    """True iff ``record`` admits at least one valid pendant removal."""
    return any(rem.pendant for rem in removals(record))


# --------------------------------------------------------------------------- iso keys


class IsoKeys:
    """The two exact isomorphism keys of a record, memoised by structure.

    The nauty certificate of the coloured incidence graph and the ordered-walk
    fingerprint ``(root type, w°)`` are both complete invariants; the experiment
    treats two records as isomorphic only when both keys agree, and counts the
    pairs on which they disagree (expected zero).

    Parameters
    ----------
    n_types, n_preds : int
        Collection-scoped vocabulary sizes used to build every hypergraph.
    """

    def __init__(self, n_types: int, n_preds: int) -> None:
        from isalhg.iso_backends.isal_ordered import ordered_fingerprint
        from isalhg.metric_space.registry import get_distance

        self.n_types = n_types
        self.n_preds = n_preds
        self._cert = get_distance("nauty_cert")
        self._ordered = ordered_fingerprint
        self._memo: dict[Any, tuple[Any, Any]] = {}

    def __call__(self, record: KBRecord) -> tuple[Any, Any]:
        """Return ``(nauty certificate, ordered-walk fingerprint)`` of ``record``."""
        key = record.key()
        hit = self._memo.get(key)
        if hit is not None:
            return hit
        H = record.to_hypergraph(n_types=self.n_types, n_preds=self.n_preds)
        root, word = self._ordered(H)
        value = (self._cert.fingerprint(H), (int(root), word))
        self._memo[key] = value
        return value


# --------------------------------------------------------------------------- copies


@dataclass
class CopyStats:
    """Counters of one source's copy draws at one ``r``."""

    draws: int = 0
    dead_ends: int = 0
    iso_rejected: int = 0
    key_disagreements: int = 0
    steps_pendant: int = 0
    steps_interior: int = 0
    steps_fallback: int = 0

    def add(self, other: CopyStats) -> None:
        """Accumulate ``other`` into this counter."""
        for name in self.__dataclass_fields__:
            setattr(self, name, getattr(self, name) + getattr(other, name))


class RemovalCache:
    """Memoise :func:`removals` by record structure (draws revisit states)."""

    def __init__(self, limit: int = 20_000) -> None:
        self._memo: dict[Any, list[Removal]] = {}
        self._limit = limit

    def __call__(self, record: KBRecord) -> list[Removal]:
        """Return the removals of ``record``."""
        key = record.key()
        hit = self._memo.get(key)
        if hit is None:
            if len(self._memo) >= self._limit:
                self._memo.clear()
            hit = removals(record)
            self._memo[key] = hit
        return hit


def _choose_step(
    opts: Sequence[Removal], rng: np.random.Generator, q_interior: float, stats: CopyStats
) -> Removal | None:
    """Draw one step: interior with probability ``q_interior`` when one exists."""
    pend = [o for o in opts if o.pendant]
    inter = [o for o in opts if not o.pendant]
    want_interior = q_interior > 0.0 and bool(inter) and rng.random() < q_interior
    pool = inter if want_interior else pend
    if not pool:
        if q_interior <= 0.0 or not inter:
            return None
        # Mix condition with no pendant option left: the step takes the other kind.
        pool = inter
        stats.steps_fallback += 1
    choice = pool[int(rng.integers(len(pool)))]
    if choice.pendant:
        stats.steps_pendant += 1
    else:
        stats.steps_interior += 1
    return choice


def sample_copy(
    source: KBRecord,
    r: int,
    rng: np.random.Generator,
    *,
    q_interior: float = 0.0,
    cache: RemovalCache | None = None,
    stats: CopyStats | None = None,
) -> tuple[KBRecord, list[tuple[str, bool]]] | None:
    """One copy of ``source`` after ``r`` successive removals.

    Parameters
    ----------
    source : KBRecord
        The real member.
    r : int
        Number of removals (>= 1).
    rng : numpy.random.Generator
        Randomness of the draw.
    q_interior : float, optional
        Probability that a step is interior when an interior removal exists.
        ``0`` (Design B) draws pendant removals only.
    cache : RemovalCache or None, optional
        Removal memo.
    stats : CopyStats or None, optional
        Counter updated in place.

    Returns
    -------
    tuple or None
        ``(copy, [(kind, pendant) per step])``, or ``None`` at a dead end.
    """
    cache = cache or RemovalCache()
    stats = stats if stats is not None else CopyStats()
    state = source
    steps: list[tuple[str, bool]] = []
    for _ in range(r):
        step = _choose_step(cache(state), rng, q_interior, stats)
        if step is None:
            return None
        steps.append((step.kind, step.pendant))
        state = step.result
    return state, steps


def make_copies(
    source: KBRecord,
    r: int,
    c: int,
    rng: np.random.Generator,
    keys: IsoKeys,
    *,
    q_interior: float = 0.0,
    max_draws: int | None = None,
    cache: RemovalCache | None = None,
) -> tuple[list[KBRecord], CopyStats]:
    """Draw ``c`` pairwise non-isomorphic copies of ``source`` at ``r`` removals.

    A draw isomorphic to an accepted copy (both exact keys agree on the same
    copy) is rejected and counted; when the keys disagree the draw is kept and
    the disagreement counted.

    Parameters
    ----------
    source : KBRecord
        The real member.
    r : int
        Removals per copy.
    c : int
        Copies wanted.
    rng : numpy.random.Generator
        Randomness of the draws.
    keys : IsoKeys
        The exact isomorphism keys.
    q_interior : float, optional
        Interior-step probability (see :func:`sample_copy`).
    max_draws : int or None, optional
        Draw budget; default ``40 * c``.
    cache : RemovalCache or None, optional
        Removal memo.

    Returns
    -------
    tuple[list[KBRecord], CopyStats]
        The copies (fewer than ``c`` when the budget ran out) and the counters.
    """
    budget = max_draws if max_draws is not None else 40 * c
    stats = CopyStats()
    cache = cache or RemovalCache()
    copies: list[KBRecord] = []
    by_cert: dict[Any, int] = {}
    by_ow: dict[Any, int] = {}
    while len(copies) < c and stats.draws < budget:
        stats.draws += 1
        drawn = sample_copy(source, r, rng, q_interior=q_interior, cache=cache, stats=stats)
        if drawn is None:
            stats.dead_ends += 1
            continue
        rec, steps = drawn
        cert, ow = keys(rec)
        j_cert, j_ow = by_cert.get(cert), by_ow.get(ow)
        if j_cert is not None and j_cert == j_ow:
            stats.iso_rejected += 1
            continue
        if (j_cert is None) != (j_ow is None) or j_cert != j_ow:
            stats.key_disagreements += 1
        idx = len(copies)
        by_cert.setdefault(cert, idx)
        by_ow.setdefault(ow, idx)
        meta = dict(rec.meta)
        meta.update(
            {
                "source_id": source.kb_id,
                "r": r,
                "steps": [[k, bool(p)] for k, p in steps],
                "n_pendant_steps": sum(1 for _, p in steps if p),
            }
        )
        copies.append(
            KBRecord(
                kb_id=f"{source.kb_id}~r{r}c{idx}",
                n=rec.n,
                types=rec.types,
                facts=rec.facts,
                label=source.kb_id,
                meta=meta,
            )
        )
    return copies, stats


@dataclass
class SourceDraw:
    """The sources of one Design-B replicate and their copies at every ``r``."""

    sources: list[KBRecord]
    copies: dict[int, list[list[KBRecord]]]
    stats: dict[int, CopyStats]
    n_tried: int
    n_skipped_iso_source: int
    n_ineligible: int
    shortfall: int
    secs: float
    q_interior: float
    extra: dict[str, Any] = field(default_factory=dict)


def select_sources(
    col: KBCollection,
    S: int,
    rs: Sequence[int],
    c: int,
    rng: np.random.Generator,
    keys: IsoKeys,
    *,
    q_interior: float = 0.0,
    max_draws: int | None = None,
) -> SourceDraw:
    """Draw ``S`` sources uniformly among the members that yield ``c`` copies at every ``r``.

    Members are visited in a seeded random order; a member is accepted iff it is
    not isomorphic to an accepted source and :func:`make_copies` returns ``c``
    copies at each ``r`` in ``rs``. The accepted sources are therefore a
    uniform draw from the eligible members, and the same sources serve every
    ``r`` (the curves over ``r`` are paired).

    Parameters
    ----------
    col : KBCollection
        The frozen collection.
    S : int
        Sources wanted.
    rs : Sequence[int]
        Removal counts the sources must support.
    c : int
        Copies per source.
    rng : numpy.random.Generator
        Randomness of the visit order and of the copies.
    keys : IsoKeys
        The exact isomorphism keys.
    q_interior : float, optional
        Interior-step probability (0 for Design B).
    max_draws : int or None, optional
        Per-``(source, r)`` draw budget.

    Returns
    -------
    SourceDraw
        Sources, copies and counters.
    """
    t0 = time.perf_counter()
    order = rng.permutation(len(col.records))
    sources: list[KBRecord] = []
    copies: dict[int, list[list[KBRecord]]] = {r: [] for r in rs}
    stats: dict[int, CopyStats] = {r: CopyStats() for r in rs}
    used_certs: set[Any] = set()
    n_tried = n_iso = n_inel = 0
    for idx in order:
        if len(sources) >= S:
            break
        member = col.records[int(idx)]
        n_tried += 1
        cert, _ = keys(member)
        if cert in used_certs:
            n_iso += 1
            continue
        cache = RemovalCache()
        trial: dict[int, list[KBRecord]] = {}
        trial_stats: dict[int, CopyStats] = {}
        ok = True
        for r in rs:
            got, st = make_copies(
                member, r, c, rng, keys, q_interior=q_interior, max_draws=max_draws, cache=cache
            )
            trial_stats[r] = st
            if len(got) < c:
                ok = False
                break
            trial[r] = got
        if not ok:
            n_inel += 1
            continue
        used_certs.add(cert)
        sources.append(member)
        for r in rs:
            copies[r].append(trial[r])
            stats[r].add(trial_stats[r])
    return SourceDraw(
        sources=sources,
        copies=copies,
        stats=stats,
        n_tried=n_tried,
        n_skipped_iso_source=n_iso,
        n_ineligible=n_inel,
        shortfall=max(0, S - len(sources)),
        secs=time.perf_counter() - t0,
        q_interior=q_interior,
    )


def interior_availability(col: KBCollection, *, limit: int | None = None) -> dict[str, Any]:
    """Share of members with a pendant removal that also admit an interior one.

    Calibrates the mix condition: a step is drawn interior with probability
    ``q = min(1, (1 - p) / a)`` when an interior removal exists, where ``p`` is
    C8's pendant share and ``a`` this availability, so that the expected share
    of interior steps is ``1 - p`` despite the members (stars) that admit none.

    Parameters
    ----------
    col : KBCollection
        The collection.
    limit : int or None, optional
        Scan only the first ``limit`` members (tests).

    Returns
    -------
    dict
        ``n_with_pendant``, ``n_with_both``, ``availability``.
    """
    n_p = n_both = 0
    for rec in col.records[:limit]:
        rem = removals(rec)
        if any(x.pendant for x in rem):
            n_p += 1
            n_both += int(any(not x.pendant for x in rem))
    return {
        "n_with_pendant": n_p,
        "n_with_both": n_both,
        "availability": n_both / n_p if n_p else 0.0,
    }


def mix_q(pendant_share: float, availability: float) -> float:
    """Interior-step probability of the mix condition (see :func:`interior_availability`)."""
    if availability <= 0.0:
        return 0.0
    return float(min(1.0, (1.0 - pendant_share) / availability))


# --------------------------------------------------------------------------- lineages


def lineages(col: KBCollection, min_versions: int = 3) -> dict[str, list[int]]:
    """Map each NDC node with at least ``min_versions`` versions to its member indices.

    Parameters
    ----------
    col : KBCollection
        An NDC time-series collection (``meta["class_id"]``, ``meta["window"]``).
    min_versions : int, optional
        Minimum number of versions (windows) of a lineage.

    Returns
    -------
    dict[str, list[int]]
        Lineage id (the node) -> member indices ordered by window.

    Raises
    ------
    KnnExperimentError
        If a lineage has two versions in one window.
    """
    by: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for i, rec in enumerate(col.records):
        by[str(rec.meta["class_id"])].append((int(rec.meta["window"]), i))
    out: dict[str, list[int]] = {}
    for node, rows in sorted(by.items(), key=lambda kv: int(kv[0])):
        windows = [w for w, _ in rows]
        if len(set(windows)) != len(windows):
            raise KnnExperimentError(f"{col.name}: lineage {node} repeats a window")
        if len(rows) >= min_versions:
            out[node] = [i for _, i in sorted(rows)]
    return out


def sample_lineages(lin: dict[str, list[int]], L: int, rng: np.random.Generator) -> list[str]:
    """A uniform sample of ``L`` lineage ids (all of them when ``L`` exceeds the count)."""
    ids = sorted(lin, key=int)
    if len(ids) <= L:
        return ids
    pick = rng.choice(len(ids), size=L, replace=False)
    return [ids[int(i)] for i in sorted(pick)]


# --------------------------------------------------------------------------- matrices


def hypergraphs(records: Sequence[KBRecord], n_types: int, n_preds: int) -> list[Any]:
    """Labelled hypergraphs of ``records`` under the collection's vocabulary sizes."""
    return [r.to_hypergraph(n_types=n_types, n_preds=n_preds) for r in records]


def build_matrices(
    records: Sequence[KBRecord],
    arms: Sequence[str],
    *,
    n_types: int,
    n_preds: int,
    n_jobs: int = 1,
) -> tuple[dict[str, FloatMatrix], dict[str, float]]:
    """Distance matrix of every arm on ``records`` and its wall-clock.

    Parameters
    ----------
    records : Sequence[KBRecord]
        The evaluated items.
    arms : Sequence[str]
        Registered distance names. ``wstar_orbit`` is refused here: its C++
        engine poisons forked children and needs a per-member budget, so it is
        built by :func:`build_ablation_matrix` in a separate process.
    n_types, n_preds : int
        Collection-scoped vocabulary sizes.
    n_jobs : int, optional
        Worker processes for the pairwise arms.

    Returns
    -------
    tuple[dict, dict]
        ``{arm: float64 matrix}`` and ``{arm: seconds}``.

    Raises
    ------
    KnnExperimentError
        If ``wstar_orbit`` is requested.
    """
    from isalhg.metric_space.toolkit.matrix import build_matrix

    if ABLATION in arms:
        raise KnnExperimentError("build the wstar_orbit ablation with build_ablation_matrix")
    hs = hypergraphs(records, n_types, n_preds)
    ids = [r.kb_id for r in records]
    mats: dict[str, FloatMatrix] = {}
    secs: dict[str, float] = {}
    # The forking pairwise arms run first: nothing before them touches a C++ engine.
    ordered = sorted(arms, key=lambda a: (not a.startswith("bipartite"), arms.index(a)))
    for arm in ordered:
        t0 = time.perf_counter()
        M = build_matrix(hs, arm, member_ids=ids, n_jobs=n_jobs)
        secs[arm] = time.perf_counter() - t0
        mats[arm] = np.asarray(M, dtype=np.float64)
    return {a: mats[a] for a in arms}, {a: secs[a] for a in arms}


def _ablation_child(
    payload: tuple[list[dict[str, Any]], int, int, float],
    conn: Any,  # noqa: ANN401 - a multiprocessing Connection
) -> None:  # pragma: no cover - runs in a spawned process
    from experiments.tkde.budget import arm_fingerprint_screen
    from isalhg.metric_space.toolkit.matrix import build_matrix_censored

    rows, n_types, n_preds, budget = payload
    recs = [KBRecord.from_json(row) for row in rows]
    hs = hypergraphs(recs, n_types, n_preds)
    ids = [r.kb_id for r in recs]
    t0 = time.perf_counter()
    M, cens = build_matrix_censored(
        hs, ABLATION, member_ids=ids, fingerprint_screen=arm_fingerprint_screen(ABLATION, budget)
    )
    conn.send((np.asarray(M, dtype=np.float64), list(cens.member_ids), time.perf_counter() - t0))
    conn.close()


def build_ablation_matrix(
    records: Sequence[KBRecord], *, n_types: int, n_preds: int, budget_s: float = 60.0
) -> tuple[FloatMatrix, int, float]:
    """The ``wstar_orbit`` matrix in a spawned child, censored members at ``inf``.

    Parameters
    ----------
    records : Sequence[KBRecord]
        The evaluated items.
    n_types, n_preds : int
        Vocabulary sizes.
    budget_s : float, optional
        Per-member canonicalisation budget (the campaign's 60 s).

    Returns
    -------
    tuple
        ``(N x N matrix with inf rows/columns for censored members, n censored, seconds)``.
    """
    import multiprocessing as mp

    ctx = mp.get_context("spawn")
    parent, child = ctx.Pipe(duplex=False)
    rows = [r.to_json() for r in records]
    proc = ctx.Process(target=_ablation_child, args=((rows, n_types, n_preds, budget_s), child))
    proc.start()
    M_kept, kept_ids, secs = parent.recv()
    proc.join()
    pos = {r.kb_id: i for i, r in enumerate(records)}
    keep = np.array([pos[i] for i in kept_ids], dtype=np.int64)
    full = np.full((len(records), len(records)), np.inf)
    full[np.ix_(keep, keep)] = M_kept
    np.fill_diagonal(full, 0.0)
    return full, len(records) - len(keep), float(secs)


# --------------------------------------------------------------------------- kNN


def _others_dp(profiles: Sequence[tuple[int, int]], m: int) -> dict[tuple[int, int, int], int]:
    """Weights of ``(draws used u, max count M, classes at M t)`` over the given classes.

    Each class ``i`` has ``a_i`` neighbours strictly closer than the k-th
    distance and ``n_i`` members in the tie block; drawing ``x_i`` of the block
    has weight ``C(n_i, x_i)``. Classes ending at count 0 never matter.
    """
    states: dict[tuple[int, int, int], int] = {(0, 0, 0): 1}
    for a_i, n_i in profiles:
        nxt: dict[tuple[int, int, int], int] = defaultdict(int)
        for (u, M, t), w in states.items():
            for x in range(0, min(n_i, m - u) + 1):
                f = a_i + x
                wx = w * math.comb(n_i, x)
                if f == 0:
                    key = (u + x, M, t)
                elif f > M:
                    key = (u + x, f, 1)
                elif f == M:
                    key = (u + x, M, t + 1)
                else:
                    key = (u + x, M, t)
                nxt[key] += wx
        states = nxt
    return states


def knn_label_probs(
    d: NDArray[Any], labels: NDArray[np.int64], k: int, n_classes: int
) -> FloatMatrix:
    """Exact probability of every predicted label of one kNN query.

    The neighbour set is the candidates strictly closer than the ``k``-th
    smallest distance plus ``k - b`` drawn uniformly from the tie block at that
    distance; the prediction is the plurality label, a vote tie broken
    uniformly at random. Non-finite distances are a block at ``+inf``.

    Parameters
    ----------
    d : ndarray
        Distances from the query to its candidates.
    labels : ndarray of int
        Class code of each candidate, in ``range(n_classes)``.
    k : int
        Neighbours (capped at the number of candidates).
    n_classes : int
        Number of classes.

    Returns
    -------
    ndarray
        ``(n_classes,)`` probabilities summing to one (zeros with no candidate).
    """
    probs = np.zeros(n_classes)
    if len(d) == 0:
        return probs
    d = np.where(np.isnan(d), np.inf, np.asarray(d, dtype=np.float64))
    k = min(k, len(d))
    dk = np.partition(d, k - 1)[k - 1]
    strict = d < dk
    block = d == dk
    b, T = int(strict.sum()), int(block.sum())
    m = k - b
    n_blk = np.bincount(labels[block], minlength=n_classes)
    if k == 1:
        return n_blk / T
    a_str = np.bincount(labels[strict], minlength=n_classes)
    cand = np.flatnonzero((a_str + n_blk) > 0)
    prof = {int(i): (int(a_str[i]), int(n_blk[i])) for i in cand}
    total = math.comb(T, m)
    by_profile: dict[tuple[int, int], list[int]] = defaultdict(list)
    for i, p in prof.items():
        by_profile[p].append(i)
    for (a_f, n_f), members in by_profile.items():
        rest = [prof[i] for i in cand if i != members[0]]
        states = _others_dp(rest, m)
        win = 0.0
        for x in range(0, min(n_f, m) + 1):
            f = a_f + x
            if f == 0:
                continue
            wx = math.comb(n_f, x)
            for (u, M, t), w in states.items():
                if u != m - x:
                    continue
                if f > M:
                    win += wx * w
                elif f == M:
                    win += wx * w / (t + 1)
        probs[members] = win / total
    return probs


def loo_knn_probs(
    D: FloatMatrix,
    codes: NDArray[np.int64],
    k: int,
    candidate_mask: NDArray[np.bool_] | None = None,
) -> FloatMatrix:
    """Leave-one-out kNN label distributions of every item.

    Parameters
    ----------
    D : ndarray
        ``(N, N)`` distances.
    codes : ndarray of int
        Class code per item.
    k : int
        Neighbours.
    candidate_mask : ndarray of bool or None, optional
        ``(N, N)``; ``mask[q, j]`` admits ``j`` as a candidate of ``q``. The
        diagonal is always excluded.

    Returns
    -------
    ndarray
        ``(N, n_classes)``; row ``q`` is the distribution of ``q``'s prediction.
    """
    N = D.shape[0]
    L = int(codes.max()) + 1 if N else 0
    out = np.zeros((N, L))
    for q in range(N):
        ok = np.ones(N, dtype=bool) if candidate_mask is None else candidate_mask[q].copy()
        ok[q] = False
        out[q] = knn_label_probs(D[q, ok], codes[ok], k, L)
    return out


def expected_accuracy(P: FloatMatrix, codes: NDArray[np.int64]) -> float:
    """Mean probability of the true label (expected accuracy)."""
    return float(P[np.arange(len(codes)), codes].mean()) if len(codes) else float("nan")


def expected_macro_f1(P: FloatMatrix, codes: NDArray[np.int64]) -> float:
    """Macro-F1 of the expected confusion matrix, over the classes present.

    ``TP_l = sum_{q in l} P_q(l)``, ``FP_l = sum_{q not in l} P_q(l)``,
    ``FN_l = |l| - TP_l``; F1 per class is ``2TP / (2TP + FP + FN)``. This is
    the F1 of the expected confusion, not the expectation of F1 over tie
    draws; the two coincide when no query has a tie.
    """
    present = np.unique(codes)
    f1 = []
    for lab in present:
        in_l = codes == lab
        tp = P[in_l, lab].sum()
        fp = P[~in_l, lab].sum()
        fn = in_l.sum() - tp
        denom = 2 * tp + fp + fn
        f1.append(2 * tp / denom if denom > 0 else 0.0)
    return float(np.mean(f1))


# --------------------------------------------------------------------------- k-medoids


def finite_for_clustering(D: FloatMatrix) -> FloatMatrix:
    """Replace non-finite distances by ``10 * (max finite + 1)`` (censored = far)."""
    out = np.array(D, dtype=np.float64)
    bad = ~np.isfinite(out)
    if bad.any():
        out[bad] = 10.0 * (float(out[~bad].max(initial=0.0)) + 1.0)
    return out


def pam(D: FloatMatrix, k: int, seed: int, *, max_iter: int = 1000) -> dict[str, Any]:
    """PAM (BUILD + SWAP) on a seeded random permutation of the items.

    Parameters
    ----------
    D : ndarray
        ``(N, N)`` distances (non-finite entries are pushed far away).
    k : int
        Number of medoids.
    seed : int
        Permutation seed.
    max_iter : int, optional
        SWAP iteration cap; the result reports whether it was reached.

    Returns
    -------
    dict
        ``labels`` (cluster per item, original order), ``medoids`` (item
        indices), ``loss``, ``n_iter``, ``n_swap``, ``hit_max_iter``.
    """
    import kmedoids

    N = D.shape[0]
    perm = np.random.default_rng(seed).permutation(N)
    Dp = finite_for_clustering(D)[np.ix_(perm, perm)]
    res = kmedoids.pam(Dp, int(k), max_iter=max_iter, init="build")
    labels = np.empty(N, dtype=np.int64)
    labels[perm] = np.asarray(res.labels, dtype=np.int64)
    return {
        "labels": labels,
        "medoids": perm[np.asarray(res.medoids, dtype=np.int64)],
        "loss": float(res.loss),
        "n_iter": int(res.n_iter),
        "n_swap": int(res.n_swap),
        "hit_max_iter": bool(int(res.n_iter) >= max_iter),
    }


def medoid_certificates(
    D: FloatMatrix, labels: NDArray[np.int64], medoids: NDArray[np.int64]
) -> dict[str, Any]:
    """Certified ratio ``cost(M) / LB`` of every PAM cluster's medoid (Prop. 6.1).

    For a cluster ``K_1..K_N`` (``N >= 2``) with medoid ``M``:
    ``cost(M) = sum_i d(M, K_i)`` and ``LB = sum_{i<j} d(K_i, K_j) / (N - 1)``;
    for a metric ``LB <= OPT`` and the cluster's own 1-medoid satisfies
    ``cost <= (2 - 2/N) LB``. The PAM medoid need not be its cluster's
    1-medoid, so both are recorded, and a ratio above ``2 - 2/N`` (possible
    for a non-metric, or for a PAM medoid that is not the 1-medoid) is counted.

    Parameters
    ----------
    D : ndarray
        ``(N, N)`` distances (non-finite entries pushed far, as for PAM).
    labels : ndarray of int
        PAM cluster index per item, aligned with ``medoids``.
    medoids : ndarray of int
        Item index of each cluster's medoid.

    Returns
    -------
    dict
        ``clusters`` (per cluster: size, cost, lb, ratio, bound, the
        1-medoid's ratio, ``pam_medoid_is_1medoid``), ``ratio_median``,
        ``ratio_max``, ``ratio_1medoid_max``, ``n_singletons``, ``n_lb_zero``,
        ``n_over_bound`` (PAM medoid) and ``n_1medoid_over_bound``.
    """
    Df = finite_for_clustering(D)
    rows: list[dict[str, Any]] = []
    n_single = n_zero = 0
    for c, m in enumerate(medoids.tolist()):
        members = np.flatnonzero(labels == c)
        N = len(members)
        if N < 2:
            n_single += 1
            continue
        sub = Df[np.ix_(members, members)]
        lb = float(sub[np.triu_indices(N, 1)].sum() / (N - 1))
        costs = sub.sum(axis=1)
        cost = float(Df[m, members].sum())
        if lb <= 0.0:
            n_zero += 1
            continue
        bound = 2.0 - 2.0 / N
        rows.append(
            {
                "size": int(N),
                "cost": cost,
                "lb": lb,
                "ratio": cost / lb,
                "bound": bound,
                "ratio_1medoid": float(costs.min()) / lb,
                "pam_medoid_is_1medoid": bool(cost <= float(costs.min()) + 1e-9),
            }
        )
    ratios = np.array([r["ratio"] for r in rows])
    r1 = np.array([r["ratio_1medoid"] for r in rows])
    eps = 1e-9
    return {
        "clusters": rows,
        "ratio_median": float(np.median(ratios)) if len(rows) else None,
        "ratio_max": float(ratios.max()) if len(rows) else None,
        "ratio_1medoid_max": float(r1.max()) if len(rows) else None,
        "n_certified": len(rows),
        "n_singletons": n_single,
        "n_lb_zero": n_zero,
        "n_over_bound": int(sum(r["ratio"] > r["bound"] + eps for r in rows)),
        "n_1medoid_over_bound": int(sum(r["ratio_1medoid"] > r["bound"] + eps for r in rows)),
        "n_pam_medoid_not_1medoid": int(sum(not r["pam_medoid_is_1medoid"] for r in rows)),
    }


def brute_force_kmedoids(D: FloatMatrix, k: int) -> float:
    """Exact k-medoids loss by enumeration (tiny inputs only)."""
    from itertools import combinations

    N = D.shape[0]
    return float(min(D[:, list(c)].min(axis=1).sum() for c in combinations(range(N), k)))


# --------------------------------------------------------------------------- evaluation


def zero_pair_census(D: FloatMatrix, iso_class: NDArray[np.int64]) -> dict[str, int]:
    """Off-diagonal zero distances, split into isomorphic pairs and false zeros."""
    iu, ju = np.triu_indices(D.shape[0], 1)
    zero = D[iu, ju] == 0
    same = iso_class[iu] == iso_class[ju]
    return {
        "zero_pairs": int(zero.sum()),
        "false_zeros": int((zero & ~same).sum()),
        "iso_pairs_nonzero": int((~zero & same).sum()),
    }


def evaluate_arm(
    D: FloatMatrix,
    codes: NDArray[np.int64],
    *,
    k_clusters: int,
    pam_seed: int,
    iso_class: NDArray[np.int64],
    candidate_mask: NDArray[np.bool_] | None = None,
    cluster: bool = True,
) -> dict[str, Any]:
    """kNN and k-medoids scores of one arm's matrix.

    Parameters
    ----------
    D : ndarray
        ``(N, N)`` distances of the evaluated items.
    codes : ndarray of int
        Class code per item.
    k_clusters : int
        PAM's ``k`` (the number of classes).
    pam_seed : int
        Seed of PAM's item permutation.
    iso_class : ndarray of int
        Isomorphism class per item (for the zero-distance census).
    candidate_mask : ndarray of bool or None, optional
        kNN candidate restriction (Design A: other windows only).
    cluster : bool, optional
        Run PAM (skipped for the deterministic all-lineage kNN reference).

    Returns
    -------
    dict
        ``acc1``, ``acc5``, ``f1_1``, ``f1_5``, ``ari``, ``nmi``, PAM details
        (with the number of distinct classes among the medoids), the zero
        census, ``n_nonfinite`` and ``secs_eval``; ``_p_correct1`` /
        ``_p_correct5`` hold the per-query probability of a correct
        prediction (for :func:`ceiling_census`; not meant for the JSON).
    """
    from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

    t0 = time.perf_counter()
    res: dict[str, Any] = {"n_nonfinite": int((~np.isfinite(D)).sum())}
    for k in KNN_KS:
        P = loo_knn_probs(D, codes, k, candidate_mask)
        res[f"acc{k}"] = expected_accuracy(P, codes)
        res[f"f1_{k}"] = expected_macro_f1(P, codes)
        res[f"_p_correct{k}"] = P[np.arange(len(codes)), codes]
    if cluster:
        cl = pam(D, k_clusters, pam_seed)
        res["ari"] = float(adjusted_rand_score(codes, cl["labels"]))
        res["nmi"] = float(normalized_mutual_info_score(codes, cl["labels"]))
        res["pam"] = {k: v for k, v in cl.items() if k not in ("labels", "medoids")}
        res["medoid_ids_idx"] = [int(x) for x in cl["medoids"]]
        res["medoid_classes_distinct"] = int(len(set(codes[cl["medoids"]].tolist())))
        res["certified"] = medoid_certificates(D, cl["labels"], cl["medoids"])
    res.update(zero_pair_census(D, iso_class))
    res["secs_eval"] = time.perf_counter() - t0
    return res


def ceiling_census(p_correct: dict[str, NDArray[np.float64]]) -> dict[str, Any]:
    """How easy a cell is for the main arms (the word and the ten competitors).

    Parameters
    ----------
    p_correct : dict[str, ndarray]
        Per arm, the per-query probability that the 1-NN prediction is correct.

    Returns
    -------
    dict
        ``all_arms_correct`` (share of queries every arm gets right with
        certainty) and ``all_nonfloor_correct`` (the same without the two
        floors, whose ties make certainty rare), ``min_arm_p_correct_mean``
        (mean over queries of the smallest per-arm probability),
        ``word_right_some_competitor_wrong`` and
        ``word_wrong_some_competitor_right`` (certainty read as ``p == 1``),
        the paired split against the best competitor by 1-NN accuracy
        (``best_competitor``, ``word_only_vs_best``, ``best_only_vs_best``:
        expected shares of queries one gets right and the other wrong, under
        independent tie draws), and ``n_arms_acc1_ge_0.9``.
    """
    arms = [a for a in ARMS if a in p_correct]
    if not arms:
        return {}
    M = np.vstack([p_correct[a] for a in arms])
    comp = [i for i, a in enumerate(arms) if a != OURS]
    nonfloor = [i for i, a in enumerate(arms) if a not in FLOORS]
    out: dict[str, Any] = {
        "arms": arms,
        "all_arms_correct": float((M == 1.0).all(axis=0).mean()),
        "all_nonfloor_correct": float((M[nonfloor] == 1.0).all(axis=0).mean()),
        "min_arm_p_correct_mean": float(M.min(axis=0).mean()),
        "n_arms_acc1_ge_0.9": int((M.mean(axis=1) >= 0.9).sum()),
    }
    if OURS in arms and comp:
        w = M[arms.index(OURS)]
        out["word_right_some_competitor_wrong"] = float(
            ((w == 1.0) & (M[comp] < 1.0).any(axis=0)).mean()
        )
        out["word_wrong_some_competitor_right"] = float(
            ((w < 1.0) & (M[comp] == 1.0).any(axis=0)).mean()
        )
        b = max(comp, key=lambda i: M[i].mean())
        out["best_competitor"] = arms[b]
        out["word_only_vs_best"] = float((w * (1.0 - M[b])).mean())
        out["best_only_vs_best"] = float(((1.0 - w) * M[b]).mean())
    return out


def exact_arm_ceiling(
    iso_class: NDArray[np.int64],
    codes: NDArray[np.int64],
    candidate_mask: NDArray[np.bool_] | None = None,
) -> float:
    """Highest 1-NN accuracy any complete invariant can reach on these items.

    A complete invariant puts a query at distance 0 from exactly its
    isomorphic candidates. When a query has such candidates, its 1-NN is drawn
    from them, so its expected accuracy is at most the share of them in its
    own class; otherwise it is at most 1. The mean over queries bounds the
    1-NN accuracy of every exact arm from above.

    Parameters
    ----------
    iso_class, codes : ndarray of int
        Isomorphism class and class label per item.
    candidate_mask : ndarray of bool or None, optional
        kNN candidate restriction, as in :func:`loo_knn_probs`.

    Returns
    -------
    float
        The ceiling.
    """
    N = len(codes)
    vals = np.ones(N)
    for q in range(N):
        ok = np.ones(N, dtype=bool) if candidate_mask is None else candidate_mask[q].copy()
        ok[q] = False
        iso = ok & (iso_class == iso_class[q])
        if iso.any():
            vals[q] = float((codes[iso] == codes[q]).mean())
    return float(vals.mean()) if N else float("nan")


def iso_classes(records: Sequence[KBRecord], keys: IsoKeys) -> tuple[NDArray[np.int64], int]:
    """Isomorphism class per record (both keys) and the number of key disagreements."""
    pairs = [keys(r) for r in records]
    by_cert: dict[Any, int] = {}
    by_ow: dict[Any, int] = {}
    out = np.empty(len(records), dtype=np.int64)
    disagreements = 0
    for i, (cert, ow) in enumerate(pairs):
        c1 = by_cert.setdefault(cert, len(by_cert))
        c2 = by_ow.setdefault(ow, len(by_ow))
        out[i] = c1
        if c1 != c2:
            disagreements += 1
    if len(by_cert) != len(by_ow):
        disagreements += abs(len(by_cert) - len(by_ow))
    return out, disagreements


def cross_class_iso(iso_class: NDArray[np.int64], codes: NDArray[np.int64]) -> dict[str, int]:
    """Items whose isomorphism class also holds an item of another class."""
    owners: dict[int, set[int]] = defaultdict(set)
    for ic, lab in zip(iso_class.tolist(), codes.tolist(), strict=True):
        owners[ic].add(lab)
    shared = {ic for ic, labs in owners.items() if len(labs) > 1}
    same_class_iso_pairs = 0
    counts = Counter(zip(iso_class.tolist(), codes.tolist(), strict=True))
    for n in counts.values():
        same_class_iso_pairs += n * (n - 1) // 2
    n_shared = int(sum(1 for ic in iso_class.tolist() if ic in shared))
    return {
        "items_in_cross_class_iso": n_shared,
        "cross_class_iso_fraction": n_shared / len(iso_class) if len(iso_class) else 0.0,
        "cross_class_iso_classes": len(shared),
        "same_class_iso_pairs": int(same_class_iso_pairs),
    }


# --------------------------------------------------------------------------- summaries


def best_competitor(arms: dict[str, dict[str, Any]], metric: str) -> tuple[str, float]:
    """The competitor (not the word, not the ablation) with the highest ``metric``.

    Returns ``("-", nan)`` when no competitor reports ``metric``.
    """
    scored = [(a, float(r[metric])) for a, r in arms.items() if a in COMPETITORS and metric in r]
    if not scored:
        return "-", float("nan")
    return max(scored, key=lambda kv: kv[1])


def to_jsonable(obj: Any) -> Any:  # noqa: ANN401 - arbitrary JSON-bound payloads
    """Recursively convert numpy scalars and arrays for ``json.dumps``."""
    if isinstance(obj, dict):
        return {str(k): to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return to_jsonable(obj.tolist())
    if isinstance(obj, np.generic):
        return obj.item()
    if isinstance(obj, float) and not math.isfinite(obj):
        return None
    return obj


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Atomic JSON write (temp file + rename)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(to_jsonable(payload), indent=1))
    tmp.replace(path)


def write_records(path: Path, records: Sequence[KBRecord]) -> None:
    """Write records as JSON lines (the evaluated items of a cell)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text("".join(json.dumps(r.to_json(), separators=(",", ":")) + "\n" for r in records))
    tmp.replace(path)


def seed_spread(values: Sequence[float]) -> dict[str, float]:
    """Mean, minimum and maximum over seeds."""
    arr = np.asarray(values, dtype=np.float64)
    return {"mean": float(arr.mean()), "min": float(arr.min()), "max": float(arr.max())}
