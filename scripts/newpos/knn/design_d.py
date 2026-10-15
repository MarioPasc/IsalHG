"""Design D of KNN_2026-10-15: linkage of partial exports against a reference catalogue (LOG.md §7).

One job is one ``(collection, mix)`` pair and writes one JSON with every
requested seed (``<out>/D_<collection>_<mix>.json``, rewritten after each seed;
seeds already in it are skipped, so an interrupted job resumes).

Catalogue: every record of the frozen collection (the C8 envelope),
deduplicated to isomorphism classes by the nauty certificate, each class
represented by its lowest member index. Queries: ``C_COPIES = 3`` partial copies
per source at each ``r`` in ``RS``; the ``S`` sources are drawn uniformly from the
catalogue records that yield 3 pairwise non-isomorphic copies at every ``r``
(``knn_lib.select_sources``, the §6.1 rule). ``mix = pendant`` uses pendant
removals only; ``mix = empirical`` uses C8's pendant / interior share with the
Design-B interior-draw correction (``knn_lib.mix_q``). Nothing is removed from
the catalogue: a copy isomorphic to another catalogue record draws every exact
arm to that record, and the exact-arm ceiling (the share of queries isomorphic to
no catalogue record) is reported per cell.

Scoring per query and arm, against the whole catalogue: the probability that the
1-NN is the source when ties are broken uniformly (expected 1-NN accuracy), and
the reciprocal of the source's expected rank (ties by expectation, C8's
convention). Rectangles come from :mod:`rect` (the ``[queries, catalogue]``
block of each arm's own matrix over ``catalogue + queries``).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import knn_lib as K  # noqa: E402, N812
import rect as R  # noqa: E402, N812

from experiments.tkde import corpora as C  # noqa: E402, N812
from isalhg.datasets.kb.base import KBCollection  # noqa: E402

logger = logging.getLogger("design_d")

C_COPIES = 3
RS: tuple[int, ...] = (1, 2, 3)
S_PROBE = 60
MIXES: tuple[str, ...] = ("pendant", "empirical")
#: The bipartite arms whose verdict reading is the symmetric min (LOG.md §7.1, adopted after
#: the probe values were seen; it can only help the competitor). The as-run orientation stays
#: in the job as a reported row.
SYM_ARMS: tuple[str, ...] = ("bipartite_ged_path_sym",)
ARMS: tuple[str, ...] = (*K.ARMS_C, *SYM_ARMS)
COMPETITORS_D: tuple[str, ...] = tuple(
    f"{a}_sym" if f"{a}_sym" in SYM_ARMS else a for a in K.COMPETITORS_C
)


class DesignDError(K.KnnExperimentError):
    """Design D cannot be set up as specified."""


# --------------------------------------------------------------------------- catalogue


def build_catalogue(col: KBCollection, keys: K.IsoKeys) -> tuple[KBCollection, dict[str, Any]]:
    """The collection deduplicated to isomorphism classes (lowest member index per class).

    Returns
    -------
    tuple
        The catalogue (a sub-collection in member order) and a census: members,
        classes by each exact key, and their disagreement count.
    """
    seen: dict[Any, int] = {}
    ow_seen: set[Any] = set()
    reps: list[str] = []
    for rec in col.records:
        cert, ow = keys(rec)
        ow_seen.add(ow)
        if cert in seen:
            continue
        seen[cert] = len(reps)
        reps.append(rec.kb_id)
    cat = C.subset(col, reps, name=f"{col.name}_catalogue")
    return cat, {
        "n_members": len(col.records),
        "n_catalogue": len(reps),
        "n_classes_ordered_walk": len(ow_seen),
        "key_disagreement": len(ow_seen) != len(reps),
    }


# --------------------------------------------------------------------------- scoring


def nn_scores(d: np.ndarray, src: int) -> tuple[float, float]:
    """``(P[1-NN is the source], 1 / expected rank of the source)`` of one query row.

    Ties are uniform: the 1-NN is drawn from the block at the minimum distance,
    and the source's rank inside its own tie block is its expectation.
    """
    d = np.where(np.isnan(d), np.inf, d)
    dmin = d.min()
    block_min = int((d == dmin).sum())
    p1 = (1.0 / block_min) if d[src] == dmin else 0.0
    better = int((d < d[src]).sum())
    tie = int((d == d[src]).sum())
    return p1, 1.0 / (1.0 + better + (tie - 1) / 2.0)


def score_rect(D: np.ndarray, sources: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Per-query 1-NN probability and reciprocal rank for a ``(Q, N)`` rectangle."""
    out = np.array([nn_scores(D[i], int(sources[i])) for i in range(len(sources))])
    return out[:, 0], out[:, 1]


