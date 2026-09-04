"""Qualifier-rich hyper-relational collections: star-KB feasibility probe (Task A).

Derives per-entity "star knowledge bases" from hyper-relational statement
corpora (WD50K family + JF17K + WikiPeople) exactly as the 2026-09-03 WD50K
probe did: one hyperedge per statement over {subject, object, qualifier
values}, edge label = the main relation, entities anonymized.  Measures the
size distribution, the arity profile, the canonicalization-envelope yield, the
labelled isomorphism census, and labelled ``w*_c`` wall-clock on a stratified
n-bucket sample.

Read-only with respect to the IsalHG repository.
"""

from __future__ import annotations

import json
import os
import statistics
import subprocess
import sys
import time
from collections import Counter, defaultdict
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

DATA_ROOT = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/data")
SCRATCH = Path(
    "/tmp/claude-1000/-home-mpascual-research-code-IsalHG/"
    "b1064998-d2d4-4d37-b206-e4206ec0bb6c/scratchpad"
)
WORKER = SCRATCH / "probe_worker.py"
PYTHON = os.path.expanduser("~/.conda/envs/isalhg/bin/python")

K_MAX = 10
ENV_N = 24
ENV_M = 110
PER_INSTANCE_BUDGET_S = 30.0
GLOBAL_TIMING_BUDGET_S = 15 * 60.0
PER_COLLECTION_TIMING_BUDGET_S = 260.0
PER_BUCKET = 8
CONSECUTIVE_DNF_ABORT = 3
MIN_STATEMENTS = 3

BUCKETS: tuple[tuple[str, int, int], ...] = (
    ("<=8", 0, 8),
    ("9-12", 9, 12),
    ("13-16", 13, 16),
    ("17-20", 17, 20),
    ("21-24", 21, 24),
)

COLLECTIONS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("wd50k_33", "csv", ("train.txt", "valid.txt", "test.txt")),
    ("wd50k_66", "csv", ("train.txt", "valid.txt", "test.txt")),
    ("wd50k_100", "csv", ("train.txt", "valid.txt", "test.txt")),
    ("jf17k", "csv", ("train.txt", "test.txt")),
    ("wikipeople", "wikipeople", ("n-ary_train.json", "n-ary_valid.json", "n-ary_test.json")),
    ("wd50k", "csv", ("train.txt", "valid.txt", "test.txt")),
)


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Statement:
    subject: str
    relation: str
    obj: str
    qual_values: tuple[str, ...]
    qual_relations: tuple[str, ...]

    @property
    def vertices(self) -> frozenset[str]:
        return frozenset((self.subject, self.obj, *self.qual_values))

    @property
    def arity(self) -> int:
        return len(self.vertices)

    @property
    def n_qualifiers(self) -> int:
        return len(self.qual_values)

    @property
    def folded_label(self) -> str:
        """Main relation folded with the sorted multiset of qualifier relations."""
        if not self.qual_relations:
            return self.relation
        return self.relation + "|" + "|".join(sorted(self.qual_relations))


def parse_csv(path: Path) -> Iterator[Statement]:
    """StarE `data/clean` statement format: s,r,o[,qr,qv]*."""
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
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
                qual_relations=tuple(rest[i] for i in range(0, len(rest) - 1, 2)),
            )


def parse_wikipeople(path: Path) -> Iterator[Statement]:
    """WikiPeople raw n-ary JSON: {"<P>_h": s, "<P>_t": o, "N": a, "<Pq>": [v...]}."""
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            main = None
            for key in rec:
                if key.endswith("_h"):
                    main = key[:-2]
                    break
            if main is None or f"{main}_t" not in rec:
                continue
            qv: list[str] = []
            qr: list[str] = []
            for key, val in rec.items():
                if key == "N" or key.endswith("_h") or key.endswith("_t"):
                    continue
                vals = val if isinstance(val, list) else [val]
                for v in vals:
                    qv.append(str(v))
                    qr.append(key)
            yield Statement(
                subject=str(rec[f"{main}_h"]),
                relation=main,
                obj=str(rec[f"{main}_t"]),
                qual_values=tuple(qv),
                qual_relations=tuple(qr),
            )


def load(name: str, kind: str, files: tuple[str, ...]) -> list[Statement]:
    parser = parse_csv if kind == "csv" else parse_wikipeople
    out: list[Statement] = []
    for f in files:
        p = DATA_ROOT / name / f
        if not p.exists():
            raise FileNotFoundError(p)
        out.extend(parser(p))
    return out


# --------------------------------------------------------------------------
# Star-KB derivation
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class StarKB:
    entity: str
    n: int
    m_stmts: int
    m: int  # distinct (label, member-set) hyperedges -- the hypergraph's m
    max_arity: int
    arity_hist: tuple[tuple[int, int], ...]
    statements: tuple[Statement, ...]


