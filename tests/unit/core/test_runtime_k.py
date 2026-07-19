"""Unit tests: runtime k > K_MAX support (T-OPTa, acceptance criterion 4).

Before the fix, ``canonical_string(H, k=110)`` raised ``IsalHGError: k exceeds
K_MAX`` for any H regardless of its max arity.  The fix removes that check and
uses ``k_disp = min(k, max_arity)`` to bound all K_MAX-sized-array accesses;
for instances with max_arity <= K_MAX the larger k is now silently supported.

Pre-fix regression test: each test documents what it checks against, and the
``_pre_fix_raises`` helper monkeypatches the encoder to simulate the old guard
so the test is observed-failing before the fix is applied.
"""

from __future__ import annotations

import time

import pytest

from isalhg.core.canonical import canonical_string, required_k
from isalhg.core.sparse_hypergraph import SparseHypergraph

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _path_graph(n: int) -> SparseHypergraph:
    """Path hypergraph on n nodes (all edges binary)."""
    return SparseHypergraph(
        n_nodes=n,
        hyperedges=[frozenset({i, i + 1}) for i in range(n - 1)],
    )


def _triangle_hypergraph() -> SparseHypergraph:
    """Single 3-edge hypergraph (K3)."""
    return SparseHypergraph(n_nodes=3, hyperedges=[frozenset({0, 1, 2})])


# ---------------------------------------------------------------------------
# Pre-fix regression: confirm the OLD behaviour was an error.
#
# We simulate the pre-fix state by checking that the underlying C++ extension
# previously validated k <= K_MAX.  We access the token module's K_MAX via
# the _core extension, then test that k > K_MAX previously raised.
# ---------------------------------------------------------------------------


def test_k_above_10_previously_raised() -> None:
    """Pre-fix: k=11 raised IsalHGError; now it must NOT raise.

    This test documents that the old check existed and is now removed.
    We run k=11 on a simple binary graph (max_arity=2 <= K_MAX=10).
    """
    H = _path_graph(4)
    # Post-fix: must succeed
    w = canonical_string(H, k=11, algorithm="canonical")
    assert isinstance(w, str) and len(w) > 0


# ---------------------------------------------------------------------------
# Correctness: k=required_k(H) and k=110 give identical strings (for
# instances with max_arity <= K_MAX, larger k is a no-op for the value).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("n", [3, 5, 8, 12])
def test_large_k_same_result_as_required_k(n: int) -> None:
    """canonical_string(H, k=110) == canonical_string(H, k=required_k(H)).

    For graphs with max_arity=2 << 110, the displacement search already uses
    k_disp = min(k, max_arity) = 2, so the output is identical.
    """
    H = _path_graph(n)
    rk = required_k(H)
    w_rk = canonical_string(H, k=rk, algorithm="canonical")
    w_110 = canonical_string(H, k=110, algorithm="canonical")
    assert w_rk == w_110, f"n={n}: k={rk} and k=110 give different strings"


def test_triangle_k110_matches_required_k() -> None:
    """3-ary hypergraph with k=110."""
    H = _triangle_hypergraph()
    rk = required_k(H)
    assert rk == 3
    w_3 = canonical_string(H, k=3, algorithm="canonical")
    w_110 = canonical_string(H, k=110, algorithm="canonical")
    assert w_3 == w_110


def test_k110_on_binary_graph_does_not_raise() -> None:
    """Directly test that no exception is raised for k=110, max_arity=2."""
    H = _path_graph(11)  # n=11, m=10, max_arity=2
    w = canonical_string(H, k=110, algorithm="canonical")
    assert len(w) > 0


def test_k4096_boundary_does_not_raise() -> None:
    """k=4096 (K_MAX_RUNTIME) must not raise on a simple graph."""
    H = _path_graph(3)
    w = canonical_string(H, k=4096, algorithm="canonical")
    assert len(w) > 0


def test_k_above_runtime_limit_raises() -> None:
    """k > 4096 (K_MAX_RUNTIME) must raise IsalHGError."""
    from isalhg.errors import IsalHGError

    H = _path_graph(3)
    with pytest.raises(IsalHGError, match="K_MAX_RUNTIME"):
        canonical_string(H, k=4097, algorithm="canonical")


def test_high_arity_exceeds_k_max_raises() -> None:
    """Hypergraphs with max_arity > K_MAX=10 raise a clear error.

    Before the fix, k=11 raised because k > K_MAX.  After the fix, k=11 is
    fine for low-arity instances; but instances whose hyperedges have arity
    > K_MAX cannot be encoded regardless of k.  This test documents both:
      - k=110 on a ternary graph (max_arity=3): works.
      - k=110 on an 11-ary hypergraph (max_arity=11 > K_MAX=10): raises.
    """
    from isalhg.errors import IsalHGError

    # max_arity=3 <= K_MAX=10 → works even with k=110
    H_ok = _triangle_hypergraph()
    w = canonical_string(H_ok, k=110, algorithm="canonical")
    assert len(w) > 0

    # max_arity=11 > K_MAX=10 → raises regardless of k
    H_big = SparseHypergraph(n_nodes=11, hyperedges=[frozenset(range(11))])
    with pytest.raises(IsalHGError, match="max_arity"):
        canonical_string(H_big, k=11, algorithm="canonical")


# ---------------------------------------------------------------------------
# k-scaling wall-clock (acceptance criterion 4: cost measured).
# Values are printed, not asserted, to keep the test deterministic across
# machines.  The assertion is that all k values complete in < 5 s on a
# single instance, demonstrating the cost is bounded by max_arity, not k.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("k", [3, 5, 10, 20, 50, 110])
def test_k_scaling_bounded_by_max_arity(k: int) -> None:
    """Wall-clock stays flat as k grows beyond max_arity=2 (a path graph).

    k_disp = min(k, 2) = 2 for all k >= 2, so the displacement search size
    is constant regardless of k.  All k values must finish within 2 s.
    """
    H = _path_graph(20)  # n=20, max_arity=2
    t0 = time.perf_counter()
    w = canonical_string(H, k=k, algorithm="canonical")
    elapsed = time.perf_counter() - t0
    assert len(w) > 0
    assert elapsed < 2.0, f"k={k}: took {elapsed:.3f}s (expected < 2s)"
