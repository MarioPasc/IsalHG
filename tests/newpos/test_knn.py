"""Unit tests for the KNN_2026-10-15 library (scripts/newpos/knn/knn_lib.py)."""

from __future__ import annotations

import itertools
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "newpos" / "knn"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import design_c as DC  # noqa: E402, N812
import design_d as DD  # noqa: E402, N812
import rect as RECT  # noqa: E402, N812
from knn_lib import ARMS_C as K_ARMS_C  # noqa: E402
from knn_lib import (  # noqa: E402
    IsoKeys,
    brute_force_kmedoids,
    cell_seed,
    expected_accuracy,
    expected_macro_f1,
    knn_label_probs,
    lineages,
    loo_knn_probs,
    make_copies,
    mix_q,
    pam,
    removals,
    sample_copy,
    select_sources,
)

from isalhg.datasets.kb.base import KBCollection, KBRecord, make_record  # noqa: E402

pytestmark = pytest.mark.unit

N_TYPES, N_PREDS = 2, 4


def _record(kb_id: str, n: int, facts: list[tuple[int, tuple[int, ...]]], **meta) -> KBRecord:
    rec = make_record(
        kb_id,
        n,
        [i % N_TYPES for i in range(n)],
        facts,
        meta={"n_types": N_TYPES, "n_preds": N_PREDS, **meta},
        require_connected=True,
    )
    assert rec is not None
    return rec


@pytest.fixture
def source() -> KBRecord:
    # A relational core (0-1-2-3 cycle of binary facts, interior structure) with
    # pendant statements and a ternary fact carrying a qualifier value (7).
    return _record(
        "src",
        9,
        [
            (0, (0, 1)),
            (1, (1, 2)),
            (2, (2, 3)),
            (3, (0, 3)),
            (0, (0, 4)),
            (1, (1, 5)),
            (2, (2, 6, 7)),
            (3, (3, 8)),
        ],
    )


@pytest.fixture
def keys() -> IsoKeys:
    return IsoKeys(N_TYPES, N_PREDS)


# --------------------------------------------------------------------------- copies


def test_removals_flag_pendant_by_inventory(source: KBRecord) -> None:
    rems = removals(source)
    assert rems
    for rem in rems:
        assert rem.result.is_connected()
        assert rem.result.m >= 3
        assert (rem.result.n < source.n) == rem.pendant
    kinds = Counter((r.kind, r.pendant) for r in rems)
    # the four leaf statements (one ternary) are pendant deletions; the cycle edges are interior
    assert kinds[("delete_fact", True)] == 4
    assert kinds[("delete_fact", False)] == 4
    # 6 and 7 occur only in the ternary fact: pendant removals. Removing 2 from it
    # would be interior but strands {6, 7}, so it is rejected.
    assert kinds[("remove_constant", True)] == 2
    assert kinds[("remove_constant", False)] == 0


def test_removal_that_duplicates_a_fact_is_skipped() -> None:
    rec = _record("dup", 4, [(0, (0, 1)), (0, (0, 1, 2)), (1, (1, 3)), (2, (2, 3))])
    for rem in removals(rec):
        if rem.kind == "remove_constant":
            assert rem.result.facts.count((0, (0, 1))) <= 1
            assert rem.constant != 2 or rem.fact_index != 1


def test_disconnecting_removal_is_rejected() -> None:
    # fact (0,1,2) bridges {0,3} and {2,4}; constant 1 is pendant, deleting the fact disconnects
    rec = _record("bridge", 5, [(0, (0, 1, 2)), (1, (0, 3)), (2, (2, 4)), (3, (3, 0)), (1, (4, 2))])
    for rem in removals(rec):
        assert rem.result.is_connected()
        assert not (rem.kind == "delete_fact" and rem.fact_index == rec.facts.index((0, (0, 1, 2))))


