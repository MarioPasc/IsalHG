"""G3 — OFAT geometry-response analysis and visualization (T-M7f).

Computes and plots:
  - Response curves: d_rep(H_0, H_t) vs step t for all registered competitors
  - MDS trajectory: 2D classical-MDS embedding of the OFAT sequence
  - nu-trajectory: non-Euclidean mass per prefix [H_0..H_t]
  - Filmstrip: drawn hypergraph snapshots at H_0, T/4, T/2, 3T/4, T
  - Monotone fraction per axis per representation
  - Jump/continuity statistic (max single-step embedded jump / median step)
    for both IsalHG and nauty

The ONE rendering convention for all drawn hypergraphs is stated in
artifacts/g3/README.md (T-M8b will reuse this for the capability-matrix figure).
Summary here: spring layout on the incidence bipartite graph (vertices as nodes,
hyperedges as nodes connected to their members), vertex dots in black, hyperedge
polygons as semi-transparent filled convex hulls (2-member edges as thick lines).

All competitor distances use get_distance(name).pairwise(H1, H2) from the registry;
failures are caught and reported so a missing optional dep (pynauty, netlsd) does
not abort the whole analysis.
"""

from __future__ import annotations

import json
import random
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from experiments.article.g3_sequence import OfatAxis, OfatStep, generate_ofat_sequence
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.metric_space.metrics.embedding import (
    classical_mds,
    embed_classical,
    neg_eigenvalue_mass,
)
from isalhg.metric_space.registry import get_distance

# ---------------------------------------------------------------------------
# Registered competitor names in preference order
# ---------------------------------------------------------------------------

COMPETITOR_NAMES: list[str] = [
    "isalhg_levenshtein",
    "hypergraph_wl_l1",
    "netlsd_l2",
    "hpd_jsd",
    "nauty_levi_edit",
    "degree_seq_l1",
]


# ---------------------------------------------------------------------------
# Distance computation helpers
# ---------------------------------------------------------------------------


def _safe_pairwise(dist_name: str, H1: SparseHypergraph, H2: SparseHypergraph) -> float | None:
    """Return pairwise distance or None if the computation fails."""
    try:
        d = get_distance(dist_name)
        return float(d.pairwise(H1, H2))
    except Exception:
        return None


def _timed_pairwise(
    dist_name: str,
    H1: SparseHypergraph,
    H2: SparseHypergraph,
    timeout_s: int,
) -> tuple[float | None, float, bool]:
    """Compute pairwise distance with a wall-clock timeout via a daemon thread.

    Parameters
    ----------
    dist_name : str
        Distance registry name.
    H1, H2 : SparseHypergraph
        Inputs.
    timeout_s : int
        Seconds to wait before giving up; the daemon thread may run longer.

    Returns
    -------
    tuple[float or None, float, bool]
        (distance_or_None, elapsed_s, timed_out).
    """
    result: list[float | None] = [None]
    exc_flag: list[bool] = [False]

    def _worker() -> None:
        try:
            d = get_distance(dist_name)
            result[0] = float(d.pairwise(H1, H2))
        except Exception:
            exc_flag[0] = True

    t_start = time.time()
    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    t.join(timeout=timeout_s)
    elapsed = time.time() - t_start
    timed_out = t.is_alive()
    return result[0], elapsed, timed_out


def compute_full_pairwise_matrix(
    steps: list[OfatStep],
    distance_name: str,
    per_step_timeout_s: int | None = None,
) -> tuple[list[list[float | None]], int]:
    """Compute the full (T+1)×(T+1) pairwise distance matrix.

    Uses the distance's ``matrix()`` method when no timeout is set (all
    fingerprints computed once, then rapidfuzz cdist — O(T) canonical calls
    instead of O(T²)).  When ``per_step_timeout_s`` is set, falls back to a
    per-pair loop with daemon-thread timeout; sets entries to None and stops
    accumulating once a pair exceeds the budget.

    Parameters
    ----------
    steps : list[OfatStep]
        OFAT sequence including the base at step 0.
    distance_name : str
        Distance registry name to evaluate.
    per_step_timeout_s : int or None
        Per-pair timeout in seconds.  None = no timeout (use matrix()).

    Returns
    -------
    tuple[list[list[float or None]], int]
        (D_matrix, T_distance_achieved) where T_distance_achieved is the last
        step index for which all distances from step 0 were computed.
        Without timeout, T_distance_achieved == len(steps) - 1.
    """
    n = len(steps)
    corpus = [s.hypergraph for s in steps]

    if per_step_timeout_s is None:
        # Fast path: bulk matrix() call
        try:
            d = get_distance(distance_name)
            mat = d.matrix(corpus)
            return [[float(mat[i, j]) for j in range(n)] for i in range(n)], n - 1
        except Exception:
            pass
        # Fallback: pairwise loop (slower; catches partially-unavailable deps)
        D: list[list[float | None]] = [
            [0.0 if i == j else None for j in range(n)] for i in range(n)
        ]
        for i in range(n):
            for j in range(i + 1, n):
                v = _safe_pairwise(distance_name, corpus[i], corpus[j])
                D[i][j] = v
                D[j][i] = v
        return D, n - 1

    # Timeout path: per-pair with daemon-thread timeout
    D_t: list[list[float | None]] = [[0.0 if i == j else None for j in range(n)] for i in range(n)]
    T_achieved = 0
    step_timings: list[float] = []

    for j in range(1, n):
        # Compute d(H_i, H_j) for all i < j; stop column if any pair times out
        col_ok = True
        col_timing: list[float] = []
        for i in range(j):
            v, elapsed, timed_out = _timed_pairwise(
                distance_name, corpus[i], corpus[j], per_step_timeout_s
            )
            col_timing.append(elapsed)
            if timed_out:
                col_ok = False
                step_timings.append(elapsed)
                break
            D_t[i][j] = v
            D_t[j][i] = v
        if not col_ok:
            # Mark remaining columns as None
            break
        T_achieved = j
        step_timings.extend(col_timing)

    return D_t, T_achieved


