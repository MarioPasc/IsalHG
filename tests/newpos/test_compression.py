"""Tests for the description-length experiment (scripts/newpos/compression/)."""

from __future__ import annotations

import math
import random
import tempfile
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("pynauty")
pytest.importorskip("rapidfuzz")

from isalhg.core.instructions import TokenC, TokenV, validate
from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.generation.ngram import TokenNGram
from isalhg.iso_backends.pynauty_levi import PynautyLeviBackend
from isalhg.metric_space.distances.fact_levenshtein import FactRankLevenshtein
from isalhg.metric_space.distances.isal_ordered import IsalOrderedLevenshtein
from isalhg.metric_space.representations.nauty_levi_edit import (
    NautyCertRowsDistance,
)
from scripts.newpos.compression import compressors as K
from scripts.newpos.compression import serialize as S
from scripts.newpos.compression.coders import EscapedNGram, cross_validated_bits, kfold_assignment
from scripts.newpos.compression.decode import decode_arm

pytestmark = pytest.mark.unit


def _kb(n_v: int = 2, n_e: int = 2) -> SparseHypergraph:
    return SparseHypergraph(
        n_nodes=6,
        hyperedges=[
            frozenset({0, 1, 2}),
            frozenset({2, 3}),
            frozenset({3, 4, 5}),
            frozenset({1, 5}),
        ],
        n_vertex_labels=n_v,
        n_edge_labels=n_e,
        vertex_labels=[0, 1 % n_v, 0, 1 % n_v, 1 % n_v, 0],
        edge_labels=[0, 1 % n_e, 1 % n_e, 0],
    )


def _shuffled_copy(H: SparseHypergraph, rng: random.Random) -> SparseHypergraph:
    """Relabel the constants and reorder the facts: an isomorphic copy."""
    sigma = list(range(H.n_nodes))
    rng.shuffle(sigma)
    copy = permute(H, sigma)
    facts = [(label, members) for _, members, label in copy.iter_edges()]
    rng.shuffle(facts)
    return SparseHypergraph(
        n_nodes=copy.n_nodes,
        hyperedges=[members for _, members in facts],
        n_vertex_labels=copy.n_vertex_labels,
        n_edge_labels=copy.n_edge_labels,
        vertex_labels=[copy.vertex_label(v) for v in range(copy.n_nodes)],
        edge_labels=[label for label, _ in facts],
    )


@pytest.mark.parametrize("n_v,n_e", [(1, 1), (2, 2), (3, 1), (1, 3)])
def test_every_arm_is_deterministic_and_isomorphism_invariant(n_v: int, n_e: int) -> None:
    H = _kb(n_v, n_e)
    reference = S.encode_member(H)
    assert S.encode_member(H) == reference
    rng = random.Random(7)
    for _ in range(6):
        assert S.encode_member(_shuffled_copy(H, rng)) == reference
    assert set(reference) == {a for a in S.ARMS if S.arm_available(a, n_v)}


def test_arms_equal_the_symbols_the_registered_distances_compare() -> None:
    from isalhg.metric_space.representations.nauty_levi_edit import NautyLeviEditDistance

    H = _kb(2, 2)
    enc = S.encode_member(H)
    assert enc["w_o"] == IsalOrderedLevenshtein().fingerprint(H)
    assert bytes(enc["cert_bytes"]) == NautyLeviEditDistance().fingerprint(H)
    assert enc["cert_rows"] == NautyCertRowsDistance().fingerprint(H)
    assert enc["fact"] == FactRankLevenshtein().fingerprint(H)


@pytest.mark.parametrize("n_v,n_e", [(1, 1), (2, 2), (1, 3)])
def test_every_arm_decodes_to_an_isomorphic_knowledge_base(n_v: int, n_e: int) -> None:
    H = _kb(n_v, n_e)
    info = S.CollectionInfo("toy", k=10, n_v=n_v, n_e=n_e, n_max=6, big_n_max=10)
    backend = PynautyLeviBackend()
    for arm, sequence in S.encode_member(H).items():
        assert backend.are_isomorphic(H, decode_arm(arm, sequence, info)), arm


def test_certificate_bytes_have_a_whole_number_of_words() -> None:
    assert len(S.encode_member(_kb())["cert_bytes"]) % 4 == 0


@pytest.mark.parametrize("length,alphabet", [(0, 1), (1, 1), (7, 316), (50, 2**20)])
def test_fixed_width_single_slot_formula(length: int, alphabet: int) -> None:
    sequence = tuple(range(length))
    bits = S.fixed_width_bits("w_o", sequence, {S.SINGLE_SLOT: alphabet})
    assert bits == pytest.approx((length + 1) * math.log2(alphabet + 1), rel=1e-12)


def test_fixed_width_slot_wise_charges_each_slot_its_own_alphabet() -> None:
    # head symbols compete with the end marker (+1); a non-head slot does not.
    sizes = {"op": 5, "i": 10}
    sequence = (("op", "P"), ("i", 3), ("op", "W"))
    expected = math.log2(5 + 1) + math.log2(10) + math.log2(5 + 1) + math.log2(5 + 1)
    assert S.fixed_width_bits("w_flat", sequence, sizes) == pytest.approx(expected, rel=1e-12)


def test_walk_alphabet_size_matches_brute_force_enumeration() -> None:
    for k, n_v, n_e in [(3, 1, 1), (4, 2, 2), (5, 3, 1)]:
        count = 1 + 2 * k  # W, P_i, N_i
        for le in range(n_e):
            for i in range(1, k + 1):
                validate([TokenC(edge_label=le, i=i)], k=k, n_vertex_labels=n_v, n_edge_labels=n_e)
                count += 1
            for i in range(1, k):
                for j in range(1, k):
                    if 2 <= i + j <= k:
                        count += n_v**j
                        validate(
                            [TokenV(edge_label=le, i=i, j=j, new_node_labels=(n_v - 1,) * j)],
                            k=k,
                            n_vertex_labels=n_v,
                            n_edge_labels=n_e,
                        )
        assert S.walk_alphabet_size(k, n_v, n_e) == count + (n_v if n_v > 1 else 0)


