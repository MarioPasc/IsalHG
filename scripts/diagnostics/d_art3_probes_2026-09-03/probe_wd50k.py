"""WD50K feasibility probe for the IsalHG canonicalization envelope.

Derives per-entity "ego knowledge bases" from the WD50K hyper-relational
statement corpus (Galkin et al., EMNLP 2020) under two encodings, measures
their size distribution, times the C++ tie-complete canonical string on a
stratified sample, and counts isomorphism classes with pynauty over the Levi
reduction.

Read-only with respect to the IsalHG repository. Writes only its own JSON
summary into the scratchpad directory.
"""

from __future__ import annotations

import json
import os
import statistics
import subprocess
import time
from collections import Counter, defaultdict
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

DATA_DIR = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/data/wd50k")
SCRATCH = Path(
    "/tmp/claude-1000/-home-mpascual-research-code-IsalHG/"
    "b1064998-d2d4-4d37-b206-e4206ec0bb6c/scratchpad"
)
WORKER = SCRATCH / "probe_worker.py"
PYTHON = os.path.expanduser("~/.conda/envs/isalhg/bin/python")

PER_INSTANCE_BUDGET_S = 60.0
GLOBAL_TIMING_BUDGET_S = 20 * 60.0
BUCKETS: tuple[tuple[str, int, int], ...] = (
    ("<=8", 0, 8),
    ("9-12", 9, 12),
    ("13-16", 13, 16),
    ("17-20", 17, 20),
    ("21-24", 21, 24),
)
PER_BUCKET = 8
CONSECUTIVE_DNF_ABORT = 3


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Statement:
    subject: str
    relation: str
    obj: str
    qual_values: tuple[str, ...]

    @property
    def vertices(self) -> frozenset[str]:
        return frozenset((self.subject, self.obj, *self.qual_values))

    @property
    def arity(self) -> int:
        return len(self.vertices)

    @property
    def n_qualifiers(self) -> int:
        return len(self.qual_values)


def parse_statements(path: Path) -> Iterator[Statement]:
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            if len(parts) < 3:
                continue
            subject, relation, obj = parts[0], parts[1], parts[2]
            rest = parts[3:]
            qual_values = tuple(rest[i] for i in range(1, len(rest), 2))
            yield Statement(subject, relation, obj, qual_values)


# --------------------------------------------------------------------------
# Ego-KB derivation
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class EgoKB:
    entity: str
    n: int  # distinct entities/values  (reading a)
    m: int  # statements
    max_arity: int
    n_prime: int  # 1 + |D| + |F|        (reading b)
    n_distinct_edges: int  # after (label, member-set) dedup
    statements: tuple[Statement, ...]


def build_ego(entity: str, stmts: list[Statement]) -> EgoKB:
    verts: set[str] = set()
    for s in stmts:
        verts |= s.vertices
    dedup = {(s.relation, s.vertices) for s in stmts}
    n = len(verts)
    return EgoKB(
        entity=entity,
        n=n,
        m=len(stmts),
        max_arity=max(s.arity for s in stmts),
        # reading (b): anchor + entities other than the anchor + one node per fact
        n_prime=1 + (n - 1 if entity in verts else n) + len(stmts),
        n_distinct_edges=len(dedup),
        statements=tuple(stmts),
    )


def quantiles(xs: list[int]) -> dict[str, float]:
    xs = sorted(xs)
    if not xs:
        return {}

    def q(p: float) -> float:
        idx = min(len(xs) - 1, max(0, int(round(p * (len(xs) - 1)))))
        return float(xs[idx])

    return {
        "min": float(xs[0]),
        "p25": q(0.25),
        "median": q(0.50),
        "p75": q(0.75),
        "p90": q(0.90),
        "max": float(xs[-1]),
        "mean": round(statistics.fmean(xs), 2),
    }


# --------------------------------------------------------------------------
# Hypergraph spec (serialised to the timing worker / built in-process)
# --------------------------------------------------------------------------


def ego_spec(ego: EgoKB, rel_ids: dict[str, int], labelled: bool) -> dict:
    verts = sorted({v for s in ego.statements for v in s.vertices})
    vid = {v: i for i, v in enumerate(verts)}
    seen: set[tuple[int, frozenset[int]]] = set()
    edges: list[list[int]] = []
    labels: list[int] = []
    for s in ego.statements:
        members = frozenset(vid[v] for v in s.vertices)
        lab = rel_ids[s.relation] if labelled else 0
        if (lab, members) in seen:
            continue
        seen.add((lab, members))
        edges.append(sorted(members))
        labels.append(lab)
    return {
        "n_nodes": len(verts),
        "edges": edges,
        "edge_labels": labels,
        "n_edge_labels": (max(rel_ids.values()) + 1) if labelled else 1,
    }


