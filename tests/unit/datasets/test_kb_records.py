"""KBRecord / KBCollection contract and JSONL round-trip."""

from __future__ import annotations

import pytest

from isalhg.datasets.kb.base import (
    Envelope,
    KBCollection,
    KBCollectionError,
    KBRecord,
    KBRecordError,
    compact,
    is_connected,
    make_record,
)
from isalhg.datasets.kb.io import read_jsonl, write_jsonl

pytestmark = pytest.mark.unit


def triangle() -> KBRecord:
    """Three constants, three binary facts, two predicates, roles present."""
    return KBRecord(
        kb_id="tri",
        n=3,
        types=(0, 1, 0),
        facts=((0, (0, 1)), (1, (1, 2)), (0, (0, 2))),
        roles=((0, 1), (0, 2), (1, 2)),
        constant_ids=("Q1", "Q2", "Q3"),
        label="cls",
        meta={"quarter": "2015Q3", "nested": {"a": [1, 2]}},
    )


class TestStructure:
    def test_facts_are_sorted_with_their_roles(self) -> None:
        record = triangle()
        assert record.facts == ((0, (0, 1)), (0, (0, 2)), (1, (1, 2)))
        assert record.roles == ((0, 1), (1, 2), (0, 2))

    def test_derived_quantities(self) -> None:
        record = triangle()
        assert record.m == 3
        assert record.max_arity == 2
        assert record.arity_histogram() == {2: 3}
        assert record.degree_sequence() == (2, 2, 2)
        assert record.is_connected()

    @pytest.mark.parametrize(
        ("kwargs", "reason"),
        [
            ({"types": (0, 1)}, "types length"),
            ({"facts": ((0, (0,)),)}, "arity 1"),
            ({"facts": ((0, (0, 1)), (0, (1, 0)))}, "duplicate fact"),
            ({"facts": ((0, (0, 9)),)}, "constant out of range"),
            ({"constant_ids": ("Q1",)}, "identity length"),
            ({"roles": ((0, 1),)}, "roles row count"),
        ],
    )
    def test_rejects_malformed(self, kwargs: dict, reason: str) -> None:
        base = {
            "kb_id": "x",
            "n": 3,
            "types": (0, 0, 0),
            "facts": ((0, (0, 1)), (0, (1, 2))),
        }
        with pytest.raises(KBRecordError):
            KBRecord(**{**base, **kwargs})

    def test_roles_row_length_must_match_arity(self) -> None:
        with pytest.raises(KBRecordError):
            KBRecord(kb_id="x", n=2, types=(0, 0), facts=((0, (0, 1)),), roles=((0, 1, 2),))


class TestBridges:
    def test_to_hypergraph_preserves_fact_order_and_labels(self) -> None:
        record = triangle()
        collection = KBCollection(
            name="c",
            records=(record,),
            type_names=("a", "b"),
            pred_names=("p", "q"),
            role_names=("S", "O", "Q"),
            k_max=2,
        )
        H = collection.records[0].to_hypergraph()
        assert H.n_nodes == 3
        assert H.n_edges == 3
        assert H.n_vertex_labels == 2
        assert H.n_edge_labels == 2
        assert [H.edge_label(e) for e in range(H.n_edges)] == [0, 0, 1]
        assert [sorted(H.members(e)) for e in range(H.n_edges)] == [[0, 1], [0, 2], [1, 2]]

    def test_roles_map_shape(self) -> None:
        record = triangle()
        roles = record.roles_map()
        assert roles == {0: {0: 0, 1: 1}, 1: {0: 1, 2: 2}, 2: {1: 0, 2: 2}}

    def test_roles_map_is_none_without_roles(self) -> None:
        record = KBRecord(kb_id="x", n=2, types=(0, 0), facts=((0, (0, 1)),))
        assert record.roles_map() is None


class TestHelpers:
    def test_is_connected_rejects_isolated_constant(self) -> None:
        assert not is_connected(3, [(0, (0, 1))])
        assert is_connected(2, [(0, (0, 1))])

    def test_make_record_drops_duplicates_and_keeps_role_alignment(self) -> None:
        record = make_record(
            "x",
            3,
            [0, 0, 0],
            [(0, (0, 1)), (0, (1, 0)), (0, (1, 2))],
            roles=[(0, 1), (9, 9), (0, 1)],
        )
        assert record is not None
        assert record.facts == ((0, (0, 1)), (0, (1, 2)))
        assert record.roles == ((0, 1), (0, 1))

    def test_make_record_rejects_disconnected_when_required(self) -> None:
        assert make_record("x", 4, [0] * 4, [(0, (0, 1)), (0, (2, 3))]) is None
        assert (
            make_record("x", 4, [0] * 4, [(0, (0, 1)), (0, (2, 3))], require_connected=False)
            is not None
        )

    def test_compact_drops_unused_constants_and_carries_identities(self) -> None:
        record = compact("x", [7, 8, 9], [(0, (0, 2))], constant_ids=["A", "B", "C"])
        assert record is not None
        assert record.n == 2
        assert record.types == (7, 9)
        assert record.constant_ids == ("A", "C")
        assert record.facts == ((0, (0, 1)),)


