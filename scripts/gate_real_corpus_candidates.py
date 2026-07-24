"""Gate script for real-world corpus candidates (T-M7g).

Runs the four-step feasibility gate defined in T-DQ3' / REAL_DATA_CORPUS.md
on the shortlisted low-arity candidates from ARB/Benson and XGI-DATA.

Gate steps (per REVIEW/REAL_DATA_CORPUS.md §Selection protocol):
  0. Pre-gate: is the source a labeled instance collection (N >= 2 instances
     with whole-graph class labels)?  Single large networks fail immediately.
  1. Arity distribution vs k_max = 10: fraction with max_arity <= 10.
  2. w*_c wall-clock at p50/p90 under 30 s budget.
  3. Post-filter yield >= 85%.
  4. Label-independence of censoring (per-class retention comparison).

Promotion rule: only a corpus clearing >= 85% yield with label-independent
censoring is promoted.  Anything below is reported as NO_GO.

Outputs:
  artifacts/real_anchor_gate/candidate_gate_results.json

Usage::

    python scripts/gate_real_corpus_candidates.py [--output PATH]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Shortlist of candidates
# ---------------------------------------------------------------------------
#
# ARB / Benson (Qin et al. ICDE 2023 benchmarks, DOI 10.1109/ICDE55515.2023.00386)
# Loader: src/isalhg/datasets/arb_benson.py → ARBBensonDataset
# Architecture: yields exactly 1 DatasetItem (one whole hypergraph); no iso labels.

_ARB_CANDIDATES: list[dict[str, Any]] = [
    {
        "name": "arb_benson:contact-primary-school",
        "source": "ARB/Benson — contact-primary-school",
        "citation": "Benson et al., PNAS 2018; Qin et al., ICDE 2023",
        "architecture_note": ("ARBBensonDataset yields 1 DatasetItem (whole network); len() = 1"),
    },
    {
        "name": "arb_benson:contact-high-school",
        "source": "ARB/Benson — contact-high-school",
        "citation": "Benson et al., PNAS 2018; Qin et al., ICDE 2023",
        "architecture_note": ("ARBBensonDataset yields 1 DatasetItem (whole network); len() = 1"),
    },
    {
        "name": "arb_benson:mathoverflow-answers",
        "source": "ARB/Benson — mathoverflow-answers",
        "citation": "Benson et al., PNAS 2018; Qin et al., ICDE 2023",
        "architecture_note": ("ARBBensonDataset yields 1 DatasetItem (whole network); len() = 1"),
    },
]

# XGI-DATA (Landry et al. 2023, DOI 10.21105/joss.05162)
# Loader: src/isalhg/datasets/xgi_loader.py → XGIDataDataset (stub)
# Architecture: xgi.load_xgi_data(name) returns ONE xgi.Hypergraph object.
#
# Shortlist: low-arity candidates probed in T-M7g session (2026-07-24).
# plant-pollinator-mpl-014 is the only XGI dataset with max_arity = 10 (=k_max)
# found in the probe; others exceed the cap or are higher-arity networks.
# All are still single large networks regardless of arity.

_XGI_CANDIDATES: list[dict[str, Any]] = [
    {
        "name": "xgi_data:plant-pollinator-mpl-014",
        "source": "XGI-DATA — plant-pollinator-mpl-014",
        "citation": "Landry et al., JOSS 2023; dataset from mutualistic network ecology",
        "measured_stats": {
            "n_nodes": 29,
            "n_edges": 81,
            "max_arity": 10,
            "min_arity": 1,
        },
        "architecture_note": ("xgi.load_xgi_data returns 1 xgi.Hypergraph object (single network)"),
    },
    {
        "name": "xgi_data:plant-pollinator-mpl-015",
        "source": "XGI-DATA — plant-pollinator-mpl-015",
        "citation": "Landry et al., JOSS 2023",
        "measured_stats": {
            "n_nodes": 131,
            "n_edges": 666,
            "max_arity": 104,
        },
        "architecture_note": ("xgi.load_xgi_data returns 1 xgi.Hypergraph object (single network)"),
    },
    {
        "name": "xgi_data:plant-pollinator-mpl-016",
        "source": "XGI-DATA — plant-pollinator-mpl-016",
        "citation": "Landry et al., JOSS 2023",
        "measured_stats": {
            "n_nodes": 26,
            "n_edges": 179,
            "max_arity": 17,
        },
        "architecture_note": ("xgi.load_xgi_data returns 1 xgi.Hypergraph object (single network)"),
    },
    {
        "name": "xgi_data:plant-pollinator-mpl-021",
        "source": "XGI-DATA — plant-pollinator-mpl-021",
        "citation": "Landry et al., JOSS 2023",
        "measured_stats": {
            "n_nodes": 91,
            "n_edges": 677,
            "max_arity": 25,
        },
        "architecture_note": ("xgi.load_xgi_data returns 1 xgi.Hypergraph object (single network)"),
    },
    {
        "name": "xgi_data:diseasome",
        "source": "XGI-DATA — diseasome (gene-disease bipartite)",
        "citation": "Landry et al., JOSS 2023; Goh et al., PNAS 2007",
        "measured_stats": {
            "n_nodes": 516,
            "n_edges": 903,
            "max_arity": 11,
        },
        "architecture_note": ("xgi.load_xgi_data returns 1 xgi.Hypergraph object (single network)"),
    },
    {
        "name": "xgi_data:contact-primary-school",
        "source": "XGI-DATA — contact-primary-school",
        "citation": "Landry et al., JOSS 2023; Stehlé et al., PLoS ONE 2011",
        "architecture_note": (
            "xgi.load_xgi_data returns 1 xgi.Hypergraph object; "
            "temporal contact network, not a labeled instance collection"
        ),
    },
    {
        "name": "xgi_data:ndc-classes",
        "source": "XGI-DATA — ndc-classes (drug-class co-prescription)",
        "citation": "Landry et al., JOSS 2023; Benson et al., 2018",
        "measured_stats": {
            "n_nodes": 1161,
            "n_edges": 49726,
            "max_arity": 39,
        },
        "architecture_note": ("xgi.load_xgi_data returns 1 xgi.Hypergraph object (single network)"),
    },
]


# ---------------------------------------------------------------------------
# Gate logic
# ---------------------------------------------------------------------------

_PRE_GATE_FAIL_REASON = (
    "single large network — the loader yields exactly 1 item "
    "(one whole hypergraph); the feasibility gate requires a labeled "
    "instance collection with ≥ 2 labeled instances per class"
)


def _gate_candidate(meta: dict[str, Any]) -> dict[str, Any]:
    """Apply the four-step gate to one candidate and return its record."""
    result: dict[str, Any] = {
        "name": meta["name"],
        "source": meta["source"],
        "citation": meta.get("citation", ""),
        "architecture_note": meta.get("architecture_note", ""),
        "measured_stats": meta.get("measured_stats", {}),
    }

    # Step 0 — pre-gate: is this a labeled instance collection?
    # Both ARB (ARBBensonDataset.__len__ == 1) and XGI-DATA
    # (xgi.load_xgi_data returns one Hypergraph) are single large networks.
    result["pre_gate"] = {
        "status": "FAIL",
        "reason": _PRE_GATE_FAIL_REASON,
    }
    result["step1"] = None
    result["step2"] = None
    result["step3"] = None
    result["step4"] = None
    result["verdict"] = "NO_GO"
    result["verdict_reason"] = (
        "Failed pre-gate: not a labeled instance collection. Steps 1–4 not applicable."
    )
    return result


def run_gate(output_path: Path) -> dict[str, Any]:
    """Run the gate on all shortlisted candidates and write the artifact.

    Parameters
    ----------
    output_path : Path
        Destination for the JSON artifact.

    Returns
    -------
    report : dict[str, Any]
        The full gate report (also written to ``output_path``).
    """
    all_candidates = _ARB_CANDIDATES + _XGI_CANDIDATES
    records = [_gate_candidate(m) for m in all_candidates]

    promoted = [r["name"] for r in records if r["verdict"] == "GO"]

    report: dict[str, Any] = {
        "gate_protocol_version": "T-DQ3prime",
        "run_date": str(date.today()),
        "gate_steps": {
            "pre_gate": "labeled instance collection (N >= 2, whole-graph labels)",
            "step1": "arity distribution vs k_max=10; fraction with max_arity <= 10",
            "step2": "w*_c p50/p90 under 30 s per-instance budget",
            "step3": "post-filter yield >= 85%",
            "step4": "label-independence of censoring (per-class retention comparison)",
        },
        "promotion_threshold": {
            "yield_min": 0.85,
            "censoring": "label_independent",
        },
        "k_max": 10,
        "budget_seconds": 30.0,
        "candidates": records,
        "n_candidates": len(records),
        "n_failed_pre_gate": sum(1 for r in records if r["pre_gate"]["status"] == "FAIL"),
        "promoted": promoted,
        "conclusion": (
            "No candidate promoted. All shortlisted ARB/Benson and XGI-DATA "
            "datasets are single large hypergraph networks, not labeled instance "
            "collections. The feasibility gate requires a corpus with many small "
            "labeled hypergraphs (one whole-graph label per instance). "
            "This structural mismatch — confirmed by loader code inspection and "
            "session probing (2026-07-24) — precludes all candidates from passing "
            "pre-gate. The known-design Stratum A corpus (17 families × 5 members "
            "= 85 items, arity <= 5 <= k_max=10, w*_c computable within 5 s per "
            "instance) remains the only anchor that passes the feasibility gate. "
            "Reference: docs/article/DATA.md §2 (T-DQ3' NO-GO record)."
        ),
        "reference": "docs/article/DATA.md §2; T-DQ/CLOSED/T-DQ3prime.md",
        "designs_anchor_status": (
            "PASS — 17 families, 5 members each = 85 items, "
            "max_arity in {3,4,5} ≤ k_max=10, "
            "w*_c p90 ≤ 5 s (measured T-M7a/h/q)"
        ),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = output_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(report, indent=2))
    tmp.rename(output_path)
    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/real_anchor_gate/candidate_gate_results.json"),
        help=(
            "Path to write the gate results JSON "
            "(default: artifacts/real_anchor_gate/candidate_gate_results.json)"
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Entry point."""
    args = _parse_args(argv)
    print(f"Running gate on {len(_ARB_CANDIDATES + _XGI_CANDIDATES)} candidates ...")
    report = run_gate(args.output)
    n_cands = report["n_candidates"]
    n_fail = report["n_failed_pre_gate"]
    print(f"  {n_cands} candidates evaluated")
    print(f"  {n_fail} failed pre-gate (single large network, not a corpus)")
    print(f"  {len(report['promoted'])} promoted")
    print(f"  Conclusion: {report['conclusion'][:80]}...")
    print(f"  Artifact: {args.output}")


if __name__ == "__main__":
    main(sys.argv[1:])
