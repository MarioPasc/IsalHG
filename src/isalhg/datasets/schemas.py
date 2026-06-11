"""Dataclasses describing dataset items and dataset metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.types import DatasetName, IsoClassId


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
    """

    name: DatasetName
    n_items: int
    arity_range: tuple[int, int]
    n_nodes_range: tuple[int, int]
    has_iso_labels: bool
    source: str
    citation: str = ""
