"""Ladders, variant collections, corruptions, the envelope sweep, synthetic RQ1.

Every generator is asserted to be a pure function of its seed, to honour its
rejection rules, and to carry the identities and metadata the evaluation needs.
"""

from __future__ import annotations

from collections import Counter

import pytest

from isalhg.datasets.kb import corruptions, envelope_sweep, ladders, synthetic_rq1
from isalhg.datasets.kb.base import (
    DEFAULT_ENVELOPE,
    Envelope,
    KBGenerationError,
    KBRecord,
    iso_fingerprint,
)

pytestmark = pytest.mark.unit

RELAXED = Envelope(n_max=24, m_min=1, m_max=110, k_max=10)


def identity_facts(record: KBRecord) -> frozenset[tuple[int, frozenset[str]]]:
    """Return ``record``'s facts addressed by external identity, not by constant number."""
    ids = record.constant_ids
    assert ids is not None
    return frozenset((pred, frozenset(ids[v] for v in members)) for pred, members in record.facts)


def base_record(kb_id: str = "base") -> KBRecord:
    """Six constants, seven facts of arity 2-3, two predicates, two types."""
    facts = (
        (0, (0, 1)),
        (0, (1, 2)),
        (0, (2, 3)),
        (1, (3, 4)),
        (1, (4, 5)),
        (0, (0, 2, 4)),
        (1, (1, 3, 5)),
    )
    return KBRecord(
        kb_id=kb_id,
        n=6,
        types=(0, 1, 0, 1, 0, 1),
        facts=facts,
        constant_ids=tuple(f"c{i}" for i in range(6)),
        meta={"n_types": 2, "n_preds": 2},
    )


def keys(records: list[KBRecord]) -> list[tuple]:
    return [r.key() for r in records]


class TestSingleEdits:
    @pytest.mark.parametrize("kind", ladders.EDIT_KINDS)
    def test_deterministic_under_seed(self, kind: str) -> None:
        a = ladders.single_edits(base_record(), kind, 4, 7)
        b = ladders.single_edits(base_record(), kind, 4, 7)
        assert keys(a) == keys(b)
        assert [r.kb_id for r in a] == [r.kb_id for r in b]
        assert [dict(r.meta) for r in a] == [dict(r.meta) for r in b]

    @pytest.mark.parametrize("kind", ladders.EDIT_KINDS)
    def test_results_are_distinct_connected_and_non_isomorphic(self, kind: str) -> None:
        base = base_record()
        fingerprint = iso_fingerprint(base)
        edits = ladders.single_edits(base, kind, 4, 11)
        assert edits, f"{kind} produced nothing on the fixture"
        assert len(set(keys(edits))) == len(edits)
        for edited in edits:
            assert edited.is_connected()
            assert iso_fingerprint(edited) != fingerprint
            assert edited.max_arity <= DEFAULT_ENVELOPE.k_max
            assert edited.meta["base_id"] == base.kb_id
            assert edited.meta["edit_kind"] == kind
            assert edited.constant_ids is not None

    @pytest.mark.parametrize(
        ("kind", "preserved"),
        [
            ("insert_fact", True),
            ("add_constant", True),
            ("insert_fact_new_constant", False),
        ],
    )
    def test_regime_flag(self, kind: str, preserved: bool) -> None:
        for edited in ladders.single_edits(base_record(), kind, 3, 3):
            assert edited.meta["constant_set_preserved"] is preserved

    def test_new_constant_edit_extends_identities(self) -> None:
        edits = ladders.single_edits(base_record(), "insert_fact_new_constant", 2, 5)
        assert edits
        for edited in edits:
            assert edited.n == 7
            assert edited.constant_ids is not None
            assert len(edited.constant_ids) == 7
            assert edited.constant_ids[:6] == base_record().constant_ids

    def test_upper_walls_are_enforced(self) -> None:
        narrow = Envelope(n_max=6, m_min=1, m_max=7, k_max=3)
        assert ladders.single_edits(base_record(), "insert_fact", 4, 1, envelope=narrow) == []

    def test_unknown_kind_raises(self) -> None:
        with pytest.raises(ValueError, match="unknown edit kind"):
            ladders.single_edits(base_record(), "nope", 1, 0)


