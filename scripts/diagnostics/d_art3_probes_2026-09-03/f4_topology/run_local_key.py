"""Driver for the E-D / E-D1 local-key follow-on (N0-N4).

Stages are independent and each writes its JSON as soon as it finishes.

    python run_local_key.py --stage n0     # correctness
    python run_local_key.py --stage n1     # single-edit response, split by regime
    python run_local_key.py --stage n2     # NDC natural series, split by regime
    python run_local_key.py --stage n3     # key diversity + the mechanism
    python run_local_key.py --stage n4     # tokens and wall-clock

E-A and E-C distances are read from the earlier probe's caches
(``m1_rows_*.json``, ``m2_rows_ndc.json``, ``m3_results.json``); nothing here
re-runs ``canonical_string``. The M1/M2/M3 corpora and job lists are rebuilt by
replaying ``run_probe.stage_*``'s RNG consumption exactly, and the replay is
checked against the cached rows' ``(base, kind)`` sequence.
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

from f4_corpora import EDIT_KINDS, gen_synthetic, load_ndc, load_wd50k66
from f4_encodings import (
    KB,
    canonical_ranks,
    nauty_fingerprint,
    token_levenshtein,
    word_B,
    word_C,
)
from f4_local_key import (
    key_addresses,
    keys_of,
    sample_edits_traced,
    verify_trace_equivalence,
    word_key,
)

from isalhg.core.sparse_hypergraph import permute

HERE = Path(__file__).resolve().parent
SEED_CORPUS = 20260904
SEED_EDITS = 20260905
SEED_PERM = 20260906
N_SYNTH_M0 = 2000
N_SYNTH_M1 = 300
N_REAL_M1 = 200
N_REAL_M0 = 500
EDITS_PER_KIND = 10

NEW = ("D", "D1")
PRESERVING_KINDS = ("insert_fact", "delete_fact", "add_constant", "remove_constant")


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
# Corpus replays (byte-identical to run_probe's)
# ---------------------------------------------------------------------------


def corpora_m1() -> dict[str, list[KB]]:
    """``run_probe.stage_m1``'s corpora, same RNG consumption order."""
    r = random.Random(SEED_CORPUS)
    ndc, _ = load_ndc()
    wd = load_wd50k66()
    return {
        "synthetic": gen_synthetic(N_SYNTH_M0, SEED_CORPUS)[:N_SYNTH_M1],
        "ndc_classes_quarter": r.sample(ndc, min(N_REAL_M1, len(ndc))),
        "wd50k66": r.sample(wd, min(N_REAL_M1, len(wd))),
    }


def corpora_m0() -> dict[str, list[KB]]:
    """``run_probe.stage_m0``'s corpora."""
    synth = gen_synthetic(N_SYNTH_M0, SEED_CORPUS)
    ndc, _ = load_ndc()
    wd = load_wd50k66()
    r = random.Random(SEED_CORPUS)
    return {
        "synthetic": synth,
        "ndc_classes_quarter": r.sample(ndc, min(N_REAL_M0, len(ndc))),
        "wd50k66": r.sample(wd, min(N_REAL_M0, len(wd))),
    }


class Words:
    """Per-KB word cache: one nauty call feeds B, C, D and D1."""

    def __init__(self, encs: tuple[str, ...] = ("B", "C", "D", "D1")) -> None:
        self.encs = encs
        self.cache: dict[tuple, dict[str, tuple]] = {}

    def get(self, kb: KB) -> dict[str, tuple]:
        key = kb_key(kb)
        hit = self.cache.get(key)
        if hit is None:
            H = kb.to_hypergraph()
            rk = canonical_ranks(H)
            hit = {}
            if "B" in self.encs:
                hit["B"] = word_B(H, rk)
            if "C" in self.encs:
                hit["C"] = word_C(H, rk)
            for e in NEW:
                if e in self.encs:
                    hit[e] = word_key(H, e, rk)
            self.cache[key] = hit
        return hit


def regime(kb: KB, ed: KB, kind: str) -> str:
    """``preserving`` iff the edit neither adds nor strands a constant."""
    if kind == "insert_fact_new_constant":
        return "changing"
    return "preserving" if ed.n == kb.n else "changing"


