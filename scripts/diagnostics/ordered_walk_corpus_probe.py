"""Verify the ordered-walk Isal word on the frozen knowledge-base corpora.

Five measurements per corpus, all three policies, printed as one table:

A. **Coverage and cost.** How many members the walk refuses (disconnected, or no
   constants at all), the wall-clock of one ``ordered_word`` call, and the word length
   in instructions against the row count of ``nauty_certificate_rows`` -- the second
   nauty tokenization, which is the like-for-like comparison (one symbol per Levi node
   against one symbol per Isal instruction).
B. **Round trip.** ``S2H`` of the word is isomorphic to the member, decided by pynauty.
C. **Invariance.** 20 relabel-and-reorder copies per member give the same fingerprint.
D. **Single-edit response.** One fact ``{hub, new constant}`` with a predicate already
   used by the member; the response is measured in instructions for each policy and, on
   the same edit, in certificate rows. This is the R1 locality axis of the design
   record, on real data, at the coarsest useful sample size -- the campaign's own M1
   grid (five edit kinds, 27 seeds, Holm-corrected) is the next wave's job.

Re-runnable and deterministic: every sample is drawn from ``--seed``.

Usage
-----
``python scripts/diagnostics/ordered_walk_corpus_probe.py``
``python scripts/diagnostics/ordered_walk_corpus_probe.py --corpora ndc_classes``
"""

from __future__ import annotations

import argparse
import random
import statistics
import sys
import time
from collections.abc import Hashable, Sequence
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from experiments.tkde.corpora import hypergraphs, load_collection  # noqa: E402
from isalhg.core.canonical import required_k  # noqa: E402
from isalhg.core.instructions import serialize  # noqa: E402
from isalhg.core.sparse_hypergraph import SparseHypergraph, permute  # noqa: E402
from isalhg.core.string_to_hypergraph import string_to_hypergraph  # noqa: E402
from isalhg.errors import (  # noqa: E402
    DegenerateHypergraphError,
    DisconnectedHypergraphError,
)
from isalhg.iso_backends.canonical_order import nauty_certificate_rows  # noqa: E402
from isalhg.iso_backends.isal_ordered import (  # noqa: E402
    POLICIES,
    ordered_fingerprint,
    ordered_word,
)
from isalhg.iso_backends.pynauty_levi import PynautyLeviBackend  # noqa: E402
from isalhg.metric_space.distances.isal_ordered import (  # noqa: E402
    IsalOrderedLevenshtein,
    _encode,
)

DEFAULT_RESULTS_ROOT = "/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE"
POLICY_NAMES = ("struct", "rank", "rank0")


def quantiles(values: Sequence[float]) -> tuple[float, float, float]:
    """Return ``(median, p90, max)``; ``(nan, nan, nan)`` on an empty input."""
    if not values:
        return (float("nan"),) * 3
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(round(0.9 * (len(ordered) - 1))))
    return statistics.median(ordered), ordered[index], ordered[-1]


def row_distance(left: Sequence[Hashable], right: Sequence[Hashable]) -> float:
    """Equality-keyed Levenshtein over two symbol sequences (one symbol per row)."""
    from rapidfuzz.distance import Levenshtein

    encoded = _encode([tuple(left), tuple(right)])
    return float(Levenshtein.distance(encoded[0], encoded[1]))


def relabelled(H: SparseHypergraph, rng: random.Random) -> SparseHypergraph:
    """Relabel the constants and shuffle the fact insertion order."""
    sigma = list(range(H.n_nodes))
    rng.shuffle(sigma)
    P = permute(H, sigma)
    facts = [(P.members(e), P.edge_label(e)) for e in P.edges()]
    rng.shuffle(facts)
    return SparseHypergraph(
        P.n_nodes,
        [m for m, _ in facts],
        n_vertex_labels=P.n_vertex_labels,
        n_edge_labels=P.n_edge_labels,
        vertex_labels=[P.vertex_label(v) for v in range(P.n_nodes)],
        edge_labels=[label for _, label in facts],
    )


def with_leaf_fact(H: SparseHypergraph, rng: random.Random) -> SparseHypergraph | None:
    """``H`` plus one fact ``{hub, new constant}`` under a predicate ``H`` already uses.

    The hub is the ``ow-struct`` root -- the constant of maximum ``(degree, type)``.
    The new constant takes the hub's type, so the edit adds structure without widening
    the vocabulary. ``None`` when ``H`` has no facts to borrow a predicate from.
    """
    if H.n_edges == 0:
        return None
    hub = ordered_word(H).root
    predicate = rng.choice([H.edge_label(e) for e in H.edges()])
    fresh = H.n_nodes
    members = [H.members(e) for e in H.edges()] + [frozenset({hub, fresh})]
    labels = [H.edge_label(e) for e in H.edges()] + [predicate]
    return SparseHypergraph(
        H.n_nodes + 1,
        members,
        n_vertex_labels=H.n_vertex_labels,
        n_edge_labels=H.n_edge_labels,
        vertex_labels=[H.vertex_label(v) for v in range(H.n_nodes)] + [H.vertex_label(hub)],
        edge_labels=labels,
    )


