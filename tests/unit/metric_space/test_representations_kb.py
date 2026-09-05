"""Competitor distances on labelled knowledge bases.

Three things are pinned here.

**The label declarations are measured, not asserted.** Every registered arm
declares ``labels_used``; :class:`TestLabelDeclarations` relabels one vertex and
one hyperedge of a fixed labelled hypergraph and checks that the distance moves
exactly for the kinds the arm declares and does not move for the kinds it does
not. A declaration that drifts away from behaviour fails here, in both
directions -- an arm that quietly stops reading predicates and an arm that
under-declares are both caught.

**The new arms behave as the design says.** ``nauty_cert_rows`` is exact at
zero, and the two bipartite GED readings are checked against costs worked out by
hand on hypergraphs small enough to enumerate.

**Nothing returns a non-finite value on labelled input.** The competitor tables
of RQ2/RQ4/RQ5 run on labelled collections that these representations had never
seen before this wave; a NaN or an exception there would silently drop a row.

``hypercot`` is excluded from the behavioural sweeps: it shells out to a pinned
conda environment that is not installed here. Its gating is checked instead --
that it fails loudly with an install hint rather than returning a wrong number.
"""

from __future__ import annotations

import math
import random

import pytest

from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.errors import SubprocessRepresentationError
from isalhg.metric_space import registry

pytestmark = pytest.mark.unit

pytest.importorskip("pynauty")
pytest.importorskip("rapidfuzz")
pytest.importorskip("scipy")

# hypercot needs a separate pinned environment; every other registered arm is
# expected to run in this one.
SUBPROCESS_ARMS: frozenset[str] = frozenset({"hypercot"})

# The roles arm refuses ``pairwise`` by design (a SparseHypergraph carries no
# roles, so answering would silently return the role-free distance and make the
# ablation identical to the primary arm).
NO_PAIRWISE_ARMS: frozenset[str] = frozenset({"fact_rank_roles"})

# HGED is NP-hard and the paper-faithful BFS solver is the slow one (~1 s per
# 7-constant pair here, with a heavy tail). The behavioural sweeps therefore
# hand these arms smaller instances and fewer of them: the sweeps check
# finiteness and sign, which do not need large inputs, and the oracle's own
# correctness lives in tests/unit/metric_space/test_hged*.py.
EXPENSIVE_ARMS: frozenset[str] = frozenset({"qin_hged", "exact_hged", "exact_ged"})


def _hypercot_env_present() -> bool:
    """Whether the pinned ``isalhg-hypercot`` conda env exists on this machine."""
    import os

    return os.path.exists(os.path.expanduser("~/.conda/envs/isalhg-hypercot/bin/python"))


def _behavioural_arms() -> list[str]:
    """Registered arms whose ``pairwise`` can be exercised in this environment."""
    return [
        name
        for name in registry.available_distances()
        if name not in SUBPROCESS_ARMS and name not in NO_PAIRWISE_ARMS
    ]


# ---------------------------------------------------------------------------
# Fixtures -- a connected, doubly-labelled knowledge base and its relabellings
# ---------------------------------------------------------------------------

# Connected on purpose: the pointer arm (isalhg_levenshtein) is only defined on
# connected hypergraphs (decision B11), and every real member of both frozen
# collections is connected.
_EDGES: list[frozenset[int]] = [
    frozenset({0, 1, 2}),
    frozenset({2, 3}),
    frozenset({0, 3, 4}),
]


def _kb(vertex_labels: list[int], edge_labels: list[int]) -> SparseHypergraph:
    """A fixed 5-constant, 3-fact knowledge base under the given labels."""
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
    """Both vocabularies non-trivial: 3 types over 5 constants, 3 predicates."""
    return _kb([0, 1, 2, 0, 1], [0, 1, 2])


@pytest.fixture
def vertex_relabelled() -> SparseHypergraph:
    """``labelled_base`` with the type of constant 4 changed from 1 to 2."""
    return _kb([0, 1, 2, 0, 2], [0, 1, 2])


