"""Unit tests for :class:`isalhg.metric_space.representations.hpd`.

HPD is iso-invariant (distance 0 on isomorphic pairs). With ``sqrt_js=True``
(the default) it returns the JS distance (a proper metric); with
``sqrt_js=False`` it returns the raw Jensen-Shannon divergence.
"""

from __future__ import annotations

import sys

import pytest

from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.errors import RepresentationDependencyMissingError
from isalhg.metric_space import registry
from isalhg.metric_space.representations.hpd import HPDDistance

pytestmark = pytest.mark.unit

# --------------------------------------------------------------------------- #
# small auxiliary corpus builders
# --------------------------------------------------------------------------- #

# Correct root is the `hypergraph/` subdirectory (task spec listed the parent,
# but the actual file map paths are relative to `hypergraph/`).
HIC_ROOT = "/media/mpascual/Sandisk2TB/research/ISAL/isalhg/data/HIC/data/hypergraph"


def _two_sharing_edges() -> SparseHypergraph:
    """Two 3-edges that share exactly two nodes; distinct from the iso_pair fixture."""
    return SparseHypergraph(
        n_nodes=5,
        hyperedges=[frozenset({0, 1, 2}), frozenset({2, 3, 4})],
    )


# --------------------------------------------------------------------------- #
# pairwise
# --------------------------------------------------------------------------- #


class TestPairwise:
    def test_zero_on_iso_pair(
        self, iso_pair_small: tuple[SparseHypergraph, SparseHypergraph, list[int]]
    ) -> None:
        h1, h2, _ = iso_pair_small
        assert HPDDistance().pairwise(h1, h2) == pytest.approx(0.0, abs=1e-12)

    def test_zero_on_permuted_design_fixture(self, fano_plane: SparseHypergraph) -> None:
        d = HPDDistance()
        perm = list(range(6, -1, -1))  # reverse 0..6
        assert d.pairwise(fano_plane, permute(fano_plane, perm)) == pytest.approx(0.0, abs=1e-12)

    def test_self_distance_zero(self, sts_9: SparseHypergraph) -> None:
        assert HPDDistance().pairwise(sts_9, sts_9) == pytest.approx(0.0, abs=1e-12)

    def test_positive_on_distinct_designs(
        self, fano_plane: SparseHypergraph, sts_9: SparseHypergraph
    ) -> None:
        # Fano has 7 nodes / 7 edges / all degree 3;
        # STS(9) has 9 nodes / 12 edges / all degree 4 — distinct portrait.
        assert HPDDistance().pairwise(fano_plane, sts_9) > 0.0

    def test_sqrt_js_default_larger_than_raw_jsd(
        self, fano_plane: SparseHypergraph, sts_9: SparseHypergraph
    ) -> None:
        """sqrt(JSD) >= JSD for JSD in [0,1]; default mode is the proper metric."""
        d_sqrt = HPDDistance(sqrt_js=True)
        d_jsd = HPDDistance(sqrt_js=False)
        v_sqrt = d_sqrt.pairwise(fano_plane, sts_9)
        v_jsd = d_jsd.pairwise(fano_plane, sts_9)
        assert v_jsd > 0.0
        assert v_sqrt > 0.0
        # sqrt(x) >= x for x in [0,1]: sqrt form must be larger
        assert v_sqrt >= v_jsd
        # relationship must hold
        assert v_sqrt**2 == pytest.approx(v_jsd, rel=1e-9)

    def test_jsd_mode_symmetric(
        self, fano_plane: SparseHypergraph, sts_9: SparseHypergraph
    ) -> None:
        d = HPDDistance(sqrt_js=False)
        assert d.pairwise(fano_plane, sts_9) == pytest.approx(
            d.pairwise(sts_9, fano_plane), rel=1e-9
        )

    def test_name(self) -> None:
        assert HPDDistance().name == "hpd_jsd"
        assert HPDDistance(sqrt_js=False).name == "hpd_jsd"


# --------------------------------------------------------------------------- #
# matrix
# --------------------------------------------------------------------------- #


