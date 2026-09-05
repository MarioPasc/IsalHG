"""NDC quarterly co-formulation knowledge bases (supplementary S2).

Source: the Cornell higher-order interaction collection (Benson, Abebe, Schaub,
Jadbabaie & Kleinberg, PNAS 2018), timestamped simplex lists
``<name>-{nverts,simplices,times,node-labels}.txt`` under
``arb_benson/temporal/``.

Derivation (S2, ported from
``scripts/diagnostics/d_art3_probes_2026-09-03/arb_temporal/arb_temporal_lib.py``
and ``f4_topology/{f4_corpora,followup_ndc_regime}.py``):

* the FDA National Drug Code directory read as a hypergraph -- a simplex is a
  marketed drug product, as the set of pharmacologic classes (or active
  substances) it contains, timestamped by first-marketing date;
* the knowledge base of node ``c`` in window ``t`` is the set of *distinct*
  co-formulation facts containing ``c`` marketed in ``t``; every fact contains
  ``c``, so every member is connected by construction;
* constants carry the FDA class *type* read off the name suffix (``[epc]``,
  ``[moa]``, ``[pe]``, else ``untyped``) for NDC-classes, and a single type for
  NDC-substances; the names themselves are identities and are never labels;
* one predicate;
* the encodable envelope ``m_min <= m <= m_max``, ``n <= n_max``,
  ``max arity <= k_max``;
* consecutive windows of the same node are *real variants*: because node
  identities persist, ``delta = |F_t triangle F_{t+1}|`` is exact ground truth
  that no isomorphism computation touches, and the pair is flagged
  *constant-preserving* when the two members span the same node set.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Sequence
from datetime import datetime, timedelta
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
from isalhg.datasets.kb.wd50k import data_root

logger = logging.getLogger(__name__)

TEMPORAL_SUBDIR = Path("arb_benson") / "temporal"

NODE_SETS: dict[str, str] = {"classes": "NDC-classes", "substances": "NDC-substances"}

WINDOW_STEPS_MS: dict[str, int] = {
    "day": 86_400_000,
    "week": 604_800_000,
    "month": 2_629_746_000,
    "quarter": 7_889_238_000,
    "year": 31_556_952_000,
}

CLASS_TYPE_SUFFIXES = ("[epc]", "[moa]", "[pe]")
CLASS_TYPE_NAMES = ("[epc]", "[moa]", "[pe]", "untyped")
CLASS_TYPE_ID = {name: i for i, name in enumerate(CLASS_TYPE_NAMES)}
UNTYPED_ID = CLASS_TYPE_ID["untyped"]

PREDICATE_NAME = "co_formulation"

CITATION = (
    "Benson, Abebe, Schaub, Jadbabaie & Kleinberg. Simplicial closure and "
    "higher-order link prediction. PNAS 115(48), 2018. "
    "DOI 10.1073/pnas.1800683115"
)

# ARB timestamps of this corpus are milliseconds since the start of year 0 in
# the proleptic Gregorian calendar; year 0 has 366 days, so day 366 is 0001-01-01.
_YEAR_ZERO_OFFSET_DAYS = 366


def _read_ints(path: Path) -> list[int]:
    if not path.is_file():
        raise KBCorpusError(f"missing ARB file {path}")
    return [int(tok) for tok in path.read_text(encoding="utf-8").split()]


def _read_node_names(path: Path) -> dict[int, str]:
    if not path.is_file():
        return {}
    names: dict[int, str] = {}
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.rstrip("\n")
            if not line:
                continue
            parts = line.split(None, 1)
            try:
                names[int(parts[0])] = parts[1] if len(parts) > 1 else ""
            except ValueError:
                continue
    return names


def quarter_label(ms_since_year_zero: int) -> str:
    """Calendar label ``<year>Q<1-4>`` of a millisecond timestamp.

    Parameters
    ----------
    ms_since_year_zero : int
        ARB timestamp: milliseconds since 0000-01-01 (proleptic Gregorian).

    Returns
    -------
    str
        For example ``"2015Q3"``. Out-of-range timestamps fall back to
        ``"?"``.
    """
    try:
        moment = datetime(1, 1, 1) + timedelta(
            milliseconds=ms_since_year_zero, days=-_YEAR_ZERO_OFFSET_DAYS
        )
    except (OverflowError, ValueError):
        return "?"
    return f"{moment.year}Q{(moment.month - 1) // 3 + 1}"


def _class_type_id(name: str) -> int:
    stripped = name.rstrip()
    for suffix in CLASS_TYPE_SUFFIXES:
        if stripped.endswith(suffix):
            return CLASS_TYPE_ID[suffix]
    return UNTYPED_ID


def _canonical_simplices(
    nverts: Sequence[int], flat: Sequence[int]
) -> tuple[list[tuple[int, ...]], list[int]]:
    """Deduplicate the simplex list; return (canonical members, per-simplex id)."""
    lookup: dict[tuple[int, ...], int] = {}
    canonical: list[tuple[int, ...]] = []
    per_simplex: list[int] = []
    cursor = 0
    for size in nverts:
        members = tuple(sorted(set(flat[cursor : cursor + size])))
        cursor += size
        sid = lookup.get(members)
        if sid is None:
            sid = len(canonical)
            lookup[members] = sid
            canonical.append(members)
        per_simplex.append(sid)
    return canonical, per_simplex


def _group_windows(
    canonical: Sequence[tuple[int, ...]],
    per_simplex: Sequence[int],
    times: Sequence[int],
    step: int,
) -> dict[tuple[int, int], frozenset[int]]:
    """Map ``(node, window)`` to the distinct canonical simplex ids around it."""
    t_min = min(times)
    groups: dict[tuple[int, int], set[int]] = defaultdict(set)
    for index, sid in enumerate(per_simplex):
        window = (times[index] - t_min) // step
        for node in canonical[sid]:
            groups[(node, window)].add(sid)
    return {key: frozenset(value) for key, value in groups.items()}


def load_ndc(
    nodes: str = "classes",
    *,
    window: str = "quarter",
    envelope: bool | Envelope = True,
    root: Path | str | None = None,
    name: str | None = None,
) -> KBCollection:
    """Derive the quarterly co-formulation knowledge bases of one NDC corpus.

    Parameters
    ----------
    nodes : {"classes", "substances"}, optional
        Which node set the directory is read with. Default ``"classes"``.
    window : str, optional
        Time-window name; one of :data:`WINDOW_STEPS_MS`. Default
        ``"quarter"``.
    envelope : bool or Envelope, optional
        ``True`` (default) applies :data:`DEFAULT_ENVELOPE`.
    root : Path or str or None, optional
        Data root override.
    name : str or None, optional
        Collection name; defaults to ``ndc_classes`` / ``ndc_substances``.

    Returns
    -------
    KBCollection
        Members ordered by ``(node, window)``. ``meta`` carries
        ``consecutive_pairs`` (with ``delta`` and ``constant_preserving``),
        ``runs`` (per node, its kb ids ordered by window),
        ``consecutive_runs`` (each maximal run of adjacent windows) and the
        node-name table.

    Raises
    ------
    KBCorpusError
        If the node set or window name is unknown, or a source file is missing.
    """
    if nodes not in NODE_SETS:
        raise KBCorpusError(f"unknown NDC node set {nodes!r}; expected one of {sorted(NODE_SETS)}")
    if window not in WINDOW_STEPS_MS:
        raise KBCorpusError(f"unknown window {window!r}; expected one of {sorted(WINDOW_STEPS_MS)}")
    win = DEFAULT_ENVELOPE if envelope is True else (None if envelope is False else envelope)
    dataset = NODE_SETS[nodes]
    base = data_root(root) / TEMPORAL_SUBDIR / dataset / dataset
    step = WINDOW_STEPS_MS[window]

    nverts = _read_ints(Path(str(base) + "-nverts.txt"))
    flat = _read_ints(Path(str(base) + "-simplices.txt"))
    times = _read_ints(Path(str(base) + "-times.txt"))
    if len(nverts) != len(times):
        raise KBCorpusError(f"{dataset}: {len(nverts)} simplices but {len(times)} timestamps")
    if sum(nverts) != len(flat):
        raise KBCorpusError(f"{dataset}: nverts sums to {sum(nverts)}, member file has {len(flat)}")
    node_names = _read_node_names(Path(str(base) + "-node-labels.txt"))

    canonical, per_simplex = _canonical_simplices(nverts, flat)
    groups = _group_windows(canonical, per_simplex, times, step)
    t_min = min(times)

    typed = nodes == "classes"
    type_names = CLASS_TYPE_NAMES if typed else ("untyped",)

    def type_of(node: int) -> int:
        if not typed:
            return 0
        return _class_type_id(node_names.get(node, ""))

    encodable: dict[tuple[int, int], frozenset[int]] = {}
    n_below_m_min = 0
    n_out_of_window = 0
    n_over_arity = 0
    n_arity1_facts = 0
    n_encodable_with_singletons = 0
    for key in sorted(groups):
        raw = groups[key]
        # A singleton product is not a ground fact: the alphabet's F token has
        # arity >= 2 (DESIGN G2), so it cannot be encoded and is not counted.
        sids = frozenset(sid for sid in raw if len(canonical[sid]) >= 2)
        n_arity1_facts += len(raw) - len(sids)
        if win is not None:
            raw_members = {v for sid in raw for v in canonical[sid]}
            raw_max_arity = max(len(canonical[sid]) for sid in raw)
            if win.admits(len(raw_members), len(raw), raw_max_arity):
                n_encodable_with_singletons += 1
        if not sids:
            continue
        members = {v for sid in sids for v in canonical[sid]}
        max_arity = max(len(canonical[sid]) for sid in sids)
        if win is not None:
            if len(sids) < win.m_min:
                n_below_m_min += 1
                continue
            if len(members) > win.n_max or len(sids) > win.m_max:
                n_out_of_window += 1
                continue
            if max_arity > win.k_max:
                n_over_arity += 1
                continue
        encodable[key] = sids

    records: list[KBRecord] = []
    constants_of: dict[tuple[int, int], frozenset[int]] = {}
    id_of: dict[tuple[int, int], str] = {}
    for node, win_index in sorted(encodable):
        sids = encodable[(node, win_index)]
        constants = sorted({v for sid in sids for v in canonical[sid]})
        remap = {v: i for i, v in enumerate(constants)}
        facts: list[Fact] = [
            (0, tuple(sorted(remap[v] for v in canonical[sid]))) for sid in sorted(sids)
        ]
        kb_id = f"{node}@{win_index}"
        window_start = t_min + win_index * step
        record = make_record(
            kb_id,
            len(constants),
            [type_of(v) for v in constants],
            facts,
            constant_ids=[str(v) for v in constants],
            meta={
                "class_id": node,
                "class_name": node_names.get(node, ""),
                "window": win_index,
                "quarter": quarter_label(window_start),
                "window_start_ms": window_start,
                "source_id": kb_id,
                "simplex_ids": sorted(sids),
            },
            require_connected=True,
        )
        if record is None:
            logger.debug("%s: (%s, %s) rejected as disconnected", dataset, node, win_index)
            continue
        records.append(record)
        constants_of[(node, win_index)] = frozenset(constants)
        id_of[(node, win_index)] = kb_id

    pairs: list[dict[str, Any]] = []
    n_preserving = 0
    for node, win_index in sorted(id_of):
        nxt = (node, win_index + 1)
        if nxt not in id_of:
            continue
        a, b = encodable[(node, win_index)], encodable[nxt]
        preserved = constants_of[(node, win_index)] == constants_of[nxt]
        n_preserving += int(preserved)
        pairs.append(
            {
                "a": id_of[(node, win_index)],
                "b": id_of[nxt],
                "delta": len(a ^ b),
                "constant_preserving": preserved,
                "class_id": node,
                "window": win_index,
                "n_constants_moved": len(constants_of[(node, win_index)] ^ constants_of[nxt]),
            }
        )

    by_node: dict[int, list[int]] = defaultdict(list)
    for node, win_index in sorted(id_of):
        by_node[node].append(win_index)
    runs = {
        str(node): [id_of[(node, w)] for w in windows] for node, windows in sorted(by_node.items())
    }
    consecutive_runs: list[dict[str, Any]] = []
    for node, windows in sorted(by_node.items()):
        current = [windows[0]]
        for previous, this in zip(windows[:-1], windows[1:], strict=True):
            if this == previous + 1:
                current.append(this)
            else:
                consecutive_runs.append(
                    {"class_id": node, "kb_ids": [id_of[(node, w)] for w in current]}
                )
                current = [this]
        consecutive_runs.append({"class_id": node, "kb_ids": [id_of[(node, w)] for w in current]})
    lengths_by_node: dict[int, int] = defaultdict(int)
    for run in consecutive_runs:
        lengths_by_node[run["class_id"]] = max(lengths_by_node[run["class_id"]], len(run["kb_ids"]))

    delta_histogram = {"0": 0, "1": 0, "2": 0, "3-5": 0, ">5": 0}
    for pair in pairs:
        delta = pair["delta"]
        if delta <= 2:
            delta_histogram[str(delta)] += 1
        elif delta <= 5:
            delta_histogram["3-5"] += 1
        else:
            delta_histogram[">5"] += 1

    meta: dict[str, Any] = {
        "source": dataset,
        "citation": CITATION,
        "data_root": str(data_root(root)),
        "window": window,
        "window_step_ms": step,
        "t_min_ms": t_min,
        "envelope": None if win is None else win.as_dict(),
        "derivation": (
            "KB of node c in window t = the distinct co-formulation facts containing c "
            "marketed in t; identities are evaluation-only"
        ),
        "n_simplices": len(nverts),
        "n_distinct_simplices": len(canonical),
        "n_groups_all": len(groups),
        "n_dropped_below_m_min": n_below_m_min,
        "n_dropped_out_of_window": n_out_of_window,
        "n_dropped_over_arity_cap": n_over_arity,
        "n_arity1_facts_dropped": n_arity1_facts,
        "n_encodable_counting_singleton_products": n_encodable_with_singletons,
        "consecutive_pairs": pairs,
        "n_consecutive_pairs": len(pairs),
        "n_pairs_constant_preserving": n_preserving,
        "n_pairs_constant_changing": len(pairs) - n_preserving,
        "delta_histogram": delta_histogram,
        "runs": runs,
        "consecutive_runs": consecutive_runs,
        "n_classes_run_ge3": sum(1 for v in lengths_by_node.values() if v >= 3),
        "n_classes_run_ge5": sum(1 for v in lengths_by_node.values() if v >= 5),
        "max_run": max(lengths_by_node.values(), default=0),
        "node_names": {str(k): v for k, v in sorted(node_names.items())},
    }
    return KBCollection(
        name=name if name is not None else f"ndc_{nodes}",
        records=tuple(records),
        type_names=type_names,
        pred_names=(PREDICATE_NAME,),
        role_names=(),
        k_max=DEFAULT_ENVELOPE.k_max if win is None else win.k_max,
        meta=meta,
    )
