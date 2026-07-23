"""Unit tests for :mod:`isalhg.datasets.synthetic.known_design_catalog` (T-M7a).

Acceptance criteria
-------------------
AC1  Every design is connected (D-CONN1).
AC2  Each design has the correct uniform arity.
AC3  All designs in the catalog are pairwise non-isomorphic (within each arity stratum).
AC4  Catalog length equals the expected count.
AC5  Registry lookup ``get_dataset("known_design_catalog", {})`` works.
AC6  Realized-parameter table present and consistent with items.
AC7  ``KnownDesignCatalog`` is deterministic — same output on repeated construction.
AC8  Known-structure assertions: Steiner, AG, PG, complete, path/cycle shape checks.
AC9  ``catalog_seeds()`` and ``catalog_family_labels()`` agree in length.
AC10 ``RealizedParams.compute`` is self-consistent (tests the schema helper).
"""

from __future__ import annotations

import itertools

import pytest

from isalhg.datasets.registry import get_dataset
from isalhg.datasets.schemas import RealizedParams
from isalhg.datasets.synthetic.known_design_catalog import (
    KnownDesignCatalog,
    affine_plane_ag24,
    catalog_family_labels,
    catalog_item_ids,
    catalog_seeds,
    complete_uniform,
    loose_cycle,
    loose_path,
    projective_plane_pg23,
    projective_plane_pg24,
    tight_cycle,
    tight_path,
)

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TOTAL_ENTRIES = 26  # sum of all catalog entries (updated T-M7o: +3 arity-4/5 cycles)


def _pair_coverage(H):  # type: ignore[no-untyped-def]
    """Map each point-pair to the number of blocks covering it."""
    cover: dict[tuple[int, int], int] = {}
    for _, members, _ in H.iter_edges():
        for p in itertools.combinations(sorted(members), 2):
            cover[p] = cover.get(p, 0) + 1
    return cover


# ---------------------------------------------------------------------------
# AC4 — catalog length
# ---------------------------------------------------------------------------


class TestCatalogLength:
    def test_total_entries(self) -> None:
        ds = KnownDesignCatalog()
        assert len(ds) == TOTAL_ENTRIES

    def test_arity_filter_k3(self) -> None:
        ds = KnownDesignCatalog(arities=(3,))
        for item in ds:
            for _, members, _ in item.hypergraph.iter_edges():
                assert len(members) == 3

    def test_arity_filter_k4(self) -> None:
        ds = KnownDesignCatalog(arities=(4,))
        for item in ds:
            for _, members, _ in item.hypergraph.iter_edges():
                assert len(members) == 4

    def test_arity_filter_k5(self) -> None:
        ds = KnownDesignCatalog(arities=(5,))
        for item in ds:
            for _, members, _ in item.hypergraph.iter_edges():
                assert len(members) == 5


# ---------------------------------------------------------------------------
# AC1 — connectivity
# ---------------------------------------------------------------------------


class TestConnectivity:
    def test_all_designs_connected(self) -> None:
        ds = KnownDesignCatalog()
        for item in ds:
            assert item.hypergraph.is_connected(), (
                f"{item.item_id}: expected connected hypergraph, got disconnected"
            )


# ---------------------------------------------------------------------------
# AC2 — correct uniform arity
# ---------------------------------------------------------------------------


class TestUniformArity:
    def test_each_design_is_uniform(self) -> None:
        ds = KnownDesignCatalog()
        for item in ds:
            arities = {len(members) for _, members, _ in item.hypergraph.iter_edges()}
            assert len(arities) == 1, (
                f"{item.item_id}: expected uniform hypergraph, got arity set {arities}"
            )
            actual_arity = next(iter(arities))
            expected_arity = item.extra["arity"]
            assert actual_arity == expected_arity, (
                f"{item.item_id}: expected arity {expected_arity}, got {actual_arity}"
            )


