"""The stabiliser-orbit oracle inside the C++ tie-complete search.

The Python engine has had the orbit hook since wave 1, but it is infeasible
above arity 4, so the article's symmetric-input evidence has to come from the
C++ engine. What the port must satisfy is a *value* claim, not a speed one:
orbit pruning is licensed by Proposition 7.3, which says the sub-searches under
two candidates in the same stabiliser orbit return equal completions -- so the
pruned search returns the frozen ``w*_c`` bit for bit. Any divergence from the
unpruned C++ string, or from the Python orbit engine, is a bug in the port, not
a new canonical form (D-TA2).

Three obligations are checked here:

1. **The frozen pins.** The same ``(length, sha256)`` values
   ``tests/unit/core/test_wstar_c_frozen.py`` pins for the unpruned search,
   re-asserted through the C++ orbit path. The doily is pinned here too: the
   unpruned engine takes ~0.5 s on it against ~0.008 s pruned, so it is the
   cheapest fixture where the two searches are visibly different programs.
2. **The differential.** Random connected labelled hypergraphs and random
   stars, C++ orbit against Python orbit and against the unpruned C++ search.
   The stars are the point: ``q`` interchangeable leaves are explored ``q!``
   times by the unpruned search and once by the pruned one, so they are where a
   mis-plumbed callback would first change the answer.
3. **The branch collapse.** The counters that make the pruning measurable,
   read through ``canonical_string_stats``.
"""

from __future__ import annotations

import hashlib
import random

import pytest

from isalhg.core.canonical import canonical_string
from isalhg.core.orbit_oracle import TrivialOrbitOracle
from isalhg.core.sparse_hypergraph import SparseHypergraph

pytestmark = pytest.mark.unit

_core = pytest.importorskip("isalhg.core._core", reason="C++ extension not built")
pytest.importorskip("pynauty", reason="pynauty is required by PynautyOrbitOracle")

from isalhg.iso_backends.orbit_oracle import (  # noqa: E402
    PynautyOrbitOracle,
    canonical_fingerprint_orbit,
    canonical_string_orbit,
)

#: ``AlgorithmVariant`` ids at the FFI boundary.
_VARIANT_CANONICAL = 7
_VARIANT_ORBIT = 9


def _pin(w: str) -> tuple[int, str]:
    return len(w), hashlib.sha256(w.encode()).hexdigest()


def _orbit_cpp(H: SparseHypergraph, k: int = 3) -> str:
    return canonical_string(
        H, k=k, algorithm="canonical_orbit", backend="cpp", orbit_oracle=PynautyOrbitOracle()
    )


def _orbit_python(H: SparseHypergraph, k: int = 3) -> str:
    return canonical_string(
        H, k=k, algorithm="canonical_orbit", backend="python", orbit_oracle=PynautyOrbitOracle()
    )


def _unpruned_cpp(H: SparseHypergraph, k: int = 3) -> str:
    return canonical_string(H, k=k, algorithm="canonical", backend="cpp")


# ---------------------------------------------------------------------------
# Corpora
# ---------------------------------------------------------------------------


def _star(q: int) -> SparseHypergraph:
    """A hub joined to ``q`` leaves by ``q`` 2-edges.

    The leaves are pairwise interchangeable, so ``Aut`` is the full symmetric
    group ``S_q`` on them: the unpruned search explores ``q!`` orderings of the
    same object, the pruned one explores a single representative. This is the
    branch-collapse witness of the pruning proposition.
    """
    return SparseHypergraph(n_nodes=q + 1, hyperedges=[frozenset({0, i}) for i in range(1, q + 1)])


