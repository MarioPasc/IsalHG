"""Tabulate the C8 orientation audit: published vs as-run vs symmetric-min bipartite arms.

Reads the published C8 JSONs (read-only), the ``asrun`` and ``symmin`` reruns
written by ``c8_orientation_audit.py`` and its ``build.json``; writes
``audit.json`` and ``AUDIT.md`` in the audit directory.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

C8_DIR = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/NEWPOS_2026-10-13/neardup")
OUT = Path(
    "/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/KNN_2026-10-15/c8_orientation_audit"
)
COLLECTIONS = ("wd50k66", "wd50k100", "ndc_classes", "ndc_substances")
OURS = "isal_ow_struct"
PATH = "bipartite_ged_path"
ASSIGN = "bipartite_ged_assign"
SKIP = {OURS, "wstar_orbit"}

# (label, file kind, metric key, test key)
CELLS = (
    ("r1 pendant MRR", "r1", "MRR_pendant", "MRR_pendant"),
    ("r1 pendant hit@1", "r1", "hit1_pendant", None),
    ("r1 pooled MRR", "r1", "MRR", "MRR"),
    ("r1 interior MRR", "r1", "MRR_interior", "MRR_interior"),
    ("r2 all MRR", "r2", "MRR_all", "all"),
    ("r2 pendant MRR", "r2", "MRR_pendant", "pendant"),
)


def _load(base: Path, kind: str, collection: str) -> dict[str, Any] | None:
    name = f"neardup_{collection}.json" if kind == "r1" else f"neardup_r2_{collection}.json"
    p = base / name
    return json.loads(p.read_text()) if p.exists() else None


def _best(d: dict[str, Any], key: str) -> tuple[str, float]:
    scored = [(a, float(r[key])) for a, r in d["arms"].items() if a not in SKIP and key in r]
    return max(scored, key=lambda kv: kv[1])


def _p(d: dict[str, Any], test: str | None, arm: str) -> float | None:
    if test is None:
        return None
    t = d.get("tests", {}).get(test, {})
    return t.get("p_holm", {}).get(arm)


def main() -> None:
    build = json.loads((OUT / "build.json").read_text())
    rows: list[dict[str, Any]] = []
    for c in COLLECTIONS:
        for label, kind, key, test in CELLS:
            pub = _load(C8_DIR, kind, c)
            asr = _load(OUT / "asrun", kind, c)
            sym = _load(OUT / "symmin", kind, c)
            if pub is None or asr is None or sym is None:
                continue
            best_pub = _best(pub, key)
            best_sym = _best(sym, key)
            word = float(pub["arms"][OURS][key])
            rows.append(
                {
                    "collection": c,
                    "cell": label,
                    "word_published": word,
                    "word_asrun": float(asr["arms"][OURS][key]),
                    "best_published": best_pub,
                    "path_published": float(pub["arms"][PATH][key]),
                    "path_asrun": float(asr["arms"][PATH][key]),
                    "path_symmin": float(sym["arms"][PATH][key]),
                    "assign_published": float(pub["arms"][ASSIGN][key]),
                    "assign_symmin": float(sym["arms"][ASSIGN][key]),
                    "best_symmin": best_sym,
                    "word_first_symmin": word > best_sym[1],
                    "p_holm_word_vs_path_symmin": _p(sym, test, PATH),
                    "p_holm_max_symmin": max(
                        (v for v in sym.get("tests", {}).get(test, {}).get("p_holm", {}).values()),
                        default=None,
                    )
                    if test
                    else None,
                    "reproduces_published": abs(float(asr["arms"][OURS][key]) - word) < 1e-12
                    and abs(float(asr["arms"][PATH][key]) - float(pub["arms"][PATH][key])) < 1e-12,
                }
            )
    claim = {}
    for c in COLLECTIONS:
        for label in ("r1 pendant MRR", "r2 pendant MRR"):
            row = next((x for x in rows if x["collection"] == c and x["cell"] == label), None)
            if row is None:
                continue
            claim[f"{c} {label}"] = bool(
                row["word_first_symmin"]
                and row["p_holm_max_symmin"] is not None
                and row["p_holm_max_symmin"] < 0.05
            )
    payload = {"rows": rows, "pendant_claim_holds": claim, "build": build}
    (OUT / "audit.json").write_text(json.dumps(payload, indent=1))
    lines = [
        "# C8 orientation audit — bipartite GED, as published vs symmetric-min",
        "",
        "C8's matrices hold `pairwise(H_i, H_j)` for `i < j` only, mirrored, so the score of a",
        "(query, candidate) pair depends on which of the two has the lower member index. The",
        "`symmin` rerun replaces both bipartite arms by `min(d(a,b), d(b,a))` and changes nothing",
        "else (same `neardup.py` / `neardup_r2.py`, same truth, bootstrap seed 0).",
        "",
        "## Asymmetry of the bipartite arms (ordered matrices)",
        "",
        "| collection | arm | asymmetric pairs | share | mean gap | as-run vs cached max diff |",
        "|---|---|---|---|---|---|",
    ]
    for c in COLLECTIONS:
        for arm in (PATH, ASSIGN):
            a = build.get(c, {}).get("arms", {}).get(arm)
            if not a:
                continue
            chk = a["max_abs_diff_asrun_vs_cached"]
            lines.append(
                f"| {c} | {arm} | {a['asymmetric_pairs']:,} | {a['asymmetric_share']:.3f} | "
                f"{a['mean_abs_orientation_gap']:.3f} | "
                f"{'n/a (built locally)' if chk is None else f'{chk:.2g}'} |"
            )
    lines += [
        "",
        "## Headline cells",
        "",
        "| collection | cell | word | best published competitor | edit path as published | "
        "edit path sym-min | assign sym-min | best competitor sym-min | word first | p_Holm word > "
        "path (sym-min) | rerun reproduces |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for x in rows:
        p = x["p_holm_word_vs_path_symmin"]
        lines.append(
            f"| {x['collection']} | {x['cell']} | {x['word_published']:.3f} | "
            f"{x['best_published'][0]} {x['best_published'][1]:.3f} | {x['path_published']:.3f} | "
            f"{x['path_symmin']:.3f} | {x['assign_symmin']:.3f} | {x['best_symmin'][0]} "
            f"{x['best_symmin'][1]:.3f} | {'yes' if x['word_first_symmin'] else '**no**'} | "
            f"{'–' if p is None else f'{p:.1e}'} | {'yes' if x['reproduces_published'] else 'NO'} |"
        )
    lines += ["", "## The Holm-corrected pendant claim under sym-min", ""]
    for k, v in claim.items():
        lines.append(f"- {k}: {'holds' if v else '**fails**'}")
    pend = [x for x in rows if x["cell"] in ("r1 pendant MRR", "r2 pendant MRR")]
    worst = max(pend, key=lambda x: x["p_holm_max_symmin"] or 0.0)
    pooled = [x for x in rows if x["cell"] == "r1 pooled MRR" and not x["word_first_symmin"]]
    lines += [
        "",
        "## Sentences of the C8 write-up the audit touches",
        "",
        f"- Largest Holm-corrected p of the word against any competitor on a pendant stratum "
        f"(radius 1 and 2): {worst['p_holm_max_symmin']:.1e} ({worst['collection']}, "
        f"{worst['cell']}); a bound stated as 'p < 1e-32' must be checked against it.",
    ]
    for x in pooled:
        lines.append(
            f"- Pooled radius-1 MRR, {x['collection']}: the sym-min edit path "
            f"({x['path_symmin']:.3f}) is numerically above the word ({x['word_published']:.3f}), "
            f"p_Holm(word > path) = {x['p_holm_word_vs_path_symmin']:.2f}; a sentence saying the "
            "word has the top pooled MRR on all four collections no longer holds there."
        )
    lines.append("")
    (OUT / "AUDIT.md").write_text("\n".join(lines) + "\n")
    print((OUT / "AUDIT.md").read_text())


if __name__ == "__main__":
    main()
