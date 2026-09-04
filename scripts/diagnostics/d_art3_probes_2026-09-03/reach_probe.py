"""G-L3 reach probe + ball-coverage consensus over Sigma_HG(3) token-Levenshtein balls.

TASK 1: for each profile, the reach r in {1,2} at which a target's isomorphism class
        appears among the canonical keys of S2H(B_r(w*_c(origin))), for
        origin = M0 (centre->copy) and origin = K_j (copy->centre, copy->copy).
TASK 2: ball-coverage consensus -- cov_r(M) = #{i : class(K_i) in decode(B_r(w*_c(M)))}.

Profiles, centres and copies are regenerated from the pilot seeds (deterministic;
each rebuild is asserted against the stored C_med).
"""

from __future__ import annotations

import json
import random
import time
from pathlib import Path

import numpy as np
import pilot_consensus as P

from isalhg.core.instructions import serialize
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.core.string_to_hypergraph import string_to_hypergraph

HERE = Path(__file__).resolve().parent
ALPHA = tuple(P.ALPHABET)
DEADLINE = time.perf_counter() + 3200.0  # hard stop inside the 60 min budget
CAND_CAP = 200
COPY_ORIGIN_B2_PROFILES = 3  # profiles per cell that get copy-origin radius-2 balls
ISOCOUNT_B2_PROFILES = 2  # profiles per cell that get the expensive B_2 iso-class census
TARGETS = ["M0", *[f"K{i}" for i in range(P.N_COPIES)]]


def out_of_time() -> bool:
    return time.perf_counter() > DEADLINE


def ball1(w: tuple) -> set[tuple]:
    """Every token word at token-Levenshtein distance <= 1 from ``w`` (includes ``w``)."""
    out = {w}
    L = len(w)
    for i in range(L):
        out.add(w[:i] + w[i + 1 :])
        pre, post = w[:i], w[i + 1 :]
        for a in ALPHA:
            out.add(pre + (a,) + post)
    for i in range(L + 1):
        pre, post = w[:i], w[i:]
        for a in ALPHA:
            out.add(pre + (a,) + post)
    return out


def invariant(H: SparseHypergraph) -> tuple:
    """Cheap iso-invariant prefilter: (n, m, degree sequence, arity sequence)."""
    return (
        H.n_nodes,
        H.n_edges,
        tuple(sorted(H.degree(v) for v in range(H.n_nodes))),
        tuple(sorted(len(e) for e in H.hyperedges())),
    )


class ProfileScanner:
    """Radius-r ball scans against one profile's eight target iso-classes, memoized."""

    def __init__(self, keys: dict[str, str], invs: set[tuple]) -> None:
        self.key_to_id = {v: k for k, v in keys.items()}
        self.invs = invs
        self.memo: dict[tuple[str, int], dict] = {}

    def scan(self, origin_key: str, radius: int, *, census: bool = False) -> dict:
        hit = self.memo.get((origin_key, radius))
        if hit is not None and (not census or hit.get("n_iso") is not None):
            return hit
        t0 = time.perf_counter()
        found: set[str] = set()
        seen_labelled: set[tuple] = set()
        iso: set[str] = set()
        n_words = 0
        n_empty = 0

        def consume(w: tuple) -> None:
            nonlocal n_words, n_empty
            n_words += 1
            H = string_to_hypergraph(serialize(w), k=P.K)
            if H.n_edges == 0:
                n_empty += 1
                return
            if not census and invariant(H) not in self.invs:
                return
            lk = P._key(H)
            if lk in seen_labelled:
                return
            seen_labelled.add(lk)
            ck = P.encode_hg(H)[0]
            if census:
                iso.add(ck)
            tid = self.key_to_id.get(ck)
            if tid is not None:
                found.add(tid)

        w0 = tuple(P.parse(origin_key))
        B1 = ball1(w0)
        if radius == 1:
            for w in B1:
                consume(w)
        else:
            seen_words: set[tuple] = set()
            for w in B1:
                for w2 in ball1(w):
                    if w2 not in seen_words:
                        seen_words.add(w2)
                        consume(w2)
        res = dict(
            found=sorted(found),
            n_words=n_words,
            n_empty=n_empty,
            n_iso=len(iso) if census else None,
            secs=time.perf_counter() - t0,
        )
        self.memo[(origin_key, radius)] = res
        return res


def build_profile(rec: dict) -> dict:
    n, m, t = rec["n"], rec["m"], rec["t"]
    M0 = P.make_centre(n, m, random.Random(rec["centre_seed"]))
    crng = random.Random(rec["profile_seed"])
    corpus = [P.make_copy(M0, t, crng) for _ in range(P.N_COPIES)]
    D = np.array([[float(P.d_I(a, b)) for b in corpus] for a in corpus])
    j = int(np.argmin(D.sum(axis=1)))
    assert P.cost(corpus[j], corpus) == rec["C_med"], "profile did not reproduce from seeds"
    keys = {"M0": P.encode_hg(M0)[0]}
    for i, Ki in enumerate(corpus):
        keys[f"K{i}"] = P.encode_hg(Ki)[0]
    return dict(
        n=n,
        m=m,
        t=t,
        M0=M0,
        corpus=corpus,
        medoid=corpus[j],
        j=j,
        keys=keys,
        invs={invariant(M0), *(invariant(Ki) for Ki in corpus)},
    )


