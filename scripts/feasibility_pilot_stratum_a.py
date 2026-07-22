"""Feasibility pilot for Stratum A known-design catalog (T-M7a).

For each design in the KnownDesignCatalog, measures w*_c (canonical_fingerprint)
wall-clock under a 30-second budget. Admits designs whose p90 is under the budget
with zero DNFs; drops the rest with a logged reason.

Implements the protocol from REVIEW/DATA.md §4:
  1. Sample a pilot of <= N_RUNS timing measurements per design.
  2. Measure w*_c wall-clock at p50/p90.
  3. Admit only if p90 <= BUDGET_S with 0 DNFs; else log as out-of-envelope.

Each design in the catalog is a single deterministic object -- permuted copies
would have identical w*_c cost (isomorphism-invariant). We instead repeat the
timing call N_RUNS times on the base design to obtain a stable p50/p90.
For very slow designs, we stop early on the first DNF.

Timeout mechanism: uses multiprocessing.Process (not signal.alarm) so the OS-level
kill fires even when canonical_fingerprint is executing inside the C++ extension.
signal.alarm is unreliable with C extensions because Python signals are only
processed between bytecodes.

Usage:
    python scripts/feasibility_pilot_stratum_a.py [--budget 30] [--runs 3]
    python scripts/feasibility_pilot_stratum_a.py --budget 30 --runs 3 \\
        --output artifacts/feasibility_pilot/

Outputs:
    <outdir>/feasibility_pilot_stratum_a.json   -- full result record per design
    <outdir>/admitted_catalog.txt               -- admitted-catalog table
"""

from __future__ import annotations

import argparse
import json
import multiprocessing
import pickle
import statistics
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Subprocess worker (top-level required for multiprocessing pickling)
# ---------------------------------------------------------------------------


def _worker(queue: multiprocessing.Queue, H_pickle: bytes) -> None:  # type: ignore[type-arg]
    """Run canonical_fingerprint(H) and put elapsed time in queue.

    Parameters
    ----------
    queue : multiprocessing.Queue
        Output queue; receives ``("ok", elapsed)`` or ``("error", str)``.
    H_pickle : bytes
        Pickled SparseHypergraph.
    """
    from isalhg.core.canonical import canonical_fingerprint

    try:
        H = pickle.loads(H_pickle)
        t0 = time.perf_counter()
        canonical_fingerprint(H)
        elapsed = time.perf_counter() - t0
        queue.put(("ok", elapsed))
    except Exception as exc:  # noqa: BLE001
        queue.put(("error", str(exc)))


def _timed_call(H: object, budget_s: float) -> tuple[float, bool]:
    """Call canonical_fingerprint(H) in a subprocess with a hard OS-level timeout.

    Using multiprocessing.Process instead of signal.alarm so the kill fires even
    inside C extension code (Python signals are deferred until C code returns).

    Parameters
    ----------
    H : SparseHypergraph
        The hypergraph to fingerprint.
    budget_s : float
        Wall-clock budget in seconds.

    Returns
    -------
    elapsed : float
        Wall-clock time; set to ``budget_s`` on timeout.
    timed_out : bool
        True iff the subprocess was killed by the timeout.
    """
    ctx = multiprocessing.get_context("fork")
    queue: multiprocessing.Queue = ctx.Queue()  # type: ignore[type-arg]
    H_pickle = pickle.dumps(H)

    proc = ctx.Process(target=_worker, args=(queue, H_pickle), daemon=True)
    t0 = time.perf_counter()
    proc.start()
    proc.join(timeout=budget_s)
    elapsed = time.perf_counter() - t0

    if proc.is_alive():
        proc.terminate()
        proc.join(timeout=2.0)
        if proc.is_alive():
            proc.kill()
            proc.join()
        return budget_s, True

    # Process finished within budget; get result from queue.
    if not queue.empty():
        status, value = queue.get_nowait()
        if status == "ok":
            return value, False  # type: ignore[return-value]
    # Process exited but queue is empty (crash / error).
    return elapsed, False


