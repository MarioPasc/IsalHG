"""The C++ ``canonical_rank`` engine is the Python one, bit for bit.

``canonical_rank`` is the family's greedy walk with the residual V tie and the
new-vertex order resolved by a canonical rank vector. Both branch sets collapse
to a singleton, so the walk is a single deterministic path -- and therefore a
canonical form whose value must not depend on which engine computed it.

Three claims, separable on failure:

1. *The two engines agree.* Every fixture the Python reference can encode, plus
   1,000 random connected labelled hypergraphs and 300 random stars, produce the
   identical string on ``backend="python"`` and ``backend="cpp"``. A difference
   is an encoder bug, not an interface bug.
2. *The interface is honest.* Ranks that are absent, mis-sized, or not a
   permutation raise instead of producing a silently wrong string; ``ranks``
   with any other algorithm raises; the C++ engine refuses to combine ranks
   with tie branching.
3. *The C++ engine reaches where the Python one cannot.* The Python reference
   materialises ``(2r+1)^k`` displacement tuples, so it is unusable above arity
   4; the C++ engine encodes arity-6 and arity-8 instances, and the strings it
   returns are relabelling-invariant and separate isomorphism classes.

The corpus-scale differential (wd50k66, ndc_classes) lives in
``tests/integration/test_cpp_rank_corpus.py``; it needs the results drive.
"""

from __future__ import annotations

import random

import pytest

from isalhg.core.canonical import canonical_string, required_k
from isalhg.core.hypergraph_to_string import greedy_h2s
from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.errors import IsalHGError

pynauty = pytest.importorskip("pynauty")

from isalhg.iso_backends.canonical_order import canonical_ranks  # noqa: E402
from isalhg.iso_backends.orbit_oracle import (  # noqa: E402
    canonical_fingerprint_rank,
    canonical_string_rank,
)
from isalhg.iso_backends.pynauty_levi import PynautyLeviBackend  # noqa: E402

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------


def _random_connected(
    rng: random.Random,
    n_vertex_labels: int | None = None,
    n_edge_labels: int | None = None,
    max_arity: int = 4,
    max_n: int = 12,
) -> SparseHypergraph:
    """A connected labelled hypergraph, built spanning-first so it is connected.

    Defaults match what the Python reference can still encode: arity <= 4,
    n <= 12, <= 3 labels a side.
    """
    n = rng.randint(2, max_n)
    n_vl = rng.randint(1, 3) if n_vertex_labels is None else n_vertex_labels
    n_el = rng.randint(1, 3) if n_edge_labels is None else n_edge_labels
    placed = [0]
    edges: set[frozenset[int]] = set()
    for v in range(1, n):
        arity = rng.randint(2, min(max_arity, len(placed) + 1))
        edges.add(frozenset({v, *rng.sample(placed, arity - 1)}))
        placed.append(v)
    for _ in range(rng.randint(0, 4)):
        arity = rng.randint(2, min(max_arity, n))
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
    """A hub with 3--10 leaves: the symmetric regime where residual ties bite.

    Some facts have arity 3--4 (hub plus two or three leaves) and some leaves
    sit in a second fact, so the automorphism group is large but not the full
    symmetric group on the leaves.
    """
    q = rng.randint(3, 10)
    n = q + 1
    leaves = list(range(1, n))
    n_el = rng.randint(1, 3)
    edges: set[frozenset[int]] = {frozenset({0, leaf}) for leaf in leaves}
    for _ in range(rng.randint(1, 3)):
        arity = rng.randint(2, min(3, q))
        edges.add(frozenset({0, *rng.sample(leaves, arity)}))
    for _ in range(rng.randint(1, 3)):
        if q >= 2:
            edges.add(frozenset(rng.sample(leaves, 2)))
    edge_list = sorted(edges, key=lambda e: (len(e), sorted(e)))
    return SparseHypergraph(
        n_nodes=n,
        hyperedges=edge_list,
        n_edge_labels=n_el,
        edge_labels=[rng.randrange(n_el) for _ in edge_list],
    )