@pytest.fixture
def edge_relabelled() -> SparseHypergraph:
    """``labelled_base`` with the predicate of fact 2 changed from 2 to 0."""
    return _kb([0, 1, 2, 0, 1], [0, 1, 0])


def _random_labelled(rng: random.Random, *, small: bool = False) -> SparseHypergraph:
    """A random connected labelled knowledge base (path spine + extra facts)."""
    n = rng.randint(3, 5) if small else rng.randint(4, 7)
    # A spine of consecutive pairs guarantees connectivity; extra facts are free.
    edges: set[frozenset[int]] = {frozenset({i, i + 1}) for i in range(n - 1)}
    for _ in range(1 if small else rng.randint(1, 3)):
        edges.add(frozenset(rng.sample(range(n), rng.randint(2, min(3, n)))))
    members = sorted(edges, key=sorted)
    return SparseHypergraph(
        n,
        members,
        n_vertex_labels=3,
        n_edge_labels=3,
        vertex_labels=[rng.randrange(3) for _ in range(n)],
        edge_labels=[rng.randrange(3) for _ in members],
    )


# ---------------------------------------------------------------------------
# The label declarations
# ---------------------------------------------------------------------------


class TestLabelDeclarations:
    """``labels_used`` must equal what the arm measurably reads."""

    def test_every_registered_arm_declares(self) -> None:
        for name in registry.available_distances():
            declared = registry.get_distance(name).labels_used
            assert isinstance(declared, frozenset), name
            assert declared <= {"vertex", "edge"}, f"{name} declares {declared}"

    @pytest.mark.parametrize("name", _behavioural_arms())
    def test_declaration_matches_measured_sensitivity(
        self,
        name: str,
        labelled_base: SparseHypergraph,
        vertex_relabelled: SparseHypergraph,
        edge_relabelled: SparseHypergraph,
    ) -> None:
        distance = registry.get_distance(name)
        moved_on_vertex = distance.pairwise(labelled_base, vertex_relabelled) > 1e-9
        moved_on_edge = distance.pairwise(labelled_base, edge_relabelled) > 1e-9
        measured = frozenset(
            kind for kind, moved in (("vertex", moved_on_vertex), ("edge", moved_on_edge)) if moved
        )
        assert measured == distance.labels_used, (
            f"{name} declares {sorted(distance.labels_used)} but measurably reads "
            f"{sorted(measured)} on the fixed labelled probe"
        )

    def test_label_blind_arms_are_blind_by_method(
        self,
        labelled_base: SparseHypergraph,
        vertex_relabelled: SparseHypergraph,
        edge_relabelled: SparseHypergraph,
    ) -> None:
        """The four label-blind competitors return exactly 0 on a pure relabelling.

        Pinned separately from the parametrized sweep because it is the claim
        the audit makes in prose: these arms are blind by method, so relabelling
        moves them not a little but not at all.
        """
        for name in ("netlsd_l2", "hpd_jsd", "size_l1", "degree_seq_l1"):
            distance = registry.get_distance(name)
            assert distance.pairwise(labelled_base, vertex_relabelled) == pytest.approx(
                0.0, abs=1e-9
            ), name
            assert distance.pairwise(labelled_base, edge_relabelled) == pytest.approx(
                0.0, abs=1e-9
            ), name

    def test_labels_used_helper_matches_the_class_attribute(self) -> None:
        for name in registry.available_distances():
            assert registry.labels_used(name) == registry.get_distance(name).labels_used


# ---------------------------------------------------------------------------
# Finiteness on labelled input
# ---------------------------------------------------------------------------


class TestFiniteOnLabelledInput:
    """No registered arm may return NaN, infinity, or raise on a labelled pair."""

    @pytest.mark.parametrize("name", _behavioural_arms())
    def test_finite_and_non_negative(self, name: str) -> None:
        rng = random.Random(11)
        distance = registry.get_distance(name)
        small = name in EXPENSIVE_ARMS
        for _ in range(4 if small else 15):
            a = _random_labelled(rng, small=small)
            b = _random_labelled(rng, small=small)
            value = distance.pairwise(a, b)
            assert isinstance(value, float), name
            assert math.isfinite(value), f"{name} returned {value}"
            assert value >= 0.0, f"{name} returned {value}"

    @pytest.mark.parametrize("name", _behavioural_arms())
    def test_self_distance_is_zero(self, name: str, labelled_base: SparseHypergraph) -> None:
        assert registry.get_distance(name).pairwise(labelled_base, labelled_base) == pytest.approx(
            0.0, abs=1e-6
        )


