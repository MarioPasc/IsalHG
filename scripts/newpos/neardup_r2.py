"""Radius-2 stratum of the near-neighbour retrieval task (companion of ``neardup.py``).

A non-isomorphic pair is at edit radius exactly 2 when it is not within one
single-fact edit and either (a) two down-edits turn one member into the other,
or (b) the two members share a down-neighbour (one down-edit on each side: a
delete-then-insert path, which covers relabelling one fact and moving a fact).
Pairs that need an insertion on both sides with no common down-neighbour are not
enumerated; they count as negatives for every representation alike.

A path is *pendant* when both of its steps change the constant inventory. Per
query (a member with at least one radius-2 partner), its radius-1 partners are
removed from the candidate list, and the reciprocal rank of its nearest radius-2
partner is scored for every cached distance, overall and on the pendant-only
pairs. Statistics as in ``neardup.py``.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import wilcoxon

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from neardup import (  # noqa: E402
    ARMS,
    D_ROOT,
    OURS,
    _key_fn,
    down_neighbours,
    holm,
    query_scores,
    rank_biserial,
)

from experiments.tkde import corpora as C  # noqa: E402
from isalhg.datasets.kb.base import KBRecord, compact  # noqa: E402

_STATE: dict[str, Any] = {}


def _init(collection: str) -> None:
    col = C.load_collection(collection, root=D_ROOT)
    _STATE["col"] = col
    _STATE["key"] = _key_fn("cert", col.n_types, col.n_preds)


def _downs(record: KBRecord) -> list[tuple[Any, bool, KBRecord]]:
    """``(key, pendant, record)`` of every connected down-neighbour."""
    consts = {a for _, args in record.facts for a in args}
    out = []
    for _kind, facts in down_neighbours(record):
        sub = compact(f"{record.kb_id}~", list(record.types), facts, require_connected=True)
        if sub is None:
            continue
        pendant = consts != {a for _, args in facts for a in args}
        out.append((_STATE["key"](sub), pendant, sub))
    return out


def _member(i: int) -> tuple[int, dict[Any, bool], dict[Any, bool]]:
    """Level-1 and level-2 down keys of member ``i``, each with 'reachable by pendant steps only'."""
    rec = _STATE["col"].records[i]
    d1: dict[Any, bool] = {}
    d2: dict[Any, bool] = {}
    for k1, p1, sub in _downs(rec):
        d1[k1] = d1.get(k1, False) or p1
        for k2, p2, _ in _downs(sub):
            d2[k2] = d2.get(k2, False) or (p1 and p2)
    return i, d1, d2


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--collection", required=True)
    ap.add_argument("--extra-matrix-dir", type=Path, default=None)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    t0 = time.perf_counter()
    _init(args.collection)
    col = _STATE["col"]
    N = len(col)
    keys = [_STATE["key"](r) for r in col.records]
    by_key: dict[Any, list[int]] = defaultdict(list)
    for i, k in enumerate(keys):
        by_key[k].append(i)
    iso = np.empty(N, dtype=np.int64)
    for c, ms in enumerate(by_key.values()):
        iso[ms] = c
    with ProcessPoolExecutor(args.workers, initializer=_init, initargs=(args.collection,)) as ex:
        levels = sorted(ex.map(_member, range(N), chunksize=16))
    r1: set[tuple[int, int]] = set()
    r2: dict[tuple[int, int], bool] = {}
    via: dict[Any, list[tuple[int, bool]]] = defaultdict(list)
    for i, d1, d2 in levels:
        for k, p in d1.items():
            via[k].append((i, p))
            for j in by_key.get(k, ()):
                r1.add((min(i, j), max(i, j)))
        for k, p in d2.items():
            for j in by_key.get(k, ()):
                if iso[i] != iso[j]:
                    pair = (min(i, j), max(i, j))
                    r2[pair] = r2.get(pair, False) or p
    for members in via.values():  # common down-neighbour: one down-edit on each side
        for a in range(len(members)):
            i, pi = members[a]
            for b in range(a + 1, len(members)):
                j, pj = members[b]
                if iso[i] != iso[j]:
                    pair = (min(i, j), max(i, j))
                    r2[pair] = r2.get(pair, False) or (pi and pj)
    for pair in r1:
        r2.pop(pair, None)
    r1_part: dict[int, set[int]] = defaultdict(set)
    for i, j in r1:
        r1_part[i].add(j)
        r1_part[j].add(i)
    part: dict[int, set[int]] = defaultdict(set)
    part_p: dict[int, set[int]] = defaultdict(set)
    for (i, j), p in r2.items():
        part[i].add(j)
        part[j].add(i)
        if p:
            part_p[i].add(j)
            part_p[j].add(i)
    summary: dict[str, Any] = {
        "collection": args.collection,
        "N": N,
        "radius1_pairs": len(r1),
        "radius2_pairs": len(r2),
        "radius2_pendant_pairs": int(sum(r2.values())),
        "queries": len(part),
        "queries_pendant": len(part_p),
        "arms": {},
    }
    print(json.dumps({k: v for k, v in summary.items() if k != "arms"}), flush=True)
    cls = [r.meta.get("class_id", r.kb_id) for r in col.records]
    per: dict[tuple[str, str], np.ndarray] = {}
    for arm in ARMS:
        path = D_ROOT / "matrices" / args.collection / f"{arm}.npy"
        if not path.exists() and args.extra_matrix_dir is not None:
            path = args.extra_matrix_dir / args.collection / f"{arm}.npy"
        if not path.exists():
            continue
        M = np.load(path).astype(np.float64)
        if M.shape[0] != N:
            summary["arms"][arm] = {"skipped": f"matrix covers {M.shape[0]} of {N} members"}
            continue
        M[~np.isfinite(M)] = np.inf
        res: dict[str, Any] = {}
        for sname, pmap in (("all", part), ("pendant", part_p)):
            rows = []
            for q in sorted(pmap):
                others = np.where(iso != iso[q])[0]
                drop = r1_part.get(q)
                if drop:
                    others = others[~np.isin(others, list(drop))]
                rows.append(query_scores(M[q, others], np.isin(others, list(pmap[q]))))
            arr = np.array(rows)
            per[(sname, arm)] = arr
            res[f"MRR_{sname}"] = float(arr[:, 0].mean())
            res[f"hit1_{sname}"] = float(arr[:, 1].mean())
        summary["arms"][arm] = res
    rng = np.random.default_rng(args.seed)
    tests: dict[str, Any] = {}
    for sname, pmap in (("all", part), ("pendant", part_p)):
        qs = sorted(pmap)
        qc = np.array([cls[q] for q in qs], dtype=object)
        uq = list(dict.fromkeys(qc.tolist()))
        grp = {c: np.where(qc == c)[0] for c in uq}
        boots = [
            np.concatenate([grp[uq[g]] for g in rng.integers(len(uq), size=len(uq))])
            for _ in range(args.boot)
        ]
        pv, eff, cis = {}, {}, {}
        x = per[(sname, OURS)][:, 0]
        for (s2, arm), arr in per.items():
            if s2 != sname:
                continue
            v = np.array([arr[b, 0].mean() for b in boots])
            cis[arm] = [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]
            if arm != OURS:
                pv[arm] = float(
                    wilcoxon(x, arr[:, 0], alternative="greater", zero_method="zsplit").pvalue
                )
                eff[arm] = rank_biserial(x, arr[:, 0])
        tests[sname] = {"p_holm": holm(pv), "rank_biserial": eff, "ci": cis}
    summary["tests"] = tests
    summary["secs"] = time.perf_counter() - t0
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / f"neardup_r2_{args.collection}.json").write_text(json.dumps(summary, indent=1))
    for sname in ("all", "pendant"):
        print(f"-- radius-2 stratum {sname}")
        for arm, r in summary["arms"].items():
            if "skipped" in r:
                continue
            ci = tests[sname]["ci"][arm]
            p = tests[sname]["p_holm"].get(arm)
            e = tests[sname]["rank_biserial"].get(arm)
            print(
                f"   {arm:22s}{r[f'MRR_{sname}']:7.3f} [{ci[0]:.3f},{ci[1]:.3f}]  hit@1 {r[f'hit1_{sname}']:.3f}  "
                + (f"{p:.2e}  {e:+.3f}" if p is not None else "(ours)")
            )
    print(f"elapsed {summary['secs']:.1f} s")


if __name__ == "__main__":
    main()
