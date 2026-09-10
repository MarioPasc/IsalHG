"""Property tests for the language layer.

Five invariants, over a hypothesis-driven distribution of random labelled
knowledge bases:

* **reach is a symmetric, exact predicate** --- ``reach(K, K') == reach(K', K)``
  and ``reach == 0`` exactly when an independent nauty certificate says the two
  are isomorphic;
* **alignments carry isomorphisms** --- permuting the second remainder by
  ``node_map`` reproduces the first, as objects;
* **alignment interiors are knowledge bases** --- every word strictly between
  two endpoints decodes, and consecutive words are one edit apart;
* **the ball is a ball** --- every word it yields is within the radius, no word
  is yielded twice, and the centre is inside;
* **the consensus is deterministic and self-consistent** --- repeated calls
  agree, and the reported winner attains the optimum of the reported candidate
  scores.
"""

from __future__ import annotations

import random

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from isalhg.core.fact_word import decode_fact_word
from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.iso_backends.canonical_order import nauty_certificate_bytes
from isalhg.language import (
    alignment_path,
    alignments,
    coverage_consensus,
    fact_key_of,
    reach,
    string_ball,
)
from isalhg.metric_space.distances.fact_levenshtein import fact_word, word_distance
from tests.unit.language._builders import transported_remainder

pytestmark = pytest.mark.property

pytest.importorskip("pynauty")
pytest.importorskip("rapidfuzz")

