"""WD50K entity knowledge bases (supplementary S1).

Source: WD50K and its qualifier-enriched subsets, released with StarE (Galkin,
Trivedi, Maheshwari, Usbeck & Lehmann, EMNLP 2020,
DOI 10.18653/v1/2020.emnlp-main.596). Statement files ``train/valid/test.txt``
carry one statement per line, ``s, r, o, (q_r, q_v)*``.

Derivation (S1, ported from
``scripts/diagnostics/d_art3_probes_2026-09-03/hyperrel/probe_hyperrel.py``):

* one knowledge base per subject entity ``e`` -- the statements with ``e`` as
  subject;
* one hyperedge per statement over ``{subject, object, qualifier values}``,
  labelled by the main relation; qualifier relations are dropped;
* statements collapsing to the same ``(relation, member set)`` are one fact;
* entities with fewer than three statements are dropped;
* the envelope ``m_min <= m <= m_max``, ``n <= n_max``, ``max arity <= k_max``;
* constants are untyped (a single type) and anonymized -- the Wikidata
  identifiers survive only in ``constant_ids``, which is evaluation-only;
* roles ``S`` / ``O`` / ``Q`` per operand; a constant occurring in two roles of
  one statement takes the smaller role id (``S < O < Q``);
* the class label is the entity's most frequent P31 type over the loaded
  population, ties broken by identifier order.
"""

from __future__ import annotations

import logging
import os
from collections import Counter, defaultdict
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from isalhg.datasets.kb.base import (
    DEFAULT_ENVELOPE,
    Envelope,
    Fact,
    KBCollection,
    KBCorpusError,
    KBRecord,
    make_record,
)

logger = logging.getLogger(__name__)

DEFAULT_DATA_ROOT = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/data")
DATA_ROOT_ENV = "ISALHG_DATA_ROOT"

SUBSET_DIRS: dict[str, str] = {
    "33": "wd50k_33",
    "66": "wd50k_66",
    "100": "wd50k_100",
    "all": "wd50k",
}
SPLIT_FILES = ("train.txt", "valid.txt", "test.txt")
MIN_STATEMENTS = 3

ROLE_NAMES = ("S", "O", "Q")
ROLE_SUBJECT, ROLE_OBJECT, ROLE_QUALIFIER = 0, 1, 2
UNTYPED = "untyped"

DEFAULT_TYPES_TSV = Path("wd50k") / "types" / "p31_types.tsv"

CITATION = (
    "Galkin, Trivedi, Maheshwari, Usbeck & Lehmann. Message Passing for "
    "Hyper-Relational Knowledge Graphs. EMNLP 2020. "
    "DOI 10.18653/v1/2020.emnlp-main.596"
)


def data_root(root: Path | str | None = None) -> Path:
    """Resolve the read-only data root.

    Parameters
    ----------
    root : Path or str or None, optional
        Explicit override. When ``None`` the ``ISALHG_DATA_ROOT`` environment
        variable is used, else the group's default drive path.

    Returns
    -------
    Path
        The data root; existence is not checked here.
    """
    if root is not None:
        return Path(root)
    env = os.environ.get(DATA_ROOT_ENV)
    return Path(env) if env else DEFAULT_DATA_ROOT


@dataclass(frozen=True)
class Statement:
    """One hyper-relational statement."""

    subject: str
    relation: str
    obj: str
    qual_values: tuple[str, ...]

    @property
    def vertices(self) -> frozenset[str]:
        """The constants the statement speaks about."""
        return frozenset((self.subject, self.obj, *self.qual_values))

    def role_of(self, constant: str) -> int:
        """Smallest role the constant occupies in this statement."""
        if constant == self.subject:
            return ROLE_SUBJECT
        if constant == self.obj:
            return ROLE_OBJECT
        return ROLE_QUALIFIER


def parse_statements(path: Path) -> Iterator[Statement]:
    """Parse one StarE ``data/clean`` statement file (``s,r,o[,qr,qv]*``)."""
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            if len(parts) < 3:
                continue
            rest = parts[3:]
            yield Statement(
                subject=parts[0],
                relation=parts[1],
                obj=parts[2],
                qual_values=tuple(rest[i] for i in range(1, len(rest), 2)),
            )