# ---------------------------------------------------------------------------
# N0 -- correctness
# ---------------------------------------------------------------------------


def stage_n0() -> None:
    rng = random.Random(SEED_PERM)
    corpora = corpora_m0()
    out: dict[str, Any] = {
        "seeds": {"corpus": SEED_CORPUS, "perm": SEED_PERM},
        "note": "E-A/E-B/E-C rows carried from m0_results.json; this stage scores E-D and E-D1",
        "corpora": {},
    }
    for name, kbs in corpora.items():
        log(f"N0 {name}: {len(kbs)} instances")
        perms: list[KB] = []
        for kb in kbs:
            H = kb.to_hypergraph()
            sig = list(range(H.n_nodes))
            rng.shuffle(sig)
            P = permute(H, sig)
            perms.append(
                KB(
                    n=H.n_nodes,
                    types=tuple(P.vertex_label(v) for v in range(H.n_nodes)),
                    facts=tuple((lab, mem) for _, mem, lab in P.iter_edges()),
                    n_types=kb.n_types,
                    n_preds=kb.n_preds,
                )
            )
        viol = dict.fromkeys(NEW, 0)
        words: dict[str, list[tuple]] = {e: [] for e in NEW}
        fps: list[bytes] = []
        for kb, pkb in zip(kbs, perms, strict=True):
            H, P = kb.to_hypergraph(), pkb.to_hypergraph()
            rk_h, rk_p = canonical_ranks(H), canonical_ranks(P)
            for e in NEW:
                w1, w2 = word_key(H, e, rk_h), word_key(P, e, rk_p)
                viol[e] += int(w1 != w2)
                words[e].append(w1)
            fps.append(nauty_fingerprint(H))

        def partition(xs: list) -> dict[Any, list[int]]:
            g: dict[Any, list[int]] = {}
            for i, x in enumerate(xs):
                g.setdefault(x, []).append(i)
            return g

        sub_ref = partition(fps)
        ref_lab = {
            i: j
            for j, (_, mem) in enumerate(sorted(sub_ref.items(), key=lambda kv: kv[1]))
            for i in mem
        }
        comp: dict[str, Any] = {}
        for e in NEW:
            sub_enc = partition(words[e])
            enc_lab = {
                i: j
                for j, (_, mem) in enumerate(sorted(sub_enc.items(), key=lambda kv: kv[1]))
                for i in mem
            }
            merges = splits = 0
            for i in range(len(kbs)):
                for j in range(i + 1, len(kbs)):
                    same_ref = ref_lab[i] == ref_lab[j]
                    same_enc = enc_lab[i] == enc_lab[j]
                    merges += int(same_enc and not same_ref)
                    splits += int(same_ref and not same_enc)
            comp[e] = {
                "n_checked": len(kbs),
                "iso_classes_nauty": len(sub_ref),
                "classes_enc": len(sub_enc),
                "false_merges": merges,
                "false_splits": splits,
            }
        out["corpora"][name] = {
            "n": len(kbs),
            "iso_invariance": {e: {"checked": len(kbs), "violations": viol[e]} for e in NEW},
            "completeness": comp,
        }
        dump(out, "n0_results.json")

    # RNG-equivalence of the traced edit replay used by N1/N3
    small = corpora["synthetic"][:400]
    out["trace_equivalence"] = verify_trace_equivalence(small, EDIT_KINDS, SEED_EDITS + 99)
    dump(out, "n0_results.json")


# ---------------------------------------------------------------------------
# N1 -- single-edit response, split by regime
# ---------------------------------------------------------------------------


def _replay_jobs(
    kbs: list[KB], rng: random.Random
) -> list[tuple[int, str, KB, KB, dict[int, int]]]:
    jobs: list[tuple[int, str, KB, KB, dict[int, int]]] = []
    for i, kb in enumerate(kbs):
        for kind in EDIT_KINDS:
            for ed, corr in sample_edits_traced(kb, kind, EDITS_PER_KIND, rng):
                jobs.append((i, kind, kb, ed, corr))
    return jobs


def _cached_rows(name: str) -> list[dict]:
    return json.loads((HERE / f"m1_rows_{name}.json").read_text())


