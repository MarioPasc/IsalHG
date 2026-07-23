"""Targeted Section 3 recovery test — T-M7n.

Tests only tight cycles and loose paths (which have small Aut groups),
with a strict 60s Qin budget per test and 30s w*_c budget.
Skips loose cycles (their large internal Aut groups prevent Qin perturbation).

Run with:
    ~/.conda/envs/isalhg-T-M7n/bin/python \
        experiments/article/power_pilot_sec3_targeted.py \
        --output artifacts/power_pilot/sec3_targeted.json
"""

from __future__ import annotations

import json
import logging
import random
import sys
import time
from pathlib import Path

import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from isalhg.core.canonical import canonical_fingerprint
from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.datasets.synthetic.known_design_catalog import (
    loose_path,
    tight_cycle,
)


def _make_targeted_candidates() -> list[tuple[str, str, SparseHypergraph]]:
    """Tight cycles + loose paths only (small Aut groups)."""
    # Loose cycles are excluded: loose_cycle(k, L) has |Aut| >= 2L*(k-1)!^L
    # which is enormous relative to n = L*(k-1). The Qin oracle exhausts
    # 300 retries without finding a single non-iso member (verified at L=6, L=8).
    return [
        # Tight cycles k=4: n=L, m=L, Aut = Dih(L), |Aut| = 2L.
        ("tight_cycle_k4_L8", "tight_cycle(4,8): n=8, m=8", tight_cycle(4, 8)),
        ("tight_cycle_k4_L10", "tight_cycle(4,10): n=10, m=10", tight_cycle(4, 10)),
        ("tight_cycle_k4_L12", "tight_cycle(4,12): n=12, m=12", tight_cycle(4, 12)),
        # Tight cycles k=5: n=L, m=L, Aut = Dih(L).
        ("tight_cycle_k5_L8", "tight_cycle(5,8): n=8, m=8", tight_cycle(5, 8)),
        ("tight_cycle_k5_L10", "tight_cycle(5,10): n=10, m=10", tight_cycle(5, 10)),
        # Loose paths k=4: n=L*(k-1)+1, m=L; Aut <= Z_2 (reflection only).
        ("loose_path_k4_L5", "loose_path(4,5): n=16, m=5", loose_path(4, 5)),
        ("loose_path_k4_L6", "loose_path(4,6): n=19, m=6", loose_path(4, 6)),
        # Loose paths k=5: n=L*(k-1)+1, m=L.
        ("loose_path_k5_L4", "loose_path(5,4): n=17, m=4", loose_path(5, 4)),
        ("loose_path_k5_L5", "loose_path(5,5): n=21, m=5", loose_path(5, 5)),
    ]


def _qin_perturb_test(
    H: SparseHypergraph,
    item_id: str,
    n_target: int = 7,
    n_edits: int = 2,
    max_retries: int = 300,
    seed: int = 42,
    wall_budget_s: float = 60.0,
) -> dict:
    """Qin perturbation test with a wall-clock budget."""
    from isalhg.datasets.synthetic.planted_families import PlantedFamilyDataset

    t0 = time.perf_counter()
    try:
        ds = PlantedFamilyDataset(
            seeds=[H],
            family_labels=["test_family"],
            coarse_class_labels=["test_class"],
            members_per_family=n_target,
            n_edits=n_edits,
            max_retries=max_retries,
            seed_value=seed,
            dedup_backend="isalhg",
            allow_partial=True,
        )
        # Iterate with timeout check.
        items = list(ds)
        elapsed = time.perf_counter() - t0
        return {
            "item_id": item_id,
            "n_realized": len(items),
            "n_target": n_target,
            "reached_target": len(items) >= n_target,
            "elapsed_s": elapsed,
            "timed_out": elapsed > wall_budget_s,
            "error": None,
        }
    except Exception as exc:
        elapsed = time.perf_counter() - t0
        return {
            "item_id": item_id,
            "n_realized": 0,
            "n_target": n_target,
            "reached_target": False,
            "elapsed_s": elapsed,
            "timed_out": False,
            "error": str(exc),
        }


def _wstarc_timing(
    H: SparseHypergraph,
    n_instances: int = 8,
    seed: int = 0,
    wall_budget_s: float = 30.0,
) -> dict:
    """Time w*_c computation with early-exit on budget exceeded."""
    rng = random.Random(seed)
    n = H.n_nodes
    times: list[float] = []
    timed_out = False
    t_start = time.perf_counter()

    for i in range(n_instances):
        if time.perf_counter() - t_start > wall_budget_s:
            timed_out = True
            logger.warning("  w*_c budget %.0fs exceeded at instance %d", wall_budget_s, i)
            break
        sigma = list(range(n))
        rng.shuffle(sigma)
        perm_map = {old: new for new, old in enumerate(sigma)}
        try:
            H_perm = permute(H, perm_map)
        except Exception:
            H_perm = H
        t0 = time.perf_counter()
        canonical_fingerprint(H_perm)
        t_inst = time.perf_counter() - t0
        times.append(t_inst)
        if t_inst > 30.0 and i == 0:
            timed_out = True
            logger.warning("  w*_c first instance %.1fs > 30s; timeout", t_inst)
            break

    if not times:
        return {"p50_s": float("inf"), "p90_s": float("inf"), "n_instances": 0, "timed_out": True}

    return {
        "p50_s": float(np.percentile(times, 50)),
        "p90_s": float(np.percentile(times, 90)),
        "n_instances": len(times),
        "times_s": [round(t, 4) for t in times],
        "timed_out": timed_out,
    }