def compute_sequence_distances(
    steps: list[OfatStep],
    distance_names: list[str] = COMPETITOR_NAMES,
) -> dict[str, list[float | None]]:
    """Compute d_rep(H_0, H_t) for each representation and each step.

    Parameters
    ----------
    steps : list[OfatStep]
        OFAT sequence from generate_ofat_sequence; steps[0].step == 0 (the base).
    distance_names : list[str]
        Distance registry names to evaluate.

    Returns
    -------
    dict[str, list[float | None]]
        Map from distance name to list of floats (one per step, None on failure).
    """
    H_0 = steps[0].hypergraph
    result: dict[str, list[float | None]] = {}
    for name in distance_names:
        row: list[float | None] = []
        for s in steps:
            if s.step == 0:
                row.append(0.0)
            else:
                row.append(_safe_pairwise(name, H_0, s.hypergraph))
        result[name] = row
    return result


def monotone_fraction(d_from_base: list[float | None]) -> float:
    """Fraction of consecutive step pairs where d increases monotonically.

    Parameters
    ----------
    d_from_base : list[float | None]
        Per-step distances d(H_0, H_t); None entries are skipped.

    Returns
    -------
    float
        In [0, 1]; 1.0 means perfectly monotone increasing.
    """
    clean = [x for x in d_from_base if x is not None]
    if len(clean) < 2:
        return float("nan")
    total = len(clean) - 1
    increasing = sum(1 for a, b in zip(clean, clean[1:], strict=False) if b > a)
    return increasing / total


def compute_mds_trajectory(
    steps: list[OfatStep],
    distance_name: str = "isalhg_levenshtein",
    n_dims: int = 2,
) -> np.ndarray | None:
    """Compute a 2D classical-MDS embedding of the OFAT sequence.

    Parameters
    ----------
    steps : list[OfatStep]
        OFAT sequence.
    distance_name : str
        Distance to use for the pairwise matrix.
    n_dims : int
        Embedding dimensionality (2 for visualization).

    Returns
    -------
    numpy.ndarray of shape (T+1, n_dims), or None if the distance fails.
    """
    n = len(steps)
    D = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        for j in range(i + 1, n):
            v = _safe_pairwise(distance_name, steps[i].hypergraph, steps[j].hypergraph)
            if v is None:
                return None
            D[i, j] = D[j, i] = v
    if n < 2:
        return np.zeros((n, n_dims))
    return embed_classical(D, n_dims)


def _pairwise_matrix_to_np(D_list: list[list[float | None]]) -> np.ndarray | None:
    """Convert a list-of-lists pairwise matrix to a numpy array.

    Returns None if any off-diagonal entry is None (computation failed).

    Parameters
    ----------
    D_list : list[list[float or None]]
        Symmetric matrix from compute_full_pairwise_matrix.

    Returns
    -------
    numpy.ndarray or None
        Float64 array of same shape, or None on any failure.
    """
    n = len(D_list)
    D = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        for j in range(n):
            v = D_list[i][j]
            if v is None:
                return None
            D[i, j] = v
    return D


def compute_mds_from_matrix(
    D_list: list[list[float | None]],
    n_dims: int = 2,
) -> np.ndarray | None:
    """Compute classical-MDS embedding from a precomputed pairwise matrix.

    Parameters
    ----------
    D_list : list[list[float or None]]
        Full pairwise distance matrix.
    n_dims : int
        Embedding dimensionality.

    Returns
    -------
    numpy.ndarray of shape (n, n_dims), or None if any entry is None.
    """
    D = _pairwise_matrix_to_np(D_list)
    if D is None:
        return None
    n = D.shape[0]
    if n < 2:
        return np.zeros((n, n_dims))
    return embed_classical(D, n_dims)


def compute_nu_trajectory(
    steps: list[OfatStep],
    distance_name: str = "isalhg_levenshtein",
) -> list[float | None]:
    """Non-Euclidean mass nu for each prefix [H_0..H_t] of the sequence.

    Parameters
    ----------
    steps : list[OfatStep]
        OFAT sequence.
    distance_name : str
        Distance to use.

    Returns
    -------
    list[float | None]
        nu value per prefix-length; first entry (n=1) is 0.0 by definition.
    """
    nus: list[float | None] = [0.0]  # single point: nu=0
    for t in range(1, len(steps)):
        sub = steps[: t + 1]
        n = len(sub)
        D = np.zeros((n, n), dtype=np.float64)
        for i in range(n):
            for j in range(i + 1, n):
                v = _safe_pairwise(distance_name, sub[i].hypergraph, sub[j].hypergraph)
                if v is None:
                    nus.append(None)
                    break
                D[i, j] = D[j, i] = v
            else:
                continue
            break
        else:
            try:
                evals, _ = classical_mds(D)
                nus.append(neg_eigenvalue_mass(evals))
            except Exception:
                nus.append(None)
    return nus


