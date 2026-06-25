"""Cohort-axes figure for the preprint.

Generates a single 5-panel figure showing how the two live generator
axes ``(n, c)`` reshape an Erdős-Rényi hypergraph at fixed arity
``r = 3``. The panels are drawn from the **actual sweep grid** of
PREPRINT.md §12.4 — `n ∈ {8, 12, 16, 20, 24, 28}` × `r = 3` × `c ∈
{1.0, 1.5, 2.0}` — under the connectivity policy of §12.4-NEW
(*ER conditional on connectivity*, deterministic reject-resample).

Panels (one baseline + two `n` variations + two `c` variations):

==============  ===  ===  ===  ============
panel           n    r    c    varied axis
==============  ===  ===  ===  ============
1 smaller n      8   3    1.5  n (down)
2 baseline      16   3    1.5  -
3 larger n      25   3    1.5  n (up)
4 sparser       16   3    1.0  c (down)
5 denser        16   3    2.0  c (up)
==============  ===  ===  ===  ============

Each panel caption carries the cohort axes (``n``, ``r``, ``c``), the
realised generator probability ``p = c·n/C(n, r)``, the number of ER
reject-resample attempts taken to draw a connected sample (1 ≡ no
resample), the realised edge count ``m``, the mean vertex degree, the
number of connected components (CC, always 1 by construction), and
the length of the canonical fingerprint produced by ``pynauty_levi``
on the displayed instance. The fingerprint-length quantity ties the
figure directly to the preprint's headline characterisation
(PREPRINT.md §4.4).

Usage
-----
::

    # default backend (xgi)
    python experiments/preprint/data/visualize_cohort_axes.py

    # specific backend
    python experiments/preprint/data/visualize_cohort_axes.py --backend hypernetx

    # one figure per registered viz backend
    python experiments/preprint/data/visualize_cohort_axes.py --all-backends

    # custom seed / output dir
    python experiments/preprint/data/visualize_cohort_axes.py \
        --seed 7 --output-dir experiments/preprint/data/figures
"""

from __future__ import annotations

import argparse
import logging
import math
from dataclasses import dataclass
from pathlib import Path

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.datasets.synthetic.erdos_renyi import UniformErdosRenyiHypergraphs
from isalhg.iso_backends.registry import get_backend
from isalhg.viz import cohort_grid_figure
from isalhg.viz.registry import available_backends
from isalhg.viz.style import save_figure

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _PanelSpec:
    label: str
    n: int
    r: int
    c: float


PANELS: tuple[_PanelSpec, ...] = (
    _PanelSpec("Smaller N", 8, 3, 1.5),
    _PanelSpec("Baseline", 16, 3, 1.5),
    _PanelSpec("Larger N", 25, 3, 1.5),
    _PanelSpec("Sparser", 16, 3, 1.0),
    _PanelSpec("Denser", 16, 3, 2.0),
)


# pynauty_levi is the universal fingerprint backend for the captions:
# it handles disconnected hypergraphs (unlike isalhg's greedy_min, decision
# B11) and runs in microseconds on n <= 20. The length of the canonical
# Levi-graph certificate is reported as a per-panel scientific scalar.
_FP_BACKEND_NAME: str = "pynauty_levi"


def _mean_degree(H: SparseHypergraph) -> float:
    if H.n_nodes == 0:
        return 0.0
    return sum(H.degree(v) for v in H.nodes()) / H.n_nodes


def _n_connected_components(H: SparseHypergraph) -> int:
    """Connected-component count over the primal graph (BFS)."""
    seen: set[int] = set()
    count = 0
    primal = H.primal_graph()
    for v in H.nodes():
        if v in seen:
            continue
        count += 1
        stack = [v]
        while stack:
            u = stack.pop()
            if u in seen:
                continue
            seen.add(u)
            stack.extend(primal.get(u, ()))
    return count


def _build_panel(
    spec: _PanelSpec,
    seed: int,
    fp_backend: object,
) -> tuple[str, str, SparseHypergraph]:
    """Materialise the panel's hypergraph, bold label, and minimal subtitle.

    Uses ``require_connected=True`` (PREPRINT.md §12.4-NEW) so the
    rendered hypergraph matches the conditional-on-connectivity
    distribution the benchmark sweep actually fingerprinted.

    Subtitle carries only the generator inputs ``(n, r, c, seed)`` —
    the four-tuple that uniquely identifies the hypergraph under the
    sweep's reject-resample. Derived quantities (edge count, mean
    degree, fingerprint length, ER probability) are dropped; readers
    who want them can recompute from the YAML / per-cell JSON.
    """
    ds = UniformErdosRenyiHypergraphs(
        n=spec.n,
        r=spec.r,
        c=spec.c,
        seed=seed,
        require_connected=True,
    )
    item = next(iter(ds))
    H = item.hypergraph
    # Diagnostics logged but not rendered in the figure.
    p = spec.c * spec.n / math.comb(spec.n, spec.r)
    mean_deg = _mean_degree(H)
    n_cc = _n_connected_components(H)
    attempts = int(item.extra.get("connected_attempts", 1))
    fp_len = len(fp_backend.fingerprint(H))  # type: ignore[attr-defined]
    subtitle = f"n={spec.n}, r={spec.r}, c={spec.c:g}, seed={seed}"
    logger.info(
        "panel %-13s n=%-3d r=%-2d c=%-4g seed=%d p=%.3e attempts=%d m=%d <deg>=%.2f CC=%d fp=%dB",
        spec.label,
        spec.n,
        spec.r,
        spec.c,
        seed,
        p,
        attempts,
        H.n_edges,
        mean_deg,
        n_cc,
        fp_len,
    )
    return spec.label, subtitle, H


def _render_one(backend: str, seed: int, output_dir: Path) -> list[Path]:
    fp_backend = get_backend(_FP_BACKEND_NAME)
    panels = [_build_panel(spec, seed, fp_backend) for spec in PANELS]
    fig = cohort_grid_figure(
        panels,
        backend=backend,
        n_columns=5,
        figsize=(17.0, 5.8),
        overall_title=None,
        label_fontsize=13,
        subtitle_fontsize=11,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = save_figure(
        fig,
        output_dir / f"cohort_axes_{backend}_seed{seed}",
        formats=("pdf", "png"),
    )
    import matplotlib.pyplot as plt

    plt.close(fig)
    for p in paths:
        logger.info("wrote %s", p)
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--backend",
        default="xgi",
        help="viz backend name (xgi | hypernetx | hypergraphx); ignored when --all-backends is set",
    )
    parser.add_argument(
        "--all-backends",
        action="store_true",
        help="render one figure per registered viz backend",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="generator seed (default: 0)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("experiments/preprint/data/figures"),
        help="directory for the saved figures",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    backends_to_render: tuple[str, ...]
    if args.all_backends:
        backends_to_render = available_backends()
        logger.info("rendering for backends: %s", list(backends_to_render))
    else:
        backends_to_render = (args.backend,)

    total_paths: list[Path] = []
    for backend in backends_to_render:
        total_paths.extend(_render_one(backend, args.seed, args.output_dir))

    print("wrote:")
    for p in total_paths:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
