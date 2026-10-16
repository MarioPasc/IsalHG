"""Every number Section S5 prints, from the full-run summary: knn_facts.tex and SECTION_FACTS.md.

Reads ``<root>/full_summary.json`` (and the figures' ``*.numbers.json`` under
``<root>/section``) and writes:

- ``<root>/section/knn_facts.tex``: one ``\\knnfact{name}{value}`` per name
  of the supplement's contract (``supplementary/figures/knn/README.md``), each
  preceded by a ``% src:`` line with the JSON path, the key and the unrounded
  value; the 72 verdict cells ``V-<row>-<collection>[-r<r>]`` as
  ``\\KNNsurv`` / ``\\KNNkill`` / ``\\KNNinf``.
- ``<root>/SECTION_FACTS.md``: the same facts as a table, with the rule used.

Bound rule. A range ``a to b`` states bounds on a set of values, so its lower
end rounds down and its upper end rounds up (three decimals for accuracies,
ARI, reciprocal ranks and shares; two for certified ratios). A maximum stated
as an upper bound rounds up. Every other value uses ordinary rounding (half up)
at three decimals; shares stated in percent round to whole percent.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import knn_lib as K  # noqa: E402, N812

COLL_TEX = {
    "wd50k66": r"\WDK{}",
    "wd50k100": r"\WDKc{}",
    "ndc_classes": r"\NDCc{}",
    "ndc_substances": r"\NDCs{}",
}
COLL_KEY = {"wd50k66": "wd66", "wd50k100": "wd100", "ndc_classes": "ndcc", "ndc_substances": "ndcs"}
ARM_TEX = {
    "isal_ow_struct": "the word",
    "bipartite_ged_path_sym": "the symmetric bipartite edit path",
    "bipartite_ged_path": "the bipartite edit path in its cached orientation",
    "bipartite_ged_assign": "the bipartite assignment value",
    "wl_h1": "one-round WL",
    "wl_l1": "the WL histogram",
    "nauty_cert_rows": r"the \nauty{} certificate rows",
    "nauty_cert": r"the \nauty{} certificate bytes",
    "fact_rank": "the fact list",
    "netlsd": "NetLSD",
    "hpd_jsd": "HPD",
    "degree_seq_l1": "the degree-sequence floor",
    "size_l1": "the size floor",
}
EDIT_ARMS = ("bipartite_ged_assign", "bipartite_ged_path_sym")
EXACT_ARMS = ("nauty_cert", "nauty_cert_rows", "fact_rank")
#: Verdict rows of the supplement's table: row key -> (cell id pattern, r values or None).
VERDICT_ROWS: dict[str, tuple[str, tuple[int, ...] | None, tuple[str, ...]]] = {
    "A": ("A/lineage/{col}", None, ("ndc_classes", "ndc_substances")),
    "B": ("B/pendant/{col}/r{r}", (1, 2, 3), tuple(COLL_KEY)),
    "Bmix": ("B/mix/{col}/r{r}", (1, 2, 3), ("wd50k66", "wd50k100")),
    "C": ("C/C-all/c3/{col}/r{r}", (1, 2, 3), tuple(COLL_KEY)),
    "Cint": ("C/C-int/c3/{col}/r{r}", (1, 2, 3), tuple(COLL_KEY)),
    "C6": ("C/C-all/c6/{col}/r{r}", (1, 2, 3), tuple(COLL_KEY)),
    "D": ("D/pendant/{col}/r{r}", (1, 2, 3), tuple(COLL_KEY)),
    "Dmix": ("D/empirical/{col}/r{r}", (1, 2), ("wd50k66", "wd50k100")),
}
TABLE_HYPOTHESES = (
    "H-KNN-A",
    "H-KNN-B",
    "H-KNN-mix",
    "H-KNN-C",
    "H-KNN-C-int",
    "H-KNN-C@c6",
    "H-KNN-D",
    "H-KNN-D-mix",
)


class FactError(Exception):
    """A fact cannot be computed from the summary."""


def _q(x: float, nd: int, mode: str) -> str:
    return str(Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-nd), rounding=mode))


def rnd(x: float, nd: int = 3) -> str:
    """Ordinary (half-up) rounding."""
    return _q(x, nd, ROUND_HALF_UP)


def down(x: float, nd: int = 3) -> str:
    """Lower bound: round down."""
    return _q(x, nd, ROUND_FLOOR)


def up(x: float, nd: int = 3) -> str:
    """Upper bound: round up."""
    return _q(x, nd, ROUND_CEILING)


@dataclass
class Fact:
    """One named number of the section."""

    name: str
    tex: str
    src: str
    raw: str
    rule: str


@dataclass
class FactBook:
    """The facts, in the order the section introduces them."""

    summary: dict[str, Any]
    facts: list[Fact] = field(default_factory=list)

    def add(self, name: str, tex: str, src: str, raw: Any, rule: str) -> None:  # noqa: ANN401
        if any(f.name == name for f in self.facts):
            raise FactError(f"fact {name} defined twice")
        src = src.replace("{col}", "*").replace("{r}", "*")
        self.facts.append(Fact(name, tex, src, str(raw), rule))

    # -- cell access ------------------------------------------------------------------------

    def cells(self, pattern: str, cols: Iterable[str], rs: Iterable[int] | None) -> list[dict]:
        out = []
        for col in cols:
            for r in rs if rs is not None else (None,):
                cid = pattern.format(col=col, r=r)
                if cid in self.summary["cells"]:
                    out.append(self.summary["cells"][cid])
        return out

    def evaluated(self, cells: list[dict]) -> list[dict]:
        """Cells that carry a verdict (feasible, with data)."""
        return [c for c in cells if c["verdict"] not in ("infeasible", "no data")]

    # -- fact builders ----------------------------------------------------------------------

    def range_fact(
        self,
        name: str,
        cells: list[dict],
        get: Callable[[dict], float],
        path: str,
        nd: int = 3,
    ) -> None:
        if not cells:
            raise FactError(f"{name}: no cells")
        vals = [(get(c), c["id"]) for c in cells]
        lo, hi = min(vals), max(vals)
        self.add(
            name,
            f"${down(lo[0], nd)}$ to ${up(hi[0], nd)}$",
            f"full_summary.json {path} over {len(cells)} cells",
            f"min {lo[0]!r} at {lo[1]}; max {hi[0]!r} at {hi[1]}",
            "range: lower end down, upper end up",
        )

    def value_fact(self, name: str, value: float, path: str, nd: int = 3) -> None:
        self.add(name, f"${rnd(value, nd)}$", f"full_summary.json {path}", repr(value), "ordinary")

    def count_fact(self, name: str, n: int, src: str, detail: str) -> None:
        self.add(name, f"${n}$", src, detail, "count")


def _word(m: str) -> Callable[[dict], float]:
    return lambda c: c["per_arm"][K.OURS][m]["mean"]


def _best(m: str) -> Callable[[dict], float]:
    return lambda c: c["best_competitor"][m]["mean"]


def _arm(arm: str, m: str) -> Callable[[dict], float]:
    return lambda c: c["per_arm"][arm][m]["mean"]


def _best_rr(c: dict) -> tuple[str, float]:
    comps = {a: c["per_arm"][a]["rr"]["mean"] for a in c["competitors"] if "rr" in c["per_arm"][a]}
    a = max(comps, key=lambda k: comps[k])
    return a, comps[a]


def _all(row: str) -> tuple[str, tuple[int, ...] | None, tuple[str, ...]]:
    return VERDICT_ROWS[row]


# --------------------------------------------------------------------------- the facts


def verdict_facts(fb: FactBook) -> None:
    """The verdict counts and the 72 verdict cells."""
    s = fb.summary
    hyp = s["hypotheses"]
    incomplete = [h for h, v in hyp.items() if v["verdict"] == "incomplete"]
    if incomplete:
        raise FactError(f"hypotheses with missing registered cells: {incomplete}")
    a = hyp["H-KNN-A"]
    fb.add(
        "A-verdict",
        {"killed": "killed", "survives": "not killed"}[a["verdict"]],
        'full_summary.json hypotheses["H-KNN-A"].verdict',
        f"{a['verdict']}; kills {[k['cell'] for k in a['kills']]}",
        "verdict",
    )
    for name, row in (("B", "B"), ("C", "C"), ("Cint", "Cint")):
        pat, rs, cols = _all(row)
        ev = fb.evaluated(fb.cells(pat, cols, rs))
        kills = [c["id"] for c in ev if c["verdict"] == "kill"]
        fb.count_fact(
            f"{name}-killed-cells",
            len(kills),
            f'full_summary.json cells["{pat}"].verdict',
            f"{len(kills)} kill of {len(ev)} evaluated: {kills}",
        )
        if name != "B":
            fb.count_fact(
                f"{name}-feasible-cells",
                len(ev),
                f'full_summary.json cells["{pat}"].feasible',
                f"{len(ev)} feasible: {[c['id'] for c in ev]}",
            )
    pat, _, cols = _all("D")
    d_claim = fb.evaluated(fb.cells(pat, cols, (1, 2)))
    d_kills = [c["id"] for c in d_claim if c["verdict"] == "kill"]
    fb.count_fact(
        "D-killed-cells",
        len(d_kills),
        f'full_summary.json cells["{pat}"].verdict (r <= 2)',
        f"{len(d_kills)} of {len(d_claim)}: {d_kills}",
    )
    claim = [
        c
        for c in s["cells"].values()
        if c["hypothesis"] in TABLE_HYPOTHESES
        and c["claim"]
        and c["verdict"] in ("word ahead", "kill")
    ]
    leads = [c["id"] for c in claim if c["best_arm_overall"]["acc1"]["arm"] in EDIT_ARMS]
    fb.count_fact(
        "claim-cells",
        len(claim),
        "full_summary.json cells[*] with claim and a verdict, hypotheses of the verdict table",
        f"{len(claim)} cells",
    )
    fb.count_fact(
        "edit-arm-leads-cells",
        len(leads),
        "full_summary.json cells[*].best_arm_overall.acc1.arm in {bipartite_ged_assign, "
        "bipartite_ged_path_sym}",
        f"{len(leads)} of {len(claim)}: {leads}",
    )
    for row, (pat, rs, cols) in VERDICT_ROWS.items():
        for col in cols:
            for r in rs if rs is not None else (None,):
                cid = pat.format(col=col, r=r)
                name = f"V-{row}-{COLL_KEY[col]}" + (f"-r{r}" if r is not None else "")
                c = s["cells"].get(cid)
                if c is None and row.startswith("C"):
                    stem = cid.rsplit("/", 1)[0]
                    c = s["cells"].get(f"{stem}/none")
                if c is None:
                    raise FactError(f"{name}: no cell {cid}")
                v = c["verdict"]
                tex = {
                    "word ahead": r"\KNNsurv",
                    "word ahead (no claim)": r"\KNNsurv",
                    "kill": r"\KNNkill",
                    "competitor ahead (no claim)": r"\KNNkill",
                    "infeasible": r"\KNNinf",
                }.get(v)
                if tex is None:
                    raise FactError(f"{name}: verdict {v!r}")
                fb.add(name, tex, f'full_summary.json cells["{c["id"]}"].verdict', v, "verdict")


def tsne_facts(fb: FactBook, section: Path) -> None:
    """The t-SNE caption, from the figure's own record."""
    meta_path = section / "fig_s5_tsne.numbers.json"
    meta = json.loads(meta_path.read_text())
    arms = meta["panel_arms"][1:]
    names = [ARM_TEX[a] for a in arms]
    fb.add(
        "tsne-competitors",
        ", ".join(names[:-1]) + " and " + names[-1],
        f"{meta_path.name} panel_arms",
        arms,
        "text",
    )
    b_cell, d_cell = meta["row_b"]["cell"], meta["row_d"]["cell"]
    col = b_cell.split("/")[2]
    fb.count_fact(
        "tsne-B-sources", len(meta["row_b"]["sources"]), f"{meta_path.name} row_b.sources", b_cell
    )
    fb.add("tsne-B-collection", COLL_TEX[col], f"{meta_path.name} row_b.cell", b_cell, "text")
    fb.count_fact("tsne-B-r", int(b_cell.rsplit("r", 1)[1]), f"{meta_path.name} row_b.cell", b_cell)
    fb.count_fact(
        "tsne-D-sources", len(meta["row_d"]["sources"]), f"{meta_path.name} row_d.sources", d_cell
    )


