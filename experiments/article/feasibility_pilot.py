"""Stratum B feasibility pilot — T-M7b.

Measures ``w*_c`` wall-clock cost for each runnable (arity_cfg, n, density)
block in the Stratum B recipe, then determines the **feasibility envelope**:
the set of cells whose ``p90(w*_c) ≤ budget_s`` with zero timeouts.

Usage::

    python -m experiments.article.feasibility_pilot \\
        --config experiments/article/configs/stratum_b_sweep.yaml \\
        --output /media/.../results/T-M7b/feasibility_envelope.json \\
        [--n-pilot 30] [--budget 30.0] [--timeout 35.0]

The ``--n-pilot`` override runs this many instances per block (default: from
YAML ``n_pilot``); ``--timeout`` caps each individual measurement (default:
``budget + 5`` seconds).

Output artifacts
----------------
``feasibility_envelope.json``
    Per-block records: p50/p90 times, admitted/excluded status, reason.
    Also contains ``figure_data`` (x=n, y-series by k and density) for the
    paper's scalability figure.

Exit codes
----------
0   All runnable blocks measured; any exclusions are documented.
1   Fatal error (config unreadable, output dir not writable, etc.).
"""

from __future__ import annotations

import argparse
import json
import logging
import signal
import statistics
import time
from pathlib import Path
from typing import Any

from experiments.article.stratum_b_cells import (
    StratumBCell,
    StratumBConfig,
    enumerate_cells,
    realized_params_for_cell,
    unique_blocks,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Timing with per-instance timeout
# ---------------------------------------------------------------------------


class _TimeoutError(Exception):
    pass


def _alarm_handler(signum: int, frame: Any) -> None:
    raise _TimeoutError


def _time_wstar_c(
    cell: StratumBCell,
    seed: int,
    timeout_s: float,
    require_connected: bool,
    connected_max_attempts: int,
) -> tuple[float | None, str, dict[str, Any]]:
    """Generate one instance and measure its ``w*_c`` wall-clock time.

    Parameters
    ----------
    cell : StratumBCell
        Block representative.
    seed : int
        PRNG seed for this instance.
    timeout_s : float
        Per-instance wall-clock limit in seconds.
    require_connected : bool
        Passed to the generator.
    connected_max_attempts : int
        Passed to the generator.

    Returns
    -------
    time_ms : float or None
        Wall-clock time in milliseconds, or None on timeout/error.
    status : str
        One of "ok", "timeout", "gen_error", "import_error".
    realized : dict
        Realized parameters (empty on error).
    """
    from isalhg.core.canonical import canonical_string
    from isalhg.datasets.synthetic.erdos_renyi import UniformErdosRenyiHypergraphs

    try:
        ds = UniformErdosRenyiHypergraphs(
            n=cell.n,
            r=cell.k,
            c=float(cell.density_ratio),
            seed=seed,
            require_connected=require_connected,
            connected_max_attempts=connected_max_attempts,
        )
        items = list(ds)
        if not items:
            return None, "gen_error", {}
        H = items[0].hypergraph
        realized = realized_params_for_cell(cell, H)
    except Exception as exc:
        logger.warning("generation failed for %s seed=%d: %s", cell.block_key, seed, exc)
        return None, "gen_error", {}

    old_handler = signal.signal(signal.SIGALRM, _alarm_handler)
    signal.alarm(int(timeout_s) + 1)
    try:
        t0 = time.perf_counter()
        canonical_string(H, k=cell.k)
        t1 = time.perf_counter()
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)
        return (t1 - t0) * 1000.0, "ok", realized
    except _TimeoutError:
        signal.signal(signal.SIGALRM, old_handler)
        logger.info("timeout: %s seed=%d budget=%.1fs", cell.block_key, seed, timeout_s)
        return None, "timeout", {}
    except Exception as exc:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)
        logger.warning("w*_c error: %s seed=%d: %s", cell.block_key, seed, exc)
        return None, "gen_error", {}


# ---------------------------------------------------------------------------
# Per-block pilot
# ---------------------------------------------------------------------------


