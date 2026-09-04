"""Why E-C moves: how far does a single-fact edit propagate through WL colours?

E-C addresses a constant by its depth-``h`` hypergraph-WL colour. The arm is
worth what that colour is *local*. This measures the fraction of constants whose
colour changes under one edit, at ``h = 1, 2, 3``, on the same corpora and the
same edit sampler as M1 -- and, as the E-B reference, the fraction of constants
whose nauty canonical rank changes.
"""

from __future__ import annotations

import json
import random
import statistics as st
from pathlib import Path

from f4_corpora import EDIT_KINDS, gen_synthetic, load_ndc, load_wd50k66, sample_edits
from f4_encodings import canonical_ranks

from isalhg.core.hypergraph_wl import wl_hash

HERE = Path(__file__).resolve().parent
SEED_CORPUS = 20260904
SEED_EDITS = 20260907
N_BASE = 100
EDITS_PER_KIND = 4
DEPTHS = (1, 2, 3, 64)


def colour_multiset_shift(before: list[int], after: list[int]) -> float:
    """Fraction of colours in ``before`` that have no counterpart in ``after``.

    Constants are not identified across an edit (ids may be renumbered), so the
    comparison is on the colour multiset: a colour surviving the edit means a
    constant whose address is unchanged.
    """
    if not before:
        return 0.0
    rem = list(after)
    kept = 0
    for c in before:
        if c in rem:
            rem.remove(c)
            kept += 1
    return 1.0 - kept / len(before)


def main() -> None:
    r = random.Random(SEED_CORPUS)
    ndc, _ = load_ndc()
    wd = load_wd50k66()
    corpora = {
        "synthetic": gen_synthetic(2000, SEED_CORPUS)[:N_BASE],
        "ndc_classes_quarter": r.sample(ndc, N_BASE),
        "wd50k66": r.sample(wd, N_BASE),
    }
    rng = random.Random(SEED_EDITS)
    out: dict[str, dict] = {}
    for name, kbs in corpora.items():
        acc: dict[str, list[float]] = {f"wl_h{d}": [] for d in DEPTHS}
        acc["nauty_rank"] = []
        for kb in kbs:
            H = kb.to_hypergraph()
            base_wl = {d: sorted(wl_hash(H, max_rounds=d)) for d in DEPTHS}
            base_rank = canonical_ranks(H)
            base_order = [v for v, _ in sorted(enumerate(base_rank), key=lambda p: p[1])]
            for kind in EDIT_KINDS:
                for ed in sample_edits(kb, kind, EDITS_PER_KIND, rng):
                    E = ed.to_hypergraph()
                    for d in DEPTHS:
                        acc[f"wl_h{d}"].append(
                            colour_multiset_shift(base_wl[d], sorted(wl_hash(E, max_rounds=d)))
                        )
                    er = canonical_ranks(E)
                    eo = [v for v, _ in sorted(enumerate(er), key=lambda p: p[1])]
                    n = min(len(base_order), len(eo))
                    same = sum(
                        1
                        for i in range(n)
                        if base_order[i] < kb.n
                        and eo[i] < ed.n
                        and kb.types[base_order[i]] == ed.types[eo[i]]
                    )
                    acc["nauty_rank"].append(1.0 - same / max(1, len(base_order)))
        out[name] = {
            "n_base": len(kbs),
            "n_edits": len(acc["wl_h3"]),
            "mean_fraction_moved": {k: round(st.fmean(v), 4) for k, v in acc.items() if v},
            "median_fraction_moved": {k: round(st.median(v), 4) for k, v in acc.items() if v},
            "frac_edits_with_zero_shift": {
                k: round(sum(1 for x in v if x == 0.0) / len(v), 4) for k, v in acc.items() if v
            },
        }
        print(name, json.dumps(out[name], indent=1), flush=True)
    (HERE / "wl_locality_results.json").write_text(json.dumps(out, indent=1))
    print("wrote wl_locality_results.json")


if __name__ == "__main__":
    main()