def design_b_facts(fb: FactBook) -> None:
    pat, rs, cols = _all("B")
    cells = fb.cells(pat, cols, rs)
    p = f'cells["{pat}"]'
    fb.range_fact("B-acc-word-range", cells, _word("acc1"), f"{p}.per_arm.isal_ow_struct.acc1.mean")
    fb.range_fact("B-acc-best-range", cells, _best("acc1"), f"{p}.best_competitor.acc1.mean")
    arms = Counter(c["best_competitor"]["acc1"]["arm"] for c in cells)
    arm, n = arms.most_common(1)[0]
    fb.add(
        "B-best-arm",
        ARM_TEX[arm],
        f"full_summary.json {p}.best_competitor.acc1.arm",
        dict(arms),
        "mode",
    )
    fb.count_fact(
        "B-best-arm-cells", n, f"full_summary.json {p}.best_competitor.acc1.arm", dict(arms)
    )
    fb.range_fact("B-ari-word-range", cells, _word("ari"), f"{p}.per_arm.isal_ow_struct.ari.mean")
    fb.range_fact("B-ari-best-range", cells, _best("ari"), f"{p}.best_competitor.ari.mean")
    beats = [
        c["id"]
        for c in cells
        if all(
            c["per_arm"][K.OURS][m]["mean"] > max(c["per_arm"][a][m]["mean"] for a in EXACT_ARMS)
            for m in ("acc1", "ari")
        )
    ]
    fb.count_fact(
        "B-word-beats-exact-cells",
        len(beats),
        f"full_summary.json {p}.per_arm.{{isal_ow_struct,nauty_cert,nauty_cert_rows,fact_rank}}"
        ".{acc1,ari}.mean",
        f"word above all three on both metrics in {beats}",
    )
    fb.range_fact(
        "B-ceiling-range",
        cells,
        lambda c: sum(c["diag"]["exact_ceiling"]) / len(c["diag"]["exact_ceiling"]),
        f"{p}.diag.exact_ceiling (mean over seeds)",
    )
    pat, rs, cols = _all("Bmix")
    mix = fb.cells(pat, cols, rs)
    p = f'cells["{pat}"]'
    fb.range_fact(
        "Bmix-acc-word-range", mix, _word("acc1"), f"{p}.per_arm.isal_ow_struct.acc1.mean"
    )
    fb.range_fact("Bmix-acc-best-range", mix, _best("acc1"), f"{p}.best_competitor.acc1.mean")


