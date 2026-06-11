"""Correctness primitives.

Used by Tiers 1, 3, and 5 to verify FP/FN = 0 against ground-truth iso-class
labels and to validate bijection certificates.
"""

from __future__ import annotations

from dataclasses import dataclass

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.types import NodeId


@dataclass(frozen=True)
class ConfusionCounts:
    """Pairwise FP/FN/TP/TN counters."""

    true_positive: int
    false_positive: int
    true_negative: int
    false_negative: int

    @property
    def total(self) -> int:
        return self.true_positive + self.false_positive + self.true_negative + self.false_negative


def confusion_from_partitions(
    ground_truth: dict[str, int],
    predicted_pairs: dict[tuple[str, str], bool],
) -> ConfusionCounts:
    """Compute pairwise confusion against a ground-truth labelling.

    Parameters
    ----------
    ground_truth : dict[str, int]
        ``item_id -> iso_class``.
    predicted_pairs : dict[tuple[str, str], bool]
        ``(item_id_a, item_id_b) -> backend.are_isomorphic(...)`` for every
        unordered pair.
    """
    raise NotImplementedError


def verify_bijection_certificate(
    H1: SparseHypergraph,
    H2: SparseHypergraph,
    sigma: dict[NodeId, NodeId],
) -> bool:
    """Check that ``sigma`` maps every hyperedge of ``H1`` to one of ``H2``.

    A valid certificate is a vertex bijection ``sigma: V(H1) -> V(H2)`` such
    that ``{sigma(e) : e in E(H1)} == E(H2)``.
    """
    raise NotImplementedError
