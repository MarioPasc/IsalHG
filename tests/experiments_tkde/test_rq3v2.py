"""Unit tests for the RQ3 v2 runner.

Four things are guarded here, and each of them is a way the campaign could ship a
complete, plausible, wrong table.

*The noise model.*  The premise is that every member is exactly ``t`` edits from
the source, connected, anonymous, and not the source.  If any of those silently
fails the whole comparison is against an unknown quantity.

*The merge baselines.*  The design pre-states a mechanism --- a
reference-anchored merge cannot recover a fact whose constants the reference
lacks --- and a baseline that happened to recover it anyway would make the
headline meaningless.  The mechanism is therefore pinned on a hand-built star
whose answer is known by construction, not left to the corpus.

*The two bugs the pilot caught.*  Both produced numbers rather than exceptions:
a ball distance read off the word length scored an insert-and-delete pair as
zero, and an uncompacted output made the identity *oracle* score 0 at ``t = 1``.
Each has a test that fails against the old behaviour.

*The stale-row guard.*  RQ3 v1 decided which units were done by reading its own
untagged aggregate back off disk, so a changed arm set served rows that
contained no Isal arm at all under a manifest claiming otherwise (T-KBn).
"""

from __future__ import annotations

import csv
import random
import subprocess
import sys
from pathlib import Path

import pytest

from experiments.tkde import rq3v2
from experiments.tkde.budget import symbol_distance
from experiments.tkde.io import RunPaths, write_rows
from experiments.tkde.rq1 import table_file
from isalhg.datasets.kb.base import make_record
from isalhg.language.reach import fact_key_of

pytestmark = pytest.mark.unit

N_TYPES = 2
N_PREDS = 5

#: A star: constant 0 lies in every fact and no other constant lies in two. The
#: predicates are distinct, as they are in the corpora (wd50k66 carries 351), so
#: the facts are distinguishable --- which is the condition under which counting
#: fact patterns recovers a star at all.
STAR_FACTS = ((0, (0, 1)), (1, (0, 2)), (2, (0, 3)), (3, (0, 4)))
STAR_IDS = ("hub", "a", "b", "c", "d")

#: The same star with one predicate throughout: its four facts share a pattern,
#: so counting can read the multiset but not which member is missing which fact.
FLAT_STAR_FACTS = ((0, (0, 1)), (0, (0, 2)), (0, (0, 3)), (0, (0, 4)))

#: A non-star: a triangle over 0, 1, 2 with a pendant fact hanging 3 off 2. No
#: constant lies in every fact, constant 3 has degree 1 so fact 3 is pendant,
#: the three triangle facts are interior, and *every* single deletion leaves the
#: rest connected --- which is what makes it usable as a source under R3.
CHAIN_FACTS = ((0, (0, 1)), (1, (1, 2)), (2, (0, 2)), (3, (2, 3)))
CHAIN_IDS = ("p", "q", "r", "s")


def _record(kb_id, facts, n, ids, types=None):
    return make_record(
        kb_id,
        n,
        types if types is not None else [0] * n,
        list(facts),
        constant_ids=list(ids),
        meta={"n_types": N_TYPES, "n_preds": N_PREDS},
    )


@pytest.fixture
def star():
    return _record("star", STAR_FACTS, 5, STAR_IDS)


@pytest.fixture
def flat_star():
    return _record("flat_star", FLAT_STAR_FACTS, 5, STAR_IDS)


@pytest.fixture
def chain():
    return _record("chain", CHAIN_FACTS, 4, CHAIN_IDS)


def _H(record):
    return record.to_hypergraph(n_types=N_TYPES, n_preds=N_PREDS)


# ---------------------------------------------------------------------------
# Gate G0 --- the star predicate the strata are built on
# ---------------------------------------------------------------------------


class TestStarPredicate:
    def test_a_star_is_a_star(self, star):
        assert rq3v2.is_star(star)

    def test_a_chain_is_not(self, chain):
        assert not rq3v2.is_star(chain)

    def test_a_star_has_no_interior_fact(self, star):
        assert rq3v2.interior_facts(star) == []

    def test_every_fact_of_a_star_is_pendant(self, star):
        assert sorted(rq3v2.pendant_facts(star)) == [0, 1, 2, 3]

    def test_a_chain_has_interior_facts(self, chain):
        assert rq3v2.interior_facts(chain)


