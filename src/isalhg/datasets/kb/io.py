"""JSONL persistence for knowledge-base collections.

Layout of a frozen collection directory (``<results>/corpora/<name>/``)::

    records.jsonl   one JSON object per record; keys = the KBRecord fields
    vocab.json      name, type/pred/role names, k_max, meta, n_records
    census.json     obtained structural census beside the expected numbers

``write_jsonl`` then ``read_jsonl`` returns an equal collection: the record
fields, the vocabularies and the metadata all round-trip. The directory is
self-contained -- nothing outside it is needed to rebuild the collection.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from isalhg.datasets.base import HypergraphDataset
from isalhg.datasets.kb.base import (
    KBCollection,
    KBCollectionError,
    KBRecord,
    dumps_record,
)
from isalhg.datasets.registry import register_dataset
from isalhg.datasets.schemas import DatasetItem, DatasetMetadata, LabelVocabulary
from isalhg.types import DatasetName

RECORDS_FILE = "records.jsonl"
VOCAB_FILE = "vocab.json"
CENSUS_FILE = "census.json"


def _atomic_write(path: Path, payload: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(payload, encoding="utf-8")
    os.replace(tmp, path)


def write_jsonl(
    collection: KBCollection,
    directory: Path | str,
    *,
    census: dict[str, Any] | None = None,
) -> Path:
    """Freeze ``collection`` into ``directory``.

    Parameters
    ----------
    collection : KBCollection
        The collection to persist.
    directory : Path or str
        Target directory; created if missing.
    census : dict or None, optional
        Census payload for ``census.json``. Defaults to
        :meth:`KBCollection.census`.

    Returns
    -------
    Path
        The directory written.
    """
    out = Path(directory)
    out.mkdir(parents=True, exist_ok=True)
    lines = "".join(dumps_record(record) + "\n" for record in collection.records)
    _atomic_write(out / RECORDS_FILE, lines)
    _atomic_write(
        out / VOCAB_FILE,
        json.dumps(collection.vocab_json(), indent=1, ensure_ascii=False) + "\n",
    )
    payload = collection.census() if census is None else census
    _atomic_write(out / CENSUS_FILE, json.dumps(payload, indent=1, ensure_ascii=False) + "\n")
    return out


def read_jsonl(directory: Path | str) -> KBCollection:
    """Load a frozen collection from ``directory``.

    Parameters
    ----------
    directory : Path or str
        A directory written by :func:`write_jsonl`.

    Returns
    -------
    KBCollection
        The collection, with member order exactly as written.

    Raises
    ------
    KBCollectionError
        If ``records.jsonl`` or ``vocab.json`` is missing, or the record count
        disagrees with the vocabulary header.
    """
    root = Path(directory)
    records_path = root / RECORDS_FILE
    vocab_path = root / VOCAB_FILE
    for path in (records_path, vocab_path):
        if not path.is_file():
            raise KBCollectionError(f"missing {path}")
    vocab = json.loads(vocab_path.read_text(encoding="utf-8"))
    records = tuple(
        KBRecord.from_json(json.loads(line))
        for line in records_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )
    declared = vocab.get("n_records")
    if declared is not None and int(declared) != len(records):
        raise KBCollectionError(
            f"{root}: vocab.json declares {declared} records, records.jsonl holds {len(records)}"
        )
    return KBCollection(
        name=str(vocab["name"]),
        records=records,
        type_names=tuple(vocab["type_names"]),
        pred_names=tuple(vocab["pred_names"]),
        role_names=tuple(vocab.get("role_names") or ()),
        k_max=int(vocab["k_max"]),
        meta=dict(vocab.get("meta") or {}),
    )


def read_census(directory: Path | str) -> dict[str, Any]:
    """Read ``census.json`` of a frozen collection; ``{}`` when absent."""
    path = Path(directory) / CENSUS_FILE
    if not path.is_file():
        return {}
    payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return payload


class KBCollectionDataset(HypergraphDataset):
    """Registry-visible view of a frozen collection as a hypergraph dataset.

    Each :class:`DatasetItem` carries the record's hypergraph, no isomorphism
    label, and the record itself (plus its roles map and identities) in
    ``extra`` so a protocol can reach the logical view.
    """

    def __init__(self, directory: Path | str) -> None:
        """Bind the dataset to a frozen collection directory (loaded lazily)."""
        self._directory = Path(directory)
        self._collection: KBCollection | None = None

    @property
    def collection(self) -> KBCollection:
        """The loaded collection."""
        if self._collection is None:
            self._collection = read_jsonl(self._directory)
        return self._collection

    @property
    def name(self) -> DatasetName:
        return f"kb_collection:{self.collection.name}"

    @property
    def metadata(self) -> DatasetMetadata:
        collection = self.collection
        arities = [r.max_arity for r in collection.records] or [0]
        min_arity = min(
            (len(members) for r in collection.records for _, members in r.facts), default=0
        )
        ns = [r.n for r in collection.records] or [0]
        return DatasetMetadata(
            name=self.name,
            n_items=len(collection),
            arity_range=(min_arity, max(arities)),
            n_nodes_range=(min(ns), max(ns)),
            has_iso_labels=False,
            source=str(self._directory),
            citation=str(collection.meta.get("citation", "")),
            label_vocabulary=LabelVocabulary(
                vertex_symbols=collection.type_names or ("⊥",),
                edge_symbols=collection.pred_names or ("⊥",),
            ),
        )

    def __iter__(self) -> Iterator[DatasetItem]:
        for record in self.collection.records:
            yield DatasetItem(
                item_id=record.kb_id,
                hypergraph=record.to_hypergraph(),
                iso_class=None,
                extra={
                    "record": record,
                    "roles_map": record.roles_map(),
                    "constant_ids": record.constant_ids,
                    "label": record.label,
                },
            )

    def __len__(self) -> int:
        return len(self.collection)


def _factory(params: dict[str, Any]) -> KBCollectionDataset:
    if "directory" not in params:
        raise KBCollectionError("kb_collection requires a 'directory' parameter")
    return KBCollectionDataset(params["directory"])


register_dataset("kb_collection", _factory)