def build_hypergraph(spec: dict):
    from isalhg.core.sparse_hypergraph import SparseHypergraph

    return SparseHypergraph(
        spec["n_nodes"],
        [frozenset(e) for e in spec["edges"]],
        n_edge_labels=spec["n_edge_labels"],
        edge_labels=spec["edge_labels"],
    )


# --------------------------------------------------------------------------
# Timing (subprocess so a DNF cannot hang the driver)
# --------------------------------------------------------------------------


def time_one(spec: dict, budget: float) -> dict:
    t0 = time.perf_counter()
    try:
        proc = subprocess.run(
            [PYTHON, str(WORKER)],
            input=json.dumps(spec),
            capture_output=True,
            text=True,
            timeout=budget,
        )
    except subprocess.TimeoutExpired:
        return {"status": "DNF", "wall_s": budget, "tokens": None}
    wall = time.perf_counter() - t0
    if proc.returncode != 0:
        return {
            "status": "ERROR",
            "wall_s": round(wall, 4),
            "tokens": None,
            "err": proc.stderr.strip().splitlines()[-1] if proc.stderr.strip() else "",
        }
    out = json.loads(proc.stdout)
    return {
        "status": "OK",
        "wall_s": round(out["wall_s"], 4),
        "proc_wall_s": round(wall, 4),
        "tokens": out["tokens"],
        "k": out["k"],
    }


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


