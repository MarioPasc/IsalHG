"""Partition-comparison primitives used by Tier 5.

Each backend produces an iso-equivalence partition of a dataset (items
grouped by fingerprint). This module computes inter-partition agreement.
"""

from __future__ import annotations

from collections.abc import Iterable

from isalhg.types import BackendName


def partition_from_fingerprints(items: Iterable[tuple[str, bytes]]) -> dict[bytes, list[str]]:
    """Group ``(item_id, fingerprint)`` pairs by fingerprint bytes."""
    raise NotImplementedError


def partitions_agree(
    p1: dict[bytes, list[str]],
    p2: dict[bytes, list[str]],
) -> bool:
    """Return True iff ``p1`` and ``p2`` induce identical equivalence classes.

    Equality compares the resulting set-of-sets of ``item_id`` groups, ignoring
    the differing fingerprint byte values across backends.
    """
    raise NotImplementedError


def agreement_matrix(
    partitions: dict[BackendName, dict[bytes, list[str]]],
) -> dict[tuple[BackendName, BackendName], bool]:
    """Cross-backend pairwise agreement on the same dataset."""
    raise NotImplementedError
