"""Unit tests for the KNN_2026-10-15 full-run aggregator and task decode."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "newpos" / "knn"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "newpos"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import aggregate_full as AF  # noqa: E402, N812
import full_run as FR  # noqa: E402, N812
import knn_lib as K  # noqa: E402, N812

pytestmark = pytest.mark.unit


def _series(word: list[float], others: dict[str, list[float]], **kw) -> AF.Series:
    s = AF.Series(
        cell_id="B/pendant/wd50k66/r1",
        design="B",
        condition="pendant",
        c=None,
        collection="wd50k66",
        r=1,
        hypothesis=kw.pop("hypothesis", "H-KNN-B"),
        claim=kw.pop("claim", True),
        competitors=K.COMPETITORS_FULL,
        feasible=kw.pop("feasible", None),
    )
    for i in range(len(word)):
        arms = {K.OURS: {"acc1": word[i], "ari": word[i] / 2}}
        for a, v in others.items():
            arms[a] = {"acc1": v[i], "ari": v[i] / 2}
        s.add(i, arms, ("acc1", "ari"))
        s.diag["n_items"].append(100)
    return s


def _flat(n: int, value: float, rng: np.random.Generator) -> list[float]:
    return list(value + rng.normal(0, 0.01, n))


def test_word_ahead_of_every_competitor_survives() -> None:
    rng = np.random.default_rng(0)
    others = {a: _flat(27, 0.5, rng) for a in K.COMPETITORS_FULL}
    others[K.PATH_ASRUN] = _flat(27, 0.95, rng)  # the as-run row never kills
    cell = AF.aggregate_series(_series(_flat(27, 0.8, rng), others))
    assert cell["verdict"] == "word ahead"
    assert cell["word_significant_vs_all"] == {"acc1": True, "ari": True}
    assert cell["as_run_path"]["acc1"]["ge_word"] is True
    assert K.PATH_ASRUN not in cell["tests"]["acc1"]
    assert set(cell["tests"]["acc1"]) == set(K.COMPETITORS_FULL)


def test_a_competitor_at_or_above_the_word_kills() -> None:
    rng = np.random.default_rng(1)
    others = {a: _flat(27, 0.5, rng) for a in K.COMPETITORS_FULL}
    others[K.PATH_SYM] = _flat(27, 0.9, rng)
    cell = AF.aggregate_series(_series(_flat(27, 0.8, rng), others))
    assert cell["verdict"] == "kill"
    assert cell["killers"]["acc1"] == [K.PATH_SYM]
    assert cell["best_competitor"]["acc1"]["arm"] == K.PATH_SYM
    t = cell["tests"]["acc1"][K.PATH_SYM]
    assert t["p_holm"] > 0.5 and t["p_holm_rev"] < 0.05
    assert cell["diff_word_minus_best"]["acc1"]["mean"] < 0


def test_wl_h1_is_an_added_row_outside_designs_a_and_b() -> None:
    rng = np.random.default_rng(4)
    ten = tuple(a for a in K.COMPETITORS_FULL if a != K.WL_H1)
    others = {a: _flat(27, 0.5, rng) for a in K.COMPETITORS_FULL}
    others[K.WL_H1] = _flat(27, 0.95, rng)
    s = _series(_flat(27, 0.8, rng), others)
    s.competitors = ten
    cell = AF.aggregate_series(s)
    assert cell["verdict"] == "word ahead"
    assert K.WL_H1 not in cell["tests"]["acc1"] and len(cell["tests"]["acc1"]) == 10
    assert cell["added_rows"][K.WL_H1]["acc1"]["ge_word"] is True
    flags = AF.added_row_flags({cell["id"]: cell})
    assert flags[K.WL_H1]["H-KNN-B"]["reaches_word"][0]["cell"] == cell["id"]
    assert cell["best_arm_overall"]["acc1"]["arm"] == K.OURS


def test_infeasible_and_non_claim_cells() -> None:
    rng = np.random.default_rng(2)
    others = {a: _flat(5, 0.5, rng) for a in K.COMPETITORS_FULL}
    inf = AF.aggregate_series(_series(_flat(5, 0.8, rng), others, feasible=False))
    assert inf["verdict"] == "infeasible"
    nc = AF.aggregate_series(_series(_flat(5, 0.2, rng), others, claim=False))
    assert nc["verdict"] == "competitor ahead (no claim)"


def test_holm_families_are_monotone() -> None:
    word = [0.8, 0.82, 0.79, 0.81, 0.83, 0.8, 0.78, 0.84]
    comps = {"a": [0.5] * 8, "b": [0.79, 0.8, 0.8, 0.8, 0.81, 0.79, 0.79, 0.82]}
    t = AF.tests_for(word, comps)
    for arm in comps:
        assert t[arm]["p_holm"] >= t[arm]["p_raw"]
        assert t[arm]["p_holm_rev"] >= t[arm]["p_raw_rev"]
    assert t["a"]["rank_biserial"] == pytest.approx(1.0)


def test_nearest_same_other() -> None:
    D = np.array(
        [
            [0.0, 1.0, 3.0, 2.0],
            [1.0, 0.0, 4.0, 5.0],
            [3.0, 4.0, 0.0, 0.5],
            [2.0, 5.0, 0.5, 0.0],
        ]
    )
    codes = np.array([0, 0, 1, 1])
    same, other = K.nearest_same_other(D, codes)
    np.testing.assert_array_equal(same, [1.0, 1.0, 0.5, 0.5])
    np.testing.assert_array_equal(other, [2.0, 4.0, 3.0, 2.0])
    mask = np.ones((4, 4), dtype=bool)
    mask[0, 1] = False
    same, _ = K.nearest_same_other(D, codes, mask)
    assert same[0] == np.inf


def test_source_and_other() -> None:
    import design_d as DD  # noqa: N812

    D = np.array([[3.0, 1.0, 2.0], [0.0, 0.0, 4.0]])
    d_src, d_other = DD.source_and_other(D, np.array([0, 1]))
    np.testing.assert_array_equal(d_src, [3.0, 0.0])
    np.testing.assert_array_equal(d_other, [1.0, 0.0])


def test_task_decode_covers_every_unit_once() -> None:
    names = [u.name for u in FR.units()]
    assert len(names) == len(set(names)) == 38
    flat = [n for group in FR.tasks() for n in group]
    assert sorted(flat) == sorted(names)
    assert set(FR.SMOKE_UNITS) <= set(names)
    cmd = FR.units()[0].command(Path("/o"), 4)
    assert cmd[cmd.index("--seeds") + 1 : cmd.index("--out")] == [str(s) for s in range(27)]
    assert "full" in cmd and "--no-summary" in cmd
