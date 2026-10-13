"""Tests of the generation benchmark on usable samples (scripts/newpos/genbench)."""

from __future__ import annotations

import gzip
import math
import random
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.newpos.genbench import analyze as an  # noqa: E402
from scripts.newpos.genbench import common as gb  # noqa: E402
from scripts.newpos.genbench import evaluate as ev  # noqa: E402

pytestmark = pytest.mark.unit

needs_corpus = pytest.mark.skipif(
    not (gb.CORPUS_ROOT / "corpora").exists(), reason="frozen TKDE corpora not available"
)

# Hand-made collection (one type, two predicates): a 2-fact path, a triangle, a hyperedge chain.
PATH3: gb.KB = (3, (0, 0, 0), ((0, (0, 1)), (0, (1, 2))))
TRIANGLE: gb.KB = (3, (0, 0, 0), ((0, (0, 1)), (0, (1, 2)), (0, (0, 2))))
CHAIN: gb.KB = (4, (0, 0, 0, 0), ((0, (0, 1, 2)), (0, (2, 3))))
MEMBERS = [PATH3, TRIANGLE, CHAIN]
# Isomorphic relabelling of PATH3 (centre is constant 2).
PATH3_RELABELLED: gb.KB = (3, (0, 0, 0), ((0, (0, 2)), (0, (1, 2))))
STAR4: gb.KB = (5, (0,) * 5, tuple((0, (0, k)) for k in range(1, 5)))
STAR4_RELABELLED: gb.KB = (5, (0,) * 5, ((0, (0, 3)), (0, (1, 3)), (0, (2, 3)), (0, (3, 4))))
DISCONNECTED: gb.KB = (4, (0,) * 4, ((0, (0, 1)), (0, (2, 3))))
LONE: gb.KB = (1, (0,), ())


def draw(index: int, kb: gb.KB | None, flag: bool | None = None) -> gb.Draw:
    """A parsed draw for ``kb`` (``None`` means rejected)."""
    if kb is None:
        return gb.Draw(index, "rejected", "arity", None, None)
    return gb.Draw(index, "decoded", None, kb, flag)


@pytest.fixture(scope="module")
def ctx() -> ev.EvalContext:
    return ev.EvalContext.from_kbs("toy", MEMBERS, n_types=1, n_preds=2)


def random_kb(rng: random.Random) -> gb.KB:
    n = rng.randint(1, 7)
    facts: list[gb.Fact] = []
    for _ in range(rng.randint(0, 6)):
        size = rng.randint(1, min(3, n))
        facts.append((rng.randint(0, 1), tuple(sorted(rng.sample(range(n), size)))))
    types = tuple(rng.randint(0, 2) for _ in range(n))
    return n, types, gb.normalize_facts(facts)


# ---------------------------------------------------------------------------
# Structure predicates
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("n", "facts", "star"),
    [
        (4, ((0, (0, 1)), (0, (0, 2)), (0, (0, 3))), True),  # centre 0 in every fact
        (2, ((0, (0, 1)),), True),  # a one-fact KB is a star
        (3, ((0, (0, 1)), (0, (1, 2))), True),  # two facts sharing one constant
        (4, ((0, (0, 1)), (0, (1, 2)), (0, (2, 3))), False),  # path of three: no centre
        (3, ((0, (0, 1)), (0, (1, 2)), (0, (0, 2))), False),  # triangle
        (4, ((0, (0, 1, 2)), (1, (0, 1, 3))), False),  # two constants occur twice
        (5, ((0, (0, 1, 2)), (1, (0, 3, 4))), True),  # hyperedge star
        (1, (), False),  # no fact, no star
    ],
)
def test_star_classification(n: int, facts: tuple[gb.Fact, ...], star: bool) -> None:
    assert gb.is_star(n, facts) is star


