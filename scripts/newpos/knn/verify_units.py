"""Check that a full-run tree holds every seed of every unit of ``full_run.units()``.

Design A / B / mix units: one cell file per (r, seed) (``A``: per seed, plus the
single ``Afull`` evaluation). Design C / D units: one job file whose ``seeds``
map holds every seed. Writes ``UNITS_CHECK.json`` into the root (rendered by
``aggregate_full.py``) and exits 1 when a unit misses a seed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import full_run as FR  # noqa: E402, N812
import knn_lib as K  # noqa: E402, N812

RS = (1, 2, 3)


def _arg(unit: FR.Unit, flag: str) -> str:
    return unit.args[unit.args.index(flag) + 1]


def check_unit(root: Path, unit: FR.Unit) -> dict[str, Any]:
    """Seeds present per unit (per r for the cell-file designs) and the missing ones."""
    d = root / unit.name
    want = set(FR.SEEDS)
    if unit.script == "probe_knn.py":
        design = _arg(unit, "--designs")
        col = _arg(unit, "--collections")
        if design == "A":
            have = {s for s in want if (d / "cells" / f"A_{col}_s{s}.json").exists()}
            afull = (d / "cells" / f"Afull_{col}.json").exists()
            missing = sorted(want - have)
            return {
                "unit": unit.name,
                "seeds": len(have),
                "missing": missing,
                "afull": afull,
                "ok": not missing and afull,
            }
        prefix = "B" if design == "B" else "Bmix"
        per_r = {
            r: {s for s in want if (d / "cells" / f"{prefix}_{col}_r{r}_s{s}.json").exists()}
            for r in RS
        }
        missing = sorted({(r, s) for r in RS for s in want - per_r[r]})
        return {
            "unit": unit.name,
            "seeds": min(len(v) for v in per_r.values()),
            "missing": missing,
            "ok": not missing,
        }
    jobs = sorted(d.glob("C_*.json")) + sorted(d.glob("D_*.json"))
    if len(jobs) != 1:
        return {
            "unit": unit.name,
            "seeds": 0,
            "missing": sorted(want),
            "ok": False,
            "note": f"{len(jobs)} job files",
        }
    seeds = {int(s) for s in json.loads(jobs[0].read_text()).get("seeds", {})}
    missing = sorted(want - seeds)
    return {"unit": unit.name, "seeds": len(seeds & want), "missing": missing, "ok": not missing}


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--root", type=Path, default=K.OUT_ROOT / "full")
    args = ap.parse_args()
    rows = [check_unit(args.root, u) for u in FR.units()]
    bad = [r for r in rows if not r["ok"]]
    (args.root / "UNITS_CHECK.json").write_text(
        json.dumps({"n_units": len(rows), "n_incomplete": len(bad), "units": rows}, indent=1)
    )
    for r in rows:
        print(
            f"{r['unit']:28s} seeds {r['seeds']:2d}"
            + (" afull" if r.get("afull") else "")
            + ("" if r["ok"] else f"  MISSING {r['missing']} {r.get('note', '')}")
        )
    print(f"{len(rows)} units, {len(bad)} incomplete")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
