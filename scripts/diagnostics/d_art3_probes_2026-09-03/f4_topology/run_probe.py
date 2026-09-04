"""Driver for the F4 topology probe (M0-M4).

Stages are independent and each writes its JSON as soon as it finishes, so an
interruption loses at most the running stage.

    python run_probe.py --stage m0
    python run_probe.py --stage m1
    python run_probe.py --stage m2
    python run_probe.py --stage m34
"""

from __future__ import annotations

import argparse
import json
import random
import statistics as st
import sys
import time
from pathlib import Path
from typing import Any

from f4_corpora import (
    EDIT_KINDS,
    gen_synthetic,
    load_ndc,
    load_wd50k66,
    random_walk,
    sample_edits,
)
from f4_encodings import (
    KB,
    byte_levenshtein,
    canonical_ranks,
    nauty_fingerprint,
    token_levenshtein,
    word_B,
    word_C,
)
from f4_exec import map_word_A

from isalhg.core.canonical import required_k
from isalhg.core.instructions import parse
from isalhg.core.sparse_hypergraph import permute

HERE = Path(__file__).resolve().parent
SEED_CORPUS = 20260904
SEED_EDITS = 20260905
SEED_PERM = 20260906
BUDGET_S = 60.0
WORKERS = 16

N_SYNTH_M0 = 2000
N_SYNTH_M1 = 300
N_REAL_M1 = 200
N_REAL_M0 = 500
EDITS_PER_KIND = 10


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def dump(obj: Any, name: str) -> None:
    path = HERE / name
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, indent=1, default=float))
    tmp.rename(path)
    log(f"wrote {path.name}")


def kb_key(kb: KB) -> tuple:
    return (kb.n, kb.types, kb.facts)


def quant(xs: list[float]) -> dict[str, float | None]:
    if not xs:
        return dict.fromkeys(("min", "p25", "med", "p75", "p90", "max", "mean"))
    s = sorted(xs)

    def q(p: float) -> float:
        return float(s[min(len(s) - 1, max(0, int(round(p * (len(s) - 1)))))])

    return {
        "min": float(s[0]),
        "p25": q(0.25),
        "med": q(0.50),
        "p75": q(0.75),
        "p90": q(0.90),
        "max": float(s[-1]),
        "mean": round(st.fmean(s), 3),
    }


# ---------------------------------------------------------------------------
# The A-arm cache: (kb_key, k) -> word or censoring record
# ---------------------------------------------------------------------------


class ArmA:
    def __init__(self, budget: float = BUDGET_S, workers: int = WORKERS) -> None:
        self.cache: dict[tuple, dict] = {}
        self.budget = budget
        self.workers = workers

    def request(self, items: list[tuple[KB, int]]) -> None:
        todo: list[tuple[KB, int]] = []
        keys: list[tuple] = []
        seen: set[tuple] = set()
        for kb, k in items:
            key = (kb_key(kb), k)
            if key in self.cache or key in seen:
                continue
            seen.add(key)
            todo.append((kb, k))
            keys.append(key)
        if not todo:
            return
        log(f"E-A: {len(todo)} canonicalizations (budget {self.budget:.0f} s, {self.workers} proc)")
        res = map_word_A(
            todo,
            budget=self.budget,
            workers=self.workers,
            progress=lambda d, n: log(f"  E-A {d}/{n}"),
        )
        for key, r in zip(keys, res, strict=True):
            if r.get("ok"):
                toks = tuple(parse(r["w"]))
                self.cache[key] = {
                    "ok": True,
                    "tokens": toks,
                    "seed": r["seed"],
                    "secs": r["secs"],
                }
            else:
                self.cache[key] = {"ok": False, "dnf": bool(r.get("dnf")), "secs": r.get("secs")}

    def word(self, kb: KB, k: int) -> tuple | None:
        rec = self.cache.get((kb_key(kb), k))
        if rec is None or not rec["ok"]:
            return None
        if kb.n_types > 1:
            return (("seed", rec["seed"]), *rec["tokens"])
        return rec["tokens"]

    def secs(self, kb: KB, k: int) -> float | None:
        rec = self.cache.get((kb_key(kb), k))
        return None if rec is None else rec.get("secs")

    def stats(self) -> dict:
        n = len(self.cache)
        ok = sum(1 for r in self.cache.values() if r["ok"])
        dnf = sum(1 for r in self.cache.values() if not r["ok"] and r.get("dnf"))
        secs = [r["secs"] for r in self.cache.values() if r["ok"]]
        return {
            "n": n,
            "ok": ok,
            "dnf": dnf,
            "err": n - ok - dnf,
            "dnf_frac": round(dnf / n, 4) if n else None,
            "secs": quant(secs),
        }


