"""Traces-Levi backend round-trip: fingerprint stability and partition agreement.

Requires ``dreadnaut`` on ``PATH`` (install via
``conda install -n isalhg -c conda-forge nauty``). Marked
``integration`` + ``subprocess`` per the project's marker conventions.
"""

from __future__ import annotations

import shutil

import pytest

from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.iso_backends.isalhg_backend import IsalHGBackend
from isalhg.iso_backends.traces_levi import TracesLeviBackend

if shutil.which("dreadnaut") is None:
    pytest.skip(
        "dreadnaut binary not on PATH; install nauty to enable this test",
        allow_module_level=True,
    )

pytestmark = [pytest.mark.integration, pytest.mark.subprocess]


@pytest.mark.parametrize(
    "fixture_name",
    ["single_edge_hypergraph", "fano_plane", "sts_9"],
)
def test_traces_fingerprint_invariant(fixture_name: str, request: pytest.FixtureRequest) -> None:
    H = request.getfixturevalue(fixture_name)
    backend = TracesLeviBackend()
    fp_h = backend.fingerprint(H)
    for seed in range(2):
        import random

        rng = random.Random(seed)
        sigma = list(range(H.n_nodes))
        rng.shuffle(sigma)
        H2 = permute(H, sigma)
        assert backend.fingerprint(H2) == fp_h, (
            f"Traces fingerprint not invariant under permutation on {fixture_name}"
        )


@pytest.mark.parametrize(
    "fixture_name",
    ["single_edge_hypergraph", "fano_plane", "sts_9"],
)
def test_partition_agreement_iso(fixture_name: str, request: pytest.FixtureRequest) -> None:
    H = request.getfixturevalue(fixture_name)
    H2 = permute(H, list(range(H.n_nodes - 1, -1, -1)))
    traces = TracesLeviBackend()
    isalhg = IsalHGBackend()
    assert traces.are_isomorphic(H, H2)
    assert isalhg.are_isomorphic(H, H2)


def test_partition_agreement_non_iso(
    non_iso_pair_small: tuple[SparseHypergraph, SparseHypergraph],
) -> None:
    h1, h2 = non_iso_pair_small
    traces = TracesLeviBackend()
    isalhg = IsalHGBackend()
    assert not traces.are_isomorphic(h1, h2)
    assert not isalhg.are_isomorphic(h1, h2)
