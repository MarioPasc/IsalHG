"""Unit tests for the RQ8 unit generator, the G0 census, and the baselines.

Every assertion here is on a hand-built record, so a failure names the rule it
broke rather than a corpus statistic.
"""

from __future__ import annotations

import random

import pytest

from experiments.tkde.rq8 import (
    KIND_INTERIOR,
    KIND_PENDANT,
    PatternStatistics,
    attach,
    build_eval_units,
    delete_fact,
    fact_degrees,
    hidden_kind,
    interior_fact_ids,
    is_star,
    pattern_of,
    patterns_of,
    root_of,
    split_members,
    star_census,
)
from isalhg.datasets.kb.base import KBCollection, KBRecord

pytestmark = pytest.mark.unit


def record(kb_id: str, n: int, types, facts, label: str | None = None) -> KBRecord:
    """A record over a two-type, three-predicate vocabulary."""
    return KBRecord(
        kb_id=kb_id,
        n=n,
        types=tuple(types),
        facts=tuple(facts),
        label=label,
        meta={"n_types": 3, "n_preds": 3},
    )


# A pure star: constant 0 is in every fact, the leaves appear once each.
STAR = record("star", 5, (0, 1, 1, 1, 1), [(0, (0, 1)), (1, (0, 2)), (2, (0, 3)), (0, (0, 4))])

# A chain: 0-1, 1-2, 2-3. Constant 0 is the root by degree only after the tie
# break; constants 1 and 2 are shared, so every fact is interior.
CHAIN = record("chain", 4, (0, 1, 1, 2), [(0, (0, 1)), (1, (1, 2)), (2, (2, 3))])

# A star with one extra fact between two leaves: not a star, and exactly the
# facts touching the shared leaves are interior.
MIXED = record(
    "mixed",
    5,
    (0, 1, 1, 1, 2),
    [(0, (0, 1)), (0, (0, 2)), (1, (0, 3)), (2, (1, 2)), (0, (0, 4))],
)


class TestStarCensus:
    """Gate G0's frozen definition."""

    def test_a_star_is_a_star(self):
        assert is_star(STAR)

    def test_the_root_of_a_star_is_the_shared_constant(self):
        assert root_of(STAR) == 0

    def test_a_chain_is_not_a_star(self):
        assert not is_star(CHAIN)

    def test_a_star_with_one_leaf_leaf_fact_is_not_a_star(self):
        # Constant 0 is still in four of five facts but not in (1, 2), and
        # constants 1 and 2 now appear twice each: both clauses fail.
        assert not is_star(MIXED)

    def test_two_shared_leaves_defeat_the_every_fact_clause(self):
        # A constant in every fact but with a shared leaf is still not a star.
        shared_leaf = record(
            "shared", 4, (0, 1, 1, 1), [(0, (0, 1)), (0, (0, 2)), (0, (0, 1, 3)), (0, (0, 3))]
        )
        degrees = fact_degrees(shared_leaf)
        assert degrees[0] == shared_leaf.m
        assert not is_star(shared_leaf)

    def test_the_census_counts_both_classes(self):
        collection = KBCollection(
            name="tiny",
            records=(STAR, CHAIN, MIXED),
            type_names=("a", "b", "c"),
            pred_names=("p", "q", "r"),
        )
        row = star_census(collection, m_min=4)
        assert row["n_members"] == 3
        assert row["n_star"] == 1
        assert row["n_non_star"] == 2
        assert row["frac_star"] == pytest.approx(1 / 3)
        # CHAIN has three facts, so only STAR and MIXED reach the pool.
        assert row["n_pool"] == 2
        assert row["n_pool_star"] == 1
        assert row["n_pool_non_star"] == 1


class TestInteriorAndPendant:
    """The rule that decides which fact may be hidden."""

    def test_a_star_has_no_interior_fact(self):
        assert interior_fact_ids(STAR) == ()

    def test_every_fact_of_a_chain_touching_a_shared_constant_is_interior(self):
        # Root is 1 or 2 (degree 2, tie by id -> 1). Constant 2 is then the only
        # shared non-root constant, so the facts containing it are interior.
        assert root_of(CHAIN) == 1
        assert interior_fact_ids(CHAIN) == (1, 2)

    def test_the_leaf_leaf_fact_and_its_neighbours_are_interior(self):
        interior = set(interior_fact_ids(MIXED))
        # Facts are stored sorted; (0,(0,1)) (0,(0,2)) (0,(0,4)) (1,(0,3)) (2,(1,2)).
        kinds = [hidden_kind(MIXED, index) for index in range(MIXED.m)]
        assert kinds.count(KIND_INTERIOR) == len(interior)
        assert kinds.count(KIND_PENDANT) == MIXED.m - len(interior)
        assert KIND_INTERIOR in kinds and KIND_PENDANT in kinds

    def test_a_record_without_constants_has_no_root(self):
        from experiments.tkde.rq8 import RQ8Error

        empty = KBRecord(kb_id="empty", n=0, types=(), facts=(), meta={"n_types": 1, "n_preds": 1})
        with pytest.raises(RQ8Error):
            root_of(empty)


