"""T-M5a article experiment runner.

Dispatches cells from a YAML config, computes results, and caches them
atomically under the configured output_root.

Usage (local, all cells)::

    python -m experiments.article.runner \\
        --config experiments/article/configs/local_smoke.yaml \\
        --output-root /media/.../results/T-M5a/

Usage (SLURM array, one cell per task)::

    python -m experiments.article.runner \\
        --config experiments/article/configs/e1_correlation.yaml \\
        --output-root /media/.../results/T-M5a/ \\
        --cell-index $SLURM_ARRAY_TASK_ID

Usage (count cells for array sizing)::

    python -m experiments.article.runner --config ... --count

Outputs (never written to the git tree):

- ``{output_root}/{cell.output_key()}/{distance}/D.npy``        (d_matrix)
- ``{output_root}/{cell.output_key()}/{distance}/meta.json``    (d_matrix)
- ``{output_root}/{cell.output_key()}/sensitivity.json``        (sensitivity)
- ``{output_root}/{cell.output_key()}/ladder.json``             (ladder)
- ``{output_root}/{cell.output_key()}/info_content.json``       (info_content)
"""

from __future__ import annotations

import argparse
import contextlib
import json
import logging
import os
import random
import tempfile
import time
from pathlib import Path
from typing import Any

import numpy as np

from experiments.article.schemas import ArticleConfig, CellSpec

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dataset factory
# ---------------------------------------------------------------------------


def _build_dataset(cell: CellSpec):  # noqa: ANN202
    """Instantiate a HypergraphDataset from *cell*.

    The seed from *cell* is injected as the ``seed`` kwarg so each cell is
    independently reproducible.
    """
    name = cell.dataset
    params: dict[str, Any] = {**cell.dataset_params, "seed": cell.seed}

    if name == "correlation_corpus":
        from isalhg.datasets.synthetic.correlation_corpus import CorrelationCorpusHypergraphs

        # Strip runner-specific keys that are not dataset constructor params.
        # n_edits_per_h belongs to run_sensitivity_cell, not to the dataset.
        corpus_params = {k: v for k, v in params.items() if k != "n_edits_per_h"}
        return CorrelationCorpusHypergraphs(**corpus_params)
    if name == "perturbation_ladder":
        from isalhg.datasets.synthetic.perturbation_ladder import PerturbationLadderHypergraphs

        # Strip G2-runner-specific keys that are not dataset constructor params.
        _ladder_strip = {"n_edits_per_h", "max_arity"}
        ladder_params = {k: v for k, v in params.items() if k not in _ladder_strip}
        return PerturbationLadderHypergraphs(**ladder_params)
    if name == "erdos_renyi":
        from isalhg.datasets.synthetic.erdos_renyi import ErdosRenyiHypergraphs

        return ErdosRenyiHypergraphs(**params)
    # Fallback to registry for future datasets
    from isalhg.datasets.registry import get_dataset

    return get_dataset(name, params)


# ---------------------------------------------------------------------------
# Distance factory
# ---------------------------------------------------------------------------


def _build_distance(name: str, params: dict[str, Any]):  # noqa: ANN202
    """Instantiate a HypergraphDistance from *name* and constructor *params*."""
    if name == "isalhg_levenshtein":
        from isalhg.metric_space.distances.isalhg_levenshtein import IsalHGLevenshtein

        return IsalHGLevenshtein(**params)
    if name == "exact_hged":
        from isalhg.metric_space.distances.hged import ExactHGED

        return ExactHGED(**params)
    if name == "bipartite_hged":
        from isalhg.metric_space.distances.hged import BipartiteHGED

        return BipartiteHGED(**params)
    if name == "qin_hged":
        from isalhg.metric_space.distances.qin_hged import QinHGED

        return QinHGED(**params)
    # Fallback to registry
    from isalhg.metric_space.registry import get_distance

    return get_distance(name)


# ---------------------------------------------------------------------------
# Atomic I/O helpers
# ---------------------------------------------------------------------------


def _atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    """Write *data* to *path* atomically (tmp file + rename)."""
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


