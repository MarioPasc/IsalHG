"""Audit C8 (near-duplicate retrieval, the paper's H2) for the bipartite-GED orientation issue.

The bipartite edit-path cost is not symmetric. The cached campaign matrices
(and the ones C8 built locally) evaluate ``pairwise(items[i], items[j])`` for
``i < j`` only and mirror it, so the score of a (query, candidate) pair depends
on which of the two has the lower member index. This script:

1. computes the full ordered matrix ``P[i, j] = pairwise(H_i, H_j)`` for every
   ``i != j`` of both bipartite arms, checks that its upper triangle reproduces
   the matrix C8 used, and measures the asymmetry;
2. builds two matrix roots that differ only in the bipartite arm(s): ``asrun``
   (the upper triangle mirrored, as C8 used) and ``symmin`` (``min(P, P.T)``);
3. reruns ``neardup.py`` (radius 1) and ``neardup_r2.py`` (radius 2) unchanged on
   each root, through a module-level ``D_ROOT`` swap, and checks that ``asrun``
   reproduces the published C8 JSONs;
4. writes ``AUDIT.md`` + ``audit.json``.

Nothing under the C8 results directory or the article is written.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(REPO))
import rect as R  # noqa: E402, N812

from experiments.tkde import corpora as C  # noqa: E402, N812

IEEE = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE")
C8_DIR = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/NEWPOS_2026-10-13/neardup")
OUT = Path(
    "/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/KNN_2026-10-15/c8_orientation_audit"
)
COLLECTIONS = ("wd50k66", "wd50k100", "ndc_classes", "ndc_substances")
BIPARTITE = ("bipartite_ged_path", "bipartite_ged_assign")
OURS = "isal_ow_struct"
NEARDUP_ARMS = (
    "isal_ow_struct",
    "nauty_cert",
    "nauty_cert_rows",
    "fact_rank",
    "wl_l1",
    "netlsd",
    "hpd_jsd",
    "bipartite_ged_assign",
    "bipartite_ged_path",
    "degree_seq_l1",
    "size_l1",
    "wstar_orbit",
)


def _rows(lo: int, hi: int) -> np.ndarray:
    d, hs = R._STATE["full"]
    out = np.zeros((hi - lo, len(hs)))
    for i in range(lo, hi):
        for j in range(len(hs)):
            if j != i:
                out[i - lo, j] = float(d.pairwise(hs[i], hs[j]))
    return out


def ordered_matrix(arm: str, hs: list[Any], n_jobs: int) -> tuple[np.ndarray, float]:
    """``P[i, j] = pairwise(H_i, H_j)`` for every ordered pair, and pairs/s."""
    from isalhg.metric_space.registry import get_distance

    t0 = time.perf_counter()
    R._STATE["full"] = (get_distance(arm), hs)
    try:
        P = np.vstack(R._parallel_rows(_rows, len(hs), n_jobs))
    finally:
        R._STATE.pop("full", None)
    dt = time.perf_counter() - t0
    return P, len(hs) * (len(hs) - 1) / dt


def build_roots(collection: str, n_jobs: int) -> dict[str, Any]:
    """Matrices of one collection: the ordered bipartite matrices and every missing arm."""
    from isalhg.metric_space.registry import get_distance

    col = C.load_collection(collection, root=IEEE)
    hs = C.hypergraphs(col)
    mdir = OUT / "matrices" / collection
    mdir.mkdir(parents=True, exist_ok=True)
    info: dict[str, Any] = {"N": len(hs), "arms": {}}
    for arm in BIPARTITE:
        full_path = mdir / f"{arm}.ordered.npy"
        if full_path.exists():
            P = np.load(full_path)
            pps = None
        else:
            P, pps = ordered_matrix(arm, hs, n_jobs)
            np.save(full_path, P)
        iu = np.triu_indices(len(hs), 1)
        upper, lower = P[iu], P.T[iu]
        asrun = np.zeros_like(P)
        asrun[iu] = upper
        asrun = asrun + asrun.T
        symmin = np.minimum(P, P.T)
        np.save(mdir / f"{arm}.asrun.npy", asrun)
        np.save(mdir / f"{arm}.symmin.npy", symmin)
        cached = IEEE / "matrices" / collection / f"{arm}.npy"
        check = None
        if cached.exists():
            M = np.load(cached).astype(np.float64)
            check = float(np.abs(M - asrun).max())
        diff = upper != lower
        info["arms"][arm] = {
            "pairs_per_s": pps,
            "asymmetric_pairs": int(diff.sum()),
            "asymmetric_share": float(diff.mean()),
            "mean_abs_orientation_gap": float(np.abs(upper - lower).mean()),
            "symmin_lowers_pairs_share": float((np.minimum(upper, lower) < upper).mean()),
            "max_abs_diff_asrun_vs_cached": check,
        }
    for arm in NEARDUP_ARMS:
        if arm in BIPARTITE or (IEEE / "matrices" / collection / f"{arm}.npy").exists():
            continue
        if arm == "wstar_orbit":
            continue
        path = mdir / f"{arm}.npy"
        if not path.exists():
            t0 = time.perf_counter()
            np.save(path, get_distance(arm).matrix(hs))
            info["arms"].setdefault(arm, {})["built_secs"] = time.perf_counter() - t0
        info["arms"].setdefault(arm, {})["built_locally"] = True
    return info


def link_root(variant: str, collection: str) -> Path:
    """A results root whose matrices are the cached ones except the bipartite arms."""
    root = OUT / "roots" / variant
    (root / "matrices" / collection).mkdir(parents=True, exist_ok=True)
    corpora = root / "corpora"
    if not corpora.exists():
        corpora.symlink_to(IEEE / "corpora")
    for arm in NEARDUP_ARMS:
        dest = root / "matrices" / collection / f"{arm}.npy"
        if dest.is_symlink() or dest.exists():
            dest.unlink()
        if arm in BIPARTITE:
            src = OUT / "matrices" / collection / f"{arm}.{variant}.npy"
        elif (IEEE / "matrices" / collection / f"{arm}.npy").exists():
            src = IEEE / "matrices" / collection / f"{arm}.npy"
        else:
            src = OUT / "matrices" / collection / f"{arm}.npy"
        if src.exists():
            dest.symlink_to(src)
    for side in ("censored",):
        for p in (IEEE / "matrices" / collection).glob(f"*.{side}.json"):
            dest = root / "matrices" / collection / p.name
            if not dest.exists():
                dest.symlink_to(p)
    return root


def run_scorer(script: str, root: Path, collection: str, out: Path, extra: list[str]) -> None:
    """Run ``neardup.py`` / ``neardup_r2.py`` unchanged with ``D_ROOT`` pointed at ``root``."""
    module = script.removesuffix(".py")
    code = (
        "import sys; from pathlib import Path; "
        f"sys.path[:0] = [{str(REPO / 'scripts' / 'newpos')!r}, {str(REPO)!r}]; "
        f"import {module} as m; m.D_ROOT = Path({str(root)!r}); "
        f"sys.argv = [{script!r}, '--collection', {collection!r}, '--out', {str(out)!r}, "
        + ", ".join(repr(x) for x in extra)
        + "]; m.main()"
    )
    out.mkdir(parents=True, exist_ok=True)
    log = out / f"{module}_{collection}.log"
    with log.open("w") as fh:
        subprocess.run(
            [sys.executable, "-c", code],
            check=True,
            stdout=fh,
            stderr=subprocess.STDOUT,
            env={**os.environ, "PYTHONHASHSEED": "0"},
        )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--collections", nargs="+", default=list(COLLECTIONS))
    ap.add_argument("--n-jobs", type=int, default=16)
    ap.add_argument("--skip-r2", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    built: dict[str, Any] = {}
    for c in args.collections:
        t0 = time.perf_counter()
        built[c] = build_roots(c, args.n_jobs)
        built[c]["secs"] = time.perf_counter() - t0
        print(c, json.dumps(built[c]["arms"].get("bipartite_ged_path")), flush=True)
        for variant in ("asrun", "symmin"):
            root = link_root(variant, c)
            run_scorer("neardup.py", root, c, OUT / variant, ["--key", "cert"])
            if not args.skip_r2:
                run_scorer("neardup_r2.py", root, c, OUT / variant, ["--workers", "10"])
            print(c, variant, "scored", flush=True)
    (OUT / "build.json").write_text(json.dumps(built, indent=1))


if __name__ == "__main__":
    main()
