"""The knowledge-base record and collection value types.

Acceptance criteria (frozen contract, ``docs/article/D_ART3/experiments/CODE_PLAN.md`` §2.4)

1. ``KBRecord`` carries ``kb_id, n, types, facts, roles, constant_ids, label,
   meta`` and nothing else; every field is immutable and JSON-representable.
2. ``to_hypergraph()`` produces a :class:`SparseHypergraph` whose edge order is
   the record's fact order, with the collection-scoped vocabulary sizes.
3. ``roles_map()`` produces ``{edge_id: {node_id: role_id}}`` in that same edge
   order -- the ``RolesMap`` shape the fact-word encoder consumes.
4. Facts are sorted, distinct, of arity >= 2, over constants in ``range(n)``.
5. ``constant_ids`` is evaluation-only: no method of this package reads it to
   decide anything structural.
"""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import Any, TypeAlias

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.errors import DatasetError
from isalhg.types import EdgeId, Fingerprint, NodeId

Fact: TypeAlias = tuple[int, tuple[int, ...]]
"""One ground fact: ``(predicate id, ascending distinct constant ids)``."""

RoleId: TypeAlias = int
RolesMap: TypeAlias = Mapping[EdgeId, Mapping[NodeId, RoleId]]

META_N_TYPES = "n_types"
META_N_PREDS = "n_preds"


class KBCorpusError(DatasetError):
    """Root of the knowledge-base corpus failures."""


class KBRecordError(KBCorpusError):
    """A record violates the structural contract."""


class KBCollectionError(KBCorpusError):
    """A collection is internally inconsistent, or its census disagrees."""


class KBGenerationError(KBCorpusError):
    """A generator was asked for something structurally impossible."""


@dataclass(frozen=True)
class Envelope:
    """Size window inside which a knowledge base is *encodable*.

    Attributes
    ----------
    n_max : int
        Largest number of constants.
    m_min : int
        Smallest number of facts (a one-fact knowledge base carries no
        structure).
    m_max : int
        Largest number of facts.
    k_max : int
        Largest fact arity the compiled alphabet supports.
    """

    n_max: int = 24
    m_min: int = 3
    m_max: int = 110
    k_max: int = 10

    def admits(self, n: int, m: int, max_arity: int) -> bool:
        """True iff ``(n, m, max_arity)`` lies inside the window."""
        return n <= self.n_max and self.m_min <= m <= self.m_max and max_arity <= self.k_max

    def as_dict(self) -> dict[str, int]:
        """JSON-representable view of the window."""
        return {
            "n_max": self.n_max,
            "m_min": self.m_min,
            "m_max": self.m_max,
            "k_max": self.k_max,
        }


DEFAULT_ENVELOPE = Envelope()
"""The measured canonicalization frontier used by every collection."""


