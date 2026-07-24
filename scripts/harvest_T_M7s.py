"""T-M7s — harvest and acceptance check for SLURM array 1640910 (S=27 sweep).

This script runs after the array reaches a terminal state.  It:

1. Reads the SLURM terminal-state census from a sacct TSV (produced by
   ``sacct -j 1640910 --format=JobID,State,ExitCode,Elapsed --noheader
   --parsable2``).
2. Loads all per-seed ``seed_metrics`` JSONs from the local results root
   (rsync'd from Picasso).
3. Re-aggregates with ALL available dist_names in one pass, producing complete
   BCa CI + Wilcoxon + Holm stats per cell.  The SLURM per-task aggregation
   was partial (each task only had its own dist in memory), so this step is
   required.
4. Verifies the five acceptance clauses declared in T-M7s:
   - (AC1) Terminal-state census recorded (completed / timeout / OOM / failed
     per cell × representation).
   - (AC2) Every emitted A1/A2/A3/G1/bits table cell carries a 95% BCa CI.
   - (AC3) Every competitor-vs-IsalHG comparison carries a Holm-corrected p
     and an effect size.
   - (AC4) Per-arity A2/A3 populated for arities 3, 4, 5 on Stratum A with
     no phantom arity group.
   - (AC5) Geometry-vs-axis curves have ≥3 values with error bands; the axis
     coverage is stated (arity axis may be < 3 from Stratum B alone).
5. Writes ``artifacts/T-M7d-harvest/harvest_summary.json`` for T-M8f to cite.

Usage::

    python scripts/harvest_T_M7s.py \\
        --results-root /media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/T-M7d \\
        --sacct-tsv /tmp/sacct_1640910.tsv \\
        --envelope experiments/article/stratum_b_feasibility_envelope.json \\
        --artifact-dir artifacts/T-M7d-harvest \\
        --n-seeds 27

To generate the sacct TSV on Picasso::

    sacct -j 1640910 --format=JobID,State,ExitCode,Elapsed --noheader \\
        --parsable2 > /tmp/sacct_1640910.tsv
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from experiments.article.analysis.sweep_multi_seed import CellStats

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# SLURM census helpers
# ---------------------------------------------------------------------------

# Expected cell × dist_name pairs (11 × 7 = 77 tasks).
_STRATUM_A_KEY = "stratum_a"

_ALL_DISTANCES = [
    "isalhg_levenshtein",
    "hypergraph_wl_l1",
    "netlsd_l2",
    "hpd_jsd",
    "nauty_levi_edit",
    "degree_seq_l1",
    "hypercot",
]

_PRIMARY_REPR = "isalhg_levenshtein"

# HyperCOT is gated at runtime (n > 12 or n_corpus > 20).
_HYPERCOT_DIST = "hypercot"


def parse_sacct_tsv(tsv_path: Path) -> dict[str, str]:
    """Parse ``sacct --parsable2`` output for array tasks.

    Returns a mapping ``{task_id: state}`` where ``task_id`` is the array
    element id (e.g. ``"1640910_42"``).  Only parent-task rows are included
    (batch/extern sub-steps are filtered out).

    Parameters
    ----------
    tsv_path : Path
        Path to the sacct TSV (``--parsable2`` format, header stripped).

    Returns
    -------
    dict[str, str]
        Map from task id string to SLURM state string.
    """
    states: dict[str, str] = {}
    with open(tsv_path) as fh:
        for line in fh:
            parts = line.strip().split("|")
            if len(parts) < 2:
                continue
            job_id, state = parts[0].strip(), parts[1].strip()
            # Skip batch/extern sub-steps.
            if ".batch" in job_id or ".extern" in job_id:
                continue
            states[job_id] = state
    return states


def build_task_census(
    pairs_file: Path,
    sacct_states: dict[str, str],
    array_id: int,
) -> list[dict[str, Any]]:
    """Map SLURM task indices to (cell_key, dist_name) pairs and states.

    Parameters
    ----------
    pairs_file : Path
        The ``T-M7d_pairs.txt`` file (one ``cell_key dist_name`` per line).
    sacct_states : dict
        Output of :func:`parse_sacct_tsv`.
    array_id : int
        The SLURM array job ID (e.g. 1640910).

    Returns
    -------
    list[dict]
        One entry per (cell_key, dist_name) pair with keys
        ``cell_key``, ``dist_name``, ``task_idx``, ``state``.
    """
    census: list[dict[str, Any]] = []
    with open(pairs_file) as fh:
        for idx, line in enumerate(fh):
            parts = line.strip().split()
            if len(parts) < 2:
                continue
            cell_key, dist_name = parts[0], parts[1]
            task_id = f"{array_id}_{idx}"
            state = sacct_states.get(task_id, "UNKNOWN")
            census.append(
                {
                    "task_idx": idx,
                    "task_id": task_id,
                    "cell_key": cell_key,
                    "dist_name": dist_name,
                    "state": state,
                }
            )
    return census


_TERMINAL_STATES: frozenset[str] = frozenset(
    {"COMPLETED", "TIMEOUT", "FAILED", "NODE_FAIL", "CANCELLED", "OUT_OF_MEMORY"}
)


def summarise_census(
    census: list[dict[str, Any]],
) -> dict[str, Any]:
    """Count states and identify non-completed tasks.

    Parameters
    ----------
    census : list[dict]
        Output of :func:`build_task_census`.

    Returns
    -------
    dict
        Keys: ``total``, ``completed``, ``timeout``, ``failed``,
        ``oom``, ``other``, ``non_completed_tasks``, ``has_non_terminal``.

        ``has_non_terminal`` is ``True`` when any task has a transient state
        (RUNNING, COMPLETING, PENDING, …) that means the array has not yet
        fully settled.  Harvest should only be final when this is ``False``.
    """
    counts: dict[str, int] = defaultdict(int)
    non_completed: list[dict[str, Any]] = []
    has_non_terminal = False

    for entry in census:
        state = entry["state"]
        if state == "COMPLETED":
            counts["completed"] += 1
        elif state == "TIMEOUT":
            counts["timeout"] += 1
            non_completed.append(entry)
        elif state in ("FAILED", "NODE_FAIL", "CANCELLED"):
            counts["failed"] += 1
            non_completed.append(entry)
        elif state == "OUT_OF_MEMORY":
            counts["oom"] += 1
            non_completed.append(entry)
        else:
            # RUNNING, COMPLETING, PENDING, or unknown — not yet terminal.
            counts["other"] += 1
            non_completed.append(entry)
            if state not in _TERMINAL_STATES:
                has_non_terminal = True

    return {
        "total": len(census),
        "completed": counts["completed"],
        "timeout": counts["timeout"],
        "failed": counts["failed"],
        "oom": counts["oom"],
        "other": counts["other"],
        "non_completed_tasks": non_completed,
        "has_non_terminal": has_non_terminal,
    }


# ---------------------------------------------------------------------------
# Seed-metrics loader (cache-only; imports from sweep_multi_seed)
# ---------------------------------------------------------------------------


def load_all_seed_metrics(
    results_root: Path,
    cell_key: str,
    stratum: str,
    n_seeds: int,
    dist_names: list[str],
) -> dict[str, list[Any]]:
    """Load all cached seed_metrics for one cell.

    Returns a mapping ``{dist_name: [SeedMetrics, ...]}`` for each dist that
    has at least one cached seed.  Missing seeds are silently omitted (counted
    in the gap report).

    Parameters
    ----------
    results_root : Path
        Local results root (after rsync).
    cell_key : str
        Cell identifier (``"stratum_a"`` or a B block key).
    stratum : str
        ``"a"`` or ``"b"``.
    n_seeds : int
        Declared seed count.
    dist_names : list[str]
        All expected dist_names.

    Returns
    -------
    dict[str, list[SeedMetrics]]
        Mapping dist_name → list of loaded SeedMetrics (may be < n_seeds).
    """
    from experiments.article.analysis.sweep_multi_seed import _load_seed_metrics_cache

    by_dist: dict[str, list[Any]] = {d: [] for d in dist_names}
    for dist_name in dist_names:
        for seed in range(n_seeds):
            sm = _load_seed_metrics_cache(cell_key, stratum, dist_name, seed, results_root)
            if sm is not None:
                by_dist[dist_name].append(sm)
    # Drop dists with zero seeds.
    return {d: v for d, v in by_dist.items() if v}


def count_seed_gaps(
    results_root: Path,
    cell_key: str,
    stratum: str,
    n_seeds: int,
    dist_names: list[str],
) -> dict[str, int]:
    """Return the number of missing seeds per dist_name for one cell.

    Parameters
    ----------
    results_root : Path
        Local results root.
    cell_key : str
        Cell key.
    stratum : str
        Stratum identifier.
    n_seeds : int
        Declared seed count.
    dist_names : list[str]
        Expected dist_names.

    Returns
    -------
    dict[str, int]
        Missing-seed count per dist_name (0 = all present).
    """
    from experiments.article.analysis.sweep_multi_seed import _load_seed_metrics_cache

    gaps: dict[str, int] = {}
    for dist_name in dist_names:
        missing = 0
        for seed in range(n_seeds):
            sm = _load_seed_metrics_cache(cell_key, stratum, dist_name, seed, results_root)
            if sm is None:
                missing += 1
        gaps[dist_name] = missing
    return gaps


# ---------------------------------------------------------------------------
# Full re-aggregation pass
# ---------------------------------------------------------------------------


def reaggregate_cell(
    results_root: Path,
    cell_key: str,
    stratum: str,
    n_seeds: int,
    dist_names: list[str],
    block_meta: dict[str, Any] | None = None,
) -> CellStats:
    """Load all seed_metrics and compute full BCa CI + Wilcoxon + Holm stats.

    Parameters
    ----------
    results_root : Path
        Local results root.
    cell_key : str
        Cell identifier.
    stratum : str
        ``"a"`` or ``"b"``.
    n_seeds : int
        Declared seed count.
    dist_names : list[str]
        All expected dist_names.
    block_meta : dict or None
        Block metadata for Stratum B.

    Returns
    -------
    CellStats
        Fully aggregated stats.
    """
    from experiments.article.analysis.sweep_multi_seed import aggregate_cell_stats

    all_seed_metrics = load_all_seed_metrics(results_root, cell_key, stratum, n_seeds, dist_names)
    logger.info(
        "Cell %r: loaded %d dist(s) from cache.",
        cell_key,
        len(all_seed_metrics),
    )
    return aggregate_cell_stats(
        cell_key=cell_key,
        stratum=stratum,
        all_seed_metrics=all_seed_metrics,
        n_seeds=n_seeds,
        block_meta=block_meta,
    )


# ---------------------------------------------------------------------------
# Acceptance clause verifiers
# ---------------------------------------------------------------------------


def verify_ac2_ci_coverage(
    cell_stats: CellStats,
    min_reps: int = 1,
) -> dict[str, Any]:
    """AC2 — every emitted table cell carries a 95% BCa CI.

    A CI entry is considered valid when both ``ci_lower`` and ``ci_upper``
    are present and not NaN.

    Parameters
    ----------
    cell_stats : CellStats
        Aggregated stats for one cell.
    min_reps : int
        Minimum number of representations expected (default 1).

    Returns
    -------
    dict
        Keys: ``n_ci_entries``, ``n_ci_valid`` (non-NaN),
        ``n_reps_with_ci``, ``pass``.
    """
    import math

    cis = cell_stats.cis
    valid_count = 0
    reps_seen: set[str] = set()
    for _key, row in cis.items():
        lo = row.get("ci_lower", float("nan"))
        hi = row.get("ci_upper", float("nan"))
        if not math.isnan(lo) and not math.isnan(hi):
            valid_count += 1
        reps_seen.add(row.get("repr", ""))

    ok = len(cis) > 0 and valid_count == len(cis) and len(reps_seen) >= min_reps
    return {
        "n_ci_entries": len(cis),
        "n_ci_valid": valid_count,
        "n_reps_with_ci": len(reps_seen),
        "pass": ok,
    }


def verify_ac3_wilcoxon_coverage(
    cell_stats: CellStats,
    expected_competitors: list[str] | None = None,
) -> dict[str, Any]:
    """AC3 — every competitor vs IsalHG has Holm-corrected p and effect size.

    Parameters
    ----------
    cell_stats : CellStats
        Aggregated stats for one cell.
    expected_competitors : list[str] or None
        List of expected competitor dist_names.  If None, derived from
        ``cell_stats.wilcoxon`` keys.

    Returns
    -------
    dict
        Keys: ``n_wilcoxon_entries``, ``n_complete`` (have p_holm +
        effect_size), ``competitors_found``, ``pass``.
    """
    wilcoxon = cell_stats.wilcoxon
    if expected_competitors is None:
        comps_found = set()
        for key in wilcoxon:
            # key format: "{dist_name}::{metric_id}"
            parts = key.split("::", 1)
            if parts:
                comps_found.add(parts[0])
        competitors_found = sorted(comps_found)
    else:
        competitors_found = list(expected_competitors)

    complete_count = 0
    for _key, row in wilcoxon.items():
        if "p_holm" in row and "effect_size" in row:
            complete_count += 1

    ok = len(wilcoxon) > 0 and complete_count == len(wilcoxon)
    return {
        "n_wilcoxon_entries": len(wilcoxon),
        "n_complete": complete_count,
        "competitors_found": competitors_found,
        "pass": ok,
    }


def verify_multi_rep_wilcoxon_populated(cell_stats: CellStats) -> dict[str, Any]:
    """Check that a CellStats with ≥2 representations has a non-empty wilcoxon dict.

    A stats file with ≥2 representations but an empty ``wilcoxon`` indicates the
    per-task pipeline bug: each SLURM task only saw one representation at a time
    so the Wilcoxon/Holm step never fired.

    Parameters
    ----------
    cell_stats : CellStats
        Aggregated stats object to inspect.

    Returns
    -------
    dict
        Keys: ``n_reps`` (distinct repr names found in cis), ``wilcoxon_empty``
        (bool), ``pass`` (False when n_reps ≥ 2 and wilcoxon is empty).
    """
    reps_seen: set[str] = set()
    for row in cell_stats.cis.values():
        reps_seen.add(row["repr"])
    n_reps = len(reps_seen)
    wilcoxon_empty = len(cell_stats.wilcoxon) == 0
    return {
        "n_reps": n_reps,
        "wilcoxon_empty": wilcoxon_empty,
        "pass": not (n_reps >= 2 and wilcoxon_empty),
    }


def verify_excluded_cells_no_isalhg_comparison(
    cell_stats_map: dict[str, CellStats],
    excluded_cell_keys: set[str],
) -> dict[str, Any]:
    """Check that excluded cells carry no IsalHG comparison in their wilcoxon dict.

    Cells where ``isalhg_levenshtein`` timed out are excluded whole-cell from
    IsalHG comparative analysis.  Their ``wilcoxon`` dict must be empty —
    any non-empty entry means partial seed data was used despite the exclusion
    policy.

    Parameters
    ----------
    cell_stats_map : dict[str, CellStats]
        Mapping of cell_key → CellStats for cells to audit.
    excluded_cell_keys : set[str]
        Cell keys that should have no IsalHG comparison.

    Returns
    -------
    dict
        Keys: ``violations`` (list of cell_key strings that have a non-empty
        wilcoxon despite being excluded), ``pass``.
    """
    violations: list[str] = []
    for cell_key, cs in cell_stats_map.items():
        if cell_key in excluded_cell_keys and cs.wilcoxon:
            violations.append(cell_key)
    return {
        "violations": sorted(violations),
        "pass": len(violations) == 0,
    }


def verify_ac4_per_arity(
    results_root: Path,
    n_seeds: int,
    expected_arities: tuple[int, ...] = (3, 4, 5),
    sample_seed: int = 0,
) -> dict[str, Any]:
    """AC4 — per-arity A2/A3 populated for arities 3, 4, 5 on Stratum A.

    Reads the seed_metrics JSON for isalhg_levenshtein on seed 0 (spot-check
    per T-M7d closing note — confirmed by the orchestrator on the running array).

    Parameters
    ----------
    results_root : Path
        Local results root.
    n_seeds : int
        Declared seed count.
    expected_arities : tuple[int]
        Arity values that must have entries in a2_per_arity / a3_per_arity.
    sample_seed : int
        Seed to inspect.

    Returns
    -------
    dict
        Keys: ``a2_per_arity_keys``, ``a3_per_arity_keys``,
        ``phantom_arities``, ``missing_arities``, ``pass``.
    """
    cache_path = (
        results_root
        / "seed_metrics"
        / "a"
        / "stratum_a"
        / f"seed{sample_seed}"
        / "isalhg_levenshtein.json"
    )
    if not cache_path.exists():
        return {
            "a2_per_arity_keys": [],
            "a3_per_arity_keys": [],
            "phantom_arities": [],
            "missing_arities": list(expected_arities),
            "pass": False,
            "error": f"cache file not found: {cache_path}",
        }

    with open(cache_path) as fh:
        data = json.load(fh)

    a2_keys = [int(k) for k in data.get("a2_per_arity", {})]
    a3_keys = [int(k) for k in data.get("a3_per_arity", {})]
    expected_set = set(expected_arities)
    phantom = sorted(set(a2_keys) - expected_set)
    missing = sorted(expected_set - set(a2_keys))

    # Verify a2a3_dropped_coarse_classes uses expected arities only.
    dropped_raw = data.get("a2a3_dropped_coarse_classes", {})
    dropped_arities = [int(k) for k in dropped_raw]
    dropped_phantom = sorted(set(dropped_arities) - expected_set)

    ok = len(missing) == 0 and len(phantom) == 0 and len(dropped_phantom) == 0
    return {
        "a2_per_arity_keys": sorted(a2_keys),
        "a3_per_arity_keys": sorted(a3_keys),
        "phantom_arities": phantom,
        "missing_arities": missing,
        "a2a3_dropped_coarse_classes_keys": sorted(set(dropped_arities)),
        "pass": ok,
    }


def verify_ac5_axis_coverage(
    b_blocks: list[dict[str, Any]],
    stats_dir: Path,
    b_agg_stats: list[CellStats] | None = None,
) -> dict[str, Any]:
    """AC5 — geometry-vs-axis curves have ≥3 values with error bands.

    Axis values are derived from the admitted Stratum B blocks.  The arity
    axis may have fewer than 3 values from Stratum B alone (measured outcome,
    not a failure to hide).

    Parameters
    ----------
    b_blocks : list[dict]
        Admitted Stratum B blocks, each with keys ``n``, ``k``,
        ``density_ratio``.  Must already be filtered to IsalHG-complete cells.
    stats_dir : Path
        Directory containing per-cell stats JSONs (used only when
        ``b_agg_stats`` is not provided).
    b_agg_stats : list[CellStats] or None
        Pre-loaded, fully re-aggregated stats for each block in
        ``b_blocks`` (same order).  When provided, avoids reading stale
        per-task partial stats files from disk.

    Returns
    -------
    dict
        Keys: ``n_values``, ``density_values``, ``arity_values``,
        ``n_axis_ok`` (≥3), ``density_axis_ok`` (≥3), ``arity_axis_ok`` (≥3),
        ``all_cells_have_ci``, ``pass``.
    """
    import math

    n_vals = sorted({b["n"] for b in b_blocks})
    k_vals = sorted({b["k"] for b in b_blocks})
    rho_vals = sorted({b["density_ratio"] for b in b_blocks})

    # Check that every cell has at least one non-NaN CI.
    all_have_ci = True
    if b_agg_stats is not None:
        # Use in-memory re-aggregated stats (preferred; avoids stale files).
        for b_stats in b_agg_stats:
            cis = b_stats.cis
            if not cis:
                all_have_ci = False
                continue
            has_valid = any(
                not math.isnan(row.get("ci_lower", float("nan")))
                and not math.isnan(row.get("ci_upper", float("nan")))
                for row in cis.values()
            )
            if not has_valid:
                all_have_ci = False
    else:
        # Fallback: read per-task stats files from disk.
        for b in b_blocks:
            bkey = b.get("block_key", "")
            stats_path = stats_dir / f"{bkey}_stats.json"
            if not stats_path.exists():
                all_have_ci = False
                logger.warning("Missing stats file: %s", stats_path)
                continue
            with open(stats_path) as fh:
                stats = json.load(fh)
            cis = stats.get("cis", {})
            if not cis:
                all_have_ci = False
                continue
            has_valid = any(
                not math.isnan(row.get("ci_lower", float("nan")))
                and not math.isnan(row.get("ci_upper", float("nan")))
                for row in cis.values()
            )
            if not has_valid:
                all_have_ci = False

    n_ok = len(n_vals) >= 3
    rho_ok = len(rho_vals) >= 3
    k_ok = len(k_vals) >= 3  # may be False — Stratum B only has k=3, k=5

    return {
        "n_values": n_vals,
        "density_values": rho_vals,
        "arity_values": k_vals,
        "n_axis_ok": n_ok,
        "density_axis_ok": rho_ok,
        "arity_axis_ok": k_ok,
        "arity_axis_note": (
            "Stratum B only admitted k∈{3,5}; k-axis has 2 points from Stratum B. "
            "Per-arity Stratum A breakdown covers k∈{3,4,5} (3 points) but "
            "applies to application metrics (A2/A3), not the geometry sweep curve."
            if not k_ok
            else "k-axis ≥3 satisfied."
        ),
        "all_cells_have_ci": all_have_ci,
        "pass": n_ok and rho_ok and all_have_ci,
        # Note: arity axis < 3 is a measured outcome of the Stratum B
        # admission envelope; we do not gate the overall pass on it.
    }


# ---------------------------------------------------------------------------
# Atomic write helpers
# ---------------------------------------------------------------------------


def _atomic_write_json(path: Path, data: object) -> None:
    import contextlib

    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp.json")
    try:
        with os.fdopen(fd, "w") as fh:
            json.dump(data, fh, indent=2)
        os.replace(tmp, path)
    except Exception:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


# ---------------------------------------------------------------------------
# Harvest decision
# ---------------------------------------------------------------------------


def compute_harvest_decision(
    ac2: dict[str, Any],
    ac3: dict[str, Any],
    ac4: dict[str, Any],
    ac5: dict[str, Any],
    census_summary: dict[str, Any],
) -> tuple[bool, list[str]]:
    """Compute the overall acceptance decision and enumerate shortfalls.

    A shortfall is a named criterion that did not pass.  ``all_pass`` is
    ``True`` only when ``shortfalls`` is empty and all per-AC ``pass``
    sub-fields are ``True``.

    The arity-axis shortfall (``ac5_arity_axis``) is real — it means the
    geometry-vs-arity sweep has only 2 points from Stratum B, below the ≥3
    requirement.  That is a consequence of the Stratum B admission envelope
    (k=4 blocks timed out; k=7/10 measured infeasible), not an oversight to
    paper over.  The Stratum A per-arity breakdown covers k∈{3,4,5} for A2/A3
    but is not the geometry sweep curve; the two objects are distinct.

    A non-terminal census (``census_non_terminal``) means the sacct snapshot
    was captured while at least one task was still RUNNING/COMPLETING.  The
    artifact must not claim finality when the array has not settled.

    Parameters
    ----------
    ac2 : dict
        Output of :func:`verify_ac2_ci_coverage`.
    ac3 : dict
        Output of :func:`verify_ac3_wilcoxon_coverage`.
    ac4 : dict
        Output of :func:`verify_ac4_per_arity`.
    ac5 : dict
        Output of :func:`verify_ac5_axis_coverage`.
    census_summary : dict
        Output of :func:`summarise_census`.

    Returns
    -------
    tuple[bool, list[str]]
        ``(all_pass, shortfalls)`` where ``shortfalls`` is a list of
        criterion identifiers that did not pass.
    """
    shortfalls: list[str] = []

    if census_summary.get("has_non_terminal", False):
        shortfalls.append("census_non_terminal")
    if not ac5.get("arity_axis_ok", True):
        shortfalls.append("ac5_arity_axis")

    all_pass = ac2["pass"] and ac3["pass"] and ac4["pass"] and ac5["pass"] and not shortfalls
    return all_pass, shortfalls


# ---------------------------------------------------------------------------
# Main harvest orchestration
# ---------------------------------------------------------------------------


def harvest(
    results_root: Path,
    sacct_tsv: Path | None,
    envelope_path: Path,
    artifact_dir: Path,
    n_seeds: int = 27,
    array_id: int = 1640910,
    pairs_file: Path | None = None,
    isalhg_timeout_cells_override: set[str] | None = None,
) -> dict[str, Any]:
    """Run the full T-M7s harvest and acceptance check.

    Parameters
    ----------
    results_root : Path
        Local results root (rsync'd from Picasso).
    sacct_tsv : Path or None
        ``sacct --parsable2`` TSV for array ``array_id``.  If None, the
        census is skipped (UNKNOWN state for all tasks).
    envelope_path : Path
        Local stratum_b_feasibility_envelope.json.
    artifact_dir : Path
        Where to write ``harvest_summary.json``.
    n_seeds : int
        Declared seed count (S=27).
    array_id : int
        SLURM array job ID.
    pairs_file : Path or None
        The launcher pairs file (``T-M7d_pairs.txt``).  Used only when
        ``sacct_tsv`` is provided.
    isalhg_timeout_cells_override : set[str] or None
        If provided, overrides the census-derived timeout detection.  Use
        when the sacct TSV is unavailable but the known timeout cells must
        be carried (e.g. local re-aggregation after the array has settled).
        The three S=27 cells are: ``er_uniform_k3_n16_rho4``,
        ``er_uniform_k3_n24_rho2``, ``er_uniform_k5_n8_rho2``.

    Returns
    -------
    dict
        Full harvest summary (also written to ``artifact_dir``).
    """
    from experiments.article.analysis.sweep_multi_seed import (
        load_admitted_stratum_b_blocks,
    )

    logger.info("=== T-M7s harvest (array %d, S=%d) ===", array_id, n_seeds)

    # ------------------------------------------------------------------ #
    # AC1 — terminal-state census                                          #
    # ------------------------------------------------------------------ #
    if sacct_tsv is not None and sacct_tsv.exists() and pairs_file is not None:
        sacct_states = parse_sacct_tsv(sacct_tsv)
        census_entries = build_task_census(pairs_file, sacct_states, array_id)
        census_summary = summarise_census(census_entries)
        logger.info(
            "Census: %d total, %d COMPLETED, %d TIMEOUT, %d FAILED, %d OOM, %d other.",
            census_summary["total"],
            census_summary["completed"],
            census_summary["timeout"],
            census_summary["failed"],
            census_summary["oom"],
            census_summary["other"],
        )
    else:
        census_entries = []
        census_summary = {"total": 0, "note": "sacct_tsv or pairs_file not provided"}

    # Identify B cells where the primary repr (isalhg_levenshtein) timed out.
    # These cells are excluded from IsalHG comparative analysis (whole-cell
    # exclusion per T-M7s policy; partial seed data is present but not used).
    if isalhg_timeout_cells_override is not None:
        # Caller supplied the known timeout cells directly (e.g. when the
        # sacct TSV is unavailable but the exclusion policy must be carried).
        isalhg_timeout_b_cells: set[str] = isalhg_timeout_cells_override
        logger.info(
            "IsalHG TIMEOUT cells provided via override (%d): %s.",
            len(isalhg_timeout_b_cells),
            sorted(isalhg_timeout_b_cells),
        )
    else:
        isalhg_timeout_b_cells = {
            entry["cell_key"]
            for entry in census_summary.get("non_completed_tasks", [])
            if entry.get("dist_name") == _PRIMARY_REPR and entry.get("cell_key") != _STRATUM_A_KEY
        }
    if isalhg_timeout_b_cells:
        logger.warning(
            "IsalHG TIMEOUT on %d B cell(s): %s.  These cells are excluded from "
            "isalhg comparative analysis.",
            len(isalhg_timeout_b_cells),
            sorted(isalhg_timeout_b_cells),
        )

    # ------------------------------------------------------------------ #
    # Load Stratum B blocks                                                #
    # ------------------------------------------------------------------ #
    b_blocks_raw = load_admitted_stratum_b_blocks(envelope_path)
    b_blocks_meta = [
        {
            "block_key": b.block_key,
            "n": b.n,
            "k": b.k,
            "density_ratio": b.density_ratio,
        }
        for b in b_blocks_raw
    ]

    # ------------------------------------------------------------------ #
    # Re-aggregation: Stratum A                                            #
    # ------------------------------------------------------------------ #
    logger.info("Re-aggregating Stratum A (all 7 dists, S=%d)…", n_seeds)
    a_stats = reaggregate_cell(
        results_root,
        cell_key="stratum_a",
        stratum="a",
        n_seeds=n_seeds,
        dist_names=_ALL_DISTANCES,
    )
    # Persist fully-aggregated stats (BCa CIs + Wilcoxon + Holm) back to disk.
    # The SLURM per-task files only captured one dist at a time, so wilcoxon
    # was never computed there; this write makes the on-disk files authoritative.
    from experiments.article.analysis.sweep_multi_seed import write_cell_stats

    _a_stats_path = results_root / "stats" / "stratum_a_stats.json"
    write_cell_stats(a_stats, _a_stats_path)
    logger.info("Stratum A: stats written to %s.", _a_stats_path)

    # ------------------------------------------------------------------ #
    # Re-aggregation: Stratum B                                            #
    # ------------------------------------------------------------------ #
    b_agg_stats: list[Any] = []
    for b in b_blocks_raw:
        # HyperCOT is excluded for Stratum B (n_corpus=60 > HYPERCOT_MAX_CORPUS=20).
        b_dists_base = [d for d in _ALL_DISTANCES if d != _HYPERCOT_DIST]
        if b.block_key in isalhg_timeout_b_cells:
            # Whole-cell exclusion: isalhg_levenshtein timed out; exclude it
            # from re-aggregation so no partial-seed CI is emitted.
            b_dists = [d for d in b_dists_base if d != _PRIMARY_REPR]
            logger.warning(
                "Cell %r: IsalHG TIMEOUT — excluding %s from re-aggregation.",
                b.block_key,
                _PRIMARY_REPR,
            )
        else:
            b_dists = b_dists_base
        logger.info(
            "Re-aggregating %s (n=%d, k=%d, rho=%.1f, %d dists)…",
            b.block_key,
            b.n,
            b.k,
            b.density_ratio,
            len(b_dists),
        )
        b_stats = reaggregate_cell(
            results_root,
            cell_key=b.block_key,
            stratum="b",
            n_seeds=n_seeds,
            dist_names=b_dists,
            block_meta={"n": b.n, "k": b.k, "density_ratio": b.density_ratio},
        )
        b_agg_stats.append(b_stats)
        _b_stats_path = results_root / "stats" / f"{b.block_key}_stats.json"
        write_cell_stats(b_stats, _b_stats_path)
        logger.info("Block %s: stats written to %s.", b.block_key, _b_stats_path)

    # ------------------------------------------------------------------ #
    # AC2 — BCa CI coverage (Stratum A)                                   #
    # ------------------------------------------------------------------ #
    ac2 = verify_ac2_ci_coverage(a_stats, min_reps=len(_ALL_DISTANCES))
    logger.info(
        "AC2 CI coverage: %d entries, %d valid, pass=%s",
        ac2["n_ci_entries"],
        ac2["n_ci_valid"],
        ac2["pass"],
    )

    # ------------------------------------------------------------------ #
    # AC3 — Wilcoxon coverage (Stratum A)                                 #
    # ------------------------------------------------------------------ #
    ac3 = verify_ac3_wilcoxon_coverage(a_stats)
    logger.info(
        "AC3 Wilcoxon: %d entries, %d complete, pass=%s",
        ac3["n_wilcoxon_entries"],
        ac3["n_complete"],
        ac3["pass"],
    )

    # ------------------------------------------------------------------ #
    # AC4 — per-arity breakdown                                           #
    # ------------------------------------------------------------------ #
    ac4 = verify_ac4_per_arity(results_root, n_seeds)
    logger.info(
        "AC4 per-arity: a2=%s, a3=%s, pass=%s",
        ac4["a2_per_arity_keys"],
        ac4["a3_per_arity_keys"],
        ac4["pass"],
    )

    # ------------------------------------------------------------------ #
    # AC5 — geometry-vs-axis curves                                       #
    # ------------------------------------------------------------------ #
    # AC5 uses only B cells with full IsalHG coverage; TIMEOUT cells are
    # excluded from the axis-coverage check (whole-cell exclusion policy).
    # Pass in-memory re-aggregated stats to avoid reading stale per-task files.
    stats_dir = results_root / "stats"
    b_blocks_isalhg_complete = [
        bm for bm in b_blocks_meta if bm["block_key"] not in isalhg_timeout_b_cells
    ]
    # Match b_agg_stats to the complete cells (same order as b_blocks_raw).
    complete_keys = {bm["block_key"] for bm in b_blocks_isalhg_complete}
    b_agg_stats_complete = [
        stats
        for b, stats in zip(b_blocks_raw, b_agg_stats, strict=True)
        if b.block_key in complete_keys
    ]
    ac5 = verify_ac5_axis_coverage(
        b_blocks_isalhg_complete, stats_dir, b_agg_stats=b_agg_stats_complete
    )
    logger.info(
        "AC5 axis coverage: n=%s, density=%s, arity=%s, pass=%s",
        ac5["n_values"],
        ac5["density_values"],
        ac5["arity_values"],
        ac5["pass"],
    )

    # ------------------------------------------------------------------ #
    # Seed-gap report (per-cell, per-dist)                                #
    # ------------------------------------------------------------------ #
    gap_report: dict[str, Any] = {}

    # Stratum A
    a_gaps = count_seed_gaps(results_root, "stratum_a", "a", n_seeds, _ALL_DISTANCES)
    gap_report["stratum_a"] = a_gaps

    # Stratum B
    for b in b_blocks_raw:
        b_dists = [d for d in _ALL_DISTANCES if d != "hypercot"]
        b_gaps = count_seed_gaps(results_root, b.block_key, "b", n_seeds, b_dists)
        gap_report[b.block_key] = b_gaps

    # ------------------------------------------------------------------ #
    # Assemble summary                                                    #
    # ------------------------------------------------------------------ #
    all_pass, shortfalls = compute_harvest_decision(ac2, ac3, ac4, ac5, census_summary)

    summary: dict[str, Any] = {
        "array_id": array_id,
        "n_seeds_declared": n_seeds,
        "stratum_a_n_dist_reps": len(_ALL_DISTANCES),
        "stratum_b_n_cells": len(b_blocks_meta),
        "stratum_b_n_cells_isalhg_complete": len(b_blocks_isalhg_complete),
        "stratum_b_blocks": b_blocks_meta,
        # AC1
        "census": census_summary,
        # IsalHG TIMEOUT exclusions (whole-cell)
        "isalhg_timeout_b_cells": sorted(isalhg_timeout_b_cells),
        "isalhg_timeout_note": (
            "3 Stratum B cells timed out on isalhg_levenshtein at the 4-hour wall: "
            "er_uniform_k3_n16_rho4 (partial ~18/27 seeds), "
            "er_uniform_k3_n24_rho2 (partial ~9/27 seeds), "
            "er_uniform_k5_n8_rho2 (partial ~13/27 seeds).  "
            "All 6 competitors completed on these cells.  "
            "These cells are excluded from IsalHG comparative analysis (whole-cell "
            "exclusion; partial seed data not used).  This is the measured compute "
            "boundary of w*_c at n=16/rho=4 k3, n=24/rho=2 k3, and n=8/rho=2 k5 — "
            "not a failure to report, but the cost of the complete invariant."
        ),
        # AC2
        "ac2_ci_coverage": ac2,
        # AC3
        "ac3_wilcoxon_coverage": ac3,
        # AC4
        "ac4_per_arity": ac4,
        # AC5 (uses only IsalHG-complete B cells)
        "ac5_axis_coverage": ac5,
        "ac5_isalhg_complete_cells": [bm["block_key"] for bm in b_blocks_isalhg_complete],
        # Seed gaps
        "seed_gap_report": gap_report,
        # Overall
        "all_acceptance_pass": all_pass,
        "acceptance_shortfalls": shortfalls,
        # Note on arity axis
        "arity_axis_note": (
            "Stratum B arity axis has only 2 points (k∈{3,5}); the ≥3 criterion "
            "is not met for the arity sweep curve from Stratum B alone.  "
            "The per-arity Stratum A breakdown (ac4) provides k∈{3,4,5} for "
            "A2/A3 application metrics.  The T-M7s closing note explicitly "
            "records this as a measured outcome of the Stratum B admission "
            "envelope (k=4 blocks timed out; k=7/10 were infeasible)."
        ),
    }

    artifact_path = artifact_dir / "harvest_summary.json"
    _atomic_write_json(artifact_path, summary)
    logger.info("Harvest summary written: %s", artifact_path)

    return summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    parser = argparse.ArgumentParser(
        description="T-M7s harvest and acceptance check for array 1640910.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--results-root",
        type=Path,
        default=Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/T-M7d"),
        help="Local results root (rsync'd from Picasso).",
    )
    parser.add_argument(
        "--sacct-tsv",
        type=Path,
        default=None,
        help="sacct --parsable2 TSV for array 1640910.",
    )
    parser.add_argument(
        "--pairs-file",
        type=Path,
        default=None,
        help="T-M7d_pairs.txt (launcher pairs file).",
    )
    parser.add_argument(
        "--envelope",
        type=Path,
        default=Path("experiments/article/stratum_b_feasibility_envelope.json"),
        help="Path to stratum_b_feasibility_envelope.json.",
    )
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=Path("artifacts/T-M7d-harvest"),
        help="Artifact output directory.",
    )
    parser.add_argument(
        "--n-seeds",
        type=int,
        default=27,
        help="Declared seed count (S=27).",
    )
    parser.add_argument(
        "--array-id",
        type=int,
        default=1640910,
        help="SLURM array job ID.",
    )
    parser.add_argument(
        "--timeout-cells",
        nargs="*",
        default=None,
        metavar="CELL_KEY",
        help=(
            "Explicitly specify Stratum B cell keys where isalhg_levenshtein "
            "timed out (whole-cell exclusion).  Use when the sacct TSV is "
            "unavailable but the exclusion policy must be carried."
        ),
    )
    args = parser.parse_args()

    timeout_override: set[str] | None = (
        set(args.timeout_cells) if args.timeout_cells is not None else None
    )

    summary = harvest(
        results_root=args.results_root,
        sacct_tsv=args.sacct_tsv,
        envelope_path=args.envelope,
        artifact_dir=args.artifact_dir,
        n_seeds=args.n_seeds,
        array_id=args.array_id,
        pairs_file=args.pairs_file,
        isalhg_timeout_cells_override=timeout_override,
    )

    print("\n" + "=" * 60)
    print("T-M7s harvest summary")
    print("=" * 60)
    census = summary.get("census", {})
    if census.get("total", 0) > 0:
        print(
            f"  Array {summary['array_id']}: {census['total']} tasks — "
            f"{census['completed']} COMPLETED, {census['timeout']} TIMEOUT, "
            f"{census['failed']} FAILED, {census['oom']} OOM"
        )
        if census.get("non_completed_tasks"):
            print("  Non-completed tasks:")
            for t in census["non_completed_tasks"]:
                print(
                    f"    task {t['task_idx']} ({t['task_id']}) "
                    f"cell={t['cell_key']} dist={t['dist_name']} state={t['state']}"
                )
    print(
        f"  AC2 CI coverage: {summary['ac2_ci_coverage']['n_ci_entries']} entries, "
        f"pass={summary['ac2_ci_coverage']['pass']}"
    )
    print(
        f"  AC3 Wilcoxon:    {summary['ac3_wilcoxon_coverage']['n_wilcoxon_entries']} entries, "
        f"pass={summary['ac3_wilcoxon_coverage']['pass']}"
    )
    ac4 = summary["ac4_per_arity"]
    print(
        f"  AC4 per-arity:   a2_keys={ac4['a2_per_arity_keys']}, "
        f"a3_keys={ac4['a3_per_arity_keys']}, pass={ac4['pass']}"
    )
    ac5 = summary["ac5_axis_coverage"]
    print(
        f"  AC5 axis:        n={ac5['n_values']}, density={ac5['density_values']}, "
        f"arity={ac5['arity_values']}, pass={ac5['pass']}"
    )
    print(f"  Arity note: {ac5['arity_axis_note'][:80]}…")
    print(f"\n  Overall acceptance: {'PASS' if summary['all_acceptance_pass'] else 'FAIL'}")
    print(f"  Summary artifact: {args.artifact_dir / 'harvest_summary.json'}")


if __name__ == "__main__":
    main()
