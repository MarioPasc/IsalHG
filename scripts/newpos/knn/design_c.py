"""Design C of KNN_2026-10-15: kNN and k-medoids among look-alike records (LOG.md §6).

One job is one ``(collection, stratum)`` pair and writes one JSON with every
requested seed (``<out>/C_<collection>_<stratum>.json``; rewritten after each
seed, and seeds already in it are skipped, so an interrupted job resumes).

Blocks. The C8 one-edit relation among the collection's real records
(``neardup.ground_truth``, keyed by the nauty certificate), on isomorphism
classes, each class represented by its lowest member index. A pair is pendant
iff the two records differ in their number of constants, interior otherwise.
A block is a seed record plus a uniform subsample of at most four of its
one-edit neighbours of the stratum's kind(s); it has at least three members;
blocks of one seed are disjoint. Only records that are valid Design-B sources
(``c`` pairwise non-isomorphic pendant copies at every ``r``, decided once per
collection with a fixed seed) enter the graph.

Two draws per seed, on separate random streams: the *counting* draw runs to
exhaustion and its number of blocks is the stratum's feasibility statistic
(< 10 is infeasible); the *pool* draw stops once the blocks hold at least
``S_TARGET`` sources (or the candidates run out) and is the evaluated pool.

Copies are Design B's (``c`` per member, ``r`` pendant removals); the copies of
a record depend only on ``(seed, record)``, so a record shares its copies across
strata within a seed. Every arm (the word, the ten §2 competitors and the
one-round WL) is scored by leave-one-out 1-NN over the whole pool (ties at
expectation), PAM ARI with ``k = S``, the exact-arm ceiling, the cross-source
isomorphism fraction, and the share of 1-NN errors that stay inside the query's
own block.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from collections import defaultdict
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import knn_lib as K  # noqa: E402, N812

from experiments.tkde import corpora as C  # noqa: E402, N812
from isalhg.datasets.kb.base import KBCollection, KBRecord  # noqa: E402

logger = logging.getLogger("design_c")

STRATA: dict[str, tuple[str, ...]] = {
    "C-all": ("pendant", "interior"),
    "C-int": ("interior",),
    "C-pend": ("pendant",),
}
S_TARGET = 60
#: Copies per member: 3 is the primary (LOG.md §6.1 amendment, before any result); 6 is the
#: registered value, still run on its feasible cells as the secondary.
C_COPIES = 3
C_SECONDARY = 6
RS: tuple[int, ...] = (1, 2, 3)
BLOCK_NEIGHBOURS = 4
BLOCK_MIN = 3
MIN_FEASIBLE_BLOCKS = 10
ELIGIBILITY_SEED = 0


class DesignCError(K.KnnExperimentError):
    """Design C cannot be set up as specified."""


# --------------------------------------------------------------------------- relation


@dataclass(frozen=True)
class OneEditGraph:
    """The C8 one-edit relation on isomorphism classes.

    Attributes
    ----------
    rep : dict[int, int]
        Isomorphism class -> representative member index (the lowest).
    adj : dict[int, dict[int, str]]
        Class -> {neighbour class: ``"pendant"`` or ``"interior"``}.
    n_member_pairs : int
        One-edit pairs among members, before deduplication.
    """

    rep: dict[int, int]
    adj: dict[int, dict[int, str]]
    n_member_pairs: int

    def edge_counts(self) -> dict[str, int]:
        """Number of class-level edges of each kind."""
        counts: dict[str, int] = defaultdict(int)
        for a, nbrs in self.adj.items():
            for b, kind in nbrs.items():
                if a < b:
                    counts[kind] += 1
        return dict(counts)


def one_edit_graph(col: KBCollection) -> OneEditGraph:
    """Build the class-level one-edit graph of ``col`` from C8's ground truth.

    Raises
    ------
    DesignCError
        If two member pairs of the same class pair disagree on the edit kind.
    """
    from neardup import ground_truth

    iso, positives = ground_truth(col, "cert")
    rep: dict[int, int] = {}
    for i, cls in enumerate(iso.tolist()):
        rep.setdefault(int(cls), i)
    adj: dict[int, dict[int, str]] = defaultdict(dict)
    for (i, j), info in positives.items():
        a, b = int(iso[i]), int(iso[j])
        kind = "pendant" if info["pendant"] else "interior"
        if adj[a].get(b, kind) != kind:
            raise DesignCError(f"{col.name}: classes {a},{b} carry both edit kinds")
        adj[a][b] = kind
        adj[b][a] = kind
    return OneEditGraph(rep=rep, adj=dict(adj), n_member_pairs=len(positives))


def cached_eligible_classes(
    col: KBCollection, graph: OneEditGraph, keys: K.IsoKeys, out: Path, c: int = C_COPIES
) -> tuple[list[int], dict[str, Any]]:
    """:func:`eligible_classes`, cached per collection under ``<out>/eligibility/``.

    The set is a deterministic function of the collection, ``c`` and the
    constants below, so the three strata of a collection share one
    computation; the cache is keyed by them and rebuilt when they differ.
    """
    import json

    key = {"c": c, "r": list(RS), "seed": ELIGIBILITY_SEED, "n_classes": len(graph.adj)}
    path = out / "eligibility" / f"eligibility_{col.name}_c{c}.json"
    if path.exists():
        cached = json.loads(path.read_text())
        if cached.get("key") == key:
            return list(cached["eligible"]), {**cached["census"], "cache_hit": True}
    eligible, census = eligible_classes(col, graph, keys, c)
    K.write_json(path, {"key": key, "eligible": eligible, "census": census})
    return eligible, {**census, "cache_hit": False}


def eligible_classes(
    col: KBCollection, graph: OneEditGraph, keys: K.IsoKeys, c: int = C_COPIES
) -> tuple[list[int], dict[str, Any]]:
    """Classes of the graph whose representative is a valid Design-B source.

    A record is eligible when :func:`knn_lib.make_copies` returns ``c``
    pairwise non-isomorphic pendant copies at every ``r`` in ``RS`` under a
    fixed per-record seed (``ELIGIBILITY_SEED``), so the set is deterministic
    per collection.

    Returns
    -------
    tuple
        Sorted eligible classes and a census (counts, seconds).
    """
    t0 = time.perf_counter()
    eligible: list[int] = []
    for cls in sorted(graph.adj):
        rec = col.records[graph.rep[cls]]
        rng = np.random.default_rng(K.cell_seed(ELIGIBILITY_SEED, "C-elig", col.name, cls))
        cache = K.RemovalCache()
        if all(len(K.make_copies(rec, r, c, rng, keys, cache=cache)[0]) >= c for r in RS):
            eligible.append(cls)
    return eligible, {
        "n_classes_in_graph": len(graph.adj),
        "n_eligible": len(eligible),
        "secs": time.perf_counter() - t0,
    }


# --------------------------------------------------------------------------- blocks


def candidate_seeds(
    adj: dict[int, dict[int, str]], kinds: Sequence[str], available: set[int]
) -> list[int]:
    """Available classes with at least ``BLOCK_MIN - 1`` available neighbours of ``kinds``."""
    return sorted(
        v
        for v in available
        if sum(1 for u, k in adj.get(v, {}).items() if k in kinds and u in available)
        >= BLOCK_MIN - 1
    )


Accept = Callable[[list[int]], list[int] | None]


def draw_blocks(
    adj: dict[int, dict[int, str]],
    kinds: Sequence[str],
    eligible: Sequence[int],
    rng: np.random.Generator,
    *,
    s_target: int | None,
    accept: Accept | None = None,
) -> tuple[list[list[int]], int]:
    """Draw disjoint blocks: a uniform seed plus up to four uniform neighbours.

    Parameters
    ----------
    adj : dict
        Class-level one-edit graph.
    kinds : Sequence[str]
        Edit kinds a neighbour may have (the stratum).
    eligible : Sequence[int]
        Classes allowed in any block.
    rng : numpy.random.Generator
        The draw's own stream.
    s_target : int or None
        Stop once the blocks hold at least this many sources; ``None`` draws
        to exhaustion (the counting draw).
    accept : callable or None, optional
        Called on every drawn block (seed first); returns the members that
        survive (e.g. after copy generation) or ``None``. A block left with
        fewer than ``BLOCK_MIN`` members is discarded and counted. Its members
        stay used.

    Returns
    -------
    tuple
        The kept blocks (seed first) and the number discarded.
    """
    available = set(eligible) & set(adj)
    blocks: list[list[int]] = []
    discarded = 0
    total = 0
    while s_target is None or total < s_target:
        cands = candidate_seeds(adj, kinds, available)
        if not cands:
            break
        v = cands[int(rng.integers(len(cands)))]
        nbrs = sorted(u for u, k in adj[v].items() if k in kinds and u in available)
        pick = rng.choice(len(nbrs), size=min(BLOCK_NEIGHBOURS, len(nbrs)), replace=False)
        block = [v] + [nbrs[int(i)] for i in sorted(pick)]
        available.difference_update(block)
        kept = accept(block) if accept is not None else block
        if kept is None or len(kept) < BLOCK_MIN:
            discarded += 1
            continue
        blocks.append(kept)
        total += len(kept)
    return blocks, discarded


def member_copies(
    record: KBRecord, cls: int, seed: int, keys: K.IsoKeys, collection: str, c: int = C_COPIES
) -> dict[int, list[KBRecord]] | None:
    """Design-B copies of one block member at every ``r``; ``None`` if a draw falls short."""
    rng = np.random.default_rng(K.cell_seed(seed, "C-copies", collection, cls))
    cache = K.RemovalCache()
    out: dict[int, list[KBRecord]] = {}
    for r in RS:
        got, _ = K.make_copies(record, r, c, rng, keys, cache=cache)
        if len(got) < c:
            return None
        out[r] = got
    return out


@dataclass
class Pool:
    """The evaluated pool of one seed."""

    blocks: list[list[int]]
    copies: dict[int, dict[int, list[KBRecord]]]
    discarded_blocks: int
    dropped_members: list[int]
    secs: float
    c: int = C_COPIES


def build_pool(
    col: KBCollection,
    graph: OneEditGraph,
    eligible: Sequence[int],
    stratum: str,
    seed: int,
    keys: K.IsoKeys,
    c: int = C_COPIES,
) -> Pool:
    """Draw the evaluated blocks of one seed and the copies of their members."""
    t0 = time.perf_counter()
    copies: dict[int, dict[int, list[KBRecord]]] = {}
    dropped: list[int] = []

    def accept(block: list[int]) -> list[int]:
        kept = []
        for cls in block:
            got = member_copies(col.records[graph.rep[cls]], cls, seed, keys, col.name, c)
            if got is None:
                dropped.append(cls)
                continue
            copies[cls] = got
            kept.append(cls)
        return kept

    rng = np.random.default_rng(K.cell_seed(seed, "C-pool", col.name, stratum))
    blocks, discarded = draw_blocks(
        graph.adj, STRATA[stratum], eligible, rng, s_target=S_TARGET, accept=accept
    )
    return Pool(blocks, copies, discarded, dropped, time.perf_counter() - t0, c)


def count_blocks(
    graph: OneEditGraph, eligible: Sequence[int], stratum: str, seed: int, collection: str
) -> int:
    """Disjoint blocks reachable by drawing to exhaustion (the feasibility statistic)."""
    rng = np.random.default_rng(K.cell_seed(seed, "C-count", collection, stratum))
    blocks, _ = draw_blocks(graph.adj, STRATA[stratum], eligible, rng, s_target=None)
    return len(blocks)


# --------------------------------------------------------------------------- evaluation


def evaluate_pool(
    col: KBCollection,
    graph: OneEditGraph,
    pool: Pool,
    r: int,
    keys: K.IsoKeys,
    seed: int,
    stratum: str,
    n_jobs: int,
    arm_set: str = "c",
) -> dict[str, Any]:
    """Every arm's scores on the copies of the pool at ``r`` (arms of ``knn_lib.ARM_SETS``)."""
    arms, competitors = K.ARM_SETS[arm_set]
    t0 = time.perf_counter()
    members = [cls for block in pool.blocks for cls in block]
    block_of = np.array([b for b, block in enumerate(pool.blocks) for _ in block])
    items = [cp for cls in members for cp in pool.copies[cls][r]]
    codes = np.repeat(np.arange(len(members)), pool.c)
    iso_class, disagreements = K.iso_classes(items, keys)
    out: dict[str, Any] = {
        "r": r,
        "n_items": len(items),
        "S": len(members),
        "iso_census": {
            "n_iso_classes": int(len(np.unique(iso_class))),
            "key_disagreements": disagreements,
            **K.cross_class_iso(iso_class, codes),
            "exact_arm_acc1_ceiling": K.exact_arm_ceiling(iso_class, codes),
        },
        "arms": {},
    }
    mats, secs = K.build_matrices(
        items, arms, n_types=col.n_types, n_preds=col.n_preds, n_jobs=n_jobs
    )
    pam_seed = K.cell_seed(seed, "C-pam", col.name, stratum, r)
    p_correct: dict[str, np.ndarray] = {}
    for arm, M in mats.items():
        res = K.evaluate_arm(
            M,
            codes,
            k_clusters=len(members),
            pam_seed=pam_seed,
            iso_class=iso_class,
            class_groups=block_of,
        )
        res["secs_matrix"] = secs[arm]
        res["medoid_ids"] = [items[i].kb_id for i in res.pop("medoid_ids_idx", [])]
        p_correct[arm] = res.pop("_p_correct1")
        res.pop("_p_correct5")
        res["p_correct1"] = [round(float(x), 6) for x in p_correct[arm]]
        out["arms"][arm] = res
    out["ceiling"] = K.ceiling_census(p_correct, (K.OURS, *competitors))
    out["pam_seed"] = pam_seed
    out["secs"] = time.perf_counter() - t0
    return out


