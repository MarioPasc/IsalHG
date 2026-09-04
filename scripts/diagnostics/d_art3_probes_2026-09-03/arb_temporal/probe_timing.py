"""Task 5: labelled / unlabelled ``w*_c`` wall-clock on the stratified samples.

Per-instance budget enforced by killing a forked child (the C++ extension does
not poll signals). A bucket-mode is abandoned after ``--max-dnf`` timeouts; the
whole run stops at ``--deadline`` seconds. Results are flushed after every
dataset, so an interruption loses at most the dataset in flight.

Usage: python probe_timing.py --budget 30 --deadline 1400 --max-dnf 3
"""

from __future__ import annotations

import json
import multiprocessing as mp
import os
import sys
import time

import arb_temporal_lib as L

# imported in the parent so every forked child inherits them (no per-call import cost)
from isalhg.core.canonical import canonical_string, required_k
from isalhg.core.instructions import parse
from isalhg.core.sparse_hypergraph import SparseHypergraph


def _child(edges, vlabels, nlab, q):
    try:
        loc = {v: i for i, v in enumerate(sorted({v for e in edges for v in e}))}
        hes = [frozenset(loc[v] for v in e) for e in edges]
        if vlabels is None:
            H = SparseHypergraph(len(loc), hes)
        else:
            vl = [0] * len(loc)
            for v, i in loc.items():
                vl[i] = vlabels[str(v)]
            H = SparseHypergraph(len(loc), hes, n_vertex_labels=nlab, vertex_labels=vl)
        k = required_k(H)
        t0 = time.perf_counter()
        w = canonical_string(H, k=k, algorithm="canonical", backend="cpp")
        el = time.perf_counter() - t0
        q.put(("ok", el, len(parse(w))))
    except Exception as exc:  # noqa: BLE001
        q.put(("error", 0.0, f"{type(exc).__name__}: {exc}"))


def run_one(edges, vlabels, nlab, budget):
    q = mp.Queue()
    p = mp.Process(target=_child, args=(edges, vlabels, nlab, q))
    t0 = time.time()
    p.start()
    p.join(budget)
    if p.is_alive():
        p.terminate()
        p.join()
        return dict(status="dnf", secs=budget)
    try:
        kind, el, extra = q.get_nowait()
    except Exception:  # noqa: BLE001
        return dict(status="crash", secs=round(time.time() - t0, 4))
    if kind == "ok":
        return dict(status="ok", secs=round(el, 4), tokens=extra)
    return dict(status="error", secs=0.0, msg=extra)


def main() -> None:
    a = sys.argv
    budget = float(a[a.index("--budget") + 1]) if "--budget" in a else 30.0
    deadline = float(a[a.index("--deadline") + 1]) if "--deadline" in a else 1400.0
    max_dnf = int(a[a.index("--max-dnf") + 1]) if "--max-dnf" in a else 3
    out = os.path.join(L.OUT, a[a.index("--out") + 1] if "--out" in a else "timing.json")
    t_start = time.time()
    results: list[dict] = []
    for ds in L.PRIORITY:
        try:
            with open(os.path.join(L.OUT, f"spec_{ds}.json")) as fh:
                spec = json.load(fh)
        except FileNotFoundError:
            continue
        items = spec["items"]
        allnodes = sorted({v for it in items for e in it["edges"] for v in e})
        vlab = {str(v): i for i, v in enumerate(allnodes)}
        nlab = len(allnodes)
        for mode in ("labelled", "unlabelled"):
            dnf_in_bucket: dict[str, int] = {}
            for it in items:
                rec = dict(
                    dataset=ds,
                    granularity=spec["granularity"],
                    mode=mode,
                    bucket=it["bucket"],
                    n=it["n"],
                    m=it["m"],
                    max_arity=it["max_arity"],
                    node=it["node"],
                    window=it["window"],
                )
                if time.time() - t_start > deadline:
                    rec.update(status="skipped_deadline")
                elif dnf_in_bucket.get(it["bucket"], 0) >= max_dnf:
                    rec.update(status="skipped_bucket_dnf")
                else:
                    rec.update(
                        run_one(it["edges"], None if mode == "unlabelled" else vlab, nlab, budget)
                    )
                    if rec["status"] == "dnf":
                        dnf_in_bucket[it["bucket"]] = dnf_in_bucket.get(it["bucket"], 0) + 1
                results.append(rec)
            print(f"[{ds}/{mode}] done, elapsed {time.time() - t_start:.0f}s", flush=True)
        with open(out, "w") as fh:  # flush after every dataset
            json.dump(results, fh)
    with open(out, "w") as fh:
        json.dump(results, fh)
    print(f"TOTAL {time.time() - t_start:.0f}s, {len(results)} cells", flush=True)


if __name__ == "__main__":
    mp.set_start_method("fork")
    main()
