"""Catalog of all Steiner triple systems of order 3-15.

Vendored complete listings of the pairwise non-isomorphic STS(n) for
``n in {3, 7, 9, 13, 15}`` (counts 1, 1, 1, 2, 80), from Olli Pottonen's
STS pages (``https://pottonen.kapsi.fi/sts19/``); classification per Kaski &
Ostergard, *The Steiner triple systems of order 19*, Math. Comp. 73 (2004),
and Colbourn & Rosa, *Triple Systems* (1999). Provenance, format, and
integrity checksums: ``isalhg/datasets/data/sts/README.md``.

Unlike the hand-built partial cyclic systems in
:mod:`isalhg.datasets.synthetic.designs`, every hypergraph produced here is a
genuine Steiner triple system: 3-uniform, with every point-pair covered by
exactly one block. Use these when the *Steiner property* is claimed (e.g. the
true non-isomorphic STS(13) pair); use the cyclic orbits when a cheap
vertex-transitive hard instance suffices.
"""

from __future__ import annotations

from collections.abc import Iterator
from importlib import resources
from typing import Any

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.datasets.base import HypergraphDataset
from isalhg.datasets.registry import register_dataset
from isalhg.datasets.schemas import DatasetItem, DatasetMetadata, LabelVocabulary
from isalhg.errors import DatasetIntegrityError, DatasetNotFoundError
from isalhg.types import DatasetName, Seed

STS_ORDERS: tuple[int, ...] = (3, 7, 9, 13, 15)
_STS_COUNTS: dict[int, int] = {3: 1, 7: 1, 9: 1, 13: 2, 15: 80}

_cache: dict[int, tuple[tuple[frozenset[int], ...], ...]] = {}


def _parse_line(line: str, n: int) -> tuple[frozenset[int], ...]:
    """Decode one catalog line into its block list (letter ``a`` = point 0)."""
    if len(line) % 3 != 0:
        raise DatasetIntegrityError(f"malformed STS({n}) line of length {len(line)}")
    blocks = tuple(
        frozenset(ord(c) - ord("a") for c in line[i : i + 3]) for i in range(0, len(line), 3)
    )
    if len(blocks) != n * (n - 1) // 6:
        raise DatasetIntegrityError(
            f"STS({n}) line has {len(blocks)} blocks, expected {n * (n - 1) // 6}"
        )
    return blocks


def _load_order(n: int) -> tuple[tuple[frozenset[int], ...], ...]:
    if n not in _STS_COUNTS:
        raise DatasetNotFoundError(f"no STS listing for order {n}; available: {STS_ORDERS}")
    if n not in _cache:
        text = resources.files("isalhg.datasets").joinpath(f"data/sts/sts{n}.txt").read_text()
        systems = tuple(_parse_line(line, n) for line in text.splitlines() if line.strip())
        if len(systems) != _STS_COUNTS[n]:
            raise DatasetIntegrityError(
                f"STS({n}) listing has {len(systems)} systems, expected {_STS_COUNTS[n]}"
            )
        _cache[n] = systems
    return _cache[n]


def sts_count(n: int) -> int:
    """Number of isomorphism classes of STS(n) in the catalog.

    Parameters
    ----------
    n : int
        Order; one of ``STS_ORDERS``.

    Returns
    -------
    int
        1, 1, 1, 2, 80 for n = 3, 7, 9, 13, 15.

    Raises
    ------
    DatasetNotFoundError
        If ``n`` is not a catalogued order.
    """
    if n not in _STS_COUNTS:
        raise DatasetNotFoundError(f"no STS listing for order {n}; available: {STS_ORDERS}")
    return _STS_COUNTS[n]


def steiner_triple_system(n: int, index: int = 0) -> SparseHypergraph:
    """Build the ``index``-th Steiner triple system of order ``n``.

    Parameters
    ----------
    n : int
        Order; one of ``STS_ORDERS``.
    index : int
        0-based index into the catalog's fixed enumeration order
        (``0 <= index < sts_count(n)``).

    Returns
    -------
    SparseHypergraph
        A fresh hypergraph on ``n`` nodes with ``n(n-1)/6`` 3-uniform blocks;
        every point-pair lies in exactly one block.

    Raises
    ------
    DatasetNotFoundError
        If ``n`` is not a catalogued order or ``index`` is out of range.
    """
    systems = _load_order(n)
    if not 0 <= index < len(systems):
        raise DatasetNotFoundError(
            f"STS({n}) has {len(systems)} systems; index {index} out of range"
        )
    return SparseHypergraph(n_nodes=n, hyperedges=systems[index])


class SteinerTripleSystems(HypergraphDataset):
    """All 85 catalogued Steiner triple systems of orders 3-15.

    Deterministic, unlabelled (trivial vocabulary); every item carries its
    catalog identity ``sts{n}_{i}`` (1-based ``i``) as both ``item_id`` and
    ``iso_class`` -- the systems are pairwise non-isomorphic by the
    classification, re-verified against pynauty at vendoring time
    (``data/sts/README.md``).
    """

    def __init__(self, orders: tuple[int, ...] = STS_ORDERS) -> None:
        unknown = [n for n in orders if n not in _STS_COUNTS]
        if unknown:
            raise DatasetNotFoundError(f"no STS listing for orders {unknown}")
        self._orders = tuple(orders)

    @property
    def name(self) -> DatasetName:
        return "sts_catalog"

    @property
    def metadata(self) -> DatasetMetadata:
        return DatasetMetadata(
            name=self.name,
            n_items=len(self),
            arity_range=(3, 3),
            n_nodes_range=(min(self._orders), max(self._orders)),
            has_iso_labels=True,
            source="pottonen.kapsi.fi/sts19 (vendored; datasets/data/sts/)",
            citation="Kaski & Ostergard, Math. Comp. 73 (2004); Colbourn & Rosa 1999",
            label_vocabulary=LabelVocabulary.trivial(),
        )

    def __iter__(self) -> Iterator[DatasetItem]:
        # iso_class is a per-item integer: the systems are pairwise
        # non-isomorphic (classification; pynauty-verified at vendoring).
        class_id = 0
        for n in self._orders:
            for i in range(sts_count(n)):
                yield DatasetItem(
                    item_id=f"sts{n}_{i + 1}",
                    hypergraph=steiner_triple_system(n, i),
                    iso_class=class_id,
                    extra={"order": n, "catalog_index": i},
                )
                class_id += 1

    def __len__(self) -> int:
        return sum(sts_count(n) for n in self._orders)

    def seed(self, seed: Seed) -> SteinerTripleSystems:  # noqa: ARG002 - deterministic
        return self


def _factory(params: dict[str, Any]) -> HypergraphDataset:
    orders = params.get("orders")
    if orders is None:
        return SteinerTripleSystems()
    return SteinerTripleSystems(orders=tuple(orders))


register_dataset("sts_catalog", _factory)
