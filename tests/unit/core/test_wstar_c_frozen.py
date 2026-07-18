"""Regression pins for the frozen canonical form ``w*_c`` (D-TA2).

``w*_c`` is frozen as the *unpruned* tie-complete lex-min (decision D-TA2,
PI 2026-07-09): the lex-min over the full residual tie set and all
label-respecting orderings. Refining the tie set with an iso-invariant key
preserves completeness (proof Lemma 6.1) but returns a *different* canonical
form, which would silently invalidate every published ``d_I`` value. These
pins exist so that any future refinement that changes the value of ``w*_c``
fails loudly; the only change that may keep them green is stabiliser-orbit
pruning (proof Proposition 6.0), which is value-preserving.

If a pin fails, the canonical form changed. That is a definitional event,
not a test to update: stop and re-read D-TA2 in
``docs/article/DEVELOPMENT/DECISIONS.md``.
"""

from __future__ import annotations

import hashlib

import pytest

from isalhg.core.canonical import canonical_string
from isalhg.core.sparse_hypergraph import SparseHypergraph

pytestmark = pytest.mark.unit

# (string length, sha256 of the serialized string), computed 2026-07-09 with
# the unpruned tie-complete search (C++ variant 7 == algorithm="canonical").
_PINNED_FIXTURES: dict[str, tuple[int, str]] = {
    "fano_plane": (
        121,
        "9695315fb1566ec737ee3b22ee65e6423690bd1a82f8c7e010b2a312214ea79b",
    ),
    "sts_9": (
        227,
        "a6282f853d79d251b58a7b8962f9e54496a225483a8785adffbcb511312047cc",
    ),
}

_PINNED_C13_013 = (
    256,
    "77d9fa1e4e99d500c3bed2debf32d6da773b1721c7e3ea26f5a734ac0ec89bec",
)

# True STS(13) pins (T-M0c, 2026-07-18): catalog systems 1 and 2 of
# datasets/data/sts/sts13.txt, ~44 s each -> slow marker. Distinct hashes =
# w*_c separates the two STS(13) isomorphism classes.
_PINNED_STS13_TRUE = {
    1: (472, "4e5e682d86de95fe7526bce05c74519856270e3eb8e907e99437b3efb53f0cc6"),
    2: (472, "bd872631a5a5a17256c411159c1a10f40d5d8ef63ef0893ab2fcbbd7a5467eca"),
}

_PINNED_CE_N4 = (
    54,
    "ab9393ffb4dc117f86481e09b44b54e2fbfc01be166aa2f3e2fdfbead0656ba3",
)


def _pin(w: str) -> tuple[int, str]:
    return len(w), hashlib.sha256(w.encode()).hexdigest()


@pytest.mark.parametrize("fixture_name", sorted(_PINNED_FIXTURES))
def test_wstar_c_pinned_on_design_fixtures(
    fixture_name: str, request: pytest.FixtureRequest
) -> None:
    H: SparseHypergraph = request.getfixturevalue(fixture_name)
    w = canonical_string(H, k=3, algorithm="canonical")
    assert _pin(w) == _PINNED_FIXTURES[fixture_name]


def test_wstar_c_pinned_on_cyclic_triple_orbit_13() -> None:
    # The (0,1,3) cyclic partial triple system (13 blocks; historically
    # mis-called "STS(13)" until T-M0c). Same object, same pin value.
    H = SparseHypergraph(
        n_nodes=13,
        hyperedges=[frozenset({i, (i + 1) % 13, (i + 3) % 13}) for i in range(13)],
    )
    w = canonical_string(H, k=3, algorithm="canonical")
    assert _pin(w) == _PINNED_C13_013


@pytest.mark.slow
@pytest.mark.parametrize("catalog_index", sorted(_PINNED_STS13_TRUE))
def test_wstar_c_pinned_on_true_sts13(catalog_index: int) -> None:
    from isalhg.datasets.synthetic.sts_catalog import steiner_triple_system

    H = steiner_triple_system(13, catalog_index - 1)
    w = canonical_string(H, k=3, algorithm="canonical")
    assert _pin(w) == _PINNED_STS13_TRUE[catalog_index]


def test_wstar_c_pinned_on_n4_counterexample() -> None:
    H = SparseHypergraph(
        n_nodes=4,
        hyperedges=[
            frozenset({1, 3}),
            frozenset({0, 1, 3}),
            frozenset({0, 2, 3}),
            frozenset({1, 2}),
        ],
    )
    w = canonical_string(H, k=3, algorithm="canonical")
    assert _pin(w) == _PINNED_CE_N4