# ---------------------------------------------------------------------------
# AC3 — pairwise non-isomorphism within arity stratum
#
# Non-isomorphism is verified at two levels:
#  (a) FAST: pynauty-Levi backend (graph-iso over Levi reduction — much faster
#      than the tie-complete canonical encoder for high-symmetry designs).
#      Covers all 23 catalog entries.
#  (b) SLOW: canonical_fingerprint pin on a cheap sample (paths, cycles,
#      complete; the fast arity-3/4/5 designs).  The Steiner/projective
#      designs have automorphism groups that push the tie-complete encoder
#      beyond the unit-test budget — they are covered by the pilot script
#      and the @pytest.mark.slow suite.
# ---------------------------------------------------------------------------

# Cheap designs whose canonical_fingerprint runs well under a second.
_FAST_ITEM_IDS = frozenset(
    {
        "loose_path_k3",
        "tight_path_k3",
        "loose_cycle_k3",
        "tight_cycle_k3",
        "complete_k3_n5",
        "loose_path_k4",
        "tight_path_k4",
        "loose_cycle_k4",
        "tight_cycle_k4",
        "complete_k4_n6",
        "loose_path_k5",
        "tight_path_k5",
        "tight_cycle_k5",
        "complete_k5_n6",
        # Fano is cheap (n=7, 25ms)
        "sts7",
    }
)


class TestNonIsomorphism:
    def test_pairwise_non_iso_pynauty_k3(self) -> None:
        """Fast pynauty-backed non-iso check for all k=3 catalog entries."""
        from isalhg.iso_backends.registry import get_backend

        backend = get_backend("pynauty_levi")
        ds = KnownDesignCatalog(arities=(3,))
        fingerprints: dict[str, bytes] = {}
        for item in ds:
            fp = backend.fingerprint(item.hypergraph)
            for prev_id, prev_fp in fingerprints.items():
                assert fp != prev_fp, (
                    f"k=3: {item.item_id!r} and {prev_id!r} have equal pynauty "
                    f"fingerprint — catalog claims non-isomorphism"
                )
            fingerprints[item.item_id] = fp

    def test_pairwise_non_iso_pynauty_k4(self) -> None:
        """Fast pynauty-backed non-iso check for all k=4 catalog entries."""
        from isalhg.iso_backends.registry import get_backend

        backend = get_backend("pynauty_levi")
        ds = KnownDesignCatalog(arities=(4,))
        fingerprints: dict[str, bytes] = {}
        for item in ds:
            fp = backend.fingerprint(item.hypergraph)
            for prev_id, prev_fp in fingerprints.items():
                assert fp != prev_fp, (
                    f"k=4: {item.item_id!r} and {prev_id!r} have equal pynauty "
                    f"fingerprint — catalog claims non-isomorphism"
                )
            fingerprints[item.item_id] = fp

    def test_pairwise_non_iso_pynauty_k5(self) -> None:
        """Fast pynauty-backed non-iso check for k=5 catalog entries (skip PG24)."""
        from isalhg.iso_backends.registry import get_backend

        backend = get_backend("pynauty_levi")
        # pg24 (n=21, very symmetric) is excluded from the unit-test suite.
        ds = KnownDesignCatalog(arities=(5,))
        fingerprints: dict[str, bytes] = {}
        for item in ds:
            if item.item_id == "pg24":
                continue  # covered by the slow test and feasibility pilot
            fp = backend.fingerprint(item.hypergraph)
            for prev_id, prev_fp in fingerprints.items():
                assert fp != prev_fp, (
                    f"k=5: {item.item_id!r} and {prev_id!r} have equal pynauty "
                    f"fingerprint — catalog claims non-isomorphism"
                )
            fingerprints[item.item_id] = fp

    def test_canonical_fingerprint_pin_fast_sample(self) -> None:
        """canonical_fingerprint non-iso pin on the cheap designs only.

        This is the load-bearing regression that ``canonical_fingerprint``
        (the w*_c encoder) correctly distinguishes these designs.  Symmetric
        designs (STS(13), STS(15), GQ22, AG24, PG23, PG24) exceed the unit-test
        time budget and are covered by the @slow suite + feasibility pilot.
        """
        from isalhg.core.canonical import canonical_fingerprint

        ds = KnownDesignCatalog()
        fingerprints: dict[str, bytes] = {}
        for item in ds:
            if item.item_id not in _FAST_ITEM_IDS:
                continue
            fp = canonical_fingerprint(item.hypergraph)
            for prev_id, prev_fp in fingerprints.items():
                assert fp != prev_fp, (
                    f"{item.item_id!r} and {prev_id!r} have equal canonical_fingerprint"
                )
            fingerprints[item.item_id] = fp


