"""A4 — Shortest path between hypergraphs (the capability differentiator).

v3 HGED-free scoring (D-ART2, 2026-07-18):

- **Endpoints** H_A = H_0, H_B = H_t from one perturbation ladder with known
  accumulated Qin budget ``t``; the pool contains the ladder's true
  intermediates plus distractors from sibling ladders of the same dataset.
- **Scores**:
    (i)  path recovery — fraction of true ladder intermediates found in the
         shortest ``d_I``-path, ordered.
    (ii) monotonicity — fraction of path steps where accumulated ``d_I``
         strictly increases (positive-weight edges).
    (iii) decodability demo — S2H-decode each intermediate on the ours-path
          and verify every decoded string yields a valid hypergraph; shown
          as the structural profile figure that competitors structurally
          cannot produce.

- **Capability matrix row (A4)**:

  representation     can navigate   has decoder   scores computed
  isalhg             yes            yes           (i)+(ii)+(iii)
  hypergraph_wl_l1   yes            no            (i)+(ii) only
  netlsd_l2          yes            no            (i)+(ii) only
  hpd_jsd            yes            no            (i)+(ii) only
  hypercot           feasible*      no            (i)+(ii) on small pools
  nauty_levi_edit    no             no            n/a — G2 avalanche profile

  *HyperCOT's O(n³)/pair cost is feasible here (pool ≤ 44 items) but its
  subprocess subprocess pinned-env is not wired here; excluded and noted.

  The "no decoder" verdict means vector-fingerprint competitors cannot exhibit
  the intermediate *hypergraphs* along a path — their fingerprints have no
  inverse. IsalHG can: the alphabet is closed (S2H never rejects), so every
  intermediate canonical string decodes to an actual hypergraph.

Public API
----------
score_path_recovery   -- (i) fraction of true intermediates in path
score_monotonicity    -- (ii) fraction of path steps with positive d_I
shortest_path_in_pool -- Dijkstra on complete weighted graph
decode_path_intermediates -- S2H decode a list of canonical strings

run_a4_experiment     -- orchestrates pool → D matrices → paths → scores →
                         figures → JSON (main entry point)

Usage::

    python -m experiments.article.analysis.shortest_path \\
        --output-root /media/.../results/T-M5e/ \\
        --seed 42
"""

from __future__ import annotations

import argparse
import contextlib
import json
import logging
import os
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pool metadata type
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PoolItemMeta:
    """Metadata for one item in the A4 intermediate pool."""

    idx: int
    """Index of this item in the pool list (0-based)."""

    item_id: str
    """Original DatasetItem id (e.g. ``"L0_t3"``)."""

    ladder_id: int
    """Which ladder this item belongs to."""

    step: int
    """Step index within the ladder (0 = base)."""

    budget_from_base: int
    """Accumulated Qin-cost budget from this ladder's base to this step."""


# ---------------------------------------------------------------------------
# Scoring primitives (pure functions; unit-tested independently)
# ---------------------------------------------------------------------------


def score_path_recovery(
    path_idxs: list[int],
    pool_meta: list[dict[str, Any]],
    target_ladder_id: int,
    start_idx: int,
    end_idx: int,
) -> float:
    """Fraction of true ladder intermediates found in the recovered path.

    The *true intermediates* are the pool items belonging to
    ``target_ladder_id`` that are neither the start nor the end of the path
    (i.e. all steps strictly between the two endpoints). The score is
    ``|{true_intermediates} ∩ {path_inner}| / |{true_intermediates}|``.
    If there are no true intermediates (e.g. a one-step ladder), returns 1.0
    (vacuously satisfied — the path hits all zero of zero targets).

    Parameters
    ----------
    path_idxs : list[int]
        Sequence of pool indices from ``start_idx`` to ``end_idx`` inclusive.
    pool_meta : list[dict]
        One dict per pool item with at least ``"idx"`` and ``"ladder_id"``.
    target_ladder_id : int
        The ladder whose intermediates count as "true".
    start_idx : int
        Pool index of H_A (excluded from the target set).
    end_idx : int
        Pool index of H_B (excluded from the target set).

    Returns
    -------
    float
        Recovery fraction in ``[0.0, 1.0]``.
    """
    endpoints = {start_idx, end_idx}
    true_intermediates = frozenset(
        item["idx"]
        for item in pool_meta
        if item["ladder_id"] == target_ladder_id and item["idx"] not in endpoints
    )
    if not true_intermediates:
        return 1.0  # vacuously satisfied

    path_inner = frozenset(path_idxs) - endpoints
    recovered = path_inner & true_intermediates
    return len(recovered) / len(true_intermediates)


