"""Abstract base class for H2S (hypergraph-to-string) algorithm variants.

All H2S variants take a hypergraph and return a ``Sigma_HG*`` token
sequence. They differ in how they pick seed nodes and how exhaustively
they explore the tie-breaking tree.

Concrete classes are not registered through a registry pattern (these
are not extension points consumed by experiment configs -- they are
internal strategies driven by :mod:`isalhg.core.canonical`).

Restriction: ZERO external dependencies. Only Python stdlib + abc +
isalhg.core.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.core.string_to_hypergraph import StringToHypergraph
from isalhg.core.trace import AlgorithmTrace
from isalhg.types import TokenSequence


class H2SAlgorithm(ABC):
    """Abstract hypergraph-to-string algorithm."""

    @abstractmethod
    def encode(self, H: SparseHypergraph) -> TokenSequence:
        """Convert ``H`` to a ``Sigma_HG*`` token sequence."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier for this algorithm variant."""
        ...

    def encode_with_trace(
        self,
        H: SparseHypergraph,
    ) -> tuple[TokenSequence, AlgorithmTrace]:
        """Encode ``H`` and return both the token sequence and a step-by-step trace.

        Default implementation: call :meth:`encode` to obtain the canonical
        token sequence, then replay it through :class:`StringToHypergraph`
        with ``direction="h2s"``. The round-trip invariant
        ``S2H(H2S(H)) ~ H`` guarantees that the per-step states observed
        during the replay match the H2S algorithm's emission states.

        Concrete subclasses may override to record an internal trace (for
        example, an exhaustive algorithm could record the search tree).

        Returns
        -------
        (TokenSequence, AlgorithmTrace)
            The canonical token sequence and the ``h2s``-labelled trace.
        """
        tokens = self.encode(H)
        k = self._infer_k_for_replay(H)
        interpreter = StringToHypergraph(
            tokens,
            k=k,
            n_vertex_labels=H.n_vertex_labels,
            n_edge_labels=H.n_edge_labels,
        )
        _, trace = interpreter.run_with_trace(direction="h2s")
        return tokens, trace

    def _infer_k_for_replay(self, H: SparseHypergraph) -> int:
        """Return the ``k`` value to use when replaying through S2H.

        Concrete algorithms that carry a ``k`` attribute should expose it
        via the ``k`` property; the default uses that attribute when
        available, otherwise falls back to ``max(2, max_arity(H))``.
        """
        k_attr = getattr(self, "k", None)
        if isinstance(k_attr, int) and k_attr >= 1:
            return k_attr
        if H.n_edges == 0:
            return 2
        return max(2, max(len(H.members(e)) for e in H.edges()))

    def __repr__(self) -> str:
        return f"{type(self).__name__}()"
