"""Render the N0-N4 JSON into the markdown tables of ``probe_f4_local_key.md``."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENCS = ("A", "B", "C", "D", "D1")
NAME = {
    "synthetic": "synth",
    "ndc_classes_quarter": "NDC",
    "wd50k66": "WD50K",
}
KIND = {
    "insert_fact": "insert_fact",
    "delete_fact": "delete_fact",
    "add_constant": "add_const",
    "remove_constant": "remove_const",
    "insert_fact_new_constant": "insert+new_const",
}


def load(name: str) -> Any:
    return json.loads((HERE / name).read_text())


def q(d: dict, key: str) -> str:
    v = d.get(key)
    return "—" if v is None else (f"{v:.0f}" if float(v).is_integer() else f"{v:.3g}")


def abs_str(entry: dict) -> str:
    a = entry["abs"]
    if a["min"] is None:
        return "—"
    return (
        f"{q(a, 'min')}/{q(a, 'p25')}/**{q(a, 'med')}**/{q(a, 'p75')}/{q(a, 'p90')}/{q(a, 'max')}"
    )


def nrm(entry: dict) -> str:
    v = entry["norm"]["med"]
    return "—" if v is None else f"{v:.3f}"


def n1_tables() -> str:
    r = load("n1_results.json")
    out: list[str] = []
    out.append(
        "| corpus | regime | n pairs | " + " | ".join(f"E-{e} abs | nrm" for e in ENCS) + " |"
    )
    out.append("|---|---|---|" + "---|---|" * len(ENCS))
    for c, blk in r["corpora"].items():
        for reg in ("preserving", "changing"):
            p = blk["regimes"][reg]["pooled"]
            cells = " | ".join(f"{abs_str(p[e])} | {nrm(p[e])}" for e in ENCS)
            out.append(f"| {NAME[c]} | {reg} | {p['n_pairs']} | {cells} |")
    out.append("")
    out.append(
        "| corpus | regime | edit kind | n | " + " | ".join(f"E-{e} abs | nrm" for e in ENCS) + " |"
    )
    out.append("|---|---|---|---|" + "---|---|" * len(ENCS))
    for c, blk in r["corpora"].items():
        for reg in ("preserving", "changing"):
            for k, e in blk["regimes"][reg]["by_kind"].items():
                if e["n_pairs"] == 0:
                    continue
                cells = " | ".join(f"{abs_str(e[x])} | {nrm(e[x])}" for x in ENCS)
                out.append(f"| {NAME[c]} | {reg} | {KIND[k]} | {e['n_pairs']} | {cells} |")
    return "\n".join(out)


def n1_locality() -> str:
    """Fraction of single-edit pairs at distance <= 1 and <= 2 tokens."""
    out: list[str] = []
    out.append("| corpus | regime | n | " + " | ".join(f"E-{e} ≤1 / ≤2" for e in ENCS) + " |")
    out.append("|---|---|---|" + "---|" * len(ENCS))
    for c, short in NAME.items():
        rows = json.loads((HERE / f"n1_rows_{c}.json").read_text())
        for reg in ("preserving", "changing"):
            sub = [r for r in rows if r["regime"] == reg]
            cells: list[str] = []
            for e in ENCS:
                k = f"d_{e}"
                s = [r for r in sub if k in r]
                if not s:
                    cells.append("—")
                    continue
                cells.append(
                    f"{sum(1 for r in s if r[k] <= 1) / len(s):.3f} / "
                    f"{sum(1 for r in s if r[k] <= 2) / len(s):.3f}"
                )
            out.append(f"| {short} | {reg} | {len(sub)} | " + " | ".join(cells) + " |")
    return "\n".join(out)


def n2_tables() -> str:
    r = load("n2_results.json")
    out: list[str] = []
    out.append(
        "| split | enc | n | ρ | r | med d at Δ = 0/1/2/3–5/>5 | Δ=1 n | ≤2 | ≤5 | med d/\\|w\\| |"
    )
    out.append("|---|---|---|---|---|---|---|---|---|---|")
    for split in ("preserving", "changing"):
        for e in ENCS:
            s = r[split][e]
            if "spearman" not in s:
                out.append(f"| {split} | E-{e} | {s['n']} | — | — | — | — | — | — | — |")
                continue
            med = " / ".join(
                "—" if s["med"][k] is None else f"{s['med'][k]:g}"
                for k in ("0", "1", "2", "3-5", ">5")
            )
            out.append(
                f"| {split} | E-{e} | {s['n']} | {s['spearman']:.3f} | {s['pearson']:.3f} | {med} "
                f"| {s['delta1_n']} | {s['delta1_le2']:.3f} | {s['delta1_le5']:.3f} "
                f"| {s['delta1_norm']:.3f} |"
            )
    out.append("")
    m = r["constants_moved_on_changing_pairs"]
    out.append("| ρ(constants moved, d) | " + " | ".join(f"E-{e}" for e in ENCS) + " |")
    out.append("|---|" + "---|" * len(ENCS))
    row = " | ".join(
        "—" if m["spearman_moved_vs_d"][e] is None else f"{m['spearman_moved_vs_d'][e]:.3f}"
        for e in ENCS
    )
    out.append(f"| 415 changing pairs (n scored) | {row} |")
    out.append(
        "| n pairs with the distance | " + " | ".join(str(m["n_by_enc"][e]) for e in ENCS) + " |"
    )
    return "\n".join(out)


def n3_tables() -> str:
    r = load("n3_results.json")
    out: list[str] = []
    out.append(
        "| corpus | key | distinct keys med/p90 | keys per constant med | "
        "class size med/p90/max | frac constants in singleton class med/mean |"
    )
    out.append("|---|---|---|---|---|---|")
    for c, blk in r["diversity"].items():
        for e in ("D", "D1"):
            d = blk[e]
            out.append(
                f"| {NAME[c]} | E-{e} | {q(d['distinct_keys'], 'med')}/{q(d['distinct_keys'], 'p90')} "  # noqa: E501
                f"| {d['keys_per_constant']['med']:.3f} "
                f"| {q(d['class_size'], 'med')}/{q(d['class_size'], 'p90')}/{q(d['class_size'], 'max')} "  # noqa: E501
                f"| {d['frac_constants_in_singleton_class']['med']:.3f}/"
                f"{d['frac_constants_in_singleton_class']['mean']:.3f} |"
            )
    out.append("")
    out.append(
        "| corpus | regime | n edits | rank changed (mean / frac 0) | "
        "E-D key (mean / frac 0) | E-D addr (mean / frac 0) | "
        "E-D1 key (mean / frac 0) | E-D1 addr (mean / frac 0) |"
    )
    out.append("|---|---|---|---|---|---|---|---|")
    for c, blk in r["mechanism"].items():
        for reg in ("preserving", "changing"):
            m = blk[reg]

            def cell(col: str, m: dict = m) -> str:
                x = m[col]
                return "—" if x["mean"] is None else f"{x['mean']:.3f} / {x['frac_zero']:.3f}"

            out.append(
                f"| {NAME[c]} | {reg} | {m['n_edits']} | {cell('rank_changed')} "
                f"| {cell('key_changed_D')} | {cell('addr_changed_D')} "
                f"| {cell('key_changed_D1')} | {cell('addr_changed_D1')} |"
            )
    return "\n".join(out)


def n4_tables() -> str:
    r = load("n4_results.json")
    out: list[str] = []
    out.append(
        "| corpus | N | n med | m med | tokens A | B | D | D1 | secs A med/p90 | B | D | D1 |"
    )
    out.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for c, blk in r["corpora"].items():
        cm = blk["cached_m3"]
        tokA = f"{q(cm['tokens']['A'], 'med')} / {q(cm['tokens']['A'], 'p90')}"
        secA = f"{cm['secs']['A']['med']:.4g} / {cm['secs']['A']['p90']:.4g}"
        toks = " | ".join(
            f"{q(blk['tokens'][e], 'med')} / {q(blk['tokens'][e], 'p90')}" for e in ("B", "D", "D1")
        )
        secs = " | ".join(
            f"{blk['secs_full'][e]['med']:.2g} / {blk['secs_full'][e]['p90']:.2g}"
            for e in ("B", "D", "D1")
        )
        out.append(
            f"| {NAME[c]} | {blk['n']} | {q(cm['kb_size']['n'], 'med')} "
            f"| {q(cm['kb_size']['m'], 'med')} | {tokA} | {toks} | {secA} | {secs} |"
        )
    return "\n".join(out)


def main() -> None:
    print("## N0\n")
    print(json.dumps(load("n0_results.json"), indent=1)[:0] or "", end="")
    r0 = load("n0_results.json")
    print(
        "| corpus | N | iso classes (nauty) | classes E-D | classes E-D1 | iso viol D/D1 | merges D/D1 | splits D/D1 |"  # noqa: E501
    )
    print("|---|---|---|---|---|---|---|---|")
    for c, b in r0["corpora"].items():
        cd, c1 = b["completeness"]["D"], b["completeness"]["D1"]
        print(
            f"| {NAME[c]} | {b['n']} | {cd['iso_classes_nauty']} | {cd['classes_enc']} "
            f"| {c1['classes_enc']} | {b['iso_invariance']['D']['violations']}/"
            f"{b['iso_invariance']['D1']['violations']} | {cd['false_merges']}/{c1['false_merges']} "  # noqa: E501
            f"| {cd['false_splits']}/{c1['false_splits']} |"
        )
    print("\ntrace equivalence:", r0["trace_equivalence"])
    print("\n## N1\n")
    print(n1_tables())
    print("\n### N1 locality fractions\n")
    print(n1_locality())
    print("\n## N2\n")
    print(n2_tables())
    print("\n## N3\n")
    print(n3_tables())
    print("\n## N4\n")
    print(n4_tables())


if __name__ == "__main__":
    main()