def stage_n1() -> None:
    rng = random.Random(SEED_EDITS)
    corpora = corpora_m1()
    out: dict[str, Any] = {
        "config": {
            "edits_per_kind": EDITS_PER_KIND,
            "seed_edits": SEED_EDITS,
            "regime_rule": "preserving iff the edit neither adds nor strands a constant",
        },
        "corpora": {},
    }
    for name, kbs in corpora.items():
        log(f"N1 {name}: {len(kbs)} base KBs")
        jobs = _replay_jobs(kbs, rng)
        cached = _cached_rows(name)
        assert len(jobs) == len(cached), (name, len(jobs), len(cached))
        for (i, kind, _, _, _), row in zip(jobs, cached, strict=True):
            assert row["base"] == i and row["kind"] == kind, (name, i, kind, row)
        log(f"  {len(jobs)} single-edit pairs (replay matches cache)")

        W = Words()
        rows: list[dict] = []
        b_mismatch = 0
        for (i, kind, kb, ed, _), row in zip(jobs, cached, strict=True):
            w1, w2 = W.get(kb), W.get(ed)
            rec: dict[str, Any] = {
                "base": i,
                "kind": kind,
                "regime": regime(kb, ed, kind),
                "n_base": kb.n,
                "n_edit": ed.n,
            }
            for e in ("B", "C", "D", "D1"):
                rec[f"d_{e}"] = token_levenshtein(w1[e], w2[e])
                rec[f"len_{e}"] = len(w1[e])
            b_mismatch += int(rec["d_B"] != row["d_B"] or rec["d_C"] != row["d_C"])
            if "d_A" in row:
                rec["d_A"] = row["d_A"]
                rec["len_A"] = row["len_A"]
            rows.append(rec)
        assert b_mismatch == 0, f"{name}: {b_mismatch} cached-vs-recomputed B/C mismatches"

        def block(sub: list[dict]) -> dict[str, Any]:
            entry: dict[str, Any] = {"n_pairs": len(sub)}
            for e in ("A", "B", "C", "D", "D1"):
                dk, lk = f"d_{e}", f"len_{e}"
                vals = [x[dk] for x in sub if dk in x]
                norm = [x[dk] / x[lk] for x in sub if dk in x and x[lk] > 0]
                entry[e] = {"n": len(vals), "abs": quant(vals), "norm": quant(norm)}
            return entry

        by: dict[str, Any] = {}
        for reg in ("preserving", "changing"):
            sub_reg = [x for x in rows if x["regime"] == reg]
            by[reg] = {
                "pooled": block(sub_reg),
                "by_kind": {
                    kind: block([x for x in sub_reg if x["kind"] == kind])
                    for kind in EDIT_KINDS
                    if any(x["kind"] == kind for x in sub_reg)
                },
            }
        out["corpora"][name] = {
            "n_base": len(kbs),
            "n_pairs": len(rows),
            "n_preserving": sum(1 for x in rows if x["regime"] == "preserving"),
            "n_changing": sum(1 for x in rows if x["regime"] == "changing"),
            "regimes": by,
            "pooled_all": block(rows),
        }
        (HERE / f"n1_rows_{name}.json").write_text(json.dumps(rows, default=float))
        dump(out, "n1_results.json")
    dump(out, "n1_results.json")


# ---------------------------------------------------------------------------
# N2 -- the NDC natural series, both regimes
# ---------------------------------------------------------------------------


