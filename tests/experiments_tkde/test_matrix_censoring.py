"""Unit tests for the sidecar-aware matrix reader (D-KBf2).

A budgeted matrix build writes its manifest over the *survivors*, so the strict
reader that validates against the full frozen order reports a censored arm as a
cache miss. These tests pin the three outcomes the consumers depend on: an
unscreened arm reads exactly as before, a screened arm reads short and names its
survivors, and a sidecar that does not partition the frozen order is refused
rather than silently indexed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from experiments.tkde.matrices import (
    MatrixCacheMissingError,
    MatrixCensoringError,
    censoring_path,
    collection_cache_dir,
    load_cached_matrix,
    load_cached_matrix_censored,
)
from isalhg.metric_space.toolkit.matrix import cache_paths, member_order_sha1

pytestmark = pytest.mark.unit

COLLECTION = "toy"
FROZEN: tuple[str, ...] = ("m0", "m1", "m2", "m3")


def _write_matrix(root: Path, arm: str, order: tuple[str, ...]) -> np.ndarray:
    """Write a symmetric hollow matrix plus the manifest that describes ``order``."""
    cache_dir = collection_cache_dir(root, COLLECTION)
    cache_dir.mkdir(parents=True, exist_ok=True)
    n = len(order)
    matrix = np.zeros((n, n), dtype=np.float32)
    for i in range(n):
        for j in range(i + 1, n):
            matrix[i, j] = matrix[j, i] = float(i + j)
    matrix_path, manifest_path = cache_paths(cache_dir, arm)
    np.save(matrix_path, matrix)
    manifest_path.write_text(
        json.dumps({"arm": arm, "n": n, "member_order_sha1": member_order_sha1(order)}),
        encoding="utf-8",
    )
    return matrix


def _write_sidecar(root: Path, arm: str, kept: tuple[str, ...], censored: tuple[str, ...]) -> None:
    """Write a censoring sidecar without going through the builder."""
    cache_dir = collection_cache_dir(root, COLLECTION)
    cache_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "arm": arm,
        "n_requested": len(FROZEN),
        "n_censored": len(censored),
        "member_ids": list(kept),
        "censored_ids": list(censored),
        "member_order_sha1": member_order_sha1(kept),
    }
    censoring_path(cache_dir, arm).write_text(json.dumps(payload), encoding="utf-8")


class TestUnscreenedArm:
    def test_full_order_is_returned_with_no_censoring(self, tmp_path: Path) -> None:
        expected = _write_matrix(tmp_path, "size_l1", FROZEN)
        matrix, kept, censored = load_cached_matrix_censored(
            tmp_path, COLLECTION, "size_l1", FROZEN
        )
        np.testing.assert_array_equal(matrix, expected)
        assert kept == FROZEN
        assert censored == ()

    def test_agrees_with_the_strict_reader(self, tmp_path: Path) -> None:
        _write_matrix(tmp_path, "size_l1", FROZEN)
        strict = load_cached_matrix(tmp_path, COLLECTION, "size_l1", FROZEN)
        matrix, _, _ = load_cached_matrix_censored(tmp_path, COLLECTION, "size_l1", FROZEN)
        np.testing.assert_array_equal(matrix, strict)

    def test_absent_matrix_still_raises(self, tmp_path: Path) -> None:
        with pytest.raises(MatrixCacheMissingError):
            load_cached_matrix_censored(tmp_path, COLLECTION, "never_built", FROZEN)


class TestScreenedArm:
    @pytest.mark.parametrize(
        ("kept", "censored"),
        [
            (("m0", "m1", "m2"), ("m3",)),
            (("m1", "m3"), ("m0", "m2")),
            (("m0",), ("m1", "m2", "m3")),
        ],
    )
    def test_short_matrix_reads_against_the_survivors(
        self, tmp_path: Path, kept: tuple[str, ...], censored: tuple[str, ...]
    ) -> None:
        expected = _write_matrix(tmp_path, "wstar_orbit", kept)
        _write_sidecar(tmp_path, "wstar_orbit", kept, censored)
        matrix, got_kept, got_censored = load_cached_matrix_censored(
            tmp_path, COLLECTION, "wstar_orbit", FROZEN
        )
        np.testing.assert_array_equal(matrix, expected)
        assert got_kept == kept
        assert got_censored == censored

    def test_the_strict_reader_would_have_missed_it(self, tmp_path: Path) -> None:
        kept = ("m0", "m1", "m2")
        _write_matrix(tmp_path, "wstar_orbit", kept)
        _write_sidecar(tmp_path, "wstar_orbit", kept, ("m3",))
        with pytest.raises(MatrixCacheMissingError):
            load_cached_matrix(tmp_path, COLLECTION, "wstar_orbit", FROZEN)

    def test_every_member_censored_yields_an_empty_survivor_set(self, tmp_path: Path) -> None:
        _write_matrix(tmp_path, "wstar_orbit", ())
        _write_sidecar(tmp_path, "wstar_orbit", (), FROZEN)
        matrix, kept, censored = load_cached_matrix_censored(
            tmp_path, COLLECTION, "wstar_orbit", FROZEN
        )
        assert matrix.shape == (0, 0)
        assert kept == ()
        assert censored == FROZEN


class TestCorruptSidecar:
    @pytest.mark.parametrize(
        ("kept", "censored", "reason"),
        [
            (("m0", "m1"), ("m2",), "a member of the frozen order appears on neither side"),
            (("m0", "m1", "m2"), ("m3", "m4"), "the sidecar names a member the order lacks"),
            (("m0", "m1", "m3"), ("m1", "m2"), "an id is both kept and censored"),
        ],
    )
    def test_a_non_partition_is_refused(
        self,
        tmp_path: Path,
        kept: tuple[str, ...],
        censored: tuple[str, ...],
        reason: str,
    ) -> None:
        _write_matrix(tmp_path, "wstar_orbit", kept)
        _write_sidecar(tmp_path, "wstar_orbit", kept, censored)
        with pytest.raises(MatrixCensoringError):
            load_cached_matrix_censored(tmp_path, COLLECTION, "wstar_orbit", FROZEN)

    def test_a_corruption_is_not_a_cache_miss(self, tmp_path: Path) -> None:
        # `cached_arms` swallows MatrixCacheMissingError; a corrupted sidecar
        # must not be swallowed with it.
        assert not issubclass(MatrixCensoringError, MatrixCacheMissingError)

    def test_an_unreadable_sidecar_falls_back_to_the_strict_reader(self, tmp_path: Path) -> None:
        _write_matrix(tmp_path, "wstar_orbit", FROZEN)
        cache_dir = collection_cache_dir(tmp_path, COLLECTION)
        censoring_path(cache_dir, "wstar_orbit").write_text("{not json", encoding="utf-8")
        matrix, kept, censored = load_cached_matrix_censored(
            tmp_path, COLLECTION, "wstar_orbit", FROZEN
        )
        assert matrix.shape == (len(FROZEN), len(FROZEN))
        assert kept == FROZEN
        assert censored == ()
