"""Canonical-string entry point.

Computes ``w*(H) = argmin_lex { greedy_H2S(H, v_0) : v_0 in argmax_lex xi(v) }``.

This is the canonical form consumed by
:class:`isalhg.iso_backends.isalhg_backend.IsalHGBackend`.

Conjecture: ``w*(H1) == w*(H2)`` iff ``H1`` and ``H2`` are isomorphic.
Empirically validated by the Tier 1 protocol; theoretical proof deferred to
the companion paper.
"""

from __future__ import annotations

from isalhg.core.sparse_hypergraph import SparseHypergraph


def canonical_string(
    H: SparseHypergraph,
    *,
    k: int,
    structural_depth: int = 3,
) -> str:
    """Compute the canonical ``Sigma_HG*`` string of ``H``."""
    raise NotImplementedError
