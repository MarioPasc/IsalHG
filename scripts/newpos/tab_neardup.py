"""LaTeX table for C8, generated from the result JSONs so that no number is hand-copied.

Columns per collection: MRR of the nearest true neighbour for pendant one-edit
neighbours (P), interior one-edit neighbours (I) and all two-edit neighbours (2).
The best value per column is bold; a dagger marks a competitor that is not
significantly below the ordered-walk word (Holm-corrected one-sided Wilcoxon,
p >= 0.05).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/NEWPOS_2026-10-13/neardup")
COLLECTIONS = (
    ("wd50k66", r"\WDK"),
    ("wd50k100", r"\WDKc"),
    ("ndc_classes", r"\NDCc"),
    ("ndc_substances", r"\NDCs"),
)
ARMS = (
    ("hpd_jsd", "HPD"),
    ("netlsd", "NetLSD"),
    ("wl_l1", "WL histogram"),
    ("bipartite_ged_assign", "bipartite GED, assignment"),
    ("bipartite_ged_path", "bipartite GED, edit path"),
    ("fact_rank", "fact list"),
    ("nauty_cert", r"\nauty{} certificate, bytes"),
    ("nauty_cert_rows", r"\nauty{} certificate, rows"),
    ("degree_seq_l1", "degree-sequence floor"),
    ("size_l1", "size floor"),
    ("isal_ow_struct", r"\textbf{\IsalHG{} $\boldsymbol{\wo}$ (ours)}"),
)
OURS = "isal_ow_struct"


def cells(r1: dict, r2: dict) -> dict[str, list[tuple[float, bool]]]:
    """Per arm: [(value, not-significantly-below-ours)] for P, I, 2."""
    out: dict[str, list[tuple[float, bool]]] = {}
    for arm, _ in ARMS:
        row = []
        for key in ("MRR_pendant", "MRR_interior"):
            v = r1["arms"][arm][key]
            p = r1["tests"][key]["p_holm"].get(arm)
            row.append((v, p is not None and p >= 0.05))
        v = r2["arms"][arm]["MRR_all"]
        p = r2["tests"]["all"]["p_holm"].get(arm)
        row.append((v, p is not None and p >= 0.05))
        out[arm] = row
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--out", type=Path, default=ROOT / "tab_neardup.tex")
    args = ap.parse_args()
    data = {}
    for c, _ in COLLECTIONS:
        r1 = json.loads((args.root / f"neardup_{c}.json").read_text())
        r2 = json.loads((args.root / f"neardup_r2_{c}.json").read_text())
        data[c] = (cells(r1, r2), r1, r2)
    best = {
        (c, j): max(data[c][0][arm][j][0] for arm, _ in ARMS)
        for c, _ in COLLECTIONS
        for j in range(3)
    }
    lines = [
        r"\begin{table*}[!t]",
        r"\centering",
        r"\caption{Near-neighbour retrieval of structural near-duplicates: mean reciprocal rank of a"
        r" record's nearest true neighbour, among all non-isomorphic members, under each"
        r" representation's distance. P: neighbours one pendant edit away; I: one interior edit"
        r" away; 2: two edits away. Ground truth by exhaustive enumeration of single-fact edits,"
        r" keyed by the \nauty{} certificate. Bold: best per column; $^{\dagger}$: not"
        r" significantly below $\wo$ (one-sided paired Wilcoxon over queries, Holm-corrected,"
        r" $p \ge 0.05$).}",
        r"\label{tab:neardup}",
        r"\scriptsize",
        r"\setlength{\tabcolsep}{3pt}",
        r"\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}l" + "ccc" * len(COLLECTIONS) + "@{}}",
        r"\toprule",
        " & "
        + " & ".join(rf"\multicolumn{{3}}{{c}}{{{name}}}" for _, name in COLLECTIONS)
        + r" \\",
        "".join(rf"\cmidrule(lr){{{2 + 3 * i}-{4 + 3 * i}}}" for i in range(len(COLLECTIONS))),
        "Representation & " + " & ".join(["P & I & 2"] * len(COLLECTIONS)) + r" \\",
    ]
    counts = []
    for c, _ in COLLECTIONS:
        r1, r2 = data[c][1], data[c][2]
        counts.append(
            f"{r1['tests']['MRR_pendant']['n_queries']:,} & {r1['tests']['MRR_interior']['n_queries']:,} & {r2['queries']:,}"
        )
    lines.append(r"\emph{queries} & " + " & ".join(counts).replace(",", "{,}") + r" \\")
    lines.append(r"\midrule")
    for arm, name in ARMS:
        if arm == OURS:
            lines.append(r"\midrule")
        vals = []
        for c, _ in COLLECTIONS:
            for j, (v, ns) in enumerate(data[c][0][arm]):
                s = f"{v:.3f}"
                if abs(v - best[(c, j)]) < 5e-4:
                    s = rf"\textbf{{{s}}}"
                if ns and arm != OURS:
                    s += r"$^{\dagger}$"
                vals.append(s)
        lines.append(f"{name} & " + " & ".join(vals) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular*}", r"\end{table*}"]
    args.out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