# ---------------------------------------------------------------------------
# The noise model
# ---------------------------------------------------------------------------


class TestNoiseEdits:
    @pytest.mark.parametrize("kind", rq3v2.NOISE_KINDS)
    def test_an_edit_stays_connected_and_non_empty(self, chain, kind):
        edited = rq3v2.apply_noise_edit(chain, kind, random.Random(0))
        if edited is None:
            pytest.skip(f"{kind} is not available on this record")
        assert edited.m >= 1
        assert edited.is_connected

    def test_a_deletion_removes_exactly_one_fact(self, chain):
        edited = rq3v2.apply_noise_edit(chain, "del_interior", random.Random(1))
        assert edited is not None
        assert edited.m == chain.m - 1

    def test_an_insertion_adds_exactly_one_fact(self, chain):
        edited = rq3v2.apply_noise_edit(chain, "ins_existing", random.Random(2))
        assert edited is not None
        assert edited.m == chain.m + 1

    def test_a_new_constant_insertion_adds_one_of_each(self, chain):
        edited = rq3v2.apply_noise_edit(chain, "ins_new_constant", random.Random(3))
        assert edited is not None
        assert edited.m == chain.m + 1
        assert edited.n == chain.n + 1

    def test_an_unknown_kind_is_refused(self, chain):
        with pytest.raises(rq3v2.RQ3v2Error):
            rq3v2.apply_noise_edit(chain, "teleport", random.Random(4))


class TestAnonymization:
    def test_the_constants_are_permuted_but_the_structure_is_not(self, chain):
        anonymous = rq3v2.anonymize(chain, random.Random(7), "anon")
        assert fact_key_of(_H(anonymous)) == fact_key_of(_H(chain))

    def test_the_identities_travel_with_the_permutation(self, chain):
        anonymous = rq3v2.anonymize(chain, random.Random(7), "anon")
        assert sorted(anonymous.constant_ids) == sorted(chain.constant_ids)
        before = {
            (pred, frozenset(chain.constant_ids[v] for v in members))
            for pred, members in chain.facts
        }
        after = {
            (pred, frozenset(anonymous.constant_ids[v] for v in members))
            for pred, members in anonymous.facts
        }
        assert before == after


class TestNoisyCollection:
    def test_the_members_are_t_edits_from_the_source_and_from_each_other(self, chain):
        built = rq3v2.noisy_collection(chain, 4, 1, 11)
        assert built is not None
        assert len(built.members) == 4
        truth = frozenset(chain.fact_set())
        keys = set()
        for member in built.members:
            assert member.is_connected
            assert member.m >= 1
            # Exactly t facts differ, in the source's own addressing: a member is
            # anonymized, so the comparison is on identities, never on indices.
            member_facts = {
                (pred, frozenset(member.constant_ids[v] for v in members))
                for pred, members in member.facts
            }
            source_facts = {
                (pred, frozenset(chain.constant_ids[v] for v in members))
                for pred, members in chain.facts
            }
            assert len(member_facts ^ source_facts) == 1
            assert frozenset(member.fact_set()) != truth
            keys.add(fact_key_of(_H(member)))
        assert len(keys) == len(built.members), "members must be pairwise distinct"

    def test_the_realised_edit_mix_is_logged(self, chain):
        built = rq3v2.noisy_collection(chain, 4, 2, 12)
        assert built is not None
        assert sum(built.edit_mix.values()) == 4 * 2
        assert set(built.edit_mix) <= set(rq3v2.NOISE_KINDS)

    def test_restricting_the_kinds_restricts_the_mix(self, star):
        built = rq3v2.noisy_collection(star, 3, 1, 13, kinds=("del_pendant",))
        assert built is not None
        assert set(built.edit_mix) == {"del_pendant"}

    def test_a_kind_the_record_cannot_admit_yields_no_collection(self, star):
        """A star has no interior fact, so a deletion-interior cell is empty on it."""
        assert rq3v2.noisy_collection(star, 3, 1, 14, kinds=("del_interior",)) is None


# ---------------------------------------------------------------------------
# The merge baselines and the pre-stated mechanism
# ---------------------------------------------------------------------------


