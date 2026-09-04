"""Full-scale E-A arm, shardable across a SLURM array.

The local probe subsamples the E-A (``w*_c``) arm because canonicalization is
the expensive encoding: E-B and E-C cost one nauty call each, E-A costs a
tie-complete branch-and-bound whose tail runs into minutes. This script
enumerates the *complete* E-A task list -- every base and every edited /
paired knowledge base of M1 (300 synthetic + 200 NDC + 200 WD50K, five edit
kinds, ten edits per kind), M2 (all 555 NDC consecutive pairs and all WD50K
ladders) and M3 -- and computes a contiguous block of it.

    python run_ea_full.py --shard 3 --nshards 24 --out <dir>

Every task is keyed by a content hash of ``(n, types, facts, k)``, so shard
outputs merge into the local probe without any index bookkeeping.

Blocks are contiguous (``tasks[lo:hi]``), not strided, so a single shard is a
coherent slice and a lost shard costs a known part of the corpus.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import time
from pathlib import Path

from f4_corpora import EDIT_KINDS, gen_synthetic, load_ndc, load_wd50k66, random_walk, sample_edits
from f4_encodings import KB
from f4_exec import map_word_A

from isalhg.core.canonical import required_k

SEED_CORPUS = 20260904
SEED_EDITS = 20260905
N_SYNTH = 300
N_REAL = 200
EDITS_PER_KIND = 10


def task_key(kb: KB, k: int) -> str:
    payload = json.dumps(
        {
            "n": kb.n,
            "types": list(kb.types),
            "facts": sorted([lab, sorted(mem)] for lab, mem in kb.facts),
            "nt": kb.n_types,
            "np": kb.n_preds,
            "k": k,
        },
        separators=(",", ":"),
    )
    return hashlib.sha1(payload.encode()).hexdigest()


def enumerate_tasks() -> list[tuple[KB, int]]:
    """Deterministic full E-A task list (same seeds as ``run_probe.py``)."""
    r = random.Random(SEED_CORPUS)
    ndc, pairs = load_ndc()
    wd = load_wd50k66()
    corpora = {
        "synthetic": gen_synthetic(2000, SEED_CORPUS)[:N_SYNTH],
        "ndc_classes_quarter": r.sample(ndc, min(N_REAL, len(ndc))),
        "wd50k66": r.sample(wd, min(N_REAL, len(wd))),
    }
    seen: set[str] = set()
    tasks: list[tuple[KB, int]] = []

    def add(kb: KB, k: int) -> None:
        key = task_key(kb, k)
        if key in seen:
            return
        seen.add(key)
        tasks.append((kb, k))

    # M1: every base and every single-edit neighbour, at the pair's k.
    rng = random.Random(SEED_EDITS)
    for kbs in corpora.values():
        for kb in kbs:
            rk = required_k(kb.to_hypergraph())
            add(kb, rk)
            for kind in EDIT_KINDS:
                for ed in sample_edits(kb, kind, EDITS_PER_KIND, rng):
                    k = max(rk, required_k(ed.to_hypergraph()))
                    add(kb, k)
                    add(ed, k)

    # M2a: all NDC consecutive encodable pairs.
    for p in pairs:
        a, b = ndc[p["i"]], ndc[p["j"]]
        k = max(required_k(a.to_hypergraph()), required_k(b.to_hypergraph()))
        add(a, k)
        add(b, k)

    # M2b: WD50K synthetic ladders t = 1..5.
    rng2 = random.Random(SEED_EDITS + 1)
    for kb in corpora["wd50k66"]:
        for t in (1, 2, 3, 4, 5):
            ed = random_walk(kb, t, rng2)
            if ed is None:
                continue
            k = max(required_k(kb.to_hypergraph()), required_k(ed.to_hypergraph()))
            add(kb, k)
            add(ed, k)
    return tasks


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--budget", type=float, default=60.0)
    ap.add_argument("--out", type=str, default=".")
    ap.add_argument("--count-only", action="store_true")
    args = ap.parse_args()

    t0 = time.time()
    tasks = enumerate_tasks()
    print(
        f"[ea] full task list: {len(tasks)} canonicalizations "
        f"(enumerated in {time.time() - t0:.1f} s)",
        flush=True,
    )
    if args.count_only:
        print(len(tasks))
        return

    n, s = len(tasks), args.shard
    q, rem = divmod(n, args.nshards)
    lo = s * q + min(s, rem)
    hi = lo + q + (1 if s < rem else 0)
    block = tasks[lo:hi]
    print(f"[ea] shard {s}/{args.nshards}: tasks [{lo}, {hi}) = {len(block)}", flush=True)

    res = map_word_A(
        block,
        budget=args.budget,
        workers=args.workers,
        progress=lambda d, m: print(f"[ea] {d}/{m}", flush=True),
    )
    out: dict[str, dict] = {}
    for (kb, k), r in zip(block, res, strict=True):
        rec = {"ok": bool(r.get("ok")), "secs": r.get("secs"), "n": kb.n, "m": kb.m}
        if r.get("ok"):
            rec["w"] = r["w"]
            rec["seed"] = r["seed"]
        else:
            rec["dnf"] = bool(r.get("dnf"))
            rec["error"] = r.get("error")
        out[task_key(kb, k)] = rec

    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    tmp = outdir / f"ea_shard_{s:04d}.json.tmp"
    tmp.write_text(json.dumps(out))
    tmp.rename(outdir / f"ea_shard_{s:04d}.json")
    ok = sum(1 for v in out.values() if v["ok"])
    dnf = sum(1 for v in out.values() if v.get("dnf"))
    print(
        f"[ea] shard {s} done: {ok} ok, {dnf} dnf, {len(out) - ok - dnf} err, "
        f"{time.time() - t0:.1f} s -> {outdir / f'ea_shard_{s:04d}.json'}",
        flush=True,
    )


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    main()