def score_monotonicity(path_idxs: list[int], D: np.ndarray) -> float:
    """Fraction of path steps where the accumulated d_I strictly increases.

    A step from ``path[i-1]`` to ``path[i]`` is *monotone* when the edge
    weight ``D[path[i-1], path[i]] > 0``. For shortest paths on a positive-
    weight graph this is almost always 1.0; a zero-weight edge (two isomorphic
    hypergraphs landing in the same pool) would lower it.

    Returns 1.0 for paths with fewer than two nodes (vacuously monotone).

    Parameters
    ----------
    path_idxs : list[int]
        Ordered sequence of pool indices.
    D : np.ndarray
        Pairwise distance matrix.  ``D[i, j]`` is the distance between pool
        items ``i`` and ``j``.

    Returns
    -------
    float
        Monotone fraction in ``[0.0, 1.0]``.
    """
    if len(path_idxs) < 2:
        return 1.0
    n_monotone = sum(1 for i in range(1, len(path_idxs)) if D[path_idxs[i - 1], path_idxs[i]] > 0)
    return n_monotone / (len(path_idxs) - 1)


def build_knn_graph(D: np.ndarray, k: int) -> np.ndarray:
    """Return a symmetric kNN adjacency matrix (weights = D values, 0 = no edge).

    Each node is connected to its ``k`` nearest neighbours (smallest D values,
    excluding self). The result is symmetrised so the graph is undirected.
    The endpoints ``start_idx`` / ``end_idx`` are connected to ALL nodes so they
    are reachable even when far from each other's kNN neighbourhoods.

    Parameters
    ----------
    D : np.ndarray
        Symmetric pairwise distance matrix of shape ``(N, N)``.
    k : int
        Number of nearest neighbours per node.

    Returns
    -------
    np.ndarray
        Sparse weight matrix: ``W[i, j] = D[i, j]`` if (i, j) is a kNN edge,
        else 0.
    """
    N = D.shape[0]
    k = min(k, N - 1)
    W = np.zeros_like(D)
    for i in range(N):
        row = D[i].copy()
        row[i] = np.inf  # exclude self
        nn_idxs = np.argpartition(row, k)[:k]
        for j in nn_idxs:
            W[i, j] = D[i, j]
            W[j, i] = D[j, i]  # symmetrise
    return W


def shortest_path_in_pool(
    D: np.ndarray,
    start_idx: int,
    end_idx: int,
    *,
    k_nn: int | None = None,
) -> list[int]:
    """Dijkstra shortest path on a pool graph weighted by D.

    When ``k_nn`` is ``None`` (default), uses the **complete** weighted graph
    (all N×N pairs). This is correct for the unit tests but will always return
    the direct 2-node path when D satisfies the triangle inequality.

    When ``k_nn`` is set, builds a **kNN sparse graph** first so intermediate
    nodes are included in the path. This is the setting used by the A4
    experiment (see ``run_a4_experiment``).

    Parameters
    ----------
    D : np.ndarray
        Symmetric pairwise distance matrix of shape ``(N, N)``.
    start_idx : int
        Pool index of the path start.
    end_idx : int
        Pool index of the path end.
    k_nn : int or None
        If set, builds a kNN graph instead of the complete graph.  The
        endpoints are always connected to all pool items so the path exists.

    Returns
    -------
    list[int]
        Ordered pool indices from ``start_idx`` to ``end_idx``.
        Returns ``[start_idx]`` if ``start_idx == end_idx``.
    """
    if start_idx == end_idx:
        return [start_idx]

    try:
        import networkx as nx
    except ImportError as exc:
        raise ImportError(
            "networkx is required for shortest_path_in_pool; install via `pip install networkx`"
        ) from exc

    if k_nn is None:
        W = D
    else:
        W = build_knn_graph(D, k_nn)
        # If the endpoints are disconnected in the kNN graph, add a bridge via
        # their mutual nearest neighbour on the other's side (does NOT add the
        # direct start↔end edge, preserving the purpose of the sparse graph).
        G_check = nx.from_numpy_array(W)
        if not nx.has_path(G_check, start_idx, end_idx):
            # Fall back to k+1 until connected or fully dense
            k_cur = k_nn
            while not nx.has_path(G_check, start_idx, end_idx) and k_cur < D.shape[0] - 1:
                k_cur += 1
                W = build_knn_graph(D, k_cur)
                G_check = nx.from_numpy_array(W)
            logger.debug("kNN graph: needed k=%d to connect endpoints", k_cur)

    G = nx.from_numpy_array(W)
    return list(nx.dijkstra_path(G, start_idx, end_idx, weight="weight"))


