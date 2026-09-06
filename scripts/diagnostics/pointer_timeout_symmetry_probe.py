"""Are the pointer-arm time-outs driven by size or by symmetry? Join RQ1 M3 rows with |Aut|."""

from __future__ import annotations

import csv
import glob
import math
import sys
from collections import defaultdict

sys.path.insert(0, "/home/mpascual/research/code/IsalHG")

from experiments.tkde import corpora  # noqa: E402
from isalhg.core.levi_reduction import to_levi  # noqa: E402
from isalhg.iso_backends.canonical_order import _to_pynauty  # noqa: E402

ROOT = "/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE"
import pynauty  # noqa: E402


def aut_order(H) -> float:
    g = _to_pynauty(to_levi(H))
    gens, grpsize1, grpsize2, orbits, n_orbits = pynauty.autgrp(g)
    return grpsize1 * (10**grpsize2)


for name in ("ndc_classes", "wd50k66"):
    coll = corpora.load_collection(name, ROOT)
    by_id = corpora.records_by_id(coll)
    rows = []
    for path in glob.glob(f"{ROOT}/RQ1_addressing/addressing/rows_m3__*-{name}-*.csv"):
        with open(path, newline="") as fh:
            rows += [r for r in csv.DictReader(fh) if r["arm"] == "isalhg_levenshtein"]
    seen = {}
    for r in rows:
        seen.setdefault(r["member_id"], r)
    rows = list(seen.values())
    print(f"\n{name}: {len(rows)} pointer-arm members")
    cache = {}
    by_m = defaultdict(lambda: [0, 0, []])
    by_aut = defaultdict(lambda: [0, 0])
    cross = defaultdict(lambda: [0, 0])
    for r in rows:
        rec = by_id[r["member_id"]]
        H = rec.to_hypergraph(n_types=coll.n_types, n_preds=coll.n_preds)
        a = aut_order(H)
        la = min(int(math.log10(a)) if a > 1 else 0, 9)
        m = int(r["m"])
        mb = (
            "<=8"
            if m <= 8
            else "9-12"
            if m <= 12
            else "13-16"
            if m <= 16
            else "17-20"
            if m <= 20
            else ">20"
        )
        c = int(r["censored"])
        by_m[mb][0] += 1
        by_m[mb][1] += c
        if not c:
            by_m[mb][2].append(float(r["secs"]))
        by_aut[la][0] += 1
        by_aut[la][1] += c
        cross[(mb, "sym" if a >= 1e3 else "low")][0] += 1
        cross[(mb, "sym" if a >= 1e3 else "low")][1] += c
    print("  censored fraction by fact count m (and median secs of completed):")
    for mb in ("<=8", "9-12", "13-16", "17-20", ">20"):
        n, c, s = by_m[mb]
        if n:
            s.sort()
            print(
                f"    m {mb:6s} n={n:4d} censored={c / n:.2f} median_secs={s[len(s) // 2] if s else float('nan'):.3f}"
            )
    print("  censored fraction by log10 |Aut(Levi)|:")
    for la in sorted(by_aut):
        n, c = by_aut[la]
        print(f"    log10|Aut|={la} n={n:4d} censored={c / n:.2f}")
    print("  cross: m bucket x (|Aut|>=1e3 'sym' / 'low'):")
    for mb in ("<=8", "9-12", "13-16", "17-20", ">20"):
        for s in ("low", "sym"):
            n, c = cross[(mb, s)]
            if n:
                print(f"    m {mb:6s} {s}: n={n:4d} censored={c / n:.2f}")
