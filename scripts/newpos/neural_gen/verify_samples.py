"""Check sample files against the frozen format and against an independent re-decode.

For every ``*.jsonl.gz`` in a directory: exact key set and order on every line, draw
indices ``0..n-1``, counts equal to the unit summary, and, on a subset of lines, a
re-decode of the stored token strings whose knowledge base must equal the stored one.
"""

from __future__ import annotations

import argparse
import ast
import gzip
import json
import random
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parents[2]
for _path in (str(_HERE), str(_REPO_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import ng_decode  # noqa: E402

KEY_TYPES: dict[str, tuple[type, ...]] = {
    "collection": (str,),
    "generator": (str,),
    "seed": (int,),
    "draw": (int,),
    "tokens": (list,),
    "root_type": (int, type(None)),
    "status": (str,),
    "reason": (str, type(None)),
    "n": (int, type(None)),
    "types": (list, type(None)),
    "facts": (list, type(None)),
    "connected": (bool, type(None)),
}


def _parse_tokens(serialization: str, strings: Sequence[str]) -> list[Any]:
    """Invert ``str()`` of the sampled token objects."""
    if serialization == "ow":
        return list(strings)
    return [ast.literal_eval(s) for s in strings]


def check_record(record: dict[str, Any]) -> list[str]:
    """Format violations of one line (empty when the line conforms)."""
    problems: list[str] = []
    if tuple(record) != ng_decode.RECORD_KEYS:
        problems.append(f"keys {tuple(record)}")
        return problems
    for key, types in KEY_TYPES.items():
        if not isinstance(record[key], types):
            problems.append(f"{key}: {type(record[key]).__name__}")
    if record["status"] not in {"decoded", "rejected"}:
        problems.append(f"status {record['status']!r}")
    rejected = record["status"] == "rejected"
    for key in ("n", "types", "facts", "connected"):
        if rejected != (record[key] is None):
            problems.append(f"{key} null-ness disagrees with status")
    if rejected != (record["reason"] is not None):
        problems.append("reason null-ness disagrees with status")
    return problems


def verify_file(
    path: Path, summary: dict[str, Any], n_redecode: int, seed: int = 0
) -> dict[str, Any]:
    """Verify one sample file; returns counts of every kind of disagreement."""
    spec = ng_decode.DecodeSpec(**summary["decode_spec"])
    serialization = summary["serialization"]
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        records = [json.loads(line) for line in handle]
    format_problems = sum(1 for r in records if check_record(r))
    draws_ok = [r["draw"] for r in records] == list(range(len(records)))
    n_decoded = sum(1 for r in records if r["status"] == "decoded")
    n_connected = sum(1 for r in records if r["connected"])
    counts_ok = (
        len(records) == summary["n_draws"]
        and n_decoded == summary["n_decoded"]
        and n_connected == summary["n_connected"]
    )
    rng = random.Random(f"verify|{path.name}|{seed}")
    chosen = rng.sample(records, min(n_redecode, len(records)))
    mismatches = 0
    for record in chosen:
        tokens = _parse_tokens(serialization, record["tokens"])
        outcome = ng_decode.process_draw(
            record["collection"],
            serialization,
            record["generator"],
            record["seed"],
            record["draw"],
            tokens,
            record["root_type"],
            spec,
        )
        if outcome.record != record:
            mismatches += 1
    return {
        "file": path.name,
        "n_lines": len(records),
        "format_problems": format_problems,
        "draws_contiguous": draws_ok,
        "counts_match_summary": counts_ok,
        "n_redecoded": len(chosen),
        "redecode_mismatches": mismatches,
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Verify every sample file of a directory; non-zero exit on any disagreement."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--n-redecode", type=int, default=300)
    args = parser.parse_args(argv)
    bad = 0
    files = sorted(args.results_dir.glob("*.jsonl.gz"))
    for path in files:
        summary_file = path.with_name(path.name.removesuffix(".jsonl.gz") + ".summary.json")
        summary = json.loads(summary_file.read_text(encoding="utf-8"))
        report = verify_file(path, summary, args.n_redecode)
        ok = (
            report["format_problems"] == 0
            and report["draws_contiguous"]
            and report["counts_match_summary"]
            and report["redecode_mismatches"] == 0
        )
        bad += int(not ok)
        print(("OK   " if ok else "FAIL ") + json.dumps(report))
    print(f"{len(files)} files, {bad} failing")
    return int(bad > 0)


if __name__ == "__main__":
    sys.exit(main())
