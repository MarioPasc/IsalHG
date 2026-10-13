"""Measure description lengths of one collection: fixed-width, learned, compressors, deltas.

Usage (from the repo root)::

    python scripts/newpos/compression/measure.py --collection ndc_classes --out <dir>

Stages (``--stages``): ``perkb`` (per-member fixed-width and held-out n-gram bits),
``comp`` (whole-collection compressor sizes + member bootstrap), ``delta`` (version
deltas, collections with consecutive pairs only). Every stage writes CSV/JSON/NPZ
files next to ``--out``; nothing is cached between stages except the symbol
sequences, which are cheap to recompute.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import math
import multiprocessing as mp
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from experiments.tkde import corpora as C  # noqa: E402
from scripts.newpos.compression import compressors as K  # noqa: E402
from scripts.newpos.compression import serialize as S  # noqa: E402
from scripts.newpos.compression.coders import cross_validated_bits  # noqa: E402

logger = logging.getLogger("compression.measure")

DEFAULT_ROOT = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE")
ORDERS: tuple[int, ...] = (1, 2, 3)
SEEDS: tuple[int, ...] = (0, 1, 2, 3, 4)
BOOT_SEED = 20261013

# Shared with forked workers (copy-on-write); set once by ``prepare``.
_STATE: dict[str, Any] = {}


# ---------------------------------------------------------------------------
# Preparation
# ---------------------------------------------------------------------------


def prepare(
    collection: str, root: Path, subsample: int | None, subsample_seed: int
) -> dict[str, Any]:
    """Load a collection, encode every member under every arm, and cache the result in ``_STATE``."""
    col = C.load_collection(collection, root=root)
    if subsample is not None and subsample < len(col.records):
        rng = np.random.default_rng(subsample_seed)
        keep = np.sort(rng.choice(len(col.records), size=subsample, replace=False))
        ids = [col.records[int(i)].kb_id for i in keep]
        col = C.subset(col, ids, name=col.name)
    hypergraphs = C.hypergraphs(col)
    n_v, n_e = hypergraphs[0].n_vertex_labels, hypergraphs[0].n_edge_labels
    info = S.CollectionInfo(
        name=collection,
        k=col.k_max,
        n_v=n_v,
        n_e=n_e,
        n_max=max(H.n_nodes for H in hypergraphs),
        big_n_max=max(H.n_nodes + H.n_edges for H in hypergraphs),
    )
    arms = [a for a in S.ARMS if S.arm_available(a, n_v)]
    sequences: dict[str, list[tuple[Any, ...]]] = {a: [] for a in arms}
    for H in hypergraphs:
        encoded = S.encode_member(H, arms)
        for arm in arms:
            sequences[arm].append(encoded[arm])
    members = [
        {
            "kb_id": rec.kb_id,
            "n": H.n_nodes,
            "m": H.n_edges,
            "star": S.is_star(H),
            "fact_bin": S.fact_bin(H.n_edges),
        }
        for rec, H in zip(col.records, hypergraphs, strict=True)
    ]
    alpha_obs = {a: S.observed_alphabet(a, sequences[a]) for a in arms}
    alpha_theo = {a: S.theoretical_alphabet(a, info) for a in arms}
    _STATE.update(
        collection=col,
        info=info,
        arms=arms,
        sequences=sequences,
        members=members,
        alpha_obs=alpha_obs,
        alpha_theo=alpha_theo,
    )
    return _STATE


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_alphabets(out: Path) -> None:
    """Persist the observed and theoretical alphabets and the collection envelope."""
    info = _STATE["info"]
    payload = {
        "collection": info.name,
        "k": info.k,
        "n_vertex_labels": info.n_v,
        "n_edge_labels": info.n_e,
        "n_max": info.n_max,
        "N_max_levi": info.big_n_max,
        "n_members": len(_STATE["members"]),
        "observed": _STATE["alpha_obs"],
        "theoretical": {
            a: {k: str(v) for k, v in d.items()} for a, d in _STATE["alpha_theo"].items()
        },
        "theoretical_log2_total": {
            a: math.log2(sum(d.values())) for a, d in _STATE["alpha_theo"].items()
        },
    }
    (out / f"alphabets_{info.name}.json").write_text(json.dumps(payload, indent=1))


# ---------------------------------------------------------------------------
# Per-member coders
# ---------------------------------------------------------------------------


def _ngram_task(task: tuple[str, int, int]) -> tuple[str, int, int, np.ndarray]:
    arm, order, seed = task
    obs = sum(_STATE["alpha_obs"][arm].values())
    theo = sum(_STATE["alpha_theo"][arm].values())
    scored = cross_validated_bits(
        _STATE["sequences"][arm],
        order=order,
        seed=seed,
        alphabet_obs=obs,
        alphabet_theo=theo,
    )
    table = np.array(
        [[s.bits_obs, s.bits_theo, s.n_unseen, s.n_seen + s.n_unseen] for s in scored],
        dtype=np.float64,
    )
    return arm, order, seed, table


def run_perkb(out: Path, procs: int, seeds: tuple[int, ...]) -> None:
    """Fixed-width and n-gram bits per member; CSV of seed 0 plus the CV-spread table."""
    arms: list[str] = _STATE["arms"]
    members = _STATE["members"]
    sequences = _STATE["sequences"]
    # Heaviest arms first so the pool stays balanced.
    weight = {a: sum(len(s) for s in sequences[a]) for a in arms}
    tasks = [
        (arm, order, seed)
        for arm in sorted(arms, key=lambda a: -weight[a])
        for order in ORDERS
        for seed in seeds
    ]
    t0 = time.perf_counter()
    results: dict[tuple[str, int, int], np.ndarray] = {}
    with mp.get_context("fork").Pool(procs) as pool:
        for done, (arm, order, seed, table) in enumerate(
            pool.imap_unordered(_ngram_task, tasks), 1
        ):
            results[(arm, order, seed)] = table
            if done % 10 == 0 or done == len(tasks):
                logger.info(
                    "n-gram tasks %d/%d (%.0fs)", done, len(tasks), time.perf_counter() - t0
                )

    rows: list[dict[str, Any]] = []
    for arm in arms:
        seqs = sequences[arm]
        fixed_obs = [S.fixed_width_bits(arm, s, _STATE["alpha_obs"][arm]) for s in seqs]
        fixed_theo = [S.fixed_width_bits(arm, s, _STATE["alpha_theo"][arm]) for s in seqs]
        for i, (member, seq) in enumerate(zip(members, seqs, strict=True)):
            row: dict[str, Any] = {
                "collection": _STATE["info"].name,
                "kb_id": member["kb_id"],
                "structure": "star" if member["star"] else "relational",
                "fact_bin": member["fact_bin"],
                "n": member["n"],
                "m": member["m"],
                "representation": arm,
                "L": len(seq),
                "bits_fixed_obs": fixed_obs[i],
                "bits_fixed_theo": fixed_theo[i],
            }
            for order in ORDERS:
                table = results[(arm, order, 0)]
                row[f"bits_ngram{order}"] = table[i, 0]
                row[f"bits_ngram{order}_theo"] = table[i, 1]
                row[f"unseen_ngram{order}"] = int(table[i, 2])
            rows.append(row)
    _write_csv(out / f"perkb_{_STATE['info'].name}.csv", rows)

    spread: list[dict[str, Any]] = []
    for (arm, order, seed), table in sorted(results.items()):
        spread.append(
            {
                "collection": _STATE["info"].name,
                "representation": arm,
                "order": order,
                "seed": seed,
                "median_bits_obs": float(np.median(table[:, 0])),
                "mean_bits_obs": float(np.mean(table[:, 0])),
                "median_bits_theo": float(np.median(table[:, 1])),
                "unseen_fraction": float(table[:, 2].sum() / table[:, 3].sum()),
            }
        )
    _write_csv(out / f"ngram_seeds_{_STATE['info'].name}.csv", spread)


# ---------------------------------------------------------------------------
# Generic compressors
# ---------------------------------------------------------------------------


def _point_task(arm: str) -> list[dict[str, object]]:
    return K.point_sizes(arm, _STATE["sequences"][arm])


def _boot_task(task: tuple[str, str, str, str]) -> tuple[str, np.ndarray]:
    arm, kind, which, rendering = task
    seqs = _STATE["sequences"][arm]
    ids = K.frequency_ids(seqs)
    table = K.codepoint_table(len(ids))
    chunks = K.render_lines(arm, seqs, rendering, ids, table)
    member_symbols = symbol_texts = None
    if which == "self_contained" and rendering in ("ids", "cp"):
        member_symbols = [frozenset(ids[s] for s in seq) for seq in seqs]
        ordered = sorted(ids, key=ids.__getitem__)
        symbol_texts = [S.symbol_text(arm, sym).encode() for sym in ordered]
    sizes = K.bootstrap_sizes(chunks, kind, _STATE["boot_index"], member_symbols, symbol_texts)
    return f"{arm}|{kind}|{which}", sizes


def run_compressors(out: Path, procs: int, reps: int, boot_arms: list[str] | None) -> None:
    """Whole-collection compressed sizes for every arm, rendering, compressor; bootstrap CIs."""
    arms: list[str] = _STATE["arms"]
    name = _STATE["info"].name
    n = len(_STATE["members"])
    t0 = time.perf_counter()
    with mp.get_context("fork").Pool(procs) as pool:
        point_rows = [r for chunk in pool.map(_point_task, arms, chunksize=1) for r in chunk]
    logger.info("compressor point sizes: %.0fs", time.perf_counter() - t0)
    _write_csv(out / f"compressors_point_{name}.csv", point_rows)
    chosen = K.choose_renderings(point_rows)

    index = np.random.default_rng(BOOT_SEED).integers(0, n, size=(reps, n))
    _STATE["boot_index"] = index
    tasks: list[tuple[str, str, str, str]] = []
    for (arm, kind), picks in chosen.items():
        if boot_arms is not None and arm not in boot_arms:
            continue
        for which, rendering in picks.items():
            tasks.append((arm, kind, which, rendering))
    t0 = time.perf_counter()
    boot: dict[str, np.ndarray] = {}
    with mp.get_context("fork").Pool(procs) as pool:
        for done, (key, sizes) in enumerate(pool.imap_unordered(_boot_task, tasks), 1):
            boot[key] = sizes
            if done % 6 == 0 or done == len(tasks):
                logger.info("bootstrap %d/%d (%.0fs)", done, len(tasks), time.perf_counter() - t0)
    np.savez_compressed(out / f"compressors_boot_{name}.npz", **boot)

    by_key = {(str(r["arm"]), str(r["compressor"]), str(r["rendering"])): r for r in point_rows}
    rows: list[dict[str, Any]] = []
    for (arm, kind), picks in sorted(chosen.items()):
        for which, rendering in picks.items():
            point = by_key[(arm, kind, rendering)]
            total = int(point["bytes"]) + (
                int(point["dict_bytes"]) if which == "self_contained" else 0
            )
            sizes = boot.get(f"{arm}|{kind}|{which}")
            low, high = K.percentile_ci(sizes) if sizes is not None else (float("nan"),) * 2
            rows.append(
                {
                    "collection": name,
                    "arm": arm,
                    "compressor": kind,
                    "number": which,
                    "rendering": rendering,
                    "bytes_total": total,
                    "bytes_per_kb": total / n,
                    "ci_low": low,
                    "ci_high": high,
                    "boot_mean": float(sizes.mean()) if sizes is not None else float("nan"),
                    "n_members": n,
                    "boot_reps": reps if sizes is not None else 0,
                }
            )
    _write_csv(out / f"compressors_{name}.csv", rows)


# ---------------------------------------------------------------------------
# Version deltas (HB3)
# ---------------------------------------------------------------------------


def _delta_task(arm: str) -> list[dict[str, Any]]:
    from rapidfuzz.distance import Levenshtein

    seqs = _STATE["sequences"][arm]
    index = {m["kb_id"]: i for i, m in enumerate(_STATE["members"])}
    ids = K.frequency_ids(seqs)
    table = K.codepoint_table(len(ids))
    cps = [K.render_cp_line(s, ids, table) for s in seqs]
    rows: list[dict[str, Any]] = []
    with K.delta_workdir() as tmp:
        work = Path(tmp)
        for pair_no, pair in enumerate(_STATE["pairs"]):
            a, b = index[pair["a"]], index[pair["b"]]
            rows.append(
                {
                    "collection": _STATE["info"].name,
                    "pair": pair_no,
                    "a": pair["a"],
                    "b": pair["b"],
                    "constant_preserving": bool(pair["constant_preserving"]),
                    "fact_delta": pair.get("delta"),
                    "arm": arm,
                    "patch_bytes": K.zstd_patch_size(cps[a].encode(), cps[b].encode(), work),
                    "self_patch_bytes": K.zstd_patch_size(cps[b].encode(), cps[b].encode(), work),
                    "edit_distance": int(Levenshtein.distance(cps[a], cps[b])),
                    "len_a": len(seqs[a]),
                    "len_b": len(seqs[b]),
                }
            )
    return rows


def run_deltas(out: Path, procs: int) -> None:
    """Version-delta sizes between consecutive natural versions, per arm."""
    present = {m["kb_id"] for m in _STATE["members"]}
    pairs = [
        p for p in C.consecutive_pairs(_STATE["collection"]) if p["a"] in present and p["b"] in present
    ]
    if not pairs:
        logger.info("no consecutive pairs in %s", _STATE["info"].name)
        return
    _STATE["pairs"] = pairs
    with mp.get_context("fork").Pool(procs) as pool:
        rows = [r for chunk in pool.map(_delta_task, _STATE["arms"], chunksize=1) for r in chunk]
    _write_csv(out / f"deltas_{_STATE['info'].name}.csv", rows)


# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    """Command-line entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--collection", required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    ap.add_argument("--subsample", type=int, default=None)
    ap.add_argument("--subsample-seed", type=int, default=0)
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--stages", default="perkb,comp,delta")
    ap.add_argument("--boot-reps", type=int, default=200)
    ap.add_argument("--boot-arms", default=None, help="comma-separated; default all")
    ap.add_argument("--seeds", default="0,1,2,3,4")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    args.out.mkdir(parents=True, exist_ok=True)
    stages = set(args.stages.split(","))
    seeds = tuple(int(s) for s in args.seeds.split(","))
    t0 = time.perf_counter()
    prepare(args.collection, args.root, args.subsample, args.subsample_seed)
    logger.info(
        "%s: %d members, %d arms, encoded in %.1fs",
        args.collection,
        len(_STATE["members"]),
        len(_STATE["arms"]),
        time.perf_counter() - t0,
    )
    write_alphabets(args.out)
    (args.out / f"members_{args.collection}.json").write_text(json.dumps(_STATE["members"]))
    if "perkb" in stages:
        run_perkb(args.out, args.procs, seeds)
    if "comp" in stages:
        boot_arms = args.boot_arms.split(",") if args.boot_arms else None
        run_compressors(args.out, args.procs, args.boot_reps, boot_arms)
    if "delta" in stages:
        run_deltas(args.out, args.procs)
    logger.info("done in %.0fs", time.perf_counter() - t0)


if __name__ == "__main__":
    main()
