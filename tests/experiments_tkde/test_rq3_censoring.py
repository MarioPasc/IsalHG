"""Unit tests for RQ3's collection-level censoring (D-KBf1).

An arm that cannot canonicalize every member of a collection reports **no**
medoid for that collection: Prop 3's ``LB <= OPT <= cost(M)`` certifies the ``N``
members, and over a survivor subset it certifies a different object while being
printed under a column headed "certified ratio". These tests pin that rule, the
supplement row that bounds its cost, and the per-(collection, method) granularity
of the census -- the medoid's censoring must not overwrite the consensus's.

The arm's screen is stubbed rather than run: the point under test is the
bookkeeping, and a real 60 s budget over the C++ engine is not a unit test.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest

from experiments.tkde import rq3

pytestmark = pytest.mark.unit

ARM = "wstar_orbit"
IDS: tuple[str, ...] = ("k0", "k1", "k2", "k3")


class _FakeRecord:
    """The slice of ``KBRecord`` the medoid path touches."""

    def __init__(self, kb_id: str, facts: frozenset[Any]) -> None:
        self.kb_id = kb_id
        self.facts = facts


def _facts(record: _FakeRecord) -> frozenset[Any]:
    return record.facts


@pytest.fixture
def members() -> list[_FakeRecord]:
    return [
        _FakeRecord(kb_id, frozenset({(index, frozenset({kb_id}))}))
        for index, kb_id in enumerate(IDS)
    ]


@pytest.fixture
def shared() -> dict[str, Any]:
    return {"collection_id": "c0", "N": len(IDS), "unit": "u0"}


@pytest.fixture
def patched(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stub the engine-facing helpers so the bookkeeping runs in milliseconds."""
    monkeypatch.setattr(rq3, "identity_facts_of_record", _facts)
    monkeypatch.setattr(
        rq3,
        "medoid_matrix",
        lambda members_H, member_ids, arm, budget_s: np.array(
            [[abs(i - j) for j in range(len(member_ids))] for i in range(len(member_ids))],
            dtype=np.float64,
        ),
    )


