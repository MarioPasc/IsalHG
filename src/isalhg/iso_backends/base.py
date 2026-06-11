"""Abstract base class for hypergraph isomorphism backends.

Every backend (IsalHG, nauty-via-Levi, Traces-via-Levi, bliss-via-Levi)
exposes the same minimal interface so the experiment orchestrator can treat
them interchangeably. The interface is the same one quoted in
``docs/PROPOSAL.md`` (Section "Tier 5 architecture -- pluggable IsoBackend").

Restriction: only Python stdlib + abc + typing + isalhg.core.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.types import BackendName, Fingerprint, NodeId


class IsoBackend(ABC):
    """Abstract hypergraph-isomorphism backend.

    Concrete subclasses must implement :meth:`fingerprint`, :meth:`are_isomorphic`,
    and the :attr:`name` property. They may override :meth:`bijection_certificate`
    when the underlying algorithm yields an explicit vertex permutation.
    """

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def name(self) -> BackendName:
        """Short identifier used in registries, configs, and result records."""
        ...

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    @abstractmethod
    def fingerprint(self, H: SparseHypergraph) -> Fingerprint:
        """Return a canonical byte string for ``H``.

        Parameters
        ----------
        H : SparseHypergraph
            Connected hypergraph in the in-memory representation defined by
            :class:`isalhg.core.sparse_hypergraph.SparseHypergraph`.

        Returns
        -------
        Fingerprint
            Bytes such that ``fingerprint(H1) == fingerprint(H2)`` whenever
            ``H1`` and ``H2`` are isomorphic and (within this backend) only
            then.
        """
        ...

    @abstractmethod
    def are_isomorphic(self, H1: SparseHypergraph, H2: SparseHypergraph) -> bool:
        """Decide whether two hypergraphs are isomorphic.

        Implementations may either delegate to fingerprint equality or call a
        native pairwise routine; the abstract layer enforces no preference.
        """
        ...

    # ------------------------------------------------------------------
    # Optional operations
    # ------------------------------------------------------------------

    def bijection_certificate(
        self, H1: SparseHypergraph, H2: SparseHypergraph
    ) -> dict[NodeId, NodeId] | None:
        """Return a vertex bijection witnessing ``H1 ~ H2`` if available.

        Default implementation returns ``None``. Backends that can produce a
        canonical permutation (nauty, Traces, bliss) override this. Callers
        must tolerate ``None`` for backends that only emit a fingerprint.
        """
        return None

    # ------------------------------------------------------------------
    # Plumbing
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"
