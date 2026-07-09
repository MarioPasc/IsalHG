"""Exact-HGED correlation corpus -- small hypergraphs for the Layer-1 study.

A controlled set of small random hypergraphs whose sizes sit within the
exact-HGED oracle ceiling (DATA.md §5), spanning a range of structural
similarity. The Layer-1 study (T-M5a) computes all pairwise ``ExactHGED`` and all
pairwise ``d_I`` / competitor distances over this corpus and correlates them; the
head-to-head against competitors is on this axis. Both labelled and unlabelled
variants are supported -- ``correlation.md`` says run both.

``iso_class`` is ``None`` (no planted partition); the study filters pairs with
``HGED > 0`` and ``d_I > 0``, matching the IsalGraph exact-GED protocol. Sizes
are drawn per item from ``n_range`` / ``n_edges_range`` so the corpus is diverse
but every instance is exact-HGED tractable.

Restriction: Python stdlib + ``isalhg.core`` + ``isalhg.datasets`` only.
"""

from __future__ import annotations

import random
from collections.abc import Iterator
from typing import Any

from isalhg.datasets.base import HypergraphDataset
from isalhg.datasets.registry import register_dataset
from isalhg.datasets.schemas import DatasetItem, DatasetMetadata, LabelVocabulary
from isalhg.datasets.synthetic._random_hg import random_hypergraph
from isalhg.types import DatasetName, Seed


class CorrelationCorpusHypergraphs(HypergraphDataset):
    """A diverse pool of small random hypergraphs for the exact-HGED study.

    Parameters
    ----------
    n_range : tuple[int, int], optional
        Inclusive vertex-count range drawn per item. Default ``(4, 7)``.
    n_edges_range : tuple[int, int], optional
        Inclusive edge-insertion-attempt range drawn per item. Default ``(2, 5)``.
    arity_range : tuple[int, int], optional
        Hyperedge-size range. Default ``(2, 3)``.
    n_items : int, optional
        Number of hypergraphs in the corpus. Default ``30``.
    n_vertex_labels, n_edge_labels : int, optional
        Label-vocabulary sizes. Default ``1`` (unlabelled). Set ``> 1`` for the
        labelled variant.
    seed : Seed, optional
        Master seed; a single RNG stream generates the whole corpus. Default ``0``.
    """

    def __init__(
        self,
        *,
        n_range: tuple[int, int] = (4, 7),
        n_edges_range: tuple[int, int] = (2, 5),
        arity_range: tuple[int, int] = (2, 3),
        n_items: int = 30,
        n_vertex_labels: int = 1,
        n_edge_labels: int = 1,
        seed: Seed = 0,
    ) -> None:
        if n_items < 1:
            raise ValueError(f"n_items must be >= 1, got {n_items}")
        if n_range[0] < 1 or n_range[1] < n_range[0]:
            raise ValueError(f"invalid n_range {n_range}")
        self._n_range = n_range
        self._n_edges_range = n_edges_range
        self._arity_range = arity_range
        self._n_items = n_items
        self._n_vertex_labels = n_vertex_labels
        self._n_edge_labels = n_edge_labels
        self._seed: Seed = int(seed)
        self._items: list[DatasetItem] = self._build()

    def _build(self) -> list[DatasetItem]:
        rng = random.Random(self._seed)
        items: list[DatasetItem] = []
        for index in range(self._n_items):
            n = rng.randint(self._n_range[0], self._n_range[1])
            m = rng.randint(self._n_edges_range[0], self._n_edges_range[1])
            H = random_hypergraph(
                n_nodes=n,
                n_edges=m,
                arity_range=self._arity_range,
                rng=rng,
                n_vertex_labels=self._n_vertex_labels,
                n_edge_labels=self._n_edge_labels,
            )
            items.append(
                DatasetItem(
                    item_id=f"c{index}",
                    hypergraph=H,
                    iso_class=None,
                    extra={"index": index, "n": H.n_nodes, "m": H.n_edges},
                )
            )
        return items

    @property
    def name(self) -> DatasetName:
        return "correlation_corpus"

    @property
    def metadata(self) -> DatasetMetadata:
        n_values = [it.hypergraph.n_nodes for it in self._items]
        arities = [len(members) for it in self._items for members in it.hypergraph.hyperedges()]
        if self._n_vertex_labels == 1 and self._n_edge_labels == 1:
            vocab = LabelVocabulary.trivial()
        else:
            vocab = LabelVocabulary(
                vertex_symbols=tuple(str(i) for i in range(self._n_vertex_labels)),
                edge_symbols=tuple(str(i) for i in range(self._n_edge_labels)),
            )
        return DatasetMetadata(
            name="correlation_corpus",
            n_items=len(self._items),
            arity_range=(min(arities), max(arities)) if arities else (0, 0),
            n_nodes_range=(min(n_values), max(n_values)),
            has_iso_labels=False,
            source="synthetic/correlation_corpus (stdlib random hypergraphs)",
            citation="",
            label_vocabulary=vocab,
        )

    def __iter__(self) -> Iterator[DatasetItem]:
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def seed(self, seed: Seed) -> CorrelationCorpusHypergraphs:
        return CorrelationCorpusHypergraphs(
            n_range=self._n_range,
            n_edges_range=self._n_edges_range,
            arity_range=self._arity_range,
            n_items=self._n_items,
            n_vertex_labels=self._n_vertex_labels,
            n_edge_labels=self._n_edge_labels,
            seed=seed,
        )


def _factory(params: dict[str, Any]) -> HypergraphDataset:
    return CorrelationCorpusHypergraphs(
        n_range=tuple(params.get("n_range", (4, 7))),
        n_edges_range=tuple(params.get("n_edges_range", (2, 5))),
        arity_range=tuple(params.get("arity_range", (2, 3))),
        n_items=int(params.get("n_items", 30)),
        n_vertex_labels=int(params.get("n_vertex_labels", 1)),
        n_edge_labels=int(params.get("n_edge_labels", 1)),
        seed=int(params.get("seed", 0)),
    )


register_dataset("correlation_corpus", _factory)
