"""RQ6 runner --- generation (DESIGN.md section 7).

Can a collection be extended with new, valid, plausible knowledge bases? The
fact alphabet answers yes by theorem: its decoder is total, so *every* sample of
a sequence model over fact words is a knowledge base and the validity rate is
1.000 by construction rather than by filtering. The comparison is a model of the
same order over a flat incidence-list serialization, whose strict decoder has to
reject a measurable fraction of its own samples.

Four exhibits are produced:

1. ``rows_samples`` --- 27 seeds x 10,000 samples per collection and model,
   with validity, the five fidelity divergences, novelty and the reach-1
   neighbourhood fraction; ``rows_rejections`` counts the baseline's rejection
   causes by rule.
2. ``rows_alignment`` --- the decodability figure's input: every interior word
   of a Levenshtein alignment between two real members, in both alphabets.
3. ``rows_completion`` --- the conditional-completion exhibit.

The reach-1 fraction is computed exactly, under ``reach'`` (D-KBf5): reach on
*compacted* remainders, so a deletion that isolates a constant removes it and the
constant count is not preserved. Candidates are filtered by
an inverted index over compacted remainder words; a sample with no member
inside the fact-count budget contributes no fraction rather than a zero.
"""

from __future__ import annotations

import argparse
import csv
import logging
import random
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from experiments.tkde import corpora, io
from experiments.tkde.config import TkdeConfigError, TkdeError, load_yaml, results_root, seeds
from experiments.tkde.rq3 import deploy_stamps, provenance, run_guarded
from isalhg.core.canonical import canonical_string, required_k
from isalhg.core.fact_word import Word, decode_fact_word
from isalhg.core.instructions import parse
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.core.string_to_hypergraph import string_to_hypergraph
from isalhg.datasets.kb.base import KBCollection
from isalhg.generation.fidelity import PROFILE_KEYS, fidelity, novelty
from isalhg.generation.incidence_baseline import flatten, strict_decode, strict_decode_reason
from isalhg.generation.ngram import TokenNGram
from isalhg.iso_backends.isal_ordered import ordered_fingerprint
from isalhg.language.alignment import alignment_path
from isalhg.language.reach import RemainderIndex, reach
from isalhg.metric_space.distances.fact_levenshtein import fact_word

logger = logging.getLogger(__name__)

RQ = "RQ6"
RQ_INDEX = 6
RQ_DIR = "RQ6_generation"
EXPERIMENT = "generation"
PARTS = "parts"

MODEL_OURS = "fact_ngram"
MODEL_BASELINE = "incidence_ngram"
#: The Isal instruction word of the ordered walk, modelled at the same order
#: over its own token alphabet. Its decoder is total *and* its image is
#: connected (Theorem C, Proposition 5.1), so validity and connectivity are both
#: 1.000 by theorem -- a strictly stronger guarantee than the fact alphabet's,
#: which is total but says nothing about connectivity.
MODEL_OW = "ow_ngram"
SAMPLE_MODELS: tuple[str, ...] = (MODEL_OURS, MODEL_OW, MODEL_BASELINE)

SAMPLE_COLUMNS: tuple[str, ...] = (
    "rq",
    "experiment",
    "collection",
    "seed",
    "arm",
    "git_sha",
    "host_cpu",
    "secs",
    "censored",
    "unit",
    "model",
    "roles",
    "n_samples",
    "n_valid",
    "n_rejected",
    "n_connected",
    "validity",
    "connectivity",
    "rejection_rate",
    "jsd_n",
    "jsd_m",
    "jsd_arity",
    "jsd_pred",
    "jsd_type",
    "novelty",
    "reach1_frac",
    "reach1_eligible",
    "reach1_hits",
)

REJECTION_COLUMNS: tuple[str, ...] = (
    "rq",
    "experiment",
    "collection",
    "seed",
    "arm",
    "git_sha",
    "host_cpu",
    "secs",
    "censored",
    "unit",
    "model",
    "reason",
    "count",
)

ALIGNMENT_COLUMNS: tuple[str, ...] = (
    "rq",
    "experiment",
    "collection",
    "seed",
    "arm",
    "git_sha",
    "host_cpu",
    "secs",
    "censored",
    "unit",
    "pair_id",
    "left_id",
    "right_id",
    "path_len",
    "n_interior",
    "n_decoded",
    "n_connected",
    "interior_n",
    "interior_m",
)