def _pilot_block(
    rep: StratumBCell,
    n_pilot: int,
    budget_s: float,
    timeout_s: float,
    require_connected: bool,
    connected_max_attempts: int,
) -> dict[str, Any]:
    """Run the feasibility pilot for one (arity_cfg, n, density) block.

    Uses seeds ``rep.seed, rep.seed+1, …, rep.seed + n_pilot - 1`` (the
    seed_index=0 representative's seed and n_pilot-1 successive seeds drawn
    from the same deterministic walk).

    Parameters
    ----------
    rep : StratumBCell
        seed_index=0 cell for the block.
    n_pilot : int
        Number of instances to measure.
    budget_s : float
        p90 admission threshold (seconds).
    timeout_s : float
        Per-instance SIGALRM ceiling (seconds).
    require_connected : bool
        Passed to the generator.
    connected_max_attempts : int
        Passed to the generator.

    Returns
    -------
    dict[str, Any]
        Per-block result record.
    """
    times_ms: list[float] = []
    statuses: list[str] = []
    realized_list: list[dict[str, Any]] = []

    for i in range(n_pilot):
        seed = rep.seed + i  # sequential offset within the pilot
        t_ms, status, realized = _time_wstar_c(
            rep, seed, timeout_s, require_connected, connected_max_attempts
        )
        statuses.append(status)
        if t_ms is not None:
            times_ms.append(t_ms)
            realized_list.append(realized)

    n_ok = statuses.count("ok")
    n_timeout = statuses.count("timeout")
    n_error = len(statuses) - n_ok - n_timeout

    p50_ms = statistics.median(times_ms) if times_ms else None
    p90_ms = (
        sorted(times_ms)[int(0.9 * len(times_ms))]
        if len(times_ms) >= 2
        else (times_ms[0] if times_ms else None)
    )

    admitted = (
        n_timeout == 0 and n_error == 0 and p90_ms is not None and p90_ms / 1000.0 <= budget_s
    )

    if not admitted:
        if n_timeout > 0:
            reason = f"timeout ({n_timeout}/{n_pilot} instances exceeded {timeout_s:.0f}s)"
        elif n_error > 0:
            reason = f"generation error ({n_error}/{n_pilot} instances failed)"
        elif p90_ms is not None and p90_ms / 1000.0 > budget_s:
            reason = f"p90={p90_ms / 1000:.1f}s exceeds budget={budget_s:.0f}s"
        else:
            reason = "insufficient ok instances"
    else:
        reason = ""

    return {
        "block_key": rep.block_key,
        "n": rep.n,
        "k": rep.k,
        "mode": rep.mode,
        "generator": rep.generator,
        "density_ratio": rep.density_ratio,
        "cell_block_index": rep.cell_block_index,
        "n_pilot": n_pilot,
        "n_ok": n_ok,
        "n_timeout": n_timeout,
        "n_error": n_error,
        "times_ms": [round(t, 2) for t in times_ms],
        "p50_ms": round(p50_ms, 2) if p50_ms is not None else None,
        "p90_ms": round(p90_ms, 2) if p90_ms is not None else None,
        "p50_s": round(p50_ms / 1000.0, 4) if p50_ms is not None else None,
        "p90_s": round(p90_ms / 1000.0, 4) if p90_ms is not None else None,
        "admitted": admitted,
        "reason": reason,
        "realized_params_sample": realized_list[:3],  # first 3 for the record
    }


# ---------------------------------------------------------------------------
# Figure data builder
# ---------------------------------------------------------------------------