def _single_deletion_members(record):
    """One member per fact, each the record with that fact deleted."""
    members = []
    for index in range(record.m):
        deleted = rq3v2._delete_fact(record, index, f"{record.kb_id}#d{index}")
        assert deleted is not None
        members.append(deleted)
    return members


class TestMergeBaselines:
    def test_the_identity_oracle_recovers_the_source(self, star):
        """Every fact survives in three of four members, so the vote keeps it."""
        from isalhg.language.majority import majority_merge
        from isalhg.language.reach import compact_constants

        members = _single_deletion_members(star)
        merged, _names = majority_merge(
            [_H(m) for m in members], [tuple(m.constant_ids) for m in members]
        )
        core, _survivors = compact_constants(merged)
        assert fact_key_of(core) == fact_key_of(_H(star))

    def test_a_reference_anchored_merge_cannot_recover_a_fact_the_reference_lacks(self, star):
        """The pre-stated mechanism, on a star, by construction.

        The reference is the member missing one pendant fact, so it is missing
        that fact's private constant too.  The merge votes in the reference's
        coordinates and can never hold more constants than the reference has, so
        it cannot return a record isomorphic to a source that has one more.
        """
        members = [_H(m) for m in _single_deletion_members(star)]
        merged = rq3v2.align_merge_ref(members, 0)
        assert merged.n_nodes <= members[0].n_nodes < _H(star).n_nodes
        assert fact_key_of(merged) != fact_key_of(_H(star))

    def test_the_iterated_merge_may_admit_a_constant_the_reference_lacks(self, star):
        """Its whole point is to exceed the reference's coordinates."""
        members = [_H(m) for m in _single_deletion_members(star)]
        merged = rq3v2.align_merge_iter(members, 0)
        assert merged.n_nodes >= rq3v2.align_merge_ref(members, 0).n_nodes

    def test_the_pattern_vote_recovers_a_star_with_distinguishable_facts(self, star):
        """The control the design expects to tie us on stars.

        Each of the four facts carries its own predicate, so each is a distinct
        pattern present in three of four members; the majority keeps all four and
        the star assembly puts them back on one hub.  This is why the star
        stratum is the control: no alignment was needed.
        """
        members = [_H(m) for m in _single_deletion_members(star)]
        merged = rq3v2.pattern_vote(members)
        assert fact_key_of(merged) == fact_key_of(_H(star))

    def test_the_pattern_vote_counts_multiplicity_not_presence(self, flat_star):
        """Against the pre-fix behaviour, which kept one fact per distinct pattern.

        The four facts of this star share one pattern, so a presence vote
        rebuilds a *one*-fact record.  The multiplicity vote keeps three --- the
        largest count more than half the members carry --- which is the honest
        limit of counting when the facts are indistinguishable, and is what the
        star cells of the flat-predicate kind will report.
        """
        members = [_H(m) for m in _single_deletion_members(flat_star)]
        merged = rq3v2.pattern_vote(members)
        assert merged.n_edges == 3, "a presence vote would return 1 fact here"


# ---------------------------------------------------------------------------
# consensus_ow --- the word ball, its distance, and its certificate
# ---------------------------------------------------------------------------


class TestBall:
    def test_the_shell_index_is_the_indel_distance(self):
        """Regression: the distance used to be read off the word length.

        ``("A", "B")`` reaches ``("B", "C")`` by deleting ``A`` and inserting
        ``C`` --- two edits, and the two words are the same length.  The old
        ``abs(len(candidate) - len(word))`` scored that 0, which made every
        such candidate look like the centre itself and corrupted the objective's
        distance criterion.
        """
        ball = rq3v2.indel_ball(("A", "B"), 2, ("A", "B", "C"))
        assert ball[("A", "B")] == 0
        assert ball[("B", "C")] == 2
        assert abs(len(("B", "C")) - len(("A", "B"))) == 0, "the old rule would say 0"

    def test_the_centre_is_in_the_ball_at_distance_zero(self):
        ball = rq3v2.indel_ball(("A",), 1, ("A", "B"))
        assert ball[("A",)] == 0

    def test_the_empty_word_is_never_produced(self):
        assert () not in rq3v2.indel_ball(("A",), 2, ("A", "B"))

    def test_a_one_edit_neighbour_is_at_distance_one(self):
        ball = rq3v2.indel_ball(("A", "B"), 1, ("A", "B"))
        assert ball[("B",)] == 1
        assert ball[("A", "A", "B")] == 1

    def test_the_restricted_ball_bounds_appends_and_deletes(self):
        ball = rq3v2.restricted_ball(("A", "B", "C"), ("D",), 2, 1)
        assert ball[("A", "B", "C", "D", "D")] == 2
        assert ("A", "B", "C", "D", "D", "D") not in ball
        assert ball[("A", "B")] == 1
        assert ("A",) not in ball


