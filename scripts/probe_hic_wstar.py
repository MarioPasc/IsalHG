"""T-DQ3' probe: wall-clock of ``w*_c`` on HIC atlas instances.

The real-anchor gate measurement (first run 2026-07-19, verdict NO-GO —
``docs/article/DATA.md`` §2). Kept as the re-test harness: after any encoder
speedup (stabiliser-orbit pruning is the sanctioned one), re-run the
``budget`` mode and compare the completion fraction against the recorded
baseline (73/100 at 10 s/instance, arity cap 10, seed 20260719).

Modes
-----
pick                       corpus_k + probe instances at size quantiles
filter CAP                 survivor count/classes under ``required_k <= CAP``
filter-all CAP             survivor fractions across all 12 HIC datasets
one IDX K                  time ``canonical_string`` on instance IDX at k=K
pyprobe IDX K              same, Python backend (no K_MAX cap)
sample K N                 seeded N-instance sample, no per-instance budget
sample-capped CAP K N      same, restricted to survivors of the arity cap
budget CAP K N BUDGET_S    seeded N-instance sweep, BUDGET_S per instance in
                           forked workers (a DNF cannot stall the sweep; the
                           C++ FFI call ignores SIGALRM)
"""

from __future__ import annotations

import logging
import random
import sys
import time
from pathlib import Path

import numpy as np

from isalhg.core.canonical import canonical_string, required_k
from isalhg.datasets.hic_atlas import HICAtlasDataset

logging.basicConfig(level=logging.ERROR)

ROOT = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/data/HIC/data/hypergraph")
NAME = "IMDB-Dir-Form"
SEED = 20260719


def _load() -> list:
    return list(HICAtlasDataset(root=ROOT, hic_name=NAME))


def _print_picks(items: list, ks: list[int], indices: dict[str, int]) -> None:
    for label, idx in indices.items():
        it = items[idx]
        H = it.hypergraph
        print(
            f"{label:6} idx={idx} id={it.item_id} n={H.n_nodes} m={H.n_edges} req_k={required_k(H)}"
        )


