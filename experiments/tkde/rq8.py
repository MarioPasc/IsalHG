"""RQ8 runner --- valid completion of a record.

Pre-registered in ``docs/article/D_ART3/experiments/HEADLINE_DESIGN_2026-09-13.md``
sections 0, 2 and 4. A record is probably missing a fact; the experiment asks each
representation to propose completions and scores whether the true completion is
among them.

The property the exhibit rests on is the **prefix property** of the ordered walk.
``w0(K-)`` is a program of the machine, and any continuation of it is another
program, so the decoder runs it to completion and the result contains ``K-``
(Proposition C.8, stated and proved in ``RQ8_PILOT.md``): appending instructions
never removes a fact or a constant, and never disconnects, because ``V`` chains its
new constants onto a placed one and ``C`` closes a fact over constants that are
already placed. A sequence model over ``w0`` words conditioned on that prefix
therefore proposes only valid, connected knowledge bases that extend the record.
No certificate and no vector fingerprint admits a completion operation at all,
which is why the non-generative rows of every RQ8 table carry the cell
``"no completion definable"`` rather than a number.

Ours is ``ow_ngram`` --- the RQ6 n-gram (order 3, interpolated Kneser-Ney) over
the ``w0`` words of the training split. It is **not** ``fact_ngram``: the
fact-rank word is the retired comparator of D-ART4 (1), scored here as the
generative baseline it was in RQ6 and never as "ours".

Two tables are written:

1. ``rows_units`` --- one row per ``(collection, stratum, seed, arm, hidden-fact
   kind)``: hit@10, pattern@10, validity, connectivity, and the
   pattern-right-attachment-wrong count that names the mechanism. The seed-level
   scores here are the replication units the Wilcoxon family runs on.
2. ``rows_detail`` --- one row per evaluation unit and arm, so every aggregate
   above can be recomputed from what it rests on.

Every row file is named ``rows_<table>__<run tag>-<unit id>.csv`` with the run tag
of :func:`experiments.tkde.rq1.run_tag`, which hashes the arm set. A run under a
changed arm set therefore lands on different file names and cannot be served the
previous run's rows.
"""

from __future__ import annotations

import argparse
import logging
import random
import sys
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypeAlias

from experiments.tkde import corpora as corpora_io
from experiments.tkde import io
from experiments.tkde.config import TkdeError, load_yaml, seeds
from experiments.tkde.rq1 import deploy_stamps, run_tag, table_file
from experiments.tkde.rq3 import provenance
from isalhg.core.canonical import required_k
from isalhg.core.fact_word import decode_fact_word
from isalhg.core.instructions import parse
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.core.string_to_hypergraph import string_to_hypergraph
from isalhg.datasets.kb.base import Fact, KBCollection, KBRecord, compact
from isalhg.generation.incidence_baseline import flatten, strict_decode
from isalhg.generation.ngram import TokenNGram
from isalhg.iso_backends.isal_ordered import ordered_fingerprint
from isalhg.metric_space.distances.fact_levenshtein import fact_word

logger = logging.getLogger(__name__)

RQ = "RQ8"
RQ_INDEX = 8
RQ_FOLDER = "RQ8_completion"
EXPERIMENT = "completion"

#: Ours. The RQ6 n-gram over ``w0`` words --- D-ART6 makes ``isal_ow_struct`` the
#: paper's program, so "ours" in every RQ8 table is this arm and never
#: ``fact_ngram`` (the RQ6 analyzer's ``MODEL_OURS`` points at the retired word;
#: that mislabel is tracked in T-KBf and is not inherited here).
ARM_OURS = "ow_ngram"

#: The secondary arm, enabled only under the spec's rule (interior hit@10 of
#: ``ow_ngram`` below 0.5 x ``pattern_cooc`` at gate G8.1). The design named a
#: one-layer GRU; torch is absent from the campaign environment and adding a
#: dependency is out of scope, so the orchestrator replaced it (2026-09-13, wave
#: ``2026-09-13-headline-w0``) with a higher-order n-gram over the same training
#: words --- same model class, same smoothing, order 6 instead of 3. Declared
#: here so it can never be read as a post-hoc addition.
ARM_OURS_HO = "ow_ngram_ho"

#: The generative baselines of the spec, in table order.
GENERATIVE_BASELINES: tuple[str, ...] = ("fact_ngram", "incidence_ngram")

#: The counting baselines. ``pattern_cooc`` is the strong practitioner
#: recommender the star stratum is expected to lose to (H8.2).
COUNTING_BASELINES: tuple[str, ...] = ("pattern_freq", "pattern_cooc", "random_pattern")

DEFAULT_ARMS: tuple[str, ...] = (ARM_OURS, *GENERATIVE_BASELINES, *COUNTING_BASELINES)

#: Representations that define a distance and nothing else. Every RQ8 table
#: carries them with :data:`NO_COMPLETION_REASON` in the cell (spec section 1
#: rule 2: a row that cannot be scored states why, never an empty cell).
NON_GENERATIVE_ROWS: tuple[str, ...] = (
    "nauty_cert",
    "nauty_cert_rows",
    "wl_l1",
    "netlsd",
    "hpd_jsd",
    "bipartite_ged_assign",
    "bipartite_ged_path",
    "hypercot",
    "size_l1",
    "degree_seq_l1",
)
NO_COMPLETION_REASON = "no completion definable"

STRATUM_STAR = "star"
STRATUM_NON_STAR = "non_star"
KIND_INTERIOR = "interior"
KIND_PENDANT = "pendant"

#: ``(predicate, arity, ascending multiset of operand types)`` --- the "fact
#: pattern" of the spec, shared by the counting baselines and by pattern@10.
Pattern: TypeAlias = tuple[int, int, tuple[int, ...]]

UNIVERSAL_COLUMNS: tuple[str, ...] = ("rq", "experiment", "git_sha", "host_cpu")

COLUMNS_UNITS: tuple[str, ...] = (
    *UNIVERSAL_COLUMNS,
    "collection",
    "stratum",
    "seed",
    "arm",
    "hidden_kind",
    "n_units",
    "n_hit",
    "n_pattern_hit",
    "n_pattern_hit_attach_miss",
    "hit_at_10",
    "pattern_at_10",
    "n_proposals",
    "n_valid",
    "n_connected",
    "validity",
    "connectivity",
    "n_train",
    "n_eval_members",
    "resample_rate",
    "secs",
    "censored",
)

