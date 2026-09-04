"""Follow-up: split the NDC natural series by whether the constant set survives.

E-B's single-edit advantage is measured on edits that leave the constant set alone
(`probe_f4_topology.md` §9). The NDC consecutive-quarter series mixes both regimes,
so this splits the 555 pairs on the ARB node-id sets of the two members and re-scores
each split. No new canonicalization: E-A distances are read from `m2_rows_ndc.json`,
which is row-aligned with `load_ndc()`'s pair list.
"""

from __future__ import annotations

import json
import statistics as st
from pathlib import Path

from f4_corpora import ENV_M_MAX, ENV_M_MIN, ENV_N, K_MAX, NDC_QUARTER_MS, load_ndc
from scipy.stats import pearsonr, spearmanr

HERE = Path(__file__).resolve().parent
STRATA = {"0": (0, 0), "1": (1, 1), "2": (2, 2), "3-5": (3, 5), ">5": (6, 10**9)}


def constant_sets() -> dict[tuple[int, int], frozenset[int]]:
    """ARB node-id set of every in-envelope quarterly star KB, keyed by (node, window)."""
    import arb_temporal_lib as atl

    corpus = atl.load("NDC-classes")
    groups = atl.build_groups(corpus, NDC_QUARTER_MS, with_full=True)
    out: dict[tuple[int, int], frozenset[int]] = {}
    for gi in range(len(groups.key)):
        if not (ENV_M_MIN <= groups.m[gi] <= ENV_M_MAX):
            continue
        if groups.n[gi] > ENV_N or groups.max_arity[gi] > K_MAX:
            continue
        members = {v for s in atl.kb_edges(corpus, groups, gi) for v in s}
        out[(int(groups.node[gi]), int(groups.window[gi]))] = frozenset(members)
    return out


def score(rows: list[dict], enc: str) -> dict:
    dk, lk = f"d_{enc}", f"len_{enc}"
    sub = [r for r in rows if dk in r]
    if len(sub) < 3:
        return {"n": len(sub)}
    d = [r[dk] for r in sub]
    delta = [r["delta"] for r in sub]
    one = [r for r in sub if r["delta"] == 1]
    return {
        "n": len(sub),
        "spearman": round(float(spearmanr(delta, d).statistic), 3),
        "pearson": round(float(pearsonr(delta, d).statistic), 3),
        "med": {
            s: (
                round(st.median([r[dk] for r in sub if lo <= r["delta"] <= hi]), 1)
                if any(lo <= r["delta"] <= hi for r in sub)
                else None
            )
            for s, (lo, hi) in STRATA.items()
        },
        "n_by": {
            s: sum(1 for r in sub if lo <= r["delta"] <= hi) for s, (lo, hi) in STRATA.items()
        },
        "delta1_n": len(one),
        "delta1_le2": round(sum(1 for r in one if r[dk] <= 2) / len(one), 3) if one else None,
        "delta1_le5": round(sum(1 for r in one if r[dk] <= 5) / len(one), 3) if one else None,
        "delta1_norm": (
            round(st.median([r[dk] / r[lk] for r in one if r[lk]]), 3) if one else None
        ),
    }


def main() -> None:
    _, pairs = load_ndc()
    rows = json.loads((HERE / "m2_rows_ndc.json").read_text())
    assert len(rows) == len(pairs), (len(rows), len(pairs))
    vs = constant_sets()

    keep: list[dict] = []
    change: list[dict] = []
    for p, r in zip(pairs, rows, strict=True):
        a = vs[(p["node"], p["window"])]
        b = vs[(p["node"], p["window"] + 1)]
        rec = dict(r)
        rec["n_const_moved"] = len(a ^ b)
        (keep if a == b else change).append(rec)

    # runs of consecutive encodable quarters with one constant set throughout
    by_node: dict[int, list[int]] = {}
    for node, win in vs:
        by_node.setdefault(node, []).append(win)
    runs: list[int] = []
    nodes_ge3: set[int] = set()
    nodes_ge5: set[int] = set()
    for node, wins in by_node.items():
        wins.sort()
        local: list[int] = []
        run = 1
        for i in range(1, len(wins)):
            same_win = wins[i] == wins[i - 1] + 1
            same_set = vs[(node, wins[i])] == vs[(node, wins[i - 1])]
            if same_win and same_set:
                run += 1
            else:
                local.append(run)
                run = 1
        local.append(run)
        runs.extend(local)
        best = max(local)
        if best >= 3:
            nodes_ge3.add(node)
        if best >= 5:
            nodes_ge5.add(node)

    moved = [r["n_const_moved"] for r in change]
    db = [r["d_B"] for r in change]
    da_rows = [r for r in change if "d_A" in r]
    out = {
        "counts": {"preserving": len(keep), "changing": len(change), "total": len(rows)},
        "preserving": {e: score(keep, e) for e in ("A", "B", "C")},
        "changing": {e: score(change, e) for e in ("A", "B", "C")},
        "runs": {
            "classes_with_any_encodable_quarter": len(by_node),
            "classes_run_ge3": len(nodes_ge3),
            "classes_run_ge5": len(nodes_ge5),
            "max_run": max(runs) if runs else 0,
            "runs_ge3": sum(1 for x in runs if x >= 3),
            "runs_ge5": sum(1 for x in runs if x >= 5),
        },
        "constants_moved_on_changing_pairs": {
            "median": st.median(moved) if moved else None,
            "mean": round(st.fmean(moved), 2) if moved else None,
            "max": max(moved) if moved else None,
            "spearman_moved_vs_dB": round(float(spearmanr(moved, db).statistic), 3),
            "spearman_moved_vs_dC": round(
                float(spearmanr(moved, [r["d_C"] for r in change]).statistic), 3
            ),
            "spearman_moved_vs_dA": (
                round(
                    float(
                        spearmanr(
                            [r["n_const_moved"] for r in da_rows], [r["d_A"] for r in da_rows]
                        ).statistic
                    ),
                    3,
                )
                if len(da_rows) > 2
                else None
            ),
            "n_A": len(da_rows),
        },
    }
    (HERE / "followup_ndc_regime.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
