"""Correctness primitives.

Used by Tiers 1, 3, and 5 to verify FP/FN = 0 against ground-truth iso-class
labels and to validate bijection certificates.
"""

from __future__ import annotations

import itertools
from collections.abc import Mapping
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
    ground_truth: Mapping[str, int],
    predicted_pairs: Mapping[tuple[str, str], bool],
) -> ConfusionCounts:
    """Compute pairwise confusion against a ground-truth labelling.

    Parameters
    ----------
    ground_truth : Mapping[str, int]
        ``item_id -> iso_class``. Two items are *truly* iso iff their
        labels are equal.
    predicted_pairs : Mapping[tuple[str, str], bool]
        ``(item_id_a, item_id_b) -> backend.are_isomorphic(...)``. Each
        unordered pair appears at most once; the key tuple's element
        order is irrelevant — both ``(a, b)`` and ``(b, a)`` are
        consulted before declaring a pair missing.

    Raises
    ------
    KeyError
        If a pair ``(a, b)`` with ``a != b in ground_truth`` has no
        prediction under either orientation.
    """
    items = sorted(ground_truth.keys())
    tp = fp = tn = fn = 0
    for a, b in itertools.combinations(items, 2):
        if (a, b) in predicted_pairs:
            pred = predicted_pairs[(a, b)]
        elif (b, a) in predicted_pairs:
            pred = predicted_pairs[(b, a)]
        else:
            raise KeyError(f"missing prediction for unordered pair ({a!r}, {b!r})")
        truth = ground_truth[a] == ground_truth[b]
        if truth and pred:
            tp += 1
        elif not truth and pred:
            fp += 1
        elif truth and not pred:
            fn += 1
        else:
            tn += 1
    return ConfusionCounts(
        true_positive=tp,
        false_positive=fp,
        true_negative=tn,
        false_negative=fn,
    )


def verify_bijection_certificate(
    H1: SparseHypergraph,
    H2: SparseHypergraph,
    sigma: Mapping[NodeId, NodeId],
) -> bool:
    """Check that ``sigma`` maps every hyperedge of ``H1`` to one of ``H2``.

    A valid certificate is a vertex bijection ``sigma: V(H1) -> V(H2)`` such
    that ``{sigma(e) : e in E(H1)} == E(H2)``. Edge-label preservation is
    required when both hypergraphs use a non-trivial vocabulary.

    Returns ``False`` (rather than raising) on any structural mismatch so
    protocols can record the failure as a metric.
    """
    if H1.n_nodes != H2.n_nodes:
        return False
    if H1.n_edges != H2.n_edges:
        return False
    if H1.n_vertex_labels != H2.n_vertex_labels:
        return False
    if H1.n_edge_labels != H2.n_edge_labels:
        return False

    keys = set(sigma.keys())
    if keys != set(range(H1.n_nodes)):
        return False
    values = set(sigma.values())
    if values != set(range(H2.n_nodes)):
        return False

    # Vertex-label preservation.
    for v in range(H1.n_nodes):
        if H1.vertex_label(v) != H2.vertex_label(sigma[v]):
            return False

    # Edge-set preservation, including edge-label match.
    h2_edges: dict[tuple[int, frozenset[NodeId]], int] = {}
    for _, members, ell in H2.iter_edges():
        h2_edges[(ell, members)] = h2_edges.get((ell, members), 0) + 1
    for _, members, ell in H1.iter_edges():
        mapped = frozenset(sigma[v] for v in members)
        key = (ell, mapped)
        if h2_edges.get(key, 0) == 0:
            return False
        h2_edges[key] -= 1
    return all(count == 0 for count in h2_edges.values())
