"""Probe C8: detecting one-edit near-duplicates in a KB collection.

Ground truth: a non-isomorphic pair (i, j) is positive iff one single-fact edit
(delete a fact, insert a fact, remove a constant from a fact, add a constant to
a fact) turns one member into the other. It is computed exactly from the
down-neighbours of every member (delete a fact; remove one constant from a fact
of arity >= 2; compact; keep connected results without duplicate facts), keyed
by the ordered-walk fingerprint, which only decides isomorphism.

Every cached distance matrix is then scored as a detector: pairwise average
precision over all non-isomorphic pairs, and per-query expected rank of the
nearest positive partner (MRR, hit@1).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from experiments.tkde import corpora as C  # noqa: E402
from isalhg.datasets.kb.base import compact  # noqa: E402
from isalhg.iso_backends.isal_ordered import ordered_fingerprint  # noqa: E402

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


def key_of(record, n_types: int, n_preds: int) -> tuple[int, str]:
    H = record.to_hypergraph(n_types=n_types, n_preds=n_preds)
    root, word = ordered_fingerprint(H)
    return int(root), word


def down_neighbours(record) -> list[tuple[str, tuple]]:
    """(edit kind, facts) of every single down-edit, before compaction."""
    facts = [(int(p), tuple(sorted(int(a) for a in args))) for p, args in record.facts]
    out: list[tuple[str, tuple]] = []
    for i in range(len(facts)):
        rest = facts[:i] + facts[i + 1 :]
        if rest:
            out.append(("delete_fact", tuple(rest)))
    for i, (p, args) in enumerate(facts):
        if len(args) < 2:
            continue
        for a in args:
            new = (p, tuple(x for x in args if x != a))
            rest = facts[:i] + [new] + facts[i + 1 :]
            if len(set(rest)) < len(rest):
                continue  # duplicate fact: not a KB under Definition 1
            out.append(("remove_constant", tuple(rest)))
    return out


def is_pendant(record, kind: str, facts: tuple) -> bool:
    before = {a for _, args in record.facts for a in args}
    after = {a for _, args in facts for a in args}
    return before != after


def is_star(record) -> bool:
    facts = [set(args) for _, args in record.facts]
    common = set.intersection(*facts) if facts else set()
    if not common:
        return False
    counts: dict[int, int] = defaultdict(int)
    for args in facts:
        for a in args:
            counts[a] += 1
    for root in common:
        if all(c == 1 for a, c in counts.items() if a != root):
            return True
    return False


def ground_truth(col) -> tuple[np.ndarray, dict[tuple[int, int], dict]]:
    recs = col.records
    nt, npred = col.n_types, col.n_preds
    keys = [key_of(r, nt, npred) for r in recs]
    by_key: dict[tuple[int, str], list[int]] = defaultdict(list)
    for i, k in enumerate(keys):
        by_key[k].append(i)
    iso_class = np.empty(len(recs), dtype=np.int64)
    for c, members in enumerate(by_key.values()):
        iso_class[members] = c
    positives: dict[tuple[int, int], dict] = {}
    for i, r in enumerate(recs):
        for kind, facts in down_neighbours(r):
            sub = compact(
                f"{r.kb_id}~",
                list(r.types),
                [(p, tuple(a)) for p, a in facts],
                require_connected=True,
            )
            if sub is None:
                continue
            k = key_of(sub, nt, npred)
            for j in by_key.get(k, ()):
                pair = (min(i, j), max(i, j))
                info = positives.setdefault(pair, {"kinds": set(), "pendant": False})
                info["kinds"].add(kind)
                info["pendant"] |= is_pendant(r, kind, facts)
    return iso_class, positives


def average_precision(scores: np.ndarray, labels: np.ndarray) -> float:
    """AP with tied scores grouped (a tie block is entered as a whole)."""
    order = np.argsort(scores, kind="stable")
    s, y = scores[order], labels[order]
    uniq, start = np.unique(s, return_index=True)
    ends = np.append(start[1:], len(s))
    tp_cum, total_pos, ap, seen = 0, y.sum(), 0.0, 0
    for a, b in zip(start, ends):
        block_pos = int(y[a:b].sum())
        tp_cum += block_pos
        seen = b
        if block_pos:
            ap += block_pos * (tp_cum / seen)
    return ap / total_pos if total_pos else float("nan")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--collection", default="wd50k66")
    ap.add_argument("--extra-matrix-dir", type=Path, default=None)
    ap.add_argument("--save-truth", type=Path, default=None)
    args = ap.parse_args()
    col = C.load_collection(args.collection, root=D_ROOT)
    N = len(col)
    iso_class, positives = ground_truth(col)
    stars = np.array([is_star(r) for r in col.records])
    iu, ju = np.triu_indices(N, 1)
    noniso = iso_class[iu] != iso_class[ju]
    label = np.zeros(len(iu), dtype=bool)
    pend = np.zeros(len(iu), dtype=bool)
    for (i, j), info in positives.items():
        t = i * N - i * (i + 1) // 2 + (j - i - 1)  # row-major index into triu_indices(N, 1)
        label[t] = True
        pend[t] = info["pendant"]
    n_pos = int(label[noniso].sum())
    print(
        f"{args.collection}: N={N}, iso classes={len(np.unique(iso_class))}, non-iso pairs={int(noniso.sum())}, "
        f"positives={n_pos} (pendant {int((label & pend & noniso).sum())}, interior {int((label & ~pend & noniso).sum())}); "
        f"members with >=1 positive: {len({i for p in positives for i in p})}"
    )
    if args.save_truth:
        args.save_truth.parent.mkdir(parents=True, exist_ok=True)
        args.save_truth.write_text(
            json.dumps(
                {
                    f"{i},{j}": {"kinds": sorted(v["kinds"]), "pendant": v["pendant"]}
                    for (i, j), v in positives.items()
                }
            )
        )
    partners: dict[int, set[int]] = defaultdict(set)
    for i, j in positives:
        partners[i].add(j)
        partners[j].add(i)
    queries = sorted(partners)
    print(
        "arm".ljust(22)
        + "AP".rjust(8)
        + "AP pend".rjust(9)
        + "AP int".rjust(8)
        + "AP star-q".rjust(10)
        + "MRR".rjust(8)
        + "hit@1".rjust(8)
        + "MRR rel-q".rjust(10)
    )
    for arm in ARMS:
        path = D_ROOT / "matrices" / args.collection / f"{arm}.npy"
        if not path.exists() and args.extra_matrix_dir is not None:
            path = args.extra_matrix_dir / args.collection / f"{arm}.npy"
        if not path.exists():
            continue
        M = np.load(path)
        if M.shape[0] != N:
            print(arm.ljust(22) + "  skipped (matrix over a censored subset)")
            continue
        d = M[iu, ju].astype(np.float64)
        m = noniso
        ap_all = average_precision(d[m], label[m])
        mp = m & (~label | pend)
        mi = m & (~label | ~pend)
        ap_p = average_precision(d[mp], label[mp])
        ap_i = average_precision(d[mi], label[mi])
        qstar = stars[iu] & stars[ju]
        ms = m & qstar
        ap_s = average_precision(d[ms], label[ms])
        rr, h1, rr_rel = [], [], []
        for q in queries:
            others = np.where(iso_class != iso_class[q])[0]
            dq = M[q, others].astype(np.float64)
            pos = np.isin(others, list(partners[q]))
            best = dq[pos].min()
            better = int(np.sum(dq < best))
            ties = int(np.sum(dq == best)) - 1
            # expected rank of the first positive within the tie block
            n_pos_tied = int(np.sum(pos & (dq == best)))
            block = ties + 1
            exp_rank = 1 + better + (block - n_pos_tied) / (n_pos_tied + 1)
            rr.append(1.0 / exp_rank)
            h1.append(n_pos_tied / block if better == 0 else 0.0)
            if not stars[q]:
                rr_rel.append(1.0 / exp_rank)
        print(
            arm.ljust(22)
            + f"{ap_all:8.3f}{ap_p:9.3f}{ap_i:8.3f}{ap_s:10.3f}"
            + f"{np.mean(rr):8.3f}{np.mean(h1):8.3f}{np.mean(rr_rel) if rr_rel else float('nan'):10.3f}",
            flush=True,
        )


if __name__ == "__main__":
    main()