class TestCensoredMembers:
    def test_no_member_censored_when_the_screen_accepts_all(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(rq3, "arm_fingerprint_screen", lambda arm, secs: lambda H: True)
        assert rq3.censored_members(ARM, list(range(4)), IDS, 60.0) == ()

    def test_every_member_censored_when_the_screen_rejects_all(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(rq3, "arm_fingerprint_screen", lambda arm, secs: lambda H: False)
        assert rq3.censored_members(ARM, list(range(4)), IDS, 60.0) == IDS

    @pytest.mark.parametrize("rejected", [{"k0"}, {"k1", "k3"}, {"k0", "k1", "k2"}])
    def test_the_censored_ids_are_reported_in_member_order(
        self, monkeypatch: pytest.MonkeyPatch, rejected: set[str]
    ) -> None:
        order = {kb_id: index for index, kb_id in enumerate(IDS)}
        monkeypatch.setattr(
            rq3,
            "arm_fingerprint_screen",
            lambda arm, secs: lambda H: IDS[H] not in rejected,
        )
        got = rq3.censored_members(ARM, list(range(4)), IDS, 60.0)
        assert set(got) == rejected
        assert list(got) == sorted(got, key=lambda kb_id: order[kb_id])

    def test_the_budget_reaches_the_screen(self, monkeypatch: pytest.MonkeyPatch) -> None:
        seen: list[float] = []

        def factory(arm: str, secs: float) -> Any:
            seen.append(secs)
            return lambda H: True

        monkeypatch.setattr(rq3, "arm_fingerprint_screen", factory)
        rq3.censored_members(ARM, [0], ("k0",), 60.0)
        assert seen == [60.0]


class TestSurvivorMedoidRow:
    def test_it_is_a_supplement_with_no_certificate(
        self, patched: None, members: list[_FakeRecord], shared: dict[str, Any]
    ) -> None:
        row = rq3.survivor_medoid_row(
            arm=ARM,
            members=members,
            members_H=list(range(4)),
            member_ids=IDS,
            censored_ids=("k3",),
            truth_facts=members[1].facts,
            shared=shared,
            budget_s=60.0,
        )
        assert row is not None
        assert row["method"] == "medoid_survivors"
        assert row["LB"] == ""
        assert row["ratio"] == ""
        assert row["n_censored_members"] == 1
        assert row["N"] == len(IDS)

    @pytest.mark.parametrize("censored", [IDS, IDS[:3]])
    def test_fewer_than_two_survivors_yields_no_row(
        self,
        patched: None,
        members: list[_FakeRecord],
        shared: dict[str, Any],
        censored: tuple[str, ...],
    ) -> None:
        row = rq3.survivor_medoid_row(
            arm=ARM,
            members=members,
            members_H=list(range(4)),
            member_ids=IDS,
            censored_ids=censored,
            truth_facts=members[0].facts,
            shared=shared,
            budget_s=60.0,
        )
        assert row is None

    def test_a_failed_build_is_logged_not_raised(
        self,
        monkeypatch: pytest.MonkeyPatch,
        members: list[_FakeRecord],
        shared: dict[str, Any],
    ) -> None:
        monkeypatch.setattr(rq3, "identity_facts_of_record", _facts)

        def boom(*args: Any, **kwargs: Any) -> Any:
            raise rq3.RQ3Error("guarded build returned 'timeout'")

        monkeypatch.setattr(rq3, "medoid_matrix", boom)
        assert (
            rq3.survivor_medoid_row(
                arm=ARM,
                members=members,
                members_H=list(range(4)),
                member_ids=IDS,
                censored_ids=("k3",),
                truth_facts=members[0].facts,
                shared=shared,
                budget_s=60.0,
            )
            is None
        )


class TestMedoidMatrixProcessModel:
    def test_a_non_engine_arm_builds_in_process(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            rq3, "build_matrix", lambda items, arm, **kw: np.zeros((len(items), len(items)))
        )
        monkeypatch.setattr(
            rq3,
            "run_guarded",
            lambda *a, **k: pytest.fail("a non-engine arm must not fork"),
        )
        assert rq3.medoid_matrix([0, 1], ("k0", "k1"), "size_l1", 60.0).shape == (2, 2)

    def test_an_engine_arm_builds_in_a_child_and_declares_it(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        seen: dict[str, Any] = {}

        def fake_guarded(fn: Any, budget: float, *, cpp_engine: bool = False) -> Any:
            seen["budget"] = budget
            seen["cpp_engine"] = cpp_engine
            return ("ok", np.zeros((2, 2)))

        monkeypatch.setattr(rq3, "build_matrix", lambda items, arm, **kw: np.zeros((2, 2)))
        monkeypatch.setattr(rq3, "run_guarded", fake_guarded)
        rq3.medoid_matrix([0, 1], ("k0", "k1"), ARM, 60.0)
        assert seen["cpp_engine"] is True
        assert seen["budget"] == 2 * 60.0 + rq3.BUILD_MARGIN_S

    @pytest.mark.parametrize("status", ["timeout", "error"])
    def test_a_guarded_build_that_does_not_return_ok_raises(
        self, monkeypatch: pytest.MonkeyPatch, status: str
    ) -> None:
        monkeypatch.setattr(rq3, "build_matrix", lambda items, arm, **kw: np.zeros((2, 2)))
        monkeypatch.setattr(rq3, "run_guarded", lambda *a, **k: (status, None))
        with pytest.raises(rq3.RQ3Error):
            rq3.medoid_matrix([0, 1], ("k0", "k1"), ARM, 60.0)


class TestColumns:
    def test_both_row_schemas_carry_the_census(self) -> None:
        assert "n_censored_members" in rq3.VARIANT_COLUMNS
        assert "n_censored_members" in rq3.NATURAL_COLUMNS

    def test_the_certificate_schema_does_not(self) -> None:
        # A censored collection emits no certificate row at all, so the column
        # would be blank on every row it could reach.
        assert "n_censored_members" not in rq3.CERTIFICATE_COLUMNS

    def test_the_screened_arms_are_the_matrices_job_s(self) -> None:
        # D-KBf1: the same screen, so the same census the reader met in RQ1.
        assert ARM in rq3.BUDGETED_MATRIX_ARMS
        assert ARM in rq3.CPP_ENGINE_ARMS


class TestSmokeConfigForwarding:
    def test_the_smoke_budget_overrides_the_campaign_s(self) -> None:
        merged = rq3._apply_smoke(
            {
                "corpus_a": {},
                "corpus_b": {},
                "fingerprint_budget_s": 60.0,
                "smoke": {"fingerprint_budget_s": 5.0},
            }
        )
        assert merged["fingerprint_budget_s"] == 5.0

    def test_without_a_smoke_override_the_campaign_budget_survives(self) -> None:
        merged = rq3._apply_smoke(
            {"corpus_a": {}, "corpus_b": {}, "fingerprint_budget_s": 60.0, "smoke": {}}
        )
        assert merged["fingerprint_budget_s"] == 60.0