@pytest.mark.parametrize("r", [1, 2, 3])
def test_copies_are_valid_pendant_and_distinct(source: KBRecord, keys: IsoKeys, r: int) -> None:
    rng = np.random.default_rng(cell_seed(0, "test", r))
    copies, stats = make_copies(source, r, 4, rng, keys)
    assert len(copies) == 4
    src_cert, src_ow = keys(source)
    certs = set()
    for cp in copies:
        assert cp.is_connected()
        assert cp.m >= 3
        assert cp.label == source.kb_id
        assert cp.meta["r"] == r
        assert all(p for _, p in cp.meta["steps"]) and len(cp.meta["steps"]) == r
        assert cp.n <= source.n - r  # every pendant step drops at least one constant
        cert, ow = keys(cp)
        assert cert != src_cert and ow != src_ow
        certs.add(cert)
    assert len(certs) == 4
    assert stats.key_disagreements == 0
    assert stats.steps_interior == 0


def test_mix_condition_takes_interior_steps(source: KBRecord) -> None:
    rng = np.random.default_rng(1)
    drawn = sample_copy(source, 1, rng, q_interior=1.0)
    assert drawn is not None
    rec, steps = drawn
    assert steps == [(steps[0][0], False)]
    assert rec.n == source.n


def test_mix_q_calibration() -> None:
    assert mix_q(0.9, 0.5) == pytest.approx(0.2)
    assert mix_q(0.5, 0.25) == 1.0
    assert mix_q(0.9, 0.0) == 0.0


def test_star_cannot_lose_three_statements_below_three_facts(keys: IsoKeys) -> None:
    star = _record("star", 5, [(0, (0, 1)), (1, (0, 2)), (2, (0, 3)), (3, (0, 4))])
    rng = np.random.default_rng(0)
    assert sample_copy(star, 2, rng) is None  # 4 facts -> at most one deletion keeps 3
    copies, _ = make_copies(star, 1, 6, rng, keys, max_draws=50)
    assert len(copies) == 4  # four distinct predicates -> four non-isomorphic copies only


def test_select_sources_excludes_ineligible_and_isomorphic(source: KBRecord, keys: IsoKeys) -> None:
    star = _record("star", 4, [(0, (0, 1)), (1, (0, 2)), (2, (0, 3))])  # no removal keeps 3 facts
    twin = KBRecord(
        kb_id="twin",
        n=source.n,
        types=source.types,
        facts=source.facts,
        meta=dict(source.meta),
    )
    col = KBCollection(
        "toy",
        (source, star, twin),
        type_names=tuple(f"t{i}" for i in range(N_TYPES)),
        pred_names=tuple(f"p{i}" for i in range(N_PREDS)),
    )
    draw = select_sources(col, 3, [1, 2], 3, np.random.default_rng(0), keys)
    assert len(draw.sources) == 1
    assert draw.n_ineligible == 1
    assert draw.n_skipped_iso_source == 1
    assert draw.shortfall == 2
    assert all(len(cs) == 3 for r in (1, 2) for cs in draw.copies[r])


def test_cell_seed_is_stable() -> None:
    assert cell_seed(0, "B", "wd50k66") == cell_seed(0, "B", "wd50k66")
    assert cell_seed(0, "B", "wd50k66") != cell_seed(1, "B", "wd50k66")
    assert cell_seed(0, "B", "wd50k66") != cell_seed(0, "B", "wd50k100")


# --------------------------------------------------------------------------- kNN


def _brute_probs(d: np.ndarray, labels: np.ndarray, k: int, L: int) -> np.ndarray:
    """Average over every candidate order consistent with the distances."""
    out = np.zeros(L)
    perms = list(itertools.permutations(range(len(d))))
    for perm in perms:
        order = sorted(perm, key=lambda i: d[i])  # stable: perm breaks distance ties
        votes = Counter(labels[i] for i in order[:k])
        top = max(votes.values())
        winners = [lab for lab, v in votes.items() if v == top]
        for lab in winners:
            out[lab] += 1.0 / len(winners)
    return out / len(perms)


@pytest.mark.parametrize("seed", range(12))
@pytest.mark.parametrize("k", [1, 3, 5])
def test_knn_probs_match_brute_force(seed: int, k: int) -> None:
    rng = np.random.default_rng(seed)
    n = 7
    d = rng.integers(0, 3, size=n).astype(float)
    labels = rng.integers(0, 3, size=n)
    got = knn_label_probs(d, labels, k, 3)
    np.testing.assert_allclose(got, _brute_probs(d, labels, k, 3), rtol=1e-12, atol=1e-12)
    assert got.sum() == pytest.approx(1.0)


