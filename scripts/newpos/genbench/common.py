"""Shared definitions of the generation benchmark on usable samples.

Everything the sampler, the evaluator, the analysis and the figure agree on lives
here: the frozen JSONL draw format, the structure predicates (connected, star,
shared constants), the largest-connected-component repair, the isomorphism key,
the compact per-unit sample set that carries the five RQ6 profiles, and the
distances between profiles.

A *usable* sample is a decoded knowledge base that is connected and has at least
one fact -- the paper's domain. ``connected`` follows RQ6 exactly
(``SparseHypergraph.is_connected`` semantics), so counts reproduce RQ6's tables.
"""

from __future__ import annotations

import gzip
import json
import logging
import math
import re
from collections import Counter
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import IO, TYPE_CHECKING, Any, TypeAlias

import numpy as np

if TYPE_CHECKING:
    from isalhg.core.sparse_hypergraph import SparseHypergraph

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[3]
CORPUS_ROOT = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE")
RESULTS_ROOT = Path(
    "/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/NEWPOS_2026-10-13/genbench_ngram"
)
RQ6_ROWS = Path(
    "/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE_isal_consensus/"
    "RQ6_generation/generation/rows_samples.csv"
)

COLLECTIONS: tuple[str, ...] = ("wd50k66", "ndc_classes")
ARM_OURS = "ow_ngram"
ARM_FACT = "fact_ngram"
ARM_INCIDENCE = "incidence_ngram"
ARM_LCC = "fact_ngram_lcc"
NGRAM_ARMS: tuple[str, ...] = (ARM_OURS, ARM_FACT, ARM_INCIDENCE)
BASELINES: tuple[str, ...] = (ARM_FACT, ARM_LCC, ARM_INCIDENCE)
PROFILE_KEYS: tuple[str, ...] = ("n", "m", "arity", "pred", "type")

#: Below this many usable samples no fidelity statistic is computed (reviewer
#: amendment 2): a plug-in JSD from a few samples is biased upward.
MIN_USABLE = 100
#: A (collection, baseline) cell is tested only if this many seeds clear MIN_USABLE.
MIN_VALID_SEEDS = 10
N_MATCH_REPEATS = 20
N_SAMPLES = 10_000
MAX_LEN = 200
N_UNCOMPRESSED_SEEDS = 3

Fact: TypeAlias = tuple[int, tuple[int, ...]]
KB: TypeAlias = tuple[int, tuple[int, ...], tuple[Fact, ...]]
IsoKey: TypeAlias = tuple[Any, ...]

_FILE_RE = re.compile(r"^(?P<collection>.+?)__(?P<generator>.+?)__s(?P<seed>\d+)\.jsonl(?:\.gz)?$")


class GenBenchError(Exception):
    """Root of the failures of the generation benchmark scripts."""


class SampleFileError(GenBenchError):
    """A sample file does not follow the frozen JSONL contract."""


# ---------------------------------------------------------------------------
# The frozen sample format
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Draw:
    """One parsed line of a frozen-format sample file.

    Attributes
    ----------
    draw : int
        Index of the draw within its unit.
    status : str
        ``"decoded"`` or ``"rejected"``.
    reason : str or None
        Rejection cause when ``status`` is ``"rejected"``.
    kb : tuple or None
        ``(n, types, facts)`` with constants numbered ``0..n-1`` and every fact
        normalised to ``(predicate, ascending distinct members)``; ``None`` when
        rejected.
    connected_flag : bool or None
        The generator's own connectivity flag, kept only to audit it.
    tokens : tuple[str, ...]
        The sampled token sequence, kept for provenance.
    root_type : int or None
        Root type supplied to the decoder, when the alphabet needs one.
    """

    draw: int
    status: str
    reason: str | None
    kb: KB | None
    connected_flag: bool | None
    tokens: tuple[str, ...] = ()
    root_type: int | None = None


