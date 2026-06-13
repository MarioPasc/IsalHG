"""Unit tests for :mod:`experiments.orchestrator` helpers.

Targets the helpers that the integration test cannot reach directly:
the stable cell hash and its normalisation against tuple/list /
set-vs-sorted-list distinctions.
"""

from __future__ import annotations

import pytest

from experiments.orchestrator import _cell_filename, _normalise_for_hash
from experiments.schemas import CellSpec

pytestmark = pytest.mark.unit


class TestCellHashNormalisation:
    def test_tuple_and_list_dataset_params_hash_equal(self) -> None:
        a = CellSpec(
            protocol="pairwise_iso",
            backend="isalhg",
            dataset="exhaustive_small",
            seed=0,
            dataset_params={"n_range": (3, 4), "arity_range": (2, 3)},
        )
        b = CellSpec(
            protocol="pairwise_iso",
            backend="isalhg",
            dataset="exhaustive_small",
            seed=0,
            dataset_params={"n_range": [3, 4], "arity_range": [2, 3]},
        )
        assert _cell_filename(a) == _cell_filename(b)

    def test_set_and_sorted_list_hash_equal(self) -> None:
        a = CellSpec(
            protocol="pairwise_iso",
            backend="isalhg",
            dataset="exhaustive_small",
            seed=0,
            backend_params={"hot_classes": {7, 3, 1}},
        )
        b = CellSpec(
            protocol="pairwise_iso",
            backend="isalhg",
            dataset="exhaustive_small",
            seed=0,
            backend_params={"hot_classes": [1, 3, 7]},
        )
        assert _cell_filename(a) == _cell_filename(b)

    def test_distinct_cells_get_distinct_filenames(self) -> None:
        a = CellSpec(
            protocol="pairwise_iso",
            backend="isalhg",
            dataset="exhaustive_small",
            seed=0,
            dataset_params={"n_range": [3, 4]},
        )
        b = CellSpec(
            protocol="pairwise_iso",
            backend="isalhg",
            dataset="exhaustive_small",
            seed=0,
            dataset_params={"n_range": [3, 5]},
        )
        assert _cell_filename(a) != _cell_filename(b)

    def test_normalise_idempotent(self) -> None:
        payload = {
            "x": (1, 2, 3),
            "y": [4, 5],
            "z": {"deep": (6, [7, 8])},
        }
        once = _normalise_for_hash(payload)
        twice = _normalise_for_hash(once)
        assert once == twice