def test_knn_tie_at_expected_accuracy() -> None:
    d = np.array([1.0, 1.0, 2.0])
    labels = np.array([0, 1, 0])
    assert knn_label_probs(d, labels, 1, 2)[0] == pytest.approx(0.5)
    # all tied at zero: a false-zero representation gets the base rate, not credit
    assert knn_label_probs(np.zeros(4), np.array([0, 1, 1, 1]), 1, 2)[0] == pytest.approx(0.25)


def test_knn_infinite_distances_rank_last() -> None:
    d = np.array([np.inf, 3.0, np.nan])
    labels = np.array([0, 1, 0])
    assert knn_label_probs(d, labels, 1, 2)[1] == pytest.approx(1.0)


def test_loo_and_candidate_mask() -> None:
    D = np.array(
        [
            [0, 1, 5, 5],
            [1, 0, 5, 5],
            [5, 5, 0, 1],
            [5, 5, 1, 0],
        ],
        dtype=float,
    )
    codes = np.array([0, 0, 1, 1])
    P = loo_knn_probs(D, codes, 1)
    assert expected_accuracy(P, codes) == 1.0
    assert expected_macro_f1(P, codes) == 1.0
    # forbid each item's true partner: every query falls back to the other class
    mask = np.ones((4, 4), dtype=bool)
    mask[0, 1] = mask[1, 0] = mask[2, 3] = mask[3, 2] = False
    P2 = loo_knn_probs(D, codes, 1, mask)
    assert expected_accuracy(P2, codes) == 0.0


def test_macro_f1_matches_sklearn_without_ties() -> None:
    from sklearn.metrics import f1_score

    rng = np.random.default_rng(3)
    codes = rng.integers(0, 4, size=40)
    pred = rng.integers(0, 4, size=40)
    P = np.eye(4)[pred]
    assert expected_macro_f1(P, codes) == pytest.approx(
        f1_score(codes, pred, average="macro", labels=np.unique(codes))
    )


def test_ceiling_census() -> None:
    from knn_lib import OURS, ceiling_census

    p = {
        OURS: np.array([1.0, 1.0, 0.0, 0.5]),
        "fact_rank": np.array([1.0, 0.0, 1.0, 1.0]),
    }
    ce = ceiling_census(p)
    assert ce["all_arms_correct"] == pytest.approx(0.25)
    assert ce["min_arm_p_correct_mean"] == pytest.approx((1 + 0 + 0 + 0.5) / 4)
    assert ce["word_right_some_competitor_wrong"] == pytest.approx(0.25)
    assert ce["word_wrong_some_competitor_right"] == pytest.approx(0.5)
    assert ce["n_arms_acc1_ge_0.9"] == 0


def test_exact_arm_ceiling() -> None:
    from knn_lib import exact_arm_ceiling

    iso = np.array([0, 0, 1, 1, 2])
    codes = np.array([0, 1, 0, 0, 1])
    assert exact_arm_ceiling(iso, codes) == pytest.approx((0 + 0 + 1 + 1 + 1) / 5)
    # an exact arm reaches the ceiling: zero distance exactly within isomorphism classes
    D = (iso[:, None] != iso[None, :]).astype(float)
    acc = expected_accuracy(loo_knn_probs(D, codes, 1), codes)
    assert acc <= exact_arm_ceiling(iso, codes) + 1e-12


