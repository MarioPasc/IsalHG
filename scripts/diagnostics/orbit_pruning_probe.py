"""Does stabiliser-orbit pruning buy what the proof says it buys?

Four measurements, each answering one question the design record poses.

``branch-table``
    The collapse. On a star with ``q`` interchangeable leaves the unpruned
    tie-complete search walks every injective placement sequence
    (``sum_d q!/(q-d)!``); the pruning proposition predicts ``q+1`` states and
    ``O(q)`` oracle calls. Both engines are run and both counts printed, with
    the emitted strings compared so the collapse is not bought with a value
    change.

``star20``
    The absolute cost. A 20-leaf star is out of reach for the unpruned search
    by many orders of magnitude; the pruned one should finish in seconds. The
    time is split between oracle calls and the rest of the search so a slow
    result says *where* it is slow.

``censored-tail``
    Hypothesis H-M3, second half: does the pruned engine complete more of the
    ``|Aut| >= 10^3`` members than the C++ engine does at 60 s? The members are
    exactly those the RQ1 M3 rows record as censored for the pointer arm, taken
    highest ``|Aut|`` first, and the completion fraction is reported per
    ``|Aut|`` bucket. A negative result is a result.

``rank-timing``
    Cost of the ``canonical_rank`` arm: the 20-leaf star and the median over
    ``wd50k66`` members.

Every timed run goes through ``experiments.tkde.budget.run_with_budget``: the
Python search does not return on ``SIGALRM``, so a censored run has to be
killed in a forked child.
"""

from __future__ import annotations

import argparse
import csv
import glob
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from isalhg.core.canonical import canonical_string  # noqa: E402
from isalhg.core.hypergraph_to_string import _python_greedy_h2s  # noqa: E402
from isalhg.core.levi_reduction import to_levi  # noqa: E402
from isalhg.core.sparse_hypergraph import SparseHypergraph  # noqa: E402
from isalhg.iso_backends.canonical_order import _to_pynauty  # noqa: E402
from isalhg.iso_backends.orbit_oracle import (  # noqa: E402
    PynautyOrbitOracle,
    canonical_string_orbit,
    canonical_string_rank,
)

DEFAULT_RESULTS_ROOT = "/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE"
BUDGET_S = 60.0


def star(q: int) -> SparseHypergraph:
    """Hub ``0`` with ``q`` interchangeable leaves, one binary fact each."""
    return SparseHypergraph(n_nodes=q + 1, hyperedges=[frozenset({0, i}) for i in range(1, q + 1)])


def aut_order(H: SparseHypergraph) -> float:
    """``|Aut(B(H))|`` via pynauty, as a float (the groups overflow ``int`` sizes)."""
    import pynauty

    _gens, size1, size2, _orbits, _n = pynauty.autgrp(_to_pynauty(to_levi(H)))
    return float(size1) * (10.0**size2)


# ---------------------------------------------------------------------------
# branch-table
# ---------------------------------------------------------------------------


def cmd_branch_table(args: argparse.Namespace) -> None:
    """Unpruned vs pruned frame and branch counts on symmetric stars."""
    print("star with q interchangeable leaves; k=2, seed=hub, tie_branch=True")
    print(
        f"{'q':>3} {'frames_unpr':>12} {'vbr_unpr':>12} {'s_unpr':>9} "
        f"{'frames_pr':>10} {'vbr_pr':>7} {'oracle':>7} {'autgrp':>7} {'s_pr':>8} {'equal':>6}"
    )
    for q in args.q:
        H = star(q)
        unpruned: dict[str, int] = {}
        start = time.perf_counter()
        w_unpruned = _python_greedy_h2s(
            H, seed_node=0, k=2, inplace=True, tie_branch=True, stats=unpruned
        )
        secs_unpruned = time.perf_counter() - start

        pruned: dict[str, int] = {}
        oracle = PynautyOrbitOracle()
        start = time.perf_counter()
        w_pruned = _python_greedy_h2s(
            H,
            seed_node=0,
            k=2,
            inplace=True,
            tie_branch=True,
            orbit_oracle=oracle,
            stats=pruned,
        )
        secs_pruned = time.perf_counter() - start
        print(
            f"{q:>3} {unpruned['frames']:>12,} {unpruned.get('v_branches', 0):>12,} "
            f"{secs_unpruned:>9.3f} {pruned['frames']:>10,} "
            f"{pruned.get('v_branches', 0):>7,} {pruned.get('oracle_calls', 0):>7,} "
            f"{oracle.autgrp_calls:>7,} {secs_pruned:>8.3f} "
            f"{'yes' if w_pruned == w_unpruned else 'NO':>6}"
        )