class TestLadder:
    def test_deterministic_and_exact_delta(self) -> None:
        base = base_record()
        rungs = ladders.constant_preserving_ladder(base, 5, 13)
        assert keys(rungs) == keys(ladders.constant_preserving_ladder(base, 5, 13))
        assert rungs
        for t, rung in enumerate(rungs, 1):
            assert rung.meta["t"] == t
            assert rung.meta["constant_set_preserved"] is True
            assert rung.n == base.n
            assert rung.types == base.types
            assert rung.constant_ids == base.constant_ids
            assert rung.is_connected()
            assert rung.meta["delta"] == ladders.fact_distance(base, rung)
            assert rung.meta["delta"] >= 1

    def test_delta_is_monotone_in_the_walk_budget(self) -> None:
        rungs = ladders.constant_preserving_ladder(base_record(), 5, 21)
        assert all(rung.meta["delta"] <= t for t, rung in enumerate(rungs, 1))

    def test_zero_budget_returns_nothing(self) -> None:
        assert ladders.constant_preserving_ladder(base_record(), 0, 1) == []


class TestVariantCollection:
    @pytest.mark.parametrize("kind", ladders.VARIANT_KINDS)
    def test_members_are_legal_and_deterministic(self, kind: str) -> None:
        source = base_record()
        members = ladders.variant_collection(source, 5, 2, kind, 4, envelope=RELAXED)
        assert members is not None
        assert keys(members) == keys(
            ladders.variant_collection(source, 5, 2, kind, 4, envelope=RELAXED)
        )
        fingerprints = {iso_fingerprint(source)}
        assert source.constant_ids is not None
        source_type_of = dict(zip(source.constant_ids, source.types, strict=True))
        for member in members:
            # a stranded constant leaves with its last fact, so the constant set
            # shrinks rather than staying pinned; identities and types travel
            assert member.constant_ids is not None
            assert member.n == len(member.constant_ids) <= source.n
            assert set(member.constant_ids) <= set(source.constant_ids)
            assert member.types == tuple(source_type_of[c] for c in member.constant_ids)
            assert member.meta["source_id"] == source.kb_id
            assert member.meta["cell_kind"] == kind
            assert member.meta["cell_t"] == 2
            assert member.meta["constant_set_preserved"] is (member.n == source.n)
            fingerprint = iso_fingerprint(member)
            assert fingerprint not in fingerprints
            fingerprints.add(fingerprint)

    def test_deletion_members_may_lose_a_constant(self) -> None:
        source = base_record()
        shrunk = [
            member
            for kind in ("del", "mix")
            for member in (
                ladders.variant_collection(source, 5, 2, kind, 4, envelope=RELAXED) or ()
            )
            if member.n < source.n
        ]
        assert shrunk, "no member stranded a constant; the fixture no longer exercises compaction"
        assert all(member.meta["constant_set_preserved"] is False for member in shrunk)

    def test_insertion_only_grows_and_deletion_only_shrinks(self) -> None:
        source = base_record()
        ins = ladders.variant_collection(source, 4, 2, "ins", 9, envelope=RELAXED)
        dele = ladders.variant_collection(source, 4, 2, "del", 9, envelope=RELAXED)
        assert ins is not None and dele is not None
        assert all(m.m == source.m + 2 for m in ins)
        assert all(m.m == source.m - 2 for m in dele)
        # constant numbers shift under compaction, so the containment is read
        # off the identities rather than off the numbering
        assert all(identity_facts(source) <= identity_facts(m) for m in ins)
        assert all(identity_facts(m) <= identity_facts(source) for m in dele)

    def test_impossible_cell_returns_none(self) -> None:
        tiny = KBRecord(kb_id="tiny", n=2, types=(0, 0), facts=((0, (0, 1)),))
        assert ladders.variant_collection(tiny, 5, 2, "del", 0) is None

    def test_unknown_kind_raises(self) -> None:
        with pytest.raises(ValueError, match="unknown variant kind"):
            ladders.variant_collection(base_record(), 3, 1, "nope", 0)


