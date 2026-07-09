"""Tier 5 dataset: the 12 HIC iso-equivalence atlas datasets.

Bundled with the HIC GitHub repo (Feng et al. 2024, Table 5):
``RHG-10``, ``RHG-3``, ``RHG-Table``, ``RHG-Pyramid``, ``IMDB-Dir-Form``,
``IMDB-Dir-Genre``, ``IMDB-Dir-Genre-M``, ``IMDB-Wri-Form``,
``IMDB-Wri-Genre``, ``IMDB-Wri-Genre-M``, ``Steam-Player``, ``Twitter-Friend``.

Each item carries a class label (e.g. genre in IMDB datasets) so the
classification and partition-agreement protocols can use it directly.

**D-CONN1 (resolved 2026-07-09):** the article's domain is connected
hypergraphs.  Every instance is restricted to its largest connected component
(LCC) before being yielded.  The per-class retention fraction (vertices and
hyperedges retained vs. original) is tracked and accessible via
:attr:`HICAtlasDataset.retention_report`.  If retention varies by class label,
:meth:`HICAtlasDataset.__init__` emits a ``WARNING``-level log message flagging
potential label-correlated fragmentation that could bias classification.

File format (one ``.txt`` file per dataset)::

    <total_count>
    <n_nodes> <n_edges> <class_label>
    <v_label_0> ... <v_label_{n_nodes-1}>
    <e0_node_0> ... <e0_node_k>
    ...
    <e_{n_edges-1}_node_0> ...
    <n_nodes> <n_edges> <class_label>   # next hypergraph block
    ...

Source: ``github.com/iMoonLab/HIC``, Apache-2.0.
Reference: Feng et al. (2024), HIC: Hypergraph Isomorphism Computation.
"""

from __future__ import annotations

import logging
from collections import deque
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.datasets.base import HypergraphDataset
from isalhg.datasets.registry import register_dataset
from isalhg.datasets.schemas import DatasetItem, DatasetMetadata, LabelVocabulary
from isalhg.types import DatasetName, EdgeLabel, HyperedgeSet, NodeId

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# File-path map: HIC dataset name → relative path under the data root.
# Path segments are exactly as found on disk (note: Steam-Player → stream_player).
# ---------------------------------------------------------------------------

_HIC_FILE_MAP: dict[str, str] = {
    "RHG-10": "RHG/RHG_10.txt",
    "RHG-3": "RHG/RHG_3.txt",
    "RHG-Table": "RHG/RHG_table.txt",
    "RHG-Pyramid": "RHG/RHG_pyramid.txt",
    "IMDB-Dir-Form": "IMDB/IMDB_dir_form.txt",
    "IMDB-Dir-Genre": "IMDB/IMDB_dir_genre.txt",
    "IMDB-Dir-Genre-M": "IMDB/IMDB_dir_genre_m.txt",
    "IMDB-Wri-Form": "IMDB/IMDB_wri_form.txt",
    "IMDB-Wri-Genre": "IMDB/IMDB_wri_genre.txt",
    "IMDB-Wri-Genre-M": "IMDB/IMDB_wri_genre_m.txt",
    "Steam-Player": "STEAM/stream_player.txt",
    "Twitter-Friend": "TWITTER/twitter_friend.txt",
}


# ---------------------------------------------------------------------------
# Retention statistics
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ClassRetentionStats:
    """LCC retention statistics aggregated over all instances of one class.

    Attributes
    ----------
    class_label : int
        The class integer from the HIC file.
    n_instances : int
        Number of hypergraph instances with this class label.
    vertices_before : int
        Sum of vertex counts before LCC restriction across instances.
    vertices_after : int
        Sum of vertex counts after LCC restriction.
    edges_before : int
        Sum of hyperedge counts before LCC restriction.
    edges_after : int
        Sum of hyperedge counts after LCC restriction.
    """

    class_label: int
    n_instances: int
    vertices_before: int
    vertices_after: int
    edges_before: int
    edges_after: int

    @property
    def vertex_fraction(self) -> float:
        """Fraction of vertices retained in the LCC (1.0 if all connected)."""
        return self.vertices_after / self.vertices_before if self.vertices_before else 1.0

    @property
    def edge_fraction(self) -> float:
        """Fraction of hyperedges retained in the LCC (1.0 if all connected)."""
        return self.edges_after / self.edges_before if self.edges_before else 1.0


