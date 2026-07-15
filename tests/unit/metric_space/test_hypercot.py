"""Unit tests for :class:`isalhg.metric_space.representations.hypercot`.

Test categories
---------------
1. **Guard-path** (always run, no pinned env needed):
   - :class:`SubprocessRepresentationError` with setup hint when the env is
     absent (bogus env name).
   - Registration: ``"hypercot"`` is retrievable from the distance registry.

2. **End-to-end** (``@pytest.mark.slow``, skipped when env absent):
   - :meth:`matrix` on ≤4 items from design fixtures + a permuted isomorphic
     pair; assert shape ``(N, N)``, symmetry, zero diagonal, and distance 0
     on the isomorphic pair.

3. **HIC smoke** (``@pytest.mark.slow``, skipped when env absent or HIC data
   missing):
   - :meth:`matrix` on ≤4 items from ``HICAtlasDataset("RHG-10")``;
     assert finite + symmetric.

Note on ``hic_name``
--------------------
The task spec quoted ``hic_name="MUTAG"``, but the valid names for
:class:`isalhg.datasets.hic_atlas.HICAtlasDataset` are the 12 HIC atlas
datasets (``"RHG-10"``, ``"RHG-3"``, ``"IMDB-Dir-Form"``, …).  ``"MUTAG"``
is a graph-classification benchmark, not one of them; using it would raise
``KeyError`` from ``_HIC_FILE_MAP``.  The test uses ``"RHG-10"`` instead.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.errors import SubprocessRepresentationError
from isalhg.metric_space import registry
from isalhg.metric_space.representations.hypercot import HyperCOTDistance

pytestmark = pytest.mark.unit

# Path of the pinned env's Python — used to decide whether to skip slow tests.
_HYPERCOT_PYTHON = Path.home() / ".conda" / "envs" / "isalhg-hypercot" / "bin" / "python"

# Absolute path to HIC data files (may not exist on every machine).
_HIC_ROOT = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/data/HIC/data")


def _env_present() -> bool:
    """True when the ``isalhg-hypercot`` conda env Python is executable."""
    return _HYPERCOT_PYTHON.is_file()


# ---------------------------------------------------------------------------
# 1. Guard-path (always run)
# ---------------------------------------------------------------------------


class TestGuardPath:
    def test_missing_env_raises_subprocess_error(self) -> None:
        """``SubprocessRepresentationError`` raised with a setup hint when env absent."""

        class _BogusDist(HyperCOTDistance):
            PINNED_ENV = "isalhg-hypercot-does-not-exist-guard-test"

        d = _BogusDist()
        H = SparseHypergraph(n_nodes=3, hyperedges=[frozenset({0, 1, 2})])
        with pytest.raises(SubprocessRepresentationError) as exc_info:
            d.pairwise(H, H)
        msg = str(exc_info.value)
        # The error must carry a concrete setup hint pointing to the env.
        assert "conda" in msg.lower() or "envs" in msg

    def test_missing_worker_raises_subprocess_error(self) -> None:
        """``SubprocessRepresentationError`` raised when worker script is absent."""

        class _BadWorkerDist(HyperCOTDistance):
            # Use the real env name but point at a nonexistent script.
            WORKER_SCRIPT = "/nonexistent/path/hypercot_worker.py"

        d = _BadWorkerDist()
        H = SparseHypergraph(n_nodes=3, hyperedges=[frozenset({0, 1, 2})])
        # Env may or may not exist; either way worker is gone → error.
        if _env_present():
            with pytest.raises(SubprocessRepresentationError):
                d.pairwise(H, H)
        else:
            with pytest.raises(SubprocessRepresentationError):
                d.pairwise(H, H)

    def test_name(self) -> None:
        assert HyperCOTDistance().name == "hypercot"

    def test_registration(self) -> None:
        """``"hypercot"`` is registered and retrievable via the distance registry."""
        d = registry.get_distance("hypercot")
        assert isinstance(d, HyperCOTDistance)
        assert d.name == "hypercot"

    def test_registration_in_available_distances(self) -> None:
        assert "hypercot" in registry.available_distances()


# ---------------------------------------------------------------------------
# 2. End-to-end (requires isalhg-hypercot env)
# ---------------------------------------------------------------------------


@pytest.mark.slow
class TestEndToEnd:
    """End-to-end tests that actually invoke the HyperCOT subprocess.

    Skipped automatically when the ``isalhg-hypercot`` conda env is absent.
    """

    def test_matrix_shape_symmetry_zero_diag(
        self,
        fano_plane: SparseHypergraph,
        iso_pair_small: tuple[SparseHypergraph, SparseHypergraph, list[int]],
    ) -> None:
        """``matrix()`` returns (N,N), symmetric, zero-diagonal result."""
        np = pytest.importorskip("numpy")
        if not _env_present():
            pytest.skip("isalhg-hypercot env not built")

        h1, h2, _ = iso_pair_small
        corpus: list[SparseHypergraph] = [fano_plane, h1, h2]
        d = HyperCOTDistance()
        mat = d.matrix(corpus)

        assert mat.shape == (3, 3)
        assert np.allclose(mat, mat.T, atol=1e-9)
        assert np.allclose(np.diag(mat), 0.0, atol=1e-9)

    def test_distance_zero_on_iso_pair(
        self,
        fano_plane: SparseHypergraph,
        iso_pair_small: tuple[SparseHypergraph, SparseHypergraph, list[int]],
    ) -> None:
        """Isomorphic hypergraphs must be at HyperCOT distance 0."""
        pytest.importorskip("numpy")
        if not _env_present():
            pytest.skip("isalhg-hypercot env not built")

        h1, h2, _ = iso_pair_small
        # iso_pair_small: H2 = permute(H1, sigma) — verified isomorphic.
        fano_perm = permute(fano_plane, [6, 5, 4, 3, 2, 1, 0])

        corpus: list[SparseHypergraph] = [fano_plane, fano_perm, h1, h2]
        d = HyperCOTDistance()
        mat = d.matrix(corpus)

        assert mat.shape == (4, 4)
        # Fano vs. its reverse permutation.
        assert mat[0, 1] == pytest.approx(0.0, abs=1e-8)
        # iso_pair_small members.
        assert mat[2, 3] == pytest.approx(0.0, abs=1e-8)

    def test_pairwise_consistent_with_matrix(
        self,
        iso_pair_small: tuple[SparseHypergraph, SparseHypergraph, list[int]],
    ) -> None:
        """``pairwise(H1, H2)`` equals ``matrix([H1, H2])[0, 1]``."""
        pytest.importorskip("numpy")
        if not _env_present():
            pytest.skip("isalhg-hypercot env not built")

        h1, h2, _ = iso_pair_small
        d = HyperCOTDistance()
        assert d.pairwise(h1, h2) == pytest.approx(d.matrix([h1, h2])[0, 1], abs=1e-12)

    def test_empty_corpus(self) -> None:
        """``matrix([])`` returns ``(0, 0)`` matrix."""
        pytest.importorskip("numpy")
        if not _env_present():
            pytest.skip("isalhg-hypercot env not built")

        d = HyperCOTDistance()
        mat = d.matrix([])
        assert mat.shape == (0, 0)


# ---------------------------------------------------------------------------
# 3. HIC smoke test
# ---------------------------------------------------------------------------


@pytest.mark.slow
class TestHICSmoke:
    """Smoke test on real HIC atlas data.

    Skipped when ``isalhg-hypercot`` env absent or ``_HIC_ROOT`` missing.
    Uses ``hic_name="RHG-10"`` — a valid HIC atlas dataset.
    """

    def test_matrix_finite_and_symmetric(self) -> None:
        np = pytest.importorskip("numpy")
        if not _env_present():
            pytest.skip("isalhg-hypercot env not built")
        if not _HIC_ROOT.exists():
            pytest.skip(f"HIC_ROOT not found: {_HIC_ROOT}")

        from isalhg.datasets.hic_atlas import HICAtlasDataset

        ds = HICAtlasDataset(root=_HIC_ROOT, hic_name="RHG-10")
        items = list(ds)[:4]
        if not items:
            pytest.skip("RHG-10 dataset yielded no items")

        corpus = [item.hypergraph for item in items]
        d = HyperCOTDistance()
        mat = d.matrix(corpus)

        n = len(corpus)
        assert mat.shape == (n, n)
        assert np.all(np.isfinite(mat))
        assert np.allclose(mat, mat.T, atol=1e-9)
