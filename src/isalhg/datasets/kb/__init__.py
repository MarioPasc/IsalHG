"""Knowledge-base collections for the TKDE article.

A *knowledge base* here is a labelled hypergraph read logically: constants are
vertices carrying a type, ground facts are hyperedges carrying a predicate and
are sets of constants. :class:`~isalhg.datasets.kb.base.KBRecord` is the frozen
value type the whole experimental pipeline speaks;
:class:`~isalhg.datasets.kb.base.KBCollection` bundles records with the
collection-scoped vocabularies.

Layering (``docs/engineering/CODE_DESIGN.md`` §4): this package may import
``isalhg.core`` and ``isalhg.iso_backends`` (the latter only inside function
bodies, so ``pynauty`` stays off the import path until an isomorphism check is
actually requested).

Modules
-------
base
    ``KBRecord`` / ``KBCollection``, the envelope, structural helpers.
io
    JSONL persistence (``records.jsonl`` + ``vocab.json`` + ``census.json``)
    and the registry-visible dataset wrapper.
wd50k
    WD50K(33/66/100/all) entity knowledge bases with roles and P31 labels.
ndc_quarterly
    NDC-classes / NDC-substances quarterly co-formulation knowledge bases.
ladders
    Seeded single-edit sets, constant-preserving ladders, variant collections.
corruptions
    Seeded fact-level corruptions and the iso-twin construction.
envelope_sweep
    The RQ7 operating-envelope grid and its random generator.
synthetic_rq1
    The 2,000-member synthetic corpus of the RQ1 addressing comparison.
"""

from __future__ import annotations

from isalhg.datasets.kb.base import (
    DEFAULT_ENVELOPE,
    Envelope,
    Fact,
    KBCollection,
    KBCollectionError,
    KBCorpusError,
    KBGenerationError,
    KBRecord,
    KBRecordError,
    compact,
    is_connected,
    iso_fingerprint,
    make_record,
)
from isalhg.datasets.kb.io import read_jsonl, write_jsonl

__all__ = [
    "DEFAULT_ENVELOPE",
    "Envelope",
    "Fact",
    "KBCollection",
    "KBCollectionError",
    "KBCorpusError",
    "KBGenerationError",
    "KBRecord",
    "KBRecordError",
    "compact",
    "is_connected",
    "iso_fingerprint",
    "make_record",
    "read_jsonl",
    "write_jsonl",
]
