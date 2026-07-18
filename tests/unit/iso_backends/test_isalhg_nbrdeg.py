"""T-M0: the neighbour-degree seed variant ``greedy_min_nbrdeg`` is a sound,
iso-invariant canonical backend whose induced iso-partition matches the
pynauty oracle.

Covers acceptance criteria (a) iso-invariance on the design fixtures and
(b) partition agreement with pynauty. Hypothesis-driven invariance over
random small hypergraphs lives in
``tests/property/test_canonical_invariance.py`` (parametrized over the same
variant); this file pins the design-theoretic instances the property test
never samples (Fano, STS(9), cyclic C13, GQ(2,2)).
"""

from __future__ import annotations

from collections.abc import Sequence

import pytest

from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.iso_backends.base import IsoBackend
from isalhg.iso_backends.isalhg_backend import IsalHGBackend

pytestmark = pytest.mark.unit

_NBRDEG = "greedy_min_nbrdeg"


def _reverse(n: int) -> list[int]:
    return list(range(n))[::-1]


def _partition(backend: IsoBackend, items: Sequence[SparseHypergraph]) -> frozenset[frozenset[int]]:
    """Partition item indices by fingerprint equality under ``backend``."""
    groups: dict[bytes, set[int]] = {}
    for i, H in enumerate(items):
        groups.setdefault(bytes(backend.fingerprint(H)), set()).add(i)
    return frozenset(frozenset(g) for g in groups.values())


@pytest.mark.parametrize("fixture_name", ["fano_plane", "sts_9", "gq_2_2_doily"])
def test_nbrdeg_fingerprint_invariant_on_designs(
    fixture_name: str, request: pytest.FixtureRequest
) -> None:
    H: SparseHypergraph = request.getfixturevalue(fixture_name)
    backend = IsalHGBackend(algorithm=_NBRDEG)
    H2 = permute(H, _reverse(H.n_nodes))
    assert backend.fingerprint(H) == backend.fingerprint(H2)


def test_nbrdeg_separates_non_iso_cyclic_13(
    cyclic_triple_13_pair: tuple[SparseHypergraph, SparseHypergraph],
) -> None:
    h1, h2 = cyclic_triple_13_pair
    backend = IsalHGBackend(algorithm=_NBRDEG)
    assert backend.fingerprint(h1) != backend.fingerprint(h2)


def test_nbrdeg_iso_and_non_iso_pairs(
    iso_pair_small: tuple[SparseHypergraph, SparseHypergraph, list[int]],
    non_iso_pair_small: tuple[SparseHypergraph, SparseHypergraph],
) -> None:
    backend = IsalHGBackend(algorithm=_NBRDEG)
    h1, h2, _ = iso_pair_small
    assert backend.are_isomorphic(h1, h2)
    g1, g2 = non_iso_pair_small
    assert not backend.are_isomorphic(g1, g2)


def test_nbrdeg_partition_matches_pynauty(
    fano_plane: SparseHypergraph,
    sts_9: SparseHypergraph,
    cyclic_triple_13_pair: tuple[SparseHypergraph, SparseHypergraph],
) -> None:
    """Criterion (b): the nbrdeg backend and pynauty induce the SAME
    iso-partition on a corpus of designs, their relabellings, and a
    known non-iso pair -- even though their fingerprint *values* differ."""
    pytest.importorskip("pynauty")
    from isalhg.iso_backends.pynauty_levi import PynautyLeviBackend

    c13_a, c13_b = cyclic_triple_13_pair
    corpus: list[SparseHypergraph] = [
        fano_plane,
        permute(fano_plane, _reverse(7)),
        sts_9,
        permute(sts_9, _reverse(9)),
        c13_a,
        c13_b,
    ]
    isalhg = IsalHGBackend(algorithm=_NBRDEG)
    pyn = PynautyLeviBackend()
    # Expected: {fano, fano'} | {sts9, sts9'} | {c13_a} | {c13_b}.
    expected = frozenset({frozenset({0, 1}), frozenset({2, 3}), frozenset({4}), frozenset({5})})
    part_isalhg = _partition(isalhg, corpus)
    assert part_isalhg == expected
    assert part_isalhg == _partition(pyn, corpus)
