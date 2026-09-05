"""Unit tests for the matrices job and the RQ4 / RQ5 runners and analyzers.

These test the parts that are cheap to get silently wrong and expensive to
discover on the cluster: the unit decode (a wrong decode yields a complete,
plausible, wrong result set), the even shard split, the strict matrix-cache
reader (which is the only thing standing between a missing dependency and an
eight-hour recomputation inside a wall sized for reading), and the analyzers'
refusal to decide a hypothesis on too few seeds.

The heavier end-to-end paths are exercised by ``--smoke`` on real corpora,
which needs the frozen collections on disk and is therefore not a unit test.
"""

from __future__ import annotations

import json

import pytest

pytestmark = pytest.mark.unit

from experiments.tkde import matrices as mx
from experiments.tkde import rq4, rq5
from experiments.tkde.analyze_rq4 import evaluate_hypotheses as rq4_hypotheses
from experiments.tkde.analyze_rq5 import evaluate_hypotheses as rq5_hypotheses
from experiments.tkde.config import TkdeConfigError


class TestShardSplit:
    """The even split that keeps every bundled task the same size."""

    @pytest.mark.parametrize(
        ("n_units", "count"),
        [(1323, 3), (65, 1), (26, 4), (10, 10), (7, 3), (0, 2), (5, 7)],
    )
    def test_shards_partition_the_units_exactly(self, n_units: int, count: int) -> None:
        covered: list[int] = []
        for index in range(count):
            lo, hi = mx.shard_bounds(n_units, index, count)
            assert lo <= hi
            covered.extend(range(lo, hi))
        assert covered == list(range(n_units))

    @pytest.mark.parametrize(("n_units", "count"), [(1323, 3), (100, 7), (65, 4)])
    def test_shard_sizes_differ_by_at_most_one(self, n_units: int, count: int) -> None:
        sizes = [hi - lo for lo, hi in (mx.shard_bounds(n_units, i, count) for i in range(count))]
        assert max(sizes) - min(sizes) <= 1

    def test_rejects_bad_shard_specifications(self) -> None:
        with pytest.raises(TkdeConfigError):
            mx.shard_bounds(10, 0, 0)
        with pytest.raises(TkdeConfigError):
            mx.shard_bounds(10, 3, 3)
        with pytest.raises(TkdeConfigError):
            mx.parse_shard("1/2/3")
        with pytest.raises(TkdeConfigError):
            mx.parse_shard("a/b")

    def test_parse_shard_roundtrip(self) -> None:
        assert mx.parse_shard("2/3") == (2, 3)


class TestMatrixUnits:
    """The matrices job's unit decode."""

    def test_default_specs_cover_the_frozen_arms(self) -> None:
        units = mx.enumerate_units(mx.DEFAULT_SPECS)
        assert len(units) == 26
        assert ("wd50k66", "fact_rank_roles") in units
        # Roles exist only in WD50K, so the roles arm must not be asked of NDC.
        assert ("ndc_classes", "fact_rank_roles") not in units
        assert units == list(dict.fromkeys(units)), "unit list must be duplicate-free"

    def test_build_specs_requires_name_and_arms(self) -> None:
        with pytest.raises(TkdeConfigError):
            mx.build_specs({"collections": [{"name": "wd50k66"}]}, smoke=False)