def pair_distance(
    arm: ArmA, kb1: KB, kb2: KB, wb1: tuple, wb2: tuple, wc1: tuple, wc2: tuple
) -> dict:
    k = max(required_k(kb1.to_hypergraph()), required_k(kb2.to_hypergraph()))
    wa1, wa2 = arm.word(kb1, k), arm.word(kb2, k)
    out = {
        "d_B": token_levenshtein(wb1, wb2),
        "d_C": token_levenshtein(wc1, wc2),
        "len_B": len(wb1),
        "len_C": len(wc1),
    }
    if wa1 is not None and wa2 is not None:
        out["d_A"] = token_levenshtein(wa1, wa2)
        out["len_A"] = len(wa1)
    return out


# ---------------------------------------------------------------------------
# M0 -- correctness
# ---------------------------------------------------------------------------


def stage_m0() -> None:
    rng = random.Random(SEED_PERM)
    synth = gen_synthetic(N_SYNTH_M0, SEED_CORPUS)
    ndc, _ = load_ndc()
    wd = load_wd50k66()
    r = random.Random(SEED_CORPUS)
    corpora = {
        "synthetic": synth,
        "ndc_classes_quarter": r.sample(ndc, min(N_REAL_M0, len(ndc))),
        "wd50k66": r.sample(wd, min(N_REAL_M0, len(wd))),
    }
    arm = ArmA()
    out: dict[str, Any] = {"seeds": {"corpus": SEED_CORPUS, "perm": SEED_PERM}, "corpora": {}}

    for name, kbs in corpora.items():
        log(f"M0 {name}: {len(kbs)} instances")
        perms: list[KB] = []
        for kb in kbs:
            H = kb.to_hypergraph()
            sig = list(range(H.n_nodes))
            rng.shuffle(sig)
            perms.append(
                KB(
                    n=H.n_nodes,
                    types=tuple(permute(H, sig).vertex_label(v) for v in range(H.n_nodes)),
                    facts=tuple((lab, mem) for _, mem, lab in permute(H, sig).iter_edges()),
                    n_types=kb.n_types,
                    n_preds=kb.n_preds,
                )
            )
        arm.request([(kb, required_k(kb.to_hypergraph())) for kb in kbs + perms])

        viol = {"A": 0, "B": 0, "C": 0}
        checked = {"A": 0, "B": 0, "C": 0}
        wordsB: list[tuple] = []
        wordsC: list[tuple] = []
        fps: list[bytes] = []
        fpA: list[Any] = []
        for kb, pkb in zip(kbs, perms, strict=True):
            H, P = kb.to_hypergraph(), pkb.to_hypergraph()
            b1, b2 = word_B(H), word_B(P)
            c1, c2 = word_C(H), word_C(P)
            viol["B"] += int(b1 != b2)
            viol["C"] += int(c1 != c2)
            checked["B"] += 1
            checked["C"] += 1
            k = required_k(H)
            a1, a2 = arm.word(kb, k), arm.word(pkb, required_k(P))
            if a1 is not None and a2 is not None:
                viol["A"] += int(a1 != a2)
                checked["A"] += 1
            wordsB.append(b1)
            wordsC.append(c1)
            fps.append(nauty_fingerprint(H))
            fpA.append(a1)

        def partition(xs: list) -> dict[Any, list[int]]:
            g: dict[Any, list[int]] = {}
            for i, x in enumerate(xs):
                g.setdefault(x, []).append(i)
            return g

        ref = partition(fps)
        comp: dict[str, Any] = {}
        for enc, words in (("A", fpA), ("B", wordsB), ("C", wordsC)):
            idx = [i for i, w in enumerate(words) if w is not None]
            sub_ref = partition([fps[i] for i in idx])
            sub_enc = partition([words[i] for i in idx])
            ref_lab = {
                i: j
                for j, (_, mem) in enumerate(sorted(sub_ref.items(), key=lambda kv: kv[1]))
                for i in mem
            }
            enc_lab = {
                i: j
                for j, (_, mem) in enumerate(sorted(sub_enc.items(), key=lambda kv: kv[1]))
                for i in mem
            }
            merges = 0
            splits = 0
            for i in range(len(idx)):
                for j in range(i + 1, len(idx)):
                    same_ref = ref_lab[i] == ref_lab[j]
                    same_enc = enc_lab[i] == enc_lab[j]
                    if same_enc and not same_ref:
                        merges += 1
                    if same_ref and not same_enc:
                        splits += 1
            comp[enc] = {
                "n_checked": len(idx),
                "iso_classes_nauty": len(sub_ref),
                "classes_enc": len(sub_enc),
                "false_merges": merges,
                "false_splits": splits,
            }
        out["corpora"][name] = {
            "n": len(kbs),
            "iso_invariance": {e: {"checked": checked[e], "violations": viol[e]} for e in "ABC"},
            "completeness": comp,
        }
        dump(out, "m0_results.json")
    out["arm_A"] = arm.stats()
    dump(out, "m0_results.json")


