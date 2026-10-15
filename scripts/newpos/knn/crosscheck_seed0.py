"""Cross-check single Picasso cells against the same cells computed locally (seed 0).

The local cells come from the full-run smoke (``full_run.py --smoke``: seed 0 of
D_ndc_classes_pendant, C3_ndc_classes_C-all, A_ndc_classes with Afull, and
B_ndc_classes) and from the Design-B timing run (seed 0 of B_wd50k66), both
computed on the workstation with the code the cluster ran. Each local cell is
compared value by value with the Picasso cell of the same unit and seed
(``compare_runs.compare``; wall-clock, throughput and worker-count keys
skipped). A key named by ``--ignore-missing-keys`` that the local cell lacks is
dropped from the Picasso side before comparing (the timing run predates the per-query
mechanism distances). Writes ``CROSSCHECK_SEED0.json`` into ``--picasso``,
which ``aggregate_full.py`` renders in FULL_SUMMARY.md.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import compare_runs as CR  # noqa: N812

DEFAULT_LOCAL = (
    Path(
        "/tmp/claude-1000/-home-mpascual-research-code-IsalHG/6e1bf485-d6d9-4736-9632-8b3e48bbb69a/scratchpad/timing/smoke2"
    ),
    Path(
        "/tmp/claude-1000/-home-mpascual-research-code-IsalHG/6e1bf485-d6d9-4736-9632-8b3e48bbb69a/scratchpad/timing"
    ),
)


def _align(a: Any, b: Any, keys: set[str]) -> Any:  # noqa: ANN401
    """``a`` without the ``keys`` that ``b`` lacks at the same place (recursively)."""
    if isinstance(a, dict) and isinstance(b, dict):
        return {
            k: _align(v, b.get(k), keys) for k, v in a.items() if not (k in keys and k not in b)
        }
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        return [_align(x, y, keys) for x, y in zip(a, b, strict=True)]
    return a


def pairs(picasso: Path, local: Path) -> list[tuple[str, Any, Any]]:
    """``(label, picasso value, local value)`` of every seed-0 cell the local tree holds."""
    out: list[tuple[str, Any, Any]] = []
    for cell in sorted(local.glob("*/cells/*_s0.json")) + sorted(
        local.glob("*/cells/Afull_*.json")
    ):
        unit = cell.parts[-3]
        twin_unit = unit if unit != "B" else "B_wd50k66"
        twin = picasso / twin_unit / "cells" / cell.name
        if twin.exists():
            out.append(
                (
                    f"{twin_unit}/cells/{cell.name}",
                    json.loads(twin.read_text()),
                    json.loads(cell.read_text()),
                )
            )
    for job in sorted(local.glob("*/[CD]_*.json")):
        twin = picasso / job.parts[-2] / job.name
        if not twin.exists():
            continue
        a, b = json.loads(twin.read_text()), json.loads(job.read_text())
        for seed in sorted(b.get("seeds", {}), key=int):
            if seed in a.get("seeds", {}):
                out.append(
                    (f"{job.parts[-2]}/{job.name}#seeds.{seed}", a["seeds"][seed], b["seeds"][seed])
                )
    return out


def run(picasso: Path, locals_: list[Path], rtol: float, ignore: set[str]) -> dict[str, Any]:
    t = CR.Tally(rtol=rtol)
    checked: list[str] = []
    for local in locals_:
        for label, a, b in pairs(picasso, local):
            CR.compare(_align(a, b, ignore), b, label, t)
            checked.append(f"{label} <- {local}")
    return {
        "generated": time.strftime("%Y-%m-%d %H:%M %Z"),
        "picasso": str(picasso),
        "local": [str(p) for p in locals_],
        "cells": checked,
        "rtol": rtol,
        "ignored_keys": sorted(ignore),
        "n_values": t.n_values,
        "n_exact": t.n_exact,
        "n_close": t.n_close,
        "n_diff": t.n_diff,
        "examples": t.examples,
    }


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--picasso", type=Path, required=True)
    ap.add_argument("--local", type=Path, nargs="+", default=list(DEFAULT_LOCAL))
    ap.add_argument("--rtol", type=float, default=1e-9)
    ap.add_argument("--ignore-missing-keys", nargs="*", default=["nn_same", "nn_other"])
    args = ap.parse_args()
    res = run(args.picasso, args.local, args.rtol, set(args.ignore_missing_keys))
    (args.picasso / "CROSSCHECK_SEED0.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "examples"}, indent=1))
    for e in res["examples"][:20]:
        print("DIFF", e)


if __name__ == "__main__":
    main()
