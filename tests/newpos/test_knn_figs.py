"""The Section-S5 figures print exactly the numbers of the full-run summary.

Runs against a built tree: ``$KNN_FULL_ROOT`` if set, else ``full/`` when it
holds ``full_summary.json``, else ``full_local/``; skipped when none is built.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "newpos" / "knn"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "newpos" / "knn" / "figs"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "newpos"))

import check_facts as CF  # noqa: E402, N812
import knn_lib as K  # noqa: E402, N812
import section_facts as SF  # noqa: E402, N812
import style as S  # noqa: E402, N812

pytestmark = pytest.mark.integration


def _root() -> Path | None:
    env = os.environ.get("KNN_FULL_ROOT")
    candidates = [Path(env)] if env else [K.OUT_ROOT / "full", K.OUT_ROOT / "full_local"]
    for root in candidates:
        if (root / "full_summary.json").exists() and (root / "section").is_dir():
            return root
    return None


ROOT = _root()
needs_root = pytest.mark.skipif(ROOT is None, reason="no built full-run tree")


def _sidecars() -> list[Path]:
    return sorted((ROOT / "section").glob("fig_s5_*.numbers.json")) if ROOT else []


@needs_root
@pytest.mark.parametrize("sidecar", _sidecars(), ids=lambda p: p.stem)
def test_printed_numbers_match_the_summary(sidecar: Path) -> None:
    summary = json.loads((ROOT / "full_summary.json").read_text())
    text = (ROOT / "FULL_SUMMARY.md").read_text() + (ROOT / "FULL_DETAIL.md").read_text()
    for entry in json.loads(sidecar.read_text())["printed"]:
        value = S.lookup(summary, entry["path"])
        assert value == entry["value"], entry["path_str"]
        assert f"{value * entry['scale']:.{entry['nd']}f}" == entry["printed"], entry["path_str"]
        assert f"{value:.3f}" in text, (
            f"{entry['path_str']} = {value:.3f} not in FULL_SUMMARY/DETAIL"
        )


@needs_root
def test_every_figure_was_built() -> None:
    for stem in ("tsne", "accuracy", "gap", "mechanism"):
        assert (ROOT / "section" / f"fig_s5_{stem}.pdf").stat().st_size > 0


@needs_root
@pytest.mark.skipif(not CF.DEFAULT_TEX.exists(), reason="section source not mounted")
def test_facts_cover_the_section() -> None:
    assert CF.check(CF.DEFAULT_TEX, ROOT / "section" / "knn_facts.tex") == []


@pytest.mark.unit
@pytest.mark.parametrize(
    ("x", "nd", "down", "up", "near"),
    [
        (0.41249, 3, "0.412", "0.413", "0.412"),
        (0.4125, 3, "0.412", "0.413", "0.413"),
        (0.3, 3, "0.300", "0.300", "0.300"),
        (1.749, 2, "1.74", "1.75", "1.75"),
    ],
)
def test_bound_rule(x: float, nd: int, down: str, up: str, near: str) -> None:
    assert SF.down(x, nd) == down
    assert SF.up(x, nd) == up
    assert SF.rnd(x, nd) == near
