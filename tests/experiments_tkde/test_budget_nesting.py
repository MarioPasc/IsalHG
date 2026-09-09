"""A budgeted call whose child budgets something of its own.

The matrices job nests two budgets: the unit runs in a forked child so the
build's in-process canonicalization cannot poison the runner, and inside that
child ``build_matrix_censored`` forks one screen per member. Python forbids a
daemonic process from having children, so the outer child must be non-daemonic
or the unit dies on its first screen.

Job 2264827 died exactly there, in five seconds, on ``wd50k66/wstar_orbit`` --
the first budgeted arm ever to reach ``DEFAULT_SPECS``. Wave 6 unit-tested both
budget levels in isolation and never their composition, which is the only place
the defect exists.
"""

from __future__ import annotations

import pytest

from experiments.tkde.budget import guarded_budget_call, run_with_budget_detail

pytestmark = pytest.mark.unit


def _leaf() -> str:
    return "leaf"


def _supervisor() -> list[str]:
    """A callable that itself budgets two children -- the matrices unit's shape."""
    return [
        guarded_budget_call(_leaf, (), 10.0, cpp_engine=False).value,
        guarded_budget_call(_leaf, (), 10.0, cpp_engine=False).value,
    ]


class TestNestedBudgets:
    def test_a_daemonic_child_cannot_budget_its_own_children(self) -> None:
        """The defect, pinned as behaviour rather than as a comment."""
        result = guarded_budget_call(_supervisor, (), 30.0, cpp_engine=False, daemon=True)
        assert not result.ok
        assert not result.censored, "this is an error, not a time-out"
        assert "daemonic" in str(result.error)

    def test_a_non_daemonic_child_may_budget_its_own_children(self) -> None:
        result = guarded_budget_call(_supervisor, (), 30.0, cpp_engine=False, daemon=False)
        assert result.ok, result.error
        assert result.value == ["leaf", "leaf"]

    def test_the_default_stays_daemonic(self) -> None:
        """Leaf children keep dying with their parent; only supervisors opt out."""
        result = run_with_budget_detail(_leaf, (), 10.0)
        assert result.ok
        assert result.value == "leaf"

    @pytest.mark.parametrize("daemon", [True, False])
    def test_the_budget_still_censors_either_way(self, daemon: bool) -> None:
        """Opting out of daemon must not weaken the time-out."""
        result = run_with_budget_detail(_sleep_forever, (), 0.5, daemon=daemon)
        assert result.censored
        assert not result.ok


def _sleep_forever() -> None:
    import time

    time.sleep(3600)