COLUMNS_DETAIL: tuple[str, ...] = (
    *UNIVERSAL_COLUMNS,
    "collection",
    "stratum",
    "seed",
    "arm",
    "member_id",
    "hidden_fact",
    "hidden_kind",
    "n_minus",
    "m_minus",
    "n_proposals",
    "n_valid",
    "n_connected",
    "hit",
    "pattern_hit",
    "secs",
)

COLUMNS_CENSUS: tuple[str, ...] = (
    *UNIVERSAL_COLUMNS,
    "collection",
    "n_members",
    "n_star",
    "frac_star",
    "n_non_star",
    "shared_constants_mean",
    "shared_facts_mean",
    "n_pool",
    "n_pool_star",
    "n_pool_non_star",
)

COLUMNS: dict[str, tuple[str, ...]] = {
    "units": COLUMNS_UNITS,
    "detail": COLUMNS_DETAIL,
    "census": COLUMNS_CENSUS,
}


class RQ8Error(TkdeError):
    """A RQ8 unit could not be built or evaluated as specified."""


# ---------------------------------------------------------------------------
# Gate G0 --- stars, roots, and the interior/pendant rule
# ---------------------------------------------------------------------------


def fact_degrees(record: KBRecord) -> list[int]:
    """Number of facts each constant occurs in, indexed by constant id."""
    degree = [0] * record.n
    for _, members in record.facts:
        for v in members:
            degree[v] += 1
    return degree


def root_of(record: KBRecord) -> int:
    """The record's root constant: highest fact-degree, ties by smallest id.

    The frozen records carry no explicit root, so the hub stands in for it. On a
    star this *is* the constant contained in every fact, so the G0 census is
    independent of the convention; it matters only for the "non-root" qualifier
    of the interior/pendant rule.

    Parameters
    ----------
    record : KBRecord
        The knowledge base.

    Returns
    -------
    int
        The root constant id.

    Raises
    ------
    RQ8Error
        If the record has no constants.
    """
    if record.n == 0:
        raise RQ8Error(f"{record.kb_id}: a record with no constants has no root")
    degree = fact_degrees(record)
    return min(range(record.n), key=lambda v: (-degree[v], v))


def is_star(record: KBRecord) -> bool:
    """Gate G0's frozen definition of a star.

    Some constant occurs in *every* fact **and** every other constant occurs in
    at most one. NDC carries no declared root, so the root is existentially
    quantified here rather than supplied --- which is exactly the spec's
    "a member is a star only if some constant is in every fact and the rest are
    unshared".

    Parameters
    ----------
    record : KBRecord
        The knowledge base.

    Returns
    -------
    bool
        Whether the record is a star.
    """
    degree = fact_degrees(record)
    for candidate in range(record.n):
        if degree[candidate] != record.m:
            continue
        if all(degree[v] <= 1 for v in range(record.n) if v != candidate):
            return True
    return False


def interior_fact_ids(record: KBRecord) -> tuple[int, ...]:
    """Facts sharing at least one non-root constant with another fact.

    The stratum where an attachment has to be chosen: a pendant fact hangs off
    the root alone, so proposing it is pattern prediction, while an interior one
    also has to pick which existing constants it reaches.

    Parameters
    ----------
    record : KBRecord
        The knowledge base.

    Returns
    -------
    tuple[int, ...]
        Ascending indices into ``record.facts``.
    """
    root = root_of(record)
    degree = fact_degrees(record)
    shared = {v for v in range(record.n) if v != root and degree[v] >= 2}
    return tuple(
        index for index, (_, members) in enumerate(record.facts) if shared.intersection(members)
    )


def hidden_kind(record: KBRecord, fact_index: int) -> str:
    """``"interior"`` or ``"pendant"`` for one fact of ``record``."""
    return KIND_INTERIOR if fact_index in set(interior_fact_ids(record)) else KIND_PENDANT


def star_census(collection: KBCollection, *, m_min: int) -> dict[str, Any]:
    """Gate G0 for one collection, plus the substrate pool it induces.

    Parameters
    ----------
    collection : KBCollection
        A frozen collection.
    m_min : int
        Smallest fact count admitted into the RQ8 substrate pool.

    Returns
    -------
    dict
        The G0 row: member counts, star fraction, and for the non-stars the mean
        number of shared constants and shared (interior) facts.
    """
    records = collection.records
    stars = [record for record in records if is_star(record)]
    non_stars = [record for record in records if not is_star(record)]
    shared_constants: list[int] = []
    shared_facts: list[int] = []
    for record in non_stars:
        root = root_of(record)
        degree = fact_degrees(record)
        shared_constants.append(sum(1 for v in range(record.n) if v != root and degree[v] >= 2))
        shared_facts.append(len(interior_fact_ids(record)))
    pool = [record for record in records if record.m >= m_min]
    return {
        "collection": collection.name,
        "n_members": len(records),
        "n_star": len(stars),
        "frac_star": len(stars) / len(records) if records else "",
        "n_non_star": len(non_stars),
        "shared_constants_mean": (
            round(sum(shared_constants) / len(shared_constants), 4) if shared_constants else ""
        ),
        "shared_facts_mean": (
            round(sum(shared_facts) / len(shared_facts), 4) if shared_facts else ""
        ),
        "n_pool": len(pool),
        "n_pool_star": sum(1 for record in pool if is_star(record)),
        "n_pool_non_star": sum(1 for record in pool if not is_star(record)),
    }


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------


def pattern_of(record: KBRecord, fact: Fact) -> Pattern:
    """``(predicate, arity, ascending operand types)`` of one fact."""
    predicate, members = fact
    return (predicate, len(members), tuple(sorted(record.types[v] for v in members)))


def patterns_of(record: KBRecord) -> tuple[Pattern, ...]:
    """Every fact's pattern, in fact order."""
    return tuple(pattern_of(record, fact) for fact in record.facts)


