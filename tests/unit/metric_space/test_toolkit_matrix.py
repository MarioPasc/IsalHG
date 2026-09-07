"""Unit tests for the distance-matrix builder and its cache.

The cache is the part that can silently corrupt every downstream table: a
matrix reused under a different member order indexes the wrong rows and nothing
raises. The tests therefore pin the key (arm, n, member-order SHA-1, params) in
both directions -- a match reuses without recomputing, any mismatch recomputes.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.errors import MetricSpaceError
from isalhg.metric_space.toolkit.matrix import (
    build_matrix,
    cache_paths,
    member_order_sha1,
)

pytestmark = pytest.mark.unit


def make_hypergraph(edges: list[tuple[int, ...]], n: int) -> SparseHypergraph:
    return SparseHypergraph(n, [frozenset(edge) for edge in edges])


@pytest.fixture
def corpus() -> tuple[list[SparseHypergraph], list[str]]:
    items = [
        make_hypergraph([(0, 1), (1, 2)], 3),
        make_hypergraph([(0, 1), (1, 2), (0, 2)], 3),
        make_hypergraph([(0, 1), (1, 2), (2, 3)], 4),
        make_hypergraph([(0, 1, 2), (2, 3)], 4),
    ]
    return items, [f"m{i}" for i in range(len(items))]


class TestMemberOrderKey:
    def test_sha1_of_the_newline_joined_ids(self) -> None:
        ids = ["a", "b", "c"]
        expected = hashlib.sha1(b"a\nb\nc", usedforsecurity=False).hexdigest()
        assert member_order_sha1(ids) == expected

    def test_order_changes_the_key(self) -> None:
        assert member_order_sha1(["a", "b"]) != member_order_sha1(["b", "a"])


class TestBuildMatrixShape:
    @pytest.mark.parametrize("arm", ["fact_rank", "size_l1"])
    def test_symmetric_zero_diagonal_finite_float32(
        self, arm: str, corpus: tuple[list[SparseHypergraph], list[str]]
    ) -> None:
        items, ids = corpus
        D = build_matrix(items, arm, member_ids=ids)
        assert D.shape == (len(items), len(items))
        assert D.dtype == np.float32
        np.testing.assert_allclose(D, D.T)
        np.testing.assert_allclose(np.diag(D), 0.0)
        assert np.isfinite(D).all()

    def test_empty_corpus(self) -> None:
        D = build_matrix([], "fact_rank", member_ids=[])
        assert D.shape == (0, 0)

    def test_single_item(self, corpus: tuple[list[SparseHypergraph], list[str]]) -> None:
        items, ids = corpus
        D = build_matrix(items[:1], "size_l1", member_ids=ids[:1])
        assert D.shape == (1, 1)
        assert D[0, 0] == 0.0

    def test_fact_rank_agrees_with_the_distance_object(
        self, corpus: tuple[list[SparseHypergraph], list[str]]
    ) -> None:
        from isalhg.metric_space.registry import get_distance

        items, ids = corpus
        built = build_matrix(items, "fact_rank", member_ids=ids)
        reference = get_distance("fact_rank").matrix(items)
        np.testing.assert_allclose(built, reference.astype(np.float32))

    def test_parallel_path_matches_the_serial_one(
        self, corpus: tuple[list[SparseHypergraph], list[str]]
    ) -> None:
        items, ids = corpus
        serial = build_matrix(items, "size_l1", member_ids=ids, n_jobs=1)
        parallel = build_matrix(items, "size_l1", member_ids=ids, n_jobs=2)
        np.testing.assert_allclose(serial, parallel)


class TestBuildMatrixValidation:
    def test_member_id_length_mismatch(
        self, corpus: tuple[list[SparseHypergraph], list[str]]
    ) -> None:
        items, ids = corpus
        with pytest.raises(MetricSpaceError, match="member_ids"):
            build_matrix(items, "size_l1", member_ids=ids[:2])

    def test_roles_length_mismatch(self, corpus: tuple[list[SparseHypergraph], list[str]]) -> None:
        items, ids = corpus
        with pytest.raises(MetricSpaceError, match="roles"):
            build_matrix(items, "fact_rank_roles", member_ids=ids, roles=[None])

    def test_bad_n_jobs(self, corpus: tuple[list[SparseHypergraph], list[str]]) -> None:
        items, ids = corpus
        with pytest.raises(MetricSpaceError, match="n_jobs"):
            build_matrix(items, "size_l1", member_ids=ids, n_jobs=0)

    def test_non_empty_params_are_refused(
        self, corpus: tuple[list[SparseHypergraph], list[str]]
    ) -> None:
        items, ids = corpus
        with pytest.raises(MetricSpaceError, match="zero-argument factories"):
            build_matrix(items, "size_l1", member_ids=ids, params={"depth": 3})


class TestFingerprintRouting:
    """An amortizing arm must not go round the pairwise loop.

    The loop asks each member's representation ``N - 1`` times, which for the
    Isal instruction words is the whole cost of the build. The router decides on
    ``fingerprint(H) is not None``, so a stub that answers must never see
    ``pairwise``.
    """

    def test_a_distance_with_a_fingerprint_never_hits_pairwise(
        self, corpus: tuple[list[SparseHypergraph], list[str]], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import isalhg.metric_space.toolkit.matrix as matrix_module

        calls: list[str] = []

        class Amortizing:
            labels_used = frozenset()
            name = "stub_amortizing"

            def fingerprint(self, H: SparseHypergraph) -> tuple[int, ...]:
                return (H.n_nodes, H.n_edges)

            def pairwise(self, H1: SparseHypergraph, H2: SparseHypergraph) -> float:
                calls.append("pairwise")
                raise AssertionError("the pairwise loop must not be reached")

            def matrix(self, items: list[SparseHypergraph]) -> np.ndarray:
                calls.append("matrix")
                sizes = np.array([H.n_nodes for H in items], dtype=np.float64)
                return np.abs(sizes[:, None] - sizes[None, :])

        monkeypatch.setattr(matrix_module, "_make_distance", lambda arm, params: Amortizing())
        items, ids = corpus
        D = build_matrix(items, "stub_amortizing", member_ids=ids)

        assert "pairwise" not in calls
        assert calls.count("matrix") == 1
        assert D.dtype == np.float32
        assert D[0, 2] == pytest.approx(1.0)

    def test_a_distance_without_a_fingerprint_uses_pairwise(
        self, corpus: tuple[list[SparseHypergraph], list[str]], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import isalhg.metric_space.toolkit.matrix as matrix_module

        calls: list[str] = []

        class NotAmortizing:
            labels_used = frozenset()
            name = "stub_pairwise"

            def fingerprint(self, H: SparseHypergraph) -> None:
                return None

            def pairwise(self, H1: SparseHypergraph, H2: SparseHypergraph) -> float:
                calls.append("pairwise")
                return float(abs(H1.n_nodes - H2.n_nodes))

        monkeypatch.setattr(matrix_module, "_make_distance", lambda arm, params: NotAmortizing())
        items, ids = corpus
        D = build_matrix(items, "stub_pairwise", member_ids=ids)

        assert calls, "the pairwise loop was skipped for a distance that does not amortize"
        assert D[0, 2] == pytest.approx(1.0)

    def test_a_raising_fingerprint_falls_back_to_pairwise(
        self, corpus: tuple[list[SparseHypergraph], list[str]], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import isalhg.metric_space.toolkit.matrix as matrix_module

        calls: list[str] = []

        class Raising:
            labels_used = frozenset()
            name = "stub_raising"

            def fingerprint(self, H: SparseHypergraph) -> None:
                raise RuntimeError("no standalone representation here")

            def pairwise(self, H1: SparseHypergraph, H2: SparseHypergraph) -> float:
                calls.append("pairwise")
                return float(abs(H1.n_nodes - H2.n_nodes))

        monkeypatch.setattr(matrix_module, "_make_distance", lambda arm, params: Raising())
        items, ids = corpus
        build_matrix(items, "stub_raising", member_ids=ids)
        assert calls

    @pytest.mark.parametrize("arm", ["nauty_cert", "isal_ow_struct"])
    def test_the_routed_matrix_equals_the_pairwise_one(
        self, arm: str, corpus: tuple[list[SparseHypergraph], list[str]]
    ) -> None:
        # The routing changed the path of several arms that were already
        # measured through the loop; the values must be the same ones.
        from isalhg.metric_space.registry import get_distance
        from isalhg.metric_space.toolkit.matrix import _build_from_pairwise

        items, ids = corpus
        routed = build_matrix(items, arm, member_ids=ids)
        looped = _build_from_pairwise(items, arm, 1, {})
        np.fill_diagonal(looped, 0.0)
        assert get_distance(arm).fingerprint(items[0]) is not None
        np.testing.assert_allclose(routed, looped, rtol=0, atol=0)


class TestCache:
    def test_writes_matrix_and_manifest(
        self, tmp_path: Path, corpus: tuple[list[SparseHypergraph], list[str]]
    ) -> None:
        items, ids = corpus
        D = build_matrix(items, "fact_rank", member_ids=ids, cache_dir=tmp_path)
        matrix_path, manifest_path = cache_paths(tmp_path, "fact_rank")
        assert matrix_path.is_file()
        assert manifest_path.is_file()

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["arm"] == "fact_rank"
        assert manifest["n"] == len(items)
        assert manifest["member_order_sha1"] == member_order_sha1(ids)
        assert manifest["params"] == {}
        assert manifest["secs_total"] >= 0.0
        assert manifest["host"]
        assert manifest["created_iso"]
        assert manifest["canonical_name"] == "fact_rank"
        np.testing.assert_allclose(np.load(matrix_path), D)

    def test_second_call_is_a_cache_hit(
        self,
        tmp_path: Path,
        corpus: tuple[list[SparseHypergraph], list[str]],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        items, ids = corpus
        first = build_matrix(items, "fact_rank", member_ids=ids, cache_dir=tmp_path)
        with caplog.at_level("INFO", logger="isalhg.metric_space.toolkit.matrix"):
            second = build_matrix(items, "fact_rank", member_ids=ids, cache_dir=tmp_path)
        assert "cache hit" in caplog.text
        np.testing.assert_allclose(first, second)

    def test_cache_hit_does_not_recompute(
        self, tmp_path: Path, corpus: tuple[list[SparseHypergraph], list[str]]
    ) -> None:
        items, ids = corpus
        build_matrix(items, "fact_rank", member_ids=ids, cache_dir=tmp_path)
        matrix_path, _ = cache_paths(tmp_path, "fact_rank")

        sentinel = np.full((len(items), len(items)), 99.0, dtype=np.float32)
        np.fill_diagonal(sentinel, 0.0)
        np.save(matrix_path, sentinel)

        reused = build_matrix(items, "fact_rank", member_ids=ids, cache_dir=tmp_path)
        np.testing.assert_allclose(reused, sentinel)

    def test_reordered_members_invalidate_the_cache(
        self, tmp_path: Path, corpus: tuple[list[SparseHypergraph], list[str]]
    ) -> None:
        items, ids = corpus
        build_matrix(items, "fact_rank", member_ids=ids, cache_dir=tmp_path)
        matrix_path, _ = cache_paths(tmp_path, "fact_rank")
        sentinel = np.full((len(items), len(items)), 99.0, dtype=np.float32)
        np.fill_diagonal(sentinel, 0.0)
        np.save(matrix_path, sentinel)

        recomputed = build_matrix(
            items[::-1], "fact_rank", member_ids=ids[::-1], cache_dir=tmp_path
        )
        assert not np.allclose(recomputed, sentinel)

    def test_shorter_corpus_invalidates_the_cache(
        self, tmp_path: Path, corpus: tuple[list[SparseHypergraph], list[str]]
    ) -> None:
        items, ids = corpus
        build_matrix(items, "size_l1", member_ids=ids, cache_dir=tmp_path)
        smaller = build_matrix(items[:3], "size_l1", member_ids=ids[:3], cache_dir=tmp_path)
        assert smaller.shape == (3, 3)

    def test_corrupt_manifest_recomputes(
        self, tmp_path: Path, corpus: tuple[list[SparseHypergraph], list[str]]
    ) -> None:
        items, ids = corpus
        expected = build_matrix(items, "size_l1", member_ids=ids, cache_dir=tmp_path)
        _, manifest_path = cache_paths(tmp_path, "size_l1")
        manifest_path.write_text("not json", encoding="utf-8")
        np.testing.assert_allclose(
            build_matrix(items, "size_l1", member_ids=ids, cache_dir=tmp_path), expected
        )

    def test_no_cache_dir_writes_nothing(
        self, tmp_path: Path, corpus: tuple[list[SparseHypergraph], list[str]]
    ) -> None:
        items, ids = corpus
        build_matrix(items, "size_l1", member_ids=ids, cache_dir=None)
        assert list(tmp_path.iterdir()) == []