# ---------------------------------------------------------------------------
# star20
# ---------------------------------------------------------------------------


class _TimingOracle:
    """Wrap an oracle and accumulate the wall-clock it consumes."""

    def __init__(self, inner: Any) -> None:
        self.inner = inner
        self.secs = 0.0

    def _timed(self, name: str, *args: Any) -> Any:
        start = time.perf_counter()
        out = getattr(self.inner, name)(*args)
        self.secs += time.perf_counter() - start
        return out

    def seed_representatives(self, H: Any, seeds: Any) -> Any:
        return self._timed("seed_representatives", H, seeds)

    def edge_representatives(self, H: Any, placed: Any, tied: Any) -> Any:
        return self._timed("edge_representatives", H, placed, tied)

    def ordering_representatives(self, H: Any, placed: Any, edge: Any, orderings: Any) -> Any:
        return self._timed("ordering_representatives", H, placed, edge, orderings)


def cmd_star20(args: argparse.Namespace) -> None:
    """Absolute cost of the pruned engine on a highly symmetric star."""
    for q in args.q:
        H = star(q)
        inner = PynautyOrbitOracle()
        oracle = _TimingOracle(inner)
        stats: dict[str, int] = {}
        start = time.perf_counter()
        tokens = _python_greedy_h2s(
            H,
            seed_node=0,
            k=2,
            inplace=True,
            tie_branch=True,
            orbit_oracle=oracle,
            stats=stats,
        )
        total = time.perf_counter() - start
        print(
            f"q={q:>3} |Aut(B(H))|={aut_order(H):.3g} total={total:.3f}s "
            f"oracle={oracle.secs:.3f}s ({100 * oracle.secs / total:.0f}%) "
            f"search={total - oracle.secs:.3f}s "
            f"frames={stats['frames']} autgrp={inner.autgrp_calls} tokens={len(tokens)}"
        )


# ---------------------------------------------------------------------------
# censored-tail
# ---------------------------------------------------------------------------


def _censored_member_ids(root: str, collection: str) -> list[str]:
    """``kb_id`` of every member the RQ1 M3 rows mark censored for the pointer arm."""
    censored: dict[str, bool] = {}
    pattern = f"{root}/RQ1_addressing/addressing/rows_m3__*-{collection}-*.csv"
    for path in glob.glob(pattern):
        with open(path, newline="") as handle:
            for row in csv.DictReader(handle):
                if row["arm"] != "isalhg_levenshtein":
                    continue
                censored.setdefault(row["member_id"], bool(int(row["censored"])))
    return [member for member, was_censored in censored.items() if was_censored]


def _bucket(aut: float) -> str:
    if aut < 1e3:
        return "<1e3"
    if aut < 1e7:
        return "1e3-1e7"
    return ">=1e7"


def _orbit_payload(H: SparseHypergraph) -> str:
    return canonical_string_orbit(H)


def cmd_censored_tail(args: argparse.Namespace) -> None:
    """Completion fraction of the pruned engine on the C++ engine's censored tail."""
    from experiments.tkde import corpora
    from experiments.tkde.budget import run_with_budget

    collection = corpora.load_collection(args.collection, args.root)
    by_id = corpora.records_by_id(collection)
    ids = _censored_member_ids(args.root, args.collection)
    if not ids:
        print(f"no censored rows found for {args.collection!r} under {args.root}")
        return
    scored: list[tuple[float, str, SparseHypergraph]] = []
    for member_id in ids:
        record = by_id.get(member_id)
        if record is None:
            continue
        H = record.to_hypergraph()
        scored.append((aut_order(H), member_id, H))
    scored.sort(key=lambda row: -row[0])
    scored = scored[: args.limit]
    print(
        f"{args.collection}: {len(ids)} members censored by the C++ engine at 60 s; "
        f"probing the {len(scored)} with the highest |Aut| at {args.budget:.0f} s"
    )

    per_bucket: dict[str, list[float]] = defaultdict(list)
    totals: dict[str, int] = defaultdict(int)
    for aut, member_id, H in scored:
        bucket = _bucket(aut)
        totals[bucket] += 1
        value, secs, censored = run_with_budget(_orbit_payload, (H,), seconds=args.budget)
        if not censored and value is not None:
            per_bucket[bucket].append(secs)
        if args.verbose:
            state = "censored" if censored else f"{secs:.2f}s"
            print(f"  {member_id:<28} n={H.n_nodes:>3} m={H.n_edges:>3} |Aut|={aut:.3g} {state}")

    print(f"{'|Aut| bucket':>12} {'n':>5} {'completed':>10} {'fraction':>9} {'median_s':>9}")
    for bucket in ("<1e3", "1e3-1e7", ">=1e7"):
        n = totals[bucket]
        if not n:
            continue
        done = per_bucket[bucket]
        median = statistics.median(done) if done else float("nan")
        print(f"{bucket:>12} {n:>5} {len(done):>10} {len(done) / n:>9.2f} {median:>9.3f}")
    total_n = sum(totals.values())
    total_done = sum(len(v) for v in per_bucket.values())
    if total_n:
        print(f"{'ALL':>12} {total_n:>5} {total_done:>10} {total_done / total_n:>9.2f}")