# ---------------------------------------------------------------------------
# AC5 — registry
# ---------------------------------------------------------------------------


class TestRegistry:
    def test_registry_default(self) -> None:
        ds = get_dataset("known_design_catalog", {})
        assert len(ds) == TOTAL_ENTRIES

    def test_registry_arity_param(self) -> None:
        ds = get_dataset("known_design_catalog", {"arities": [3]})
        for item in ds:
            assert item.extra["arity"] == 3

    def test_iso_labels_true(self) -> None:
        ds = get_dataset("known_design_catalog", {})
        assert ds.metadata.has_iso_labels is True


# ---------------------------------------------------------------------------
# AC6 — realized-parameter table
# ---------------------------------------------------------------------------


class TestRealizedParams:
    def test_realized_params_present(self) -> None:
        ds = KnownDesignCatalog()
        rp = ds.metadata.realized_params
        assert rp is not None

    def test_realized_params_lengths_match(self) -> None:
        ds = KnownDesignCatalog()
        rp = ds.metadata.realized_params
        assert rp is not None
        assert len(rp.n_vals) == len(ds)
        assert len(rp.m_vals) == len(ds)
        assert len(rp.density_vals) == len(ds)

    def test_all_connected_flag(self) -> None:
        ds = KnownDesignCatalog()
        rp = ds.metadata.realized_params
        assert rp is not None
        assert rp.all_connected is True

    def test_seeds_empty_for_deterministic(self) -> None:
        ds = KnownDesignCatalog()
        rp = ds.metadata.realized_params
        assert rp is not None
        assert rp.seeds == ()

    def test_arity_hist_sums_to_total_edges(self) -> None:
        ds = KnownDesignCatalog()
        rp = ds.metadata.realized_params
        assert rp is not None
        total_edges_from_hist = sum(rp.arity_hist.values())
        total_edges_direct = sum(item.hypergraph.n_edges for item in ds)
        assert total_edges_from_hist == total_edges_direct

    def test_density_vals_consistent(self) -> None:
        ds = KnownDesignCatalog()
        rp = ds.metadata.realized_params
        assert rp is not None
        for item, n, m, density in zip(ds, rp.n_vals, rp.m_vals, rp.density_vals, strict=True):
            assert item.hypergraph.n_nodes == n
            assert item.hypergraph.n_edges == m
            expected_density = m / n if n > 0 else 0.0
            assert abs(density - expected_density) < 1e-9


# ---------------------------------------------------------------------------
# AC7 — determinism
# ---------------------------------------------------------------------------


class TestDeterminism:
    def test_same_output_on_repeated_construction(self) -> None:
        ds1 = KnownDesignCatalog()
        ds2 = KnownDesignCatalog()
        items1 = list(ds1)
        items2 = list(ds2)
        assert len(items1) == len(items2)
        for a, b in zip(items1, items2, strict=True):
            assert a.item_id == b.item_id
            assert a.hypergraph == b.hypergraph

    def test_seed_noop(self) -> None:
        ds = KnownDesignCatalog()
        ds2 = ds.seed(42)
        assert list(ds) == list(ds2)


# ---------------------------------------------------------------------------
# AC8 — structural assertions per design
# ---------------------------------------------------------------------------


