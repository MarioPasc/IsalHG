"""Unit tests for ``isalhg.core.algorithms.registry``."""

from __future__ import annotations

import pytest

from isalhg.core.algorithms.base import H2SAlgorithm
from isalhg.core.algorithms.registry import (
    AlgorithmFactory,
    available_algorithms,
    get_algorithm,
    register_algorithm,
)
from isalhg.errors import AlgorithmUnavailableError

pytestmark = pytest.mark.unit


_EXPECTED_NAMES = (
    "exhaustive",
    "greedy_min",
    "greedy_min_inplace",
    "greedy_min_inplace_wl_pruned",
    "greedy_min_wl_pruned",
    "greedy_single",
    "pruned_exhaustive",
)


def test_available_algorithms_lists_all_registered_names() -> None:
    names = available_algorithms()
    for expected in _EXPECTED_NAMES:
        assert expected in names, f"{expected!r} missing from {names}"


def test_get_algorithm_greedy_min_returns_instance() -> None:
    algo = get_algorithm("greedy_min", k=3)
    assert isinstance(algo, H2SAlgorithm)
    assert algo.name == "greedy_min"


def test_get_algorithm_unknown_raises() -> None:
    with pytest.raises(AlgorithmUnavailableError):
        get_algorithm("does_not_exist", k=3)


def test_register_algorithm_duplicate_raises() -> None:
    factory: AlgorithmFactory = lambda k, d: get_algorithm("greedy_min", k=k, structural_depth=d)
    with pytest.raises(ValueError, match="already registered"):
        register_algorithm("greedy_min", factory)