@dataclass(frozen=True)
class UnitFile:
    """A sample file located by its ``<collection>__<generator>__s<seed>`` name."""

    collection: str
    generator: str
    seed: int
    path: Path


def normalize_facts(raw: Iterable[Sequence[Any]]) -> tuple[Fact, ...]:
    """Normalise facts to ``(pred, ascending distinct members)``, dropping repeats.

    Parameters
    ----------
    raw : Iterable[Sequence]
        Facts as ``[pred, [arg, ...]]``.

    Returns
    -------
    tuple[Fact, ...]
        First occurrence order preserved; duplicate ``(pred, member set)``
        pairs collapse as in ``SparseHypergraph``.
    """
    seen: set[Fact] = set()
    out: list[Fact] = []
    for entry in raw:
        fact = (int(entry[0]), tuple(sorted({int(v) for v in entry[1]})))
        if fact not in seen:
            seen.add(fact)
            out.append(fact)
    return tuple(out)


def parse_draw(line: str) -> Draw:
    """Parse one JSONL line of the frozen format.

    Parameters
    ----------
    line : str
        A JSON object with the contract's keys.

    Returns
    -------
    Draw
        The parsed draw.

    Raises
    ------
    SampleFileError
        If the line is not JSON, lacks a required key, or has an unknown status.
    """
    try:
        obj = json.loads(line)
        status = obj["status"]
        draw = int(obj["draw"])
    except (ValueError, KeyError, TypeError) as exc:
        raise SampleFileError(f"unparseable draw line: {line[:120]!r}") from exc
    if status not in {"decoded", "rejected"}:
        raise SampleFileError(f"unknown status {status!r}")
    flag = None if obj.get("connected") is None else bool(obj["connected"])
    tokens = tuple(str(t) for t in obj.get("tokens") or ())
    root = obj.get("root_type")
    root_type = None if root is None else int(root)
    if status == "rejected":
        return Draw(draw, status, obj.get("reason"), None, flag, tokens, root_type)
    try:
        n = int(obj["n"])
        types = tuple(int(t) for t in obj["types"])
        facts = normalize_facts(obj["facts"])
    except (KeyError, TypeError, ValueError) as exc:
        raise SampleFileError(f"decoded draw {draw} lacks n/types/facts") from exc
    if len(types) != n:
        raise SampleFileError(f"decoded draw {draw}: {len(types)} types for n={n}")
    for _, members in facts:
        if not members or members[0] < 0 or members[-1] >= n:
            raise SampleFileError(f"decoded draw {draw}: fact is empty or leaves [0,{n})")
    return Draw(draw, status, obj.get("reason"), (n, types, facts), flag, tokens, root_type)


def _open_text(path: Path, mode: str) -> IO[str]:
    if path.suffix == ".gz":
        return gzip.open(path, mode + "t", encoding="utf-8")
    return open(path, mode, encoding="utf-8")


def read_draws(path: Path) -> Iterator[Draw]:
    """Yield the draws of one sample file (plain or gzip)."""
    with _open_text(path, "r") as handle:
        for line in handle:
            if line.strip():
                yield parse_draw(line)


def scan_directory(
    directory: Path, collection: str, generators: Sequence[str] | None = None
) -> list[UnitFile]:
    """Locate the sample files of one collection in ``directory``.

    Parameters
    ----------
    directory : Path
        Directory holding ``<collection>__<generator>__s<seed>.jsonl[.gz]``.
    collection : str
        Collection name to keep.
    generators : Sequence[str] or None, optional
        Keep only these generator names.

    Returns
    -------
    list[UnitFile]
        Sorted by ``(generator, seed)``. A plain and a gzip file of the same
        unit is an error.

    Raises
    ------
    SampleFileError
        If a unit is present twice.
    """
    found: dict[tuple[str, int], UnitFile] = {}
    for path in sorted(directory.iterdir()):
        match = _FILE_RE.match(path.name)
        if match is None or match["collection"] != collection:
            continue
        generator, seed = match["generator"], int(match["seed"])
        if generators is not None and generator not in generators:
            continue
        key = (generator, seed)
        if key in found:
            raise SampleFileError(f"{collection}/{generator}/s{seed} present twice")
        found[key] = UnitFile(collection, generator, seed, path)
    return [found[key] for key in sorted(found)]