def test_shared_constants_counts_constants_in_two_or_more_facts() -> None:
    assert gb.n_shared(TRIANGLE[0], TRIANGLE[2]) == 3
    assert gb.n_shared(PATH3[0], PATH3[2]) == 1
    assert gb.n_shared(STAR4[0], STAR4[2]) == 1


@pytest.mark.parametrize("seed", range(40))
def test_connectivity_matches_sparse_hypergraph(seed: int) -> None:
    kb = random_kb(random.Random(seed))
    H = gb.to_hypergraph(kb, 3, 2)
    assert gb.is_connected(kb[0], kb[2]) == H.is_connected()


def test_usable_requires_connected_and_a_fact() -> None:
    assert gb.is_usable(PATH3)
    assert not gb.is_usable(DISCONNECTED)
    assert not gb.is_usable(LONE)  # connected by convention but has no fact


# ---------------------------------------------------------------------------
# Profiles and distances agree with the library
# ---------------------------------------------------------------------------


def test_sample_set_profile_matches_library_profile() -> None:
    from isalhg.generation.fidelity import profile

    kbs = [random_kb(random.Random(s)) for s in range(60)]
    mine = gb.SampleSet.from_kbs(kbs).profile()
    theirs = profile([gb.to_hypergraph(kb, 3, 2) for kb in kbs])
    for key in gb.PROFILE_KEYS:
        length = max(len(mine[key]), len(theirs[key]))
        a, b = np.zeros(length), np.zeros(length)
        a[: len(mine[key])], b[: len(theirs[key])] = mine[key], theirs[key]
        np.testing.assert_allclose(a, b, atol=1e-12, err_msg=key)


def test_jsd_profiles_match_library_fidelity() -> None:
    from isalhg.generation.fidelity import fidelity

    a = [random_kb(random.Random(s)) for s in range(50)]
    b = [random_kb(random.Random(1000 + s)) for s in range(50)]
    mine = gb.jsd_profiles(gb.SampleSet.from_kbs(a).profile(), gb.SampleSet.from_kbs(b).profile())
    theirs = fidelity(
        [gb.to_hypergraph(kb, 3, 2) for kb in a], [gb.to_hypergraph(kb, 3, 2) for kb in b]
    )
    for key in gb.PROFILE_KEYS:
        assert mine[key] == pytest.approx(theirs[f"jsd_{key}"], abs=1e-12)


def test_take_preserves_profile_and_order() -> None:
    kbs = [random_kb(random.Random(s)) for s in range(30)]
    full = gb.SampleSet.from_kbs(kbs)
    idx = np.array([5, 5, 0, 29, 12])
    sub = full.take(idx)
    expected = gb.SampleSet.from_kbs([kbs[i] for i in idx])
    for name in ("n", "m", "star", "shared", "fact_ptr", "arity", "pred", "node_ptr", "vtype"):
        np.testing.assert_array_equal(getattr(sub, name), getattr(expected, name), err_msg=name)


def test_w1_of_identical_and_shifted_histograms() -> None:
    p = np.array([0.0, 1.0, 0.0])
    assert gb.w1(p, p) == 0.0
    assert gb.w1(p, np.array([0.0, 0.0, 1.0])) == pytest.approx(1.0)
    assert math.isnan(gb.w1(np.zeros(2), p))


# ---------------------------------------------------------------------------
# The frozen JSONL contract
# ---------------------------------------------------------------------------


