"""Bits harvest: information-content comparison on the body corpora.

Computes fixed-width-code bits for IsalHG vs the incidence-list
construction model on the planted_main and planted_small corpora
(T-M5b body corpora). Bypasses the runner's planted_families kwarg
mismatch bug by instantiating PlantedFamilyDataset directly.

Writes per-corpus info_content.json files and then calls
analyze_info_content to produce the Wilcoxon + OLS summary.

Spec: PROPOSAL.md §4, correlation.md §Information content.

Usage (standalone)::

    python -m experiments.article.analysis.bits_harvest \\
        --output-dir /media/.../results/T-M5a/bits
"""

from __future__ import annotations

import argparse
import contextlib
import json
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Corpus configurations (mirrors mds_planted.yaml body corpora)
# ---------------------------------------------------------------------------

BODY_CORPORA: list[dict[str, Any]] = [
    {
        "label": "planted_main",
        "dataset_params": {
            "n_families": 5,
            "members_per_family": 12,
            "n_nodes": 10,
            "k": 3,
            "n_edges": 10,
            "seed_value": 42,
            "n_edits": 3,
            "max_retries": 300,
        },
    },
    {
        "label": "planted_small",
        "dataset_params": {
            "n_families": 4,
            "members_per_family": 5,
            "n_nodes": 6,
            "k": 3,
            "n_edges": 5,
            "seed_value": 42,
            "n_edits": 2,
            "max_retries": 200,
        },
    },
]


# ---------------------------------------------------------------------------
# Atomic I/O
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
# Per-corpus info_content computation
# ---------------------------------------------------------------------------


def compute_corpus_bits(
    label: str,
    dataset_params: dict[str, Any],
    output_dir: Path,
) -> dict[str, Any]:
    """Compute info-content bits for one planted-family corpus.

    Parameters
    ----------
    label : str
        Corpus label (e.g. 'planted_main').
    dataset_params : dict
        Parameters passed to PlantedFamilyDataset.
    output_dir : Path
        Directory for this corpus's info_content.json.

    Returns
    -------
    dict
        The info_content data dict (same schema as runner.run_info_content_cell).
    """
    result_path = output_dir / "info_content.json"

    # Idempotence: skip if already done
    if result_path.exists():
        try:
            with open(result_path) as f:
                data = json.load(f)
            if data.get("status") == "done":
                logger.info("  skip %s (done)", label)
                return data
        except (json.JSONDecodeError, KeyError):
            pass

    from isalhg.core.canonical import canonical_string
    from isalhg.core.instructions import parse as parse_tokens
    from isalhg.datasets.synthetic.planted_families import PlantedFamilyDataset
    from isalhg.metric_space.metrics.information import (
        alphabet_size_isalhg,
        bits_incidence_list,
        bits_isalhg,
        compression_ratio,
    )

    logger.info("  computing bits for corpus %s ...", label)
    t0 = time.perf_counter()

    params = dict(dataset_params)
    dataset = PlantedFamilyDataset(**params)
    items = list(dataset)
    hypergraphs = [item.hypergraph for item in items]

    # k = max arity across corpus
    k_corpus = max(
        (max((len(m) for m in H.hyperedges()), default=2) for H in hypergraphs),
        default=2,
    )
    alpha_size = alphabet_size_isalhg(k_corpus)

    records: list[dict[str, Any]] = []
    for H in hypergraphs:
        w = canonical_string(H, k=k_corpus)
        # Use the proper parser: ";" also appears inside brackets as a field
        # separator, so raw split(";") overcounts tokens ~2×.
        n_tokens = len(parse_tokens(w))

        arities = [len(m) for m in H.hyperedges()]
        n_nodes = H.n_nodes

        b_isal = bits_isalhg(n_tokens, k_corpus)
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

    elapsed = time.perf_counter() - t0
    ratios = np.array([r["compression_ratio"] for r in records])

    data: dict[str, Any] = {
        "status": "done",
        "label": label,
        "k": k_corpus,
        "alphabet_size": alpha_size,
        "n_items": len(records),
        "wall_clock_s": float(elapsed),
        "dataset_params": dataset_params,
        "median_compression_ratio": float(np.median(ratios)),
        "fraction_shorter": float(np.mean(ratios > 1.0)),
        "records": records,
    }

    _atomic_write_json(result_path, data)
    logger.info(
        "  %s: N=%d  k=%d  |Σ|=%d  median_r=%.3f  frac_shorter=%.3f  wall=%.1fs",
        label,
        len(records),
        k_corpus,
        alpha_size,
        float(np.median(ratios)),
        float(np.mean(ratios > 1.0)),
        elapsed,
    )
    return data