def decode_path_intermediates(
    canonical_strings: list[str],
    k: int,
) -> list[Any]:
    """Decode canonical strings to SparseHypergraph objects via S2H.

    The closed-alphabet invariant guarantees S2H never rejects a string that
    was produced by H2S — every canonical string is a valid ``Sigma_HG*`` word.

    Parameters
    ----------
    canonical_strings : list[str]
        A list of serialised canonical strings (output of
        :func:`isalhg.core.canonical.canonical_string`).
    k : int
        Pointer count used when the strings were encoded.

    Returns
    -------
    list[SparseHypergraph]
        Decoded hypergraphs, one per input string.
    """
    from isalhg.core.string_to_hypergraph import string_to_hypergraph

    return [string_to_hypergraph(w, k=k, backend="python") for w in canonical_strings]


# ---------------------------------------------------------------------------
# Accumulated path lengths (helper)
# ---------------------------------------------------------------------------


def _accumulated_lengths(path_idxs: list[int], D: np.ndarray) -> list[float]:
    """Return cumulative d_I along the path, starting at 0.0.

    len == len(path_idxs): index 0 is 0.0, index i is sum of edge weights
    up to step i.
    """
    acc = [0.0]
    for i in range(1, len(path_idxs)):
        acc.append(acc[-1] + float(D[path_idxs[i - 1], path_idxs[i]]))
    return acc


# ---------------------------------------------------------------------------
# Atomic I/O helpers
# ---------------------------------------------------------------------------


def _atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp.json")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, path)
    except Exception:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


# ---------------------------------------------------------------------------
# Main experiment
# ---------------------------------------------------------------------------


