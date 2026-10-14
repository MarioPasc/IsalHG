"""Probe C2: how well each representation's distance supports exact metric search.

Reads the cached full distance matrices of a collection and reports, per arm:
the intrinsic dimensionality rho = mu^2 / (2 sigma^2) of the pairwise-distance
distribution (Chavez, Navarro, Baeza-Yates, Marroquin 2001), and the number of
distance evaluations an exact pivot-based k-NN search (LAESA-style, best-first
on the pivot lower bound) needs per query, as a fraction of the collection.
The pivot lower bound is valid only for distances obeying the triangle
inequality; for a non-metric arm the search may return a wrong answer, and the
probe counts how often it does.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

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


def load(collection: str, arm: str) -> tuple[np.ndarray, np.ndarray]:
    """Return the matrix and a boolean mask of usable (uncensored) members."""
    base = D_ROOT / "matrices" / collection
    M = np.load(base / f"{arm}.npy").astype(np.float64)
    keep = np.ones(M.shape[0], dtype=bool)
    cens = base / f"{arm}.censored.json"
    if cens.exists():
        info = json.loads(cens.read_text())
        ids = info["member_ids"]
        bad = set(info["censored_ids"])
        if len(ids) == M.shape[0]:
            keep = np.array([i not in bad for i in ids])
        else:
            # matrix holds only the surviving members
            keep = np.ones(M.shape[0], dtype=bool)
    return M, keep


def rho(M: np.ndarray) -> tuple[float, float, float]:
    iu = np.triu_indices(M.shape[0], 1)
    d = M[iu]
    mu, sd = float(d.mean()), float(d.std())
    return mu * mu / (2 * sd * sd), mu, sd


def pivots_maxsep(M: np.ndarray, p: int, rng: np.random.Generator) -> list[int]:
    first = int(rng.integers(M.shape[0]))
    piv = [first]
    mind = M[first].copy()
    for _ in range(p - 1):
        nxt = int(np.argmax(mind))
        piv.append(nxt)
        mind = np.minimum(mind, M[nxt])
    return piv


def knn_cost(M: np.ndarray, piv: list[int], queries: np.ndarray, k: int) -> tuple[float, float]:
    """Mean fraction of objects evaluated and fraction of queries answered wrongly."""
    N = M.shape[0]
    P = M[:, piv]  # N x p
    evals, wrong = [], 0
    for q in queries:
        lb = np.abs(P - P[q]).max(axis=1)  # pivot lower bound on d(q, x)
        lb[q] = np.inf  # the query is not its own neighbour
        order = np.argsort(lb, kind="stable")
        best: list[float] = []
        n_eval = len(piv)
        for x in order:
            if lb[x] == np.inf:
                break
            if len(best) == k and lb[x] > best[-1]:
                break
            if x in piv:
                dx = M[q, x]
            else:
                dx = M[q, x]
                n_eval += 1
            best.append(dx)
            best.sort()
            best = best[:k]
        truth = np.sort(np.delete(M[q], q))[:k]
        if not np.allclose(np.array(best), truth):
            wrong += 1
        evals.append(n_eval / (N - 1))
    return float(np.mean(evals)), wrong / len(queries)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--collection", default="wd50k66")
    ap.add_argument("--queries", type=int, default=400)
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--pivots", type=int, nargs="+", default=[8, 32])
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--subset", default=None, help="optional .npy boolean mask over members")
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    print(f"collection={args.collection} k={args.k} queries={args.queries} seed={args.seed}")
    header = "arm".ljust(22) + "N".rjust(6) + "rho".rjust(8) + "mu".rjust(9) + "sd".rjust(8)
    for p in args.pivots:
        header += f"  eval@p{p}".rjust(11) + f" wrong@p{p}".rjust(10)
    print(header)
    for arm in ARMS:
        try:
            M, keep = load(args.collection, arm)
        except FileNotFoundError:
            continue
        if args.subset:
            keep = keep & np.load(args.subset)
        M = M[np.ix_(keep, keep)]
        r, mu, sd = rho(M)
        line = arm.ljust(22) + f"{M.shape[0]:6d}{r:8.2f}{mu:9.3f}{sd:8.3f}"
        qrng = np.random.default_rng(args.seed + 1)
        queries = qrng.choice(M.shape[0], size=min(args.queries, M.shape[0]), replace=False)
        for p in args.pivots:
            piv = pivots_maxsep(M, p, rng)
            frac, wrong = knn_cost(M, piv, queries, args.k)
            line += f"{frac:11.3f}{wrong:10.3f}"
        print(line, flush=True)


if __name__ == "__main__":
    main()