# ---------------------------------------------------------------------------
# Aggregate analysis
# ---------------------------------------------------------------------------


def harvest_bits(
    output_dir: Path,
) -> dict[str, Any]:
    """Compute bits for all body corpora and run Wilcoxon + OLS analysis.

    Parameters
    ----------
    output_dir : Path
        Root output directory. Per-corpus data lands in
        ``{output_dir}/{label}/info_content.json``; the aggregate
        summary + figure land in ``{output_dir}/bits_result.json``
        and ``{output_dir}/bits_figure.pdf``.

    Returns
    -------
    dict
        Aggregate result dict.
    """
    from experiments.article.analysis.information_content import analyze_info_content

    output_dir.mkdir(parents=True, exist_ok=True)

    corpus_results: list[dict[str, Any]] = []
    for corpus_cfg in BODY_CORPORA:
        label = corpus_cfg["label"]
        corpus_dir = output_dir / label
        corpus_dir.mkdir(parents=True, exist_ok=True)
        data = compute_corpus_bits(label, corpus_cfg["dataset_params"], corpus_dir)
        corpus_results.append({"label": label, "data": data})

    # Pool all records for the aggregate Wilcoxon + OLS
    all_records: list[dict[str, Any]] = []
    for cr in corpus_results:
        all_records.extend(cr["data"].get("records", []))

    pooled_path = output_dir / "pooled_info_content.json"
    # Build a pooled info_content.json in the format analyze_info_content expects
    if all_records:
        pooled_k = max(r["k_max"] for r in all_records)
        pooled_data = {
            "status": "done",
            "label": "pooled_body_corpora",
            "k": pooled_k,
            "alphabet_size": None,
            "n_items": len(all_records),
            "records": all_records,
        }
        _atomic_write_json(pooled_path, pooled_data)

        aggregate = analyze_info_content(pooled_path, output_dir)
        aggregate["per_corpus"] = [
            {
                "label": cr["label"],
                "n_items": cr["data"].get("n_items", 0),
                "median_r": cr["data"].get("median_compression_ratio", float("nan")),
                "frac_shorter": cr["data"].get("fraction_shorter", float("nan")),
            }
            for cr in corpus_results
        ]
    else:
        aggregate = {"status": "no_data"}

    logger.info(
        "Bits aggregate: N=%d  median_r=%.3f  frac_shorter=%.3f  Wilcoxon_p=%.3g  beta=%.3f",
        aggregate.get("n_items", 0),
        aggregate.get("median_compression_ratio", float("nan")),
        aggregate.get("fraction_shorter", float("nan")),
        aggregate.get("wilcoxon_pvalue", float("nan")),
        aggregate.get("ols_beta", float("nan")),
    )
    return aggregate


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry point for standalone execution."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Root directory for bits analysis output.",
    )
    args = parser.parse_args()

    result = harvest_bits(args.output_dir)

    print(f"\nBits harvest summary (N={result.get('n_items', 'N/A')} hypergraphs)")
    print(f"  Median compression ratio  : {result.get('median_compression_ratio', 'N/A'):.4f}")
    print(f"  Fraction IsalHG shorter   : {result.get('fraction_shorter', 'N/A'):.4f}")
    print(f"  Wilcoxon p-value          : {result.get('wilcoxon_pvalue', 'N/A'):.3g}")
    print(f"  OLS beta                  : {result.get('ols_beta', 'N/A'):.4f}")
    if "per_corpus" in result:
        print("\n  Per-corpus:")
        for pc in result["per_corpus"]:
            print(
                f"    {pc['label']}: N={pc['n_items']}  "
                f"median_r={pc['median_r']:.3f}  "
                f"frac_shorter={pc['frac_shorter']:.3f}"
            )
    print(f"\n  Results written to {args.output_dir}")


if __name__ == "__main__":
    main()