# ---------------------------------------------------------------------------
# Raw parse record
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _RawRecord:
    n_nodes: int
    class_label: int
    vertex_labels: tuple[int, ...]
    hyperedges: tuple[frozenset[int], ...]


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def _parse_hic_file(path: Path) -> list[_RawRecord]:
    """Parse a HIC ``.txt`` file into raw per-hypergraph records.

    Parameters
    ----------
    path : Path
        Path to the HIC dataset file.

    Returns
    -------
    list[_RawRecord]
        One record per hypergraph block, in file order.

    Raises
    ------
    FileNotFoundError
        If ``path`` does not exist.
    ValueError
        If the file header is malformed.
    """
    records: list[_RawRecord] = []
    with path.open() as f:
        total = int(f.readline().strip())
        for _ in range(total):
            header = f.readline().strip().split()
            n_nodes, n_edges, class_label = int(header[0]), int(header[1]), int(header[2])
            vertex_labels = tuple(map(int, f.readline().strip().split()))
            hyperedges: list[frozenset[int]] = []
            for _ in range(n_edges):
                nodes = tuple(map(int, f.readline().strip().split()))
                hyperedges.append(frozenset(nodes))
            records.append(
                _RawRecord(
                    n_nodes=n_nodes,
                    class_label=class_label,
                    vertex_labels=vertex_labels,
                    hyperedges=tuple(hyperedges),
                )
            )
    return records


# ---------------------------------------------------------------------------
# LCC extraction
# ---------------------------------------------------------------------------


def _largest_connected_component(
    H: SparseHypergraph,
) -> tuple[SparseHypergraph, int, int]:
    """Restrict ``H`` to its largest connected component.

    Uses the primal-graph BFS already provided by
    :meth:`SparseHypergraph.primal_graph`.  Vertex IDs are remapped to
    ``0 ... |LCC|-1`` in ascending original-ID order; only hyperedges whose
    member set is fully contained in the LCC are kept.

    Parameters
    ----------
    H : SparseHypergraph
        Input hypergraph; may be disconnected.

    Returns
    -------
    SparseHypergraph
        Sub-hypergraph induced on the LCC.  If ``H`` is already connected,
        returns ``H`` unchanged (no copy, no allocation).
    int
        Vertex count of the LCC (equals ``H.n_nodes`` when connected).
    int
        Hyperedge count of the LCC (equals ``H.n_edges`` when connected).
    """
    if H.is_connected():
        return H, H.n_nodes, H.n_edges

    adj = H.primal_graph()
    unvisited: set[NodeId] = set(range(H.n_nodes))
    components: list[frozenset[NodeId]] = []
    while unvisited:
        start = min(unvisited)
        comp: set[NodeId] = {start}
        queue: deque[NodeId] = deque([start])
        while queue:
            u = queue.popleft()
            for w in adj[u]:
                if w not in comp:
                    comp.add(w)
                    queue.append(w)
        components.append(frozenset(comp))
        unvisited -= comp

    lcc: frozenset[NodeId] = max(components, key=len)
    lcc_sorted = sorted(lcc)
    remap: dict[NodeId, NodeId] = {old: new for new, old in enumerate(lcc_sorted)}

    edges: list[HyperedgeSet] = []
    edge_labels: list[EdgeLabel] = []
    for _, members, ell in H.iter_edges():
        if members <= lcc:
            edges.append(frozenset(remap[u] for u in members))
            edge_labels.append(ell)

    sub = SparseHypergraph(
        n_nodes=len(lcc),
        hyperedges=edges,
        n_vertex_labels=H.n_vertex_labels,
        n_edge_labels=H.n_edge_labels,
        vertex_labels=[H.vertex_label(u) for u in lcc_sorted],
        edge_labels=edge_labels,
    )
    return sub, len(lcc), len(edges)


# ---------------------------------------------------------------------------
# Dataset class
# ---------------------------------------------------------------------------


