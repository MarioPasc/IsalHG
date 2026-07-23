"""Render one sample of every synthetic hypergraph type in the S7 corpora.

Renders the *workable* Stratum A designs plus the Stratum B random generators
with the HyperNetX (Euler-diagram) backend. The highly-symmetric families that
trouble IsalHG canonicalization are excluded per the S7 decision:

  - feasibility-excluded (w*_c DNF at the 300 s cluster budget):
    ag24, pg23, pg24 (affine/projective planes), sts13_0/1, sts15_0 (large Steiner);
  - perturbation-excluded (complete k-uniform: maximal automorphism group ⇒ bounded
    Qin edits land back in the same iso-class ⇒ no non-isomorphic members):
    complete_k3_n5, complete_k4_n6, complete_k5_n6.

The kept families (paths, cycles, small Steiner/GQ) supply arity 3–5 with either
perturbable members (cycles) or single-instance geometry/visual anchors (paths).

Not a library module; a one-off inspection script (print allowed).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

from isalhg.datasets.synthetic.known_design_catalog import (
    _ALL_ENTRIES,
    design_status,
    set_admitted_ids,
)
from isalhg.viz.cohort_panel import cohort_grid_figure
from isalhg.viz.style import save_figure

OUT = Path("artifacts/synthetic_catalog")
BACKEND = "hypernetx"

# Highly-symmetric / broken families excluded from the corpus (S7 decision).
EXCLUDED_FAMILIES: frozenset[str] = frozenset(
    {
        "ag24",
        "pg23",
        "pg24",
        "sts13_0",
        "sts13_1",
        "sts15_0",  # feasibility DNF
        "complete_k3_n5",
        "complete_k4_n6",
        "complete_k5_n6",  # perturbation fails
    }
)


def _load_true_status() -> None:
    """Populate the module gate from the feasibility-pilot artifact."""
    import json

    p = Path("artifacts/feasibility_pilot/feasibility_pilot_stratum_a.json")
    if not p.exists():
        return
    des = json.loads(p.read_text())["designs"]
    admitted = frozenset(k for k, v in des.items() if v.get("status") == "ADMITTED")
    pending = frozenset(k for k, v in des.items() if v.get("status") == "PENDING_CLUSTER")
    set_admitted_ids(admitted, pending_ids=pending)


def _dims(H):  # noqa: ANN001
    return H.n_nodes, H.n_edges, sorted({len(e) for e in H.hyperedges()})


def _panel(entry, H):  # noqa: ANN001
    n, m, _ = _dims(H)
    status = design_status(entry.item_id)
    subtitle = f"a={entry.arity}  n={n}  m={m}  [{status}]"
    return (entry.family_label, subtitle, H)


def _kept_entries():  # noqa: ANN202
    return [(e, H) for e, H in _ALL_ENTRIES if e.item_id not in EXCLUDED_FAMILIES]


def stratum_a_kept() -> None:
    panels = [_panel(e, H) for e, H in _kept_entries()]
    ncols = 4
    nrows = (len(panels) + ncols - 1) // ncols
    fig = cohort_grid_figure(
        panels,
        backend=BACKEND,
        n_columns=ncols,
        figsize=(5.0 * ncols, 5.0 * nrows),
        axis_margin=0.7,
        overall_title="Stratum A — workable designs (HyperNetX; symmetric families excluded)",
    )
    paths = save_figure(fig, OUT / "stratum_a_kept_hnx", formats=("png",))
    print(f"stratum_a_kept: {len(panels)} designs -> {paths[0]}")


def arity45_kept() -> None:
    panels = [_panel(e, H) for e, H in _kept_entries() if e.arity in (4, 5)]
    ncols = 4
    nrows = (len(panels) + ncols - 1) // ncols
    fig = cohort_grid_figure(
        panels,
        backend=BACKEND,
        n_columns=ncols,
        figsize=(5.0 * ncols, 5.0 * nrows),
        axis_margin=0.7,
        overall_title="Stratum A — kept arity-4/5 designs (HyperNetX)",
    )
    paths = save_figure(fig, OUT / "arity45_kept_hnx", formats=("png",))
    print(f"arity45_kept: {len(panels)} designs -> {paths[0]}")


def stratum_b() -> None:
    from isalhg.datasets.registry import get_dataset

    specs: list[tuple[str, str, dict]] = [
        ("random_erdos_renyi", "ER k=3 n=16 m/n=2", {"n": 16, "r": 3, "c": 2.0}),
        ("random_erdos_renyi", "ER k=5 n=12 m/n=2", {"n": 12, "r": 5, "c": 2.0}),
        ("random_erdos_renyi", "ER k=7 n=12 m/n=2", {"n": 12, "r": 7, "c": 2.0}),
        ("random_erdos_renyi", "ER k=10 n=16 m/n=2", {"n": 16, "r": 10, "c": 2.0}),
        ("chung_lu", "Chung-Lu k=3 n=16 c=2", {"n": 16, "k": 3, "c": 2.0}),
        ("random_erdos_renyi_mixed", "Mixed [2,5] n=16 c=2", {"n": 16, "k": 5, "c": 2.0}),
    ]
    panels = []
    for name, label, params in specs:
        try:
            ds = get_dataset(name, params)
            ds = ds.seed(0) if hasattr(ds, "seed") else ds
            item = next(iter(ds))
            H = item.hypergraph
            n, m, ars = _dims(H)
            panels.append((label.split(" n=")[0], f"{label}\nn={n} m={m} arity={ars}", H))
        except Exception as exc:  # noqa: BLE001
            print(f"  [skip] {name} {params}: {type(exc).__name__}: {exc}")
    if not panels:
        print("stratum_b: no panels built")
        return
    ncols = 3
    nrows = (len(panels) + ncols - 1) // ncols
    fig = cohort_grid_figure(
        panels,
        backend=BACKEND,
        n_columns=ncols,
        figsize=(5.0 * ncols, 5.2 * nrows),
        axis_margin=0.7,
        overall_title="Stratum B — random generators (HyperNetX)",
    )
    paths = save_figure(fig, OUT / "stratum_b_random_hnx", formats=("png",))
    print(f"stratum_b: {len(panels)} generators -> {paths[0]}")


HIC_ROOT = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/data/HIC/data/hypergraph")


def hic_examples(hic_name: str = "IMDB-Wri-Genre", per_class: int = 2, max_n: int = 16) -> None:
    """Render small real-data hypergraph examples from one HIC IMDB genre set.

    Picks up to ``per_class`` drawable (n ≤ ``max_n``) movie hypergraphs from each
    genre class so the real corpus can be compared visually to the synthetic one.
    """
    from isalhg.datasets.registry import get_dataset

    ds = get_dataset("hic_atlas", {"root": HIC_ROOT, "hic_name": hic_name})
    by_class: dict[object, list] = {}
    sizes: list[int] = []
    for item in ds:
        H = item.hypergraph
        sizes.append(H.n_nodes)
        cl = item.extra.get("class_label", item.iso_class)
        bucket = by_class.setdefault(cl, [])
        if H.n_nodes <= max_n and len(bucket) < per_class:
            bucket.append((item, H))
    panels = []
    for cl in sorted(by_class, key=str):
        for item, H in by_class[cl]:
            n, m, ars = _dims(H)
            panels.append((f"genre {cl}", f"n={n} m={m} arity={ars}", H))
    if sizes:
        srt = sorted(sizes)
        print(
            f"hic {hic_name}: {len(sizes)} items; n range {srt[0]}-{srt[-1]} "
            f"median {srt[len(srt) // 2]}; drawable(n<={max_n}) panels={len(panels)}"
        )
    if not panels:
        print(f"hic {hic_name}: no drawable panels (all n > {max_n})")
        return
    ncols = 4
    nrows = (len(panels) + ncols - 1) // ncols
    fig = cohort_grid_figure(
        panels,
        backend=BACKEND,
        n_columns=ncols,
        figsize=(5.0 * ncols, 5.0 * nrows),
        axis_margin=0.7,
        overall_title=f"HIC real data — {hic_name} (small examples, HyperNetX)",
    )
    paths = save_figure(fig, OUT / f"hic_{hic_name.lower().replace('-', '_')}", formats=("png",))
    print(f"hic {hic_name}: {len(panels)} examples -> {paths[0]}")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    _load_true_status()
    print(f"excluded {len(EXCLUDED_FAMILIES)} families: {sorted(EXCLUDED_FAMILIES)}")
    stratum_a_kept()
    arity45_kept()
    stratum_b()
    hic_examples("IMDB-Wri-Genre")
    hic_examples("IMDB-Dir-Genre")
    print("done")
