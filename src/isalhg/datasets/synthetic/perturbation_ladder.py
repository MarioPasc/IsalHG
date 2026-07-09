"""Perturbation-ladder dataset -- hypergraph pairs at a known HGED upper bound.

Each *ladder* starts from a random base hypergraph and applies one random
generator edit at a time (:func:`isalhg.core.sparse_hypergraph.edit_path`
semantics), recording ``max_t + 1`` snapshots. Snapshot ``t`` sits at a known
distance ``HGED(base, snapshot_t) <= budget_t`` from the base, where
``budget_t`` is the accumulated **Qin-taxonomy cost** of the applied edits
(:func:`isalhg.core.sparse_hypergraph.qin_edit_cost`; a whole-hyperedge
insert/delete of arity ``a`` contributes ``a + 1``). The budget is an *upper
bound* because random edits may cancel or compose (``correlation.md`` §HGED).

The ladder is the **scale tier** of the HGED oracle (decision DQ2): it supplies
a supervised distance axis without an exact-HGED solve, so it reaches sizes past
the exact-oracle ceiling (DATA.md §1). Snapshots are not isomorphism classes, so
``iso_class`` is ``None``; the ladder id and step are recorded in ``extra`` and
the base-vs-snapshot pairs are exposed through :meth:`ladder_pairs` for the
correlation study and the ``t >= HGED`` acceptance check.

Restriction: Python stdlib + ``isalhg.core`` + ``isalhg.datasets`` only.
"""

from __future__ import annotations

import random
from collections.abc import Iterator
from typing import Any

from isalhg.core.sparse_hypergraph import SparseHypergraph, qin_edit_cost, random_edit
from isalhg.datasets.base import HypergraphDataset
from isalhg.datasets.registry import register_dataset
from isalhg.datasets.schemas import DatasetItem, DatasetMetadata, LabelVocabulary
from isalhg.datasets.synthetic._random_hg import random_hypergraph
from isalhg.types import DatasetName, Seed

# Distinct prime strides keep each ladder's PRNG stream independent of the
# others while remaining a pure function of the dataset seed.
_LADDER_STRIDE = 1_000_003