def test_draw_line_roundtrip_plain_and_gzip(tmp_path: Path) -> None:
    lines = [
        gb.draw_line(
            collection="toy",
            generator="g",
            seed=1,
            draw=0,
            tokens=["a", "b"],
            root_type=0,
            status="decoded",
            reason=None,
            kb=PATH3,
            connected=True,
        ),
        gb.draw_line(
            collection="toy",
            generator="g",
            seed=1,
            draw=1,
            tokens=["c"],
            root_type=None,
            status="rejected",
            reason="arity",
            kb=None,
            connected=None,
        ),
    ]
    for name, opener in (("toy__g__s1.jsonl", open), ("toy__g__s2.jsonl.gz", gzip.open)):
        with opener(tmp_path / name, "wt", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")
        draws = list(gb.read_draws(tmp_path / name))
        assert [d.status for d in draws] == ["decoded", "rejected"]
        assert draws[0].kb == PATH3 and draws[0].tokens == ("a", "b") and draws[1].reason == "arity"
    found = gb.scan_directory(tmp_path, "toy")
    assert [(f.generator, f.seed) for f in found] == [("g", 1), ("g", 2)]
    assert gb.scan_directory(tmp_path, "other") == []


@pytest.mark.parametrize(
    "line",
    [
        "not json",
        '{"draw": 0}',
        '{"draw": 0, "status": "weird"}',
        '{"draw": 0, "status": "decoded", "n": 2, "types": [0], "facts": []}',
        '{"draw": 0, "status": "decoded", "n": 2, "types": [0, 0], "facts": [[0, [0, 5]]]}',
    ],
)
def test_malformed_lines_are_rejected(line: str) -> None:
    with pytest.raises(gb.SampleFileError):
        gb.parse_draw(line)


# ---------------------------------------------------------------------------
# The unit evaluator on a hand-made sample
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def toy_unit(ctx: ev.EvalContext) -> tuple[dict, gb.SampleSet]:
    draws = [
        draw(0, PATH3),  # in the collection
        draw(1, PATH3_RELABELLED),  # same isomorphism class as draw 0
        draw(2, STAR4),  # new class
        draw(3, STAR4_RELABELLED),  # same new class
        draw(4, DISCONNECTED),  # decoded, outside the domain
        draw(5, LONE),  # connected by convention, no fact
        draw(6, None),  # rejected
    ]
    return ev.evaluate_unit(ctx, "toy_gen", 7, draws)


def test_evaluator_counts(toy_unit: tuple[dict, gb.SampleSet]) -> None:
    row, usable = toy_unit
    assert (row["n_draws"], row["n_decoded"], row["n_rejected"]) == (7, 6, 1)
    assert row["n_connected"] == 5  # draws 0, 1, 2, 3 and the lone constant (RQ6's definition)
    assert row["n_empty"] == 1
    assert row["n_usable"] == len(usable) == 4
    assert row["connectivity"] == pytest.approx(5 / 6)
    assert row["validity"] == pytest.approx(6 / 7)


def test_uniqueness_and_novelty_are_keyed_by_isomorphism_class(
    toy_unit: tuple[dict, gb.SampleSet],
) -> None:
    row, _ = toy_unit
    assert row["n_unique_usable"] == 2  # {path3 class, star4 class}
    assert row["n_novel_usable"] == 2  # both star4 draws, counted with multiplicity
    assert row["n_unique_novel_usable"] == 1
    assert row["n_singleton_novel_usable"] == 0  # the novel class occurs twice
    assert row["vun_per_draw"] == pytest.approx(1 / 7)
    assert row["vun_singleton_per_draw"] == 0.0
    assert row["n_key_error"] == 0


def test_usable_set_excludes_disconnected_and_empty(toy_unit: tuple[dict, gb.SampleSet]) -> None:
    _, usable = toy_unit
    assert sorted(usable.n.tolist()) == [3, 3, 5, 5]
    assert usable.m.tolist() == [2, 2, 4, 4]
    assert usable.star.tolist() == [
        True,
        True,
        True,
        True,
    ]  # a 2-fact path and a 4-leaf star are both stars


@pytest.mark.parametrize(
    ("kb", "inside"),
    [
        (PATH3, False),  # m = 2 < 3
        (STAR4, True),
        (TRIANGLE, True),
        ((25, (0,) * 25, tuple((0, (0, k)) for k in range(1, 25))), False),  # n = 25 > 24
        (
            (12, (0,) * 12, tuple((0, (0, k)) for k in range(1, 12)) + ((1, tuple(range(10))),)),
            True,
        ),
        (
            (12, (0,) * 12, tuple((0, (0, k)) for k in range(1, 12)) + ((1, tuple(range(12))),)),
            False,
        ),
    ],
)
def test_envelope_membership(kb: gb.KB, inside: bool) -> None:
    assert gb.in_envelope(kb) is inside  # arity 12 > 10 is the last case


def test_posthoc_envelope_columns(toy_unit: tuple[dict, gb.SampleSet]) -> None:
    row, _ = toy_unit
    assert row["n_usable_inenv"] == 2  # only the two 4-leaf stars; the 2-fact paths have m < 3
    assert row["n_unique_novel_inenv"] == 1
    assert row["vun_inenv_per_draw"] == pytest.approx(1 / 7)


def test_fidelity_is_withheld_below_min_usable(toy_unit: tuple[dict, gb.SampleSet]) -> None:
    row, _ = toy_unit
    assert row["fidelity_ok"] == 0
    assert all(math.isnan(row[f"jsd_{k}_use"]) for k in gb.PROFILE_KEYS)
    assert math.isnan(row["mean_m_use"])
    assert not math.isnan(row["jsd_n_all"])  # the all-decoded view (RQ6's) is still reported


def test_fidelity_is_computed_from_min_usable(ctx: ev.EvalContext) -> None:
    draws = [draw(i, MEMBERS[i % 3]) for i in range(gb.MIN_USABLE)]
    row, usable = ev.evaluate_unit(ctx, "toy_gen", 0, draws)
    assert row["fidelity_ok"] == 1 and len(usable) == gb.MIN_USABLE
    assert row["jsd_m_use"] < 0.01  # a resample of the members is close to them
    assert row["coll_star_frac"] == pytest.approx(2 / 3)  # triangle is the only non-star
    assert row["n_unique_novel_usable"] == 0 and row["vun_per_draw"] == 0.0


def test_connected_flag_is_audited_not_trusted(ctx: ev.EvalContext) -> None:
    row, _ = ev.evaluate_unit(
        ctx, "toy_gen", 0, [draw(0, DISCONNECTED, flag=True), draw(1, PATH3, flag=True)]
    )
    assert row["n_flag_mismatch"] == 1
    assert row["n_connected"] == 1


def test_evaluator_reads_any_generator_name_from_files(tmp_path: Path, ctx: ev.EvalContext) -> None:
    path = tmp_path / "toy__gru_ow__s3.jsonl"
    path.write_text(
        gb.draw_line(
            collection="toy",
            generator="gru_ow",
            seed=3,
            draw=0,
            tokens=[],
            root_type=0,
            status="decoded",
            reason=None,
            kb=STAR4,
            connected=True,
        )
        + "\n"
    )
    (unit,) = gb.scan_directory(tmp_path, "toy")
    row, _ = ev.evaluate_unit(ctx, unit.generator, unit.seed, gb.read_draws(unit.path))
    assert (row["generator"], row["seed"], row["n_usable"]) == ("gru_ow", 3, 1)


# ---------------------------------------------------------------------------
# The largest-connected-component repair
# ---------------------------------------------------------------------------


def test_lcc_keeps_the_component_with_most_constants() -> None:
    # Components {0,1,2} (two facts), {3,4} (one fact), isolated {5}; one type per constant.
    kb: gb.KB = (6, (0, 1, 2, 3, 4, 5), ((0, (0, 1)), (1, (1, 2)), (0, (3, 4))))
    fixed = gb.repair_lcc(kb, n_types=6, n_preds=2)
    assert fixed.kb == (3, (0, 1, 2), ((0, (0, 1)), (1, (1, 2))))
    assert fixed.n_components == 3 and not fixed.rule_disagree


def test_lcc_renumbers_constants_and_keeps_types() -> None:
    kb: gb.KB = (5, (0, 0, 1, 2, 0), ((0, (0, 1)), (0, (2, 3)), (1, (3, 4)), (0, (2, 4))))
    fixed = gb.repair_lcc(kb, n_types=3, n_preds=2)
    assert fixed.kb == (3, (1, 2, 0), ((0, (0, 1)), (0, (0, 2)), (1, (1, 2))))


def test_lcc_tie_goes_to_more_facts_then_lowest_word() -> None:
    # Same constants (3 each); the second component has more facts.
    kb: gb.KB = (6, (0,) * 6, ((0, (0, 1)), (0, (1, 2)), (0, (3, 4)), (0, (4, 5)), (0, (3, 5))))
    assert gb.repair_lcc(kb, 1, 2).kb == (3, (0, 0, 0), ((0, (0, 1)), (0, (0, 2)), (0, (1, 2))))
    # Full tie in (constants, facts): the component with the lowest (root type, word) wins.
    tied: gb.KB = (4, (0,) * 4, ((0, (0, 1)), (1, (2, 3))))
    kept = gb.repair_lcc(tied, 1, 2).kb
    candidates = [(0, (0, 1)), (1, (0, 1))]
    best = min(candidates, key=lambda fact: gb.iso_key((2, (0, 0), (fact,)), 1, 2))
    assert kept == (2, (0, 0), (best,))


def test_lcc_rule_disagreement_is_flagged() -> None:
    wide = tuple((p, (0, 1)) for p in range(4))  # 2 constants, 4 facts (distinct predicates)
    tall = ((0, (2, 3)), (0, (3, 4)), (0, (4, 5)))  # 4 constants, 3 facts
    kb: gb.KB = (6, (0,) * 6, wide + tall)
    fixed = gb.repair_lcc(kb, 1, 4)
    assert fixed.kb[0] == 4  # constants first
    assert fixed.rule_disagree  # a facts-first reading would have kept the other component


def test_connected_kb_is_left_untouched() -> None:
    fixed = gb.repair_lcc(TRIANGLE, 1, 2)
    assert fixed.kb == TRIANGLE and fixed.n_components == 1


def test_repair_arm_is_always_usable(ctx: ev.EvalContext) -> None:
    draws = [draw(0, DISCONNECTED), draw(1, PATH3), draw(2, LONE)]
    row, usable = ev.evaluate_unit(ctx, "toy_gen_lcc", 0, draws, repair=True)
    assert row["n_connected"] == row["n_decoded"] == 3
    assert (
        row["n_usable"] == len(usable) == 2
    )  # the lone constant has no fact and is still out of domain
    assert row["n_empty"] == 1


# ---------------------------------------------------------------------------
# Matched comparison, tests and verdicts
# ---------------------------------------------------------------------------


def test_matched_averaging_is_deterministic_and_full_set_is_exact() -> None:
    rng = random.Random(0)
    sample = gb.SampleSet.from_kbs([random_kb(rng) for _ in range(300)])
    ref = gb.SampleSet.from_kbs([random_kb(rng) for _ in range(300)])
    profile = ref.profile()
    first = an._averaged(sample, 120, ref, profile, ("a", 1))
    second = an._averaged(sample, 120, ref, profile, ("a", 1))
    assert first == second
    other = an._averaged(sample, 120, ref, profile, ("a", 2))
    assert first["jsd_m"] != other["jsd_m"]
    assert an._averaged(sample, 300, ref, profile, ("a", 1)) == gb.set_metrics(sample, ref, profile)


def _cell(base: float, ours: float, n: int = 15) -> dict:
    metrics = {k: 0.0 for k in (*an.HA1_METRICS, an.HA2_METRIC)}
    return {
        "seeds": list(range(n)),
        "per_seed": [
            {
                "size": 500,
                "base": {**metrics, "jsd_m": base + 0.001 * i},
                "ours": {**metrics, "jsd_m": ours},
                "ideal": {**metrics},
            }
            for i in range(n)
        ],
    }


def test_test_rows_orientation_and_holm() -> None:
    worse = an.test_rows("c", "b", "u_b", _cell(0.2, 0.1), ("jsd_m",), 15, 500.0)
    an.apply_holm(worse, "family")
    assert (
        worse[0]["testable"]
        and worse[0]["reject"]
        and worse[0]["rank_biserial"] == pytest.approx(1.0)
    )
    better = an.test_rows("c", "b", "u_b", _cell(0.1, 0.2), ("jsd_m",), 15, 500.0)
    an.apply_holm(better, "family")
    assert not better[0]["reject"] and better[0]["rank_biserial"] == pytest.approx(-1.0)


def test_cell_with_too_few_seeds_is_untestable() -> None:
    (row,) = an.test_rows(
        "c", "b", "u_b", _cell(0.2, 0.1, n=gb.MIN_VALID_SEEDS - 1), ("jsd_m",), 27, 40.0
    )
    assert not row["testable"] and "p_raw" not in row


def test_ha1_verdict_requires_direction() -> None:
    reject = [{"testable": True, "reject": True} for _ in range(3)]

    def direction(sign_ok: bool) -> dict:
        cell = {"ci_on_predicted_side": sign_ok}
        return {"n_valid_seeds": 27, "mean_n": cell, "mean_m": cell, "star_frac": cell}

    assert an.ha1_verdict(reject, direction(True)) == "SUPPORTED"
    assert an.ha1_verdict(reject, direction(False)) == "WRONG-DIRECTION"
    assert (
        an.ha1_verdict([{"testable": True, "reject": False}] * 3, direction(True))
        == "NOT SUPPORTED"
    )
    assert an.ha1_verdict([{"testable": False}] * 3, direction(True)) == "INSUFFICIENT"


# ---------------------------------------------------------------------------
# Against the real campaign (needs the frozen corpora and the C++ engine)
# ---------------------------------------------------------------------------


@needs_corpus
@pytest.mark.parametrize(("name", "star"), [("wd50k66", 0.534), ("ndc_classes", 0.030)])
def test_collection_star_fractions_match_the_brief(name: str, star: float) -> None:
    context = ev.EvalContext.from_collection(name)
    assert float(context.reference.star.mean()) == pytest.approx(star, abs=5e-4)


@needs_corpus
@pytest.mark.parametrize("kind", ["ow_ngram", "fact_ngram", "incidence_ngram"])
def test_sampler_reproduces_rq6_validity_and_connectivity(kind: str) -> None:
    from experiments.tkde import rq6
    from scripts.newpos.genbench import sample_ngram as sn

    config = sn.rq6_config()
    seed = sn.rq6_seeds(config)[0]
    assert seed == 60000
    context = rq6.build_context("ndc_classes", config, gb.CORPUS_ROOT)
    n_samples = 500
    unit = rq6.SampleUnit("ndc_classes", kind, seed)
    row, _ = rq6.run_sample_unit(
        unit,
        {"n_samples": n_samples, "reach1_subset": 0, "max_len": gb.MAX_LEN},
        context,
        rq6.Reach1Index([]),
        {},
    )
    records = list(sn.sample_unit(context, kind, seed, n_samples, gb.MAX_LEN))
    decoded = [r for r in records if r["status"] == "decoded"]
    assert len(records) == n_samples
    assert len(decoded) == row["n_valid"]
    assert sum(1 for r in decoded if r["connected"]) == row["n_connected"]
    # The evaluator recomputes the same connectivity from n/types/facts alone.
    parsed = [
        gb.parse_draw(
            gb.draw_line(
                **{
                    k: r[k]
                    for k in (
                        "collection",
                        "generator",
                        "seed",
                        "draw",
                        "tokens",
                        "root_type",
                        "status",
                        "reason",
                    )
                },
                kb=None
                if r["n"] is None
                else (r["n"], tuple(r["types"]), gb.normalize_facts(r["facts"])),
                connected=r["connected"],
            )
        )
        for r in records
    ]
    assert (
        sum(1 for d in parsed if d.kb and gb.is_connected(d.kb[0], d.kb[2])) == row["n_connected"]
    )