class HICAtlasDataset(HypergraphDataset):
    """One of the 12 HIC atlas datasets.

    Parameters
    ----------
    root : Path
        Data root directory; the file is loaded from
        ``root / _HIC_FILE_MAP[hic_name]``.
    hic_name : str
        One of the 12 ``KNOWN_NAMES``.

    Notes
    -----
    Parsing is eager: all hypergraphs are loaded at construction time and
    cached in memory.  This is required for correct ``__len__`` without a
    second pass.

    Every instance is restricted to its LCC (D-CONN1).  The full retention
    statistics are accessible via :attr:`retention_report`.
    """

    KNOWN_NAMES: tuple[str, ...] = tuple(_HIC_FILE_MAP.keys())

    def __init__(self, root: Path, hic_name: str) -> None:
        if hic_name not in _HIC_FILE_MAP:
            raise ValueError(f"Unknown HIC dataset {hic_name!r}; known: {list(_HIC_FILE_MAP)}")
        self._root = Path(root)
        self._hic_name = hic_name
        self._file_path: Path = self._root / _HIC_FILE_MAP[hic_name]

        # Populated by _load():
        self._items: list[DatasetItem] = []
        self._vocabulary: LabelVocabulary = LabelVocabulary.trivial()
        self._retention_report: dict[int, ClassRetentionStats] = {}
        self._arity_range: tuple[int, int] = (0, 0)
        self._n_nodes_range: tuple[int, int] = (0, 0)

        self._load()

    # ------------------------------------------------------------------
    # Loader
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Parse the file, extract LCCs, build vocabulary, track retention."""
        raw_records = _parse_hic_file(self._file_path)

        # Build vocabulary from all unique integer vertex labels across the corpus.
        all_vlabels: set[int] = set()
        for rec in raw_records:
            all_vlabels.update(rec.vertex_labels)

        sorted_vlabels = sorted(all_vlabels)
        if sorted_vlabels == [0] or not sorted_vlabels:
            vocab = LabelVocabulary.trivial()
            label_to_id: dict[int, int] = {0: 0}
            n_vertex_labels = 1
        else:
            vocab = LabelVocabulary(
                vertex_symbols=tuple(str(lbl) for lbl in sorted_vlabels),
                edge_symbols=("⊥",),
            )
            label_to_id = {lbl: i for i, lbl in enumerate(sorted_vlabels)}
            n_vertex_labels = len(sorted_vlabels)

        # Build items, extract LCCs, accumulate stats.
        items: list[DatasetItem] = []
        # class_label → [(verts_before, verts_after, edges_before, edges_after)]
        retention_accum: dict[int, list[tuple[int, int, int, int]]] = {}
        min_arity: int | None = None
        max_arity: int = 0
        min_nodes: int | None = None
        max_nodes: int = 0

        for idx, rec in enumerate(raw_records):
            mapped_vlabels = [label_to_id[lbl] for lbl in rec.vertex_labels]
            H_raw = SparseHypergraph(
                n_nodes=rec.n_nodes,
                hyperedges=list(rec.hyperedges),
                n_vertex_labels=n_vertex_labels,
                vertex_labels=mapped_vlabels,
            )
            H_lcc, verts_after, edges_after = _largest_connected_component(H_raw)

            # Accumulate retention per class.
            cl = rec.class_label
            if cl not in retention_accum:
                retention_accum[cl] = []
            retention_accum[cl].append((rec.n_nodes, verts_after, len(rec.hyperedges), edges_after))

            # Update arity and node-count ranges over the LCC.
            if H_lcc.n_nodes > 0:
                min_nodes = H_lcc.n_nodes if min_nodes is None else min(min_nodes, H_lcc.n_nodes)
                max_nodes = max(max_nodes, H_lcc.n_nodes)
            for _, members, _ in H_lcc.iter_edges():
                a = len(members)
                min_arity = a if min_arity is None else min(min_arity, a)
                max_arity = max(max_arity, a)

            items.append(
                DatasetItem(
                    item_id=f"hic:{self._hic_name}:{idx:06d}",
                    hypergraph=H_lcc,
                    iso_class=rec.class_label,
                    extra={
                        "source_index": idx,
                        "class_label": rec.class_label,
                        "n_nodes_raw": rec.n_nodes,
                        "n_edges_raw": len(rec.hyperedges),
                        "n_nodes_lcc": H_lcc.n_nodes,
                        "n_edges_lcc": H_lcc.n_edges,
                    },
                )
            )

        # Build ClassRetentionStats per class.
        retention_report: dict[int, ClassRetentionStats] = {}
        for cl, stats_list in retention_accum.items():
            vb = sum(s[0] for s in stats_list)
            va = sum(s[1] for s in stats_list)
            eb = sum(s[2] for s in stats_list)
            ea = sum(s[3] for s in stats_list)
            retention_report[cl] = ClassRetentionStats(
                class_label=cl,
                n_instances=len(stats_list),
                vertices_before=vb,
                vertices_after=va,
                edges_before=eb,
                edges_after=ea,
            )

        # Log overall retention summary.
        total_vb = sum(s.vertices_before for s in retention_report.values())
        total_va = sum(s.vertices_after for s in retention_report.values())
        total_eb = sum(s.edges_before for s in retention_report.values())
        total_ea = sum(s.edges_after for s in retention_report.values())
        logger.info(
            "HICAtlasDataset(%s): loaded %d instances, %d classes; "
            "LCC retention: vertices %.4f (%d/%d), edges %.4f (%d/%d)",
            self._hic_name,
            len(items),
            len(retention_report),
            total_va / total_vb if total_vb else 1.0,
            total_va,
            total_vb,
            total_ea / total_eb if total_eb else 1.0,
            total_ea,
            total_eb,
        )

        # Warn about label-correlated fragmentation (D-CONN1).
        flagged = {cl: s for cl, s in retention_report.items() if s.vertex_fraction < 1.0}
        if flagged:
            logger.warning(
                "HICAtlasDataset(%s): %d/%d classes have vertex retention < 1.0 "
                "(label-correlated fragmentation could bias classification); "
                "per-class vertex retention: %s",
                self._hic_name,
                len(flagged),
                len(retention_report),
                {cl: f"{s.vertex_fraction:.4f}" for cl, s in sorted(flagged.items())},
            )

        self._items = items
        self._vocabulary = vocab
        self._retention_report = retention_report
        self._arity_range = (min_arity or 0, max_arity)
        self._n_nodes_range = (min_nodes or 0, max_nodes)

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    @property
    def name(self) -> DatasetName:
        return f"hic:{self._hic_name}"

    @property
    def metadata(self) -> DatasetMetadata:
        return DatasetMetadata(
            name=self.name,
            n_items=len(self._items),
            arity_range=self._arity_range,
            n_nodes_range=self._n_nodes_range,
            has_iso_labels=True,
            source=(f"iMoonLab/HIC (Apache-2.0), github.com/iMoonLab/HIC; file: {self._file_path}"),
            citation=(
                "Feng et al. (2024). HIC: Hypergraph Isomorphism Computation. "
                "github.com/iMoonLab/HIC"
            ),
            label_vocabulary=self._vocabulary,
        )

    # ------------------------------------------------------------------
    # Iteration
    # ------------------------------------------------------------------

    def __iter__(self) -> Iterator[DatasetItem]:
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    # ------------------------------------------------------------------
    # D-CONN1 retention report
    # ------------------------------------------------------------------

    @property
    def retention_report(self) -> dict[int, ClassRetentionStats]:
        """Per-class LCC retention statistics (D-CONN1).

        Returns
        -------
        dict[int, ClassRetentionStats]
            Maps each class label to its aggregated retention statistics.
            Reviewers can use :attr:`ClassRetentionStats.vertex_fraction` and
            :attr:`ClassRetentionStats.edge_fraction` to quantify the impact
            of the connectivity restriction.
        """
        return self._retention_report


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


def _factory(params: dict[str, Any]) -> HypergraphDataset:
    """Factory for the ``"hic_atlas"`` registry key.

    Parameters
    ----------
    params : dict[str, Any]
        Must contain ``"root"`` (str or Path) and ``"hic_name"`` (str).
    """
    root = Path(str(params["root"]))
    hic_name = str(params["hic_name"])
    return HICAtlasDataset(root=root, hic_name=hic_name)


register_dataset("hic_atlas", _factory)