def _random_high_arity(rng: random.Random) -> SparseHypergraph:
    """A connected instance with arity up to 8 -- beyond the Python reference.

    The Python encoder enumerates ``(2r+1)^k`` displacement tuples per frame,
    which is why the corpora with arity median 6 are C++-only. These instances
    exercise that regime, and deliberately include far-apart high-arity facts:
    they are the adversarial corner where the C++ frame also pays, because the
    cost-class enumeration is combinatorial in ``k_disp`` (measured 1.6 s per
    instance at arity 8, against 0.05 ms on the real ndc_classes members).
    Tests over this family are marked ``slow`` for that reason; the real
    high-arity evidence at scale is
    ``tests/integration/test_cpp_rank_corpus.py``.
    """
    n = rng.randint(9, 14)
    placed = [0]
    edges: set[frozenset[int]] = set()
    for v in range(1, n):
        arity = rng.randint(2, min(8, len(placed) + 1))
        edges.add(frozenset({v, *rng.sample(placed, arity - 1)}))
        placed.append(v)
    for _ in range(rng.randint(1, 3)):
        arity = rng.randint(5, min(8, n))
        edges.add(frozenset(rng.sample(range(n), arity)))
    edge_list = sorted(edges, key=lambda e: (len(e), sorted(e)))
    return SparseHypergraph(n_nodes=n, hyperedges=edge_list)


def _dense_arity_6(rng: random.Random) -> SparseHypergraph:
    """An arity-6 instance shaped like the corpus members: overlapping facts.

    ``ndc_classes`` has arity median 6 and its facts overlap heavily, so the
    walk emits at displacement cost 0--1 and the frame is sub-millisecond.
    This is the cheap high-arity family; :func:`_random_high_arity` is the
    adversarial one.
    """
    n = rng.randint(8, 11)
    base = list(range(n))
    edges: set[frozenset[int]] = set()
    for start in range(0, n - 5):
        edges.add(frozenset(base[start : start + 6]))
    for _ in range(rng.randint(1, 3)):
        arity = rng.randint(3, 6)
        start = rng.randint(0, n - arity)
        edges.add(frozenset(base[start : start + arity]))
    edge_list = sorted(edges, key=lambda e: (len(e), sorted(e)))
    return SparseHypergraph(n_nodes=n, hyperedges=edge_list)


def _both_engines(H: SparseHypergraph, k: int | None = None) -> tuple[str, str]:
    """``(python, cpp)`` ``canonical_rank`` strings for the same ``(H, k, ranks)``."""
    ranks = canonical_ranks(H)
    kk = required_k(H) if k is None else k
    common = {"k": kk, "algorithm": "canonical_rank", "ranks": ranks}
    return (
        canonical_string(H, backend="python", **common),
        canonical_string(H, backend="cpp", **common),
    )


# ---------------------------------------------------------------------------
# 1. The two engines agree
# ---------------------------------------------------------------------------


class TestBackendsAgreeOnFixtures:
    """Every design fixture the Python reference can encode."""

    @pytest.mark.parametrize(
        "fixture_name",
        [
            "trivial_hypergraph",
            "single_edge_hypergraph",
            "fano_plane",
            "sts_9",
            "gq_2_2_doily",
            "qin_fig1_hypergraph",
        ],
    )
    def test_named_fixture(self, fixture_name: str, request: pytest.FixtureRequest) -> None:
        H: SparseHypergraph = request.getfixturevalue(fixture_name)
        py, cpp = _both_engines(H)
        assert py == cpp

    def test_cyclic_triple_13_pair(
        self, cyclic_triple_13_pair: tuple[SparseHypergraph, SparseHypergraph]
    ) -> None:
        for H in cyclic_triple_13_pair:
            py, cpp = _both_engines(H)
            assert py == cpp

    def test_iso_pair_small(
        self, iso_pair_small: tuple[SparseHypergraph, SparseHypergraph, list[int]]
    ) -> None:
        left, right, _ = iso_pair_small
        k = max(required_k(left), required_k(right))
        for H in (left, right):
            py, cpp = _both_engines(H, k=k)
            assert py == cpp

    def test_non_iso_pair_small(
        self, non_iso_pair_small: tuple[SparseHypergraph, SparseHypergraph]
    ) -> None:
        left, right = non_iso_pair_small
        k = max(required_k(left), required_k(right))
        for H in (left, right):
            py, cpp = _both_engines(H, k=k)
            assert py == cpp

    def test_n4_tie_counterexample(self) -> None:
        """The n=4 instance that pins ``w*_greedy != w*_c``.

        It is the smallest input where the residual V tie is non-trivial, so
        it is the smallest place the rank key can change the answer.
        """
        H = SparseHypergraph(
            n_nodes=4,
            hyperedges=[
                frozenset({1, 3}),
                frozenset({0, 1, 3}),
                frozenset({0, 2, 3}),
                frozenset({1, 2}),
            ],
        )
        py, cpp = _both_engines(H, k=3)
        assert py == cpp


