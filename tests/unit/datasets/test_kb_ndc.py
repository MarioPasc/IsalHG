"""NDC quarterly derivation: the windowing machinery, then the real-data census."""

from __future__ import annotations

import pytest

from isalhg.datasets.kb.base import KBCorpusError
from isalhg.datasets.kb.ndc_quarterly import (
    CLASS_TYPE_ID,
    WINDOW_STEPS_MS,
    _canonical_simplices,
    _class_type_id,
    _group_windows,
    load_ndc,
    quarter_label,
)
from isalhg.datasets.kb.wd50k import data_root

pytestmark = pytest.mark.unit

_NDC = data_root() / "arb_benson" / "temporal" / "NDC-classes" / "NDC-classes-nverts.txt"
needs_data = pytest.mark.skipif(
    not _NDC.is_file(), reason=f"ARB temporal data root {data_root()} is not available"
)


class TestWindowing:
    def test_canonical_simplices_deduplicate_by_member_set(self) -> None:
        canonical, per_simplex = _canonical_simplices([2, 2, 3], [1, 2, 2, 1, 1, 2, 3])
        assert canonical == [(1, 2), (1, 2, 3)]
        assert per_simplex == [0, 0, 1]

    def test_groups_collect_distinct_simplices_per_node_and_window(self) -> None:
        canonical = [(1, 2), (2, 3)]
        per_simplex = [0, 1, 0]
        step = WINDOW_STEPS_MS["quarter"]
        times = [0, 0, step]
        groups = _group_windows(canonical, per_simplex, times, step)
        assert groups[(1, 0)] == frozenset({0})
        assert groups[(2, 0)] == frozenset({0, 1})
        assert groups[(1, 1)] == frozenset({0})

    def test_class_type_comes_from_the_name_suffix(self) -> None:
        assert _class_type_id("beta blocker [epc]") == CLASS_TYPE_ID["[epc]"]
        assert _class_type_id("something [moa] ") == CLASS_TYPE_ID["[moa]"]
        assert _class_type_id("x [pe]") == CLASS_TYPE_ID["[pe]"]
        assert _class_type_id("plain name") == CLASS_TYPE_ID["untyped"]

    def test_quarter_label_of_a_known_instant(self) -> None:
        # 2000-01-01 is 730,485 days after 0000-01-01 in the proleptic calendar.
        assert quarter_label(730_485 * 86_400_000) == "2000Q1"
        assert quarter_label((730_485 + 200) * 86_400_000) == "2000Q3"

    def test_unknown_arguments_raise(self) -> None:
        with pytest.raises(KBCorpusError, match="unknown NDC node set"):
            load_ndc("proteins")
        with pytest.raises(KBCorpusError, match="unknown window"):
            load_ndc("classes", window="fortnight")


@needs_data
class TestRealClasses:
    @pytest.fixture(scope="class")
    def collection(self):
        return load_ndc("classes")

    def test_grouping_reproduces_the_supplement_before_the_arity_two_rule(self, collection) -> None:
        meta = collection.meta
        assert meta["n_simplices"] == 49724
        # 1,432 encodable members in the supplement, which counted
        # singleton-product simplices as facts; the alphabet's F token has
        # arity >= 2, so those cannot be encoded and are not counted.
        assert meta["n_encodable_counting_singleton_products"] == 1432
        assert len(collection) == 1381

    def test_pairs_carry_exact_deltas_and_the_regime_flag(self, collection) -> None:
        meta = collection.meta
        pairs = meta["consecutive_pairs"]
        assert len(pairs) == meta["n_consecutive_pairs"] == 528
        assert meta["n_pairs_constant_preserving"] == 128
        assert meta["n_pairs_constant_changing"] == 400
        assert meta["n_pairs_constant_preserving"] + meta["n_pairs_constant_changing"] == len(pairs)
        assert meta["delta_histogram"] == {"0": 77, "1": 117, "2": 129, "3-5": 180, ">5": 25}
        index = collection.index()
        for pair in pairs:
            assert pair["a"] in index and pair["b"] in index
            assert pair["delta"] >= 0
            assert isinstance(pair["constant_preserving"], bool)

    def test_delta_zero_pairs_have_equal_fact_sets_in_the_identity_space(self, collection) -> None:
        by_id = {r.kb_id: r for r in collection.records}
        zero = [p for p in collection.meta["consecutive_pairs"] if p["delta"] == 0][:20]
        assert zero
        for pair in zero:
            a, b = by_id[pair["a"]], by_id[pair["b"]]
            assert a.m == b.m
            assert pair["constant_preserving"] is True

    def test_runs_are_reported(self, collection) -> None:
        meta = collection.meta
        assert meta["n_classes_run_ge3"] == 42
        assert meta["n_classes_run_ge5"] == 19
        assert all(len(run["kb_ids"]) >= 1 for run in meta["consecutive_runs"])

    def test_series_census_carries_the_rq3_sizing_numbers(self, collection) -> None:
        series = collection.census()["series"]
        assert series["n_consecutive_pairs"] == 528
        assert series["delta_histogram"] == {"0": 77, "1": 117, "2": 129, "3-5": 180, ">5": 25}
        assert series["n_pairs_constant_preserving"] == 128
        assert series["n_pairs_constant_changing"] == 400
        assert series["n_classes_run_ge3"] == 42
        assert series["n_classes_run_ge5"] == 19
        assert series["n_runs_ge3"] == 107
        assert series["n_runs_ge5"] == 46
        assert series["max_run"] == 36

    def test_constants_are_typed_by_the_fda_suffix(self, collection) -> None:
        assert collection.type_names == ("[epc]", "[moa]", "[pe]", "untyped")
        assert collection.pred_names == ("co_formulation",)
        assert sorted({t for r in collection.records for t in r.types}) == [0, 1, 2, 3]

    def test_members_are_connected_encodable_and_identity_carrying(self, collection) -> None:
        for record in collection.records[:300]:
            assert record.is_connected()
            assert record.m >= 3
            assert record.n <= 24
            assert 2 <= record.max_arity <= 10
            assert record.constant_ids is not None
            assert record.roles is None
            assert record.meta["quarter"].endswith(("Q1", "Q2", "Q3", "Q4"))


@needs_data
class TestRealSubstances:
    def test_control_reconciles_with_the_supplement(self) -> None:
        collection = load_ndc("substances")
        meta = collection.meta
        assert meta["n_encodable_counting_singleton_products"] == 2222
        assert len(collection) == 1745
        assert meta["n_consecutive_pairs"] == 885
        assert collection.type_names == ("untyped",)
        assert collection.census()["frac_facts_arity_ge3"] == pytest.approx(0.753, abs=0.002)