# ---------------------------------------------------------------------------
# The new certificate-rows arm
# ---------------------------------------------------------------------------


class TestNautyCertRows:
    """``nauty_cert_rows`` is the second tokenization of the same canonical form."""

    def test_registered(self) -> None:
        assert registry.get_distance("nauty_cert_rows").name == "nauty_cert_rows"

    def test_zero_on_isomorphic_pairs(self) -> None:
        rng = random.Random(3)
        distance = registry.get_distance("nauty_cert_rows")
        for _ in range(25):
            H = _random_labelled(rng)
            sigma = list(range(H.n_nodes))
            rng.shuffle(sigma)
            assert distance.pairwise(H, permute(H, sigma)) == 0.0

    def test_positive_on_non_isomorphic_pairs(self) -> None:
        """Exactness at zero: a non-isomorphic pair never collides."""
        from isalhg.iso_backends.pynauty_levi import PynautyLeviBackend

        backend = PynautyLeviBackend()
        distance = registry.get_distance("nauty_cert_rows")
        rng = random.Random(5)
        checked = 0
        for _ in range(200):
            a, b = _random_labelled(rng), _random_labelled(rng)
            if backend.fingerprint(a) == backend.fingerprint(b):
                continue
            checked += 1
            assert distance.pairwise(a, b) > 0.0
        assert checked >= 50, f"only {checked} non-isomorphic pairs sampled"

    def test_agrees_with_the_certificate_arm_on_the_iso_partition(self) -> None:
        """Both tokenizations read one canonical form, so they must agree on ``d == 0``."""
        rows = registry.get_distance("nauty_cert_rows")
        cert = registry.get_distance("nauty_cert")
        rng = random.Random(7)
        for _ in range(60):
            a, b = _random_labelled(rng), _random_labelled(rng)
            assert (rows.pairwise(a, b) == 0.0) == (cert.pairwise(a, b) == 0.0)

    def test_matrix_matches_pairwise(self) -> None:
        np = pytest.importorskip("numpy")
        rng = random.Random(13)
        corpus = [_random_labelled(rng) for _ in range(6)]
        distance = registry.get_distance("nauty_cert_rows")
        matrix = distance.matrix(corpus)
        assert matrix.shape == (6, 6)
        np.testing.assert_allclose(matrix, matrix.T)
        np.testing.assert_allclose(np.diag(matrix), 0.0)
        for i in range(6):
            for j in range(i + 1, 6):
                assert matrix[i, j] == distance.pairwise(corpus[i], corpus[j])

    def test_empty_corpus_matrix(self) -> None:
        np = pytest.importorskip("numpy")
        assert registry.get_distance("nauty_cert_rows").matrix([]).shape == (0, 0)
        assert np is not None


# ---------------------------------------------------------------------------
# The two bipartite GED readings
# ---------------------------------------------------------------------------