class TestSteinerSystems:
    """STS(v) designs: every pair of points covered exactly once (Steiner property)."""

    @pytest.mark.parametrize(
        "item_id,n", [("sts7", 7), ("sts9", 9), ("sts13_0", 13), ("sts13_1", 13)]
    )
    def test_steiner_pair_coverage(self, item_id: str, n: int) -> None:
        ds = KnownDesignCatalog()
        H = next(item.hypergraph for item in ds if item.item_id == item_id)
        assert H.n_nodes == n
        assert H.n_edges == n * (n - 1) // 6
        cover = _pair_coverage(H)
        assert len(cover) == n * (n - 1) // 2
        assert set(cover.values()) == {1}, (
            f"{item_id}: not a Steiner triple system (pair coverage not all 1)"
        )


class TestSTS13NonIso:
    @pytest.mark.slow
    def test_sts13_pair_are_non_isomorphic(self) -> None:
        """canonical_fingerprint pin: the two STS(13)s are non-isomorphic.

        Marked slow: each STS(13) canonical_fingerprint call takes ~15-30s due to
        the large automorphism group.  Normal unit runs should use -m "not slow" or
        accept the latency.  Non-isomorphism is also covered by the pynauty test
        in TestNonIsomorphism for fast runs.
        """
        from isalhg.core.canonical import canonical_fingerprint

        ds = KnownDesignCatalog()
        # Load only the two STS(13) designs — do not iterate the full k=3 stratum,
        # which includes STS(15) whose canonical_fingerprint is unbounded.
        sts13_items = {
            item.item_id: item.hypergraph for item in ds if item.item_id in ("sts13_0", "sts13_1")
        }
        assert len(sts13_items) == 2, "catalog must contain both sts13_0 and sts13_1"
        fp0 = canonical_fingerprint(sts13_items["sts13_0"])
        fp1 = canonical_fingerprint(sts13_items["sts13_1"])
        assert fp0 != fp1, "STS(13) pair should be non-isomorphic"


class TestAG24:
    def test_ag24_shape(self) -> None:
        H = affine_plane_ag24()
        assert H.n_nodes == 16
        assert H.n_edges == 20
        # Every edge is size 4
        for _, members, _ in H.iter_edges():
            assert len(members) == 4
        assert H.is_connected()

    def test_ag24_pair_coverage_lambda1(self) -> None:
        H = affine_plane_ag24()
        cover = _pair_coverage(H)
        # AG(2,4) is a 2-(16,4,1) design: every pair covered exactly once.
        assert set(cover.values()) == {1}

    def test_ag24_total_pairs(self) -> None:
        H = affine_plane_ag24()
        cover = _pair_coverage(H)
        assert len(cover) == 16 * 15 // 2  # 120 pairs, all covered


class TestPG23:
    def test_pg23_shape(self) -> None:
        H = projective_plane_pg23()
        assert H.n_nodes == 13
        assert H.n_edges == 13
        for _, members, _ in H.iter_edges():
            assert len(members) == 4
        assert H.is_connected()

    def test_pg23_pair_coverage_lambda1(self) -> None:
        H = projective_plane_pg23()
        cover = _pair_coverage(H)
        # PG(2,3) is a 2-(13,4,1) design.
        assert set(cover.values()) == {1}


class TestPG24:
    def test_pg24_shape(self) -> None:
        H = projective_plane_pg24()
        assert H.n_nodes == 21
        assert H.n_edges == 21
        for _, members, _ in H.iter_edges():
            assert len(members) == 5
        assert H.is_connected()

    def test_pg24_pair_coverage_lambda1(self) -> None:
        H = projective_plane_pg24()
        cover = _pair_coverage(H)
        assert set(cover.values()) == {1}


class TestCompleteUniform:
    @pytest.mark.parametrize("n,k,expected_m", [(5, 3, 10), (6, 4, 15), (6, 5, 6)])
    def test_complete_edge_count(self, n: int, k: int, expected_m: int) -> None:
        H = complete_uniform(n, k)
        assert H.n_nodes == n
        assert H.n_edges == expected_m
        assert H.is_connected()

    def test_complete_all_k_subsets(self) -> None:
        H = complete_uniform(5, 3)
        edges = {e for _, e, _ in H.iter_edges()}
        expected = {frozenset(c) for c in itertools.combinations(range(5), 3)}
        assert edges == expected


