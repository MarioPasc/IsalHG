"""IsalHG backend.

Wraps the canonical-string algorithm from :mod:`isalhg.core.canonical` behind
the :class:`IsoBackend` interface. The fingerprint is the canonical string
itself, UTF-8 encoded.
"""

from __future__ import annotations

from isalhg.core.canonical import canonical_string, required_k
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.iso_backends.base import IsoBackend
from isalhg.iso_backends.registry import register_backend
from isalhg.types import BackendName, Fingerprint


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

    def fingerprint(self, H: SparseHypergraph) -> Fingerprint:
        k_eff = required_k(H) if self._k is None else self._k
        s = canonical_string(
            H,
            k=k_eff,
            structural_depth=self._structural_depth,
            algorithm=self._algorithm,
        )
        return s.encode("utf-8")

    def are_isomorphic(self, H1: SparseHypergraph, H2: SparseHypergraph) -> bool:
        if H1.n_vertex_labels != H2.n_vertex_labels:
            return False
        if H1.n_edge_labels != H2.n_edge_labels:
            return False
        k_eff = max(required_k(H1), required_k(H2)) if self._k is None else self._k
        s1 = canonical_string(
            H1,
            k=k_eff,
            structural_depth=self._structural_depth,
            algorithm=self._algorithm,
        )
        s2 = canonical_string(
            H2,
            k=k_eff,
            structural_depth=self._structural_depth,
            algorithm=self._algorithm,
        )
        return s1 == s2


# Self-register at import time (per registry pattern, CODE_DESIGN.md §3).
# ``isalhg`` is the legacy alias for the production canonical
# (``greedy_min``); per-algorithm aliases ``isalhg_<name>`` are
# registered for the algorithm-comparison preprint study.
register_backend("isalhg", lambda: IsalHGBackend(algorithm="greedy_min"))
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
