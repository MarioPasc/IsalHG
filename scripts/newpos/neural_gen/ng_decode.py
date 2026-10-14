"""Decoding of sampled token sequences, class keys, the frozen sample format and its tallies.

The decoders are the n-gram experiment's own (``experiments.tkde.rq6._ow_decode``,
``decode_fact_word``, ``strict_decode``); nothing here re-implements them.
"""

from __future__ import annotations

import gzip
import json
import logging
import os
import random
import sys
from collections import Counter
from collections.abc import Hashable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from experiments.tkde.rq6 import _ow_decode  # noqa: E402
from isalhg.core.fact_word import decode_fact_word  # noqa: E402
from isalhg.core.sparse_hypergraph import SparseHypergraph  # noqa: E402
from isalhg.generation.incidence_baseline import strict_decode, strict_decode_reason  # noqa: E402
from isalhg.iso_backends.isal_ordered import ordered_fingerprint  # noqa: E402

logger = logging.getLogger(__name__)

#: Frozen key set and order of one sample-file line (contract with the evaluator).
RECORD_KEYS: tuple[str, ...] = (
    "collection",
    "generator",
    "seed",
    "draw",
    "tokens",
    "root_type",
    "status",
    "reason",
    "n",
    "types",
    "facts",
    "connected",
)

ClassKey = tuple[int, str]


@dataclass(frozen=True)
class DecodeSpec:
    """Collection-level decoder parameters, as ``rq6.build_context`` derives them."""

    n_types: int
    n_preds: int
    k: int


@dataclass(frozen=True)
class DecodedDraw:
    """Outcome of decoding one draw."""

    status: str
    reason: str | None
    hypergraph: SparseHypergraph | None
    connected: bool | None


def decode_draw(
    serialization: str,
    tokens: Sequence[Hashable],
    spec: DecodeSpec,
    root: int | None,
) -> DecodedDraw:
    """Decode one sampled token sequence the way ``rq6.run_sample_unit`` does.

    Parameters
    ----------
    serialization : {"ow", "fact", "incidence"}
        Which decoder to apply.
    tokens : Sequence[Hashable]
        The original token objects (not their strings).
    spec : DecodeSpec
        ``n_types``, ``n_preds`` and ``k`` of the collection.
    root : int or None
        Root type for the ordered-walk decoder; ignored by the others.

    Returns
    -------
    DecodedDraw
        ``status`` is ``"decoded"`` or ``"rejected"``; a rejected draw carries the
        rule (incidence) or exception name (a total decoder raising, which is
        recorded rather than allowed to abort the unit).
    """
    if serialization == "incidence":
        hypergraph = strict_decode(tokens, n_types=spec.n_types, n_preds=spec.n_preds)
        if hypergraph is None:
            reason = (
                strict_decode_reason(tokens, n_types=spec.n_types, n_preds=spec.n_preds)
                or "unknown"
            )
            return DecodedDraw("rejected", reason, None, None)
        return DecodedDraw("decoded", None, hypergraph, bool(hypergraph.is_connected()))
    try:
        if serialization == "ow":
            hypergraph = _ow_decode(tokens, spec.k, spec.n_types, spec.n_preds, int(root or 0))
        else:
            hypergraph, _ = decode_fact_word(
                tuple(tokens), n_types=spec.n_types, n_preds=spec.n_preds
            )
    except Exception as exc:  # noqa: BLE001 - a total decoder must not raise; count it if it does
        logger.error("%s sample did not decode: %s", serialization, exc)
        return DecodedDraw("rejected", type(exc).__name__, None, None)
    return DecodedDraw("decoded", None, hypergraph, bool(hypergraph.is_connected()))