class TestCorruptions:
    @pytest.mark.parametrize("kind", corruptions.CORRUPTION_KINDS)
    @pytest.mark.parametrize("budget", [1, 2])
    def test_deterministic_and_non_isomorphic(self, kind: str, budget: int) -> None:
        base = base_record()
        first = corruptions.corrupt(base, kind, budget, 17)
        second = corruptions.corrupt(base, kind, budget, 17)
        assert first is not None
        assert first.key() == second.key()
        assert first.meta["noniso_verified"] is True
        assert iso_fingerprint(first) != iso_fingerprint(base)
        assert first.meta["corruption"] == kind
        assert first.meta["budget"] == budget
        assert first.constant_ids is not None

    @pytest.mark.parametrize("budget", [1, 2])
    def test_budgets_move_the_fact_count(self, budget: int) -> None:
        base = base_record()
        spurious = corruptions.corrupt(base, "spurious_fact", budget, 3)
        missing = corruptions.corrupt(base, "missing_fact", budget, 3)
        wrong = corruptions.corrupt(base, "wrong_argument", budget, 3)
        assert spurious is not None and missing is not None and wrong is not None
        assert spurious.m == base.m + budget
        assert base.fact_set() < spurious.fact_set()
        assert missing.m == base.m - budget
        assert wrong.m == base.m

    def test_iso_twin_preserves_every_coarse_statistic(self) -> None:
        base = base_record()
        twin = corruptions.corrupt(base, "iso_twin", 1, 29)
        assert twin is not None
        assert twin.n == base.n
        assert twin.m == base.m
        assert twin.arity_histogram() == base.arity_histogram()
        assert twin.degree_sequence() == base.degree_sequence()
        assert Counter(twin.types) == Counter(base.types)
        assert Counter(p for p, _ in twin.facts) == Counter(p for p, _ in base.facts)
        assert twin.meta["invariants_preserved"] is True
        assert isinstance(twin.meta["wl1_equal"], bool)
        assert twin.meta["n_swaps"] >= 1
        assert iso_fingerprint(twin) != iso_fingerprint(base)

    def test_wl1_histogram_is_permutation_invariant(self) -> None:
        base = base_record()
        relabelled = KBRecord(
            kb_id="perm",
            n=base.n,
            types=tuple(base.types[(v + 3) % 6] for v in range(6)),
            facts=tuple(
                (pred, tuple(sorted((v - 3) % 6 for v in members))) for pred, members in base.facts
            ),
        )
        assert corruptions.wl1_histogram(base) == corruptions.wl1_histogram(relabelled)

    def test_invalid_arguments(self) -> None:
        with pytest.raises(ValueError, match="unknown corruption kind"):
            corruptions.corrupt(base_record(), "nope", 1, 0)
        with pytest.raises(ValueError, match="budget"):
            corruptions.corrupt(base_record(), "missing_fact", 0, 0)

    def test_over_budget_deletion_is_refused(self) -> None:
        small = KBRecord(kb_id="s", n=3, types=(0, 0, 0), facts=((0, (0, 1)), (0, (1, 2))))
        assert corruptions.corrupt(small, "missing_fact", 2, 0) is None