N_TYPES = 3
N_PREDS = 2
CASE_SETTINGS = settings(
    max_examples=60,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
SEEDS = st.integers(min_value=0, max_value=2**31 - 1)


def random_kb(
    rng: random.Random,
    *,
    n_lo: int = 4,
    n_hi: int = 8,
    m_lo: int = 2,
    m_hi: int = 6,
    arity_hi: int = 4,
) -> SparseHypergraph:
    """A random labelled knowledge base with distinct ``(predicate, members)`` facts."""
    n = rng.randint(n_lo, n_hi)
    m = rng.randint(m_lo, m_hi)
    seen: set[tuple[int, frozenset[int]]] = set()
    edges: list[frozenset[int]] = []
    labels: list[int] = []
    for _ in range(m * 10):
        if len(edges) == m:
            break
        arity = rng.randint(2, min(arity_hi, n))
        members = frozenset(rng.sample(range(n), arity))
        label = rng.randrange(N_PREDS)
        if (label, members) in seen:
            continue
        seen.add((label, members))
        edges.append(members)
        labels.append(label)
    return SparseHypergraph(
        n_nodes=n,
        hyperedges=edges,
        n_vertex_labels=N_TYPES,
        n_edge_labels=N_PREDS,
        vertex_labels=[rng.randrange(N_TYPES) for _ in range(n)],
        edge_labels=labels,
    )


def neighbour(rng: random.Random, H: SparseHypergraph) -> SparseHypergraph:
    """A knowledge base near ``H``: a relabelling, one insertion, or one deletion."""
    facts = [(label, members) for _, members, label in H.iter_edges()]
    choice = rng.randrange(3)
    if choice == 0 or (choice == 2 and not facts):
        sigma = list(range(H.n_nodes))
        rng.shuffle(sigma)
        return permute(H, sigma)
    if choice == 1:
        for _ in range(50):
            arity = rng.randint(2, min(4, H.n_nodes))
            candidate = (
                rng.randrange(N_PREDS),
                frozenset(rng.sample(range(H.n_nodes), arity)),
            )
            if candidate not in facts:
                facts = [*facts, candidate]
                break
    else:
        del facts[rng.randrange(len(facts))]
    return SparseHypergraph(
        n_nodes=H.n_nodes,
        hyperedges=[members for _, members in facts],
        n_vertex_labels=N_TYPES,
        n_edge_labels=N_PREDS,
        vertex_labels=[H.vertex_label(v) for v in range(H.n_nodes)],
        edge_labels=[label for label, _ in facts],
    )


class TestReach:
    @given(SEEDS)
    @CASE_SETTINGS
    def test_symmetric(self, seed: int) -> None:
        rng = random.Random(seed)
        H = random_kb(rng)
        other = neighbour(rng, H)
        assert reach(H, other) == reach(other, H)

    @given(SEEDS)
    @CASE_SETTINGS
    def test_zero_iff_isomorphic(self, seed: int) -> None:
        rng = random.Random(seed)
        H = random_kb(rng)
        other = neighbour(rng, H)
        isomorphic = nauty_certificate_bytes(H) == nauty_certificate_bytes(other)
        assert (reach(H, other) == 0) is isomorphic

    @given(SEEDS)
    @CASE_SETTINGS
    def test_monotone_in_the_radius(self, seed: int) -> None:
        rng = random.Random(seed)
        H = random_kb(rng)
        other = neighbour(rng, H)
        narrow = reach(H, other, r_max=1)
        wide = reach(H, other, r_max=2)
        if narrow is not None:
            assert wide == narrow


class TestAlignments:
    @given(SEEDS)
    @CASE_SETTINGS
    def test_node_map_is_an_isomorphism(self, seed: int) -> None:
        rng = random.Random(seed)
        H = random_kb(rng, n_hi=6, m_hi=4, arity_hi=3)
        other = neighbour(rng, H)
        for alignment in alignments(H, other, 2):
            carried, left = transported_remainder(
                H,
                alignment.deleted_from_k,
                other,
                alignment.deleted_from_k2,
                alignment.node_map,
            )
            assert carried == left

    @given(SEEDS)
    @CASE_SETTINGS
    def test_alignment_exists_exactly_when_reach_is_finite(self, seed: int) -> None:
        rng = random.Random(seed)
        H = random_kb(rng, n_hi=6, m_hi=4, arity_hi=3)
        other = neighbour(rng, H)
        assert bool(alignments(H, other, 2)) is (reach(H, other, r_max=2) is not None)


class TestAlignmentPath:
    @given(SEEDS)
    @CASE_SETTINGS
    def test_interiors_decode_and_step_by_one(self, seed: int) -> None:
        rng = random.Random(seed)
        first = fact_word(random_kb(rng))
        second = fact_word(random_kb(rng))
        interior = alignment_path(first, second)
        assert len(interior) == max(word_distance(first, second) - 1, 0)
        chain = [first, *interior, second]
        for before, after in zip(chain, chain[1:], strict=False):
            assert word_distance(before, after) == 1
        for word in interior:
            decoded, _ = decode_fact_word(word, n_types=N_TYPES, n_preds=N_PREDS)
            assert decoded.n_nodes >= 0


class TestStringBall:
    @given(SEEDS)
    @CASE_SETTINGS
    def test_radius_and_deduplication(self, seed: int) -> None:
        from rapidfuzz.distance import Indel

        rng = random.Random(seed)
        H = random_kb(rng, n_hi=5, m_hi=3, arity_hi=3)
        word = fact_word(H)
        vocab = [("T", 0), ("T", 1), ("F", 0, (0, 1))]
        ball = list(string_ball(word, 1, vocab))
        assert ball[0] == word
        assert len(ball) == len(set(ball))
        codes: dict[object, str] = {}

        def encode(w):
            return "".join(codes.setdefault(token, chr(0x100 + len(codes))) for token in w)

        base = encode(word)
        assert all(Indel.distance(base, encode(other)) <= 2 for other in ball)


class TestConsensus:
    @given(SEEDS)
    @settings(max_examples=25, deadline=None)
    def test_deterministic_and_self_consistent(self, seed: int) -> None:
        rng = random.Random(seed)
        source = random_kb(rng, n_lo=5, n_hi=7, m_lo=4, m_hi=5, arity_hi=3)
        members = [source, *(neighbour(rng, source) for _ in range(3))]
        first = coverage_consensus(members, r=2)
        assert first.candidates == coverage_consensus(members, r=2).candidates
        # The reported winner attains the optimum of the first two criteria and
        # is one of the candidates that attain it. Which of them it is, is the
        # tie break's business and is pinned in
        # ``tests/unit/language/test_consensus_domain_tiebreak.py``: the winner
        # is not the fact-word minimum, so asserting that here would re-assert
        # the retired representation.
        best = min((-score.coverage, score.sum_reach) for score in first.candidates)
        tied = [score for score in first.candidates if (-score.coverage, score.sum_reach) == best]
        assert (-first.coverage, first.sum_reach) == best
        assert first.word in {score.word for score in tied}
        assert first.n_ties == len(tied) - 1
        assert fact_key_of(first.kb) == first.word
        assert first.n_candidates == len(first.candidates)
        assert first.connected is True
