"""Two RQ1 checks the analyzer does not emit.

``agreement`` -- which arms compute the *same canonical word*.
    The four-cell ablation of `ISAL_VARIANT_DESIGN.md` §3b contains one pair
    that must agree bit for bit (`wstar_orbit` is `w*_c` with the tie-complete
    search pruned to one branch per stabiliser orbit -- Proposition C.7, value
    preserving) and two that must differ (`wstar_rank` is a *new* canonical
    value; the ordered walk is a different canonical program altogether).
    Wave 4/5 checked this on 700 + 600 instances; this runs it on every member
    of the campaign, from the `word_hash` column of `rows_m0items`, over the
    members where both arms completed inside their budget.

``m4-rho`` -- Spearman ρ against ``nauty_cert_rows``.
    Hypothesis H-M4 is stated against the certificate *at instruction
    granularity*; the analyzer's M4 table reports ρ against ``nauty_cert``, the
    byte certificate, only. Comparing an Isal instruction against a certificate
    byte measures the tokenisation rather than the addressing, so the number
    the hypothesis names has to be computed separately.
"""

from __future__ import annotations

import argparse
import glob
import logging
import sys
from collections.abc import Sequence
from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr

logger = logging.getLogger(__name__)

#: Pairs whose agreement is a claim of the design, with the expected direction.
AGREEMENT_PAIRS: tuple[tuple[str, str, str], ...] = (
    ("isalhg_levenshtein", "wstar_orbit", "must be identical (Prop. C.7)"),
    ("isalhg_levenshtein", "wstar_rank", "must differ (a new canonical value)"),
    ("wstar_orbit", "wstar_rank", "must differ"),
    ("isalhg_levenshtein", "isal_ow_struct", "must differ (a different program)"),
    ("isal_ow_struct", "isal_ow_rank", "policies differ"),
    ("isal_ow_struct", "isal_ow_rank0", "policies differ"),
)

M4_ARMS: tuple[str, ...] = (
    "isal_ow_struct",
    "isal_ow_rank",
    "isal_ow_rank0",
    "isalhg_levenshtein",
    "wstar_orbit",
    "wstar_rank",
    "fact_rank",
)
CERT_ROWS_ARM = "nauty_cert_rows"


def _load(exp_dir: Path, table: str) -> pd.DataFrame:
    paths = sorted(glob.glob(str(exp_dir / f"rows_{table}__*.csv")))
    if not paths:
        raise SystemExit(f"no rows_{table} files under {exp_dir}")
    frame = pd.concat([pd.read_csv(p) for p in paths], ignore_index=True)
    return frame[frame["censored"] != True]  # noqa: E712 -- the column is object-typed


def agreement(exp_dir: Path) -> None:
    """Word-hash agreement per arm pair, on members where both completed."""
    frame = _load(exp_dir, "m0items")
    wide = frame.pivot_table(
        index=["collection", "seed", "member_id"],
        columns="arm",
        values="word_hash",
        aggfunc="first",
    )
    print("arm pair agreement (members where both arms completed)")
    for a, b, expectation in AGREEMENT_PAIRS:
        if a not in wide.columns or b not in wide.columns:
            continue
        sub = wide[[a, b]].dropna()
        if sub.empty:
            continue
        equal = int((sub[a].astype(str) == sub[b].astype(str)).sum())
        print(
            f"  {a:<20} vs {b:<18} n={len(sub):>6} identical={equal:>6} "
            f"({equal / len(sub):.4f})  -- {expectation}"
        )


def m4_rho(exp_dir: Path) -> None:
    """Spearman rho of every arm's distance against ``nauty_cert_rows``."""
    frame = _load(exp_dir, "m4")
    print(f"M4 -- Spearman rho against {CERT_ROWS_ARM} (H-M4 target: >= 0.6)")
    for collection, group in frame.groupby("collection", sort=True):
        wide = group.pivot_table(
            index=["series", "pair_id"], columns="arm", values="d", aggfunc="first"
        )
        if CERT_ROWS_ARM not in wide.columns:
            continue
        for arm in M4_ARMS:
            if arm not in wide.columns:
                continue
            sub = wide[[arm, CERT_ROWS_ARM]].dropna()
            if len(sub) < 10:
                continue
            rho = spearmanr(sub[arm], sub[CERT_ROWS_ARM]).statistic
            flag = "" if rho >= 0.6 else "   <- below H-M4"
            print(f"  {collection:<15} {arm:<22} n={len(sub):>5} rho={rho:.3f}{flag}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("check", choices=("agreement", "m4-rho", "both"))
    parser.add_argument("--root", required=True, type=Path, help="results root")
    parser.add_argument("--experiment", default="addressing")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    exp_dir = args.root / "RQ1_addressing" / args.experiment
    if args.check in ("agreement", "both"):
        agreement(exp_dir)
    if args.check in ("m4-rho", "both"):
        m4_rho(exp_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
