"""RQ2's own-collection build must be screened, like every other unbounded build.

``census_own_collections`` makes RQ2 compute ``ndc_substances`` itself instead of
reading it from the matrices job. That collection is the campaign's most
arity-heavy -- 139 facts of arity 10, 127 of arity 9, 228 of arity 8, 227 of
arity 7 -- and arity-driven displacement enumeration is exactly what the
``wstar_orbit`` residual tail is made of. An unscreened, in-process build there
hangs the census and poisons the runner for every arm after it.

Found by the D-KBf2 consumer agent as its highest residual risk; these tests pin
the fix rather than the report.
"""

from __future__ import annotations

import inspect

import pytest

from experiments.tkde import matrices as mx
from experiments.tkde import rq2

pytestmark = pytest.mark.unit


class TestOwnBuildIsBudgeted:
    def test_matrix_for_accepts_a_screen_budget(self) -> None:
        assert "arm_budget_s" in inspect.signature(rq2.matrix_for).parameters

    def test_the_unbounded_arms_are_the_ones_screened(self) -> None:
        """The screen keys off the same set the matrices job uses, not a local list."""
        assert "wstar_orbit" in mx.BUDGETED_MATRIX_ARMS
        assert rq2.POINTER_ARMS.issuperset({"wstar_orbit", "isalhg_levenshtein"})

    def test_the_own_path_routes_through_the_shared_builder(self) -> None:
        """One entry point for building a budgeted matrix, so one process model."""
        source = inspect.getsource(rq2.matrix_for)
        assert "build_budgeted_matrix" in source
        # The unscreened build must remain reachable only below the budgeted branch.
        assert source.index("build_budgeted_matrix") < source.index("matrix = build_matrix(")

    def test_the_shared_builder_is_public_and_forks_non_daemonically(self) -> None:
        """T-KBi's rule: no private cross-module import for a shared mechanism."""
        assert callable(mx.build_budgeted_matrix)
        assert not mx.build_budgeted_matrix.__name__.startswith("_")
        assert "daemon=False" in inspect.getsource(mx.build_budgeted_matrix)

    def test_budget_is_required_not_defaulted(self) -> None:
        """A caller must say what the budget is; silently defaulting hides a hang."""
        budget = inspect.signature(mx.build_budgeted_matrix).parameters["budget_s"]
        assert budget.default is inspect.Parameter.empty
        assert budget.kind is inspect.Parameter.KEYWORD_ONLY

    def test_it_actually_runs(self, tmp_path) -> None:
        """Call it, do not merely inspect it.

        The inspection tests above all passed while the function carried an
        undefined ``guarded_budget_call`` -- the formatter had dropped the import
        when an intermediate edit left it briefly unused. Only a real call
        catches that, so this builds a two-member matrix end to end.
        """
        pytest.importorskip("numpy")
        from isalhg.core.sparse_hypergraph import SparseHypergraph

        items = [
            SparseHypergraph(n_nodes=4, hyperedges=[frozenset({0, 1}), frozenset({1, 2, 3})]),
            SparseHypergraph(n_nodes=3, hyperedges=[frozenset({0, 1}), frozenset({1, 2})]),
        ]
        ids = ["a", "b"]
        cache_dir = mx.collection_cache_dir(tmp_path, "probe")
        cache_dir.mkdir(parents=True)
        kept, censored = mx.build_budgeted_matrix(
            items, ids, None, "wstar_orbit", cache_dir, budget_s=60.0, label="probe/wstar_orbit"
        )
        assert kept == ("a", "b")
        assert censored == ()
        matrix, kept_ids, censored_ids = mx.load_cached_matrix_censored(
            tmp_path, "probe", "wstar_orbit", ids
        )
        assert matrix.shape == (2, 2)
        assert kept_ids == ("a", "b")
        assert censored_ids == ()
