"""Property tests added during the T-OPTa orbit-pruning investigation.

Background (T-OPTa, 2026-07-19)
---------------------------------
A stabiliser-orbit pruning block was implemented in the C++ tie-complete
encoder (variant 7) and then REMOVED when Hypothesis falsified the invariant:
the per-node fingerprint (sorted multiset of (output_id, edge_label) pairs for
connections to already-mapped vertices) is a NECESSARY but not SUFFICIENT
condition for orbit membership.  When a new node has additional edges to
unlabelled vertices, two candidates can share the fingerprint while residing in
distinct orbits, causing the pruned encoder to miss the lex-min branch.  The
correct orbit computation requires the canonical form of the sub-hypergraph
induced on new nodes and their unlabelled neighbours, which is circular.

The tests below are retained because they add coverage NOT present in
``test_cpp_differential.py``:

  (a) Labelled regime: 2-symbol vertex vocabulary.  ``test_cpp_differential.py``
      only tests unlabelled (trivial) inputs.
  (b) Full-canonical (multi-seed) comparison: ``test_cpp_differential.py``
      covers per-seed; here we test ``canonical_string`` (all-seed lex-min).

The "orbit pruning" framing is superseded; these are generic C++ vs Python
regression tests for labelled inputs.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from isalhg.core.canonical import _python_canonical_string, canonical_string, required_k
from isalhg.core.hypergraph_to_string import _python_greedy_h2s, greedy_h2s
from isalhg.core.instructions import serialize
from isalhg.core.sparse_hypergraph import SparseHypergraph
from tests.property.test_canonical_invariance import small_connected_hypergraph

pytestmark = pytest.mark.property


# ---------------------------------------------------------------------------
# Infrastructure check.
# ---------------------------------------------------------------------------


def test_disagreement_detection() -> None:
    """The test infrastructure catches a disagreement."""
    H = SparseHypergraph(n_nodes=3, hyperedges=[frozenset({0, 1}), frozenset({1, 2})])
    k = required_k(H)
    py = serialize(list(_python_greedy_h2s(H, seed_node=0, k=k, inplace=True, tie_branch=True)))
    wrong = py + "X"
    assert py != wrong


# ---------------------------------------------------------------------------
# (a) Per-seed tie-complete: labelled regime.
# ---------------------------------------------------------------------------


@st.composite
def small_labelled_hypergraph(
    draw: st.DrawFn, max_n: int = 5, max_arity: int = 3
) -> SparseHypergraph:
    """Connected hypergraph with vertex labels drawn from {0, 1}."""
    n = draw(st.integers(min_value=2, max_value=max_n))
    perm = draw(st.permutations(list(range(n))))
    spanning_edges: list[frozenset[int]] = []
    for i in range(1, n):
        parent_idx = draw(st.integers(min_value=0, max_value=i - 1))
        spanning_edges.append(frozenset({perm[i], perm[parent_idx]}))
    n_extra = draw(st.integers(min_value=0, max_value=2))
    extra: list[frozenset[int]] = []
    for _ in range(n_extra):
        arity = draw(st.integers(min_value=2, max_value=min(max_arity, n)))
        members = draw(
            st.sets(
                st.integers(min_value=0, max_value=n - 1),
                min_size=arity,
                max_size=arity,
            )
        )
        extra.append(frozenset(members))
    labels = draw(
        st.lists(
            st.integers(min_value=0, max_value=1),
            min_size=n,
            max_size=n,
        )
    )
    return SparseHypergraph(
        n_nodes=n,
        hyperedges=spanning_edges + extra,
        n_vertex_labels=2,
        vertex_labels=labels,
    )


@settings(max_examples=80, deadline=None)
@given(small_labelled_hypergraph(max_n=5, max_arity=3))
def test_cpp_equals_python_seed0_labelled(H: SparseHypergraph) -> None:
    """C++ tie-complete encoder matches Python (seed 0, 2-symbol labels)."""
    k = required_k(H)
    py = serialize(list(_python_greedy_h2s(H, seed_node=0, k=k, inplace=True, tie_branch=True)))
    cpp = serialize(list(greedy_h2s(H, seed_node=0, k=k, tie_branch=True)))
    assert py == cpp, (
        f"C++ != Python (seed 0, labelled) on H(n={H.n_nodes}, m={H.n_edges})\n"
        f"  labels: {H.vertex_labels!r}\n"
        f"  py:  {py!r}\n"
        f"  cpp: {cpp!r}"
    )


# ---------------------------------------------------------------------------
# (b) Full canonical string (multi-seed lex-min): labelled + unlabelled.
# ---------------------------------------------------------------------------


@settings(max_examples=60, deadline=None)
@given(small_connected_hypergraph(max_n=6, max_arity=3))
def test_full_canonical_cpp_equals_python_unlabelled(H: SparseHypergraph) -> None:
    """canonical_string (C++ all-seed) matches _python_canonical_string."""
    k = required_k(H)
    cpp_w = canonical_string(H, k=k, algorithm="canonical")
    py_w = _python_canonical_string(H, k=k, structural_depth=3, algorithm="canonical")
    assert cpp_w == py_w, (
        f"canonical_string mismatch on H(n={H.n_nodes}, m={H.n_edges})\n"
        f"  cpp: {cpp_w!r}\n"
        f"  py:  {py_w!r}"
    )


@settings(max_examples=60, deadline=None)
@given(small_labelled_hypergraph(max_n=5, max_arity=3))
def test_full_canonical_cpp_equals_python_labelled(H: SparseHypergraph) -> None:
    """canonical_string (C++ all-seed) matches Python, 2-symbol vertex labels."""
    k = required_k(H)
    cpp_w = canonical_string(H, k=k, algorithm="canonical")
    py_w = _python_canonical_string(H, k=k, structural_depth=3, algorithm="canonical")
    assert cpp_w == py_w, (
        f"canonical_string mismatch (labelled) on H(n={H.n_nodes}, m={H.n_edges})\n"
        f"  labels: {H.vertex_labels!r}\n"
        f"  cpp: {cpp_w!r}\n"
        f"  py:  {py_w!r}"
    )