COMPLETION_COLUMNS: tuple[str, ...] = (
    "rq",
    "experiment",
    "collection",
    "seed",
    "arm",
    "git_sha",
    "host_cpu",
    "secs",
    "censored",
    "unit",
    "member_id",
    "n_prefix",
    "n_removed",
    "valid",
    "iso_original",
    "reach1",
)


class RQ6Error(TkdeError):
    """A RQ6 unit could not be built or evaluated as specified."""


# ---------------------------------------------------------------------------
# Collection-scoped, cached derivations
# ---------------------------------------------------------------------------


@dataclass
class CollectionContext:
    """Everything the RQ6 units need from one collection, computed once."""

    name: str
    collection: KBCollection
    roles: bool
    hypergraphs: list[SparseHypergraph]
    member_ids: list[str]
    words: list[Word]
    keys: list[Word]
    flat: list[tuple[tuple[Any, ...], ...]]
    n_types: int
    n_preds: int
    ow_words: list[tuple[str, ...]]
    ow_roots: list[int]
    k: int

    def model(self, kind: str) -> TokenNGram:
        """Return a freshly fitted order-3 model of one alphabet.

        Deliberately not cached across units. ``TokenNGram`` memoises one dense
        vector over the whole vocabulary per distinct sampling context, in a
        cache that is unbounded and reset only by ``fit``. A model shared across
        the 27 seeds therefore accumulates about 0.7 GB per 2,000 samples and
        reached 20.4 GB after eight units on ``wd50k66`` (job 2213221,
        OUT_OF_MEMORY). Refitting costs 0.15 s at the worst measured collection,
        and the memo cache dies with the model, so peak RSS is one unit's cache
        rather than the whole shard's.
        """
        started = time.perf_counter()
        source: Sequence[Any]
        if kind == MODEL_OURS:
            source = self.words
        elif kind == MODEL_OW:
            source = self.ow_words
        else:
            source = self.flat
        model = TokenNGram(order=3).fit(source)
        logger.info(
            "fitted %s on %s (%d words) in %.1f s",
            kind,
            self.name,
            len(source),
            time.perf_counter() - started,
        )
        return model


def _ow_word(H: SparseHypergraph) -> tuple[int, str]:
    """``(root vertex label, ordered-walk word)`` of ``H`` under the default policy."""
    root_label, word = ordered_fingerprint(H)
    return int(root_label), word


def _ow_tokens(word: str) -> tuple[str, ...]:
    """Tokenize an ordered-walk word into its surface tokens.

    Same rule as the pointer alphabet's: the instruction parser, never a split
    on ``";"``, because a token carries its own semicolons inside brackets
    (``V[0;1;2;0,2]``).
    """
    return tuple(token.serialize() for token in parse(word))


def _ow_decode(tokens: Sequence[str], k: int, n_types: int, n_preds: int, root: int) -> Any:
    """Decode one ordered-walk token sequence back to a hypergraph."""
    return string_to_hypergraph(
        ";".join(str(token) for token in tokens),
        k=k,
        n_vertex_labels=n_types,
        n_edge_labels=n_preds,
        seed_label=root,
        backend="python",
    )


def _ow_interiors(
    left: str,
    right: str,
    k: int,
    n_types: int,
    n_preds: int,
    root: int,
) -> tuple[int, int, list[tuple[int, int, bool]]]:
    """Decode every interior word of an ordered-walk alignment path.

    Proposition 5.1 says every one of them is a *connected* hypergraph, which
    is what the ``n_connected`` column of the row records against ``n_decoded``.
    """
    path = alignment_path(_ow_tokens(left), _ow_tokens(right))
    interiors = path[1:-1] if len(path) >= 2 else []
    decoded: list[tuple[int, int, bool]] = []
    for tokens in interiors:
        try:
            H = _ow_decode(tokens, k, n_types, n_preds, root)
        except Exception as exc:  # noqa: BLE001 - the closed alphabet must not reject
            logger.error("ordered-walk interior did not decode: %s", exc)
            continue
        decoded.append((H.n_nodes, H.n_edges, H.is_connected()))
    return len(path), len(interiors), decoded


