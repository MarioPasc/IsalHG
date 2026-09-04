"""Merge the Picasso E-A shards into one keyed store, and summarize coverage.

    rsync -a picasso:/mnt/.../fscratch/results/f4_topology/ea/ ./ea_shards/
    python merge_ea_shards.py --shards ./ea_shards

Writes ``ea_full.json`` (``task_key -> {ok, w, seed, secs}``) next to the shard
directory. ``run_probe.py`` can then be re-run against it by pre-seeding
``ArmA.cache``; the key is the content hash from ``run_ea_full.task_key``, so no
index bookkeeping is needed.
"""

from __future__ import annotations

import argparse
import json
import statistics as st
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shards", required=True, type=Path)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    merged: dict[str, dict] = {}
    files = sorted(args.shards.glob("ea_shard_*.json"))
    for f in files:
        merged.update(json.loads(f.read_text()))

    ok = [v for v in merged.values() if v.get("ok")]
    dnf = [v for v in merged.values() if v.get("dnf")]
    secs = [v["secs"] for v in ok if v.get("secs") is not None]
    out = args.out or args.shards.parent / "ea_full.json"
    out.write_text(json.dumps(merged))
    print(f"shards merged : {len(files)}")
    print(f"tasks         : {len(merged)}")
    print(f"ok            : {len(ok)}")
    print(f"dnf (censored): {len(dnf)}  ({len(dnf) / max(1, len(merged)):.4f})")
    print(f"err           : {len(merged) - len(ok) - len(dnf)}")
    if secs:
        s = sorted(secs)
        print(
            f"secs          : med {st.median(s):.4f}  "
            f"p90 {s[int(0.9 * (len(s) - 1))]:.4f}  max {s[-1]:.2f}"
        )
    print(f"written       : {out}")


if __name__ == "__main__":
    main()