def main() -> None:
    t_start = time.perf_counter()
    result: dict = {}

    files = [DATA_DIR / f for f in ("train.txt", "valid.txt", "test.txt")]
    all_stmts: list[Statement] = []
    for f in files:
        all_stmts.extend(parse_statements(f))
    print(f"[parse] statements={len(all_stmts)}", flush=True)

    # ---- global corpus stats -------------------------------------------
    arity_hist = Counter(s.arity for s in all_stmts)
    qual_hist = Counter(s.n_qualifiers for s in all_stmts)
    n_with_qual = sum(v for k, v in qual_hist.items() if k >= 1)
    n_arity_ge3 = sum(v for k, v in arity_hist.items() if k >= 3)
    relations = sorted({s.relation for s in all_stmts})
    rel_ids = {r: i for i, r in enumerate(relations)}
    entities_all = {v for s in all_stmts for v in s.vertices}
    result["corpus"] = {
        "n_statements": len(all_stmts),
        "n_relations_main": len(relations),
        "n_entities_values": len(entities_all),
        "arity_hist": dict(sorted(arity_hist.items())),
        "qualifier_hist": dict(sorted(qual_hist.items())),
        "n_with_qualifier": n_with_qual,
        "frac_with_qualifier": round(n_with_qual / len(all_stmts), 4),
        "n_arity_ge3": n_arity_ge3,
        "frac_arity_ge3": round(n_arity_ge3 / len(all_stmts), 4),
    }

    # ---- ego-KBs --------------------------------------------------------
    by_subject: dict[str, list[Statement]] = defaultdict(list)
    by_incident: dict[str, list[Statement]] = defaultdict(list)
    for s in all_stmts:
        by_subject[s.subject].append(s)
        for v in s.vertices:
            by_incident[v].append(s)

    egos_subj = [build_ego(e, ss) for e, ss in by_subject.items() if len(ss) >= 3]
    egos_inc = [build_ego(e, ss) for e, ss in by_incident.items() if len(ss) >= 3]
    print(f"[ego] subject-only>=3: {len(egos_subj)}  incident>=3: {len(egos_inc)}", flush=True)

    def ego_block(egos: list[EgoKB]) -> dict:
        return {
            "count": len(egos),
            "n": quantiles([e.n for e in egos]),
            "m": quantiles([e.m for e in egos]),
            "max_arity": quantiles([e.max_arity for e in egos]),
            "n_prime": quantiles([e.n_prime for e in egos]),
            "n_le_12": sum(1 for e in egos if e.n <= 12),
            "n_le_16": sum(1 for e in egos if e.n <= 16),
            "n_le_24": sum(1 for e in egos if e.n <= 24),
            "nprime_le_12": sum(1 for e in egos if e.n_prime <= 12),
            "nprime_le_16": sum(1 for e in egos if e.n_prime <= 16),
            "nprime_le_24": sum(1 for e in egos if e.n_prime <= 24),
            "maxarity_hist": dict(sorted(Counter(e.max_arity for e in egos).items())),
            "n_with_any_hyperedge": sum(1 for e in egos if e.max_arity >= 3),
        }

    result["ego_subject"] = ego_block(egos_subj)
    result["ego_incident"] = ego_block(egos_inc)

    # envelope-restricted (n<=24) view of reading (a), subject-only
    env = [e for e in egos_subj if e.n <= 24]
    result["envelope_subject_n_le_24"] = {
        "count": len(env),
        "m": quantiles([e.m for e in env]),
        "max_arity_hist": dict(sorted(Counter(e.max_arity for e in env).items())),
        "n_hyper": sum(1 for e in env if e.max_arity >= 3),
        "density_m_over_n": round(statistics.fmean([e.m / e.n for e in env]), 3),
    }

    # ---- timing ---------------------------------------------------------
    egos_sorted = sorted(env, key=lambda e: (e.n, e.m, e.entity))
    timing: dict = {}
    aborted = False
    for label, lo, hi in BUCKETS:
        pool = [e for e in egos_sorted if lo <= e.n <= hi]
        # deterministic stratified pick: evenly spaced through the pool
        if len(pool) > PER_BUCKET:
            step = len(pool) / PER_BUCKET
            sample = [pool[int(i * step)] for i in range(PER_BUCKET)]
        else:
            sample = pool
        timing[label] = {"pool_size": len(pool), "sampled": len(sample), "modes": {}}
        for mode, labelled in (("labelled", True), ("unlabelled", False)):
            rows = []
            consecutive_dnf = 0
            for ego in sample:
                if time.perf_counter() - t_start > GLOBAL_TIMING_BUDGET_S:
                    aborted = True
                    break
                if consecutive_dnf >= CONSECUTIVE_DNF_ABORT:
                    break
                spec = ego_spec(ego, rel_ids, labelled)
                r = time_one(spec, PER_INSTANCE_BUDGET_S)
                r.update(entity=ego.entity, n=ego.n, m=ego.m, max_arity=ego.max_arity)
                rows.append(r)
                consecutive_dnf = consecutive_dnf + 1 if r["status"] == "DNF" else 0
                print(
                    f"[time] {label}/{mode} {ego.entity} n={ego.n} m={ego.m} "
                    f"a={ego.max_arity} -> {r['status']} {r['wall_s']}s",
                    flush=True,
                )
            ok = [r for r in rows if r["status"] == "OK"]
            walls = sorted(r["wall_s"] for r in ok)
            toks = sorted(r["tokens"] for r in ok)
            timing[label]["modes"][mode] = {
                "attempted": len(rows),
                "ok": len(ok),
                "dnf": sum(1 for r in rows if r["status"] == "DNF"),
                "error": sum(1 for r in rows if r["status"] == "ERROR"),
                "errors": [r.get("err", "") for r in rows if r["status"] == "ERROR"][:3],
                "median_s": round(statistics.median(walls), 4) if walls else None,
                "p90_s": (
                    round(walls[min(len(walls) - 1, int(round(0.9 * (len(walls) - 1))))], 4)
                    if walls
                    else None
                ),
                "max_s": round(walls[-1], 4) if walls else None,
                "median_tokens": statistics.median(toks) if toks else None,
                "p90_tokens": (
                    toks[min(len(toks) - 1, int(round(0.9 * (len(toks) - 1))))] if toks else None
                ),
                "rows": rows,
            }
    result["timing"] = timing
    result["timing_aborted_on_budget"] = aborted

    # ---- census ---------------------------------------------------------
    from isalhg.core.sparse_hypergraph import SparseHypergraph
    from isalhg.iso_backends.pynauty_levi import PynautyLeviBackend

    backend = PynautyLeviBackend()
    # sanity: does the Levi backend see edge labels?
    a = SparseHypergraph(
        4, [frozenset({0, 1, 2}), frozenset({2, 3})], n_edge_labels=2, edge_labels=[0, 1]
    )
    b = SparseHypergraph(
        4, [frozenset({0, 1, 2}), frozenset({2, 3})], n_edge_labels=2, edge_labels=[1, 0]
    )
    label_sensitive = backend.fingerprint(a) != backend.fingerprint(b)
    result["census_label_sensitivity_check"] = bool(label_sensitive)

    census: dict = {}
    for mode, labelled in (("labelled", True), ("unlabelled", False)):
        fps = Counter()
        t0 = time.perf_counter()
        for ego in env:
            H = build_hypergraph(ego_spec(ego, rel_ids, labelled))
            fps[backend.fingerprint(H)] += 1
        top = fps.most_common(10)
        census[mode] = {
            "n_ego_kbs": len(env),
            "distinct_classes": len(fps),
            "ratio_classes_per_kb": round(len(fps) / len(env), 4),
            "singletons": sum(1 for c in fps.values() if c == 1),
            "top10_frequencies": [c for _, c in top],
            "top10_share": round(sum(c for _, c in top) / len(env), 4),
            "wall_s": round(time.perf_counter() - t0, 2),
        }
        print(f"[census] {mode}: {census[mode]['distinct_classes']}/{len(env)}", flush=True)
    result["census"] = census
    result["total_wall_s"] = round(time.perf_counter() - t_start, 1)

    out = SCRATCH / "probe_wd50k_results.json"
    out.write_text(json.dumps(result, indent=1, default=str))
    print(json.dumps({k: v for k, v in result.items() if k != "timing"}, default=str)[:20])
    print(f"[done] {result['total_wall_s']}s -> {out}", flush=True)


if __name__ == "__main__":
    main()