def coverage_and_cost(name: str, members: list[SparseHypergraph]) -> list[SparseHypergraph]:
    """Print section A and return the members the walk accepts."""
    disconnected: list[int] = []
    degenerate: list[int] = []
    accepted: list[SparseHypergraph] = []
    for index, H in enumerate(members):
        try:
            ordered_word(H)
        except DisconnectedHypergraphError:
            disconnected.append(index)
        except DegenerateHypergraphError:
            degenerate.append(index)
        else:
            accepted.append(H)
    print(f"\n=== {name}: {len(members)} members ===")
    print(f"  refused: {len(disconnected)} disconnected, {len(degenerate)} with no constants")
    print(f"  accepted: {len(accepted)}")

    rows = [len(nauty_certificate_rows(H)) for H in accepted]
    print(
        "  nauty_certificate_rows symbols  median {:7.1f}  p90 {:7.1f}  max {:6.0f}".format(
            *quantiles(rows)
        )
    )
    for policy_name in POLICY_NAMES:
        policy = POLICIES[policy_name]
        millis: list[float] = []
        lengths: list[float] = []
        for H in accepted:
            start = time.perf_counter()
            result = ordered_word(H, policy=policy)
            millis.append((time.perf_counter() - start) * 1000.0)
            lengths.append(len(result.tokens))
        print(
            f"  ow-{policy_name:<6s} ms            "
            "median {:7.3f}  p90 {:7.3f}  max {:6.1f}".format(*quantiles(millis))
        )
        print(
            f"  ow-{policy_name:<6s} instructions  "
            "median {:7.1f}  p90 {:7.1f}  max {:6.0f}".format(*quantiles(lengths))
        )
    return accepted


def round_trip(accepted: list[SparseHypergraph], sample: int, rng: random.Random) -> None:
    """Print section B."""
    backend = PynautyLeviBackend()
    chosen = rng.sample(accepted, min(sample, len(accepted)))
    for policy_name in POLICY_NAMES:
        policy = POLICIES[policy_name]
        good = 0
        for H in chosen:
            result = ordered_word(H, policy=policy)
            decoded = string_to_hypergraph(
                serialize(result.tokens),
                k=required_k(H),
                n_vertex_labels=H.n_vertex_labels,
                n_edge_labels=H.n_edge_labels,
                seed_label=result.root_label,
            )
            good += backend.are_isomorphic(H, decoded)
        print(f"  ow-{policy_name:<6s} round trip    {good}/{len(chosen)} isomorphic")


def invariance(
    accepted: list[SparseHypergraph], sample: int, repeats: int, rng: random.Random
) -> None:
    """Print section C."""
    chosen = rng.sample(accepted, min(sample, len(accepted)))
    for policy_name in POLICY_NAMES:
        policy = POLICIES[policy_name]
        good = 0
        for H in chosen:
            expected = ordered_fingerprint(H, policy=policy)
            if all(
                ordered_fingerprint(relabelled(H, rng), policy=policy) == expected
                for _ in range(repeats)
            ):
                good += 1
        print(
            f"  ow-{policy_name:<6s} invariance    {good}/{len(chosen)} members "
            f"stable over {repeats} relabellings"
        )


def single_edit(accepted: list[SparseHypergraph], sample: int, rng: random.Random) -> None:
    """Print section D."""
    chosen = rng.sample(accepted, min(sample, len(accepted)))
    pairs: list[tuple[SparseHypergraph, SparseHypergraph]] = []
    for H in chosen:
        edited = with_leaf_fact(H, rng)
        if edited is not None:
            pairs.append((H, edited))
    print(f"  single-edit pairs: {len(pairs)} (insert one fact {{hub, new constant}})")
    for policy_name in POLICY_NAMES:
        distance = IsalOrderedLevenshtein(policy_name)
        costs = [distance.pairwise(a, b) for a, b in pairs]
        within = sum(1 for c in costs if c <= 2) / len(costs) if costs else float("nan")
        median, p90, worst = quantiles(costs)
        print(
            f"  ow-{policy_name:<6s} response      "
            f"median {median:6.1f}  p90 {p90:6.1f}  max {worst:6.0f}  frac<=2 {within:.3f}"
        )
    cert = [row_distance(nauty_certificate_rows(a), nauty_certificate_rows(b)) for a, b in pairs]
    within = sum(1 for c in cert if c <= 2) / len(cert) if cert else float("nan")
    median, p90, worst = quantiles(cert)
    print(
        "  nauty_cert_rows response      "
        f"median {median:6.1f}  p90 {p90:6.1f}  max {worst:6.0f}  frac<=2 {within:.3f}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpora", nargs="+", default=["wd50k66", "ndc_classes"])
    parser.add_argument("--results-root", default=DEFAULT_RESULTS_ROOT)
    parser.add_argument("--sample", type=int, default=300)
    parser.add_argument("--edit-sample", type=int, default=200)
    parser.add_argument("--relabellings", type=int, default=20)
    parser.add_argument("--seed", type=int, default=20260906)
    args = parser.parse_args()

    for name in args.corpora:
        members = hypergraphs(load_collection(name, args.results_root))
        accepted = coverage_and_cost(name, members)
        if not accepted:
            continue
        rng = random.Random(args.seed)
        round_trip(accepted, args.sample, rng)
        invariance(accepted, args.sample, args.relabellings, rng)
        if name == "wd50k66":
            single_edit(accepted, args.edit_sample, rng)


if __name__ == "__main__":
    main()
