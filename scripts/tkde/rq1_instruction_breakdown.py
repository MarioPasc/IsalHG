"""RQ1 M1 single-edit response in instructions, broken down by edit kind.

`ISAL_VARIANT_DESIGN.md` §4 specifies M1 as "per (arm, corpus, kind, regime):
absolute median in instructions and in campaign symbols".  The analyzer
delivers half of that: its `M1 -- single-edit response` table is per
(collection, edit_kind, regime, arm) but at *symbol* granularity, and its
`M1 -- SELECTION` table is at instruction granularity but aggregates over edit
kinds.  The instruction-granularity split by edit kind -- the granularity the
paper reports (L7, L11) -- is in neither.

It is the split that carries the reading.  The Isal walks are the most local
representation under *deletions* and lose under *insertions over existing
arguments*; a table pooled over edit kinds averages the two and shows neither.
This script emits the missing breakdown from the merged row files, plus the
pooled-over-corpora rows, in the same Markdown shape the analyzer uses.

Read-only: it never writes into the experiment directory unless ``--out`` says
so.
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

WITHIN_INSTRUCTIONS = 2
RQ_FOLDER = "RQ1_addressing"
EXPERIMENT = "addressing"


def load_m1(exp_dir: Path) -> pd.DataFrame:
    """Concatenate the tagged ``rows_m1`` files that carry the instruction column."""
    frames: list[pd.DataFrame] = []
    for path in sorted(exp_dir.glob("rows_m1__*.csv")):
        # An untagged file is a stale smoke; the analyzer skips those too.
        if "__" not in path.name or path.name.split("__", 1)[1].startswith("m1-"):
            continue
        try:
            frame = pd.read_csv(
                path,
                usecols=[
                    "collection",
                    "edit_kind",
                    "regime",
                    "arm",
                    "d_instr",
                    "n_instr",
                    "base_id",
                    "censored",
                ],
            )
        except ValueError:
            continue  # a launch that predates the instruction columns
        frames.append(frame)
    if not frames:
        raise SystemExit(f"no instruction-carrying m1 rows under {exp_dir}")
    frame = pd.concat(frames, ignore_index=True)
    frame["d_instr"] = pd.to_numeric(frame["d_instr"], errors="coerce")
    return frame[frame["d_instr"].notna()]


def summarise(frame: pd.DataFrame, by: Sequence[str]) -> pd.DataFrame:
    """Median, IQR and within-<=2 fraction of ``d_instr`` per group."""

    def one(group: pd.DataFrame) -> pd.Series:
        values = group["d_instr"].to_numpy(dtype=float)
        q1, q3 = np.percentile(values, [25, 75])
        return pd.Series(
            {
                "n": int(len(values)),
                "n_base": int(group["base_id"].nunique()),
                "median_d_instr": float(np.median(values)),
                "iqr": float(q3 - q1),
                f"within_{WITHIN_INSTRUCTIONS}": float((values <= WITHIN_INSTRUCTIONS).mean()),
            }
        )

    return frame.groupby(list(by), sort=True)[["d_instr", "base_id"]].apply(one).reset_index()


def to_markdown(frame: pd.DataFrame, title: str) -> str:
    lines = [f"## {title}", ""]
    lines.append("| " + " | ".join(frame.columns) + " |")
    lines.append("|" + "---|" * len(frame.columns))
    for row in frame.itertuples(index=False):
        cells = []
        for value in row:
            if isinstance(value, float):
                cells.append(f"{value:.4g}")
            else:
                cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path, help="results root")
    parser.add_argument("--experiment", default=EXPERIMENT)
    parser.add_argument(
        "--arms", nargs="*", default=(), help="restrict to these arms (default: all)"
    )
    parser.add_argument("--out", type=Path, default=None, help="write Markdown here")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    exp_dir = args.root / RQ_FOLDER / args.experiment
    frame = load_m1(exp_dir)
    if args.arms:
        frame = frame[frame["arm"].isin(list(args.arms))]

    per_corpus = summarise(frame, ["collection", "edit_kind", "regime", "arm"])
    pooled = summarise(frame, ["edit_kind", "regime", "arm"])
    pooled.insert(0, "collection", "(pooled)")
    pooled_kind = summarise(frame, ["edit_kind", "arm"])
    pooled_kind.insert(0, "collection", "(pooled)")
    pooled_kind.insert(2, "regime", "(both)")

    text = "\n".join(
        [
            "# RQ1 M1 -- single-edit response in instructions, by edit kind",
            "",
            "Fills the gap between the analyzer's symbol-granularity M1 table and",
            "its edit-kind-agnostic SELECTION table (design section 4 asks for both",
            "at once). `regime` 1 is constant-set-preserved.",
            "",
            to_markdown(pooled_kind, "Pooled over corpora and regimes"),
            to_markdown(pooled, "Pooled over corpora, by regime"),
            to_markdown(per_corpus, "Per corpus"),
        ]
    )

    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
        logger.info("wrote %s", args.out)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
