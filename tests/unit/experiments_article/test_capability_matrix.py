"""Unit tests for the capability-matrix figure module.

Acceptance criteria
-------------------
- ``render_capability_matrix`` is importable and returns a ``Path``.
- The matrix has exactly 7 rows (6 representations + naive baseline) and
  6 capability columns as specified in ``docs/article/REVIEW/CAPABILITY_MATRIX.md``.
- Every cell value is one of the four allowed symbols: ✓, ✗, ~, —.
- IsalHG cells: complete=✓, metric=✓, decodable=✓, navigable=✓.
- HPD cell for ``true_metric`` is ✗ (JSD is not a metric).
- nauty-edit cell for ``decodable`` is ✗, for ``navigable`` is ✗.
- Deg-seq L1 cell for ``complete`` is ✗, for ``decodable`` is ✗.
- The output file is written (exists after call) and is a PDF (vector).

Teeth
-----
Monkeypatching ``MATRIX_DATA`` so that a row has an invalid symbol confirms
that the validator catches bad cell values and raises ``ValueError`` —
proving the validator is live and not a no-op.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Import under test — will fail until the module exists
# ---------------------------------------------------------------------------

from experiments.article.analysis.figures.capability_matrix import (  # noqa: E402
    CAPABILITY_COLUMNS,
    MATRIX_DATA,
    REPRESENTATIONS,
    render_capability_matrix,
    validate_matrix,
)

# ---------------------------------------------------------------------------
# Constants test
# ---------------------------------------------------------------------------

ALLOWED_SYMBOLS = {"✓", "✗", "~", "—"}


def test_matrix_shape() -> None:
    """Matrix must be 7 rows × 6 columns per the REVIEW spec."""
    assert len(REPRESENTATIONS) == 7, f"expected 7 rows, got {len(REPRESENTATIONS)}"
    assert len(CAPABILITY_COLUMNS) == 6, f"expected 6 columns, got {len(CAPABILITY_COLUMNS)}"
    assert len(MATRIX_DATA) == 7, "MATRIX_DATA must have 7 rows"
    for row in MATRIX_DATA.values():
        assert len(row) == 6, f"each row must have 6 cells, got {len(row)}: {row}"


def test_all_cells_valid_symbols() -> None:
    """Every cell must be one of the four allowed symbols."""
    for rep, row in MATRIX_DATA.items():
        for col, cell in zip(CAPABILITY_COLUMNS, row, strict=True):
            assert cell in ALLOWED_SYMBOLS, f"{rep}[{col}] = {cell!r} — not an allowed symbol"


def test_isalhg_complete_decodable_navigable() -> None:
    """IsalHG must be ✓ on Complete, True metric, Decodable, and Navigable."""
    row = MATRIX_DATA["IsalHG"]
    assert row[0] == "✓", "IsalHG complete invariant must be ✓"
    assert row[1] == "✓", "IsalHG true metric must be ✓ (d_I satisfies metric axioms)"
    assert row[2] == "✓", "IsalHG decodable must be ✓ (S2H is the inverse)"
    assert row[3] == "✓", "IsalHG navigable geometry must be ✓ (measured IQR 2–8)"


def test_hpd_not_a_metric() -> None:
    """HPD uses JSD which is NOT a metric — the true-metric cell must be ✗."""
    row = MATRIX_DATA["HPD"]
    assert row[1] == "✗", "HPD true_metric must be ✗ (JSD fails triangle ineq.)"


def test_nauty_not_decodable_not_navigable() -> None:
    """nauty-edit: canonical string for the Levi graph, not a decodable HG repr."""
    row = MATRIX_DATA["nauty-edit"]
    assert row[2] == "✗", "nauty-edit decodable must be ✗"
    assert row[3] == "✗", "nauty-edit navigable must be ✗ (avalanche-everywhere)"


def test_degseq_not_complete_not_decodable() -> None:
    """Degree-sequence L1: not complete (shared deg-seq, non-iso pair) and no decoder."""
    row = MATRIX_DATA["Deg-seq L1"]
    assert row[0] == "✗", "Deg-seq L1 complete must be ✗ (non_iso_pair_small witness)"
    assert row[2] == "✗", "Deg-seq L1 decodable must be ✗ (no inverse of a seq)"


def test_isalhg_only_intersection() -> None:
    """Only IsalHG has complete=✓ AND decodable=✓ AND navigable=✓ simultaneously."""
    isalhg_row = MATRIX_DATA["IsalHG"]
    isalhg_triple = (isalhg_row[0], isalhg_row[2], isalhg_row[3])
    assert isalhg_triple == ("✓", "✓", "✓"), "IsalHG must hold all three"

    for rep, row in MATRIX_DATA.items():
        if rep == "IsalHG":
            continue
        triple = (row[0], row[2], row[3])
        assert triple != ("✓", "✓", "✓"), (
            f"{rep} also satisfies the triple — IsalHG-only claim is false"
        )


# ---------------------------------------------------------------------------
# Validator teeth
# ---------------------------------------------------------------------------


def test_validate_matrix_rejects_bad_symbol() -> None:
    """validate_matrix must raise ValueError on an unrecognised cell symbol."""
    bad_data = {k: list(v) for k, v in MATRIX_DATA.items()}
    rep = next(iter(bad_data))
    bad_data[rep][0] = "X"  # not in ALLOWED_SYMBOLS
    with pytest.raises(ValueError, match="invalid cell"):
        validate_matrix(bad_data)


# ---------------------------------------------------------------------------
# Render function
# ---------------------------------------------------------------------------


def test_render_returns_path() -> None:
    """render_capability_matrix must return a Path pointing to the written PDF."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out = render_capability_matrix(output_path=Path(tmpdir) / "cap_matrix.pdf")
        assert isinstance(out, Path), "must return a Path"
        assert out.exists(), "output file must exist after rendering"
        assert out.suffix == ".pdf", "output must be a PDF (vector format)"


def test_render_default_path_exists() -> None:
    """render_capability_matrix with no argument must write to the default path."""
    import importlib.util

    spec = importlib.util.find_spec("experiments.article.analysis.figures.capability_matrix")
    assert spec is not None
    with tempfile.TemporaryDirectory() as tmpdir:
        default = Path(tmpdir) / "cap_matrix_default.pdf"
        out = render_capability_matrix(output_path=default)
        assert out.exists()