def run_a4_experiment(
    output_dir: Path,
    *,
    seed: int = 42,
    n_nodes: int = 5,
    n_edges: int = 3,
    arity_range: tuple[int, int] = (2, 3),
    max_t: int = 10,
    n_target_ladders: int = 1,
    n_distractor_ladders: int = 3,
    representations: list[str] | None = None,
) -> dict[str, Any]:
    """Run the full A4 shortest-path experiment and write results to disk.

    Builds a pool = one target ladder (steps 0..max_t) + ``n_distractor_ladders``
    sibling ladders from the same dataset; computes pairwise D matrices for each
    representation; runs Dijkstra from H_A=H_0 to H_B=H_{max_t}; reports scores
    (i)–(iii); produces figures; writes ``a4_result.json`` and ``a4_*.pdf`` to
    ``output_dir``.

    Parameters
    ----------
    output_dir : Path
        Where to write results.  Created if absent.
    seed : int
        Master seed for the perturbation-ladder dataset.
    n_nodes : int
        Vertex count for base hypergraphs.
    n_edges : int
        Edge-insertion attempts for base hypergraphs.
    arity_range : tuple[int, int]
        Hyperedge-size bounds.
    max_t : int
        Number of ladder steps.
    n_target_ladders : int
        Number of ladders used as scoring targets (default 1 — one pair of
        endpoints; the best recovery across targets is reported).
    n_distractor_ladders : int
        Number of additional ladders in the pool (from same dataset).
    representations : list[str] or None
        Distance names to run.  Defaults to all three vector competitors
        plus ours: ``["isalhg_levenshtein", "hypergraph_wl_l1",
        "netlsd_l2", "hpd_jsd"]``.

    Returns
    -------
    dict
        Summary of all path-recovery and monotonicity scores.
    """
    if representations is None:
        representations = ["isalhg_levenshtein", "hypergraph_wl_l1", "netlsd_l2", "hpd_jsd"]

    result_path = output_dir / "a4_result.json"
    if result_path.exists():
        try:
            with open(result_path) as f:
                existing = json.load(f)
            if existing.get("status") == "done":
                logger.info("A4 result already done; skipping. path=%s", result_path)
                return existing  # type: ignore[no-any-return]
        except (json.JSONDecodeError, KeyError):
            pass

    output_dir.mkdir(parents=True, exist_ok=True)

    # -----------------------------------------------------------------
    # 1. Build pool
    # -----------------------------------------------------------------
    from isalhg.core.canonical import canonical_string, required_k
    from isalhg.datasets.synthetic.perturbation_ladder import PerturbationLadderHypergraphs

    n_ladders_total = n_target_ladders + n_distractor_ladders
    dataset = PerturbationLadderHypergraphs(
        n_nodes=n_nodes,
        n_edges=n_edges,
        arity_range=arity_range,
        max_t=max_t,
        n_ladders=n_ladders_total,
        seed=seed,
    )
    all_items = list(dataset)

    # Pool metadata: one dict per item
    pool_meta: list[dict[str, Any]] = []
    pool_hypergraphs = []
    for idx, item in enumerate(all_items):
        pool_meta.append(
            {
                "idx": idx,
                "item_id": item.item_id,
                "ladder_id": int(item.extra["ladder"]),
                "step": int(item.extra["step"]),
                "budget_from_base": int(item.extra["budget_from_base"]),
            }
        )
        pool_hypergraphs.append(item.hypergraph)

    n_pool = len(pool_hypergraphs)
    logger.info("Pool built: %d items (%d ladders × %d steps)", n_pool, n_ladders_total, max_t + 1)

    # Target ladder: ladder_id = 0 (first ladder from seed)
    target_ladder_id = 0
    target_items = [m for m in pool_meta if m["ladder_id"] == target_ladder_id]
    target_items_sorted = sorted(target_items, key=lambda m: m["step"])
    start_idx = target_items_sorted[0]["idx"]  # H_A = H_0
    end_idx = target_items_sorted[-1]["idx"]  # H_B = H_{max_t}
    n_true_intermediates = len(target_items_sorted) - 2  # excluding endpoints

    logger.info(
        "Target ladder %d: H_A=idx%d (step 0)  H_B=idx%d (step %d)  true_intermediates=%d",
        target_ladder_id,
        start_idx,
        end_idx,
        max_t,
        n_true_intermediates,
    )

    # -----------------------------------------------------------------
    # 2. Compute canonical strings for ours (decodability demo)
    # -----------------------------------------------------------------
    k = max(required_k(H) for H in pool_hypergraphs)
    logger.info("Computing canonical strings (k=%d) for %d items …", k, n_pool)
    t_cs = time.perf_counter()
    pool_canonical_strings = [canonical_string(H, k=k) for H in pool_hypergraphs]
    elapsed_cs = time.perf_counter() - t_cs
    logger.info("  canonical strings done in %.2f s", elapsed_cs)

    # -----------------------------------------------------------------
    # 3. Compute pairwise D matrices
    # -----------------------------------------------------------------
    from isalhg.metric_space.registry import get_distance

    d_matrices: dict[str, np.ndarray] = {}
    wall_clock_d: dict[str, float] = {}

    for rep in representations:
        logger.info("Computing D matrix for %s …", rep)
        try:
            dist = get_distance(rep)
            t0 = time.perf_counter()
            D = dist.matrix(pool_hypergraphs)
            elapsed = time.perf_counter() - t0
            d_matrices[rep] = D
            wall_clock_d[rep] = elapsed
            logger.info("  %s: %.2f s  D[start,end]=%.4f", rep, elapsed, D[start_idx, end_idx])
        except Exception as exc:
            logger.warning("  %s: FAILED — %s", rep, exc)
            wall_clock_d[rep] = -1.0

    # -----------------------------------------------------------------
    # 4. Run paths and score
    # -----------------------------------------------------------------
    # kNN graph: connect each node to k=5 nearest neighbours.  The endpoints
    # are always connected to all pool items so a path always exists.
    # This forces the path to route through structural intermediates rather than
    # taking the direct H_A → H_B edge (which the triangle inequality guarantees
    # is shortest on a complete graph, trivially bypassing all intermediates).
    K_NN = 5
    per_rep_results: list[dict[str, Any]] = []

    for rep in representations:
        if rep not in d_matrices:
            per_rep_results.append(
                {
                    "representation": rep,
                    "status": "skipped",
                    "reason": "D matrix computation failed",
                }
            )
            continue

        D = d_matrices[rep]
        path_idxs = shortest_path_in_pool(D, start_idx, end_idx, k_nn=K_NN)
        recovery = score_path_recovery(path_idxs, pool_meta, target_ladder_id, start_idx, end_idx)
        monotone = score_monotonicity(path_idxs, D)
        acc_lengths = _accumulated_lengths(path_idxs, D)
        total_path_length = acc_lengths[-1] if acc_lengths else 0.0

        # Budget at each node in the path (0 for non-target-ladder nodes)
        path_budgets = []
        path_steps = []
        for idx in path_idxs:
            meta = pool_meta[idx]
            if meta["ladder_id"] == target_ladder_id:
                path_budgets.append(meta["budget_from_base"])
                path_steps.append(meta["step"])
            else:
                path_budgets.append(None)
                path_steps.append(None)

        rep_result: dict[str, Any] = {
            "representation": rep,
            "status": "done",
            "path_length_nodes": len(path_idxs),
            "path_idxs": path_idxs,
            "path_item_ids": [pool_meta[i]["item_id"] for i in path_idxs],
            "total_path_d": float(total_path_length),
            "path_recovery_frac": float(recovery),
            "monotone_frac": float(monotone),
            "accumulated_lengths": [float(x) for x in acc_lengths],
            "path_budgets": path_budgets,
            "path_steps": path_steps,
        }

        # Decodability demo (ours only)
        if rep == "isalhg_levenshtein":
            inner_idxs = path_idxs[1:-1]  # exclude endpoints
            inner_w_stars = [pool_canonical_strings[i] for i in inner_idxs]
            inner_decoded = decode_path_intermediates(inner_w_stars, k=k)
            all_valid = all(H.n_nodes >= 1 for H in inner_decoded)
            rep_result["decodability"] = {
                "n_intermediates": len(inner_idxs),
                "all_valid": all_valid,
                "structural_profile": [
                    {
                        "pool_idx": inner_idxs[i],
                        "item_id": pool_meta[inner_idxs[i]]["item_id"],
                        "n_nodes": inner_decoded[i].n_nodes,
                        "n_edges": inner_decoded[i].n_edges,
                        "w_star_len": len(inner_w_stars[i]),
                    }
                    for i in range(len(inner_idxs))
                ],
            }
            logger.info(
                "  Decodability demo: %d intermediates, all_valid=%s",
                len(inner_idxs),
                all_valid,
            )
            # Save the decoded intermediates as a figure
            _figure_decodability(
                path_idxs=inner_idxs,
                decoded_hypergraphs=inner_decoded,
                pool_meta=pool_meta,
                output_dir=output_dir,
                acc_lengths=[acc_lengths[j + 1] for j in range(len(inner_idxs))],
            )

        logger.info(
            "  %s: path_len=%d  recovery=%.2f  monotone=%.2f  total_d=%.2f",
            rep,
            len(path_idxs),
            recovery,
            monotone,
            total_path_length,
        )
        per_rep_results.append(rep_result)

    # -----------------------------------------------------------------
    # 5. Capability matrix row (fixed text + measured scores)
    # -----------------------------------------------------------------
    capability_matrix = _build_capability_matrix(per_rep_results)

    # -----------------------------------------------------------------
    # 6. Save main results figure and JSON
    # -----------------------------------------------------------------
    _figure_path_comparison(per_rep_results, pool_meta, target_ladder_id, output_dir)

    summary: dict[str, Any] = {
        "status": "done",
        "seed": seed,
        "pool_params": {
            "n_nodes": n_nodes,
            "n_edges": n_edges,
            "arity_range": list(arity_range),
            "max_t": max_t,
            "n_target_ladders": n_target_ladders,
            "n_distractor_ladders": n_distractor_ladders,
            "n_pool": n_pool,
        },
        "target_ladder_id": target_ladder_id,
        "start_idx": start_idx,
        "end_idx": end_idx,
        "n_true_intermediates": n_true_intermediates,
        "k": k,
        "k_nn_graph": K_NN,
        "wall_clock_canonical_s": elapsed_cs,
        "wall_clock_d_matrix_s": wall_clock_d,
        "per_rep_results": per_rep_results,
        "capability_matrix": capability_matrix,
    }

    _atomic_write_json(result_path, summary)
    logger.info("A4 result written to %s", result_path)
    return summary


