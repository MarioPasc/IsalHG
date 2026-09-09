"""Unit tests for RQ2/RQ4/RQ5 consuming a censored arm's short matrix (D-KBf2).

The matrix and its manifest describe the survivors, so a consumer that indexes
by position in the frozen order reads a correct-looking matrix under the wrong
member ids. These tests pin the three properties that rule that out: the row map
is by member id, every cross-arm statistic is restricted to the intersection of
the arms' survivor sets (the RQ1 ``restrict_to_common_units`` rule one level
down), and the per-arm census is reported rather than absorbed (L15).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from experiments.tkde import rq2, rq4, rq5
from experiments.tkde.matrices import (
    censoring_path,
    collection_cache_dir,
    common_member_ids,
    load_arm_matrices,
)
from isalhg.metric_space.toolkit.matrix import cache_paths, member_order_sha1

pytestmark = pytest.mark.unit

COLLECTION = "toy"
FROZEN: tuple[str, ...] = ("m0", "m1", "m2", "m3")


def _write_arm(root: Path, arm: str, kept: tuple[str, ...], censored: tuple[str, ...]) -> None:
    """Write one arm's matrix, manifest and (when censored) sidecar."""
    cache_dir = collection_cache_dir(root, COLLECTION)
    cache_dir.mkdir(parents=True, exist_ok=True)
    n = len(kept)
    matrix = np.zeros((n, n), dtype=np.float32)
    for i in range(n):
        for j in range(i + 1, n):
            matrix[i, j] = matrix[j, i] = float(i + j + 1)
    matrix_path, manifest_path = cache_paths(cache_dir, arm)
    np.save(matrix_path, matrix)
    manifest_path.write_text(
        json.dumps({"arm": arm, "n": n, "member_order_sha1": member_order_sha1(kept)}),
        encoding="utf-8",
    )
    if censored:
        censoring_path(cache_dir, arm).write_text(
            json.dumps(
                {
                    "arm": arm,
                    "n_requested": len(FROZEN),
                    "n_censored": len(censored),
                    "member_ids": list(kept),
                    "censored_ids": list(censored),
                    "member_order_sha1": member_order_sha1(kept),
                }
            ),
            encoding="utf-8",
        )


class TestLoadArmMatrices:
    def test_the_row_map_is_by_member_id(self, tmp_path: Path) -> None:
        _write_arm(tmp_path, "wstar_orbit", ("m0", "m2", "m3"), ("m1",))
        loaded = load_arm_matrices(tmp_path, COLLECTION, ["wstar_orbit"], FROZEN)
        _, row_of = loaded["wstar_orbit"]
        assert row_of == {"m0": 0, "m2": 1, "m3": 2}

    def test_an_unscreened_arm_maps_the_whole_frozen_order(self, tmp_path: Path) -> None:
        _write_arm(tmp_path, "size_l1", FROZEN, ())
        _, row_of = load_arm_matrices(tmp_path, COLLECTION, ["size_l1"], FROZEN)["size_l1"]
        assert row_of == {kb_id: index for index, kb_id in enumerate(FROZEN)}

    def test_an_arm_with_no_matrix_is_omitted_not_raised(self, tmp_path: Path) -> None:
        _write_arm(tmp_path, "size_l1", FROZEN, ())
        loaded = load_arm_matrices(tmp_path, COLLECTION, ["size_l1", "never_built"], FROZEN)
        assert set(loaded) == {"size_l1"}

    def test_the_cache_is_reused_across_calls(self, tmp_path: Path) -> None:
        _write_arm(tmp_path, "size_l1", FROZEN, ())
        cache: dict[str, Any] = {}
        first = load_arm_matrices(tmp_path, COLLECTION, ["size_l1"], FROZEN, cache=cache)
        (cache_dir := collection_cache_dir(tmp_path, COLLECTION)).joinpath("size_l1.npy").unlink()
        assert cache_dir.exists()
        second = load_arm_matrices(tmp_path, COLLECTION, ["size_l1"], FROZEN, cache=cache)
        assert second["size_l1"][1] == first["size_l1"][1]


