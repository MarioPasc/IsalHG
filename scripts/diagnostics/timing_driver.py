"""Time w*_c on dumped candidates via subprocess, 900 s cap each."""

import glob
import os
import subprocess
import sys
import time

SCRATCH = os.path.dirname(os.path.abspath(__file__))
TIMEOUT = 900

ORDER = [
    "sts15_idx22_rigid_swap200",
    "sts15_idx22_rigid_swap1",
    "sts15_idx22_rigid_swap2",
    "sts15_idx22_rigid_pristine",
    "sts15_idx23_rigid2_pristine",
    "sts15_idx53_median_pristine",
    "sts15_idx0_swap1",
    "sts19_s0_rigid_pristine",
    "sts15_idx0_pristine",
]


def main() -> None:
    available = {
        os.path.basename(p)[5:-5]: p for p in glob.glob(os.path.join(SCRATCH, "cand_*.json"))
    }
    print("available candidates:", sorted(available), flush=True)
    py = sys.executable
    timer = os.path.join(SCRATCH, "time_wstar.py")
    labels = [l for l in ORDER if l in available]
    labels += [l for l in sorted(available) if l not in labels]
    for label in labels:
        t0 = time.perf_counter()
        try:
            r = subprocess.run(
                [py, timer, available[label]],
                capture_output=True,
                text=True,
                timeout=TIMEOUT,
                env=os.environ,
            )
            out = (r.stdout + r.stderr).strip()
            print(out if out else f"TIMING {label} EXIT={r.returncode} (no output)", flush=True)
        except subprocess.TimeoutExpired:
            print(
                f"TIMING {label} TIMEOUT>{TIMEOUT}s (wall {time.perf_counter() - t0:.0f}s)",
                flush=True,
            )


if __name__ == "__main__":
    main()
