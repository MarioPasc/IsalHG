"""Merge Picasso cluster results into the Stratum B feasibility envelope.

After the T-M7h array job completes on Picasso, rsync the per-block result
JSONs from the cluster to a local directory, then run this script to update
``experiments/article/stratum_b_feasibility_envelope.json`` with
cluster-measured p50/p90 and final admitted/excluded decisions.

Usage
-----
Merge Stratum B per-block results::

    python scripts/T-M7h_merge_envelope.py \\
        --stratum-b-dir /media/.../results/T-M7h/stratum_b/per_block/ \\
        --envelope experiments/article/stratum_b_feasibility_envelope.json \\
        [--dry-run]

Merge Stratum A cluster result::

    python scripts/T-M7h_merge_envelope.py \\
        --stratum-a-json /media/.../results/T-M7h/stratum_a/feasibility_pilot_stratum_a.json \\
        --stratum-a-artifacts artifacts/feasibility_pilot/ \\
        [--dry-run]

Both may be combined in one call.  The script is idempotent: re-running
after additional blocks arrive only patches those blocks.

Admission criterion (DATA.md §4)
---------------------------------
Stratum B: ``p90 ≤ 30 s AND n_timeout == 0 AND n_error == 0`` over 30 instances.
Stratum A: ``p90 ≤ 30 s AND dnf == False`` (status == "ADMITTED" from the cluster run).
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

# ---------------------------------------------------------------------------
# Stratum B merge
# ---------------------------------------------------------------------------


def _merge_stratum_b(
    stratum_b_dir: Path,
    envelope_path: Path,
    dry_run: bool,
) -> None:
    """Patch per-block cluster results into the main feasibility envelope.

    Parameters
    ----------
    stratum_b_dir : Path
        Directory containing per-block JSONs written by the SLURM workers
        (one file per block, named ``block_<BLOCK_KEY>.json`` or the
        path passed to ``--output`` in ``feasibility_pilot.py``).
    envelope_path : Path
        Path to ``stratum_b_feasibility_envelope.json``.
    dry_run : bool
        If True, print what would change but do not write.
    """
    with envelope_path.open() as fh:
        envelope: dict = json.load(fh)

    # Index existing block_results by block_key for O(1) lookup.
    by_key: dict[str, dict] = {r["block_key"]: r for r in envelope.get("block_results", [])}

    block_jsons = sorted(stratum_b_dir.glob("*.json"))
    if not block_jsons:
        print(f"[merge_stratum_b] No JSON files found in {stratum_b_dir}")
        return

    patched = 0
    for jpath in block_jsons:
        with jpath.open() as fh:
            data: dict = json.load(fh)

        # A per-block output contains a "block_results" list with one entry.
        block_results: list[dict] = data.get("block_results", [])
        if not block_results:
            print(f"  [skip] {jpath.name}: no block_results key")
            continue

        for result in block_results:
            bkey = result.get("block_key")
            if not bkey:
                print(f"  [skip] entry without block_key in {jpath.name}")
                continue

            if bkey not in by_key:
                print(f"  [new]  {bkey}: not in envelope, appending")
                by_key[bkey] = result
                patched += 1
                continue

            old = by_key[bkey]
            old_status = old.get("local_status", "unknown")
            new_admitted = result.get("admitted", False)
            new_status = "admitted" if new_admitted else "cluster_excluded"

            if dry_run:
                print(
                    f"  [dry]  {bkey}: {old_status} → {new_status} "
                    f"(p50={result.get('p50_ms')} p90={result.get('p90_ms')} "
                    f"n_pilot={result.get('n_pilot')})"
                )
            else:
                print(
                    f"  [patch] {bkey}: {old_status} → {new_status} "
                    f"(p50={result.get('p50_ms')} p90={result.get('p90_ms')} "
                    f"n_pilot={result.get('n_pilot')})"
                )

            # Merge cluster measurements into the existing entry.
            merged = dict(old)
            merged.update(
                {
                    "cluster_p50_ms": result.get("p50_ms"),
                    "cluster_p90_ms": result.get("p90_ms"),
                    "cluster_n_pilot": result.get("n_pilot"),
                    "cluster_n_ok": result.get("n_ok"),
                    "cluster_n_timeout": result.get("n_timeout"),
                    "cluster_times_ms": result.get("times_ms", []),
                    "cluster_status": new_status,
                    "admitted": new_admitted,
                    "local_status": new_status,
                    "cluster_reason": result.get("reason", ""),
                }
            )
            by_key[bkey] = merged
            patched += 1

    if dry_run:
        print(f"[dry_run] Would patch {patched} blocks.")
        return

    # Rebuild envelope with updated block_results.
    envelope["block_results"] = list(by_key.values())

    # Update admitted_block_keys and pending_cluster.
    admitted_keys = [r["block_key"] for r in by_key.values() if r.get("admitted")]
    still_pending = [
        {"block_key": r["block_key"], "reason": r.get("cluster_reason", r.get("reason", ""))}
        for r in by_key.values()
        if r.get("local_status") == "pending_cluster"
    ]
    cluster_excluded = [
        {"block_key": r["block_key"], "reason": r.get("cluster_reason", "")}
        for r in by_key.values()
        if r.get("cluster_status") == "cluster_excluded"
    ]

    envelope["admitted_block_keys"] = admitted_keys
    envelope["pending_cluster"] = still_pending
    envelope["cluster_excluded"] = cluster_excluded

    # Update summary.
    summary = envelope.get("summary", {})
    summary["n_locally_admitted"] = sum(
        1 for r in by_key.values() if r.get("local_status") == "admitted"
    )
    summary["n_cluster_admitted"] = sum(
        1 for r in by_key.values() if r.get("cluster_status") == "admitted"
    )
    summary["n_cluster_excluded"] = len(cluster_excluded)
    summary["n_pending_cluster_measurement"] = len(still_pending)
    envelope["summary"] = summary

    # Atomic write.
    tmp = envelope_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(envelope, indent=2), encoding="utf-8")
    tmp.replace(envelope_path)
    print(f"[merge_stratum_b] Patched {patched} blocks → {envelope_path}")


# ---------------------------------------------------------------------------
# Stratum A merge
# ---------------------------------------------------------------------------


def _merge_stratum_a(
    cluster_json: Path,
    artifacts_dir: Path,
    dry_run: bool,
) -> None:
    """Update Stratum A artifacts with cluster-measured results.

    Parameters
    ----------
    cluster_json : Path
        ``feasibility_pilot_stratum_a.json`` written by the cluster job.
    artifacts_dir : Path
        Local ``artifacts/feasibility_pilot/`` directory to update.
    dry_run : bool
        If True, print what would change but do not write.
    """
    with cluster_json.open() as fh:
        cluster_data: dict = json.load(fh)

    local_json = artifacts_dir / "feasibility_pilot_stratum_a.json"
    if local_json.exists():
        with local_json.open() as fh:
            local_data: dict = json.load(fh)
    else:
        local_data = {}

    cluster_designs: dict = cluster_data.get("designs", {})
    local_designs: dict = local_data.get("designs", {})

    for iid, crec in cluster_designs.items():
        old_status = local_designs.get(iid, {}).get("status", "UNKNOWN")
        new_status = crec.get("status", "UNKNOWN")
        if dry_run:
            print(
                f"  [dry]  {iid}: {old_status} → {new_status} "
                f"(p50={crec.get('p50_s'):.3f}s p90={crec.get('p90_s'):.3f}s)"
            )
        else:
            print(
                f"  [patch] {iid}: {old_status} → {new_status} "
                f"(p50={crec.get('p50_s'):.3f}s p90={crec.get('p90_s'):.3f}s)"
            )

    if dry_run:
        print(f"[dry_run] Would update {artifacts_dir} from {cluster_json}")
        return

    # Copy the cluster result JSON over the local one.
    dest_json = artifacts_dir / "feasibility_pilot_stratum_a.json"
    shutil.copy2(cluster_json, dest_json)
    print(f"[merge_stratum_a] Copied cluster JSON → {dest_json}")

    # Regenerate admitted_catalog.txt from the cluster result.
    admitted = [r for r in cluster_designs.values() if r.get("status") == "ADMITTED"]
    excluded = [r for r in cluster_designs.values() if r.get("status") == "EXCLUDED"]
    pending = [r for r in cluster_designs.values() if r.get("status") == "PENDING_CLUSTER"]

    header_cols = (
        f"{'item_id':<20} {'arity':>5} {'n':>4} {'m':>4} "
        f"{'p50(s)':>8} {'p90(s)':>8} {'status':>10}  reason"
    )
    sep = "-" * len(header_cols)

    table_path = artifacts_dir / "admitted_catalog.txt"
    with table_path.open("w") as fh:
        fh.write("# Admitted Stratum A catalog (T-M7h cluster feasibility pilot)\n")
        fh.write(
            f"# Budget (timeout): {cluster_data.get('budget_s')}s  "
            f"Threshold: {cluster_data.get('threshold_s')}s  "
            f"Runs: {cluster_data.get('n_runs')}\n\n"
        )
        fh.write(header_cols + "\n")
        fh.write(sep + "\n")
        for r in admitted:
            fh.write(
                f"{r['item_id']:<20} {r['arity']:>5} {r['n']:>4} {r['m']:>4} "
                f"{r['p50_s']:>8.3f} {r['p90_s']:>8.3f} {'ADMITTED':>10}  \n"
            )
        fh.write(sep + "\n")
        fh.write(f"Total admitted: {len(admitted)} / {len(cluster_designs)}\n\n")
        if excluded:
            fh.write("# Cluster-excluded (confirmed infeasible at 300s timeout)\n")
            fh.write(f"{'item_id':<20}  reason\n")
            for r in excluded:
                fh.write(f"{r['item_id']:<20}  {r['reason']}\n")
            fh.write("\n")
        if pending:
            fh.write("# Still pending-cluster\n")
            fh.write(f"{'item_id':<20}  reason\n")
            for r in pending:
                fh.write(f"{r['item_id']:<20}  {r['reason']}\n")

    print(f"[merge_stratum_a] Updated admitted_catalog.txt → {table_path}")
    print(f"  Admitted: {len(admitted)}  Excluded: {len(excluded)}  Still pending: {len(pending)}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__.splitlines()[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--stratum-b-dir",
        type=Path,
        default=None,
        help="Directory of per-block Stratum B cluster JSONs.",
    )
    p.add_argument(
        "--envelope",
        type=Path,
        default=Path("experiments/article/stratum_b_feasibility_envelope.json"),
        help="Path to stratum_b_feasibility_envelope.json (default: repo default).",
    )
    p.add_argument(
        "--stratum-a-json",
        type=Path,
        default=None,
        help="Path to feasibility_pilot_stratum_a.json from the cluster job.",
    )
    p.add_argument(
        "--stratum-a-artifacts",
        type=Path,
        default=Path("artifacts/feasibility_pilot"),
        help="Local artifacts/feasibility_pilot/ directory to update.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would change without writing files.",
    )
    return p.parse_args()


def main() -> int:
    args = _parse_args()

    if args.stratum_b_dir is None and args.stratum_a_json is None:
        print("ERROR: provide at least one of --stratum-b-dir or --stratum-a-json")
        return 1

    if args.stratum_b_dir is not None:
        if not args.stratum_b_dir.is_dir():
            print(f"ERROR: --stratum-b-dir does not exist: {args.stratum_b_dir}")
            return 1
        if not args.envelope.exists():
            print(f"ERROR: --envelope does not exist: {args.envelope}")
            return 1
        print(f"\n=== Stratum B merge: {args.stratum_b_dir} → {args.envelope} ===")
        _merge_stratum_b(args.stratum_b_dir, args.envelope, args.dry_run)

    if args.stratum_a_json is not None:
        if not args.stratum_a_json.exists():
            print(f"ERROR: --stratum-a-json does not exist: {args.stratum_a_json}")
            return 1
        print(f"\n=== Stratum A merge: {args.stratum_a_json} → {args.stratum_a_artifacts} ===")
        _merge_stratum_a(args.stratum_a_json, args.stratum_a_artifacts, args.dry_run)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