# ---------------------------------------------------------------------------
# M1 -- single-edit response
# ---------------------------------------------------------------------------


EA_CAP_M1 = {"synthetic": 300, "ndc_classes_quarter": 60, "wd50k66": 200}


def stage_m1(ea_kbs: int) -> None:
    rng = random.Random(SEED_EDITS)
    r = random.Random(SEED_CORPUS)
    ndc, _ = load_ndc()
    wd = load_wd50k66()
    corpora = {
        "synthetic": gen_synthetic(N_SYNTH_M0, SEED_CORPUS)[:N_SYNTH_M1],
        "ndc_classes_quarter": r.sample(ndc, min(N_REAL_M1, len(ndc))),
        "wd50k66": r.sample(wd, min(N_REAL_M1, len(wd))),
    }
    out: dict[str, Any] = {
        "config": {
            "edits_per_kind": EDITS_PER_KIND,
            "seed_edits": SEED_EDITS,
            "budget_s": BUDGET_S,
            "ea_kbs_per_corpus": {k: min(v, ea_kbs) for k, v in EA_CAP_M1.items()},
        },
        "corpora": {},
    }
    for name, kbs in corpora.items():
        log(f"M1 {name}: {len(kbs)} base KBs")
        arm = ArmA()
        ea_set = set(range(min(EA_CAP_M1[name], ea_kbs, len(kbs))))
        jobs: list[tuple[int, str, KB, KB]] = []
        for i, kb in enumerate(kbs):
            for kind in EDIT_KINDS:
                for ed in sample_edits(kb, kind, EDITS_PER_KIND, rng):
                    jobs.append((i, kind, kb, ed))
        log(f"  {len(jobs)} single-edit pairs")
        want = [
            (kb, max(required_k(kb.to_hypergraph()), required_k(ed.to_hypergraph())))
            for i, _, kb, ed in jobs
            if i in ea_set
        ] + [
            (ed, max(required_k(kb.to_hypergraph()), required_k(ed.to_hypergraph())))
            for i, _, kb, ed in jobs
            if i in ea_set
        ]
        arm.request(want)

        cacheB: dict[tuple, tuple] = {}
        cacheC: dict[tuple, tuple] = {}

        def wbc(kb: KB) -> tuple[tuple, tuple]:
            key = kb_key(kb)
            if key not in cacheB:
                H = kb.to_hypergraph()
                rk = canonical_ranks(H)
                cacheB[key] = word_B(H, rk)
                cacheC[key] = word_C(H, rk)
            return cacheB[key], cacheC[key]

        rows: list[dict] = []
        for i, kind, kb, ed in jobs:
            b1, c1 = wbc(kb)
            b2, c2 = wbc(ed)
            rec = pair_distance(arm, kb, ed, b1, b2, c1, c2)
            rec["kind"] = kind
            rec["base"] = i
            rows.append(rec)

        by_kind: dict[str, Any] = {}
        for kind in EDIT_KINDS:
            sub = [x for x in rows if x["kind"] == kind]
            entry: dict[str, Any] = {"n_pairs": len(sub)}
            for enc in "ABC":
                dk, lk = f"d_{enc}", f"len_{enc}"
                vals = [x[dk] for x in sub if dk in x]
                norm = [x[dk] / x[lk] for x in sub if dk in x and x[lk] > 0]
                entry[enc] = {"n": len(vals), "abs": quant(vals), "norm": quant(norm)}
            by_kind[kind] = entry
        pooled: dict[str, Any] = {}
        for enc in "ABC":
            dk, lk = f"d_{enc}", f"len_{enc}"
            vals = [x[dk] for x in rows if dk in x]
            norm = [x[dk] / x[lk] for x in rows if dk in x and x[lk] > 0]
            pooled[enc] = {"n": len(vals), "abs": quant(vals), "norm": quant(norm)}
        out["corpora"][name] = {
            "n_base": len(kbs),
            "n_pairs": len(rows),
            "by_kind": by_kind,
            "pooled": pooled,
            "arm_A": arm.stats(),
            "base_len": {
                enc: quant([len(wbc(kb)[j]) for kb in kbs]) for j, enc in ((0, "B"), (1, "C"))
            },
        }
        dump(out, "m1_results.json")
        (HERE / f"m1_rows_{name}.json").write_text(json.dumps(rows, default=float))
    dump(out, "m1_results.json")


