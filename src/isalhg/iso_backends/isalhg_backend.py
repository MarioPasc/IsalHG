"""IsalHG backend.

Wraps the canonical-string algorithm from :mod:`isalhg.core.canonical` behind
the :class:`IsoBackend` interface. The fingerprint is the canonical string
itself, UTF-8 encoded.

Subprocess isolation
--------------------
Set the environment variable ``ISALHG_BACKEND_ISOLATE=1`` to run the
canonical-string call in a child process (``multiprocessing.Process``).
A crash in the C++ extension (SIGSEGV/SIGABRT, e.g. on dense Erdős-Rényi
inputs) then surfaces as a Python ``IsalHGBackendCrashError`` in the
parent rather than killing the SLURM task. The protocol layer maps that
to a DNF record. Overhead is one fork + one IPC roundtrip per call
(~50-200 ms); negligible relative to the fingerprint cost on cells
where the C++ extension is liable to crash.
"""

from __future__ import annotations

import multiprocessing as _mp
import os

from isalhg.core.canonical import canonical_string, required_k
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.iso_backends.base import IsoBackend
from isalhg.iso_backends.registry import register_backend
from isalhg.types import BackendName, Fingerprint


class IsalHGBackendCrashError(RuntimeError):
    """Raised when the isolated canonical-string subprocess dies abnormally."""


def _fingerprint_worker(
    queue,
    H: SparseHypergraph,
    *,
    k: int | None,
    structural_depth: int,
    algorithm: str,
) -> None:
    try:
        s = canonical_string(H, k=k, structural_depth=structural_depth, algorithm=algorithm)
        queue.put(("ok", s.encode("utf-8")))
    except BaseException as exc:  # noqa: BLE001 - report any failure mode
        queue.put(("err", f"{type(exc).__name__}: {exc}"))


def _fingerprint_isolated(
    H: SparseHypergraph,
    *,
    k: int | None,
    structural_depth: int,
    algorithm: str,
) -> bytes:
    # Per-call hard timeout: ISALHG_SUBPROC_TIMEOUT_S (default 600). Enforced
    # here rather than via the protocol's outer signal.alarm because
    # ``Process.join()`` is not always interruptible by SIGALRM, leaving
    # orphaned child processes spinning long after the parent gives up.
    timeout_s = float(os.environ.get("ISALHG_SUBPROC_TIMEOUT_S", "600"))
    ctx = _mp.get_context("fork")
    queue: _mp.Queue = ctx.Queue(maxsize=1)
    proc = ctx.Process(
        target=_fingerprint_worker,
        args=(queue,),
        kwargs={
            "H": H,
            "k": k,
            "structural_depth": structural_depth,
            "algorithm": algorithm,
        },
    )
    proc.start()
    proc.join(timeout=timeout_s)
    if proc.is_alive():
        proc.terminate()
        proc.join(timeout=5.0)
        if proc.is_alive():
            proc.kill()
            proc.join(timeout=5.0)
        raise TimeoutError(f"canonical_string subprocess exceeded {timeout_s:g}s; terminated.")
    if proc.exitcode != 0:
        # SIGSEGV (signal 11) reports exitcode -11 in multiprocessing.
        raise IsalHGBackendCrashError(
            f"canonical_string subprocess exit={proc.exitcode}; "
            "likely SIGSEGV/SIGABRT in the C++ extension."
        )
    if queue.empty():
        raise IsalHGBackendCrashError("canonical_string subprocess produced no result before exit.")
    status, payload = queue.get()
    if status == "err":
        raise RuntimeError(payload)
    return payload


class IsalHGBackend(IsoBackend):
    """``IsoBackend`` adapter for the IsalHG canonical-string algorithm.

    Parameters
    ----------
    k : int or None
        Maximum hyperedge arity supported. When ``None`` (default) the
        backend chooses ``k`` per-call via :func:`isalhg.core.canonical.required_k`.
        Two hypergraphs compared via :meth:`are_isomorphic` MUST share the
        same effective ``k``; the default of ``None`` ensures this by
        taking the max over both inputs.
    structural_depth : int
        Depth of the ``xi`` / ``eta`` structural tuples (invariant 8).
    """

    def __init__(
        self,
        *,
        k: int | None = None,
        structural_depth: int = 3,
        algorithm: str = "greedy_min",
    ) -> None:
        self._k = k
        self._structural_depth = structural_depth
        self._algorithm = algorithm

    @property
    def name(self) -> BackendName:
        return f"isalhg_{self._algorithm}"

    def _fingerprint_bytes(self, H: SparseHypergraph, k_eff: int) -> bytes:
        if os.environ.get("ISALHG_BACKEND_ISOLATE", "0") == "1":
            return _fingerprint_isolated(
                H,
                k=k_eff,
                structural_depth=self._structural_depth,
                algorithm=self._algorithm,
            )
        s = canonical_string(
            H,
            k=k_eff,
            structural_depth=self._structural_depth,
            algorithm=self._algorithm,
        )
        return s.encode("utf-8")

    def fingerprint(self, H: SparseHypergraph) -> Fingerprint:
        k_eff = required_k(H) if self._k is None else self._k
        return self._fingerprint_bytes(H, k_eff)

    def are_isomorphic(self, H1: SparseHypergraph, H2: SparseHypergraph) -> bool:
        if H1.n_vertex_labels != H2.n_vertex_labels:
            return False
        if H1.n_edge_labels != H2.n_edge_labels:
            return False
        k_eff = max(required_k(H1), required_k(H2)) if self._k is None else self._k
        return self._fingerprint_bytes(H1, k_eff) == self._fingerprint_bytes(H2, k_eff)


# Self-register at import time (per registry pattern, CODE_DESIGN.md §3).
# ``isalhg`` is the legacy alias for the production canonical
# (``greedy_min``); per-algorithm aliases ``isalhg_<name>`` are
# registered for the algorithm-comparison preprint study.
#
# ``ISALHG_ALGORITHM`` env var overrides the default algorithm bound to
# the ``"isalhg"`` registry name. Used by the preprint Picasso pipeline
# to swap in ``greedy_single`` when ``greedy_min`` is empirically too
# slow (it backtracks over label-class permutations and is exponential
# on dense random ER hypergraphs; open question #1 in DEVELOPMENT.md).
_DEFAULT_ISALHG_ALGORITHM = os.environ.get("ISALHG_ALGORITHM", "greedy_min")
register_backend("isalhg", lambda: IsalHGBackend(algorithm=_DEFAULT_ISALHG_ALGORITHM))
for _algo in (
    "greedy_min",
    "greedy_single",
    "exhaustive",
    "greedy_min_inplace",
    "greedy_min_wl_pruned",
    "greedy_min_inplace_wl_pruned",
    "pruned_exhaustive",
):
    register_backend(
        f"isalhg_{_algo}",
        lambda algo=_algo: IsalHGBackend(algorithm=algo),
    )
del _algo
