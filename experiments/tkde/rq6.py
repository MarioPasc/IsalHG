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

The reach-1 fraction is computed exactly. Its precondition (same constant count
and same type multiset) is a necessary condition for a finite reach at fixed
constants; a sample with no member satisfying it contributes no fraction rather
than a zero.
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
from experiments.tkde.rq3 import provenance, run_guarded
from isalhg.core.canonical import canonical_string, required_k
from isalhg.core.fact_word import Word, decode_fact_word
from isalhg.core.instructions import parse
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.core.string_to_hypergraph import string_to_hypergraph
from isalhg.datasets.kb.base import KBCollection
from isalhg.generation.fidelity import PROFILE_KEYS, fidelity, novelty
from isalhg.generation.incidence_baseline import flatten, strict_decode, strict_decode_reason
from isalhg.generation.ngram import TokenNGram
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
    "validity",
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

    def model(self, kind: str) -> TokenNGram:
        """Return the fitted order-3 model of one alphabet, cached."""
        if not hasattr(self, "_models"):
            self._models: dict[str, TokenNGram] = {}
        if kind not in self._models:
            started = time.perf_counter()
            source = self.words if kind == MODEL_OURS else self.flat
            self._models[kind] = TokenNGram(order=3).fit(source)
            logger.info(
                "fitted %s on %s (%d words) in %.1f s",
                kind,
                self.name,
                len(source),
                time.perf_counter() - started,
            )
        return self._models[kind]


def build_context(name: str, config: Mapping[str, Any], root: Path | None) -> CollectionContext:
    """Load one collection and precompute its words, keys and flat serializations."""
    collection = corpora.load_collection(name, root)
    roles = bool(config["roles"].get(name, False)) and collection.has_roles
    n_types, n_preds = collection.n_types, collection.n_preds
    hypergraphs = corpora.hypergraphs(collection)
    roles_maps = corpora.roles_maps(collection) if roles else [None] * len(hypergraphs)
    words = [fact_word(H, rm) for H, rm in zip(hypergraphs, roles_maps, strict=True)]
    keys = words if not roles else [fact_word(H) for H in hypergraphs]
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
    )


# ---------------------------------------------------------------------------
# The reach-1 neighbourhood
# ---------------------------------------------------------------------------


def _shape(H: SparseHypergraph) -> tuple[int, tuple[int, ...]]:
    """The reach precondition: constant count and sorted type multiset."""
    return H.n_nodes, tuple(sorted(H.vertex_label(v) for v in range(H.n_nodes)))


def _deletion_keys(H: SparseHypergraph) -> dict[Word, int]:
    """``{canonical key: fewest deletions reaching it}`` for at most one deletion."""
    return RemainderIndex(H, 1).min_deletions()


class Reach1Index:
    """Answers "is this sample within reach 1 of some member?" exactly.

    Members are bucketed by the reach precondition. Inside a bucket the question
    reduces to three key comparisons, because ``|A| + |B| <= 1`` admits only
    ``(0,0)``, ``(1,0)`` and ``(0,1)``; the surviving candidate is then confirmed
    with :func:`isalhg.language.reach.reach` itself, so the recorded answer is
    the library's, not this index's.
    """

    def __init__(self, members: Sequence[SparseHypergraph]) -> None:
        self._members = list(members)
        self._buckets: dict[tuple[int, tuple[int, ...]], list[int]] = {}
        for index, H in enumerate(self._members):
            self._buckets.setdefault(_shape(H), []).append(index)
        self._deletions: dict[int, dict[Word, int]] = {}
        self._keys: dict[int, Word] = {}

    def _member_deletions(self, index: int) -> dict[Word, int]:
        if index not in self._deletions:
            self._deletions[index] = _deletion_keys(self._members[index])
        return self._deletions[index]

    def _member_key(self, index: int) -> Word:
        if index not in self._keys:
            self._keys[index] = fact_word(self._members[index])
        return self._keys[index]

    def within_one(self, sample: SparseHypergraph) -> bool | None:
        """``True``/``False`` if the precondition holds for some member, else ``None``."""
        bucket = self._buckets.get(_shape(sample))
        if not bucket:
            return None
        sample_deletions = _deletion_keys(sample)
        sample_key = fact_word(sample)
        for index in bucket:
            member_deletions = self._member_deletions(index)
            member_key = self._member_key(index)
            plausible = (
                sample_key in member_deletions
                or member_key in sample_deletions
                or sample_key == member_key
            )
            if plausible and reach(sample, self._members[index], r_max=1) is not None:
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
    for word in words:
        if unit.model == MODEL_OURS:
            H, _ = decode_fact_word(word, n_types=context.n_types, n_preds=context.n_preds)
            decoded.append(H)
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
        "validity": n_valid / n_samples if n_samples else "",
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
        for model in (MODEL_OURS, MODEL_BASELINE):
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
    io.write_manifest(paths, extra={"complete": not summary["deferred"], "shard": shard})
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
