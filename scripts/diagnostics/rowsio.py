"""The only sanctioned way for a diagnostic to read campaign rows.

Two defects recurred through the 2026-09-10 session, both silent, both producing
a confident wrong number, and both caught by a mechanical check rather than by
review:

* a value compared against the wrong spelling (``"1"`` against ``'1.0'``), which
  matched nothing and reported a rate of zero whose true value was 0.279;
* a row key that did not identify a row, which collapsed 600 completion rows onto
  6 and 62,398 RQ3 rows onto 57,941, and then *passed*.

Both were re-introduced by the same author within an hour of writing the lesson
about them. A rule that has to be remembered at each call site will not be, so
the guards live here and every diagnostic goes through :func:`load_rows` and
:func:`key_by`.

The rules, enforced rather than documented:

1. **Numeric fields are coerced, never string-compared.** :func:`num` is the only
   way to read one.
2. **A key must identify a row.** :func:`key_by` raises when two rows share a
   key rather than dropping one by last-wins.
3. **Every read reports the number of rows it consumed**, so a check that
   compared almost nothing is visible instead of green.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable, Sequence
from pathlib import Path


class RowsError(Exception):
    """A rows file could not be read under the guarantees this module makes."""


class KeyCollisionError(RowsError):
    """The chosen key columns do not uniquely identify a row."""


def num(value: str | None) -> float | None:
    """Read a numeric field, or ``None`` when blank or unparsable.

    Campaign CSVs spell the same logical value differently across corpora --
    ``'1'`` where nothing censored and ``'1.0'`` where something did, because a
    blank coerces the column to float (T-KBs). Comparing such a field against a
    string literal is the defect this function exists to remove: always write
    ``num(row["exact_recovery"]) == 1.0``.
    """
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def load_rows(path: Path, *, label: str | None = None, quiet: bool = False) -> list[dict[str, str]]:
    """Read one rows CSV and announce how many rows it consumed.

    Parameters
    ----------
    path : Path
        The CSV to read.
    label : str or None
        Name used in the announcement; defaults to the file name.
    quiet : bool
        Suppress the announcement. Use only when the caller prints its own N.

    Returns
    -------
    list of dict
        Every row, in file order.

    Raises
    ------
    RowsError
        If the file is missing or has no header.
    """
    if not path.is_file():
        raise RowsError(f"no rows file at {path}")
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise RowsError(f"{path} has no header")
        rows = list(reader)
    if not quiet:
        print(f"[rows] {label or path.name}: consumed {len(rows)} rows")
    return rows


def key_by(
    rows: Iterable[dict[str, str]],
    columns: Sequence[str],
    *,
    label: str = "rows",
) -> dict[tuple[str, ...], dict[str, str]]:
    """Index rows by ``columns``, refusing to lose any.

    Raises
    ------
    KeyCollisionError
        If two rows share a key. Dropping one by last-wins leaves a comparison
        that passes because it compared almost nothing, which is invisible
        precisely because passing looks like success. The error names the count
        so the caller can see which column is missing from the key -- on RQ3 the
        answer was ``radius``, because Corpus A writes one coverage row per
        radius per unit.
    """
    materialised = list(rows)
    indexed = {tuple(r.get(c, "") for c in columns): r for r in materialised}
    if len(indexed) != len(materialised):
        raise KeyCollisionError(
            f"{label}: {len(materialised)} rows collapse onto {len(indexed)} keys "
            f"using {tuple(columns)}; {len(materialised) - len(indexed)} would be "
            "dropped silently. A column that distinguishes them is missing."
        )
    return indexed


def expect_rows(rows: Sequence[object], expected: int, *, label: str = "rows") -> None:
    """Fail when a check consumed a different number of rows than expected.

    Raises
    ------
    RowsError
        If ``len(rows) != expected``.
    """
    if len(rows) != expected:
        raise RowsError(f"{label}: expected {expected} rows, consumed {len(rows)}")