def stage_n2() -> None:
    from followup_ndc_regime import constant_sets
    from scipy.stats import pearsonr, spearmanr

    strata = {"0": (0, 0), "1": (1, 1), "2": (2, 2), "3-5": (3, 5), ">5": (6, 10**9)}
    kbs, pairs = load_ndc()
    cached = json.loads((HERE / "m2_rows_ndc.json").read_text())
    assert len(cached) == len(pairs), (len(cached), len(pairs))
    vs = constant_sets()
    log(f"N2 NDC: {len(pairs)} consecutive encodable pairs")

    W = Words()
    keep: list[dict] = []
    change: list[dict] = []
    for p, row in zip(pairs, cached, strict=True):
        a, b = kbs[p["i"]], kbs[p["j"]]
        w1, w2 = W.get(a), W.get(b)
        rec = dict(row)
        for e in NEW:
            rec[f"d_{e}"] = token_levenshtein(w1[e], w2[e])
            rec[f"len_{e}"] = len(w1[e])
        sa, sb = vs[(p["node"], p["window"])], vs[(p["node"], p["window"] + 1)]
        rec["n_const_moved"] = len(sa ^ sb)
        (keep if sa == sb else change).append(rec)

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
                for s, (lo, hi) in strata.items()
            },
            "n_by": {
                s: sum(1 for r in sub if lo <= r["delta"] <= hi) for s, (lo, hi) in strata.items()
            },
            "delta1_n": len(one),
            "delta1_le2": round(sum(1 for r in one if r[dk] <= 2) / len(one), 3) if one else None,
            "delta1_le5": round(sum(1 for r in one if r[dk] <= 5) / len(one), 3) if one else None,
            "delta1_norm": (
                round(st.median([r[dk] / r[lk] for r in one if r[lk]]), 3) if one else None
            ),
        }

    encs = ("A", "B", "C", "D", "D1")
    moved = [r["n_const_moved"] for r in change]
    out = {
        "counts": {"preserving": len(keep), "changing": len(change), "total": len(cached)},
        "preserving": {e: score(keep, e) for e in encs},
        "changing": {e: score(change, e) for e in encs},
        "constants_moved_on_changing_pairs": {
            "median": st.median(moved),
            "mean": round(st.fmean(moved), 2),
            "max": max(moved),
            "spearman_moved_vs_d": {
                e: (
                    round(
                        float(
                            spearmanr(
                                [r["n_const_moved"] for r in change if f"d_{e}" in r],
                                [r[f"d_{e}"] for r in change if f"d_{e}" in r],
                            ).statistic
                        ),
                        3,
                    )
                    if sum(1 for r in change if f"d_{e}" in r) > 2
                    else None
                )
                for e in encs
            },
            "n_by_enc": {e: sum(1 for r in change if f"d_{e}" in r) for e in encs},
        },
    }
    (HERE / "n2_rows_ndc.json").write_text(json.dumps({"preserving": keep, "changing": change}))
    dump(out, "n2_results.json")


# ---------------------------------------------------------------------------
# N3 -- key diversity and the mechanism
# ---------------------------------------------------------------------------


