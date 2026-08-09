"""Diagnostic: is the Stratum-A A2/A3 ranking driven by corpus size heterogeneity?

Rebuilds the 85-item Stratum A corpus, computes trivial size-only distances,
and runs the same A2 (PAM ARI) / A3 (kNN AUC-OvR@5) pipeline on them.
Also reports Spearman(D_rep, size gap) per representation.
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

warnings.filterwarnings("ignore")

# Stratum A results were archived at T-M4b (superseded/ convention); the
# probe's forensic reproduction reads the archived matrices.
RESULTS = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/superseded/T-M7d_stratum_a")
DMAT = RESULTS / "d_matrix" / "stratum_a"
REPS = [
    "isalhg_levenshtein",
    "hypergraph_wl_l1",
    "netlsd_l2",
    "hpd_jsd",
    "nauty_levi_edit",
    "degree_seq_l1",
    "hypercot",
]


def build_corpus(seed_value: int):
    from isalhg.datasets.synthetic.known_design_catalog import build_stratum_a_corpus

    meta = json.loads((DMAT / f"seed{seed_value}" / REPS[0] / "meta.json").read_text())
    ds = build_stratum_a_corpus(
        members_per_family=meta["members_per_family"],
        n_edits=meta["n_edits"],
        seed_value=seed_value,
        admitted_ids=frozenset(meta["admitted_ids"]),
    )
    items = list(ds)
    return items, meta


def descriptors(items):
    from isalhg.core.canonical import canonical_string

    rows = []
    for it in items:
        H = it.hypergraph
        edges = [tuple(H.members(e)) for e in H.edges()]
        n = H.n_nodes
        m = H.n_edges
        inc = sum(len(e) for e in edges)
        kmax = max((len(e) for e in edges), default=0)
        try:
            w = canonical_string(H)
            wlen = len(w) if isinstance(w, str) else len(list(w))
        except Exception:
            wlen = np.nan
        rows.append(
            dict(
                n=n,
                m=m,
                inc=inc,
                kmax=kmax,
                wlen=wlen,
                fam=it.extra.get("family_label", it.extra.get("family_index")),
            )
        )
    return rows


def pam_ari(D, labels, k, rng_seed=42):
    import kmedoids
    from sklearn.metrics import adjusted_rand_score

    best, best_loss = None, np.inf
    for s in range(10):
        r = kmedoids.fasterpam(D, k, random_state=rng_seed + s)
        if r.loss < best_loss:
            best_loss, best = r.loss, r
    return float(adjusted_rand_score(labels, np.asarray(best.labels)))


def knn_auc(D, labels, k=5, n_folds=5, rng_seed=42):
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import StratifiedKFold
    from sklearn.neighbors import KNeighborsClassifier

    labels = np.asarray(labels)
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=rng_seed)
    proba = np.zeros((len(labels), len(np.unique(labels))))
    classes = np.unique(labels)
    for tr, te in skf.split(np.zeros(len(labels)), labels):
        clf = KNeighborsClassifier(n_neighbors=k, metric="precomputed")
        clf.fit(D[np.ix_(tr, tr)], labels[tr])
        p = clf.predict_proba(D[np.ix_(te, tr)])
        for j, c in enumerate(clf.classes_):
            proba[te, np.searchsorted(classes, c)] = p[:, j]
    return float(roc_auc_score(labels, proba, multi_class="ovr", average="macro"))


def main():
    seeds = [0, 1, 2, 3, 4]
    out = {r: {"ari": [], "auc": [], "rho_size": [], "rho_wlen": []} for r in REPS}
    for name in ["SIZE_inc", "SIZE_nm", "SIZE_m"]:
        out[name] = {"ari": [], "auc": [], "rho_size": [], "rho_wlen": []}

    desc0 = None
    for sd in seeds:
        items, meta = build_corpus(sd)
        d = descriptors(items)
        if desc0 is None:
            desc0 = d
        labels = np.array([r["fam"] for r in d])
        inc = np.array([r["inc"] for r in d], float)
        nn = np.array([r["n"] for r in d], float)
        mm = np.array([r["m"] for r in d], float)
        wl = np.array([r["wlen"] for r in d], float)

        D_inc = np.abs(inc[:, None] - inc[None, :])
        D_nm = np.abs(nn[:, None] - nn[None, :]) + np.abs(mm[:, None] - mm[None, :])
        D_m = np.abs(mm[:, None] - mm[None, :])
        D_wl = np.abs(wl[:, None] - wl[None, :])
        iu = np.triu_indices(len(labels), 1)

        k = len(set(labels))
        for nm, Dx in [("SIZE_inc", D_inc), ("SIZE_nm", D_nm), ("SIZE_m", D_m)]:
            out[nm]["ari"].append(pam_ari(Dx, labels, k))
            out[nm]["auc"].append(knn_auc(Dx, labels))

        for rep in REPS:
            f = DMAT / f"seed{sd}" / rep / "D.npy"
            if not f.exists():
                continue
            D = np.load(f)
            out[rep]["ari"].append(pam_ari(D, labels, k))
            out[rep]["auc"].append(knn_auc(D, labels))
            out[rep]["rho_size"].append(spearmanr(D[iu], D_inc[iu]).statistic)
            out[rep]["rho_wlen"].append(spearmanr(D[iu], D_wl[iu]).statistic)

    print("\n=== CORPUS SIZE HETEROGENEITY (seed 0, 17 families) ===")
    import collections

    byfam = collections.defaultdict(list)
    for r in desc0:
        byfam[r["fam"]].append(r)
    print(f"{'family':<18}{'n':>5}{'m':>5}{'inc':>6}{'|w*|':>7}{'k':>4}")
    for fam, rs in sorted(byfam.items()):
        r = rs[0]
        print(f"{str(fam):<18}{r['n']:>5}{r['m']:>5}{r['inc']:>6}{r['wlen']:>7}{r['kmax']:>4}")
    incs = np.array([r["inc"] for r in desc0], float)
    wls = np.array([r["wlen"] for r in desc0], float)
    print(
        f"\nincidence mass: min={incs.min():.0f} max={incs.max():.0f} "
        f"mean={incs.mean():.1f} CV={incs.std() / incs.mean():.3f}"
    )
    print(
        f"|w*_c|        : min={wls.min():.0f} max={wls.max():.0f} "
        f"mean={wls.mean():.1f} CV={wls.std() / wls.mean():.3f}"
    )

    print(f"\n=== A2 ARI / A3 AUC@5 over {len(seeds)} seeds (mean ± sd) ===")
    print(f"{'representation':<24}{'ARI':>16}{'AUC@5':>16}{'rho(D,Dsize)':>15}{'rho(D,D|w*|)':>15}")
    rows = []
    for rep, v in out.items():
        if not v["ari"]:
            continue
        a, u = np.array(v["ari"]), np.array(v["auc"])
        rs = np.mean(v["rho_size"]) if v["rho_size"] else np.nan
        rw = np.mean(v["rho_wlen"]) if v["rho_wlen"] else np.nan
        rows.append((rep, a.mean(), a.std(), u.mean(), u.std(), rs, rw))
    for rep, am, asd, um, usd, rs, rw in sorted(rows, key=lambda x: -x[1]):
        print(f"{rep:<24}{am:>9.3f}±{asd:<5.3f}{um:>9.3f}±{usd:<5.3f}{rs:>15.3f}{rw:>15.3f}")


if __name__ == "__main__":
    main()
