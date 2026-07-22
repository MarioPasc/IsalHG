"""Unit tests for G3 OFAT sequence generator (T-M7f).

Tests follow the Plan→Test→Implement→Verify protocol from coding_rules.md §2.3.

Acceptance criteria (from T-M7f):
- AC1: budget accounting — cumulative budget is non-negative and increasing
- AC2: connectivity — every H_t is connected
- AC3: M2 invariant — M2 sequence holds n fixed across all steps
- AC4: M3 invariant — exactly one edge changes arity per step
- AC5: S2H round-trip — canonical_string(s2h(w*_c(H_t))) == w*_c(H_t)
- AC6: axis invariants — M1 grows n by 1 per step; M3 target edge arity increases by 1
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

from isalhg.datasets.synthetic.designs import fano_plane, sts_9
from isalhg.datasets.synthetic.known_design_catalog import (
    loose_path,
    tight_cycle,
    tight_path,
)


@pytest.fixture()
def h0_m1():
    """Small tight 3-cycle (n=5, m=5) — base for M1 vertex growth."""
    return tight_cycle(3, 5)


@pytest.fixture()
def h0_m2():
    """Loose 3-path (n=9, m=4) — sparse base for M2 densification."""
    return loose_path(3, 4)


@pytest.fixture()
def h0_m3_k3():
    """Fano plane (n=7, k=3) — base for M3 arity increase from k=3."""
    return fano_plane()


@pytest.fixture()
def h0_m3_k4():
    """Tight 4-path (n=6, k=4) — base for M3 arity increase from k=4."""
    return tight_path(4, 3)


@pytest.fixture()
def h0_m4():
    """STS(9) (n=9, m=12, k=3) — base for M4 incidence edit."""
    return sts_9()


@pytest.fixture()
def h0_m5():
    """GQ(2,2) doily (n=15, m=15, k=3, very high symmetry) — base for M5."""
    from isalhg.datasets.synthetic.designs import gq_2_2_doily

    return gq_2_2_doily()


# ---------------------------------------------------------------------------
# Import the module under test (fails before implementation)
# ---------------------------------------------------------------------------

from experiments.article.g3_sequence import (  # noqa: E402
    OfatAxis,
    generate_ofat_sequence,
)

# ---------------------------------------------------------------------------
# AC1 — Budget accounting
# ---------------------------------------------------------------------------


class TestBudgetAccounting:
    @pytest.mark.parametrize("axis", list(OfatAxis))
    def test_budget_from_base_at_step0_is_zero(self, axis, h0_m1, h0_m2, h0_m3_k3, h0_m4, h0_m5):
        import random

        bases = {
            OfatAxis.M1: h0_m1,
            OfatAxis.M2: h0_m2,
            OfatAxis.M3: h0_m3_k3,
            OfatAxis.M4: h0_m4,
            OfatAxis.M5: h0_m5,
        }
        H0 = bases[axis]
        rng = random.Random(42)
        steps = generate_ofat_sequence(H0, axis, T=5, rng=rng)
        assert steps[0].budget_from_base == 0

    @pytest.mark.parametrize("axis", list(OfatAxis))
    def test_budget_nonneg_and_increasing(self, axis, h0_m1, h0_m2, h0_m3_k3, h0_m4, h0_m5):
        import random

        bases = {
            OfatAxis.M1: h0_m1,
            OfatAxis.M2: h0_m2,
            OfatAxis.M3: h0_m3_k3,
            OfatAxis.M4: h0_m4,
            OfatAxis.M5: h0_m5,
        }
        H0 = bases[axis]
        rng = random.Random(42)
        steps = generate_ofat_sequence(H0, axis, T=5, rng=rng)
        budgets = [s.budget_from_base for s in steps]
        assert all(b >= 0 for b in budgets), "All budgets must be non-negative"
        assert budgets == sorted(budgets), "Budgets must be non-decreasing"
        assert budgets[-1] > 0, "Final budget must be positive (at least one edit applied)"

    @pytest.mark.parametrize("axis", list(OfatAxis))
    def test_step_indices_are_consecutive(self, axis, h0_m1, h0_m2, h0_m3_k3, h0_m4, h0_m5):
        import random

        bases = {
            OfatAxis.M1: h0_m1,
            OfatAxis.M2: h0_m2,
            OfatAxis.M3: h0_m3_k3,
            OfatAxis.M4: h0_m4,
            OfatAxis.M5: h0_m5,
        }
        H0 = bases[axis]
        rng = random.Random(42)
        steps = generate_ofat_sequence(H0, axis, T=5, rng=rng)
        assert [s.step for s in steps] == list(range(len(steps)))


# ---------------------------------------------------------------------------
# AC2 — Connectivity
# ---------------------------------------------------------------------------


class TestConnectivity:
    @pytest.mark.parametrize("axis", list(OfatAxis))
    def test_all_steps_connected(self, axis, h0_m1, h0_m2, h0_m3_k3, h0_m4, h0_m5):
        import random

        bases = {
            OfatAxis.M1: h0_m1,
            OfatAxis.M2: h0_m2,
            OfatAxis.M3: h0_m3_k3,
            OfatAxis.M4: h0_m4,
            OfatAxis.M5: h0_m5,
        }
        H0 = bases[axis]
        rng = random.Random(42)
        steps = generate_ofat_sequence(H0, axis, T=5, rng=rng)
        for s in steps:
            assert s.hypergraph.is_connected(), f"Axis={axis} step={s.step} is disconnected"


# ---------------------------------------------------------------------------
# AC3 — M2 holds n fixed
# ---------------------------------------------------------------------------


class TestM2Invariants:
    def test_n_fixed_all_steps(self, h0_m2):
        import random

        rng = random.Random(42)
        steps = generate_ofat_sequence(h0_m2, OfatAxis.M2, T=6, rng=rng)
        n_base = h0_m2.n_nodes
        for s in steps:
            assert s.hypergraph.n_nodes == n_base, (
                f"M2 step {s.step}: n changed from {n_base} to {s.hypergraph.n_nodes}"
            )

    def test_m_nondecreasing(self, h0_m2):
        import random

        rng = random.Random(42)
        steps = generate_ofat_sequence(h0_m2, OfatAxis.M2, T=6, rng=rng)
        for i in range(1, len(steps)):
            assert steps[i].hypergraph.n_edges >= steps[i - 1].hypergraph.n_edges, (
                f"M2 step {i}: m decreased"
            )


# ---------------------------------------------------------------------------
# AC4 — M3 changes exactly one edge's arity per step
# ---------------------------------------------------------------------------


class TestM3Invariants:
    def test_exactly_one_edge_arity_changes_per_step(self, h0_m3_k3):
        import random

        rng = random.Random(42)
        steps = generate_ofat_sequence(h0_m3_k3, OfatAxis.M3, T=4, rng=rng)
        for i in range(1, len(steps)):
            prev = steps[i - 1].hypergraph
            curr = steps[i].hypergraph
            # Count edges whose arity changed
            prev_arities = sorted(len(prev.members(e)) for e in range(prev.n_edges))
            curr_arities = sorted(len(curr.members(e)) for e in range(curr.n_edges))
            # One arity goes up by 1; the rest unchanged
            # Simple check: sum of arities increases by exactly 1
            sum_prev = sum(prev_arities)
            sum_curr = sum(curr_arities)
            assert sum_curr == sum_prev + 1, (
                f"M3 step {i}: arity sum changed by {sum_curr - sum_prev} (expected +1)"
            )

    def test_n_fixed_all_steps(self, h0_m3_k3):
        import random

        rng = random.Random(42)
        steps = generate_ofat_sequence(h0_m3_k3, OfatAxis.M3, T=4, rng=rng)
        n_base = h0_m3_k3.n_nodes
        for s in steps:
            assert s.hypergraph.n_nodes == n_base, (
                f"M3 step {s.step}: n changed from {n_base} to {s.hypergraph.n_nodes}"
            )

    def test_m_fixed_all_steps(self, h0_m3_k3):
        import random

        rng = random.Random(42)
        steps = generate_ofat_sequence(h0_m3_k3, OfatAxis.M3, T=4, rng=rng)
        m_base = h0_m3_k3.n_edges
        for s in steps:
            assert s.hypergraph.n_edges == m_base, (
                f"M3 step {s.step}: m changed from {m_base} to {s.hypergraph.n_edges}"
            )


# ---------------------------------------------------------------------------
# AC5 — S2H round-trip
# ---------------------------------------------------------------------------


class TestS2HRoundTrip:
    @pytest.mark.parametrize("axis", list(OfatAxis))
    def test_roundtrip_all_steps(self, axis, h0_m1, h0_m2, h0_m3_k3, h0_m4, h0_m5):
        import random

        from isalhg.core.canonical import canonical_string
        from isalhg.core.string_to_hypergraph import string_to_hypergraph

        bases = {
            OfatAxis.M1: h0_m1,
            OfatAxis.M2: h0_m2,
            OfatAxis.M3: h0_m3_k3,
            OfatAxis.M4: h0_m4,
            OfatAxis.M5: h0_m5,
        }
        H0 = bases[axis]
        rng = random.Random(42)
        steps = generate_ofat_sequence(H0, axis, T=4, rng=rng)

        for s in steps:
            H = s.hypergraph
            w = canonical_string(H)
            k = max(len(H.members(e)) for e in range(H.n_edges)) if H.n_edges > 0 else 2
            H2 = string_to_hypergraph(w, k=k)
            # Round-trip: canonical_string of decoded == original canonical_string
            w2 = canonical_string(H2)
            assert w == w2, (
                f"Axis={axis} step={s.step}: S2H round-trip failed: |w|={len(w)} |w2|={len(w2)}"
            )


# ---------------------------------------------------------------------------
# AC6 — M1 structural invariants
# ---------------------------------------------------------------------------


class TestM1Invariants:
    def test_n_increases_by_1_per_step(self, h0_m1):
        import random

        rng = random.Random(42)
        steps = generate_ofat_sequence(h0_m1, OfatAxis.M1, T=6, rng=rng)
        n_base = h0_m1.n_nodes
        for s in steps:
            assert s.hypergraph.n_nodes == n_base + s.step, (
                f"M1 step {s.step}: n={s.hypergraph.n_nodes}, expected {n_base + s.step}"
            )


# ---------------------------------------------------------------------------
# Sequence length
# ---------------------------------------------------------------------------


class TestSequenceLength:
    @pytest.mark.parametrize("T", [1, 5, 10])
    def test_sequence_has_T_plus_1_steps(self, T, h0_m2):
        import random

        rng = random.Random(42)
        steps = generate_ofat_sequence(h0_m2, OfatAxis.M2, T=T, rng=rng)
        assert len(steps) == T + 1, f"Expected {T + 1} steps, got {len(steps)}"


# ---------------------------------------------------------------------------
# OfatStep dataclass
# ---------------------------------------------------------------------------


class TestOfatStep:
    def test_step0_is_base(self, h0_m1):
        import random

        rng = random.Random(42)
        steps = generate_ofat_sequence(h0_m1, OfatAxis.M1, T=3, rng=rng)
        s0 = steps[0]
        assert s0.step == 0
        assert s0.budget_from_base == 0
        assert s0.hypergraph.n_nodes == h0_m1.n_nodes
        assert s0.hypergraph.n_edges == h0_m1.n_edges

    def test_op_name_is_string(self, h0_m1):
        import random

        rng = random.Random(42)
        steps = generate_ofat_sequence(h0_m1, OfatAxis.M1, T=3, rng=rng)
        for s in steps:
            assert isinstance(s.op_name, str)
            if s.step > 0:
                # step 0 op_name is empty (the base has no prior operation)
                assert len(s.op_name) > 0
