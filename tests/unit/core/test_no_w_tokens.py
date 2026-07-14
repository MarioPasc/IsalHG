"""The canonical encoder emits no ``W`` tokens (Theorem B length-lemma proviso).

The string-length envelope ``|w*_c| <= m(1+kn)`` of
``proofs/stability/theorem_b_stability.tex`` (Lemma "String-length envelope")
counts one V/C token per edge plus unit-step pointer runs; it holds *provided*
the encoder never emits gratuitous ``W`` tokens. ``W`` remains a legal
``Sigma_HG`` token (CLAUDE.md invariant 6: S2H accepts it and canonicalization
must not strip it from *input* strings), but neither backend has a W-emission
rule -- the Python encoder never constructs ``TokenW`` and the C++ core never
calls ``Token::make_w()``. This module pins that fact; if it ever fails, the
length envelope of Theorem B must be re-derived (ledger task T-TBb, D4).
"""

from __future__ import annotations

import random

import pytest

from isalhg.core.canonical import canonical_string
from isalhg.core.instructions import TokenW, parse
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.datasets.synthetic._random_hg import random_connected_hypergraph

pytestmark = pytest.mark.unit


def _assert_no_w(w: str) -> None:
    assert not any(isinstance(tok, TokenW) for tok in parse(w))


# The edge-order counterexample hypergraph (primal graph K4, constant eta;
# same object as tests/unit/core/test_canonical_encoder.py).
_K4_CE = SparseHypergraph(
    n_nodes=4,
    hyperedges=[
        frozenset({1, 3}),
        frozenset({0, 1, 3}),
        frozenset({0, 2, 3}),
        frozenset({1, 2}),
    ],
)


@pytest.mark.parametrize("backend", ["cpp", "python"])
def test_no_w_tokens_small_fixtures(
    backend: str,
    single_edge_hypergraph: SparseHypergraph,
    iso_pair_small: tuple[SparseHypergraph, SparseHypergraph, list[int]],
    qin_fig1_hypergraph: SparseHypergraph,
) -> None:
    h1, h2, _ = iso_pair_small
    for H in (single_edge_hypergraph, h1, h2, qin_fig1_hypergraph, _K4_CE):
        _assert_no_w(canonical_string(H, backend=backend))


def test_no_w_tokens_design_fixtures(
    fano_plane: SparseHypergraph,
    sts_9: SparseHypergraph,
    sts_13_pair: tuple[SparseHypergraph, SparseHypergraph],
    gq_2_2_doily: SparseHypergraph,
) -> None:
    """Tie-degenerate designs, C++ backend only (w*_c is expensive here)."""
    sts13_a, sts13_b = sts_13_pair
    for H in (fano_plane, sts_9, sts13_a, sts13_b, gq_2_2_doily):
        _assert_no_w(canonical_string(H, backend="cpp"))


@pytest.mark.parametrize("backend", ["cpp", "python"])
@pytest.mark.parametrize("seed", [0, 1, 2, 3, 4])
def test_no_w_tokens_random_connected(backend: str, seed: int) -> None:
    # The Python reference is exponentially slower on tie-degenerate draws;
    # smaller instances exercise the same emission rules.
    hi_n, hi_m = (10, 12) if backend == "cpp" else (6, 7)
    rng = random.Random(seed)
    H, _ = random_connected_hypergraph(
        n_nodes=rng.randint(4, hi_n),
        n_edges=rng.randint(4, hi_m),
        arity_range=(2, 4),
        rng=rng,
    )
    _assert_no_w(canonical_string(H, backend=backend))