class TestStrictCacheReader:
    """A missing or mis-ordered matrix must raise, never recompute."""

    def test_missing_matrix_raises(self, tmp_path) -> None:
        with pytest.raises(mx.MatrixCacheMissingError, match="no cached matrix"):
            mx.load_cached_matrix(tmp_path, "wd50k66", "fact_rank", ["a", "b"])

    def test_member_order_mismatch_raises(self, tmp_path) -> None:
        numpy = pytest.importorskip("numpy")
        cache_dir = mx.collection_cache_dir(tmp_path, "wd50k66")
        cache_dir.mkdir(parents=True)
        matrix_path, manifest_path = mx.cache_paths(cache_dir, "fact_rank")
        with matrix_path.open("wb") as handle:
            numpy.save(handle, numpy.zeros((2, 2), dtype=numpy.float32))
        manifest_path.write_text(
            json.dumps({"n": 2, "member_order_sha1": "deadbeef", "arm": "fact_rank"})
        )
        # Same size, different order: the submatrix indices of every consumer
        # would be meaningless, so this must not be served.
        with pytest.raises(mx.MatrixCacheMissingError, match="member order mismatch"):
            mx.load_cached_matrix(tmp_path, "wd50k66", "fact_rank", ["a", "b"])

    def test_matching_order_is_served(self, tmp_path) -> None:
        numpy = pytest.importorskip("numpy")
        from isalhg.metric_space.toolkit.matrix import member_order_sha1

        ids = ["a", "b", "c"]
        cache_dir = mx.collection_cache_dir(tmp_path, "ndc_classes")
        cache_dir.mkdir(parents=True)
        matrix_path, manifest_path = mx.cache_paths(cache_dir, "size_l1")
        with matrix_path.open("wb") as handle:
            numpy.save(handle, numpy.zeros((3, 3), dtype=numpy.float32))
        manifest_path.write_text(
            json.dumps({"n": 3, "member_order_sha1": member_order_sha1(ids), "arm": "size_l1"})
        )
        loaded = mx.load_cached_matrix(tmp_path, "ndc_classes", "size_l1", ids)
        assert loaded.shape == (3, 3)
        assert mx.cached_arms(tmp_path, "ndc_classes", ids) == ("size_l1",)


class TestRq4Units:
    """RQ4's seed-major decode -- the property the bundling relies on."""

    def _units(self) -> list[rq4.Unit]:
        subs = [
            rq4.SubCollection("ndc_classes", "ndc_classes", None, 0),
            rq4.SubCollection("wd50k66_Q5", "wd50k66", "Q5", 47),
            rq4.SubCollection("wd50k66_Q11424", "wd50k66", "Q11424", 47),
        ]
        return rq4.enumerate_units(subs, list(rq4.DEFAULT_CORRUPTIONS), 4)

    def test_unit_count_is_the_product(self) -> None:
        assert len(self._units()) == 4 * 3 * 7

    def test_units_are_seed_major(self) -> None:
        units = self._units()
        block = 3 * 7
        for start in range(0, len(units), block):
            chunk = units[start : start + block]
            assert len({u.seed for u in chunk}) == 1, "a block must be one seed"
            names = [u.experiment.sub.name for u in chunk]
            # Every sub-collection appears equally often in every block, which
            # is what makes an even split give equal-cost tasks.
            assert len(set(names)) == 3
            assert all(names.count(n) == 7 for n in set(names))

    def test_unit_ids_are_unique_and_stable(self) -> None:
        units = self._units()
        ids = [u.unit_id for u in units]
        assert len(set(ids)) == len(ids)
        assert self._units()[5].unit_id == units[5].unit_id

    def test_default_corruptions_match_the_design(self) -> None:
        kinds = {k for k, _ in rq4.DEFAULT_CORRUPTIONS}
        assert kinds == {"spurious_fact", "missing_fact", "wrong_argument", "iso_twin"}
        assert sum(1 for k, _ in rq4.DEFAULT_CORRUPTIONS if k == "iso_twin") == 1
        assert len(rq4.DEFAULT_CORRUPTIONS) == 7

    def test_floors_and_exact_arms_are_in_the_arm_list(self) -> None:
        for arm in rq4.FLOOR_ARMS + rq4.EXACT_ARMS:
            assert arm in rq4.DEFAULT_ARMS


