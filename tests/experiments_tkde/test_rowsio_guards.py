"""The diagnostic row-reading guards must fail loudly, not quietly.

Both defects these guards remove were re-introduced by the author within an hour
of writing the lesson about them, so the guards are tested rather than trusted:
a rule that must be remembered at each call site will not be.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "diagnostics"))

import rowsio  # noqa: E402

pytestmark = pytest.mark.unit


class TestNumericCoercion:
    """The same logical value is spelled differently across corpora (T-KBs)."""

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [("1", 1.0), ("1.0", 1.0), ("0", 0.0), ("0.0", 0.0), ("2.5", 2.5), ("-1", -1.0)],
    )
    def test_both_spellings_coerce_to_the_same_value(self, raw: str, expected: float) -> None:
        assert rowsio.num(raw) == expected

    @pytest.mark.parametrize("raw", ["", None, "n/a", "NULL", "  "])
    def test_unparsable_is_none_not_zero(self, raw: str | None) -> None:
        # None, never 0.0: a blank means "not computed", and folding it into a
        # zero reports a measured failure the pipeline never measured.
        assert rowsio.num(raw) is None

    def test_the_bug_this_removes(self) -> None:
        """``'1.0' == "1"`` is False; the coercion is the whole point."""
        assert "1.0" != "1"
        assert rowsio.num("1.0") == rowsio.num("1") == 1.0


class TestKeyCollision:
    """A key that does not identify a row must raise, never drop by last-wins."""

    @staticmethod
    def _rows() -> list[dict[str, str]]:
        # The shape that caused the RQ3 defect: one row per (unit, radius), with
        # a key that omits radius.
        return [
            {"unit": "u1", "radius": "2", "value": "10"},
            {"unit": "u1", "radius": "t", "value": "99"},
            {"unit": "u2", "radius": "2", "value": "20"},
            {"unit": "u2", "radius": "t", "value": "88"},
        ]

    def test_an_incomplete_key_raises(self) -> None:
        with pytest.raises(rowsio.KeyCollisionError) as caught:
            rowsio.key_by(self._rows(), ("unit",), label="probe")
        message = str(caught.value)
        assert "4 rows collapse onto 2 keys" in message
        assert "2 would be" in message

    def test_a_complete_key_keeps_every_row(self) -> None:
        indexed = rowsio.key_by(self._rows(), ("unit", "radius"))
        assert len(indexed) == 4
        assert indexed[("u1", "t")]["value"] == "99"

    def test_the_silent_failure_it_prevents(self) -> None:
        """Without the guard, last-wins keeps 2 of 4 rows and looks successful."""
        naive = {r["unit"]: r for r in self._rows()}
        assert len(naive) == 2, "the naive index really does lose half the rows"
        assert naive["u1"]["value"] == "99", "and silently keeps whichever came last"


class TestExpectRows:
    """A check whose N differs from the expected N fails rather than passes."""

    def test_matching_count_passes(self) -> None:
        rowsio.expect_rows([1, 2, 3], 3)

    def test_mismatched_count_raises(self) -> None:
        with pytest.raises(rowsio.RowsError, match="expected 600 rows, consumed 6"):
            rowsio.expect_rows([1] * 6, 600, label="completion")


class TestLoadRows:
    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(rowsio.RowsError, match="no rows file"):
            rowsio.load_rows(tmp_path / "absent.csv")

    def test_reports_the_count_it_consumed(self, tmp_path: Path, capsys) -> None:  # noqa: ANN001
        path = tmp_path / "rows.csv"
        path.write_text("a,b\n1,2\n3,4\n")
        rows = rowsio.load_rows(path, label="probe")
        assert len(rows) == 2
        assert "consumed 2 rows" in capsys.readouterr().out