def compute_nu_from_matrix(
    D_list: list[list[float | None]],
) -> list[float | None]:
    """Compute ν-trajectory from a precomputed full pairwise distance matrix.

    Uses prefix submatrices of the precomputed D without additional distance
    calls.  This is the efficient alternative to compute_nu_trajectory when
    the full pairwise matrix is already available.

    Parameters
    ----------
    D_list : list[list[float or None]]
        Full (T+1)×(T+1) pairwise distance matrix (symmetric, diagonal 0).

    Returns
    -------
    list[float or None]
        nu value per prefix [H_0..H_t]; entry t=0 is 0.0 by definition.
    """
    T_plus_1 = len(D_list)
    nus: list[float | None] = [0.0]  # prefix of length 1: no pairs, nu=0

    for t in range(1, T_plus_1):
        # Extract the (t+1)×(t+1) prefix submatrix.
        sub_size = t + 1
        D_sub = np.zeros((sub_size, sub_size), dtype=np.float64)
        ok = True
        for i in range(sub_size):
            for j in range(sub_size):
                v = D_list[i][j]
                if v is None:
                    ok = False
                    break
                D_sub[i, j] = v
            if not ok:
                break
        if not ok:
            nus.append(None)
            continue
        try:
            evals, _ = classical_mds(D_sub)
            nus.append(neg_eigenvalue_mass(evals))
        except Exception:
            nus.append(None)

    return nus


def mds_jump_stat(
    coords: np.ndarray | None,
) -> dict[str, float | None]:
    """Compute max single-step embedded jump and median step for an MDS trajectory.

    Parameters
    ----------
    coords : numpy.ndarray of shape (T+1, 2), or None
        MDS embedding of the OFAT sequence.

    Returns
    -------
    dict
        Keys: ``max_jump`` (float or None), ``median_step`` (float or None),
        ``ratio`` (float or None, = max_jump / median_step).
    """
    if coords is None or coords.shape[0] < 2:
        return {"max_jump": None, "median_step": None, "ratio": None}
    diffs = np.linalg.norm(np.diff(coords, axis=0), axis=1)
    max_j = float(diffs.max())
    med_j = float(np.median(diffs))
    ratio = (max_j / med_j) if med_j > 0.0 else None
    return {"max_jump": max_j, "median_step": med_j, "ratio": ratio}


def nu_sign_summary(nus: list[float | None]) -> str | None:
    """Summarize the ν-trajectory as a monotone-direction label.

    Parameters
    ----------
    nus : list[float or None]
        Output of compute_nu_from_matrix.

    Returns
    -------
    str or None
        One of ``'increases'``, ``'decreases'``, ``'near_zero'``, ``'mixed'``,
        or None if all entries are None.
    """
    valid = [v for v in nus if v is not None]
    if not valid:
        return None
    if max(abs(v) for v in valid) < 1e-6:
        return "near_zero"
    increasing = sum(1 for a, b in zip(valid, valid[1:], strict=False) if b > a)
    total = len(valid) - 1
    if total == 0:
        return "near_zero"
    frac = increasing / total
    if frac >= 0.75:
        return "increases"
    if frac <= 0.25:
        return "decreases"
    return "mixed"


# ---------------------------------------------------------------------------
# Rendering: spring-layout + convex-hull hyperedge patches
# ---------------------------------------------------------------------------


def _incidence_spring_layout(
    H: SparseHypergraph,
    rng: random.Random | None = None,
    iterations: int = 80,
) -> dict[str, np.ndarray]:
    """Compute a spring layout for the vertices of H using networkx.

    Builds the incidence bipartite graph (vertex-nodes and edge-nodes, connected
    iff vertex in edge) and runs spring_layout on it.  Only the vertex
    positions are returned (edge-nodes are discarded after layout).

    Parameters
    ----------
    H : SparseHypergraph
        Hypergraph to lay out.
    rng : random.Random or None
        Seed source for reproducibility.
    iterations : int
        Spring layout iteration count.

    Returns
    -------
    dict[str, numpy.ndarray]
        Map from role to position array: 'vertices' has shape (n_nodes, 2).
    """
    try:
        import networkx as nx
    except ImportError:
        # Fallback: circular layout
        angles = np.linspace(0, 2 * np.pi, H.n_nodes, endpoint=False)
        vpos = np.column_stack([np.cos(angles), np.sin(angles)])
        return {"vertices": vpos}

    G = nx.Graph()
    v_nodes = [f"v{i}" for i in range(H.n_nodes)]
    e_nodes = [f"e{j}" for j in range(H.n_edges)]
    G.add_nodes_from(v_nodes)
    G.add_nodes_from(e_nodes)
    for j in range(H.n_edges):
        for v in H.members(j):
            G.add_edge(v_nodes[v], e_nodes[j])

    seed_int: int | None = None
    if rng is not None:
        seed_int = rng.randint(0, 2**31)

    pos = nx.spring_layout(G, seed=seed_int, iterations=iterations)
    vpos = np.array([pos[f"v{i}"] for i in range(H.n_nodes)])
    return {"vertices": vpos}