def hypergraph_patterns(H: SparseHypergraph) -> tuple[Pattern, ...]:
    """Fact patterns of a decoded proposal, which carries no ``KBRecord``."""
    return tuple(
        (label, len(members), tuple(sorted(H.vertex_label(v) for v in members)))
        for _, members, label in H.iter_edges()
    )


def added_patterns(proposal: tuple[Pattern, ...], base: tuple[Pattern, ...]) -> list[Pattern]:
    """Multiset difference ``proposal - base``.

    Identity-free on purpose: the arms disagree about whether a proposal keeps
    the record's constant numbering, so "which facts were added" is answered on
    patterns, which every arm expresses in the same vocabulary.

    Parameters
    ----------
    proposal : tuple[Pattern, ...]
        Patterns of the proposed knowledge base.
    base : tuple[Pattern, ...]
        Patterns of ``K-``.

    Returns
    -------
    list[Pattern]
        The patterns present in ``proposal`` beyond their multiplicity in
        ``base``.
    """
    remaining = list(base)
    extra: list[Pattern] = []
    for item in proposal:
        if item in remaining:
            remaining.remove(item)
        else:
            extra.append(item)
    return extra


# ---------------------------------------------------------------------------
# Units
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Unit:
    """One independently computable, independently resumable piece of work."""

    collection: str
    stratum: str
    seed_index: int

    @property
    def unit_id(self) -> str:
        """Stable id; part of every row file name this unit writes."""
        return f"{self.collection}-{self.stratum}-s{self.seed_index:03d}"

    @property
    def tables(self) -> tuple[str, ...]:
        """Row tables this unit is responsible for."""
        return ("units", "detail")


@dataclass(frozen=True)
class EvalUnit:
    """One ``(member, hidden fact)`` evaluation unit.

    Attributes
    ----------
    truth : KBRecord
        The member; the completion that counts as a hit.
    minus : KBRecord
        ``K-``: the member with the hidden fact deleted and any constant left
        factless dropped. Connected by construction.
    hidden : Fact
        The deleted fact, in ``truth``'s constant numbering.
    kind : str
        ``"interior"`` or ``"pendant"``.
    """

    truth: KBRecord
    minus: KBRecord
    hidden: Fact
    kind: str

    @property
    def hidden_pattern(self) -> Pattern:
        """The hidden fact's pattern --- what pattern@10 looks for."""
        return pattern_of(self.truth, self.hidden)


def delete_fact(record: KBRecord, fact_index: int) -> KBRecord | None:
    """``K-``: ``record`` without fact ``fact_index``, compacted, or ``None``.

    ``None`` when the deletion disconnects the remainder --- the spec's resample
    condition, whose rate is logged.

    Parameters
    ----------
    record : KBRecord
        The member.
    fact_index : int
        Index into ``record.facts``.

    Returns
    -------
    KBRecord or None
        The connected remainder, or ``None``.
    """
    kept = [fact for index, fact in enumerate(record.facts) if index != fact_index]
    if not kept:
        return None
    return compact(
        f"{record.kb_id}-minus{fact_index}",
        record.types,
        kept,
        constant_ids=record.constant_ids,
        label=record.label,
        meta=dict(record.meta),
        require_connected=True,
    )


def _candidate_facts(record: KBRecord, stratum: str) -> tuple[int, ...]:
    """Fact indices the hidden fact may be drawn from, under the stratum rule."""
    if stratum == STRATUM_NON_STAR:
        return interior_fact_ids(record)
    return tuple(range(record.m))


def build_eval_units(
    members: Sequence[KBRecord],
    stratum: str,
    *,
    per_member: int,
    limit: int,
    rng: random.Random,
) -> tuple[list[EvalUnit], int, int]:
    """Draw the evaluation units of one ``(collection, stratum, seed)``.

    Parameters
    ----------
    members : Sequence[KBRecord]
        The evaluation split.
    stratum : str
        ``"star"`` or ``"non_star"``; decides which facts may be hidden.
    per_member : int
        Largest number of hidden facts drawn from one member.
    limit : int
        Largest number of units returned.
    rng : random.Random
        The unit's generator.

    Returns
    -------
    tuple
        ``(units, n_attempted, n_resampled)``; ``n_resampled`` counts the draws
        whose remainder was disconnected and were therefore discarded.
    """
    units: list[EvalUnit] = []
    attempted = resampled = 0
    order = list(members)
    rng.shuffle(order)
    for record in order:
        candidates = list(_candidate_facts(record, stratum))
        rng.shuffle(candidates)
        taken = 0
        for fact_index in candidates:
            if taken >= per_member or len(units) >= limit:
                break
            attempted += 1
            minus = delete_fact(record, fact_index)
            if minus is None:
                resampled += 1
                continue
            units.append(
                EvalUnit(
                    truth=record,
                    minus=minus,
                    hidden=record.facts[fact_index],
                    kind=hidden_kind(record, fact_index),
                )
            )
            taken += 1
        if len(units) >= limit:
            break
    return units, attempted, resampled


def split_members(
    pool: Sequence[KBRecord], *, train_frac: float, rng: random.Random
) -> tuple[list[KBRecord], list[KBRecord]]:
    """80/20 split by member, stratified by class label where one exists.

    Stratifying keeps the evaluation split's class mix comparable across seeds;
    unlabelled members form their own stratum, so a collection without labels
    degenerates to a plain shuffle.

    Parameters
    ----------
    pool : Sequence[KBRecord]
        The substrate pool of one stratum.
    train_frac : float
        Fraction assigned to training.
    rng : random.Random
        The unit's generator.

    Returns
    -------
    tuple[list[KBRecord], list[KBRecord]]
        ``(train, evaluation)``; the two are disjoint by construction, which is
        what the leakage guard in the test suite asserts.
    """
    buckets: dict[str, list[KBRecord]] = {}
    for record in pool:
        buckets.setdefault(record.label or "", []).append(record)
    train: list[KBRecord] = []
    evaluation: list[KBRecord] = []
    for key in sorted(buckets):
        group = list(buckets[key])
        rng.shuffle(group)
        cut = int(round(len(group) * train_frac))
        # A singleton class must not vanish from training: with cut == 0 the
        # model would never see the class it is then asked to complete.
        cut = min(max(cut, 1), len(group)) if group else 0
        train.extend(group[:cut])
        evaluation.extend(group[cut:])
    return train, evaluation