TOY = [
    ("a", "b", "c"),
    ("a", "b", "b"),
    ("a", "c", "c"),
    ("b", "b", "c"),
    ("a", "b", "c"),
    ("c", "b", "a"),
]


def test_ngram_code_length_is_minus_log2_of_the_model_probability() -> None:
    train, held = TOY[:5], TOY[5]
    model = TokenNGram(order=3).fit(train)
    coder = EscapedNGram(3, alphabet_obs=3, alphabet_theo=3).fit(train)
    scored = coder.score(held)
    assert scored.n_unseen == 0
    expected = -model.logprob(held) / math.log(2)
    assert scored.core_bits == pytest.approx(expected, rel=1e-9)
    # the escape reserve multiplies every seen event by (1 - eps)
    reserve = (len(held) + 1) * -math.log2(1.0 - coder.eps)
    assert scored.bits_obs == pytest.approx(expected + reserve, rel=1e-9)


def test_escape_scheme_is_finite_on_an_unseen_token_and_prices_by_alphabet() -> None:
    coder = EscapedNGram(3, alphabet_obs=11, alphabet_theo=1000).fit(TOY)
    seen = coder.score(("a", "b", "c"))
    novel = coder.score(("a", "z", "c"))
    assert novel.n_unseen == 1
    assert math.isfinite(novel.bits_obs) and math.isfinite(novel.bits_theo)
    assert novel.bits_obs > seen.bits_obs
    assert novel.bits_theo > novel.bits_obs  # larger declared alphabet, costlier escape
    # a pure-escape event costs -log2(eps) + log2(U), U = |A| - |V_train|
    u_obs = 11 - 3
    delta = novel.bits_obs - novel.core_bits
    assert delta >= -math.log2(coder.eps) + math.log2(u_obs) - 1e-9


def test_kfold_assignment_partitions_members_and_is_seeded() -> None:
    folds = kfold_assignment(23, 5, seed=0)
    assert sorted(np.concatenate(folds).tolist()) == list(range(23))
    assert [len(f) for f in folds] == [5, 5, 5, 4, 4]
    again = kfold_assignment(23, 5, seed=0)
    assert all(np.array_equal(a, b) for a, b in zip(folds, again, strict=True))
    assert not all(
        np.array_equal(a, b) for a, b in zip(folds, kfold_assignment(23, 5, seed=1), strict=True)
    )


def test_cross_validation_codes_each_member_with_a_model_that_never_saw_it() -> None:
    words = [tuple("abcab"[: 2 + i % 3]) for i in range(20)]
    scored = cross_validated_bits(
        words, order=2, seed=0, alphabet_obs=3, alphabet_theo=3, n_folds=5
    )
    assert len(scored) == 20
    assert all(math.isfinite(s.bits_obs) and s.bits_obs > 0 for s in scored)


@pytest.mark.parametrize(
    "members,expected",
    [
        ([{0, 1}, {0, 2}, {0, 3}], True),  # sunflower with a one-point kernel
        ([{0, 1, 2}], True),  # a single fact
        ([{0, 1}, {1, 2}, {2, 3}], False),  # path: no constant in every fact
        ([{0, 1}, {0, 1, 2}], False),  # two constants in both facts
    ],
)
def test_star_classification(members: list[set[int]], expected: bool) -> None:
    n = 1 + max(max(m) for m in members)
    H = SparseHypergraph(n_nodes=n, hyperedges=[frozenset(m) for m in members])
    assert S.is_star(H) is expected


@pytest.mark.parametrize(
    "m,label", [(3, "m=3"), (4, "m=4-5"), (5, "m=4-5"), (8, "m=6-8"), (12, "m=9-12"), (30, "m>=13")]
)
def test_fact_bins(m: int, label: str) -> None:
    assert S.fact_bin(m) == label


def test_codepoint_table_skips_controls_and_surrogates() -> None:
    table = K.codepoint_table(70_000)
    assert len(set(table)) == 70_000
    assert all(
        0x21 <= c < 0x110000 and not 0x7F <= c <= 0xA0 and not 0xD800 <= c <= 0xDFFF for c in table
    )
    assert 0x0A not in table and 0x20 not in table


def test_frequency_ids_rank_by_count_then_first_occurrence() -> None:
    ids = K.frequency_ids([("x", "y", "y"), ("z", "y", "x")])
    assert ids == {"y": 0, "x": 1, "z": 2}


def test_compressor_sizes_and_self_patch() -> None:
    data = b"V[3;1;2;0,0];" * 400
    for kind in K.COMPRESSORS:
        assert 0 < K.compress_size(kind, data) < len(data)
    with tempfile.TemporaryDirectory() as tmp:
        same = K.zstd_patch_size(data, data, Path(tmp))
        other = K.zstd_patch_size(b"unrelated bytes " * 50, data, Path(tmp))
    assert same <= other


def test_choose_renderings_charges_the_dictionary() -> None:
    rows = [
        {"arm": "a", "compressor": "xz", "rendering": "ids", "bytes": 10, "dict_bytes": 100},
        {"arm": "a", "compressor": "xz", "rendering": "cp", "bytes": 12, "dict_bytes": 100},
        {"arm": "a", "compressor": "xz", "rendering": "lit", "bytes": 50, "dict_bytes": 0},
    ]
    picks = K.choose_renderings(rows)[("a", "xz")]
    assert picks == {"spec": "ids", "self_contained": "lit"}
