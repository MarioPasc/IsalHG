"""Calibration + convergence check for the CV intrinsic-dimension estimator.

(a) Ground truth: known-rank Euclidean clouds at N=85 -> does CV recover D?
(b) Convergence: subsample the real Stratum A D_I matrix -> does D_hat depend on N?
"""

from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore")

from experiments.article.analysis.mds import cv_dimension_selection

DMAT = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/T-M7d/d_matrix/stratum_a")


def euclid_D(X):
    d2 = ((X[:, None, :] - X[None, :, :]) ** 2).sum(-1)
    return np.sqrt(np.maximum(d2, 0))


def main():
    rng = np.random.default_rng(0)

    print("=== (a) CALIBRATION: known-rank Euclidean clouds, N=85 ===")
    print(f"{'true D':>8}{'noise':>8}{'D_hat (CV)':>12}")
    for true_d in [2, 3, 5, 10, 17, 25]:
        for noise in [0.0, 0.1]:
            X = rng.normal(size=(85, true_d))
            D = euclid_D(X)
            if noise > 0:
                E = rng.normal(scale=noise * D[D > 0].mean(), size=D.shape)
                E = np.abs((E + E.T) / 2)
                np.fill_diagonal(E, 0)
                D = D + E
            dh, _ = cv_dimension_selection(D, rng_seed=0)
            print(f"{true_d:>8}{noise:>8.2f}{dh:>12}")

    print("\n=== (b) CONVERGENCE: subsample the real Stratum A d_I matrix ===")
    D_full = np.load(DMAT / "seed0" / "isalhg_levenshtein" / "D.npy")
    N = D_full.shape[0]
    print(f"full N = {N}")
    print(f"{'N_sub':>8}{'D_hat mean':>12}{'sd':>8}{'reps':>6}")
    for n_sub in [30, 45, 60, 75, 85]:
        vals = []
        for rep in range(8 if n_sub < N else 1):
            idx = rng.choice(N, n_sub, replace=False) if n_sub < N else np.arange(N)
            dh, _ = cv_dimension_selection(D_full[np.ix_(idx, idx)], rng_seed=rep)
            vals.append(dh)
        v = np.array(vals, float)
        print(f"{n_sub:>8}{v.mean():>12.1f}{v.std():>8.1f}{len(v):>6}")

    print("\n=== (c) same, for competitors at full N=85 ===")
    print(f"{'representation':<24}{'D_hat':>8}{'params/constraints':>20}")
    for rep in [
        "isalhg_levenshtein",
        "netlsd_l2",
        "degree_seq_l1",
        "hypergraph_wl_l1",
        "hpd_jsd",
        "nauty_levi_edit",
        "hypercot",
    ]:
        f = DMAT / "seed0" / rep / "D.npy"
        if not f.exists():
            continue
        D = np.load(f)
        dh, errs = cv_dimension_selection(D, rng_seed=0)
        ratio = (N * dh) / (N * (N - 1) / 2)
        print(f"{rep:<24}{dh:>8}{ratio:>20.3f}")


if __name__ == "__main__":
    main()