def class_key(hypergraph: SparseHypergraph) -> tuple[ClassKey | None, str | None]:
    """Isomorphism-class key ``ordered_fingerprint(H)`` of a connected knowledge base.

    Returns
    -------
    tuple[ClassKey | None, str | None]
        ``(key, None)`` on success, ``(None, exception name)`` if the fingerprint
        cannot be computed.
    """
    try:
        root_label, word = ordered_fingerprint(hypergraph)
    except Exception as exc:  # noqa: BLE001 - counted, not fatal
        return None, type(exc).__name__
    return (int(root_label), word), None


def member_keys(hypergraphs: Iterable[Any]) -> list[ClassKey]:
    """Class key of every collection member, in member order."""
    return [(int(r), w) for r, w in (ordered_fingerprint(H) for H in hypergraphs)]


def kb_fields(hypergraph: SparseHypergraph) -> tuple[int, list[int], list[list[Any]]]:
    """``(n, types, facts)`` in the shape of a ``KBRecord`` JSON.

    Facts are ``[predicate, ascending constant ids]`` sorted by ``(predicate, ids)``.
    """
    n = int(hypergraph.n_nodes)
    types = [int(hypergraph.vertex_label(v)) for v in range(n)]
    facts = sorted(
        (int(label), sorted(int(v) for v in members))
        for _, members, label in hypergraph.iter_edges()
    )
    return n, types, [[pred, members] for pred, members in facts]


def build_record(
    collection: str,
    generator: str,
    seed: int,
    draw: int,
    tokens: Sequence[Hashable],
    root_type: int | None,
    decoded: DecodedDraw,
) -> dict[str, Any]:
    """One sample-file line with exactly the frozen keys, in the frozen order."""
    n: int | None = None
    types: list[int] | None = None
    facts: list[list[Any]] | None = None
    if decoded.hypergraph is not None:
        n, types, facts = kb_fields(decoded.hypergraph)
    record: dict[str, Any] = {
        "collection": collection,
        "generator": generator,
        "seed": int(seed),
        "draw": int(draw),
        "tokens": [str(t) for t in tokens],
        "root_type": None if root_type is None else int(root_type),
        "status": decoded.status,
        "reason": decoded.reason,
        "n": n,
        "types": types,
        "facts": facts,
        "connected": decoded.connected,
    }
    return record


@dataclass
class DrawOutcome:
    """A built record plus what the tallies need and the file does not carry."""

    record: dict[str, Any]
    usable: bool
    key: ClassKey | None
    key_error: str | None
    n_nodes: int | None
    n_edges: int | None


def process_draw(
    collection: str,
    serialization: str,
    generator: str,
    seed: int,
    draw: int,
    tokens: Sequence[Hashable],
    root_type: int | None,
    spec: DecodeSpec,
) -> DrawOutcome:
    """Decode one draw, build its record, and compute its class key if it is usable.

    A draw is usable when it decoded, is connected, and has at least one constant:
    the empty knowledge base is vacuously connected but has no canonical word.
    """
    decoded = decode_draw(serialization, tokens, spec, root_type)
    record = build_record(collection, generator, seed, draw, tokens, root_type, decoded)
    hypergraph = decoded.hypergraph
    usable = bool(decoded.connected) and hypergraph is not None and hypergraph.n_nodes >= 1
    key: ClassKey | None = None
    key_error: str | None = None
    if usable:
        key, key_error = class_key(hypergraph)
    return DrawOutcome(
        record=record,
        usable=usable,
        key=key,
        key_error=key_error,
        n_nodes=None if hypergraph is None else int(hypergraph.n_nodes),
        n_edges=None if hypergraph is None else int(hypergraph.n_edges),
    )


def draw_roots(collection: str, seed: int, train_roots: Sequence[int], n_draws: int) -> list[int]:
    """Root types for the ordered-walk decoder, drawn from the training roots' empirical law."""
    rng = random.Random(f"newpos-gru-ow-root|{collection}|{seed}")
    return [rng.choice(train_roots) if train_roots else 0 for _ in range(n_draws)]


