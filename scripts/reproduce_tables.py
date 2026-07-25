"""Reproduce the article's geometry table, bits, and a paired test from the
shipped per-seed caches alone, and diff against the committed stats artifact.

This is the T-M8d reproducibility driver. It reads
``<results>/T-M7d/seed_metrics/`` (the small per-seed JSON caches shipped with
the artifact), re-aggregates the Stratum A cell with the same BCa / Wilcoxon /
Holm pipeline the article used, and asserts the reproduced values match
``<results>/T-M7d/stats/stratum_a_stats.json`` to full precision. No cluster
access and no D-matrix recomputation are needed.

Run from the repository root:

    PYTHONPATH=. python scripts/reproduce_tables.py \
        --results-root /path/to/results/T-M7d

Exit code 0 on full agreement, 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from experiments.article.analysis.sweep_multi_seed import ALL_DISTANCES
from scripts.harvest_T_M7s import reaggregate_cell

_GEOMETRY_METRICS = ("nu", "d_hat", "stress", "hubness_skewness")
_TOL = 1e-9


def _cis(d: dict) -> dict:
    return d.get("cis", {})


def _wilcoxon(d: dict) -> dict:
    return d.get("wilcoxon", {})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--results-root",
        type=Path,
        default=Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/T-M7d"),
        help="T-M7d results root holding seed_metrics/ and stats/.",
    )
    args = parser.parse_args()
    root: Path = args.results_root

    with open(root / "stats" / "stratum_a_stats.json") as fh:
        committed = json.load(fh)
    cs = reaggregate_cell(root, "stratum_a", "a", 27, list(ALL_DISTANCES))
    repro = json.loads(json.dumps(cs, default=lambda o: getattr(o, "__dict__", str(o))))

    c_ci, r_ci = _cis(committed), _cis(repro)
    c_w, r_w = _wilcoxon(committed), _wilcoxon(repro)

    checks: list[tuple[str, float | None, float | None, bool]] = []
    for metric in _GEOMETRY_METRICS:
        key = f"isalhg_levenshtein::g1_a1::{metric}"
        a = c_ci.get(key, {}).get("mean")
        b = r_ci.get(key, {}).get("mean")
        checks.append((f"geometry {metric}", a, b, _close(a, b)))

    bits_key = next((k for k in c_ci if "isalhg_levenshtein" in k and "bits" in k), None)
    if bits_key:
        a = c_ci[bits_key]["mean"]
        b = r_ci.get(bits_key, {}).get("mean")
        checks.append((f"bits {bits_key.split('::')[-1]}", a, b, _close(a, b)))

    key = "degree_seq_l1::a2::ari"
    a = c_w.get(key, {}).get("reverse", {}).get("p_holm")
    b = r_w.get(key, {}).get("reverse", {}).get("p_holm")
    checks.append(("wilcoxon degree_seq a2::ari reverse p_holm", a, b, _close(a, b, 1e-12)))

    print(f"{'check':46s} {'committed':>14s} {'reproduced':>14s}  ok")
    all_ok = True
    for name, a, b, ok in checks:
        all_ok &= ok
        print(f"{name:46s} {_fmt(a):>14s} {_fmt(b):>14s}  {'PASS' if ok else 'FAIL'}")
    print("\nDRY-RUN", "PASS" if all_ok else "FAIL")
    return 0 if all_ok else 1


def _close(a: float | None, b: float | None, tol: float = _TOL) -> bool:
    return a is not None and b is not None and abs(a - b) < tol


def _fmt(x: float | None) -> str:
    return f"{x:.6g}" if isinstance(x, (int, float)) else str(x)


if __name__ == "__main__":
    sys.exit(main())
