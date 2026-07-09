"""Symmetric-design cohort for the algorithm-comparison study.

Yields the canonical small Steiner systems and generalised quadrangle
used as torture-test fixtures throughout the codebase: Fano STS(7),
STS(9)=AG(2,3), a non-isomorphic pair of cyclic triple systems on 13
points, and GQ(2,2) (the doily). The structures are built by
:mod:`isalhg.datasets.synthetic.designs`, which is also what
``tests/conftest.py`` uses; this module only exposes them as a registered
:class:`HypergraphDataset` so the orchestrator can iterate them like any
other dataset.

All hypergraphs are 3-uniform, deterministic, and unlabelled (trivial
vocabulary). The dataset's ``seed`` is a no-op.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.datasets.base import HypergraphDataset
from isalhg.datasets.registry import register_dataset
from isalhg.datasets.schemas import DatasetItem, DatasetMetadata, LabelVocabulary
from isalhg.datasets.synthetic.designs import (
    cyclic_sts_13,
    fano_plane,
    gq_2_2_doily,
    sts_9,
)
from isalhg.types import DatasetName, Seed

_FIXTURES: tuple[tuple[str, SparseHypergraph], ...] = (
    ("fano_sts7", fano_plane()),
    ("sts9", sts_9()),
    ("sts13_cyclic_014", cyclic_sts_13((0, 1, 4))),
    ("sts13_cyclic_016", cyclic_sts_13((0, 1, 6))),
    ("gq_2_2_doily", gq_2_2_doily()),
)


class SymmetricDesigns(HypergraphDataset):
    """Five hand-built symmetric designs, deterministic, 3-uniform."""

    def __init__(self) -> None:
        pass

    @property
    def name(self) -> DatasetName:
        return "symmetric_designs"

    @property
    def metadata(self) -> DatasetMetadata:
        n_nodes = [H.n_nodes for _, H in _FIXTURES]
        return DatasetMetadata(
            name=self.name,
            n_items=len(_FIXTURES),
            arity_range=(3, 3),
            n_nodes_range=(min(n_nodes), max(n_nodes)),
            has_iso_labels=False,
            source="hand-built; Fano/STS(9)/cyclic-13-pair/GQ(2,2)",
            citation=("Beth-Jungnickel-Lenz 1999; Hall 1986; Sylvester 1861; Payne-Thas 2009"),
            label_vocabulary=LabelVocabulary.trivial(),
        )

    def __iter__(self) -> Iterator[DatasetItem]:
        for name, H in _FIXTURES:
            yield DatasetItem(
                item_id=name,
                hypergraph=H,
                iso_class=None,
                extra={"design": name, "n_nodes": H.n_nodes, "n_edges": H.n_edges},
            )

    def __len__(self) -> int:
        return len(_FIXTURES)

    def seed(self, seed: Seed) -> SymmetricDesigns:  # noqa: ARG002 - deterministic
        return self


def _factory(params: dict[str, Any]) -> HypergraphDataset:  # noqa: ARG001
    return SymmetricDesigns()


register_dataset("symmetric_designs", _factory)
