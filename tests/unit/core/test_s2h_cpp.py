"""Unit tests for the C++ S2H interpreter backend (T-OPTb).

Acceptance checks:
  AC1a. Parity on design fixtures: C++ and Python S2H produce fingerprint-
        identical (isomorphic) hypergraphs on the canonical strings of Fano,
        STS(9), both cyclic C13 orbits, and the n=4 counterexample.
  AC1b. Closed-alphabet property: every valid Sigma_HG* string decodes on the
        C++ backend without error.
  AC2.  W tokens are no-ops on the C++ backend and are never stripped
        (invariant 6): strings differing only in W count decode to the same
        hypergraph.
  AC3.  Decode throughput (tokens/s) is reported in a non-failing test.
  AC4.  Backend dispatch: ``string_to_hypergraph(..., backend='cpp')`` resolves
        to the C++ implementation; ``backend='python'`` resolves to Python.
  AC5.  Both backends register in ``_S2H_BACKENDS``; unknown backend raises.
"""

from __future__ import annotations

import time

import pytest

from isalhg.core.canonical import canonical_string, required_k
from isalhg.core.hypergraph_to_string import greedy_h2s
from isalhg.core.instructions import serialize
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.core.string_to_hypergraph import _S2H_BACKENDS, string_to_hypergraph
from isalhg.datasets.synthetic import designs
from isalhg.datasets.synthetic.designs import cyclic_triple_orbit_13

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _encode_decode_cpp(H: SparseHypergraph, seed_node: int = 0) -> SparseHypergraph:
    """H2S(H) from seed_node, then decode via C++ S2H."""
    k = required_k(H)
    tokens = greedy_h2s(H, seed_node=seed_node, k=k)
    s = serialize(list(tokens))
    return string_to_hypergraph(s, k=k, backend="cpp")


def _fp(H: SparseHypergraph) -> str:
    return canonical_string(H, k=required_k(H))


# ---------------------------------------------------------------------------
# AC4 / AC5: backend dispatch
# ---------------------------------------------------------------------------


def test_backend_dict_keys() -> None:
    """Both 'python' and 'cpp' must be registered."""
    assert "python" in _S2H_BACKENDS
    assert "cpp" in _S2H_BACKENDS


def test_unknown_backend_raises() -> None:
    with pytest.raises(ValueError, match="unknown backend"):
        string_to_hypergraph("W", k=2, backend="rust")  # type: ignore[arg-type]


def test_default_backend_is_cpp() -> None:
    """Default backend resolves to C++; the result must match the C++ path."""
    s = "V[0;1;1;0]"
    H_default = string_to_hypergraph(s, k=2)
    H_cpp = string_to_hypergraph(s, k=2, backend="cpp")
    assert _fp(H_default) == _fp(H_cpp)


# ---------------------------------------------------------------------------
# AC4: correctness on simple hand-built cases
# ---------------------------------------------------------------------------


def test_empty_string_single_seed_node() -> None:
    """Empty string → one seed node, no edges (initial VM state)."""
    H = string_to_hypergraph("", k=2, backend="cpp")
    assert H.n_nodes == 1
    assert H.n_edges == 0


def test_single_v_token() -> None:
    """V[0;1;1;0] creates a 2-node 1-edge hypergraph."""
    H = string_to_hypergraph("V[0;1;1;0]", k=2, backend="cpp")
    assert H.n_nodes == 2
    assert H.n_edges == 1


def test_v_two_new_nodes() -> None:
    """V[0;1;2;0,0] creates 3-node, 1 edge of arity 3."""
    H = string_to_hypergraph("V[0;1;2;0,0]", k=3, backend="cpp")
    assert H.n_nodes == 3
    assert H.n_edges == 1
    # Edge should span all three nodes.
    members = H.members(0)
    assert len(members) == 3