class TestBipartiteReadings:
    """The edit-path reading bounds the oracle; the assignment reading does not."""

    def test_both_registered_with_the_alias(self) -> None:
        assert registry.get_distance("bipartite_ged_path").name == "bipartite_hged"
        assert registry.get_distance("bipartite_hged").name == "bipartite_hged"
        assert registry.get_distance("bipartite_ged_assign").name == "bipartite_ged_assign"

    def test_path_reading_upper_bounds_the_exact_oracle(self) -> None:
        rng = random.Random(17)
        path = registry.get_distance("bipartite_ged_path")
        exact = registry.get_distance("exact_ged")
        for _ in range(12):
            a = _random_labelled(rng, small=True)
            b = _random_labelled(rng, small=True)
            assert path.pairwise(a, b) >= exact.pairwise(a, b) - 1e-9

    def test_hand_computed_single_edge_relabel(self) -> None:
        """Two single-fact bases differing only in the predicate: one substitution.

        Both readings are worked out by hand. The edit path substitutes the
        hyperedge label at unit cost, so it is 1. The assignment reading is 0:
        its matrix scores a matched vertex pair by ``[types differ] + |deg
        difference|``, the types agree and both degrees are 1, and no predicate
        appears anywhere in the matrix.
        """
        edges = [frozenset({0, 1})]
        a = SparseHypergraph(
            2, edges, n_vertex_labels=1, n_edge_labels=2, vertex_labels=[0, 0], edge_labels=[0]
        )
        b = SparseHypergraph(
            2, edges, n_vertex_labels=1, n_edge_labels=2, vertex_labels=[0, 0], edge_labels=[1]
        )
        assert registry.get_distance("bipartite_ged_path").pairwise(a, b) == 1.0
        assert registry.get_distance("bipartite_ged_assign").pairwise(a, b) == 0.0

    def test_hand_computed_vertex_relabel(self) -> None:
        """One constant's type differs: one substitution in both readings.

        Edit path: the vertex bijection is forced (both bases are a single
        2-fact path), and exactly one matched pair has differing types, so the
        vertex term is 1 and the edge term 0. Assignment: the substitution block
        charges the same 1 for that pair, and the degrees agree.
        """
        edges = [frozenset({0, 1}), frozenset({1, 2})]
        a = SparseHypergraph(
            3,
            edges,
            n_vertex_labels=2,
            n_edge_labels=1,
            vertex_labels=[0, 0, 0],
            edge_labels=[0, 0],
        )
        b = SparseHypergraph(
            3,
            edges,
            n_vertex_labels=2,
            n_edge_labels=1,
            vertex_labels=[0, 0, 1],
            edge_labels=[0, 0],
        )
        assert registry.get_distance("bipartite_ged_path").pairwise(a, b) == 1.0
        assert registry.get_distance("bipartite_ged_assign").pairwise(a, b) == 1.0

    def test_hand_computed_disjoint_sizes(self) -> None:
        """Against the empty base, every constant is an insertion at ``1 + deg``.

        The 2-constant single-fact base has both degrees 1, so the assignment
        value is ``(1 + 1) + (1 + 1) = 4``.
        """
        a = SparseHypergraph(
            2,
            [frozenset({0, 1})],
            n_vertex_labels=1,
            n_edge_labels=1,
            vertex_labels=[0, 0],
            edge_labels=[0],
        )
        empty = SparseHypergraph(
            0, [], n_vertex_labels=1, n_edge_labels=1, vertex_labels=[], edge_labels=[]
        )
        assert registry.get_distance("bipartite_ged_assign").pairwise(a, empty) == 4.0
        assert registry.get_distance("bipartite_ged_assign").pairwise(empty, empty) == 0.0

    def test_assignment_reading_is_symmetric_and_zero_on_isomorphic_pairs(self) -> None:
        rng = random.Random(19)
        distance = registry.get_distance("bipartite_ged_assign")
        for _ in range(20):
            H = _random_labelled(rng)
            sigma = list(range(H.n_nodes))
            rng.shuffle(sigma)
            image = permute(H, sigma)
            assert distance.pairwise(H, image) == pytest.approx(0.0, abs=1e-9)
            assert distance.pairwise(H, image) == pytest.approx(distance.pairwise(image, H))

    def test_assignment_reading_has_false_zeros(self) -> None:
        """The documented failure mode, pinned so nobody "fixes" it into a metric.

        Two non-isomorphic bases whose constants pair up with equal degrees and
        matching types score 0: nothing in the matrix records *which* constants
        share a fact. RQ2 measures the rate of exactly this.
        """
        from isalhg.iso_backends.pynauty_levi import PynautyLeviBackend

        # Two 3-facts sharing a vertex pair, vs three 2-facts in a path: both
        # have degree sequence [2, 2, 1, 1].
        a = SparseHypergraph(
            4,
            [frozenset({0, 1, 2}), frozenset({0, 1, 3})],
            n_vertex_labels=1,
            n_edge_labels=1,
            vertex_labels=[0] * 4,
            edge_labels=[0, 0],
        )
        b = SparseHypergraph(
            4,
            [frozenset({0, 1}), frozenset({1, 2}), frozenset({2, 3})],
            n_vertex_labels=1,
            n_edge_labels=1,
            vertex_labels=[0] * 4,
            edge_labels=[0, 0, 0],
        )
        backend = PynautyLeviBackend()
        assert backend.fingerprint(a) != backend.fingerprint(b)
        assert registry.get_distance("bipartite_ged_assign").pairwise(a, b) == 0.0
        # The edit-path reading is not fooled.
        assert registry.get_distance("bipartite_ged_path").pairwise(a, b) > 0.0


