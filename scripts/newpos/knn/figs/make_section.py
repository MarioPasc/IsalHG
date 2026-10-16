"""Build every Section-S5 deliverable from one full-run tree, in order.

``aggregate_full.py`` (FULL_SUMMARY.md, FULL_DETAIL.md, full_summary.json),
the four figures (``section/fig_s5_{tsne,accuracy,gap,mechanism}.pdf`` with PNG
previews and printed-number records), ``section_facts.py`` (knn_facts.tex,
SECTION_FACTS.md) and ``check_facts.py`` against the section source. Stops at
the first failing step.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import knn_lib as K  # noqa: E402, N812


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--root", type=Path, default=K.OUT_ROOT / "full")
    ap.add_argument("--n-jobs", type=int, default=16)
    ap.add_argument("--allow-missing", action="store_true", help="partial tree (during a run)")
    ap.add_argument("--tex", type=Path, default=None, help="s5_knn.tex to check against")
    args = ap.parse_args()
    py = sys.executable
    root = str(args.root)
    steps = [
        [py, str(HERE.parent / "aggregate_full.py"), "--root", root],
        [py, str(HERE / "fig_tsne.py"), "--root", root, "--n-jobs", str(args.n_jobs)],
        [py, str(HERE / "fig_accuracy.py"), "--root", root],
        [py, str(HERE / "fig_gap.py"), "--root", root],
        [py, str(HERE / "fig_mechanism.py"), "--root", root],
        [py, str(HERE / "section_facts.py"), "--root", root]
        + (["--allow-missing"] if args.allow_missing else []),
        [py, str(HERE / "check_facts.py"), "--facts", str(args.root / "section" / "knn_facts.tex")]
        + (["--tex", str(args.tex)] if args.tex else []),
    ]
    for cmd in steps:
        print(">>", " ".join(cmd[1:]), flush=True)
        status = subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL).returncode
        if status:
            sys.exit(f"step failed ({status}): {' '.join(cmd[1:])}")
    print("section deliverables built under", args.root / "section")


if __name__ == "__main__":
    main()
