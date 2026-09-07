"""Stabiliser-orbit pruning is value-preserving, and the rank program is complete.

Three claims are separated deliberately, because they can fail independently:

1. *The hook is value-neutral.* Driving the search with
   :class:`~isalhg.core.orbit_oracle.TrivialOrbitOracle` -- which returns every
   branch set unchanged -- must reproduce the hook-off output exactly. A
   difference here is a plumbing bug, not a group-theory bug.
2. *The pruning is value-preserving.* Driving it with the real
   :class:`~isalhg.iso_backends.orbit_oracle.PynautyOrbitOracle` must reproduce
   the frozen ``w*_c``. The pins are re-derived from
   ``tests/unit/core/test_wstar_c_frozen.py`` (which is frozen and never
   edited); a mismatch means the pruning removed a branch that was not an
   automorphic duplicate.
3. *``canonical_rank`` is a canonical form.* It is a different program from
   ``w*_c``, so nothing pins its value; what is tested is that its fingerprint
   is invariant under relabelling and separates isomorphism classes.

Marker policy. Only the two true-STS(13) pins carry ``slow``; they are the one
fixture whose pruned search costs minutes rather than seconds on the Python
engine. Everything else -- including the full 500-instance and 200-star
differentials against the unpruned search -- runs unmarked, in well under a
minute in total.
"""

from __future__ import annotations

import hashlib
import random

import pytest

from isalhg.core.canonical import canonical_fingerprint, canonical_string
from isalhg.core.hypergraph_to_string import _python_greedy_h2s, greedy_h2s
from isalhg.core.instructions import serialize
from isalhg.core.orbit_oracle import OrbitOracle, TrivialOrbitOracle
from isalhg.core.sparse_hypergraph import SparseHypergraph, permute

pynauty = pytest.importorskip("pynauty")

from isalhg.iso_backends.orbit_oracle import (  # noqa: E402
    PynautyOrbitOracle,
    canonical_fingerprint_orbit,
    canonical_fingerprint_rank,
    canonical_string_orbit,
    canonical_string_rank,
)
from isalhg.iso_backends.pynauty_levi import PynautyLeviBackend  # noqa: E402

pytestmark = pytest.mark.unit

# Re-derived from the frozen pins of ``test_wstar_c_frozen.py``. That file is
# the definitional record and is never edited; these copies exist so a failure
# here names orbit pruning rather than the canonical form.
_PIN_FANO = (121, "9695315fb1566ec737ee3b22ee65e6423690bd1a82f8c7e010b2a312214ea79b")
_PIN_STS9 = (227, "a6282f853d79d251b58a7b8962f9e54496a225483a8785adffbcb511312047cc")
_PIN_C13_013 = (256, "77d9fa1e4e99d500c3bed2debf32d6da773b1721c7e3ea26f5a734ac0ec89bec")
_PIN_CE_N4 = (54, "ab9393ffb4dc117f86481e09b44b54e2fbfc01be166aa2f3e2fdfbead0656ba3")
_PIN_STS13_TRUE = {
    0: (472, "4e5e682d86de95fe7526bce05c74519856270e3eb8e907e99437b3efb53f0cc6"),
    1: (472, "bd872631a5a5a17256c411159c1a10f40d5d8ef63ef0893ab2fcbbd7a5467eca"),
}


def _pin(w: str) -> tuple[int, str]:
    return len(w), hashlib.sha256(w.encode()).hexdigest()


def _c13_013() -> SparseHypergraph:
    return SparseHypergraph(
        n_nodes=13,
        hyperedges=[frozenset({i, (i + 1) % 13, (i + 3) % 13}) for i in range(13)],
    )


def _ce_n4() -> SparseHypergraph:
    return SparseHypergraph(
        n_nodes=4,
        hyperedges=[
            frozenset({1, 3}),
            frozenset({0, 1, 3}),
            frozenset({0, 2, 3}),
            frozenset({1, 2}),
        ],
    )


# ---------------------------------------------------------------------------
# Random generators
# ---------------------------------------------------------------------------