def design_a_facts(fb: FactBook) -> None:
    for col, key in (("ndc_classes", "ndcc"), ("ndc_substances", "ndcs")):
        cid = f"A/lineage/{col}"
        c = fb.summary["cells"][cid]
        p = f'cells["{cid}"]'
        fb.value_fact(
            f"A-{key}-acc-word", _word("acc1")(c), f"{p}.per_arm.isal_ow_struct.acc1.mean"
        )
        fb.value_fact(f"A-{key}-ari-word", _word("ari")(c), f"{p}.per_arm.isal_ow_struct.ari.mean")
        fb.value_fact(
            f"A-{key}-acc-best",
            _best("acc1")(c),
            f"{p}.best_competitor.acc1.mean ({c['best_competitor']['acc1']['arm']})",
        )
        fb.value_fact(
            f"A-{key}-ari-best",
            _best("ari")(c),
            f"{p}.best_competitor.ari.mean ({c['best_competitor']['ari']['arm']})",
        )
    for name, key, label in (
        ("A-shared-iso", "cross_class_iso", "diag.cross_class_iso"),
        ("A-ceiling", "exact_ceiling", "diag.exact_ceiling"),
    ):
        parts, raws = [], []
        for col in ("ndc_classes", "ndc_substances"):
            vals = fb.summary["cells"][f"A/lineage/{col}"]["diag"][key]
            v = sum(vals) / len(vals)
            parts.append(f"${rnd(v)}$ ({COLL_TEX[col].removesuffix('{}')})")
            raws.append(f"{col} {v!r}")
        fb.add(
            name,
            " and ".join(parts),
            f'full_summary.json cells["A/lineage/*"].{label} (mean over seeds)',
            "; ".join(raws),
            "ordinary",
        )