def draw_hypergraph(
    H: SparseHypergraph,
    ax: Any,
    title: str = "",
    rng: random.Random | None = None,
) -> None:
    """Draw H on axes ax using the ONE G3 rendering convention.

    Convention (stated once here; identical to artifacts/g3/README.md):
    - 2D spring layout on the incidence bipartite graph (networkx spring_layout).
    - Hyperedges with >= 3 vertices: filled convex-hull polygon, alpha=0.25.
    - Hyperedges with 2 vertices: thick line segment, alpha=0.6.
    - Vertex dots: filled black circles, zorder=3.
    - Edge colors: tab10 palette, cycled over hyperedge index.

    Parameters
    ----------
    H : SparseHypergraph
        Hypergraph to draw.
    ax : matplotlib.axes.Axes
        Target axes.
    title : str
        Axes title.
    rng : random.Random or None
        Seed for reproducible layout.
    """
    from matplotlib import cm
    from scipy.spatial import ConvexHull

    layout = _incidence_spring_layout(H, rng=rng)
    vpos = layout["vertices"]

    palette = cm.tab10.colors

    ax.set_aspect("equal")
    ax.axis("off")
    if title:
        ax.set_title(title, fontsize=8, pad=2)

    for j in range(H.n_edges):
        members = list(H.members(j))
        color = palette[j % len(palette)]
        pts = vpos[members]
        if len(pts) >= 3:
            try:
                hull = ConvexHull(pts)
                hull_pts = pts[hull.vertices]
                from matplotlib.patches import Polygon

                poly = Polygon(
                    hull_pts,
                    closed=True,
                    facecolor=color,
                    edgecolor=color,
                    alpha=0.25,
                    linewidth=1.0,
                    zorder=1,
                )
                ax.add_patch(poly)
            except Exception:
                ax.plot(pts[:, 0], pts[:, 1], "-", color=color, alpha=0.4, linewidth=2)
        elif len(pts) == 2:
            ax.plot(pts[:, 0], pts[:, 1], "-", color=color, alpha=0.6, linewidth=2.5, zorder=2)

    if H.n_nodes > 0:
        ax.scatter(vpos[:, 0], vpos[:, 1], s=30, c="black", zorder=3)

    if vpos.shape[0] > 0:
        margin = 0.15
        xmin, xmax = vpos[:, 0].min(), vpos[:, 0].max()
        ymin, ymax = vpos[:, 1].min(), vpos[:, 1].max()
        ax.set_xlim(xmin - margin, xmax + margin)
        ax.set_ylim(ymin - margin, ymax + margin)