class TestBackendsAgreeOnRandomInstances:
    """1,000 random connected labelled hypergraphs plus 300 random stars."""

    def test_1000_random_connected(self) -> None:
        rng = random.Random(20260907)
        for i in range(1000):
            H = _random_connected(rng)
            py, cpp = _both_engines(H)
            assert py == cpp, f"instance {i} differs\n  py ={py}\n  cpp={cpp}"

    def test_300_random_stars(self) -> None:
        rng = random.Random(4242)
        for i in range(300):
            H = _random_star(rng)
            py, cpp = _both_engines(H)
            assert py == cpp, f"star {i} differs\n  py ={py}\n  cpp={cpp}"

    def test_agree_under_relabelling(self) -> None:
        """Agreement must survive the relabelling, not only the given layout."""
        rng = random.Random(99)
        for _ in range(200):
            H = _random_connected(rng, max_n=8)
            order = list(range(H.n_nodes))
            rng.shuffle(order)
            G = permute(H, order)
            py, cpp = _both_engines(G, k=max(required_k(H), required_k(G)))
            assert py == cpp


# ---------------------------------------------------------------------------
# 2. The interface is honest
# ---------------------------------------------------------------------------


class TestRankArgumentContract:
    """Bad rank vectors raise; they never yield a quietly wrong string."""

    def test_missing_ranks_raises(self, fano_plane: SparseHypergraph) -> None:
        with pytest.raises(ValueError, match="requires ranks"):
            canonical_string(fano_plane, k=3, algorithm="canonical_rank", backend="cpp")

    def test_wrong_length_raises(self, fano_plane: SparseHypergraph) -> None:
        with pytest.raises(ValueError, match="length"):
            canonical_string(
                fano_plane, k=3, algorithm="canonical_rank", backend="cpp", ranks=[0, 1, 2]
            )

    @pytest.mark.parametrize(
        "bad",
        [
            [0, 1, 2, 3, 4, 5, 5],  # repeated rank
            [0, 1, 2, 3, 4, 5, 7],  # out of range
            [-1, 1, 2, 3, 4, 5, 6],  # negative
        ],
    )
    def test_non_permutation_raises(self, fano_plane: SparseHypergraph, bad: list[int]) -> None:
        with pytest.raises(IsalHGError, match="permutation"):
            canonical_string(fano_plane, k=3, algorithm="canonical_rank", backend="cpp", ranks=bad)

    def test_ranks_with_other_algorithm_raises(self, fano_plane: SparseHypergraph) -> None:
        with pytest.raises(ValueError, match="only honoured by"):
            canonical_string(
                fano_plane, k=3, algorithm="canonical", backend="cpp", ranks=list(range(7))
            )

    def test_cpp_greedy_h2s_still_refuses_ranks(self, fano_plane: SparseHypergraph) -> None:
        """``greedy_h2s`` is the per-seed entry; ranks belong on the canonical one."""
        with pytest.raises(ValueError, match="ranks requires backend"):
            greedy_h2s(fano_plane, seed_node=0, k=3, backend="cpp", ranks=list(range(7)))

    def test_disconnected_raises_on_both_backends(self) -> None:
        H = SparseHypergraph(n_nodes=4, hyperedges=[frozenset({0, 1}), frozenset({2, 3})])
        from isalhg.errors import DisconnectedHypergraphError

        for backend in ("python", "cpp"):
            with pytest.raises(DisconnectedHypergraphError):
                canonical_string(
                    H, k=2, algorithm="canonical_rank", backend=backend, ranks=list(range(4))
                )


class TestEntryPointsDefaultToCpp:
    """``canonical_string_rank`` / ``canonical_fingerprint_rank`` route to C++."""

    def test_default_matches_explicit_cpp(self, fano_plane: SparseHypergraph) -> None:
        default = canonical_string_rank(fano_plane, k=3)
        explicit = canonical_string_rank(fano_plane, k=3, backend="cpp")
        assert default == explicit

    def test_default_matches_python_backend(self, fano_plane: SparseHypergraph) -> None:
        assert canonical_string_rank(fano_plane, k=3) == canonical_string_rank(
            fano_plane, k=3, backend="python"
        )

    def test_fingerprint_default_matches_python(self, sts_9: SparseHypergraph) -> None:
        assert canonical_fingerprint_rank(sts_9, k=3) == canonical_fingerprint_rank(
            sts_9, k=3, backend="python"
        )

    def test_wstar_rank_arm_runs_on_arity_6(self) -> None:
        """The harness arm reads through the same entry point, so it inherits C++.

        Arity 6 is the point: it is the ``ndc_classes`` median, and the Python
        engine is refused there (``PYTHON_ENGINE_MAX_K = 4``). Before the port
        this call raised; now it returns the word.
        """
        from isalhg.metric_space.registry import get_distance

        rng = random.Random(7)
        H = _dense_arity_6(rng)
        assert required_k(H) == 6
        arm = get_distance("wstar_rank")
        symbols = arm.fingerprint(H)
        assert symbols
        assert arm.pairwise(H, H) == 0.0

    def test_wstar_rank_arm_matches_the_entry_point(self, fano_plane: SparseHypergraph) -> None:
        """The arm's symbol sequence is the entry point's word, token for token.

        Fano declares one vertex label, so the arm does not seed-prefix and the
        two sequences must coincide exactly.
        """
        from isalhg.core.instructions import parse
        from isalhg.metric_space.registry import get_distance

        arm = get_distance("wstar_rank")
        _, word = canonical_fingerprint_rank(fano_plane, k=3)
        assert list(arm.fingerprint(fano_plane)) == list(parse(word))