def build_context(name: str, config: Mapping[str, Any], root: Path | None) -> CollectionContext:
    """Load one collection and precompute its words, keys and flat serializations."""
    collection = corpora.load_collection(name, root)
    roles = bool(config["roles"].get(name, False)) and collection.has_roles
    n_types, n_preds = collection.n_types, collection.n_preds
    hypergraphs = corpora.hypergraphs(collection)
    roles_maps = corpora.roles_maps(collection) if roles else [None] * len(hypergraphs)
    words = [fact_word(H, rm) for H, rm in zip(hypergraphs, roles_maps, strict=True)]
    keys = words if not roles else [fact_word(H) for H in hypergraphs]
    ordered = [_ow_word(H) for H in hypergraphs]
    return CollectionContext(
        name=name,
        collection=collection,
        roles=roles,
        hypergraphs=hypergraphs,
        member_ids=corpora.member_ids(collection),
        words=words,
        keys=keys,
        flat=[flatten(H) for H in hypergraphs],
        n_types=n_types,
        n_preds=n_preds,
        ow_words=[_ow_tokens(word) for _root, word in ordered],
        ow_roots=[root_label for root_label, _word in ordered],
        # The collection's k: every member has to decode under one alphabet, and
        # a sample's arity is bounded by the widest fact the model ever saw.
        k=max((required_k(H) for H in hypergraphs), default=2),
    )


# ---------------------------------------------------------------------------
# The reach-1 neighbourhood
# ---------------------------------------------------------------------------


def _deletion_keys(H: SparseHypergraph) -> dict[Word, int]:
    """``{compacted remainder word: fewest deletions reaching it}``, at most one deletion."""
    return RemainderIndex(H, 1).min_deletions()


class Reach1Index:
    """Answers "is this sample within reach 1 of some member?" exactly.

    Candidates come from an inverted index over compacted remainder words and
    the survivor is confirmed with :func:`isalhg.language.reach.reach`, so the
    recorded answer is the library's and not this index's.

    Two earlier shortcuts were unsound under ``reach'`` (D-KBf5) and are gone:

    * bucketing members by ``(constant count, type multiset)`` -- the *frozen*
      precondition. A deletion under ``reach'`` compacts away newly isolated
      constants, so the constant count is not preserved and equal-shape
      bucketing withheld exactly the pairs the definition admits;
    * a plausibility test mixing ``fact_word(sample)``, an **uncompacted** word,
      with :class:`RemainderIndex` keys, which are **compacted**. The two are
      not comparable, so the test could reject a genuine reach-1 pair.

    The shared-remainder test that replaces them is not a heuristic: ``reach'``
    is by definition the least ``|A| + |B|`` whose compacted remainders agree,
    so a common word within budget *is* the answer.

    Bucketing returns, on a key that **is** valid after compaction: the fact
    count. If ``reach'(K, K2) <= 1`` then the compacted remainders are
    isomorphic, hence carry the same number of facts, so
    ``m - |A| = m2 - |B|`` with ``|A| + |B| <= 1``; the only solutions are
    ``(0,0)``, ``(1,0)`` and ``(0,1)``, giving ``|m - m2| <= 1``. Scanning the
    three buckets ``m-1, m, m+1`` is therefore exact, and unlike the constant
    count the fact count *is* preserved up to the budget, because a deletion
    removes exactly one fact while compaction removes only constants.

    A scan over that window is still too slow to run: measured on the campaign's
    own collections the three buckets hold **1,112 of 1,381** members on
    ``ndc_classes`` (a 1.2x reduction -- fact counts take only 14 distinct
    values, so adjacent buckets hold nearly everything) and 1,502 of 3,988 on
    ``wd50k66``. At 1,000 samples per unit that is still millions of pair tests.

    So the lookup is inverted instead. Every member contributes its compacted
    remainder words to one dictionary, keyed by word and valued by
    ``(member, deletions)``. A sample is then answered with hash lookups over
    its own ``1 + m`` remainder words, independent of the number of members.

    The budget test stays ``ds + dm <= 1`` on a **shared** word, and that is
    load-bearing: testing whether the two level-1 *sets* intersect would admit
    ``K - a ~ K2 - b``, which is ``reach' = 2``. Since each ``d`` is 0 or 1, the
    sum rule admits exactly ``(0,0)``, ``(1,0)`` and ``(0,1)`` -- the three cases
    of ``reach' <= 1`` -- and nothing else.
    """

    def __init__(self, members: Sequence[SparseHypergraph]) -> None:
        self._members = list(members)
        self._by_facts: dict[int, int] = {}
        for H in self._members:
            self._by_facts[H.n_edges] = self._by_facts.get(H.n_edges, 0) + 1
        self._word_index: dict[Word, list[tuple[int, int]]] | None = None

    def _index(self) -> dict[Word, list[tuple[int, int]]]:
        """Build, once, the word -> ``[(member, deletions)]`` map."""
        if self._word_index is None:
            index: dict[Word, list[tuple[int, int]]] = {}
            for member, H in enumerate(self._members):
                for word, deletions in _deletion_keys(H).items():
                    index.setdefault(word, []).append((member, deletions))
            self._word_index = index
        return self._word_index

    def _eligible(self, sample: SparseHypergraph) -> bool:
        """Whether any member is inside the fact-count budget of ``sample``.

        The cheap, compaction-sound eligibility gate that replaces the frozen
        precondition: ``|m - m2| <= 1`` is necessary for ``reach' <= 1``, so a
        sample with no member in the window is genuinely incomparable and
        contributes no fraction. It is strictly more permissive than the old
        gate, which is the direction T-KBo requires.
        """
        m = sample.n_edges
        return any(self._by_facts.get(m + delta) for delta in (-1, 0, 1))

    def within_one(self, sample: SparseHypergraph) -> bool | None:
        """Whether some member is within ``reach' <= 1`` of ``sample``.

        Returns
        -------
        bool or None
            ``None`` when no member is within the fact-count budget of
            ``sample``, preserving the tri-state the callers expect: the
            question was not answerable rather than answered "no".
        """
        if not self._eligible(sample):
            return None
        index = self._index()
        for word, ds in _deletion_keys(sample).items():
            for member, dm in index.get(word, ()):
                if ds + dm <= 1 and reach(sample, self._members[member], r_max=1) is not None:
                    return True
        return False


