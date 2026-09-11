"""Screen prose figures against the built corpora's censuses.

A corpus correction propagates to every figure derived from it, and a member-count
check cannot see that: the exposed figure is usually a *ratio*, one derivation
downstream. The 2026-09-11 sweep found three such figures in ``prose.md`` — all
downstream of one reconciliation (1,432 → 1,381, 3,994 → 3,988) that had reached
the counts and stopped.

**Two screens, run in order.**

1. **Exact (primary).** ``freeze_corpora.py`` records, per corpus, an audit row per
   quantity: ``quantity / expected / obtained / delta / match``. **``expected`` is
   the pre-freeze value**, so a prose figure equal to the ``expected`` of a
   mismatched row is stale *by construction* — no threshold, no inference, and a
   **certainty** rather than a candidate. It is also complete over everything the
   freeze audit compared, which is the set of quantities that could have gone
   stale.
2. **Near-miss (second net).** For quantities the audit never compared, a prose
   number within ``TOLERANCE`` of an obtained value without equalling it is a
   candidate. This is a *net*, not a proof, and its window must be wide: the
   reconciliations on record range from **0.16 %** (3,167 → 3,162) to **5.11 %**
   (555 → 528), so a 1 % window — the first version's — would have missed two of
   the three figures actually corrected on 2026-09-11. Calibrating a window to the
   one case it caught is how a screen comes to report "residual: none" about a
   set it cannot see.

**Why not near-miss alone.** The first version of this check searched the prose for
each census field's *built* value and reported presence. That detects presence, not
staleness, and cannot work without already knowing the superseded number — so it
found the one corpus whose pre-freeze values happened to be to hand and reported the
other four clear. A screen that only works where you already know the answer is not
a screen. (Both corrections raised by ``[IsalHG-Fable]``.)

**This is a screen, not an audit.** It matches digit strings, so it yields
candidates that a human clears — and it cannot see whether the *noun* beside a
number is the right noun, which is what T-KBg's predicate pass is for. It proves a
figure stale; it never proves one correct.

Exits **non-zero** when candidates remain, so it can gate the fold rather than
merely inform it: a check that cannot stop the thing it checks is not a check.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

#: Second-net window. Set from the largest delta in the recorded reconciliations
#: (555 -> 528 is 5.11 %), not from the case that happened to be caught first.
TOLERANCE = 0.06

#: Below this, collisions swamp the signal (page numbers, small counts, years).
MIN_VALUE = 100

DEFAULT_CORPORA = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE/corpora")
DEFAULT_PROSE = Path(__file__).resolve().parents[2] / "docs/article/D_ART3/prose.md"

#: Cleared by hand on 2026-09-11; each is a genuine coincidence, not a stale value.
#: Listed rather than silently filtered, so a reader can re-check the judgement.
KNOWN_BENIGN = {
    ("ndc_substances", "delta_gt5", 578): '"one in 578" is a collision rate',
    ("ndc_classes", "n_records_with_arity_ge3", 1381): (
        "1,381 is n_records; the adjacent field is 1,380"
    ),
    ("ndc_classes", "n_records", 1300): "1,300 = the orbit port's 700+600 differentials",
    ("ndc_classes", "n_records_with_arity_ge3", 1300): "same 1,300 differentials",
    ("ndc_classes", "n_dropped_over_arity_cap", 528): "528 is n_consecutive_pairs",
    ("ndc_classes", "n_encodable_counting_singleton_products", 1381): (
        "1,381 is n_records; 1,432 is this field and is correctly absent"
    ),
    ("ndc_classes", "delta_1", 111): '"m <= 111 in ~0.03 s" -- the envelope probe',
    ("ndc_substances", "n_dropped_over_arity_cap", 400): (
        "400 is ndc_classes' constant-changing pairs, and a Prop C.5 sample size"
    ),
    ("ndc_substances", "delta_gt5", 600): "600 s, the tail characterisation budget",
}


def prose_integers(text: str) -> set[int]:
    """Every integer >= MIN_VALUE appearing in the prose, comma-formatting allowed."""
    out = set()
    # (?<![\d.]) and (?![\d.]) keep the match from starting or ending inside a
    # decimal: without them "0.4157" yields 4157 and "0.0386" yields 386, which
    # put four numbers that do not exist in the prose onto the candidate list.
    for match in re.finditer(r"(?<![\d.])\d[\d,]{2,}(?![\d.])", text):
        try:
            value = int(match.group().replace(",", ""))
        except ValueError:
            continue
        if value < MIN_VALUE:
            continue
        # A bare four-digit year is a citation, not a measurement. The prose
        # comma-formats every data figure ("1,381", "3,162"), so an uncommaed
        # 1900-2100 is a date: without this, 2001/2019/2026 collide with
        # synthetic_rq1's n_records = 2,000 and fill the candidate list.
        if "," not in match.group() and 1900 <= value <= 2100:
            continue
        out.add(value)
    return out


def stale_expectations(path: Path) -> list[tuple[str, float, float]]:
    """``(quantity, expected, obtained)`` for every quantity the freeze audit moved.

    ``expected`` is the pre-freeze value. A prose figure equal to one is stale by
    construction, which is what makes this screen exact rather than heuristic.
    """
    payload = json.loads(path.read_text())
    out = []
    for row in payload.get("audit", {}).get("rows", []):
        if row.get("match") is True:
            continue
        expected, obtained = row.get("expected"), row.get("obtained")
        if isinstance(expected, (int, float)) and isinstance(obtained, (int, float)):
            out.append((str(row.get("quantity")), expected, obtained))
    return out


def prose_numbers(text: str) -> set[float]:
    """Every number in the prose, integers and decimals alike."""
    out: set[float] = set()
    for match in re.finditer(r"(?<![\d.])\d[\d,]*(?:\.\d+)?(?![\d.])", text):
        try:
            out.add(float(match.group().replace(",", "")))
        except ValueError:
            continue
    return out


def census_fields(path: Path) -> dict[str, int]:
    """Integer census quantities for one collection, from its ``census.json``."""
    payload = json.loads(path.read_text())
    observed = payload.get("audit", {}).get("observed", {})
    return {
        key: value
        for key, value in observed.items()
        if isinstance(value, int) and not isinstance(value, bool) and value >= MIN_VALUE
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpora", type=Path, default=DEFAULT_CORPORA)
    parser.add_argument("--prose", type=Path, default=DEFAULT_PROSE)
    parser.add_argument(
        "--show-benign",
        action="store_true",
        help="also print the candidates already cleared by hand",
    )
    args = parser.parse_args()

    if not args.prose.is_file():
        print(f"no prose at {args.prose}", file=sys.stderr)
        return 2
    censuses = sorted(args.corpora.glob("*/census.json"))
    if not censuses:
        print(f"no census.json under {args.corpora}", file=sys.stderr)
        return 2

    text = args.prose.read_text()
    numbers = prose_integers(text)
    every = prose_numbers(text)
    print(f"prose: {args.prose}  ({len(numbers)} integers >= {MIN_VALUE})")
    print(f"corpora: {len(censuses)} censuses under {args.corpora}\n")

    # -- screen 1: exact, against the freeze audit's own pre-freeze values --------
    stale: list[str] = []
    compared = 0
    for census in censuses:
        collection = census.parent.name
        for quantity, expected, obtained in stale_expectations(census):
            compared += 1
            if float(expected) in every:
                stale.append(
                    f"  {collection:16s} {quantity:34s} "
                    f"PRE-FREEZE {expected:,g} present (built: {obtained:,g})"
                )
    print(f"screen 1 (exact, {compared} mismatched quantities across all corpora):")
    if stale:
        print("  STALE VALUES IN THE PROSE -- these are certainties, not candidates:")
        print("\n".join(stale))
    else:
        print("  clean: no pre-freeze value from any freeze-audit row appears.")
    print()

    open_candidates: list[str] = []
    benign_seen: list[str] = []
    for census in censuses:
        collection = census.parent.name
        for field, value in census_fields(census).items():
            for found in numbers:
                if found == value or abs(found - value) / value > TOLERANCE:
                    continue
                line = f"  {collection:16s} {field:34s} census {value:,}  prose has {found:,}"
                reason = KNOWN_BENIGN.get((collection, field, found))
                if reason:
                    benign_seen.append(f"{line}   [benign: {reason}]")
                else:
                    open_candidates.append(line)

    if args.show_benign and benign_seen:
        print("cleared by hand previously:")
        print("\n".join(benign_seen), "\n")

    if stale:
        print(
            f"\n{len(stale)} stale value(s) from screen 1 must be corrected before "
            "the fold."
        )
        return 1

    if not open_candidates:
        print(
            f"CLEAN: no prose integer sits within {TOLERANCE:.0%} of a census value "
            "without equalling it."
        )
        print(f"({len(benign_seen)} known-benign near-misses suppressed; --show-benign)")
        return 0

    print(f"screen 2 (near-miss, window {TOLERANCE:.0%}) -- CANDIDATES:")
    print("\n".join(open_candidates))
    print(
        f"\n{len(open_candidates)} candidate(s). Each is a *candidate*: clear it against "
        "the census\nby hand, then either correct the prose or add it to KNOWN_BENIGN "
        "with its reason."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
