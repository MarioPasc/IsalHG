"""Every Levi backend agrees with the exhaustive label-preserving oracle.

The property T-TAe restores: for labelled hypergraphs, ``are_isomorphic`` and
``fingerprint`` equality both decide isomorphism exactly, where "exactly" is
adjudicated by ``_labelled_oracle.brute_force_iso`` -- an exhaustive search over
the ``n!`` bijections that shares no machinery with the backends.

``labelled_hypergraph_pair`` draws two labellings of one structure over a shared
non-trivial vocabulary (``n <= 5``, ``|Sigma_V| in {2, 3}``), which is the regime
the defect lived in: the structures agree, so only the label ids can separate
the pair.
"""

from __future__ import annotations

import shutil

import pytest
from hypothesis import HealthCheck, given, settings

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.iso_backends.base import IsoBackend
from tests.property._labelled_oracle import brute_force_iso, labelled_hypergraph_pair

pytestmark = pytest.mark.property


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


@pytest.mark.parametrize("backend", _BACKEND_ARGS, ids=_BACKEND_IDS)
@given(pair=labelled_hypergraph_pair(max_n=5, max_arity=3))
@settings(deadline=None, max_examples=200, suppress_health_check=[HealthCheck.too_slow])
def test_are_isomorphic_matches_oracle(
    backend: IsoBackend, pair: tuple[SparseHypergraph, SparseHypergraph]
) -> None:
    H1, H2 = pair
    assert backend.are_isomorphic(H1, H2) is brute_force_iso(H1, H2)


@pytest.mark.parametrize("backend", _BACKEND_ARGS, ids=_BACKEND_IDS)
@given(pair=labelled_hypergraph_pair(max_n=5, max_arity=3))
@settings(deadline=None, max_examples=200, suppress_health_check=[HealthCheck.too_slow])
def test_fingerprint_equality_matches_oracle(
    backend: IsoBackend, pair: tuple[SparseHypergraph, SparseHypergraph]
) -> None:
    H1, H2 = pair
    equal = backend.fingerprint(H1) == backend.fingerprint(H2)
    assert equal is brute_force_iso(H1, H2)
