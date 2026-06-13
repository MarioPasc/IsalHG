"""Shared helper for backends invoked through an external binary.

Traces (``dreadnaut`` from the nauty distribution) has no Python binding; bliss
ships a CLI that is occasionally used as a fallback when ``python-igraph`` is
unavailable. Centralising the subprocess plumbing (binary discovery, timeout,
stderr capture, temp-file management) keeps the concrete backends focused on
input serialisation and output parsing.

Restriction: Python stdlib only.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from abc import abstractmethod
from pathlib import Path
from typing import ClassVar

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.errors import (
    BackendOutputParseError,
    BackendTimeoutError,
    BackendUnavailableError,
)
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
        self._binary_path: Path | None = binary_path
        self._timeout_s: float = timeout_s if timeout_s is not None else self.DEFAULT_TIMEOUT_S
        self._resolved_path: Path | None = None

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
    # Shared plumbing
    # ------------------------------------------------------------------

    def _resolve_binary(self) -> Path:
        """Locate :attr:`BINARY_NAME` on ``PATH`` or honour the constructor hint.

        Result is cached on the instance.

        Raises
        ------
        isalhg.errors.BackendUnavailableError
            If the binary cannot be located.
        """
        if self._resolved_path is not None:
            return self._resolved_path
        if self._binary_path is not None:
            p = Path(self._binary_path)
            if not (p.is_file() and os.access(p, os.X_OK)):
                raise BackendUnavailableError(f"binary at {p!s} is not an executable file")
            self._resolved_path = p
            return p
        if not self.BINARY_NAME:
            raise BackendUnavailableError(f"{type(self).__name__} did not set BINARY_NAME")
        which = shutil.which(self.BINARY_NAME)
        if which is None:
            raise BackendUnavailableError(
                f"binary {self.BINARY_NAME!r} not found on PATH; "
                f"install via `conda install -n isalhg -c conda-forge nauty` "
                f"or `sudo apt-get install nauty`"
            )
        self._resolved_path = Path(which)
        return self._resolved_path

    def _invoke(self, payload: str) -> str:
        """Run the binary with ``payload`` on stdin under the configured timeout.

        Returns the binary's stdout text.

        Raises
        ------
        isalhg.errors.BackendTimeoutError
            On timeout.
        isalhg.errors.BackendOutputParseError
            On non-zero exit or non-empty stderr that the subclass cannot
            handle (the default is to surface it here).
        """
        binary = self._resolve_binary()
        try:
            completed = subprocess.run(
                [str(binary)],
                input=payload,
                text=True,
                capture_output=True,
                timeout=self._timeout_s,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise BackendTimeoutError(
                f"{self.BINARY_NAME} exceeded {self._timeout_s:.1f}s budget"
            ) from exc
        if completed.returncode != 0:
            stderr_excerpt = (completed.stderr or "")[:4096]
            raise BackendOutputParseError(
                f"{self.BINARY_NAME} returned code {completed.returncode}; "
                f"stderr: {stderr_excerpt!r}"
            )
        return completed.stdout

    # ------------------------------------------------------------------
    # IsoBackend hooks
    # ------------------------------------------------------------------

    def fingerprint(self, H: SparseHypergraph) -> Fingerprint:
        if H.n_nodes == 0:
            return b""
        return self._parse(self._invoke(self._serialize(H)))

    def are_isomorphic(self, H1: SparseHypergraph, H2: SparseHypergraph) -> bool:
        if H1.n_vertex_labels != H2.n_vertex_labels:
            return False
        if H1.n_edge_labels != H2.n_edge_labels:
            return False
        if H1.n_nodes != H2.n_nodes or H1.n_edges != H2.n_edges:
            return False
        return self.fingerprint(H1) == self.fingerprint(H2)
