"""One-edit near-duplicate detection in a KB collection, scored for every representation.

Task. Among the non-isomorphic pairs of a collection, find those one single-fact
edit apart (insert a fact, delete a fact, add a constant to a fact, remove a
constant from a fact; Section 3 of the paper). Isomorphic pairs are the census's
business and are excluded.

Ground truth, exact and representation-free. For every member K, enumerate its
down-neighbours -- delete one fact, or remove one constant from one fact of arity
at least two -- drop constants left in no fact, and discard results that are
disconnected or repeat a fact. Up-edits are the reverse of down-edits, so a pair
is positive iff one member is isomorphic to a down-neighbour of the other.
Isomorphism is decided by a complete invariant: the nauty certificate of the
coloured incidence graph (default) or the ordered-walk fingerprint; the two must
give the same truth, and ``--key both`` checks it.

Scores per representation (the cached distance matrix of the collection):
global pairwise average precision; per query (a member with at least one
positive partner, ranking every non-isomorphic other member by distance) the
reciprocal rank of its nearest positive, hit@1, hit@10 and average precision.
Ties are resolved by expectation (rank) or entered as a block (precision), never
in the representation's favour. Uncertainty: bootstrap over queries (clustered
by class on the NDC series); ours against each competitor: one-sided paired
Wilcoxon signed-rank on per-query values, Holm-corrected, rank-biserial effect.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import wilcoxon

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from experiments.tkde import corpora as C  # noqa: E402
from isalhg.datasets.kb.base import KBRecord, compact  # noqa: E402
from isalhg.iso_backends.isal_ordered import ordered_fingerprint  # noqa: E402
from isalhg.metric_space.registry import get_distance  # noqa: E402

D_ROOT = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE")
OURS = "isal_ow_struct"
ARMS = (
    OURS,
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


# --------------------------------------------------------------------------- truth


def _key_fn(kind: str, n_types: int, n_preds: int):
    cert = get_distance("nauty_cert")

    def key(record: KBRecord) -> Any:
        H = record.to_hypergraph(n_types=n_types, n_preds=n_preds)
        if kind == "cert":
            return cert.fingerprint(H)
        root, word = ordered_fingerprint(H)
        return (int(root), word)

    return key


def down_neighbours(record: KBRecord) -> list[tuple[str, list[tuple[int, tuple[int, ...]]]]]:
    """``(edit kind, facts)`` of every single down-edit, before compaction."""
    facts = [(int(p), tuple(sorted(int(a) for a in args))) for p, args in record.facts]
    out: list[tuple[str, list[tuple[int, tuple[int, ...]]]]] = []
    for i in range(len(facts)):
        rest = facts[:i] + facts[i + 1 :]
        if rest:
            out.append(("delete_fact", rest))
    for i, (p, args) in enumerate(facts):
        if len(args) < 2:
            continue
        for a in args:
            rest = facts[:i] + [(p, tuple(x for x in args if x != a))] + facts[i + 1 :]
            if len(set(rest)) == len(rest):
                out.append(("remove_constant", rest))
    return out


def is_star(record: KBRecord) -> bool:
    """One constant in every fact and no other constant in two facts."""
    facts = [set(args) for _, args in record.facts]
    if not facts:
        return False
    counts: dict[int, int] = defaultdict(int)
    for args in facts:
        for a in args:
            counts[a] += 1
    for root in set.intersection(*facts):
        if all(c == 1 for a, c in counts.items() if a != root):
            return True
    return False


def ground_truth(
    col: Any, key_kind: str
) -> tuple[np.ndarray, dict[tuple[int, int], dict[str, Any]]]:
    recs = col.records
    key = _key_fn(key_kind, col.n_types, col.n_preds)
    keys = [key(r) for r in recs]
    by_key: dict[Any, list[int]] = defaultdict(list)
    for i, k in enumerate(keys):
        by_key[k].append(i)
    iso_class = np.empty(len(recs), dtype=np.int64)
    for c, members in enumerate(by_key.values()):
        iso_class[members] = c
    positives: dict[tuple[int, int], dict[str, Any]] = {}
    for i, r in enumerate(recs):
        consts = {a for _, args in r.facts for a in args}
        for kind, facts in down_neighbours(r):
            sub = compact(f"{r.kb_id}~", list(r.types), facts, require_connected=True)
            if sub is None:
                continue
            for j in by_key.get(key(sub), ()):
                pair = (min(i, j), max(i, j))
                info = positives.setdefault(pair, {"kinds": set(), "pendant": False})
                info["kinds"].add(kind)
                info["pendant"] |= consts != {a for _, args in facts for a in args}
    return iso_class, positives


# --------------------------------------------------------------------------- scores


def block_ap(scores: np.ndarray, labels: np.ndarray) -> float:
    """Average precision, ascending score = more similar, tie blocks entered whole."""
    if not labels.any():
        return float("nan")
    order = np.argsort(scores, kind="stable")
    s, y = scores[order], labels[order].astype(np.int64)
    _, start = np.unique(s, return_index=True)
    ends = np.append(start[1:], len(s))
    pos_in_block = np.add.reduceat(y, start)
    tp_cum = np.cumsum(pos_in_block)
    prec_at_end = tp_cum / ends
    return float(np.sum(pos_in_block * prec_at_end) / y.sum())


def query_scores(d: np.ndarray, pos: np.ndarray) -> tuple[float, float, float, float]:
    """(reciprocal rank, hit@1, hit@10, AP) of one query, ties by expectation."""
    best = d[pos].min()
    better = int(np.sum(d < best))
    block = int(np.sum(d == best))
    k = int(np.sum(pos & (d == best)))
    # expected rank of the first positive drawn from a tie block of `block` with `k` positives
    exp_rank = 1 + better + (block - k) / (k + 1)
    hit1 = (k / block) if better == 0 else 0.0
    # P(some positive within the first 10) under a random order of the tie block
    slots = 10 - better
    if slots <= 0:
        hit10 = 0.0
    elif slots >= block:
        hit10 = 1.0
    else:
        neg = block - k
        p_none = 1.0
        for t in range(slots):
            p_none *= max(neg - t, 0) / (block - t)
        hit10 = 1.0 - p_none
    return 1.0 / exp_rank, hit1, hit10, block_ap(d, pos)


def holm(pvals: dict[str, float]) -> dict[str, float]:
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m, out, running = len(items), {}, 0.0
    for r, (name, p) in enumerate(items):
        running = max(running, min(1.0, (m - r) * p))
        out[name] = running
    return out


def rank_biserial(x: np.ndarray, y: np.ndarray) -> float:
    diff = x - y
    diff = diff[diff != 0]
    if not len(diff):
        return 0.0
    ranks = np.argsort(np.argsort(np.abs(diff))) + 1.0
    wp, wn = ranks[diff > 0].sum(), ranks[diff < 0].sum()
    return float((wp - wn) / (wp + wn))


# --------------------------------------------------------------------------- main


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--collection", default="wd50k66")
    ap.add_argument("--key", choices=["cert", "ow", "both"], default="cert")
    ap.add_argument("--extra-matrix-dir", type=Path, default=None)
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument(
        "--restrict-to-arm",
        default=None,
        help="score every arm on the members a censored arm canonicalised (e.g. wstar_orbit)",
    )
    args = ap.parse_args()
    t0 = time.perf_counter()
    col = C.load_collection(args.collection, root=D_ROOT)
    full_ids = C.member_ids(col)
    N_full = len(full_ids)
    sel = np.arange(N_full)
    if args.restrict_to_arm:
        info = json.loads(
            (
                D_ROOT / "matrices" / args.collection / f"{args.restrict_to_arm}.censored.json"
            ).read_text()
        )
        bad = set(info["censored_ids"])
        kept = [m for m in full_ids if m not in bad]
        sel = np.array([full_ids.index(m) for m in kept])
        col = C.subset(col, kept, name=col.name)
    N = len(col)
    kinds = ["cert", "ow"] if args.key == "both" else [args.key]
    truths = {k: ground_truth(col, k) for k in kinds}
    if len(kinds) == 2:
        (ic, pc), (io, po) = truths["cert"], truths["ow"]
        same_part = (
            len(set(zip(ic.tolist(), io.tolist())))
            == len(set(ic.tolist()))
            == len(set(io.tolist()))
        )
        same_pos = set(pc) == set(po)
        print(
            f"truth check cert vs ow: same partition={same_part}, same positives={same_pos} ({len(pc)} vs {len(po)})"
        )
        if not (same_part and same_pos):
            raise SystemExit("ground truth depends on the isomorphism key: stop and investigate")
    iso_class, positives = truths[kinds[0]]
    stars = np.array([is_star(r) for r in col.records])
    cls = [r.meta.get("class_id", r.kb_id) for r in col.records]
    partners: dict[int, set[int]] = defaultdict(set)
    pend_partner: dict[int, set[int]] = defaultdict(set)
    int_partner: dict[int, set[int]] = defaultdict(set)
    for (i, j), info in positives.items():
        partners[i].add(j)
        partners[j].add(i)
        side = pend_partner if info["pendant"] else int_partner
        side[i].add(j)
        side[j].add(i)
    queries = np.array(sorted(partners))
    # Stratified retrieval: a query's positives are its pendant (or interior)
    # partners; its partners of the other kind are removed from the candidate
    # list, being neither a miss nor a false hit.
    strata = {
        "all": (queries, partners, {}),
        "pendant": (np.array(sorted(pend_partner)), pend_partner, int_partner),
        "interior": (np.array(sorted(int_partner)), int_partner, pend_partner),
    }
    iu, ju = np.triu_indices(N, 1)
    noniso = iso_class[iu] != iso_class[ju]
    lab = np.zeros(len(iu), dtype=bool)
    pend = np.zeros(len(iu), dtype=bool)
    for (i, j), info in positives.items():
        t = i * N - i * (i + 1) // 2 + (j - i - 1)
        lab[t], pend[t] = True, info["pendant"]
    summary: dict[str, Any] = {
        "collection": args.collection,
        "N": N,
        "iso_classes": int(len(np.unique(iso_class))),
        "non_iso_pairs": int(noniso.sum()),
        "positives": int(lab[noniso].sum()),
        "positives_pendant": int((lab & pend & noniso).sum()),
        "positives_interior": int((lab & ~pend & noniso).sum()),
        "queries": int(len(queries)),
        "queries_star": int(stars[queries].sum()),
        "corpus_star_fraction": float(stars.mean()),
        "queries_star_fraction": float(stars[queries].mean()) if len(queries) else None,
        "queries_pendant": int(len(strata["pendant"][0])),
        "queries_interior": int(len(strata["interior"][0])),
        "key": args.key,
        "arms": {},
    }
    print(json.dumps({k: v for k, v in summary.items() if k != "arms"}))
    per_query: dict[str, np.ndarray] = {}
    per_query_strata: dict[tuple[str, str], np.ndarray] = {}
    for arm in ARMS:
        path = D_ROOT / "matrices" / args.collection / f"{arm}.npy"
        if not path.exists() and args.extra_matrix_dir is not None:
            path = args.extra_matrix_dir / args.collection / f"{arm}.npy"
        if not path.exists():
            continue
        M = np.load(path)
        if M.shape[0] == N_full and N_full != N:
            M = M[np.ix_(sel, sel)]
        if M.shape[0] != N:
            summary["arms"][arm] = {"skipped": f"matrix covers {M.shape[0]} of {N} members"}
            continue
        M = M.astype(np.float64)
        n_nonfinite = int((~np.isfinite(M)).sum())
        M[~np.isfinite(M)] = np.inf  # a censored distance ranks last, never first
        d = M[iu, ju]
        res: dict[str, Any] = {
            "nonfinite_cells": n_nonfinite,
            "AP": block_ap(d[noniso], lab[noniso]),
            "AP_pendant": block_ap(d[noniso & (~lab | pend)], lab[noniso & (~lab | pend)]),
            "AP_interior": block_ap(d[noniso & (~lab | ~pend)], lab[noniso & (~lab | ~pend)]),
        }
        for sname, (qs, pos_map, excl_map) in strata.items():
            rows = []
            for q in qs:
                others = np.where(iso_class != iso_class[q])[0]
                drop = excl_map.get(q)
                if drop:
                    others = others[~np.isin(others, list(drop))]
                rows.append(query_scores(M[q, others], np.isin(others, list(pos_map[q]))))
            arr = np.array(rows) if rows else np.zeros((0, 4))
            per_query_strata[(sname, arm)] = arr
            if sname != "all" and len(arr):
                res[f"MRR_{sname}"] = float(arr[:, 0].mean())
                res[f"hit1_{sname}"] = float(arr[:, 1].mean())
        pq = per_query_strata[("all", arm)]  # RR, hit1, hit10, AP
        per_query[arm] = pq
        res.update(
            {
                "MRR": float(pq[:, 0].mean()),
                "hit1": float(pq[:, 1].mean()),
                "hit10": float(pq[:, 2].mean()),
                "MAP": float(pq[:, 3].mean()),
                "MRR_star_q": float(pq[stars[queries], 0].mean()) if stars[queries].any() else None,
                "MRR_rel_q": float(pq[~stars[queries], 0].mean())
                if (~stars[queries]).any()
                else None,
            }
        )
        summary["arms"][arm] = res
    # bootstrap over queries, clustered by class
    rng = np.random.default_rng(args.seed)
    qcls = np.array([cls[q] for q in queries], dtype=object)
    uniq = list(dict.fromkeys(qcls.tolist()))
    groups = {c: np.where(qcls == c)[0] for c in uniq}
    boots = [
        np.concatenate([groups[uniq[g]] for g in rng.integers(len(uniq), size=len(uniq))])
        for _ in range(args.boot)
    ]
    for arm, pq in per_query.items():
        for col_i, name in enumerate(("MRR", "hit1", "hit10", "MAP")):
            vals = np.array([pq[b, col_i].mean() for b in boots])
            summary["arms"][arm][f"{name}_ci"] = [
                float(np.percentile(vals, 2.5)),
                float(np.percentile(vals, 97.5)),
            ]
    tests: dict[str, Any] = {}
    if OURS in per_query:
        for col_i, name in enumerate(("MRR", "MAP")):
            pv, eff, diffs = {}, {}, {}
            for arm, pq in per_query.items():
                if arm == OURS:
                    continue
                x, y = per_query[OURS][:, col_i], pq[:, col_i]
                pv[arm] = float(wilcoxon(x, y, alternative="greater", zero_method="zsplit").pvalue)
                eff[arm] = rank_biserial(x, y)
                dv = np.array([x[b].mean() - y[b].mean() for b in boots])
                diffs[arm] = [
                    float(x.mean() - y.mean()),
                    float(np.percentile(dv, 2.5)),
                    float(np.percentile(dv, 97.5)),
                ]
            tests[name] = {
                "p_holm": holm(pv),
                "p_raw": pv,
                "rank_biserial": eff,
                "diff_ci": diffs,
            }
        for sname in ("pendant", "interior"):
            qs = strata[sname][0]
            if not len(qs):
                continue
            scl = np.array([cls[q] for q in qs], dtype=object)
            su = list(dict.fromkeys(scl.tolist()))
            sg = {c: np.where(scl == c)[0] for c in su}
            sboots = [
                np.concatenate([sg[su[g]] for g in rng.integers(len(su), size=len(su))])
                for _ in range(args.boot)
            ]
            pv, eff, cis = {}, {}, {}
            x = per_query_strata[(sname, OURS)][:, 0]
            for (s2, arm), arr in per_query_strata.items():
                if s2 != sname:
                    continue
                vals = np.array([arr[b, 0].mean() for b in sboots])
                cis[arm] = [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))]
                if arm == OURS:
                    continue
                pv[arm] = float(
                    wilcoxon(x, arr[:, 0], alternative="greater", zero_method="zsplit").pvalue
                )
                eff[arm] = rank_biserial(x, arr[:, 0])
            tests[f"MRR_{sname}"] = {
                "n_queries": int(len(qs)),
                "p_holm": holm(pv),
                "rank_biserial": eff,
                "ci": cis,
            }
    summary["tests"] = tests
    summary["secs"] = time.perf_counter() - t0
    args.out.mkdir(parents=True, exist_ok=True)
    tag = args.collection + (f"__on_{args.restrict_to_arm}" if args.restrict_to_arm else "")
    summary["restrict_to_arm"] = args.restrict_to_arm
    (args.out / f"neardup_{tag}.json").write_text(json.dumps(summary, indent=1))
    (args.out / f"neardup_{tag}_truth.json").write_text(
        json.dumps(
            {
                f"{i},{j}": {"kinds": sorted(v["kinds"]), "pendant": v["pendant"]}
                for (i, j), v in positives.items()
            }
        )
    )
    hdr = f"{'arm':22s}{'AP':>7s}{'APpend':>8s}{'APint':>7s}{'MRR':>7s}  {'95% CI':14s}{'hit@1':>7s}{'hit@10':>7s}{'MAP':>7s}{'MRRrel':>8s}  p_Holm(MRR)  r_rb"
    print(hdr)
    for arm, r in summary["arms"].items():
        if "skipped" in r:
            print(f"{arm:22s}  {r['skipped']}")
            continue
        ci = r["MRR_ci"]
        p = tests.get("MRR", {}).get("p_holm", {}).get(arm)
        e = tests.get("MRR", {}).get("rank_biserial", {}).get(arm)
        rel = r["MRR_rel_q"] if r["MRR_rel_q"] is not None else float("nan")
        print(
            f"{arm:22s}{r['AP']:7.3f}{r['AP_pendant']:8.3f}{r['AP_interior']:7.3f}{r['MRR']:7.3f}  [{ci[0]:.3f},{ci[1]:.3f}]"
            f"{r['hit1']:7.3f}{r['hit10']:7.3f}{r['MAP']:7.3f}{rel:8.3f}  "
            + (f"{p:.2e}  {e:+.3f}" if p is not None else "   (ours)")
        )
    for sname in ("pendant", "interior"):
        t = tests.get(f"MRR_{sname}")
        if not t:
            continue
        print(f"-- stratum {sname}: {t['n_queries']} queries; MRR [95% CI], p_Holm, r_rb vs ours")
        for arm, r in summary["arms"].items():
            if "skipped" in r or f"MRR_{sname}" not in r:
                continue
            ci = t["ci"][arm]
            p = t["p_holm"].get(arm)
            e = t["rank_biserial"].get(arm)
            print(
                f"   {arm:22s}{r[f'MRR_{sname}']:7.3f} [{ci[0]:.3f},{ci[1]:.3f}]  hit@1 {r[f'hit1_{sname}']:.3f}  "
                + (f"{p:.2e}  {e:+.3f}" if p is not None else "(ours)")
            )
    print(
        f"star fraction: corpus {summary['corpus_star_fraction']:.3f}, queries {summary['queries_star_fraction']:.3f}; "
        f"non-finite cells: { {a: r.get('nonfinite_cells') for a, r in summary['arms'].items() if 'skipped' not in r} }"
    )
    print(f"elapsed {summary['secs']:.1f} s")


if __name__ == "__main__":
    main()