def _freeze_json(value: Any) -> Any:
    """Normalize a metadata value to a JSON-native, comparison-stable form."""
    if isinstance(value, tuple):
        return [_freeze_json(v) for v in value]
    if isinstance(value, list):
        return [_freeze_json(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _freeze_json(v) for k, v in value.items()}
    return value


def is_connected(n: int, facts: Sequence[Fact]) -> bool:
    """True iff every constant occurs and the primal graph on them is connected.

    Parameters
    ----------
    n : int
        Number of constants; ids are ``0 .. n-1``.
    facts : Sequence[Fact]
        The ground facts.

    Returns
    -------
    bool
        ``False`` when a constant is isolated (not merely disconnected): a
        knowledge base is its set of facts, so an unused constant is not part
        of it.
    """
    used: set[int] = set()
    for _, members in facts:
        used.update(members)
    if n == 0 or len(used) != n:
        return False
    adjacency: dict[int, set[int]] = defaultdict(set)
    for _, members in facts:
        for a in members:
            for b in members:
                if a != b:
                    adjacency[a].add(b)
    start = next(iter(used))
    seen = {start}
    stack = [start]
    while stack:
        v = stack.pop()
        for u in adjacency[v]:
            if u not in seen:
                seen.add(u)
                stack.append(u)
    return len(seen) == n


def _normalize_facts(
    facts: Iterable[Sequence[Any]],
) -> tuple[Fact, ...]:
    out: list[Fact] = []
    for entry in facts:
        pred, members = entry[0], entry[1]
        out.append((int(pred), tuple(sorted({int(v) for v in members}))))
    return tuple(out)


@dataclass(frozen=True)
class KBRecord:
    """One knowledge base.

    Parameters
    ----------
    kb_id : str
        Stable identifier, unique inside its collection.
    n : int
        Number of constants; ids are ``0 .. n-1``.
    types : tuple[int, ...]
        Per-constant type id, in ``range(n_types)`` of the collection.
    facts : tuple[Fact, ...]
        Ground facts ``(predicate id, ascending distinct constant ids)``;
        arity ``>= 2``, no duplicates. Stored sorted by
        ``(predicate, operands)``.
    roles : tuple[tuple[int, ...], ...] or None, optional
        Per fact, one role id per operand, aligned with the operand tuple.
        ``None`` when the collection has no roles.
    constant_ids : tuple[str, ...] or None, optional
        External identities of the constants, aligned with ``types``.
        **Evaluation only** -- no method here reads them.
    label : str or None, optional
        Class label (RQ5 ground truth).
    meta : Mapping[str, Any], optional
        JSON-native side information. Two keys are reserved and stamped by
        :class:`KBCollection`: ``"n_types"`` and ``"n_preds"``, the
        collection-scoped vocabulary sizes that :meth:`to_hypergraph` needs.

    Raises
    ------
    KBRecordError
        If the structural contract is violated.
    """

    kb_id: str
    n: int
    types: tuple[int, ...]
    facts: tuple[Fact, ...]
    roles: tuple[tuple[int, ...], ...] | None = None
    constant_ids: tuple[str, ...] | None = None
    label: str | None = None
    meta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        set_ = object.__setattr__
        set_(self, "n", int(self.n))
        set_(self, "types", tuple(int(t) for t in self.types))
        facts = _normalize_facts(self.facts)
        roles = (
            None if self.roles is None else tuple(tuple(int(r) for r in row) for row in self.roles)
        )
        if roles is not None and len(roles) != len(facts):
            raise KBRecordError(f"{self.kb_id}: roles has {len(roles)} rows for {len(facts)} facts")
        order = sorted(range(len(facts)), key=lambda i: facts[i])
        set_(self, "facts", tuple(facts[i] for i in order))
        set_(self, "roles", None if roles is None else tuple(roles[i] for i in order))
        if self.constant_ids is not None:
            set_(self, "constant_ids", tuple(str(c) for c in self.constant_ids))
        set_(self, "label", None if self.label is None else str(self.label))
        set_(self, "meta", _freeze_json(dict(self.meta)))
        self._validate()

    def _validate(self) -> None:
        if self.n < 0:
            raise KBRecordError(f"{self.kb_id}: n must be non-negative, got {self.n}")
        if len(self.types) != self.n:
            raise KBRecordError(
                f"{self.kb_id}: types has length {len(self.types)}, expected {self.n}"
            )
        if self.constant_ids is not None and len(self.constant_ids) != self.n:
            raise KBRecordError(
                f"{self.kb_id}: constant_ids has length {len(self.constant_ids)}, expected {self.n}"
            )
        seen: set[Fact] = set()
        for index, (pred, members) in enumerate(self.facts):
            if len(members) < 2:
                raise KBRecordError(
                    f"{self.kb_id}: fact {index} has arity {len(members)}, expected >= 2"
                )
            if members[-1] >= self.n or members[0] < 0:
                raise KBRecordError(
                    f"{self.kb_id}: fact {index} addresses a constant outside [0, {self.n})"
                )
            if pred < 0:
                raise KBRecordError(f"{self.kb_id}: fact {index} has negative predicate {pred}")
            if (pred, members) in seen:
                raise KBRecordError(f"{self.kb_id}: duplicate fact {(pred, members)!r}")
            seen.add((pred, members))
        if self.roles is not None:
            for index, row in enumerate(self.roles):
                if len(row) != len(self.facts[index][1]):
                    raise KBRecordError(
                        f"{self.kb_id}: roles row {index} has {len(row)} entries for a fact "
                        f"of arity {len(self.facts[index][1])}"
                    )

    # ------------------------------------------------------------------
    # Derived quantities
    # ------------------------------------------------------------------

    @property
    def m(self) -> int:
        """Number of facts."""
        return len(self.facts)

    @property
    def max_arity(self) -> int:
        """Largest fact arity, or 0 when the record has no facts."""
        return max((len(members) for _, members in self.facts), default=0)

    @property
    def n_types(self) -> int:
        """Collection-scoped type-vocabulary size (from ``meta``, else observed)."""
        stamped = self.meta.get(META_N_TYPES)
        if stamped is not None:
            return int(stamped)
        return max(self.types, default=0) + 1

    @property
    def n_preds(self) -> int:
        """Collection-scoped predicate-vocabulary size (from ``meta``, else observed)."""
        stamped = self.meta.get(META_N_PREDS)
        if stamped is not None:
            return int(stamped)
        return max((pred for pred, _ in self.facts), default=0) + 1

    def arity_histogram(self) -> dict[int, int]:
        """Map arity -> number of facts of that arity."""
        hist: dict[int, int] = {}
        for _, members in self.facts:
            hist[len(members)] = hist.get(len(members), 0) + 1
        return hist

    def degree_sequence(self) -> tuple[int, ...]:
        """Descending per-constant fact degree."""
        degree = [0] * self.n
        for _, members in self.facts:
            for v in members:
                degree[v] += 1
        return tuple(sorted(degree, reverse=True))

    def fact_set(self) -> frozenset[Fact]:
        """The facts as a set -- the object the fact-level distance measures."""
        return frozenset(self.facts)

    def key(self) -> tuple[int, tuple[int, ...], tuple[Fact, ...]]:
        """Hashable structural key ignoring identifiers, labels and metadata."""
        return (self.n, self.types, self.facts)

    def is_connected(self) -> bool:
        """True iff every constant occurs in a fact and the primal graph is connected."""
        return is_connected(self.n, self.facts)

    # ------------------------------------------------------------------
    # Bridges
    # ------------------------------------------------------------------

    def to_hypergraph(
        self, *, n_types: int | None = None, n_preds: int | None = None
    ) -> SparseHypergraph:
        """Build the labelled hypergraph of this record.

        Vertex labels are the constant types, edge labels the predicates, and
        the edge order is the record's fact order.

        Parameters
        ----------
        n_types : int or None, optional
            Vertex-vocabulary size. Defaults to the collection-scoped value
            stamped in ``meta``, else ``max(types) + 1``.
        n_preds : int or None, optional
            Edge-vocabulary size. Defaults to the collection-scoped value
            stamped in ``meta``, else ``max(predicate) + 1``.

        Returns
        -------
        SparseHypergraph
            Labelled hypergraph with ``n_nodes == self.n`` and
            ``n_edges == self.m``.
        """
        nt = self.n_types if n_types is None else n_types
        np_ = self.n_preds if n_preds is None else n_preds
        return SparseHypergraph(
            self.n,
            [frozenset(members) for _, members in self.facts],
            n_vertex_labels=max(1, nt),
            n_edge_labels=max(1, np_),
            vertex_labels=list(self.types),
            edge_labels=[pred for pred, _ in self.facts],
        )

    def roles_map(self) -> RolesMap | None:
        """Return ``{edge_id: {node_id: role_id}}``, or ``None`` without roles."""
        if self.roles is None:
            return None
        out: dict[EdgeId, dict[NodeId, RoleId]] = {}
        for edge_id, ((_, members), row) in enumerate(zip(self.facts, self.roles, strict=True)):
            out[edge_id] = dict(zip(members, row, strict=True))
        return out

    def to_json(self) -> dict[str, Any]:
        """JSON-native view; the keys are exactly the dataclass fields."""
        return {
            "kb_id": self.kb_id,
            "n": self.n,
            "types": list(self.types),
            "facts": [[pred, list(members)] for pred, members in self.facts],
            "roles": None if self.roles is None else [list(row) for row in self.roles],
            "constant_ids": None if self.constant_ids is None else list(self.constant_ids),
            "label": self.label,
            "meta": dict(self.meta),
        }

    @classmethod
    def from_json(cls, payload: Mapping[str, Any]) -> KBRecord:
        """Inverse of :meth:`to_json`."""
        return cls(
            kb_id=str(payload["kb_id"]),
            n=int(payload["n"]),
            types=tuple(int(t) for t in payload["types"]),
            facts=_normalize_facts(payload["facts"]),
            roles=(
                None
                if payload.get("roles") is None
                else tuple(tuple(int(r) for r in row) for row in payload["roles"])
            ),
            constant_ids=(
                None
                if payload.get("constant_ids") is None
                else tuple(str(c) for c in payload["constant_ids"])
            ),
            label=payload.get("label"),
            meta=dict(payload.get("meta") or {}),
        )


def make_record(
    kb_id: str,
    n: int,
    types: Sequence[int],
    facts: Sequence[Fact],
    *,
    roles: Sequence[Sequence[int]] | None = None,
    constant_ids: Sequence[str] | None = None,
    label: str | None = None,
    meta: Mapping[str, Any] | None = None,
    require_connected: bool = True,
) -> KBRecord | None:
    """Build a record, returning ``None`` when the structure is rejected.

    Parameters
    ----------
    kb_id : str
        Identifier for the result.
    n : int
        Number of constants.
    types : Sequence[int]
        Per-constant type ids.
    facts : Sequence[Fact]
        Ground facts; duplicates are dropped, arity < 2 rejects the record.
    roles : Sequence[Sequence[int]] or None, optional
        Per-fact role rows aligned with ``facts`` before deduplication.
    constant_ids : Sequence[str] or None, optional
        External identities.
    label : str or None, optional
        Class label.
    meta : Mapping[str, Any] or None, optional
        Side information.
    require_connected : bool, optional
        When true (default) a disconnected result -- or one with an isolated
        constant -- is rejected.

    Returns
    -------
    KBRecord or None
        ``None`` when the record is empty, has an arity-1 fact, or fails the
        connectivity requirement.
    """
    normalized = _normalize_facts(facts)
    if not normalized or any(len(members) < 2 for _, members in normalized):
        return None
    seen: set[Fact] = set()
    keep: list[int] = []
    for index, fact in enumerate(normalized):
        if fact in seen:
            continue
        seen.add(fact)
        keep.append(index)
    kept_facts = tuple(normalized[i] for i in keep)
    kept_roles = None if roles is None else tuple(tuple(roles[i]) for i in keep)
    if require_connected and not is_connected(n, kept_facts):
        return None
    return KBRecord(
        kb_id=kb_id,
        n=n,
        types=tuple(types),
        facts=kept_facts,
        roles=kept_roles,
        constant_ids=None if constant_ids is None else tuple(constant_ids),
        label=label,
        meta=dict(meta or {}),
    )


def compact(
    kb_id: str,
    types: Sequence[int],
    facts: Sequence[Fact],
    *,
    constant_ids: Sequence[str] | None = None,
    label: str | None = None,
    meta: Mapping[str, Any] | None = None,
    require_connected: bool = True,
) -> KBRecord | None:
    """Drop constants that occur in no fact, renumber densely, and build a record.

    A knowledge base *is* its set of ground facts, so a constant left with no
    fact after a deletion has left the knowledge base.

    Parameters
    ----------
    kb_id : str
        Identifier for the result.
    types : Sequence[int]
        Per-constant type ids in the *pre-compaction* numbering.
    facts : Sequence[Fact]
        Facts in the pre-compaction numbering.
    constant_ids : Sequence[str] or None, optional
        Identities in the pre-compaction numbering; the surviving subset is
        carried through in the new order.
    label : str or None, optional
        Class label.
    meta : Mapping[str, Any] or None, optional
        Side information.
    require_connected : bool, optional
        Reject a disconnected result.

    Returns
    -------
    KBRecord or None
        ``None`` when nothing survives or the result is rejected.
    """
    normalized = _normalize_facts(facts)
    used = sorted({v for _, members in normalized for v in members})
    if not used:
        return None
    remap = {v: i for i, v in enumerate(used)}
    new_facts = [(pred, tuple(remap[v] for v in members)) for pred, members in normalized]
    return make_record(
        kb_id,
        len(used),
        [types[v] for v in used],
        new_facts,
        constant_ids=None if constant_ids is None else [constant_ids[v] for v in used],
        label=label,
        meta=meta,
        require_connected=require_connected,
    )


def iso_fingerprint(record: KBRecord) -> Fingerprint:
    """Isomorphism fingerprint of ``record`` via ``pynauty`` on the Levi graph.

    Two records are isomorphic as labelled knowledge bases iff their
    fingerprints are equal. Used as the rejection oracle of every generator.

    Parameters
    ----------
    record : KBRecord
        The record to fingerprint.

    Returns
    -------
    Fingerprint
        Opaque bytes; comparable only within one vocabulary scoping.
    """
    from isalhg.iso_backends.pynauty_levi import PynautyLeviBackend

    return PynautyLeviBackend().fingerprint(record.to_hypergraph())


@dataclass(frozen=True)
class KBCollection:
    """A named set of knowledge bases sharing one vocabulary scoping.

    Parameters
    ----------
    name : str
        Collection identifier; also the frozen directory name.
    records : tuple[KBRecord, ...]
        Members, in a deterministic order that every downstream matrix uses.
    type_names : tuple[str, ...]
        Semantic name of type id ``i``.
    pred_names : tuple[str, ...]
        Semantic name of predicate id ``i``.
    role_names : tuple[str, ...]
        Semantic name of role id ``i``; empty when the collection has no roles.
    k_max : int
        Largest fact arity present.
    meta : Mapping[str, Any]
        Collection-level side information (derivation parameters, the envelope,
        ``consecutive_pairs`` and ``runs`` for the time series, the census).

    Raises
    ------
    KBCollectionError
        On duplicate ``kb_id``, or a record outside the declared vocabularies.
    """

    name: str
    records: tuple[KBRecord, ...]
    type_names: tuple[str, ...]
    pred_names: tuple[str, ...]
    role_names: tuple[str, ...] = ()
    k_max: int = DEFAULT_ENVELOPE.k_max
    meta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        set_ = object.__setattr__
        set_(self, "type_names", tuple(str(t) for t in self.type_names))
        set_(self, "pred_names", tuple(str(p) for p in self.pred_names))
        set_(self, "role_names", tuple(str(r) for r in self.role_names))
        set_(self, "meta", _freeze_json(dict(self.meta)))
        n_types = len(self.type_names)
        n_preds = len(self.pred_names)
        stamped: list[KBRecord] = []
        seen: set[str] = set()
        for record in self.records:
            if record.kb_id in seen:
                raise KBCollectionError(f"{self.name}: duplicate kb_id {record.kb_id!r}")
            seen.add(record.kb_id)
            if record.types and max(record.types) >= n_types:
                raise KBCollectionError(
                    f"{self.name}/{record.kb_id}: type id {max(record.types)} outside "
                    f"[0, {n_types})"
                )
            preds = [pred for pred, _ in record.facts]
            if preds and max(preds) >= n_preds:
                raise KBCollectionError(
                    f"{self.name}/{record.kb_id}: predicate id {max(preds)} outside [0, {n_preds})"
                )
            if record.roles is not None and self.role_names:
                flat = [r for row in record.roles for r in row]
                if flat and max(flat) >= len(self.role_names):
                    raise KBCollectionError(
                        f"{self.name}/{record.kb_id}: role id {max(flat)} outside "
                        f"[0, {len(self.role_names)})"
                    )
            meta = dict(record.meta)
            meta[META_N_TYPES] = n_types
            meta[META_N_PREDS] = n_preds
            stamped.append(replace(record, meta=meta))
        set_(self, "records", tuple(stamped))

    def __len__(self) -> int:
        return len(self.records)

    def __iter__(self) -> Iterator[KBRecord]:
        return iter(self.records)

    @property
    def n_types(self) -> int:
        """Type-vocabulary size."""
        return len(self.type_names)

    @property
    def n_preds(self) -> int:
        """Predicate-vocabulary size."""
        return len(self.pred_names)

    @property
    def has_roles(self) -> bool:
        """True iff every record carries a roles field."""
        return bool(self.records) and all(r.roles is not None for r in self.records)

    def index(self) -> dict[str, int]:
        """Map ``kb_id`` to member position."""
        return {record.kb_id: i for i, record in enumerate(self.records)}

    def vocab_json(self) -> dict[str, Any]:
        """The ``vocab.json`` payload."""
        return {
            "name": self.name,
            "type_names": list(self.type_names),
            "pred_names": list(self.pred_names),
            "role_names": list(self.role_names),
            "k_max": self.k_max,
            "meta": dict(self.meta),
            "n_records": len(self.records),
        }

    def series_census(self) -> dict[str, Any]:
        """Variant-series census: pairs, their ``delta`` profile, regimes and runs.

        Empty for a collection that is not a time series. The RQ3 cell sizes are
        read from here, so it is reported explicitly rather than left implicit in
        ``meta``.

        Returns
        -------
        dict
            ``n_consecutive_pairs``, ``delta_histogram`` over
            ``0 / 1 / 2 / 3-5 / >5``, ``n_pairs_constant_preserving`` and
            ``n_pairs_constant_changing``, ``n_classes_run_ge3`` /
            ``n_classes_run_ge5`` / ``max_run``, ``n_runs_ge3`` /
            ``n_runs_ge5``, and ``n_classes_with_any_member``.
        """
        pairs = self.meta.get("consecutive_pairs")
        if not pairs:
            return {}
        run_lengths = [
            len(run.get("kb_ids", ())) for run in (self.meta.get("consecutive_runs") or [])
        ]
        return {
            "n_consecutive_pairs": self.meta.get("n_consecutive_pairs", len(pairs)),
            "delta_histogram": dict(self.meta.get("delta_histogram") or {}),
            "n_pairs_constant_preserving": self.meta.get("n_pairs_constant_preserving"),
            "n_pairs_constant_changing": self.meta.get("n_pairs_constant_changing"),
            "n_classes_run_ge3": self.meta.get("n_classes_run_ge3"),
            "n_classes_run_ge5": self.meta.get("n_classes_run_ge5"),
            "max_run": self.meta.get("max_run"),
            "n_runs_ge3": sum(1 for length in run_lengths if length >= 3),
            "n_runs_ge5": sum(1 for length in run_lengths if length >= 5),
            "n_classes_with_any_member": len(self.meta.get("runs") or {}),
        }

    def census(self) -> dict[str, Any]:
        """Structural census of the collection (sizes, arity, labels, roles, series)."""
        ns = sorted(r.n for r in self.records)
        ms = sorted(r.m for r in self.records)
        arities = sorted(r.max_arity for r in self.records)
        hist: dict[int, int] = {}
        for record in self.records:
            for arity, count in record.arity_histogram().items():
                hist[arity] = hist.get(arity, 0) + count
        n_edges = sum(hist.values())
        labels: dict[str, int] = {}
        for record in self.records:
            if record.label is not None:
                labels[record.label] = labels.get(record.label, 0) + 1
        return {
            "n_records": len(self.records),
            "series": self.series_census(),
            "n": _quantiles(ns),
            "m": _quantiles(ms),
            "max_arity": _quantiles(arities),
            "arity_histogram": {str(a): hist[a] for a in sorted(hist)},
            "n_facts_total": n_edges,
            "frac_facts_arity_ge3": (
                round(sum(c for a, c in hist.items() if a >= 3) / n_edges, 4) if n_edges else 0.0
            ),
            "n_records_with_arity_ge3": sum(1 for r in self.records if r.max_arity >= 3),
            "n_types": self.n_types,
            "n_preds": self.n_preds,
            "n_roles": len(self.role_names),
            "has_roles": self.has_roles,
            "n_labelled": sum(1 for r in self.records if r.label is not None),
            "label_counts": dict(sorted(labels.items(), key=lambda kv: (-kv[1], kv[0]))),
            "n_labels_ge20": sum(1 for c in labels.values() if c >= 20),
            "coverage_labels_ge20": (
                round(
                    sum(c for c in labels.values() if c >= 20) / len(self.records),
                    4,
                )
                if self.records
                else 0.0
            ),
        }


def _quantiles(xs: Sequence[int]) -> dict[str, float]:
    """Min / p25 / median / p75 / p90 / max / mean of a sorted-able sequence."""
    if not xs:
        return {}
    ordered = sorted(xs)

    def q(p: float) -> float:
        idx = min(len(ordered) - 1, max(0, int(round(p * (len(ordered) - 1)))))
        return float(ordered[idx])

    return {
        "min": float(ordered[0]),
        "p25": q(0.25),
        "median": q(0.50),
        "p75": q(0.75),
        "p90": q(0.90),
        "max": float(ordered[-1]),
        "mean": round(sum(ordered) / len(ordered), 3),
    }


def dumps_record(record: KBRecord) -> str:
    """Serialise one record to a single JSON line."""
    return json.dumps(record.to_json(), separators=(",", ":"), ensure_ascii=False)
