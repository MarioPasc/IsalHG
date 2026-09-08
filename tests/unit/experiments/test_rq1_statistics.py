"""Unit tests for ``scripts/tkde/rq1_statistics.py``.

Every frame here is synthetic and tiny. The real campaign lives on the cluster;
what is testable locally is the arithmetic that turns rows into intervals -- the
restriction, the cluster keys and their guards, the Holm family, and the
degenerate cases.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

pytestmark = pytest.mark.unit

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "tkde" / "rq1_statistics.py"


def _load_module() -> Any:
    """Import the script by path; ``scripts/`` is not an importable package."""
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    spec = importlib.util.spec_from_file_location("rq1_statistics", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # ``dataclasses`` resolves annotations through ``sys.modules[cls.__module__]``,
    # so the module has to be registered before its body runs.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


rq1 = _load_module()


ARMS = ("wstar_orbit", "isal_ow_struct", "nauty_cert_rows")


def _m1_frame(
    *,
    collections: tuple[str, ...] = ("synthetic_rq1",),
    members_per_collection: int = 4,
    edits: int = 3,
    arms: tuple[str, ...] = ARMS,
    censor: dict[str, set[int]] | None = None,
) -> pd.DataFrame:
    """A synthetic ``rows_m1`` frame with a deterministic response per arm.

    ``censor`` maps an arm to the ``edit_idx`` values it failed to complete, which
    is how the real tree's per-arm censoring shows up.
    """
    censor = censor or {}
    records: list[dict[str, Any]] = []
    for collection in collections:
        for member in range(members_per_collection):
            base_id = f"{member}@{2000 + member}" if collection == "ndc_classes" else str(member)
            for kind, regime in (("pendant", 0), ("interior", 1)):
                for idx in range(edits):
                    for offset, arm in enumerate(arms):
                        records.append(
                            {
                                "collection": collection,
                                "seed": 7,
                                "base_id": base_id,
                                "edit_kind": kind,
                                "edit_idx": idx,
                                "regime": regime,
                                "arm": arm,
                                "d_instr": 1 + offset + (idx % 2) + regime,
                                "censored": idx in censor.get(arm, set()),
                            }
                        )
    return pd.DataFrame.from_records(records)


class TestRestriction:
    """The intersection that makes arms comparable."""

    def test_censored_arm_shrinks_every_arm_to_the_same_n(self) -> None:
        frame = rq1.drop_censored(_m1_frame(censor={"isal_ow_struct": {2}}))
        restricted, report = rq1.restrict_to_common_units(frame, rq1.M1_UNIT_KEYS, ARMS, "d_instr")
        counts = restricted.groupby("arm").size()
        assert set(counts.unique()) == {report["units_after"]}
        # 4 members x 2 kinds x 2 surviving edit indices.
        assert report["units_after"] == 16
        assert report["units_per_arm_before"]["wstar_orbit"] == 24
        assert report["units_per_arm_before"]["isal_ow_struct"] == 16

    def test_missing_arm_is_reported_not_required(self) -> None:
        frame = rq1.drop_censored(_m1_frame())
        _, report = rq1.restrict_to_common_units(
            frame, rq1.M1_UNIT_KEYS, (*ARMS, "never_run"), "d_instr"
        )
        assert report["arms_missing"] == ["never_run"]
        assert report["units_after"] == 24

    def test_empty_intersection_raises(self) -> None:
        # Complementary censoring: both arms still appear, on disjoint units.
        frame = rq1.drop_censored(_m1_frame(censor={"isal_ow_struct": {0, 1}, "wstar_orbit": {2}}))
        with pytest.raises(rq1.RestrictionError):
            rq1.restrict_to_common_units(frame, rq1.M1_UNIT_KEYS, ARMS, "d_instr")


class TestClusterKeys:
    """The entity/ladder keys and the inventory guards."""

    def test_entity_split_is_a_no_op_without_an_at_sign(self) -> None:
        ids = pd.Series(["3@443", "3@444", "17", "17"])
        assert rq1.entity_of(ids).tolist() == ["3", "3", "17", "17"]

    def test_m1_structure_raises_when_ndc_does_not_coarsen(self) -> None:
        frame = _m1_frame(collections=("ndc_classes",))
        frame["base_id"] = frame["base_id"].str.replace("@", "_", regex=False)
        with pytest.raises(rq1.ClusterStructureError, match="silently failed"):
            rq1.check_m1_structure(frame, strict=True)

    def test_m1_structure_reports_instead_of_raising_when_not_strict(self) -> None:
        frame = _m1_frame(collections=("ndc_classes",))
        frame["base_id"] = frame["base_id"].str.replace("@", "_", regex=False)
        lines = rq1.check_m1_structure(frame, strict=False)
        assert any("ndc_classes" in line for line in lines)

    def test_m2_structure_raises_on_the_wrong_inventory(self) -> None:
        frame = pd.DataFrame(
            {
                "collection": ["wd50k66"] * 6,
                "seed": [1, 1, 1, 2, 2, 2],
                "series": ["ladder"] * 6,
                "pair_id": ["Q1|t1", "Q1|t2", "Q1|t3", "Q2|t1", "Q2|t2", "Q2|t3"],
                "regime": [1] * 6,
                "arm": ["wstar_orbit"] * 6,
                "d": [1, 2, 3, 1, 2, 3],
                "delta": [1, 2, 3, 1, 2, 3],
                "censored": [False] * 6,
            }
        )
        with pytest.raises(rq1.ClusterStructureError):
            rq1.check_m2_structure(frame, strict=True)

    def test_m2_ladder_key_is_the_prefix_and_natural_key_is_the_entity(self) -> None:
        frame = pd.DataFrame(
            {
                "collection": ["wd50k66", "ndc_classes"],
                "series": ["ladder", "natural"],
                "pair_id": ["Q1000|t3", "3@443|3@444"],
            }
        )
        keys = rq1.m2_cluster_key(frame).tolist()
        assert keys == ["wd50k66::ladder::Q1000", "ndc_classes::natural::3"]

    def test_parse_failure_guard_fires_on_one_cluster_per_row(self) -> None:
        with pytest.raises(rq1.ClusterStructureError, match="did not parse"):
            rq1.guard_parse_failure(10, 10, "m2 test")

    def test_parse_failure_guard_is_silent_on_tiny_groups(self) -> None:
        rq1.guard_parse_failure(2, 2, "m2 test")


class TestClusterFractionCi:
    """The pooled within-two fraction and its cluster bootstrap."""

    def test_interval_is_bounded_and_covers_the_point(self) -> None:
        rng = np.random.default_rng(3)
        indicator = rng.integers(0, 2, size=60).astype(float)
        clusters = np.repeat(np.arange(20), 3)
        result = rq1.cluster_fraction_ci(indicator, clusters, n_resamples=400, seed=0)
        assert result is not None
        assert 0.0 <= result["low"] <= result["point"] <= result["high"] <= 1.0
        assert result["n"] == 60
        assert result["n_clusters"] == 20

    def test_clustering_widens_the_interval(self) -> None:
        # Every row of a cluster is identical, so the clustered bootstrap has 12
        # independent draws where the row-level bootstrap thinks it has 60.
        per_cluster = np.array([1.0] * 6 + [0.0] * 6)
        indicator = np.repeat(per_cluster, 5)
        clustered = rq1.cluster_fraction_ci(
            indicator, np.repeat(np.arange(12), 5), n_resamples=2000, seed=0
        )
        independent = rq1.cluster_fraction_ci(
            indicator, np.arange(indicator.size), n_resamples=2000, seed=0
        )
        assert clustered is not None and independent is not None
        assert clustered["point"] == pytest.approx(independent["point"])
        clustered_width = clustered["high"] - clustered["low"]
        independent_width = independent["high"] - independent["low"]
        assert clustered_width > independent_width

    def test_single_cluster_is_degenerate_not_an_error(self) -> None:
        result = rq1.cluster_fraction_ci([1.0, 0.0, 1.0], ["a", "a", "a"], n_resamples=50)
        assert result is not None
        assert result["method"] == "degenerate_single_cluster"
        assert result["low"] == result["point"] == result["high"]

    def test_empty_input_returns_none(self) -> None:
        assert rq1.cluster_fraction_ci([], [], n_resamples=50) is None


class TestClusterMedianCi:
    """The pooled median with a per-cluster BCa interval."""

    def test_point_is_pooled_and_interval_covers_it(self) -> None:
        pooled = np.array([1.0, 1.0, 2.0, 8.0, 9.0, 9.0])
        per_cluster = np.array([1.0, 8.5, 9.0])
        result = rq1.cluster_median_ci(pooled, per_cluster, n_resamples=400, seed=0)
        assert result is not None
        assert result["point"] == pytest.approx(5.0)
        assert result["low"] <= result["point"] <= result["high"]
        assert result["n_clusters"] == 3

    def test_empty_returns_none(self) -> None:
        assert rq1.cluster_median_ci([], [], n_resamples=50) is None


class TestSpearmanHelpers:
    """The hand-written rho and the paired difference bootstrap."""

    def test_rho_matches_scipy(self) -> None:
        from scipy.stats import spearmanr

        rng = np.random.default_rng(11)
        x = rng.normal(size=40)
        y = 0.7 * x + rng.normal(size=40)
        assert rq1.spearman_rho(x, y) == pytest.approx(float(spearmanr(x, y).statistic))

    def test_rho_is_nan_on_a_constant_side(self) -> None:
        assert np.isnan(rq1.spearman_rho(np.ones(10), np.arange(10.0)))

    def test_paired_difference_is_zero_for_identical_arms(self) -> None:
        rng = np.random.default_rng(5)
        delta = rng.integers(1, 6, size=50).astype(float)
        response = delta + rng.normal(scale=0.3, size=50)
        result = rq1.paired_rho_difference(
            delta, response, response, np.repeat(np.arange(10), 5), n_resamples=200, seed=0
        )
        assert result is not None
        assert result["point"] == pytest.approx(0.0)
        assert result["low"] <= 0.0 <= result["high"]
        assert result["p_raw"] == pytest.approx(1.0)

    def test_paired_difference_returns_none_on_a_constant_predictor(self) -> None:
        assert (
            rq1.paired_rho_difference(
                np.ones(10),
                np.arange(10.0),
                np.arange(10.0),
                np.repeat(np.arange(5), 2),
                n_resamples=20,
            )
            is None
        )


class TestPairedFamily:
    """Holm across the arms of one family, with the reference excluded."""

    def test_reference_is_excluded_and_holm_covers_the_family(self) -> None:
        rng = np.random.default_rng(2)
        reference = rng.normal(size=30)
        others = {
            "isal_ow_struct": reference + rng.normal(scale=0.1, size=30) + 1.0,
            "isal_ow_rank": reference + rng.normal(scale=0.1, size=30) + 0.5,
            "nauty_cert_rows": reference + rng.normal(scale=0.1, size=30) - 2.0,
        }
        rows = rq1.paired_cluster_family(reference, others, n_resamples=200, seed=0)
        assert [row["arm"] for row in rows] == list(others)
        assert "wstar_orbit" not in [row["arm"] for row in rows]
        assert all(row["p_holm"] >= row["p_raw"] for row in rows)
        # Holm's largest adjustment is the family size on the smallest p.
        smallest = min(rows, key=lambda row: row["p_raw"])
        assert smallest["p_holm"] == pytest.approx(min(1.0, smallest["p_raw"] * len(rows)))

    def test_identical_arms_are_not_significant(self) -> None:
        reference = np.arange(20.0)
        rows = rq1.paired_cluster_family(
            reference, {"twin": reference.copy()}, n_resamples=100, seed=0
        )
        assert rows[0]["p_raw"] == pytest.approx(1.0)
        assert rows[0]["reject"] is False


class TestAnalyzeM1:
    """The M1 driver on a frame small enough to check by hand."""

    def test_cells_are_ordered_pendant_first_and_carry_all_three_counts(self) -> None:
        frame = rq1.drop_censored(_m1_frame(censor={"isal_ow_struct": {2}}))
        section = rq1.analyze_m1(frame, ARMS, "wstar_orbit", n_resamples=200, seed=0, strict=False)
        regimes = [cell["regime"] for cell in section["cells"]]
        assert regimes == sorted(regimes)
        assert regimes[0] == 0
        for cell in section["cells"]:
            assert cell["n_clusters"] >= 1
            assert cell["n_members"] >= cell["n_clusters"]
            assert {row["arm"] for row in cell["arms"]} == set(ARMS)
            for statistic in ("response", "within"):
                arms_tested = {row["arm"] for row in cell["comparisons"][statistic]}
                assert "wstar_orbit" not in arms_tested

    def test_ndc_members_collapse_onto_entities(self) -> None:
        frame = rq1.drop_censored(_m1_frame(collections=("ndc_classes",)))
        frame["base_id"] = "3@" + frame["base_id"].str.split("@").str[1]
        section = rq1.analyze_m1(frame, ARMS, "wstar_orbit", n_resamples=100, seed=0, strict=False)
        for cell in section["cells"]:
            assert cell["n_members"] == 4
            assert cell["n_clusters"] == 1

    def test_unknown_reference_arm_raises(self) -> None:
        frame = rq1.drop_censored(_m1_frame())
        with pytest.raises(rq1.Rq1StatisticsError):
            rq1.analyze_m1(frame, ARMS, "not_an_arm", n_resamples=50, strict=False)


class TestAnalyzeM2:
    """The M2 driver, with the structural assertions relaxed for a toy frame."""

    @staticmethod
    def _frame() -> pd.DataFrame:
        records: list[dict[str, Any]] = []
        for entity in range(6):
            for quarter in range(4):
                for arm_index, arm in enumerate(ARMS):
                    delta = quarter + 1
                    records.append(
                        {
                            "collection": "ndc_classes",
                            "seed": 1,
                            "series": "natural",
                            "pair_id": f"{entity}@{400 + quarter}|{entity}@{401 + quarter}",
                            "delta": delta,
                            "regime": 0,
                            "arm": arm,
                            "d": delta * (arm_index + 1) + (quarter % 2),
                            "censored": False,
                        }
                    )
        return pd.DataFrame.from_records(records)

    def test_groups_carry_rho_and_holm_corrected_differences(self) -> None:
        section = rq1.analyze_m2(
            rq1.drop_censored(self._frame()),
            ARMS,
            "wstar_orbit",
            n_resamples=200,
            seed=0,
            strict=False,
        )
        assert len(section["groups"]) == 1
        group = section["groups"][0]
        assert group["n"] == 24
        assert group["n_clusters"] == 6
        assert all(entry["rho"] is not None for entry in group["arms"])
        assert {entry["arm"] for entry in group["differences"]} == set(ARMS) - {"wstar_orbit"}
        assert all("p_holm" in entry["difference"] for entry in group["differences"])

    def test_constant_delta_yields_none_rather_than_raising(self) -> None:
        frame = self._frame()
        frame["delta"] = 1
        section = rq1.analyze_m2(
            rq1.drop_censored(frame),
            ARMS,
            "wstar_orbit",
            n_resamples=50,
            seed=0,
            strict=False,
        )
        group = section["groups"][0]
        assert all(entry["rho"] is None for entry in group["arms"])
        assert all(entry["difference"] is None for entry in group["differences"])

    def test_one_cluster_per_row_raises(self) -> None:
        frame = self._frame()
        # The entity separator is gone, so the key degenerates to the pair id.
        frame["pair_id"] = frame["pair_id"].str.replace("@", "_", regex=False)
        with pytest.raises(rq1.ClusterStructureError, match="did not parse"):
            rq1.analyze_m2(
                rq1.drop_censored(frame),
                ARMS,
                "wstar_orbit",
                n_resamples=50,
                seed=0,
                strict=False,
            )


class TestAnalyzeM4:
    """The M4 driver against the row-granular certificate."""

    @staticmethod
    def _frame() -> pd.DataFrame:
        records: list[dict[str, Any]] = []
        for pair in range(12):
            for arm_index, arm in enumerate(ARMS):
                records.append(
                    {
                        "collection": "wd50k66",
                        "seed": 3,
                        "series": "random",
                        "pair_id": f"a{pair}|b{pair}|{pair}",
                        "arm": arm,
                        "d": pair * (arm_index + 1) + (pair % 3),
                        "d_cert": pair,
                        "censored": False,
                    }
                )
        return pd.DataFrame.from_records(records)

    def test_certificate_correlates_perfectly_with_itself(self) -> None:
        section = rq1.analyze_m4(rq1.drop_censored(self._frame()), ARMS, n_resamples=100, seed=0)
        rows = {entry["arm"]: entry["rho"] for entry in section["collections"][0]["arms"]}
        assert rows[rq1.CERT_ROWS_ARM]["point"] == pytest.approx(1.0)
        assert all(-1.0 <= row["low"] <= row["high"] <= 1.0 for row in rows.values())

    def test_missing_certificate_arm_raises(self) -> None:
        frame = self._frame()
        frame = frame[frame["arm"] != rq1.CERT_ROWS_ARM]
        with pytest.raises(rq1.Rq1StatisticsError, match=rq1.CERT_ROWS_ARM):
            rq1.analyze_m4(rq1.drop_censored(frame), ARMS[:2], n_resamples=50, seed=0)


class TestRendering:
    """The Markdown carries the counts and the units sentence."""

    def test_report_states_the_unit_restriction_under_every_table(self) -> None:
        frame = rq1.drop_censored(_m1_frame())
        payload = {
            "run": {
                "exp_dir": "/tmp/example",
                "arms": list(ARMS),
                "reference": "wstar_orbit",
                "n_resamples": 100,
                "seed": 0,
                "confidence": 0.95,
            },
            "m1": rq1.analyze_m1(frame, ARMS, "wstar_orbit", n_resamples=100, seed=0, strict=False),
        }
        text = rq1.render_markdown(payload)
        assert text.count(rq1.UNIT_SENTENCE) >= 2
        assert "n_clusters" in text
        assert "seed 0" in text
