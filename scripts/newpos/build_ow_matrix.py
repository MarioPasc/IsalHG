"""Build the ``isal_ow_struct`` (``w°``) distance matrix of a frozen collection.

Writes ``<out>/<collection>/isal_ow_struct.npy`` in corpus member order, for
collections whose cached matrix set lacks the ordered-walk arm.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from experiments.tkde import corpora as C  # noqa: E402
from isalhg.metric_space.registry import get_distance  # noqa: E402

D_ROOT = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--collection", required=True)
    ap.add_argument("--arm", default="isal_ow_struct")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    col = C.load_collection(args.collection, root=D_ROOT)
    hs = C.hypergraphs(col)
    t0 = time.perf_counter()
    M = get_distance(args.arm).matrix(hs)
    dt = time.perf_counter() - t0
    dest = args.out / args.collection
    dest.mkdir(parents=True, exist_ok=True)
    np.save(dest / f"{args.arm}.npy", M)
    print(f"{args.collection}/{args.arm}: {M.shape} in {dt:.2f} s -> {dest}")


if __name__ == "__main__":
    main()