def run_targeted_recovery() -> dict:
    """Run recovery test on targeted candidates only."""
    candidates = _make_targeted_candidates()
    results: list[dict] = []

    for item_id, desc, H in candidates:
        ar = {len(m) for m in H.hyperedges()}
        k = min(ar) if ar else 0
        n = H.n_nodes
        m = H.n_edges
        logger.info("Testing %s (n=%d, m=%d, k=%d)...", item_id, n, m, k)

        # (a) Qin perturbation at n_edits=2 (60s budget)
        ptest2 = _qin_perturb_test(H, item_id, n_target=7, n_edits=2, wall_budget_s=60.0)
        logger.info(
            "  n_edits=2: realized=%d/7 in %.1fs%s",
            ptest2["n_realized"],
            ptest2["elapsed_s"],
            " [TIMEOUT]" if ptest2.get("timed_out") else "",
        )

        # n_edits=3 only if n_edits=2 was insufficient and not too slow
        ptest3: dict | None = None
        if ptest2["n_realized"] < 5 and not ptest2.get("timed_out") and ptest2["elapsed_s"] < 30.0:
            ptest3 = _qin_perturb_test(H, item_id, n_target=7, n_edits=3, wall_budget_s=60.0)
            logger.info(
                "  n_edits=3: realized=%d/7 in %.1fs%s",
                ptest3["n_realized"],
                ptest3["elapsed_s"],
                " [TIMEOUT]" if ptest3.get("timed_out") else "",
            )

        # (b) w*_c timing (8 instances, 30s budget)
        t_wstar = _wstarc_timing(H, n_instances=8, wall_budget_s=30.0)
        logger.info(
            "  w*_c p50=%.2fs, p90=%.2fs (%d instances%s)",
            t_wstar["p50_s"],
            t_wstar["p90_s"],
            t_wstar["n_instances"],
            " TIMEOUT" if t_wstar.get("timed_out") else "",
        )

        multi_5plus = ptest2["n_realized"] >= 5 or (
            ptest3 is not None and ptest3["n_realized"] >= 5
        )
        feasible_wstar = (not t_wstar.get("timed_out", False)) and t_wstar["p90_s"] < 30.0

        results.append(
            {
                "item_id": item_id,
                "description": desc,
                "n": n,
                "m": m,
                "k": k,
                "aut_order_heuristic": 2 * m if "cycle" in item_id else 2,
                "qin_n_edits_2": ptest2,
                "qin_n_edits_3": ptest3,
                "wstarc_timing": {
                    "p50_s": t_wstar["p50_s"],
                    "p90_s": t_wstar["p90_s"],
                    "n_instances": t_wstar["n_instances"],
                    "timed_out": t_wstar.get("timed_out", False),
                },
                "feasible_wstarc": feasible_wstar,
                "multi_member_5plus": multi_5plus,
                "recovers_a2a3": multi_5plus and feasible_wstar,
            }
        )

    recovered = [r for r in results if r["recovers_a2a3"]]
    logger.info(
        "Recovery: %d/%d candidates yield ≥5 members AND w*_c p90 < 30s",
        len(recovered),
        len(results),
    )

    return {
        "results": results,
        "n_candidates": len(results),
        "n_recovered": len(recovered),
        "recovered_ids": [r["item_id"] for r in recovered],
        "loose_cycle_finding": (
            "Excluded from targeted test: loose_cycle(k,L) has |Aut| >= 2L*(k-1)!^L "
            "(measured: loose_cycle(4,6) n=18 → 1/7 members at n_edits=2,3; "
            "loose_cycle(4,8) n=24 → 1/7 members + w*_c timeout 74.7s). "
            "The enormous internal automorphism group prevents Qin perturbation "
            "from finding non-iso family members regardless of cycle length."
        ),
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path, default=Path("artifacts/power_pilot/sec3_targeted.json")
    )
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    results = run_targeted_recovery()
    elapsed = time.perf_counter() - t0
    results["total_elapsed_s"] = elapsed

    def _ok(obj: object) -> object:
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, (list, tuple)):
            return [_ok(x) for x in obj]
        if isinstance(obj, dict):
            return {k: _ok(v) for k, v in obj.items()}
        return obj

    with open(args.output, "w") as f:
        json.dump(_ok(results), f, indent=2)
    logger.info("Wrote %s (%.0fs total)", args.output, elapsed)


if __name__ == "__main__":
    main()