def stage_n3() -> None:
    corpora = corpora_m1()
    out: dict[str, Any] = {"diversity": {}, "mechanism": {}}

    for name, kbs in corpora.items():
        log(f"N3 diversity {name}: {len(kbs)} base KBs")
        div: dict[str, Any] = {}
        for e in NEW:
            n_keys: list[float] = []
            sizes: list[float] = []
            frac_singleton: list[float] = []
            frac_keys_per_n: list[float] = []
            for kb in kbs:
                H = kb.to_hypergraph()
                ks = keys_of(H, e)
                counts: dict[Any, int] = {}
                for k in ks:
                    counts[k] = counts.get(k, 0) + 1
                n_keys.append(float(len(counts)))
                sizes.extend(float(c) for c in counts.values())
                frac_singleton.append(sum(c for c in counts.values() if c == 1) / H.n_nodes)
                frac_keys_per_n.append(len(counts) / H.n_nodes)
            div[e] = {
                "distinct_keys": quant(n_keys),
                "class_size": quant(sizes),
                "frac_constants_in_singleton_class": quant(frac_singleton),
                "keys_per_constant": quant(frac_keys_per_n),
            }
        out["diversity"][name] = div
        dump(out, "n3_results.json")

    rng = random.Random(SEED_EDITS)
    for name, kbs in corpora.items():
        log(f"N3 mechanism {name}")
        jobs = _replay_jobs(kbs, rng)
        rows: list[dict] = []
        addr_cache: dict[tuple, dict[str, tuple]] = {}
        key_cache: dict[tuple, dict[str, tuple]] = {}
        rank_cache: dict[tuple, tuple[int, ...]] = {}

        def state(
            kb: KB,
            addr_cache: dict = addr_cache,
            key_cache: dict = key_cache,
            rank_cache: dict = rank_cache,
        ) -> tuple[dict[str, tuple], dict[str, tuple], tuple[int, ...]]:
            kk = kb_key(kb)
            if kk not in addr_cache:
                H = kb.to_hypergraph()
                rk = canonical_ranks(H)
                rank_cache[kk] = rk
                addr_cache[kk] = {e: key_addresses(H, e, rk) for e in NEW}
                key_cache[kk] = {e: keys_of(H, e) for e in NEW}
            return addr_cache[kk], key_cache[kk], rank_cache[kk]

        for i, kind, kb, ed, corr in jobs:
            a1, k1, r1 = state(kb)
            a2, k2, r2 = state(ed)
            surv = sorted(corr)
            if not surv:
                continue
            rec: dict[str, Any] = {
                "base": i,
                "kind": kind,
                "regime": regime(kb, ed, kind),
                "n_surviving": len(surv),
                "rank_changed": sum(1 for v in surv if r1[v] != r2[corr[v]]) / len(surv),
            }
            for e in NEW:
                rec[f"key_changed_{e}"] = sum(1 for v in surv if k1[e][v] != k2[e][corr[v]]) / len(
                    surv
                )
                rec[f"addr_changed_{e}"] = sum(1 for v in surv if a1[e][v] != a2[e][corr[v]]) / len(
                    surv
                )
            rows.append(rec)

        def agg(sub: list[dict]) -> dict[str, Any]:
            cols = ["rank_changed"] + [
                f"{p}_{e}" for e in NEW for p in ("key_changed", "addr_changed")
            ]
            res: dict[str, Any] = {"n_edits": len(sub)}
            for c in cols:
                vals = [x[c] for x in sub]
                res[c] = {
                    "mean": round(st.fmean(vals), 4) if vals else None,
                    "frac_zero": round(sum(1 for v in vals if v == 0) / len(vals), 4)
                    if vals
                    else None,
                }
            return res

        out["mechanism"][name] = {
            "all": agg(rows),
            "preserving": agg([x for x in rows if x["regime"] == "preserving"]),
            "changing": agg([x for x in rows if x["regime"] == "changing"]),
            "by_kind": {
                kind: agg([x for x in rows if x["kind"] == kind])
                for kind in EDIT_KINDS
                if any(x["kind"] == kind for x in rows)
            },
        }
        dump(out, "n3_results.json")
    dump(out, "n3_results.json")


# ---------------------------------------------------------------------------
# N4 -- tokens and cost
# ---------------------------------------------------------------------------


def stage_n4() -> None:
    corpora = corpora_m1()
    cached = json.loads((HERE / "m3_results.json").read_text())
    out: dict[str, Any] = {
        "note": "E-A/E-B/E-C rows carried from m3_results.json (same corpora)",
        "corpora": {},
    }
    for name, kbs in corpora.items():
        log(f"N4 {name}: {len(kbs)} KBs")
        lens: dict[str, list[float]] = {e: [] for e in NEW}
        secs: dict[str, list[float]] = {e: [] for e in NEW}
        secs["B"] = []
        lens["B"] = []
        nauty: list[float] = []
        for kb in kbs:
            H = kb.to_hypergraph()
            t0 = time.perf_counter()
            canonical_ranks(H)
            nauty.append(time.perf_counter() - t0)
            for e in ("B", *NEW):
                t0 = time.perf_counter()
                rk2 = canonical_ranks(H)
                w = word_B(H, rk2) if e == "B" else word_key(H, e, rk2)
                secs[e].append(time.perf_counter() - t0)
                lens[e].append(float(len(w)))
        out["corpora"][name] = {
            "n": len(kbs),
            "tokens": {e: quant(lens[e]) for e in ("B", *NEW)},
            "secs_full": {e: quant(secs[e]) for e in ("B", *NEW)},
            "secs_nauty_only": quant(nauty),
            "cached_m3": {
                "tokens": cached[name]["tokens"],
                "secs": cached[name]["secs"],
                "kb_size": cached[name]["kb_size"],
            },
        }
        dump(out, "n4_results.json")
    dump(out, "n4_results.json")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=("n0", "n1", "n2", "n3", "n4"))
    args = ap.parse_args()
    t0 = time.time()
    {"n0": stage_n0, "n1": stage_n1, "n2": stage_n2, "n3": stage_n3, "n4": stage_n4}[args.stage]()
    log(f"stage {args.stage} done in {time.time() - t0:.1f} s")


if __name__ == "__main__":
    sys.exit(main())
