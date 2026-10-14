"""Probe C7: does the distance between consecutive versions track the true change?

For every natural consecutive pair (a, b) of an NDC quarterly series the corpus
records ``delta``, the exact fact-level difference computed from the constant
identities (which no representation sees). Per arm, Spearman's rho between
d(a, b) and delta over all pairs, with a cluster bootstrap over classes (pairs
of one class are not independent) and the bootstrapped paired difference
against the ordered-walk arm.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from experiments.tkde import corpora as C  # noqa: E402

D_ROOT = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE")
OURS = "isal_ow_struct"
ARMS = (
    OURS,
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


def rho(x: np.ndarray, y: np.ndarray) -> float:
    r = spearmanr(x, y).statistic
    return float(r) if np.isfinite(r) else float("nan")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--collection", default="ndc_classes")
    ap.add_argument("--extra-matrix-dir", type=Path, default=None)
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--stratum", choices=["all", "pres", "chg"], default="all")
    args = ap.parse_args()
    col = C.load_collection(args.collection, root=D_ROOT)
    idx = {m: i for i, m in enumerate(C.member_ids(col))}
    pairs = C.consecutive_pairs(col)
    if args.stratum != "all":
        want = args.stratum == "pres"
        pairs = [p for p in pairs if bool(p["constant_preserving"]) == want]
    a = np.array([idx[p["a"]] for p in pairs])
    b = np.array([idx[p["b"]] for p in pairs])
    delta = np.array([float(p["delta"]) for p in pairs])
    cls = np.array([p["class_id"] for p in pairs])
    classes = np.unique(cls)
    members = {c: np.where(cls == c)[0] for c in classes}
    rng = np.random.default_rng(args.seed)
    boots = [
        np.concatenate([members[c] for c in rng.choice(classes, size=len(classes))])
        for _ in range(args.boot)
    ]
    dist = {}
    for arm in ARMS:
        path = D_ROOT / "matrices" / args.collection / f"{arm}.npy"
        if not path.exists() and args.extra_matrix_dir is not None:
            path = args.extra_matrix_dir / args.collection / f"{arm}.npy"
        if not path.exists():
            continue
        M = np.load(path, mmap_mode="r")
        dist[arm] = np.array([M[i, j] for i, j in zip(a, b)], dtype=np.float64)
    print(
        f"{args.collection} stratum={args.stratum}: {len(pairs)} pairs, {len(classes)} classes, "
        f"delta median {np.median(delta):.0f} (0: {int(np.sum(delta == 0))})"
    )
    ours_boot = np.array([rho(dist[OURS][s], delta[s]) for s in boots])
    print("arm".ljust(22) + "rho".rjust(7) + "   95% CI".ljust(18) + "rho(w°)-rho  95% CI")
    for arm, d in dist.items():
        r = rho(d, delta)
        rb = np.array([rho(d[s], delta[s]) for s in boots])
        lo, hi = np.nanpercentile(rb, [2.5, 97.5])
        line = arm.ljust(22) + f"{r:7.3f}   [{lo:.3f}, {hi:.3f}]"
        if arm != OURS:
            diff = ours_boot - rb
            dlo, dhi = np.nanpercentile(diff, [2.5, 97.5])
            line += f"   {rho(dist[OURS], delta) - r:+.3f} [{dlo:+.3f}, {dhi:+.3f}]"
        print(line)


if __name__ == "__main__":
    main()