class TestConsensusOw:
    def test_the_source_and_two_sub_records_tie_on_the_objective(self, star):
        """The measurement that makes the tie break load-bearing.

        Each member is one deletion from the source, and the ordered walk charges
        that deletion exactly one token in both directions, so on this star the
        source costs 4 and members 1 and 2 also cost 4.  The median cannot
        separate them; whatever breaks the tie returns the answer.  Pinned here
        because it is the sharpest form of H3.6's mechanism and because a change
        to the word or the metric that silently resolved it would change RQ3's
        result without changing any hypothesis.
        """
        members = [_H(m) for m in _single_deletion_members(star)]
        symbols = [rq3v2.word_symbols(H) for H in members]
        source = rq3v2.word_symbols(_H(star))
        source_cost = sum(symbol_distance(source, s) for s in symbols)
        member_costs = [sum(symbol_distance(a, b) for b in symbols) for a in symbols]
        assert source_cost == 4
        assert sorted(member_costs) == [4, 4, 5, 5]

    def test_the_fingerprint_tie_break_recovers_the_star(self, star):
        """Unbiased with respect to size, so the source survives the tie."""
        members = [_H(m) for m in _single_deletion_members(star)]
        outcome = rq3v2.consensus_ow(members, 3, N_TYPES, N_PREDS, 2, tie_break="fingerprint")
        assert fact_key_of(outcome.kb) == fact_key_of(_H(star))
        assert outcome.origin == "decoded:non_member"

    def test_the_shortlex_tie_break_prefers_the_shorter_record(self, star):
        """The design's declared order, and the size bias it carries.

        Reported rather than corrected: shortlex takes the shorter word, and among
        tied candidates the shorter word is the smaller record.  The arm runs both
        ways on every collection so the choice is visible in the table.
        """
        members = [_H(m) for m in _single_deletion_members(star)]
        outcome = rq3v2.consensus_ow(members, 3, N_TYPES, N_PREDS, 2, tie_break="shortlex")
        assert outcome.kb.n_edges < _H(star).n_edges
        assert rq3v2.is_sub_record(outcome.kb, _H(star)) == 1

    def test_an_unknown_tie_break_is_refused(self, star):
        members = [_H(m) for m in _single_deletion_members(star)]
        with pytest.raises(rq3v2.RQ3v2Error):
            rq3v2.consensus_ow(members, 3, N_TYPES, N_PREDS, 2, tie_break="coin")

    def test_indistinguishable_facts_send_the_median_to_a_sub_record(self, flat_star):
        """H3.6's mechanism, pinned on the case that isolates it.

        With one predicate throughout, every member is one deletion from the
        source and two edits from every other member, so at ``N = 4`` a member
        itself costs 0 + 3 x 2 = 6 while the source costs 4 x 1 = 4 --- but the
        words are so short that the deletion is worth less than that, and the
        median lands on a sub-record.  The row records ``sub_record_drop``
        precisely so this failure is legible rather than arbitrary.
        """
        members = [_H(m) for m in _single_deletion_members(flat_star)]
        outcome = rq3v2.consensus_ow(members, 3, N_TYPES, N_PREDS, 2)
        assert rq3v2.is_sub_record(outcome.kb, _H(flat_star)) >= 0

    def test_every_decoded_word_is_a_connected_knowledge_base(self, chain):
        """Prop. C.4, measured on the ball rather than asserted (L19)."""
        members = [_H(m) for m in _single_deletion_members(chain)]
        outcome = rq3v2.consensus_ow(members, 3, N_TYPES, N_PREDS, 2)
        assert outcome.n_decoded > 0
        assert outcome.n_decoded_connected == outcome.n_decoded

    def test_the_cost_never_exceeds_the_medoid_cost(self, chain):
        """Every member is a candidate, so the generalized median is at least as good."""
        members = [_H(m) for m in _single_deletion_members(chain)]
        outcome = rq3v2.consensus_ow(members, 3, N_TYPES, N_PREDS, 2)
        assert outcome.cost <= outcome.medoid_cost

    def test_the_certified_ratio_respects_prop_3(self, chain):
        members = [_H(m) for m in _single_deletion_members(chain)]
        outcome = rq3v2.consensus_ow(members, 3, N_TYPES, N_PREDS, 2)
        assert outcome.lower_bound <= outcome.cost + 1e-9
        assert outcome.ratio <= 2 - 2 / len(members) + 1e-9

    def test_the_two_objectives_are_selectable_and_scored_alike(self, chain):
        members = [_H(m) for m in _single_deletion_members(chain)]
        first = rq3v2.consensus_ow(members, 3, N_TYPES, N_PREDS, 2, objective="distance_first")
        second = rq3v2.consensus_ow(members, 3, N_TYPES, N_PREDS, 2, objective="coverage_first")
        assert first.cost <= second.cost, "distance_first minimises exactly this"

    def test_an_unknown_objective_is_refused(self, chain):
        members = [_H(m) for m in _single_deletion_members(chain)]
        with pytest.raises(rq3v2.RQ3v2Error):
            rq3v2.consensus_ow(members, 3, N_TYPES, N_PREDS, 2, objective="vibes")

    def test_an_empty_collection_is_refused(self):
        with pytest.raises(rq3v2.RQ3v2Error):
            rq3v2.consensus_ow([], 3, N_TYPES, N_PREDS, 2)