def test_medoid_certificates_on_a_metric() -> None:
    from knn_lib import medoid_certificates

    rng = np.random.default_rng(5)
    X = rng.normal(size=(12, 2))
    D = np.sqrt(((X[:, None, :] - X[None, :, :]) ** 2).sum(-1))
    res = pam(D, 3, 0)
    cert = medoid_certificates(D, res["labels"], res["medoids"])
    assert cert["n_1medoid_over_bound"] == 0
    for row in cert["clusters"]:
        members = np.flatnonzero(res["labels"] == res["labels"][0])
        assert row["ratio_1medoid"] <= row["bound"] + 1e-12
        assert row["ratio"] >= row["ratio_1medoid"] - 1e-12
        assert row["lb"] > 0 and len(members) >= 1
    # hand case: three points on a line at 0, 1, 2 -> LB = (1 + 2 + 1) / 2 = 2, medoid cost 2
    line = np.array([[0, 1, 2], [1, 0, 1], [2, 1, 0]], dtype=float)
    one = medoid_certificates(line, np.zeros(3, dtype=np.int64), np.array([1]))
    assert one["clusters"][0]["ratio"] == pytest.approx(1.0)
    assert one["clusters"][0]["bound"] == pytest.approx(4 / 3)


# --------------------------------------------------------------------------- PAM


@pytest.mark.parametrize("seed", range(6))
@pytest.mark.parametrize("k", [2, 3])
def test_pam_matches_brute_force_on_tiny_cases(seed: int, k: int) -> None:
    rng = np.random.default_rng(seed)
    centres = rng.normal(scale=6.0, size=(k, 2))
    X = np.concatenate([c + rng.normal(size=(3, 2)) for c in centres])
    D = np.sqrt(((X[:, None, :] - X[None, :, :]) ** 2).sum(-1))
    res = pam(D, k, seed)
    assert res["loss"] == pytest.approx(brute_force_kmedoids(D, k), rel=1e-9)
    # every item sits with its nearest medoid, in the original item order
    nearest = res["medoids"][np.argmin(D[:, res["medoids"]], axis=1)]
    assert np.array_equal(res["medoids"][res["labels"]], nearest)


# --------------------------------------------------------------------------- lineages


def test_lineages_need_three_versions() -> None:
    recs = []
    for node, windows in ((1, [0, 1, 2]), (2, [0, 3]), (3, [1, 2, 4, 5])):
        for w in windows:
            recs.append(
                _record(
                    f"{node}@{w}",
                    3,
                    [(0, (0, 1)), (1, (1, 2)), (2, (0, 2))],
                    class_id=node,
                    window=w,
                )
            )
    col = KBCollection(
        "toy_ndc",
        tuple(recs),
        type_names=tuple(f"t{i}" for i in range(N_TYPES)),
        pred_names=tuple(f"p{i}" for i in range(N_PREDS)),
    )
    lin = lineages(col)
    assert sorted(lin) == ["1", "3"]
    assert [col.records[i].meta["window"] for i in lin["3"]] == [1, 2, 4, 5]


# --------------------------------------------------------------------------- Design C


def _toy_graph(seed: int, n: int = 60, p: float = 0.12) -> dict[int, dict[int, str]]:
    rng = np.random.default_rng(seed)
    adj: dict[int, dict[int, str]] = {v: {} for v in range(n)}
    for a in range(n):
        for b in range(a + 1, n):
            if rng.random() < p:
                kind = "pendant" if rng.random() < 0.6 else "interior"
                adj[a][b] = adj[b][a] = kind
    return adj


@pytest.mark.parametrize("stratum", list(DC.STRATA))
@pytest.mark.parametrize("seed", range(4))
@pytest.mark.parametrize("s_target", [None, 20])
def test_blocks_are_disjoint_and_match_the_stratum(
    stratum: str, seed: int, s_target: int | None
) -> None:
    adj = _toy_graph(seed)
    eligible = [v for v in adj if v % 7 != 0]
    kinds = DC.STRATA[stratum]
    blocks, discarded = DC.draw_blocks(
        adj, kinds, eligible, np.random.default_rng(seed), s_target=s_target
    )
    assert blocks and discarded == 0
    used = [v for b in blocks for v in b]
    assert len(used) == len(set(used)), "blocks overlap"
    assert set(used) <= set(eligible)
    for block in blocks:
        assert DC.BLOCK_MIN <= len(block) <= DC.BLOCK_NEIGHBOURS + 1
        head = block[0]
        for member in block[1:]:
            assert adj[head][member] in kinds, "a neighbour's edit kind is outside the stratum"
    remaining = set(eligible) - set(used)
    if s_target is None or sum(len(b) for b in blocks) < s_target:
        assert DC.candidate_seeds(adj, kinds, remaining) == [], "the draw stopped early"