def _random_connected(
    rng: random.Random,
    *,
    max_nodes: int = 8,
    max_arity: int = 4,
    n_vertex_labels: int = 3,
    n_edge_labels: int = 3,
) -> SparseHypergraph:
    """A random connected labelled hypergraph within the Python engine's budget.

    ``n <= 8`` and ``arity <= 4`` keep the Python reference inside the
    ``(2n-1)^k`` displacement bound documented in
    ``experiments/tkde/budget.py``; the differential is worthless if the
    reference cannot run.

    Connectivity is built in rather than rejected for: each new vertex joins an
    edge that already contains a placed one.
    """
    n = rng.randint(2, max_nodes)
    placed = [0]
    edges: set[frozenset[int]] = set()
    for v in range(1, n):
        arity = rng.randint(2, min(max_arity, len(placed) + 1))
        edges.add(frozenset({v, *rng.sample(placed, arity - 1)}))
        placed.append(v)
    for _ in range(rng.randint(0, n)):
        arity = rng.randint(2, min(max_arity, n))
        edges.add(frozenset(rng.sample(range(n), arity)))
    ordered = sorted(edges, key=sorted)
    return SparseHypergraph(
        n_nodes=n,
        hyperedges=ordered,
        n_vertex_labels=n_vertex_labels,
        n_edge_labels=n_edge_labels,
        vertex_labels=[rng.randrange(n_vertex_labels) for _ in range(n)],
        edge_labels=[rng.randrange(n_edge_labels) for _ in ordered],
    )


# ---------------------------------------------------------------------------
# 1. The frozen pins, through the C++ orbit path
# ---------------------------------------------------------------------------

#: Copied from ``test_wstar_c_frozen.py`` (computed 2026-07-09 with the
#: unpruned search) so this file asserts the pins independently: if the two
#: ever disagree, the port changed the canonical form, which is a definitional
#: event, not a test to update (D-TA2). The doily row is new -- measured here
#: 2026-09-07 and cross-checked against the unpruned C++ search in the same
#: run.
_PINS: dict[str, tuple[int, str]] = {
    "fano_plane": (121, "9695315fb1566ec737ee3b22ee65e6423690bd1a82f8c7e010b2a312214ea79b"),
    "sts_9": (227, "a6282f853d79d251b58a7b8962f9e54496a225483a8785adffbcb511312047cc"),
    "gq_2_2_doily": (276, "59621b4f890ae41d6a4aadb707510cdb5597b03d3351ee49a4448b1dec2d04bb"),
}

_PIN_C13_013 = (256, "77d9fa1e4e99d500c3bed2debf32d6da773b1721c7e3ea26f5a734ac0ec89bec")
_PIN_CE_N4 = (54, "ab9393ffb4dc117f86481e09b44b54e2fbfc01be166aa2f3e2fdfbead0656ba3")
_PINS_STS13_TRUE = {
    1: (472, "4e5e682d86de95fe7526bce05c74519856270e3eb8e907e99437b3efb53f0cc6"),
    2: (472, "bd872631a5a5a17256c411159c1a10f40d5d8ef63ef0893ab2fcbbd7a5467eca"),
}


def _c13_013() -> SparseHypergraph:
    return SparseHypergraph(
        n_nodes=13,
        hyperedges=[frozenset({i, (i + 1) % 13, (i + 3) % 13}) for i in range(13)],
    )


def _n4_counterexample() -> SparseHypergraph:
    return SparseHypergraph(
        n_nodes=4,
        hyperedges=[
            frozenset({1, 3}),
            frozenset({0, 1, 3}),
            frozenset({0, 2, 3}),
            frozenset({1, 2}),
        ],
    )


class TestFrozenPinsThroughTheCppOrbitPath:
    """``w*_c`` is unchanged by the pruning, on the objects that define it."""

    @pytest.mark.parametrize("fixture_name", sorted(_PINS))
    def test_design_fixtures(self, fixture_name: str, request: pytest.FixtureRequest) -> None:
        H: SparseHypergraph = request.getfixturevalue(fixture_name)
        assert _pin(_orbit_cpp(H)) == _PINS[fixture_name]

    def test_cyclic_triple_orbit_13(self) -> None:
        assert _pin(_orbit_cpp(_c13_013())) == _PIN_C13_013

    def test_n4_counterexample(self) -> None:
        assert _pin(_orbit_cpp(_n4_counterexample())) == _PIN_CE_N4

    @pytest.mark.slow
    @pytest.mark.parametrize("catalog_index", sorted(_PINS_STS13_TRUE))
    def test_true_sts13(self, catalog_index: int) -> None:
        from isalhg.datasets.synthetic.sts_catalog import steiner_triple_system

        H = steiner_triple_system(13, catalog_index - 1)
        assert _pin(_orbit_cpp(H)) == _PINS_STS13_TRUE[catalog_index]