class PerturbationLadderHypergraphs(HypergraphDataset):
    """Ladders of unit-edit snapshots off random base hypergraphs.

    Parameters
    ----------
    n_nodes : int, optional
        Base-hypergraph vertex count. Default ``6``.
    n_edges : int, optional
        Base-hypergraph edge-insertion attempts. Default ``4``.
    arity_range : tuple[int, int], optional
        Base-hypergraph hyperedge-size range. Default ``(2, 3)``.
    max_t : int, optional
        Number of unit edits per ladder (snapshots ``0..max_t``). Default ``8``.
    n_ladders : int, optional
        Number of independent ladders (each its own random base). Default ``5``.
    n_vertex_labels, n_edge_labels : int, optional
        Label-vocabulary sizes for the bases. Default ``1`` (unlabelled).
    seed : Seed, optional
        Master seed; ladder ``L`` uses ``seed + L * 1_000_003``. Default ``0``.
    """

    def __init__(
        self,
        *,
        n_nodes: int = 6,
        n_edges: int = 4,
        arity_range: tuple[int, int] = (2, 3),
        max_t: int = 8,
        n_ladders: int = 5,
        n_vertex_labels: int = 1,
        n_edge_labels: int = 1,
        seed: Seed = 0,
    ) -> None:
        if max_t < 0:
            raise ValueError(f"max_t must be >= 0, got {max_t}")
        if n_ladders < 1:
            raise ValueError(f"n_ladders must be >= 1, got {n_ladders}")
        self._n_nodes = n_nodes
        self._n_edges = n_edges
        self._arity_range = arity_range
        self._max_t = max_t
        self._n_ladders = n_ladders
        self._n_vertex_labels = n_vertex_labels
        self._n_edge_labels = n_edge_labels
        self._seed: Seed = int(seed)
        self._items: list[DatasetItem] = self._build()

    def _build(self) -> list[DatasetItem]:
        items: list[DatasetItem] = []
        for ladder in range(self._n_ladders):
            rng = random.Random(self._seed + ladder * _LADDER_STRIDE)
            base = random_hypergraph(
                n_nodes=self._n_nodes,
                n_edges=self._n_edges,
                arity_range=self._arity_range,
                rng=rng,
                n_vertex_labels=self._n_vertex_labels,
                n_edge_labels=self._n_edge_labels,
            )
            current = base
            items.append(
                DatasetItem(
                    item_id=f"L{ladder}_t0",
                    hypergraph=current,
                    iso_class=None,
                    extra={"ladder": ladder, "step": 0, "budget_from_base": 0, "op": "base"},
                )
            )
            budget = 0
            for step in range(1, self._max_t + 1):
                nxt, op = random_edit(current, rng)
                budget += qin_edit_cost(current, nxt)
                current = nxt
                items.append(
                    DatasetItem(
                        item_id=f"L{ladder}_t{step}",
                        hypergraph=current,
                        iso_class=None,
                        extra={
                            "ladder": ladder,
                            "step": step,
                            "budget_from_base": budget,
                            "op": op,
                        },
                    )
                )
        return items

    @property
    def name(self) -> DatasetName:
        return "perturbation_ladder"

    @property
    def metadata(self) -> DatasetMetadata:
        n_values = [it.hypergraph.n_nodes for it in self._items]
        arities = [len(members) for it in self._items for members in it.hypergraph.hyperedges()]
        return DatasetMetadata(
            name="perturbation_ladder",
            n_items=len(self._items),
            arity_range=(min(arities), max(arities)) if arities else (0, 0),
            n_nodes_range=(min(n_values), max(n_values)),
            has_iso_labels=False,
            source="synthetic/perturbation_ladder (generator edits, Qin-cost budget)",
            citation="Qin et al., ICDE 2023 (HGED, empty-shell taxonomy)",
            label_vocabulary=LabelVocabulary.trivial()
            if self._n_vertex_labels == 1 and self._n_edge_labels == 1
            else LabelVocabulary(
                vertex_symbols=tuple(str(i) for i in range(self._n_vertex_labels)),
                edge_symbols=tuple(str(i) for i in range(self._n_edge_labels)),
            ),
        )

    def __iter__(self) -> Iterator[DatasetItem]:
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def seed(self, seed: Seed) -> PerturbationLadderHypergraphs:
        return PerturbationLadderHypergraphs(
            n_nodes=self._n_nodes,
            n_edges=self._n_edges,
            arity_range=self._arity_range,
            max_t=self._max_t,
            n_ladders=self._n_ladders,
            n_vertex_labels=self._n_vertex_labels,
            n_edge_labels=self._n_edge_labels,
            seed=seed,
        )

    def ladder_pairs(self) -> list[tuple[SparseHypergraph, SparseHypergraph, int]]:
        """Return ``(base, snapshot_t, budget_t)`` triples for every step ``t >= 1``.

        ``budget_t`` is the accumulated Qin-taxonomy cost of the applied edits,
        the known HGED upper bound: ``HGED(base, snapshot_t) <= budget_t``.
        Consumed by the correlation study (T-M5a) and the acceptance test.
        """
        pairs: list[tuple[SparseHypergraph, SparseHypergraph, int]] = []
        by_ladder: dict[int, SparseHypergraph] = {}
        for it in self._items:
            if it.extra["step"] == 0:
                by_ladder[it.extra["ladder"]] = it.hypergraph
        for it in self._items:
            if it.extra["step"] >= 1:
                base = by_ladder[it.extra["ladder"]]
                pairs.append((base, it.hypergraph, int(it.extra["budget_from_base"])))
        return pairs


def _factory(params: dict[str, Any]) -> HypergraphDataset:
    return PerturbationLadderHypergraphs(
        n_nodes=int(params.get("n_nodes", 6)),
        n_edges=int(params.get("n_edges", 4)),
        arity_range=tuple(params.get("arity_range", (2, 3))),
        max_t=int(params.get("max_t", 8)),
        n_ladders=int(params.get("n_ladders", 5)),
        n_vertex_labels=int(params.get("n_vertex_labels", 1)),
        n_edge_labels=int(params.get("n_edge_labels", 1)),
        seed=int(params.get("seed", 0)),
    )


register_dataset("perturbation_ladder", _factory)
