"""RQ3 v2 --- the golden record from N anonymous noisy descriptions.

Pre-registered in ``docs/article/D_ART3/experiments/HEADLINE_DESIGN_2026-09-13.md``
sections 0-3, with the orchestrator's rulings of 2026-09-13 (word-space
``consensus_ow``; ``consensus_fact`` as the pre-registered fact-space ablation;
H3.5).  Every hypothesis, arm, metric and fallback is fixed before the run.

The question
------------
``N`` descriptions of one thing, written by different sources, disagree by a few
facts, and their constants are anonymous.  Which record is the reference?

Why v1 could not answer it, and what changed
--------------------------------------------
v1 asked the same question under conditions its own premise denied.  Its
majority merge read the constant identities every other method was refused, so
it was an oracle competing as a baseline; its medoids could only ever return a
member, which is a structural floor rather than a result; and its natural NDC
quarters tied under a gate that was underpowered.  v2 fixes the conditions:
every baseline is anonymous, the identity merge is labelled an oracle, the
strata are star / non-star (gate G0) because on a star the isomorphism class is
the multiset of fact patterns and plain counting recovers the source without any
alignment, and the two consensus arms are scored against each other so that the
word-space claim is not asserted where the fact-space computation would do.

The mechanism the design pre-states
-----------------------------------
A reference-anchored merge cannot recover a fact the reference lacks unless it
can align the constants of that fact across the members, and those constants are
exactly the ones the reference does not have.  The consensus has no reference:
it enumerates a neighbourhood of *every* member in the language and scores the
knowledge bases it decodes.  We therefore expect to win on the non-star strata
and to tie counting on the stars, and both are reported (H3.1, H3.4).

The objective, and why it is taken in the indel metric
------------------------------------------------------
``consensus_ow`` returns the **generalized median** of the members in word
space: the candidate minimising the summed distance from its own ``w°`` to each
member's.  The medoid is that same objective restricted to the members, so the
consensus cost is at most the medoid's by construction, and Prop 3's pairwise
bound lower-bounds the optimum over *every* point of the space --- which gives
the arm a certified ratio that a coverage objective cannot have.

The distance is the **indel** distance, not Levenshtein.  Levenshtein charges a
substitution one edit, and a substitution has no fact-level counterpart at unit
cost: replacing one fact's instruction by another's is one Levenshtein edit but
two fact edits.  The under-charge falls precisely on the candidates that compete
with the source.  On a star whose ``N`` members each drop one fact, the source
is 1 from every member and costs ``N``; two members differ by a fact swap, which
indel charges 2 and Levenshtein 1, so a member costs ``2(N-1)`` under indel and
``N-1`` under Levenshtein.  Under indel the source wins strictly for ``N >= 3``;
under Levenshtein it *ties* and the tie break decides.  Indel is also the metric
of the ball being enumerated, so objective and candidate set live in one
geometry.  ``consensus_ow_lev`` runs the Levenshtein median as the pre-registered
ablation that exhibits this, and ``consensus_ow_coverage`` the coverage-first
order; all three read one pool (:func:`build_ball_pool`), since they differ in
how they rank candidates and not in which candidates exist.
"""

from __future__ import annotations

import argparse
import csv
import logging
import random
import time
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np

from experiments.tkde import corpora, io
from experiments.tkde.budget import (
    CPP_ENGINE_ARMS,
    arm_fingerprint_screen,
    guarded_budget_call,
    symbol_distance,
)
from experiments.tkde.config import TkdeConfigError, TkdeError, load_yaml, results_root, seeds
from experiments.tkde.matrices import BUDGETED_MATRIX_ARMS
from experiments.tkde.rq1 import run_tag, table_file
from isalhg.core.instructions import parse
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.core.string_to_hypergraph import string_to_hypergraph
from isalhg.datasets.kb.base import KBCollection, KBRecord, compact, make_record
from isalhg.iso_backends.isal_ordered import ordered_fingerprint, ordered_symbols
from isalhg.language.consensus import coverage_consensus
from isalhg.language.majority import majority_merge
from isalhg.language.reach import compact_constants, fact_key_of, remove_facts
from isalhg.metric_space.toolkit.matrix import build_matrix
from isalhg.metric_space.toolkit.medoid import medoid

logger = logging.getLogger(__name__)

RQ = "RQ3v2"
RQ_INDEX = 32
RQ_DIR = "RQ3v2_golden_record"
EXPERIMENT = "anonymous_consensus"

#: The eleven distance arms of the campaign's standing rule (design section 1
#: rule 2).  Every one of them supplies a medoid row, and a medoid can only ever
#: return one of its inputs, so its exact recovery is 0 by construction --- the
#: structural floor the design asks to be printed rather than hidden.
MEDOID_ARMS: tuple[str, ...] = (
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
    "isal_ow_struct",
)

#: The arm whose medoid anchors ``align_merge_ref`` (design section 3).
REFERENCE_ARM = "bipartite_ged_assign"

#: The four noise edit kinds, drawn uniformly and independently per edit.
NOISE_KINDS: tuple[str, ...] = (
    "del_pendant",
    "del_interior",
    "ins_existing",
    "ins_new_constant",
)

#: Task baselines, in report order.  ``majority_merge_id`` reads the constant
#: identities the premise denies every other arm and is therefore labelled an
#: oracle everywhere it appears, never a competitor.
MERGE_METHODS: tuple[str, ...] = (
    "majority_merge_id",
    "align_merge_ref",
    "align_merge_iter",
    "pattern_vote",
)

CONSENSUS_METHODS: tuple[str, ...] = ("consensus_ow", "consensus_fact")

STRATA: tuple[str, ...] = ("star", "non_star")

ROWS_TABLE = "golden"

ROW_COLUMNS: tuple[str, ...] = (
    "rq",
    "experiment",
    "run_tag",
    "collection",
    "stratum",
    "seed",
    "git_sha",
    "host_cpu",
    "unit",
    "cell",
    "cell_N",
    "cell_t",
    "source_id",
    "collection_id",
    "N",
    "t",
    "method",
    "arm",
    "is_oracle",
    "radius",
    "secs",
    "censored",
    "reason",
    "exact_recovery",
    "fact_dist",
    "fact_dist_judge",
    "medoid_cost",
    "LB",
    "ratio",
    "n_censored_members",
    "pool_size",
    "pool_secs",
    "winner_origin",
    "winner_connected",
    "n_ties",
    "n_decoded",
    "n_decoded_connected",
    "coverage",
    "sub_record_drop",
    "edit_mix",
    "source_n",
    "source_m",
    "source_max_arity",
)

#: Slack over and above ``N`` per-member budgets for a guarded matrix build; it
#: covers the pairwise pass the per-member screen does not bound.
BUILD_MARGIN_S = 60.0

#: A knowledge base larger than this is not put to the exact oracle: E1' placed
#: the exact-HGED ceiling at n <= 10 (DATA.md section 4), and a pair above it
#: costs more than the row is worth.  Such rows are judged by
#: ``bipartite_ged_path`` and say so in ``fact_dist_judge``.
EXACT_HGED_MAX_N = 10

Fact = tuple[int, tuple[int, ...]]
Tokens = tuple[str, ...]


class RQ3v2Error(TkdeError):
    """An RQ3 v2 unit could not be built or evaluated as specified."""


# ---------------------------------------------------------------------------
# Gate G0 --- the star census, and the strata it defines
# ---------------------------------------------------------------------------


def constant_degrees(record: KBRecord) -> Counter[int]:
    """How many facts each constant of ``record`` occurs in."""
    occurrences: Counter[int] = Counter()
    for _predicate, members in record.facts:
        for constant in set(members):
            occurrences[constant] += 1
    return occurrences


def is_star(record: KBRecord) -> bool:
    """True when ``record`` is a star in the sense of gate G0.

    A star has one constant in *every* fact and no other constant in two or
    more, so its isomorphism class is the multiset of fact patterns and plain
    counting determines it.  WD50K's root is the entity and the definition
    recovers it without reading the metadata; NDC has no root, so an NDC record
    is a star only when such a constant happens to exist.

    Parameters
    ----------
    record : KBRecord
        The knowledge base.

    Returns
    -------
    bool
        Whether the record is a star.
    """
    occurrences = constant_degrees(record)
    m = len(record.facts)
    in_every = [v for v, count in occurrences.items() if count == m]
    shared = {v for v, count in occurrences.items() if count >= 2}
    return any(not (shared - {root}) for root in in_every)


