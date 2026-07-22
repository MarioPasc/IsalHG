"""Dataclasses describing dataset items, dataset metadata, and label vocabularies."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.types import DatasetName, IsoClassId


@dataclass(frozen=True)
class RealizedParams:
    """Per-corpus realized distribution of structural parameters (T-M7a).

    Stores the *measured* structural properties of a dataset after generation,
    as opposed to the requested generator parameters. Required by the strict
    data spec (``REVIEW/DATA.md`` §5 reporting rules).

    Attributes
    ----------
    n_vals : tuple[int, ...]
        Vertex count for each item, in iteration order.
    m_vals : tuple[int, ...]
        Edge count for each item, in iteration order.
    density_vals : tuple[float, ...]
        Density ``m/n`` for each item (0.0 when ``n == 0``).
    arity_hist : dict[int, int]
        Arity → total number of edges of that arity, pooled across all items.
    all_connected : bool
        ``True`` iff every item passed the connectivity check (D-CONN1).
    seeds : tuple[int, ...]
        PRNG seeds used during stochastic generation.  Empty for deterministic
        datasets.
    """

    n_vals: tuple[int, ...]
    m_vals: tuple[int, ...]
    density_vals: tuple[float, ...]
    arity_hist: dict[int, int]
    all_connected: bool
    seeds: tuple[int, ...]

    @classmethod
    def compute(
        cls,
        hypergraphs: list[SparseHypergraph],
        seeds: tuple[int, ...] = (),
    ) -> RealizedParams:
        """Compute realized params from a list of hypergraphs.

        Parameters
        ----------
        hypergraphs : list[SparseHypergraph]
            The corpus items, in iteration order.
        seeds : tuple[int, ...]
            PRNG seeds used during generation; empty for deterministic datasets.

        Returns
        -------
        RealizedParams
            Populated realized-parameter record.
        """
        n_vals: list[int] = []
        m_vals: list[int] = []
        density_vals: list[float] = []
        arity_hist: dict[int, int] = {}
        all_connected = True

        for H in hypergraphs:
            n = H.n_nodes
            m = H.n_edges
            n_vals.append(n)
            m_vals.append(m)
            density_vals.append(m / n if n > 0 else 0.0)
            if not H.is_connected():
                all_connected = False
            for _, members, _ in H.iter_edges():
                a = len(members)
                arity_hist[a] = arity_hist.get(a, 0) + 1

        return cls(
            n_vals=tuple(n_vals),
            m_vals=tuple(m_vals),
            density_vals=tuple(density_vals),
            arity_hist=dict(sorted(arity_hist.items())),
            all_connected=all_connected,
            seeds=seeds,
        )


@dataclass(frozen=True)
class LabelVocabulary:
    """Per-dataset semantic-string → int-ID vocabulary (decision I45).

    Attributes
    ----------
    vertex_symbols : tuple[str, ...]
        Lexicographically sorted semantic strings for vertex labels.
        Position ``i`` is the symbol whose integer ID is ``i``.
    edge_symbols : tuple[str, ...]
        Same for hyperedge labels.

    Notes
    -----
    Trivial-vocabulary datasets (unlabelled synthetic hypergraphs)
    declare ``LabelVocabulary.trivial()`` so the canonical algorithm runs
    identically on labelled and unlabelled inputs without a special-case
    branch.

    Real labelled datasets (Tier 4 / Tier 5 loaders, e.g. the HIC atlas)
    call :meth:`fit` at load time. The production ``fit`` implementation
    is deferred to Phase 6.
    """

    vertex_symbols: tuple[str, ...]
    edge_symbols: tuple[str, ...]

    @property
    def n_vertex_labels(self) -> int:
        return len(self.vertex_symbols)

    @property
    def n_edge_labels(self) -> int:
        return len(self.edge_symbols)

    @classmethod
    def trivial(cls) -> LabelVocabulary:
        """Single-symbol vocabulary used by unlabelled synthetic datasets."""
        return cls(vertex_symbols=("⊥",), edge_symbols=("⊥",))

    @classmethod
    def fit(cls, items: Iterable[tuple[Iterable[str], Iterable[str]]]) -> LabelVocabulary:
        """Collect semantic labels across a corpus and assign contiguous int IDs.

        Parameters
        ----------
        items : Iterable[tuple[Iterable[str], Iterable[str]]]
            One ``(vertex_label_strings, edge_label_strings)`` pair per corpus
            item -- the semantic strings observed on that item's vertices and
            hyperedges, before integer encoding.

        Returns
        -------
        LabelVocabulary
            All observed strings, lexicographically sorted, position = int ID.
            A side with no observed labels falls back to the trivial
            single-symbol vocabulary so ``SparseHypergraph``'s ``>= 1``
            vocabulary-size invariant always holds.
        """
        vertex_symbols: set[str] = set()
        edge_symbols: set[str] = set()
        for v_labels, e_labels in items:
            vertex_symbols.update(v_labels)
            edge_symbols.update(e_labels)
        return cls(
            vertex_symbols=tuple(sorted(vertex_symbols)) or ("⊥",),
            edge_symbols=tuple(sorted(edge_symbols)) or ("⊥",),
        )


@dataclass(frozen=True)
class DatasetItem:
    """One element yielded by a :class:`HypergraphDataset`.

    Attributes
    ----------
    item_id : str
        Stable identifier unique within the dataset.
    hypergraph : SparseHypergraph
        The hypergraph itself.
    iso_class : IsoClassId | None
        Ground-truth isomorphism-class label, when known (Tiers 1 and 5).
        ``None`` for datasets without a known partition (Tiers 2, 3, 4).
    extra : dict[str, Any]
        Loader-specific side metadata (e.g. source row, generator seed).
    """

    item_id: str
    hypergraph: SparseHypergraph
    iso_class: IsoClassId | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DatasetMetadata:
    """Static description of a dataset.

    Attributes
    ----------
    name : DatasetName
        Canonical identifier used in registries and configs.
    n_items : int
        Number of items the iterator will yield.
    arity_range : tuple[int, int]
        ``(min_arity, max_arity)`` across all hyperedges in the dataset.
    n_nodes_range : tuple[int, int]
        ``(min_n, max_n)`` across all hypergraphs in the dataset.
    has_iso_labels : bool
        True iff every :class:`DatasetItem` carries a non-None ``iso_class``.
    source : str
        Free-text origin (URL, DOI, library function, generator name).
    citation : str
        Bibliographic citation if the dataset accompanies a publication.
    label_vocabulary : LabelVocabulary
        Per-dataset semantic-string → int-ID map (decision I45).
        Defaults to the trivial vocabulary.
    """

    name: DatasetName
    n_items: int
    arity_range: tuple[int, int]
    n_nodes_range: tuple[int, int]
    has_iso_labels: bool
    source: str
    citation: str = ""
    label_vocabulary: LabelVocabulary = field(default_factory=LabelVocabulary.trivial)
    realized_params: RealizedParams | None = None
