"""Multi-seed sweep runner — T-M7d.

Runs G1 + A1 (geometry table) + A2 (clustering) + A3 (kNN) + bits over:
  - Stratum A: the 17 admitted known-design seeds (``known_design_catalog``)
    via ``build_stratum_a_corpus(seed_value=s)`` for S independent seeds.
  - Stratum B: every admitted ER block from ``stratum_b_feasibility_envelope.json``
    (read-only at runtime; a later-admitted cell needs no code change).

Seven representations per cell:
  isalhg_levenshtein (reference / d_I), hypergraph_wl_l1, netlsd_l2, hpd_jsd,
  nauty_levi_edit, degree_seq_l1 (naive baseline, T-M7c), and HyperCOT where
  feasible (small corpora only; scale limit O(n³)/pair).

Statistics harness (``experiments.analysis.stats``):
  BCa 95% CI per (representation, metric, cell); one-sided Wilcoxon signed-rank
  vs IsalHG per competitor with Holm–Bonferroni across (representations × metrics);
  median paired diff + rank-biserial; A3 nested correctly
  (``aggregate_a3_seed_scores`` — resample seeds only, not fold × seed).

k-family discipline (PROPOSAL.md §0, stability.md §1, DATA.md §5):
  ``d_I^{k,h,Σ}`` is an index family.  Absolute d_I values across different k
  are **incomparable**.  This module only compares dimensionless geometry
  descriptors (ν, D̂, stress, hubness skew) across k and within-k application
  rankings — never pooled raw d_I.

Landmine (T-M5a, S5 history):
  Bits must count Σ_HG tokens through the bracket-aware parser
  (``isalhg.core.instructions.parse``), never ``w.split(";")``.  Raw split
  overcounts ~2× because ";" also appears as a field separator inside
  ``V[...]``/``C[...]`` brackets.  The regression tests in
  ``tests/unit/experiments_article/test_bits_harvest.py`` (T15 pin) cover this.

Stratum A vs B metrics:
  - Stratum A: G1 + A1 + A2 + A3 + bits (has family labels for clustering/kNN).
  - Stratum B: G1 + A1 + bits only (no semantic labels; feeds geometry-vs-axis
    curves for ν, D̂, stress, hubness vs n / density / arity).

LOCAL SMOKE USAGE::

    python -m experiments.article.analysis.sweep_multi_seed \\
        --envelope experiments/article/stratum_b_feasibility_envelope.json \\
        --output-root /media/.../results/T-M7d \\
        --n-seeds 20 \\
        --n-corpus 30 \\
        --n-max 16 \\
        --stratum a b

FULL SWEEP (Picasso, use sbatch workers)::

    python -m experiments.article.analysis.sweep_multi_seed \\
        --envelope experiments/article/stratum_b_feasibility_envelope.json \\
        --output-root /media/.../results/T-M7d \\
        --n-seeds 20 \\
        --n-corpus 60 \\
        --stratum a b \\
        --cell-key stratum_a      # or a specific B block key
        --dist-name isalhg_levenshtein   # one dist per SLURM task
"""

from __future__ import annotations

import argparse
import contextlib
import json
import logging
import os
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Admitted Stratum A IDs (fixed after T-M7a feasibility pilot)
# ---------------------------------------------------------------------------

ADMITTED_A_IDS: frozenset[str] = frozenset(
    [
        # arity 3
        "sts7",
        "sts9",
        "gq22",
        "loose_path_k3",
        "tight_path_k3",
        "loose_cycle_k3",
        "tight_cycle_k3",
        "complete_k3_n5",
        # arity 4
        "loose_path_k4",
        "tight_path_k4",
        "loose_cycle_k4",
        "tight_cycle_k4",
        "complete_k4_n6",
        # arity 5
        "loose_path_k5",
        "tight_path_k5",
        "tight_cycle_k5",
        "complete_k5_n6",
    ]
)

# Arity-3 fallback (always feasible for PlantedFamilyDataset member generation).
# Arity-4/5 designs with m=3 hyperedges cannot produce non-isomorphic Qin-edit
# perturbations within the standard retry budget: the edit space is too small.
# run_stratum_a_seed falls back to this subset when the full set fails.
ADMITTED_A_IDS_ARITY3: frozenset[str] = frozenset(
    [
        "sts7",
        "sts9",
        "gq22",
        "loose_path_k3",
        "tight_path_k3",
        "loose_cycle_k3",
        "tight_cycle_k3",
        "complete_k3_n5",
    ]
)

# ---------------------------------------------------------------------------
# Seven representations
# ---------------------------------------------------------------------------

# All 7 reps for the full sweep.
ALL_DISTANCES: list[str] = [
    "isalhg_levenshtein",  # reference / d_I
    "hypergraph_wl_l1",
    "netlsd_l2",
    "hpd_jsd",
    "nauty_levi_edit",
    "degree_seq_l1",  # naive baseline, T-M7c
    "hypercot",  # O(n³)/pair; gated at runtime by HYPERCOT_MAX_N / HYPERCOT_MAX_CORPUS
]

# HyperCOT is O(n³)/pair; only admit for small n.
HYPERCOT_MAX_N: int = 12
HYPERCOT_MAX_CORPUS: int = 20

# IsalHG is the reference for Wilcoxon paired tests.
PRIMARY_REPR: str = "isalhg_levenshtein"

# Display labels for tables and figures.
REPR_LABELS: dict[str, str] = {
    "isalhg_levenshtein": "IsalHG",
    "hypergraph_wl_l1": "WL-L1",
    "netlsd_l2": "NetLSD",
    "hpd_jsd": "HPD-JSD",
    "nauty_levi_edit": "NautyEdit",
    "degree_seq_l1": "DegreeSeq",
    "hypercot": "HyperCOT",
}

_BOOTSTRAP_N_RESAMPLES: int = 9999
_BOOTSTRAP_SEED: int = 0
_KNN_K_VALUES: list[int] = [1, 3, 5]
_N_CV_FOLDS: int = 5
_N_KMEDOIDS_INIT: int = 10

# Stratum A sweep parameters.
# members=5 × 8 arity-3 families = 40 items ≥ _N_CV_FOLDS × n_classes (40) — A3 feasible.
_STRATUM_A_MEMBERS_PER_FAMILY: int = 5
_STRATUM_A_N_EDITS: int = 2
_STRATUM_A_MAX_RETRIES: int = 300

# Stratum B Erdős–Rényi: connected-domain generator.
_STRATUM_B_CONNECTED_MAX_ATTEMPTS: int = 1000

# ---------------------------------------------------------------------------
# Atomic I/O helpers
# ---------------------------------------------------------------------------


def _atomic_write_npy(path: Path, arr: np.ndarray) -> None:
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


def _atomic_write_json(path: Path, data: Any) -> None:
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