# ---------------------------------------------------------------------------
# Collection context
# ---------------------------------------------------------------------------


@dataclass
class CollectionContext:
    """Everything a RQ8 unit needs from one collection, computed once."""

    name: str
    collection: KBCollection
    n_types: int
    n_preds: int
    k: int
    records: list[KBRecord]
    hypergraphs: list[SparseHypergraph]
    _ow: dict[str, tuple[int, tuple[str, ...]]] = field(default_factory=dict)
    _certificate: dict[str, tuple[int, str]] = field(default_factory=dict)

    def ow_word(self, record: KBRecord) -> tuple[int, tuple[str, ...]]:
        """``(root type, ordered-walk tokens)`` of one record, memoised by id."""
        cached = self._ow.get(record.kb_id)
        if cached is None:
            root_label, word = ordered_fingerprint(record.to_hypergraph())
            cached = (int(root_label), ow_tokens(word))
            self._ow[record.kb_id] = cached
        return cached

    def decode_ow(self, tokens: Sequence[str], root_label: int) -> SparseHypergraph:
        """Run an ordered-walk token sequence on a fresh VM."""
        return string_to_hypergraph(
            ";".join(str(token) for token in tokens),
            k=self.k,
            n_vertex_labels=self.n_types,
            n_edge_labels=self.n_preds,
            seed_label=root_label,
            backend="python",
        )


def ow_tokens(word: str) -> tuple[str, ...]:
    """Tokenize an ordered-walk word into its surface tokens.

    Through the instruction parser and never a split on ``";"``: a token carries
    its own semicolons inside brackets (``V[0;1;2;0,2]``), so a naive split cuts
    tokens in half and the result no longer parses.
    """
    return tuple(token.serialize() for token in parse(word))


def build_context(name: str, root: Path | None) -> CollectionContext:
    """Load one frozen collection and precompute what every unit needs."""
    collection = corpora_io.load_collection(name, root)
    records = list(collection.records)
    hypergraphs = corpora_io.hypergraphs(collection)
    return CollectionContext(
        name=name,
        collection=collection,
        n_types=collection.n_types,
        n_preds=collection.n_preds,
        # One k per collection (L10, R5): a sampled continuation may name an
        # arity wider than the record it extends, so the pointer count is the
        # corpus maximum rather than the member's.
        k=max((required_k(H) for H in hypergraphs), default=2),
        records=records,
        hypergraphs=hypergraphs,
    )


def certificate(H: SparseHypergraph) -> tuple[int, str] | None:
    """``(root type, w0)`` --- the complete invariant of Theorem C, or ``None``.

    ``None`` when ``H`` is not a connected knowledge base, which is the only
    input the ordered walk refuses (R3). Callers treat that as "this proposal
    cannot be a hit", never as an error.
    """
    try:
        root_label, word = ordered_fingerprint(H)
    except Exception as exc:  # noqa: BLE001 - a refusal is data, not a crash
        logger.debug("no certificate: %s", exc)
        return None
    return (int(root_label), word)


# ---------------------------------------------------------------------------
# Proposals
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Proposal:
    """One proposed completion.

    Attributes
    ----------
    hypergraph : SparseHypergraph or None
        ``None`` when the arm's decoder rejected its own sample.
    connected : bool
        Whether the decoded proposal is a connected knowledge base.
    patterns : tuple[Pattern, ...]
        Its fact patterns; empty when it did not decode.
    cert : tuple[int, str] or None
        Its certificate, used both to deduplicate and to test isomorphism.
    """

    hypergraph: SparseHypergraph | None
    connected: bool
    patterns: tuple[Pattern, ...]
    cert: tuple[int, str] | None

    @property
    def valid(self) -> bool:
        """Whether the proposal decoded at all."""
        return self.hypergraph is not None


def _as_proposal(H: SparseHypergraph | None) -> Proposal:
    if H is None:
        return Proposal(hypergraph=None, connected=False, patterns=(), cert=None)
    connected = H.is_connected()
    return Proposal(
        hypergraph=H,
        connected=connected,
        patterns=hypergraph_patterns(H),
        cert=certificate(H) if connected else None,
    )


def _collect(
    draw: Any,
    base_patterns: tuple[Pattern, ...],
    *,
    k_proposals: int,
    resamples: int,
) -> list[Proposal]:
    """Draw distinct completions that add at least one fact.

    ``draw(attempt)`` returns one :class:`Proposal`. Each of the ``k_proposals``
    slots gets up to ``resamples`` attempts to produce a proposal that both adds
    a fact and carries a certificate not already taken; an attempt that decodes
    but adds nothing is still counted in the validity and connectivity totals,
    because refusing to count it would report a filtered rate as a measured one.

    Parameters
    ----------
    draw : callable
        ``(attempt index) -> Proposal``.
    base_patterns : tuple[Pattern, ...]
        Patterns of ``K-``; the "at least one new fact" test is against these.
    k_proposals : int
        How many distinct completions to return.
    resamples : int
        Attempts allowed per slot (``R`` of the spec).

    Returns
    -------
    list[Proposal]
        Every attempt made, in order --- the accepted ones and the rejected
        ones, so the caller can score hit@10 on the accepted set and report
        validity over everything drawn.
    """
    attempts: list[Proposal] = []
    accepted: list[Proposal] = []
    seen: set[tuple[int, str]] = set()
    index = 0
    for _ in range(k_proposals):
        for _ in range(resamples):
            proposal = draw(index)
            index += 1
            attempts.append(proposal)
            if not proposal.valid or proposal.cert is None:
                continue
            if proposal.cert in seen:
                continue
            if len(proposal.patterns) <= len(base_patterns):
                continue
            seen.add(proposal.cert)
            accepted.append(proposal)
            break
        if len(accepted) >= k_proposals:
            break
    return attempts


def _accepted(attempts: Sequence[Proposal], base_patterns: tuple[Pattern, ...]) -> list[Proposal]:
    """The distinct fact-adding proposals among ``attempts``, in draw order."""
    seen: set[tuple[int, str]] = set()
    out: list[Proposal] = []
    for proposal in attempts:
        if not proposal.valid or proposal.cert is None or proposal.cert in seen:
            continue
        if len(proposal.patterns) <= len(base_patterns):
            continue
        seen.add(proposal.cert)
        out.append(proposal)
    return out


