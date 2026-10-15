"""Compare two KNN_2026-10-15 full-run trees value by value (cross-machine reproducibility).

Walks every result file of ``--a`` (unit JSONs and the evaluated items as JSON
lines; run logs and anything under ``_smoke`` excluded), finds its twin under
``--b``, and compares every numeric value recursively: exactly equal, equal
within ``--rtol``, or different. Wall-clock, throughput and worker-count keys
are skipped (they measure the machine, not the result). Writes
``REPRO_CHECK.json`` into ``--out`` (default ``--a``), which ``aggregate_full.py``
renders as a section of ``FULL_SUMMARY.md``.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SKIP_KEYS = ("secs", "pairs_per_s", "n_jobs", "generated", "argv")
SKIP_DIRS = ("runs", "logs", "_smoke")


@dataclass
class Tally:
    """Running counts of the comparison."""

    rtol: float
    n_values: int = 0
    n_exact: int = 0
    n_close: int = 0
    n_diff: int = 0
    examples: list[str] = field(default_factory=list)

    def number(self, a: float, b: float, where: str) -> None:
        self.n_values += 1
        if a == b or (math.isnan(a) and math.isnan(b)):
            self.n_exact += 1
        elif math.isclose(a, b, rel_tol=self.rtol, abs_tol=self.rtol):
            self.n_close += 1
        else:
            self.n_diff += 1
            if len(self.examples) < 50:
                self.examples.append(f"{where}: {a!r} vs {b!r}")

    def other(self, equal: bool, where: str, a: Any, b: Any) -> None:  # noqa: ANN401
        self.n_values += 1
        if equal:
            self.n_exact += 1
        else:
            self.n_diff += 1
            if len(self.examples) < 50:
                self.examples.append(f"{where}: {str(a)[:80]!r} vs {str(b)[:80]!r}")


def _skip_key(key: str) -> bool:
    return any(key.startswith(k) for k in SKIP_KEYS)


def compare(a: Any, b: Any, where: str, t: Tally) -> None:  # noqa: ANN401
    """Recursive comparison of two decoded JSON values."""
    if isinstance(a, bool) or isinstance(b, bool):
        t.other(a == b, where, a, b)
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
        t.number(float(a), float(b), where)
    elif isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if _skip_key(k):
                continue
            if k not in a or k not in b:
                t.other(False, f"{where}.{k}", a.get(k, "<missing>"), b.get(k, "<missing>"))
                continue
            compare(a[k], b[k], f"{where}.{k}", t)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            t.other(False, f"{where}[len]", len(a), len(b))
            return
        for i, (x, y) in enumerate(zip(a, b, strict=True)):
            compare(x, y, f"{where}[{i}]", t)
    else:
        t.other(a == b, where, a, b)


def result_files(root: Path) -> list[Path]:
    """Every result file under ``root``, relative, excluding logs and smokes."""
    out = []
    for p in root.rglob("*"):
        rel = p.relative_to(root)
        if not p.is_file() or any(part in SKIP_DIRS for part in rel.parts):
            continue
        # Unit files only: the top-level summaries and figures are derived from them.
        if p.suffix in (".json", ".jsonl") and len(rel.parts) > 1 and rel.parts[0] != "figures":
            out.append(rel)
    return sorted(out)


def run(a: Path, b: Path, rtol: float) -> dict[str, Any]:
    """Compare every result file of ``a`` with its twin in ``b``."""
    t = Tally(rtol=rtol)
    files_a, files_b = set(result_files(a)), set(result_files(b))
    for rel in sorted(files_a & files_b):
        if rel.suffix == ".jsonl":
            la = (a / rel).read_text().splitlines()
            lb = (b / rel).read_text().splitlines()
            compare([json.loads(x) for x in la], [json.loads(x) for x in lb], str(rel), t)
        else:
            compare(
                json.loads((a / rel).read_text()), json.loads((b / rel).read_text()), str(rel), t
            )
    missing = sorted(str(p) for p in files_a ^ files_b)
    return {
        "a": str(a),
        "b": str(b),
        "generated": time.strftime("%Y-%m-%d %H:%M %Z"),
        "rtol": rtol,
        "n_files": len(files_a & files_b),
        "n_values": t.n_values,
        "n_exact": t.n_exact,
        "n_close": t.n_close,
        "n_diff": t.n_diff,
        "n_missing": len(missing),
        "missing": missing[:50],
        "examples": t.examples,
        "skipped_keys": list(SKIP_KEYS),
    }


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--a", type=Path, required=True, help="the canonical tree (Picasso)")
    ap.add_argument("--b", type=Path, required=True, help="the replica (local)")
    ap.add_argument("--rtol", type=float, default=1e-9)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    res = run(args.a, args.b, args.rtol)
    out = (args.out or args.a) / "REPRO_CHECK.json"
    out.write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k not in ("examples", "missing")}, indent=1))
    for e in res["examples"][:20]:
        print("DIFF", e)
    for m in res["missing"][:20]:
        print("MISSING", m)


if __name__ == "__main__":
    main()