def _build_figure_data(block_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Build the feasibility-envelope figure data from block results.

    The paper's scalability figure shows ``w*_c`` p50/p90 vs ``n``, faceted by
    arity k and density ρ.  Admitted cells are filled; excluded cells appear
    as open markers at or above the budget line.

    Parameters
    ----------
    block_results : list[dict]
        Per-block result dicts from :func:`_pilot_block`.

    Returns
    -------
    dict[str, Any]
        Nested structure: ``figure_data[k][rho] = {n_values, p50_ms, p90_ms,
        admitted}``.
    """
    from collections import defaultdict

    # Index by (k, density_ratio)
    indexed: dict[tuple[int, float], dict[int, dict[str, Any]]] = defaultdict(dict)
    for r in block_results:
        key = (r["k"], float(r["density_ratio"]))
        indexed[key][r["n"]] = r

    figure_data: dict[str, Any] = {}
    for (k, rho), by_n in sorted(indexed.items()):
        rho_key = f"rho{int(rho) if rho == int(rho) else rho}"
        group_key = f"k{k}_{rho_key}"
        n_sorted = sorted(by_n.keys())
        figure_data[group_key] = {
            "k": k,
            "density_ratio": rho,
            "n_values": n_sorted,
            "p50_ms": [by_n[n]["p50_ms"] for n in n_sorted],
            "p90_ms": [by_n[n]["p90_ms"] for n in n_sorted],
            "admitted": [by_n[n]["admitted"] for n in n_sorted],
        }
    return figure_data


# ---------------------------------------------------------------------------
# Main pilot runner
# ---------------------------------------------------------------------------


def run_pilot(
    config_path: Path,
    output_path: Path,
    n_pilot_override: int | None = None,
    budget_override: float | None = None,
    timeout_override: float | None = None,
) -> dict[str, Any]:
    """Run the full Stratum B feasibility pilot.

    Parameters
    ----------
    config_path : Path
        Path to the Stratum B recipe YAML.
    output_path : Path
        Where to write ``feasibility_envelope.json``.
    n_pilot_override : int or None
        If set, override the YAML ``n_pilot``.
    budget_override : float or None
        If set, override the YAML ``budget_s``.
    timeout_override : float or None
        Per-instance timeout; defaults to ``budget_s + 5``.

    Returns
    -------
    dict[str, Any]
        The full envelope artifact (also written to ``output_path``).
    """
    cfg = StratumBConfig.from_yaml(config_path)
    n_pilot = n_pilot_override if n_pilot_override is not None else cfg.n_pilot
    budget_s = budget_override if budget_override is not None else cfg.budget_s
    timeout_s = timeout_override if timeout_override is not None else (budget_s + 5.0)

    all_cells = enumerate_cells(cfg)
    blocks = unique_blocks(cfg, runnable_only=True)

    # Non-runnable blocks (declared but skipped)
    non_runnable_blocks: list[dict[str, Any]] = []
    seen_block_indices: set[int] = set()
    for cell in all_cells:
        if not cell.runnable and cell.cell_block_index not in seen_block_indices:
            seen_block_indices.add(cell.cell_block_index)
            non_runnable_blocks.append(
                {
                    "block_key": cell.block_key,
                    "n": cell.n,
                    "k": cell.k,
                    "mode": cell.mode,
                    "generator": cell.generator,
                    "density_ratio": cell.density_ratio,
                    "cell_block_index": cell.cell_block_index,
                    "runnable": False,
                    "skip_reason": cell.skip_reason,
                    "admitted": False,
                    "reason": f"not_runnable:{cell.skip_reason}",
                }
            )

    logger.info(
        "Pilot: %d runnable blocks, %d non-runnable, n_pilot=%d, budget=%.1fs, timeout=%.1fs",
        len(blocks),
        len(non_runnable_blocks),
        n_pilot,
        budget_s,
        timeout_s,
    )

    block_results: list[dict[str, Any]] = []
    for i, rep in enumerate(blocks):
        logger.info(
            "[%d/%d] %s (n=%d, k=%d, rho=%.0f)",
            i + 1,
            len(blocks),
            rep.block_key,
            rep.n,
            rep.k,
            rep.density_ratio,
        )
        result = _pilot_block(
            rep,
            n_pilot=n_pilot,
            budget_s=budget_s,
            timeout_s=timeout_s,
            require_connected=cfg.require_connected,
            connected_max_attempts=cfg.connected_max_attempts,
        )
        block_results.append(result)
        status = "ADMIT" if result["admitted"] else "EXCLUDE"
        logger.info(
            "  → %s p50=%.1fms p90=%.1fms %s",
            status,
            result["p50_ms"] or 0.0,
            result["p90_ms"] or 0.0,
            f"[{result['reason']}]" if result["reason"] else "",
        )

    admitted_keys = [r["block_key"] for r in block_results if r["admitted"]]
    excluded = [
        {"block_key": r["block_key"], "reason": r["reason"]}
        for r in block_results
        if not r["admitted"]
    ]
    # Also add non-runnable as excluded
    excluded += [{"block_key": r["block_key"], "reason": r["reason"]} for r in non_runnable_blocks]

    figure_data = _build_figure_data(block_results)

    artifact: dict[str, Any] = {
        "config": {
            "yaml": str(config_path),
            "n_pilot": n_pilot,
            "budget_s": budget_s,
            "timeout_s": timeout_s,
            "seed_base": cfg.seed_base,
            "seed_stride": cfg.seed_stride,
            "n_seeds": cfg.n_seeds,
        },
        "summary": {
            "n_runnable_blocks": len(blocks),
            "n_non_runnable_blocks": len(non_runnable_blocks),
            "n_admitted": len(admitted_keys),
            "n_excluded_runnable": len([r for r in block_results if not r["admitted"]]),
            "n_excluded_non_runnable": len(non_runnable_blocks),
        },
        "admitted_block_keys": admitted_keys,
        "excluded": excluded,
        "block_results": block_results,
        "non_runnable_blocks": non_runnable_blocks,
        "figure_data": figure_data,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = output_path.with_suffix(output_path.suffix + ".tmp")
    tmp.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    tmp.replace(output_path)
    logger.info("Envelope written to %s", output_path)

    return artifact


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--config", type=Path, required=True, help="Stratum B recipe YAML")
    p.add_argument("--output", type=Path, required=True, help="Output JSON path")
    p.add_argument("--n-pilot", type=int, default=None, help="Pilot instance count override")
    p.add_argument("--budget", type=float, default=None, help="Admission budget (s) override")
    p.add_argument("--timeout", type=float, default=None, help="Per-instance timeout (s)")
    p.add_argument("--verbose", action="store_true")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    try:
        run_pilot(
            config_path=args.config,
            output_path=args.output,
            n_pilot_override=args.n_pilot,
            budget_override=args.budget,
            timeout_override=args.timeout,
        )
    except Exception:
        logger.exception("Fatal error in feasibility pilot")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
