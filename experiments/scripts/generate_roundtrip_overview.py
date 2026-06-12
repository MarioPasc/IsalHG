"""Roundtrip overview figures.

Generates the IsalHG analogue of IsalSR's ``generate_algorithm_overview.py``
across multiple hypergraph fixtures and multiple visualisation backends.

For each ``(hypergraph, backend)`` pair the script emits, into the
output directory and in ``pdf + svg + png``:

- ``{H}_{b}_start``        -- single-column initial-state card
- ``{H}_{b}_end``          -- single-column final-state card
- ``{H}_{b}_s2h_steps``    -- N-column S2H step strip
- ``{H}_{b}_h2s_steps``    -- N-column H2S step strip
- ``{H}_{b}_roundtrip``    -- H2S on top, S2H on bottom, shared columns

It also dumps, once per hypergraph (backend-agnostic), the JSON traces:

- ``{H}_trace_h2s.json``
- ``{H}_trace_s2h.json``

The S2H trace is obtained by replaying the canonical string through
:meth:`StringToHypergraph.run_with_trace`. The H2S trace is the default
:meth:`H2SAlgorithm.encode_with_trace` (which by construction also
delegates to the S2H interpreter -- the round-trip invariant
``S2H(H2S(H)) ~ H`` makes the two snapshot streams identical when the
same algorithm and the same ``k`` are used; the framing is what
differs).

Usage::

    python -m experiments.scripts.generate_roundtrip_overview \\
        --out-dir /media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/roundtrip \\
        --backends xgi hypernetx hypergraphx \\
        --n-steps 7
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # non-interactive; safe under headless runs
import matplotlib.pyplot as plt

from isalhg.core.algorithms.greedy_min import GreedyMin
from isalhg.core.canonical import required_k
from isalhg.core.instructions import serialize
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.core.string_to_hypergraph import StringToHypergraph
from isalhg.core.trace import dump_trace
from isalhg.viz.composite import (
    roundtrip_figure,
    single_card_figure,
    steps_figure,
)
from isalhg.viz.registry import available_backends
from isalhg.viz.style import apply_ieee_style, save_figure

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Fixtures (inline; sibling copies of the ``tests/conftest.py`` versions)
# ---------------------------------------------------------------------------


def build_fano_plane() -> SparseHypergraph:
    """Fano plane STS(7), the classical 3-uniform symmetric design."""
    lines = [
        frozenset({0, 1, 2}),
        frozenset({0, 3, 4}),
        frozenset({0, 5, 6}),
        frozenset({1, 3, 5}),
        frozenset({1, 4, 6}),
        frozenset({2, 3, 6}),
        frozenset({2, 4, 5}),
    ]
    return SparseHypergraph(n_nodes=7, hyperedges=lines)


def build_sts9() -> SparseHypergraph:
    """The unique Steiner Triple System STS(9), realised as AG(2, 3)."""
    blocks = [
        frozenset({0, 1, 2}),
        frozenset({3, 4, 5}),
        frozenset({6, 7, 8}),
        frozenset({0, 3, 6}),
        frozenset({1, 4, 7}),
        frozenset({2, 5, 8}),
        frozenset({0, 4, 8}),
        frozenset({1, 5, 6}),
        frozenset({2, 3, 7}),
        frozenset({0, 5, 7}),
        frozenset({1, 3, 8}),
        frozenset({2, 4, 6}),
    ]
    return SparseHypergraph(n_nodes=9, hyperedges=blocks)


HYPERGRAPHS: dict[str, callable] = {  # type: ignore[type-arg]
    "fano_plane": build_fano_plane,
    "sts_9": build_sts9,
}


# ---------------------------------------------------------------------------
# Per-hypergraph driver
# ---------------------------------------------------------------------------


def _emit_one(
    H_name: str,
    H: SparseHypergraph,
    out_dir: Path,
    *,
    backends: tuple[str, ...],
    n_steps: int,
    algorithm: str,
) -> None:
    if algorithm != "greedy_min":
        raise ValueError(f"only 'greedy_min' is supported in this version, got {algorithm!r}")
    k = required_k(H)
    algo = GreedyMin(k=k)

    logger.info("[%s] encoding H (n=%d, m=%d, k=%d)", H_name, H.n_nodes, H.n_edges, k)
    tokens, trace_h2s = algo.encode_with_trace(H)

    interpreter = StringToHypergraph(
        tokens,
        k=k,
        n_vertex_labels=H.n_vertex_labels,
        n_edge_labels=H.n_edge_labels,
    )
    _, trace_s2h = interpreter.run_with_trace(direction="s2h")

    canonical_str = serialize(list(tokens))
    logger.info(
        "[%s] canonical: %d tokens, %d snapshots, |w*|=%d chars",
        H_name,
        len(tokens),
        len(trace_h2s.snapshots),
        len(canonical_str),
    )

    # JSON traces (once per hypergraph)
    dump_trace(trace_h2s, out_dir / f"{H_name}_trace_h2s.json")
    dump_trace(trace_s2h, out_dir / f"{H_name}_trace_s2h.json")

    tokens_tuple = tuple(tokens)

    for backend in backends:
        logger.info("[%s][%s] rendering figures", H_name, backend)

        # 1. S2H start card (empty hypergraph + empty string + seed CDLL)
        fig = single_card_figure(
            trace_s2h.snapshots[0],
            H,
            tokens_tuple,
            backend=backend,
            title=None,
            direction="s2h",
        )
        save_figure(fig, out_dir / f"{H_name}_{backend}_s2h_start")
        plt.close(fig)

        # 2. S2H end card (full hypergraph + full string + full CDLL)
        fig = single_card_figure(
            trace_s2h.snapshots[-1],
            H,
            tokens_tuple,
            backend=backend,
            title=None,
            direction="s2h",
        )
        save_figure(fig, out_dir / f"{H_name}_{backend}_s2h_end")
        plt.close(fig)

        # 1b. H2S start card (full hypergraph + empty string + seed CDLL)
        fig = single_card_figure(
            trace_h2s.snapshots[0],
            H,
            tokens_tuple,
            backend=backend,
            title=None,
            direction="h2s",
        )
        save_figure(fig, out_dir / f"{H_name}_{backend}_h2s_start")
        plt.close(fig)

        # 2b. H2S end card (consumed hypergraph + full string + full CDLL)
        fig = single_card_figure(
            trace_h2s.snapshots[-1],
            H,
            tokens_tuple,
            backend=backend,
            title=None,
            direction="h2s",
        )
        save_figure(fig, out_dir / f"{H_name}_{backend}_h2s_end")
        plt.close(fig)

        # 3. S2H step strip
        fig = steps_figure(
            trace_s2h.snapshots,
            H,
            tokens_tuple,
            backend=backend,
            direction="s2h",
            n_columns=n_steps,
            overall_title=None,
        )
        save_figure(fig, out_dir / f"{H_name}_{backend}_s2h_steps")
        plt.close(fig)

        # 4. H2S step strip
        fig = steps_figure(
            trace_h2s.snapshots,
            H,
            tokens_tuple,
            backend=backend,
            direction="h2s",
            n_columns=n_steps,
            overall_title=None,
        )
        save_figure(fig, out_dir / f"{H_name}_{backend}_h2s_steps")
        plt.close(fig)

        # 5. Roundtrip collage
        fig = roundtrip_figure(
            trace_s2h.snapshots,
            trace_h2s.snapshots,
            H,
            tokens_tuple,
            backend=backend,
            n_columns=n_steps,
            overall_title=None,
        )
        save_figure(fig, out_dir / f"{H_name}_{backend}_roundtrip")
        plt.close(fig)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/roundtrip"),
        help="Directory where figures and JSON traces are written.",
    )
    parser.add_argument(
        "--backends",
        nargs="+",
        default=["xgi", "hypernetx", "hypergraphx"],
        help="Viz backends to render through.",
    )
    parser.add_argument(
        "--hypergraphs",
        nargs="+",
        default=list(HYPERGRAPHS.keys()),
        choices=list(HYPERGRAPHS.keys()),
        help="Hypergraph fixtures to render.",
    )
    parser.add_argument(
        "--n-steps",
        type=int,
        default=7,
        help="Number of sampled snapshot columns per step strip.",
    )
    parser.add_argument(
        "--algorithm",
        type=str,
        default="greedy_min",
        help="H2S algorithm variant (only 'greedy_min' is currently wired).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    args = _parse_args(argv)

    apply_ieee_style()

    args.out_dir.mkdir(parents=True, exist_ok=True)

    known = set(available_backends())
    missing = [b for b in args.backends if b not in known]
    if missing:
        logger.error("requested backends not registered: %s; available: %s", missing, sorted(known))
        return 2

    for H_name in args.hypergraphs:
        H = HYPERGRAPHS[H_name]()
        _emit_one(
            H_name,
            H,
            args.out_dir,
            backends=tuple(args.backends),
            n_steps=args.n_steps,
            algorithm=args.algorithm,
        )

    logger.info("done. outputs in %s", args.out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