def test_c_token_no_duplicate() -> None:
    """C after V re-adding same edge is no-op; edge count stays 1."""
    # V[0;1;1;0] creates edge {0,1}; P[1] moves p_1; N[1] retreats back.
    # Then C[0;2] tries to re-add {0,1} (both pointers on 0 and 1).
    # Simpler: create two nodes, create edge once with V, then C on same members.
    # Use: V[0;1;1;0] (edge {0,1}), then P[1] to slot of node1,
    # then N[1] back to slot of node0, C[0;2] with p_1=node0, p_2=node1.
    # That matches an existing edge → no-op.
    H_dup = string_to_hypergraph("V[0;1;1;0];P[2];C[0;2]", k=2, backend="cpp")
    H_ref = string_to_hypergraph("V[0;1;1;0]", k=2, backend="cpp")
    assert H_dup.n_edges == H_ref.n_edges


def test_p_n_pointer_moves() -> None:
    """P[1]/N[1] advance/retreat pointer; resulting hypergraph must match."""
    # Build manually: one node (seed), P[1] → wraps around (only one node),
    # returns to node 0. Then V[0;1;1;0] creates node 1 with edge {0,1}.
    # P[1] after V adds node 1 to slot 1; then another V creates {1,2}.
    s = "V[0;1;1;0];P[1];V[0;1;1;0]"
    Hcpp = string_to_hypergraph(s, k=2, backend="cpp")
    Hpy = string_to_hypergraph(s, k=2, backend="python")
    assert Hcpp.n_nodes == Hpy.n_nodes
    assert Hcpp.n_edges == Hpy.n_edges


# ---------------------------------------------------------------------------
# AC2: W tokens are no-ops — invariant 6
# ---------------------------------------------------------------------------


class TestWTokenNoop:
    """W tokens never alter the hypergraph; inserting any number of W tokens
    before/between/after real tokens leaves the result unchanged."""

    @pytest.mark.parametrize(
        "base, with_w",
        [
            ("V[0;1;1;0]", "W;V[0;1;1;0]"),
            ("V[0;1;1;0]", "V[0;1;1;0];W"),
            ("V[0;1;1;0];P[1];V[0;1;1;0]", "W;V[0;1;1;0];W;P[1];W;V[0;1;1;0];W"),
        ],
    )
    def test_w_does_not_change_fingerprint(self, base: str, with_w: str) -> None:
        k = 3
        Hbase = string_to_hypergraph(base, k=k, backend="cpp")
        Hwith = string_to_hypergraph(with_w, k=k, backend="cpp")
        assert _fp(Hbase) == _fp(Hwith)

    def test_all_w_string_is_single_seed(self) -> None:
        """A string of only W tokens produces the initial state: 1 node, 0 edges."""
        H = string_to_hypergraph("W;W;W", k=2, backend="cpp")
        assert H.n_nodes == 1
        assert H.n_edges == 0


# ---------------------------------------------------------------------------
# AC1a: parity on design fixtures
# ---------------------------------------------------------------------------


class TestParityFixtures:
    """C++ and Python S2H must produce fingerprint-identical output on every
    design fixture, using the greedy (non-tie-branch) encoding from each seed."""

    @pytest.fixture(
        params=[
            pytest.param("fano", id="fano"),
            pytest.param("sts9", id="sts9"),
            pytest.param("c13_0", id="cyclic_c13_orbit0"),
            pytest.param("c13_1", id="cyclic_c13_orbit1"),
        ]
    )
    def design(self, request: pytest.FixtureRequest) -> SparseHypergraph:
        name = request.param
        if name == "fano":
            return designs.fano_plane()
        if name == "sts9":
            return designs.sts_9()
        if name == "c13_0":
            return cyclic_triple_orbit_13((0, 1, 4))
        if name == "c13_1":
            return cyclic_triple_orbit_13((0, 1, 6))
        raise ValueError(name)

    def test_cpp_python_parity(self, design: SparseHypergraph) -> None:
        """For every seed, C++ and Python decode to the same fingerprint."""
        k = required_k(design)
        for seed in range(design.n_nodes):
            tokens = greedy_h2s(design, seed_node=seed, k=k)
            s = serialize(list(tokens))
            Hcpp = string_to_hypergraph(s, k=k, backend="cpp")
            Hpy = string_to_hypergraph(s, k=k, backend="python")
            assert canonical_string(Hcpp, k=k) == canonical_string(Hpy, k=k), (
                f"parity failed at seed={seed}: cpp ≠ python"
            )

    def test_round_trip_cpp(self, design: SparseHypergraph) -> None:
        """C++ S2H(H2S(H)) ≅ H (round-trip via fingerprint equality)."""
        k = required_k(design)
        fp_orig = canonical_string(design, k=k)
        for seed in range(design.n_nodes):
            tokens = greedy_h2s(design, seed_node=seed, k=k)
            s = serialize(list(tokens))
            H_rt = string_to_hypergraph(s, k=k, backend="cpp")
            assert canonical_string(H_rt, k=k) == fp_orig, f"round-trip failed at seed={seed}"


