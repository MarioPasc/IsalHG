"""Render the markdown tables of `probe_f4_topology.md` from the stage JSONs."""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENC = ("A", "B", "C")
CORPORA = ("synthetic", "ndc_classes_quarter", "wd50k66")
SHORT = {"synthetic": "synthetic", "ndc_classes_quarter": "NDC-classes", "wd50k66": "WD50K(66)"}


def load(name: str) -> dict | None:
    p = HERE / name
    return json.loads(p.read_text()) if p.exists() else None


def f(x, nd: int = 2) -> str:
    if x is None:
        return "--"
    return f"{x:.{nd}f}" if isinstance(x, float) else str(x)


def q(d: dict, nd: int = 1) -> str:
    return " / ".join(f(d[k], nd) for k in ("min", "p25", "med", "p75", "p90", "max"))


def m0() -> None:
    d = load("m0_results.json")
    if not d:
        return
    print("\n### M0a -- isomorphism invariance\n")
    print("| corpus | N | E-A checked / viol | E-B | E-C |")
    print("|---|---|---|---|---|")
    for c in CORPORA:
        v = d["corpora"][c]["iso_invariance"]
        print(
            f"| {SHORT[c]} | {d['corpora'][c]['n']} | "
            + " | ".join(f"{v[e]['checked']} / {v[e]['violations']}" for e in ENC)
            + " |"
        )
    print("\n### M0b -- completeness against pynauty-Levi\n")
    print(
        "| corpus | enc | N | iso classes (nauty) | classes (enc) | false merges | false splits |"
    )
    print("|---|---|---|---|---|---|---|")
    for c in CORPORA:
        for e in ENC:
            x = d["corpora"][c]["completeness"][e]
            print(
                f"| {SHORT[c]} | E-{e} | {x['n_checked']} | {x['iso_classes_nauty']} | "
                f"{x['classes_enc']} | {x['false_merges']} | {x['false_splits']} |"
            )
    a = d.get("arm_A")
    if a:
        print(
            f"\nE-A arm: {a['n']} canonicalizations, {a['ok']} ok, {a['dnf']} censored "
            f"at 60 s ({a['dnf_frac']:.4f}), secs med {a['secs']['med']:.4f} / "
            f"p90 {a['secs']['p90']:.4f} / max {a['secs']['max']:.1f}"
        )


def m1() -> None:
    d = load("m1_results.json")
    if not d:
        return
    print("\n### M1 -- single-edit response, absolute tokens (min/p25/med/p75/p90/max)\n")
    for c in CORPORA:
        if c not in d["corpora"]:
            continue
        v = d["corpora"][c]
        print(f"\n**{SHORT[c]}** -- {v['n_base']} base KBs, {v['n_pairs']} single-edit pairs\n")
        print(
            "| edit kind | n | E-A abs | E-A norm med | E-B abs | E-B norm med | E-C abs | E-C norm med |"
        )
        print("|---|---|---|---|---|---|---|---|")
        for kind, e in list(v["by_kind"].items()) + [
            ("**pooled**", {"n_pairs": v["n_pairs"], **v["pooled"]})
        ]:
            cells = []
            for enc in ENC:
                s = e[enc]
                if s["n"] == 0:
                    cells += ["--", "--"]
                else:
                    cells += [q(s["abs"], 0), f(s["norm"]["med"], 3)]
            print(f"| {kind} | {e['n_pairs']} | " + " | ".join(cells) + " |")
        a = v["arm_A"]
        print(
            f"\nE-A coverage: {a['n']} canonicalizations, {a['dnf']} censored "
            f"({a['dnf_frac']:.4f}); pairs scored under E-A: {v['pooled']['A']['n']}."
        )


