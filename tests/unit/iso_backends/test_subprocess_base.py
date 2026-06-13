"""Unit tests for :class:`isalhg.iso_backends.subprocess_base.SubprocessIsoBackend`."""

from __future__ import annotations

import stat
from pathlib import Path

import pytest

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.errors import (
    BackendOutputParseError,
    BackendTimeoutError,
    BackendUnavailableError,
)
from isalhg.iso_backends.subprocess_base import SubprocessIsoBackend
from isalhg.types import BackendName, Fingerprint

pytestmark = pytest.mark.unit


class _MockBackend(SubprocessIsoBackend):
    """SubprocessIsoBackend subclass for testing plumbing only.

    Serialisation is just the canonical edge-list string of the input;
    parsing is the identity (utf-8 encode). The 'binary' is a tiny shell
    script that echoes its stdin to stdout.
    """

    @property
    def name(self) -> BackendName:
        return "_mock"

    def _serialize(self, H: SparseHypergraph) -> str:
        edges = sorted(tuple(sorted(m)) for _, m, _ in H.iter_edges())
        return repr((H.n_nodes, edges))

    def _parse(self, stdout: str) -> Fingerprint:
        return stdout.strip().encode("utf-8")


@pytest.fixture
def echo_binary(tmp_path: Path) -> Path:
    p = tmp_path / "echo_binary.sh"
    p.write_text("#!/bin/sh\ncat -\n")
    p.chmod(p.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return p


def test_resolve_binary_missing_raises_unavailable() -> None:
    backend = _MockBackend(binary_path=Path("/nonexistent/binary-xyz-not-here"))
    with pytest.raises(BackendUnavailableError):
        backend._resolve_binary()  # noqa: SLF001


def test_invoke_passes_payload_through(echo_binary: Path) -> None:
    backend = _MockBackend(binary_path=echo_binary)
    out = backend._invoke("hello world\n")  # noqa: SLF001
    assert out == "hello world\n"


def test_fingerprint_round_trip(echo_binary: Path) -> None:
    H = SparseHypergraph(n_nodes=3, hyperedges=[frozenset({0, 1, 2})])
    backend = _MockBackend(binary_path=echo_binary)
    fp = backend.fingerprint(H)
    assert fp == b"(3, [(0, 1, 2)])"


def test_are_isomorphic_label_count_early_outs(echo_binary: Path) -> None:
    H1 = SparseHypergraph(n_nodes=3, hyperedges=[frozenset({0, 1, 2})])
    H2 = SparseHypergraph(
        n_nodes=3,
        hyperedges=[frozenset({0, 1, 2})],
        n_vertex_labels=2,
    )
    backend = _MockBackend(binary_path=echo_binary)
    assert backend.are_isomorphic(H1, H2) is False


def test_invoke_timeout_raises_backend_timeout(tmp_path: Path) -> None:
    slow_binary = tmp_path / "sleeper.sh"
    slow_binary.write_text("#!/bin/sh\nsleep 5\ncat -\n")
    slow_binary.chmod(slow_binary.stat().st_mode | stat.S_IXUSR)
    backend = _MockBackend(binary_path=slow_binary, timeout_s=0.5)
    with pytest.raises(BackendTimeoutError):
        backend._invoke("payload")  # noqa: SLF001


def test_invoke_non_zero_exit_raises_parse_error(tmp_path: Path) -> None:
    failing = tmp_path / "fail.sh"
    failing.write_text("#!/bin/sh\necho 'error' 1>&2\nexit 2\n")
    failing.chmod(failing.stat().st_mode | stat.S_IXUSR)
    backend = _MockBackend(binary_path=failing)
    with pytest.raises(BackendOutputParseError):
        backend._invoke("anything")  # noqa: SLF001


def test_resolve_caches_result(echo_binary: Path) -> None:
    backend = _MockBackend(binary_path=echo_binary)
    p1 = backend._resolve_binary()  # noqa: SLF001
    p2 = backend._resolve_binary()  # noqa: SLF001
    assert p1 == p2
