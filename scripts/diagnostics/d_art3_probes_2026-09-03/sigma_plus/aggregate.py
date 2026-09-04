"""Aggregate Task 4 / Task 5 results into report tables + the anchor-rank probe."""

from __future__ import annotations

import json
import random
import statistics as st
from collections import defaultdict

import sigma_plus as SP
from t3_prop4 import anchor_of, make_kb

from isalhg.core.canonical import canonical_string

K = 3


def t4_table() -> None:
    d = json.load(open("results_t4.json"))
    g = defaultdict(list)
    for r in d["rows"]:
        g[(r["n"], r["m"], r["t"], r["family"])].append(r)
    print(
        f"\nTask 4 -- {d['profiles_done']} profiles, {d['wall']:.0f}s, "
        f"{d['n_canon']} component canonicalizations"
    )
    print(
        "| cell | t | fam | cov1(H0)/7 | best copy/6 | H0 uniq max r1 | "
        "cov2(H0)/7 | best copy/6 | H0 uniq max r2 | copy->copy r1 | C-facts/m |"
    )
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for kk in sorted(g):
        rs = g[kk]
        n, m, t, fam = kk
        cf = st.mean(r["enum"]["n_cost1_facts"] for r in rs)
        me = st.mean(r["enum"]["n_edges"] for r in rs)
        print(
            f"| ({n},{m}) | {t} | {fam} | {st.mean(r['cov1_H0'] for r in rs):.2f} | "
            f"{st.mean(r['cov1_best_copy'] for r in rs):.2f} | "
            f"{sum(r['H0_unique_max1'] for r in rs)}/{len(rs)} | "
            f"{st.mean(r['cov2_H0'] for r in rs):.2f} | "
            f"{st.mean(r['cov2_best_copy'] for r in rs):.2f} | "
            f"{sum(r['H0_unique_max2'] for r in rs)}/{len(rs)} | "
            f"{st.mean(r['copy_to_copy_r1'] for r in rs):.2f} | {cf:.1f}/{me:.1f} |"
        )
    e = d["rows"][0]["enum"]
    print(
        f"\nper-candidate enumeration (n=8 example): L={e['L']} "
        f"package decodes={e['n_package_decodes']} A+ decodes={e['n_aplus_decodes']} "
        f"|A|={e['n_A_tokens']} |A+|={e['n_Aplus_tokens']} |S+|={e['n_sigma_plus']}"
    )
    big = max(d["rows"], key=lambda r: r["enum"]["n_sigma_plus"])["enum"]
    print(
        f"per-candidate enumeration (n=10 example): L={big['L']} "
        f"package decodes={big['n_package_decodes']} A+ decodes={big['n_aplus_decodes']} "
        f"|A|={big['n_A_tokens']} |A+|={big['n_Aplus_tokens']} |S+|={big['n_sigma_plus']}"
    )


def t5_table() -> None:
    d = json.load(open("results_t5.json"))
    print("\nTask 5 -- ball cost")
    print(
        "| cell | centre | n | L | |S_HG|=13 | |S_HG|(3 lbl)=25 | |A| | |A+| | |S+| | "
        "|B1| (13) | |B1| (25) | |B1+| | ratio +/13 |"
    )
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in d["rows"]:
        print(
            f"| {r['cell']} | {r['centre']} | {r['n']} | {r['L']} | 13 | 25 | {r['n_A']} | "
            f"{r['n_Aplus']} | {r['sigma_plus']} | {r['B1_trivial']} | {r['B1_pkg']} | "
            f"{r['B1_plus']} | {r['ratio_plus_over_trivial']:.1f}x |"
        )
    print(
        "\n| centre | L | words in B1+ | decode s | us/word | connected&non-empty | "
        "distinct structures | canon ms each (n=300) | projected full canon s |"
    )
    print("|---|---|---|---|---|---|---|---|---|")
    for r in d["timed"]:
        print(
            f"| {r['centre']} | {r['L']} | {r['words']} | {r['decode_secs']:.2f} | "
            f"{r['decode_us_per_word']:.1f} | {r['connected_nonempty']} "
            f"({100 * r['connected_nonempty'] / r['words']:.1f}%) | "
            f"{r['distinct_structures']} | {r['canon_ms_each']:.2f} | "
            f"{r['projected_full_canon_secs']:.1f} |"
        )


def anchor_probe(n_kb: int = 300) -> None:
    rng = random.Random(20260903 + 99)
    non_anchor, deg_dom = 0, 0
    ranks = []
    for _ in range(n_kb):
        H = make_kb(rng)
        H0 = SP.decode_plus(SP.parse_plus(canonical_string(H, k=K)), k=K, n_edge_labels=3)
        a = anchor_of(H0)
        if a != 0:
            non_anchor += 1
            ranks.append(a)
        # is the anchor the strict max-degree vertex of H?
        degs = sorted((H.degree(v) for v in range(H.n_nodes)), reverse=True)
        deg_dom += int(H.degree(anchor_of(H)) > degs[1])
    print(
        f"\nanchor probe on {n_kb} fresh KBs: seed != anchor in {non_anchor} "
        f"({100 * non_anchor / n_kb:.1f} %); non-zero anchor ranks seen: {sorted(set(ranks))}; "
        f"anchor is the strict max-degree vertex in {deg_dom}/{n_kb}"
    )


if __name__ == "__main__":
    t4_table()
    t5_table()
    anchor_probe()