# ---------------------------------------------------------------------------
# Aliases and gating
# ---------------------------------------------------------------------------


class TestAliases:
    """Each alias resolves to its canonical arm and computes the same value."""

    @pytest.mark.parametrize(
        ("alias", "canonical"),
        [
            ("nauty_cert", "nauty_levi_edit"),
            ("wl_l1", "hypergraph_wl_l1"),
            ("netlsd", "netlsd_l2"),
            ("exact_ged", "exact_hged"),
            ("bipartite_ged_path", "bipartite_hged"),
        ],
    )
    def test_alias_resolves_and_agrees(
        self, alias: str, canonical: str, labelled_base: SparseHypergraph
    ) -> None:
        assert registry.ALIASES[alias] == canonical
        aliased = registry.get_distance(alias)
        direct = registry.get_distance(canonical)
        assert aliased.name == direct.name
        other = _kb([0, 1, 2, 0, 2], [0, 1, 2])
        assert aliased.pairwise(labelled_base, other) == pytest.approx(
            direct.pairwise(labelled_base, other)
        )

    def test_alias_table_covers_every_alias_name(self) -> None:
        """Every registered name is either canonical or listed in ``ALIASES``."""
        for alias, canonical in registry.ALIASES.items():
            assert alias in registry.available_distances()
            assert registry.get_distance(alias).name == registry.get_distance(canonical).name


class TestHyperCOTGating:
    """The subprocess arm must fail loudly, never return a wrong number."""

    def test_declares_label_blind(self) -> None:
        assert registry.get_distance("hypercot").labels_used == frozenset()

    def test_raises_with_a_setup_hint_when_the_pinned_env_is_absent(
        self, labelled_base: SparseHypergraph
    ) -> None:
        if _hypercot_env_present():
            pytest.skip("the pinned isalhg-hypercot env is installed here")
        with pytest.raises(SubprocessRepresentationError):
            registry.get_distance("hypercot").pairwise(labelled_base, labelled_base)

    def test_returns_a_finite_value_when_the_env_is_present(self) -> None:
        if not _hypercot_env_present():
            pytest.skip("the pinned isalhg-hypercot env is not installed here")
        rng = random.Random(23)
        distance = registry.get_distance("hypercot")
        for _ in range(3):
            value = distance.pairwise(_random_labelled(rng), _random_labelled(rng))
            assert math.isfinite(value)

    def test_isomorphic_pairs_score_near_zero_but_may_go_slightly_negative(self) -> None:
        """The co-optimal transport cost is a numerical optimum, not an exact count.

        Measured here: an isomorphic pair returns ``-9.9e-16`` rather than
        ``0.0``. Consumers must therefore compare with a tolerance and clamp at
        zero -- an unclamped ``sqrt`` or a non-negativity assertion downstream
        would fail on a *correct* result. Pinned so the requirement is visible
        to whoever writes the matrix builder.
        """
        if not _hypercot_env_present():
            pytest.skip("the pinned isalhg-hypercot env is not installed here")
        rng = random.Random(29)
        distance = registry.get_distance("hypercot")
        H = _random_labelled(rng)
        sigma = list(range(H.n_nodes))
        rng.shuffle(sigma)
        value = distance.pairwise(H, permute(H, sigma))
        assert value == pytest.approx(0.0, abs=1e-9)
