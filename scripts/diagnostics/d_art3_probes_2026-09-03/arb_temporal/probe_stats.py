"""Tasks 1-4 of the ARB temporal star-KB probe: granularity, sizes, variants, census.

Usage:  python probe_stats.py <dataset> [--census-cap 1500]
Writes stats_<dataset>.json and spec_<dataset>.json next to this file.
"""

from __future__ import annotations

import json
import os
import random
import sys
import time

import arb_temporal_lib as L
import numpy as np

CENSUS_CAP = 1500
CENSUS_TIME_CAP = 55.0  # task 4 runs only where it fits inside a minute per dataset
BUCKETS = [(1, 10), (11, 30), (31, 60), (61, 110)]
PER_BUCKET = 4  # <= 16 timing instances per dataset


def granularity_scan(c: L.Corpus, cands: list[tuple[str, int]]) -> list[dict]:
    out = []
    for gname, step in cands:
        t0 = time.time()
        g = L.build_groups(c, step, with_full=False)
        out.append(
            dict(
                granularity=gname,
                step=step,
                n_windows=int(g.n_windows),
                n_kbs=int(len(g.m)),
                med_m=float(np.median(g.m)),
                p90_m=float(np.percentile(g.m, 90)),
                secs=round(time.time() - t0, 1),
            )
        )
        del g
    return out


def pick_two(scan: list[dict]) -> list[str]:
    """Two granularities whose median m is closest to the middle of the 3-30 band.

    Corpora where no candidate reaches median m = 3 (resp. none stays under 30)
    fall back to the two coarsest (resp. finest) candidates, so the reported pair
    is the most favourable available rather than an arbitrary tie-break.
    """
    if all(r["med_m"] < 3 for r in scan):
        return [scan[-1]["granularity"], scan[-2]["granularity"]]
    if all(r["med_m"] > 30 for r in scan):
        return [scan[0]["granularity"], scan[1]["granularity"]]

    def score(r):
        return abs(np.log(max(r["med_m"], 1e-9) / 10.0))

    ranked = sorted(scan, key=score)
    return [ranked[0]["granularity"], ranked[1]["granularity"]]