class TestEnvelope:
    def test_admits(self) -> None:
        env = Envelope(n_max=24, m_min=3, m_max=110, k_max=10)
        assert env.admits(24, 3, 10)
        assert not env.admits(25, 3, 10)
        assert not env.admits(24, 2, 10)
        assert not env.admits(24, 111, 10)
        assert not env.admits(24, 3, 11)


class TestCollection:
    def test_stamps_vocabulary_sizes(self) -> None:
        collection = KBCollection(
            name="c", records=(triangle(),), type_names=("a", "b"), pred_names=("p", "q")
        )
        assert collection.records[0].n_types == 2
        assert collection.records[0].n_preds == 2

    def test_rejects_duplicate_ids(self) -> None:
        with pytest.raises(KBCollectionError):
            KBCollection(
                name="c",
                records=(triangle(), triangle()),
                type_names=("a", "b"),
                pred_names=("p", "q"),
            )

    def test_rejects_label_outside_vocabulary(self) -> None:
        with pytest.raises(KBCollectionError):
            KBCollection(name="c", records=(triangle(),), type_names=("a",), pred_names=("p", "q"))

    def test_census_counts(self) -> None:
        census = KBCollection(
            name="c", records=(triangle(),), type_names=("a", "b"), pred_names=("p", "q")
        ).census()
        assert census["n_records"] == 1
        assert census["arity_histogram"] == {"2": 3}
        assert census["frac_facts_arity_ge3"] == 0.0
        assert census["label_counts"] == {"cls": 1}
        assert census["series"] == {}

    def test_series_census_is_reported_for_a_time_series(self) -> None:
        collection = KBCollection(
            name="c",
            records=(triangle(),),
            type_names=("a", "b"),
            pred_names=("p", "q"),
            meta={
                "consecutive_pairs": [{"a": "tri", "b": "tri2", "delta": 1}],
                "n_consecutive_pairs": 1,
                "delta_histogram": {"0": 0, "1": 1, "2": 0, "3-5": 0, ">5": 0},
                "n_pairs_constant_preserving": 1,
                "n_pairs_constant_changing": 0,
                "n_classes_run_ge3": 0,
                "n_classes_run_ge5": 0,
                "max_run": 2,
                "runs": {"7": ["tri", "tri2"]},
                "consecutive_runs": [{"class_id": 7, "kb_ids": ["tri", "tri2"]}],
            },
        )
        series = collection.census()["series"]
        assert series["n_consecutive_pairs"] == 1
        assert series["delta_histogram"]["1"] == 1
        assert series["n_runs_ge3"] == 0
        assert series["n_classes_with_any_member"] == 1


class TestRoundTrip:
    def _collection(self) -> KBCollection:
        plain = KBRecord(
            kb_id="plain",
            n=3,
            types=(0, 0, 1),
            facts=((1, (0, 1, 2)),),
        )
        return KBCollection(
            name="round",
            records=(triangle(), plain),
            type_names=("a", "b"),
            pred_names=("p", "q"),
            role_names=("S", "O", "Q"),
            k_max=3,
            meta={"consecutive_pairs": [{"a": "tri", "b": "plain", "delta": 2}]},
        )

    def test_write_then_read_is_equal(self, tmp_path) -> None:
        original = self._collection()
        directory = write_jsonl(original, tmp_path / "round")
        assert (directory / "records.jsonl").is_file()
        assert (directory / "vocab.json").is_file()
        assert (directory / "census.json").is_file()
        assert read_jsonl(directory) == original

    def test_round_trip_preserves_every_field(self, tmp_path) -> None:
        loaded = read_jsonl(write_jsonl(self._collection(), tmp_path / "r2"))
        record = loaded.records[0]
        assert record.kb_id == "tri"
        assert record.roles == ((0, 1), (1, 2), (0, 2))
        assert record.constant_ids == ("Q1", "Q2", "Q3")
        assert record.label == "cls"
        assert record.meta["quarter"] == "2015Q3"
        assert record.meta["nested"] == {"a": [1, 2]}
        assert loaded.records[1].roles is None
        assert loaded.meta["consecutive_pairs"][0]["delta"] == 2

    def test_registry_dataset_yields_hypergraphs(self, tmp_path) -> None:
        from isalhg.datasets.registry import get_dataset

        directory = write_jsonl(self._collection(), tmp_path / "r3")
        dataset = get_dataset("kb_collection", {"directory": str(directory)})
        items = list(dataset)
        assert len(items) == len(dataset) == 2
        assert items[0].item_id == "tri"
        assert items[0].hypergraph.n_edges == 3
        assert dataset.metadata.n_items == 2