class TestEnvelopeSweep:
    def test_grid_shape(self) -> None:
        cells = envelope_sweep.grid()
        core = [c for c in cells if not c["fact_alphabet_only"]]
        assert len(core) == 6 * 4 * 3 * 2 * 2
        assert len(cells) - len(core) == 3 * 2
        assert {c["n_seeds"] for c in cells} == {27}

    def test_every_grid_cell_is_feasible(self) -> None:
        cells = envelope_sweep.grid()
        assert all(c["feasible"] for c in cells)
        assert all(c["n"] <= envelope_sweep.max_constants(c["m"], c["k"]) for c in cells)

    def test_sparse_arity_two_cells_are_trees(self) -> None:
        cells = [c for c in envelope_sweep.grid() if c["density"] == "sparse" and c["k"] == 2]
        assert cells
        assert all(c["n"] == c["m"] + 1 for c in cells)

    def test_constants_for(self) -> None:
        assert envelope_sweep.constants_for(10, 3, "sparse") == 15
        assert envelope_sweep.constants_for(10, 3, "dense") == 8
        # The sparse target is capped at the structural maximum; it binds at k = 2.
        assert envelope_sweep.constants_for(10, 2, "sparse") == 11
        assert envelope_sweep.constants_for(160, 2, "sparse") == 161
        assert envelope_sweep.max_constants(10, 2) == 11
        with pytest.raises(KBGenerationError):
            envelope_sweep.constants_for(10, 3, "medium")

    @pytest.mark.parametrize("density", ["sparse", "dense"])
    @pytest.mark.parametrize(("m", "k"), [(10, 2), (10, 3), (20, 4), (40, 5)])
    def test_random_kb_matches_its_cell(self, m: int, k: int, density: str) -> None:
        record = envelope_sweep.random_kb(m, k, 3, 4, density, 0)
        assert record.m == m
        assert record.n == envelope_sweep.constants_for(m, k, density)
        assert record.max_arity <= k
        assert min(len(members) for _, members in record.facts) >= 2
        assert record.is_connected()
        assert max(record.types) < 4
        assert max(pred for pred, _ in record.facts) < 3

    def test_random_kb_is_deterministic(self) -> None:
        a = envelope_sweep.random_kb(20, 3, 3, 4, "dense", 5)
        b = envelope_sweep.random_kb(20, 3, 3, 4, "dense", 5)
        assert a.key() == b.key()
        assert a.key() != envelope_sweep.random_kb(20, 3, 3, 4, "dense", 6).key()

    def test_every_grid_cell_realises_at_the_smallest_sizes(self) -> None:
        cells = [c for c in envelope_sweep.grid() if c["m"] == 10]
        assert len(cells) == 4 * 3 * 2 * 2
        for cell in cells:
            record = envelope_sweep.random_kb(
                cell["m"],
                cell["k"],
                cell["n_edge_labels"],
                cell["n_vertex_labels"],
                cell["density"],
                0,
            )
            assert record.n == cell["n"]
            assert record.m == cell["m"]
            assert record.is_connected()

    def test_the_infeasibility_guard_still_fires(self, monkeypatch) -> None:
        # Unreachable through grid() now that the sparse target is capped; the
        # guard protects a caller that widens the rule again.
        monkeypatch.setattr(envelope_sweep, "constants_for", lambda m, k, density: 99)
        with pytest.raises(KBGenerationError, match="spans at most"):
            envelope_sweep.random_kb(10, 2, 1, 1, "sparse", 0)

    def test_unknown_density_raises(self) -> None:
        with pytest.raises(KBGenerationError, match="unknown density"):
            envelope_sweep.is_feasible(10, 2, "medium")


class TestSyntheticRQ1:
    def test_small_corpus_is_deterministic_and_in_range(self) -> None:
        first = synthetic_rq1.corpus(40, seed=1)
        second = synthetic_rq1.corpus(40, seed=1)
        assert len(first) == 40
        assert keys(list(first.records)) == keys(list(second.records))
        assert synthetic_rq1.corpus(40, seed=2).records[0].key() != first.records[0].key()
        for record in first.records:
            assert 6 <= record.n <= 16
            assert 6 <= record.m <= 20
            assert 2 <= record.max_arity <= 4
            assert record.is_connected()
            assert max(record.types) < 3
        assert first.type_names == ("t0", "t1", "t2")
        assert first.pred_names == ("p0", "p1", "p2")