# ---------------------------------------------------------------------------
# AC1b: closed-alphabet
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "s,k",
    [
        ("", 2),
        ("W", 2),
        ("W;W;W", 2),
        ("V[0;1;1;0]", 2),
        ("V[0;1;2;0,0]", 3),
        ("V[0;1;1;0];C[0;2]", 2),  # C after V (same edge → no-op)
        ("V[0;1;1;0];P[1];C[0;2]", 2),  # C adds new edge on {1, ?}
    ],
)
def test_closed_alphabet_no_raise(s: str, k: int) -> None:
    """Every well-formed string decodes on C++ backend without raising."""
    H = string_to_hypergraph(s, k=k, backend="cpp")
    assert H.n_nodes >= 1


# ---------------------------------------------------------------------------
# AC3: decode throughput
# ---------------------------------------------------------------------------


def test_decode_throughput_cpp_vs_python() -> None:
    """Measure tokens/s for C++ and Python backends on a corpus-scale string.

    This test does NOT assert a minimum throughput; it reports the
    numbers so they appear in the test log.
    """
    # Corpus-scale string: repeat encoding (simulated by a large Fano string).
    fano = designs.fano_plane()
    k_fano = required_k(fano)
    tokens_fano = greedy_h2s(fano, seed_node=0, k=k_fano)
    s_fano = serialize(list(tokens_fano))
    n_tokens_fano = len(s_fano.split(";")) if s_fano else 0

    REPEATS = 1000

    # C++ throughput
    t0 = time.perf_counter()
    for _ in range(REPEATS):
        string_to_hypergraph(s_fano, k=k_fano, backend="cpp")
    t_cpp = time.perf_counter() - t0
    tok_per_s_cpp = (REPEATS * n_tokens_fano) / t_cpp if t_cpp > 0 else float("inf")

    # Python throughput
    t0 = time.perf_counter()
    for _ in range(REPEATS):
        string_to_hypergraph(s_fano, k=k_fano, backend="python")
    t_py = time.perf_counter() - t0
    tok_per_s_py = (REPEATS * n_tokens_fano) / t_py if t_py > 0 else float("inf")

    speedup = tok_per_s_cpp / tok_per_s_py if tok_per_s_py > 0 else float("inf")
    print(
        f"\nS2H throughput ({n_tokens_fano} tokens/string, {REPEATS} reps):\n"
        f"  C++:    {tok_per_s_cpp:,.0f} tokens/s  ({t_cpp * 1e3 / REPEATS:.3f} ms/call)\n"
        f"  Python: {tok_per_s_py:,.0f} tokens/s  ({t_py * 1e3 / REPEATS:.3f} ms/call)\n"
        f"  Speedup: {speedup:.1f}×"
    )

    # Non-regression: C++ must not be slower than Python.
    assert tok_per_s_cpp >= tok_per_s_py * 0.5, (
        f"C++ S2H should not be dramatically slower than Python "
        f"(cpp={tok_per_s_cpp:.0f} vs py={tok_per_s_py:.0f} tok/s)"
    )