def test_block_acceptance_drops_members_and_discards_small_blocks() -> None:
    adj = _toy_graph(1)

    def drop(block: list[int]) -> list[int]:
        return block[:3] if len(block) == 5 else block[:2]

    blocks, discarded = DC.draw_blocks(
        adj, DC.STRATA["C-all"], list(adj), np.random.default_rng(0), s_target=None, accept=drop
    )
    assert blocks and all(len(b) == 3 for b in blocks)
    assert discarded > 0


def test_one_edit_graph_dedups_and_labels_kinds() -> None:
    base = [(0, (0, 1)), (1, (1, 2)), (2, (0, 2)), (3, (2, 3)), (0, (3, 4))]
    a = _record("A", 5, base)
    b = _record("B", 4, base[:4])  # minus the leaf statement (0, (3, 4)): pendant
    d = _record("D", 5, [f for f in base if f != (2, (0, 2))])  # minus a cycle edge: interior
    # A with constants 0 and 2 swapped (both carry type 0): isomorphic to A
    perm = {0: 2, 1: 1, 2: 0, 3: 3, 4: 4}
    a2 = _record("A2", 5, [(p, tuple(sorted(perm[x] for x in args))) for p, args in base])
    col = KBCollection(
        "toy_c",
        (a, b, d, a2),
        type_names=tuple(f"t{i}" for i in range(N_TYPES)),
        pred_names=tuple(f"p{i}" for i in range(N_PREDS)),
    )
    g = DC.one_edit_graph(col)
    assert len(g.rep) == 3  # A and A2 collapse to one class, represented by A (index 0)
    cls = {i: c for c, i in g.rep.items()}
    assert g.adj[cls[0]] == {cls[1]: "pendant", cls[2]: "interior"}
    assert g.edge_counts() == {"pendant": 1, "interior": 1}


def test_member_copies_are_deterministic(source: KBRecord, keys: IsoKeys) -> None:
    one = DC.member_copies(source, 7, 0, keys, "toy", 3)
    two = DC.member_copies(source, 7, 0, keys, "toy", 3)
    assert one is not None and two is not None
    assert {r: [c.facts for c in cs] for r, cs in one.items()} == {
        r: [c.facts for c in cs] for r, cs in two.items()
    }
    assert all(len(cs) == 3 for cs in one.values())


def test_error_split() -> None:
    from knn_lib import error_split

    groups = np.array([0, 0, 1])  # classes 0 and 1 share a block; class 2 is alone
    codes = np.array([0, 2])
    P = np.array([[0.5, 0.25, 0.25], [0.5, 0.0, 0.5]])
    out = error_split(P, codes, groups)
    assert out["err_within_group"] == pytest.approx(0.25 / 2)
    assert out["err_other_group"] == pytest.approx((0.25 + 0.5) / 2)
    assert out["err_within_share"] == pytest.approx(0.25)


def test_wl_h1_arm(source: KBRecord, keys: IsoKeys) -> None:
    from knn_lib import WL_H1, build_matrices

    copies, _ = make_copies(source, 1, 3, np.random.default_rng(0), keys)
    twin = KBRecord(
        kb_id="twin", n=source.n, types=source.types, facts=source.facts, meta=dict(source.meta)
    )
    mats, secs = build_matrices([source, twin, *copies], [WL_H1], n_types=N_TYPES, n_preds=N_PREDS)
    M = mats[WL_H1]
    assert M[0, 1] == 0.0
    assert (M[0, 2:] > 0).all() and np.isfinite(M).all()
    assert secs[WL_H1] >= 0.0


# --------------------------------------------------------------------------- Design D


def test_nn_scores_ties_at_expectation() -> None:
    d = np.array([2.0, 1.0, 1.0, 3.0])
    p1, rr = DD.nn_scores(d, 1)
    assert p1 == pytest.approx(0.5)
    assert rr == pytest.approx(1 / 1.5)
    p1, rr = DD.nn_scores(d, 3)
    assert p1 == 0.0
    assert rr == pytest.approx(0.25)
    p1, rr = DD.nn_scores(np.array([0.0, 5.0]), 0)
    assert (p1, rr) == (1.0, 1.0)