def draw_line(
    *,
    collection: str,
    generator: str,
    seed: int,
    draw: int,
    tokens: Sequence[str],
    root_type: int | None,
    status: str,
    reason: str | None,
    kb: KB | None,
    connected: bool | None,
) -> str:
    """Serialise one draw to a frozen-format JSON line (no trailing newline)."""
    record: dict[str, Any] = {
        "collection": collection,
        "generator": generator,
        "seed": seed,
        "draw": draw,
        "tokens": list(tokens),
        "root_type": root_type,
        "status": status,
        "reason": reason,
        "n": None if kb is None else kb[0],
        "types": None if kb is None else list(kb[1]),
        "facts": None if kb is None else [[p, list(members)] for p, members in kb[2]],
        "connected": connected,
    }
    return json.dumps(record, separators=(",", ":"))


# ---------------------------------------------------------------------------
# Structure predicates
# ---------------------------------------------------------------------------


def _find(parent: list[int], v: int) -> int:
    while parent[v] != v:
        parent[v] = parent[parent[v]]
        v = parent[v]
    return v


def component_labels(n: int, facts: Sequence[Fact]) -> list[int]:
    """Connected-component representative of every constant (primal graph).

    Parameters
    ----------
    n : int
        Number of constants.
    facts : Sequence[Fact]
        The facts; a fact connects all of its members.

    Returns
    -------
    list[int]
        ``rep[v]`` is a canonical representative; constants sharing a value are
        connected, and an isolated constant is its own component.
    """
    parent = list(range(n))
    for _, members in facts:
        root = _find(parent, members[0])
        for v in members[1:]:
            other = _find(parent, v)
            if other != root:
                parent[other] = root
    return [_find(parent, v) for v in range(n)]


def is_connected(n: int, facts: Sequence[Fact]) -> bool:
    """RQ6's connectivity: ``SparseHypergraph.is_connected`` semantics.

    A knowledge base with at most one constant is connected by convention; with
    more, every constant must lie in the one component, so an isolated constant
    disconnects it.
    """
    if n <= 1:
        return True
    return len(set(component_labels(n, facts))) == 1


def occurrence(n: int, facts: Sequence[Fact]) -> list[int]:
    """Number of facts containing each constant."""
    occ = [0] * n
    for _, members in facts:
        for v in members:
            occ[v] += 1
    return occ


def is_star(n: int, facts: Sequence[Fact]) -> bool:
    """Whether one constant occurs in every fact and no other occurs in two.

    A one-fact knowledge base is a star; an empty one is not (it has no fact for
    a constant to occur in).
    """
    m = len(facts)
    if m == 0:
        return False
    occ = occurrence(n, facts)
    for center in range(n):
        if occ[center] != m:
            continue
        if all(occ[v] <= 1 for v in range(n) if v != center):
            return True
    return False


def n_shared(n: int, facts: Sequence[Fact]) -> int:
    """Number of constants that occur in at least two facts."""
    return sum(1 for count in occurrence(n, facts) if count >= 2)


def in_envelope(kb: KB) -> bool:
    """Whether a knowledge base lies inside the collections' encodability envelope.

    The envelope (``n <= 24``, ``3 <= m <= 110``, arity ``<= 10``) is the window every
    member of the frozen collections satisfies; ``usable`` (decoded and connected) does
    not imply it, so this is reported as a post-hoc diagnostic only.
    """
    from isalhg.datasets.kb.base import DEFAULT_ENVELOPE

    n, _types, facts = kb
    widest = max((len(members) for _, members in facts), default=0)
    return DEFAULT_ENVELOPE.admits(n, len(facts), widest)


