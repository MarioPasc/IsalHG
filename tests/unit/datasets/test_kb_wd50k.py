"""WD50K derivation: the parser and the roles, then the real-data census.

The real-data tests are skipped when the data root is absent, so the suite runs
on a machine that has no copy of WD50K.
"""

from __future__ import annotations

import pytest

from isalhg.datasets.kb.base import KBCorpusError
from isalhg.datasets.kb.wd50k import (
    ROLE_OBJECT,
    ROLE_QUALIFIER,
    ROLE_SUBJECT,
    Statement,
    assign_labels,
    data_root,
    load_wd50k,
    parse_statements,
    read_p31_types,
)

pytestmark = pytest.mark.unit

DATA_PRESENT = (data_root() / "wd50k_66" / "train.txt").is_file()
TYPES_PRESENT = (data_root() / "wd50k" / "types" / "p31_types.tsv").is_file()
needs_data = pytest.mark.skipif(
    not (DATA_PRESENT and TYPES_PRESENT),
    reason=f"WD50K data root {data_root()} is not available",
)


class TestParser:
    def test_reads_subject_relation_object_and_qualifier_values(self, tmp_path) -> None:
        path = tmp_path / "train.txt"
        path.write_text("Q1,P1,Q2,P3,Q4,P5,Q6\nQ1,P2,Q3\n\n", encoding="utf-8")
        statements = list(parse_statements(path))
        assert len(statements) == 2
        assert statements[0].qual_values == ("Q4", "Q6")
        assert statements[0].vertices == frozenset({"Q1", "Q2", "Q4", "Q6"})
        assert statements[1].qual_values == ()

    def test_roles_are_subject_object_qualifier(self) -> None:
        statement = Statement("Q1", "P1", "Q2", ("Q3",))
        assert statement.role_of("Q1") == ROLE_SUBJECT
        assert statement.role_of("Q2") == ROLE_OBJECT
        assert statement.role_of("Q3") == ROLE_QUALIFIER

    def test_a_constant_in_two_roles_takes_the_smaller_id(self) -> None:
        statement = Statement("Q1", "P1", "Q1", ("Q1",))
        assert statement.role_of("Q1") == ROLE_SUBJECT

    def test_unknown_subset_raises(self) -> None:
        with pytest.raises(KBCorpusError, match="unknown WD50K subset"):
            load_wd50k("77")

    def test_missing_types_table_raises(self, tmp_path) -> None:
        with pytest.raises(KBCorpusError, match="P31 type table"):
            read_p31_types(tmp_path / "absent.tsv")


class TestLabelPolicy:
    def test_most_frequent_type_wins_ties_by_identifier(self) -> None:
        types = {"Q1": ["Q5", "Q9"], "Q2": ["Q9"], "Q3": ["Q9"], "Q4": ["Q7", "Q5"]}
        labels, population = assign_labels(["Q1", "Q2", "Q3", "Q4"], types)
        assert population["Q9"] == 3
        assert labels["Q1"] == "Q9"
        assert labels["Q4"] == "Q5"

    def test_tie_is_broken_by_numeric_identifier_order(self) -> None:
        types = {"A": ["Q90", "Q9"]}
        labels, _ = assign_labels(["A"], types)
        assert labels["A"] == "Q9"

    def test_entity_without_a_type_is_unlabelled(self) -> None:
        labels, _ = assign_labels(["A"], {"A": []})
        assert labels == {}


@needs_data
class TestRealCensus:
    @pytest.fixture(scope="class")
    def collection(self):
        return load_wd50k("66")

    def test_population_and_envelope_reconcile_with_the_supplement(self, collection) -> None:
        meta = collection.meta
        assert meta["n_entities_ge_min_statements"] == 4554
        assert meta["n_dropped_over_arity_cap"] == 14
        # 3,994 in the supplement, which applied no m >= 3 floor; the frozen
        # envelope does, and the six members it removes are the whole difference.
        assert len(collection) == 3988
        assert len(collection) + meta["n_dropped_below_m_min"] == 3994

    def test_sizes_and_arity_match_the_supplement(self, collection) -> None:
        census = collection.census()
        assert census["n"]["median"] == 8
        assert census["m"]["median"] == 5
        assert census["frac_facts_arity_ge3"] == pytest.approx(0.547, abs=0.002)
        assert census["n_records_with_arity_ge3"] == 3162

    def test_labels_match_the_supplement(self, collection) -> None:
        census = collection.census()
        assert census["n_labels_ge20"] == 14
        assert census["coverage_labels_ge20"] == pytest.approx(0.875, abs=0.002)
        assert census["label_counts"]["Q5"] == 1830
        assert census["label_counts"]["Q11424"] == 1092

    def test_records_are_connected_typed_and_role_carrying(self, collection) -> None:
        assert collection.type_names == ("untyped",)
        assert collection.role_names == ("S", "O", "Q")
        assert collection.has_roles
        for record in collection.records[:200]:
            assert record.is_connected()
            assert record.max_arity <= 10
            assert record.constant_ids is not None
            roles = record.roles_map()
            assert roles is not None
            assert set(roles) == set(range(record.m))
            for edge_id, (_, members) in enumerate(record.facts):
                assert set(roles[edge_id]) == set(members)

    def test_full_variant_keeps_every_entity(self) -> None:
        assert len(load_wd50k("66", envelope=False)) == 4554

    def test_purity_control(self) -> None:
        control = load_wd50k("100")
        assert len(control) == 1837
        assert len(control) + control.meta["n_dropped_below_m_min"] == 1847
        assert control.census()["frac_facts_arity_ge3"] == pytest.approx(0.998, abs=0.002)