def block_record(graph: OneEditGraph, col: KBCollection, block: list[int]) -> dict[str, Any]:
    """JSON view of one block: member ids, sizes, and each neighbour's edit kind to the seed."""
    seed = block[0]
    return {
        "classes": block,
        "kb_ids": [col.records[graph.rep[c]].kb_id for c in block],
        "n": [col.records[graph.rep[c]].n for c in block],
        "m": [col.records[graph.rep[c]].m for c in block],
        "kinds_to_seed": [graph.adj[seed][c] for c in block[1:]],
    }


def run_seed(
    col: KBCollection,
    graph: OneEditGraph,
    eligible: Sequence[int],
    stratum: str,
    seed: int,
    keys: K.IsoKeys,
    n_jobs: int,
    c: int = C_COPIES,
    arm_set: str = "c",
) -> dict[str, Any]:
    """Counting draw, pool draw, and the three ``r`` cells of one seed."""
    t0 = time.perf_counter()
    n_available = count_blocks(graph, eligible, stratum, seed, col.name)
    pool = build_pool(col, graph, eligible, stratum, seed, keys, c)
    payload: dict[str, Any] = {
        "seed": seed,
        "count_seed": K.cell_seed(seed, "C-count", col.name, stratum),
        "pool_seed": K.cell_seed(seed, "C-pool", col.name, stratum),
        "n_blocks_available": n_available,
        "feasible_seed": n_available >= MIN_FEASIBLE_BLOCKS,
        "n_blocks": len(pool.blocks),
        "S": sum(len(b) for b in pool.blocks),
        "blocks": [block_record(graph, col, b) for b in pool.blocks],
        "discarded_blocks": pool.discarded_blocks,
        "dropped_members": pool.dropped_members,
        "secs_pool": pool.secs,
        "cells": {},
    }
    if len(pool.blocks) >= 2:
        for r in RS:
            payload["cells"][str(r)] = evaluate_pool(
                col, graph, pool, r, keys, seed, stratum, n_jobs, arm_set
            )
    payload["secs_seed"] = time.perf_counter() - t0
    return payload