def full_stats(c: L.Corpus, gname: str, step: int) -> tuple[dict, L.Groups, np.ndarray]:
    g = L.build_groups(c, step, with_full=True)
    env = (g.n <= L.ENV_N) & (g.m <= L.ENV_M)

    ar = c.c_arity[g.usid]
    hist = np.bincount(ar)
    gid_pair = np.repeat(np.arange(len(g.gstart)), g.m)
    ar_env = ar[env[gid_pair]]
    hist_env = np.bincount(ar_env) if len(ar_env) else np.zeros(1, dtype=int)

    # consecutive-window pairs (strict window indices t, t+1), both non-empty
    nxt = np.searchsorted(g.key, g.key + 1)
    ok = (nxt < len(g.key)) & (g.window + 1 < g.n_windows)
    ok[ok] &= g.key[nxt[ok]] == g.key[ok] + 1
    li = np.flatnonzero(ok)
    ri = nxt[li]

    def delta_block(mask: np.ndarray) -> dict:
        both = mask[li] & mask[ri]
        le, re = li[both], ri[both]
        dl = g.m[le] + g.m[re] - 2 * g.inter[le]

        def frac(sel):
            return dict(count=int(sel.sum()), frac=float(sel.mean()) if len(dl) else 0.0)

        one: dict[int, int] = {}
        for nd in g.node[le[dl == 1]]:
            one[int(nd)] = one.get(int(nd), 0) + 1
        return dict(
            n_pairs_both_nonempty=int(len(li)),
            n_pairs_both_in_env=int(len(le)),
            d0=frac(dl == 0),
            d1=frac(dl == 1),
            d2=frac(dl == 2),
            d3_5=frac((dl >= 3) & (dl <= 5)),
            d_gt5=frac(dl > 5),
            med_delta=float(np.median(dl)) if len(dl) else None,
            n_nodes_ge3_one_edit_pairs=int(sum(1 for v in one.values() if v >= 3)),
        )

    def runs(mask: np.ndarray) -> tuple[int, int]:
        ei = np.flatnonzero(mask)
        order = np.lexsort((g.window[ei], g.node[ei]))
        ns_, ws_ = g.node[ei][order], g.window[ei][order]
        run, best = 1, {}
        for i in range(1, len(ns_) + 1):
            if i < len(ns_) and ns_[i] == ns_[i - 1] and ws_[i] == ws_[i - 1] + 1:
                run += 1
            else:
                nd = int(ns_[i - 1])
                best[nd] = max(best.get(nd, 0), run)
                run = 1
        return (
            sum(1 for v in best.values() if v >= 3),
            sum(1 for v in best.values() if v >= 5),
        )

    dd = delta_block(env)
    n_run3, n_run5 = runs(env)

    sub = env & (g.m >= 3)  # "substantive": at least 3 facts
    dd_sub = delta_block(sub)
    sub_run3, sub_run5 = runs(sub)

    enc = sub & (g.max_arity <= L.K_MAX)  # the compiled encoder refuses arity > K_MAX
    dd_enc = delta_block(enc)
    enc_run3, enc_run5 = runs(enc)

    st = dict(
        granularity=gname,
        step=step,
        n_windows=int(g.n_windows),
        n_kbs=int(len(g.m)),
        n_dist=L.pct(g.n),
        m_dist=L.pct(g.m),
        maxarity_dist=L.pct(g.max_arity),
        arity_hist={int(a): int(hist[a]) for a in range(len(hist)) if hist[a]},
        arity_hist_env={int(a): int(hist_env[a]) for a in range(len(hist_env)) if hist_env[a]},
        frac_kb_with_arity_ge3=float((g.max_arity >= 3).mean()),
        envelope_count=int(env.sum()),
        envelope_frac=float(env.mean()),
        frac_env_kb_with_arity_ge3=float((g.max_arity[env] >= 3).mean()) if env.any() else 0.0,
        frac_env_maxarity_le10=float((g.max_arity[env] <= L.K_MAX).mean()) if env.any() else 0.0,
        delta=dd,
        n_nodes_run3_in_env=int(n_run3),
        n_nodes_run5_in_env=int(n_run5),
        n_nodes_ge3_one_edit_pairs=dd["n_nodes_ge3_one_edit_pairs"],
        n_distinct_nodes_in_env=int(len(np.unique(g.node[env]))),
        sub_m3_count=int(sub.sum()),
        sub_m3_delta=dd_sub,
        sub_m3_run3=int(sub_run3),
        sub_m3_run5=int(sub_run5),
        enc_count=int(enc.sum()),
        enc_delta=dd_enc,
        enc_run3=int(enc_run3),
        enc_run5=int(enc_run5),
    )
    return st, g, env


def census(c: L.Corpus, g: L.Groups, env: np.ndarray, cap: int, rng: random.Random) -> dict:
    from isalhg.core.sparse_hypergraph import SparseHypergraph
    from isalhg.iso_backends.pynauty_levi import PynautyLeviBackend

    idx = np.flatnonzero(env).tolist()
    sampled = len(idx) > cap
    if sampled:
        idx = rng.sample(idx, cap)
    be = PynautyLeviBackend()
    unl, lab, factsets = set(), set(), set()
    allnodes = sorted({v for gi in idx for e in L.kb_edges(c, g, gi) for v in e})
    lut = {v: i for i, v in enumerate(allnodes)}
    fails = 0
    t0 = time.time()
    done = 0
    for gi in idx:
        if time.time() - t0 > CENSUS_TIME_CAP:
            break
        edges = L.kb_edges(c, g, gi)
        loc = {v: i for i, v in enumerate(sorted({v for e in edges for v in e}))}
        hes = [frozenset(loc[v] for v in e) for e in edges]
        try:
            unl.add(be.fingerprint(SparseHypergraph(len(loc), hes)))
            vl = [0] * len(loc)
            for v, i in loc.items():
                vl[i] = lut[v]
            unlab = SparseHypergraph(len(loc), hes, n_vertex_labels=len(lut), vertex_labels=vl)
            lab.add(be.fingerprint(unlab))
        except Exception:  # noqa: BLE001
            fails += 1
        factsets.add(frozenset(frozenset(e) for e in edges))
        done += 1
    return dict(
        sampled=sampled or done < len(idx),
        n_census=done,
        n_in_envelope=int(env.sum()),
        distinct_unlabelled=len(unl),
        distinct_identity_labelled=len(lab),
        distinct_fact_sets=len(factsets),
        errors=fails,
        secs=round(time.time() - t0, 1),
        truncated_by_time=done < len(idx),
    )


