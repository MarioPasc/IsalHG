"""Shared helper for backends invoked through an external binary.

Traces (``dreadnaut`` from the nauty distribution) has no Python binding; bliss
ships a CLI that is occasionally used as a fallback when ``python-igraph`` is
unavailable. Centralising the subprocess plumbing (binary discovery, timeout,
stderr capture, temp-file management) keeps the concrete backends focused on
input serialisation and output parsing.

Restriction: Python stdlib only.
"""

from __future__ import annotations

from abc import abstractmethod
from pathlib import Path
from typing import ClassVar

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.iso_backends.base import IsoBackend
from isalhg.types import Fingerprint


class SubprocessIsoBackend(IsoBackend):
    """Abstract base for iso backends that shell out to an external binary.

    Concrete subclasses define how a :class:`SparseHypergraph` is serialised to
    the binary's input format and how its stdout is parsed into a canonical
    byte string.
    """

    #: Name of the executable searched for on ``PATH``. Must be set by subclasses.
    BINARY_NAME: ClassVar[str] = ""

    #: Default wall-clock budget per invocation, in seconds.
    DEFAULT_TIMEOUT_S: ClassVar[float] = 600.0

    def __init__(
        self,
        binary_path: Path | None = None,
        timeout_s: float | None = None,
    ) -> None:
        """Store discovery hints; do not validate yet.

        Parameters
        ----------
        binary_path : Path | None
            Explicit path to the executable. ``None`` triggers ``shutil.which``
            on :attr:`BINARY_NAME` at first call.
        timeout_s : float | None
            Per-invocation wall-clock budget. ``None`` uses :attr:`DEFAULT_TIMEOUT_S`.
        """
        self._binary_path = binary_path
        self._timeout_s = timeout_s if timeout_s is not None else self.DEFAULT_TIMEOUT_S

    # ------------------------------------------------------------------
    # Subclass extension points
    # ------------------------------------------------------------------

    @abstractmethod
    def _serialize(self, H: SparseHypergraph) -> str:
        """Render ``H`` in the format expected by the external binary."""
        ...

    @abstractmethod
    def _parse(self, stdout: str) -> Fingerprint:
        """Extract the canonical byte string from the binary's stdout."""
        ...

    # ------------------------------------------------------------------
    # Shared plumbing (implementations to be filled by the coding agent)
    # ------------------------------------------------------------------

    def _resolve_binary(self) -> Path:
        """Locate :attr:`BINARY_NAME` on ``PATH`` or honour the constructor hint.

        Raises
        ------
        isalhg.errors.BackendUnavailableError
            If the binary cannot be located.
        """
        raise NotImplementedError

    def _invoke(self, payload: str) -> str:
        """Run the binary with ``payload`` on stdin under the configured timeout.

        Raises
        ------
        isalhg.errors.BackendTimeoutError
            On timeout.
        isalhg.errors.BackendOutputParseError
            On non-zero exit or unexpected stderr.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # IsoBackend hooks
    # ------------------------------------------------------------------

    def fingerprint(self, H: SparseHypergraph) -> Fingerprint:
        raise NotImplementedError

    def are_isomorphic(self, H1: SparseHypergraph, H2: SparseHypergraph) -> bool:
        raise NotImplementedError