@pytest.mark.parametrize("arm", list(K_ARMS_C))
def test_rect_equals_the_union_matrix_block(source: KBRecord, keys: IsoKeys, arm: str) -> None:
    from knn_lib import build_matrices

    rng = np.random.default_rng(0)
    other = _record("other", 6, [(0, (0, 1)), (1, (1, 2)), (2, (2, 3)), (3, (3, 4)), (0, (4, 5))])
    catalogue = [source, other, *make_copies(source, 2, 3, rng, keys)[0]]
    queries = [*make_copies(source, 1, 3, rng, keys)[0], *make_copies(other, 1, 2, rng, keys)[0]]
    cat_hs = [r.to_hypergraph(n_types=N_TYPES, n_preds=N_PREDS) for r in catalogue]
    q_hs = [r.to_hypergraph(n_types=N_TYPES, n_preds=N_PREDS) for r in queries]
    got = RECT.make_arm(arm, n_jobs=1).fit(cat_hs).rect(q_hs)
    mats, _ = build_matrices([*catalogue, *queries], [arm], n_types=N_TYPES, n_preds=N_PREDS)
    want = mats[arm][len(catalogue) :, : len(catalogue)]
    # build_matrix stores float32, the rectangle float64: integer arms agree exactly
    np.testing.assert_allclose(got, want, rtol=1e-6, atol=1e-7)


def test_rect_parallel_matches_serial(source: KBRecord, keys: IsoKeys) -> None:
    rng = np.random.default_rng(1)
    catalogue = [source, *make_copies(source, 1, 4, rng, keys)[0]]
    queries = make_copies(source, 2, 4, rng, keys)[0]
    cat_hs = [r.to_hypergraph(n_types=N_TYPES, n_preds=N_PREDS) for r in catalogue]
    q_hs = [r.to_hypergraph(n_types=N_TYPES, n_preds=N_PREDS) for r in queries]
    for arm in ("bipartite_ged_path", "hpd_jsd"):
        serial = RECT.make_arm(arm, n_jobs=1).fit(cat_hs).rect(q_hs)
        parallel = RECT.make_arm(arm, n_jobs=2).fit(cat_hs).rect(q_hs)
        np.testing.assert_array_equal(serial, parallel)


CACHED = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE/matrices")


@pytest.mark.integration
@pytest.mark.skipif(not CACHED.is_dir(), reason="cached campaign matrices not mounted")
@pytest.mark.parametrize(
    "arm",
    [
        "isal_ow_struct",
        "nauty_cert",
        "nauty_cert_rows",
        "fact_rank",
        "netlsd",
        "hpd_jsd",
        "degree_seq_l1",
        "size_l1",
        "bipartite_ged_assign",
        "bipartite_ged_path",
    ],
)
def test_rect_reproduces_cached_catalogue_entries(arm: str) -> None:
    from experiments.tkde import corpora

    col = corpora.load_collection("ndc_classes")
    hs = corpora.hypergraphs(col)
    rng = np.random.default_rng(7)
    cat_idx = np.sort(rng.choice(len(hs), 40, replace=False))
    q_idx = np.sort(rng.choice(len(hs), 8, replace=False))
    got = RECT.make_arm(arm, n_jobs=1).fit([hs[i] for i in cat_idx]).rect([hs[i] for i in q_idx])
    cached = np.load(CACHED / "ndc_classes" / f"{arm}.npy", mmap_mode="r")
    want = np.asarray(cached[np.ix_(q_idx, cat_idx)], dtype=np.float64)
    # cached[i, j] = pairwise(i, j) for i < j; the rectangle is pairwise(catalogue, query)
    mask = cat_idx[None, :] < q_idx[:, None]
    assert mask.sum() > 50
    np.testing.assert_allclose(got[mask], want[mask], rtol=0, atol=1e-6)  # cache is float32