# ---------------------------------------------------------------------------
# 3. The C++ engine reaches where the Python one cannot
# ---------------------------------------------------------------------------


class TestArity6IsCppOnly:
    """Arity 6 -- the ``ndc_classes`` median, and beyond the Python guard.

    Cheap: these instances have overlapping facts, so the walk emits at
    displacement cost 0--1 the way the real corpus members do.
    """

    def test_python_guard_refuses_this_family(self) -> None:
        """State the premise rather than assume it."""
        rng = random.Random(11)
        for _ in range(20):
            assert required_k(_dense_arity_6(rng)) > 4

    def test_encodes_200_instances(self) -> None:
        rng = random.Random(31337)
        for i in range(200):
            H = _dense_arity_6(rng)
            assert canonical_string_rank(H), f"instance {i} produced an empty string"

    def test_invariant_under_20_relabellings(self) -> None:
        rng = random.Random(555)
        for i in range(40):
            H = _dense_arity_6(rng)
            k = required_k(H)
            expected = canonical_fingerprint_rank(H, k=k)
            for _ in range(20):
                order = list(range(H.n_nodes))
                rng.shuffle(order)
                assert canonical_fingerprint_rank(permute(H, order), k=k) == expected, (
                    f"instance {i} not relabelling-invariant"
                )

    def test_agrees_with_pynauty_on_150_pairs(self) -> None:
        rng = random.Random(606)
        backend = PynautyLeviBackend()
        iso_pairs = 0
        for i in range(150):
            left = _dense_arity_6(rng)
            if rng.random() < 0.5:
                order = list(range(left.n_nodes))
                rng.shuffle(order)
                right = permute(left, order)
                iso_pairs += 1
            else:
                right = _dense_arity_6(rng)
            k = max(required_k(left), required_k(right))
            same = canonical_fingerprint_rank(left, k=k) == canonical_fingerprint_rank(right, k=k)
            assert same == backend.are_isomorphic(left, right), f"pair {i} disagrees with pynauty"
        assert iso_pairs > 50


@pytest.mark.slow
class TestAdversarialHighArityIsCppOnly:
    """Arity up to 8 with far-apart facts -- the corner where the frame pays.

    Marked ``slow``: the C++ cost-class enumeration is combinatorial in
    ``k_disp``, so one instance of this family costs ~1.6 s against ~0.05 ms
    for a real ndc_classes member. That is a property of the displacement
    search (it holds for ``w*_c`` too, more so), not of the rank key. Kept
    small and separate so it documents the corner without dominating the run.
    """

    def test_encodes_20_instances(self) -> None:
        rng = random.Random(31337)
        for i in range(20):
            H = _random_high_arity(rng)
            assert canonical_string_rank(H), f"instance {i} produced an empty string"

    def test_invariant_under_relabelling(self) -> None:
        rng = random.Random(555)
        for i in range(8):
            H = _random_high_arity(rng)
            k = required_k(H)
            expected = canonical_fingerprint_rank(H, k=k)
            for _ in range(3):
                order = list(range(H.n_nodes))
                rng.shuffle(order)
                assert canonical_fingerprint_rank(permute(H, order), k=k) == expected, (
                    f"instance {i} not relabelling-invariant"
                )

    def test_agrees_with_pynauty_on_20_pairs(self) -> None:
        """Fingerprint equality is isomorphism, on inputs the Python engine cannot reach."""
        rng = random.Random(8080)
        backend = PynautyLeviBackend()
        iso_pairs = 0
        for i in range(20):
            left = _random_high_arity(rng)
            if rng.random() < 0.5:
                order = list(range(left.n_nodes))
                rng.shuffle(order)
                right = permute(left, order)
                iso_pairs += 1
            else:
                right = _random_high_arity(rng)
            k = max(required_k(left), required_k(right))
            same = canonical_fingerprint_rank(left, k=k) == canonical_fingerprint_rank(right, k=k)
            assert same == backend.are_isomorphic(left, right), f"pair {i} disagrees with pynauty"
        assert iso_pairs > 5