def m2() -> None:
    d = load("m2_results.json")
    if not d:
        return
    print("\n### M2 -- variant series: distance vs known fact-level difference\n")
    for key, label in (
        ("ndc_classes_quarter", "NDC-classes quarterly, natural consecutive pairs"),
        ("wd50k66_synthetic_ladder", "WD50K(66), synthetic ladders t=1..5"),
    ):
        if key not in d:
            continue
        v = d[key]
        print(f"\n**{label}** -- {v['n_pairs']} pairs\n")
        print("| enc | n | Spearman | Pearson | med d @ D=0 | 1 | 2 | 3-5 | >5 |")
        print("|---|---|---|---|---|---|---|---|---|")
        for e in ENC:
            s = v.get(e, {})
            if "spearman" not in s:
                print(f"| E-{e} | {s.get('n', 0)} | -- | -- | -- | -- | -- | -- | -- |")
                continue
            ms = s["median_by_stratum"]
            print(
                f"| E-{e} | {s['n']} | {f(s['spearman'], 3)} | {f(s['pearson'], 3)} | "
                + " | ".join(f(ms[k], 1) for k in ("0", "1", "2", "3-5", ">5"))
                + " |"
            )
        print("\n| enc | D=1 pairs | frac d<=2 | frac d<=5 | frac d>=25% of word | med d/\\|w\\| |")
        print("|---|---|---|---|---|---|")
        for e in ENC:
            s = v.get(e, {})
            if "delta1" not in s:
                continue
            o = s["delta1"]
            print(
                f"| E-{e} | {o['n']} | {f(o['frac_le2'], 3)} | {f(o['frac_le5'], 3)} | "
                f"{f(o['frac_ge25pct'], 3)} | {f(o['median_norm'], 3)} |"
            )
        ns = v[ENC[1]]["n_by_stratum"]
        print("\nStratum sizes: " + ", ".join(f"D={k}: {n}" for k, n in ns.items()))


def m3() -> None:
    d = load("m3_results.json")
    if not d:
        return
    print("\n### M3 -- compactness and cost\n")
    print(
        "| corpus | N | n med | m med | tokens A med/p90 | tokens B | tokens C | secs A med/p90 | secs B | secs C | A DNF |"
    )
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for c in CORPORA:
        if c not in d:
            continue
        v = d[c]
        t, s, a = v["tokens"], v["secs"], v["arm_A"]

        def pair(x, nd=1):
            return f"{f(x['med'], nd)} / {f(x['p90'], nd)}"

        print(
            f"| {SHORT[c]} | {v['n']} | {f(v['kb_size']['n']['med'], 0)} | "
            f"{f(v['kb_size']['m']['med'], 0)} | {pair(t['A'], 0)} | {pair(t['B'], 0)} | "
            f"{pair(t['C'], 0)} | {pair(s['A'], 4)} | {pair(s['B'], 5)} | {pair(s['C'], 5)} | "
            f"{f(a['dnf_frac'], 4)} |"
        )


def m4() -> None:
    d = load("m4_results.json")
    if not d:
        return
    print("\n### M4 -- proximity to the nauty-certificate distance\n")
    print(
        "| pair set | pairs | rho(nauty, d_B) | rho(nauty, d_C) | rho(d_B, d_C) | med nauty bytes | med d_B | med d_C |"
    )
    print("|---|---|---|---|---|---|---|---|")
    for k, v in d.items():
        m = v["median"]
        print(
            f"| {k} | {v['n_pairs']} | {f(v['spearman_nauty_vs_B'], 3)} | "
            f"{f(v['spearman_nauty_vs_C'], 3)} | {f(v['spearman_B_vs_C'], 3)} | "
            f"{f(m['nauty_bytes'], 0)} | {f(m['B'], 0)} | {f(m['C'], 0)} |"
        )


def roles() -> None:
    d = load("mroles_results.json")
    if not d:
        return
    print("\n### E-C-roles (WD50K(66) only)\n")
    print(f"{d['n_base']} base KBs, {d['n_pairs']} single-edit pairs.")
    print(
        f"Token count: E-C med {f(d['tokens']['C']['med'], 0)}, "
        f"E-C-roles med {f(d['tokens']['C_roles']['med'], 0)}; "
        f"distinct symbols per word: E-C med {f(d['distinct_symbols']['C']['med'], 0)}, "
        f"E-C-roles med {f(d['distinct_symbols']['C_roles']['med'], 0)}.\n"
    )
    print("| edit kind | n | E-C abs | E-C norm med | E-C-roles abs | E-C-roles norm med |")
    print("|---|---|---|---|---|---|")
    rows = list(d["by_kind"].items()) + [("**pooled**", {"n_pairs": d["n_pairs"], **d["pooled"]})]
    for kind, e in rows:
        print(
            f"| {kind} | {e['n_pairs']} | {q(e['C']['abs'], 0)} | {f(e['C']['norm']['med'], 3)} | "
            f"{q(e['C_roles']['abs'], 0)} | {f(e['C_roles']['norm']['med'], 3)} |"
        )


if __name__ == "__main__":
    m0()
    m1()
    m2()
    m3()
    m4()
    roles()