class TestMatrix:
    def test_matrix_shape_symmetric_zero_diagonal(
        self,
        fano_plane: SparseHypergraph,
        sts_9: SparseHypergraph,
        single_edge_hypergraph: SparseHypergraph,
        iso_pair_small: tuple[SparseHypergraph, SparseHypergraph, list[int]],
        non_iso_pair_small: tuple[SparseHypergraph, SparseHypergraph],
    ) -> None:
        np = pytest.importorskip("numpy")
        i1, i2, _ = iso_pair_small
        h1, _ = non_iso_pair_small
        corpus = [
            fano_plane,
            permute(fano_plane, [1, 2, 3, 4, 5, 6, 0]),
            sts_9,
            i1,
            i2,
            h1,
        ]
        mat = HPDDistance().matrix(corpus)
        assert mat.shape == (6, 6)
        assert np.allclose(mat, mat.T)
        assert np.allclose(np.diag(mat), 0.0)
        assert (mat >= 0.0).all()

    def test_matrix_iso_pairs_zero(
        self,
        fano_plane: SparseHypergraph,
        iso_pair_small: tuple[SparseHypergraph, SparseHypergraph, list[int]],
    ) -> None:
        pytest.importorskip("numpy")
        i1, i2, _ = iso_pair_small
        corpus = [
            fano_plane,
            permute(fano_plane, [1, 2, 3, 4, 5, 6, 0]),
            i1,
            i2,
        ]
        mat = HPDDistance().matrix(corpus)
        assert mat[0, 1] == pytest.approx(0.0, abs=1e-12)  # fano vs permuted fano
        assert mat[2, 3] == pytest.approx(0.0, abs=1e-12)  # iso pair

    def test_positive_off_diagonal_distinct(
        self,
        fano_plane: SparseHypergraph,
        sts_9: SparseHypergraph,
    ) -> None:
        pytest.importorskip("numpy")
        corpus = [fano_plane, sts_9]
        mat = HPDDistance().matrix(corpus)
        assert mat[0, 1] > 0.0


# --------------------------------------------------------------------------- #
# dependency guard
# --------------------------------------------------------------------------- #


class TestDependencyGuard:
    def test_missing_xgi_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """RepresentationDependencyMissingError when xgi is absent."""
        monkeypatch.setitem(sys.modules, "xgi", None)  # type: ignore[arg-type]
        d = HPDDistance()
        h = SparseHypergraph(n_nodes=4, hyperedges=[frozenset({0, 1, 2}), frozenset({0, 1, 3})])
        with pytest.raises(RepresentationDependencyMissingError):
            d.pairwise(h, h)


# --------------------------------------------------------------------------- #
# registry
# --------------------------------------------------------------------------- #


class TestRegistry:
    def test_registered_and_retrievable(self) -> None:
        # Importing this test module (via `from ... import HPDDistance` above)
        # has already triggered register_distance("hpd_jsd", ...).
        d = registry.get_distance("hpd_jsd")
        assert isinstance(d, HPDDistance)
        assert d.name == "hpd_jsd"
        assert "hpd_jsd" in registry.available_distances()


# --------------------------------------------------------------------------- #
# HIC smoke test
# --------------------------------------------------------------------------- #


@pytest.mark.slow
def test_hic_smoke() -> None:
    """Load <=6 items from HICAtlasDataset and verify matrix is finite + symmetric."""
    import os
    from pathlib import Path

    np = pytest.importorskip("numpy")

    if not os.path.isdir(HIC_ROOT):
        pytest.skip(f"HIC data root not found: {HIC_ROOT}")

    try:
        from isalhg.datasets.hic_atlas import HICAtlasDataset
    except ImportError:
        pytest.skip("isalhg.datasets.hic_atlas not importable")

    # "RHG-10" is the smallest available HIC dataset in _HIC_FILE_MAP.
    # (Task spec listed "MUTAG" which is not a valid HIC dataset name.)
    ds = HICAtlasDataset(root=Path(HIC_ROOT), hic_name="RHG-10")
    items = list(ds)[:6]
    if not items:
        pytest.skip("HIC dataset yielded no items")

    corpus = [item.hypergraph for item in items]
    mat = HPDDistance().matrix(corpus)
    assert np.all(np.isfinite(mat)), "matrix has non-finite entries"
    assert np.allclose(mat, mat.T, atol=1e-12), "matrix is not symmetric"