# ---------------------------------------------------------------------------
# M2 -- variant series
# ---------------------------------------------------------------------------


def _series_report(rows: list[dict]) -> dict:
    from scipy.stats import pearsonr, spearmanr

    out: dict[str, Any] = {"n_pairs": len(rows)}
    strata = {"0": (0, 0), "1": (1, 1), "2": (2, 2), "3-5": (3, 5), ">5": (6, 10**9)}
    for enc in "ABC":
        dk, lk = f"d_{enc}", f"len_{enc}"
        sub = [x for x in rows if dk in x]
        if len(sub) < 3:
            out[enc] = {"n": len(sub)}
            continue
        d = [x[dk] for x in sub]
        delta = [x["delta"] for x in sub]
        one = [x for x in sub if x["delta"] == 1]
        out[enc] = {
            "n": len(sub),
            "spearman": round(float(spearmanr(delta, d).statistic), 4),
            "pearson": round(float(pearsonr(delta, d).statistic), 4),
            "median_by_stratum": {
                s: (
                    round(st.median([x[dk] for x in sub if lo <= x["delta"] <= hi]), 2)
                    if any(lo <= x["delta"] <= hi for x in sub)
                    else None
                )
                for s, (lo, hi) in strata.items()
            },
            "n_by_stratum": {
                s: sum(1 for x in sub if lo <= x["delta"] <= hi) for s, (lo, hi) in strata.items()
            },
            "delta1": {
                "n": len(one),
                "frac_le2": round(sum(1 for x in one if x[dk] <= 2) / len(one), 4) if one else None,
                "frac_le5": round(sum(1 for x in one if x[dk] <= 5) / len(one), 4) if one else None,
                "frac_ge25pct": (
                    round(sum(1 for x in one if x[lk] > 0 and x[dk] >= 0.25 * x[lk]) / len(one), 4)
                    if one
                    else None
                ),
                "median_norm": (
                    round(st.median([x[dk] / x[lk] for x in one if x[lk] > 0]), 4) if one else None
                ),
            },
        }
    return out


