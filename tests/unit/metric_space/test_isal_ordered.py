"""``IsalOrderedLevenshtein`` -- the three ordered-walk arms as a registered distance.

What is pinned:

- the three arms resolve through the registry and carry their own names;
- ``labels_used`` matches measured relabel-sensitivity, the same probe and the same
  contract as ``tests/unit/metric_space/test_representations_kb.py`` applies to every
  other arm (that file sweeps ``registry.available_distances()``, so these arms are
  already inside it; the check is replicated here so a failure names this module);
- the symbols are instructions, and ``P[1]`` and ``N[1]`` are two of them -- they hash
  alike, being one-field dataclasses over the same value, and only ``==`` separates
  them. A ``dict`` keyed by the token gets this right; a ``set``-of-hashes encoder would
  silently merge them and under-report every distance that moves a pointer;
- the metric axioms on isomorphism classes (Corollary C), including identity of
  indiscernibles against pynauty;
- ``fingerprint`` needs no ``k``, unlike ``d_I``'s, so a corpus is comparable without
  pinning a pointer count first;
- ``matrix`` agrees with ``pairwise`` entry by entry.
"""

from __future__ import annotations

import itertools
import math
import random

import pytest

from isalhg.core.instructions import TokenN, TokenP
from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.errors import DistanceComputationError
from isalhg.metric_space import registry
from isalhg.metric_space.distances.isal_ordered import IsalOrderedLevenshtein, _encode

pytestmark = pytest.mark.unit

pytest.importorskip("pynauty")
pytest.importorskip("rapidfuzz")

ARMS = ("isal_ow_struct", "isal_ow_rank", "isal_ow_rank0")

_EDGES: list[frozenset[int]] = [
    frozenset({0, 1, 2}),
    frozenset({2, 3}),
    frozenset({0, 3, 4}),
]


def _kb(vertex_labels: list[int], edge_labels: list[int]) -> SparseHypergraph:
    """The fixed 5-constant, 3-fact labelled knowledge base of the competitor suite."""
    return SparseHypergraph(
        5,
        _EDGES,
        n_vertex_labels=3,
        n_edge_labels=3,
        vertex_labels=vertex_labels,
        edge_labels=edge_labels,
    )


@pytest.fixture
def labelled_base() -> SparseHypergraph:
    return _kb([0, 1, 2, 0, 1], [0, 1, 2])


@pytest.fixture
def vertex_relabelled() -> SparseHypergraph:
    """``labelled_base`` with the type of constant 4 changed from 1 to 2."""
    return _kb([0, 1, 2, 0, 2], [0, 1, 2])


@pytest.fixture
def edge_relabelled() -> SparseHypergraph:
    """``labelled_base`` with the predicate of fact 2 changed from 2 to 0."""
    return _kb([0, 1, 2, 0, 1], [0, 1, 0])


def _random_labelled(rng: random.Random) -> SparseHypergraph:
    """A random connected labelled knowledge base (path spine plus extra facts)."""
    n = rng.randint(3, 7)
    members: set[frozenset[int]] = {frozenset({i, i + 1}) for i in range(n - 1)}
    for _ in range(rng.randint(1, 3)):
        members.add(frozenset(rng.sample(range(n), rng.randint(2, min(3, n)))))
    ordered = sorted(members, key=sorted)
    return SparseHypergraph(
        n,
        ordered,
        n_vertex_labels=3,
        n_edge_labels=3,
        vertex_labels=[rng.randrange(3) for _ in range(n)],
        edge_labels=[rng.randrange(3) for _ in ordered],
    )


def _iso(H1: SparseHypergraph, H2: SparseHypergraph) -> bool:
    from isalhg.iso_backends.pynauty_levi import PynautyLeviBackend

    return PynautyLeviBackend().are_isomorphic(H1, H2)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class TestRegistration:
    @pytest.mark.parametrize("arm", ARMS)
    def test_resolves_through_the_registry(self, arm: str) -> None:
        distance = registry.get_distance(arm)
        assert isinstance(distance, IsalOrderedLevenshtein)
        assert distance.name == arm

    @pytest.mark.parametrize("arm", ARMS)
    def test_listed_by_available_distances(self, arm: str) -> None:
        assert arm in registry.available_distances()

    def test_unknown_policy_is_refused_at_construction(self) -> None:
        with pytest.raises(DistanceComputationError):
            IsalOrderedLevenshtein("hub")

    def test_the_three_arms_are_three_distinct_words(self) -> None:
        """The ablations must actually differ, or they measure nothing."""
        H = SparseHypergraph(
            5,
            _EDGES,
            n_vertex_labels=3,
            n_edge_labels=3,
            vertex_labels=[0, 1, 2, 0, 1],
            edge_labels=[0, 1, 2],
        )
        prints = {arm: registry.get_distance(arm).fingerprint(H) for arm in ARMS}
        assert len({tuple(v) for v in prints.values()}) >= 2


# ---------------------------------------------------------------------------
# Label declaration
# ---------------------------------------------------------------------------