class TestRq5Units:
    """RQ5 splits the full design by arm and a balanced design by seed."""

    def _experiments(self) -> list[rq5.Experiment]:
        return [
            rq5.Experiment("full", "wd50k66", "full", ("fact_rank", "size_l1"), 20, 20, 4),
            rq5.Experiment("bal", "wd50k66", "balanced", ("fact_rank", "size_l1"), 20, 20, 4),
        ]

    def test_unit_split_matches_where_the_cost_is(self) -> None:
        units = rq5.enumerate_units(self._experiments())
        assert len(units) == 2 + 4
        assert [u.arm for u in units[:2]] == ["fact_rank", "size_l1"]
        assert all(u.arm is None and u.seed is not None for u in units[2:])

    def test_eligible_classes_are_ordered_by_support(self) -> None:
        labels = ["a"] * 30 + ["b"] * 25 + ["c"] * 5 + [None] * 3
        assert rq5.eligible_classes(labels, 20) == ["a", "b"]
        assert rq5.eligible_classes(labels, 5) == ["a", "b", "c"]
        assert rq5.eligible_classes(labels, 100) == []

    def test_balanced_selection_is_seeded_and_stratified(self) -> None:
        labels = ["a"] * 30 + ["b"] * 25
        experiment = self._experiments()[1]
        first = rq5._select_indices(experiment, labels, ["a", "b"], 7)
        again = rq5._select_indices(experiment, labels, ["a", "b"], 7)
        other = rq5._select_indices(experiment, labels, ["a", "b"], 8)
        assert first == again, "the same seed must give the same sample"
        assert first != other
        assert len(first) == 40
        assert sum(1 for i in first if labels[i] == "a") == 20

    def test_pam_cost_prefers_a_tighter_partition(self) -> None:
        numpy = pytest.importorskip("numpy")
        D = numpy.array(
            [[0.0, 1.0, 9.0, 9.0], [1.0, 0.0, 9.0, 9.0], [9.0, 9.0, 0.0, 1.0], [9.0, 9.0, 1.0, 0.0]]
        )
        good = numpy.array([0, 0, 1, 1])
        bad = numpy.array([0, 1, 0, 1])
        assert rq5._pam_cost(D, good) < rq5._pam_cost(D, bad)

    def test_bootstrap_interval_contains_the_point_estimate(self) -> None:
        """Subsampling, not the ordinary bootstrap.

        Resampling members *with* replacement duplicates them, and a duplicate
        agrees with itself in both partitions, so every pair-counting index is
        biased upward -- measured badly enough that the interval excluded its
        own point estimate. This pins the remedy.
        """
        numpy = pytest.importorskip("numpy")
        from isalhg.metric_space.toolkit import ari

        rng = numpy.random.default_rng(0)
        truth = [f"c{i % 8}" for i in range(240)]
        predicted = numpy.array([int(t[1:]) for t in truth])
        # Perturb a fifth of the assignments so ARI is high but not degenerate.
        flip = rng.choice(240, size=48, replace=False)
        predicted[flip] = rng.integers(0, 8, size=48)

        point = ari(truth, list(predicted))
        low, high = rq5._bootstrap_ari(truth, predicted, seed=5, n_resamples=300)
        assert low <= point <= high, f"{point} outside [{low}, {high}]"


class TestHypothesisVerdicts:
    """A short sample must read as inconclusive, never as a negative result."""

    def test_rq5_is_inconclusive_below_the_seed_floor(self) -> None:
        pandas = pytest.importorskip("pandas")
        clustering = pandas.DataFrame({"seed": [1, 2], "design": ["balanced"] * 2})
        geometry = [
            {"arm": "fact_rank", "nu": 0.1, "n_negative_eigen": 1656, "hubness_skew_k10": 0.9}
        ]
        verdicts = rq5_hypotheses([], [], geometry, clustering)
        assert set(verdicts) == {"H5a", "H5b", "H5c", "H5d"}
        assert all(v["verdict"] == "inconclusive" for v in verdicts.values())

    def test_rq5_h5a_splits_the_nu_and_hubness_clauses(self) -> None:
        pandas = pytest.importorskip("pandas")
        clustering = pandas.DataFrame({"seed": list(range(27)), "design": ["balanced"] * 27})
        # The measured full-design profile: nu > 0 with a large negative
        # spectrum, but hubness far above the ceiling.
        geometry = [
            {"arm": "fact_rank", "nu": 0.1015, "n_negative_eigen": 1656, "hubness_skew_k10": 5.408}
        ]
        verdict = rq5_hypotheses([], [], geometry, clustering)["H5a"]
        assert verdict["verdict"] == "not_supported"
        assert verdict["nu_positive"] is True
        assert verdict["non_trivial_negative_spectrum"] is True
        assert verdict["hubness_moderate"] is False

    def test_rq4_is_inconclusive_below_the_seed_floor(self) -> None:
        summary = [
            {
                "subcollection": "ndc_classes",
                "corruption": "iso_twin",
                "budget": 1,
                "score": "knn",
                "arm": "fact_rank",
                "auc_mean": 0.76,
                "auc_low": 0.7,
                "auc_high": 0.8,
                "above_chance": True,
                "is_exact": True,
                "is_floor": False,
            }
        ]
        verdicts = rq4_hypotheses(summary, [], n_seeds=2)
        assert verdicts["H4a"]["verdict"] == "inconclusive"

    def test_rq4_h4a_reads_the_exactness_split(self) -> None:
        def row(arm: str, auc: float, exact: bool, above: bool) -> dict:
            return {
                "subcollection": "ndc_classes",
                "corruption": "iso_twin",
                "budget": 1,
                "score": "knn",
                "arm": arm,
                "auc_mean": auc,
                "auc_low": auc - 0.02,
                "auc_high": auc + 0.02,
                "above_chance": above,
                "is_exact": exact,
                "is_floor": not exact,
            }

        summary = [
            row("fact_rank", 0.76, True, True),
            row("nauty_cert", 0.72, True, True),
            row("size_l1", 0.51, False, False),
            row("degree_seq_l1", 0.50, False, False),
        ]
        verdict = rq4_hypotheses(summary, [], n_seeds=27)["H4a"]
        assert verdict["verdict"] == "supported"
        assert verdict["n_exact_above_chance"] == 2
        assert verdict["n_incomplete_above_chance"] == 0
        assert verdict["exact_mean_auc"] > verdict["incomplete_mean_auc"]


