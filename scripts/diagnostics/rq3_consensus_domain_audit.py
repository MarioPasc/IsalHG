"""Measure what the domain exclusion and the Isal tie break move on Corpus A.

Two questions the campaign rows cannot answer, because what they need was
computed inside ``coverage_consensus`` and never persisted:

1. **The audit number.** How often did the winner under the old objective lie
   outside the language's domain?  Those rows reported a representative with no
   Isal string, so they were already invalid; the count is the blast radius of
   the exclusion, since dropping a *losing* candidate from an argmax is a no-op.
2. **The split.** Of the results that move, how many move because an
   out-of-domain winner was excluded and how many because the tie break changed
   from the retired fact word to the Isal string?

The three objectives are run over the same collections:

``old``
    no domain exclusion, fact-word tie break --- the code as it stood at
    44c48e3.
``mid``
    domain exclusion, fact-word tie break --- the exclusion alone.
``new``
    domain exclusion, Isal tie break --- the shipped objective.

A result that differs between ``old`` and ``mid`` moved because of the
exclusion; one that differs between ``mid`` and ``new`` moved because of the tie
break; both can happen to one collection and the script counts them separately.

This reproduces Corpus A's construction exactly (``enumerate_units_a``,
``eligible_sources``, ``cell_source_window``, ``variant_collection``, the same
seed schedule and per-unit RNG), then walks the unit list in order and stops at
``--collections``.  It is a *subset* measurement by design: it is meant to be
run on a workstation over a few hundred collections, not to reproduce the
campaign.

Run, from the repository root::

    PYTHONPATH=. python scripts/diagnostics/rq3_consensus_domain_audit.py \\
        --config experiments/tkde/configs/rq3.yaml --collections 300
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from collections import Counter
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from experiments.tkde import corpora
from experiments.tkde.config import load_yaml
from experiments.tkde.rq3 import (
    cell_source_window,
    consensus_identities,
    eligible_sources,
    enumerate_units_a,
    fact_distance,
    identity_facts_of_hypergraph,
    identity_facts_of_record,
    identity_ids,
)
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.datasets.kb.base import KBRecord
from isalhg.datasets.kb.ladders import variant_collection
from isalhg.language import consensus as consensus_module
from isalhg.language.consensus import (
    ConsensusError,
    ConsensusResult,
    coverage_consensus,
    in_language_domain,
)
from isalhg.language.reach import fact_key_of


class AuditError(RuntimeError):
    """Raised when the audit cannot be run as asked."""


@contextmanager
def _hooks(
    domain: Callable[[SparseHypergraph], bool],
    word: Callable[[SparseHypergraph], object],
) -> Iterator[None]:
    """Run the consensus with its domain test and tie-break word substituted."""
    saved_domain = consensus_module.in_language_domain
    saved_word = consensus_module.isal_fingerprint
    consensus_module.in_language_domain = domain  # type: ignore[assignment]
    consensus_module.isal_fingerprint = word  # type: ignore[assignment]
    try:
        yield
    finally:
        consensus_module.in_language_domain = saved_domain  # type: ignore[assignment]
        consensus_module.isal_fingerprint = saved_word  # type: ignore[assignment]


def old_objective(members: Sequence[SparseHypergraph], r: int, budget: str) -> ConsensusResult:
    """The pre-change objective: every candidate admitted, fact-word tie break."""
    with _hooks(lambda _H: True, fact_key_of):
        return coverage_consensus(members, r, alignment_budget=budget)  # type: ignore[arg-type]


def mid_objective(members: Sequence[SparseHypergraph], r: int, budget: str) -> ConsensusResult:
    """The exclusion alone: in-domain candidates, fact-word tie break."""
    with _hooks(in_language_domain, fact_key_of):
        return coverage_consensus(members, r, alignment_budget=budget)  # type: ignore[arg-type]


@dataclass
class Tally:
    """Running counts for one corpus."""

    collections: int = 0
    old_winner_out_of_domain: int = 0
    old_winner_empty: int = 0
    old_winner_disconnected: int = 0
    moved_by_exclusion: int = 0
    moved_by_tie_break: int = 0
    moved_either: int = 0
    all_candidates_out_of_domain: int = 0
    winner_origin: Counter[str] = field(default_factory=Counter)
    ties_old: Counter[int] = field(default_factory=Counter)
    ties_new: Counter[int] = field(default_factory=Counter)
    excluded_total: int = 0
    tie_free_identical: int = 0
    tie_free_total: int = 0
    moved_closer_to_truth: int = 0
    moved_further_from_truth: int = 0
    moved_same_distance: int = 0
    recovery_gained: int = 0
    recovery_lost: int = 0

    def as_dict(self) -> dict[str, Any]:
        """Return the tally as JSON-serialisable fields."""
        return {
            "collections": self.collections,
            "old_winner_out_of_domain": self.old_winner_out_of_domain,
            "old_winner_empty": self.old_winner_empty,
            "old_winner_disconnected": self.old_winner_disconnected,
            "moved_by_exclusion": self.moved_by_exclusion,
            "moved_by_tie_break": self.moved_by_tie_break,
            "moved_either": self.moved_either,
            "all_candidates_out_of_domain": self.all_candidates_out_of_domain,
            "winner_origin": dict(self.winner_origin),
            "ties_old_zero": self.ties_old.get(0, 0),
            "ties_new_zero": self.ties_new.get(0, 0),
            "ties_old_hist": dict(sorted(self.ties_old.items())),
            "ties_new_hist": dict(sorted(self.ties_new.items())),
            "excluded_total": self.excluded_total,
            "tie_free_identical": self.tie_free_identical,
            "tie_free_total": self.tie_free_total,
            "moved_closer_to_truth": self.moved_closer_to_truth,
            "moved_further_from_truth": self.moved_further_from_truth,
            "moved_same_distance": self.moved_same_distance,
            "recovery_gained": self.recovery_gained,
            "recovery_lost": self.recovery_lost,
        }


def _members_of(records: Sequence[KBRecord], n_types: int, n_preds: int) -> list[SparseHypergraph]:
    return [r.to_hypergraph(n_types=n_types, n_preds=n_preds) for r in records]


def audit_collection(
    members: Sequence[SparseHypergraph],
    identities: Sequence[Sequence[str]],
    truth_facts: frozenset[tuple[int, frozenset[str]]],
    r: int,
    budget: str,
    tally: Tally,
) -> None:
    """Score one collection under the three objectives and fold it into ``tally``.

    Parameters
    ----------
    members : Sequence of SparseHypergraph
        The collection, in the order the identities are given.
    identities : Sequence of Sequence of str
        Per member, its external constant identities (evaluation only).
    truth_facts : frozenset
        The source's identity-addressed fact set, so a moved result can be
        scored on the axis RQ3 reports rather than only counted.
    r : int
        Consensus radius.
    budget : str
        Alignment budget.
    tally : Tally
        Folded into in place.
    """
    tally.collections += 1
    old = old_objective(members, r, budget)
    try:
        mid = mid_objective(members, r, budget)
        new = coverage_consensus(members, r, alignment_budget=budget)  # type: ignore[arg-type]
    except ConsensusError:
        tally.all_candidates_out_of_domain += 1
        return

    # The reproduction is only worth something if it is the old rule. The old
    # code sorted every candidate by (-coverage, sum_reach, pool key) and took
    # the head, and the pool key is the fact word, so this must hold exactly.
    expected = min(
        old.candidates, key=lambda score: (-score.coverage, score.sum_reach, score.word)
    ).word
    if old.word != expected:
        raise AuditError("old_objective does not reproduce the pre-change selection rule")

    if not in_language_domain(old.kb):
        tally.old_winner_out_of_domain += 1
        if old.kb.n_nodes == 0:
            tally.old_winner_empty += 1
        else:
            tally.old_winner_disconnected += 1

    by_exclusion = old.word != mid.word
    by_tie_break = mid.word != new.word
    tally.moved_by_exclusion += int(by_exclusion)
    tally.moved_by_tie_break += int(by_tie_break)
    tally.moved_either += int(old.word != new.word)

    tally.winner_origin[new.origin.split(":")[0]] += 1
    tally.ties_old[old.n_ties] += 1
    tally.ties_new[new.n_ties] += 1
    tally.excluded_total += new.n_excluded

    if old.word != new.word:
        # A moved result is only interesting if it moved on the axis RQ3
        # reports, so score both winners against the source.
        before = fact_distance(
            identity_facts_of_hypergraph(old.kb, consensus_identities(old, identities)),
            truth_facts,
        )
        after = fact_distance(
            identity_facts_of_hypergraph(new.kb, consensus_identities(new, identities)),
            truth_facts,
        )
        if after < before:
            tally.moved_closer_to_truth += 1
        elif after > before:
            tally.moved_further_from_truth += 1
        else:
            tally.moved_same_distance += 1
        tally.recovery_gained += int(before != 0 and after == 0)
        tally.recovery_lost += int(before == 0 and after != 0)

    if new.n_ties == 0 and new.n_excluded == 0:
        tally.tie_free_total += 1
        tally.tie_free_identical += int(
            old.word == new.word
            and (old.coverage, old.sum_reach) == (new.coverage, new.sum_reach)
            and old.candidates == new.candidates
        )


def run(
    config_path: Path, limit: int, seeds_per_cell: int, data_root: Path | None
) -> dict[str, Any]:
    """Audit up to ``limit`` Corpus A collections, spread over every cell.

    ``enumerate_units_a`` orders units collection-major and seed-minor, so a
    plain prefix would be all ``ins`` cells of one corpus.  Taking the first
    ``seeds_per_cell`` seeds of every cell instead covers all 24 cells --- which
    matters here, because the out-of-domain winners are a deletion-cell
    phenomenon and a prefix would miss them.

    Parameters
    ----------
    config_path : Path
        The RQ3 configuration.
    limit : int
        Ceiling on audited collections.
    seeds_per_cell : int
        How many of each cell's seeds to walk.
    data_root : Path or None
        Corpora root override.

    Returns
    -------
    dict
        The per-corpus tallies, JSON-serialisable.
    """
    config = load_yaml(config_path)
    block = config["corpus_a"]
    window = block["source_window"]
    budget = str(block.get("alignment_budget", "triangle"))
    radius = int(block.get("radius_default", 2))
    sources_per_cell = int(block["sources_per_cell"])
    tallies: dict[str, Tally] = {}
    loaded: dict[str, Any] = {}
    audited = 0

    seen_per_cell: Counter[tuple[str, str]] = Counter()
    for unit in enumerate_units_a(config):
        if audited >= limit:
            break
        cell_key = (unit.collection, unit.cell)
        if seen_per_cell[cell_key] >= seeds_per_cell:
            continue
        seen_per_cell[cell_key] += 1
        collection = loaded.get(unit.collection)
        if collection is None:
            collection = corpora.load_collection(unit.collection, data_root)
            loaded[unit.collection] = collection
        pool = eligible_sources(collection, cell_source_window(window, unit.kind, unit.n_members))
        if not pool:
            continue
        rng = random.Random(f"{unit.collection}|{unit.cell}|{unit.seed}")
        chosen = rng.sample(range(len(pool)), min(sources_per_cell, len(pool)))
        tally = tallies.setdefault(unit.collection, Tally())
        for index, source_index in enumerate(chosen):
            if audited >= limit:
                break
            source = pool[source_index]
            records = variant_collection(
                source, unit.n_members, unit.t, unit.kind, unit.seed * 1_000 + index
            )
            if records is None:
                continue
            members = _members_of(records, collection.n_types, collection.n_preds)
            audit_collection(
                members,
                [identity_ids(record) for record in records],
                identity_facts_of_record(source),
                radius,
                budget,
                tally,
            )
            audited += 1

    return {
        "config": str(config_path),
        "radius": radius,
        "alignment_budget": budget,
        "seeds_per_cell": seeds_per_cell,
        "cells_walked": len(seen_per_cell),
        "audited": audited,
        "per_corpus": {name: tally.as_dict() for name, tally in sorted(tallies.items())},
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("experiments/tkde/configs/rq3.yaml"))
    parser.add_argument("--collections", type=int, default=300)
    parser.add_argument(
        "--seeds-per-cell",
        type=int,
        default=1,
        help="seeds walked per cell; 1 covers all 24 cells at 8 sources each",
    )
    parser.add_argument("--data-root", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    started = time.perf_counter()
    report = run(args.config, int(args.collections), int(args.seeds_per_cell), args.data_root)
    report["wall_clock_s"] = round(time.perf_counter() - started, 1)
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.out is not None:
        args.out.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