def star_census(
    collection: KBCollection, window: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """Return the G0 census of ``collection``, optionally restricted to a window.

    Parameters
    ----------
    collection : KBCollection
        The frozen collection.
    window : Mapping or None, optional
        The source window; ``None`` censuses every record.

    Returns
    -------
    dict
        Counts and fractions per stratum, plus, for the non-stars, the median
        number of shared constants and of facts carrying one.
    """
    records = [r for r in collection.records if window is None or in_source_window(r, window)]
    stars = [r for r in records if is_star(r)]
    non_stars = [r for r in records if not is_star(r)]
    shared_counts: list[int] = []
    shared_facts: list[int] = []
    for record in non_stars:
        occurrences = constant_degrees(record)
        m = len(record.facts)
        in_every = [v for v, count in occurrences.items() if count == m]
        root = in_every[0] if in_every else None
        shared = {v for v, count in occurrences.items() if count >= 2} - (
            {root} if root is not None else set()
        )
        shared_counts.append(len(shared))
        shared_facts.append(sum(1 for _p, mem in record.facts if any(v in shared for v in mem)))

    def median(values: Sequence[int]) -> int | None:
        return sorted(values)[len(values) // 2] if values else None

    return {
        "collection": collection.name,
        "n_records": len(records),
        "n_stars": len(stars),
        "n_non_stars": len(non_stars),
        "frac_star": round(len(stars) / len(records), 4) if records else None,
        "non_star_median_shared_constants": median(shared_counts),
        "non_star_median_shared_facts": median(shared_facts),
    }


def in_source_window(record: KBRecord, window: Mapping[str, Any]) -> bool:
    """Whether ``record`` may be a source: inside the window and carrying identities."""
    return (
        int(window["n_min"]) <= record.n <= int(window["n_max"])
        and int(window["m_min"]) <= record.m <= int(window["m_max"])
        and record.max_arity <= int(window["max_arity"])
        and record.constant_ids is not None
    )


def eligible_sources(
    collection: KBCollection, window: Mapping[str, Any], stratum: str
) -> list[KBRecord]:
    """Sources of one stratum inside the window, in collection order."""
    want_star = stratum == "star"
    return [
        record
        for record in collection.records
        if in_source_window(record, window) and is_star(record) == want_star
    ]


# ---------------------------------------------------------------------------
# The noise model --- four edit kinds, mixed, R3-connected, anonymized
# ---------------------------------------------------------------------------


def _delete_fact(record: KBRecord, index: int, kb_id: str) -> KBRecord | None:
    """``record`` without fact ``index``, compacted; ``None`` when R3 fails."""
    kept = [fact for i, fact in enumerate(record.facts) if i != index]
    if not kept:
        return None
    return compact(
        kb_id,
        list(record.types),
        kept,
        constant_ids=None if record.constant_ids is None else list(record.constant_ids),
        label=record.label,
        meta={"n_types": record.n_types, "n_preds": record.n_preds},
        require_connected=True,
    )


def pendant_facts(record: KBRecord) -> list[int]:
    """Facts carrying a constant of degree 1 whose removal leaves R3 satisfied.

    Deleting a pendant fact takes a constant out of the knowledge base with it,
    which is the regime a reference-anchored merge cannot repair: the missing
    constant has no counterpart in the reference to align to.
    """
    occurrences = constant_degrees(record)
    return [
        i
        for i, (_predicate, members) in enumerate(record.facts)
        if any(occurrences[v] == 1 for v in members)
        and _delete_fact(record, i, f"{record.kb_id}#p") is not None
    ]


def interior_facts(record: KBRecord) -> list[int]:
    """Facts every constant of which is shared, whose removal leaves R3 satisfied.

    Deleting an interior fact strands nothing, so every constant of the source
    still occurs in every member; this is the stratum where attachment, not
    alignment, is what a merge has to get right.
    """
    occurrences = constant_degrees(record)
    return [
        i
        for i, (_predicate, members) in enumerate(record.facts)
        if all(occurrences[v] >= 2 for v in members)
        and _delete_fact(record, i, f"{record.kb_id}#i") is not None
    ]


def apply_noise_edit(record: KBRecord, kind: str, rng: random.Random) -> KBRecord | None:
    """Apply one edit of ``kind`` to ``record``; ``None`` when it admits none.

    Parameters
    ----------
    record : KBRecord
        The knowledge base to perturb.
    kind : str
        One of :data:`NOISE_KINDS`.
    rng : random.Random
        The seeded generator.

    Returns
    -------
    KBRecord or None
        The edited record, connected and non-empty, or ``None``.

    Raises
    ------
    RQ3v2Error
        If ``kind`` is not a noise kind.
    """
    if kind == "del_pendant":
        pool = pendant_facts(record)
        return _delete_fact(record, rng.choice(pool), f"{record.kb_id}#dp") if pool else None
    if kind == "del_interior":
        pool = interior_facts(record)
        return _delete_fact(record, rng.choice(pool), f"{record.kb_id}#di") if pool else None
    if kind not in ("ins_existing", "ins_new_constant"):
        raise RQ3v2Error(f"unknown noise kind {kind!r}; expected one of {NOISE_KINDS}")

    arities = sorted({len(members) for _p, members in record.facts})
    existing = set(record.facts)
    ids = record.constant_ids
    if kind == "ins_existing":
        for _attempt in range(60):
            arity = max(2, min(rng.choice(arities), record.n))
            candidate: Fact = (
                rng.randrange(record.n_preds),
                tuple(sorted(rng.sample(range(record.n), arity))),
            )
            if candidate in existing:
                continue
            return make_record(
                f"{record.kb_id}#ie",
                record.n,
                list(record.types),
                [*record.facts, candidate],
                constant_ids=None if ids is None else list(ids),
                label=record.label,
                meta={"n_types": record.n_types, "n_preds": record.n_preds},
                require_connected=True,
            )
        return None

    arity = max(2, min(rng.choice(arities), record.n + 1))
    entrant = record.n
    others = rng.sample(range(record.n), arity - 1)
    candidate = (rng.randrange(record.n_preds), tuple(sorted((entrant, *others))))
    return make_record(
        f"{record.kb_id}#inc",
        record.n + 1,
        [*record.types, rng.randrange(record.n_types)],
        [*record.facts, candidate],
        constant_ids=None if ids is None else [*ids, f"{record.kb_id}::new{record.n}"],
        label=record.label,
        meta={"n_types": record.n_types, "n_preds": record.n_preds},
        require_connected=True,
    )


def anonymize(record: KBRecord, rng: random.Random, kb_id: str) -> KBRecord:
    """Relabel ``record``'s constants by a random permutation.

    The premise is that the descriptions are anonymous: a constant *index* must
    carry no information linking one member to another.  The identities travel
    with the permutation so that the evaluation and the identity oracle still
    address the same objects; no anonymous method ever reads them.

    Parameters
    ----------
    record : KBRecord
        The member to anonymize.
    rng : random.Random
        The seeded generator.
    kb_id : str
        Identifier of the result.

    Returns
    -------
    KBRecord
        The same knowledge base under a permuted constant numbering.
    """
    order = list(range(record.n))
    rng.shuffle(order)
    # ``order[new] = old``; invert it to rewrite the facts.
    position = {old: new for new, old in enumerate(order)}
    facts = [
        (predicate, tuple(sorted(position[v] for v in members)))
        for predicate, members in record.facts
    ]
    ids = record.constant_ids
    return KBRecord(
        kb_id=kb_id,
        n=record.n,
        types=tuple(record.types[old] for old in order),
        facts=tuple(sorted(facts)),
        constant_ids=None if ids is None else tuple(ids[old] for old in order),
        label=record.label,
        meta=dict(record.meta),
    )


@dataclass(frozen=True)
class NoisyCollection:
    """``N`` anonymized variants of one source, and what produced them.

    Parameters
    ----------
    members : tuple[KBRecord, ...]
        The descriptions, anonymized, pairwise distinct as fact sets and each
        distinct from the source.
    edit_mix : Mapping[str, int]
        The realised count per edit kind over the whole collection.  The
        pre-stated mechanism is only testable against the mix that actually
        occurred, so it is logged rather than assumed uniform.
    attempts : int
        How many resampling rounds the collection cost.
    """

    members: tuple[KBRecord, ...]
    edit_mix: Mapping[str, int]
    attempts: int


def noisy_collection(
    source: KBRecord,
    n_members: int,
    t: int,
    seed: int,
    *,
    kinds: Sequence[str] = NOISE_KINDS,
    max_attempts: int = 40,
) -> NoisyCollection | None:
    """Build one collection: ``N`` members, ``t`` mixed edits each, anonymized.

    Each member receives ``t`` independent edits whose kinds are drawn uniformly
    from ``kinds``.  Every intermediate stays connected and non-empty (R3), the
    member differs from the source as a fact set, and the members are pairwise
    distinct.  The fact-level distance from member to source is ``t`` by
    construction only when the edits do not cancel; they cannot, because a
    deletion never re-inserts and an insertion never inserts a fact already
    present.

    Parameters
    ----------
    source : KBRecord
        The truth, inside the source window and carrying identities.
    n_members : int
        ``N``.
    t : int
        Edits per member.
    seed : int
        Seed of the local generator.
    kinds : Sequence of str, optional
        The kinds drawn from; the design's default is all four.
    max_attempts : int, optional
        Resampling rounds per member.

    Returns
    -------
    NoisyCollection or None
        The collection, or ``None`` when a member could not be built.
    """
    rng = random.Random(f"rq3v2|{source.kb_id}|{n_members}|{t}|{seed}")
    members: list[KBRecord] = []
    mix: Counter[str] = Counter()
    seen: set[frozenset[Fact]] = {frozenset(source.fact_set())}
    attempts = 0
    for index in range(n_members):
        built: KBRecord | None = None
        for _attempt in range(max_attempts):
            attempts += 1
            working: KBRecord | None = source
            applied: list[str] = []
            for _step in range(t):
                kind = rng.choice(list(kinds))
                assert working is not None
                working = apply_noise_edit(working, kind, rng)
                if working is None:
                    break
                applied.append(kind)
            if working is None:
                continue
            key = frozenset(working.fact_set())
            if key in seen:
                continue
            seen.add(key)
            mix.update(applied)
            built = anonymize(working, rng, f"{source.kb_id}#m{index}N{n_members}t{t}s{seed}")
            break
        if built is None:
            return None
        members.append(built)
    return NoisyCollection(tuple(members), dict(mix), attempts)


# ---------------------------------------------------------------------------
# The evaluation axis --- iso-invariant, because the output need not be a member
# ---------------------------------------------------------------------------


def certificate(H: SparseHypergraph) -> tuple[int, str]:
    """Return the ordered-walk fingerprint ``(root type, w-degree word)``.

    ``w°`` is a complete isomorphism invariant (Theorem C), so certificate
    equality *is* isomorphism.  Exact recovery is measured with it rather than
    with a fact-level comparison because a consensus output carries no constant
    identities: it is a decoded word, not a member, which is the whole point of
    the arm.
    """
    root_label, word = ordered_fingerprint(H)
    return int(root_label), word


def exact_hged_applicable(H1: SparseHypergraph, H2: SparseHypergraph) -> bool:
    """Whether the pair is inside the measured exact-oracle ceiling."""
    return max(H1.n_nodes, H2.n_nodes) <= EXACT_HGED_MAX_N


def fact_level_distance(
    H: SparseHypergraph, truth: SparseHypergraph, timeout_s: float | None
) -> tuple[float, str]:
    """Return ``(distance, judge)`` between a returned record and the truth.

    The exact hypergraph edit distance is the axis the design fixes, and it is
    iso-invariant, so it scores an output that is not a member.  Above the
    measured ceiling, or on a timeout, the row is judged by
    ``bipartite_ged_path`` and says so, which is the flagging the design asks
    for rather than a silent substitution.

    Parameters
    ----------
    H : SparseHypergraph
        The record a method returned.
    truth : SparseHypergraph
        The source.
    timeout_s : float or None
        Wall-clock budget for one exact call.

    Returns
    -------
    tuple
        The distance and the name of the judge that produced it.
    """
    from isalhg.errors import IsalHGError
    from isalhg.metric_space.distances.hged import ExactHGED
    from isalhg.metric_space.registry import get_distance

    if exact_hged_applicable(H, truth):
        try:
            return float(ExactHGED(timeout=timeout_s).pairwise(H, truth)), "exact_hged"
        except (IsalHGError, ValueError, RuntimeError) as exc:
            logger.info("exact oracle declined the pair (%s); falling back", exc)
    fallback = get_distance("bipartite_ged_path")
    return float(fallback.pairwise(H, truth)), "bipartite_ged_path"


def identity_facts(H: SparseHypergraph, names: Sequence[str]) -> frozenset[tuple[int, frozenset]]:
    """``H``'s facts addressed by external constant identity (evaluation only)."""
    return frozenset(
        (label, frozenset(names[v] for v in members)) for _e, members, label in H.iter_edges()
    )


# ---------------------------------------------------------------------------
# The anonymous merge baselines
# ---------------------------------------------------------------------------


def _scipy_lsa() -> tuple[Any, Any]:
    from scipy.optimize import linear_sum_assignment

    return linear_sum_assignment, np


def align_to_reference(member: SparseHypergraph, reference: SparseHypergraph) -> dict[int, int]:
    """Hungarian correspondence from ``member``'s constants to ``reference``'s.

    Uses the campaign's own Riesen-Bunke assignment --- the same construction
    the ``bipartite_ged_assign`` arm scores with, and therefore the same one
    that chose the reference --- so the baseline is aligned by its own
    machinery rather than by a second, weaker rule written for it.  The map is
    partial: a constant the assignment deletes has no image.
    """
    from isalhg.metric_space.distances.hged import _bipartite_matching

    lsa, numpy_module = _scipy_lsa()
    return _bipartite_matching(member, reference, lsa, numpy_module)


def _rebuild(
    n_nodes: int,
    types: Sequence[int],
    facts: Iterable[tuple[int, tuple[int, ...]]],
    template: SparseHypergraph,
) -> SparseHypergraph:
    """Assemble a hypergraph over the template's vocabularies."""
    ordered = sorted({(label, tuple(sorted(members))) for label, members in facts})
    return SparseHypergraph(
        n_nodes,
        [frozenset(members) for _label, members in ordered],
        n_vertex_labels=template.n_vertex_labels,
        n_edge_labels=template.n_edge_labels,
        vertex_labels=list(types),
        edge_labels=[label for label, _members in ordered],
    )


def align_merge_ref(members: Sequence[SparseHypergraph], reference_index: int) -> SparseHypergraph:
    """Majority vote in the reference's coordinates, after a Hungarian alignment.

    Every member is aligned to the reference and votes on facts expressed in the
    reference's constant numbering; a fact over a constant the alignment left
    unmatched is dropped, because there is no coordinate to cast it in.  That
    drop is the mechanism the design pre-states: a fact the reference lacks
    names constants the reference lacks, so it cannot be voted back in.
    """
    reference = members[reference_index]
    votes: Counter[tuple[int, tuple[int, ...]]] = Counter()
    for index, member in enumerate(members):
        if index == reference_index:
            mapping: dict[int, int] = {v: v for v in range(member.n_nodes)}
        else:
            mapping = align_to_reference(member, reference)
        for _e, member_set, label in member.iter_edges():
            if all(v in mapping for v in member_set):
                votes[(label, tuple(sorted(mapping[v] for v in member_set)))] += 1
    kept = [fact for fact, count in votes.items() if 2 * count > len(members)]
    types = [reference.vertex_label(v) for v in range(reference.n_nodes)]
    return _rebuild(reference.n_nodes, types, kept, reference)


def align_merge_iter(
    members: Sequence[SparseHypergraph], reference_index: int, rounds: int = 3
) -> SparseHypergraph:
    """``align_merge_ref`` re-aligned to its own output, admitting new constants.

    After each round the merged record becomes the alignment target.  A constant
    that no member could match is admitted when at least half the members carry
    an unmatched constant of the same type participating in the same fact
    pattern (predicate and arity): that is the strongest reconstruction of an
    N-way alignment available without solving one, and it is what a practitioner
    would write.
    """
    current = align_merge_ref(members, reference_index)
    total = len(members)
    for _round in range(max(0, rounds - 1)):
        if current.n_nodes == 0:
            break
        votes: Counter[tuple[int, tuple[int, ...]]] = Counter()
        orphan_votes: Counter[tuple[int, int, int]] = Counter()
        orphan_examples: dict[tuple[int, int, int], list[tuple[int, tuple[int, ...]]]] = (
            defaultdict(list)
        )
        for member in members:
            mapping = align_to_reference(member, current)
            for _e, member_set, label in member.iter_edges():
                matched = [v for v in member_set if v in mapping]
                if len(matched) == len(member_set):
                    votes[(label, tuple(sorted(mapping[v] for v in member_set)))] += 1
                    continue
                unmatched = [v for v in member_set if v not in mapping]
                if len(unmatched) != 1:
                    continue
                pattern = (label, len(member_set), member.vertex_label(unmatched[0]))
                orphan_votes[pattern] += 1
                orphan_examples[pattern].append((label, tuple(sorted(mapping[v] for v in matched))))
        kept = [fact for fact, count in votes.items() if 2 * count > total]
        types = [current.vertex_label(v) for v in range(current.n_nodes)]
        for pattern, count in orphan_votes.items():
            if 2 * count < total:
                continue
            anchor = Counter(orphan_examples[pattern]).most_common(1)[0][0]
            entrant = len(types)
            types.append(pattern[2])
            kept.append((anchor[0], tuple(sorted((*anchor[1], entrant)))))
        current = _rebuild(len(types), types, kept, current)
    return current


def _fact_pattern(H: SparseHypergraph, edge: int) -> tuple[int, int, tuple[int, ...]]:
    """``(predicate, arity, sorted multiset of constant types)`` of one fact."""
    members = H.members(edge)
    return (
        H.edge_label(edge),
        len(members),
        tuple(sorted(H.vertex_label(v) for v in members)),
    )


def pattern_vote(members: Sequence[SparseHypergraph]) -> SparseHypergraph:
    """Alignment-free majority over fact patterns, assembled around a hub.

    A pattern is ``(predicate, arity, multiset of constant types)``.  On a star
    the isomorphism class *is* the multiset of patterns, so this recovers the
    source exactly without any alignment --- which is why it is the control the
    design expects to tie us there (H3.4).  On a non-star the patterns do not
    determine the attachments, and the stated heuristic applies: each fact is
    attached to the highest-degree constants of matching type available, a new
    constant being created when none is.
    """
    total = len(members)
    # The vote is on *multiplicity*, not on presence. On a star the isomorphism
    # class is the multiset of fact patterns, so a baseline that recorded only
    # which patterns occur would rebuild a one-fact record from a four-fact star
    # and would lose the control it exists to provide. The kept multiplicity of
    # a pattern is the largest c such that strictly more than half the members
    # carry at least c copies of it.
    per_member: list[Counter[tuple[int, int, tuple[int, ...]]]] = []
    for member in members:
        seen: Counter[tuple[int, int, tuple[int, ...]]] = Counter()
        for edge in range(member.n_edges):
            seen[_fact_pattern(member, edge)] += 1
        per_member.append(seen)
    kept: list[tuple[int, int, tuple[int, ...]]] = []
    for pattern in sorted({p for seen in per_member for p in seen}):
        multiplicity = 0
        for level in range(1, max(seen.get(pattern, 0) for seen in per_member) + 1):
            if 2 * sum(1 for seen in per_member if seen.get(pattern, 0) >= level) > total:
                multiplicity = level
            else:
                break
        kept.extend([pattern] * multiplicity)
    if not kept:
        kept = sorted({p for seen in per_member for p in seen})[:1]
    template = members[0]
    # A hub of the modal type carries every fact, which is the star assembly;
    # the remaining slots are filled by the highest-degree constant of the
    # matching type, creating one when the pool is empty.
    hub_type = Counter(
        member.vertex_label(v) for member in members for v in range(member.n_nodes)
    ).most_common(1)[0][0]
    # Which types are shared, decided from what the members show rather than
    # from the answer.  A type counts as shared when some member holds *two or
    # more* constants of it at degree >= 2: one such constant is exactly the
    # star's hub, and treating its type as shared would attach every fact to the
    # same leaf, turning a four-leaf star into a two-constant record and erasing
    # the control the star stratum exists to provide.  Where a type is shared
    # the stated heuristic applies --- attach to the highest-degree constant of
    # matching type --- and where it is not, the assembly grows a fresh leaf,
    # which is the star assembly.
    shared_types: set[int] = set()
    for member in members:
        hubs: Counter[int] = Counter()
        for v in range(member.n_nodes):
            if member.degree(v) >= 2:
                hubs[member.vertex_label(v)] += 1
        shared_types |= {label for label, count in hubs.items() if count >= 2}

    types: list[int] = [hub_type]
    degree: Counter[int] = Counter()
    facts: list[tuple[int, tuple[int, ...]]] = []
    emitted: set[tuple[int, tuple[int, ...]]] = set()
    for predicate, arity, slot_types in kept:
        remaining = list(slot_types)
        if hub_type in remaining:
            remaining.remove(hub_type)
        # Two passes. The first follows the heuristic; if it reproduces a fact
        # already emitted the second creates fresh constants instead, because a
        # repeated pattern in the vote means a second fact of that shape and a
        # knowledge base cannot hold the same fact twice.
        for fresh in (False, True):
            chosen: list[int] = [0]
            grown: list[int] = []
            for slot_type in remaining[: max(0, arity - 1)]:
                pool = [
                    v
                    for v in range(len(types))
                    if types[v] == slot_type and v not in chosen and v != 0
                ]
                if pool and not fresh and slot_type in shared_types:
                    pick = max(pool, key=lambda v: (degree[v], -v))
                else:
                    pick = len(types) + len(grown)
                    grown.append(slot_type)
                chosen.append(pick)
            while len(chosen) < arity:
                chosen.append(len(types) + len(grown))
                grown.append(hub_type)
            candidate = (predicate, tuple(sorted(chosen)))
            if candidate not in emitted or fresh:
                types.extend(grown)
                for v in chosen:
                    degree[v] += 1
                facts.append(candidate)
                emitted.add(candidate)
                break
    return _rebuild(len(types), types, facts, template)


# ---------------------------------------------------------------------------
# consensus_ow --- the ball-coverage consensus in the w-degree language
# ---------------------------------------------------------------------------


def word_tokens(H: SparseHypergraph) -> tuple[int, Tokens]:
    """``(root type, ordered-walk token sequence)`` of ``H``."""
    root_label, word = ordered_fingerprint(H)
    return int(root_label), tuple(token.serialize() for token in parse(word))


def word_symbols(H: SparseHypergraph) -> tuple[Any, ...]:
    """``w°`` as one symbol per instruction --- the alphabet ``d_I`` measures over.

    A multi-digit field such as ``P[10]`` counts once, not four times (L7), and
    the seed type is prepended exactly when the vertex vocabulary is non-trivial
    (L8), which is the campaign's frozen ``isal_ow_struct`` convention.
    """
    return ordered_symbols(H)


def indel_distance(a: Sequence[Any], b: Sequence[Any]) -> int:
    """Insertions and deletions only: ``|a| + |b| - 2 |LCS(a, b)|``.

    The metric of the ball this arm enumerates, and therefore the one its
    objective must be written in.  Levenshtein charges a *substitution* one edit,
    and a substitution has no fact-level counterpart at unit cost: replacing one
    fact's instruction by another's is one Levenshtein edit but two fact edits, a
    deletion and an insertion.  The under-charging falls precisely on the
    candidates that compete with the source.

    On the star fixture the consequence is exact.  Each member is the source
    minus one fact, so under indel the source is 1 from every member and costs
    ``N``; two members differ by a fact swap, which is 2 under indel and 1 under
    Levenshtein, so a member costs ``2(N - 1)``.  Under indel the source wins
    strictly for every ``N >= 3``; under Levenshtein it ties at ``N = 4`` and the
    tie break decides.

    Parameters
    ----------
    a, b : Sequence
        Symbol sequences, comparable by equality.

    Returns
    -------
    int
        The indel distance.
    """
    from rapidfuzz.distance import Indel

    return int(Indel.distance(list(a), list(b)))


#: The two word metrics this experiment measures in. ``indel`` is the primary,
#: because it is the metric of the enumerated ball; ``levenshtein`` is the
#: pre-registered ablation that exhibits the substitution effect.
WORD_METRICS: dict[str, Callable[[Sequence[Any], Sequence[Any]], int]] = {
    "indel": indel_distance,
    "levenshtein": lambda a, b: int(symbol_distance(tuple(a), tuple(b))),
}


def word_matrix(symbols: Sequence[Sequence[Any]], metric: str) -> Any:
    """The members' ``N x N`` word-distance matrix under ``metric``.

    Parameters
    ----------
    symbols : Sequence of Sequence
        One symbol sequence per member, in row order.
    metric : str
        A key of :data:`WORD_METRICS`.

    Returns
    -------
    numpy.ndarray
        Symmetric ``float64`` with a zero diagonal.
    """
    distance = WORD_METRICS[metric]
    size = len(symbols)
    D = np.zeros((size, size), dtype=np.float64)
    for i in range(size):
        for j in range(i + 1, size):
            D[i, j] = D[j, i] = float(distance(symbols[i], symbols[j]))
    return D


def is_sub_record(candidate: SparseHypergraph, truth: SparseHypergraph, max_drop: int = 3) -> int:
    """Whether ``candidate`` is the truth with at most ``max_drop`` facts removed.

    Pre-registered for H3.6.  The word median can prefer a knowledge base
    *smaller* than the source at small ``N``, because dropping a fact one member
    lacks saves that member an insertion --- 5 to 10 tokens in the measured
    locality profile --- and costs the other ``N - 1`` a deletion of about one
    token each.  Whether the shortfall is a sub-record or an arbitrary object is
    the difference between a legible failure mode and an unexplained one, so the
    row carries it.

    Returns
    -------
    int
        The number of facts dropped, or ``-1`` when the candidate is not a
        sub-record within ``max_drop``.
    """
    target = fact_key_of(candidate)
    if target == fact_key_of(truth):
        return 0
    for size in range(1, min(max_drop, truth.n_edges) + 1):
        for drop in combinations(range(truth.n_edges), size):
            reduced = remove_facts(truth, drop)
            if reduced.n_edges == 0:
                continue
            if fact_key_of(reduced) == target:
                return size
    return -1


def indel_ball(word: Tokens, radius: int, vocabulary: Sequence[str]) -> dict[Tokens, int]:
    """Every token sequence within ``radius`` insertions and deletions of ``word``.

    Substitutions are excluded, matching the reach the design fixes: a
    substitution would collapse the ``2t`` gap between two members.  The empty
    sequence is never produced --- it decodes to no knowledge base.

    Returns
    -------
    dict[Tokens, int]
        Each word mapped to the shell it first appeared in.  Because the shells
        are generated breadth-first over *single* edits, that index is the word's
        exact indel distance from the centre, which is what the objective's
        second criterion sums; deriving it from the length difference instead
        would score an insert-and-delete pair as distance 0.
    """
    seen: dict[Tokens, int] = {word: 0}
    frontier: list[Tokens] = [word]
    for shell in range(1, max(0, radius) + 1):
        following: list[Tokens] = []
        for current in frontier:
            for i in range(len(current)):
                candidate = current[:i] + current[i + 1 :]
                if candidate and candidate not in seen:
                    seen[candidate] = shell
                    following.append(candidate)
            for i in range(len(current) + 1):
                for token in vocabulary:
                    candidate = current[:i] + (token,) + current[i:]
                    if candidate not in seen:
                        seen[candidate] = shell
                        following.append(candidate)
        frontier = following
    return seen


def restricted_ball(
    word: Tokens, vocabulary: Sequence[str], append: int, delete: int
) -> dict[Tokens, int]:
    """The design's fallback ball: append at most ``append``, delete at most ``delete``.

    Appending is bounded to the end of the program and deleting is free in
    position, which is the asymmetry the ordered walk earns: a fact appended to
    a knowledge base extends the walk, while a deleted fact removes instructions
    wherever they sat.  The value is the number of edits applied, so it is the
    same currency as :func:`indel_ball`'s shell index.
    """
    out: dict[Tokens, int] = {word: 0}
    tails: dict[Tokens, int] = {(): 0}
    for _ in range(max(0, append)):
        grown = {tail + (token,): cost + 1 for tail, cost in tails.items() for token in vocabulary}
        for tail, cost in grown.items():
            if cost < tails.get(tail, cost + 1):
                tails[tail] = cost
            tails.setdefault(tail, cost)
    for tail, cost in tails.items():
        candidate = word + tail
        if cost < out.get(candidate, cost + 1):
            out[candidate] = cost
        out.setdefault(candidate, cost)
    for size in range(1, max(0, delete) + 1):
        for drop in combinations(range(len(word)), size):
            candidate = tuple(t for i, t in enumerate(word) if i not in drop)
            if candidate and size < out.get(candidate, size + 1):
                out[candidate] = size
            elif candidate:
                out.setdefault(candidate, size)
    return out


def decode_word(tokens: Tokens, k: int, n_types: int, n_preds: int, root: int) -> SparseHypergraph:
    """Decode one token sequence back to a knowledge base.

    Total by Prop. C.4: the alphabet is closed, so the interpreter never
    rejects and every result is a connected knowledge base.  The pilot measured
    that on 426,433 decoded words without an exception or a disconnected result.
    """
    return string_to_hypergraph(
        ";".join(tokens),
        k=k,
        n_vertex_labels=n_types,
        n_edge_labels=n_preds,
        seed_label=root,
        backend="python",
    )


def _structure_key(H: SparseHypergraph) -> tuple:
    """A cheap decode-collapse key, paid before the canonical key."""
    return (
        H.n_nodes,
        tuple(sorted(H.vertex_label(v) for v in range(H.n_nodes))),
        tuple(sorted((label, tuple(sorted(members))) for _e, members, label in H.iter_edges())),
    )


@dataclass(frozen=True)
class ConsensusOutcome:
    """What one consensus call contributes to a row.

    Parameters
    ----------
    kb : SparseHypergraph
        The representative the objective selected.
    coverage : int
        Members whose ball reached the winning class.
    sum_reach : float
        The winning value of the objective's distance criterion.
    origin : str
        ``"member:<i>"`` when the winner is an input, ``"decoded:non_member"``
        when it is an object no member wrote --- the claim RQ3 makes, so the row
        states it rather than leaving it to be inferred.
    n_ties : int
        Candidates the first two criteria could not separate from the winner.
    pool_size, pool_secs : int, float
        Size of the deduplicated candidate set and the enumeration's wall-clock;
        the cost is part of the argument, so it is persisted.
    n_decoded, n_decoded_connected : int
        Words decoded and how many decoded to a connected knowledge base. Their
        equality is the ambient decodability of Prop. C.4, measured rather than
        asserted (L19).
    cost, lower_bound, ratio, medoid_cost : float
        The generalized-median cost of the winner, Prop 3's pairwise lower bound
        on the optimum over *every* point of the space, their ratio, and the
        medoid's cost for comparison. ``cost <= medoid_cost`` by construction,
        because every member is itself a candidate.
    """

    kb: SparseHypergraph
    coverage: int
    sum_reach: float
    origin: str
    n_ties: int
    pool_size: int
    pool_secs: float
    n_decoded: int
    n_decoded_connected: int
    cost: float = float("nan")
    lower_bound: float = float("nan")
    ratio: float = float("nan")
    medoid_cost: float = float("nan")


def consensus_ow(
    members: Sequence[SparseHypergraph],
    k: int,
    n_types: int,
    n_preds: int,
    radius: int,
    *,
    ball: str = "indel",
    append: int = 3,
    delete: int = 2,
    objective: str = "distance_first",
    tie_break: str = "fingerprint",
    metric: str = "indel",
) -> ConsensusOutcome:
    """Ball-coverage consensus over the ``w°`` language.

    For every member, enumerate the token ball of its ordered-walk word over the
    collection's own vocabulary --- the instructions some description actually
    wrote --- and decode every word.  Group the results by canonical key and
    score each class by how many *distinct* members reached it, breaking ties by
    the summed minimal token distance from the members that did and then by the
    shortlex of the class's own ``w°``.  Coverage is read off the enumeration,
    so no separate reach is computed.

    The candidate is a word.  It decodes to a knowledge base whether or not any
    member wrote it down, which is the property no certificate and no vector
    has, and the reason the arm can return the source when every member is
    ``t`` edits away from it.

    Parameters
    ----------
    members : Sequence[SparseHypergraph]
        The descriptions.
    k, n_types, n_preds : int
        The collection's alphabet scope; every member decodes under one.
    radius : int
        Ball radius in single-token edits.
    ball : {"indel", "restricted"}, optional
        Which family to enumerate.  ``"restricted"`` is the design's fallback.
    append, delete : int, optional
        Bounds of the restricted family.
    objective : {"distance_first", "coverage_first"}, optional
        Which lexicographic order selects the winner.  ``"distance_first"``
        (default, and the pre-registered primary) is the generalized median in
        the word metric: minimise ``sum_i d_I(w(M), w(K_i))``, ties by coverage,
        then by the shortlex of ``w``.  ``"coverage_first"`` is v1's order, kept
        as the named ablation.

        The two differ because the *word ball* is not symmetric in what it
        reaches, even though the metric is: the pilot measured a single fact
        deletion at a median of 1 token and a single fact insertion at 5--10
        (gate G3.1b1), so inside a fixed radius every member can delete its way
        to a common core while none can insert its way to a larger object.
        Coverage therefore carries a bias toward knowledge bases *smaller* than
        the source, and the summed distance does not.  In fact space, where
        ``reach'`` charges an insertion and a deletion alike, no such bias
        exists and coverage is the natural first criterion --- which is why v1
        used it.

    Returns
    -------
    ConsensusOutcome
        The winner, its objective values, and the census of the enumeration.

    Raises
    ------
    RQ3v2Error
        If ``members`` is empty or the enumeration produced no class.
    """
    pool = build_ball_pool(
        members, k, n_types, n_preds, radius, ball=ball, append=append, delete=delete
    )
    return select_consensus(
        pool, members, radius, objective=objective, tie_break=tie_break, metric=metric
    )


@dataclass(frozen=True)
class BallPool:
    """The decoded candidate set, built once and scored under several objectives.

    The three ``consensus_ow`` arms differ only in how they *rank* the candidates
    --- metric, first criterion, tie break --- and not at all in which candidates
    exist.  Enumerating the ball once and scoring it three times is therefore
    three times cheaper than three calls, and it also makes the arms exactly
    comparable: they see the same pool by construction rather than by trusting
    the enumeration to be deterministic.

    Parameters
    ----------
    reached : dict
        Per class key, the set of member indices whose ball reached it.
    representative : dict
        Per class key, one decoded knowledge base of that class.
    member_symbols : tuple
        Each member's ``w°`` symbol sequence, in member order.
    n_decoded, n_decoded_connected : int
        Words decoded, and how many decoded to a connected knowledge base.
    secs : float
        Wall-clock of the enumeration.
    """

    reached: Mapping[Any, set[int]]
    representative: Mapping[Any, SparseHypergraph]
    member_symbols: tuple[tuple[Any, ...], ...]
    n_decoded: int
    n_decoded_connected: int
    secs: float


def build_ball_pool(
    members: Sequence[SparseHypergraph],
    k: int,
    n_types: int,
    n_preds: int,
    radius: int,
    *,
    ball: str = "indel",
    append: int = 3,
    delete: int = 2,
) -> BallPool:
    """Enumerate and decode the members' token balls; see :class:`BallPool`."""
    if not members:
        raise RQ3v2Error("consensus_ow needs at least one member")
    started = time.perf_counter()
    roots: list[int] = []
    words: list[Tokens] = []
    for H in members:
        root, tokens = word_tokens(H)
        roots.append(root)
        words.append(tokens)
    vocabulary = tuple(sorted({token for word in words for token in word}))

    reached: dict[Any, set[int]] = defaultdict(set)
    representative: dict[Any, SparseHypergraph] = {}
    n_decoded = 0
    n_connected = 0
    for index, word in enumerate(words):
        shell = (
            indel_ball(word, radius, vocabulary)
            if ball == "indel"
            else restricted_ball(word, vocabulary, append, delete)
        )
        # The ordered walk is a program: token order decides the decode, so the
        # ball must not be collapsed by a multiset signature. Decode every
        # distinct word and collapse on the decoded structure, which is cheap,
        # before paying for the canonical key.
        structures: dict[tuple, tuple[SparseHypergraph, int]] = {}
        for candidate, distance in shell.items():
            try:
                decoded = decode_word(candidate, k, n_types, n_preds, roots[index])
            except Exception as exc:  # noqa: BLE001 - a closed alphabet must not reject
                logger.warning("a ball word did not decode: %s", exc)
                continue
            n_decoded += 1
            if decoded.is_connected():
                n_connected += 1
            key = _structure_key(decoded)
            known = structures.get(key)
            if known is None or distance < known[1]:
                structures[key] = (decoded, distance)
        for decoded, _distance in structures.values():
            if decoded.n_nodes == 0 or not decoded.is_connected():
                continue
            class_key = fact_key_of(decoded)
            reached[class_key].add(index)
            representative.setdefault(class_key, decoded)

    if not representative:
        raise RQ3v2Error("the ball enumeration produced no in-domain class")
    return BallPool(
        reached=reached,
        representative=representative,
        member_symbols=tuple(word_symbols(H) for H in members),
        n_decoded=n_decoded,
        n_decoded_connected=n_connected,
        secs=time.perf_counter() - started,
    )


def select_consensus(
    pool: BallPool,
    members: Sequence[SparseHypergraph],
    radius: int,
    *,
    objective: str = "distance_first",
    tie_break: str = "fingerprint",
    metric: str = "indel",
) -> ConsensusOutcome:
    """Rank an already-enumerated :class:`BallPool` and return the winner."""
    reached = pool.reached
    representative = pool.representative
    member_symbols = list(pool.member_symbols)
    started = pool.secs

    if objective not in ("coverage_first", "distance_first"):
        raise RQ3v2Error(
            f"objective must be 'coverage_first' or 'distance_first'; got {objective!r}"
        )
    if tie_break not in ("shortlex", "fingerprint"):
        raise RQ3v2Error(f"tie_break must be 'shortlex' or 'fingerprint'; got {tie_break!r}")
    if metric not in WORD_METRICS:
        raise RQ3v2Error(f"metric must be one of {sorted(WORD_METRICS)}; got {metric!r}")
    distance = WORD_METRICS[metric]

    # The cost is the generalized-median objective in the word metric: the sum of
    # the distances from the candidate's own w-degree to each member's. It is not
    # the BFS shell index, which measures a raw word's distance to one centre
    # rather than the class's distance to all of them. Because the members are
    # themselves candidates, the winning cost is at most the medoid's, and Prop 3's
    # pairwise bound LB = sum_{i<j} d(K_i, K_j) / (N - 1) lower-bounds the optimum
    # over every point of the space --- so the arm carries a certified ratio,
    # which a coverage objective cannot. The bound is taken in the SAME metric the
    # cost is, or the ratio compares two different quantities.
    bound = medoid(word_matrix(member_symbols, metric))

    scored: list[tuple[float, int, tuple[int, tuple[str, ...]], Any]] = []
    values: dict[Any, tuple[int, float]] = {}
    for class_key, hits in reached.items():
        # One ordered walk per class, not one per (class, member): the candidate's
        # own word does not depend on which member it is being compared with, and
        # recomputing it inside the sum made the scoring loop cost N times what it
        # should --- on the axis H3.6 varies, which is the worst place for it.
        candidate_symbols = word_symbols(representative[class_key])
        cost = float(sum(distance(candidate_symbols, symbols) for symbols in member_symbols))
        coverage = len(hits)
        values[class_key] = (coverage, cost)
        primary, secondary = (
            (float(-coverage), int(cost)) if objective == "coverage_first" else (cost, -coverage)
        )
        serialized = tuple(str(s) for s in candidate_symbols)
        # The final tie break. Under the indel metric it is rarely decisive --- the
        # source separates strictly from its sub-records --- but under Levenshtein
        # it decided the answer outright, and shortlex decided it *downward*: the
        # shorter word is the smaller record, so the ball's size bias reappeared
        # here. "fingerprint" orders by the augmented fingerprint alone, which is
        # size-neutral and is the order v1's consensus already uses for this
        # purpose; it is the primary. "shortlex" is retained only so that the bias
        # stays documented by a test.
        order = (len(serialized), serialized) if tie_break == "shortlex" else (0, serialized)
        scored.append((primary, secondary, order, class_key))
    scored.sort()
    best = scored[0]
    n_ties = sum(1 for entry in scored if entry[0] == best[0] and entry[1] == best[1]) - 1
    winner_key = best[3]
    winner = representative[winner_key]
    winner_coverage, winner_cost = values[winner_key]
    member_keys = {fact_key_of(H): i for i, H in enumerate(members)}
    origin = (
        f"member:{member_keys[winner_key]}" if winner_key in member_keys else "decoded:non_member"
    )
    return ConsensusOutcome(
        kb=winner,
        coverage=winner_coverage,
        sum_reach=winner_cost,
        origin=origin,
        n_ties=n_ties,
        pool_size=len(representative),
        pool_secs=started,
        n_decoded=pool.n_decoded,
        n_decoded_connected=pool.n_decoded_connected,
        cost=winner_cost,
        lower_bound=bound.lower_bound,
        ratio=(
            winner_cost / bound.lower_bound
            if bound.lower_bound
            else (1.0 if winner_cost == 0 else float("inf"))
        ),
        medoid_cost=bound.cost,
    )


def consensus_fact(
    members: Sequence[SparseHypergraph], radius: int, alignment_budget: str = "triangle"
) -> ConsensusOutcome:
    """The pre-registered fact-space ablation (H3.5).

    The same coverage objective computed in fact space by v1's ``reach'``
    machinery: candidates come from pairwise alignment transfers rather than
    from a token ball, and coverage counts members within fact reach ``r``.  It
    is representation-free, so it is what a reviewer will ask for, and running
    it is how the word-space claim is bounded rather than asserted.
    """
    started = time.perf_counter()
    result = coverage_consensus(members, radius, alignment_budget=alignment_budget)  # type: ignore[arg-type]
    return ConsensusOutcome(
        kb=result.kb,
        coverage=result.coverage,
        sum_reach=result.sum_reach,
        origin=result.origin,
        n_ties=result.n_ties,
        pool_size=result.n_candidates,
        pool_secs=time.perf_counter() - started,
        n_decoded=result.n_candidates + result.n_disconnected,
        n_decoded_connected=result.n_candidates,
    )


# ---------------------------------------------------------------------------
# Medoids --- the structural floor, printed rather than hidden
# ---------------------------------------------------------------------------


def run_guarded(fn: Callable[[], Any], budget_s: float, *, cpp_engine: bool = False) -> Any:
    """Run ``fn`` in a forked child killed after ``budget_s``; ``None`` on failure."""
    result = guarded_budget_call(fn, (), budget_s, cpp_engine=cpp_engine)
    if not result.ok:
        return None
    return result.value


def medoid_matrix(
    members: Sequence[SparseHypergraph],
    member_ids: Sequence[str],
    arm: str,
    budget_s: float | None,
) -> Any:
    """One collection's ``N x N`` matrix under the arm's process model."""

    def build() -> Any:
        return build_matrix(list(members), arm, member_ids=list(member_ids), cache_dir=None)

    if arm not in CPP_ENGINE_ARMS:
        return np.asarray(build(), dtype=np.float64)
    ceiling = len(members) * float(budget_s or 0.0) + BUILD_MARGIN_S
    value = run_guarded(build, ceiling, cpp_engine=True)
    if value is None:
        raise RQ3v2Error(f"guarded matrix build for arm {arm!r} did not finish")
    return np.asarray(value, dtype=np.float64)


def censored_members(
    arm: str,
    members: Sequence[SparseHypergraph],
    member_ids: Sequence[str],
    budget_s: float,
) -> tuple[str, ...]:
    """Ids whose representation under ``arm`` did not finish in ``budget_s``."""
    screen = arm_fingerprint_screen(arm, budget_s)
    return tuple(kb_id for kb_id, H in zip(member_ids, members, strict=True) if not screen(H))


# ---------------------------------------------------------------------------
# One collection: every arm, every method
# ---------------------------------------------------------------------------


def _blank_row(shared: Mapping[str, Any], **overrides: Any) -> dict[str, Any]:
    """A row with every optional column blank, then ``overrides`` applied."""
    row: dict[str, Any] = {
        **shared,
        "arm": "",
        "is_oracle": 0,
        "radius": "",
        "secs": "",
        "censored": 0,
        "reason": "",
        "exact_recovery": "",
        "fact_dist": "",
        "fact_dist_judge": "",
        "medoid_cost": "",
        "LB": "",
        "ratio": "",
        "n_censored_members": "",
        "pool_size": "",
        "pool_secs": "",
        "winner_origin": "",
        "winner_connected": "",
        "n_ties": "",
        "n_decoded": "",
        "n_decoded_connected": "",
        "coverage": "",
        "sub_record_drop": "",
    }
    row.update(overrides)
    return row


def _score(
    H: SparseHypergraph,
    truth_H: SparseHypergraph,
    truth_cert: tuple[int, str],
    timeout_s: float | None,
) -> dict[str, Any]:
    """Exact recovery and fact-level distance of one returned record.

    A merge can return a record outside the language's domain --- empty, or
    disconnected because the facts it voted in no longer hang together.  Such a
    record has no ordered walk, so it cannot be isomorphic to the source, which
    is connected: exact recovery is 0, not blank.  The fact-level distance is
    still measured, because the edit distance is defined on it and the row would
    otherwise hide how far off the output was.  ``reason`` carries the domain
    failure, which is itself a measured property of the baseline and the column
    the capability table reads.
    """
    # A knowledge base is its set of facts (D-KBf5), so a constant no surviving
    # fact names has left it. Every method's output is compacted before it is
    # scored, which is a normalisation and not a repair: without it the identity
    # oracle loses at t = 1 purely because ``majority_merge`` carries the union
    # of the identities, including a constant whose only fact lost the vote.
    H, _survivors = compact_constants(H)
    reason = ""
    if H.n_nodes == 0 or not H.is_connected():
        recovered = 0
        reason = "returned record is outside the language domain (empty or disconnected)"
    else:
        try:
            recovered = int(certificate(H) == truth_cert)
        except Exception as exc:  # noqa: BLE001 - a degenerate output must not kill the unit
            logger.info("certificate refused a returned record: %s", exc)
            return {
                "exact_recovery": "",
                "fact_dist": "",
                "fact_dist_judge": "",
                "reason": f"{type(exc).__name__}: {exc}"[:160],
            }
    try:
        distance, judge = fact_level_distance(H, truth_H, timeout_s)
    except Exception as exc:  # noqa: BLE001 - a judge failure must not kill the unit
        logger.info("no judge could score a returned record: %s", exc)
        return {
            "exact_recovery": recovered,
            "fact_dist": "",
            "fact_dist_judge": "",
            "reason": (reason or f"{type(exc).__name__}: {exc}")[:160],
        }
    return {
        "exact_recovery": recovered,
        "fact_dist": distance,
        "fact_dist_judge": judge,
        "reason": reason,
    }


def evaluate_collection(
    *,
    members: Sequence[KBRecord],
    truth: KBRecord,
    collection: KBCollection,
    arms: Sequence[str],
    radius: int,
    shared: Mapping[str, Any],
    fingerprint_budget_s: float | None,
    hged_timeout_s: float | None,
    method_budget_s: float,
    ball: str,
    append: int,
    delete: int,
    objective: str,
    objective_ablation: bool,
    tie_break: str,
    metric: str,
) -> list[dict[str, Any]]:
    """Run every arm and method on one collection and return its rows."""
    n_types, n_preds = collection.n_types, collection.n_preds
    members_H = [r.to_hypergraph(n_types=n_types, n_preds=n_preds) for r in members]
    member_ids = [r.kb_id for r in members]
    identities = [tuple(r.constant_ids or ()) for r in members]
    truth_H = truth.to_hypergraph(n_types=n_types, n_preds=n_preds)
    truth_cert = certificate(truth_H)
    k = max(collection.k_max, truth.max_arity, *(r.max_arity for r in members))
    rows: list[dict[str, Any]] = []

    # The members' medoid under the same indel metric the consensus minimises, so
    # the certified ratios are comparable. A ratio under Levenshtein and a ratio
    # under indel are two different quantities and must never be read against
    # each other; the `medoid:isal_ow_struct` row below is the Levenshtein one and
    # stays for the cross-representation table.
    started = time.perf_counter()
    try:
        indel_bound = medoid(word_matrix([word_symbols(H) for H in members_H], "indel"))
        indel_scored = _score(members_H[indel_bound.index], truth_H, truth_cert, hged_timeout_s)
        rows.append(
            _blank_row(
                shared,
                method="medoid",
                arm="isal_ow_indel",
                secs=time.perf_counter() - started,
                medoid_cost=indel_bound.cost,
                LB=indel_bound.lower_bound,
                ratio=indel_bound.ratio,
                **indel_scored,
            )
        )
    except Exception as exc:  # noqa: BLE001 - one dead arm must not kill the unit
        logger.warning("isal_ow_indel medoid failed on %s: %s", shared.get("collection_id"), exc)
        rows.append(
            _blank_row(
                shared,
                method="medoid",
                arm="isal_ow_indel",
                secs=time.perf_counter() - started,
                censored=1,
                reason=f"{type(exc).__name__}: {exc}"[:160],
            )
        )

    reference_index = 0
    for arm in arms:
        started = time.perf_counter()
        screened = fingerprint_budget_s is not None and arm in BUDGETED_MATRIX_ARMS
        dropped = (
            censored_members(arm, members_H, member_ids, float(fingerprint_budget_s or 0.0))
            if screened
            else ()
        )
        if dropped:
            rows.append(
                _blank_row(
                    shared,
                    method="medoid",
                    arm=arm,
                    secs=time.perf_counter() - started,
                    censored=1,
                    reason=f"{len(dropped)} of {len(members_H)} members censored by the screen",
                    n_censored_members=len(dropped),
                )
            )
            continue
        try:
            D = medoid_matrix(members_H, member_ids, arm, fingerprint_budget_s)
            result = medoid(D)
            scored = _score(members_H[result.index], truth_H, truth_cert, hged_timeout_s)
            if arm == REFERENCE_ARM:
                reference_index = int(result.index)
            rows.append(
                _blank_row(
                    shared,
                    method="medoid",
                    arm=arm,
                    secs=time.perf_counter() - started,
                    n_censored_members=0 if screened else "",
                    medoid_cost=result.cost,
                    LB=result.lower_bound,
                    ratio=result.ratio,
                    **scored,
                )
            )
        except Exception as exc:  # noqa: BLE001 - one dead arm must not kill the unit
            logger.warning("arm %s failed on %s: %s", arm, shared.get("collection_id"), exc)
            rows.append(
                _blank_row(
                    shared,
                    method="medoid",
                    arm=arm,
                    secs=time.perf_counter() - started,
                    censored=1,
                    reason=f"{type(exc).__name__}: {exc}"[:160],
                    n_censored_members=0 if screened else "",
                )
            )

    merges: dict[str, Callable[[], SparseHypergraph]] = {
        "majority_merge_id": lambda: majority_merge(members_H, identities)[0],
        "align_merge_ref": lambda: align_merge_ref(members_H, reference_index),
        "align_merge_iter": lambda: align_merge_iter(members_H, reference_index),
        "pattern_vote": lambda: pattern_vote(members_H),
    }
    for name, method in merges.items():
        started = time.perf_counter()
        try:
            merged = method()
            scored = _score(merged, truth_H, truth_cert, hged_timeout_s)
            rows.append(
                _blank_row(
                    shared,
                    method=name,
                    arm="identities" if name == "majority_merge_id" else "anonymous",
                    is_oracle=int(name == "majority_merge_id"),
                    secs=time.perf_counter() - started,
                    **scored,
                )
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("%s failed on %s: %s", name, shared.get("collection_id"), exc)
            rows.append(
                _blank_row(
                    shared,
                    method=name,
                    arm="identities" if name == "majority_merge_id" else "anonymous",
                    is_oracle=int(name == "majority_merge_id"),
                    secs=time.perf_counter() - started,
                    censored=1,
                    reason=f"{type(exc).__name__}: {exc}"[:160],
                )
            )

    # The ball arms differ only in how they RANK the candidates, never in which
    # candidates exist, so the pool is enumerated once and scored several times.
    # That is the dominant cost divided by the number of arms, and it also makes
    # the arms exactly comparable: they see one pool by construction rather than
    # by trusting three enumerations to agree.
    #
    # `_lev` changes only the metric and so exhibits the substitution effect ---
    # Levenshtein charges a fact swap 1 where indel charges 2, and the
    # under-charge lands on exactly the candidates that compete with the source.
    # `_coverage` changes only the objective's first criterion.
    other_metric = "levenshtein" if metric == "indel" else "indel"
    other_objective = "distance_first" if objective == "coverage_first" else "coverage_first"
    rankings: list[tuple[str, str, str]] = [("consensus_ow", objective, metric)]
    if objective_ablation:
        rankings.append(("consensus_ow_lev", objective, other_metric))
        rankings.append(("consensus_ow_coverage", other_objective, metric))

    def ball_arms() -> dict[str, ConsensusOutcome]:
        pool = build_ball_pool(
            members_H, k, n_types, n_preds, radius, ball=ball, append=append, delete=delete
        )
        return {
            name: select_consensus(
                pool,
                members_H,
                radius,
                objective=objective_name,
                tie_break=tie_break,
                metric=metric_name,
            )
            for name, objective_name, metric_name in rankings
        }

    started = time.perf_counter()
    bundled = run_guarded(ball_arms, method_budget_s, cpp_engine=False)
    ball_secs = time.perf_counter() - started
    for name, _objective_name, _metric_name in rankings:
        outcome = None if bundled is None else bundled.get(name)
        rows.append(
            _consensus_row(
                shared,
                name,
                outcome,
                radius,
                ball_secs,
                method_budget_s,
                truth_H,
                truth_cert,
                hged_timeout_s,
            )
        )

    consensus_calls: dict[str, Callable[[], ConsensusOutcome]] = {
        "consensus_fact": lambda: consensus_fact(members_H, radius),
    }
    for name, call in consensus_calls.items():
        started = time.perf_counter()
        # It reaches the engine in a child; the parent never canonicalizes, so no
        # later guarded fork can be censored for a poisoning this process caused.
        outcome = run_guarded(call, method_budget_s, cpp_engine=True)
        rows.append(
            _consensus_row(
                shared,
                name,
                outcome,
                radius,
                time.perf_counter() - started,
                method_budget_s,
                truth_H,
                truth_cert,
                hged_timeout_s,
            )
        )
    return rows


def _consensus_row(
    shared: Mapping[str, Any],
    name: str,
    outcome: ConsensusOutcome | None,
    radius: int,
    secs: float,
    budget_s: float,
    truth_H: SparseHypergraph,
    truth_cert: tuple[int, str],
    hged_timeout_s: float | None,
) -> dict[str, Any]:
    """One consensus arm's row, censored or scored."""
    arm = "fact_reach" if name == "consensus_fact" else "isal_ow_struct"
    if outcome is None:
        return _blank_row(
            shared,
            method=name,
            arm=arm,
            radius=radius,
            secs=secs,
            censored=1,
            reason=f"budget {budget_s:.0f} s exceeded or the call failed",
        )
    scored = _score(outcome.kb, truth_H, truth_cert, hged_timeout_s)
    try:
        drop: Any = is_sub_record(outcome.kb, truth_H)
    except Exception as exc:  # noqa: BLE001 - an H3.6 label must not kill the unit
        logger.info("sub-record test declined a winner: %s", exc)
        drop = ""
    return _blank_row(
        shared,
        method=name,
        arm=arm,
        radius=radius,
        secs=secs,
        pool_size=outcome.pool_size,
        pool_secs=round(outcome.pool_secs, 4),
        winner_origin=outcome.origin,
        winner_connected=int(outcome.kb.is_connected()),
        n_ties=outcome.n_ties,
        n_decoded=outcome.n_decoded,
        n_decoded_connected=outcome.n_decoded_connected,
        coverage=outcome.coverage,
        sub_record_drop=drop,
        medoid_cost=outcome.medoid_cost,
        LB=outcome.lower_bound,
        ratio=outcome.ratio,
        **scored,
    )


# ---------------------------------------------------------------------------
# Unit enumeration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Unit:
    """One cell and seed: a corpus, a stratum, ``N``, ``t``, holding its sources."""

    collection: str
    stratum: str
    n_members: int
    t: int
    seed: int

    @property
    def cell(self) -> str:
        return f"{self.stratum}_N{self.n_members}_t{self.t}"

    @property
    def unit_id(self) -> str:
        return f"{self.collection}-{self.cell}-s{self.seed}"


def enumerate_units(config: Mapping[str, Any]) -> list[Unit]:
    """Every unit of the design, in a fixed order."""
    block = config["design"]
    schedule = seeds(RQ_INDEX, int(config.get("seed_count", 27)))
    units: list[Unit] = []
    for collection in block["collections"]:
        for stratum in block.get("strata", STRATA):
            for n_members in block["n_values"]:
                for t in block["t_values"]:
                    for seed in schedule:
                        units.append(
                            Unit(str(collection), str(stratum), int(n_members), int(t), int(seed))
                        )
    return units


def unit_is_done(paths: io.RunPaths, unit: Unit, tag: str) -> bool:
    """True when this unit's tagged row file exists and parses.

    The authority is the *tagged* file name, never a row read back out of an
    untagged aggregate.  RQ3 v1 skipped units by re-reading its own aggregated
    rows, so when the arm set changed the runner served rows that contained no
    Isal arm at all under a manifest claiming otherwise (T-KBn).  A tag over the
    measured configuration makes that failure impossible: a changed arm set is a
    changed tag and therefore a different file.
    """
    target = paths.dir / f"rows_{table_file(tag, ROWS_TABLE, unit.unit_id)}.csv"
    if not target.is_file():
        return False
    try:
        with target.open(encoding="utf-8", newline="") as handle:
            header = next(csv.reader(handle))
    except (OSError, StopIteration, UnicodeDecodeError):
        return False
    return "run_tag" in header


def run_unit(
    unit: Unit,
    config: Mapping[str, Any],
    collection: KBCollection,
    pool: Sequence[KBRecord],
    base: Mapping[str, Any],
    tag: str,
) -> tuple[list[dict[str, Any]], int]:
    """Run one unit; return ``(rows, dropped collections)``."""
    block = config["design"]
    arms = tuple(config.get("medoid_arms", MEDOID_ARMS))
    kinds = tuple(block.get("noise_kinds", NOISE_KINDS))
    sources_per_cell = int(block["sources_per_cell"])
    shared_base = {
        **base,
        "rq": RQ,
        "experiment": EXPERIMENT,
        "run_tag": tag,
        "collection": unit.collection,
        "stratum": unit.stratum,
        "seed": unit.seed,
        "unit": unit.unit_id,
        "cell": unit.cell,
        "cell_N": unit.n_members,
        "cell_t": unit.t,
        "N": unit.n_members,
        "t": unit.t,
    }
    if not pool:
        # A structurally empty stratum is a measured fact of gate G0 (no NDC
        # member inside the source window is a star), so it is reported as a row
        # carrying its reason rather than as an absence.
        return [
            _blank_row(
                {
                    **shared_base,
                    "source_id": "",
                    "collection_id": "",
                    "method": "cell_empty",
                    "edit_mix": "",
                    "source_n": "",
                    "source_m": "",
                    "source_max_arity": "",
                },
                censored=1,
                reason=(
                    f"no member of {unit.collection} inside the source window is "
                    f"{'a star' if unit.stratum == 'star' else 'a non-star'} (gate G0)"
                ),
            )
        ], 0

    rng = random.Random(f"rq3v2|{unit.unit_id}")
    chosen = rng.sample(range(len(pool)), min(sources_per_cell, len(pool)))
    rows: list[dict[str, Any]] = []
    dropped = 0
    for index, source_index in enumerate(chosen):
        source = pool[source_index]
        built = noisy_collection(
            source, unit.n_members, unit.t, unit.seed * 1_000 + index, kinds=kinds
        )
        if built is None:
            dropped += 1
            logger.info("dropped collection: %s source=%s", unit.unit_id, source.kb_id)
            continue
        shared = {
            **shared_base,
            "source_id": source.kb_id,
            "collection_id": f"{unit.cell}|s{unit.seed}|{source.kb_id}",
            "edit_mix": built.edit_mix,
            "source_n": source.n,
            "source_m": source.m,
            "source_max_arity": source.max_arity,
        }
        rows.extend(
            evaluate_collection(
                members=built.members,
                truth=source,
                collection=collection,
                arms=arms,
                radius=int(block.get("radius", 2)),
                shared=shared,
                fingerprint_budget_s=_budget(config.get("fingerprint_budget_s")),
                hged_timeout_s=_budget(config.get("hged_timeout_s")),
                method_budget_s=float(config.get("method_budget_s", 1800)),
                ball=str(block.get("ball", "indel")),
                append=int(block.get("ball_append", 3)),
                delete=int(block.get("ball_delete", 2)),
                objective=str(block.get("objective", "distance_first")),
                objective_ablation=bool(block.get("objective_ablation", True)),
                tie_break=str(block.get("tie_break", "fingerprint")),
                metric=str(block.get("metric", "indel")),
            )
        )
    return rows, dropped


def _budget(value: Any) -> float | None:
    """Read a wall-clock budget from the config: ``None`` or a positive float."""
    if value is None:
        return None
    budget = float(value)
    return budget if budget > 0 else None


# ---------------------------------------------------------------------------
# Shard driver
# ---------------------------------------------------------------------------


def provenance() -> tuple[str, str]:
    """``(git_sha, host_cpu)`` for the universal row columns."""
    return str(io._repo_provenance()["git_sha"] or ""), io._cpu_model()


def run_shard(
    config: Mapping[str, Any],
    out: Path,
    shard: tuple[int, int],
    *,
    data_root: Path | None,
    start_cutoff_s: float | None,
) -> dict[str, Any]:
    """Execute one shard of the RQ3 v2 unit list.

    Parameters
    ----------
    config : Mapping
        The parsed configuration.
    out : Path
        Results root the rows are written under.
    shard : tuple of int
        ``(index, count)``, one-based index.
    data_root : Path or None
        Corpora root override.
    start_cutoff_s : float or None
        Refuse to *start* a unit after this many seconds; the shard's first unit
        is exempt, or the shard livelocks.

    Returns
    -------
    dict
        The shard's summary.
    """
    index, count = shard
    started = time.perf_counter()
    git_sha, host_cpu = provenance()
    base = {"git_sha": git_sha, "host_cpu": host_cpu}
    tag = run_tag(config)
    paths = io.RunPaths(root=out, rq=RQ_DIR, experiment=EXPERIMENT)
    paths.ensure()

    units = enumerate_units(config)
    mine = [unit for i, unit in enumerate(units) if i % count == index - 1]

    collections: dict[str, KBCollection] = {}
    window = config["design"]["source_window"]

    def load(name: str) -> KBCollection:
        if name not in collections:
            collections[name] = corpora.load_collection(name, data_root)
        return collections[name]

    summary: dict[str, Any] = {
        "shard": f"shard_{index:03d}of{count:03d}",
        "run_tag": tag,
        "n_units_total": len(units),
        "n_units_mine": len(mine),
        "n_units_executed": 0,
        "n_units_resumed": 0,
        "dropped_total": 0,
        "dropped_by_cell": {},
        "source_pools": {},
        "star_census": {},
        "deferred": [],
        "n_rows": 0,
    }

    pools: dict[tuple[str, str], list[KBRecord]] = {}
    for name in config["design"]["collections"]:
        collection = load(str(name))
        summary["star_census"][str(name)] = star_census(collection, window)
        for stratum in config["design"].get("strata", STRATA):
            key = (str(name), str(stratum))
            pools[key] = eligible_sources(collection, window, str(stratum))
            summary["source_pools"][f"{key[0]}|{key[1]}"] = {
                "n_pool": len(pools[key]),
                "status": "ok" if pools[key] else "structurally_empty",
            }

    executed = 0
    for unit in mine:
        if unit_is_done(paths, unit, tag):
            summary["n_units_resumed"] += 1
            continue
        if executed and start_cutoff_s and time.perf_counter() - started >= start_cutoff_s:
            summary["deferred"].append(unit.unit_id)
            continue
        collection = load(unit.collection)
        rows, dropped = run_unit(
            unit, config, collection, pools[(unit.collection, unit.stratum)], base, tag
        )
        io.write_rows(paths, table_file(tag, ROWS_TABLE, unit.unit_id), rows, columns=ROW_COLUMNS)
        summary["n_rows"] += len(rows)
        summary["dropped_total"] += dropped
        if dropped:
            cell = f"{unit.collection}|{unit.cell}"
            summary["dropped_by_cell"][cell] = summary["dropped_by_cell"].get(cell, 0) + dropped
        executed += 1
        logger.info("unit done: %s (%d rows)", unit.unit_id, len(rows))

    summary["n_units_executed"] = executed
    summary["secs"] = time.perf_counter() - started
    io.write_config(paths, {**dict(config), "derived": {"run_tag": tag, "shard": shard}})
    io.write_summary(paths, summary)
    io.write_manifest(
        paths,
        extra={"run_tag": tag, "shard": shard, "complete": not summary["deferred"]},
    )
    return summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_shard(text: str) -> tuple[int, int]:
    try:
        left, right = text.split("/")
        index, count = int(left), int(right)
    except ValueError as exc:
        raise TkdeConfigError(f"--shard expects 'i/N', got {text!r}") from exc
    if not 1 <= index <= count:
        raise TkdeConfigError(f"--shard index out of range: {text!r}")
    return index, count


def _apply_overlay(config: dict[str, Any], block: str) -> dict[str, Any]:
    """Shrink the configuration to the ``smoke`` or ``pilot`` overlay.

    The overlay is a genuine configuration change, so it enters the run tag and
    its rows can never be served to the full campaign: a smoke and the campaign
    share the unit-id namespace, and RQ3 v1's untagged files are exactly how two
    runs came to be indistinguishable on disk (T-KBn).  ``smoke`` is excluded
    from the tag payload for the same reason ``n_shards`` is --- it names which
    overlay ran, and the overlay's own parameters already carry the difference.
    """
    overlay = config.get(block) or {}
    merged = dict(config)
    merged["seed_count"] = int(overlay.get("seed_count", config.get("seed_count", 27)))
    merged["design"] = {**config["design"], **(overlay.get("design") or {})}
    for key in ("medoid_arms", "fingerprint_budget_s", "method_budget_s", "hged_timeout_s"):
        if key in overlay:
            merged[key] = overlay[key]
    merged["overlay"] = block
    merged["smoke"] = True
    return merged


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point of ``python -m experiments.tkde.rq3v2``."""
    parser = argparse.ArgumentParser(description="RQ3 v2 --- the golden record")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--shard", default="1/1")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--pilot", action="store_true", help="run the local pilot overlay")
    parser.add_argument("--count", action="store_true", help="print the unit count and exit")
    parser.add_argument("--census", action="store_true", help="print the G0 census and exit")
    parser.add_argument("--data-root", type=Path, default=None)
    parser.add_argument("--start-cutoff-s", type=float, default=None)
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, str(args.log_level).upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    config = load_yaml(args.config)
    if args.smoke and args.pilot:
        raise TkdeConfigError("--smoke and --pilot are two different overlays; pass one")
    if args.smoke:
        config = _apply_overlay(config, "smoke")
    elif args.pilot:
        config = _apply_overlay(config, "pilot")

    if args.count:
        print(len(enumerate_units(config)))
        return 0

    if args.census:
        import json

        window = config["design"]["source_window"]
        print(
            json.dumps(
                {
                    str(name): star_census(
                        corpora.load_collection(str(name), args.data_root), window
                    )
                    for name in config["design"]["collections"]
                },
                indent=2,
            )
        )
        return 0

    out = Path(args.out) if args.out is not None else results_root()
    summary = run_shard(
        config,
        out,
        _parse_shard(args.shard),
        data_root=args.data_root,
        start_cutoff_s=args.start_cutoff_s,
    )
    logger.info(
        "shard %s (tag %s): %d units, %d rows, %d dropped, %.1f s",
        summary["shard"],
        summary["run_tag"],
        summary["n_units_executed"],
        summary["n_rows"],
        summary["dropped_total"],
        summary["secs"],
    )
    if summary["deferred"]:
        logger.warning("deferred %d units at the start cutoff", len(summary["deferred"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