class TestDeleteFact:
    """``K-`` is connected or it is not produced."""

    def test_deleting_a_pendant_fact_keeps_the_remainder_connected(self):
        minus = delete_fact(STAR, 0)
        assert minus is not None
        assert minus.is_connected()
        assert minus.m == STAR.m - 1

    def test_the_leaf_that_lost_its_only_fact_is_dropped(self):
        minus = delete_fact(STAR, 0)
        assert minus is not None
        assert minus.n == STAR.n - 1

    def test_deleting_a_bridge_returns_none(self):
        # Removing the middle link of the chain splits it in two.
        assert delete_fact(CHAIN, 1) is None

    def test_deleting_the_only_fact_returns_none(self):
        single = record("single", 2, (0, 1), [(0, (0, 1))])
        assert delete_fact(single, 0) is None


class TestEvalUnits:
    """The unit generator honours the stratum rule and reports its resamples."""

    def test_non_star_units_hide_only_interior_facts(self):
        units, _attempted, _resampled = build_eval_units(
            [MIXED], "non_star", per_member=5, limit=10, rng=random.Random(0)
        )
        assert units
        assert all(unit.kind == KIND_INTERIOR for unit in units)

    def test_star_units_hide_any_fact(self):
        units, _attempted, _resampled = build_eval_units(
            [STAR], "star", per_member=5, limit=10, rng=random.Random(0)
        )
        assert units
        assert all(unit.kind == KIND_PENDANT for unit in units)

    def test_every_unit_carries_a_connected_remainder(self):
        units, _attempted, _resampled = build_eval_units(
            [STAR, CHAIN, MIXED], "non_star", per_member=5, limit=50, rng=random.Random(1)
        )
        assert all(unit.minus.is_connected() for unit in units)

    def test_a_disconnecting_draw_is_counted_as_a_resample(self):
        units, attempted, resampled = build_eval_units(
            [CHAIN], "non_star", per_member=5, limit=10, rng=random.Random(0)
        )
        # Fact 1 is the bridge and fact 2 is interior; the bridge is refused.
        assert resampled >= 1
        assert attempted == len(units) + resampled

    def test_per_member_caps_the_draw(self):
        units, _attempted, _resampled = build_eval_units(
            [MIXED], "non_star", per_member=1, limit=10, rng=random.Random(0)
        )
        assert len(units) == 1

    def test_the_limit_caps_the_unit_count(self):
        units, _attempted, _resampled = build_eval_units(
            [MIXED, CHAIN], "non_star", per_member=5, limit=2, rng=random.Random(0)
        )
        assert len(units) == 2

    def test_the_hidden_fact_is_not_in_the_remainder(self):
        units, _a, _r = build_eval_units(
            [MIXED], "non_star", per_member=5, limit=10, rng=random.Random(3)
        )
        for unit in units:
            assert unit.truth.m == unit.minus.m + 1
            assert unit.hidden in unit.truth.facts


class TestSplitLeakage:
    """The evaluation split is never seen by a model."""

    @staticmethod
    def _pool(n: int) -> list[KBRecord]:
        return [
            record(f"m{index}", 3, (0, 1, 1), [(0, (0, 1)), (1, (0, 2))], label=f"c{index % 3}")
            for index in range(n)
        ]

    def test_train_and_evaluation_are_disjoint(self):
        train, evaluation = split_members(self._pool(50), train_frac=0.8, rng=random.Random(0))
        assert {r.kb_id for r in train}.isdisjoint({r.kb_id for r in evaluation})

    def test_the_split_covers_the_pool(self):
        pool = self._pool(50)
        train, evaluation = split_members(pool, train_frac=0.8, rng=random.Random(0))
        assert len(train) + len(evaluation) == len(pool)

    def test_the_split_is_deterministic_in_the_seed(self):
        pool = self._pool(40)
        first = split_members(pool, train_frac=0.8, rng=random.Random(7))
        second = split_members(pool, train_frac=0.8, rng=random.Random(7))
        assert [r.kb_id for r in first[0]] == [r.kb_id for r in second[0]]
        assert [r.kb_id for r in first[1]] == [r.kb_id for r in second[1]]

    def test_two_seeds_redraw_the_split(self):
        pool = self._pool(60)
        first = {r.kb_id for r in split_members(pool, train_frac=0.8, rng=random.Random(1))[1]}
        second = {r.kb_id for r in split_members(pool, train_frac=0.8, rng=random.Random(2))[1]}
        assert first != second

    def test_every_class_reaches_training(self):
        pool = self._pool(30)
        train, _evaluation = split_members(pool, train_frac=0.8, rng=random.Random(0))
        assert {r.label for r in train} == {r.label for r in pool}

    def test_a_singleton_class_is_not_lost_to_evaluation(self):
        pool = [*self._pool(9), record("solo", 3, (0, 1, 1), [(0, (0, 1)), (1, (0, 2))], "rare")]
        train, _evaluation = split_members(pool, train_frac=0.8, rng=random.Random(0))
        assert "rare" in {r.label for r in train}