class TestCommonMemberIds:
    def test_no_censoring_keeps_every_member(self, tmp_path: Path) -> None:
        for arm in ("size_l1", "wl_l1"):
            _write_arm(tmp_path, arm, FROZEN, ())
        loaded = load_arm_matrices(tmp_path, COLLECTION, ["size_l1", "wl_l1"], FROZEN)
        assert common_member_ids(FROZEN, loaded) == FROZEN

    def test_the_intersection_is_taken_across_arms(self, tmp_path: Path) -> None:
        _write_arm(tmp_path, "wstar_orbit", ("m0", "m1", "m2"), ("m3",))
        _write_arm(tmp_path, "wl_l1", ("m1", "m2", "m3"), ("m0",))
        loaded = load_arm_matrices(tmp_path, COLLECTION, ["wstar_orbit", "wl_l1"], FROZEN)
        assert common_member_ids(FROZEN, loaded) == ("m1", "m2")

    def test_an_empty_intersection_is_reported_not_raised(self, tmp_path: Path) -> None:
        _write_arm(tmp_path, "wstar_orbit", ("m0", "m1"), ("m2", "m3"))
        _write_arm(tmp_path, "wl_l1", ("m2", "m3"), ("m0", "m1"))
        loaded = load_arm_matrices(tmp_path, COLLECTION, ["wstar_orbit", "wl_l1"], FROZEN)
        assert common_member_ids(FROZEN, loaded) == ()

    def test_every_member_censored_on_one_arm_empties_the_set(self, tmp_path: Path) -> None:
        _write_arm(tmp_path, "wstar_orbit", (), FROZEN)
        _write_arm(tmp_path, "size_l1", FROZEN, ())
        loaded = load_arm_matrices(tmp_path, COLLECTION, ["wstar_orbit", "size_l1"], FROZEN)
        assert common_member_ids(FROZEN, loaded) == ()

    def test_with_no_arms_loaded_there_is_nothing_to_intersect(self) -> None:
        assert common_member_ids(FROZEN, {}) == FROZEN

    def test_the_input_order_is_preserved(self, tmp_path: Path) -> None:
        _write_arm(tmp_path, "wstar_orbit", ("m3", "m1", "m0"), ("m2",))
        loaded = load_arm_matrices(tmp_path, COLLECTION, ["wstar_orbit"], FROZEN)
        assert common_member_ids(FROZEN, loaded) == ("m0", "m1", "m3")


class TestRq4Census:
    """The label split L15 requires: positives are marginally likelier to censor."""

    @staticmethod
    def _loaded(kept: tuple[str, ...]) -> dict[str, tuple[Any, dict[str, int]]]:
        return {"a": (None, {kb_id: row for row, kb_id in enumerate(kept)})}

    def test_nothing_censored_keeps_every_position(self) -> None:
        census = rq4.common_positions(FROZEN, self._loaded(FROZEN), {0})
        assert census.kept == (0, 1, 2, 3)
        assert census.n_censored == 0
        assert census.rate_anomaly == 0.0
        assert census.rate_clean == 0.0

    def test_a_censored_positive_is_counted_as_one(self) -> None:
        census = rq4.common_positions(FROZEN, self._loaded(("m1", "m2", "m3")), {0})
        assert census.kept == (1, 2, 3)
        assert census.n_censored_anomaly == 1
        assert census.n_censored_clean == 0
        assert census.rate_anomaly == 1.0
        assert census.rate_clean == 0.0

    def test_a_censored_negative_is_counted_as_clean(self) -> None:
        census = rq4.common_positions(FROZEN, self._loaded(("m0", "m1", "m2")), {0})
        assert census.n_censored_anomaly == 0
        assert census.n_censored_clean == 1
        assert census.rate_anomaly == 0.0
        assert census.rate_clean == pytest.approx(1 / 3)

    def test_every_member_censored(self) -> None:
        census = rq4.common_positions(FROZEN, self._loaded(()), {0, 1})
        assert census.kept == ()
        assert census.n_censored == 4
        assert census.n_censored_anomaly == 2
        assert census.n_censored_clean == 2

    def test_no_anomaly_selected_leaves_the_rate_blank(self) -> None:
        census = rq4.common_positions(FROZEN, self._loaded(FROZEN), set())
        assert census.rate_anomaly == ""

    def test_the_row_carries_the_census_columns(self) -> None:
        for column in (
            "n_censored_members",
            "n_censored_anomaly",
            "n_censored_clean",
            "censor_rate_anomaly",
            "censor_rate_clean",
        ):
            assert column in rq4.ROWS_AUC_COLUMNS