def timing_spec(c: L.Corpus, g: L.Groups, env: np.ndarray, rng: random.Random) -> list[dict]:
    out = []
    for lo, hi in BUCKETS:
        base = env & (g.max_arity <= L.K_MAX) & (g.m <= hi)
        pref = np.flatnonzero(base & (g.m >= max(lo, 3))).tolist()
        sel = pref if len(pref) >= PER_BUCKET else np.flatnonzero(base & (g.m >= lo)).tolist()
        if not sel:
            continue
        pick = sel if len(sel) <= PER_BUCKET else rng.sample(sel, PER_BUCKET)
        for gi in pick:
            out.append(
                dict(
                    bucket=f"{lo}-{hi}",
                    node=int(g.node[gi]),
                    window=int(g.window[gi]),
                    n=int(g.n[gi]),
                    m=int(g.m[gi]),
                    max_arity=int(g.max_arity[gi]),
                    edges=L.kb_edges(c, g, gi),
                )
            )
    return out


def main() -> None:
    name = sys.argv[1]
    cap = CENSUS_CAP
    if "--census-cap" in sys.argv:
        cap = int(sys.argv[sys.argv.index("--census-cap") + 1])
    cfg = L.DATASETS[name]
    t0 = time.time()
    c = L.load(name)
    load_s = time.time() - t0
    base = dict(
        dataset=name,
        unit=cfg["unit"],
        load_secs=round(load_s, 1),
        n_simplices=c.n_simplices,
        n_distinct_simplices=c.n_canon,
        n_nodes_max_id=c.n_nodes - 1,
        n_nodes_used=int(len(np.unique(c.c_members))),
        arity_range=[int(c.c_arity.min()), int(c.c_arity.max())],
        has_node_labels=bool(c.node_names),
        n_node_labels=len(c.node_names),
        t_min=int(c.times.min()),
        t_max=int(c.times.max()),
    )
    print(f"[{name}] loaded in {load_s:.1f}s N={c.n_simplices} distinct={c.n_canon}", flush=True)

    scan = granularity_scan(c, cfg["cands"])
    chosen = pick_two(scan)
    print(
        f"[{name}] scan={[(r['granularity'], round(r['med_m'])) for r in scan]} -> {chosen}",
        flush=True,
    )

    per_gran, specs = {}, {}
    for gname in chosen:
        step = dict(cfg["cands"])[gname]
        st, g, env = full_stats(c, gname, step)
        st["census"] = census(c, g, env, cap, random.Random(L.SEED))
        specs[gname] = timing_spec(c, g, env, random.Random(L.SEED + 1))
        per_gran[gname] = st
        print(
            f"[{name}/{gname}] KB={st['n_kbs']} med n/m={st['n_dist']['med']}/{st['m_dist']['med']} "
            f"env={st['envelope_count']} enc={st['enc_count']} "
            f"d1(enc)={st['enc_delta']['d1']['count']} census={st['census']['secs']}s",
            flush=True,
        )
        del g, env

    base["granularity_scan"] = scan
    base["chosen"] = chosen
    base["per_granularity"] = per_gran
    base["total_secs"] = round(time.time() - t0, 1)
    best = max(chosen, key=lambda gn: per_gran[gn]["enc_delta"]["n_pairs_both_in_env"])
    base["timing_granularity"] = best
    L.dump(base, os.path.join(L.OUT, f"stats_{name}.json"))
    with open(os.path.join(L.OUT, f"spec_{name}.json"), "w") as fh:
        json.dump(dict(dataset=name, granularity=best, items=specs.get(best, [])), fh)
    print(f"[{name}] DONE in {base['total_secs']}s", flush=True)


if __name__ == "__main__":
    main()