def _random_connected(
    rng: random.Random,
    n_vertex_labels: int | None = None,
    n_edge_labels: int | None = None,
) -> SparseHypergraph:
    """A connected labelled hypergraph, ``n <= 8``, arity <= 4, <= 3 labels a side.

    Built by growing a spanning structure first (each new vertex enters an edge
    with an already-placed one), so connectivity holds by construction.

    ``n_vertex_labels`` / ``n_edge_labels`` may be pinned by the caller. Two
    hypergraphs are only comparable when they declare the *same* vocabulary
    sizes: the Levi colouring places edge-node colours at
    ``|Sigma_v| + edge_label``, so a differing ``|Sigma_v|`` shifts every
    edge-side colour and ``pynauty_levi`` reports non-isomorphism on
    structurally identical inputs.
    """
    n = rng.randint(2, 8)
    n_vl = rng.randint(1, 3) if n_vertex_labels is None else n_vertex_labels
    n_el = rng.randint(1, 3) if n_edge_labels is None else n_edge_labels
    placed = [0]
    edges: set[frozenset[int]] = set()
    for v in range(1, n):
        arity = rng.randint(2, min(4, len(placed) + 1))
        members = {v, *rng.sample(placed, arity - 1)}
        edges.add(frozenset(members))
        placed.append(v)
    for _ in range(rng.randint(0, 4)):
        arity = rng.randint(2, min(4, n))
        edges.add(frozenset(rng.sample(range(n), arity)))
    edge_list = sorted(edges, key=lambda e: (len(e), sorted(e)))
    return SparseHypergraph(
        n_nodes=n,
        hyperedges=edge_list,
        n_vertex_labels=n_vl,
        n_edge_labels=n_el,
        vertex_labels=[rng.randrange(n_vl) for _ in range(n)],
        edge_labels=[rng.randrange(n_el) for _ in edge_list],
    )


def _random_star(rng: random.Random) -> SparseHypergraph:
    """A hub with 3--8 leaves: the symmetric regime orbit pruning targets.

    Some facts have arity 3--4 (hub + two or three leaves) and some leaves
    appear in a second fact, so the stabiliser is non-trivial but generally
    smaller than the full symmetric group on the leaves.
    """
    q = rng.randint(3, 8)
    n = q + 1
    leaves = list(range(1, n))
    n_el = rng.randint(1, 3)
    edges: set[frozenset[int]] = {frozenset({0, leaf}) for leaf in leaves}
    for _ in range(rng.randint(0, 2)):
        arity = rng.randint(2, min(3, q))
        edges.add(frozenset({0, *rng.sample(leaves, arity)}))
    for _ in range(rng.randint(0, 2)):
        if q >= 2:
            edges.add(frozenset(rng.sample(leaves, 2)))
    edge_list = sorted(edges, key=lambda e: (len(e), sorted(e)))
    return SparseHypergraph(
        n_nodes=n,
        hyperedges=edge_list,
        n_edge_labels=n_el,
        edge_labels=[rng.randrange(n_el) for _ in edge_list],
    )


def _arity_k(*graphs: SparseHypergraph) -> int:
    return max(
        2,
        *(max((len(H.members(e)) for e in H.edges()), default=2) for H in graphs),
    )


def _unpruned(H: SparseHypergraph) -> str:
    """``w*_c`` from the unpruned Python tie-complete search."""
    return canonical_string(H, algorithm="canonical", backend="python")


def _pruned(H: SparseHypergraph) -> str:
    """``w*_c`` from the orbit-pruned Python search."""
    return canonical_string_orbit(H)


def _assert_hook_is_neutral(H: SparseHypergraph) -> None:
    """Hook-off and ``TrivialOrbitOracle`` emit the identical token sequence."""
    k = _arity_k(H)
    off = _python_greedy_h2s(H, seed_node=0, k=k, inplace=True, tie_branch=True)
    on = _python_greedy_h2s(
        H, seed_node=0, k=k, inplace=True, tie_branch=True, orbit_oracle=TrivialOrbitOracle()
    )
    assert serialize(list(on)) == serialize(list(off))


# ---------------------------------------------------------------------------
# 1. The hook is value-neutral
# ---------------------------------------------------------------------------


