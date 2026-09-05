#!/usr/bin/env python
"""Freeze the TKDE collections to ``<RESULTS_ROOT>/corpora/<name>/``.

Each collection is derived from the read-only data root, written as
``records.jsonl`` + ``vocab.json``, and audited against the census numbers of
``docs/article/D_ART3/supplementary_data.md``: every expected number is written
to ``census.json`` beside the obtained one, with the difference, so a mismatch
is visible rather than absorbed.

Usage
-----
    python scripts/tkde/freeze_corpora.py \\
        --collections wd50k66 wd50k66_full wd50k100 ndc_classes \\
                      ndc_substances synthetic_rq1 \\
        --out "$ISALHG_RESULTS_ROOT/corpora"
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from isalhg.datasets.kb.base import KBCollection
from isalhg.datasets.kb.io import write_jsonl
from isalhg.datasets.kb.ndc_quarterly import load_ndc
from isalhg.datasets.kb.synthetic_rq1 import corpus as synthetic_corpus
from isalhg.datasets.kb.wd50k import load_wd50k

logger = logging.getLogger("freeze_corpora")

BUILDERS: dict[str, Callable[[Path | None], KBCollection]] = {
    "wd50k66": lambda root: load_wd50k("66", root=root),
    "wd50k66_full": lambda root: load_wd50k("66", envelope=False, root=root),
    "wd50k100": lambda root: load_wd50k("100", root=root),
    "wd50k_all": lambda root: load_wd50k("all", root=root),
    "ndc_classes": lambda root: load_ndc("classes", root=root),
    "ndc_substances": lambda root: load_ndc("substances", root=root),
    "synthetic_rq1": lambda root: synthetic_corpus(),
}

DEFAULT_COLLECTIONS = (
    "wd50k66",
    "wd50k66_full",
    "wd50k100",
    "ndc_classes",
    "ndc_substances",
    "synthetic_rq1",
)

# The census of supplementary_data.md S1-S4, as published.
EXPECTED: dict[str, dict[str, float]] = {
    "wd50k66": {
        "n_records": 3994,
        "n_entities_ge_min_statements": 4554,
        "n_records_with_arity_ge3": 3167,
        "n_dropped_over_arity_cap": 14,
        "n_labels_ge20": 14,
        "coverage_labels_ge20": 0.875,
        "median_n": 8,
        "median_m": 5,
        "frac_facts_arity_ge3": 0.547,
    },
    "wd50k66_full": {"n_records": 4554},
    "wd50k100": {"n_records": 1847, "frac_facts_arity_ge3": 0.998, "median_n": 11},
    "ndc_classes": {
        "n_records": 1432,
        "n_encodable_counting_singleton_products": 1432,
        "n_consecutive_pairs": 555,
        "delta_0": 85,
        "delta_1": 120,
        "delta_2": 134,
        "delta_3_5": 191,
        "delta_gt5": 25,
        "n_pairs_constant_preserving": 140,
        "n_pairs_constant_changing": 415,
        "n_classes_run_ge3": 45,
        "n_classes_run_ge5": 20,
        "n_simplices": 49724,
    },
    "ndc_substances": {
        "n_records": 2222,
        "n_encodable_counting_singleton_products": 2222,
        "n_consecutive_pairs": 1106,
        "delta_1": 35,
    },
    "synthetic_rq1": {"n_records": 2000},
}

# Why an audited quantity is expected to differ. Every deviation from the
# published census has exactly one of these two mechanisms behind it; both are
# consequences of the frozen contract, not of the derivation.
FACT_ARITY_RULE = (
    "the supplement counted a singleton product as a fact; the alphabet's F token has "
    "arity >= 2 (DESIGN G2), so singleton products are dropped and the members whose "
    "remaining fact count falls below m_min leave the collection"
)
M_MIN_RULE = (
    "the supplement's WD50K envelope was 'n <= 24 and m <= 110' with no fact floor; the "
    "frozen envelope of DESIGN G4 is '3 <= m <= 110', and the members it removes are the "
    "whole difference (n_records + n_dropped_below_m_min reproduces the published count)"
)

EXPLANATIONS: dict[str, dict[str, str]] = {
    "wd50k66": dict.fromkeys(
        ("n_records", "n_records_with_arity_ge3", "coverage_labels_ge20"), M_MIN_RULE
    ),
    "wd50k100": dict.fromkeys(("n_records",), M_MIN_RULE),
    "ndc_classes": dict.fromkeys(
        (
            "n_records",
            "n_consecutive_pairs",
            "delta_0",
            "delta_1",
            "delta_2",
            "delta_3_5",
            "delta_gt5",
            "n_pairs_constant_preserving",
            "n_pairs_constant_changing",
            "n_classes_run_ge3",
            "n_classes_run_ge5",
        ),
        FACT_ARITY_RULE,
    ),
    "ndc_substances": dict.fromkeys(
        ("n_records", "n_consecutive_pairs", "delta_1"), FACT_ARITY_RULE
    ),
}


def observed(collection: KBCollection, census: dict[str, Any]) -> dict[str, float]:
    """Pull the audited quantities out of a collection and its census."""
    meta = collection.meta
    delta = dict(meta.get("delta_histogram") or {})
    out: dict[str, float] = {
        "n_records": census["n_records"],
        "frac_facts_arity_ge3": census["frac_facts_arity_ge3"],
        "n_records_with_arity_ge3": census["n_records_with_arity_ge3"],
        "n_labels_ge20": census["n_labels_ge20"],
        "coverage_labels_ge20": census["coverage_labels_ge20"],
        "median_n": census["n"].get("median", 0.0),
        "median_m": census["m"].get("median", 0.0),
    }
    for key in (
        "n_entities_ge_min_statements",
        "n_dropped_over_arity_cap",
        "n_consecutive_pairs",
        "n_pairs_constant_preserving",
        "n_pairs_constant_changing",
        "n_classes_run_ge3",
        "n_classes_run_ge5",
        "n_simplices",
        "n_encodable_counting_singleton_products",
    ):
        if key in meta:
            out[key] = meta[key]
    if delta:
        out["delta_0"] = delta.get("0", 0)
        out["delta_1"] = delta.get("1", 0)
        out["delta_2"] = delta.get("2", 0)
        out["delta_3_5"] = delta.get("3-5", 0)
        out["delta_gt5"] = delta.get(">5", 0)
    return out


def audit(name: str, collection: KBCollection, census: dict[str, Any]) -> dict[str, Any]:
    """Build the expected-vs-obtained table for ``census.json``."""
    got = observed(collection, census)
    explanations = EXPLANATIONS.get(name, {})
    rows = []
    for key, want in EXPECTED.get(name, {}).items():
        have = got.get(key)
        match = have is not None and abs(float(have) - float(want)) <= 0.001 * max(
            1.0, abs(float(want))
        )
        rows.append(
            {
                "quantity": key,
                "expected": want,
                "obtained": have,
                "delta": None if have is None else round(float(have) - float(want), 6),
                "match": match,
                "explanation": None if match else explanations.get(key),
            }
        )
    return {
        "collection": name,
        "source": "docs/article/D_ART3/supplementary_data.md",
        "rows": rows,
        "n_mismatched": sum(1 for r in rows if not r["match"]),
        "n_unexplained": sum(1 for r in rows if not r["match"] and not r["explanation"]),
        "observed": got,
    }


def freeze(name: str, out_root: Path, data_root: Path | None) -> dict[str, Any]:
    """Derive, audit and write one collection; return its summary row."""
    if name not in BUILDERS:
        raise SystemExit(f"unknown collection {name!r}; expected one of {sorted(BUILDERS)}")
    t0 = time.perf_counter()
    collection = BUILDERS[name](data_root)
    build_secs = time.perf_counter() - t0
    census = collection.census()
    payload = dict(census)
    payload["loader_meta"] = {
        k: v
        for k, v in collection.meta.items()
        if k not in ("consecutive_pairs", "runs", "consecutive_runs", "node_names")
    }
    payload["audit"] = audit(name, collection, census)
    payload["build_secs"] = round(build_secs, 2)
    directory = write_jsonl(collection, out_root / collection.name, census=payload)
    size = sum(p.stat().st_size for p in directory.iterdir() if p.is_file())
    row = {
        "collection": collection.name,
        "directory": str(directory),
        "n_records": len(collection),
        "build_secs": round(build_secs, 2),
        "bytes": size,
        "n_mismatched": payload["audit"]["n_mismatched"],
        "n_unexplained": payload["audit"]["n_unexplained"],
    }
    logger.info(
        "%s: %d records, %.1f s, %.1f MB, %d audited quantities off (%d unexplained)",
        collection.name,
        len(collection),
        build_secs,
        size / 1e6,
        payload["audit"]["n_mismatched"],
        payload["audit"]["n_unexplained"],
    )
    for check in payload["audit"]["rows"]:
        if check["match"]:
            continue
        log = logger.info if check["explanation"] else logger.warning
        log(
            "  %s: expected %s, obtained %s (delta %s)%s",
            check["quantity"],
            check["expected"],
            check["obtained"],
            check["delta"],
            f" -- {check['explanation']}" if check["explanation"] else " -- UNEXPLAINED",
        )
    return row


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collections", nargs="+", default=list(DEFAULT_COLLECTIONS))
    parser.add_argument("--out", required=True, help="corpora root to write into")
    parser.add_argument("--data-root", default=None, help="override ISALHG_DATA_ROOT")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(message)s",
    )
    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)
    data_root = Path(args.data_root) if args.data_root else None
    rows = [freeze(name, out_root, data_root) for name in args.collections]
    summary = {"corpora_root": str(out_root), "collections": rows}
    (out_root / "MANIFEST.json").write_text(
        json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
