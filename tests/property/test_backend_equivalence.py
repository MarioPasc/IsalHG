"""Backend equivalence: ``backend="cpp"`` and ``backend="python"`` produce
identical output across every user-facing entry point in ``isalhg.core``.

This is the formal differential test for the dual-backend dispatch added
on top of the C++ port. A failure here means the C++ implementation and
the Python reference disagree on some input — either the algorithm
itself drifted, the FNV-1a constants are out of sync, or the backend
dispatch routes incorrectly.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings

from isalhg.core.canonical import available_cpp_variants, canonical_string, required_k
from isalhg.core.hypergraph_to_string import greedy_h2s, hypergraph_to_string
from isalhg.core.hypergraph_wl import wl_hash, wl_partition
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.core.structural_tuples import max_xi_nodes
from isalhg.datasets.synthetic.designs import fano_plane, gq_2_2_doily, sts_9
from tests.property.test_canonical_invariance import small_connected_hypergraph

pytestmark = pytest.mark.property


# Fast designs covered with all seven native variants. The doily is too
# slow in the Python backend (greedy_h2s single-seed ~21 s; multi-seed
# variants DNF >300 s) so we only check single-seed equivalence on it,
# under the ``slow`` marker.
_FAST_NAMED = [("fano", fano_plane()), ("sts9", sts_9())]
_SLOW_NAMED = [("doily", gq_2_2_doily())]
_NATIVE_VARIANTS = [
    "greedy_min",
    "greedy_single",
    "greedy_min_inplace",
    "greedy_min_wl_pruned",
    "greedy_min_inplace_wl_pruned",
    "greedy_min_nbrdeg",
    "greedy_single_nbrdeg",
]


@pytest.mark.parametrize("name,H", _FAST_NAMED)
@pytest.mark.parametrize("algorithm", _NATIVE_VARIANTS)
def test_canonical_string_backends_agree_named(
    name: str, H: SparseHypergraph, algorithm: str
) -> None:
    py = canonical_string(H, algorithm=algorithm, backend="python")
    cpp = canonical_string(H, algorithm=algorithm, backend="cpp")
    assert py == cpp, f"{name} / {algorithm}: backends disagree"


@pytest.mark.slow
def test_canonical_string_complete_backends_agree_fano() -> None:
    # "canonical" (formerly greedy_min_complete) is excluded from _NATIVE_VARIANTS: the Python
    # tie-complete reference costs ~3.4 s on Fano and ~132 s on STS(9).
    H = fano_plane()
    py = canonical_string(H, algorithm="canonical", backend="python")
    cpp = canonical_string(H, algorithm="canonical", backend="cpp")
    assert py == cpp


@settings(max_examples=25, deadline=None)
@given(small_connected_hypergraph(max_n=5, max_arity=3))
def test_canonical_string_complete_backends_agree_hypothesis(H: SparseHypergraph) -> None:
    py = canonical_string(H, algorithm="canonical", backend="python")
    cpp = canonical_string(H, algorithm="canonical", backend="cpp")
    assert py == cpp


def test_complete_is_a_native_cpp_variant() -> None:
    assert "canonical" in available_cpp_variants()


@pytest.mark.slow
@pytest.mark.parametrize("name,H", _SLOW_NAMED)
def test_canonical_string_backends_agree_doily_single(name: str, H: SparseHypergraph) -> None:
    # Python multi-seed on doily is DNF >300 s. greedy_single is the
    # only finite Python timing.
    py = canonical_string(H, algorithm="greedy_single", backend="python")
    cpp = canonical_string(H, algorithm="greedy_single", backend="cpp")
    assert py == cpp


@pytest.mark.parametrize("name,H", _FAST_NAMED)
def test_greedy_h2s_backends_agree_named(name: str, H: SparseHypergraph) -> None:
    k = required_k(H)
    py = greedy_h2s(H, seed_node=0, k=k, backend="python")
    cpp = greedy_h2s(H, seed_node=0, k=k, backend="cpp")
    assert py == cpp, f"{name}: greedy_h2s backends disagree"


@pytest.mark.slow
@pytest.mark.parametrize("name,H", _SLOW_NAMED)
def test_greedy_h2s_backends_agree_doily(name: str, H: SparseHypergraph) -> None:
    k = required_k(H)
    py = greedy_h2s(H, seed_node=0, k=k, backend="python")
    cpp = greedy_h2s(H, seed_node=0, k=k, backend="cpp")
    assert py == cpp


@pytest.mark.parametrize("name,H", _FAST_NAMED + _SLOW_NAMED)
def test_wl_hash_backends_agree_named(name: str, H: SparseHypergraph) -> None:
    py = wl_hash(H, backend="python")
    cpp = wl_hash(H, backend="cpp")
    assert py == cpp, f"{name}: wl_hash backends disagree"


@pytest.mark.parametrize("name,H", _FAST_NAMED + _SLOW_NAMED)
def test_wl_partition_backends_agree_named(name: str, H: SparseHypergraph) -> None:
    py = wl_partition(H, backend="python")
    cpp = wl_partition(H, backend="cpp")
    # Compare by sorted (sorted_members) tuples — colour ids are equal but
    # dict ordering may differ.
    py_groups = sorted(tuple(sorted(v)) for v in py.values())
    cpp_groups = sorted(tuple(sorted(v)) for v in cpp.values())
    assert py_groups == cpp_groups, f"{name}: wl_partition backends disagree"


@pytest.mark.parametrize("name,H", _FAST_NAMED + _SLOW_NAMED)
def test_max_xi_nodes_backends_agree_named(name: str, H: SparseHypergraph) -> None:
    py = max_xi_nodes(H, backend="python")
    cpp = max_xi_nodes(H, backend="cpp")
    # max_xi_nodes returns a tuple of NodeIds. Order should match (both
    # iterate vertices in ascending id order).
    assert sorted(py) == sorted(cpp), f"{name}: max_xi_nodes backends disagree"


@pytest.mark.parametrize("name,H", _FAST_NAMED)
def test_hypergraph_to_string_backends_agree_named(name: str, H: SparseHypergraph) -> None:
    k = required_k(H)
    py = hypergraph_to_string(H, seed_node=0, k=k, backend="python")
    cpp = hypergraph_to_string(H, seed_node=0, k=k, backend="cpp")
    assert py == cpp, f"{name}: hypergraph_to_string backends disagree"


@settings(max_examples=40, deadline=None)
@given(small_connected_hypergraph(max_n=6, max_arity=3))
def test_canonical_string_backends_agree_hypothesis(H: SparseHypergraph) -> None:
    py = canonical_string(H, backend="python")
    cpp = canonical_string(H, backend="cpp")
    assert py == cpp


def test_default_backend_is_cpp() -> None:
    from isalhg.core.backends import DEFAULT_BACKEND

    assert DEFAULT_BACKEND == "cpp"


def test_unknown_backend_raises() -> None:
    H = fano_plane()
    with pytest.raises(ValueError, match="unknown backend"):
        canonical_string(H, backend="rust")
    with pytest.raises(ValueError, match="unknown backend"):
        greedy_h2s(H, seed_node=0, k=3, backend="haskell")
    with pytest.raises(ValueError, match="unknown backend"):
        wl_hash(H, backend="erlang")
    with pytest.raises(ValueError, match="unknown backend"):
        max_xi_nodes(H, backend="ocaml")
