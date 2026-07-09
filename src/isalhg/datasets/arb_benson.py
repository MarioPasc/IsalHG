"""Tier 4/5 dataset: Austin Benson ARB hypergraph collection (node-labeled).

Source: https://www.cs.cornell.edu/~arb/data/. Loads the node-labeled triple
format used by the contact / co-answering hypergraphs -- per dataset directory
``<name>/``:

* ``hyperedges-<name>.txt`` -- one hyperedge per line, comma-separated
  **1-based** node indices;
* ``node-labels-<name>.txt`` -- line ``v`` holds the label index (or a
  comma-separated *list* of label indices, e.g. mathoverflow-answers) of node
  ``v``, **1-based** on both axes;
* ``label-names-<name>.txt`` -- line ``i`` names label index ``i``.

These are the PS / HS / MO benchmarks of Qin et al. (ICDE 2023, DOI
10.1109/ICDE55515.2023.00386); the loader feeds the T-M2a Table II
reproduction. Multi-label nodes are encoded as a **composite symbol** -- the
lexicographically sorted tag names joined with ``","`` -- so Qin's
``l(v) = l(f(v))`` equality semantics compare full tag sets (decision D2,
2026-07-08). Hyperedge labels do not exist in this format: the edge vocabulary
is trivial and every edge carries label ``0``.

The dataset yields ONE :class:`DatasetItem` -- the whole hypergraph -- with
per-instance size statistics in ``extra``; ego-network extraction for the
Qin benchmarks happens downstream (:func:`isalhg.core.sparse_hypergraph.ego_network`).
Duplicate member-sets in the hyperedge file (MO has exactly one) are merged by
:class:`SparseHypergraph`; ``extra["m_file"]`` vs ``extra["m_loaded"]`` records
the difference. No isomorphism labels.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.datasets.base import HypergraphDataset
from isalhg.datasets.registry import register_dataset
from isalhg.datasets.schemas import DatasetItem, DatasetMetadata, LabelVocabulary
from isalhg.errors import DatasetIntegrityError
from isalhg.types import DatasetName


class ARBBensonDataset(HypergraphDataset):
    """Loader for one node-labeled ARB/Benson dataset directory."""

    def __init__(self, root: Path | str, name: str) -> None:
        """Load the dataset in directory ``root / name`` (lazily, on first access)."""
        self._root = Path(root)
        self._dataset = name
        self._item: DatasetItem | None = None
        self._metadata: DatasetMetadata | None = None

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    def _path(self, kind: str) -> Path:
        path = self._root / self._dataset / f"{kind}-{self._dataset}.txt"
        if not path.is_file():
            raise DatasetIntegrityError(f"missing ARB file: {path}")
        return path

    def _load(self) -> None:
        if self._item is not None:
            return
        label_names = self._path("label-names").read_text().splitlines()

        node_symbols: list[str] = []
        for line_no, line in enumerate(self._path("node-labels").read_text().splitlines(), start=1):
            try:
                indices = [int(tok) for tok in line.strip().split(",") if tok]
            except ValueError as exc:
                raise DatasetIntegrityError(
                    f"{self._dataset}: malformed node-labels line {line_no}: {line!r}"
                ) from exc
            names = []
            for idx in indices:
                if not 1 <= idx <= len(label_names):
                    raise DatasetIntegrityError(
                        f"{self._dataset}: label index {idx} outside "
                        f"1..{len(label_names)} at node-labels line {line_no}"
                    )
                names.append(label_names[idx - 1])
            node_symbols.append(",".join(sorted(names)))
        n_nodes = len(node_symbols)

        edges: list[frozenset[int]] = []
        for line_no, line in enumerate(self._path("hyperedges").read_text().splitlines(), start=1):
            if not line.strip():
                continue
            members = frozenset(int(tok) - 1 for tok in line.strip().split(","))
            if any(not 0 <= v < n_nodes for v in members):
                raise DatasetIntegrityError(
                    f"{self._dataset}: node index outside 1..{n_nodes} at hyperedges line {line_no}"
                )
            edges.append(members)

        vocabulary = LabelVocabulary.fit([(node_symbols, ())])
        symbol_id = {symbol: i for i, symbol in enumerate(vocabulary.vertex_symbols)}
        hypergraph = SparseHypergraph(
            n_nodes=n_nodes,
            hyperedges=edges,
            n_vertex_labels=vocabulary.n_vertex_labels,
            n_edge_labels=vocabulary.n_edge_labels,
            vertex_labels=[symbol_id[s] for s in node_symbols],
        )

        arities = sorted(len(e) for e in edges)
        extra: dict[str, Any] = {
            "n_nodes": n_nodes,
            "m_file": len(edges),
            "m_loaded": hypergraph.n_edges,
            "arity_min": arities[0] if arities else 0,
            "arity_max": arities[-1] if arities else 0,
            "arity_mean": round(sum(arities) / len(arities), 3) if arities else 0.0,
            "n_vertex_symbols": vocabulary.n_vertex_labels,
        }
        self._item = DatasetItem(
            item_id=self._dataset, hypergraph=hypergraph, iso_class=None, extra=extra
        )
        self._metadata = DatasetMetadata(
            name=self.name,
            n_items=1,
            arity_range=(extra["arity_min"], extra["arity_max"]),
            n_nodes_range=(n_nodes, n_nodes),
            has_iso_labels=False,
            source="https://www.cs.cornell.edu/~arb/data/",
            citation=(
                "Benson et al., Simplicial closure and higher-order link prediction, "
                "PNAS 2018; benchmark triple of Qin et al., ICDE 2023, "
                "DOI 10.1109/ICDE55515.2023.00386"
            ),
            label_vocabulary=vocabulary,
        )

    # ------------------------------------------------------------------
    # HypergraphDataset interface
    # ------------------------------------------------------------------

    @property
    def name(self) -> DatasetName:
        return f"arb_benson:{self._dataset}"

    @property
    def metadata(self) -> DatasetMetadata:
        self._load()
        assert self._metadata is not None
        return self._metadata

    def __iter__(self) -> Iterator[DatasetItem]:
        self._load()
        assert self._item is not None
        yield self._item

    def __len__(self) -> int:
        return 1


def _factory(params: dict[str, Any]) -> ARBBensonDataset:
    return ARBBensonDataset(root=Path(params["root"]), name=str(params["name"]))


register_dataset("arb_benson", _factory)