class TestPatternBaselines:
    """The counting arms, on hand-built training corpora."""

    @staticmethod
    def _training() -> list[KBRecord]:
        common = record("a", 3, (0, 1, 1), [(0, (0, 1)), (0, (0, 2))])
        rare = record("b", 3, (0, 1, 2), [(0, (0, 1)), (2, (0, 2))])
        return [common, common, common, rare]

    def test_frequency_ranks_the_commonest_pattern_first(self):
        statistics = PatternStatistics.fit(self._training())
        ranked = statistics.by_frequency(CHAIN, 3)
        assert ranked[0] == (0, 2, (0, 1))

    def test_cooccurrence_conditions_on_the_record(self):
        statistics = PatternStatistics.fit(self._training())
        # A record carrying only the rare pattern should rank its co-occurring
        # partner above patterns it never appears with.
        holder = record("h", 3, (0, 1, 2), [(2, (0, 2))])
        ranked = statistics.by_cooccurrence(holder, 3)
        assert (0, 2, (0, 1)) in ranked

    def test_cooccurrence_falls_back_to_frequency_on_an_unseen_record(self):
        statistics = PatternStatistics.fit(self._training())
        unseen = record("u", 2, (2, 2), [(1, (0, 1))])
        assert statistics.by_cooccurrence(unseen, 2) == statistics.by_frequency(unseen, 2)

    def test_random_draws_come_from_the_training_vocabulary(self):
        statistics = PatternStatistics.fit(self._training())
        drawn = statistics.at_random(10, random.Random(0))
        assert set(drawn) <= set(statistics.vocabulary)

    def test_the_vocabulary_is_the_training_patterns(self):
        statistics = PatternStatistics.fit(self._training())
        assert set(statistics.vocabulary) == {(0, 2, (0, 1)), (2, 2, (0, 2))}


class TestAttachment:
    """The attachment heuristic: root for stars, highest degree otherwise."""

    def test_a_star_attachment_uses_the_root(self):
        pattern = pattern_of(STAR, (1, (0, 1)))
        extended = attach(STAR, pattern, prefer_root=True)
        assert extended is not None
        added = [fact for fact in extended.facts if fact not in STAR.facts]
        assert len(added) == 1
        # Compaction preserves the ordering of the surviving constants, so the
        # root keeps id 0 and must be an operand of the new fact.
        assert 0 in added[0][1]

    def test_a_non_star_attachment_prefers_the_highest_degree_constant(self):
        pattern = (1, 2, (1, 1))
        extended = attach(MIXED, pattern, prefer_root=False)
        assert extended is not None
        added = [fact for fact in extended.facts if fact not in MIXED.facts]
        assert len(added) == 1
        degrees = fact_degrees(MIXED)
        best = max((v for v in range(MIXED.n) if MIXED.types[v] == 1), key=lambda v: degrees[v])
        assert best in added[0][1]

    def test_the_result_is_connected(self):
        for pattern in {*patterns_of(MIXED), (1, 2, (2, 2)), (2, 3, (1, 1, 2))}:
            extended = attach(MIXED, pattern, prefer_root=False)
            if extended is not None:
                assert extended.is_connected(), pattern

    def test_a_pattern_with_no_matching_type_anchors_on_the_hub(self):
        # Type 2 occurs once in MIXED; a pattern over two type-2 operands has to
        # create one and still reach the knowledge base.
        extended = attach(MIXED, (1, 2, (2, 2)), prefer_root=False)
        assert extended is not None
        assert extended.is_connected()

    def test_an_attachment_reproducing_an_existing_fact_is_refused(self):
        # The heuristic is deterministic: on STAR the pattern of fact 0 resolves
        # to the root plus the highest-degree type-1 constant, which is the
        # fact itself. Emitting it would be a duplicate, so the attachment is
        # refused and the arm loses the slot rather than proposing nothing new.
        star_pattern = pattern_of(STAR, STAR.facts[0])
        assert star_pattern in patterns_of(STAR)
        assert attach(STAR, star_pattern, prefer_root=True) is None

    def test_the_next_rank_recovers_a_pattern_the_top_choice_wastes(self):
        # The same pattern one position down the degree ranking reaches a
        # different leaf, so the recommender does not lose the slot.
        star_pattern = pattern_of(STAR, STAR.facts[0])
        recovered = attach(STAR, star_pattern, prefer_root=True, rank=1)
        assert recovered is not None
        assert recovered.m == STAR.m + 1
        assert recovered.is_connected()

    def test_a_rank_past_the_end_falls_back_to_the_last_choice(self):
        # Out-of-range ranks must not raise; they clamp to the deepest choice.
        assert attach(MIXED, (1, 2, (1, 1)), prefer_root=False, rank=99) is not None

    def test_an_arity_one_pattern_is_refused(self):
        assert attach(MIXED, (0, 1, (1,)), prefer_root=False) is None
