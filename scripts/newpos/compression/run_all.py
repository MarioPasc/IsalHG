"""Run measure.py on the four frozen collections, then analyze.py and fig_bits.py.

Usage (from the repo root)::

    python scripts/newpos/compression/run_all.py --out <results dir>
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_OUT = Path(
    "/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/NEWPOS_2026-10-13/compression"
)
COLLECTIONS = ("wd50k66", "ndc_classes", "ndc_substances", "wd50k100")


def main() -> None:
    """Measure every collection sequentially (each uses ``--procs`` workers), then analyse."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--boot-reps", type=int, default=200)
    ap.add_argument("--skip-measure", action="store_true")
    ap.add_argument("--measure-only", action="store_true")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    if not args.skip_measure:
        for name in COLLECTIONS:
            log = args.out / f"log_{name}.txt"
            cmd = [
                sys.executable,
                str(HERE / "measure.py"),
                "--collection",
                name,
                "--out",
                str(args.out),
                "--procs",
                str(args.procs),
                "--boot-reps",
                str(args.boot_reps),
            ]
            with log.open("w") as handle:
                subprocess.run(cmd, stdout=handle, stderr=subprocess.STDOUT, check=True)
    if args.measure_only:
        return
    subprocess.run([sys.executable, str(HERE / "analyze.py"), "--res", str(args.out)], check=True)
    subprocess.run([sys.executable, str(HERE / "fig_bits.py"), "--res", str(args.out)], check=True)


if __name__ == "__main__":
    main()