def is_usable(kb: KB) -> bool:
    """Whether a decoded knowledge base is inside the paper's domain."""
    n, _types, facts = kb
    return len(facts) >= 1 and is_connected(n, facts)


# ---------------------------------------------------------------------------
# Isomorphism key
# ---------------------------------------------------------------------------


def to_hypergraph(kb: KB, n_types: int, n_preds: int) -> SparseHypergraph:
    """Build the ``SparseHypergraph`` of a knowledge base under the collection's vocabularies."""
    from isalhg.core.sparse_hypergraph import SparseHypergraph

    n, types, facts = kb
    return SparseHypergraph(
        n,
        [members for _, members in facts],
        n_vertex_labels=max(n_types, max(types, default=0) + 1),
        n_edge_labels=max(n_preds, max((p for p, _ in facts), default=0) + 1),
        vertex_labels=list(types),
        edge_labels=[p for p, _ in facts],
    )


def iso_key(kb: KB, n_types: int, n_preds: int) -> IsoKey:
    """``ordered_fingerprint`` of a connected knowledge base: ``(root type, w°)``.

    Raises
    ------
    isalhg.errors.IsalHGError
        If the knowledge base is disconnected or empty.
    """
    from isalhg.iso_backends.isal_ordered import ordered_fingerprint

    root, word = ordered_fingerprint(to_hypergraph(kb, n_types, n_preds))
    return (int(root), word)


# ---------------------------------------------------------------------------
# Largest-connected-component repair
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Repair:
    """Result of keeping the largest component of a knowledge base.

    Attributes
    ----------
    kb : tuple
        The kept component, constants renumbered ``0..n'-1`` in increasing
        original id.
    n_components : int
        Number of components of the input (isolated constants included).
    rule_disagree : bool
        Whether a facts-first reading of "largest" would have kept a different
        component than the constants-first rule used here.
    """

    kb: KB
    n_components: int
    rule_disagree: bool


def _sub_kb(members: Sequence[int], fact_ids: Sequence[int], kb: KB) -> KB:
    _n, types, facts = kb
    renumber = {v: i for i, v in enumerate(sorted(members))}
    sub_types = tuple(types[v] for v in sorted(members))
    sub_facts = tuple(
        sorted((facts[f][0], tuple(renumber[v] for v in facts[f][1])) for f in fact_ids)
    )
    return (len(renumber), sub_types, sub_facts)


def repair_lcc(kb: KB, n_types: int, n_preds: int) -> Repair:
    """Keep the largest connected component of ``kb``.

    "Largest" is the component with the most constants; ties go to the one with
    more facts, then to the lowest ``(root type, w°)`` of the component.

    Parameters
    ----------
    kb : tuple
        ``(n, types, facts)``; may be disconnected, may have isolated constants.
    n_types, n_preds : int
        Collection vocabulary sizes, needed only to fingerprint tied components.

    Returns
    -------
    Repair
        The kept component and an audit of the tie-breaking rule.
    """
    n, _types, facts = kb
    if n == 0:
        return Repair(kb, 0, False)
    labels = component_labels(n, facts)
    verts: dict[int, list[int]] = {}
    for v, rep in enumerate(labels):
        verts.setdefault(rep, []).append(v)
    fact_ids: dict[int, list[int]] = {rep: [] for rep in verts}
    for f, (_p, members) in enumerate(facts):
        fact_ids[labels[members[0]]].append(f)
    reps = sorted(verts)
    if len(reps) == 1:
        return Repair(kb, 1, False)

    def by_constants(rep: int) -> tuple[int, int]:
        return (len(verts[rep]), len(fact_ids[rep]))

    def by_facts(rep: int) -> tuple[int, int]:
        return (len(fact_ids[rep]), len(verts[rep]))

    best = max(by_constants(r) for r in reps)
    tied = [r for r in reps if by_constants(r) == best]
    if len(tied) > 1:
        scored = []
        for rep in tied:
            sub = _sub_kb(verts[rep], fact_ids[rep], kb)
            scored.append((iso_key(sub, n_types, n_preds), rep))
        chosen = min(scored)[1]
    else:
        chosen = tied[0]
    best_facts = max(by_facts(r) for r in reps)
    facts_first = {r for r in reps if by_facts(r) == best_facts}
    return Repair(
        _sub_kb(verts[chosen], fact_ids[chosen], kb),
        len(reps),
        not (set(tied) & facts_first),
    )