def tally(
    outcomes: Sequence[DrawOutcome],
    capped: Sequence[bool],
    train_keys: set[ClassKey],
    heldout_keys: set[ClassKey],
) -> dict[str, Any]:
    """Counts and rates of one unit.

    Parameters
    ----------
    outcomes : Sequence[DrawOutcome]
        One per draw.
    capped : Sequence[bool]
        Cap flags aligned with ``outcomes``.
    train_keys : set[ClassKey]
        Class keys of the training members.
    heldout_keys : set[ClassKey]
        Class keys of the validation and test members.

    Returns
    -------
    dict[str, Any]
        Counts (``n_draws`` ... ``n_vun``), rates, and the rejection-reason and
        fingerprint-error histograms. ``n_novel_usable`` counts usable draws with
        multiplicity whose class is not a member of the full collection;
        ``n_vun`` counts distinct such classes.
    """
    n_draws = len(outcomes)
    decoded = [o for o in outcomes if o.record["status"] == "decoded"]
    usable = [o for o in outcomes if o.usable]
    keyed = [o.key for o in usable if o.key is not None]
    unique = set(keyed)
    all_keys = train_keys | heldout_keys
    novel_draws = [k for k in keyed if k not in all_keys]
    vun = {k for k in unique if k not in all_keys}
    copies_train = sum(1 for k in keyed if k in train_keys)
    copies_heldout = sum(1 for k in keyed if k not in train_keys and k in heldout_keys)
    reasons = Counter(o.record["reason"] for o in outcomes if o.record["status"] == "rejected")
    key_errors = Counter(o.key_error for o in usable if o.key_error is not None)
    n_connected = sum(1 for o in decoded if o.record["connected"])
    n_empty = sum(1 for o in decoded if o.n_nodes == 0)
    # The evaluator additionally requires m >= 1; the delta is reported so the two
    # notions of "usable" can be reconciled exactly.
    n_zero_fact_usable = sum(1 for o in usable if o.n_edges == 0)
    return {
        "n_draws": n_draws,
        "n_decoded": len(decoded),
        "n_rejected": n_draws - len(decoded),
        "n_connected": n_connected,
        "n_empty_decoded": n_empty,
        "n_usable": len(usable),
        "n_zero_fact_usable": n_zero_fact_usable,
        "n_keyed_usable": len(keyed),
        "n_key_errors": len(usable) - len(keyed),
        "n_unique_usable": len(unique),
        "n_novel_usable": len(novel_draws),
        "n_copy_train": copies_train,
        "n_copy_heldout": copies_heldout,
        "n_vun": len(vun),
        "n_capped": int(sum(capped)),
        "validity": len(decoded) / n_draws if n_draws else None,
        "connectivity_given_decoded": n_connected / len(decoded) if decoded else None,
        "usable_per_draw": len(usable) / n_draws if n_draws else None,
        "residual_ood_rate": 1.0 - len(usable) / n_draws if n_draws else None,
        "uniqueness": len(unique) / len(keyed) if keyed else None,
        "novelty": len(novel_draws) / len(keyed) if keyed else None,
        "vun_per_draw": len(vun) / n_draws if n_draws else None,
        "mean_n_decoded": _mean(o.n_nodes for o in decoded),
        "mean_m_decoded": _mean(o.n_edges for o in decoded),
        "rejection_reasons": dict(sorted(reasons.items(), key=lambda kv: str(kv[0]))),
        "key_errors": dict(sorted(key_errors.items())),
    }


def _mean(values: Iterable[int | None]) -> float | None:
    kept = [v for v in values if v is not None]
    return sum(kept) / len(kept) if kept else None


def write_samples_atomic(path: Path, outcomes: Sequence[DrawOutcome]) -> None:
    """Write the gzipped JSONL file via a temporary name so a kill never leaves a partial file."""
    tmp = path.with_name(path.name + ".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8", compresslevel=6) as handle:
        for outcome in outcomes:
            handle.write(json.dumps(outcome.record, separators=(",", ":")) + "\n")
    os.replace(tmp, path)


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    """Write a JSON file atomically."""
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
    os.replace(tmp, path)