# ---------------------------------------------------------------------------
# Unit 1 and 2 --- sampling, validity, fidelity
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SampleUnit:
    """One ``(collection, model, seed)`` sampling unit."""

    collection: str
    model: str
    seed: int

    @property
    def key(self) -> str:
        return f"S|{self.collection}|{self.model}|s{self.seed}"


def run_sample_unit(
    unit: SampleUnit,
    config: Mapping[str, Any],
    context: CollectionContext,
    reach_index: Reach1Index,
    base: Mapping[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Sample, decode, and score one unit; return ``(sample row, rejection rows)``."""
    n_samples = int(config["n_samples"])
    reach_subset = int(config["reach1_subset"])
    started = time.perf_counter()
    model = context.model(unit.model)
    words = model.sample(n_samples, seed=unit.seed, max_len=int(config.get("max_len", 200)))

    decoded: list[SparseHypergraph] = []
    reasons: dict[str, int] = {}
    n_rejected = 0
    # The ordered walk never writes the root's own type into the word, so a
    # sample needs one supplied. It is drawn from the fit corpus's empirical
    # root-type distribution under this unit's seed, which keeps the type
    # profile the fidelity table scores comparable to the collection's.
    root_rng = random.Random(f"rq6-ow-root|{unit.collection}|{unit.seed}")
    for word in words:
        if unit.model == MODEL_OURS:
            H, _ = decode_fact_word(word, n_types=context.n_types, n_preds=context.n_preds)
            decoded.append(H)
            continue
        if unit.model == MODEL_OW:
            root = root_rng.choice(context.ow_roots) if context.ow_roots else 0
            try:
                decoded.append(_ow_decode(word, context.k, context.n_types, context.n_preds, root))
            except Exception as exc:  # noqa: BLE001 - a total decoder must not raise
                # Proposition 5.1 says this branch is unreachable; it is kept so
                # a falsification is counted and named rather than crashing the
                # shard and losing the measurement that found it.
                logger.error("ordered-walk sample did not decode: %s", exc)
                n_rejected += 1
                reasons[type(exc).__name__] = reasons.get(type(exc).__name__, 0) + 1
            continue
        H_or_none = strict_decode(word, n_types=context.n_types, n_preds=context.n_preds)
        if H_or_none is None:
            n_rejected += 1
            reason = (
                strict_decode_reason(word, n_types=context.n_types, n_preds=context.n_preds)
                or "unknown"
            )
            reasons[reason] = reasons.get(reason, 0) + 1
            continue
        decoded.append(H_or_none)

    n_valid = len(decoded)
    n_connected = sum(1 for H in decoded if H.is_connected())
    row: dict[str, Any] = {
        **base,
        "rq": RQ,
        "experiment": EXPERIMENT,
        "collection": unit.collection,
        "seed": unit.seed,
        "arm": unit.model,
        "unit": unit.key,
        "model": unit.model,
        "roles": int(context.roles),
        "n_samples": n_samples,
        "n_valid": n_valid,
        "n_rejected": n_rejected,
        "n_connected": n_connected,
        "validity": n_valid / n_samples if n_samples else "",
        "connectivity": n_connected / n_valid if n_valid else "",
        "rejection_rate": n_rejected / n_samples if n_samples else "",
        "censored": 0,
    }

    if decoded:
        divergences = fidelity(decoded, context.hypergraphs)
        row.update(divergences)
        row["novelty"] = novelty([fact_word(H) for H in decoded], context.keys)
        subset = decoded[:reach_subset]
        eligible = hits = 0
        for H in subset:
            answer = reach_index.within_one(H)
            if answer is None:
                continue
            eligible += 1
            hits += int(answer)
        row["reach1_eligible"] = eligible
        row["reach1_hits"] = hits
        row["reach1_frac"] = hits / eligible if eligible else ""
    else:
        row.update({f"jsd_{name}": "" for name in PROFILE_KEYS})
        row["novelty"] = ""
        row["reach1_eligible"] = 0
        row["reach1_hits"] = 0
        row["reach1_frac"] = ""

    row["secs"] = time.perf_counter() - started
    rejection_rows = [
        {
            **base,
            "rq": RQ,
            "experiment": EXPERIMENT,
            "collection": unit.collection,
            "seed": unit.seed,
            "arm": unit.model,
            "unit": unit.key,
            "model": unit.model,
            "reason": reason,
            "count": count,
            "secs": "",
            "censored": 0,
        }
        for reason, count in sorted(reasons.items())
    ]
    return row, rejection_rows


# ---------------------------------------------------------------------------
# Unit 3 --- the decodability figure
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AlignmentUnit:
    """The decodability exhibit for one collection."""

    collection: str

    @property
    def key(self) -> str:
        return f"A|{self.collection}"


def _fact_interiors(
    left: Word,
    right: Word,
    n_types: int,
    n_preds: int,
) -> tuple[int, int, list[tuple[int, int, bool]]]:
    """Decode every interior word of a fact-alphabet alignment path.

    A failure here would falsify the totality of the decoder, so it is recorded
    as an undecoded interior and logged rather than allowed to abort the run.
    """
    path = alignment_path(left, right)
    interiors = path[1:-1] if len(path) >= 2 else []
    decoded: list[tuple[int, int, bool]] = []
    for word in interiors:
        try:
            H, _ = decode_fact_word(word, n_types=n_types, n_preds=n_preds)
        except Exception as exc:  # noqa: BLE001 - a total decoder must not raise
            logger.error("fact-alphabet interior did not decode: %s", exc)
            continue
        decoded.append((H.n_nodes, H.n_edges, H.is_connected()))
    return len(path), len(interiors), decoded


def _pointer_word(H: SparseHypergraph, k: int) -> str:
    """Canonical pointer-alphabet word of ``H`` under the C++ engine."""
    return canonical_string(H, k=k, algorithm="canonical", backend="cpp")


def _pointer_tokens(word: str) -> tuple[str, ...]:
    """Tokenize a pointer-alphabet word into its surface tokens."""
    return tuple(token.serialize() for token in parse(word))


def _pointer_interiors(
    left: str,
    right: str,
    k: int,
    n_types: int,
    n_preds: int,
) -> tuple[int, int, list[tuple[int, int, bool]]]:
    """Decode every interior word of a pointer-alphabet alignment path.

    The words are tokenized with the instruction parser, not by splitting on
    ``";"``: a pointer token carries its own semicolons inside brackets
    (``V[0;1;2;0,2]``), so a naive split cuts tokens in half and the interiors
    then fail to parse.
    """
    path = alignment_path(_pointer_tokens(left), _pointer_tokens(right))
    interiors = path[1:-1] if len(path) >= 2 else []
    decoded: list[tuple[int, int, bool]] = []
    for tokens in interiors:
        text = ";".join(str(token) for token in tokens)
        try:
            H = string_to_hypergraph(
                text,
                k=k,
                n_vertex_labels=n_types,
                n_edge_labels=n_preds,
                backend="python",
            )
        except Exception as exc:  # noqa: BLE001 - the closed alphabet must not reject
            logger.error("pointer-alphabet interior did not decode: %s", exc)
            continue
        decoded.append((H.n_nodes, H.n_edges, H.is_connected()))
    return len(path), len(interiors), decoded


def run_alignment_unit(
    unit: AlignmentUnit,
    config: Mapping[str, Any],
    context: CollectionContext,
    base: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Build the decodability rows for one collection, both alphabets."""
    block = config["alignment"]
    window = block["member_window"]
    budget = float(block.get("pointer_budget_s", 60))
    eligible = [
        index
        for index, H in enumerate(context.hypergraphs)
        if H.n_nodes <= int(window["n_max"]) and H.n_edges <= int(window["m_max"])
    ]
    if len(eligible) < 2:
        raise RQ6Error(f"{unit.collection}: fewer than two members inside the alignment window")
    rng = random.Random(f"rq6-alignment|{unit.collection}")
    n_pairs = int(block.get("n_pairs", 20))
    pairs = [tuple(rng.sample(eligible, 2)) for _ in range(n_pairs)]

    rows: list[dict[str, Any]] = []
    shared = {
        **base,
        "rq": RQ,
        "experiment": EXPERIMENT,
        "collection": unit.collection,
        "seed": 0,
        "unit": unit.key,
    }
    for pair_id, (i, j) in enumerate(pairs):
        left_H, right_H = context.hypergraphs[i], context.hypergraphs[j]
        started = time.perf_counter()
        path_len, n_interior, decoded = _fact_interiors(
            context.words[i], context.words[j], context.n_types, context.n_preds
        )
        rows.append(
            _alignment_row(
                shared,
                "fact_rank",
                pair_id,
                context.member_ids[i],
                context.member_ids[j],
                path_len,
                n_interior,
                decoded,
                time.perf_counter() - started,
                censored=0,
            )
        )

        started = time.perf_counter()
        k = max(required_k(left_H), required_k(right_H))
        left_root, left_ow = _ow_word(left_H)
        _right_root, right_ow = _ow_word(right_H)
        path_len, n_interior, decoded = _ow_interiors(
            left_ow, right_ow, k, context.n_types, context.n_preds, left_root
        )
        rows.append(
            _alignment_row(
                shared,
                "isal_ow_struct",
                pair_id,
                context.member_ids[i],
                context.member_ids[j],
                path_len,
                n_interior,
                decoded,
                time.perf_counter() - started,
                censored=0,
            )
        )

        started = time.perf_counter()
        status, value = run_guarded(
            lambda left_H=left_H, right_H=right_H, k=k: (
                _pointer_word(left_H, k),
                _pointer_word(right_H, k),
            ),
            budget,
        )
        if status != "ok":
            logger.warning("pointer word %s on pair %d: %s", status, pair_id, value)
            rows.append(
                _alignment_row(
                    shared,
                    "pointer",
                    pair_id,
                    context.member_ids[i],
                    context.member_ids[j],
                    "",
                    0,
                    [],
                    time.perf_counter() - started,
                    censored=1,
                )
            )
            continue
        left_word, right_word = value
        path_len, n_interior, decoded = _pointer_interiors(
            left_word, right_word, k, context.n_types, context.n_preds
        )
        rows.append(
            _alignment_row(
                shared,
                "pointer",
                pair_id,
                context.member_ids[i],
                context.member_ids[j],
                path_len,
                n_interior,
                decoded,
                time.perf_counter() - started,
                censored=0,
            )
        )
    return rows


def _alignment_row(
    shared: Mapping[str, Any],
    arm: str,
    pair_id: int,
    left_id: str,
    right_id: str,
    path_len: int | str,
    n_interior: int,
    decoded: Sequence[tuple[int, int, bool]],
    secs: float,
    *,
    censored: int,
) -> dict[str, Any]:
    return {
        **shared,
        "arm": arm,
        "pair_id": pair_id,
        "left_id": left_id,
        "right_id": right_id,
        "path_len": path_len,
        "n_interior": n_interior,
        "n_decoded": len(decoded),
        "n_connected": sum(1 for _, _, connected in decoded if connected),
        "interior_n": [n for n, _, _ in decoded],
        "interior_m": [m for _, m, _ in decoded],
        "secs": secs,
        "censored": censored,
    }


# ---------------------------------------------------------------------------
# Unit 4 --- conditional completion
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CompletionUnit:
    """The completion exhibit for one collection and one seed."""

    collection: str
    seed: int

    @property
    def key(self) -> str:
        return f"C|{self.collection}|s{self.seed}"


def run_completion_unit(
    unit: CompletionUnit,
    config: Mapping[str, Any],
    context: CollectionContext,
    base: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Truncate the fact tokens of real members and complete them from the model."""
    block = config["completion"]
    n_members = int(block.get("n_members", 100))
    model = context.model(MODEL_OURS)
    rng = random.Random(f"rq6-completion|{unit.collection}")
    eligible = [index for index, H in enumerate(context.hypergraphs) if H.n_edges >= 3]
    chosen = rng.sample(eligible, min(n_members, len(eligible)))

    rows: list[dict[str, Any]] = []
    for index in chosen:
        H = context.hypergraphs[index]
        word = context.words[index]
        n_constants = H.n_nodes
        m = H.n_edges
        removed = m // 3
        if removed < 1:
            continue
        prefix = word[: n_constants + m - removed]
        started = time.perf_counter()
        completed = model.complete(
            prefix, seed=unit.seed + index, max_len=int(config.get("max_len", 200))
        )
        valid, iso_original, reach1 = 1, "", ""
        try:
            decoded, _ = decode_fact_word(
                completed, n_types=context.n_types, n_preds=context.n_preds
            )
        except Exception as exc:  # noqa: BLE001 - a total decoder must not raise
            logger.error("completion did not decode for %s: %s", context.member_ids[index], exc)
            valid = 0
            decoded = None
        if decoded is not None:
            iso_original = int(fact_word(decoded) == context.keys[index])
            reach1 = int(reach(decoded, H, r_max=1) is not None)
        rows.append(
            {
                **base,
                "rq": RQ,
                "experiment": EXPERIMENT,
                "collection": unit.collection,
                "seed": unit.seed,
                "arm": MODEL_OURS,
                "unit": unit.key,
                "member_id": context.member_ids[index],
                "n_prefix": len(prefix),
                "n_removed": removed,
                "valid": valid,
                "iso_original": iso_original,
                "reach1": reach1,
                "secs": time.perf_counter() - started,
                "censored": 0,
            }
        )
    return rows


# ---------------------------------------------------------------------------
# Unit enumeration and the shard driver
# ---------------------------------------------------------------------------


def enumerate_units(config: Mapping[str, Any]) -> list[Any]:
    """Every RQ6 unit, in a fixed order."""
    schedule = seeds(RQ_INDEX, int(config.get("seed_count", 27)))
    units: list[Any] = []
    for name in config["collections"]:
        for model in SAMPLE_MODELS:
            units.extend(SampleUnit(name, model, seed) for seed in schedule)
    for name in config["alignment"]["collections"]:
        units.append(AlignmentUnit(name))
    completion_seeds = schedule[: int(config["completion"].get("n_seeds", 3))]
    for name in config["collections"]:
        units.extend(CompletionUnit(name, seed) for seed in completion_seeds)
    return units


def _shard_paths(out: Path, index: int, count: int) -> io.RunPaths:
    return io.RunPaths(root=out, rq=RQ_DIR, experiment=f"{EXPERIMENT}/{PARTS}/{_tag(index, count)}")


def _tag(index: int, count: int) -> str:
    return f"shard_{index:03d}of{count:03d}"


def _read_rows(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _done(rows: Sequence[Mapping[str, Any]]) -> set[str]:
    return {str(row["unit"]) for row in rows if row.get("unit")}


def run_shard(
    config: Mapping[str, Any],
    out: Path,
    shard: tuple[int, int],
    *,
    data_root: Path | None,
    start_cutoff_s: float | None,
) -> dict[str, Any]:
    """Execute one shard of the RQ6 unit list and return its summary."""
    index, count = shard
    started = time.perf_counter()
    git_sha, host_cpu = provenance()
    base = {"git_sha": git_sha, "host_cpu": host_cpu}
    paths = _shard_paths(out, index, count)

    rows_samples = _read_rows(paths.dir / "rows_samples.csv")
    rows_rejections = _read_rows(paths.dir / "rows_rejections.csv")
    rows_alignment = _read_rows(paths.dir / "rows_alignment.csv")
    rows_completion = _read_rows(paths.dir / "rows_completion.csv")
    done = _done(rows_samples) | _done(rows_alignment) | _done(rows_completion)

    units = enumerate_units(config)
    mine = [u for i, u in enumerate(units) if i % count == index - 1]

    contexts: dict[str, CollectionContext] = {}
    reach_indices: dict[str, Reach1Index] = {}

    def context_of(name: str) -> CollectionContext:
        if name not in contexts:
            contexts[name] = build_context(name, config, data_root)
        return contexts[name]

    def reach_index_of(name: str) -> Reach1Index:
        if name not in reach_indices:
            reach_indices[name] = Reach1Index(context_of(name).hypergraphs)
        return reach_indices[name]

    summary: dict[str, Any] = {
        "shard": _tag(index, count),
        "n_units": len(mine),
        "deferred": [],
        "resumed": len(done),
    }

    executed = 0
    for unit in mine:
        if unit.key in done:
            continue
        if executed and start_cutoff_s and time.perf_counter() - started >= start_cutoff_s:
            summary["deferred"].append(unit.key)
            continue
        if isinstance(unit, SampleUnit):
            row, rejections = run_sample_unit(
                unit, config, context_of(unit.collection), reach_index_of(unit.collection), base
            )
            rows_samples.append(row)
            rows_rejections.extend(rejections)
            io.write_rows(paths, "rejections", rows_rejections, columns=REJECTION_COLUMNS)
            io.write_rows(paths, "samples", rows_samples, columns=SAMPLE_COLUMNS)
        elif isinstance(unit, AlignmentUnit):
            rows_alignment.extend(
                run_alignment_unit(unit, config, context_of(unit.collection), base)
            )
            io.write_rows(paths, "alignment", rows_alignment, columns=ALIGNMENT_COLUMNS)
        else:
            rows_completion.extend(
                run_completion_unit(unit, config, context_of(unit.collection), base)
            )
            io.write_rows(paths, "completion", rows_completion, columns=COMPLETION_COLUMNS)
        executed += 1
        logger.info("unit done: %s", unit.key)

    summary["secs"] = time.perf_counter() - started
    summary["n_rows_samples"] = len(rows_samples)
    summary["n_rows_alignment"] = len(rows_alignment)
    summary["n_rows_completion"] = len(rows_completion)
    summary["n_units_executed"] = executed

    io.write_rows(paths, "samples", rows_samples, columns=SAMPLE_COLUMNS)
    io.write_rows(paths, "rejections", rows_rejections, columns=REJECTION_COLUMNS)
    io.write_rows(paths, "alignment", rows_alignment, columns=ALIGNMENT_COLUMNS)
    io.write_rows(paths, "completion", rows_completion, columns=COMPLETION_COLUMNS)
    io.write_config(paths, dict(config))
    io.write_summary(paths, summary)
    io.write_manifest(
        paths,
        extra={"complete": not summary["deferred"], "shard": shard, **deploy_stamps()},
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


def _apply_smoke(config: dict[str, Any]) -> dict[str, Any]:
    """Shrink the configuration to the pre-registered smoke cell."""
    smoke = config.get("smoke") or {}
    merged = dict(config)
    merged.update({key: value for key, value in smoke.items() if key not in ("alignment",)})
    merged["alignment"] = {**config["alignment"], **(smoke.get("alignment") or {})}
    merged["completion"] = {**config["completion"], **(smoke.get("completion") or {})}
    merged["smoke"] = True
    return merged


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point of ``python -m experiments.tkde.rq6``."""
    parser = argparse.ArgumentParser(description="RQ6 --- generation")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--shard", default="1/1")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--count", action="store_true", help="print the unit count and exit")
    parser.add_argument(
        "--data-root",
        type=Path,
        default=None,
        help="directory holding corpora/; defaults to the results root",
    )
    parser.add_argument("--start-cutoff-s", type=float, default=None)
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, str(args.log_level).upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    config = load_yaml(args.config)
    if args.smoke:
        config = _apply_smoke(config)

    if args.count:
        print(len(enumerate_units(config)))
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
        "shard %s: %d sample rows, %d alignment rows, %d completion rows, %.1f s",
        summary["shard"],
        summary["n_rows_samples"],
        summary["n_rows_alignment"],
        summary["n_rows_completion"],
        summary["secs"],
    )
    if summary["deferred"]:
        logger.warning("deferred %d units at the start cutoff", len(summary["deferred"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