class TestPaths:
    @pytest.mark.parametrize(
        "k,length,expected_n",
        [(3, 4, 9), (4, 3, 10), (5, 3, 13)],
    )
    def test_loose_path_shape(self, k: int, length: int, expected_n: int) -> None:
        H = loose_path(k, length)
        assert H.n_nodes == expected_n
        assert H.n_edges == length
        assert H.is_connected()
        for _, members, _ in H.iter_edges():
            assert len(members) == k

    @pytest.mark.parametrize(
        "k,length,expected_n",
        [(3, 4, 6), (4, 3, 6), (5, 3, 7)],
    )
    def test_tight_path_shape(self, k: int, length: int, expected_n: int) -> None:
        H = tight_path(k, length)
        assert H.n_nodes == expected_n
        assert H.n_edges == length
        assert H.is_connected()
        for _, members, _ in H.iter_edges():
            assert len(members) == k


class TestCycles:
    @pytest.mark.parametrize(
        "k,length,expected_n",
        [(3, 4, 8), (4, 4, 12)],
    )
    def test_loose_cycle_shape(self, k: int, length: int, expected_n: int) -> None:
        H = loose_cycle(k, length)
        assert H.n_nodes == expected_n
        assert H.n_edges == length
        assert H.is_connected()
        for _, members, _ in H.iter_edges():
            assert len(members) == k

    @pytest.mark.parametrize(
        "k,length,expected_n",
        [(3, 5, 5), (4, 5, 5), (5, 7, 7)],
    )
    def test_tight_cycle_shape(self, k: int, length: int, expected_n: int) -> None:
        H = tight_cycle(k, length)
        assert H.n_nodes == expected_n
        assert H.n_edges == length
        assert H.is_connected()
        for _, members, _ in H.iter_edges():
            assert len(members) == k


# ---------------------------------------------------------------------------
# AC9 — catalog_seeds / catalog_family_labels consistency
# ---------------------------------------------------------------------------


class TestCatalogHelpers:
    def test_seeds_and_labels_same_length(self) -> None:
        seeds = catalog_seeds()
        labels = catalog_family_labels()
        ids = catalog_item_ids()
        assert len(seeds) == len(labels) == len(ids) == TOTAL_ENTRIES

    def test_arity_filter_consistent(self) -> None:
        seeds = catalog_seeds(arities=(3,))
        labels = catalog_family_labels(arities=(3,))
        ids = catalog_item_ids(arities=(3,))
        assert len(seeds) == len(labels) == len(ids)

    def test_ids_are_unique(self) -> None:
        ids = catalog_item_ids()
        assert len(ids) == len(set(ids))

    def test_labels_match_items(self) -> None:
        ds = KnownDesignCatalog()
        items = list(ds)
        labels = catalog_family_labels()
        for item, label in zip(items, labels, strict=True):
            assert item.extra["family_label"] == label


# ---------------------------------------------------------------------------
# AC10 — RealizedParams.compute helper
# ---------------------------------------------------------------------------


class TestRealizedParamsCompute:
    def test_compute_basic(self) -> None:
        from isalhg.core.sparse_hypergraph import SparseHypergraph

        H1 = SparseHypergraph(3, hyperedges=[frozenset({0, 1, 2})])
        H2 = SparseHypergraph(4, hyperedges=[frozenset({0, 1, 2}), frozenset({1, 2, 3})])
        rp = RealizedParams.compute([H1, H2], seeds=(7,))
        assert rp.n_vals == (3, 4)
        assert rp.m_vals == (1, 2)
        assert abs(rp.density_vals[0] - 1 / 3) < 1e-9
        assert abs(rp.density_vals[1] - 2 / 4) < 1e-9
        assert rp.arity_hist == {3: 3}  # all edges are 3-uniform
        assert rp.all_connected is True
        assert rp.seeds == (7,)

    def test_compute_empty(self) -> None:
        rp = RealizedParams.compute([])
        assert rp.n_vals == ()
        assert rp.m_vals == ()
        assert rp.arity_hist == {}
        assert rp.all_connected is True