# --- generative arms --------------------------------------------------------


def completion_cap(prefix: Sequence[Any], max_len: int, max_new: int) -> int:
    """Total-length cap that still leaves room for a continuation.

    :meth:`TokenNGram.complete` caps the *whole* word, prefix included, and
    returns the prefix unchanged when it already sits at the cap. A record whose
    word is longer than the flat ``max_len`` would then produce no proposal at
    all for every arm whose word is long --- which is a measurement of word
    length, not of the model. The cap is therefore at least ``max_new`` tokens
    beyond the prefix.
    """
    return max(int(max_len), len(prefix) + int(max_new))


def propose_ow(
    context: CollectionContext,
    model: TokenNGram,
    unit: EvalUnit,
    *,
    seed: int,
    k_proposals: int,
    resamples: int,
    max_len: int,
    max_new: int,
) -> list[Proposal]:
    """Ours: continue ``w0(K-)`` verbatim and decode.

    The prefix survives intact, so Proposition C.8 applies to every proposal:
    it decodes, it is connected, and it contains ``K-``.
    """
    root_label, prefix = context.ow_word(unit.minus)
    base = patterns_of(unit.minus)
    cap = completion_cap(prefix, max_len, max_new)

    def draw(attempt: int) -> Proposal:
        word = model.complete(prefix, seed=seed + attempt, max_len=cap)
        try:
            H = context.decode_ow(word, root_label)
        except Exception as exc:  # noqa: BLE001 - Prop. C.8 says this cannot happen
            logger.error("%s: ordered-walk completion did not decode: %s", unit.truth.kb_id, exc)
            return _as_proposal(None)
        return _as_proposal(H)

    return _collect(draw, base, k_proposals=k_proposals, resamples=resamples)


def propose_fact(
    context: CollectionContext,
    model: TokenNGram,
    unit: EvalUnit,
    *,
    seed: int,
    k_proposals: int,
    resamples: int,
    max_len: int,
    max_new: int,
) -> list[Proposal]:
    """``fact_ngram``: continue the fact-rank word of ``K-``.

    The decoder is total, so validity is 1; connectivity is not guaranteed,
    which is the H8.3 contrast.
    """
    prefix = fact_word(unit.minus.to_hypergraph())
    base = patterns_of(unit.minus)
    cap = completion_cap(prefix, max_len, max_new)

    def draw(attempt: int) -> Proposal:
        word = model.complete(prefix, seed=seed + attempt, max_len=cap)
        try:
            H, _ = decode_fact_word(word, n_types=context.n_types, n_preds=context.n_preds)
        except Exception as exc:  # noqa: BLE001 - a total decoder must not raise
            logger.error("%s: fact-word completion did not decode: %s", unit.truth.kb_id, exc)
            return _as_proposal(None)
        return _as_proposal(H)

    return _collect(draw, base, k_proposals=k_proposals, resamples=resamples)


def propose_incidence(
    context: CollectionContext,
    model: TokenNGram,
    unit: EvalUnit,
    *,
    seed: int,
    k_proposals: int,
    resamples: int,
    max_len: int,
    max_new: int,
) -> list[Proposal]:
    """``incidence_ngram``: continue the flat incidence list; strict decoder.

    The prefix drops the serialization's ``("END",)`` terminator. Keeping it
    would measure the prefix construction rather than the baseline: every
    continuation would sit after a terminator the decoder stops at, so the arm
    could never add a fact and would score 0 by construction. The declared
    constant count *is* kept, because that is a real constraint of the flat
    language --- a completion over a new constant contradicts it and is
    rejected, which is exactly the H8.3 contrast.
    """
    prefix = flatten(unit.minus.to_hypergraph())[:-1]
    base = patterns_of(unit.minus)
    cap = completion_cap(prefix, max_len, max_new)

    def draw(attempt: int) -> Proposal:
        word = model.complete(prefix, seed=seed + attempt, max_len=cap)
        return _as_proposal(strict_decode(word, n_types=context.n_types, n_preds=context.n_preds))

    return _collect(draw, base, k_proposals=k_proposals, resamples=resamples)


# --- counting arms ----------------------------------------------------------


def attach(record: KBRecord, pattern: Pattern, *, prefer_root: bool) -> KBRecord | None:
    """Attach one fact pattern to ``record`` under the spec's heuristic.

    The heuristic, stated once: **the root for stars, the highest-degree
    constants of matching type otherwise**, with remaining operands created as
    new constants of the required type. One slot is always filled by an existing
    constant --- the best type match, or the hub when no type matches --- so the
    result is connected. That last fallback deliberately strengthens the
    baseline: leaving the fact unattached would score the recommender's
    connectivity rather than its recommendation, and a handicapped baseline is
    not a baseline (L12).

    Parameters
    ----------
    record : KBRecord
        ``K-``.
    pattern : Pattern
        ``(predicate, arity, ascending operand types)``.
    prefer_root : bool
        Whether the root must occupy a slot --- the star rule.

    Returns
    -------
    KBRecord or None
        The extended record, or ``None`` when the attachment reproduces a fact
        ``record`` already carries (no new fact, so no proposal).
    """
    predicate, arity, types = pattern
    if arity < 2 or len(types) != arity:
        return None
    degree = fact_degrees(record)
    root = root_of(record)
    used: set[int] = set()
    operands: list[int] = []
    new_types: list[int] = []
    wanted = list(types)

    if prefer_root:
        root_type = record.types[root]
        if root_type in wanted:
            wanted.remove(root_type)
            operands.append(root)
            used.add(root)

    for want in wanted:
        choices = [v for v in range(record.n) if v not in used and record.types[v] == want]
        if choices:
            best = max(choices, key=lambda v: (degree[v], -v))
            operands.append(best)
            used.add(best)
        else:
            new_types.append(want)

    if not operands:
        # No operand type occurs in the record: anchor on the hub so the new
        # fact reaches the knowledge base instead of floating free.
        operands.append(root)
        used.add(root)
        if new_types:
            new_types.pop()

    types_out = list(record.types)
    for label in new_types:
        operands.append(len(types_out))
        types_out.append(label)

    fact: Fact = (predicate, tuple(sorted(set(operands))))
    if len(fact[1]) != arity or fact in record.facts:
        return None
    return compact(
        f"{record.kb_id}+{predicate}",
        types_out,
        [*record.facts, fact],
        meta=dict(record.meta),
        require_connected=False,
    )