class TestTrivialOracleIsValueNeutral:
    """``TrivialOrbitOracle`` must leave the search output untouched."""

    def test_trivial_oracle_satisfies_the_protocol(self) -> None:
        assert isinstance(TrivialOrbitOracle(), OrbitOracle)

    def test_matches_hook_off_on_the_fano_plane(self, fano_plane: SparseHypergraph) -> None:
        _assert_hook_is_neutral(fano_plane)

    def test_matches_hook_off_on_the_n4_counterexample(self) -> None:
        _assert_hook_is_neutral(_ce_n4())

    def test_matches_hook_off_on_200_random_instances(self) -> None:
        rng = random.Random(20260906)
        for _ in range(200):
            _assert_hook_is_neutral(_random_connected(rng))


# ---------------------------------------------------------------------------
# 2. The pruning is value-preserving
# ---------------------------------------------------------------------------


class TestFrozenPins:
    """``canonical_string_orbit`` reproduces the frozen ``w*_c`` bit for bit."""

    def test_fano(self, fano_plane: SparseHypergraph) -> None:
        assert _pin(canonical_string_orbit(fano_plane, k=3)) == _PIN_FANO

    def test_sts_9(self, sts_9: SparseHypergraph) -> None:
        assert _pin(canonical_string_orbit(sts_9, k=3)) == _PIN_STS9

    def test_n4_counterexample(self) -> None:
        assert _pin(canonical_string_orbit(_ce_n4(), k=3)) == _PIN_CE_N4

    def test_cyclic_triple_orbit_13(self) -> None:
        assert _pin(canonical_string_orbit(_c13_013(), k=3)) == _PIN_C13_013

    def test_gq_2_2_matches_the_cpp_engine(self, gq_2_2_doily: SparseHypergraph) -> None:
        # No frozen pin exists for the doily; the C++ w*_c is the reference.
        expected = canonical_string(gq_2_2_doily, k=3, algorithm="canonical", backend="cpp")
        assert canonical_string_orbit(gq_2_2_doily, k=3) == expected

    @pytest.mark.slow
    @pytest.mark.parametrize("catalog_index", sorted(_PIN_STS13_TRUE))
    def test_true_sts13(self, catalog_index: int) -> None:
        from isalhg.datasets.synthetic.sts_catalog import steiner_triple_system

        H = steiner_triple_system(13, catalog_index)
        assert _pin(canonical_string_orbit(H, k=3)) == _PIN_STS13_TRUE[catalog_index]


class TestDifferentialAgainstUnprunedSearch:
    """Pruned and unpruned Python searches agree on every sampled instance."""

    def test_500_random_connected_labelled_instances(self) -> None:
        rng = random.Random(4242)
        for i in range(500):
            H = _random_connected(rng)
            assert _pruned(H) == _unpruned(H), f"instance {i} diverged"

    def test_200_random_stars(self) -> None:
        rng = random.Random(99)
        for i in range(200):
            H = _random_star(rng)
            assert _pruned(H) == _unpruned(H), f"star {i} diverged"

    def test_pruning_actually_collapses_a_symmetric_star(self) -> None:
        # Hub plus 7 interchangeable leaves: the unpruned search walks every
        # injective placement sequence (sum_d 7!/(7-d)! = 13,700 states), the
        # pruned one walks q+1.
        H = SparseHypergraph(n_nodes=8, hyperedges=[frozenset({0, i}) for i in range(1, 8)])
        off: dict[str, int] = {}
        on: dict[str, int] = {}
        w_off = _python_greedy_h2s(H, seed_node=0, k=2, inplace=True, tie_branch=True, stats=off)
        w_on = _python_greedy_h2s(
            H,
            seed_node=0,
            k=2,
            inplace=True,
            tie_branch=True,
            orbit_oracle=PynautyOrbitOracle(),
            stats=on,
        )
        assert w_on == w_off
        assert off["frames"] == 13700
        assert on["frames"] == 8
        assert on["v_branches"] == 7