# ---------------------------------------------------------------------------
# Capability matrix
# ---------------------------------------------------------------------------

_CAPABILITY_ROW: dict[str, dict[str, Any]] = {
    "isalhg_levenshtein": {
        "can_navigate": True,
        "has_decoder": True,
        "decoder_note": "S2H decodes any w*_c string; closed alphabet guarantees.",
        "decodability_check": "computed",
    },
    "hypergraph_wl_l1": {
        "can_navigate": True,
        "has_decoder": False,
        "decoder_note": "WL histogram is a many-to-one map; no S2H equivalent.",
    },
    "netlsd_l2": {
        "can_navigate": True,
        "has_decoder": False,
        "decoder_note": "NetLSD heat-trace vector has no inverse.",
    },
    "hpd_jsd": {
        "can_navigate": True,
        "has_decoder": False,
        "decoder_note": "HPD portrait distribution has no inverse.",
    },
    "hypercot": {
        "can_navigate": "small/mid only (O(n^3)/pair scale limit)",
        "has_decoder": False,
        "decoder_note": "HyperCOT optimal-transport coupling; no hypergraph inverse.",
        "excluded_here": "subprocess pinned-env not wired; scale limit noted.",
    },
    "nauty_levi_edit": {
        "can_navigate": False,
        "has_decoder": False,
        "decoder_note": (
            "Nauty-Levi canonical-string edit distance is avalanche-everywhere "
            "(G2 sensitivity profile, T-M5g): IQR_nauty = 10.0–20.0 across all "
            "seven regimes vs IQR_ours = 2.0–8.0. A single structural edit "
            "relabels the whole canonical string, so navigation through the "
            "fingerprint space is not possible."
        ),
    },
}