def stage_m2(ea_pairs: int) -> None:
    out: dict[str, Any] = {"config": {"budget_s": BUDGET_S, "ea_pairs_cap": ea_pairs}}
    cacheB: dict[tuple, tuple] = {}
    cacheC: dict[tuple, tuple] = {}

    def wbc(kb: KB) -> tuple[tuple, tuple]:
        key = kb_key(kb)
        if key not in cacheB:
            H = kb.to_hypergraph()
            rk = canonical_ranks(H)
            cacheB[key] = word_B(H, rk)
            cacheC[key] = word_C(H, rk)
        return cacheB[key], cacheC[key]

    # --- NDC natural series -------------------------------------------------
    kbs, pairs = load_ndc()
    log(f"M2 NDC: {len(pairs)} consecutive encodable pairs")
    arm = ArmA()
    sel = list(range(len(pairs)))
    random.Random(SEED_CORPUS).shuffle(sel)
    sel = set(sel[:ea_pairs])
    want: list[tuple[KB, int]] = []
    for pi, p in enumerate(pairs):
        if pi not in sel:
            continue
        a, b = kbs[p["i"]], kbs[p["j"]]
        k = max(required_k(a.to_hypergraph()), required_k(b.to_hypergraph()))
        want += [(a, k), (b, k)]
    arm.request(want)
    rows: list[dict] = []
    for p in pairs:
        a, b = kbs[p["i"]], kbs[p["j"]]
        b1, c1 = wbc(a)
        b2, c2 = wbc(b)
        rec = pair_distance(arm, a, b, b1, b2, c1, c2)
        rec["delta"] = p["delta"]
        rows.append(rec)
    out["ndc_classes_quarter"] = _series_report(rows)
    out["ndc_classes_quarter"]["arm_A"] = arm.stats()
    (HERE / "m2_rows_ndc.json").write_text(json.dumps(rows, default=float))
    dump(out, "m2_results.json")

    # --- WD50K synthetic ladders -------------------------------------------
    wd = load_wd50k66()
    r = random.Random(SEED_CORPUS)
    base = r.sample(wd, min(N_REAL_M1, len(wd)))
    rng = random.Random(SEED_EDITS + 1)
    log(f"M2 WD50K(66): {len(base)} base KBs, synthetic ladders t=1..5")
    arm2 = ArmA()
    ladder: list[tuple[KB, KB, int]] = []
    for kb in base:
        for t in (1, 2, 3, 4, 5):
            ed = random_walk(kb, t, rng)
            if ed is None:
                continue
            delta = len(kb.fact_set() ^ ed.fact_set())
            ladder.append((kb, ed, delta))
    ea_cap = min(ea_pairs, len(ladder))
    idx = list(range(len(ladder)))
    random.Random(SEED_CORPUS).shuffle(idx)
    keep = set(idx[:ea_cap])
    want2: list[tuple[KB, int]] = []
    for li, (kb, ed, _) in enumerate(ladder):
        if li not in keep:
            continue
        k = max(required_k(kb.to_hypergraph()), required_k(ed.to_hypergraph()))
        want2 += [(kb, k), (ed, k)]
    arm2.request(want2)
    rows2: list[dict] = []
    for kb, ed, delta in ladder:
        b1, c1 = wbc(kb)
        b2, c2 = wbc(ed)
        rec = pair_distance(arm2, kb, ed, b1, b2, c1, c2)
        rec["delta"] = delta
        rows2.append(rec)
    out["wd50k66_synthetic_ladder"] = _series_report(rows2)
    out["wd50k66_synthetic_ladder"]["arm_A"] = arm2.stats()
    out["wd50k66_synthetic_ladder"]["note"] = (
        "no natural variant series exists for WD50K; edits are synthetic "
        "constant-set-preserving fact insert/delete walks of length t=1..5, "
        "delta = |F_0 symmetric-difference F_t| computed exactly on stable ids"
    )
    (HERE / "m2_rows_wd50k.json").write_text(json.dumps(rows2, default=float))
    dump(out, "m2_results.json")


# ---------------------------------------------------------------------------
# M3 / M4 -- compactness, cost, differentiation from nauty
# ---------------------------------------------------------------------------