def main() -> None:
    recs = json.loads((HERE / "pilot_consensus_results.json").read_text())["records"]
    task1: list[dict] = []
    task2: list[dict] = []
    t_start = time.perf_counter()
    copy_b2_done = {(8, 10): 0, (10, 12): 0}
    census_done = {(8, 10): 0, (10, 12): 0}

    for ridx, rec in enumerate(recs):
        pr = build_profile(rec)
        cell = (pr["n"], pr["m"])
        cid = rec["centre_seed"] % 1000
        sc = ProfileScanner(pr["keys"], pr["invs"])
        med_id = f"K{pr['j']}"
        do_copy_b2 = copy_b2_done[cell] < COPY_ORIGIN_B2_PROFILES and pr["t"] == 1
        do_census = census_done[cell] < ISOCOUNT_B2_PROFILES and pr["t"] == 1

        # ---- TASK 1 ----------------------------------------------------------
        entry = dict(n=pr["n"], m=pr["m"], t=pr["t"], centre=cid, medoid_id=med_id, origins={})
        for oid in TARGETS:
            ok = pr["keys"][oid]
            r1 = sc.scan(ok, 1, census=True)
            e = dict(
                r1_found=[x for x in r1["found"] if x != oid],
                B1_words=r1["n_words"],
                B1_iso=r1["n_iso"],
                B1_secs=r1["secs"],
            )
            if (oid == "M0" or do_copy_b2) and not out_of_time():
                cens = do_census and oid == "M0"
                r2 = sc.scan(ok, 2, census=cens)
                e.update(
                    r2_found=[x for x in r2["found"] if x != oid],
                    B2_words=r2["n_words"],
                    B2_iso=r2["n_iso"],
                    B2_secs=r2["secs"],
                )
            entry["origins"][oid] = e
        if do_copy_b2:
            copy_b2_done[cell] += 1
        if do_census:
            census_done[cell] += 1
        task1.append(entry)

        # ---- TASK 2 ----------------------------------------------------------
        pool: dict[str, SparseHypergraph] = {}
        for w in ball1(tuple(P.parse(pr["keys"][med_id]))):
            H = string_to_hypergraph(serialize(w), k=P.K)
            if H.n_edges:
                pool.setdefault(P.encode_hg(H)[0], H)
        pool_keys = sorted(pool)
        if len(pool_keys) > CAND_CAP:
            pool_keys = sorted(
                random.Random(rec["profile_seed"] + 31337).sample(pool_keys, CAND_CAP)
            )
        cand: dict[str, SparseHypergraph] = {"M0": pr["M0"]}
        for i, Ki in enumerate(pr["corpus"]):
            cand[f"K{i}"] = Ki
        known = set(pr["keys"].values())
        for kk in pool_keys:
            if kk not in known:
                cand[f"B1:{kk[:10]}"] = pool[kk]
                known.add(kk)

        copies = {f"K{i}" for i in range(P.N_COPIES)}
        cov1: dict[str, int] = {}
        f1: dict[str, list[str]] = {}
        for cid_, H in cand.items():
            res = sc.scan(P.encode_hg(H)[0], 1)
            hit = sorted(set(res["found"]) & copies)
            f1[cid_] = hit
            cov1[cid_] = len(hit)

        maxcov = max(cov1.values())
        ties = [k for k, v in cov1.items() if v == maxcov]
        best_no = max(v for k, v in cov1.items() if k != "M0")
        top5 = [
            k
            for k, _ in sorted(
                ((k, v) for k, v in cov1.items() if k not in ("M0", med_id)), key=lambda kv: -kv[1]
            )[:5]
        ]

        cov2: dict[str, int] = {}
        trunc: dict[str, int] = {}
        for cid_ in ["M0", med_id, *top5]:
            if out_of_time():
                break
            res2 = sc.scan(P.encode_hg(cand[cid_])[0], 2)
            hit2 = set(res2["found"]) & copies
            cov2[cid_] = len(hit2)
            a1 = set(f1[cid_])
            trunc[cid_] = sum(
                1 if f"K{i}" in a1 else (2 if f"K{i}" in hit2 else 3) for i in range(P.N_COPIES)
            )

        task2.append(
            dict(
                n=pr["n"],
                m=pr["m"],
                t=pr["t"],
                centre=cid,
                medoid_id=med_id,
                n_candidates=len(cand),
                pool_iso=len(pool),
                cov1=cov1,
                cov2=cov2,
                trunc=trunc,
                cov1_M0=cov1["M0"],
                cov1_med=cov1[med_id],
                cov1_best_non_oracle=best_no,
                M0_is_max=(cov1["M0"] == maxcov),
                n_ties=len(ties),
                unique_max=(cov1["M0"] == maxcov and len(ties) == 1),
            )
        )
        m0e = entry["origins"]["M0"]
        print(
            f"[{ridx + 1}/24] ({pr['n']},{pr['m']}) t={pr['t']} c={cid}: "
            f"M0->copies r1={len(m0e['r1_found'])}/7 r2={len(m0e.get('r2_found', []))}/7 | "
            f"cov1 M0={cov1['M0']} med={cov1[med_id]} bestNO={best_no} ties={len(ties)} | "
            f"cov2 M0={cov2.get('M0')} med={cov2.get(med_id)} | "
            f"{time.perf_counter() - t_start:.0f}s",
            flush=True,
        )
        if out_of_time():
            print("DEADLINE reached; stopping early", flush=True)
            break

    (HERE / "reach_results.json").write_text(
        json.dumps(
            dict(
                task1=task1,
                task2=task2,
                wall_clock=time.perf_counter() - t_start,
                stats=dict(
                    n_canon=P.STATS.n_canon,
                    canon_time=P.STATS.canon_time,
                    max_canon=P.STATS.max_canon,
                    dnf=P.STATS.dnf,
                ),
            ),
            indent=1,
        )
    )
    print(
        f"\nwall clock {time.perf_counter() - t_start:.0f}s; canon={P.STATS.n_canon} "
        f"max={P.STATS.max_canon:.3f}s DNF={P.STATS.dnf}"
    )


if __name__ == "__main__":
    main()