class TestUnhonourableRequestsRaise:
    """The oracle and the ranks never fall back silently."""

    def test_oracle_on_the_cpp_backend_raises(self, fano_plane: SparseHypergraph) -> None:
        with pytest.raises(ValueError, match="backend='python'"):
            greedy_h2s(
                fano_plane,
                seed_node=0,
                k=3,
                tie_branch=True,
                backend="cpp",
                orbit_oracle=TrivialOrbitOracle(),
            )

    def test_oracle_without_tie_branch_raises(self, fano_plane: SparseHypergraph) -> None:
        with pytest.raises(ValueError, match="tie_branch=True"):
            greedy_h2s(
                fano_plane,
                seed_node=0,
                k=3,
                backend="python",
                orbit_oracle=TrivialOrbitOracle(),
            )

    def test_canonical_orbit_without_an_oracle_raises(self, fano_plane: SparseHypergraph) -> None:
        with pytest.raises(ValueError, match="requires an orbit_oracle"):
            canonical_string(fano_plane, k=3, algorithm="canonical_orbit")

    def test_canonical_orbit_on_the_cpp_backend_raises(self, fano_plane: SparseHypergraph) -> None:
        with pytest.raises(ValueError, match="Python backend only"):
            canonical_string(
                fano_plane,
                k=3,
                algorithm="canonical_orbit",
                backend="cpp",
                orbit_oracle=PynautyOrbitOracle(),
            )

    def test_oracle_with_another_algorithm_raises(self, fano_plane: SparseHypergraph) -> None:
        with pytest.raises(ValueError, match="only honoured by"):
            canonical_string(
                fano_plane, k=3, algorithm="canonical", orbit_oracle=PynautyOrbitOracle()
            )

    def test_canonical_rank_without_ranks_raises(self, fano_plane: SparseHypergraph) -> None:
        with pytest.raises(ValueError, match="requires ranks"):
            canonical_string(fano_plane, k=3, algorithm="canonical_rank")

    def test_ranks_with_tie_branch_raises(self, fano_plane: SparseHypergraph) -> None:
        with pytest.raises(ValueError, match="mutually exclusive"):
            greedy_h2s(
                fano_plane,
                seed_node=0,
                k=3,
                tie_branch=True,
                backend="python",
                ranks=tuple(range(7)),
            )

    def test_ranks_of_the_wrong_length_raise(self, fano_plane: SparseHypergraph) -> None:
        with pytest.raises(ValueError, match="expected 7"):
            canonical_string(
                fano_plane, k=3, algorithm="canonical_rank", ranks=(0, 1, 2), backend="python"
            )


class TestExistingProgramsAreUntouched:
    """The hooks must not move the byte-level output of any shipped algorithm."""

    @pytest.mark.parametrize(
        "algorithm", ["canonical", "greedy_min", "greedy_min_nbrdeg", "greedy_single"]
    )
    def test_python_and_cpp_still_agree(self, algorithm: str, fano_plane: SparseHypergraph) -> None:
        py = canonical_string(fano_plane, k=3, algorithm=algorithm, backend="python")
        cpp = canonical_string(fano_plane, k=3, algorithm=algorithm, backend="cpp")
        assert py == cpp


class TestOrbitFingerprint:
    """``canonical_fingerprint_orbit`` matches the unpruned fingerprint."""

    def test_matches_on_a_labelled_instance(self, qin_fig1_hypergraph: SparseHypergraph) -> None:
        expected = canonical_fingerprint(qin_fig1_hypergraph, algorithm="canonical")
        assert canonical_fingerprint_orbit(qin_fig1_hypergraph) == expected


# ---------------------------------------------------------------------------
# 3. canonical_rank is a canonical form (a different one)
# ---------------------------------------------------------------------------


