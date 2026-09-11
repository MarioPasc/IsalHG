"""Decompose the per-member identity cost into the shared call and what follows.

RQ2 step 5 (the L17/R6 concession) was first quoted as a *multiple* — "the Isal
word costs 1.77x a nauty certificate". `[IsalHG-Fable]` observed that
``nauty_cert``, ``nauty_cert_rows`` and ``isal_ow_struct`` all make the **same**
canonical-labelling call on the same coloured Levi graph and differ only in what
they do afterwards, so a multiple between them hides a shared term nobody has
measured. Timing the bare call turns the multiple into a quantity: *the language
costs X ms on top of a call every arm in the comparison pays anyway.*

Two design points, both learned the hard way in this session:

* **Medians, not means.** The per-member figure from the N-scaling pass is
  ``total / N``. On ``wstar_orbit`` that mean is 622x its own median, so it
  describes an ``N``-member corpus rather than a member. Both are printed, and
  the divergence between them is itself reported.
* **One machine.** Absolute milliseconds are not portable: the same arm on the
  same code path costs 2.3x more on the cluster than on a workstation. This
  script is meant to run **on the cluster**, so its numbers sit beside the
  campaign's rather than needing a caveat.

This is **characterisation** (D-ART5 decision 2): it writes no census row and
must never supply one.
"""

from __future__ import annotations

import random
import statistics
import sys
import time
from collections.abc import Callable, Sequence
from typing import Any

SAMPLE = 200
SEED = 70000
COLLECTION = "wd50k66"

# Every arm below issues the same canonical-labelling call; the difference is
# what each does with the result. That is what makes the subtraction meaningful.
ARMS = ("nauty_cert", "nauty_cert_rows", "fact_rank", "isal_ow_struct", "wstar_orbit")


def _per_member(fn: Callable[[Any], Any], items: Sequence[Any]) -> dict[str, float]:
    """Time ``fn`` once per member, returning the distribution rather than a total."""
    times = []
    for item in items:
        start = time.perf_counter()
        fn(item)
        times.append((time.perf_counter() - start) * 1000.0)
    ordered = sorted(times)
    last = len(ordered) - 1
    return {
        "median": statistics.median(times),
        "mean": statistics.fmean(times),
        "p90": ordered[int(0.90 * last)],
        "p99": ordered[int(0.99 * last)],
        "max": max(times),
    }


def main() -> None:
    print(__doc__)
    from experiments.tkde import corpora as corpora_io
    from isalhg.iso_backends.canonical_order import canonical_ranks
    from isalhg.metric_space.registry import get_distance

    collection = corpora_io.load_collection(COLLECTION)
    graphs = corpora_io.hypergraphs(collection)
    rng = random.Random(SEED)
    items = [graphs[i] for i in rng.sample(range(len(graphs)), SAMPLE)]
    print(
        f"host: {__import__('platform').node()}  |  {COLLECTION}, {SAMPLE} members, seed {SEED}\n"
    )

    shared = _per_member(canonical_ranks, items)
    results = {"canonical_ranks (SHARED)": shared}
    for arm in ARMS:
        results[arm] = _per_member(get_distance(arm).fingerprint, items)

    print(f"  {'arm':28s} {'median':>10s} {'mean':>11s} {'p90':>10s} {'p99':>11s} {'max':>11s}")
    for name, r in results.items():
        print(
            f"  {name:28s} {r['median']:10.4f} {r['mean']:11.4f} "
            f"{r['p90']:10.4f} {r['p99']:11.3f} {r['max']:11.3f}"
        )

    print(f"\n  on top of the shared call (median {shared['median']:.4f} ms):")
    for arm in ARMS:
        delta = results[arm]["median"] - shared["median"]
        print(
            f"    {arm:22s} +{delta:8.4f} ms   "
            f"({results[arm]['median'] / shared['median']:5.2f}x the shared call)"
        )

    print("\n  mean/median divergence (a heavy tail hides inside a mean):")
    for name, r in results.items():
        ratio = r["mean"] / r["median"] if r["median"] else float("nan")
        flag = "  <- mean does not describe a member" if ratio > 2 else ""
        print(f"    {name:28s} {ratio:8.1f}x{flag}")


if __name__ == "__main__":
    sys.exit(main())