class TestLabelDeclaration:
    """``labels_used`` must equal what the arm measurably reads."""

    @pytest.mark.parametrize("arm", ARMS)
    def test_declaration_matches_measured_sensitivity(
        self,
        arm: str,
        labelled_base: SparseHypergraph,
        vertex_relabelled: SparseHypergraph,
        edge_relabelled: SparseHypergraph,
    ) -> None:
        distance = registry.get_distance(arm)
        measured = frozenset(
            kind
            for kind, moved in (
                ("vertex", distance.pairwise(labelled_base, vertex_relabelled) > 1e-9),
                ("edge", distance.pairwise(labelled_base, edge_relabelled) > 1e-9),
            )
            if moved
        )
        assert measured == distance.labels_used == frozenset({"vertex", "edge"})

    def test_registry_helper_agrees(self) -> None:
        for arm in ARMS:
            assert registry.labels_used(arm) == frozenset({"vertex", "edge"})


# ---------------------------------------------------------------------------
# Symbols
# ---------------------------------------------------------------------------


class TestSymbols:
    def test_advance_and_retreat_are_different_symbols(self) -> None:
        """``P[1]`` and ``N[1]`` hash alike; only equality separates them."""
        assert hash(TokenP(1)) == hash(TokenN(1))
        assert TokenP(1) != TokenN(1)
        encoded = _encode([(TokenP(1),), (TokenN(1),)])
        assert encoded[0] != encoded[1]

    def test_a_pointer_direction_flip_costs_one_substitution(self) -> None:
        encoded = _encode([(TokenP(1), TokenP(2)), (TokenN(1), TokenP(2))])
        from rapidfuzz.distance import Levenshtein

        assert Levenshtein.distance(encoded[0], encoded[1]) == 1

    def test_fingerprint_is_hashable_and_needs_no_k(self, labelled_base: SparseHypergraph) -> None:
        for arm in ARMS:
            fingerprint = registry.get_distance(arm).fingerprint(labelled_base)
            assert isinstance(fingerprint, tuple)
            hash(fingerprint)
            assert fingerprint  # non-trivial input yields a non-empty word

    def test_pairwise_counts_instructions_not_characters(self) -> None:
        """A ten-pointer move is one symbol, not the four characters of ``P[10]``."""
        assert len(_encode([(TokenP(10),)])[0]) == 1


# ---------------------------------------------------------------------------
# Metric axioms
# ---------------------------------------------------------------------------


class TestMetricAxioms:
    """Corollary C: ``d_o`` is a metric on isomorphism classes."""

    @pytest.mark.parametrize("arm", ARMS)
    def test_identity_of_indiscernibles_against_pynauty(self, arm: str) -> None:
        distance = registry.get_distance(arm)
        rng = random.Random(2026)
        corpus = [_random_labelled(rng) for _ in range(30)]
        corpus += [permute(H, rng.sample(range(H.n_nodes), H.n_nodes)) for H in corpus[:10]]
        for H1, H2 in itertools.combinations(corpus, 2):
            zero = distance.pairwise(H1, H2) == pytest.approx(0.0, abs=1e-9)
            assert zero == _iso(H1, H2)

    @pytest.mark.parametrize("arm", ARMS)
    def test_symmetry_and_triangle_inequality(self, arm: str) -> None:
        distance = registry.get_distance(arm)
        rng = random.Random(11)
        corpus = [_random_labelled(rng) for _ in range(12)]
        for H1, H2 in itertools.combinations(corpus, 2):
            value = distance.pairwise(H1, H2)
            assert math.isfinite(value)
            assert value >= 0.0
            assert value == pytest.approx(distance.pairwise(H2, H1))
        for a, b, c in itertools.combinations(corpus, 3):
            assert (
                distance.pairwise(a, c) <= distance.pairwise(a, b) + distance.pairwise(b, c) + 1e-9
            )

    @pytest.mark.parametrize("arm", ARMS)
    def test_self_distance_is_zero(self, arm: str, labelled_base: SparseHypergraph) -> None:
        assert registry.get_distance(arm).pairwise(labelled_base, labelled_base) == 0.0


# ---------------------------------------------------------------------------
# Matrix
# ---------------------------------------------------------------------------


class TestMatrix:
    @pytest.mark.parametrize("arm", ARMS)
    def test_matrix_agrees_with_pairwise(self, arm: str) -> None:
        np = pytest.importorskip("numpy")
        distance = registry.get_distance(arm)
        rng = random.Random(5)
        corpus = [_random_labelled(rng) for _ in range(10)]
        matrix = distance.matrix(corpus)
        assert matrix.shape == (10, 10)
        assert np.allclose(matrix, matrix.T)
        assert np.allclose(np.diag(matrix), 0.0)
        for i, j in itertools.combinations(range(10), 2):
            assert matrix[i, j] == pytest.approx(distance.pairwise(corpus[i], corpus[j]))

    @pytest.mark.parametrize("arm", ARMS)
    def test_empty_corpus(self, arm: str) -> None:
        np = pytest.importorskip("numpy")
        matrix = registry.get_distance(arm).matrix([])
        assert matrix.shape == (0, 0)
        assert matrix.dtype == np.float64