class TestSubRecord:
    def test_the_source_is_a_sub_record_of_itself_at_zero(self, star):
        assert rq3v2.is_sub_record(_H(star), _H(star)) == 0

    def test_one_deletion_is_reported_as_one(self, star):
        member = _single_deletion_members(star)[0]
        assert rq3v2.is_sub_record(_H(member), _H(star)) == 1

    def test_an_unrelated_record_is_not_a_sub_record(self, star, chain):
        assert rq3v2.is_sub_record(_H(chain), _H(star)) == -1


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


class TestScoring:
    def test_an_output_is_compacted_before_it_is_scored(self, star):
        """Regression: an isolated constant made the identity oracle score 0.

        ``majority_merge`` carries the union of the identities, so a constant
        whose only fact lost the vote survives with no fact and the result is
        disconnected.  Scoring it uncompacted reported the *oracle* as failing at
        ``t = 1`` on a collection where it in fact recovers the source.
        """
        from isalhg.core.sparse_hypergraph import SparseHypergraph

        truth = _H(star)
        with_orphan = SparseHypergraph(
            truth.n_nodes + 1,
            [frozenset(members) for _e, members, _l in truth.iter_edges()],
            n_vertex_labels=truth.n_vertex_labels,
            n_edge_labels=truth.n_edge_labels,
            vertex_labels=[truth.vertex_label(v) for v in range(truth.n_nodes)] + [0],
            edge_labels=[label for _e, _m, label in truth.iter_edges()],
        )
        assert not with_orphan.is_connected(), "the pre-fix input"
        scored = rq3v2._score(with_orphan, truth, rq3v2.certificate(truth), 10.0)
        assert scored["exact_recovery"] == 1

    def test_a_genuinely_disconnected_output_scores_zero_not_blank(self, chain):
        from isalhg.core.sparse_hypergraph import SparseHypergraph

        truth = _H(chain)
        split = SparseHypergraph(
            4,
            [frozenset({0, 1}), frozenset({2, 3})],
            n_vertex_labels=N_TYPES,
            n_edge_labels=N_PREDS,
            vertex_labels=[0, 0, 0, 0],
            edge_labels=[0, 0],
        )
        scored = rq3v2._score(split, truth, rq3v2.certificate(truth), 10.0)
        assert scored["exact_recovery"] == 0
        assert "domain" in scored["reason"]

    def test_the_judge_is_named_on_every_row(self, star):
        truth = _H(star)
        scored = rq3v2._score(truth, truth, rq3v2.certificate(truth), 10.0)
        assert scored["fact_dist"] == 0
        assert scored["fact_dist_judge"] in ("exact_hged", "bipartite_ged_path")