def main() -> int:  # noqa: PLR0915
    mode = sys.argv[1]

    if mode == "filter-all":
        cap = int(sys.argv[2])
        for name in HICAtlasDataset.KNOWN_NAMES:
            its = list(HICAtlasDataset(root=ROOT, hic_name=name))
            kk = [required_k(it.hypergraph) for it in its]
            surv = sum(1 for v in kk if v <= cap)
            nn = np.array([it.hypergraph.n_nodes for it in its])
            print(
                f"{name:18} N={len(its):5d} survive(k<={cap})={surv:5d} "
                f"({surv / len(its):.1%})  n[med={int(np.median(nn))} max={nn.max()}]"
            )
        return 0

    items = _load()
    ks = [required_k(it.hypergraph) for it in items]
    corpus_k = max(ks)
    ns = np.array([it.hypergraph.n_nodes for it in items])

    if mode == "pick":
        order = np.argsort(ns)
        print(f"dataset={NAME} N={len(items)} corpus_k={corpus_k}")
        _print_picks(
            items,
            ks,
            {
                "median": int(order[len(order) // 2]),
                "p90": int(order[int(0.90 * (len(order) - 1))]),
                "p99": int(order[int(0.99 * (len(order) - 1))]),
                "max": int(order[-1]),
            },
        )
        return 0

    if mode == "filter":
        cap = int(sys.argv[2])
        surv = [i for i, kk in enumerate(ks) if kk <= cap]
        by_class: dict[object, list[int]] = {}
        for i, it in enumerate(items):
            by_class.setdefault(it.extra.get("class_label"), []).append(i)
        print(f"cap={cap}: {len(surv)}/{len(items)} survive ({len(surv) / len(items):.1%})")
        for cls, idxs in sorted(by_class.items(), key=str):
            kept = sum(1 for i in idxs if ks[i] <= cap)
            print(f"  class={cls}: {kept}/{len(idxs)} ({kept / len(idxs):.1%})")
        sn = np.array([items[i].hypergraph.n_nodes for i in surv])
        so = np.argsort(sn)
        _print_picks(
            items,
            ks,
            {
                "median": surv[int(so[len(so) // 2])],
                "p90": surv[int(so[int(0.90 * (len(so) - 1))])],
                "p99": surv[int(so[int(0.99 * (len(so) - 1))])],
                "max": surv[int(so[-1])],
            },
        )
        return 0

    if mode in ("one", "pyprobe"):
        idx, k = int(sys.argv[2]), int(sys.argv[3])
        it = items[idx]
        H = it.hypergraph
        backend = "python" if mode == "pyprobe" else None
        t0 = time.perf_counter()
        w = canonical_string(H, k=k, backend=backend)
        dt = time.perf_counter() - t0
        tag = "PYTHON " if mode == "pyprobe" else ""
        print(
            f"{tag}idx={idx} id={it.item_id} n={H.n_nodes} m={H.n_edges} "
            f"k={k} |w|={len(w)} t={dt:.3f}s"
        )
        return 0

    if mode in ("sample", "sample-capped"):
        if mode == "sample-capped":
            cap, k, n_sample = int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
            pool = [i for i, kk in enumerate(ks) if kk <= cap]
        else:
            k, n_sample = int(sys.argv[2]), int(sys.argv[3])
            pool = list(range(len(items)))
        rng = random.Random(SEED)
        idxs = rng.sample(pool, min(n_sample, len(pool)))
        times = []
        for idx in idxs:
            H = items[idx].hypergraph
            t0 = time.perf_counter()
            canonical_string(H, k=k)
            dt = time.perf_counter() - t0
            times.append(dt)
            print(f"idx={idx} n={H.n_nodes} m={H.n_edges} t={dt:.3f}s", flush=True)
        arr = np.array(times)
        print(
            f"SAMPLE k={k} n_sample={len(idxs)} median={np.median(arr):.4f}s "
            f"mean={arr.mean():.4f}s max={arr.max():.4f}s "
            f"est_pool_total={arr.mean() * len(pool):.0f}s"
        )
        return 0

    if mode == "budget":
        import multiprocessing as mp

        cap, k, n_sample, budget_s = (
            int(sys.argv[2]),
            int(sys.argv[3]),
            int(sys.argv[4]),
            float(sys.argv[5]),
        )
        pool = [i for i, kk in enumerate(ks) if kk <= cap]
        rng = random.Random(SEED)
        idxs = rng.sample(pool, min(n_sample, len(pool)))
        ctx = mp.get_context("fork")

        def _work(idx: int, q) -> None:  # noqa: ANN001
            H = items[idx].hypergraph
            t0 = time.perf_counter()
            canonical_string(H, k=k)
            q.put(time.perf_counter() - t0)

        rows = []
        for idx in idxs:
            H = items[idx].hypergraph
            q = ctx.Queue()
            p = ctx.Process(target=_work, args=(idx, q))
            p.start()
            p.join(budget_s)
            if p.is_alive():
                p.terminate()
                p.join()
                rows.append((idx, H.n_nodes, H.n_edges, None))
            else:
                rows.append((idx, H.n_nodes, H.n_edges, q.get()))
        done = [r for r in rows if r[3] is not None]
        dnf = [r for r in rows if r[3] is None]
        times = np.array([r[3] for r in done]) if done else np.array([0.0])
        print(
            f"BUDGET cap={cap} k={k} sample={len(rows)} budget={budget_s}s: "
            f"completed {len(done)}/{len(rows)} ({len(done) / len(rows):.1%}); "
            f"t[med={np.median(times):.3f} p90={np.percentile(times, 90):.3f} "
            f"max={times.max():.3f}]s"
        )
        if dnf:
            dnf_sorted = sorted(dnf, key=lambda r: (r[1], r[2]))
            head = ", ".join(f"idx={r[0]}(n={r[1]},m={r[2]})" for r in dnf_sorted[:12])
            print(f"DNF ({len(dnf)}): {head}")
        return 0

    raise SystemExit(f"unknown mode {mode!r}")


if __name__ == "__main__":
    sys.exit(main())