class TestCanonicalRankInvariance:
    """``F_rank`` is constant on isomorphism classes."""

    @staticmethod
    def _reorder_edges(H: SparseHypergraph, order: list[int]) -> SparseHypergraph:
        """The same hypergraph, with its edges inserted in ``order``."""
        eids = list(H.edges())
        return SparseHypergraph(
            n_nodes=H.n_nodes,
            hyperedges=[H.members(eids[i]) for i in order],
            n_vertex_labels=H.n_vertex_labels,
            n_edge_labels=H.n_edge_labels,
            vertex_labels=[H.vertex_label(v) for v in H.nodes()],
            edge_labels=[H.edge_label(eids[i]) for i in order],
        )

    @pytest.mark.parametrize("fixture_name", ["fano_plane", "sts_9"])
    def test_invariant_under_100_relabellings(
        self, fixture_name: str, request: pytest.FixtureRequest
    ) -> None:
        H: SparseHypergraph = request.getfixturevalue(fixture_name)
        expected = canonical_fingerprint_rank(H, k=3)
        rng = random.Random(7)
        order = list(range(H.n_nodes))
        for _ in range(100):
            rng.shuffle(order)
            assert canonical_fingerprint_rank(permute(H, list(order)), k=3) == expected

    def test_invariant_on_200_random_instances(self) -> None:
        rng = random.Random(1234)
        for i in range(200):
            H = _random_connected(rng)
            order = list(range(H.n_nodes))
            rng.shuffle(order)
            assert canonical_fingerprint_rank(H) == canonical_fingerprint_rank(permute(H, order)), (
                f"instance {i} not invariant"
            )

    def test_invariant_under_edge_insertion_order_on_400_instances(self) -> None:
        """Edge ids must not be observable.

        ``permute`` relabels vertices but preserves edge ids, so the relabelling
        tests above cannot see a residual tie broken by edge id. This one
        rebuilds the same hypergraph with its edges inserted in a shuffled
        order, which is exactly what the rank key exists to make irrelevant.
        """
        rng = random.Random(20260907)
        for i in range(400):
            H = _random_connected(rng)
            k = _arity_k(H)
            expected = canonical_fingerprint_rank(H, k=k)
            order = list(range(H.n_edges))
            rng.shuffle(order)
            G = self._reorder_edges(H, order)
            assert canonical_fingerprint_rank(G, k=k) == expected, (
                f"instance {i} depends on edge insertion order"
            )


def _rank_pair_census(n_pairs: int, seed: int) -> tuple[int, int]:
    """Compare ``F_rank`` equality with pynauty isomorphism over random pairs.

    Both members of a pair declare the *same* vocabulary sizes. Comparing
    fingerprints across differing vocabularies is not defined: the Levi
    colouring offsets edge colours by ``|Sigma_v|``, so ``pynauty_levi``
    separates structurally identical inputs that declare different
    ``n_vertex_labels`` while every canonical string -- ``w*_c`` included --
    merges them.

    Returns
    -------
    tuple[int, int]
        ``(pairs compared, isomorphic pairs among them)``.
    """
    rng = random.Random(seed)
    backend = PynautyLeviBackend()
    iso_pairs = 0
    for i in range(n_pairs):
        n_vl, n_el = rng.randint(1, 3), rng.randint(1, 3)
        left = _random_connected(rng, n_vl, n_el)
        if rng.random() < 0.5:
            order = list(range(left.n_nodes))
            rng.shuffle(order)
            right = permute(left, order)
            iso_pairs += 1
        else:
            right = _random_connected(rng, n_vl, n_el)
        k = _arity_k(left, right)
        same = canonical_fingerprint_rank(left, k=k) == canonical_fingerprint_rank(right, k=k)
        assert same == backend.are_isomorphic(left, right), f"pair {i} disagrees with pynauty"
    return n_pairs, iso_pairs


class TestCanonicalRankCompleteness:
    """Fingerprint equality agrees with pynauty on isomorphism."""

    def test_agrees_with_pynauty_on_500_pairs(self) -> None:
        compared, iso_pairs = _rank_pair_census(500, 31337)
        assert compared == 500
        assert iso_pairs > 200


class TestCanonicalRankIsADifferentProgram:
    """It is complete, but it is not ``w*_c`` -- pin the difference."""

    def test_differs_from_wstar_c_on_the_n4_counterexample(self) -> None:
        H = _ce_n4()
        assert canonical_string_rank(H, k=3) != canonical_string(H, k=3, algorithm="canonical")

    def test_equals_wstar_c_where_ties_do_not_bite(self, fano_plane: SparseHypergraph) -> None:
        assert canonical_string_rank(fano_plane, k=3) == canonical_string(
            fano_plane, k=3, algorithm="canonical"
        )
