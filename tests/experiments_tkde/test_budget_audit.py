"""The T-KBf budgeting audit: every in-process Isal engine call is bounded.

Four claims, one class each:

* ``build_matrix_censored`` drops and reports the members a per-member budget
  rejects, instead of letting the whole-matrix build run unbounded (T-KBf B);
* ``rq3.run_guarded`` refuses on a poisoned fork instead of reporting a
  censoring that never ran (T-KBf C);
* ``rq7.run_nscaling`` does the same for its whole-matrix child (T-KBf A);
* ``fact_rank_roles`` is not reachable as a measured arm (T-KBf D).

None of these runs a real canonicalization: the fork-health verdict and the
per-member screen are both injected, which is the point of injecting them.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from experiments.tkde import budget as budget_mod
from experiments.tkde import matrices as mx
from experiments.tkde import rq3, rq5, rq7
from experiments.tkde.budget import TkdeBudgetError
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.metric_space.toolkit.matrix import (
    MatrixCensoring,
    build_matrix,
    build_matrix_censored,
)

pytestmark = pytest.mark.unit

CONFIG_DIR = Path(__file__).resolve().parents[2] / "experiments" / "tkde" / "configs"
ROLES_ARM = "fact_rank_roles"


def _corpus() -> list[SparseHypergraph]:
    """Four small connected hypergraphs of distinct sizes."""
    return [
        SparseHypergraph(3, [frozenset({0, 1}), frozenset({1, 2})]),
        SparseHypergraph(4, [frozenset({0, 1, 2}), frozenset({2, 3})]),
        SparseHypergraph(5, [frozenset({0, 1}), frozenset({1, 2, 3}), frozenset({3, 4})]),
        SparseHypergraph(6, [frozenset({0, 1, 2, 3}), frozenset({3, 4}), frozenset({4, 5})]),
    ]


class TestBuildMatrixCensored:
    """T-KBf (B): the N x N route takes a per-member budget and reports it."""

    def test_unscreened_matches_build_matrix(self) -> None:
        items = _corpus()
        ids = [f"m{i}" for i in range(len(items))]
        expected = build_matrix(items, "size_l1", member_ids=ids, cache_dir=None)

        matrix, censoring = build_matrix_censored(items, "size_l1", member_ids=ids)

        assert censoring == MatrixCensoring(
            member_ids=tuple(ids), censored_ids=(), n_requested=len(items)
        )
        assert censoring.n_censored == 0
        assert censoring.censored_fraction == 0.0
        assert matrix.shape == expected.shape
        assert (matrix == expected).all()

    def test_censored_members_are_dropped_and_reported(self) -> None:
        items = _corpus()
        ids = [f"m{i}" for i in range(len(items))]
        # A synthetic stand-in for the measured hazard: the widest member is the
        # one whose canonicalization does not come back inside the budget.
        screen = lambda H: max(len(e) for _, e, _ in H.iter_edges()) < 4  # noqa: E731

        matrix, censoring = build_matrix_censored(
            items, "size_l1", member_ids=ids, fingerprint_screen=screen
        )

        assert censoring.censored_ids == ("m3",)
        assert censoring.member_ids == ("m0", "m1", "m2")
        assert censoring.n_requested == 4
        assert censoring.n_censored == 1
        assert censoring.censored_fraction == pytest.approx(0.25)
        assert matrix.shape == (3, 3)

    def test_matrix_over_survivors_equals_the_subcorpus_matrix(self) -> None:
        items = _corpus()
        ids = [f"m{i}" for i in range(len(items))]
        keep = [0, 2]
        expected = build_matrix(
            [items[i] for i in keep],
            "size_l1",
            member_ids=[ids[i] for i in keep],
            cache_dir=None,
        )

        matrix, censoring = build_matrix_censored(
            items,
            "size_l1",
            member_ids=ids,
            fingerprint_screen=lambda H: H.n_nodes in (3, 5),
        )

        assert censoring.member_ids == ("m0", "m2")
        assert (matrix == expected).all()

    def test_member_ids_must_correspond(self) -> None:
        from isalhg.errors import MetricSpaceError

        with pytest.raises(MetricSpaceError):
            build_matrix_censored(_corpus(), "size_l1", member_ids=["only-one"])


class TestGuardedBudgetCall:
    """The canary discipline, factored out of ``engine_word`` for reuse."""

    def test_returns_the_value_on_a_healthy_fork(self, monkeypatch: Any) -> None:
        monkeypatch.setattr(budget_mod, "cpp_fork_is_healthy", lambda **_: True)
        assert budget_mod.guarded_budget_call(int, ("17",), 30.0).value == 17

    def test_refuses_on_a_poisoned_fork(self, monkeypatch: Any) -> None:
        monkeypatch.setattr(budget_mod, "cpp_fork_is_healthy", lambda **_: False)
        with pytest.raises(TkdeBudgetError, match="deadlocks"):
            budget_mod.guarded_budget_call(int, ("17",), 30.0)


class TestRq3RunGuarded:
    """T-KBf (C): ``run_guarded`` gained the fork-health canary."""

    def test_ok_path(self, monkeypatch: Any) -> None:
        monkeypatch.setattr(budget_mod, "cpp_fork_is_healthy", lambda **_: True)
        assert rq3.run_guarded(lambda: 41 + 1, 30.0) == ("ok", 42)

    def test_error_path(self, monkeypatch: Any) -> None:
        monkeypatch.setattr(budget_mod, "cpp_fork_is_healthy", lambda **_: True)
        status, message = rq3.run_guarded(_raise, 30.0)
        assert status == "error"
        assert "ValueError" in str(message)

    def test_refuses_instead_of_reporting_a_censoring_that_never_ran(
        self, monkeypatch: Any
    ) -> None:
        monkeypatch.setattr(budget_mod, "cpp_fork_is_healthy", lambda **_: False)
        with pytest.raises(TkdeBudgetError, match="deadlocks"):
            rq3.run_guarded(lambda: 1, 30.0)


def _raise() -> None:
    raise ValueError("consensus blew up")


class _Record:
    def __init__(self, kb_id: str) -> None:
        self.kb_id = kb_id


class _Collection:
    name = "unit_test"

    def __init__(self, n: int) -> None:
        self.records = [_Record(f"m{i}") for i in range(n)]


class TestRq7NScalingGuard:
    """T-KBf (A): the only unbudgeted-in-spirit path of RQ7 now carries the canary."""

    def _ctx(self) -> dict[str, Any]:
        return {
            "collection": _Collection(3),
            "graphs": _corpus()[:3],
            "config": {"nscaling_reps": 1, "nscaling_budget_s": 5.0},
            "stamp": {"rq": 7, "experiment": "envelope", "git_sha": "", "host_cpu": ""},
        }

    def test_refuses_on_a_poisoned_fork(self, monkeypatch: Any) -> None:
        monkeypatch.setattr(budget_mod, "cpp_fork_is_healthy", lambda **_: False)
        unit = rq7.Unit("nscaling", "size_l1-N3", extra={"arm": "size_l1", "N": 3})
        with pytest.raises(TkdeBudgetError, match="deadlocks"):
            rq7.run_nscaling(unit, self._ctx())

    def test_measures_on_a_healthy_fork(self, monkeypatch: Any) -> None:
        monkeypatch.setattr(budget_mod, "cpp_fork_is_healthy", lambda **_: True)
        unit = rq7.Unit("nscaling", "size_l1-N3", extra={"arm": "size_l1", "N": 3})
        rows = rq7.run_nscaling(unit, self._ctx())["nscaling"]
        assert len(rows) == 1
        assert rows[0]["censored"] == 0
        assert rows[0]["error"] == ""


class TestRolesArmIsNotMeasurable:
    """T-KBf (D): ``fact_rank_roles`` fails M0 invariance and may not reach a table."""

    def test_absent_from_the_matrix_specs(self) -> None:
        for specs in (mx.DEFAULT_SPECS, mx.SMOKE_SPECS):
            for collection, arms in specs.items():
                assert ROLES_ARM not in arms, collection

    def test_absent_from_the_rq5_default_arms(self) -> None:
        assert ROLES_ARM not in rq5.DEFAULT_ARMS

    @pytest.mark.parametrize(
        "name", ["matrices.yaml", "rq1.yaml", "rq3.yaml", "rq5.yaml", "rq6.yaml", "rq7.yaml"]
    )
    def test_absent_from_the_shipped_configs(self, name: str) -> None:
        path = CONFIG_DIR / name
        if not path.is_file():
            pytest.skip(f"{name} is not shipped")
        assert ROLES_ARM not in path.read_text(encoding="utf-8")
        # Parsed as well as textually, so a future list built another way is caught.
        assert ROLES_ARM not in _arm_names(yaml.safe_load(path.read_text(encoding="utf-8")))

    def test_the_encoder_itself_is_kept(self) -> None:
        # Only the arm is dropped: the roles word is still the record of what
        # was measured and must stay computable.
        from isalhg.metric_space.registry import get_distance

        assert get_distance(ROLES_ARM).name == ROLES_ARM


def _arm_names(node: Any) -> set[str]:
    """Every string reachable under an ``arms``-like key of a parsed config."""
    found: set[str] = set()
    if isinstance(node, dict):
        for key, value in node.items():
            if isinstance(key, str) and "arms" in key and isinstance(value, list):
                found |= {str(v) for v in value}
            found |= _arm_names(value)
    elif isinstance(node, list):
        for entry in node:
            found |= _arm_names(entry)
    return found