def design_c_facts(fb: FactBook) -> None:
    pat, rs, cols = _all("C")
    all_c = fb.cells(pat, cols, rs)
    sizes = [s for c in all_c for s in c["diag"].get("S", [])]
    fb.add(
        "C-sources-range",
        f"${min(sizes)}$ to ${max(sizes)}$",
        f'full_summary.json cells["{pat}"].diag.S (every seed, every collection)',
        f"min {min(sizes)}, max {max(sizes)}",
        "range of integers",
    )
    ev = fb.evaluated(all_c)
    p = f'cells["{pat}"]'
    fb.range_fact(
        "C-acc-word-range", ev, _word("acc1"), f"{p}.per_arm.isal_ow_struct.acc1.mean (feasible)"
    )
    fb.range_fact(
        "C-acc-best-range", ev, _best("acc1"), f"{p}.best_competitor.acc1.mean (feasible)"
    )
    pat, rs, cols = _all("Cint")
    ev = fb.evaluated(fb.cells(pat, cols, rs))
    p = f'cells["{pat}"]'
    fb.range_fact(
        "Cint-acc-word-range", ev, _word("acc1"), f"{p}.per_arm.isal_ow_struct.acc1.mean (feasible)"
    )
    fb.range_fact(
        "Cint-acc-best-range", ev, _best("acc1"), f"{p}.best_competitor.acc1.mean (feasible)"
    )
    pend = fb.evaluated(fb.cells("C/C-pend/c3/{col}/r{r}", COLL_KEY, (1, 2, 3)))
    arms = Counter(c["best_arm_overall"]["acc1"]["arm"] for c in pend)
    arm, n = arms.most_common(1)[0]
    src = 'full_summary.json cells["C/C-pend/c3/{col}/r{r}"].best_arm_overall.acc1.arm (feasible)'
    fb.add("Cpend-best-arm", ARM_TEX[arm], src, dict(arms), "mode")
    fb.count_fact("Cpend-best-cells", n, src, dict(arms))
    fb.count_fact("Cpend-feasible-cells", len(pend), src, [c["id"] for c in pend])
    pat, rs, cols = _all("C6")
    ev = fb.evaluated(fb.cells(pat, cols, rs))
    p = f'cells["{pat}"]'
    fb.count_fact(
        "C6-feasible-cells", len(ev), f"full_summary.json {p}.feasible", [c["id"] for c in ev]
    )
    if ev:
        fb.range_fact(
            "C6-acc-word-range", ev, _word("acc1"), f"{p}.per_arm.isal_ow_struct.acc1.mean"
        )
        fb.range_fact("C6-acc-best-range", ev, _best("acc1"), f"{p}.best_competitor.acc1.mean")