def load_statements(subset: str, root: Path | str | None = None) -> list[Statement]:
    """Load every split of one WD50K subset.

    Raises
    ------
    KBCorpusError
        If the subset name is unknown or a split file is missing.
    """
    if subset not in SUBSET_DIRS:
        raise KBCorpusError(f"unknown WD50K subset {subset!r}; expected one of {SUBSET_DIRS}")
    base = data_root(root) / SUBSET_DIRS[subset]
    out: list[Statement] = []
    for name in SPLIT_FILES:
        path = base / name
        if not path.is_file():
            raise KBCorpusError(f"missing WD50K split file {path}")
        out.extend(parse_statements(path))
    return out


def read_p31_types(path: Path) -> dict[str, list[str]]:
    """Read the ``entity<TAB>Q1,Q2,...`` P31 table.

    Raises
    ------
    KBCorpusError
        If the file is absent.
    """
    if not path.is_file():
        raise KBCorpusError(
            f"missing the Wikidata P31 type table {path}; it carries the RQ5 class labels"
        )
    types: dict[str, list[str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or "\t" not in line:
            continue
        qid, _, values = line.partition("\t")
        types[qid] = [v for v in values.split(",") if v]
    return types


def _qid_order(qid: str) -> tuple[int, int, str]:
    """Identifier order: numeric Q-ids first, by number; anything else by string."""
    if qid.startswith("Q") and qid[1:].isdigit():
        return (0, int(qid[1:]), "")
    return (1, 0, qid)


def assign_labels(
    entities: Sequence[str], types: dict[str, list[str]]
) -> tuple[dict[str, str], Counter[str]]:
    """One class label per entity: most frequent P31 over the population.

    Parameters
    ----------
    entities : Sequence[str]
        The population whose type frequencies define "most frequent".
    types : dict[str, list[str]]
        Entity -> its P31 values.

    Returns
    -------
    labels : dict[str, str]
        Entity -> chosen type, for entities carrying at least one P31 value.
    population : Counter[str]
        Type -> number of population entities carrying it.
    """
    population: Counter[str] = Counter(t for e in entities for t in types.get(e, ()))
    labels: dict[str, str] = {}
    for entity in entities:
        values = types.get(entity) or []
        if values:
            labels[entity] = min(values, key=lambda t: (-population[t], _qid_order(t)))
    return labels, population


def _build_record(
    entity: str,
    statements: Sequence[Statement],
    relation_ids: dict[str, int],
    *,
    roles: bool,
    label: str | None,
) -> KBRecord | None:
    """Assemble the star knowledge base of one subject entity."""
    constants = sorted({v for s in statements if len(s.vertices) >= 2 for v in s.vertices})
    remap = {v: i for i, v in enumerate(constants)}
    facts: list[Fact] = []
    role_rows: list[tuple[int, ...]] = []
    seen: set[Fact] = set()
    for statement in statements:
        if len(statement.vertices) < 2:
            continue
        members = tuple(sorted(remap[v] for v in statement.vertices))
        fact = (relation_ids[statement.relation], members)
        if fact in seen:
            continue
        seen.add(fact)
        facts.append(fact)
        if roles:
            role_rows.append(tuple(statement.role_of(constants[v]) for v in members))
    return make_record(
        entity,
        len(constants),
        [0] * len(constants),
        facts,
        roles=role_rows if roles else None,
        constant_ids=constants,
        label=label,
        meta={"source_id": entity, "n_statements": len(statements)},
        require_connected=False,
    )


def load_wd50k(
    subset: str = "66",
    *,
    envelope: bool | Envelope = True,
    roles: bool = True,
    types_tsv: Path | str | None = None,
    root: Path | str | None = None,
    name: str | None = None,
) -> KBCollection:
    """Derive the entity knowledge bases of one WD50K subset.

    Parameters
    ----------
    subset : {"33", "66", "100", "all"}, optional
        Which qualifier-enriched subset to read. Default ``"66"``.
    envelope : bool or Envelope, optional
        ``True`` (default) applies :data:`DEFAULT_ENVELOPE`; ``False`` keeps
        every entity with at least ``MIN_STATEMENTS`` statements; an
        :class:`Envelope` applies that window.
    roles : bool, optional
        Carry the S / O / Q role of every operand. Default ``True``.
    types_tsv : Path or str or None, optional
        The P31 table. Defaults to ``<data root>/wd50k/types/p31_types.tsv``.
    root : Path or str or None, optional
        Data root override.
    name : str or None, optional
        Collection name; defaults to ``wd50k<subset>`` (``wd50k66_full``
        without the envelope).

    Returns
    -------
    KBCollection
        Members in ascending entity-identifier order, one type
        (``"untyped"``), one predicate per main relation, roles ``S/O/Q``.

    Raises
    ------
    KBCorpusError
        If the subset, a split file or the P31 table is missing.
    """
    window = DEFAULT_ENVELOPE if envelope is True else (None if envelope is False else envelope)
    statements = load_statements(subset, root)
    relations = sorted({s.relation for s in statements})
    relation_ids = {r: i for i, r in enumerate(relations)}

    by_subject: dict[str, list[Statement]] = defaultdict(list)
    for statement in statements:
        by_subject[statement.subject].append(statement)

    kept: list[tuple[str, list[Statement]]] = []
    n_entities_all = 0
    n_over_arity = 0
    n_out_of_window = 0
    n_arity1_statements = 0
    n_below_m_min = 0
    for entity in sorted(by_subject):
        group = by_subject[entity]
        if len(group) < MIN_STATEMENTS:
            continue
        n_entities_all += 1
        relational = [s for s in group if len(s.vertices) >= 2]
        n_arity1_statements += len(group) - len(relational)
        if not relational:
            continue
        if window is None:
            kept.append((entity, relational))
            continue
        constants = {v for s in relational for v in s.vertices}
        facts = {(s.relation, s.vertices) for s in relational}
        max_arity = max(len(members) for _, members in facts)
        if len(facts) < window.m_min:
            n_below_m_min += 1
            continue
        if len(constants) > window.n_max or len(facts) > window.m_max:
            n_out_of_window += 1
            continue
        if max_arity > window.k_max:
            n_over_arity += 1
            continue
        kept.append((entity, relational))

    tsv = Path(types_tsv) if types_tsv is not None else data_root(root) / DEFAULT_TYPES_TSV
    types = read_p31_types(tsv)
    entities = [entity for entity, _ in kept]
    labels, population = assign_labels(entities, types)

    records: list[KBRecord] = []
    for entity, group in kept:
        record = _build_record(entity, group, relation_ids, roles=roles, label=labels.get(entity))
        if record is None:
            logger.warning("wd50k(%s): entity %s produced no facts", subset, entity)
            continue
        records.append(record)

    collection_name = (
        name
        if name is not None
        else (f"wd50k{subset}" if window is not None else f"wd50k{subset}_full")
    )
    meta: dict[str, Any] = {
        "source": f"WD50K({subset})",
        "citation": CITATION,
        "data_root": str(data_root(root)),
        "subset_dir": SUBSET_DIRS[subset],
        "types_tsv": str(tsv),
        "min_statements": MIN_STATEMENTS,
        "envelope": None if window is None else window.as_dict(),
        "roles": roles,
        "derivation": (
            "one KB per subject entity; hyperedge = {subject, object, qualifier values} "
            "labelled by the main relation; qualifier relations dropped"
        ),
        "n_statements": len(statements),
        "n_main_relations": len(relations),
        "n_entities_ge_min_statements": n_entities_all,
        "n_dropped_out_of_window": n_out_of_window,
        "n_dropped_below_m_min": n_below_m_min,
        "n_dropped_over_arity_cap": n_over_arity,
        "n_arity1_statements_dropped": n_arity1_statements,
        "n_labelled": len(labels),
        "label_population_top": [{"type": t, "count": c} for t, c in population.most_common(20)],
    }
    return KBCollection(
        name=collection_name,
        records=tuple(records),
        type_names=(UNTYPED,),
        pred_names=tuple(relations),
        role_names=ROLE_NAMES if roles else (),
        k_max=DEFAULT_ENVELOPE.k_max if window is None else window.k_max,
        meta=meta,
    )