def stage_m34(ea_kbs: int) -> None:
    r = random.Random(SEED_CORPUS)
    ndc, pairs = load_ndc()
    wd = load_wd50k66()
    corpora = {
        "synthetic": gen_synthetic(N_SYNTH_M0, SEED_CORPUS)[:N_SYNTH_M1],
        "ndc_classes_quarter": r.sample(ndc, min(N_REAL_M1, len(ndc))),
        "wd50k66": r.sample(wd, min(N_REAL_M1, len(wd))),
    }
    m3: dict[str, Any] = {"config": {"budget_s": BUDGET_S, "ea_kbs_per_corpus": ea_kbs}}
    for name, kbs in corpora.items():
        arm = ArmA()
        arm.request([(kb, required_k(kb.to_hypergraph())) for kb in kbs[:ea_kbs]])
        lenB: list[float] = []
        lenC: list[float] = []
        tB: list[float] = []
        tC: list[float] = []
        for kb in kbs:
            H = kb.to_hypergraph()
            t0 = time.perf_counter()
            rk = canonical_ranks(H)
            wb = word_B(H, rk)
            tB.append(time.perf_counter() - t0)
            t0 = time.perf_counter()
            rk2 = canonical_ranks(H)
            wc = word_C(H, rk2)
            tC.append(time.perf_counter() - t0)
            lenB.append(len(wb))
            lenC.append(len(wc))
        lenA = [
            len(arm.word(kb, required_k(kb.to_hypergraph())) or ())
            for kb in kbs[:ea_kbs]
            if arm.word(kb, required_k(kb.to_hypergraph())) is not None
        ]
        tA = [
            arm.secs(kb, required_k(kb.to_hypergraph()))
            for kb in kbs[:ea_kbs]
            if arm.secs(kb, required_k(kb.to_hypergraph())) is not None
        ]
        m3[name] = {
            "n": len(kbs),
            "n_A": len(lenA),
            "tokens": {"A": quant(lenA), "B": quant(lenB), "C": quant(lenC)},
            "secs": {"A": quant([x for x in tA if x is not None]), "B": quant(tB), "C": quant(tC)},
            "arm_A": arm.stats(),
            "kb_size": {"n": quant([kb.n for kb in kbs]), "m": quant([float(kb.m) for kb in kbs])},
        }
        dump(m3, "m3_results.json")
    dump(m3, "m3_results.json")

    # ---- M4: how close is E-B to the nauty certificate? --------------------
    from scipy.stats import spearmanr

    m4: dict[str, Any] = {}
    cache: dict[tuple, tuple[tuple, tuple, bytes]] = {}

    def trio(kb: KB) -> tuple[tuple, tuple, bytes]:
        key = kb_key(kb)
        if key not in cache:
            H = kb.to_hypergraph()
            rk = canonical_ranks(H)
            cache[key] = (word_B(H, rk), word_C(H, rk), nauty_fingerprint(H))
        return cache[key]

    pair_sets: dict[str, list[tuple[KB, KB]]] = {}
    pair_sets["ndc_consecutive"] = [(ndc[p["i"]], ndc[p["j"]]) for p in pairs]
    rng = random.Random(SEED_EDITS + 2)
    for name, kbs in corpora.items():
        sub: list[tuple[KB, KB]] = []
        for kb in kbs[:120]:
            for kind in EDIT_KINDS:
                for ed in sample_edits(kb, kind, 2, rng):
                    sub.append((kb, ed))
        pair_sets[f"{name}_single_edit"] = sub
        pool = kbs[:120]
        rnd = [(rng.choice(pool), rng.choice(pool)) for _ in range(600)]
        pair_sets[f"{name}_random"] = [(a, b) for a, b in rnd if kb_key(a) != kb_key(b)]

    for name, ps in pair_sets.items():
        dn: list[float] = []
        db: list[float] = []
        dc: list[float] = []
        for a, b in ps:
            wb1, wc1, f1 = trio(a)
            wb2, wc2, f2 = trio(b)
            dn.append(byte_levenshtein(f1, f2))
            db.append(token_levenshtein(wb1, wb2))
            dc.append(token_levenshtein(wc1, wc2))
        m4[name] = {
            "n_pairs": len(ps),
            "spearman_nauty_vs_B": round(float(spearmanr(dn, db).statistic), 4) if ps else None,
            "spearman_nauty_vs_C": round(float(spearmanr(dn, dc).statistic), 4) if ps else None,
            "spearman_B_vs_C": round(float(spearmanr(db, dc).statistic), 4) if ps else None,
            "median": {"nauty_bytes": st.median(dn), "B": st.median(db), "C": st.median(dc)},
        }
        dump(m4, "m4_results.json")
    dump(m4, "m4_results.json")