class TestSmokeIsolation:
    """Smoke output must never be mistaken for campaign output.

    A cluster smoke task runs a REAL unit under the REAL config, so its rows
    carry the same unit id the full run uses and are shaped exactly like the
    campaign's. Written into the real folder they would make the idempotent
    full run skip that unit and ship the smoke's output as the result -- a
    complete, plausible, wrong result set with nothing to flag it.
    """

    def test_smoke_component_is_detected_anywhere_in_the_path(self) -> None:
        assert mx.contains_smoke("/r/RQ4_screen/_smoke/rows/rows_auc__x.csv")
        assert mx.contains_smoke("_smoke/rows_auc__x.csv")
        assert mx.contains_smoke("/r/matrices/_smoke/wd50k66/fact_rank.npy")
        assert not mx.contains_smoke("/r/RQ4_screen/rows/rows_auc__x.csv")
        # A substring is not a component: a peer's folder may legitimately be
        # named "_smoke_rq3" without being smoke output of ours to exclude.
        assert not mx.contains_smoke("/r/_smoke_rq3/rows/rows_auc__x.csv")

    def test_smoke_matrices_cache_is_a_separate_directory(self) -> None:
        real = mx.collection_cache_dir("/r", "wd50k66")
        smoke = mx.collection_cache_dir("/r", "wd50k66", smoke=True)
        assert real != smoke
        assert not mx.contains_smoke(real)
        assert mx.contains_smoke(smoke)
        assert smoke.name == "wd50k66"

    def test_analyzers_exclude_smoke_rows_and_keep_real_ones(self, tmp_path) -> None:
        pytest.importorskip("pandas")
        from experiments.tkde.analyze_rq4 import _read as read_rq4

        real_dir = tmp_path / "RQ4_screen" / "rows"
        smoke_dir = tmp_path / "RQ4_screen" / "_smoke" / "rows"
        real_dir.mkdir(parents=True)
        smoke_dir.mkdir(parents=True)
        header = (
            "rq,experiment,collection,seed,arm,secs,censored,subcollection,"
            "corruption,budget,score,auc,n_inliers,n_anomalies,n_skipped\n"
        )
        row = "RQ4,e,ndc_classes,{seed},fact_rank,1.0,0,ndc_classes,iso_twin,1,knn,{auc},10,1,0\n"
        (real_dir / "rows_auc__e__seed40000.csv").write_text(
            header + row.format(seed=40000, auc=0.9)
        )
        # The same unit id with a different value -- exactly the collision.
        (smoke_dir / "rows_auc__e__seed40000.csv").write_text(
            header + row.format(seed=40000, auc=0.1)
        )

        frame = read_rq4(tmp_path, "auc")
        assert len(frame) == 1, "the smoke row must not be concatenated"
        assert float(frame["auc"].iloc[0]) == 0.9

    def test_deploy_stamps_name_both_trees(self) -> None:
        stamps = mx.deploy_stamps()
        # Both keys are always present, so a manifest never silently describes
        # half of what ran: `isalhg.*` comes from the shared checkout via the
        # editable finder, `experiments.*` from the agent's own deployment.
        assert set(stamps) == {"src_deploy", "runner_deploy"}