# --------------------------------------------------------------------------- job


def run_job(
    collection: str,
    stratum: str,
    seeds: Sequence[int],
    out: Path,
    n_jobs: int,
    c: int = C_COPIES,
    arm_set: str = "c",
) -> Path:
    """Run every requested seed of one ``(collection, stratum, c)`` job; resume from disk."""
    import json

    if stratum not in STRATA:
        raise DesignCError(f"unknown stratum {stratum!r}; expected one of {sorted(STRATA)}")
    arms, competitors = K.ARM_SETS[arm_set]
    path = out / f"C_{collection}_{stratum}_c{c}.json"
    payload: dict[str, Any]
    if path.exists():
        payload = json.loads(path.read_text())
        stored = payload.get("config", {}).get("arms")
        if stored is not None and stored != list(arms):
            raise DesignCError(f"{path} was run with arms {stored}, asked for {list(arms)}")
    else:
        payload = {"collection": collection, "stratum": stratum, "c": c, "seeds": {}}
    t0 = time.perf_counter()
    col = C.load_collection(collection)
    keys = K.IsoKeys(col.n_types, col.n_preds)
    graph = one_edit_graph(col)
    eligible, elig_census = cached_eligible_classes(col, graph, keys, out, c)
    kinds = STRATA[stratum]
    payload.update(
        {
            "design": "C",
            "c": c,
            "role": "primary" if c == C_COPIES else "secondary (registered c = 6)",
            "config": {
                "S_target": S_TARGET,
                "c": c,
                "r": list(RS),
                "block_neighbours": BLOCK_NEIGHBOURS,
                "block_min": BLOCK_MIN,
                "min_feasible_blocks": MIN_FEASIBLE_BLOCKS,
                "eligibility_seed": ELIGIBILITY_SEED,
                "kinds": list(kinds),
                "arm_set": arm_set,
                "arms": list(arms),
                "competitors": list(competitors),
                "n_jobs": n_jobs,
            },
            "graph": {
                "n_member_pairs": graph.n_member_pairs,
                "n_classes_in_graph": len(graph.adj),
                "edges": graph.edge_counts(),
            },
            "eligibility": elig_census,
            "eligible_classes": eligible,
            "n_candidate_block_seeds": len(candidate_seeds(graph.adj, kinds, set(eligible))),
            "secs_setup": time.perf_counter() - t0,
        }
    )
    for seed in seeds:
        if str(seed) in payload["seeds"]:
            logger.info("%s %s seed %d on disk, skipped", collection, stratum, seed)
            continue
        res = run_seed(col, graph, eligible, stratum, seed, keys, n_jobs, c, arm_set)
        payload["seeds"][str(seed)] = res
        K.write_json(path, payload)
        _log_seed(collection, stratum, res, competitors)
    K.write_json(path, payload)
    return path


