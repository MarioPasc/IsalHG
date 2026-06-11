"""Traces backend via the Levi bipartite reduction (subprocess to ``dreadnaut``).

Traces ships only as a CLI (``dreadnaut`` from the nauty distribution); there
is no Python binding as of nauty 2.8. This backend serialises the Levi graph
to dreadnaut's input language, invokes the binary, and parses the canonical
labelling from stdout.
"""

from __future__ import annotations

from typing import ClassVar

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.iso_backends.subprocess_base import SubprocessIsoBackend
from isalhg.types import BackendName, Fingerprint


class TracesLeviBackend(SubprocessIsoBackend):
    """Traces isomorphism backend over the Levi bipartite reduction."""

    BINARY_NAME: ClassVar[str] = "dreadnaut"

    @property
    def name(self) -> BackendName:
        return "traces_levi"

    def _serialize(self, H: SparseHypergraph) -> str:
        raise NotImplementedError

    def _parse(self, stdout: str) -> Fingerprint:
        raise NotImplementedError
