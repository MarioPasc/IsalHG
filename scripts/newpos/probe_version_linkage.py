"""Probe C3: anonymous version linkage on the NDC-classes quarterly series.

For every natural consecutive pair (a, b) of one drug class -- a at window w,
b at the class's next window -- rank every member of b's window by its
distance to a, and score the rank of b. Ties are resolved by expectation: a
target tied with t others at its distance has expected rank r + t/2 and
expected hit@1 1/(t+1) when the tie is at the top. No representation sees a
class identity or a constant name. Reported per arm and per stratum of the
pair (constant-preserving vs constant-changing).
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from experiments.tkde import corpora as C  # noqa: E402

D_ROOT = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE")
ARMS = (
    "isal_ow_struct",
    "wstar_orbit",
    "nauty_cert",
    "nauty_cert_rows",
    "wl_l1",
    "netlsd",
    "hpd_jsd",
    "bipartite_ged_assign",
    "bipartite_ged_path",
    "degree_seq_l1",
    "size_l1",
)


def expected_rank(dist: np.ndarray, target: int) -> tuple[float, float]:
    dt = dist[target]
    better = int(np.sum(dist < dt))
    ties = int(np.sum(dist == dt)) - 1
    rank = 1 + better + ties / 2.0
    hit1 = (1.0 / (ties + 1)) if better == 0 else 0.0
    return rank, hit1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--collection", default="ndc_classes")
    ap.add_argument("--direction", choices=["forward", "both"], default="both")
    ap.add_argument(
        "--extra-matrix-dir",
        type=Path,
        default=None,
        help="directory holding <collection>/<arm>.npy for arms missing from the cache",
    )
    args = ap.parse_args()
    col = C.load_collection(args.collection, root=D_ROOT)
    ids = C.member_ids(col)
    idx = {m: i for i, m in enumerate(ids)}
    window = np.array([r.meta.get("window") for r in col.records])
    pairs = C.consecutive_pairs(col)
    queries = []
    for p in pairs:
        queries.append((idx[p["a"]], idx[p["b"]], p["constant_preserving"]))
        if args.direction == "both":
            queries.append((idx[p["b"]], idx[p["a"]], p["constant_preserving"]))
    cand_size = [int(np.sum(window == window[t])) for _, t, _ in queries]
    print(
        f"{args.collection}: {len(pairs)} pairs, {len(queries)} queries; candidates per query "
        f"median {int(np.median(cand_size))}, min {min(cand_size)}, max {max(cand_size)}"
    )
    print(
        "arm".ljust(22)
        + "MRR".rjust(7)
        + "hit@1".rjust(8)
        + "  | MRR pres".rjust(12)
        + " hit1 pres".rjust(10)
        + "  | MRR chg".rjust(11)
        + " hit1 chg".rjust(9)
    )
    for arm in ARMS:
        path = D_ROOT / "matrices" / args.collection / f"{arm}.npy"
        if not path.exists() and args.extra_matrix_dir is not None:
            path = args.extra_matrix_dir / args.collection / f"{arm}.npy"
        if not path.exists():
            continue
        M = np.load(path)
        if M.shape[0] != len(ids):
            print(arm.ljust(22) + "  skipped (matrix over a censored subset)")
            continue
        acc = defaultdict(list)
        for q, t, pres in queries:
            cands = np.where(window == window[t])[0]
            dist = M[q, cands].astype(np.float64)
            rank, hit = expected_rank(dist, int(np.where(cands == t)[0][0]))
            for key in ("all", "pres" if pres else "chg"):
                acc[key].append((1.0 / rank, hit))

        def fmt(key: str) -> str:
            a = np.array(acc[key])
            return f"{a[:, 0].mean():7.3f}{a[:, 1].mean():8.3f}"

        print(
            arm.ljust(22)
            + fmt("all")
            + "  |"
            + fmt("pres").rjust(17)
            + "  |"
            + fmt("chg").rjust(16)
        )


if __name__ == "__main__":
    main()