def _log_seed(
    collection: str, stratum: str, res: dict[str, Any], competitors: Sequence[str]
) -> None:
    parts = []
    for r, cell in res["cells"].items():
        w = cell["arms"][K.OURS]
        b_acc = K.best_competitor(cell["arms"], "acc1", competitors)
        b_ari = K.best_competitor(cell["arms"], "ari", competitors)
        parts.append(
            f"r{r}: w° {w['acc1']:.3f}/{w['ari']:.3f} vs {b_acc[0]} {b_acc[1]:.3f} / "
            f"{b_ari[0]} {b_ari[1]:.3f}"
        )
    logger.info(
        "%s %s seed %s: available %d blocks, pool %d blocks S=%d (%.1f s) | %s",
        collection,
        stratum,
        res["seed"],
        res["n_blocks_available"],
        res["n_blocks"],
        res["S"],
        res["secs_seed"],
        " | ".join(parts),
    )


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--collection", required=True, choices=list(K.COLLECTIONS))
    ap.add_argument("--stratum", required=True, choices=list(STRATA))
    ap.add_argument("--seeds", nargs="+", type=int, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument(
        "--n-jobs",
        type=int,
        default=int(os.environ.get("SLURM_CPUS_PER_TASK", os.cpu_count() or 1)),
    )
    ap.add_argument(
        "--copies",
        type=int,
        default=C_COPIES,
        choices=[C_COPIES, C_SECONDARY],
        help="copies per member: 3 (primary, LOG.md §6.1) or 6 (the registered secondary)",
    )
    ap.add_argument(
        "--arm-set",
        choices=["c", "full"],
        default="c",
        help="c: the §6 arms (probe); full: LOG.md §8 (symmetric-min edit path as the verdict "
        "arm, the as-run path as a reported row)",
    )
    args = ap.parse_args()
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(name)s %(message)s", datefmt="%H:%M:%S"
    )
    for noisy in ("isalhg", "experiments"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    args.out.mkdir(parents=True, exist_ok=True)
    path = run_job(
        args.collection, args.stratum, args.seeds, args.out, args.n_jobs, args.copies, args.arm_set
    )
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
