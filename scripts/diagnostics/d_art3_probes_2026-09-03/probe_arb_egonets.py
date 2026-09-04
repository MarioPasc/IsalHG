"""Feasibility probe: ARB/Benson labeled contact hypergraphs as ego-net KB corpora.

Measures the two never-measured gates for the D-ART3 consensus experiment:
(G-D1/G-L2) ego-net size distribution + KBs per class label, and (G-L1-like)
`w*_c` wall-clock on labelled vs unlabelled ego-nets.

Read-only w.r.t. the repository: nothing under /home/mpascual/research/code/IsalHG
is written. All artifacts land in the scratchpad directory.

Subcommands
-----------
stats   Tasks 1-3: dataset summary, ego-net census, isomorphism-class census.
timing  Task 4: stratified `w*_c` timing, labelled vs unlabelled, subprocess timeout.
"""

from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import random
import statistics
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from isalhg.core.canonical import canonical_string, required_k
from isalhg.core.instructions import parse
from isalhg.core.sparse_hypergraph import SparseHypergraph, ego_network
from isalhg.datasets.arb_benson import ARBBensonDataset

ROOT = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/data/arb_benson/labeled")
OUT = Path(
    "/tmp/claude-1000/-home-mpascual-research-code-IsalHG/"
    "b1064998-d2d4-4d37-b206-e4206ec0bb6c/scratchpad"
)
DATASETS = ("contact-high-school", "contact-primary-school")
SEED = 20260903
SIZE_CAPS = (8, 12, 16, 24)
BUCKETS = ((1, 8), (9, 12), (13, 16), (17, 20), (21, 24), (25, 30))


# ----------------------------------------------------------------------
# Serialisation helpers (hypergraphs cross a process boundary for timing)
# ----------------------------------------------------------------------
def to_spec(H: SparseHypergraph) -> dict[str, Any]:
    return {
        "n": H.n_nodes,
        "edges": [sorted(m) for _, m, _ in H.iter_edges()],
        "vlabels": [H.vertex_label(v) for v in H.nodes()],
        "nvl": H.n_vertex_labels,
    }


def from_spec(spec: dict[str, Any], *, labelled: bool) -> SparseHypergraph:
    return SparseHypergraph(
        n_nodes=spec["n"],
        hyperedges=[frozenset(e) for e in spec["edges"]],
        n_vertex_labels=spec["nvl"] if labelled else 1,
        vertex_labels=spec["vlabels"] if labelled else [0] * spec["n"],
    )


def strip_labels(H: SparseHypergraph) -> SparseHypergraph:
    return SparseHypergraph(
        n_nodes=H.n_nodes,
        hyperedges=[m for _, m, _ in H.iter_edges()],
        n_vertex_labels=1,
        vertex_labels=[0] * H.n_nodes,
    )


def quantiles(xs: list[int]) -> dict[str, float]:
    if not xs:
        return {}
    s = sorted(xs)

    def q(p: float) -> float:
        i = min(len(s) - 1, max(0, int(round(p * (len(s) - 1)))))
        return float(s[i])

    return {
        "min": float(s[0]),
        "p25": q(0.25),
        "median": q(0.50),
        "p75": q(0.75),
        "p90": q(0.90),
        "max": float(s[-1]),
        "mean": round(statistics.fmean(s), 2),
    }


