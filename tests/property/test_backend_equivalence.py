"""Backend equivalence: ``backend="cpp"`` and ``backend="python"`` produce
identical output across every user-facing entry point in ``isalhg.core``.

This is the formal differential test for the dual-backend dispatch added
on top of the C++ port. A failure here means the C++ implementation and
the Python reference disagree on some input — either the algorithm
itself drifted, the FNV-1a constants are out of sync, or the backend
dispatch routes incorrectly.
"""

from __future__ import annotations

import itertools

import pytest
from hypothesis import given, settings

from isalhg.core.canonical import canonical_string, required_k
from isalhg.core.hypergraph_to_string import greedy_h2s, hypergraph_to_string
from isalhg.core.hypergraph_wl import wl_hash, wl_partition
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.core.structural_tuples import max_xi_nodes
from tests.property.test_canonical_invariance import small_connected_hypergraph

pytestmark = pytest.mark.property


def _fano() -> SparseHypergraph:
    edges = [
        [0, 1, 2],
        [0, 3, 4],
        [0, 5, 6],
        [1, 3, 5],
        [1, 4, 6],
        [2, 3, 6],
        [2, 4, 5],
    ]
    return SparseHypergraph(n_nodes=7, hyperedges=edges)


def _sts9() -> SparseHypergraph:
    edges = [
        [0, 1, 2],
        [3, 4, 5],
        [6, 7, 8],
        [0, 3, 6],
        [1, 4, 7],
        [2, 5, 8],
        [0, 4, 8],
        [1, 5, 6],
        [2, 3, 7],
        [0, 5, 7],
        [1, 3, 8],
        [2, 4, 6],
    ]
    return SparseHypergraph(n_nodes=9, hyperedges=edges)


def _doily() -> SparseHypergraph:
    pairs = list(itertools.combinations(range(1, 7), 2))
    pid = {p: i for i, p in enumerate(pairs)}

    def _matchings(es: tuple[int, ...]):
        if not es:
            yield ()
            return
        a = es[0]
        rest = es[1:]
        for i, b in enumerate(rest):
            for tail in _matchings(rest[:i] + rest[i + 1 :]):
                yield ((a, b),) + tail

    lines = [sorted(pid[tuple(sorted(p))] for p in m) for m in _matchings(tuple(range(1, 7)))]
    return SparseHypergraph(n_nodes=15, hyperedges=lines)


# Fast designs covered with all five native variants. The doily is too
# slow in the Python backend (greedy_h2s single-seed ~21 s; multi-seed
# variants DNF >300 s) so we only check single-seed equivalence on it,
# under the ``slow`` marker.
_FAST_NAMED = [("fano", _fano()), ("sts9", _sts9())]
_SLOW_NAMED = [("doily", _doily())]
_NATIVE_VARIANTS = [
    "greedy_min",
    "greedy_single",
    "greedy_min_inplace",
    "greedy_min_wl_pruned",
    "greedy_min_inplace_wl_pruned",
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
    H = _fano()
    with pytest.raises(ValueError, match="unknown backend"):
        canonical_string(H, backend="rust")
    with pytest.raises(ValueError, match="unknown backend"):
        greedy_h2s(H, seed_node=0, k=3, backend="haskell")
    with pytest.raises(ValueError, match="unknown backend"):
        wl_hash(H, backend="erlang")
    with pytest.raises(ValueError, match="unknown backend"):
        max_xi_nodes(H, backend="ocaml")
