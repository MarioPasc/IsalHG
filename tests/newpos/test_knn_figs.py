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


def _facts() -> dict[str, str]:
    return CF.defined_facts((ROOT / "section" / "knn_facts.tex").read_text())[0]


@needs_root
def test_mechanism_second_row_follows_its_rule() -> None:
    import fig_mechanism as FM  # noqa: N812

    summary = json.loads((ROOT / "full_summary.json").read_text())
    meta = json.loads((ROOT / "section" / "fig_s5_mechanism.numbers.json").read_text())
    assert meta["rule2"] == FM.ROW2_RULE
    b = [
        c
        for c in summary["cells"].values()
        if c["design"] == "B" and c["condition"] == "pendant" and c["claim"]
    ]
    assert len(b) == 12
    leads = {
        c["id"]: c["per_arm"][K.PATH_SYM]["acc1"]["mean"] - c["per_arm"][K.OURS]["acc1"]["mean"]
        for c in b
    }
    assert meta["cell2"] == max(leads, key=leads.get)
    assert meta["rule2_lead_acc1"] == pytest.approx(leads[meta["cell2"]])
    # Every panel prints its own-nearer and tie shares: two arms x two rows x two shares.
    assert len(meta["printed"]) == 8
    assert {e["path"][-2] for e in meta["printed"]} == {"own_strictly_nearer", "tie"}


@needs_root
def test_mechanism_facts_match_the_summary() -> None:
    summary = json.loads((ROOT / "full_summary.json").read_text())
    facts = _facts()
    b = [
        c
        for c in summary["cells"].values()
        if c["design"] == "B" and c["condition"] == "pendant" and c["claim"]
    ]
    word = [c["mechanism"][K.OURS]["own_strictly_nearer"]["mean"] for c in b]
    edit = [c["mechanism"][K.PATH_SYM]["own_strictly_nearer"]["mean"] for c in b]
    higher = sum(e > w for w, e in zip(word, edit, strict=True))
    assert facts["mechB-edit-higher-cells"] == f"${higher}$"
    assert facts["mechB-own-word-range"] == (
        rf"${SF.down(100 * min(word), 0)}$ to ${SF.up(100 * max(word), 0)}$\,\%"
    )
    assert facts["mechB-own-edit-range"] == (
        rf"${SF.down(100 * min(edit), 0)}$ to ${SF.up(100 * max(edit), 0)}$\,\%"
    )
    for name in (
        "mech2-cell",
        "mech2-sibling-closer-word",
        "mech2-sibling-closer-edit",
        "mech-tie-word",
        "mech-tie-edit",
        "mech2-tie-word",
        "mech2-tie-edit",
        "mechB-tie-word-range",
        "mechB-tie-edit-range",
    ):
        assert name in facts, name


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