# ---------------------------------------------------------------------------
# 2. Differentials
# ---------------------------------------------------------------------------


class TestDifferentialAgainstTheReferences:
    """Bit-exactness against the Python orbit engine and the unpruned search."""

    @pytest.mark.parametrize("seed", [0, 1, 2, 3, 4])
    def test_random_connected_labelled(self, seed: int) -> None:
        rng = random.Random(seed)
        oracle = PynautyOrbitOracle()
        for _ in range(20):
            H = _random_connected(rng)
            k = max(2, max((len(m) for _, m, _ in H.iter_edges()), default=2))
            want = _unpruned_cpp(H, k)
            assert _orbit_cpp(H, k) == want
            assert _orbit_python(H, k) == want
            # The same oracle instance across many hypergraphs exercises the
            # id()-keyed cache the adapter forwards into.
            assert (
                canonical_string(
                    H, k=k, algorithm="canonical_orbit", backend="cpp", orbit_oracle=oracle
                )
                == want
            )

    @pytest.mark.parametrize("q", [2, 3, 4, 5, 6, 7, 8])
    def test_stars(self, q: int) -> None:
        H = _star(q)
        want = _unpruned_cpp(H, k=2)
        assert _orbit_cpp(H, k=2) == want
        assert _orbit_python(H, k=2) == want

    def test_trivial_oracle_is_value_neutral(self, fano_plane: SparseHypergraph) -> None:
        """The identity oracle must reproduce the unpruned string exactly.

        It prunes nothing, so any difference is plumbing -- the branch set the
        C++ side hands to the callback, or the way it reads the answer back --
        rather than group theory.
        """
        assert canonical_string(
            fano_plane,
            k=3,
            algorithm="canonical_orbit",
            backend="cpp",
            orbit_oracle=TrivialOrbitOracle(),
        ) == _unpruned_cpp(fano_plane)

    def test_entry_points_default_to_cpp(self, sts_9: SparseHypergraph) -> None:
        want = _unpruned_cpp(sts_9)
        assert canonical_string_orbit(sts_9, k=3) == want
        assert canonical_string_orbit(sts_9, k=3, backend="cpp") == want
        assert canonical_string_orbit(sts_9, k=3, backend="python") == want

    def test_fingerprint_entry_point(self) -> None:
        """``F(H) = (seed label, w*_c)`` survives the port on a labelled input.

        The seed label is the one label ``w*_c`` never emits, so a labelled
        fixture is the only place a mis-reduced seed set would show up in the
        fingerprint but not in the string.
        """
        from isalhg.core.canonical import canonical_fingerprint

        H = _random_connected(random.Random(11))
        k = max(2, max(len(m) for _, m, _ in H.iter_edges()))
        want = canonical_fingerprint(H, k=k, algorithm="canonical")
        assert canonical_fingerprint_orbit(H, k=k) == want
        assert canonical_fingerprint_orbit(H, k=k, backend="python") == want


# ---------------------------------------------------------------------------
# 3. The branch collapse
# ---------------------------------------------------------------------------