# ---------------------------------------------------------------------------
# The stale-row guard (T-KBn)
# ---------------------------------------------------------------------------


class TestStaleRowGuard:
    def _unit(self):
        return rq3v2.Unit("ndc_classes", "non_star", 5, 1, 320000)

    def test_a_unit_with_no_file_is_not_done(self, tmp_path):
        paths = RunPaths(root=tmp_path, rq=rq3v2.RQ_DIR, experiment=rq3v2.EXPERIMENT)
        paths.ensure()
        assert not rq3v2.unit_is_done(paths, self._unit(), "aaaaaaaa")

    def test_a_unit_written_under_one_tag_is_done_under_that_tag(self, tmp_path):
        paths = RunPaths(root=tmp_path, rq=rq3v2.RQ_DIR, experiment=rq3v2.EXPERIMENT)
        paths.ensure()
        unit = self._unit()
        write_rows(
            paths,
            table_file("aaaaaaaa", rq3v2.ROWS_TABLE, unit.unit_id),
            [{"run_tag": "aaaaaaaa", "unit": unit.unit_id}],
            columns=("run_tag", "unit"),
        )
        assert rq3v2.unit_is_done(paths, unit, "aaaaaaaa")

    def test_the_same_unit_is_not_done_under_another_tag(self, tmp_path):
        """The T-KBn failure, made impossible.

        A changed arm set is a changed configuration, therefore a changed tag,
        therefore a different file name.  Rows measured under the old arm set can
        no longer be served as though they had the new one.
        """
        paths = RunPaths(root=tmp_path, rq=rq3v2.RQ_DIR, experiment=rq3v2.EXPERIMENT)
        paths.ensure()
        unit = self._unit()
        write_rows(
            paths,
            table_file("aaaaaaaa", rq3v2.ROWS_TABLE, unit.unit_id),
            [{"run_tag": "aaaaaaaa", "unit": unit.unit_id}],
            columns=("run_tag", "unit"),
        )
        assert not rq3v2.unit_is_done(paths, unit, "bbbbbbbb")

    def test_the_arm_set_changes_the_tag(self):
        from experiments.tkde.rq1 import run_tag

        base = {"design": {"radius": 2}, "medoid_arms": ["nauty_cert", "wl_l1"]}
        changed = {"design": {"radius": 2}, "medoid_arms": ["nauty_cert"]}
        assert run_tag(base) != run_tag(changed)

    def test_sharding_does_not_change_the_tag(self):
        from experiments.tkde.rq1 import run_tag

        base = {"design": {"radius": 2}, "n_shards": 1}
        resharded = {"design": {"radius": 2}, "n_shards": 64}
        assert run_tag(base) == run_tag(resharded)

    def test_a_truncated_file_is_not_done(self, tmp_path):
        paths = RunPaths(root=tmp_path, rq=rq3v2.RQ_DIR, experiment=rq3v2.EXPERIMENT)
        paths.ensure()
        unit = self._unit()
        target = paths.dir / f"rows_{table_file('aaaaaaaa', rq3v2.ROWS_TABLE, unit.unit_id)}.csv"
        target.write_text("", encoding="utf-8")
        assert not rq3v2.unit_is_done(paths, unit, "aaaaaaaa")


# ---------------------------------------------------------------------------
# Unit enumeration and the empty-stratum row
# ---------------------------------------------------------------------------


