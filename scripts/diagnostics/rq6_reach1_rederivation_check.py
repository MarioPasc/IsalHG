"""Verify the RQ6 ``reach1`` re-derivation changed only what it was allowed to.

T-KBo rebuilt ``Reach1Index`` on ``reach'``. RQ6 persists no per-sample data, but
sampling is deterministic — refitting the model from scratch and resampling at
the same seed gives byte-identical output — so a re-run at the same seeds is a
**re-derivation over the same samples**, not a resampling. That makes a strict
check available, and this script is committed *before* the new rows exist so the
criterion cannot be chosen after seeing them.

The three columns allowed to move, all in ``rows_samples``:

* ``reach1_frac`` — the quantity being re-derived;
* ``reach1_eligible`` — the eligibility gate changed;
* ``reach1_hits`` — the index changed.

Everything else must be **bit-identical**, including two that look like they
should move and must not: ``rows_completion.reach1`` calls
:func:`isalhg.language.reach.reach` directly and never touches the index, and
``rows_alignment`` does not use it at all.

The direction is predicted too. The old index only ever considered members of
identical ``(constant count, type multiset)``, which is strictly more
restrictive than "some member sits at ``reach' <= 1``". So the new answer set
contains the old one and the new eligibility gate is more permissive:
``reach1_eligible`` may only rise, and no sample may flip ``True -> False``.
A decrease in either **falsifies the fix** rather than being explained away.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

MOVABLE: frozenset[str] = frozenset({"reach1_frac", "reach1_eligible", "reach1_hits"})

#: Columns that identify a row, so old and new are compared like for like.
#: ``member_id``, ``pair_id`` and ``reason`` are load-bearing: without them the
#: 600 completion rows collapse onto 6 keys and 594 are silently dropped by dict
#: overwrite, leaving a check that passes because it compared almost nothing.
#: :func:`load` asserts no such collapse rather than trusting this list.
KEYS: tuple[str, ...] = (
    "collection",
    "model",
    "seed",
    "unit",
    "arm",
    "member_id",
    "pair_id",
    "reason",
)

#: Provenance columns that legitimately differ between two runs and say nothing
#: about the measurement.
PROVENANCE: frozenset[str] = frozenset({"git_sha", "host_cpu", "secs"})


class KeyCollisionError(Exception):
    """The identifying columns do not uniquely identify a row."""


def load(path: Path) -> dict[tuple[str, ...], dict[str, str]]:
    """Read one rows file, keyed by the identifying columns present in it.

    Raises
    ------
    KeyCollision
        If two rows share a key. That would silently drop rows through dict
        overwrite and leave a comparison that passes because it compared almost
        nothing -- the failure mode this whole check exists to catch, so it
        raises rather than warns.
    """
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        return {}
    keys = tuple(k for k in KEYS if k in rows[0])
    out = {tuple(r.get(k, "") for k in keys): r for r in rows}
    if len(out) != len(rows):
        raise KeyCollisionError(
            f"{path.name}: {len(rows)} rows collapse onto {len(out)} keys using "
            f"{keys}; {len(rows) - len(out)} would be dropped silently"
        )
    return out


def compare(old_path: Path, new_path: Path, label: str) -> int:
    """Compare one table; return the number of violations."""
    old, new = load(old_path), load(new_path)
    if not old or not new:
        print(f"[{label}] SKIP: {'old' if not old else 'new'} rows absent")
        return 0
    violations = 0
    missing = set(old) - set(new)
    added = set(new) - set(old)
    if missing or added:
        print(f"[{label}] row sets differ: {len(missing)} missing, {len(added)} added")
        violations += len(missing) + len(added)

    changed: dict[str, int] = {}
    for key in sorted(set(old) & set(new)):
        for column, before in old[key].items():
            if column in PROVENANCE or column not in new[key]:
                continue
            if new[key][column] != before:
                changed[column] = changed.get(column, 0) + 1

    for column, count in sorted(changed.items()):
        verdict = "allowed" if column in MOVABLE else "VIOLATION"
        if column not in MOVABLE:
            violations += count
        print(f"[{label}]   {column:22s} differs in {count:5d} rows  -> {verdict}")
    if not changed:
        print(f"[{label}] every column bit-identical ({len(old)} rows)")
    return violations


def direction(old_path: Path, new_path: Path) -> int:
    """Check the predicted direction on ``rows_samples``; return violations."""
    old, new = load(old_path), load(new_path)
    if not old or not new:
        return 0
    dropped = flipped = 0
    for key in sorted(set(old) & set(new)):
        try:
            old_e = int(float(old[key]["reach1_eligible"] or 0))
            new_e = int(float(new[key]["reach1_eligible"] or 0))
            old_h = int(float(old[key]["reach1_hits"] or 0))
            new_h = int(float(new[key]["reach1_hits"] or 0))
        except (KeyError, ValueError):
            continue
        if new_e < old_e:
            dropped += 1
        if new_h < old_h:
            flipped += 1
    print()
    print("PRE-REGISTERED DIRECTION (the old index was strictly more restrictive):")
    print(f"   units where reach1_eligible FELL: {dropped}  (predicted 0)")
    print(f"   units where reach1_hits FELL:     {flipped}  (predicted 0)")
    if dropped or flipped:
        print("   -> FALSIFIED: the new index is not a superset of the old one")
    else:
        print("   -> holds")
    return dropped + flipped


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--old-root",
        required=True,
        type=Path,
        help=(
            "superseded results root. It MUST be a reach' lineage "
            "(IEEETKDE_isal_consensus or _reachprime); comparing against a "
            "pre-reach' root conflates the D-KBf5 library change with the index "
            "change under test, and rows_completion.reach1 legitimately moves "
            "there because reach() itself changed."
        ),
    )
    parser.add_argument("--new-root", required=True, type=Path, help="re-derived results root")
    args = parser.parse_args()

    base = "RQ6_generation/generation"
    total = 0
    for table in ("samples", "completion", "alignment", "rejections"):
        old = args.old_root / base / f"rows_{table}.csv"
        new = args.new_root / base / f"rows_{table}.csv"
        if not old.is_file() or not new.is_file():
            print(f"[{table}] SKIP: absent on one side")
            continue
        total += compare(old, new, table)
    total += direction(
        args.old_root / base / "rows_samples.csv",
        args.new_root / base / "rows_samples.csv",
    )
    print()
    print(f"VERDICT: {'PASS' if total == 0 else f'{total} violations'}")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