# ----------------------------------------------------------------------
# Tasks 1-3
# ----------------------------------------------------------------------
def run_stats(census_cap: int) -> dict[str, Any]:
    from isalhg.iso_backends.pynauty_levi import PynautyLeviBackend

    backend = PynautyLeviBackend()
    report: dict[str, Any] = {"seed": SEED, "census_cap": census_cap, "datasets": {}}

    for name in DATASETS:
        t0 = time.perf_counter()
        ds = ARBBensonDataset(root=ROOT, name=name)
        item = next(iter(ds))
        H = item.hypergraph
        vocab = ds.metadata.label_vocabulary
        symbols = list(vocab.vertex_symbols)

        label_freq = Counter(H.vertex_label(v) for v in H.nodes())
        arities = [len(m) for _, m, _ in H.iter_edges()]

        entry: dict[str, Any] = {
            "n_vertices": H.n_nodes,
            "m_unique_edges": H.n_edges,
            "m_file": item.extra.get("m_file"),
            "max_arity": max(arities) if arities else 0,
            "min_arity": min(arities) if arities else 0,
            "arity_hist": dict(sorted(Counter(arities).items())),
            "n_labels": len(symbols),
            "label_freq": {symbols[i]: c for i, c in sorted(label_freq.items())},
            "whole_connected": H.is_connected(),
        }

        # --- Task 2: ego networks -------------------------------------
        egos: list[dict[str, Any]] = []
        disconnected: list[int] = []
        for v in H.nodes():
            E = ego_network(H, v)
            if not E.is_connected():
                disconnected.append(v)
            e_ar = [len(m) for _, m, _ in E.iter_edges()]
            egos.append(
                {
                    "v": v,
                    "label": symbols[H.vertex_label(v)],
                    "n": E.n_nodes,
                    "m": E.n_edges,
                    "max_arity": max(e_ar) if e_ar else 0,
                }
            )

        ns = [e["n"] for e in egos]
        entry["ego"] = {
            "count": len(egos),
            "n": quantiles(ns),
            "m": quantiles([e["m"] for e in egos]),
            "max_arity": quantiles([e["max_arity"] for e in egos]),
            "disconnected_centres": disconnected,
            "frac_n_le": {
                str(c): round(sum(1 for x in ns if x <= c) / len(ns), 4) for c in SIZE_CAPS
            },
            "count_n_le": {str(c): sum(1 for x in ns if x <= c) for c in SIZE_CAPS},
            "n_hist_small": dict(sorted(Counter(x for x in ns if x <= 40).items())),
        }

        by_label: dict[str, dict[str, Any]] = {}
        for e in egos:
            g = by_label.setdefault(
                e["label"], {"N_total": 0, **{f"N_le_{c}": 0 for c in SIZE_CAPS}, "ns": []}
            )
            g["N_total"] += 1
            g["ns"].append(e["n"])
            for c in SIZE_CAPS:
                if e["n"] <= c:
                    g[f"N_le_{c}"] += 1
        for g in by_label.values():
            g["n_quantiles"] = quantiles(g.pop("ns"))
        entry["ego"]["by_label"] = by_label

        # --- Task 3: isomorphism census (n <= census_cap) --------------
        cens_lab: dict[str, set[Any]] = defaultdict(set)
        cens_unlab: dict[str, set[Any]] = defaultdict(set)
        all_lab: set[Any] = set()
        all_unlab: set[Any] = set()
        n_census = 0
        for e in egos:
            if e["n"] > census_cap:
                continue
            n_census += 1
            E = ego_network(H, e["v"])
            f_lab = backend.fingerprint(E)
            f_unlab = backend.fingerprint(strip_labels(E))
            all_lab.add(f_lab)
            all_unlab.add(f_unlab)
            cens_lab[e["label"]].add(f_lab)
            cens_unlab[e["label"]].add(f_unlab)

        counts = Counter(e["label"] for e in egos if e["n"] <= census_cap)
        entry["census"] = {
            "n_egonets": n_census,
            "distinct_labelled": len(all_lab),
            "distinct_unlabelled": len(all_unlab),
            "by_label": {
                lab: {
                    "n_egonets": counts[lab],
                    "distinct_labelled": len(cens_lab[lab]),
                    "distinct_unlabelled": len(cens_unlab[lab]),
                }
                for lab in sorted(counts)
            },
        }
        entry["wall_s"] = round(time.perf_counter() - t0, 2)
        report["datasets"][name] = entry
        print(f"[stats] {name} done in {entry['wall_s']}s", flush=True)

    (OUT / "probe_stats.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))
    return report


# ----------------------------------------------------------------------
# Task 4: timing with a hard subprocess timeout
# ----------------------------------------------------------------------
def _worker(spec: dict[str, Any], labelled: bool, q: Any) -> None:
    try:
        H = from_spec(spec, labelled=labelled)
        k = required_k(H)
        t0 = time.perf_counter()
        w = canonical_string(H, k=k, algorithm="canonical", backend="cpp")
        dt = time.perf_counter() - t0
        q.put({"ok": True, "sec": dt, "tokens": len(parse(w)), "chars": len(w), "k": k})
    except Exception as exc:  # noqa: BLE001 - report, never crash the parent
        q.put({"ok": False, "error": f"{type(exc).__name__}: {exc}"})


def time_one(spec: dict[str, Any], labelled: bool, budget: float) -> dict[str, Any]:
    ctx = mp.get_context("fork")
    q = ctx.Queue()
    p = ctx.Process(target=_worker, args=(spec, labelled, q))
    t0 = time.perf_counter()
    p.start()
    p.join(budget)
    if p.is_alive():
        p.terminate()
        p.join(5)
        if p.is_alive():
            p.kill()
        return {"ok": False, "dnf": True, "sec": budget}
    try:
        res = q.get_nowait()
    except Exception:  # noqa: BLE001
        return {
            "ok": False,
            "dnf": False,
            "error": "no result (child died)",
            "sec": time.perf_counter() - t0,
        }
    res["dnf"] = False
    return res


def run_timing(per_bucket: int, budget: float, deadline_s: float) -> dict[str, Any]:
    rng = random.Random(SEED)
    started = time.perf_counter()
    report: dict[str, Any] = {
        "seed": SEED,
        "per_bucket": per_bucket,
        "budget_s": budget,
        "engine": "C++ (isalhg.core._core), backend='cpp', algorithm='canonical'",
        "datasets": {},
    }

    for name in DATASETS:
        ds = ARBBensonDataset(root=ROOT, name=name)
        H = next(iter(ds)).hypergraph
        pool: dict[str, list[int]] = defaultdict(list)
        sizes: list[tuple[int, int]] = []
        for v in H.nodes():
            nei = {v}
            for e in H.incident_edges(v):
                nei |= H.members(e)
            sizes.append((v, len(nei)))
        for v, nsz in sizes:
            for lo, hi in BUCKETS:
                if lo <= nsz <= hi:
                    pool[f"{lo}-{hi}"].append(v)
                    break

        out: dict[str, Any] = {}
        for lo, hi in BUCKETS:
            key = f"{lo}-{hi}"
            cand = pool.get(key, [])
            if not cand:
                out[key] = {"available": 0}
                continue
            sample = rng.sample(cand, min(per_bucket, len(cand)))
            rows: list[dict[str, Any]] = []
            for v in sample:
                E = ego_network(H, v)
                spec = to_spec(E)
                row: dict[str, Any] = {"v": v, "n": E.n_nodes, "m": E.n_edges}
                for mode, lab in (("labelled", True), ("unlabelled", False)):
                    if time.perf_counter() - started > deadline_s:
                        row[mode] = {"skipped": "deadline"}
                        continue
                    row[mode] = time_one(spec, lab, budget)
                rows.append(row)
                print(
                    f"[timing] {name} {key} v={v} n={E.n_nodes} m={E.n_edges} "
                    f"L={row['labelled']} U={row['unlabelled']}",
                    flush=True,
                )
            out[key] = {"available": len(cand), "sampled": len(sample), "rows": rows}
        report["datasets"][name] = out
        (OUT / "probe_timing.json").write_text(json.dumps(report, indent=1))
        print(f"[timing] {name} done, elapsed {time.perf_counter() - started:.0f}s", flush=True)

    report["elapsed_s"] = round(time.perf_counter() - started, 1)
    (OUT / "probe_timing.json").write_text(json.dumps(report, indent=1))
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["stats", "timing"])
    ap.add_argument("--census-cap", type=int, default=24)
    ap.add_argument("--per-bucket", type=int, default=8)
    ap.add_argument("--budget", type=float, default=60.0)
    ap.add_argument("--deadline", type=float, default=2400.0)
    a = ap.parse_args()
    if a.stage == "stats":
        run_stats(a.census_cap)
    else:
        run_timing(a.per_bucket, a.budget, a.deadline)
    return 0


if __name__ == "__main__":
    sys.exit(main())