def propose_patterns(
    context: CollectionContext,
    unit: EvalUnit,
    ranked: Sequence[Pattern],
    *,
    prefer_root: bool,
    k_proposals: int,
) -> list[Proposal]:
    """Attach the top-``k`` ranked patterns to ``K-``, in rank order.

    A ranked pattern whose attachment reproduces a fact ``K-`` already carries
    emits nothing --- a wasted slot, not an invalid proposal. Recording it as a
    decode failure would put a counting artefact in the validity column, which
    is the H8.3 measurement; the ranking simply runs deeper than the slot count
    so the arm still gets its ``k`` proposals.
    """
    base = patterns_of(unit.minus)
    attempts: list[Proposal] = []
    for pattern in ranked:
        if len(_accepted(attempts, base)) >= k_proposals:
            break
        extended = attach(unit.minus, pattern, prefer_root=prefer_root)
        if extended is None:
            continue
        attempts.append(
            _as_proposal(extended.to_hypergraph(n_types=context.n_types, n_preds=context.n_preds))
        )
    return attempts


@dataclass(frozen=True)
class PatternStatistics:
    """What the counting baselines are fitted on."""

    frequency: dict[Pattern, int]
    cooccurrence: dict[Pattern, dict[Pattern, int]]
    vocabulary: tuple[Pattern, ...]

    @classmethod
    def fit(cls, records: Sequence[KBRecord]) -> PatternStatistics:
        """Count pattern frequency and pattern-given-pattern co-occurrence."""
        frequency: dict[Pattern, int] = {}
        cooccurrence: dict[Pattern, dict[Pattern, int]] = {}
        for record in records:
            observed = patterns_of(record)
            for pattern in observed:
                frequency[pattern] = frequency.get(pattern, 0) + 1
            for context_pattern in set(observed):
                bucket = cooccurrence.setdefault(context_pattern, {})
                for pattern in observed:
                    bucket[pattern] = bucket.get(pattern, 0) + 1
        vocabulary = tuple(sorted(frequency, key=lambda p: (-frequency[p], p)))
        return cls(frequency=frequency, cooccurrence=cooccurrence, vocabulary=vocabulary)

    def by_frequency(self, record: KBRecord, limit: int) -> list[Pattern]:
        """``pattern_freq``: the commonest training patterns, type-conditioned.

        Type-conditioned means restricted to patterns whose operand types the
        record can supply or create; in practice that is every pattern, so the
        ranking is the training frequency with the record's own patterns kept
        (a repeated pattern over different constants is a legitimate proposal).
        """
        return list(self.vocabulary[: max(limit, 0)])

    def by_cooccurrence(self, record: KBRecord, limit: int) -> list[Pattern]:
        """``pattern_cooc``: item-item conditional frequency given ``K-``.

        The strong practitioner recommender: score every candidate pattern by
        how often it co-occurs with the patterns the record already carries,
        normalised by the conditioning pattern's own frequency, and take the
        top ``limit``.
        """
        scores: dict[Pattern, float] = {}
        for present in set(patterns_of(record)):
            bucket = self.cooccurrence.get(present)
            if not bucket:
                continue
            total = float(sum(bucket.values()))
            for candidate, count in bucket.items():
                scores[candidate] = scores.get(candidate, 0.0) + count / total
        if not scores:
            return self.by_frequency(record, limit)
        ranked = sorted(scores, key=lambda p: (-scores[p], -self.frequency.get(p, 0), p))
        return ranked[: max(limit, 0)]

    def at_random(self, limit: int, rng: random.Random) -> list[Pattern]:
        """``random_pattern``: uniform draws from the training vocabulary."""
        if not self.vocabulary:
            return []
        return [rng.choice(self.vocabulary) for _ in range(max(limit, 0))]


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Score:
    """One arm's outcome on one evaluation unit."""

    n_proposals: int
    n_valid: int
    n_connected: int
    hit: bool
    pattern_hit: bool


def score(
    unit: EvalUnit, attempts: Sequence[Proposal], truth_cert: tuple[int, str] | None
) -> Score:
    """Score one arm's attempts on one evaluation unit.

    ``hit`` is exact: some accepted proposal is valid, connected, and carries the
    truth's certificate, which is a complete isomorphism invariant (Theorem C).
    ``pattern_hit`` is the weaker credit: the hidden fact's pattern appears among
    the patterns some accepted proposal added.
    """
    base = patterns_of(unit.minus)
    accepted = _accepted(attempts, base)
    wanted = unit.hidden_pattern
    hit = truth_cert is not None and any(
        proposal.connected and proposal.cert == truth_cert for proposal in accepted
    )
    pattern_hit = any(wanted in added_patterns(p.patterns, base) for p in accepted)
    return Score(
        n_proposals=len(attempts),
        n_valid=sum(1 for p in attempts if p.valid),
        n_connected=sum(1 for p in attempts if p.connected),
        hit=hit,
        pattern_hit=pattern_hit,
    )


# ---------------------------------------------------------------------------
# The unit runner
# ---------------------------------------------------------------------------


def _fit_models(
    context: CollectionContext,
    train: Sequence[KBRecord],
    arms: Sequence[str],
    order: int,
    order_ho: int,
) -> dict[str, TokenNGram]:
    """Fit each generative arm's n-gram on the training words only."""
    models: dict[str, TokenNGram] = {}
    if ARM_OURS in arms or ARM_OURS_HO in arms:
        words = [context.ow_word(record)[1] for record in train]
        if ARM_OURS in arms:
            models[ARM_OURS] = TokenNGram(order=order).fit(words)
        if ARM_OURS_HO in arms:
            models[ARM_OURS_HO] = TokenNGram(order=order_ho).fit(words)
    if "fact_ngram" in arms:
        models["fact_ngram"] = TokenNGram(order=order).fit(
            [fact_word(record.to_hypergraph()) for record in train]
        )
    if "incidence_ngram" in arms:
        models["incidence_ngram"] = TokenNGram(order=order).fit(
            [flatten(record.to_hypergraph()) for record in train]
        )
    return models