def _atomic_write_npy(path: Path, arr: np.ndarray) -> None:
    """Save numpy array *arr* to *path* atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp.npy")
    try:
        os.close(fd)
        np.save(tmp, arr)
        os.replace(tmp, path)
    except Exception:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def _is_done(output_dir: Path, tag: str) -> bool:
    """Return True iff ``{output_dir}/{tag}.json`` exists with status='done'."""
    meta_path = output_dir / f"{tag}.json"
    if not meta_path.exists():
        return False
    try:
        with open(meta_path) as f:
            data = json.load(f)
        return data.get("status") == "done"
    except (json.JSONDecodeError, KeyError):
        return False


# ---------------------------------------------------------------------------
# Corpus loading (shared across cell types)
# ---------------------------------------------------------------------------


def _corpus_statistics(hypergraphs: list) -> dict[str, Any]:
    """Compute structural statistics across *hypergraphs* for metadata."""
    if not hypergraphs:
        return {}
    max_degrees = [max((H.degree(v) for v in H.nodes()), default=0) for H in hypergraphs]
    mean_arities = [
        (sum(len(m) for m in H.hyperedges()) / H.n_edges) if H.n_edges > 0 else 0.0
        for H in hypergraphs
    ]
    densities = [H.n_edges / H.n_nodes if H.n_nodes > 0 else 0.0 for H in hypergraphs]
    return {
        "mean_max_degree": float(np.mean(max_degrees)),
        "median_max_degree": float(np.median(max_degrees)),
        "mean_arity": float(np.mean(mean_arities)),
        "mean_density": float(np.mean(densities)),
        "n_nodes_mean": float(np.mean([H.n_nodes for H in hypergraphs])),
        "n_edges_mean": float(np.mean([H.n_edges for H in hypergraphs])),
    }


def _load_corpus(cell: CellSpec) -> tuple[list, dict[str, Any]]:
    """Load dataset items; return ``(hypergraphs, corpus_metadata)``.

    The metadata dict includes the acceptance rate computed from
    ``item.extra['acceptance_attempts']`` (D-CONN1 connectivity filter
    statistic required by DATA.md §1).
    """
    dataset = _build_dataset(cell)
    items = list(dataset)
    hypergraphs = [item.hypergraph for item in items]

    acceptance_attempts = [item.extra.get("acceptance_attempts", 1) for item in items]
    n = len(items)
    total_attempts = sum(acceptance_attempts)

    stats = _corpus_statistics(hypergraphs)
    meta: dict[str, Any] = {
        "n_items": n,
        "acceptance_rate": n / total_attempts if total_attempts > 0 else 1.0,
        "mean_acceptance_attempts": total_attempts / n if n > 0 else 1.0,
        "dataset": cell.dataset,
        "dataset_params": cell.dataset_params,
        "seed": cell.seed,
    }
    meta.update(stats)
    return hypergraphs, meta


# ---------------------------------------------------------------------------
# Cell runner: d_matrix
# ---------------------------------------------------------------------------


def run_d_matrix_cell(cell: CellSpec, output_dir: Path) -> dict[str, Any]:
    """Compute and cache pairwise distance matrices for each distance in cell.

    Each distance gets its own subdirectory ``{output_dir}/{distance_name}/``
    containing ``D.npy`` (the dense symmetric matrix) and ``meta.json``.
    Results are idempotent: already-completed distances are skipped.

    Parameters
    ----------
    cell : CellSpec
        Must have ``type='d_matrix'`` and a non-empty ``distances`` list.
    output_dir : Path
        Root output directory for this cell.

    Returns
    -------
    dict
        Top-level metadata merged from corpus stats and per-distance results.
    """
    result: dict[str, Any] = {"status": "done", "distances": {}}
    hypergraphs, corpus_meta = _load_corpus(cell)
    result.update(corpus_meta)

    for dist_name in cell.distances:
        dist_dir = output_dir / dist_name
        if _is_done(dist_dir, "meta"):
            logger.info("  skip %s/%s (done)", cell.output_key(), dist_name)
            with open(dist_dir / "meta.json") as f:
                result["distances"][dist_name] = json.load(f)
            continue

        dist_params = cell.distance_params.get(dist_name, {})
        distance = _build_distance(dist_name, dist_params)

        t0 = time.perf_counter()
        D: np.ndarray = distance.matrix(hypergraphs)
        elapsed = time.perf_counter() - t0
        logger.info("  %s: %.2fs  shape=%s", dist_name, elapsed, D.shape)

        dist_meta: dict[str, Any] = {
            "status": "done",
            "distance": dist_name,
            "distance_params": dist_params,
            "shape": list(D.shape),
            "wall_clock_s": elapsed,
        }
        dist_meta.update(corpus_meta)

        _atomic_write_npy(dist_dir / "D.npy", D)
        _atomic_write_json(dist_dir / "meta.json", dist_meta)
        result["distances"][dist_name] = dist_meta

    return result


# ---------------------------------------------------------------------------
# Cell runner: sensitivity (E2b)
# ---------------------------------------------------------------------------


def run_sensitivity_cell(cell: CellSpec, output_dir: Path) -> dict[str, Any]:
    """E2b — measure s(e) = d_I(H, H⊕e) for random single edits.

    For each hypergraph in the corpus, sample ``n_edits_per_h`` random atomic
    edits (all Qin edit types via ``random_edit``) and record the resulting
    d_I.  The op type is preserved so histograms can be broken out per edit
    type and per density regime.

    Parameters
    ----------
    cell : CellSpec
        ``dataset_params`` may include ``n_edits_per_h`` (default 20).
    output_dir : Path

    Returns
    -------
    dict
        Sensitivity statistics and raw per-edit records.
    """
    result_path = output_dir / "sensitivity.json"
    if _is_done(output_dir, "sensitivity"):
        logger.info("  skip %s sensitivity (done)", cell.output_key())
        with open(result_path) as f:
            return json.load(f)

    from isalhg.core.sparse_hypergraph import random_edit
    from isalhg.metric_space.distances.isalhg_levenshtein import IsalHGLevenshtein

    dist_params = cell.distance_params.get("isalhg_levenshtein", {})
    distance = IsalHGLevenshtein(**dist_params)

    hypergraphs, corpus_meta = _load_corpus(cell)
    n_edits_per_h = int(cell.dataset_params.get("n_edits_per_h", 20))
    rng = random.Random(cell.seed)

    per_h: list[dict[str, Any]] = []
    for h_idx, H in enumerate(hypergraphs):
        edits: list[dict[str, Any]] = []
        for _ in range(n_edits_per_h):
            try:
                H_prime, op_name = random_edit(H, rng)
                s_e = float(distance.pairwise(H, H_prime))
                edits.append({"op": op_name, "s_e": s_e})
            except Exception as exc:
                logger.debug("random_edit failed h_idx=%d: %s", h_idx, exc)
        per_h.append({"h_idx": h_idx, "edits": edits})

    all_s_e = [e["s_e"] for h in per_h for e in h["edits"]]
    by_op: dict[str, list[float]] = {}
    for h in per_h:
        for e in h["edits"]:
            by_op.setdefault(e["op"], []).append(e["s_e"])

    result: dict[str, Any] = {
        "status": "done",
        "n_edits_total": len(all_s_e),
        "mean_sensitivity": float(np.mean(all_s_e)) if all_s_e else 0.0,
        "median_sensitivity": float(np.median(all_s_e)) if all_s_e else 0.0,
        "per_op_mean": {op: float(np.mean(vals)) for op, vals in by_op.items()},
        "per_op_count": {op: len(vals) for op, vals in by_op.items()},
        "all_s_e": all_s_e,
        "per_h_results": per_h,
    }
    result.update(corpus_meta)
    _atomic_write_json(result_path, result)
    return result


# ---------------------------------------------------------------------------
# Cell runner: ladder (E3 + T-TBb proxy)
# ---------------------------------------------------------------------------


def run_ladder_cell(cell: CellSpec, output_dir: Path) -> dict[str, Any]:
    """E3 + T-TBb proxy — d_I increments along perturbation ladders.

    For each ladder in PerturbationLadderHypergraphs:
    - Computes ``d_I(base, H_t)`` for every rung (cumulative distance).
    - Computes ``d_I(H_{t-1}, H_t)`` for every rung (per-step increment).

    The per-step increments are the R(e)/T_span(e) proxy measurements
    requested for T-TBb: they bound the per-edit contribution to d_I and
    are logged to ``ladder.json["all_increments"]``.

    Parameters
    ----------
    cell : CellSpec
        ``dataset`` must be ``'perturbation_ladder'``.
    output_dir : Path

    Returns
    -------
    dict
        Ladder statistics including per-step increments.
    """
    result_path = output_dir / "ladder.json"
    if _is_done(output_dir, "ladder"):
        logger.info("  skip %s ladder (done)", cell.output_key())
        with open(result_path) as f:
            return json.load(f)

    from isalhg.datasets.synthetic.perturbation_ladder import PerturbationLadderHypergraphs
    from isalhg.metric_space.distances.isalhg_levenshtein import IsalHGLevenshtein

    dist_params = cell.distance_params.get("isalhg_levenshtein", {})
    distance = IsalHGLevenshtein(**dist_params)

    params: dict[str, Any] = {**cell.dataset_params, "seed": cell.seed}
    dataset = PerturbationLadderHypergraphs(**params)

    # Group items by ladder id
    by_ladder: dict[int, list] = {}
    for item in dataset:
        lid = int(item.extra["ladder"])
        by_ladder.setdefault(lid, []).append(item)

    ladders_data: list[dict[str, Any]] = []
    all_increments: list[float] = []

    for lid, items in sorted(by_ladder.items()):
        items_sorted = sorted(items, key=lambda x: int(x.extra["step"]))
        base = items_sorted[0].hypergraph  # step 0

        # Acceptance rate for this ladder
        total_acc = sum(item.extra.get("acceptance_attempts", 1) for item in items_sorted)
        n_items = len(items_sorted)
        acceptance_rate = n_items / total_acc if total_acc > 0 else 1.0

        steps: list[dict[str, Any]] = []
        prev_H = base

        for item in items_sorted[1:]:  # skip step 0 (the base itself)
            H_t = item.hypergraph
            budget_t = int(item.extra["budget_from_base"])
            step_t = int(item.extra["step"])

            d_I_from_base = float(distance.pairwise(base, H_t))
            d_I_increment = float(distance.pairwise(prev_H, H_t))
            all_increments.append(d_I_increment)

            steps.append(
                {
                    "step": step_t,
                    "budget_from_base": budget_t,
                    "d_I_from_base": d_I_from_base,
                    "d_I_increment": d_I_increment,
                    "op": item.extra.get("op", ""),
                }
            )
            prev_H = H_t

        ladders_data.append(
            {
                "ladder_id": lid,
                "n_steps": len(steps),
                "acceptance_rate": acceptance_rate,
                "steps": steps,
            }
        )

    result: dict[str, Any] = {
        "status": "done",
        "n_ladders": len(ladders_data),
        "all_increments": all_increments,
        "mean_d_I_increment": float(np.mean(all_increments)) if all_increments else 0.0,
        "median_d_I_increment": float(np.median(all_increments)) if all_increments else 0.0,
        "ladders": ladders_data,
        "dataset_params": cell.dataset_params,
        "seed": cell.seed,
    }
    _atomic_write_json(result_path, result)
    return result


# ---------------------------------------------------------------------------
# Cell runner: info_content
# ---------------------------------------------------------------------------


def run_info_content_cell(cell: CellSpec, output_dir: Path) -> dict[str, Any]:
    """Information-content comparison: IsalHG bits vs incidence-list bits.

    For each hypergraph in the corpus:
    - ``B_IsalHG = |w*(H)| * log2(|Σ_HG(k)|)``   (fixed-width token code)
    - ``B_incidence = incidence-list encoding``    (competitor construction model)
    - ``r = B_incidence / B_IsalHG``              (compression ratio; r > 1 favours IsalHG)

    The Wilcoxon signed-rank test on ``r - 1 > 0`` and OLS ``B_IsalHG = a +
    β·B_incidence`` (β < 1 ⇒ systematic compression) are computed in the
    analysis layer from the per-record ``records`` list.

    Parameters
    ----------
    cell : CellSpec
    output_dir : Path

    Returns
    -------
    dict
        Per-H records plus summary statistics.
    """
    result_path = output_dir / "info_content.json"
    if _is_done(output_dir, "info_content"):
        logger.info("  skip %s info_content (done)", cell.output_key())
        with open(result_path) as f:
            return json.load(f)

    from isalhg.core.canonical import canonical_string
    from isalhg.metric_space.metrics.information import (
        alphabet_size_isalhg,
        bits_incidence_list,
        bits_isalhg,
        compression_ratio,
    )

    hypergraphs, corpus_meta = _load_corpus(cell)

    # Determine k = max arity across corpus (Σ_HG(k) size depends on k)
    k = max(
        (max((len(m) for m in H.hyperedges()), default=2) for H in hypergraphs),
        default=2,
    )
    alpha_size = alphabet_size_isalhg(k)

    records: list[dict[str, Any]] = []
    for H in hypergraphs:
        # canonical_string returns semicolon-separated token string
        w = canonical_string(H, k=k)
        tokens = [t for t in w.split(";") if t]
        n_tokens = len(tokens)

        arities = [len(m) for m in H.hyperedges()]
        n_nodes = H.n_nodes

        b_isal = bits_isalhg(n_tokens, k)
        b_inc = bits_incidence_list(n_nodes, arities)
        r = compression_ratio(b_inc, b_isal) if b_isal > 0 else float("nan")

        records.append(
            {
                "n_nodes": n_nodes,
                "n_edges": H.n_edges,
                "k_max": max(arities) if arities else 0,
                "n_tokens": n_tokens,
                "bits_isalhg": b_isal,
                "bits_incidence_list": b_inc,
                "compression_ratio": r,
            }
        )

    ratios = [rec["compression_ratio"] for rec in records if not _is_nan(rec["compression_ratio"])]

    result: dict[str, Any] = {
        "status": "done",
        "k": k,
        "alphabet_size": alpha_size,
        "n_items": len(records),
        "median_compression_ratio": float(np.median(ratios)) if ratios else float("nan"),
        "fraction_shorter": sum(1 for r in ratios if r > 1.0) / len(ratios) if ratios else 0.0,
        "records": records,
    }
    result.update(corpus_meta)
    _atomic_write_json(result_path, result)
    return result


def _is_nan(x: float) -> bool:
    import math

    return math.isnan(x)


# ---------------------------------------------------------------------------
# Cell runner: G2 sensitivity (T-M5g)
# ---------------------------------------------------------------------------


#: Design fixture names that ``run_g2_design_sensitivity_cell`` recognises.
_G2_DESIGN_BUILDERS: dict[str, Any] = {}  # populated lazily below


def _load_g2_designs() -> dict[str, Any]:
    """Return the design-builder dict, importing designs on first call."""
    if not _G2_DESIGN_BUILDERS:
        from isalhg.datasets.synthetic.designs import (
            cyclic_triple_orbit_13,
            fano_plane,
            gq_2_2_doily,
            sts_9,
        )

        _G2_DESIGN_BUILDERS["fano_plane"] = fano_plane
        _G2_DESIGN_BUILDERS["sts_9"] = sts_9
        _G2_DESIGN_BUILDERS["cyclic_triple_orbit_13"] = lambda: cyclic_triple_orbit_13((0, 1, 3))
        _G2_DESIGN_BUILDERS["gq_2_2_doily"] = gq_2_2_doily
    return _G2_DESIGN_BUILDERS


def _g2_edit_record(
    H: Any,
    rng: random.Random,
    distance_isalhg: Any,
    distance_nauty: Any,
    max_arity: int,
) -> dict[str, Any]:
    """Apply one connectivity-preserving edit and return both sensitivity values."""
    from isalhg.core.sparse_hypergraph import qin_edit_cost, random_connected_edit

    H_prime, op_name = random_connected_edit(H, rng, max_arity=max_arity)
    s_e_isalhg = float(distance_isalhg.pairwise(H, H_prime))
    s_e_nauty = float(distance_nauty.pairwise(H, H_prime))
    qin = int(qin_edit_cost(H, H_prime))
    return {
        "op": op_name,
        "s_e_isalhg": s_e_isalhg,
        "s_e_nauty": s_e_nauty,
        "qin_cost": qin,
    }


def run_g2_sensitivity_cell(cell: CellSpec, output_dir: Path) -> dict[str, Any]:
    """G2 sensitivity: s(e) for both IsalHG and nauty contrast per connected edit.

    Applies connectivity-preserving random edits (:func:`random_connected_edit`)
    to each hypergraph in the corpus and records both ``s_e_isalhg`` (IsalHG
    Levenshtein) and ``s_e_nauty`` (nauty-Levi edit distance). The dual
    measurement is the G2 contrast: ours (compact, structured) vs nauty
    (avalanche-everywhere on any edit).

    The corpus is loaded via the dataset factory identical to
    ``run_sensitivity_cell``. Use ``dataset_params.max_arity`` (default 3)
    to cap edit arity and ``dataset_params.n_edits_per_h`` (default 20).

    Output: ``{output_dir}/g2_sensitivity.json``.

    Parameters
    ----------
    cell : CellSpec
        ``type`` must be ``'g2_sensitivity'``.
    output_dir : Path

    Returns
    -------
    dict
        Result with ``records`` list and aggregate summary statistics.
    """
    result_path = output_dir / "g2_sensitivity.json"
    if _is_done(output_dir, "g2_sensitivity"):
        logger.info("  skip %s g2_sensitivity (done)", cell.output_key())
        with open(result_path) as f:
            return json.load(f)

    from isalhg.metric_space.distances.isalhg_levenshtein import IsalHGLevenshtein
    from isalhg.metric_space.representations.nauty_levi_edit import NautyLeviEditDistance

    dist_params = cell.distance_params.get("isalhg_levenshtein", {})
    distance_isalhg = IsalHGLevenshtein(**dist_params)
    distance_nauty = NautyLeviEditDistance()

    hypergraphs, corpus_meta = _load_corpus(cell)
    n_edits_per_h = int(cell.dataset_params.get("n_edits_per_h", 20))
    max_arity = int(cell.dataset_params.get("max_arity", 3))
    rng = random.Random(cell.seed)

    records: list[dict[str, Any]] = []
    for h_idx, H in enumerate(hypergraphs):
        edits: list[dict[str, Any]] = []
        for _ in range(n_edits_per_h):
            try:
                edits.append(_g2_edit_record(H, rng, distance_isalhg, distance_nauty, max_arity))
            except Exception as exc:
                logger.debug("g2 edit failed h_idx=%d: %s", h_idx, exc)
        records.append(
            {
                "source_id": f"H_{h_idx}",
                "source_type": "random",
                # Strip trailing seed suffix (e.g. "sparse_s0" → "sparse") so
                # the regime key matches the _REGIME_PREDICTION dict in analysis/g2.py.
                "regime": (cell.label or "random").split("_s")[0],
                "design_name": None,
                "edits": edits,
            }
        )

    all_s_e = [e["s_e_isalhg"] for r in records for e in r["edits"]]
    all_nauty = [e["s_e_nauty"] for r in records for e in r["edits"]]

    result: dict[str, Any] = {
        "status": "done",
        "type": "g2_sensitivity",
        "n_edits_total": len(all_s_e),
        "mean_s_e_isalhg": float(np.mean(all_s_e)) if all_s_e else 0.0,
        "median_s_e_isalhg": float(np.median(all_s_e)) if all_s_e else 0.0,
        "mean_s_e_nauty": float(np.mean(all_nauty)) if all_nauty else 0.0,
        "median_s_e_nauty": float(np.median(all_nauty)) if all_nauty else 0.0,
        "records": records,
    }
    result.update(corpus_meta)
    _atomic_write_json(result_path, result)
    return result


def run_g2_design_sensitivity_cell(cell: CellSpec, output_dir: Path) -> dict[str, Any]:
    """G2 design-fixture sensitivity: s(e) on Fano / STS(9) / C13 / GQ(2,2).

    Runs the dual-distance sensitivity measurement on the four hand-built
    symmetric-design fixtures. These are the calibration objects for the
    three-regime prediction from ``stability.md`` §4.2:

    - Predicted near-unimodal (coherent): ``fano_plane``, ``sts_9``
    - Predicted heavy-tailed / bimodal (incoherent): ``cyclic_triple_orbit_13``,
      ``gq_2_2_doily``

    ``dataset_params.designs`` lists the fixture names to run (subset of the
    four keys above; default is all four).
    ``dataset_params.n_edits_per_design`` (default 20) controls the edit count.
    ``dataset_params.max_arity`` (default 3) caps edit arity.

    Output: ``{output_dir}/g2_design_sensitivity.json``.

    Parameters
    ----------
    cell : CellSpec
        ``type`` must be ``'g2_design_sensitivity'``.
    output_dir : Path

    Returns
    -------
    dict
        Result with ``records`` list keyed by design name.
    """
    result_path = output_dir / "g2_design_sensitivity.json"
    if _is_done(output_dir, "g2_design_sensitivity"):
        logger.info("  skip %s g2_design_sensitivity (done)", cell.output_key())
        with open(result_path) as f:
            return json.load(f)

    from isalhg.metric_space.distances.isalhg_levenshtein import IsalHGLevenshtein
    from isalhg.metric_space.representations.nauty_levi_edit import NautyLeviEditDistance

    dist_params = cell.distance_params.get("isalhg_levenshtein", {})
    distance_isalhg = IsalHGLevenshtein(**dist_params)
    distance_nauty = NautyLeviEditDistance()

    design_builders = _load_g2_designs()
    designs_to_run: list[str] = list(cell.dataset_params.get("designs", list(design_builders)))
    n_edits = int(cell.dataset_params.get("n_edits_per_design", 20))
    max_arity = int(cell.dataset_params.get("max_arity", 3))
    rng = random.Random(cell.seed)

    records: list[dict[str, Any]] = []
    for design_name in designs_to_run:
        if design_name not in design_builders:
            logger.warning("Unknown design fixture %r; skipping", design_name)
            continue
        H = design_builders[design_name]()
        edits: list[dict[str, Any]] = []
        for _ in range(n_edits):
            try:
                edits.append(_g2_edit_record(H, rng, distance_isalhg, distance_nauty, max_arity))
            except Exception as exc:
                logger.debug("g2 design edit failed %s: %s", design_name, exc)
        records.append(
            {
                "source_id": design_name,
                "source_type": "design",
                "regime": "design",
                "design_name": design_name,
                "n_nodes": H.n_nodes,
                "n_edges": H.n_edges,
                "edits": edits,
            }
        )

    all_s_e = [e["s_e_isalhg"] for r in records for e in r["edits"]]
    all_nauty = [e["s_e_nauty"] for r in records for e in r["edits"]]

    result: dict[str, Any] = {
        "status": "done",
        "type": "g2_design_sensitivity",
        "designs": designs_to_run,
        "n_edits_total": len(all_s_e),
        "mean_s_e_isalhg": float(np.mean(all_s_e)) if all_s_e else 0.0,
        "median_s_e_isalhg": float(np.median(all_s_e)) if all_s_e else 0.0,
        "mean_s_e_nauty": float(np.mean(all_nauty)) if all_nauty else 0.0,
        "median_s_e_nauty": float(np.median(all_nauty)) if all_nauty else 0.0,
        "records": records,
        "seed": cell.seed,
    }
    _atomic_write_json(result_path, result)
    return result


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

_CELL_RUNNERS: dict[str, Any] = {
    "d_matrix": run_d_matrix_cell,
    "sensitivity": run_sensitivity_cell,
    "ladder": run_ladder_cell,
    "info_content": run_info_content_cell,
    "g2_sensitivity": run_g2_sensitivity_cell,
    "g2_design_sensitivity": run_g2_design_sensitivity_cell,
}


def run_cell(cell: CellSpec, output_dir: Path) -> dict[str, Any]:
    """Execute *cell*, writing results to *output_dir*.

    Parameters
    ----------
    cell : CellSpec
    output_dir : Path

    Returns
    -------
    dict
        Result metadata dict.

    Raises
    ------
    ValueError
        If ``cell.type`` is not recognised.
    """
    runner_fn = _CELL_RUNNERS.get(cell.type)
    if runner_fn is None:
        known = sorted(_CELL_RUNNERS)
        raise ValueError(f"Unknown cell type {cell.type!r}; known: {known}")
    logger.info(
        "cell type=%s dataset=%s label=%r seed=%d",
        cell.type,
        cell.dataset,
        cell.label,
        cell.seed,
    )
    return runner_fn(cell, output_dir)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry point for ``python -m experiments.article.runner``."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    parser = argparse.ArgumentParser(
        description="T-M5a article experiment runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--config", type=Path, required=True, help="YAML config path")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=None,
        help="Override output_root from config",
    )
    parser.add_argument(
        "--cell-index",
        type=int,
        default=None,
        help="Run only this cell (0-based). Defaults to $SLURM_ARRAY_TASK_ID if set.",
    )
    parser.add_argument(
        "--count",
        action="store_true",
        help="Print the number of cells and exit (for SLURM array sizing)",
    )
    args = parser.parse_args()

    config = ArticleConfig.from_yaml(args.config)
    if args.output_root is not None:
        config = ArticleConfig(output_root=args.output_root, cells=config.cells)

    if args.count:
        print(len(config.cells))
        return

    cell_index = args.cell_index
    if cell_index is None:
        slurm_id = os.environ.get("SLURM_ARRAY_TASK_ID")
        if slurm_id is not None:
            cell_index = int(slurm_id)

    cells_to_run = [config.cells[cell_index]] if cell_index is not None else list(config.cells)

    t_start = time.perf_counter()
    for i, cell in enumerate(cells_to_run):
        logger.info("--- cell %d/%d ---", i + 1, len(cells_to_run))
        output_dir = config.cell_output_dir(cell)
        run_cell(cell, output_dir)

    logger.info("All done in %.1fs", time.perf_counter() - t_start)


if __name__ == "__main__":
    main()