def build_star(entity: str, stmts: list[Statement]) -> StarKB:
    verts: set[str] = set()
    for s in stmts:
        verts |= s.vertices
    dedup = {(s.relation, s.vertices) for s in stmts}
    return StarKB(
        entity=entity,
        n=len(verts),
        m_stmts=len(stmts),
        m=len(dedup),
        max_arity=max(len(mem) for _, mem in dedup),
        arity_hist=tuple(sorted(Counter(len(mem) for _, mem in dedup).items())),
        statements=tuple(stmts),
    )


def quantiles(xs: list[int]) -> dict[str, float]:
    xs = sorted(xs)
    if not xs:
        return {}

    def q(p: float) -> float:
        return float(xs[min(len(xs) - 1, max(0, int(round(p * (len(xs) - 1)))))])

    return {
        "min": float(xs[0]),
        "p25": q(0.25),
        "median": q(0.50),
        "p75": q(0.75),
        "p90": q(0.90),
        "max": float(xs[-1]),
        "mean": round(statistics.fmean(xs), 2),
    }


def star_spec(star: StarKB, rel_ids: dict[str, int]) -> dict:
    verts = sorted({v for s in star.statements for v in s.vertices})
    vid = {v: i for i, v in enumerate(verts)}
    seen: set[tuple[int, frozenset[int]]] = set()
    edges: list[list[int]] = []
    labels: list[int] = []
    for s in star.statements:
        members = frozenset(vid[v] for v in s.vertices)
        lab = rel_ids[s.relation]
        if (lab, members) in seen:
            continue
        seen.add((lab, members))
        edges.append(sorted(members))
        labels.append(lab)
    return {
        "n_nodes": len(verts),
        "edges": edges,
        "edge_labels": labels,
        "n_edge_labels": max(rel_ids.values()) + 1,
    }


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
        tail = proc.stderr.strip().splitlines()
        return {
            "status": "ERROR",
            "wall_s": round(wall, 4),
            "tokens": None,
            "err": tail[-1] if tail else "",
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
# Per-collection probe
# --------------------------------------------------------------------------


def probe(name: str, kind: str, files: tuple[str, ...], t_global: float) -> dict:
    t0 = time.perf_counter()
    stmts = load(name, kind, files)
    relations = sorted({s.relation for s in stmts})
    rel_ids = {r: i for i, r in enumerate(relations)}
    folded = {s.folded_label for s in stmts}
    n_qual = sum(1 for s in stmts if s.n_qualifiers >= 1)

    res: dict = {
        "corpus": {
            "n_statements": len(stmts),
            "n_main_relations": len(relations),
            "n_entities_values": len({v for s in stmts for v in s.vertices}),
            "n_with_qualifier": n_qual,
            "frac_with_qualifier": round(n_qual / len(stmts), 4),
            "stmt_arity_hist": dict(sorted(Counter(s.arity for s in stmts).items())),
            "n_folded_edge_labels": len(folded),
            "folded_over_main": round(len(folded) / len(relations), 2),
        }
    }

    by_subject: dict[str, list[Statement]] = defaultdict(list)
    for s in stmts:
        by_subject[s.subject].append(s)
    stars = [build_star(e, ss) for e, ss in by_subject.items() if len(ss) >= MIN_STATEMENTS]
    print(f"[{name}] statements={len(stmts)} stars>=3={len(stars)}", flush=True)

    edge_ar: Counter[int] = Counter()
    for st in stars:
        for a, c in st.arity_hist:
            edge_ar[a] += c
    tot_edges = sum(edge_ar.values())
    res["stars"] = {
        "count": len(stars),
        "n": quantiles([s.n for s in stars]),
        "m": quantiles([s.m for s in stars]),
        "m_statements": quantiles([s.m_stmts for s in stars]),
        "max_arity": quantiles([s.max_arity for s in stars]),
        "edge_arity_hist": dict(sorted(edge_ar.items())),
        "n_edges": tot_edges,
        "frac_edges_arity_ge3": round(sum(c for a, c in edge_ar.items() if a >= 3) / tot_edges, 4),
        "n_stars_with_hyperedge": sum(1 for s in stars if s.max_arity >= 3),
        "frac_stars_with_hyperedge": round(
            sum(1 for s in stars if s.max_arity >= 3) / len(stars), 4
        ),
    }

    env_all = [s for s in stars if s.n <= ENV_N and s.m <= ENV_M]
    over_k = [s for s in env_all if s.max_arity > K_MAX]
    env = [s for s in env_all if s.max_arity <= K_MAX]
    e_ar: Counter[int] = Counter()
    for st in env:
        for a, c in st.arity_hist:
            e_ar[a] += c
    e_tot = max(1, sum(e_ar.values()))
    res["envelope"] = {
        "rule": f"n<={ENV_N} and m<={ENV_M}",
        "count_raw": len(env_all),
        "count_over_k_max": len(over_k),
        "count": len(env),
        "yield_frac_of_stars": round(len(env) / len(stars), 4),
        "n": quantiles([s.n for s in env]),
        "m": quantiles([s.m for s in env]),
        "max_arity": quantiles([s.max_arity for s in env]),
        "edge_arity_hist": dict(sorted(e_ar.items())),
        "frac_edges_arity_ge3": round(sum(c for a, c in e_ar.items() if a >= 3) / e_tot, 4),
        "n_with_hyperedge": sum(1 for s in env if s.max_arity >= 3),
        "frac_with_hyperedge": round(sum(1 for s in env if s.max_arity >= 3) / max(1, len(env)), 4),
        "also_n_le_24_only": sum(1 for s in stars if s.n <= ENV_N),
    }
    print(f"[{name}] envelope={len(env)} (raw {len(env_all)}, >K_MAX {len(over_k)})", flush=True)

    # ---- census (labelled + unlabelled) --------------------------------
    from isalhg.core.sparse_hypergraph import SparseHypergraph
    from isalhg.iso_backends.pynauty_levi import PynautyLeviBackend

    backend = PynautyLeviBackend()
    census: dict = {}
    for mode in ("labelled", "unlabelled"):
        fps: Counter[bytes] = Counter()
        tc = time.perf_counter()
        for st in env:
            spec = star_spec(st, rel_ids)
            if mode == "unlabelled":
                spec = dict(spec, edge_labels=[0] * len(spec["edges"]), n_edge_labels=1)
            H = SparseHypergraph(
                spec["n_nodes"],
                [frozenset(e) for e in spec["edges"]],
                n_edge_labels=spec["n_edge_labels"],
                edge_labels=spec["edge_labels"],
            )
            fps[backend.fingerprint(H)] += 1
        top = fps.most_common(10)
        census[mode] = {
            "n_kbs": len(env),
            "distinct_classes": len(fps),
            "classes_per_kb": round(len(fps) / max(1, len(env)), 4),
            "singletons": sum(1 for c in fps.values() if c == 1),
            "top10_sizes": [c for _, c in top],
            "top10_share": round(sum(c for _, c in top) / max(1, len(env)), 4),
            "wall_s": round(time.perf_counter() - tc, 2),
        }
        print(f"[{name}] census {mode}: {len(fps)}/{len(env)}", flush=True)
    res["census"] = census

    # ---- timing (labelled only) ----------------------------------------
    env_sorted = sorted(env, key=lambda s: (s.n, s.m, s.entity))
    timing: dict = {}
    for label, lo, hi in BUCKETS:
        pool = [s for s in env_sorted if lo <= s.n <= hi]
        if len(pool) > PER_BUCKET:
            step = len(pool) / PER_BUCKET
            sample = [pool[int(i * step)] for i in range(PER_BUCKET)]
        else:
            sample = pool
        rows: list[dict] = []
        consecutive = 0
        for st in sample:
            now = time.perf_counter()
            if now - t_global > GLOBAL_TIMING_BUDGET_S or now - t0 > PER_COLLECTION_TIMING_BUDGET_S:
                break
            if consecutive >= CONSECUTIVE_DNF_ABORT:
                break
            r = time_one(star_spec(st, rel_ids), PER_INSTANCE_BUDGET_S)
            r.update(entity=st.entity, n=st.n, m=st.m, max_arity=st.max_arity)
            rows.append(r)
            consecutive = consecutive + 1 if r["status"] == "DNF" else 0
        ok = [r for r in rows if r["status"] == "OK"]
        walls = sorted(r["wall_s"] for r in ok)
        toks = sorted(r["tokens"] for r in ok)
        timing[label] = {
            "pool": len(pool),
            "attempted": len(rows),
            "ok": len(ok),
            "dnf": sum(1 for r in rows if r["status"] == "DNF"),
            "error": sum(1 for r in rows if r["status"] == "ERROR"),
            "errors": [r.get("err", "") for r in rows if r["status"] == "ERROR"][:2],
            "median_s": round(statistics.median(walls), 4) if walls else None,
            "p90_s": (
                round(walls[min(len(walls) - 1, int(round(0.9 * (len(walls) - 1))))], 4)
                if walls
                else None
            ),
            "max_s": round(walls[-1], 4) if walls else None,
            "median_tokens": statistics.median(toks) if toks else None,
            "max_tokens": toks[-1] if toks else None,
            "rows": rows,
        }
        print(
            f"[{name}] timing {label}: pool={len(pool)} att={len(rows)} "
            f"ok={len(ok)} dnf={timing[label]['dnf']} med={timing[label]['median_s']}",
            flush=True,
        )
    res["timing"] = timing
    res["wall_s"] = round(time.perf_counter() - t0, 1)

    # entity list for Task B
    res["_env_entities"] = [s.entity for s in env]
    return res


def main() -> None:
    t_global = time.perf_counter()
    only = sys.argv[1:] or None
    out: dict = {}
    for name, kind, files in COLLECTIONS:
        if only and name not in only:
            continue
        out[name] = probe(name, kind, files, t_global)
        (SCRATCH / "probe_hyperrel_results.json").write_text(json.dumps(out, indent=1, default=str))
    print(f"[done] total {round(time.perf_counter() - t_global, 1)}s", flush=True)


if __name__ == "__main__":
    main()