class TestRq5Census:
    """Arity-heavy Wikidata types censor more, so the rate is reported per type."""

    def test_nothing_censored_is_zero_everywhere(self) -> None:
        selected = ["Q5", "Q5", "Q11424"]
        assert rq5.censored_by_class(selected, selected) == {"Q5": (0, 0.0), "Q11424": (0, 0.0)}

    def test_the_rate_is_per_type_not_pooled(self) -> None:
        selected = ["Q5", "Q5", "Q5", "Q5", "Q11424", "Q11424"]
        kept = ["Q5", "Q5", "Q5", "Q5", "Q11424"]
        census = rq5.censored_by_class(selected, kept)
        assert census["Q5"] == (0, 0.0)
        assert census["Q11424"] == (1, 0.5)

    def test_a_wholly_censored_type_reports_rate_one(self) -> None:
        census = rq5.censored_by_class(["Q5", "Q11424"], ["Q5"])
        assert census["Q11424"] == (1, 1.0)

    @pytest.mark.parametrize("column", ["n_censored_class", "censor_rate_class"])
    def test_the_per_class_row_carries_the_census(self, column: str) -> None:
        assert column in rq5.ROWS_PER_CLASS_COLUMNS

    def test_the_clustering_and_geometry_rows_carry_the_total(self) -> None:
        assert "n_censored_members" in rq5.ROWS_CLUSTERING_COLUMNS
        assert "n_censored_members" in rq5.ROWS_GEOMETRY_COLUMNS


class TestRq2Census:
    """A false-merge count is comparable only over a shared member set."""

    def test_an_own_collection_is_never_screened(self, tmp_path: Path) -> None:
        got = rq2.census_common_ids(
            tmp_path / "matrices", COLLECTION, ("wstar_orbit",), FROZEN, own=True
        )
        assert got == FROZEN

    def test_no_sidecar_means_the_whole_frozen_order(self, tmp_path: Path) -> None:
        _write_arm(tmp_path, "size_l1", FROZEN, ())
        got = rq2.census_common_ids(
            tmp_path / "matrices", COLLECTION, ("size_l1",), FROZEN, own=False
        )
        assert got == FROZEN

    def test_the_union_of_censorings_is_removed_from_every_arm(self, tmp_path: Path) -> None:
        _write_arm(tmp_path, "wstar_orbit", ("m0", "m1", "m2"), ("m3",))
        _write_arm(tmp_path, "wl_l1", ("m1", "m2", "m3"), ("m0",))
        got = rq2.census_common_ids(
            tmp_path / "matrices", COLLECTION, ("wstar_orbit", "wl_l1"), FROZEN, own=False
        )
        assert got == ("m1", "m2")

    def test_an_arm_absent_from_the_sidecars_does_not_restrict(self, tmp_path: Path) -> None:
        _write_arm(tmp_path, "wstar_orbit", ("m0", "m1", "m2"), ("m3",))
        got = rq2.census_common_ids(
            tmp_path / "matrices", COLLECTION, ("wstar_orbit", "never_built"), FROZEN, own=False
        )
        assert got == ("m0", "m1", "m2")

    def test_every_member_censored_empties_the_set(self, tmp_path: Path) -> None:
        _write_arm(tmp_path, "wstar_orbit", (), FROZEN)
        got = rq2.census_common_ids(
            tmp_path / "matrices", COLLECTION, ("wstar_orbit",), FROZEN, own=False
        )
        assert got == ()

    @pytest.mark.parametrize("column", ["n_requested", "n_censored_arm", "n_censored_common"])
    def test_the_census_row_carries_the_counts(self, column: str) -> None:
        assert column in rq2.COLUMNS_CENSUS
