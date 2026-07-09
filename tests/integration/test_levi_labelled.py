"""Regression: the Levi backends respect absolute vertex- and edge-label identity.

nauty and Traces receive the colouring as an ordered partition, whose cells are
identified by position. Before T-TAe the unoccupied label ids contributed no
cell, so over ``|Sigma_V| = 2`` the one-edge hypergraphs labelled ``(0, 0)`` and
``(1, 1)`` handed both engines the same partition and both answered
``are_isomorphic == True``. Def. 1.3 of the Theorem A proof requires
``l_V2(phi(v)) == l_V1(v)``, so they are not isomorphic.

A second, independent instance: nauty's certificate omits the colouring
altogether, so a pair whose colour classes differ in *size* can still share a
certificate. Both are repaired by prefixing ``LeviGraph.color_signature``.

bliss is exempt by construction -- igraph passes colour *values* to bliss -- and
is included here to pin that.

Each backend is skipped when its optional dependency does not resolve.
"""

from __future__ import annotations

import shutil

import pytest

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.iso_backends.base import IsoBackend

pytestmark = pytest.mark.integration


def _available_backends() -> list[tuple[str, IsoBackend]]:
    found: list[tuple[str, IsoBackend]] = []
    try:
        import pynauty  # noqa: F401

        from isalhg.iso_backends.pynauty_levi import PynautyLeviBackend

        found.append(("pynauty_levi", PynautyLeviBackend()))
    except ImportError:
        pass
    try:
        import igraph  # noqa: F401

        from isalhg.iso_backends.bliss_levi import BlissLeviBackend

        found.append(("bliss_levi", BlissLeviBackend()))
    except ImportError:
        pass
    if shutil.which("dreadnaut") is not None:
        from isalhg.iso_backends.traces_levi import TracesLeviBackend

        found.append(("traces_levi", TracesLeviBackend()))
    return found


BACKENDS = _available_backends()
if not BACKENDS:
    pytest.skip("no Levi backend available", allow_module_level=True)

_BACKEND_ARGS = [b for _, b in BACKENDS]
_BACKEND_IDS = [name for name, _ in BACKENDS]


def _v(labels: list[int], edges: list[set[int]], n_vertex_labels: int) -> SparseHypergraph:
    return SparseHypergraph(
        n_nodes=len(labels),
        hyperedges=[frozenset(e) for e in edges],
        n_vertex_labels=n_vertex_labels,
        vertex_labels=labels,
    )


_PAIRS: list[tuple[str, SparseHypergraph, SparseHypergraph, bool]] = [
    # The T-TAe counterexample: the unoccupied label id vanishes from the partition.
    ("all_zero_vs_all_one", _v([0, 0], [{0, 1}], 2), _v([1, 1], [{0, 1}], 2), False),
    # Colour classes of equal size, different ids.
    ("label_shift", _v([0, 1, 1], [{0, 1}], 3), _v([0, 2, 2], [{0, 1}], 3), False),
    # The label's only carrier is an isolated vertex.
    ("isolated_vertex", _v([0, 1], [{0}], 3), _v([0, 2], [{0}], 3), False),
    # Edge labels are erased by the same mechanism.
    (
        "edge_label_shift",
        SparseHypergraph(2, [frozenset({0, 1})], n_edge_labels=2, edge_labels=[0]),
        SparseHypergraph(2, [frozenset({0, 1})], n_edge_labels=2, edge_labels=[1]),
        False,
    ),
    # Positive control: a genuine relabelling must still be recognised.
    (
        "relabelling_is_iso",
        _v([0, 1, 1], [{0, 1}, {1, 2}], 3),
        _v([1, 1, 0], [{1, 2}, {0, 1}], 3),
        True,
    ),
]

_PAIR_ARGS = [(a, b, c) for _, a, b, c in _PAIRS]
_PAIR_IDS = [name for name, *_ in _PAIRS]


@pytest.mark.parametrize("backend", _BACKEND_ARGS, ids=_BACKEND_IDS)
@pytest.mark.parametrize(("H1", "H2", "expected"), _PAIR_ARGS, ids=_PAIR_IDS)
def test_are_isomorphic_respects_absolute_labels(
    backend: IsoBackend, H1: SparseHypergraph, H2: SparseHypergraph, expected: bool
) -> None:
    assert backend.are_isomorphic(H1, H2) is expected


@pytest.mark.parametrize("backend", _BACKEND_ARGS, ids=_BACKEND_IDS)
@pytest.mark.parametrize(("H1", "H2", "expected"), _PAIR_ARGS, ids=_PAIR_IDS)
def test_fingerprint_agrees_with_are_isomorphic(
    backend: IsoBackend, H1: SparseHypergraph, H2: SparseHypergraph, expected: bool
) -> None:
    """Invariant 9: fingerprint equality and ``are_isomorphic`` never disagree."""
    assert (backend.fingerprint(H1) == backend.fingerprint(H2)) is expected


@pytest.mark.parametrize("backend", _BACKEND_ARGS, ids=_BACKEND_IDS)
def test_bipartition_split_is_pinned(backend: IsoBackend) -> None:
    """Same Levi graph, different ``(|V|, |E|)`` split of its bipartition.

    Both hypergraphs reduce to the path on five nodes; only the side each node
    sits on differs. A certificate that ignores the colouring cannot separate
    them, and ``fingerprint`` is what the partition-agreement protocol keys on.
    """
    H1 = SparseHypergraph(3, [frozenset({0, 1}), frozenset({1, 2})])
    H2 = SparseHypergraph(2, [frozenset({0}), frozenset({0, 1}), frozenset({1})])
    assert backend.fingerprint(H1) != backend.fingerprint(H2)
