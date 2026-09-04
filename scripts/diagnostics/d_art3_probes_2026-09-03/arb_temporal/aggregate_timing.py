"""Render timing.json as the report's task-5 table.

One row per (dataset, m-bucket); the labelled and unlabelled measurements share
the row as ``labelled / unlabelled`` columns.
"""

from __future__ import annotations

import json
import os
from collections import defaultdict

import arb_temporal_lib as L
import numpy as np

with open(os.path.join(L.OUT, "timing.json")) as fh:
    R = json.load(fh)
BUCKETS = ["1-10", "11-30", "31-60", "61-110"]

by = defaultdict(list)
for r in R:
    by[(r["dataset"], r["mode"], r["bucket"])].append(r)
datasets = [n for n in L.PRIORITY if any(r["dataset"] == n for r in R)]


def q(rs, p, key="secs", nd=4):
    a = [r[key] for r in rs if r["status"] == "ok"]
    return f"{np.percentile(a, p):.{nd}f}" if a else "-"


def counts(rs):
    ok = sum(1 for r in rs if r["status"] == "ok")
    dnf = sum(1 for r in rs if r["status"] == "dnf")
    sk = sum(1 for r in rs if str(r["status"]).startswith("skipped"))
    er = sum(1 for r in rs if r["status"] in ("error", "crash"))
    return ok, dnf, sk, er


print(
    "| dataset | gran | bucket | N | med n | med m | med s L/U | p90 s L/U | DNF L/U | skip L/U | med tokens L/U |"
)
print("|---|---|---|---|---|---|---|---|---|---|---|")
for ds in datasets:
    for b in BUCKETS:
        lab, unl = by.get((ds, "labelled", b)), by.get((ds, "unlabelled", b))
        if not lab:
            continue
        ol, dl, sl, _ = counts(lab)
        ou, du, su, _ = counts(unl)
        print(
            f"| {ds} | {lab[0]['granularity']} | {b} | {len(lab)} | "
            f"{np.median([r['n'] for r in lab]):.0f} | {np.median([r['m'] for r in lab]):.0f} | "
            f"{q(lab, 50)} / {q(unl, 50)} | {q(lab, 90)} / {q(unl, 90)} | "
            f"{dl}/{len(lab)} · {du}/{len(unl)} | {sl} · {su} | "
            f"{q(lab, 50, 'tokens', 0)} / {q(unl, 50, 'tokens', 0)} |"
        )

print()
paired = defaultdict(dict)
for r in R:
    if r["status"] == "ok":
        paired[(r["dataset"], r["node"], r["window"])][r["mode"]] = r["secs"]
both = [(v["unlabelled"], v["labelled"]) for v in paired.values() if len(v) == 2]
if both:
    sp = np.array([u / max(lb, 1e-9) for u, lb in both])
    print(
        f"Paired completions (both modes finished): N={len(both)}; median speedup "
        f"unlabelled/labelled = **{np.median(sp):.2f}x**; labelled faster in "
        f"{int((sp > 1).sum())}/{len(both)}; aggregate {sum(u for u, _ in both):.1f} s "
        f"vs {sum(lb for _, lb in both):.1f} s."
    )
