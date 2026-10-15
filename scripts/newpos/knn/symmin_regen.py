"""Regenerate every article number that uses the bipartite edit path, with the symmetric min.

The article will define the edit-path competitor as ``d_sym(a, b) = min(d(a, b), d(b, a))``.
This script recomputes the numbers that used the as-run orientation through their
original code paths, changing only the edit-path values, and writes everything under
``KNN_2026-10-15/symmin_regen/``:

* ``neardup/``  -- C8 (``neardup.py``, ``neardup_r2.py``, and the ``--restrict-to-arm
  wstar_orbit`` runs), from the sym-min matrix roots of ``c8_orientation_audit.py``;
* ``tab_neardup.tex`` and ``fig_neardup_retrieval.{pdf,png}`` -- the C8 table and figure
  generators run unchanged on those JSONs;
* ``rq2/`` -- the H1 census: the RQ2 rows of the edit path (census, asymmetry and
  triangle rows, exactness at zero) recomputed with the sym-min value, the RQ2
  aggregation functions re-run on all rows, and ``summary.json`` patched in its three
  affected sections (every other section copied); the F1 figure script run on it.

Every recomputation is validated first: the as-run values recomputed here must equal the
stored ones (orientation, member order, relabelling stream).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import random
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(REPO))
import c8_orientation_audit as AUD  # noqa: E402, N812

from experiments.tkde import corpora as C  # noqa: E402, N812

RESULTS = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results")
OUT = RESULTS / "KNN_2026-10-15" / "symmin_regen"
AUDIT = RESULTS / "KNN_2026-10-15" / "c8_orientation_audit"
RQ2_DIR = RESULTS / "IEEETKDE_ow" / "RQ2_wellposedness" / "wellposedness"
ARTICLE = Path(
    "/media/mpascual/Sandisk2TB/research/ISAL/isalhg/article/journal/"
    "6a788a680cdbdddd16e47a6e-lighten/submission"
)
PATH = "bipartite_ged_path"
RQ2_COLLECTIONS = ("ndc_classes", "ndc_substances", "wd50k66")


# --------------------------------------------------------------------------- C8


def regen_c8() -> dict[str, Any]:
    """Copy the sym-min C8 reruns, add the wstar-restricted ones, run the table and figure."""
    dest = OUT / "neardup"
    dest.mkdir(parents=True, exist_ok=True)
    for p in sorted((AUDIT / "symmin").glob("neardup*.json")):
        shutil.copy2(p, dest / p.name)
    checks: dict[str, Any] = {}
    for c in ("wd50k66", "ndc_classes"):
        for variant, target in (("symmin", dest), ("asrun", OUT / "asrun_check")):
            root = AUD.link_root(variant, c)
            AUD.run_scorer(
                "neardup.py", root, c, target, ["--key", "cert", "--restrict-to-arm", "wstar_orbit"]
            )
        mine = json.loads((OUT / "asrun_check" / f"neardup_{c}__on_wstar_orbit.json").read_text())
        pub = json.loads((AUD.C8_DIR / f"neardup_{c}__on_wstar_orbit.json").read_text())
        checks[c] = all(
            abs(mine["arms"][a]["MRR"] - pub["arms"][a]["MRR"]) < 1e-12
            for a in pub["arms"]
            if "MRR" in pub["arms"][a]
        )
    py = sys.executable
    for script, out_name in (("tab_neardup.py", "tab_neardup.tex"), ("fig_neardup.py", None)):
        out = OUT / (out_name or "fig_neardup_retrieval.pdf")
        subprocess.run(
            [py, str(REPO / "scripts" / "newpos" / script), "--root", str(dest), "--out", str(out)],
            check=True,
        )
    # The same generator on the published JSONs, so the regenerated table can be diffed
    # against an unchanged-code baseline rather than against the hand-edited article copy.
    subprocess.run(
        [
            py,
            str(REPO / "scripts" / "newpos" / "tab_neardup.py"),
            "--root",
            str(AUD.C8_DIR),
            "--out",
            str(OUT / "tab_neardup_published_regen.tex"),
        ],
        check=True,
    )
    return {"wstar_restricted_asrun_reproduces_published": checks}


# --------------------------------------------------------------------------- RQ2


def _ordered(collection: str) -> np.ndarray:
    return np.load(AUDIT / "matrices" / collection / f"{PATH}.ordered.npy")


def regen_rq2_rows() -> dict[str, Any]:
    """Rewrite the edit-path rows of the RQ2 census, bipartite and exact0 tables."""
    import pandas as pd

    from experiments.tkde import rq2
    from isalhg.core.sparse_hypergraph import permute
    from isalhg.metric_space.registry import get_distance

    rows_dir = OUT / "rq2" / "RQ2_wellposedness" / "wellposedness"
    rows_dir.mkdir(parents=True, exist_ok=True)
    for p in RQ2_DIR.glob("rows_*.csv"):
        shutil.copy2(p, rows_dir / p.name)
    d = get_distance(PATH)
    report: dict[str, Any] = {}
    for c in RQ2_COLLECTIONS:
        col = C.load_collection(c)
        graphs = C.hypergraphs(col)
        ids = [r.kb_id for r in col.records]
        pos = {k: i for i, k in enumerate(ids)}
        P = _ordered(c)
        S = np.minimum(P, P.T)
        rep: dict[str, Any] = {}

        # census: the zero-distance components under the sym-min matrix
        name = f"rows_census__f14fffbc-census-{c}-{PATH}.csv"
        census = pd.read_csv(RQ2_DIR / name)
        asrun = np.zeros_like(P)
        iu = np.triu_indices(len(ids), 1)
        asrun[iu] = P[iu]
        asrun = asrun + asrun.T
        class_ids = rq2._true_class_ids(graphs)
        old = rq2.census_counts(asrun, class_ids)
        new = rq2.census_counts(S, class_ids)
        rep["census_asrun_reproduces"] = old["n_classes_arm"] == int(
            census["n_classes_arm"][0]
        ) and old["n_false_merges"] == int(census["n_false_merges"][0])
        census.loc[0, "n_false_merges"] = new["n_false_merges"]
        census.loc[0, "n_classes_arm"] = new["n_classes_arm"]
        census.to_csv(rows_dir / name, index=False)
        rep["census_old"] = {k: old[k] for k in ("n_false_merges", "n_classes_arm")}
        rep["census_new"] = {
            k: new[k] for k in ("n_false_merges", "n_classes_arm", "n_classes_true")
        }

        # asymmetry and triangle rows
        name = f"rows_bipartite__f14fffbc-bipartite-{c}.csv"
        bip = pd.read_csv(RQ2_DIR / name, dtype={"violation": "object"})
        mism = 0
        tol = rq2.ZERO_TOLERANCE
        for i, row in bip.iterrows():
            if row["arm"] != PATH:
                continue
            parts = str(row["ids"]).split("|")
            if row["kind"] == "pair":
                a, b = pos[parts[0]], pos[parts[1]]
                mism += int(P[a, b] != float(row["d_ab"])) + int(P[b, a] != float(row["d_ba"]))
                v = S[a, b]
                bip.loc[i, ["d_ab", "d_ba"]] = [v, v]
                bip.loc[i, "violation"] = 0
            elif row["kind"] == "triple":
                a, b, cc = pos[parts[0]], pos[parts[1]], pos[parts[2]]
                mism += int(P[a, b] != float(row["d_ab"])) + int(P[b, cc] != float(row["d_bc"]))
                mism += int(P[a, cc] != float(row["d_ac"]))
                dab, dbc, dac = S[a, b], S[b, cc], S[a, cc]
                bip.loc[i, ["d_ab", "d_bc", "d_ac"]] = [dab, dbc, dac]
                bip.loc[i, "violation"] = int(dac > dab + dbc + tol)
        bip.to_csv(rows_dir / name, index=False)
        rep["bipartite_stored_vs_ordered_mismatches"] = mism

        # exactness at zero: replay the relabelling stream of rq2.run_exact0
        name = f"rows_exact0__f14fffbc-exact0-{c}-{PATH}.csv"
        ex = pd.read_csv(RQ2_DIR / name)
        master = rq2.seeds(rq2.RQ_INDEX)[0]
        rng = random.Random(master + 7)
        mism0 = 0
        for index in range(min(int(len(ex)), len(graphs))):
            member = rng.randrange(len(graphs))
            H = graphs[member]
            order = list(range(col.records[member].n))
            rng.shuffle(order)
            Hp = permute(H, {node: order[node] for node in range(len(order))})
            fwd, back = float(d.pairwise(H, Hp)), float(d.pairwise(Hp, H))
            assert ex.loc[index, "pair_id"] == f"{ids[member]}|sigma{index}"
            mism0 += int(abs(fwd - float(ex.loc[index, "d"])) > 1e-9)
            v = min(fwd, back)
            ex.loc[index, "d"] = v
            ex.loc[index, "at_zero"] = int(rq2.is_zero(v))
        ex.to_csv(rows_dir / name, index=False)
        rep["exact0_stored_vs_replay_mismatches"] = mism0
        rep["exact0_new_at_zero"] = int(ex["at_zero"].sum())
        report[c] = rep
    return report


def regen_rq2_summary() -> dict[str, Any]:
    """Patch ``summary.json`` with the census, bipartite and exact0 sections of the new rows."""
    from experiments.tkde import analyze_rq2 as A  # noqa: N812
    from experiments.tkde.analyze_rq1 import load_table

    original = json.loads((RQ2_DIR / "summary.json").read_text())

    def sections(root: Path) -> dict[str, Any]:
        return {
            "exact0": A.exactness_at_zero(load_table(root, A.RQ_FOLDER, "exact0")),
            "census": A.census(load_table(root, A.RQ_FOLDER, "census")),
            "bipartite": A.bipartite(load_table(root, A.RQ_FOLDER, "bipartite")),
        }

    # Validation: the three sections recomputed from the original rows equal the frozen ones.
    base = OUT / "rq2_original_rows"
    (base / "RQ2_wellposedness" / "wellposedness").mkdir(parents=True, exist_ok=True)
    for p in RQ2_DIR.glob("rows_*.csv"):
        target = base / "RQ2_wellposedness" / "wellposedness" / p.name
        if not target.exists():
            target.symlink_to(p)
    same = sections(base)
    reproduces = {
        k: json.dumps(same[k], sort_keys=True, default=str)
        == json.dumps(original[k], sort_keys=True, default=str)
        for k in same
    }
    new = sections(OUT / "rq2")
    patched = dict(original)
    patched.update(new)
    patched["symmin_regen"] = {
        "note": "census, bipartite and exact0 recomputed with the edit path read as "
        "min(d(a,b), d(b,a)); every other section copied from the frozen summary.json",
        "frozen_source": str(RQ2_DIR / "summary.json"),
    }
    dest = OUT / "rq2" / "RQ2_wellposedness" / "wellposedness" / "summary.json"
    dest.write_text(json.dumps(patched, indent=2, default=str))
    return {"sections_reproduce_frozen": reproduces, "summary": str(dest)}


def regen_f1(summary: Path) -> dict[str, Any]:
    """Run the article's F1 script on the regenerated summary (its count assertions reported)."""
    path = ARTICLE / "article" / "figures" / "scripts" / "fig_f1_partition.py"
    spec = importlib.util.spec_from_file_location("fig_f1_partition", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    mod.SUMMARY = summary
    mod.OUT = OUT / "fig_partition.pdf"
    failed = None
    try:
        mod.check(mod.load_census())
    except AssertionError as exc:
        failed = f"AssertionError {exc!r} (the script pins the as-run counts)"
    original_check = mod.check
    mod.check = lambda census: None
    mod.main()
    mod.check = original_check
    return {"figure": str(mod.OUT), "frozen_assertions": failed or "all pass"}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--skip-c8", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {}
    if not args.skip_c8:
        report["c8"] = regen_c8()
    report["rq2_rows"] = regen_rq2_rows()
    report["rq2_summary"] = regen_rq2_summary()
    report["f1"] = regen_f1(Path(report["rq2_summary"]["summary"]))
    (OUT / "regen_report.json").write_text(json.dumps(report, indent=1, default=str))
    print(json.dumps(report, indent=1, default=str))


if __name__ == "__main__":
    main()
