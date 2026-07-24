"""Shared base for distances computed via a pinned conda-env subprocess.

Mirrors :class:`isalhg.iso_backends.subprocess_base.SubprocessIsoBackend`
but for *whole-corpus* distance-matrix computation instead of per-hypergraph
fingerprints.  The flow is:

1. Serialise the corpus to a temporary JSON file.
2. Shell out to a dedicated conda env's Python running a worker script.
3. Parse back the dense distance matrix from a second temporary JSON file.
4. Delete both temporary files.

The pinned env is identified by the ``PINNED_ENV`` class attribute (conda
env name).  The worker script path is identified by ``WORKER_SCRIPT``.

Serialisation schema
--------------------
Input to the worker (``_serialise_corpus`` output):

.. code-block:: json

    {
        "corpus": [
            {
                "n_nodes": 7,
                "n_vertex_labels": 1,
                "n_edge_labels": 1,
                "vertex_labels": [0, 0, 0, 0, 0, 0, 0],
                "edge_members": [[0, 1, 3], [1, 2, 4], ...]
            }
        ]
    }

Output from the worker:

.. code-block:: json

    {"matrix": [[0.0, 1.5, ...], ...]}

Restriction: Python stdlib only (no numpy at module import time).
"""

from __future__ import annotations

import contextlib
import json
import os
import subprocess
import tempfile
from abc import abstractmethod
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.errors import RepresentationDependencyMissingError, SubprocessRepresentationError
from isalhg.metric_space.base import HypergraphDistance

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray


def _serialise_corpus(corpus: Sequence[SparseHypergraph]) -> dict[str, object]:
    """Serialise a corpus of hypergraphs to a plain JSON-serialisable dict.

    Parameters
    ----------
    corpus : Sequence[SparseHypergraph]
        The hypergraphs to serialise.

    Returns
    -------
    dict
        JSON-ready representation following the schema in the module docstring.
    """
    items = []
    for H in corpus:
        vertex_labels = [H.vertex_label(v) for v in range(H.n_nodes)]
        edge_members: list[list[int]] = []
        for _, members, _ in H.iter_edges():
            edge_members.append(sorted(members))
        items.append(
            {
                "n_nodes": H.n_nodes,
                "n_vertex_labels": H.n_vertex_labels,
                "n_edge_labels": H.n_edge_labels,
                "vertex_labels": vertex_labels,
                "edge_members": edge_members,
            }
        )
    return {"corpus": items}