def design_d_facts(fb: FactBook) -> None:
    pat, _, cols = _all("D")
    claim = fb.cells(pat, cols, (1, 2))
    p = f'cells["{pat}"] (r <= 2)'
    fb.range_fact("D-acc-word-range", claim, _word("acc1"), f"{p}.per_arm.isal_ow_struct.acc1.mean")
    fb.range_fact("D-acc-best-range", claim, _best("acc1"), f"{p}.best_competitor.acc1.mean")
    kills = [c for c in claim if c["verdict"] == "kill"]
    if kills:
        dec = max(kills, key=lambda c: _best("acc1")(c) - _word("acc1")(c))
        rule = "the killed claim cell with the largest best-minus-word gap"
    else:
        dec = min(claim, key=lambda c: _word("acc1")(c) - _best("acc1")(c))
        rule = "no kill: the claim cell with the smallest word-minus-best gap"
    cid = dec["id"]
    fb.add(
        "D-deciding-cell",
        f"{COLL_TEX[dec['collection']]} at $r={dec['r']}$",
        f'full_summary.json cells["{cid}"]',
        rule,
        "selection",
    )
    fb.value_fact(
        "D-deciding-word", _word("acc1")(dec), f'cells["{cid}"].per_arm.isal_ow_struct.acc1.mean'
    )
    arm = dec["best_competitor"]["acc1"]["arm"]
    fb.add(
        "D-deciding-arm",
        ARM_TEX[arm],
        f'full_summary.json cells["{cid}"].best_competitor.acc1.arm',
        arm,
        "text",
    )
    fb.value_fact(
        "D-deciding-best", _best("acc1")(dec), f'cells["{cid}"].best_competitor.acc1.mean'
    )
    r3 = fb.cells(pat, cols, (3,))
    p3 = f'cells["{pat}"] (r = 3)'
    fb.range_fact(
        "D-r3-acc-word-range", r3, _word("acc1"), f"{p3}.per_arm.isal_ow_struct.acc1.mean"
    )
    fb.range_fact("D-r3-acc-best-range", r3, _best("acc1"), f"{p3}.best_competitor.acc1.mean")
    fb.range_fact("D-mrr-word-range", claim, _word("rr"), f"{p}.per_arm.isal_ow_struct.rr.mean")
    fb.range_fact(
        "D-mrr-best-range",
        claim,
        lambda c: _best_rr(c)[1],
        f"{p}.per_arm.<best verdict competitor by rr>.rr.mean",
    )
    pat_m, _, cols_m = _all("Dmix")
    mix = fb.cells(pat_m, cols_m, (1, 2))
    pm = f'cells["{pat_m}"] (r <= 2)'
    fb.range_fact(
        "Dmix-acc-word-range", mix, _word("acc1"), f"{pm}.per_arm.isal_ow_struct.acc1.mean"
    )
    fb.range_fact("Dmix-acc-best-range", mix, _best("acc1"), f"{pm}.best_competitor.acc1.mean")
    fb.range_fact(
        "D-asrun-range",
        claim,
        _arm(K.PATH_ASRUN, "acc1"),
        f"{p}.per_arm.bipartite_ged_path.acc1.mean",
    )
    fb.range_fact(
        "D-symmin-range",
        claim,
        _arm(K.PATH_SYM, "acc1"),
        f"{p}.per_arm.bipartite_ged_path_sym.acc1.mean",
    )