def stage_roles() -> None:
    """Optional fourth arm: E-C-roles on WD50K(66) (M1 response + M3 token count)."""
    from f4_roles import ROLE_NAMES, load_wd50k66_roles, sample_edits_roles, word_C_roles

    rkbs = load_wd50k66_roles()
    r = random.Random(SEED_CORPUS)
    base = r.sample(rkbs, min(N_REAL_M1, len(rkbs)))
    rng = random.Random(SEED_EDITS + 3)
    log(f"E-C-roles: {len(base)} WD50K(66) base KBs")

    cache: dict[tuple, tuple[Any, Any]] = {}

    def words(rkb: Any) -> tuple[Any, Any]:
        key = (rkb.n, rkb.types, rkb.rfacts)
        if key not in cache:
            kb = rkb.to_kb()
            H = kb.to_hypergraph()
            rk = canonical_ranks(H)
            cache[key] = (word_C(H, rk), word_C_roles(rkb))
        return cache[key]

    rows: list[dict] = []
    for i, rkb in enumerate(base):
        c1, cr1 = words(rkb)
        for kind in EDIT_KINDS:
            for ed in sample_edits_roles(rkb, kind, EDITS_PER_KIND, rng):
                c2, cr2 = words(ed)
                rows.append(
                    {
                        "base": i,
                        "kind": kind,
                        "d_C": token_levenshtein(c1, c2),
                        "d_Croles": token_levenshtein(cr1, cr2),
                        "len_C": len(c1),
                        "len_Croles": len(cr1),
                    }
                )
    out: dict[str, Any] = {
        "corpus": "wd50k66",
        "roles": ROLE_NAMES,
        "n_base": len(base),
        "n_pairs": len(rows),
        "by_kind": {},
        "tokens": {
            "C": quant([len(words(x)[0]) for x in base]),
            "C_roles": quant([len(words(x)[1]) for x in base]),
        },
        "distinct_symbols": {
            "C": quant([float(len(set(words(x)[0]))) for x in base]),
            "C_roles": quant([float(len(set(words(x)[1]))) for x in base]),
        },
    }
    for kind in EDIT_KINDS:
        sub = [x for x in rows if x["kind"] == kind]
        out["by_kind"][kind] = {
            "n_pairs": len(sub),
            "C": {
                "abs": quant([x["d_C"] for x in sub]),
                "norm": quant([x["d_C"] / x["len_C"] for x in sub if x["len_C"]]),
            },
            "C_roles": {
                "abs": quant([x["d_Croles"] for x in sub]),
                "norm": quant([x["d_Croles"] / x["len_Croles"] for x in sub if x["len_Croles"]]),
            },
        }
    out["pooled"] = {
        "C": {
            "abs": quant([x["d_C"] for x in rows]),
            "norm": quant([x["d_C"] / x["len_C"] for x in rows if x["len_C"]]),
        },
        "C_roles": {
            "abs": quant([x["d_Croles"] for x in rows]),
            "norm": quant([x["d_Croles"] / x["len_Croles"] for x in rows if x["len_Croles"]]),
        },
    }
    dump(out, "mroles_results.json")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=("m0", "m1", "m2", "m34", "roles"))
    ap.add_argument("--ea-kbs", type=int, default=N_SYNTH_M1)
    ap.add_argument("--ea-pairs", type=int, default=10**6)
    ap.add_argument("--workers", type=int, default=WORKERS)
    args = ap.parse_args()
    globals()["WORKERS"] = args.workers
    t0 = time.time()
    if args.stage == "m0":
        stage_m0()
    elif args.stage == "m1":
        stage_m1(args.ea_kbs)
    elif args.stage == "m2":
        stage_m2(args.ea_pairs)
    elif args.stage == "roles":
        stage_roles()
    else:
        stage_m34(args.ea_kbs)
    log(f"stage {args.stage} done in {time.time() - t0:.1f} s")


if __name__ == "__main__":
    sys.exit(main())
