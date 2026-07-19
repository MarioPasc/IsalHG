"""Unit tests for :class:`isalhg.metric_space.representations.nauty_levi_edit`.

NautyLeviEditDistance is an *exact* isomorphism invariant (distance 0 iff the
two Levi canonical forms agree, which implies iso for complete invariants). All
tests require ``pynauty`` to be installed; the suite skips cleanly when it is
absent.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.errors import RepresentationDependencyMissingError
from isalhg.metric_space import registry
from isalhg.metric_space.representations.nauty_levi_edit import NautyLeviEditDistance

pytestmark = pytest.mark.unit

pynauty = pytest.importorskip("pynauty")

HIC_ROOT = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/data/HIC/data/hypergraph")
_HIC_SMOKE_FILE = HIC_ROOT / "RHG" / "RHG_10.txt"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _path_hypergraph() -> SparseHypergraph:
    """4-node path hypergraph with three 2-edges."""
    return SparseHypergraph(
        n_nodes=4,
        hyperedges=[frozenset({0, 1}), frozenset({1, 2}), frozenset({2, 3})],
    )


def _triangle_hypergraph() -> SparseHypergraph:
    """3-node hypergraph with one 3-edge."""
    return SparseHypergraph(n_nodes=3, hyperedges=[frozenset({0, 1, 2})])


# ---------------------------------------------------------------------------
# Pairwise
# ---------------------------------------------------------------------------


class TestPairwise:
    def test_zero_on_iso_pair(
        self, iso_pair_small: tuple[SparseHypergraph, SparseHypergraph, list[int]]
    ) -> None:
        h1, h2, _ = iso_pair_small
        d = NautyLeviEditDistance()
        assert d.pairwise(h1, h2) == 0.0

    def test_zero_on_permuted_fano(self, fano_plane: SparseHypergraph) -> None:
        d = NautyLeviEditDistance()
        sigma = [6, 5, 4, 3, 2, 1, 0]
        assert d.pairwise(fano_plane, permute(fano_plane, sigma)) == 0.0

    def test_zero_on_permuted_sts9(self, sts_9: SparseHypergraph) -> None:
        d = NautyLeviEditDistance()
        sigma = list(reversed(range(9)))  # [8,7,6,5,4,3,2,1,0]
        assert d.pairwise(sts_9, permute(sts_9, sigma)) == 0.0

    def test_self_distance_zero(self, fano_plane: SparseHypergraph) -> None:
        d = NautyLeviEditDistance()
        assert d.pairwise(fano_plane, fano_plane) == 0.0

    def test_positive_on_distinct_designs(
        self, fano_plane: SparseHypergraph, sts_9: SparseHypergraph
    ) -> None:
        d = NautyLeviEditDistance()
        assert d.pairwise(fano_plane, sts_9) > 0.0

    def test_positive_on_non_iso_pair(
        self, non_iso_pair_small: tuple[SparseHypergraph, SparseHypergraph]
    ) -> None:
        h1, h2 = non_iso_pair_small
        d = NautyLeviEditDistance()
        assert d.pairwise(h1, h2) > 0.0

    def test_symmetry(self, fano_plane: SparseHypergraph, sts_9: SparseHypergraph) -> None:
        d = NautyLeviEditDistance()
        assert d.pairwise(fano_plane, sts_9) == d.pairwise(sts_9, fano_plane)

    def test_name(self) -> None:
        assert NautyLeviEditDistance().name == "nauty_levi_edit"


# ---------------------------------------------------------------------------
# Matrix
# ---------------------------------------------------------------------------


class TestMatrix:
    def test_matrix_shape_and_symmetry(
        self,
        fano_plane: SparseHypergraph,
        sts_9: SparseHypergraph,
        single_edge_hypergraph: SparseHypergraph,
        iso_pair_small: tuple[SparseHypergraph, SparseHypergraph, list[int]],
        non_iso_pair_small: tuple[SparseHypergraph, SparseHypergraph],
    ) -> None:
        np = pytest.importorskip("numpy")
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
        d = NautyLeviEditDistance()
        mat = d.matrix(corpus)
        assert mat.shape == (10, 10)
        assert np.allclose(mat, mat.T)
        assert np.allclose(np.diag(mat), 0.0)

    def test_matrix_zero_on_iso_pairs(
        self,
        fano_plane: SparseHypergraph,
        sts_9: SparseHypergraph,
        iso_pair_small: tuple[SparseHypergraph, SparseHypergraph, list[int]],
    ) -> None:
        pytest.importorskip("numpy")
        i1, i2, _ = iso_pair_small
        corpus = [
            fano_plane,
            permute(fano_plane, [1, 2, 3, 4, 5, 6, 0]),
            sts_9,
            permute(sts_9, [1, 2, 3, 4, 5, 6, 7, 8, 0]),
            i1,
            i2,
        ]
        d = NautyLeviEditDistance()
        mat = d.matrix(corpus)
        assert mat[0, 1] == 0.0  # fano vs permuted fano
        assert mat[2, 3] == 0.0  # sts9 vs permuted sts9
        assert mat[4, 5] == 0.0  # iso pair

    def test_matrix_positive_on_distinct_designs(
        self, fano_plane: SparseHypergraph, sts_9: SparseHypergraph
    ) -> None:
        pytest.importorskip("numpy")
        corpus = [fano_plane, sts_9]
        d = NautyLeviEditDistance()
        mat = d.matrix(corpus)
        assert mat[0, 1] > 0.0

    def test_empty_corpus(self) -> None:
        pytest.importorskip("numpy")
        d = NautyLeviEditDistance()
        mat = d.matrix([])
        assert mat.shape == (0, 0)


# ---------------------------------------------------------------------------
# Guarded import raises RepresentationDependencyMissingError
# ---------------------------------------------------------------------------


class TestGuardedImport:
    def test_pynauty_missing_raises_on_pairwise(
        self,
        fano_plane: SparseHypergraph,
        sts_9: SparseHypergraph,
    ) -> None:
        """Simulate pynauty absence by patching builtins.__import__."""
        import builtins

        real_import = builtins.__import__

        def _block_pynauty(name: str, *args: object, **kwargs: object) -> object:
            if name == "pynauty":
                raise ImportError("No module named 'pynauty'")
            return real_import(name, *args, **kwargs)

        # Remove pynauty from sys.modules so the guarded re-import is attempted.
        saved = sys.modules.pop("pynauty", None)
        try:
            with patch("builtins.__import__", side_effect=_block_pynauty):
                d = NautyLeviEditDistance()
                with pytest.raises(RepresentationDependencyMissingError, match="pynauty"):
                    d.pairwise(fano_plane, sts_9)
        finally:
            if saved is not None:
                sys.modules["pynauty"] = saved

    def test_pynauty_missing_raises_on_fingerprint(
        self,
        fano_plane: SparseHypergraph,
    ) -> None:
        import builtins

        real_import = builtins.__import__

        def _block_pynauty(name: str, *args: object, **kwargs: object) -> object:
            if name == "pynauty":
                raise ImportError("No module named 'pynauty'")
            return real_import(name, *args, **kwargs)

        saved = sys.modules.pop("pynauty", None)
        try:
            with patch("builtins.__import__", side_effect=_block_pynauty):
                d = NautyLeviEditDistance()
                with pytest.raises(RepresentationDependencyMissingError, match="pynauty"):
                    d.fingerprint(fano_plane)
        finally:
            if saved is not None:
                sys.modules["pynauty"] = saved


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class TestRegistry:
    def test_registered_and_retrievable(self) -> None:
        # Importing the module triggers register_distance at module load time.
        import isalhg.metric_space.representations.nauty_levi_edit  # noqa: F401

        d = registry.get_distance("nauty_levi_edit")
        assert isinstance(d, NautyLeviEditDistance)
        assert d.name == "nauty_levi_edit"
        assert "nauty_levi_edit" in registry.available_distances()


# ---------------------------------------------------------------------------
# HIC smoke test
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not _HIC_SMOKE_FILE.exists(),
    reason=f"HIC data file not found at {_HIC_SMOKE_FILE}; skipping smoke test",
)
class TestHICSmokeTest:
    def test_matrix_on_small_hic_corpus(self) -> None:
        np = pytest.importorskip("numpy")
        from isalhg.datasets.hic_atlas import HICAtlasDataset

        dataset = HICAtlasDataset(root=HIC_ROOT, hic_name="RHG-10")
        items = list(dataset)[:6]
        corpus = [item.hypergraph for item in items]
        assert len(corpus) >= 1, "Expected at least 1 item from MUTAG"
        d = NautyLeviEditDistance()
        mat = d.matrix(corpus)
        n = len(corpus)
        assert mat.shape == (n, n)
        assert np.all(np.isfinite(mat))
        assert np.allclose(mat, mat.T)