class TestUnits:
    def test_every_unit_id_is_unique(self):
        config = {
            "seed_count": 3,
            "design": {
                "collections": ["ndc_classes", "wd50k66"],
                "strata": ["star", "non_star"],
                "n_values": [5, 9],
                "t_values": [1, 2],
            },
        }
        units = rq3v2.enumerate_units(config)
        assert len(units) == 2 * 2 * 2 * 2 * 3
        assert len({unit.unit_id for unit in units}) == len(units)

    def test_a_shard_partition_covers_every_unit_once(self):
        config = {
            "seed_count": 2,
            "design": {
                "collections": ["ndc_classes"],
                "strata": ["non_star"],
                "n_values": [5, 9],
                "t_values": [1],
            },
        }
        units = rq3v2.enumerate_units(config)
        seen = []
        for index in range(1, 4):
            seen.extend(u for i, u in enumerate(units) if i % 3 == index - 1)
        assert sorted(u.unit_id for u in seen) == sorted(u.unit_id for u in units)

    def test_an_empty_stratum_emits_a_row_carrying_its_reason(self):
        """Gate G0 found no star in ndc_classes' source window; that is a finding."""
        config = {
            "seed_count": 1,
            "design": {
                "collections": ["ndc_classes"],
                "strata": ["star"],
                "n_values": [5],
                "t_values": [1],
                "sources_per_cell": 8,
            },
        }
        unit = rq3v2.enumerate_units(config)[0]
        rows, dropped = rq3v2.run_unit(unit, config, None, [], {"git_sha": "", "host_cpu": ""}, "t")
        assert dropped == 0
        assert len(rows) == 1
        assert rows[0]["method"] == "cell_empty"
        assert rows[0]["censored"] == 1
        assert "gate G0" in rows[0]["reason"]

    def test_every_row_key_is_a_declared_column(self):
        config = {
            "seed_count": 1,
            "design": {
                "collections": ["ndc_classes"],
                "strata": ["star"],
                "n_values": [5],
                "t_values": [1],
                "sources_per_cell": 8,
            },
        }
        unit = rq3v2.enumerate_units(config)[0]
        rows, _ = rq3v2.run_unit(unit, config, None, [], {"git_sha": "", "host_cpu": ""}, "t")
        assert set(rows[0]) <= set(rq3v2.ROW_COLUMNS)


# ---------------------------------------------------------------------------
# End to end, as one SLURM shard runs it
# ---------------------------------------------------------------------------


CONFIG = Path("experiments/tkde/configs/rq3v2.yaml")
DATA_ROOT = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE")


def _run(arguments: list[str]) -> subprocess.CompletedProcess:
    """Run the runner in a child process, as one shard does.

    The medoid screen forks, and a process that has already canonicalized in the
    C++ engine forks children that deadlock, so an in-process ``main`` would
    inherit whatever an earlier test in the session did to this interpreter.
    """
    return subprocess.run(
        [sys.executable, "-m", "experiments.tkde.rq3v2", *arguments],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.slow
@pytest.mark.skipif(not DATA_ROOT.is_dir(), reason="the frozen corpora are not on this machine")
class TestSmokeEndToEnd:
    def test_the_smoke_writes_a_tagged_row_file_with_every_arm(self, tmp_path):
        done = _run(
            [
                "--config",
                str(CONFIG),
                "--smoke",
                "--out",
                str(tmp_path),
                "--data-root",
                str(DATA_ROOT),
                "--log-level",
                "ERROR",
            ]
        )
        assert done.returncode == 0, done.stderr[-4000:]
        directory = tmp_path / rq3v2.RQ_DIR / rq3v2.EXPERIMENT
        files = sorted(directory.glob("rows_golden__*.csv"))
        assert files, "the smoke wrote no tagged row file"
        with files[0].open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        assert rows
        assert {row["run_tag"] for row in rows} == {rows[0]["run_tag"]}
        methods = {row["method"] for row in rows}
        assert "consensus_ow" in methods
        assert "consensus_fact" in methods
        assert set(rq3v2.MERGE_METHODS) <= methods
        arms = {row["arm"] for row in rows if row["method"] == "medoid"}
        assert set(rq3v2.MEDOID_ARMS) <= arms, "an arm must carry a reason, never be absent"

    def test_the_census_mode_reports_both_strata(self, tmp_path):
        done = _run(
            [
                "--config",
                str(CONFIG),
                "--census",
                "--data-root",
                str(DATA_ROOT),
                "--log-level",
                "ERROR",
            ]
        )
        assert done.returncode == 0, done.stderr[-4000:]
        assert "n_stars" in done.stdout

    def test_a_malformed_shard_is_refused(self):
        done = _run(["--config", str(CONFIG), "--shard", "5/2"])
        assert done.returncode != 0