class SubprocessRepresentation(HypergraphDistance):
    """Abstract base for distances computed via a pinned conda-env subprocess.

    Concrete subclasses declare:

    ``PINNED_ENV`` — conda env name (e.g. ``"isalhg-hypercot"``).  The Python
    executable is assumed to live at
    ``~/.conda/envs/{PINNED_ENV}/bin/python``.

    ``WORKER_SCRIPT`` — absolute path to the Python worker script that runs
    inside the pinned env.

    Both class attributes must be non-empty strings; ``SubprocessRepresentationError``
    is raised at call time if either is absent or the env/script cannot be
    located.

    Raises
    ------
    isalhg.errors.SubprocessRepresentationError
        When the pinned env Python is absent, the worker script is missing,
        or the subprocess exits non-zero or times out.
    """

    PINNED_ENV: ClassVar[str] = ""
    WORKER_SCRIPT: ClassVar[str] = ""
    DEFAULT_TIMEOUT_S: ClassVar[float] = 3600.0

    def __init__(self, timeout_s: float | None = None) -> None:
        """Create the representation.

        Parameters
        ----------
        timeout_s : float or None, optional
            Wall-clock budget in seconds for the subprocess call.
            ``None`` uses :attr:`DEFAULT_TIMEOUT_S` (1 hour).
        """
        self._timeout_s: float = timeout_s if timeout_s is not None else self.DEFAULT_TIMEOUT_S
        self._resolved_python: Path | None = None

    # ------------------------------------------------------------------
    # Extension point
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier used in registries and result records."""
        ...

    # ------------------------------------------------------------------
    # Env / script discovery
    # ------------------------------------------------------------------

    def _python_path(self) -> Path:
        """Canonical path to the pinned env's Python executable.

        Probes ``~/.conda/envs/<env>`` first (local convention), then
        ``~/fscratch/conda_envs/<env>`` (Picasso convention, where conda
        is configured to store envs on the fast scratch filesystem).
        """
        if not self.PINNED_ENV:
            raise SubprocessRepresentationError(f"{type(self).__name__} did not set PINNED_ENV")
        home = Path.home()
        candidates = [
            home / ".conda" / "envs" / self.PINNED_ENV / "bin" / "python",
            home / "fscratch" / "conda_envs" / self.PINNED_ENV / "bin" / "python",
        ]
        for p in candidates:
            if p.is_file() and os.access(p, os.X_OK):
                return p
        # None found — return the default path so _resolve_python raises a
        # descriptive error referencing the conventional location.
        return candidates[0]

    def _resolve_python(self) -> Path:
        """Locate the pinned env's Python, caching the result.

        Raises
        ------
        isalhg.errors.SubprocessRepresentationError
            When the Python executable is absent or not executable.
        """
        if self._resolved_python is not None:
            return self._resolved_python
        p = self._python_path()
        if not (p.is_file() and os.access(p, os.X_OK)):
            raise SubprocessRepresentationError(
                f"Pinned-env Python not found at {p}.\n"
                "Build it with:\n"
                "  conda env create -f envs/hypercot.yml\n"
                "  git clone https://github.com/samirchowdhury/HyperCOT /tmp/HyperCOT\n"
                "  ~/.conda/envs/isalhg-hypercot/bin/pip install -e /tmp/HyperCOT"
            )
        self._resolved_python = p
        return p

    def _resolve_worker(self) -> Path:
        """Locate the worker script.

        Raises
        ------
        isalhg.errors.SubprocessRepresentationError
            When :attr:`WORKER_SCRIPT` is unset or the file does not exist.
        """
        if not self.WORKER_SCRIPT:
            raise SubprocessRepresentationError(f"{type(self).__name__} did not set WORKER_SCRIPT")
        p = Path(self.WORKER_SCRIPT)
        if not p.is_file():
            raise SubprocessRepresentationError(f"Worker script not found: {p}")
        return p

    # ------------------------------------------------------------------
    # HypergraphDistance interface
    # ------------------------------------------------------------------

    def matrix(self, corpus: Sequence[SparseHypergraph]) -> NDArray[np.float64]:
        """Compute the dense pairwise distance matrix via one subprocess call.

        Parameters
        ----------
        corpus : Sequence[SparseHypergraph]
            The hypergraphs to embed.  Row/column ``i`` corresponds to
            ``corpus[i]``.

        Returns
        -------
        numpy.ndarray
            Symmetric ``(len(corpus), len(corpus))`` ``float64`` matrix with
            a zero diagonal.

        Raises
        ------
        isalhg.errors.SubprocessRepresentationError
            On missing env, missing worker, timeout, non-zero exit, or
            malformed output.
        isalhg.errors.RepresentationDependencyMissingError
            If ``numpy`` is not installed.
        """
        try:
            import numpy as np
        except ImportError as exc:
            raise RepresentationDependencyMissingError(
                "numpy is required for SubprocessRepresentation.matrix(); "
                "install via `pip install numpy`"
            ) from exc

        n = len(corpus)
        if n == 0:
            return np.zeros((0, 0), dtype=np.float64)

        python = self._resolve_python()
        worker = self._resolve_worker()
        payload = _serialise_corpus(corpus)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as fin:
            json.dump(payload, fin)
            input_path = fin.name

        output_path = input_path + ".out.json"

        try:
            completed = subprocess.run(
                [str(python), str(worker), input_path, output_path],
                text=True,
                capture_output=True,
                timeout=self._timeout_s,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise SubprocessRepresentationError(
                f"{self.name} subprocess exceeded {self._timeout_s:.1f}s budget"
            ) from exc
        finally:
            with contextlib.suppress(OSError):
                os.unlink(input_path)

        if completed.returncode != 0:
            stderr = (completed.stderr or "")[:4096]
            raise SubprocessRepresentationError(
                f"{self.name} worker returned code {completed.returncode}; stderr: {stderr!r}"
            )

        try:
            with open(output_path) as fout:
                result = json.load(fout)
            flat = result["matrix"]
            mat = np.array(flat, dtype=np.float64)
        except (KeyError, ValueError, OSError) as exc:
            raise SubprocessRepresentationError(
                f"{self.name} worker produced malformed output: {exc}"
            ) from exc
        finally:
            with contextlib.suppress(OSError):
                os.unlink(output_path)

        if mat.shape != (n, n):
            raise SubprocessRepresentationError(
                f"{self.name} worker returned matrix of shape {mat.shape}, expected ({n}, {n})"
            )
        return mat

    def pairwise(self, H1: SparseHypergraph, H2: SparseHypergraph) -> float:
        """Compute the pairwise distance by delegating to :meth:`matrix`.

        Implemented as ``matrix([H1, H2])[0, 1]``.

        Parameters
        ----------
        H1, H2 : SparseHypergraph
            The two hypergraphs to compare.

        Returns
        -------
        float
            Non-negative dissimilarity.
        """
        mat = self.matrix([H1, H2])
        return float(mat[0, 1])