def certified_facts(fb: FactBook) -> None:
    clustered = [c for c in fb.summary["cells"].values() if K.OURS in c.get("certified", {})]
    meds = [
        (m, c["id"]) for c in clustered for m in c["certified"][K.OURS]["ratio_median_per_seed"]
    ]
    lo, hi = min(meds), max(meds)
    src = "full_summary.json cells[*].certified.isal_ow_struct"
    fb.add(
        "ratio-median-range",
        f"${down(lo[0], 2)}$ to ${up(hi[0], 2)}$",
        f"{src}.ratio_median_per_seed over {len(clustered)} clustered cells",
        f"min {lo[0]!r} at {lo[1]}; max {hi[0]!r} at {hi[1]}",
        "range: lower end down, upper end up (2 decimals)",
    )
    mx = max((c["certified"][K.OURS]["ratio_max"], c["id"]) for c in clustered)
    fb.add(
        "ratio-max",
        f"${up(mx[0], 2)}$",
        f"{src}.ratio_max",
        f"{mx[0]!r} at {mx[1]}",
        "upper bound: up",
    )
    over = sum(c["certified"][K.OURS]["n_over_bound"] for c in clustered)
    total = sum(c["certified"][K.OURS]["n_certified"] for c in clustered)
    fb.count_fact("ratio-exceed", over, f"{src}.n_over_bound (sum)", over)
    fb.add(
        "ratio-clusters",
        f"${total:,}$".replace(",", "{,}"),
        f"{src}.n_certified (sum)",
        total,
        "count",
    )
    any_arm = sum(v["n_over_bound"] for c in clustered for v in c["certified"].values())
    fb.count_fact(
        "ratio-exceed-any-arm",
        any_arm,
        "full_summary.json cells[*].certified.<every arm>.n_over_bound (sum; extra fact)",
        any_arm,
    )


