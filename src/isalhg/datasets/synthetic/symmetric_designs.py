"""Symmetric-design cohort for the algorithm-comparison study.

Yields the canonical small Steiner systems and generalised quadrangle
used as torture-test fixtures throughout the codebase: Fano STS(7),
STS(9)=AG(2,3), the two non-isomorphic STS(13), and GQ(2,2) (the
doily). Identical to the hand-built fixtures in ``tests/conftest.py``,
exposed here as a registered :class:`HypergraphDataset` so the
orchestrator can iterate them like any other dataset.

Citations
---------
- Fano (1892); standard reference Beth, Jungnickel, Lenz, *Design Theory*, 1999.
- STS(9) as AG(2,3): Hall, *Combinatorial Theory*, 1986.
- STS(13) classification: Heinlein 2023 arXiv:2303.01207.
- GQ(2,2) symplectic realisation: Payne & Thas, *Finite Generalized
  Quadrangles*, §1.2.

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
from isalhg.types import DatasetName, Seed


def _fano() -> SparseHypergraph:
    lines = [
        frozenset({0, 1, 2}),
        frozenset({0, 3, 4}),
        frozenset({0, 5, 6}),
        frozenset({1, 3, 5}),
        frozenset({1, 4, 6}),
        frozenset({2, 3, 6}),
        frozenset({2, 4, 5}),
    ]
    return SparseHypergraph(n_nodes=7, hyperedges=lines)


def _sts_9() -> SparseHypergraph:
    blocks = [
        frozenset({0, 1, 2}),
        frozenset({3, 4, 5}),
        frozenset({6, 7, 8}),
        frozenset({0, 3, 6}),
        frozenset({1, 4, 7}),
        frozenset({2, 5, 8}),
        frozenset({0, 4, 8}),
        frozenset({1, 5, 6}),
        frozenset({2, 3, 7}),
        frozenset({0, 5, 7}),
        frozenset({1, 3, 8}),
        frozenset({2, 4, 6}),
    ]
    return SparseHypergraph(n_nodes=9, hyperedges=blocks)


def _cyclic_sts_13(base: tuple[int, int, int]) -> SparseHypergraph:
    n = 13
    edges = [frozenset((b + i) % n for b in base) for i in range(n)]
    return SparseHypergraph(n_nodes=n, hyperedges=edges)


def _gq_2_2() -> SparseHypergraph:
    edges = [
        frozenset({0, 1, 2}),
        frozenset({0, 3, 4}),
        frozenset({0, 5, 6}),
        frozenset({1, 3, 7}),
        frozenset({1, 5, 8}),
        frozenset({2, 4, 9}),
        frozenset({2, 6, 10}),
        frozenset({3, 8, 11}),
        frozenset({4, 7, 12}),
        frozenset({5, 10, 13}),
        frozenset({6, 9, 14}),
        frozenset({7, 11, 13}),
        frozenset({8, 12, 14}),
        frozenset({9, 11, 12}),
        frozenset({10, 13, 14}),
    ]
    return SparseHypergraph(n_nodes=15, hyperedges=edges)


_FIXTURES: tuple[tuple[str, SparseHypergraph], ...] = (
    ("fano_sts7", _fano()),
    ("sts9", _sts_9()),
    ("sts13_cyclic_014", _cyclic_sts_13((0, 1, 4))),
    ("sts13_cyclic_016", _cyclic_sts_13((0, 1, 6))),
    ("gq_2_2_doily", _gq_2_2()),
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
            source="hand-built; Fano/STS(9)/STS(13)/GQ(2,2)",
            citation=(
                "Beth-Jungnickel-Lenz 1999; Hall 1986; "
                "Heinlein 2023 arXiv:2303.01207; Payne-Thas 2009"
            ),
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
