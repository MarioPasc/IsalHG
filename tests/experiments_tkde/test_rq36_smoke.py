"""Unit tests for the RQ3 and RQ6 runners and their analyzers.

The load-bearing test is the RQ3 evaluation axis on a hand-built collection
whose answer is known by construction: the source is one fact-token insertion
away from every member, so a method that returns the source scores 0 and a
method that can only return an input scores exactly ``t``. Everything else here
guards the mechanics that silently produce plausible-but-wrong campaigns: the
shard partition, the process-level budget guard, the reach-1 index, and the
analyzers' ability to run on partial rows.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import pytest

from experiments.tkde import analyze_rq3, analyze_rq6, rq3, rq6
from experiments.tkde.config import TkdeConfigError
from isalhg.datasets.kb.base import make_record
from isalhg.generation.incidence_baseline import flatten
from isalhg.language.consensus import coverage_consensus
from isalhg.language.reach import reach
from isalhg.metric_space.distances.fact_levenshtein import fact_word
from isalhg.metric_space.toolkit.matrix import build_matrix
from isalhg.metric_space.toolkit.medoid import medoid

pytestmark = pytest.mark.unit

N_TYPES = 1
N_PREDS = 1
SOURCE_FACTS = ((0, (0, 1)), (0, (1, 2)), (0, (2, 3)))
INSERTIONS = ((0, (0, 2)), (0, (0, 3)), (0, (0, 1, 2)), (0, (0, 1, 2, 3)))
IDENTITIES = ("a", "b", "c", "d")


def _run_rq3(arguments: list[str]) -> None:
    """Run the RQ3 runner in a child process, as one SLURM shard does.

    Since D-KBf1 the medoid screens its members for the engine arms, and that
    screen forks. A process that has already canonicalized in the C++ engine
    forks children that deadlock, so the screen's canary refuses rather than
    report a censoring that never happened -- and an in-process ``rq3.main``
    inherits whatever an earlier test in the session did to this interpreter.
    The campaign never has that problem because every shard is a fresh process;
    this makes the test model the campaign rather than weaken the guard.
    """
    completed = subprocess.run(
        [sys.executable, "-m", "experiments.tkde.rq3", *arguments],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr[-4000:]


def _record(kb_id: str, facts: tuple[tuple[int, tuple[int, ...]], ...], n: int = 4):
    record = make_record(
        kb_id,
        n,
        (0,) * n,
        facts,
        constant_ids=tuple(f"c{index}" for index in range(n)) if n != 4 else IDENTITIES,
        meta={"n_types": N_TYPES, "n_preds": N_PREDS},
    )
    assert record is not None, f"{kb_id} was rejected by the record contract"
    return record


@pytest.fixture
def source():
    """A four-constant path of three binary facts, with external identities."""
    return _record("source", SOURCE_FACTS)


@pytest.fixture
def members(source):
    """Four pairwise non-isomorphic members, each one insertion away from the source."""
    built = [
        _record(f"member{index}", (*SOURCE_FACTS, extra)) for index, extra in enumerate(INSERTIONS)
    ]
    keys = {fact_word(record.to_hypergraph()) for record in built}
    assert len(keys) == len(built), "the fixture members are not pairwise non-isomorphic"
    assert fact_word(source.to_hypergraph()) not in keys
    return built


class TestIdentityEvaluation:
    """The RQ3 axis: exact fact-level distance under constant identities."""

    def test_every_member_is_exactly_t_from_the_source(self, source, members):
        truth = rq3.identity_facts_of_record(source)
        for member in members:
            distance = rq3.fact_distance(rq3.identity_facts_of_record(member), truth)
            assert distance == 1

    def test_the_source_scores_zero_against_itself(self, source):
        truth = rq3.identity_facts_of_record(source)
        assert rq3.fact_distance(truth, truth) == 0

    def test_the_coverage_consensus_recovers_the_source(self, source, members):
        hypergraphs = [record.to_hypergraph() for record in members]
        identities = [rq3.identity_ids(record) for record in members]
        outcome = rq3.consensus_outcome(
            hypergraphs, identities, rq3.identity_facts_of_record(source), r=2
        )
        assert outcome.fact_dist == 0
        assert outcome.coverage == len(members)
        assert outcome.n_candidates > len(members)

    def test_majority_merge_recovers_the_source(self, source, members):
        hypergraphs = [record.to_hypergraph() for record in members]
        identities = [rq3.identity_ids(record) for record in members]
        distance = rq3.majority_outcome(
            hypergraphs, identities, rq3.identity_facts_of_record(source)
        )
        assert distance == 0

    def test_the_medoid_returns_an_input_and_so_scores_t(self, source, members):
        hypergraphs = [record.to_hypergraph() for record in members]
        matrix = build_matrix(
            hypergraphs,
            "fact_rank",
            member_ids=[record.kb_id for record in members],
            cache_dir=None,
        )
        result = medoid(matrix.astype("float64"))
        distance = rq3.fact_distance(
            rq3.identity_facts_of_record(members[result.index]),
            rq3.identity_facts_of_record(source),
        )
        assert distance == 1
        assert result.lower_bound <= result.cost + rq3.ZERO_TOLERANCE
        assert result.ratio <= 2.0 - 2.0 / len(members) + rq3.ZERO_TOLERANCE

    def test_the_node_map_is_honoured(self, source):
        """A candidate expressed under a permutation must still read its own identities."""
        H = source.to_hypergraph()
        straight = rq3.identity_facts_of_hypergraph(H, IDENTITIES)
        assert straight == rq3.identity_facts_of_record(source)
        # The path 0-1-2-3 is symmetric under reversal, so the permutation has to
        # be one the fact set does not absorb, or the test asserts nothing.
        swap = (1, 0, 2, 3)
        shifted = rq3.identity_facts_of_hypergraph(H, IDENTITIES, node_map=swap)
        assert shifted != straight
        assert shifted == frozenset(
            (pred, frozenset(IDENTITIES[swap[v]] for v in operands))
            for pred, operands in SOURCE_FACTS
        )

    def test_the_consensus_output_is_read_through_its_anchor(self, source, members):
        """``node_map`` and ``anchor`` together define the identity space of the output."""
        hypergraphs = [record.to_hypergraph() for record in members]
        result = coverage_consensus(hypergraphs, 2)
        identities = rq3.identity_ids(members[result.anchor])
        out = rq3.identity_facts_of_hypergraph(result.kb, identities, result.node_map)
        assert out == rq3.identity_facts_of_record(source)


class TestBudgetGuard:
    """The process-level guard the pointer alphabet and the natural series need."""

    def test_a_value_comes_back(self):
        status, value = rq3.run_guarded(lambda: 6 * 7, 30.0)
        assert (status, value) == ("ok", 42)

    def test_an_overrun_is_killed_and_reported(self):
        started = time.perf_counter()
        status, _ = rq3.run_guarded(lambda: time.sleep(30), 0.5)
        assert status == "timeout"
        assert time.perf_counter() - started < 20.0

    def test_a_failure_is_reported_not_raised(self):
        status, message = rq3.run_guarded(lambda: 1 / 0, 30.0)
        assert status == "error"
        assert "ZeroDivisionError" in message


class TestUnitEnumeration:
    """A shard partition that drops or duplicates a unit is a silent wrong campaign."""

    @staticmethod
    def _config() -> dict:
        return {
            "seed_count": 3,
            "corpus_a": {
                "collections": ["ndc_classes", "wd50k66"],
                "n_values": [5, 9],
                "t_values": [1, 2],
                "kinds": ["ins", "del", "mix"],
                "sources_per_cell": 8,
                "source_window": {},
            },
        }

    def test_corpus_a_enumerates_every_cell_and_seed(self):
        units = rq3.enumerate_units_a(self._config())
        assert len(units) == 2 * 2 * 2 * 3 * 3
        assert len({unit.key for unit in units}) == len(units)

    @pytest.mark.parametrize("count", [1, 3, 7])
    def test_the_shard_partition_is_exact(self, count):
        units = rq3.enumerate_units_a(self._config())
        seen: list[str] = []
        for index in range(1, count + 1):
            seen.extend(u.key for i, u in enumerate(units) if i % count == index - 1)
        assert sorted(seen) == sorted(unit.key for unit in units)

    @pytest.mark.parametrize("text", ["0/4", "5/4", "x/4", "3"])
    def test_a_bad_shard_is_refused(self, text):
        with pytest.raises(TkdeConfigError):
            rq3._parse_shard(text)

    def test_rq6_units_are_unique(self):
        config = {
            "seed_count": 4,
            "collections": ["wd50k66", "ndc_classes"],
            "alignment": {"collections": ["wd50k66"]},
            "completion": {"n_seeds": 2},
        }
        units = rq6.enumerate_units(config)
        assert len(units) == 2 * 2 * 4 + 1 + 2 * 2
        assert len({unit.key for unit in units}) == len(units)


class TestSourcePool:
    """Deletion-only cells need m >= N + 1, or the cell is structurally empty."""

    WINDOW = {"n_min": 4, "n_max": 12, "m_min": 4, "m_max": 12, "max_arity": 6}

    @pytest.mark.parametrize("kind", ["ins", "mix"])
    def test_the_frozen_window_is_untouched_for_insertions(self, kind):
        assert rq3.cell_source_window(self.WINDOW, kind, 9) == self.WINDOW

    @pytest.mark.parametrize(("n_members", "expected"), [(5, 6), (9, 10), (2, 4)])
    def test_deletion_cells_raise_the_fact_floor(self, n_members, expected):
        window = rq3.cell_source_window(self.WINDOW, "del", n_members)
        assert window["m_min"] == expected
        assert window["m_max"] == self.WINDOW["m_max"]
        assert window["n_min"] == self.WINDOW["n_min"]

    def test_the_tightened_window_selects_only_large_enough_sources(self):
        from isalhg.datasets.kb.base import KBCollection

        small = _record("small", SOURCE_FACTS)
        big = _record("big", (*SOURCE_FACTS, *INSERTIONS))
        collection = KBCollection(
            name="fixture",
            records=(small, big),
            type_names=("t",),
            pred_names=("p",),
        )
        assert big.m >= 6 > small.m
        window = rq3.cell_source_window(self.WINDOW, "del", 5)
        pool = rq3.eligible_sources(collection, window)
        assert [record.kb_id for record in pool] == ["big"]

    @pytest.mark.parametrize(
        ("size", "expected"), [(0, "infeasible"), (3, "pool_limited"), (8, "ok"), (99, "ok")]
    )
    def test_pool_status(self, size, expected):
        assert rq3.pool_status(size, 8) == expected


class TestReach1Index:
    """The RQ6 neighbourhood index must agree with ``reach`` and honour its precondition."""

    def test_a_single_insertion_is_within_reach_one(self, source, members):
        index = rq6.Reach1Index([record.to_hypergraph() for record in members])
        assert index.within_one(source.to_hypergraph()) is True

    def test_a_member_is_within_reach_of_itself(self, members):
        hypergraphs = [record.to_hypergraph() for record in members]
        index = rq6.Reach1Index(hypergraphs)
        assert index.within_one(hypergraphs[0]) is True

    def test_a_different_constant_count_does_not_decide_the_answer(self, members):
        """A differing constant count must not short-circuit the index (T-KBo).

        This test previously asserted ``is None`` here, encoding the *frozen*
        reach precondition: equal constant count plus type multiset. Under
        ``reach'`` (D-KBf5) a deletion compacts away constants it isolates, so
        the count is not preserved across a reach-1 step and that gate withheld
        exactly the pairs the definition admits.

        The contract is now stated against ``reach`` itself rather than against
        any gate, so it cannot go stale the same way again.
        """
        hypergraphs = [record.to_hypergraph() for record in members]
        index = rq6.Reach1Index(hypergraphs)
        other = _record(
            "wider", ((0, (0, 1)), (0, (1, 2)), (0, (2, 3)), (0, (3, 4))), n=5
        ).to_hypergraph()
        assert any(H.n_nodes != other.n_nodes for H in hypergraphs), (
            "the fixture must actually differ in constant count for this to test anything"
        )
        expected = any(reach(other, H, r_max=1) is not None for H in hypergraphs)
        answer = index.within_one(other)
        assert answer is expected or (answer is None and not expected), (
            f"index said {answer!r}; reach says a reach-1 member exists: {expected}"
        )

    def test_a_distant_knowledge_base_is_not_within_reach_one(self, members):
        index = rq6.Reach1Index([record.to_hypergraph() for record in members])
        star = _record("star", ((0, (0, 1)), (0, (0, 2)), (0, (0, 3)), (0, (1, 2, 3))))
        assert index.within_one(star.to_hypergraph()) is False


class TestModelIsNotSharedAcrossUnits:
    """``TokenNGram`` memoises a dense vocabulary vector per sampling context.

    That cache is unbounded and is reset only by ``fit``. Sharing one fitted
    model across the 27 seeds therefore grew RSS by about 2.7 GB per unit and
    killed job 2213221 at 20.4 GB after eight units. Each unit must get its own
    model so the cache dies with it.
    """

    @staticmethod
    def _context(members) -> rq6.CollectionContext:
        hypergraphs = [record.to_hypergraph() for record in members]
        return rq6.CollectionContext(
            name="probe",
            collection=None,  # type: ignore[arg-type]
            roles=False,
            hypergraphs=hypergraphs,
            member_ids=[f"m{i}" for i in range(len(hypergraphs))],
            words=[fact_word(H) for H in hypergraphs],
            keys=[fact_word(H) for H in hypergraphs],
            flat=[flatten(H) for H in hypergraphs],
            n_types=1,
            n_preds=1,
        )

    def test_each_call_returns_a_fresh_model(self, members):
        context = self._context(members)
        first = context.model(rq6.MODEL_OURS)
        second = context.model(rq6.MODEL_OURS)
        assert first is not second, "a shared model carries its memo cache across units"

    def test_the_fresh_model_samples_identically(self, members):
        """Refitting is a memory fix, not a change of measurement."""
        context = self._context(members)
        first = context.model(rq6.MODEL_OURS).sample(16, seed=7, max_len=40)
        second = context.model(rq6.MODEL_OURS).sample(16, seed=7, max_len=40)
        assert first == second

    def test_a_used_model_is_not_reachable_from_the_context(self, members):
        """No attribute may retain the model, or the cache outlives the unit."""
        context = self._context(members)
        model = context.model(rq6.MODEL_OURS)
        model.sample(8, seed=1, max_len=40)
        retained = [value for value in vars(context).values() if value is model]
        assert not retained


class TestAnalyzerLabels:
    """The analyzers name methods from the rows; a wrong label silently mixes arms."""

    @pytest.mark.parametrize(
        ("row", "expected"),
        [
            ({"method": "medoid", "arm": "netlsd", "radius": ""}, "medoid[netlsd]"),
            ({"method": "coverage", "arm": "fact_rank", "radius": "2"}, "coverage_r2"),
            # pandas types the column as float when every consensus row in a
            # partial file carries radius 2; a string comparison would then
            # mislabel the default radius on every row.
            ({"method": "coverage", "arm": "fact_rank", "radius": 2}, "coverage_r2"),
            ({"method": "coverage", "arm": "fact_rank", "radius": 2.0}, "coverage_r2"),
            ({"method": "coverage", "arm": "fact_rank", "radius": "2.0"}, "coverage_r2"),
            ({"method": "coverage", "arm": "fact_rank", "radius": "t"}, "coverage_rt"),
            ({"method": "majority_merge", "arm": "identities", "radius": ""}, "majority_merge"),
        ],
    )
    def test_method_label(self, row, expected):
        assert analyze_rq3.method_label(row) == expected

    def test_the_analyzers_survive_an_empty_root(self, tmp_path):
        assert analyze_rq3.main(["--root", str(tmp_path)]) == 1
        assert analyze_rq6.main(["--root", str(tmp_path)]) == 1


class TestSmokeIsolation:
    """Smoke rows carry the same unit ids as the real run and must never merge in."""

    def test_a_smoke_component_inside_the_root_is_skipped(self, tmp_path: Path):
        real = tmp_path / "RQ3_representative/corpus_a/parts/shard_001of001/rows_variants.csv"
        smoke = tmp_path / "RQ3_representative/_smoke/corpus_a/parts/s/rows_variants.csv"
        for path in (real, smoke):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
        assert analyze_rq3.is_smoke_path(real, tmp_path) is False
        assert analyze_rq3.is_smoke_path(smoke, tmp_path) is True

    def test_a_smoke_root_still_analyzes_itself(self, tmp_path: Path):
        """The test is on the path relative to the root, not on the absolute path."""
        root = tmp_path / "_smoke_rq3"
        rows = root / "RQ3_representative/corpus_a/parts/shard_001of001/rows_variants.csv"
        rows.parent.mkdir(parents=True, exist_ok=True)
        rows.touch()
        assert analyze_rq3.is_smoke_path(rows, root) is False

    def test_an_unrelated_path_is_not_smoke(self, tmp_path: Path):
        assert analyze_rq3.is_smoke_path(Path("/elsewhere/rows.csv"), tmp_path) is False


class TestDeployStamps:
    """A cluster manifest must name both trees, not only the runner's."""

    def test_the_stamps_name_the_imported_package(self):
        import isalhg

        stamps = rq3.deploy_stamps()
        assert set(stamps) == {"src_deploy", "runner_deploy", "isalhg_path"}
        assert stamps["isalhg_path"] == str(Path(isalhg.__file__).resolve())

    def test_a_missing_stamp_is_none_not_an_error(self, tmp_path: Path):
        assert rq3._read_stamp(tmp_path) is None

    def test_a_present_stamp_is_read_and_stripped(self, tmp_path: Path):
        (tmp_path / rq3.DEPLOY_STAMP).write_text("sha=abc branch=b\n", encoding="utf-8")
        assert rq3._read_stamp(tmp_path) == "sha=abc branch=b"


