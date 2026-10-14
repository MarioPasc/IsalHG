"""RQ4's word fast path: the values it serves, and the members it loses.

Two claims are pinned here.

**Equality.** Every :data:`experiments.tkde.rq4.WORD_ARMS` arm is served from
one word per member and a single ``rapidfuzz`` pass instead of from
``HypergraphDistance.pairwise``, which re-derives the canonical labelling on
both sides of every call. The saving is the whole point -- ``2 N``
canonicalizations per anomaly row become ``N + 1`` -- but it is only admissible
if the numbers are the same ones, so the reference matrix is computed through
``pairwise`` itself and compared entry by entry. It is computed inside a forked
child, because a ``pairwise`` call on an Isal engine arm canonicalizes in this
process and a later budgeted fork would then deadlock on the extension
(``budget.cpp_fork_is_healthy``).

**Censoring.** The corpus members were screened once by the matrices job, but an
anomaly is a hypergraph that job never saw. One whose word does not finish
inside the per-member budget is dropped from the unit and counted in the
``n_censored_word_*`` columns (L15); it is never scored, and never silently
given a zero row. When every anomaly of a unit is lost the unit reports no AUC.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from experiments.tkde import rq4
from experiments.tkde.budget import CPP_ENGINE_ARMS, cpp_fork_is_healthy, guarded_budget_call
from experiments.tkde.matrices import censoring_path, collection_cache_dir
from isalhg.datasets.kb.base import KBCollection, make_record
from isalhg.metric_space.toolkit.matrix import cache_paths, member_order_sha1

pytestmark = pytest.mark.unit

COLLECTION = "toy"
LABELS = ("Q5", "Q11424")
BUDGET_S = 120.0

#: Enough members for the contamination rate to select two anomalies
#: (``max(1, round(0.05 N))``), so "one anomaly censored" and "every anomaly
#: censored" are distinguishable outcomes rather than the same one.
N_MEMBERS = 40

#: Facts per pristine member. A ``spurious_fact`` corruption adds exactly one,
#: which is how the stubbed word oracle below recognises an anomaly without
#: needing the member id the hypergraph does not carry.
BASE_FACTS = 3


def _record(index: int, n_facts: int = BASE_FACTS) -> Any:
    """A small connected record; ``index`` varies the shape, not only the ids."""
    facts = [(index % 2, (arg, arg + 1)) for arg in range(n_facts)]
    record = make_record(
        f"m{index:02d}",
        n_facts + 1,
        tuple((c + index) % 2 for c in range(n_facts + 1)),
        tuple(facts),
        constant_ids=tuple(f"m{index:02d}c{c}" for c in range(n_facts + 1)),
        label=LABELS[index % len(LABELS)],
        meta={"n_types": 2, "n_preds": 2},
    )
    assert record is not None
    return record


@pytest.fixture
def collection() -> KBCollection:
    """A synthetic collection of connected, structurally varied members."""
    return KBCollection(
        name=COLLECTION,
        records=tuple(_record(index) for index in range(N_MEMBERS)),
        type_names=("t0", "t1"),
        pred_names=("p0", "p1"),
    )


#: Structurally distinct shapes, so the equality check compares words that
#: actually differ -- a corpus of near-identical members would pass on
#: near-zero distances and prove nothing.
SHAPES: tuple[tuple[int, tuple[tuple[int, tuple[int, ...]], ...]], ...] = (
    (4, ((0, (0, 1)), (0, (1, 2)), (0, (2, 3)))),  # path
    (4, ((0, (0, 1)), (0, (0, 2)), (0, (0, 3)))),  # star
    (4, ((0, (0, 1, 2)), (1, (2, 3)))),  # one arity-3 fact
    (5, ((0, (0, 1)), (1, (1, 2)), (0, (2, 3)), (1, (3, 4)))),  # alternating path
    (4, ((0, (0, 1, 2, 3)),)),  # a single arity-4 fact
    (5, ((0, (0, 1, 2)), (0, (2, 3, 4)))),  # two arity-3 facts
)


def _shaped(index: int) -> Any:
    """The ``index``-th member of :data:`SHAPES`, typed so labels vary too."""
    n, facts = SHAPES[index]
    record = make_record(
        f"s{index:02d}",
        n,
        tuple((c + index) % 2 for c in range(n)),
        facts,
        constant_ids=tuple(f"s{index:02d}c{c}" for c in range(n)),
        label=LABELS[index % len(LABELS)],
        meta={"n_types": 2, "n_preds": 2},
    )
    assert record is not None
    return record


def _pairwise_matrix(arm: str, items: list[Any]) -> list[list[float]]:
    """The reference: ``pairwise`` on every ordered pair. Runs in a fork child."""
    from isalhg.metric_space.registry import get_distance

    distance = get_distance(arm)
    return [[float(distance.pairwise(a, b)) for b in items] for a in items]


class TestWordPathEqualsPairwise:
    """The fast path must return exactly what ``pairwise`` would have returned."""

    @staticmethod
    def _items(count: int) -> list[Any]:
        return [_shaped(index).to_hypergraph() for index in range(count)]

    @pytest.mark.parametrize("arm", ["fact_rank", "isal_ow_struct", "wstar_orbit"])
    def test_word_rows_match_pairwise(self, arm: str) -> None:
        if arm in CPP_ENGINE_ARMS and not cpp_fork_is_healthy():
            pytest.skip("the C++ canonicalizer already ran in this process; forks deadlock")
        items = self._items(len(SHAPES))
        augment = any(H.n_vertex_labels > 1 for H in items)

        words = [rq4.member_word(arm, H, augment=augment, budget_s=BUDGET_S) for H in items]
        assert all(word is not None for word in words)
        rows = rq4.word_rows(words, list(range(len(items))), n_jobs=1)

        reference = guarded_budget_call(
            _pairwise_matrix, (arm, items), BUDGET_S, cpp_engine=arm in CPP_ENGINE_ARMS
        )
        assert reference.ok, reference.error
        # The corpus must be far from degenerate, or equality proves nothing.
        off_diagonal = [rows[i][j] for i in range(len(items)) for j in range(len(items)) if i != j]
        assert min(off_diagonal) > 0.0
        for i, row in enumerate(rows):
            for j, value in enumerate(row):
                assert value == pytest.approx(reference.value[i][j]), (arm, i, j)

    @pytest.mark.parametrize("arm", ["fact_rank", "isal_ow_struct"])
    def test_identical_members_are_at_distance_zero(self, arm: str) -> None:
        items = self._items(3)
        words = [rq4.member_word(arm, H, augment=False, budget_s=BUDGET_S) for H in items]
        rows = rq4.word_rows(words, list(range(len(items))), n_jobs=1)
        for index, row in enumerate(rows):
            assert row[index] == pytest.approx(0.0)

    @pytest.mark.parametrize("n_items", [1, 2])
    def test_degenerate_populations(self, n_items: int) -> None:
        items = self._items(n_items)
        words = [rq4.member_word("fact_rank", H, augment=False, budget_s=BUDGET_S) for H in items]
        rows = rq4.word_rows(words, [0], n_jobs=1)
        assert len(rows) == 1
        assert len(rows[0]) == n_items


class TestUnitWords:
    """The per-member memo, and how a hole is reported."""

    def test_pristine_words_are_computed_once_per_subcollection(
        self, collection: KBCollection
    ) -> None:
        seen: list[int] = []

        def fake(arm: str, H: Any, *, augment: bool, budget_s: float) -> tuple[Any, ...]:
            seen.append(id(H))
            return ("w", H.n_edges)

        items = [record.to_hypergraph() for record in collection.records[:5]]
        ids = [record.kb_id for record in collection.records[:5]]
        cache: dict[str, Any] = {}
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(rq4, "member_word", fake)
            first, lost, arms = rq4.unit_words(
                ["fact_rank"], items, ids, [], budget_s=1.0, cache=cache, cache_scope="sub"
            )
            assert not lost and not arms
            n_first = len(seen)
            second, _, _ = rq4.unit_words(
                ["fact_rank"], items, ids, [], budget_s=1.0, cache=cache, cache_scope="sub"
            )
        assert n_first == 5
        # The second unit reuses the memo: no member is encoded twice.
        assert len(seen) == 5
        assert first == second

    def test_a_hole_is_reported_not_hidden(self, collection: KBCollection) -> None:
        def fake(arm: str, H: Any, *, augment: bool, budget_s: float) -> tuple[Any, ...] | None:
            return None if H.n_edges > BASE_FACTS else ("w", H.n_nodes)

        items = [record.to_hypergraph() for record in collection.records[:4]]
        items[2] = _record(2, BASE_FACTS + 1).to_hypergraph()
        ids = [record.kb_id for record in collection.records[:4]]
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(rq4, "member_word", fake)
            words, lost, arms = rq4.unit_words(
                ["fact_rank"], items, ids, [2], budget_s=1.0, cache={}, cache_scope="sub"
            )
        assert lost == [2]
        assert arms == {"fact_rank"}
        assert words["fact_rank"][2] is None


class TestFoldWordCensus:
    """The L15 accounting of the members the word budget lost."""

    @staticmethod
    def _census(kept: tuple[int, ...]) -> rq4.Census:
        return rq4.Census(
            kept=kept,
            n_censored=0,
            n_censored_anomaly=0,
            n_censored_clean=0,
            rate_anomaly=0.0,
            rate_clean=0.0,
        )

    def test_no_loss_returns_the_same_census(self) -> None:
        census = self._census((0, 1, 2))
        assert rq4.fold_word_census(census, [], {0}, set(), n_chosen=1, n_members=3) is census

    def test_an_anomaly_loss_is_split_from_a_clean_one(self) -> None:
        census = self._census((0, 1, 2, 3))
        folded = rq4.fold_word_census(census, [0, 3], {0}, {"wstar_orbit"}, n_chosen=1, n_members=4)
        assert folded.kept == (1, 2)
        assert folded.n_censored == 2
        assert folded.n_censored_word_anomaly == 1
        assert folded.n_censored_word_clean == 1
        assert folded.n_censored_anomaly == 1
        assert folded.n_censored_clean == 1
        assert folded.rate_anomaly == pytest.approx(1.0)
        assert folded.rate_clean == pytest.approx(1 / 3)
        assert folded.word_censored_arms == "wstar_orbit"

    def test_the_positions_are_read_against_kept_not_the_parent(self) -> None:
        # `kept` already skips member 1, so local index 1 is parent member 2.
        census = self._census((0, 2, 3))
        folded = rq4.fold_word_census(census, [1], {2}, {"fact_rank"}, n_chosen=1, n_members=4)
        assert folded.kept == (0, 3)
        assert folded.n_censored_word_anomaly == 1
        assert folded.n_censored_word_clean == 0


def _distances(ids: tuple[str, ...]) -> np.ndarray:
    """A metric whose value depends only on the member ids, never on position."""
    codes = [int(kb_id[1:]) for kb_id in ids]
    matrix = np.zeros((len(ids), len(ids)), dtype=np.float32)
    for i, a in enumerate(codes):
        for j, b in enumerate(codes):
            if i != j:
                matrix[i, j] = float(abs(a - b) + 1)
    return matrix


def _write_arm(root: Path, arm: str, kept: tuple[str, ...], censored: tuple[str, ...]) -> None:
    cache_dir = collection_cache_dir(root, COLLECTION)
    cache_dir.mkdir(parents=True, exist_ok=True)
    matrix_path, manifest_path = cache_paths(cache_dir, arm)
    np.save(matrix_path, _distances(kept))
    manifest_path.write_text(
        json.dumps({"arm": arm, "n": len(kept), "member_order_sha1": member_order_sha1(kept)}),
        encoding="utf-8",
    )
    if censored:
        censoring_path(cache_dir, arm).write_text(
            json.dumps(
                {
                    "arm": arm,
                    "n_requested": len(kept) + len(censored),
                    "n_censored": len(censored),
                    "member_ids": list(kept),
                    "censored_ids": list(censored),
                    "member_order_sha1": member_order_sha1(kept),
                }
            ),
            encoding="utf-8",
        )


ALL_IDS: tuple[str, ...] = tuple(f"m{i:02d}" for i in range(N_MEMBERS))


class TestAnomalyCensoring:
    """An anomaly whose word does not finish is dropped and counted, not scored."""

    ARMS: tuple[str, ...] = ("wstar_orbit", "size_l1")

    @staticmethod
    def _unit() -> rq4.Unit:
        sub = rq4.SubCollection(COLLECTION, COLLECTION, None, 0)
        return rq4.Unit(index=0, experiment=rq4.Experiment(sub, "spurious_fact", 1), seed=40000)

    def _run(
        self, collection: KBCollection, root: Path, censor: str
    ) -> dict[str, list[dict[str, Any]]]:
        """Run one unit with a word oracle that censors ``censor`` anomalies."""
        state = {"seen": 0}

        def fake(arm: str, H: Any, *, augment: bool, budget_s: float) -> tuple[Any, ...] | None:
            corrupted = H.n_edges > BASE_FACTS
            if corrupted and censor != "none":
                state["seen"] += 1
                if censor == "all" or state["seen"] == 1:
                    return None
            return ("w", H.n_nodes, H.n_edges)

        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(rq4, "member_word", fake)
            return rq4.run_unit(
                self._unit(),
                matrices_root=root,
                corpora_root=None,
                arms=self.ARMS,
                n_jobs=1,
                collection_cache={COLLECTION: collection},
                member_budget_s=1.0,
            )

    def test_no_censoring_scores_every_member(
        self, collection: KBCollection, tmp_path: Path
    ) -> None:
        for arm in self.ARMS:
            _write_arm(tmp_path, arm, ALL_IDS, ())
        rows = self._run(collection, tmp_path, "none")["auc"]
        assert rows
        for row in rows:
            assert row["censored"] == 0
            assert row["n_inliers"] + row["n_anomalies"] == N_MEMBERS
            assert row["n_censored_word_anomaly"] == 0
            assert row["n_censored_word_clean"] == 0
            assert row["word_censored_arms"] == ""

    def test_one_censored_anomaly_is_dropped_and_counted(
        self, collection: KBCollection, tmp_path: Path
    ) -> None:
        for arm in self.ARMS:
            _write_arm(tmp_path, arm, ALL_IDS, ())
        rows = self._run(collection, tmp_path, "one")["auc"]
        assert rows
        for row in rows:
            assert row["n_censored_word_anomaly"] == 1
            assert row["n_censored_word_clean"] == 0
            assert row["word_censored_arms"] == "wstar_orbit"
            # The member is gone from the population, not scored as an inlier.
            assert row["n_inliers"] + row["n_anomalies"] == N_MEMBERS - 1
            assert row["n_censored_members"] == 1
            assert row["censored"] == 0
            assert not np.isnan(row["auc"])

    def test_every_censored_anomaly_yields_no_auc(
        self, collection: KBCollection, tmp_path: Path
    ) -> None:
        for arm in self.ARMS:
            _write_arm(tmp_path, arm, ALL_IDS, ())
        rows = self._run(collection, tmp_path, "all")["auc"]
        assert rows
        n_anomalies = max(1, round(rq4.CONTAMINATION * N_MEMBERS))
        for row in rows:
            assert row["censored"] == 1
            assert np.isnan(row["auc"])
            assert row["n_censored_word_anomaly"] == n_anomalies
            assert row["n_anomalies"] == 0

    def test_an_arm_without_a_matrix_costs_no_words(
        self, collection: KBCollection, tmp_path: Path
    ) -> None:
        """A censored arm's rows are never computed: they would be discarded."""
        _write_arm(tmp_path, "size_l1", ALL_IDS, ())
        seen: list[str] = []

        def fake(arm: str, H: Any, *, augment: bool, budget_s: float) -> tuple[Any, ...]:
            seen.append(arm)
            return ("w", H.n_nodes)

        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(rq4, "member_word", fake)
            tables = rq4.run_unit(
                self._unit(),
                matrices_root=tmp_path,
                corpora_root=None,
                arms=self.ARMS,
                n_jobs=1,
                collection_cache={COLLECTION: collection},
                member_budget_s=1.0,
            )
        assert "wstar_orbit" not in seen
        censored = [row for row in tables["auc"] if row["arm"] == "wstar_orbit"]
        assert censored and all(row["censored"] == 1 for row in censored)