def _load_json_or_none(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Stratum B envelope loader
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StratumBBlock:
    """One admitted Stratum B ER block from the feasibility envelope."""

    block_key: str  # e.g. "er_uniform_k3_n8_rho1"
    n: int
    k: int
    density_ratio: float  # rho = m/n


def load_admitted_stratum_b_blocks(envelope_path: Path | str) -> list[StratumBBlock]:
    """Read admitted Stratum B blocks from the feasibility envelope JSON.

    The envelope is read-only; this function never modifies it.

    Parameters
    ----------
    envelope_path : Path or str
        Path to ``stratum_b_feasibility_envelope.json``.

    Returns
    -------
    list[StratumBBlock]
        Admitted blocks in the order they appear in ``admitted_block_keys``.

    Raises
    ------
    FileNotFoundError
        If the envelope file does not exist.
    """
    envelope_path = Path(envelope_path)
    with open(envelope_path) as fh:
        data: dict[str, Any] = json.load(fh)

    admitted_keys: list[str] = data["admitted_block_keys"]
    block_results: dict[str, dict[str, Any]] = {
        br["block_key"]: br for br in data.get("block_results", []) if isinstance(br, dict)
    }

    blocks: list[StratumBBlock] = []
    for bk in admitted_keys:
        if bk in block_results:
            br = block_results[bk]
            blocks.append(
                StratumBBlock(
                    block_key=bk,
                    n=int(br["n"]),
                    k=int(br["k"]),
                    density_ratio=float(br["density_ratio"]),
                )
            )
        else:
            logger.warning("admitted key %r has no block_result entry; skipping.", bk)

    logger.info("Loaded %d admitted Stratum B blocks.", len(blocks))
    return blocks


# ---------------------------------------------------------------------------
# Corpus builders
# ---------------------------------------------------------------------------


def build_stratum_a_seed_corpus(
    seed: int,
    admitted_ids: frozenset[str] = ADMITTED_A_IDS,
    members_per_family: int = _STRATUM_A_MEMBERS_PER_FAMILY,
    n_edits: int = _STRATUM_A_N_EDITS,
    max_retries: int = _STRATUM_A_MAX_RETRIES,
) -> tuple[list[Any], list[int], list[str]]:
    """Build one Stratum A corpus sample under a given generator seed.

    Uses ``build_stratum_a_corpus(seed_value=seed, admitted_ids=admitted_ids)``
    which feeds the admitted known-design seeds into PlantedFamilyDataset.
    Different seeds yield different non-isomorphic perturbation members while
    preserving family membership.

    Parameters
    ----------
    seed : int
        Generator seed (0-indexed; the outer resampling unit).
    admitted_ids : frozenset[str]
        Admitted catalog item IDs.
    members_per_family : int
        Members per family including the seed hypergraph.
    n_edits : int
        Qin edit budget per non-seed member.
    max_retries : int
        Rejection-sampling attempts per member.

    Returns
    -------
    hypergraphs : list[SparseHypergraph]
    labels : list[int]
        Family index (0-indexed) for each hypergraph, same order as
        ``hypergraphs``.
    family_label_strings : list[str]
        String family label (e.g. ``"STS7"``) for each hypergraph.
    """
    from isalhg.datasets.synthetic.known_design_catalog import build_stratum_a_corpus

    dataset = build_stratum_a_corpus(
        members_per_family=members_per_family,
        n_edits=n_edits,
        max_retries=max_retries,
        seed_value=seed,
        dedup_backend="isalhg",
        admitted_ids=admitted_ids,
    )
    items = list(dataset)
    hypergraphs = [item.hypergraph for item in items]
    labels = [int(item.extra.get("family_index", 0)) for item in items]
    family_label_strings = [str(item.extra.get("family_label", "")) for item in items]
    return hypergraphs, labels, family_label_strings


def build_stratum_b_seed_corpus(
    block: StratumBBlock,
    corpus_seed: int,
    n_corpus: int,
) -> list[Any]:
    """Build one Stratum B ER corpus sample.

    Sub-seeds: ``corpus_seed * n_corpus + i`` for ``i ∈ [0, n_corpus)``.
    Each sub-seed produces one connected uniform ER hypergraph.

    Parameters
    ----------
    block : StratumBBlock
        Block specification (n, k, density_ratio).
    corpus_seed : int
        Outer resampling seed (0-indexed).
    n_corpus : int
        Number of ER instances to generate.

    Returns
    -------
    list[SparseHypergraph]
        Connected ER hypergraphs; may be shorter than ``n_corpus`` when some
        rejection-sampling attempts fail connectivity.
    """
    from isalhg.datasets.synthetic.erdos_renyi import UniformErdosRenyiHypergraphs

    hypergraphs: list[Any] = []
    base = corpus_seed * n_corpus
    for i in range(n_corpus):
        sub_seed = base + i
        try:
            ds = UniformErdosRenyiHypergraphs(
                n=block.n,
                r=block.k,
                c=float(block.density_ratio),
                seed=sub_seed,
                require_connected=True,
                connected_max_attempts=_STRATUM_B_CONNECTED_MAX_ATTEMPTS,
            )
            items = list(ds)
            if items:
                hypergraphs.append(items[0].hypergraph)
        except Exception as exc:
            logger.debug("ER(%s, seed=%d): %s", block.block_key, sub_seed, exc)
    return hypergraphs


# ---------------------------------------------------------------------------
# D-matrix caching (runner-compatible layout)
# ---------------------------------------------------------------------------


def _d_matrix_is_done(dist_dir: Path) -> bool:
    meta = _load_json_or_none(dist_dir / "meta.json")
    return bool(meta and meta.get("status") == "done")


def compute_and_cache_d_matrix(
    hypergraphs: list[Any],
    dist_name: str,
    cache_dir: Path,
    corpus_meta: dict[str, Any],
) -> np.ndarray | None:
    """Compute the pairwise distance matrix and cache it atomically.

    Cache layout::

        {cache_dir}/{dist_name}/D.npy
        {cache_dir}/{dist_name}/meta.json  (status: "done")

    Parameters
    ----------
    hypergraphs : list[SparseHypergraph]
        Ordered corpus.
    dist_name : str
        Registered distance name.
    cache_dir : Path
        Cell × seed cache root (e.g. ``{output_root}/d_matrix/stratum_a/seed0``).
    corpus_meta : dict
        Metadata written into meta.json (seeds, n, k, …).

    Returns
    -------
    numpy.ndarray or None
        Symmetric (N, N) distance matrix, or None if computation fails.
    """
    from isalhg.metric_space.registry import get_distance

    dist_dir = cache_dir / dist_name
    d_npy = dist_dir / "D.npy"

    if _d_matrix_is_done(dist_dir):
        logger.debug("cache hit: %s", d_npy)
        return np.load(d_npy)

    try:
        dist_obj = get_distance(dist_name)
        logger.info("  computing %s (N=%d)...", dist_name, len(hypergraphs))
        t0 = time.perf_counter()
        D: np.ndarray = dist_obj.matrix(hypergraphs)
        elapsed = time.perf_counter() - t0
        logger.info("  %s: %.2fs  shape=%s", dist_name, elapsed, D.shape)
    except Exception as exc:
        logger.warning("  %s FAILED: %s", dist_name, exc)
        return None

    meta: dict[str, Any] = {
        "status": "done",
        "distance": dist_name,
        "shape": list(D.shape),
        "wall_clock_s": elapsed,
    }
    meta.update(corpus_meta)

    dist_dir.mkdir(parents=True, exist_ok=True)
    _atomic_write_npy(d_npy, D)
    _atomic_write_json(dist_dir / "meta.json", meta)
    return D


# ---------------------------------------------------------------------------
# Per-seed metric computors
# ---------------------------------------------------------------------------


def compute_g1_a1(
    D: np.ndarray,
    corpus_name: str,
    repr_name: str,
    max_cv_dims: int | None = None,
) -> dict[str, Any] | None:
    """Compute G1 (concentration + hubness) and A1 (geometry table row).

    Parameters
    ----------
    D : numpy.ndarray
        Symmetric (N, N) distance matrix.
    corpus_name : str
        Label for the corpus.
    repr_name : str
        Distance name.
    max_cv_dims : int or None
        Maximum CV dimension (default: min(N-1, 40)).

    Returns
    -------
    dict or None
        Keys: nu, d_hat, d_hat_censored, stress, diameter, median, iqr,
        hubness_skewness.  None if the corpus is too small.
    """
    from experiments.article.analysis.mds import (
        cv_dimension_selection,
        geometry_table_row,
    )

    N = D.shape[0]
    if N < 4:
        logger.warning("%s/%s: N=%d < 4; skip geometry.", corpus_name, repr_name, N)
        return None

    cap = max_cv_dims or min(N - 1, 40)

    try:
        d_hat, cv_errors = cv_dimension_selection(D, max_dims=cap)
    except Exception as exc:
        logger.warning("cv_dimension_selection failed (%s/%s): %s", corpus_name, repr_name, exc)
        d_hat = min(2, N - 1)
        cv_errors = []

    # Flag censored D̂ (rides to cap — monotone-decreasing CV curve).
    censored = len(cv_errors) >= cap and d_hat == cap

    try:
        row = geometry_table_row(corpus_name, repr_name, D, d_hat)
    except Exception as exc:
        logger.warning("geometry_table_row failed (%s/%s): %s", corpus_name, repr_name, exc)
        return None

    return {
        "nu": float(row["nu"]),
        "d_hat": int(d_hat),
        "d_hat_censored": bool(censored),
        "stress": float(row["stress_at_d_hat"]),
        "diameter": float(row["diameter"]),
        "median": float(row["median"]),
        "iqr": float(row["iqr"]),
        "hubness_skewness": float(row["hubness_skewness"]),
    }


def compute_a2(
    D: np.ndarray,
    labels: list[int],
    n_families: int,
    rng_seed: int = 42,
) -> dict[str, Any] | None:
    """Compute A2 clustering metrics (one-seed pass).

    Parameters
    ----------
    D : numpy.ndarray
        Symmetric (N, N) distance matrix.
    labels : list[int]
        True family indices (0-indexed), length N.
    n_families : int
        Number of planted families (= k for k-medoids).
    rng_seed : int
        Base RNG seed.

    Returns
    -------
    dict or None
        Keys: ari, nmi, silhouette, dunn, davies_bouldin.
    """
    from experiments.article.analysis.clustering import clustering_metrics, run_kmedoids

    N = len(labels)
    if n_families + 1 > N:
        logger.warning("A2: N=%d < n_families=%d + 1; skip.", N, n_families)
        return None

    true_labels = np.array(labels, dtype=np.intp)
    try:
        km = run_kmedoids(D, k=n_families, n_init=_N_KMEDOIDS_INIT, rng_seed=rng_seed)
        metrics = clustering_metrics(D, km.labels, km.medoids, true_labels)
    except Exception as exc:
        logger.warning("A2 clustering failed: %s", exc)
        return None

    return {
        "ari": float(metrics["ari"]),
        "nmi": float(metrics["nmi"]),
        "silhouette": float(metrics["silhouette"]),
        "dunn": float(metrics["dunn"]),
        "davies_bouldin": float(metrics["davies_bouldin"]),
    }


def compute_a3_fold_aucs(
    D: np.ndarray,
    labels: list[int],
    n_families: int,
    k_values: list[int] = _KNN_K_VALUES,
    rng_seed: int = 42,
) -> dict[int, float] | None:
    """Compute A3 kNN seed-level AUC (mean over stratified CV folds).

    The seed-level AUC is the fold-mean AUC for one seed's corpus.  The
    caller then bootstraps / runs Wilcoxon over the S seed-level AUCs using
    ``aggregate_a3_seed_scores``.  This correctly avoids double-counting
    fold × seed variance.

    Parameters
    ----------
    D : numpy.ndarray
        Symmetric (N, N) distance matrix.
    labels : list[int]
        True family indices (0-indexed), length N.
    n_families : int
        Number of distinct families.
    k_values : list[int]
        kNN k values to evaluate.
    rng_seed : int
        Seed for stratified fold generation.

    Returns
    -------
    dict[int, float] or None
        ``{k: seed_level_auc}`` for each k in k_values.
        None if computation fails.
    """
    from experiments.article.analysis.knn import run_knn_cv, stratified_fold_indices

    labels_arr = np.array(labels, dtype=np.intp)
    n_classes = len(np.unique(labels_arr))
    if n_classes < 2:
        logger.warning("A3: only %d class; skip.", n_classes)
        return None
    if len(labels) < _N_CV_FOLDS * n_classes:
        logger.warning(
            "A3: N=%d too small for %d-fold with %d classes; skip.",
            len(labels),
            _N_CV_FOLDS,
            n_classes,
        )
        return None

    try:
        fold_indices = stratified_fold_indices(labels_arr, n_folds=_N_CV_FOLDS, rng_seed=rng_seed)
        knn_results = run_knn_cv(D, labels_arr, k_values, fold_indices, n_classes)
    except Exception as exc:
        logger.warning("A3 kNN CV failed: %s", exc)
        return None

    return {r["k"]: float(r["auc_ovr"]) for r in knn_results}


def compute_bits_for_hypergraphs(
    hypergraphs: list[Any],
) -> dict[str, Any] | None:
    """Compute fixed-width-code information content vs incidence-list baseline.

    Uses the bracket-aware parser (``isalhg.core.instructions.parse``) to count
    tokens.  Raw ``w.split(";")`` overcounts ~2× because ";" also appears as a
    field separator inside ``V[...]``/``C[...]`` brackets.

    Parameters
    ----------
    hypergraphs : list[SparseHypergraph]
        Corpus to measure.

    Returns
    -------
    dict or None
        Keys: n_items, k_corpus, mean_ratio, median_ratio, gt1_fraction,
        mean_bits_isalhg, mean_bits_inclist.  None if computation fails.
    """
    from isalhg.core.canonical import canonical_string
    from isalhg.core.instructions import parse as parse_tokens
    from isalhg.metric_space.metrics.information import (
        alphabet_size_isalhg,
        bits_incidence_list,
        bits_isalhg,
        compression_ratio,
    )

    if not hypergraphs:
        return None

    try:
        k_corpus = max(
            (max((len(m) for m in H.hyperedges()), default=2) for H in hypergraphs),
            default=2,
        )
        alpha_size = alphabet_size_isalhg(k_corpus)

        ratios: list[float] = []
        bits_isal_list: list[float] = []
        bits_inc_list: list[float] = []

        for H in hypergraphs:
            w = canonical_string(H, k=k_corpus)
            # Bracket-aware parser (T15 regression pin — never raw split).
            n_tokens = len(parse_tokens(w))

            arities = [len(m) for m in H.hyperedges()]
            n_nodes = H.n_nodes

            b_isal = bits_isalhg(n_tokens, k_corpus)
            b_inc = bits_incidence_list(n_nodes, arities)
            r = compression_ratio(b_inc, b_isal) if b_isal > 0 else float("nan")

            ratios.append(r)
            bits_isal_list.append(b_isal)
            bits_inc_list.append(b_inc)

        valid_ratios = [r for r in ratios if not np.isnan(r)]
        return {
            "n_items": len(hypergraphs),
            "k_corpus": int(k_corpus),
            "alphabet_size": int(alpha_size),
            "mean_ratio": float(np.mean(valid_ratios)) if valid_ratios else float("nan"),
            "median_ratio": float(np.median(valid_ratios)) if valid_ratios else float("nan"),
            "gt1_fraction": float(np.mean([r > 1 for r in valid_ratios]))
            if valid_ratios
            else float("nan"),
            "mean_bits_isalhg": float(np.mean(bits_isal_list)),
            "mean_bits_inclist": float(np.mean(bits_inc_list)),
        }
    except Exception as exc:
        logger.warning("bits computation failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Per-seed result container
# ---------------------------------------------------------------------------


@dataclass
class SeedMetrics:
    """All metrics for one (cell, seed, representation)."""

    cell_key: str
    stratum: str  # "a" or "b"
    dist_name: str
    seed: int
    n_corpus: int
    g1_a1: dict[str, Any] | None  # G1 + A1 geometry
    a2: dict[str, Any] | None  # A2 clustering (Stratum A only)
    a3: dict[int, float] | None  # A3 kNN AUC per k (Stratum A only)
    bits: dict[str, Any] | None  # bits (isalhg_levenshtein only)


# ---------------------------------------------------------------------------
# Single-seed runner: Stratum A
# ---------------------------------------------------------------------------


def run_stratum_a_seed(
    seed: int,
    dist_names: list[str],
    output_root: Path,
    admitted_ids: frozenset[str] = ADMITTED_A_IDS,
    members_per_family: int = _STRATUM_A_MEMBERS_PER_FAMILY,
    n_edits: int = _STRATUM_A_N_EDITS,
    max_retries: int = _STRATUM_A_MAX_RETRIES,
    max_cv_dims: int | None = None,
) -> list[SeedMetrics]:
    """Run all representations for one Stratum A seed.

    Parameters
    ----------
    seed : int
        Corpus seed (0-indexed resampling unit).
    dist_names : list[str]
        Distance representations to run.
    output_root : Path
        Root output directory.
    admitted_ids : frozenset[str]
        Admitted catalog item IDs.
    members_per_family : int
        Members per family.
    n_edits : int
        Edit budget.
    max_retries : int
        Rejection-sampling retries.
    max_cv_dims : int or None
        Max CV dimension for D̂ selection.

    Returns
    -------
    list[SeedMetrics]
        One per representation.
    """
    cell_key = "stratum_a"
    cache_root = output_root / "d_matrix" / "stratum_a" / f"seed{seed}"

    # Build corpus once (reused across all representations).
    logger.info("Stratum A seed %d: building corpus...", seed)
    t0 = time.perf_counter()
    used_ids = admitted_ids
    try:
        hypergraphs, labels, label_strings = build_stratum_a_seed_corpus(
            seed=seed,
            admitted_ids=admitted_ids,
            members_per_family=members_per_family,
            n_edits=n_edits,
            max_retries=max_retries,
        )
    except Exception as exc:
        # Arity-4/5 designs with m=3 hyperedges exhaust the retry budget because
        # the Qin-edit space is too small to find non-isomorphic members.
        # Fall back to the arity-3 subset which is always feasible.
        logger.warning(
            "Stratum A seed %d: full corpus failed (%s). "
            "Arity-4/5 designs with m=3 edges have no viable Qin-edit perturbations. "
            "Retrying with arity-3 subset (%d designs).",
            seed,
            exc,
            len(ADMITTED_A_IDS_ARITY3),
        )
        used_ids = ADMITTED_A_IDS_ARITY3
        try:
            hypergraphs, labels, label_strings = build_stratum_a_seed_corpus(
                seed=seed,
                admitted_ids=ADMITTED_A_IDS_ARITY3,
                members_per_family=members_per_family,
                n_edits=n_edits,
                max_retries=max_retries,
            )
        except Exception as exc2:
            logger.error("Stratum A seed %d: arity-3 fallback also failed: %s", seed, exc2)
            return []

    n = len(hypergraphs)
    n_families = len(used_ids)
    logger.info(
        "Stratum A seed %d: N=%d items, %d families, %.2fs",
        seed,
        n,
        n_families,
        time.perf_counter() - t0,
    )

    corpus_meta = {
        "stratum": "a",
        "seed": seed,
        "n_items": n,
        "n_families": n_families,
        "members_per_family": members_per_family,
        "n_edits": n_edits,
        "admitted_ids": sorted(used_ids),
        "fallback_to_arity3": used_ids is not admitted_ids,
    }

    results: list[SeedMetrics] = []

    for dist_name in dist_names:
        logger.info("  Stratum A seed %d: %s", seed, dist_name)

        D = compute_and_cache_d_matrix(hypergraphs, dist_name, cache_root, corpus_meta)
        if D is None:
            results.append(
                SeedMetrics(
                    cell_key=cell_key,
                    stratum="a",
                    dist_name=dist_name,
                    seed=seed,
                    n_corpus=n,
                    g1_a1=None,
                    a2=None,
                    a3=None,
                    bits=None,
                )
            )
            continue

        g1_a1 = compute_g1_a1(D, cell_key, dist_name, max_cv_dims=max_cv_dims)
        a2 = compute_a2(D, labels, n_families, rng_seed=seed)
        a3 = compute_a3_fold_aucs(D, labels, n_families, rng_seed=seed)

        # Bits only for IsalHG (others don't produce canonical strings).
        bits: dict[str, Any] | None = None
        if dist_name == PRIMARY_REPR:
            bits = compute_bits_for_hypergraphs(hypergraphs)

        sm = SeedMetrics(
            cell_key=cell_key,
            stratum="a",
            dist_name=dist_name,
            seed=seed,
            n_corpus=n,
            g1_a1=g1_a1,
            a2=a2,
            a3=a3,
            bits=bits,
        )
        results.append(sm)
        _cache_seed_metrics(sm, output_root)

    return results


# ---------------------------------------------------------------------------
# Single-seed runner: Stratum B
# ---------------------------------------------------------------------------


def run_stratum_b_seed(
    block: StratumBBlock,
    seed: int,
    dist_names: list[str],
    output_root: Path,
    n_corpus: int = 60,
    max_cv_dims: int | None = None,
) -> list[SeedMetrics]:
    """Run all representations for one Stratum B (ER block) seed.

    Parameters
    ----------
    block : StratumBBlock
        Block specification.
    seed : int
        Corpus seed (0-indexed).
    dist_names : list[str]
        Distance representations.
    output_root : Path
        Root output directory.
    n_corpus : int
        ER instances per seed.
    max_cv_dims : int or None
        Max CV dimension.

    Returns
    -------
    list[SeedMetrics]
        One per representation.
    """
    cell_key = block.block_key
    cache_root = output_root / "d_matrix" / "stratum_b" / block.block_key / f"seed{seed}"

    # Build ER corpus.
    logger.info("Stratum B %s seed %d: building ER corpus...", block.block_key, seed)
    hypergraphs = build_stratum_b_seed_corpus(block, corpus_seed=seed, n_corpus=n_corpus)
    n = len(hypergraphs)

    if n < 4:
        logger.warning("Stratum B %s seed %d: N=%d < 4; skipping.", block.block_key, seed, n)
        return []

    corpus_meta = {
        "stratum": "b",
        "block_key": block.block_key,
        "seed": seed,
        "n": block.n,
        "k": block.k,
        "density_ratio": block.density_ratio,
        "n_corpus_actual": n,
    }

    results: list[SeedMetrics] = []

    for dist_name in dist_names:
        # HyperCOT scale limit: only on small n, small N.
        if dist_name == "hypercot" and (block.n > HYPERCOT_MAX_N or n > HYPERCOT_MAX_CORPUS):
            logger.info(
                "  %s skipped HyperCOT (n=%d > %d or N=%d > %d; O(n³)/pair limit)",
                block.block_key,
                block.n,
                HYPERCOT_MAX_N,
                n,
                HYPERCOT_MAX_CORPUS,
            )
            results.append(
                SeedMetrics(
                    cell_key=cell_key,
                    stratum="b",
                    dist_name=dist_name,
                    seed=seed,
                    n_corpus=n,
                    g1_a1=None,
                    a2=None,
                    a3=None,
                    bits=None,
                )
            )
            continue

        logger.info("  Stratum B %s seed %d: %s", block.block_key, seed, dist_name)
        D = compute_and_cache_d_matrix(hypergraphs, dist_name, cache_root, corpus_meta)
        if D is None:
            results.append(
                SeedMetrics(
                    cell_key=cell_key,
                    stratum="b",
                    dist_name=dist_name,
                    seed=seed,
                    n_corpus=n,
                    g1_a1=None,
                    a2=None,
                    a3=None,
                    bits=None,
                )
            )
            continue

        g1_a1 = compute_g1_a1(D, cell_key, dist_name, max_cv_dims=max_cv_dims)

        # Bits: Stratum B → only IsalHG.
        bits: dict[str, Any] | None = None
        if dist_name == PRIMARY_REPR:
            bits = compute_bits_for_hypergraphs(hypergraphs)

        # A2/A3 skipped for Stratum B (no semantic family labels).
        sm = SeedMetrics(
            cell_key=cell_key,
            stratum="b",
            dist_name=dist_name,
            seed=seed,
            n_corpus=n,
            g1_a1=g1_a1,
            a2=None,
            a3=None,
            bits=bits,
        )
        results.append(sm)
        _cache_seed_metrics(sm, output_root)

    return results


# ---------------------------------------------------------------------------
# Per-seed metrics cache
# ---------------------------------------------------------------------------


def _seed_metrics_cache_path(sm: SeedMetrics, output_root: Path) -> Path:
    return (
        output_root
        / "seed_metrics"
        / sm.stratum
        / sm.cell_key
        / f"seed{sm.seed}"
        / f"{sm.dist_name}.json"
    )


def _cache_seed_metrics(sm: SeedMetrics, output_root: Path) -> None:
    path = _seed_metrics_cache_path(sm, output_root)
    payload: dict[str, Any] = {
        "cell_key": sm.cell_key,
        "stratum": sm.stratum,
        "dist_name": sm.dist_name,
        "seed": sm.seed,
        "n_corpus": sm.n_corpus,
        "g1_a1": sm.g1_a1,
        "a2": sm.a2,
        "a3": {str(k): v for k, v in sm.a3.items()} if sm.a3 else None,
        "bits": sm.bits,
    }
    _atomic_write_json(path, payload)


def _load_seed_metrics_cache(
    cell_key: str,
    stratum: str,
    dist_name: str,
    seed: int,
    output_root: Path,
) -> SeedMetrics | None:
    path = output_root / "seed_metrics" / stratum / cell_key / f"seed{seed}" / f"{dist_name}.json"
    data = _load_json_or_none(path)
    if data is None:
        return None
    a3_raw = data.get("a3")
    a3 = {int(k): float(v) for k, v in a3_raw.items()} if a3_raw else None
    return SeedMetrics(
        cell_key=data["cell_key"],
        stratum=data["stratum"],
        dist_name=data["dist_name"],
        seed=data["seed"],
        n_corpus=data.get("n_corpus", 0),
        g1_a1=data.get("g1_a1"),
        a2=data.get("a2"),
        a3=a3,
        bits=data.get("bits"),
    )


# ---------------------------------------------------------------------------
# Statistics aggregation (BCa CI + Wilcoxon + Holm)
# ---------------------------------------------------------------------------


def _extract_metric_scores(
    seed_metrics: list[SeedMetrics],
    metric_family: str,
    metric_key: str,
) -> list[float | None]:
    """Extract per-seed scores for one (representation, metric) pair.

    Parameters
    ----------
    seed_metrics : list[SeedMetrics]
        All SeedMetrics objects for one (cell, representation).
    metric_family : str
        One of ``"g1_a1"``, ``"a2"``, ``"bits"``.
    metric_key : str
        The sub-key within the metric family dict.

    Returns
    -------
    list[float or None]
        Length = n_seeds; None where computation failed.
    """
    scores: list[float | None] = []
    for sm in seed_metrics:
        family_data = getattr(sm, metric_family, None)
        if family_data is None:
            scores.append(None)
        else:
            val = family_data.get(metric_key)
            scores.append(float(val) if val is not None else None)
    return scores


def _extract_a3_scores(
    seed_metrics: list[SeedMetrics],
    k: int,
) -> list[float | None]:
    """Extract per-seed A3 AUC scores for a given k."""
    scores: list[float | None] = []
    for sm in seed_metrics:
        if sm.a3 is None:
            scores.append(None)
        else:
            scores.append(sm.a3.get(k))
    return scores


@dataclass
class CellStats:
    """Aggregated BCa CIs + Wilcoxon + Holm for one cell."""

    cell_key: str
    stratum: str
    n_seeds: int
    # (metric_id, repr_name) → {mean, ci_lower, ci_upper, n_valid}
    cis: dict[str, dict[str, Any]] = field(default_factory=dict)
    # (metric_id, repr_name) → {statistic, p_holm, effect_size, median_diff}
    wilcoxon: dict[str, dict[str, Any]] = field(default_factory=dict)
    # block metadata (Stratum B only)
    block_meta: dict[str, Any] | None = None


def aggregate_cell_stats(
    cell_key: str,
    stratum: str,
    all_seed_metrics: dict[str, list[SeedMetrics]],  # dist_name → list[SeedMetrics]
    n_seeds: int,
    block_meta: dict[str, Any] | None = None,
) -> CellStats:
    """Compute BCa CIs + Wilcoxon + Holm for one cell.

    The family-wise Holm correction is applied over all
    (competitor_repr × metric_id) pairs jointly.

    Parameters
    ----------
    cell_key : str
        Cell identifier.
    stratum : str
        "a" or "b".
    all_seed_metrics : dict
        Maps dist_name → list of SeedMetrics (length n_seeds).
    n_seeds : int
        Declared seed count.
    block_meta : dict or None
        Stratum B block metadata (n, k, density_ratio).

    Returns
    -------
    CellStats
        Fully populated with CIs and Wilcoxon tests.
    """
    from experiments.analysis.stats import (
        bca_bootstrap_ci,
        holm_bonferroni,
        wilcoxon_one_sided,
    )

    cs = CellStats(
        cell_key=cell_key,
        stratum=stratum,
        n_seeds=n_seeds,
        block_meta=block_meta,
    )

    # Define which metrics to aggregate per stratum.
    geom_metrics = ["nu", "stress", "hubness_skewness", "d_hat"]
    a2_metrics = ["ari", "nmi", "silhouette"] if stratum == "a" else []
    bits_metrics = ["median_ratio", "gt1_fraction"] if PRIMARY_REPR in all_seed_metrics else []

    def _metric_id(family: str, key: str, k: int | None = None) -> str:
        if k is None:
            return f"{family}::{key}"
        return f"{family}::auc_k{k}"

    dist_names = list(all_seed_metrics.keys())

    # --- BCa CI per (repr, metric) ---
    for dist_name, seed_list in all_seed_metrics.items():
        for mkey in geom_metrics:
            raw = _extract_metric_scores(seed_list, "g1_a1", mkey)
            valid = [v for v in raw if v is not None]
            mid = _metric_id("g1_a1", mkey)
            row: dict[str, Any] = {
                "repr": dist_name,
                "metric": mid,
                "mean": float(np.mean(valid)) if valid else float("nan"),
                "n_valid": len(valid),
            }
            if len(valid) >= 3:
                try:
                    ci = bca_bootstrap_ci(
                        valid, n_resamples=_BOOTSTRAP_N_RESAMPLES, rng_seed=_BOOTSTRAP_SEED
                    )
                    row["ci_lower"] = ci.lower
                    row["ci_upper"] = ci.upper
                except Exception:
                    row["ci_lower"] = float("nan")
                    row["ci_upper"] = float("nan")
            else:
                row["ci_lower"] = float("nan")
                row["ci_upper"] = float("nan")
            cs.cis[f"{dist_name}::{mid}"] = row

        for mkey in a2_metrics:
            raw = _extract_metric_scores(seed_list, "a2", mkey)
            valid = [v for v in raw if v is not None]
            mid = _metric_id("a2", mkey)
            row = {
                "repr": dist_name,
                "metric": mid,
                "mean": float(np.mean(valid)) if valid else float("nan"),
                "n_valid": len(valid),
            }
            if len(valid) >= 3:
                try:
                    ci = bca_bootstrap_ci(
                        valid, n_resamples=_BOOTSTRAP_N_RESAMPLES, rng_seed=_BOOTSTRAP_SEED
                    )
                    row["ci_lower"] = ci.lower
                    row["ci_upper"] = ci.upper
                except Exception:
                    row["ci_lower"] = float("nan")
                    row["ci_upper"] = float("nan")
            else:
                row["ci_lower"] = float("nan")
                row["ci_upper"] = float("nan")
            cs.cis[f"{dist_name}::{mid}"] = row

        # A3: per k value.
        if stratum == "a":
            for k in _KNN_K_VALUES:
                raw_a3 = _extract_a3_scores(seed_list, k)
                valid_a3 = [v for v in raw_a3 if v is not None]
                mid = _metric_id("a3", "auc", k)
                row = {
                    "repr": dist_name,
                    "metric": mid,
                    "mean": float(np.mean(valid_a3)) if valid_a3 else float("nan"),
                    "n_valid": len(valid_a3),
                }
                if len(valid_a3) >= 3:
                    try:
                        ci = bca_bootstrap_ci(
                            valid_a3,
                            n_resamples=_BOOTSTRAP_N_RESAMPLES,
                            rng_seed=_BOOTSTRAP_SEED,
                        )
                        row["ci_lower"] = ci.lower
                        row["ci_upper"] = ci.upper
                    except Exception:
                        row["ci_lower"] = float("nan")
                        row["ci_upper"] = float("nan")
                else:
                    row["ci_lower"] = float("nan")
                    row["ci_upper"] = float("nan")
                cs.cis[f"{dist_name}::{mid}"] = row

        if dist_name == PRIMARY_REPR:
            for mkey in bits_metrics:
                raw = _extract_metric_scores(seed_list, "bits", mkey)
                valid = [v for v in raw if v is not None]
                mid = _metric_id("bits", mkey)
                row = {
                    "repr": dist_name,
                    "metric": mid,
                    "mean": float(np.mean(valid)) if valid else float("nan"),
                    "n_valid": len(valid),
                }
                if len(valid) >= 3:
                    try:
                        ci = bca_bootstrap_ci(
                            valid, n_resamples=_BOOTSTRAP_N_RESAMPLES, rng_seed=_BOOTSTRAP_SEED
                        )
                        row["ci_lower"] = ci.lower
                        row["ci_upper"] = ci.upper
                    except Exception:
                        row["ci_lower"] = float("nan")
                        row["ci_upper"] = float("nan")
                else:
                    row["ci_lower"] = float("nan")
                    row["ci_upper"] = float("nan")
                cs.cis[f"{dist_name}::{mid}"] = row

    # --- Wilcoxon + Holm across (competitor × metric) family ---
    competitors = [d for d in dist_names if d != PRIMARY_REPR]
    if PRIMARY_REPR not in all_seed_metrics or not competitors:
        return cs

    primary_seeds = all_seed_metrics[PRIMARY_REPR]

    # Build the list of (competitor, metric_id) pairs.
    all_metrics: list[str] = [_metric_id("g1_a1", m) for m in geom_metrics]
    if stratum == "a":
        all_metrics += [_metric_id("a2", m) for m in a2_metrics]
        all_metrics += [_metric_id("a3", "auc", k) for k in _KNN_K_VALUES]

    raw_p_values: list[float] = []
    wilcoxon_todo: list[tuple[str, str]] = []  # (competitor, metric_id)

    for comp in competitors:
        comp_seeds = all_seed_metrics[comp]
        for mid in all_metrics:
            # Determine family and key.
            family, _, key_or_k = mid.partition("::")

            if family == "g1_a1":
                prim_raw = _extract_metric_scores(primary_seeds, "g1_a1", key_or_k)
                comp_raw = _extract_metric_scores(comp_seeds, "g1_a1", key_or_k)
            elif family == "a2":
                prim_raw = _extract_metric_scores(primary_seeds, "a2", key_or_k)
                comp_raw = _extract_metric_scores(comp_seeds, "a2", key_or_k)
            elif family == "a3":
                k_val = int(key_or_k.replace("auc_k", ""))
                prim_raw = _extract_a3_scores(primary_seeds, k_val)
                comp_raw = _extract_a3_scores(comp_seeds, k_val)
            else:
                raw_p_values.append(1.0)
                wilcoxon_todo.append((comp, mid))
                continue

            pairs = [
                (p, c)
                for p, c in zip(prim_raw, comp_raw, strict=False)
                if p is not None and c is not None
            ]
            if len(pairs) < 3:
                raw_p_values.append(1.0)
                wilcoxon_todo.append((comp, mid))
                continue

            try:
                wres = wilcoxon_one_sided(
                    [p for p, _ in pairs],
                    [c for _, c in pairs],
                )
                raw_p_values.append(wres.p_value)
            except Exception:
                raw_p_values.append(1.0)
                wres = None  # type: ignore[assignment]
            wilcoxon_todo.append((comp, mid))

    # Holm correction.
    if raw_p_values:
        holm_res = holm_bonferroni(raw_p_values)
        adj_p = holm_res.adjusted_p_values

        for idx, (comp, mid) in enumerate(wilcoxon_todo):
            comp_seeds = all_seed_metrics[comp]
            family, _, key_or_k = mid.partition("::")

            if family == "g1_a1":
                prim_raw = _extract_metric_scores(primary_seeds, "g1_a1", key_or_k)
                comp_raw = _extract_metric_scores(comp_seeds, "g1_a1", key_or_k)
            elif family == "a2":
                prim_raw = _extract_metric_scores(primary_seeds, "a2", key_or_k)
                comp_raw = _extract_metric_scores(comp_seeds, "a2", key_or_k)
            elif family == "a3":
                k_val = int(key_or_k.replace("auc_k", ""))
                prim_raw = _extract_a3_scores(primary_seeds, k_val)
                comp_raw = _extract_a3_scores(comp_seeds, k_val)
            else:
                continue

            pairs = [
                (p, c)
                for p, c in zip(prim_raw, comp_raw, strict=False)
                if p is not None and c is not None
            ]
            if len(pairs) < 3:
                cs.wilcoxon[f"{comp}::{mid}"] = {
                    "repr": comp,
                    "metric": mid,
                    "p_holm": float(adj_p[idx]),
                    "effect_size": float("nan"),
                    "median_diff": float("nan"),
                    "n_pairs": 0,
                }
                continue

            try:
                wres = wilcoxon_one_sided(
                    [p for p, _ in pairs],
                    [c for _, c in pairs],
                )
                cs.wilcoxon[f"{comp}::{mid}"] = {
                    "repr": comp,
                    "metric": mid,
                    "p_holm": float(adj_p[idx]),
                    "p_raw": float(wres.p_value),
                    "effect_size": float(wres.effect_size),
                    "median_diff": float(wres.median_diff),
                    "test_used": wres.test_used,
                    "n_pairs": len(pairs),
                    "family_size": len(raw_p_values),
                }
            except Exception as exc:
                logger.warning("Wilcoxon failed (%s, %s): %s", comp, mid, exc)

    return cs


# ---------------------------------------------------------------------------
# Geometry-vs-axis curves (Stratum B)
# ---------------------------------------------------------------------------


def plot_geometry_curves(
    all_b_stats: list[tuple[StratumBBlock, CellStats]],
    output_dir: Path,
) -> None:
    """Emit geometry-vs-axis curves for Stratum B cells.

    Plots ν, D̂, stress-1, and hubness skew vs each of:
      - n (node count), holding k and density fixed per group
      - density (rho = m/n), holding k and n fixed
      - arity (k), holding n and density fixed

    Only dimensionless descriptors are compared across k (DATA.md §5).
    Error bands = BCa CI from the CellStats objects.

    Parameters
    ----------
    all_b_stats : list of (StratumBBlock, CellStats)
        All Stratum B cell statistics.
    output_dir : Path
        Directory for figure output.
    """
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        logger.warning("matplotlib not available; skipping geometry curves.")
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    geom_keys = ["nu", "stress", "hubness_skewness", "d_hat"]
    geom_labels = {
        "nu": "ν (non-Euclidean mass)",
        "stress": "Stress-1 at D̂",
        "hubness_skewness": "Hubness skew (k=10)",
        "d_hat": "D̂ (intrinsic dimension)",
    }

    # Collect primary repr curves.
    def _get_mean_ci(cs: CellStats, metric_key: str) -> tuple[float, float, float]:
        mid = f"g1_a1::{metric_key}"
        key = f"{PRIMARY_REPR}::{mid}"
        row = cs.cis.get(key)
        if row is None:
            return float("nan"), float("nan"), float("nan")
        return (
            row.get("mean", float("nan")),
            row.get("ci_lower", float("nan")),
            row.get("ci_upper", float("nan")),
        )

    def _plot_axis_curve(
        ax_name: str,
        ax_getter: Any,
        group_keys: dict[str, Any],
    ) -> None:
        for gk_label, gk_filter in group_keys.items():
            cells = [(block, cs) for block, cs in all_b_stats if gk_filter(block)]
            if not cells:
                continue
            cells.sort(key=lambda bc: ax_getter(bc[0]))

            for mkey in geom_keys:
                fig, ax = plt.subplots(figsize=(6, 4))
                xs = [ax_getter(b) for b, _ in cells]
                means = [_get_mean_ci(cs, mkey)[0] for _, cs in cells]
                ci_l = [_get_mean_ci(cs, mkey)[1] for _, cs in cells]
                ci_u = [_get_mean_ci(cs, mkey)[2] for _, cs in cells]

                ax.plot(xs, means, "o-", label=f"{gk_label} IsalHG")
                ax.fill_between(
                    xs,
                    [lo if not np.isnan(lo) else m for m, lo in zip(means, ci_l, strict=False)],
                    [hi if not np.isnan(hi) else m for m, hi in zip(means, ci_u, strict=False)],
                    alpha=0.2,
                )
                ax.set_xlabel(ax_name)
                ax.set_ylabel(geom_labels.get(mkey, mkey))
                ax.set_title(f"{geom_labels.get(mkey, mkey)} vs {ax_name}\n({gk_label})")
                ax.legend(fontsize=8)

                safe_label = gk_label.replace("/", "_").replace("=", "")
                fname = output_dir / f"{mkey}_vs_{ax_name}_{safe_label}.png"
                fig.savefig(fname, dpi=120, bbox_inches="tight")
                plt.close(fig)
                logger.info("  figure: %s", fname)

    # --- Curves vs n (group by k and density) ---
    k_vals = sorted({b.k for b, _ in all_b_stats})
    rho_vals = sorted({b.density_ratio for b, _ in all_b_stats})
    for k in k_vals:
        for rho in rho_vals:
            label = f"k{k}_rho{rho}"
            _plot_axis_curve(
                ax_name="n",
                ax_getter=lambda b: b.n,
                group_keys={label: lambda b, _k=k, _r=rho: b.k == _k and b.density_ratio == _r},
            )

    # --- Curves vs density (group by k and n) ---
    n_vals = sorted({b.n for b, _ in all_b_stats})
    for k in k_vals:
        for n in n_vals:
            label = f"k{k}_n{n}"
            _plot_axis_curve(
                ax_name="density",
                ax_getter=lambda b: b.density_ratio,
                group_keys={label: lambda b, _k=k, _n=n: b.k == _k and b.n == _n},
            )

    # --- Curves vs arity (group by n and density) ---
    for n in n_vals:
        for rho in rho_vals:
            label = f"n{n}_rho{rho}"
            _plot_axis_curve(
                ax_name="arity_k",
                ax_getter=lambda b: b.k,
                group_keys={label: lambda b, _n=n, _r=rho: b.n == _n and b.density_ratio == _r},
            )


# ---------------------------------------------------------------------------
# Full sweep orchestration
# ---------------------------------------------------------------------------


def run_sweep(
    envelope_path: Path | str,
    output_root: Path | str,
    n_seeds: int = 20,
    n_corpus_b: int = 60,
    dist_names: list[str] | None = None,
    run_stratum_a: bool = True,
    run_stratum_b: bool = True,
    n_max: int | None = None,
    cell_key_filter: str | None = None,
    dist_name_filter: str | None = None,
    max_cv_dims: int | None = None,
    admitted_ids: frozenset[str] = ADMITTED_A_IDS,
) -> dict[str, Any]:
    """Run the full multi-seed sweep over Stratum A and/or Stratum B.

    Parameters
    ----------
    envelope_path : Path or str
        Path to ``stratum_b_feasibility_envelope.json`` (read-only).
    output_root : Path or str
        Root directory for results.
    n_seeds : int, optional
        Seeds per cell (S; default 20).
    n_corpus_b : int, optional
        ER instances per Stratum B seed (default 60).
    dist_names : list[str] or None, optional
        Distances to compute.  Defaults to ALL_DISTANCES.
    run_stratum_a : bool, optional
        Whether to process Stratum A.  Default True.
    run_stratum_b : bool, optional
        Whether to process Stratum B.  Default True.
    n_max : int | None, optional
        If set, restrict Stratum B to blocks with n ≤ n_max (local smoke).
    cell_key_filter : str | None, optional
        If set, process only this cell key (SLURM array mode).
    dist_name_filter : str | None, optional
        If set, compute only this distance (SLURM array mode).
    max_cv_dims : int | None, optional
        Maximum CV dimension.
    admitted_ids : frozenset[str], optional
        Admitted Stratum A catalog IDs.

    Returns
    -------
    dict
        Summary with keys ``n_stratum_a_seeds``, ``n_stratum_b_cells``,
        ``stratum_a_stats``, ``stratum_b_stats``.
    """
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    if dist_names is None:
        dist_names = list(ALL_DISTANCES)

    if dist_name_filter is not None:
        dist_names = [d for d in dist_names if d == dist_name_filter]
        logger.info("Distance filter: %r — %d distance(s)", dist_name_filter, len(dist_names))

    all_b_stats: list[tuple[StratumBBlock, CellStats]] = []

    # ---- Stratum A ----
    if run_stratum_a and (cell_key_filter is None or cell_key_filter == "stratum_a"):
        logger.info("=== Stratum A sweep (S=%d, %d reps) ===", n_seeds, len(dist_names))
        a_seed_metrics_by_dist: dict[str, list[SeedMetrics]] = {d: [] for d in dist_names}

        for seed in range(n_seeds):
            # Check per-seed cache first.
            all_cached = True
            for dist_name in dist_names:
                cached = _load_seed_metrics_cache("stratum_a", "a", dist_name, seed, output_root)
                if cached is None:
                    all_cached = False
                    break

            if all_cached:
                for dist_name in dist_names:
                    cached = _load_seed_metrics_cache(
                        "stratum_a", "a", dist_name, seed, output_root
                    )
                    if cached:
                        a_seed_metrics_by_dist[dist_name].append(cached)
                logger.info("Stratum A seed %d: cache hit (all %d reps).", seed, len(dist_names))
                continue

            seed_results = run_stratum_a_seed(
                seed=seed,
                dist_names=dist_names,
                output_root=output_root,
                admitted_ids=admitted_ids,
                max_cv_dims=max_cv_dims,
            )
            for sm in seed_results:
                a_seed_metrics_by_dist[sm.dist_name].append(sm)

        if a_seed_metrics_by_dist:
            a_stats = aggregate_cell_stats(
                cell_key="stratum_a",
                stratum="a",
                all_seed_metrics=a_seed_metrics_by_dist,
                n_seeds=n_seeds,
            )
            _write_cell_stats(a_stats, output_root / "stats" / "stratum_a_stats.json")
            logger.info("Stratum A: stats written.")

    # ---- Stratum B ----
    if run_stratum_b:
        blocks = load_admitted_stratum_b_blocks(envelope_path)

        if n_max is not None:
            blocks = [b for b in blocks if b.n <= n_max]
            logger.info("Stratum B: filtered to %d blocks (n ≤ %d).", len(blocks), n_max)

        if cell_key_filter is not None and cell_key_filter != "stratum_a":
            blocks = [b for b in blocks if b.block_key == cell_key_filter]
            logger.info("Stratum B: cell filter %r → %d block(s).", cell_key_filter, len(blocks))

        for block in blocks:
            logger.info(
                "=== Stratum B block %s (n=%d, k=%d, rho=%.1f) ===",
                block.block_key,
                block.n,
                block.k,
                block.density_ratio,
            )
            b_seed_metrics_by_dist: dict[str, list[SeedMetrics]] = {d: [] for d in dist_names}

            for seed in range(n_seeds):
                all_cached = True
                for dist_name in dist_names:
                    cached = _load_seed_metrics_cache(
                        block.block_key, "b", dist_name, seed, output_root
                    )
                    if cached is None:
                        all_cached = False
                        break

                if all_cached:
                    for dist_name in dist_names:
                        cached = _load_seed_metrics_cache(
                            block.block_key, "b", dist_name, seed, output_root
                        )
                        if cached:
                            b_seed_metrics_by_dist[dist_name].append(cached)
                    logger.info("  Block %s seed %d: cache hit.", block.block_key, seed)
                    continue

                seed_results = run_stratum_b_seed(
                    block=block,
                    seed=seed,
                    dist_names=dist_names,
                    output_root=output_root,
                    n_corpus=n_corpus_b,
                    max_cv_dims=max_cv_dims,
                )
                for sm in seed_results:
                    b_seed_metrics_by_dist[sm.dist_name].append(sm)

            b_stats = aggregate_cell_stats(
                cell_key=block.block_key,
                stratum="b",
                all_seed_metrics=b_seed_metrics_by_dist,
                n_seeds=n_seeds,
                block_meta={
                    "n": block.n,
                    "k": block.k,
                    "density_ratio": block.density_ratio,
                },
            )
            all_b_stats.append((block, b_stats))
            _write_cell_stats(
                b_stats,
                output_root / "stats" / f"{block.block_key}_stats.json",
            )
            logger.info("Block %s: stats written.", block.block_key)

    # Geometry-vs-axis curves.
    if all_b_stats:
        curves_dir = output_root / "figures" / "stratum_b_curves"
        plot_geometry_curves(all_b_stats, curves_dir)

    # Summary.
    summary: dict[str, Any] = {
        "n_seeds": n_seeds,
        "dist_names": dist_names,
        "n_stratum_a_seeds": n_seeds if run_stratum_a else 0,
        "n_stratum_b_cells": len(all_b_stats),
        "stratum_b_blocks": [
            {
                "block_key": b.block_key,
                "n": b.n,
                "k": b.k,
                "density_ratio": b.density_ratio,
            }
            for b, _ in all_b_stats
        ],
    }
    _atomic_write_json(output_root / "sweep_summary.json", summary)
    logger.info("Sweep summary written: %s", output_root / "sweep_summary.json")
    return summary


# ---------------------------------------------------------------------------
# JSON serialisation
# ---------------------------------------------------------------------------


def _write_cell_stats(cs: CellStats, path: Path) -> None:
    payload = {
        "cell_key": cs.cell_key,
        "stratum": cs.stratum,
        "n_seeds": cs.n_seeds,
        "block_meta": cs.block_meta,
        "cis": cs.cis,
        "wilcoxon": cs.wilcoxon,
    }
    _atomic_write_json(path, payload)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry point for the T-M7d multi-seed sweep."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    parser = argparse.ArgumentParser(
        description="T-M7d multi-seed sweep runner (Stratum A + B, 7 representations).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--envelope",
        type=Path,
        default=Path("experiments/article/stratum_b_feasibility_envelope.json"),
        help="Path to stratum_b_feasibility_envelope.json (read-only).",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/T-M7d"),
        help="Root output directory.",
    )
    parser.add_argument(
        "--n-seeds",
        type=int,
        default=20,
        help="Seeds per cell (S; default 20).",
    )
    parser.add_argument(
        "--n-corpus",
        type=int,
        default=60,
        help="ER instances per Stratum B seed (default 60).",
    )
    parser.add_argument(
        "--distances",
        nargs="+",
        default=ALL_DISTANCES,
        help="Distance names to compute (default: all 6 without HyperCOT).",
    )
    parser.add_argument(
        "--stratum",
        nargs="+",
        choices=["a", "b"],
        default=["a", "b"],
        help="Which strata to run (default: a b).",
    )
    parser.add_argument(
        "--n-max",
        type=int,
        default=None,
        help="Restrict Stratum B to blocks with n ≤ n-max (local smoke).",
    )
    parser.add_argument(
        "--cell-key",
        type=str,
        default=None,
        help=(
            'Process only this cell key ("stratum_a" or a B block key). Used in SLURM array jobs.'
        ),
    )
    parser.add_argument(
        "--dist-name",
        type=str,
        default=None,
        help="Compute only this distance.  Used with --cell-key in SLURM array jobs.",
    )
    parser.add_argument(
        "--max-cv-dims",
        type=int,
        default=None,
        help="Maximum CV dimension for D̂ selection.",
    )
    args = parser.parse_args()

    summary = run_sweep(
        envelope_path=args.envelope,
        output_root=args.output_root,
        n_seeds=args.n_seeds,
        n_corpus_b=args.n_corpus,
        dist_names=args.distances,
        run_stratum_a="a" in args.stratum,
        run_stratum_b="b" in args.stratum,
        n_max=args.n_max,
        cell_key_filter=args.cell_key,
        dist_name_filter=args.dist_name,
        max_cv_dims=args.max_cv_dims,
    )

    print(f"\n{'=' * 60}")
    print("T-M7d sweep complete")
    print(f"{'=' * 60}")
    print(f"  Seeds: {summary['n_seeds']}")
    print(f"  Distances: {summary['dist_names']}")
    print(f"  Stratum A seeds: {summary['n_stratum_a_seeds']}")
    print(f"  Stratum B cells: {summary['n_stratum_b_cells']}")
    if summary["stratum_b_blocks"]:
        print("  Stratum B blocks processed:")
        for b in summary["stratum_b_blocks"]:
            print(f"    {b['block_key']} (n={b['n']}, k={b['k']}, rho={b['density_ratio']})")


if __name__ == "__main__":
    main()