# ---------------------------------------------------------------------------
# rank-timing
# ---------------------------------------------------------------------------


def _rank_payload(H: SparseHypergraph) -> str:
    return canonical_string_rank(H)


def _cpp_payload(H: SparseHypergraph) -> str:
    return canonical_string(H, algorithm="canonical", backend="cpp")


def cmd_rank_timing(args: argparse.Namespace) -> None:
    """Cost of the ``canonical_rank`` arm on the star and on a corpus sample."""
    import random

    from experiments.tkde import corpora
    from experiments.tkde.budget import run_with_budget

    for q in args.q:
        H = star(q)
        start = time.perf_counter()
        canonical_string_rank(H, k=2)
        print(f"canonical_rank on a {q}-leaf star: {1000 * (time.perf_counter() - start):.1f} ms")

    collection = corpora.load_collection(args.collection, args.root)
    members = corpora.hypergraphs(collection)
    rng = random.Random(args.seed)
    if len(members) > args.limit:
        members = rng.sample(members, args.limit)
    rank_ms: list[float] = []
    cpp_ms: list[float] = []
    rank_censored = 0
    for H in members:
        value, secs, censored = run_with_budget(_rank_payload, (H,), seconds=args.budget)
        if censored or value is None:
            rank_censored += 1
        else:
            rank_ms.append(1000 * secs)
        value, secs, censored = run_with_budget(_cpp_payload, (H,), seconds=args.budget)
        if not censored and value is not None:
            cpp_ms.append(1000 * secs)
    print(
        f"{args.collection}: {len(members)} members; canonical_rank median "
        f"{statistics.median(rank_ms):.1f} ms over {len(rank_ms)} completed "
        f"({rank_censored} censored); C++ w*_c median "
        f"{statistics.median(cpp_ms):.1f} ms over {len(cpp_ms)} completed"
    )


# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p_table = sub.add_parser("branch-table", help="unpruned vs pruned branch counts on stars")
    p_table.add_argument("--q", type=int, nargs="+", default=[5, 6, 7, 8])
    p_table.set_defaults(func=cmd_branch_table)

    p_star = sub.add_parser("star20", help="pruned-engine cost on a large symmetric star")
    p_star.add_argument("--q", type=int, nargs="+", default=[20])
    p_star.set_defaults(func=cmd_star20)

    p_tail = sub.add_parser("censored-tail", help="pruned engine on the C++ engine's censored tail")
    p_tail.add_argument("--collection", default="wd50k66")
    p_tail.add_argument("--root", default=DEFAULT_RESULTS_ROOT)
    p_tail.add_argument("--limit", type=int, default=100)
    p_tail.add_argument("--budget", type=float, default=BUDGET_S)
    p_tail.add_argument("--verbose", action="store_true")
    p_tail.set_defaults(func=cmd_censored_tail)

    p_rank = sub.add_parser("rank-timing", help="canonical_rank cost")
    p_rank.add_argument("--collection", default="wd50k66")
    p_rank.add_argument("--root", default=DEFAULT_RESULTS_ROOT)
    p_rank.add_argument("--q", type=int, nargs="+", default=[20])
    p_rank.add_argument("--limit", type=int, default=300)
    p_rank.add_argument("--budget", type=float, default=BUDGET_S)
    p_rank.add_argument("--seed", type=int, default=20260906)
    p_rank.set_defaults(func=cmd_rank_timing)

    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
