"""Render the Task A / Task B tables from the probe JSONs."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

SCRATCH = Path(
    "/tmp/claude-1000/-home-mpascual-research-code-IsalHG/"
    "b1064998-d2d4-4d37-b206-e4206ec0bb6c/scratchpad"
)
ORDER = ("wd50k_33", "wd50k_66", "wd50k_100", "jf17k", "wikipeople", "wd50k")


def load() -> dict:
    res = json.loads((SCRATCH / "probe_hyperrel_results.json").read_text())
    extra = SCRATCH / "results_wd50k_100.json"
    if extra.exists():
        res.update(json.loads(extra.read_text()))
    return res


def q(d: dict, key: str) -> str:
    x = d[key]
    f = lambda v: str(int(v)) if float(v).is_integer() else f"{v:.1f}"  # noqa: E731
    return " / ".join(f(x[k]) for k in ("min", "p25", "median", "p75", "p90", "max"))


def main() -> None:
    res = load()
    names = [n for n in ORDER if n in res]

    print("## C1 corpus")
    print(
        "| collection | statements | main rels | entities/values | with qualifier | folded labels |"
    )
    print("|---|---|---|---|---|---|")
    for n in names:
        c = res[n]["corpus"]
        print(
            f"| {n} | {c['n_statements']:,} | {c['n_main_relations']:,} | "
            f"{c['n_entities_values']:,} | {c['n_with_qualifier']:,} "
            f"({100 * c['frac_with_qualifier']:.1f} %) | {c['n_folded_edge_labels']:,} "
            f"(×{c['folded_over_main']}) |"
        )

    print("\n## C2 star KBs (entities with >= 3 statements)")
    print(
        "| collection | KBs | n min/p25/med/p75/p90/max | m (edges) | max arity | edges arity>=3 | KBs w/ hyperedge |"
    )
    print("|---|---|---|---|---|---|---|")
    for n in names:
        s = res[n]["stars"]
        print(
            f"| {n} | {s['count']:,} | {q(s, 'n')} | {q(s, 'm')} | {q(s, 'max_arity')} | "
            f"{100 * s['frac_edges_arity_ge3']:.1f} % | "
            f"{s['n_stars_with_hyperedge']:,} ({100 * s['frac_stars_with_hyperedge']:.1f} %) |"
        )

    print("\n## C3 edge-arity histogram (all star KBs)")
    for n in names:
        h = res[n]["stars"]["edge_arity_hist"]
        items = sorted((int(k), v) for k, v in h.items())
        head = ", ".join(f"{a}:{c:,}" for a, c in items[:9])
        tail = sum(c for a, c in items if a > 9)
        print(
            f"- **{n}** (total {res[n]['stars']['n_edges']:,}): {head}"
            + (f", >=10:{tail:,}" if tail else "")
        )

    print("\n## C4 envelope (n<=24 and m<=110)")
    print(
        "| collection | in-envelope | of stars | >K_MAX dropped | n med | m med | max arity med/max | edges arity>=3 | KBs w/ hyperedge |"
    )
    print("|---|---|---|---|---|---|---|---|---|")
    for n in names:
        e = res[n]["envelope"]
        print(
            f"| {n} | {e['count']:,} | {100 * e['yield_frac_of_stars']:.1f} % | {e['count_over_k_max']} | "
            f"{e['n']['median']:.0f} | {e['m']['median']:.0f} | "
            f"{e['max_arity']['median']:.0f}/{e['max_arity']['max']:.0f} | "
            f"{100 * e['frac_edges_arity_ge3']:.1f} % | "
            f"{e['n_with_hyperedge']:,} ({100 * e['frac_with_hyperedge']:.1f} %) |"
        )

    print("\n## C5 isomorphism census over in-envelope KBs (pynauty-Levi)")
    print(
        "| collection | KBs | labelled classes | singletons | top-10 share | unlabelled classes | top-10 share |"
    )
    print("|---|---|---|---|---|---|---|")
    for n in names:
        c = res[n]["census"]
        lab, unl = c["labelled"], c["unlabelled"]
        print(
            f"| {n} | {lab['n_kbs']:,} | {lab['distinct_classes']:,} "
            f"({lab['classes_per_kb']:.3f}/KB) | {lab['singletons']:,} | "
            f"{100 * lab['top10_share']:.1f} % | {unl['distinct_classes']:,} | "
            f"{100 * unl['top10_share']:.1f} % |"
        )

    print("\n## C6 labelled w*_c timing (30 s/instance, subprocess)")
    print("| collection | bucket | pool | att | OK | DNF | ERR | med s | p90 s | max s | med tok |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for n in names:
        for b, t in res[n]["timing"].items():
            print(
                f"| {n} | {b} | {t['pool']:,} | {t['attempted']} | {t['ok']} | {t['dnf']} | "
                f"{t['error']} | {t['median_s']} | {t['p90_s']} | {t['max_s']} | {t['median_tokens']} |"
            )

    tp = SCRATCH / "types_raw.json"
    if tp.exists():
        d = json.loads(tp.read_text())
        types = d["types"]
        with_t = {k: v for k, v in types.items() if v}
        cnt = Counter(t for v in with_t.values() for t in v)
        print(
            f"\n## B1 P31 coverage: {len(with_t):,}/{len(types):,} = {100 * len(with_t) / max(1, len(types)):.1f} %"
        )
        big = [t for t, c in cnt.items() if c >= 20]
        members = sum(1 for v in with_t.values() if any(t in big for t in v))
        print(f"types with >=20 entities: {len(big)}; entities carrying one: {members:,}")
        print("top-30:", json.dumps(cnt.most_common(30)))


if __name__ == "__main__":
    main()