# ---------------------------------------------------------------------------
# A compact sample set carrying the five RQ6 profiles
# ---------------------------------------------------------------------------


def _gather(ptr: np.ndarray, flat: np.ndarray, idx: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Concatenate the CSR segments ``idx`` of ``(ptr, flat)``."""
    starts = ptr[idx]
    lengths = ptr[idx + 1] - starts
    new_ptr = np.concatenate([[0], np.cumsum(lengths)]).astype(np.int64)
    total = int(new_ptr[-1])
    if total == 0:
        return new_ptr, flat[:0]
    offsets = np.repeat(starts - new_ptr[:-1], lengths)
    return new_ptr, flat[offsets + np.arange(total)]


@dataclass
class SampleSet:
    """Per-sample structure of a set of knowledge bases.

    Per sample: ``n``, ``m``, a star flag and the number of shared constants.
    Per fact (CSR over ``fact_ptr``): arity and predicate. Per constant (CSR over
    ``node_ptr``): type. The five RQ6 histograms are bincounts of these.
    """

    n: np.ndarray
    m: np.ndarray
    star: np.ndarray
    shared: np.ndarray
    fact_ptr: np.ndarray
    arity: np.ndarray
    pred: np.ndarray
    node_ptr: np.ndarray
    vtype: np.ndarray

    def __len__(self) -> int:
        return int(self.n.shape[0])

    @classmethod
    def from_kbs(cls, kbs: Iterable[KB]) -> SampleSet:
        """Build a sample set from ``(n, types, facts)`` triples."""
        ns: list[int] = []
        ms: list[int] = []
        stars: list[bool] = []
        shareds: list[int] = []
        fact_ptr = [0]
        node_ptr = [0]
        arity: list[int] = []
        pred: list[int] = []
        vtype: list[int] = []
        for n, types, facts in kbs:
            ns.append(n)
            ms.append(len(facts))
            stars.append(is_star(n, facts))
            shareds.append(n_shared(n, facts))
            for p, members in facts:
                arity.append(len(members))
                pred.append(p)
            vtype.extend(types)
            fact_ptr.append(len(arity))
            node_ptr.append(len(vtype))
        return cls(
            n=np.asarray(ns, dtype=np.int32),
            m=np.asarray(ms, dtype=np.int32),
            star=np.asarray(stars, dtype=bool),
            shared=np.asarray(shareds, dtype=np.int32),
            fact_ptr=np.asarray(fact_ptr, dtype=np.int64),
            arity=np.asarray(arity, dtype=np.int32),
            pred=np.asarray(pred, dtype=np.int32),
            node_ptr=np.asarray(node_ptr, dtype=np.int64),
            vtype=np.asarray(vtype, dtype=np.int32),
        )

    def take(self, idx: np.ndarray) -> SampleSet:
        """Sub-set at integer positions ``idx`` (order and repeats preserved)."""
        idx = np.asarray(idx, dtype=np.int64)
        fact_ptr, arity = _gather(self.fact_ptr, self.arity, idx)
        _, pred = _gather(self.fact_ptr, self.pred, idx)
        node_ptr, vtype = _gather(self.node_ptr, self.vtype, idx)
        return SampleSet(
            self.n[idx],
            self.m[idx],
            self.star[idx],
            self.shared[idx],
            fact_ptr,
            arity,
            pred,
            node_ptr,
            vtype,
        )

    def profile(self) -> dict[str, np.ndarray]:
        """The five normalised RQ6 histograms; all-zero for an empty population."""

        def hist(values: np.ndarray) -> np.ndarray:
            if values.size == 0:
                return np.zeros(1)
            counts = np.bincount(values).astype(np.float64)
            return counts / counts.sum()

        return {
            "n": hist(self.n),
            "m": hist(self.m),
            "arity": hist(self.arity),
            "pred": hist(self.pred),
            "type": hist(self.vtype),
        }

    def save(self, path: Path) -> None:
        """Write the arrays to a compressed ``.npz``."""
        np.savez_compressed(
            path,
            n=self.n,
            m=self.m,
            star=self.star,
            shared=self.shared,
            fact_ptr=self.fact_ptr,
            arity=self.arity,
            pred=self.pred,
            node_ptr=self.node_ptr,
            vtype=self.vtype,
        )

    @classmethod
    def load(cls, path: Path) -> SampleSet:
        """Read a sample set written by :meth:`save`."""
        with np.load(path) as data:
            return cls(**{name: data[name] for name in data.files})


# ---------------------------------------------------------------------------
# Distances between profiles
# ---------------------------------------------------------------------------


def jsd_profiles(
    sample: dict[str, np.ndarray], reference: dict[str, np.ndarray]
) -> dict[str, float]:
    """The five Jensen-Shannon divergences (bits) of RQ6, via the library's ``jsd``."""
    from isalhg.generation.fidelity import jsd

    return {key: jsd(sample[key], reference[key]) for key in PROFILE_KEYS}


def w1(p: np.ndarray, q: np.ndarray) -> float:
    """Wasserstein-1 between two histograms indexed by integer value from 0."""
    from scipy.stats import wasserstein_distance

    if p.sum() <= 0 or q.sum() <= 0:
        return math.nan
    return float(wasserstein_distance(np.arange(len(p)), np.arange(len(q)), p, q))


def set_metrics(
    sample: SampleSet, reference: SampleSet, ref_profile: dict[str, np.ndarray]
) -> dict[str, float]:
    """All fidelity quantities of one sample set against the collection.

    Returns
    -------
    dict[str, float]
        ``jsd_{n,m,arity,pred,type}``, ``w1_n``, ``w1_m``, ``mean_n``, ``mean_m``,
        ``star_frac``, ``rel_frac``, ``rel_dev`` (|relational fraction minus the
        collection's|) and ``shared``. NaN throughout for an empty set.
    """
    if len(sample) == 0:
        keys = [f"jsd_{k}" for k in PROFILE_KEYS] + [
            "w1_n",
            "w1_m",
            "mean_n",
            "mean_m",
            "star_frac",
            "rel_frac",
            "rel_dev",
            "shared",
        ]
        return {k: math.nan for k in keys}
    profile = sample.profile()
    out = {f"jsd_{k}": v for k, v in jsd_profiles(profile, ref_profile).items()}
    out["w1_n"] = w1(profile["n"], ref_profile["n"])
    out["w1_m"] = w1(profile["m"], ref_profile["m"])
    out["mean_n"] = float(sample.n.mean())
    out["mean_m"] = float(sample.m.mean())
    out["star_frac"] = float(sample.star.mean())
    out["rel_frac"] = 1.0 - out["star_frac"]
    out["rel_dev"] = abs(out["rel_frac"] - (1.0 - float(reference.star.mean())))
    out["shared"] = float(sample.shared.mean())
    return out


def unit_stem(collection: str, generator: str, seed: int) -> str:
    """File stem of one unit: ``<collection>__<generator>__s<seed>``."""
    return f"{collection}__{generator}__s{seed}"


def count_reasons(reasons: Iterable[str | None]) -> dict[str, int]:
    """Histogram of rejection causes, ``None`` mapped to ``"unknown"``."""
    return dict(Counter(r if r else "unknown" for r in reasons))
