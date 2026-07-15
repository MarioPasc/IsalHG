"""Unit tests for :class:`isalhg.metric_space.representations.netlsd`.

NetLSD is a *spectral* invariant: isomorphic hypergraphs yield signatures
that are equal up to floating-point noise, so iso-pair distance assertions
use ``numpy.testing.assert_allclose(atol=1e-6)`` rather than exact equality.
This is documented in the module docstring and is a genuine property
difference from the exact-invariant baselines (``d_I``, nauty-edit).

``netlsd`` is a soft dependency (``pip install netlsd``).  Tests that require
it are guarded with ``pytest.importorskip("netlsd")``.  The
``test_missing_dependency`` test verifies that the
:class:`RepresentationDependencyMissingError` is raised when the library
is simulated-absent via ``unittest.mock``.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import numpy as np
import numpy.testing as npt
import pytest

from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.errors import RepresentationDependencyMissingError

pytestmark = pytest.mark.unit

HIC_ROOT = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/data/HIC/data")


def _path_hypergraph() -> SparseHypergraph:
    """4-node path hypergraph (3 binary edges)."""
    return SparseHypergraph(
        n_nodes=4,
        hyperedges=[frozenset({0, 1}), frozenset({1, 2}), frozenset({2, 3})],
    )


class TestPairwise:
    def test_iso_pair_near_zero(
        self, iso_pair_small: tuple[SparseHypergraph, SparseHypergraph, list[int]]
    ) -> None:
        pytest.importorskip("netlsd")
        from isalhg.metric_space.representations.netlsd import NetLSDDistance

        h1, h2, _ = iso_pair_small
        d = NetLSDDistance().pairwise(h1, h2)
        npt.assert_allclose(d, 0.0, atol=1e-6)

    def test_permuted_fano_near_zero(self, fano_plane: SparseHypergraph) -> None:
        pytest.importorskip("netlsd")
        from isalhg.metric_space.representations.netlsd import NetLSDDistance

        d = NetLSDDistance()
        dist = d.pairwise(fano_plane, permute(fano_plane, [6, 5, 4, 3, 2, 1, 0]))
        npt.assert_allclose(dist, 0.0, atol=1e-6)

    def test_self_distance_near_zero(self, sts_9: SparseHypergraph) -> None:
        pytest.importorskip("netlsd")
        from isalhg.metric_space.representations.netlsd import NetLSDDistance

        d = NetLSDDistance().pairwise(sts_9, sts_9)
        npt.assert_allclose(d, 0.0, atol=1e-6)

    def test_positive_on_distinct_designs(
        self, fano_plane: SparseHypergraph, sts_9: SparseHypergraph
    ) -> None:
        pytest.importorskip("netlsd")
        from isalhg.metric_space.representations.netlsd import NetLSDDistance

        # Fano: 7 nodes / 7 edges (3-uniform).  STS(9): 9 nodes / 12 edges.
        # Distinct spectra => positive L2 distance.
        assert NetLSDDistance().pairwise(fano_plane, sts_9) > 0.0

    def test_name(self) -> None:
        from isalhg.metric_space.representations.netlsd import NetLSDDistance

        assert NetLSDDistance().name == "netlsd_l2"


class TestMatrix:
    def test_matrix_shape_symmetry_and_zero_diagonal(
        self,
        fano_plane: SparseHypergraph,
        sts_9: SparseHypergraph,
        single_edge_hypergraph: SparseHypergraph,
        iso_pair_small: tuple[SparseHypergraph, SparseHypergraph, list[int]],
        non_iso_pair_small: tuple[SparseHypergraph, SparseHypergraph],
    ) -> None:
        pytest.importorskip("netlsd")
        from isalhg.metric_space.representations.netlsd import NetLSDDistance

        i1, i2, _ = iso_pair_small
        h1, h2 = non_iso_pair_small
        corpus = [
            fano_plane,
            permute(fano_plane, [1, 2, 3, 4, 5, 6, 0]),
            sts_9,
            permute(sts_9, [1, 2, 3, 4, 5, 6, 7, 8, 0]),
            i1,
            i2,
            h1,
            h2,
            single_edge_hypergraph,
            _path_hypergraph(),
        ]
        D = NetLSDDistance().matrix(corpus)
        assert D.shape == (10, 10)
        assert np.allclose(D, D.T)
        assert np.allclose(np.diag(D), 0.0)
        assert np.all(np.isfinite(D))
        # Isomorphic pairs must be near zero.
        npt.assert_allclose(D[0, 1], 0.0, atol=1e-6)  # fano vs permuted fano
        npt.assert_allclose(D[2, 3], 0.0, atol=1e-6)  # sts9 vs permuted sts9
        npt.assert_allclose(D[4, 5], 0.0, atol=1e-6)  # small iso pair
        # Distinct designs must be separated.
        assert D[0, 2] > 0.0  # fano vs sts9

    def test_empty_corpus(self) -> None:
        from isalhg.metric_space.representations.netlsd import NetLSDDistance

        pytest.importorskip("netlsd")
        D = NetLSDDistance().matrix([])
        assert D.shape == (0, 0)

    def test_fingerprint_consistency(self, fano_plane: SparseHypergraph) -> None:
        """matrix() and two independent fingerprint() + L2 calls must agree."""
        pytest.importorskip("netlsd")
        from isalhg.metric_space.representations.netlsd import NetLSDDistance

        d = NetLSDDistance()
        sts = SparseHypergraph(n_nodes=3, hyperedges=[frozenset({0, 1}), frozenset({1, 2})])
        D_mat = d.matrix([fano_plane, sts])
        sig_fano = d.fingerprint(fano_plane)
        sig_sts = d.fingerprint(sts)
        d_direct = float(np.linalg.norm(sig_fano - sig_sts))
        npt.assert_allclose(D_mat[0, 1], d_direct, atol=1e-12)


class TestMissingDependency:
    def test_fingerprint_raises_when_netlsd_absent(self, fano_plane: SparseHypergraph) -> None:
        """fingerprint() raises RepresentationDependencyMissingError when netlsd is absent."""
        from isalhg.metric_space.representations.netlsd import NetLSDDistance

        with (
            patch.dict("sys.modules", {"netlsd": None}),
            pytest.raises(RepresentationDependencyMissingError),
        ):
            NetLSDDistance().fingerprint(fano_plane)


class TestRegistration:
    def test_registered_and_retrievable(self) -> None:
        pytest.importorskip("netlsd")
        # Importing the module triggers registration.
        import isalhg.metric_space.representations.netlsd  # noqa: F401
        from isalhg.metric_space import registry

        d = registry.get_distance("netlsd_l2")
        from isalhg.metric_space.representations.netlsd import NetLSDDistance

        assert isinstance(d, NetLSDDistance)
        assert d.name == "netlsd_l2"
        assert "netlsd_l2" in registry.available_distances()


class TestHICSmokeTest:
    def test_hic_rhg10_matrix_finite_symmetric(self) -> None:
        """Smoke test on real HIC data (at most 6 items from RHG-10).

        MUTAG is a graph-classification benchmark, not an HIC dataset name.
        Valid HIC names are RHG-10/3/Table/Pyramid, IMDB-*, Steam-Player,
        Twitter-Friend.  RHG-10 is the smallest random hypergraph corpus.
        """
        if not HIC_ROOT.exists():
            pytest.skip(f"HIC data root not found: {HIC_ROOT}")
        pytest.importorskip("netlsd")
        from isalhg.datasets.hic_atlas import HICAtlasDataset
        from isalhg.metric_space.representations.netlsd import NetLSDDistance

        try:
            dataset = HICAtlasDataset(root=HIC_ROOT, hic_name="RHG-10")
        except FileNotFoundError as exc:
            pytest.skip(f"HIC RHG-10 data file not present: {exc}")
        items = list(dataset)[:6]
        corpus = [item.hypergraph for item in items]
        if not corpus:
            pytest.skip("RHG-10 dataset yielded no items")
        D = NetLSDDistance().matrix(corpus)
        assert D.shape == (len(corpus), len(corpus))
        assert np.all(np.isfinite(D))
        assert np.allclose(D, D.T)
