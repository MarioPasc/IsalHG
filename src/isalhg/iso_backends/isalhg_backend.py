"""IsalHG backend.

Wraps the canonical-string algorithm from :mod:`isalhg.core.canonical` behind
the :class:`IsoBackend` interface.

Fingerprint
-----------
The fingerprint is the *augmented* fingerprint ``F(H) = (seed label, w*(H))``
of Theorem A, UTF-8 encoded. ``w*`` never emits the label of its own seed
vertex, so on a non-trivial vertex vocabulary two non-isomorphic hypergraphs
can share it -- the labels ``(0, 0)`` and ``(1, 0)`` over a single edge are the
minimal witness. The seed label separates them.

On a trivial vocabulary (``n_vertex_labels == 1``) the seed label is
identically ``0`` and is omitted, so the fingerprint is byte-identical to the
bare canonical string. ``are_isomorphic`` refuses to compare hypergraphs whose
vocabularies differ, so both sides of a comparison always agree on the format.

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

from isalhg.core.canonical import canonical_string, required_k, seed_vertex_label
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.iso_backends.base import IsoBackend
from isalhg.iso_backends.registry import register_backend
from isalhg.types import BackendName, Fingerprint

# Separates the seed label from the canonical string in a labelled fingerprint.
# Absent from the ``Sigma_HG`` grammar, so the two components stay recoverable.
_SEED_LABEL_SEP = "|"


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
        queue.put(("ok", s))
    except BaseException as exc:  # noqa: BLE001 - report any failure mode
        queue.put(("err", f"{type(exc).__name__}: {exc}"))


def _canonical_string_isolated(
    H: SparseHypergraph,
    *,
    k: int | None,
    structural_depth: int,
    algorithm: str,
) -> str:
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
    return str(payload)


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
    algorithm : str
        Canonical-string variant (invariant 4). Defaults to
        ``"greedy_min_complete"`` -- the unpruned tie-complete lex-min
        ``w*_c`` over the neighbour-degree seed cascade, for which
        fingerprint equality is *exact* on connected inputs (Theorem A;
        D-TA1/T-TAd). The greedy variants remain sound one-sided tests
        (equal fingerprints certify isomorphism, unequal ones are
        inconclusive on tie-degenerate inputs); ``greedy_single*``
        variants additionally trade seed soundness for speed and must not
        be used where an exact iso decision is required.
    """

    def __init__(
        self,
        *,
        k: int | None = None,
        structural_depth: int = 3,
        algorithm: str = "greedy_min_complete",
    ) -> None:
        self._k = k
        self._structural_depth = structural_depth
        self._algorithm = algorithm

    @property
    def name(self) -> BackendName:
        return f"isalhg_{self._algorithm}"

    def _canonical_string(self, H: SparseHypergraph, k_eff: int) -> str:
        if os.environ.get("ISALHG_BACKEND_ISOLATE", "0") == "1":
            return _canonical_string_isolated(
                H,
                k=k_eff,
                structural_depth=self._structural_depth,
                algorithm=self._algorithm,
            )
        return canonical_string(
            H,
            k=k_eff,
            structural_depth=self._structural_depth,
            algorithm=self._algorithm,
        )

    def _fingerprint_bytes(self, H: SparseHypergraph, k_eff: int) -> bytes:
        w = self._canonical_string(H, k_eff)
        if H.n_vertex_labels == 1:
            return w.encode("utf-8")
        return f"{seed_vertex_label(H, w)}{_SEED_LABEL_SEP}{w}".encode()

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
# ``isalhg`` is the alias for the production canonical; per-algorithm
# aliases ``isalhg_<name>`` are registered for the algorithm-comparison
# preprint study.
#
# Default algorithm is ``greedy_min_complete`` (D-TA1, flipped at T-TAd):
# the unpruned tie-complete lex-min ``w*_c``, the only variant whose
# fingerprint equality is exact on connected inputs (Theorem A; frozen at
# D-TA2).
#
# ``ISALHG_ALGORITHM`` env var overrides the default algorithm bound to
# the ``"isalhg"`` registry name. Used by the preprint Picasso pipeline
# to pin ``greedy_single`` when the multi-seed variants are empirically
# too slow (they backtrack over label-class permutations and are
# exponential on dense random ER hypergraphs -- open question #1 in
# docs/engineering/DEVELOPMENT.md; the neighbour-degree seed set shrinks
# the seed count but does not change that inner-loop cost). A pipeline
# that sets the env var is therefore unaffected by the default flip.
_DEFAULT_ISALHG_ALGORITHM = os.environ.get("ISALHG_ALGORITHM", "greedy_min_complete")
register_backend("isalhg", lambda: IsalHGBackend(algorithm=_DEFAULT_ISALHG_ALGORITHM))
for _algo in (
    "greedy_min",
    "greedy_single",
    "exhaustive",
    "greedy_min_inplace",
    "greedy_min_wl_pruned",
    "greedy_min_inplace_wl_pruned",
    "greedy_min_nbrdeg",
    "greedy_single_nbrdeg",
    "greedy_min_complete",
    "pruned_exhaustive",
):
    register_backend(
        f"isalhg_{_algo}",
        lambda algo=_algo: IsalHGBackend(algorithm=algo),
    )
del _algo