def make_filmstrip(
    steps: list[OfatStep],
    axis: OfatAxis,
    output_path: Path,
    seed: int = 42,
) -> None:
    """Save a 5-panel filmstrip (H_0, H_{T/4}, H_{T/2}, H_{3T/4}, H_T).

    Parameters
    ----------
    steps : list[OfatStep]
        OFAT sequence.
    axis : OfatAxis
        Axis name (for title).
    output_path : Path
        Where to write the PNG.
    seed : int
        RNG seed for reproducible spring layout.
    """
    import matplotlib.pyplot as plt

    T = len(steps) - 1
    indices = [0, T // 4, T // 2, 3 * T // 4, T]
    indices = [min(i, T) for i in indices]

    fig, axes = plt.subplots(1, 5, figsize=(14, 3))
    rng = random.Random(seed)
    for ax, idx in zip(axes, indices, strict=False):
        s = steps[idx]
        label = "H_{0}" if idx == 0 else f"H_{{{idx}}}"
        budget = s.budget_from_base
        title = f"{label}\nn={s.hypergraph.n_nodes}, m={s.hypergraph.n_edges}, b={budget}"
        draw_hypergraph(s.hypergraph, ax, title=title, rng=rng)

    fig.suptitle(f"G3 filmstrip — axis {axis.value}", fontsize=10, y=1.01)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Response curve and MDS trajectory figures
# ---------------------------------------------------------------------------


def make_response_curve(
    steps: list[OfatStep],
    distances: dict[str, list[float | None]],
    axis: OfatAxis,
    output_path: Path,
) -> None:
    """Save a response curve figure: d_rep(H_0, H_t) vs step for all reps.

    Parameters
    ----------
    steps : list[OfatStep]
        OFAT sequence.
    distances : dict
        Output of compute_sequence_distances.
    axis : OfatAxis
        Axis name (for title).
    output_path : Path
        Where to write the PNG.
    """
    import matplotlib.pyplot as plt

    budgets = [s.budget_from_base for s in steps]
    t_vals = [s.step for s in steps]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

    line_styles = ["-", "--", "-.", ":", "-", "--"]
    colors = ["tab:blue", "tab:orange", "tab:green", "tab:red", "tab:purple", "tab:brown"]

    for (name, vals), ls, color in zip(distances.items(), line_styles, colors, strict=False):
        clean = [(t, v) for t, v in zip(t_vals, vals, strict=False) if v is not None]
        if not clean:
            continue
        ts, vs = zip(*clean, strict=False)
        label = name.replace("_", " ")
        ax1.plot(ts, vs, ls, color=color, label=label, marker="o", markersize=3)
        ax2.plot(budgets[: len(ts)], vs, ls, color=color, label=label, marker="o", markersize=3)

    ax1.set_xlabel("Step t")
    ax1.set_ylabel("d(H_0, H_t)")
    ax1.set_title(f"Response curve — {axis.value}")
    ax1.legend(fontsize=7)
    ax1.grid(True, alpha=0.3)

    ax2.set_xlabel("Budget from base (Qin cost)")
    ax2.set_ylabel("d(H_0, H_t)")
    ax2.set_title(f"Response vs budget — {axis.value}")
    ax2.legend(fontsize=7)
    ax2.grid(True, alpha=0.3)

    # Monotone fractions annotation
    isal_vals = distances.get("isalhg_levenshtein", [])
    mf = monotone_fraction(isal_vals)
    ax1.set_xlabel(f"Step t  (IsalHG monotone fraction: {mf:.2f})")

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close(fig)


def make_mds_trajectory(
    steps: list[OfatStep],
    coords: np.ndarray | None,
    axis: OfatAxis,
    output_path: Path,
    coords_nauty: np.ndarray | None = None,
) -> None:
    """Save a 2D MDS trajectory figure showing both IsalHG and nauty embeddings.

    Parameters
    ----------
    steps : list[OfatStep]
        OFAT sequence.
    coords : numpy.ndarray of shape (T+1, 2) or None
        IsalHG MDS embedding; if None, the figure shows a skip notice.
    axis : OfatAxis
        Axis name.
    output_path : Path
        Where to write the PNG.
    coords_nauty : numpy.ndarray of shape (T+1, 2) or None
        Nauty MDS embedding; if None, subplot is skipped.
    """
    import matplotlib.pyplot as plt

    n_panels = 2 if coords_nauty is not None else 1
    fig, axes = plt.subplots(1, n_panels, figsize=(6 * n_panels, 5))
    if n_panels == 1:
        axes = [axes]

    for ax, c, label in zip(
        axes,
        [coords, coords_nauty],
        ["IsalHG d_I", "nauty_levi_edit"],
        strict=False,
    ):
        if c is None:
            ax.text(
                0.5,
                0.5,
                "MDS computation unavailable",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
        else:
            x, y = c[:, 0], c[:, 1]
            ax.plot(x, y, "-o", color="tab:blue", markersize=5, zorder=2)
            for s, xi, yi in zip(steps, x, y, strict=False):
                ax.text(xi, yi, str(s.step), fontsize=7, ha="left", va="bottom")
            ax.scatter([x[0]], [y[0]], color="green", s=80, zorder=3, label="H_0")
            ax.scatter([x[-1]], [y[-1]], color="red", s=80, zorder=3, label=f"H_{len(steps) - 1}")
            ax.set_xlabel("MDS dim 1")
            ax.set_ylabel("MDS dim 2")
            ax.legend(fontsize=8)
            ax.grid(True, alpha=0.3)
        ax.set_title(f"MDS trajectory ({label}) — {axis.value}")

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close(fig)


def make_nu_trajectory(
    steps: list[OfatStep],
    nus: list[float | None],
    axis: OfatAxis,
    output_path: Path,
) -> None:
    """Save a nu-trajectory figure.

    Parameters
    ----------
    steps : list[OfatStep]
        OFAT sequence.
    nus : list[float or None]
        Per-prefix nu values from compute_nu_from_matrix.
    axis : OfatAxis
        Axis name.
    output_path : Path
        Where to write the PNG.
    """
    import matplotlib.pyplot as plt

    t_vals = [s.step for s in steps]
    clean = [(t, v) for t, v in zip(t_vals, nus, strict=False) if v is not None]

    fig, ax = plt.subplots(figsize=(6, 4))
    if clean:
        ts, vs = zip(*clean, strict=False)
        ax.plot(ts, vs, "-o", color="tab:blue", markersize=5)
        ax.axhline(0.0, color="gray", linestyle="--", alpha=0.5)
        ax.set_xlabel("Prefix length (number of sequence steps included)")
        ax.set_ylabel("Non-Euclidean mass ν")
    else:
        ax.text(
            0.5, 0.5, "nu computation unavailable", ha="center", va="center", transform=ax.transAxes
        )

    ax.set_title(f"ν-trajectory — {axis.value}")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Result record (JSON-serializable)
# ---------------------------------------------------------------------------


@dataclass
class G3AxisResult:
    """Analysis result for one OFAT axis sequence.

    Fields
    ------
    axis : str
        OfatAxis.value string.
    base_design : str
        Name of the Stratum A base used.
    T_achieved : int
        Number of steps actually computed (may be < T_requested if axis exhausted).
    budgets : list[int]
        Qin budget per step.
    n_nodes : list[int]
        n per step.
    n_edges : list[int]
        m per step.
    distances : dict[str, list[float or None]]
        d_rep(H_0, H_t) per rep per step.
    monotone_fractions : dict[str, float]
        Per-rep monotone fraction.
    d_matrix_isalhg : list[list[float or None]]
        Full (T+1)×(T+1) pairwise d_I matrix.
    d_matrix_nauty : list[list[float or None]]
        Full (T+1)×(T+1) pairwise nauty distance matrix.
    mds_coords_isalhg : list[list[float]] or None
        2D MDS embedding coords for IsalHG (shape (T+1, 2)).
    mds_coords_nauty : list[list[float]] or None
        2D MDS embedding coords for nauty.
    continuity_isalhg : dict[str, float or None]
        MDS trajectory jump stat for IsalHG: max_jump, median_step, ratio.
    continuity_nauty : dict[str, float or None]
        MDS trajectory jump stat for nauty.
    nu_trajectory : list[float or None]
        nu per prefix (IsalHG distance), computed from d_matrix_isalhg.
    nu_sign : str or None
        Monotone direction of ν: 'increases', 'decreases', 'near_zero', 'mixed'.
    vm_k : int or None
        Fixed VM k used to encode all M3 sequence members (None for other axes).
    wall_clock_s : float
        Total analysis time in seconds.
    """

    axis: str
    base_design: str
    T_achieved: int
    budgets: list[int]
    n_nodes: list[int]
    n_edges: list[int]
    distances: dict[str, list[float | None]]
    monotone_fractions: dict[str, float]
    d_matrix_isalhg: list[list[float | None]]
    d_matrix_nauty: list[list[float | None]]
    mds_coords_isalhg: list[list[float]] | None
    mds_coords_nauty: list[list[float]] | None
    continuity_isalhg: dict[str, float | None]
    continuity_nauty: dict[str, float | None]
    nu_trajectory: list[float | None]
    nu_sign: str | None
    vm_k: int | None
    wall_clock_s: float
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d


# ---------------------------------------------------------------------------
# Main runner: run one axis, save all artifacts
# ---------------------------------------------------------------------------


def run_ofat_axis(
    H_0: SparseHypergraph,
    axis: OfatAxis,
    base_design_name: str,
    T: int,
    rng: random.Random,
    output_dir: Path,
    distance_names: list[str] = COMPETITOR_NAMES,
    vm_k: int | None = None,
    per_step_timeout_s: int | None = None,
) -> G3AxisResult:
    """Run one OFAT axis, compute all metrics, save all artifacts.

    Computes the full (T+1)×(T+1) pairwise matrix for both IsalHG and nauty,
    derives the MDS trajectory, jump/continuity statistics, and ν-trajectory
    from the precomputed matrices (no repeated distance calls).

    Parameters
    ----------
    H_0 : SparseHypergraph
        Connected base hypergraph.
    axis : OfatAxis
        Which axis.
    base_design_name : str
        Human-readable name for the base (used in titles and JSON).
    T : int
        Target steps.
    rng : random.Random
        Seeded RNG.
    output_dir : Path
        Where to save PNGs and JSON.
    distance_names : list[str]
        Representations to evaluate.
    vm_k : int or None
        Fixed VM k used for encoding M3 sequences (None for other axes).
    per_step_timeout_s : int or None
        Per-pair timeout for the IsalHG pairwise matrix computation (seconds).
        None = no timeout (fast path: matrix() call).  Set for axes whose
        canonical encoder is expensive at high arity (e.g. loose_path_k5_n13).
        When a timeout is hit, remaining matrix entries are None and
        T_distance_achieved < T_achieved_sequence; the gap is recorded in extra.

    Returns
    -------
    G3AxisResult
        All computed metrics.
    """
    t0 = time.time()

    steps = generate_ofat_sequence(H_0, axis, T=T, rng=rng)
    T_sequence = len(steps) - 1

    # Row-distance: d(H_0, H_t) for all competitors.
    # When per_step_timeout_s is set, exclude isalhg_levenshtein from this call
    # to avoid unguarded slow calls (e.g., loose_path_k5 at arity 7+ takes >90s
    # per pair with no timeout).  The row-0 values are extracted from d_mat_isal
    # after the matrix computation instead.
    if per_step_timeout_s is not None and "isalhg_levenshtein" in distance_names:
        names_for_seq = [n for n in distance_names if n != "isalhg_levenshtein"]
    else:
        names_for_seq = distance_names
    distances = compute_sequence_distances(steps, names_for_seq)

    # Full pairwise matrices (each pair computed exactly once)
    print(
        f"    computing full pairwise IsalHG matrix ({len(steps)} steps, "
        f"timeout={per_step_timeout_s}s) ..."
    )
    d_mat_isal, T_dist_isal = compute_full_pairwise_matrix(
        steps, "isalhg_levenshtein", per_step_timeout_s=per_step_timeout_s
    )

    # Restore isalhg row-0 distances from the pairwise matrix (timeout-safe)
    if per_step_timeout_s is not None and "isalhg_levenshtein" in distance_names:
        distances["isalhg_levenshtein"] = [d_mat_isal[0][t] for t in range(len(steps))]

    mf = {name: monotone_fraction(vals) for name, vals in distances.items()}

    print(f"    computing full pairwise nauty matrix ({len(steps)} steps) ...")
    d_mat_nauty, _T_dist_nauty = compute_full_pairwise_matrix(steps, "nauty_levi_edit")

    # MDS trajectories from precomputed matrices
    coords_isal = compute_mds_from_matrix(d_mat_isal)
    coords_nauty = compute_mds_from_matrix(d_mat_nauty)

    # Jump/continuity statistics
    continuity_isal = mds_jump_stat(coords_isal)
    continuity_nauty_d = mds_jump_stat(coords_nauty)

    # ν-trajectory from precomputed IsalHG matrix (no repeated distance calls)
    nus = compute_nu_from_matrix(d_mat_isal)
    nu_sign = nu_sign_summary(nus)

    t_elapsed = time.time() - t0

    # Serialize coords (list of lists for JSON)
    def _coords_to_list(c: np.ndarray | None) -> list[list[float]] | None:
        if c is None:
            return None
        return [[float(x) for x in row] for row in c]

    # Build extra metadata (quantitative justification for partial results)
    extra: dict[str, Any] = {}
    if per_step_timeout_s is not None and T_dist_isal < T_sequence:
        extra["T_achieved_sequence"] = T_sequence
        extra["T_achieved_distance"] = T_dist_isal
        extra["per_step_timeout_s"] = per_step_timeout_s
        extra["canonical_cost_note"] = (
            f"loose_path_k5_n13 sequence generator achieved T={T_sequence} steps. "
            f"d_I pairwise computation feasible for steps 0..{T_dist_isal} only; "
            f"step {T_dist_isal + 1}+ timed out at {per_step_timeout_s}s per pair. "
            f"Root cause: tie-complete canonical encoder is exponential in arity "
            f"for loose 5-paths (arity 5: ~0.05s/call; arity 6: ~6s/call; "
            f"arity 7: DNF >90s/call). Full d_I matrix requires HPC or C++ engine."
        )

    result = G3AxisResult(
        axis=axis.value,
        base_design=base_design_name,
        T_achieved=T_sequence,
        budgets=[s.budget_from_base for s in steps],
        n_nodes=[s.hypergraph.n_nodes for s in steps],
        n_edges=[s.hypergraph.n_edges for s in steps],
        distances=distances,
        monotone_fractions=mf,
        d_matrix_isalhg=d_mat_isal,
        d_matrix_nauty=d_mat_nauty,
        mds_coords_isalhg=_coords_to_list(coords_isal),
        mds_coords_nauty=_coords_to_list(coords_nauty),
        continuity_isalhg=continuity_isal,
        continuity_nauty=continuity_nauty_d,
        nu_trajectory=nus,
        nu_sign=nu_sign,
        vm_k=vm_k,
        wall_clock_s=t_elapsed,
        extra=extra,
    )

    axis_slug = axis.value.replace(" ", "_")
    base_slug = base_design_name.replace(" ", "_").replace("(", "").replace(")", "")

    # Save filmstrip
    film_path = output_dir / f"filmstrip_{axis_slug}_{base_slug}.png"
    make_filmstrip(steps, axis, film_path, seed=42)

    # Save response curve
    resp_path = output_dir / f"response_curve_{axis_slug}_{base_slug}.png"
    make_response_curve(steps, distances, axis, resp_path)

    # Save MDS trajectory (with nauty overlay)
    mds_path = output_dir / f"mds_traj_{axis_slug}_{base_slug}.png"
    make_mds_trajectory(steps, coords_isal, axis, mds_path, coords_nauty=coords_nauty)

    # Save nu trajectory
    nu_path = output_dir / f"nu_traj_{axis_slug}_{base_slug}.png"
    make_nu_trajectory(steps, nus, axis, nu_path)

    # Save JSON result
    json_path = output_dir / f"result_{axis_slug}_{base_slug}.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w") as f:
        json.dump(result.to_dict(), f, indent=2, default=str)

    return result


# ---------------------------------------------------------------------------
# Default G3 experiment: all five axes with ADMITTED bases (n <= 20)
# ---------------------------------------------------------------------------


def default_g3_config() -> list[dict[str, Any]]:
    """Return the default OFAT axis configurations.

    Each entry specifies axis, base builder name, T, and seed.
    Only ADMITTED designs with n <= 20 are used as bases.

    M3 discipline: each M3 sub-experiment uses a FIXED VM k for all members
    of the sequence.  The package default k=10 is used throughout (encoding
    each member at k=10 regardless of the sequence's max arity).  This field
    is stored as ``vm_k`` in the result JSON.

    Returns
    -------
    list[dict]
        Config entries with keys: axis, base_name, T, seed, vm_k (M3 only).
    """
    return [
        # M1: vertex growth — tight 3-cycle (n=5, m=5)
        {"axis": "M1", "base_name": "tight_cycle_k3_n5", "T": 10, "seed": 1001},
        # M2: densification — loose 3-path (n=9, m=4)
        {"axis": "M2", "base_name": "loose_path_k3_n9", "T": 10, "seed": 1002},
        # M3 k=3: arity increase — Fano plane (n=7, m=7, k=3)
        # Fixed VM k=10 (package default) for all members of this sequence.
        {"axis": "M3", "base_name": "fano_plane_k3", "T": 10, "seed": 1003, "vm_k": 10},
        # M3 k=4: arity increase — tight 4-path (n=6, m=3, k=4)
        # Fixed VM k=10 (package default) for all members.
        {"axis": "M3", "base_name": "tight_path_k4_n6", "T": 5, "seed": 1004, "vm_k": 10},
        # M3 k=5 (tight): arity increase — tight 5-path (n=7, m=3, k=5).
        # T_achieved=3: tight path exhausts all vertices in 3 arity-growth steps.
        # Fixed VM k=10 (package default) for all members.
        {"axis": "M3", "base_name": "tight_path_k5_n7", "T": 4, "seed": 1005, "vm_k": 10},
        # M3 k=5 (loose): loose 5-path (n=13, m=3, k=5) — longer sequence.
        # n=13 allows each edge to grow from arity 5 up to arity 13 (8 steps/edge),
        # giving >=10 achievable steps.  Fixed VM k=10.
        # per_step_timeout_s=45: the tie-complete canonical encoder is infeasible
        # locally at arity >= 7 (arity 5: ~0.05s/call, arity 6: ~6s/call,
        # arity 7: DNF >90s/call).  The partial d_I matrix (T_distance_achieved=1)
        # + quantitative timing justification are recorded in extra.
        {
            "axis": "M3",
            "base_name": "loose_path_k5_n13",
            "T": 10,
            "seed": 1008,
            "vm_k": 10,
            "per_step_timeout_s": 45,
        },
        # M4: incidence edit — STS(9) (n=9, m=12, k=3)
        {"axis": "M4", "base_name": "sts9_k3", "T": 10, "seed": 1006},
        # M5: symmetry break — GQ(2,2) doily (n=15, m=15, k=3, high symmetry)
        {"axis": "M5", "base_name": "gq22_k3", "T": 10, "seed": 1007},
    ]


def _build_base(base_name: str) -> SparseHypergraph:
    """Construct the Stratum A base hypergraph for a given config name.

    Parameters
    ----------
    base_name : str
        One of the names in default_g3_config.

    Returns
    -------
    SparseHypergraph
        The base hypergraph.

    Raises
    ------
    ValueError
        If the name is not recognized.
    """
    from isalhg.datasets.synthetic.designs import fano_plane, gq_2_2_doily, sts_9
    from isalhg.datasets.synthetic.known_design_catalog import (
        loose_path,
        tight_cycle,
        tight_path,
    )

    mapping: dict[str, SparseHypergraph] = {
        "tight_cycle_k3_n5": tight_cycle(3, 5),
        "loose_path_k3_n9": loose_path(3, 4),
        "fano_plane_k3": fano_plane(),
        "tight_path_k4_n6": tight_path(4, 3),
        "tight_path_k5_n7": tight_path(5, 3),
        # loose_path(5, 3): n = 3*(5-1)+1 = 13, m = 3, arity 5 per edge.
        # Each edge shares 1 vertex with the next; 8 non-member vertices per edge.
        "loose_path_k5_n13": loose_path(5, 3),
        "sts9_k3": sts_9(),
        "gq22_k3": gq_2_2_doily(),
    }
    if base_name not in mapping:
        raise ValueError(f"Unknown base_name {base_name!r}; valid: {list(mapping)}")
    return mapping[base_name]


def _axis_from_str(axis_str: str) -> OfatAxis:
    mapping = {
        "M1": OfatAxis.M1,
        "M2": OfatAxis.M2,
        "M3": OfatAxis.M3,
        "M4": OfatAxis.M4,
        "M5": OfatAxis.M5,
    }
    if axis_str not in mapping:
        raise ValueError(f"Unknown axis {axis_str!r}; valid: {list(mapping)}")
    return mapping[axis_str]


def run_default_g3(
    output_dir: Path | None = None,
    distance_names: list[str] = COMPETITOR_NAMES,
) -> list[G3AxisResult]:
    """Run the full default G3 OFAT experiment.

    Parameters
    ----------
    output_dir : Path or None
        Where to save artifacts. Defaults to artifacts/g3/ relative to repo root.
    distance_names : list[str]
        Distance representations to evaluate.

    Returns
    -------
    list[G3AxisResult]
        One result per axis config.
    """
    if output_dir is None:
        output_dir = Path(__file__).parent.parent.parent / "artifacts" / "g3"
    output_dir.mkdir(parents=True, exist_ok=True)

    configs = default_g3_config()
    results: list[G3AxisResult] = []

    for cfg in configs:
        axis = _axis_from_str(cfg["axis"])
        base_name = cfg["base_name"]
        T = cfg["T"]
        seed = cfg["seed"]
        vm_k = cfg.get("vm_k")
        per_step_timeout_s = cfg.get("per_step_timeout_s")
        H_0 = _build_base(base_name)
        rng = random.Random(seed)
        print(f"[G3] Running axis={axis.value} base={base_name} T={T} seed={seed}")
        result = run_ofat_axis(
            H_0=H_0,
            axis=axis,
            base_design_name=base_name,
            T=T,
            rng=rng,
            output_dir=output_dir,
            distance_names=distance_names,
            vm_k=vm_k,
            per_step_timeout_s=per_step_timeout_s,
        )
        mf_isal = result.monotone_fractions.get("isalhg_levenshtein", float("nan"))
        jump_isal = result.continuity_isalhg.get("max_jump")
        jump_nauty = result.continuity_nauty.get("max_jump")
        print(
            f"  -> T_achieved={result.T_achieved} "
            f"wall_clock={result.wall_clock_s:.1f}s "
            f"IsalHG_mf={mf_isal:.2f} "
            f"nu_sign={result.nu_sign} "
            f"jump_isal={jump_isal} jump_nauty={jump_nauty}"
        )
        results.append(result)

    return results