class TestBranchCollapse:
    """The pruning is measurable, and it is what the proposition predicts."""

    @pytest.mark.parametrize("q", [5, 6, 7])
    def test_star_frames_collapse(self, q: int) -> None:
        H = _star(q)
        off_word, off = _core.canonical_string_stats(H, 2, 3, _VARIANT_CANONICAL, 0, None, None)
        on_word, on = _core.canonical_string_stats(
            H, 2, 3, _VARIANT_ORBIT, 0, None, PynautyOrbitOracle()
        )
        assert on_word == off_word
        assert on["frames"] < off["frames"]
        assert on["oracle_calls"] > 0
        # The unpruned search consults no oracle, and the pruned one reduces
        # the seed set exactly once.
        assert off["oracle_calls"] == 0
        assert off["seed_oracle_calls"] == 0
        assert on["seed_oracle_calls"] == 1

    def test_star_collapse_grows_with_symmetry(self) -> None:
        """The unpruned/pruned frame ratio increases with ``q``.

        ``Aut`` of the ``q``-star contains ``S_q``, so the duplicate work the
        oracle removes grows super-linearly while the pruned search stays flat.
        A port that consulted the oracle at only some ties would still be
        bit-exact but would show a flat ratio, which is why this is asserted
        separately from the equality tests.
        """
        ratios = []
        for q in (5, 8):
            H = _star(q)
            _, off = _core.canonical_string_stats(H, 2, 3, _VARIANT_CANONICAL, 0, None, None)
            _, on = _core.canonical_string_stats(
                H, 2, 3, _VARIANT_ORBIT, 0, None, PynautyOrbitOracle()
            )
            ratios.append(off["frames"] / on["frames"])
        assert ratios[1] > ratios[0]

    def test_counters_do_not_change_the_string(self, gq_2_2_doily: SparseHypergraph) -> None:
        word, stats = _core.canonical_string_stats(
            gq_2_2_doily, 3, 3, _VARIANT_ORBIT, 0, None, PynautyOrbitOracle()
        )
        assert word == _orbit_cpp(gq_2_2_doily)
        assert stats["frames"] > 0
        assert stats["seeds_run"] >= 1


# ---------------------------------------------------------------------------
# 4. Contracts
# ---------------------------------------------------------------------------


class TestContracts:
    """The variant never falls back silently, on either side of the boundary."""

    def test_cpp_orbit_without_an_oracle_raises(self, fano_plane: SparseHypergraph) -> None:
        with pytest.raises(ValueError, match="requires an orbit_oracle"):
            canonical_string(fano_plane, k=3, algorithm="canonical_orbit", backend="cpp")

    def test_native_orbit_variant_without_an_oracle_raises(
        self, fano_plane: SparseHypergraph
    ) -> None:
        from isalhg.errors import IsalHGError

        with pytest.raises(IsalHGError, match="requires an orbit oracle"):
            _core.canonical_string(fano_plane, 3, 3, _VARIANT_ORBIT, 0, None, None)

    def test_native_oracle_with_another_variant_raises(self, fano_plane: SparseHypergraph) -> None:
        from isalhg.errors import IsalHGError

        with pytest.raises(IsalHGError, match="only honoured by"):
            _core.canonical_string(
                fano_plane, 3, 3, _VARIANT_CANONICAL, 0, None, PynautyOrbitOracle()
            )

    def test_disconnected_input_raises(self) -> None:
        from isalhg.errors import DisconnectedHypergraphError

        H = SparseHypergraph(n_nodes=4, hyperedges=[frozenset({0, 1}), frozenset({2, 3})])
        with pytest.raises(DisconnectedHypergraphError):
            _orbit_cpp(H, k=2)

    def test_oracle_exception_surfaces(self, fano_plane: SparseHypergraph) -> None:
        """A Python exception inside a callback reaches the caller as an error.

        It is re-raised as ``IsalHGError`` rather than the original type: the
        adapter converts it to text while the GIL is still held so no PyObject
        refcount is touched on the GIL-free side of the unwind.
        """
        from isalhg.errors import IsalHGError

        class Exploding(TrivialOrbitOracle):
            def edge_representatives(self, H, placed, tied_edges):  # type: ignore[no-untyped-def]
                raise RuntimeError("boom")

        with pytest.raises(IsalHGError, match="boom"):
            canonical_string(
                fano_plane,
                k=3,
                algorithm="canonical_orbit",
                backend="cpp",
                orbit_oracle=Exploding(),
            )
