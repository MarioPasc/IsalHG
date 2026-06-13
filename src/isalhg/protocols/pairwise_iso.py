"""Pairwise isomorphism protocol -- Tiers 1 and 3.

Iterates over the dataset's ``DatasetItem`` cross-product, queries
``backend.are_isomorphic`` for every pair, and records
``(false_positives, false_negatives, per_pair_wall_clock_s)`` against the
ground-truth ``iso_class`` labels.

Tier 1 sets a tight time budget; Tier 3 sets a 600 s per-instance timeout.
Both use the same protocol class; the orchestrator differentiates them by
parameters.
"""

from __future__ import annotations

import itertools
import time
from dataclasses import asdict
from typing import Any

from isalhg.datasets.base import HypergraphDataset
from isalhg.errors import ProtocolPreconditionError
from isalhg.iso_backends.base import IsoBackend
from isalhg.metrics.correctness import (
    confusion_from_partitions,
    verify_bijection_certificate,
)
from isalhg.protocols.base import BenchmarkProtocol, ProtocolResult
from isalhg.protocols.registry import register_protocol
from isalhg.types import ProtocolName, Seed


class PairwiseIsoProtocol(BenchmarkProtocol):
    """Pairwise isomorphism decision over a labelled dataset."""

    def __init__(self, *, timeout_s: float = 600.0, check_bijection: bool = True) -> None:
        """Configure per-pair timeout and whether to verify bijection certificates."""
        self._timeout_s = float(timeout_s)
        self._check_bijection = bool(check_bijection)

    @property
    def name(self) -> ProtocolName:
        return "pairwise_iso"

    def measure(
        self,
        backend: IsoBackend,
        dataset: HypergraphDataset,
        seed: Seed,
    ) -> ProtocolResult:
        if not dataset.metadata.has_iso_labels:
            raise ProtocolPreconditionError(
                f"PairwiseIsoProtocol requires has_iso_labels=True; "
                f"dataset {dataset.name!r} has no ground-truth iso classes"
            )

        items = list(dataset.seed(seed))
        if any(item.iso_class is None for item in items):
            raise ProtocolPreconditionError(
                f"dataset {dataset.name!r} declares has_iso_labels but yielded "
                f"items with iso_class=None"
            )

        ground_truth: dict[str, int] = {item.item_id: int(item.iso_class) for item in items}  # type: ignore[arg-type]
        item_by_id = {item.item_id: item for item in items}

        predicted: dict[tuple[str, str], bool] = {}
        per_pair_times: list[dict[str, Any]] = []
        timeouts: list[tuple[str, str]] = []
        bijection_violations: list[dict[str, Any]] = []

        total_start = time.perf_counter()
        for a, b in itertools.combinations(sorted(item_by_id.keys()), 2):
            pair_start = time.perf_counter()
            pred = backend.are_isomorphic(item_by_id[a].hypergraph, item_by_id[b].hypergraph)
            pair_wall = time.perf_counter() - pair_start
            predicted[(a, b)] = bool(pred)
            per_pair_times.append(
                {"pair": (a, b), "wall_s": pair_wall, "predicted_iso": bool(pred)}
            )
            if pair_wall > self._timeout_s:
                timeouts.append((a, b))

            if pred and self._check_bijection:
                cert = backend.bijection_certificate(
                    item_by_id[a].hypergraph, item_by_id[b].hypergraph
                )
                if cert is not None:
                    ok = verify_bijection_certificate(
                        item_by_id[a].hypergraph,
                        item_by_id[b].hypergraph,
                        cert,
                    )
                    if not ok:
                        bijection_violations.append(
                            {"pair": (a, b), "reason": "certificate_invalid"}
                        )

        wall_clock_s = time.perf_counter() - total_start
        counts = confusion_from_partitions(ground_truth, predicted)

        measurements: dict[str, Any] = {
            "confusion": asdict(counts),
            "n_items": len(items),
            "n_pairs": len(items) * (len(items) - 1) // 2,
            "timeouts": timeouts,
            "bijection_violations": bijection_violations,
            "per_pair_summary": {
                "count": len(per_pair_times),
                "wall_s_total": sum(p["wall_s"] for p in per_pair_times),
                "wall_s_max": max((p["wall_s"] for p in per_pair_times), default=0.0),
            },
        }
        return ProtocolResult(
            protocol=self.name,
            backend=backend.name,
            dataset=dataset.name,
            seed=seed,
            wall_clock_s=wall_clock_s,
            measurements=measurements,
        )


def _factory(params: dict[str, Any]) -> BenchmarkProtocol:
    return PairwiseIsoProtocol(
        timeout_s=float(params.get("timeout_s", 600.0)),
        check_bijection=bool(params.get("check_bijection", True)),
    )


register_protocol("pairwise_iso", _factory)