def run_unit(
    unit: Unit,
    config: Mapping[str, Any],
    context: CollectionContext,
    base: Mapping[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    """Compute one ``(collection, stratum, seed)`` unit.

    Returns
    -------
    dict
        ``{"units": [...], "detail": [...]}`` --- the aggregate rows and the
        per-evaluation-unit rows they are computed from.
    """
    started = time.perf_counter()
    arms = tuple(config.get("arms") or DEFAULT_ARMS)
    m_min = int(config.get("m_min", 4))
    k_proposals = int(config.get("k_proposals", 10))
    resamples = int(config.get("resamples", 20))
    max_len = int(config.get("max_len", 200))
    max_new = int(config.get("max_new_tokens", 60))
    order = int(config.get("ngram_order", 3))
    order_ho = int(config.get("ngram_order_ho", 6))
    train_frac = float(config.get("train_frac", 0.8))
    per_member = int(config.get("units_per_member", 2))
    limit = int(config.get("max_eval_units", 200))
    seed = seeds(RQ_INDEX, int(config.get("seed_count", 27)))[unit.seed_index]

    want_star = unit.stratum == STRATUM_STAR
    pool = [
        record for record in context.records if record.m >= m_min and is_star(record) == want_star
    ]
    if len(pool) < int(config.get("min_pool", 20)):
        logger.warning(
            "%s: stratum %s has %d members at m >= %d; not reportable, unit skipped",
            context.name,
            unit.stratum,
            len(pool),
            m_min,
        )
        return {"units": [], "detail": []}

    rng = random.Random(f"rq8|{context.name}|{unit.stratum}|{seed}")
    train, evaluation = split_members(pool, train_frac=train_frac, rng=rng)
    eval_units, attempted, resampled = build_eval_units(
        evaluation, unit.stratum, per_member=per_member, limit=limit, rng=rng
    )
    if not eval_units:
        raise RQ8Error(f"{unit.unit_id}: no evaluation unit survived the connectivity rule")

    models = _fit_models(context, train, arms, order, order_ho)
    statistics = PatternStatistics.fit(train)
    truth_certs = {
        eval_unit.truth.kb_id: certificate(
            eval_unit.truth.to_hypergraph(n_types=context.n_types, n_preds=context.n_preds)
        )
        for eval_unit in eval_units
    }

    shared = {
        **base,
        "rq": RQ,
        "experiment": EXPERIMENT,
        "collection": context.name,
        "stratum": unit.stratum,
        "seed": seed,
    }
    detail: list[dict[str, Any]] = []
    totals: dict[tuple[str, str], dict[str, int]] = {}

    for position, eval_unit in enumerate(eval_units):
        for arm in arms:
            arm_started = time.perf_counter()
            attempts = _propose(
                arm,
                context,
                models,
                statistics,
                eval_unit,
                seed=seed + 1_000 * position,
                k_proposals=k_proposals,
                resamples=resamples,
                max_len=max_len,
                max_new=max_new,
                prefer_root=want_star,
                rng=random.Random(f"rq8|{arm}|{context.name}|{seed}|{position}"),
            )
            outcome = score(eval_unit, attempts, truth_certs[eval_unit.truth.kb_id])
            detail.append(
                {
                    **shared,
                    "arm": arm,
                    "member_id": eval_unit.truth.kb_id,
                    "hidden_fact": list(eval_unit.hidden[1]),
                    "hidden_kind": eval_unit.kind,
                    "n_minus": eval_unit.minus.n,
                    "m_minus": eval_unit.minus.m,
                    "n_proposals": outcome.n_proposals,
                    "n_valid": outcome.n_valid,
                    "n_connected": outcome.n_connected,
                    "hit": int(outcome.hit),
                    "pattern_hit": int(outcome.pattern_hit),
                    "secs": time.perf_counter() - arm_started,
                }
            )
            bucket = totals.setdefault(
                (arm, eval_unit.kind),
                {
                    "n_units": 0,
                    "n_hit": 0,
                    "n_pattern_hit": 0,
                    "n_pattern_hit_attach_miss": 0,
                    "n_proposals": 0,
                    "n_valid": 0,
                    "n_connected": 0,
                },
            )
            bucket["n_units"] += 1
            bucket["n_hit"] += int(outcome.hit)
            bucket["n_pattern_hit"] += int(outcome.pattern_hit)
            bucket["n_pattern_hit_attach_miss"] += int(outcome.pattern_hit and not outcome.hit)
            bucket["n_proposals"] += outcome.n_proposals
            bucket["n_valid"] += outcome.n_valid
            bucket["n_connected"] += outcome.n_connected

    elapsed = time.perf_counter() - started
    units_rows = [
        {
            **shared,
            "arm": arm,
            "hidden_kind": kind,
            **bucket,
            "hit_at_10": bucket["n_hit"] / bucket["n_units"] if bucket["n_units"] else "",
            "pattern_at_10": (
                bucket["n_pattern_hit"] / bucket["n_units"] if bucket["n_units"] else ""
            ),
            "validity": bucket["n_valid"] / bucket["n_proposals"] if bucket["n_proposals"] else "",
            "connectivity": (
                bucket["n_connected"] / bucket["n_valid"] if bucket["n_valid"] else ""
            ),
            "n_train": len(train),
            "n_eval_members": len(evaluation),
            "resample_rate": resampled / attempted if attempted else "",
            "secs": elapsed,
            "censored": 0,
        }
        for (arm, kind), bucket in sorted(totals.items())
    ]
    return {"units": units_rows, "detail": detail}


def _propose(
    arm: str,
    context: CollectionContext,
    models: Mapping[str, TokenNGram],
    statistics: PatternStatistics,
    unit: EvalUnit,
    *,
    seed: int,
    k_proposals: int,
    resamples: int,
    max_len: int,
    max_new: int,
    prefer_root: bool,
    rng: random.Random,
) -> list[Proposal]:
    """Dispatch one arm's proposal routine."""
    if arm in (ARM_OURS, ARM_OURS_HO):
        return propose_ow(
            context,
            models[arm],
            unit,
            seed=seed,
            k_proposals=k_proposals,
            resamples=resamples,
            max_len=max_len,
            max_new=max_new,
        )
    if arm == "fact_ngram":
        return propose_fact(
            context,
            models[arm],
            unit,
            seed=seed,
            k_proposals=k_proposals,
            resamples=resamples,
            max_len=max_len,
            max_new=max_new,
        )
    if arm == "incidence_ngram":
        return propose_incidence(
            context,
            models[arm],
            unit,
            seed=seed,
            k_proposals=k_proposals,
            resamples=resamples,
            max_len=max_len,
            max_new=max_new,
        )
    # The counting arms rank more patterns than slots, because an attachment can
    # reproduce a fact the record already carries and yield no proposal.
    depth = k_proposals * 3
    if arm == "pattern_freq":
        ranked = statistics.by_frequency(unit.minus, depth)
    elif arm == "pattern_cooc":
        ranked = statistics.by_cooccurrence(unit.minus, depth)
    elif arm == "random_pattern":
        ranked = statistics.at_random(depth, rng)
    else:
        raise RQ8Error(f"unknown arm {arm!r}")
    return propose_patterns(context, unit, ranked, prefer_root=prefer_root, k_proposals=k_proposals)


# ---------------------------------------------------------------------------
# Unit enumeration and the CLI
# ---------------------------------------------------------------------------


def enumerate_units(config: Mapping[str, Any]) -> list[Unit]:
    """Every RQ8 unit, in a fixed order."""
    seed_count = int(config.get("seed_count", 27))
    units: list[Unit] = []
    for name in config["collections"]:
        strata = config.get("strata", {}).get(name) or [STRATUM_NON_STAR]
        for stratum in strata:
            units.extend(Unit(name, str(stratum), index) for index in range(seed_count))
    return units


def unit_is_done(paths: io.RunPaths, unit: Unit, tag: str) -> bool:
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


def write_census(
    config: Mapping[str, Any],
    paths: io.RunPaths,
    tag: str,
    data_root: Path | None,
    base: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Compute gate G0 for every collection and write ``rows_census``."""
    m_min = int(config.get("m_min", 4))
    rows = [
        {
            **base,
            "rq": RQ,
            "experiment": EXPERIMENT,
            **star_census(corpora_io.load_collection(name, data_root), m_min=m_min),
        }
        for name in config["collections"]
    ]
    io.write_rows(paths, table_file(tag, "census", "g0"), rows, columns=COLUMNS_CENSUS)
    return rows


def smoke_config(config: dict[str, Any]) -> dict[str, Any]:
    """Shrink a configuration to the ``--smoke`` shape (minutes, not hours)."""
    smoke = dict(config)
    smoke.update(config.get("smoke") or {})
    smoke.pop("smoke", None)
    return smoke


def build_parser() -> argparse.ArgumentParser:
    """The frozen runner CLI."""
    parser = argparse.ArgumentParser(prog="experiments.tkde.rq8", description="RQ8 --- completion")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--data-root", type=Path, default=None)
    parser.add_argument("--shard", default=None, help="i/N: run shard i of N")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--census-only", action="store_true", help="compute gate G0 and exit")
    parser.add_argument("--count", action="store_true", help="print the shard count and exit")
    parser.add_argument("--list-units", action="store_true")
    parser.add_argument("--start-cutoff-epoch", type=float, default=None)
    parser.add_argument("--log-level", default="INFO")
    return parser


def parse_shard(spec: str | None, n_units: int) -> tuple[int, int]:
    """Parse ``i/N``; the default is the single shard ``0/1``."""
    if not spec:
        return 0, 1
    try:
        index, total = (int(part) for part in spec.split("/", 1))
    except ValueError as exc:
        raise RQ8Error(f"--shard must look like i/N, got {spec!r}") from exc
    if total < 1 or not 0 <= index < total:
        raise RQ8Error(f"--shard {spec!r} is out of range for {n_units} units")
    return index, total


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point of ``python -m experiments.tkde.rq8``."""
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, str(args.log_level).upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
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
    experiment = str(config.get("experiment", EXPERIMENT))
    paths = io.RunPaths(root=results_root, rq=RQ_FOLDER, experiment=experiment)
    paths.ensure()
    tag = run_tag(config)
    git_sha, host_cpu = provenance()
    base = {"git_sha": git_sha, "host_cpu": host_cpu}

    if args.census_only:
        for row in write_census(config, paths, tag, args.data_root, base):
            logger.info("G0 %s", row)
        return 0

    shard, n_shards = parse_shard(args.shard, len(units))
    mine = units[shard::n_shards]
    logger.info(
        "RQ8: shard %d/%d -> %d of %d units (run tag %s)",
        shard,
        n_shards,
        len(mine),
        len(units),
        tag,
    )
    if shard == 0:
        write_census(config, paths, tag, args.data_root, base)

    contexts: dict[str, CollectionContext] = {}
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
        if unit.collection not in contexts:
            contexts[unit.collection] = build_context(unit.collection, args.data_root)
        started = time.monotonic()
        tables = run_unit(unit, config, contexts[unit.collection], base)
        for table, rows in tables.items():
            io.write_rows(paths, table_file(tag, table, unit.unit_id), rows, columns=COLUMNS[table])
            written[table] = written.get(table, 0) + len(rows)
        logger.info("unit %s done in %.1f s", unit.unit_id, time.monotonic() - started)

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
        "seeds": seeds(RQ_INDEX, int(config.get("seed_count", 27))),
        "arms": list(config.get("arms") or DEFAULT_ARMS),
        "non_generative_rows": list(NON_GENERATIVE_ROWS),
        "units": [unit.unit_id for unit in mine],
    }
    extra = {
        "shard": f"{shard}/{n_shards}",
        "run_tag": tag,
        "rows_written": written,
        **deploy_stamps(),
    }
    io.write_config(paths, record)
    io.write_manifest(paths, extra=extra)
    shard_paths = io.RunPaths(
        root=results_root, rq=RQ_FOLDER, experiment=f"{experiment}/_shards/{shard:03d}"
    )
    io.write_config(shard_paths, record)
    io.write_manifest(shard_paths, extra=extra)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
