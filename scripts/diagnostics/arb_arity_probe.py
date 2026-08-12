"""Cheap half of gate G-D1: arity distribution per ARB dataset.

Reads only the simplex-size axis (``*-nverts.txt`` for the temporal family,
line-wise comma counts for the labeled family). No canonical forms, no
graph construction -- this is a line scan.
"""

from __future__ import annotations

import statistics
from pathlib import Path

ROOT = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/data/arb_benson")


def temporal_arities(d: Path) -> list[int]:
    f = next(d.glob("*-nverts.txt"), None)
    if f is None:
        return []
    with f.open() as fh:
        return [int(line) for line in fh if line.strip()]


def labeled_arities(d: Path) -> list[int]:
    f = next(d.glob("hyperedges-*.txt"), None)
    if f is None:
        return []
    out = []
    with f.open() as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(line.count(",") + 1)
    return out


def frac(a: list[int], cap: int) -> float:
    return sum(1 for x in a if x <= cap) / len(a)


rows = []
for family, reader in (("temporal", temporal_arities), ("labeled", labeled_arities)):
    for d in sorted((ROOT / family).iterdir()):
        if not d.is_dir():
            continue
        a = reader(d)
        if not a:
            rows.append((family, d.name, 0, 0, 0, 0, 0, 0.0, 0.0, 0.0))
            continue
        a.sort()
        rows.append(
            (
                family,
                d.name,
                len(a),
                a[0],
                int(statistics.median(a)),
                a[int(0.95 * (len(a) - 1))],
                a[-1],
                frac(a, 3),
                frac(a, 5),
                frac(a, 10),
            )
        )

hdr = f"{'family':9} {'dataset':26} {'|E|':>10} {'min':>4} {'med':>4} {'p95':>5} {'max':>7} {'<=3':>6} {'<=5':>6} {'<=10':>6}"
print(hdr)
print("-" * len(hdr))
for r in rows:
    print(
        f"{r[0]:9} {r[1]:26} {r[2]:>10,} {r[3]:>4} {r[4]:>4} {r[5]:>5} {r[6]:>7} "
        f"{r[7]:>6.3f} {r[8]:>6.3f} {r[9]:>6.3f}"
    )