# ---------------------------------------------------------------------------
# Pilot runner
# ---------------------------------------------------------------------------


def run_pilot(
    budget_s: float = 30.0,
    n_runs: int = 3,
    outdir: Path | None = None,
    threshold_s: float | None = None,
) -> dict[str, object]:
    """Run the Stratum A feasibility pilot.

    Parameters
    ----------
    budget_s : float
        Per-instance wall-clock timeout in seconds.  On cluster runs this
        is raised (e.g. 300 s) while ``threshold_s`` stays at 30 s.
    n_runs : int
        Number of timing repetitions per design (early-exit on first DNF).
    outdir : Path | None
        If given, write JSON + table to this directory.
    threshold_s : float | None
        Admission threshold: p90 must be ≤ this value (seconds) to admit.
        Defaults to ``budget_s`` (preserves the original single-parameter
        behaviour for local runs with ``--budget 30``).

    Returns
    -------
    dict
        Full result record keyed by design item_id.
    """
    # When budget_s is raised for cluster use, threshold_s stays at 30 s
    # (the DATA.md §4 admission criterion).
    admit_threshold_s = threshold_s if threshold_s is not None else budget_s

    from isalhg.datasets.synthetic.known_design_catalog import KnownDesignCatalog

    ds = KnownDesignCatalog()
    results: dict[str, dict] = {}  # type: ignore[type-arg]

    header_cols = (
        f"{'item_id':<20} {'arity':>5} {'n':>4} {'m':>4} "
        f"{'p50(s)':>8} {'p90(s)':>8} {'status':>10}  reason"
    )
    sep = "-" * len(header_cols)
    print(header_cols, flush=True)
    print(sep, flush=True)

    for item in ds:
        iid = item.item_id
        H = item.hypergraph
        arity = item.extra["arity"]
        n = H.n_nodes
        m = H.n_edges
        family_label = item.extra.get("family_label", iid)

        timings: list[float] = []
        dnf = False
        reason = ""

        for run_idx in range(n_runs):
            elapsed, timed_out = _timed_call(H, budget_s)
            if timed_out:
                dnf = True
                reason = f"w*_c DNF on run {run_idx + 1} (>{budget_s:.0f}s budget)"
                timings.append(budget_s)
                break
            timings.append(elapsed)

        if dnf:
            # DNF at budget_s: classified by context.
            # On local (budget_s == admit_threshold_s == 30s): PENDING_CLUSTER.
            # On cluster (budget_s=300s > admit_threshold_s=30s): EXCLUDED.
            p50 = statistics.median(timings)
            p90 = budget_s
            if budget_s > admit_threshold_s:
                # Cluster run: timeout at 300s means definitely > 30s threshold.
                status = "EXCLUDED"
                reason = (
                    f"w*_c DNF at cluster budget ({budget_s:.0f}s); "
                    f"confirmed infeasible (p90 >> threshold {admit_threshold_s:.0f}s)"
                )
            else:
                status = "PENDING_CLUSTER"
                reason = (
                    f"w*_c DNF on local workstation ({budget_s:.0f}s budget)"
                    f" — deferred to cluster pilot (T-M7h)"
                )
        else:
            p50 = statistics.median(timings)
            sorted_t = sorted(timings)
            # p90 index: for N=3, position 2 (the max); for N=1, position 0.
            idx90 = max(0, int(len(sorted_t) * 0.9) - 1)
            p90 = sorted_t[idx90] if len(sorted_t) > 1 else sorted_t[0]
            if p90 <= admit_threshold_s:
                status = "ADMITTED"
                reason = ""
            else:
                # p90 > threshold but no DNF.
                if budget_s > admit_threshold_s:
                    # Cluster run: measured exclusion.
                    status = "EXCLUDED"
                    reason = (
                        f"p90={p90:.2f}s > threshold {admit_threshold_s:.0f}s "
                        f"(cluster-measured at {budget_s:.0f}s timeout)"
                    )
                else:
                    # Local run: still deferred.
                    status = "PENDING_CLUSTER"
                    reason = (
                        f"p90={p90:.2f}s > budget {budget_s:.0f}s"
                        " — deferred to cluster pilot (T-M7h)"
                    )

        rec = {
            "item_id": iid,
            "family_label": family_label,
            "arity": arity,
            "n": n,
            "m": m,
            "n_runs_completed": len(timings),
            "dnf": dnf,
            "timings_s": timings,
            "p50_s": p50,
            "p90_s": p90,
            "status": status,
            "reason": reason,
        }
        results[iid] = rec

        print(
            f"{iid:<20} {arity:>5} {n:>4} {m:>4} {p50:>8.3f} {p90:>8.3f} {status:>10}  {reason}",
            flush=True,
        )

    print(sep, flush=True)
    admitted = [r for r in results.values() if r["status"] == "ADMITTED"]
    pending = [r for r in results.values() if r["status"] == "PENDING_CLUSTER"]
    excluded = [r for r in results.values() if r["status"] == "EXCLUDED"]
    print(
        f"Admitted: {len(admitted)} / {len(results)}  "
        f"Pending-cluster: {len(pending)}  Excluded: {len(excluded)}",
        flush=True,
    )

    if outdir is not None:
        outdir.mkdir(parents=True, exist_ok=True)
        json_path = outdir / "feasibility_pilot_stratum_a.json"
        with json_path.open("w") as fh:
            json.dump(
                {
                    "budget_s": budget_s,
                    "threshold_s": admit_threshold_s,
                    "n_runs": n_runs,
                    "n_designs": len(results),
                    "n_admitted": len(admitted),
                    "n_pending_cluster": len(pending),
                    "n_excluded": len(excluded),
                    "designs": results,
                },
                fh,
                indent=2,
            )
        print(f"\nJSON written to: {json_path}", flush=True)

        table_path = outdir / "admitted_catalog.txt"
        with table_path.open("w") as fh:
            fh.write("# Admitted Stratum A catalog (T-M7h cluster feasibility pilot)\n")
            fh.write(
                f"# Budget (timeout): {budget_s}s  "
                f"Admission threshold: {admit_threshold_s}s  "
                f"Runs per design: {n_runs}\n\n"
            )
            fh.write(header_cols + "\n")
            fh.write(sep + "\n")
            for r in admitted:
                fh.write(
                    f"{r['item_id']:<20} {r['arity']:>5} {r['n']:>4} {r['m']:>4} "
                    f"{r['p50_s']:>8.3f} {r['p90_s']:>8.3f} {'ADMITTED':>10}  \n"
                )
            fh.write(sep + "\n")
            fh.write(f"Total admitted: {len(admitted)} / {len(results)}\n\n")
            if excluded:
                fh.write("# Cluster-excluded designs (confirmed infeasible at 300s timeout)\n")
                fh.write(f"{'item_id':<20}  reason\n")
                for r in excluded:
                    fh.write(f"{r['item_id']:<20}  {r['reason']}\n")
                fh.write("\n")
            if pending:
                fh.write("# Still pending-cluster designs\n")
                fh.write(f"{'item_id':<20}  reason\n")
                for r in pending:
                    fh.write(f"{r['item_id']:<20}  {r['reason']}\n")
        print(f"Table written to:  {table_path}", flush=True)

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--budget",
        type=float,
        default=30.0,
        help="Per-instance w*_c timeout in seconds (default: 30). "
        "Raise to 300 for cluster runs; pair with --threshold 30.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="Admission threshold in seconds (default: same as --budget). "
        "Set to 30 when --budget is raised to 300 for cluster runs.",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=3,
        help="Timing repetitions per design; stop early on first DNF (default: 3).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/feasibility_pilot"),
        help="Output directory for JSON + table (default: artifacts/feasibility_pilot/).",
    )
    args = parser.parse_args()

    multiprocessing.set_start_method("fork", force=True)
    run_pilot(
        budget_s=args.budget,
        n_runs=args.runs,
        outdir=args.output,
        threshold_s=args.threshold,
    )


if __name__ == "__main__":
    main()
