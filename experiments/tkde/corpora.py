"""Access to the frozen TKDE corpora.

Every runner reads its members through this module and nothing else: the frozen
JSONL under ``<RESULTS_ROOT>/corpora/<collection>/`` is the only input, so a
run is reproducible from the directory the sync script pushes to Picasso.

The helpers return their results in *member order* -- the order of
``collection.records``, which is the order every cached ``N x N`` distance
matrix is indexed by.
"""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.datasets.kb.base import KBCollection, KBCollectionError, KBRecord
from isalhg.datasets.kb.io import read_census, read_jsonl

DEFAULT_RESULTS_ROOT = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE")
RESULTS_ROOT_ENV = "ISALHG_RESULTS_ROOT"
CORPORA_SUBDIR = "corpora"

COLLECTIONS: tuple[str, ...] = (
    "wd50k66",
    "wd50k66_full",
    "wd50k100",
    "ndc_classes",
    "ndc_substances",
    "synthetic_rq1",
)


def results_root(root: Path | str | None = None) -> Path:
    """Resolve the results root (``ISALHG_RESULTS_ROOT``, else the drive default)."""
    if root is not None:
        return Path(root)
    env = os.environ.get(RESULTS_ROOT_ENV)
    return Path(env) if env else DEFAULT_RESULTS_ROOT


def corpora_root(root: Path | str | None = None) -> Path:
    """Directory holding the frozen collections.

    Resolution order: an explicit ``root`` (the directory holding ``corpora/``);
    ``ISALHG_CORPORA_ROOT``; ``ISALHG_DATA_ROOT/corpora`` when that directory
    exists (the layout on Picasso, where the frozen corpora are staged with the
    raw data and the results root is a different filesystem); otherwise the
    results root, which is where the freeze script writes them locally.
    """
    if root is not None:
        return Path(root) / CORPORA_SUBDIR
    explicit = os.environ.get("ISALHG_CORPORA_ROOT")
    if explicit:
        return Path(explicit)
    data_root = os.environ.get("ISALHG_DATA_ROOT")
    if data_root and (Path(data_root) / CORPORA_SUBDIR).is_dir():
        return Path(data_root) / CORPORA_SUBDIR
    return results_root(None) / CORPORA_SUBDIR


def collection_dir(name: str, root: Path | str | None = None) -> Path:
    """Directory of one frozen collection."""
    return corpora_root(root) / name


def available_collections(root: Path | str | None = None) -> tuple[str, ...]:
    """Names of the frozen collections present under the corpora root."""
    base = corpora_root(root)
    if not base.is_dir():
        return ()
    return tuple(
        sorted(p.name for p in base.iterdir() if p.is_dir() and (p / "records.jsonl").is_file())
    )


def load_collection(name: str, root: Path | str | None = None) -> KBCollection:
    """Load one frozen collection by name.

    Parameters
    ----------
    name : str
        Collection directory name, e.g. ``"wd50k66"``.
    root : Path or str or None, optional
        Results root override; the collection is read from
        ``<root>/corpora/<name>/``.

    Returns
    -------
    KBCollection
        The collection, member order as frozen.

    Raises
    ------
    KBCollectionError
        If the directory is missing or incomplete.
    """
    directory = collection_dir(name, root)
    if not directory.is_dir():
        raise KBCollectionError(
            f"no frozen collection at {directory}; run scripts/tkde/freeze_corpora.py"
        )
    return read_jsonl(directory)


def load_census(name: str, root: Path | str | None = None) -> dict[str, Any]:
    """Read the frozen ``census.json`` of one collection (``{}`` when absent)."""
    return read_census(collection_dir(name, root))


def hypergraphs(collection: KBCollection) -> list[SparseHypergraph]:
    """Labelled hypergraph of every member, in member order."""
    return [record.to_hypergraph() for record in collection.records]


def roles_maps(collection: KBCollection) -> list[Mapping[int, Mapping[int, int]] | None]:
    """``RolesMap`` of every member, in member order; ``None`` where absent."""
    return [record.roles_map() for record in collection.records]


def identities(collection: KBCollection) -> list[tuple[str, ...] | None]:
    """External constant identities of every member -- evaluation use only."""
    return [record.constant_ids for record in collection.records]


def labels(collection: KBCollection) -> list[str | None]:
    """Class label of every member, in member order."""
    return [record.label for record in collection.records]


def member_ids(collection: KBCollection) -> list[str]:
    """``kb_id`` of every member, in member order."""
    return [record.kb_id for record in collection.records]


def records_by_id(collection: KBCollection) -> dict[str, KBRecord]:
    """Map ``kb_id`` to the record."""
    return {record.kb_id: record for record in collection.records}


def consecutive_pairs(collection: KBCollection) -> list[dict[str, Any]]:
    """The natural consecutive-window pairs of a time series (empty otherwise).

    Each entry carries ``a``, ``b`` (member ids), ``delta`` (the exact
    fact-level difference from the identities) and ``constant_preserving``.
    """
    return list(collection.meta.get("consecutive_pairs") or [])


def runs(collection: KBCollection) -> dict[str, list[str]]:
    """Per class id, its member ids ordered by window (empty otherwise)."""
    return dict(collection.meta.get("runs") or {})


def consecutive_runs(collection: KBCollection, min_length: int = 1) -> list[dict[str, Any]]:
    """Maximal runs of adjacent windows, filtered by length.

    Parameters
    ----------
    collection : KBCollection
        A time-series collection.
    min_length : int, optional
        Keep only runs of at least this many members.

    Returns
    -------
    list[dict]
        Entries ``{"class_id": ..., "kb_ids": [...]}``.
    """
    return [
        run
        for run in (collection.meta.get("consecutive_runs") or [])
        if len(run.get("kb_ids", ())) >= min_length
    ]


def subset(
    collection: KBCollection, ids: Sequence[str], *, name: str | None = None
) -> KBCollection:
    """A sub-collection in the given id order, sharing the parent's vocabularies.

    Parameters
    ----------
    collection : KBCollection
        The parent.
    ids : Sequence[str]
        Member ids to keep, in the order the sub-collection should have.
    name : str or None, optional
        Name of the result; defaults to ``<parent>_subset``.

    Returns
    -------
    KBCollection
        The sub-collection; ``meta["parent"]`` names the parent.

    Raises
    ------
    KBCollectionError
        If an id is not a member of ``collection``.
    """
    index = records_by_id(collection)
    missing = [i for i in ids if i not in index]
    if missing:
        raise KBCollectionError(f"{collection.name}: unknown member ids {missing[:5]}")
    meta = dict(collection.meta)
    meta["parent"] = collection.name
    return KBCollection(
        name=name or f"{collection.name}_subset",
        records=tuple(index[i] for i in ids),
        type_names=collection.type_names,
        pred_names=collection.pred_names,
        role_names=collection.role_names,
        k_max=collection.k_max,
        meta=meta,
    )