class TestMatricesRootIsSeparable:
    """The matrix cache is read from a root the task never writes to.

    On Picasso ``--out`` is the node-local staging tree that
    ``tkde_stage_localscratch`` creates EMPTY, while the matrices job wrote its
    26 ``.npy`` files once, on another node, to the shared HOME results root.
    A runner that reads the cache under ``--out`` therefore finds nothing and
    raises on its first unit; a local run never shows it, because there the two
    roots coincide.
    """

    def test_read_root_and_write_root_are_independent(self, tmp_path) -> None:
        numpy = pytest.importorskip("numpy")
        from isalhg.metric_space.toolkit.matrix import member_order_sha1

        ids = ["a", "b"]
        read_root = tmp_path / "home_results"
        write_root = tmp_path / "node_scratch"
        write_root.mkdir()
        cache_dir = mx.collection_cache_dir(read_root, "ndc_classes")
        cache_dir.mkdir(parents=True)
        matrix_path, manifest_path = mx.cache_paths(cache_dir, "size_l1")
        with matrix_path.open("wb") as handle:
            numpy.save(handle, numpy.zeros((2, 2), dtype=numpy.float32))
        manifest_path.write_text(
            json.dumps({"n": 2, "member_order_sha1": member_order_sha1(ids), "arm": "size_l1"})
        )

        assert mx.load_cached_matrix(read_root, "ndc_classes", "size_l1", ids).shape == (2, 2)
        with pytest.raises(mx.MatrixCacheMissingError):
            mx.load_cached_matrix(write_root, "ndc_classes", "size_l1", ids)

    @pytest.mark.parametrize("module", [rq4, rq5])
    def test_runners_take_a_matrices_root(self, module) -> None:
        import inspect

        for name in ("run_unit", "ensure_smoke_matrices"):
            params = inspect.signature(getattr(module, name)).parameters
            assert "matrices_root" in params, f"{module.__name__}.{name}"
            assert "out_root" not in params, f"{module.__name__}.{name} still reads under --out"

    @pytest.mark.parametrize("rq", ["rq4", "rq5"])
    def test_workers_pass_the_shared_results_root(self, rq) -> None:
        from pathlib import Path

        worker = Path(__file__).resolve().parents[2] / "slurm" / "tkde" / f"{rq}_worker.sh"
        text = worker.read_text(encoding="utf-8")
        # Both the smoke branch and the shard branch must read the shared root.
        assert text.count('--matrices-root "${ISALHG_RESULTS_ROOT}"') == 2, rq
        # The payload runs in the background so the copy-back traps can fire.
        assert text.count('tkde_run_synced "${PY}"') == 2, rq


class TestArmFailureIsCensoredNotFatal:
    """A competitor that raises on one corrupted record censors its arm.

    Measured on job 2215163: ``_hpd_vendor.hyperedge_portrait`` raises
    IndexError on some corrupted NDC records, the exception crossed back out of
    ``imap_unordered``, and all three RQ4 tasks died five minutes in, losing
    every unit they had already completed.
    """

    def test_score_matrix_returns_none_when_a_row_is_missing(self) -> None:
        numpy = pytest.importorskip("numpy")

        base = numpy.zeros((3, 3), dtype=float)
        rows = {(0, "hpd_jsd"): [0.0, 1.0, 2.0]}
        assert rq4._score_matrix(base, rows, [0], "hpd_jsd") is not None
        # Position 1 has no row for this arm: substituting the pristine member's
        # cached row would score a collection the anomaly was never injected in.
        assert rq4._score_matrix(base, rows, [0, 1], "hpd_jsd") is None

    def test_row_worker_returns_none_instead_of_raising(self, monkeypatch) -> None:
        class _Exploding:
            def pairwise(self, a, b):  # noqa: ANN001, ANN202
                raise IndexError("index 1 is out of bounds for axis 0 with size 1")

        monkeypatch.setitem(rq4._POOL_STATE, "items", ["h0", "h1"])
        monkeypatch.setitem(rq4._POOL_STATE, "distances", {"hpd_jsd": _Exploding()})
        position, arm, row = rq4._row_worker((0, "hpd_jsd"))
        assert (position, arm) == (0, "hpd_jsd")
        assert row is None
