"""Cross-check single Picasso cells against the same cells computed locally (seed 0).

The local cells are seed-0 runs of a few cheap units, recomputed on the
workstation with the code the cluster ran (2 cores, under 10 minutes; default
``<OUT_ROOT>/crosscheck_local``: C3_ndc_classes_C-all, C3_ndc_substances_C-int,
D_ndc_classes_pendant, A_ndc_classes). Each local cell is compared value by
value with the Picasso cell of the same unit and seed (``compare_runs.compare``;
wall-clock, throughput and worker-count keys skipped). A key named by
``--ignore-missing-keys`` that the local cell lacks is dropped from the Picasso
side before comparing (for local cells that predate the per-query mechanism
distances). Writes ``CROSSCHECK_SEED0.json`` into ``--picasso``, which
``aggregate_full.py`` renders in FULL_SUMMARY.md.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any

import compare_runs as CR  # noqa: N812

DEFAULT_LOCAL = (
    Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/KNN_2026-10-15/crosscheck_local"),
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


class ArmTally(CR.Tally):
    """:class:`compare_runs.Tally` that also counts differences per arm."""

    def __init__(self, rtol: float) -> None:
        super().__init__(rtol=rtol)
        self.diff_by_arm: Counter[str] = Counter()
        self.values_by_arm: Counter[str] = Counter()

    @staticmethod
    def _arm(where: str) -> str:
        m = re.search(r"arms\.([a-z0-9_]+)", where)
        return m.group(1) if m else "(cell level)"

    def number(self, a: float, b: float, where: str) -> None:
        before = self.n_diff
        super().number(a, b, where)
        self.values_by_arm[self._arm(where)] += 1
        self.diff_by_arm[self._arm(where)] += self.n_diff - before

    def other(self, equal: bool, where: str, a: Any, b: Any) -> None:  # noqa: ANN401
        before = self.n_diff
        super().other(equal, where, a, b)
        self.values_by_arm[self._arm(where)] += 1
        self.diff_by_arm[self._arm(where)] += self.n_diff - before


def _metric_gaps(a: Any, b: Any, label: str) -> list[dict[str, Any]]:  # noqa: ANN401
    """Per arm and hypothesis metric, the Picasso and local values where they differ."""
    out = []
    cells = a["cells"].items() if "cells" in a else [("", a)]
    for r, ca in cells:
        cb = b["cells"][r] if r else b
        for arm, va in ca.get("arms", {}).items():
            for m in ("acc1", "ari", "rr"):
                x, y = va.get(m), cb["arms"].get(arm, {}).get(m)
                if x is not None and y is not None and x != y:
                    out.append(
                        {
                            "cell": f"{label}{'#r' + r if r else ''}",
                            "arm": arm,
                            "metric": m,
                            "picasso": x,
                            "local": y,
                            "abs_diff": abs(x - y),
                        }
                    )
    return out


def run(picasso: Path, locals_: list[Path], rtol: float, ignore: set[str]) -> dict[str, Any]:
    t = ArmTally(rtol=rtol)
    checked: list[str] = []
    gaps: list[dict[str, Any]] = []
    for local in locals_:
        for label, a, b in pairs(picasso, local):
            CR.compare(_align(a, b, ignore), b, label, t)
            checked.append(f"{label} <- {local}")
            gaps += _metric_gaps(a, b, label)
    return {
        "diff_by_arm": dict(t.diff_by_arm),
        "values_by_arm": dict(t.values_by_arm),
        "metric_gaps": gaps,
        "max_metric_gap": max(gaps, key=lambda g: g["abs_diff"]) if gaps else None,
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
    ap.add_argument(
        "--prior-gap",
        type=float,
        default=None,
        help="largest hypothesis-metric gap seen by an earlier cross-check whose local files "
        "are gone; the platform-sensitivity flag uses the larger of the two",
    )
    ap.add_argument("--prior-note", default="", help="where the prior gap was observed")
    args = ap.parse_args()
    res = run(args.picasso, args.local, args.rtol, set(args.ignore_missing_keys))
    if args.prior_gap is not None:
        res["prior"] = {"abs_diff": args.prior_gap, "note": args.prior_note}
    (args.picasso / "CROSSCHECK_SEED0.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "examples"}, indent=1))
    for e in res["examples"][:20]:
        print("DIFF", e)


if __name__ == "__main__":
    main()