def _share_fact(fb: FactBook, name: str, cid: str, arm: str, key: str) -> None:
    v = fb.summary["cells"][cid]["mechanism"][arm][key]["mean"]
    fb.add(
        name,
        rf"${rnd(100 * v, 0)}$\,\%",
        f'full_summary.json cells["{cid}"].mechanism.{arm}.{key}.mean',
        repr(v),
        "percent, ordinary",
    )


def mechanism_facts(fb: FactBook, section: Path) -> None:
    """Both rows of the mechanism figure, and the shares over the B pendant claim cells."""
    meta_path = section / "fig_s5_mechanism.numbers.json"
    meta = json.loads(meta_path.read_text())
    for prefix, key in (("mech", "cell"), ("mech2", "cell2")):
        cid = meta[key]
        _, _, col, r = cid.split("/")
        fb.add(
            f"{prefix}-cell",
            f"{COLL_TEX[col]} (Design B, $r={r.removeprefix('r')}$)",
            f"{meta_path.name} {key}" + (f" (rule: {meta['rule2']})" if key == "cell2" else ""),
            cid,
            "text" if key == "cell" else "selection",
        )
        for side, arm in (("word", K.OURS), ("edit", K.PATH_SYM)):
            _share_fact(fb, f"{prefix}-sibling-closer-{side}", cid, arm, "own_strictly_nearer")
            _share_fact(fb, f"{prefix}-tie-{side}", cid, arm, "tie")
    pat, rs, cols = _all("B")
    cells = [c for c in fb.cells(pat, cols, rs) if c["claim"]]
    if len(cells) != 12:
        raise FactError(f"mechB: {len(cells)} B pendant claim cells, expected 12")
    p = f'cells["{pat}"].mechanism'
    for side, arm in (("word", K.OURS), ("edit", K.PATH_SYM)):
        for key, label in (("own_strictly_nearer", "own"), ("tie", "tie")):
            vals = [(c["mechanism"][arm][key]["mean"], c["id"]) for c in cells]
            lo, hi = min(vals), max(vals)
            fb.add(
                f"mechB-{label}-{side}-range",
                rf"${down(100 * lo[0], 0)}$ to ${up(100 * hi[0], 0)}$\,\%",
                f"full_summary.json {p}.{arm}.{key}.mean over the 12 B pendant claim cells",
                f"min {lo[0]!r} at {lo[1]}; max {hi[0]!r} at {hi[1]}",
                "range in percent: lower end down, upper end up",
            )
    higher = [
        c["id"]
        for c in cells
        if c["mechanism"][K.PATH_SYM]["own_strictly_nearer"]["mean"]
        > c["mechanism"][K.OURS]["own_strictly_nearer"]["mean"]
    ]
    fb.count_fact(
        "mechB-edit-higher-cells",
        len(higher),
        f"full_summary.json {p}.{{bipartite_ged_path_sym,isal_ow_struct}}.own_strictly_nearer.mean",
        f"{len(higher)} of 12: {higher}",
    )