def _corpora_available() -> bool:
    from experiments.tkde import corpora

    try:
        names = corpora.available_collections()
    except OSError:
        return False
    return "ndc_classes" in names


@pytest.mark.skipif(not _corpora_available(), reason="frozen corpora are not on this machine")
class TestEndToEnd:
    """One tiny real run of each runner, then its analyzer, on the frozen corpora."""

    def test_rq3_smoke_and_analysis(self, tmp_path: Path):
        config = Path("experiments/tkde/configs/rq3.yaml")
        _run_rq3(["--config", str(config), "--out", str(tmp_path), "--smoke"])
        rows = tmp_path / "RQ3_representative/corpus_a/parts/shard_001of001/rows_variants.csv"
        assert rows.is_file()
        certificates = (
            tmp_path
            / "RQ2_wellposedness/certificate_validity/parts/shard_001of001/rows_certificate.csv"
        )
        assert certificates.is_file()
        assert analyze_rq3.main(["--root", str(tmp_path)]) == 0
        merged = tmp_path / "RQ2_wellposedness/certificate_validity/rows_certificate.csv"
        assert merged.is_file(), "RQ2's analyzer reads this exact path"
        assert (tmp_path / "RQ3_representative/corpus_a/tables.md").is_file()

    def test_rq3_is_idempotent_per_unit(self, tmp_path: Path):
        config = Path("experiments/tkde/configs/rq3.yaml")
        arguments = ["--config", str(config), "--out", str(tmp_path), "--smoke"]
        _run_rq3(arguments)
        rows = tmp_path / "RQ3_representative/corpus_a/parts/shard_001of001/rows_variants.csv"
        first = rows.read_text(encoding="utf-8")
        _run_rq3(arguments)
        assert rows.read_text(encoding="utf-8") == first

    def test_rq6_smoke_and_analysis(self, tmp_path: Path):
        config = tmp_path / "rq6_tiny.yaml"
        config.write_text(
            "\n".join(
                [
                    "rq: RQ6",
                    "seed_count: 1",
                    "collections: [ndc_classes]",
                    "roles: {ndc_classes: false}",
                    "n_samples: 50",
                    "max_len: 60",
                    "reach1_subset: 10",
                    "alignment:",
                    "  collections: [ndc_classes]",
                    "  n_pairs: 1",
                    "  member_window: {n_max: 8, m_max: 5}",
                    "  pointer_budget_s: 10",
                    "completion: {n_members: 3, n_seeds: 1}",
                ]
            ),
            encoding="utf-8",
        )
        assert rq6.main(["--config", str(config), "--out", str(tmp_path)]) == 0
        rows = tmp_path / "RQ6_generation/generation/parts/shard_001of001/rows_samples.csv"
        assert rows.is_file()
        assert analyze_rq6.main(["--root", str(tmp_path)]) == 0
        assert (tmp_path / "RQ6_generation/generation/tables.md").is_file()

    def test_validity_is_one_on_the_fact_alphabet(self, tmp_path: Path):
        """Prop 6 in the runner: every sampled fact word decodes."""
        import csv

        config = tmp_path / "rq6_validity.yaml"
        config.write_text(
            "\n".join(
                [
                    "rq: RQ6",
                    "seed_count: 1",
                    "collections: [ndc_classes]",
                    "roles: {ndc_classes: false}",
                    "n_samples: 500",
                    "max_len: 80",
                    "reach1_subset: 0",
                    "alignment: {collections: [], n_pairs: 0,"
                    " member_window: {n_max: 8, m_max: 5}, pointer_budget_s: 10}",
                    "completion: {n_members: 0, n_seeds: 0}",
                ]
            ),
            encoding="utf-8",
        )
        assert rq6.main(["--config", str(config), "--out", str(tmp_path)]) == 0
        path = tmp_path / "RQ6_generation/generation/parts/shard_001of001/rows_samples.csv"
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        ours = [row for row in rows if row["model"] == rq6.MODEL_OURS]
        assert ours, "the fact-alphabet unit did not run"
        for row in ours:
            assert int(row["n_valid"]) == int(row["n_samples"])
            assert float(row["validity"]) == 1.0