# --------------------------------------------------------------------------- job


def fit_arms(cat_hs: Sequence[Any], n_jobs: int) -> dict[str, R.ArmRect]:
    """Fit every arm's rectangle on the catalogue (fingerprints computed once per job)."""
    arms: dict[str, R.ArmRect] = {}
    # The forking pairwise arms are fitted and run before anything else touches C++ state.
    for name in sorted(ARMS, key=lambda a: (not a.startswith("bipartite"), ARMS.index(a))):
        arms[name] = R.make_arm(name, n_jobs).fit(cat_hs)
        logger.info("fitted %s on %d records in %.1f s", name, len(cat_hs), arms[name].secs_fit)
    return {a: arms[a] for a in ARMS}


def run_seed(
    col: KBCollection,
    cat: KBCollection,
    cat_certs: dict[Any, int],
    arms: dict[str, R.ArmRect],
    keys: K.IsoKeys,
    mix: str,
    q_interior: float,
    seed: int,
    S: int,
    existing: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Sources, copies and the three ``r`` cells of one seed.

    With ``existing`` (a seed already on disk), the sources and copies are
    regenerated from the same seed, checked against the stored source ids, and
    only the arms missing from the stored cells are computed.
    """
    t0 = time.perf_counter()
    source_seed = K.cell_seed(seed, "D", col.name, mix, "sources")
    draw = K.select_sources(
        cat, S, RS, C_COPIES, np.random.default_rng(source_seed), keys, q_interior=q_interior
    )
    index = cat.index()
    if existing is not None and [s.kb_id for s in draw.sources] != existing["source_ids"]:
        raise DesignDError(
            f"{col.name} seed {seed}: regenerated sources differ from the stored ones"
        )
    payload: dict[str, Any] = existing or {
        "seed": seed,
        "source_seed": source_seed,
        "S": len(draw.sources),
        "shortfall": draw.shortfall,
        "source_ids": [s.kb_id for s in draw.sources],
        "eligibility": {
            "n_tried": draw.n_tried,
            "n_ineligible": draw.n_ineligible,
            "secs_select": draw.secs,
        },
        "cells": {},
    }
    for r in RS:
        tr = time.perf_counter()
        items = [cp for per in draw.copies[r] for cp in per]
        sources = np.array([index[cp.label] for cp in items])
        hs = K.hypergraphs(items, col.n_types, col.n_preds)
        shared = np.array([keys(cp)[0] in cat_certs for cp in items])
        st = draw.stats[r]
        steps = st.steps_pendant + st.steps_interior
        cell: dict[str, Any] = payload["cells"].get(str(r)) or {
            "r": r,
            "n_queries": len(items),
            "exact_arm_ceiling": float(1.0 - shared.mean()),
            "n_iso_to_catalogue": int(shared.sum()),
            "copies": {
                "draws": st.draws,
                "iso_rejected_within_source": st.iso_rejected,
                "key_disagreements": st.key_disagreements,
                "realized_pendant_share": st.steps_pendant / steps if steps else None,
                "steps_fallback": st.steps_fallback,
            },
            "arms": {},
        }
        for name, arm in arms.items():
            if name in cell["arms"]:
                continue
            ta = time.perf_counter()
            D = arm.rect(hs)
            secs = time.perf_counter() - ta
            p1, rr = score_rect(D, sources)
            cell["arms"][name] = {
                "acc1": float(p1.mean()),
                "rr": float(rr.mean()),
                "secs": secs,
                "pairs_per_s": arm.last_pairs_per_s,
                "nn_zero_share": float((D.min(axis=1) == 0).mean()),
                "p_correct1": [round(float(x), 6) for x in p1],
                "rr_q": [round(float(x), 6) for x in rr],
            }
        if existing is None:
            cell["secs"] = time.perf_counter() - tr
        payload["cells"][str(r)] = cell
    if existing is None:
        payload["secs_seed"] = time.perf_counter() - t0
    else:
        payload.setdefault("secs_augment", []).append(time.perf_counter() - t0)
    return payload


def run_job(
    collection: str,
    mix: str,
    seeds: Sequence[int],
    out: Path,
    n_jobs: int,
    S: int = S_PROBE,
) -> Path:
    """Run every requested seed of one ``(collection, mix)`` job; resume from disk."""
    if mix not in MIXES:
        raise DesignDError(f"unknown mix {mix!r}; expected one of {MIXES}")
    path = out / f"D_{collection}_{mix}.json"
    payload: dict[str, Any] = (
        json.loads(path.read_text())
        if path.exists()
        else {"collection": collection, "mix": mix, "seeds": {}}
    )
    if payload.get("config", {}).get("S", S) != S:
        raise DesignDError(f"{path} holds S={payload['config']['S']}, asked for S={S}")
    t0 = time.perf_counter()
    col = C.load_collection(collection)
    keys = K.IsoKeys(col.n_types, col.n_preds)
    cat, census = build_catalogue(col, keys)
    cat_certs = {keys(rec)[0]: i for i, rec in enumerate(cat.records)}
    q, calib = 0.0, None
    if mix == "empirical":
        calib = K.interior_availability(col)
        q = K.mix_q(K.PENDANT_SHARE[collection], calib["availability"])
    cat_hs = K.hypergraphs(cat.records, col.n_types, col.n_preds)
    arms = fit_arms(cat_hs, n_jobs)
    payload.update(
        {
            "design": "D",
            "config": {
                "S": S,
                "c": C_COPIES,
                "r": list(RS),
                "arms": list(ARMS),
                "competitors": list(COMPETITORS_D),
                "n_jobs": n_jobs,
                "q_interior": q,
                "target_pendant_share": K.PENDANT_SHARE[collection] if mix == "empirical" else 1.0,
                "availability": calib,
                "orientation": (
                    "bipartite arms: '<arm>' = pairwise(catalogue_record, query) (as run, a "
                    "reported row); '<arm>_sym' = min of both orientations (the verdict arm, "
                    "LOG.md 7.1)"
                ),
            },
            "catalogue": census,
            "secs_fit": {a: arm.secs_fit for a, arm in arms.items()},
            "secs_setup": time.perf_counter() - t0,
        }
    )
    for seed in seeds:
        existing = payload["seeds"].get(str(seed))
        if existing is not None:
            missing = {a for a in ARMS for c in existing["cells"].values() if a not in c["arms"]}
            if not missing:
                logger.info("%s %s seed %d on disk, skipped", collection, mix, seed)
                continue
            logger.info("%s %s seed %d: adding arms %s", collection, mix, seed, sorted(missing))
            todo = {a: arm for a, arm in arms.items() if a in missing}
            payload["seeds"][str(seed)] = run_seed(
                col, cat, cat_certs, todo, keys, mix, q, seed, S, existing
            )
            K.write_json(path, payload)
            continue
        res = run_seed(col, cat, cat_certs, arms, keys, mix, q, seed, S)
        payload["seeds"][str(seed)] = res
        K.write_json(path, payload)
        _log_seed(collection, mix, res)
    K.write_json(path, payload)
    return path


def _log_seed(collection: str, mix: str, res: dict[str, Any]) -> None:
    parts = []
    for r, cell in res["cells"].items():
        w = cell["arms"][K.OURS]
        b = K.best_competitor(cell["arms"], "acc1", K.COMPETITORS_C)
        bp = cell["arms"]["bipartite_ged_path"].get("pairs_per_s") or 0.0
        parts.append(
            f"r{r}: w° {w['acc1']:.3f} vs {b[0]} {b[1]:.3f} (ceiling "
            f"{cell['exact_arm_ceiling']:.3f}; bip {bp:,.0f} pairs/s)"
        )
    logger.info(
        "%s %s seed %s: S=%d (%.1f s) | %s",
        collection,
        mix,
        res["seed"],
        res["S"],
        res["secs_seed"],
        " | ".join(parts),
    )


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--collection", required=True, choices=list(K.COLLECTIONS))
    ap.add_argument("--mix", required=True, choices=list(MIXES))
    ap.add_argument("--seeds", nargs="+", type=int, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--sources", type=int, default=S_PROBE, help="S (60 probe, 200 full run)")
    ap.add_argument(
        "--n-jobs",
        type=int,
        default=int(os.environ.get("SLURM_CPUS_PER_TASK", os.cpu_count() or 1)),
    )
    args = ap.parse_args()
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(name)s %(message)s", datefmt="%H:%M:%S"
    )
    for noisy in ("isalhg", "experiments"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    args.out.mkdir(parents=True, exist_ok=True)
    path = run_job(args.collection, args.mix, args.seeds, args.out, args.n_jobs, args.sources)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