def added_row_facts(fb: FactBook) -> None:
    """Extra facts for the writer: one-round WL as an added row in Designs A and B."""
    flags = fb.summary.get("added_row_flags", {}).get(K.WL_H1, {})
    cells = sum(v["cells"] for h, v in flags.items() if h in ("H-KNN-A", "H-KNN-B", "H-KNN-mix"))
    hits = [
        x["cell"]
        for h, v in flags.items()
        if h in ("H-KNN-A", "H-KNN-B", "H-KNN-mix")
        for x in v["reaches_word"]
    ]
    fb.count_fact(
        "wlh1-AB-reaches-word-cells",
        len(hits),
        'full_summary.json added_row_flags.wl_h1["H-KNN-A","H-KNN-B","H-KNN-mix"] (extra fact)',
        f"{len(hits)} of {cells}: {hits}",
    )
    fb.count_fact(
        "wlh1-AB-cells", cells, "full_summary.json added_row_flags.wl_h1 (extra fact)", cells
    )


def build(root: Path, allow_missing: bool = False) -> FactBook:
    """Every fact of the section.

    With ``allow_missing`` (a partial tree, during a run), a group whose cells
    are not all there yet is skipped with a warning instead of failing; the
    check script then lists the names still undefined.
    """
    summary = json.loads((root / "full_summary.json").read_text())
    fb = FactBook(summary)
    section = root / "section"
    groups: list[Callable[[], None]] = [
        lambda: verdict_facts(fb),
        lambda: tsne_facts(fb, section),
        lambda: design_b_facts(fb),
        lambda: design_a_facts(fb),
        lambda: design_c_facts(fb),
        lambda: design_d_facts(fb),
        lambda: certified_facts(fb),
        lambda: mechanism_facts(fb, section),
        lambda: added_row_facts(fb),
    ]
    for group in groups:
        try:
            group()
        except (FactError, KeyError, ValueError, FileNotFoundError, StopIteration) as e:
            if not allow_missing:
                raise
            print(f"[partial] skipped a group: {type(e).__name__}: {e}", file=sys.stderr)
    return fb


def write_tex(fb: FactBook, path: Path, root: Path) -> None:
    lines = [
        "% knn_facts.tex -- generated by scripts/newpos/knn/figs/section_facts.py; do not edit.",
        f"% root: {root}",
        f"% summary generated: {fb.summary['generated']}; facts generated: "
        f"{time.strftime('%Y-%m-%d %H:%M %Z')}",
        "% Bound rule: range lower ends round down and upper ends up; upper bounds round up;",
        "% other values round half up (3 decimals; percent to whole numbers).",
        "",
    ]
    for f in fb.facts:
        lines.append(f"% src: {f.src} ({f.raw})")
        lines.append(rf"\knnfact{{{f.name}}}{{{f.tex}}}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")


def write_md(fb: FactBook, path: Path, root: Path) -> None:
    lines = [
        "# Section S5 facts (generated by `section_facts.py`; do not edit)",
        "",
        f"Root `{root}`; summary generated {fb.summary['generated']}. Every value comes from "
        "`full_summary.json` (or a figure's `*.numbers.json` record) at the path given. Bound "
        "rule: a range's lower end rounds down and its upper end rounds up; a stated maximum "
        "rounds up; every other value rounds half up at three decimals (percent: whole numbers). "
        "The same lines, as `\\knnfact`, are in `section/knn_facts.tex`.",
        "",
        "| name | value (LaTeX) | source | unrounded | rule |",
        "|---|---|---|---|---|",
    ]
    for f in fb.facts:
        cells = [f.name, f.tex, f.src, f.raw, f.rule]
        lines.append("| " + " | ".join(c.replace("|", "\\|") for c in cells) + " |")
    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--root", type=Path, default=K.OUT_ROOT / "full")
    ap.add_argument("--allow-missing", action="store_true", help="partial tree (during a run)")
    args = ap.parse_args()
    fb = build(args.root, args.allow_missing)
    write_tex(fb, args.root / "section" / "knn_facts.tex", args.root)
    write_md(fb, args.root / "SECTION_FACTS.md", args.root)
    print(f"{len(fb.facts)} facts -> {args.root / 'section' / 'knn_facts.tex'}")


if __name__ == "__main__":
    main()