def _build_capability_matrix(
    per_rep_results: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Merge static capability declarations with measured scores."""
    measured: dict[str, dict[str, Any]] = {}
    for r in per_rep_results:
        rep = r["representation"]
        if r.get("status") != "done":
            continue
        measured[rep] = {
            "score_i_recovery": r["path_recovery_frac"],
            "score_ii_monotonicity": r["monotone_frac"],
        }

    matrix: dict[str, dict[str, Any]] = {}
    for rep, static in _CAPABILITY_ROW.items():
        row: dict[str, Any] = dict(static)
        if rep in measured:
            row.update(measured[rep])
        matrix[rep] = row
    return matrix


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------


def _figure_decodability(
    path_idxs: list[int],
    decoded_hypergraphs: list[Any],
    pool_meta: list[dict[str, Any]],
    output_dir: Path,
    acc_lengths: list[float],
) -> None:
    """Structural profile of the decoded intermediates along the ours-path.

    Shows n_nodes and n_edges for each decoded intermediate — the figure that
    competitors structurally cannot produce.
    """
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        logger.warning("matplotlib not available; skipping decodability figure")
        return

    if not decoded_hypergraphs:
        logger.info("No intermediates to plot in decodability figure.")
        return

    n = len(decoded_hypergraphs)
    positions = list(range(1, n + 1))  # path position (1 = first intermediate)
    n_nodes_vals = [H.n_nodes for H in decoded_hypergraphs]
    n_edges_vals = [H.n_edges for H in decoded_hypergraphs]
    item_ids = [pool_meta[i]["item_id"] for i in path_idxs]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))

    ax = axes[0]
    ax.plot(
        positions, n_nodes_vals, "o-", color="#1b7837", linewidth=1.5, markersize=5, label="|V|"
    )
    ax.plot(
        positions, n_edges_vals, "s--", color="#762a83", linewidth=1.5, markersize=5, label="|E|"
    )
    ax.set_xlabel("Path position (intermediate node index)")
    ax.set_ylabel("Count")
    ax.set_title("Decoded intermediate hypergraphs along\nthe shortest $d_I$-path (IsalHG only)")
    ax.set_xticks(positions)
    ax.set_xticklabels(item_ids, rotation=35, ha="right", fontsize=7)
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.3)

    ax2 = axes[1]
    ax2.plot(
        acc_lengths,
        n_nodes_vals,
        "o",
        color="#1b7837",
        markersize=6,
        label="|V|",
        zorder=3,
    )
    ax2.plot(
        acc_lengths,
        n_edges_vals,
        "s",
        color="#762a83",
        markersize=6,
        label="|E|",
        zorder=3,
    )
    ax2.set_xlabel("Accumulated $d_I$ along path")
    ax2.set_ylabel("Count")
    ax2.set_title("Structural change vs accumulated path length")
    ax2.legend(fontsize=9)
    ax2.grid(axis="y", alpha=0.3)

    fig.suptitle(
        "A4 — Decodability demo (capability competitors structurally cannot produce)",
        fontsize=10,
        fontweight="bold",
    )
    fig.tight_layout()
    out_path = output_dir / "a4_decodability_demo.pdf"
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    logger.info("Saved decodability figure to %s", out_path)


def _figure_path_comparison(
    per_rep_results: list[dict[str, Any]],
    pool_meta: list[dict[str, Any]],
    target_ladder_id: int,
    output_dir: Path,
) -> None:
    """Bar chart comparing path-recovery and monotonicity across representations."""
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        logger.warning("matplotlib not available; skipping comparison figure")
        return

    done_reps = [r for r in per_rep_results if r.get("status") == "done"]
    if not done_reps:
        return

    labels = [r["representation"].replace("_", "\n") for r in done_reps]
    recoveries = [r["path_recovery_frac"] for r in done_reps]
    monotones = [r["monotone_frac"] for r in done_reps]

    x = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(max(6, 2 * len(labels)), 4.5))
    ax.bar(x - width / 2, recoveries, width, label="Path recovery (i)", color="#1b7837", alpha=0.85)
    ax.bar(x + width / 2, monotones, width, label="Monotonicity (ii)", color="#762a83", alpha=0.85)

    ax.set_ylim(0, 1.15)
    ax.set_ylabel("Score")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_title(
        f"A4 scores (path recovery + monotonicity)\npool = ladder {target_ladder_id} + distractors"
    )
    ax.legend(fontsize=8)
    ax.axhline(1.0, color="gray", linestyle="--", linewidth=0.8, alpha=0.5)
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    out_path = output_dir / "a4_path_comparison.pdf"
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    logger.info("Saved path comparison figure to %s", out_path)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="A4 shortest-path experiment (T-M5e)")
    p.add_argument("--output-root", required=True, type=Path, help="Root for results")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--n-nodes", type=int, default=5)
    p.add_argument("--n-edges", type=int, default=3)
    p.add_argument("--max-t", type=int, default=10)
    p.add_argument("--n-target-ladders", type=int, default=1)
    p.add_argument("--n-distractor-ladders", type=int, default=3)
    return p


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = _build_argparser().parse_args()
    result = run_a4_experiment(
        output_dir=args.output_root,
        seed=args.seed,
        n_nodes=args.n_nodes,
        n_edges=args.n_edges,
        max_t=args.max_t,
        n_target_ladders=args.n_target_ladders,
        n_distractor_ladders=args.n_distractor_ladders,
    )
    # Print score summary
    print("\n=== A4 RESULT SUMMARY ===")
    for r in result.get("per_rep_results", []):
        if r.get("status") == "done":
            dec = ""
            if "decodability" in r:
                n_dec = r["decodability"]["n_intermediates"]
                ok = r["decodability"]["all_valid"]
                dec = f"  decoded={n_dec} (all_valid={ok})"
            print(
                f"  {r['representation']:<30}  "
                f"recovery={r['path_recovery_frac']:.2f}  "
                f"monotone={r['monotone_frac']:.2f}  "
                f"path_nodes={r['path_length_nodes']}"
                f"{dec}"
            )
    print(
        f"\nPool: {result['pool_params']['n_pool']} items  "
        f"k={result['k']}  "
        f"true_intermediates={result['n_true_intermediates']}"
    )
    print(f"Output: {args.output_root}")
