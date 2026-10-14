"""The ordered walk ``OW_pi``: round trip, invariance, validity, completeness, locality.

Six claims are pinned here, one per section, and they are the six the article rests
on (``theorem_c_ordered_walk.tex``).

1. **Round trip** (Lemma C.3). ``S2H`` of the emitted word is isomorphic to the input,
   decided by pynauty on the coloured Levi graph -- never by our own fingerprint, which
   would make the check circular.
2. **Invariance**. Relabelling the constants and shuffling the fact insertion order
   leaves ``(root type, word)`` untouched. This is the half of Theorem C that the
   greedy canonical string ``w*`` fails.
3. **Validity** (Lemma C.2). Every emitted token is in ``Sigma_HG(k)``; no ``W`` is ever
   emitted; the pointers ``p_1..p_i`` are on distinct slots at every ``V`` and ``C``, so
   no fact is silently narrowed and the decoder's duplicate check never fires.
4. **Completeness** (Theorem C). Equal fingerprints iff isomorphic, in both directions,
   against pynauty on a thousand pairs.
5. **k-independence**. The word is the same for every admissible pointer count. This is
   what lets ``d_o`` compare a corpus without pinning ``k`` first, unlike ``d_I``.
6. **Star locality** (Proposition 6.3). Under the no-crossing move rule a leaf insertion
   costs at most 2 instructions on every star, and a closing-fact insertion at most 3.
   See :class:`TestStarLocality`.

The golden pins are the ordered walk's **own** table. They are not the ``w*_c`` pins of
``test_wstar_c_frozen.py`` and must never be compared with them: ``w*_c`` and ``w_o`` are
different canonical forms of the same family, different strings by construction.
"""

from __future__ import annotations

import hashlib
import random
from collections.abc import Sequence

import pytest

from isalhg.core.algorithms.ordered_walk import (
    OrderedWalkError,
    OrderedWalkPolicy,
    ordered_walk,
)
from isalhg.core.canonical import required_k
from isalhg.core.cdll import CircularDoublyLinkedList
from isalhg.core.instructions import (
    Token,
    TokenC,
    TokenN,
    TokenP,
    TokenV,
    TokenW,
    serialize,
    validate,
)
from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.core.string_to_hypergraph import string_to_hypergraph
from isalhg.datasets.synthetic import designs
from isalhg.errors import DegenerateHypergraphError, DisconnectedHypergraphError
from isalhg.iso_backends.isal_ordered import (
    POLICIES,
    ordered_fingerprint,
    ordered_symbols,
    ordered_word,
)

pytestmark = pytest.mark.unit

pytest.importorskip("pynauty")

POLICY_NAMES = ("struct", "rank", "rank0")

_N_RANDOM = 2000
_N_PAIRS = 1000
_N_ISO_PAIRS = 340


# ---------------------------------------------------------------------------
# Corpora
# ---------------------------------------------------------------------------


def _random_connected(rng: random.Random) -> SparseHypergraph:
    """A random connected labelled hypergraph: n <= 10, arity <= 5, 3 types, 3 predicates.

    A spine of consecutive pairs guarantees connectivity; the extra facts are free.
    Both the member order and the labels are drawn from ``rng``, so the corpus
    exercises the fact-insertion-order sensitivity the invariance claim denies.
    """
    n = rng.randint(1, 10)
    members: set[frozenset[int]] = {frozenset({i, i + 1}) for i in range(n - 1)}
    for _ in range(rng.randint(0, n)):
        arity = rng.randint(2, min(5, max(2, n)))
        if arity <= n:
            members.add(frozenset(rng.sample(range(n), arity)))
    ordered = sorted(members, key=sorted)
    rng.shuffle(ordered)
    return SparseHypergraph(
        n,
        ordered,
        n_vertex_labels=3,
        n_edge_labels=3,
        vertex_labels=[rng.randrange(3) for _ in range(n)],
        edge_labels=[rng.randrange(3) for _ in ordered],
    )


def _shuffled_copy(H: SparseHypergraph, rng: random.Random) -> SparseHypergraph:
    """Relabel the constants and shuffle the fact insertion order."""
    sigma = list(range(H.n_nodes))
    rng.shuffle(sigma)
    P = permute(H, sigma)
    facts = [(P.members(e), P.edge_label(e)) for e in P.edges()]
    rng.shuffle(facts)
    return SparseHypergraph(
        P.n_nodes,
        [m for m, _ in facts],
        n_vertex_labels=P.n_vertex_labels,
        n_edge_labels=P.n_edge_labels,
        vertex_labels=[P.vertex_label(v) for v in range(P.n_nodes)],
        edge_labels=[label for _, label in facts],
    )


@pytest.fixture(scope="module")
def random_corpus() -> list[SparseHypergraph]:
    """``_N_RANDOM`` random connected labelled hypergraphs under a pinned seed."""
    rng = random.Random(20260906)
    return [_random_connected(rng) for _ in range(_N_RANDOM)]


def _design_fixtures() -> dict[str, SparseHypergraph]:
    """The named designs plus five catalog Steiner systems, by pin key."""
    from isalhg.datasets.synthetic.sts_catalog import steiner_triple_system

    return {
        "fano_plane": designs.fano_plane(),
        "sts_9": designs.sts_9(),
        "cyclic_triple_13_014": designs.cyclic_triple_orbit_13((0, 1, 4)),
        "cyclic_triple_13_016": designs.cyclic_triple_orbit_13((0, 1, 6)),
        "gq_2_2_doily": designs.gq_2_2_doily(),
        "n4_pair_h1": SparseHypergraph(4, [frozenset({0, 1, 2}), frozenset({0, 1, 3})]),
        "n4_pair_h2": SparseHypergraph(
            4, [frozenset({0, 1}), frozenset({1, 2}), frozenset({2, 3})]
        ),
        "sts_catalog_7_0": steiner_triple_system(7, 0),
        "sts_catalog_9_0": steiner_triple_system(9, 0),
        "sts_catalog_13_0": steiner_triple_system(13, 0),
        "sts_catalog_13_1": steiner_triple_system(13, 1),
        "sts_catalog_15_0": steiner_triple_system(15, 0),
    }


@pytest.fixture(scope="module")
def design_fixtures() -> dict[str, SparseHypergraph]:
    return _design_fixtures()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _decode(H: SparseHypergraph, policy: OrderedWalkPolicy) -> SparseHypergraph:
    """Run the emitted word back through S2H at ``required_k(H)``."""
    result = ordered_word(H, policy=policy)
    return string_to_hypergraph(
        serialize(result.tokens),
        k=required_k(H),
        n_vertex_labels=H.n_vertex_labels,
        n_edge_labels=H.n_edge_labels,
        seed_label=result.root_label,
    )


def _iso(H1: SparseHypergraph, H2: SparseHypergraph) -> bool:
    """Isomorphism decided by pynauty on the coloured Levi graph -- the outside oracle."""
    from isalhg.iso_backends.pynauty_levi import PynautyLeviBackend

    return PynautyLeviBackend().are_isomorphic(H1, H2)


def _fact_pointer_slots(tokens: Sequence[Token], k: int) -> list[tuple[int, ...]]:
    """Replay the program and return the pointer slots in force at every ``V``/``C``.

    Reproduces the decoder's CDLL exactly (new constants chained after ``p_1`` in listed
    order), so a duplicate inside one entry means the decoder would have built a fact of
    lower arity than the token claims.
    """
    capacity = 1 + sum(t.j for t in tokens if isinstance(t, TokenV))
    cdll = CircularDoublyLinkedList(capacity=capacity)
    cdll.insert_after(0, 0)
    pointers = [0] * k
    next_value = 1
    seen: list[tuple[int, ...]] = []
    for token in tokens:
        if isinstance(token, TokenP):
            pointers[token.i - 1] = cdll.next_node(pointers[token.i - 1])
        elif isinstance(token, TokenN):
            pointers[token.i - 1] = cdll.prev_node(pointers[token.i - 1])
        elif isinstance(token, TokenC):
            seen.append(tuple(pointers[: token.i]))
        elif isinstance(token, TokenV):
            seen.append(tuple(pointers[: token.i]))
            after = pointers[0]
            for _ in range(token.j):
                after = cdll.insert_after(after, next_value)
                next_value += 1
    return seen


def _longest_move_run(tokens: Sequence[Token]) -> int:
    """Length of the longest run of one repeated ``P``/``N`` token in ``tokens``."""
    longest = 0
    current = 0
    previous: Token | None = None
    for token in tokens:
        if not isinstance(token, (TokenN, TokenP)):
            previous, current = None, 0
            continue
        current = current + 1 if token == previous else 1
        previous = token
        longest = max(longest, current)
    return longest


# ---------------------------------------------------------------------------
# 1. Round trip
# ---------------------------------------------------------------------------


class TestRoundTrip:
    """``S2H(w_o(H); k, root type)`` is isomorphic to ``H`` (Lemma C.3)."""

    @pytest.mark.parametrize("policy_name", POLICY_NAMES)
    def test_design_fixtures(
        self, policy_name: str, design_fixtures: dict[str, SparseHypergraph]
    ) -> None:
        policy = POLICIES[policy_name]
        for name, H in design_fixtures.items():
            assert _iso(H, _decode(H, policy)), f"{policy_name} / {name}"

    @pytest.mark.parametrize("policy_name", POLICY_NAMES)
    def test_random_corpus(self, policy_name: str, random_corpus: list[SparseHypergraph]) -> None:
        policy = POLICIES[policy_name]
        failures = [
            index for index, H in enumerate(random_corpus) if not _iso(H, _decode(H, policy))
        ]
        assert failures == [], f"{policy_name}: {len(failures)} of {_N_RANDOM} failed"

    def test_creation_order_is_the_isomorphism(self) -> None:
        """Position ``t`` of ``creation_order`` is the constant the decoder creates t-th."""
        H = designs.fano_plane()
        result = ordered_word(H)
        decoded = _decode(H, POLICIES["struct"])
        phi = {v: t for t, v in enumerate(result.creation_order)}
        assert sorted(phi.values()) == list(range(H.n_nodes))
        for e in H.edges():
            image = frozenset(phi[v] for v in H.members(e))
            assert decoded.has_edge(image, H.edge_label(e))


# ---------------------------------------------------------------------------
# 2. Invariance
# ---------------------------------------------------------------------------


class TestInvariance:
    """The fingerprint survives constant relabelling and fact reordering."""

    @pytest.mark.parametrize("policy_name", POLICY_NAMES)
    def test_designs_under_200_relabellings(
        self, policy_name: str, design_fixtures: dict[str, SparseHypergraph]
    ) -> None:
        policy = POLICIES[policy_name]
        rng = random.Random(4242)
        # The 15-point catalog system is the slowest member and adds nothing the
        # 13-point ones do not; 200 relabellings of it dominates the suite's runtime.
        cheap = {k: v for k, v in design_fixtures.items() if k != "sts_catalog_15_0"}
        for name, H in cheap.items():
            expected = ordered_fingerprint(H, policy=policy)
            for _ in range(200):
                assert ordered_fingerprint(_shuffled_copy(H, rng), policy=policy) == expected, (
                    f"{policy_name} / {name}"
                )

    @pytest.mark.parametrize("policy_name", POLICY_NAMES)
    def test_random_corpus_under_20_relabellings(
        self, policy_name: str, random_corpus: list[SparseHypergraph]
    ) -> None:
        policy = POLICIES[policy_name]
        rng = random.Random(99)
        violations = 0
        for H in random_corpus:
            expected = ordered_fingerprint(H, policy=policy)
            for _ in range(20):
                if ordered_fingerprint(_shuffled_copy(H, rng), policy=policy) != expected:
                    violations += 1
        assert violations == 0, f"{policy_name}: {violations} invariance violations"


# ---------------------------------------------------------------------------
# 3. Validity
# ---------------------------------------------------------------------------


class TestValidity:
    """Lemma C.2: alphabet-valid, no ``W``, distinct pointers at every fact."""

    @pytest.mark.parametrize("policy_name", POLICY_NAMES)
    def test_designs_and_random(
        self,
        policy_name: str,
        design_fixtures: dict[str, SparseHypergraph],
        random_corpus: list[SparseHypergraph],
    ) -> None:
        policy = POLICIES[policy_name]
        corpus = list(design_fixtures.values()) + random_corpus
        for H in corpus:
            k = required_k(H)
            tokens = ordered_walk(H, _ranks(H), policy=policy, k=k).tokens
            validate(
                list(tokens),
                k=k,
                n_vertex_labels=H.n_vertex_labels,
                n_edge_labels=H.n_edge_labels,
            )
            assert not any(isinstance(t, TokenW) for t in tokens)
            for slots in _fact_pointer_slots(tokens, k):
                assert len(set(slots)) == len(slots), (
                    f"{policy_name}: coincident pointers at a fact of a {H.n_nodes}-constant input"
                )

    @pytest.mark.parametrize("policy_name", POLICY_NAMES)
    def test_no_move_run_is_longer_than_n_minus_one(
        self,
        policy_name: str,
        design_fixtures: dict[str, SparseHypergraph],
        random_corpus: list[SparseHypergraph],
    ) -> None:
        """The no-crossing rule bounds every run by the root-free arc, so by ``n - 1``.

        A longer run means a move wrapped past the root, which is the bug the rule
        exists to exclude: a wrapping run's length depends on the constant count, and
        an insertion anywhere would then rewrite it.
        """
        policy = POLICIES[policy_name]
        for H in list(design_fixtures.values()) + random_corpus[:500]:
            tokens = ordered_word(H, policy=policy).tokens
            assert _longest_move_run(tokens) <= max(1, H.n_nodes - 1), (
                f"{policy_name}: a move run exceeded n - 1 on a {H.n_nodes}-constant input"
            )

    def test_k_argument_rejects_an_inadmissible_pointer_count(self) -> None:
        from isalhg.errors import InvalidInstructionError

        H = designs.fano_plane()
        with pytest.raises(InvalidInstructionError):
            ordered_walk(H, _ranks(H), k=2)


def _ranks(H: SparseHypergraph) -> tuple[int, ...]:
    from isalhg.iso_backends.canonical_order import canonical_ranks

    return canonical_ranks(H)


# ---------------------------------------------------------------------------
# 4. Completeness
# ---------------------------------------------------------------------------


class TestCompleteness:
    """Theorem C: equal fingerprints iff isomorphic, decided against pynauty."""

    @pytest.mark.parametrize("policy_name", POLICY_NAMES)
    def test_thousand_pairs(self, policy_name: str) -> None:
        policy = POLICIES[policy_name]
        rng = random.Random(777)
        false_merge = 0
        false_split = 0
        iso_pairs = 0
        for index in range(_N_PAIRS):
            H1 = _random_connected(rng)
            if index < _N_ISO_PAIRS:
                H2 = _shuffled_copy(H1, rng)
                iso_pairs += 1
            else:
                H2 = _random_connected(rng)
            same_word = ordered_fingerprint(H1, policy=policy) == ordered_fingerprint(
                H2, policy=policy
            )
            isomorphic = _iso(H1, H2)
            if same_word and not isomorphic:
                false_merge += 1
            if isomorphic and not same_word:
                false_split += 1
        assert iso_pairs >= 300
        assert (false_merge, false_split) == (0, 0), (
            f"{policy_name}: {false_merge} false merges, {false_split} false splits "
            f"over {_N_PAIRS} pairs"
        )

    def test_non_isomorphic_designs_separate(self) -> None:
        left = designs.cyclic_triple_orbit_13((0, 1, 4))
        right = designs.cyclic_triple_orbit_13((0, 1, 6))
        assert not _iso(left, right)
        for policy in POLICIES.values():
            assert ordered_fingerprint(left, policy=policy) != ordered_fingerprint(
                right, policy=policy
            )


# ---------------------------------------------------------------------------
# 5. k-independence
# ---------------------------------------------------------------------------


class TestPointerCountIndependence:
    """The program never names a pointer beyond ``max(2, max arity)``."""

    @pytest.mark.parametrize("policy_name", POLICY_NAMES)
    def test_same_tokens_at_required_k_and_at_ten(
        self, policy_name: str, random_corpus: list[SparseHypergraph]
    ) -> None:
        policy = POLICIES[policy_name]
        for H in random_corpus[:200]:
            ranks = _ranks(H)
            tight = ordered_walk(H, ranks, policy=policy, k=required_k(H)).tokens
            wide = ordered_walk(H, ranks, policy=policy, k=10).tokens
            assert tight == wide


# ---------------------------------------------------------------------------
# 6. Star locality
# ---------------------------------------------------------------------------


def _build_star(
    rng: random.Random, n_leaves: int, n_predicates: int
) -> list[tuple[frozenset[int], int]]:
    """A binary star at constant 0: one creating fact per leaf, 20 % with a second."""
    facts = [(frozenset({0, leaf}), rng.randrange(n_predicates)) for leaf in range(1, n_leaves + 1)]
    for leaf in range(1, n_leaves + 1):
        if rng.random() < 0.20:
            creator = min(label for m, label in facts if m == frozenset({0, leaf}))
            above = [q for q in range(n_predicates) if q > creator]
            if above:
                facts.append((frozenset({0, leaf}), rng.choice(above)))
    return facts


def _star(n_nodes: int, facts: list[tuple[frozenset[int], int]]) -> SparseHypergraph:
    return SparseHypergraph(
        n_nodes,
        [m for m, _ in facts],
        n_vertex_labels=1,
        n_edge_labels=5,
        edge_labels=[label for _, label in facts],
    )


def _token_distance(H1: SparseHypergraph, H2: SparseHypergraph) -> float:
    from isalhg.metric_space.distances.isal_ordered import IsalOrderedLevenshtein

    return IsalOrderedLevenshtein("struct").pairwise(H1, H2)


class TestStarLocality:
    """Proposition 6.3 under the no-crossing move rule.

    Every move is computed in backward-position coordinates from the root and never
    wraps, so a run's length counts slots on the root-free arc. Chaining a new constant
    immediately after ``p_1`` leaves those counts alone, which is what makes the bound
    unconditional: (a) holds at exactly 2 on every star, not only on the ones whose
    sweep happens to be rendered backward.

    (b) is stated at 3 rather than 2 because of the signature-shift channel
    (Remark 6.5): the inserted closing fact changes ``sig(x)``, which can move ``x``
    later inside its run of *identical* ``V`` tokens. That is invisible in the
    V-sequence but it shifts ``pos``, so one further run boundary moves. When ``x``
    keeps its creation position the bound is 2, and measurably 1.
    """

    N_STARS = 100

    def _stars(self) -> list[list[tuple[frozenset[int], int]]]:
        rng = random.Random(2026)
        return [_build_star(rng, rng.randint(20, 40), 5) for _ in range(self.N_STARS)]

    def test_leaf_insertion_costs_at_most_two(self) -> None:
        """Proposition 6.3(a), unconditional under the no-crossing rule."""
        rng = random.Random(31)
        costs: list[float] = []
        for facts in self._stars():
            n_leaves = max(max(m) for m, _ in facts)
            H = _star(n_leaves + 1, facts)
            H2 = _star(n_leaves + 2, [*facts, (frozenset({0, n_leaves + 1}), rng.randrange(5))])
            costs.append(_token_distance(H, H2))
        assert len(costs) == self.N_STARS
        assert max(costs) <= 2, f"max leaf-insertion cost {max(costs)}"

    def test_closing_fact_insertion_costs_at_most_three(self) -> None:
        """Proposition 6.3(b): <= 3 when a later leaf is targeted, <= 2 when x stays put."""
        rng = random.Random(32)
        later: list[float] = []
        position_kept: list[float] = []
        for facts in self._stars():
            n_leaves = max(max(m) for m, _ in facts)
            H = _star(n_leaves + 1, facts)
            walk = ordered_word(H)
            index = {v: i for i, v in enumerate(walk.creation_order)}
            candidates = []
            for x in range(1, n_leaves + 1):
                present = {label for m, label in facts if m == frozenset({0, x})}
                above = [q for q in range(5) if q > min(present) and q not in present]
                # The proposition needs a closing fact already targeting x or a later
                # leaf, so the new C splits a run instead of extending the sweep.
                targeted = any(
                    index[z] >= index[x] and H.degree(z) >= 2 for z in range(1, n_leaves + 1)
                )
                if above and targeted:
                    candidates.append((x, above[0]))
            if not candidates:
                continue
            x, predicate = rng.choice(candidates)
            H2 = _star(n_leaves + 1, [*facts, (frozenset({0, x}), predicate)])
            cost = _token_distance(H, H2)
            later.append(cost)
            if walk.creation_order.index(x) == ordered_word(H2).creation_order.index(x):
                position_kept.append(cost)
        assert len(later) >= 80, f"only {len(later)} stars offered a later-targeted leaf"
        assert max(later) <= 3, f"max later-targeted cost {max(later)}"
        assert position_kept, "no star kept x's creation position"
        assert max(position_kept) <= 2, f"max position-kept cost {max(position_kept)}"

    def test_the_star_sweep_never_crosses_the_root(self) -> None:
        """On a binary star the C-phase is one monotone backward sweep: no ``P`` at all."""
        for facts in self._stars():
            n_leaves = max(max(m) for m, _ in facts)
            H = _star(n_leaves + 1, facts)
            assert not any(isinstance(t, TokenP) for t in ordered_word(H).tokens)

    def test_general_star_response_is_local_in_the_median(self) -> None:
        """The measurement the article reports beside the two bounds."""
        import statistics

        rng = random.Random(33)
        costs: list[float] = []
        for facts in self._stars():
            n_leaves = max(max(m) for m, _ in facts)
            H = _star(n_leaves + 1, facts)
            H2 = _star(n_leaves + 2, [*facts, (frozenset({0, n_leaves + 1}), rng.randrange(5))])
            costs.append(_token_distance(H, H2))
        assert statistics.median(costs) <= 2.0
        assert sum(1 for cost in costs if cost <= 2) / len(costs) == 1.0


# ---------------------------------------------------------------------------
# 7. Golden pins
# ---------------------------------------------------------------------------

# (len(word), sha256(word)) per (policy, fixture), computed 2026-09-06 by the emitter
# of this commit. A pin failing means the EMITTER CHANGED DEFINITION -- a different
# canonical form, not a test to refresh. Stop and re-read the design record
# (docs/article/D_ART3/experiments/ISAL_VARIANT_DESIGN.md) and Definition 3.2 of
# theorem_c_ordered_walk.tex before touching a number here.
#
# This table is the ordered walk's own. It is NOT the w*_c table of
# test_wstar_c_frozen.py and the two must never be reconciled: w*_c is the
# tie-complete lex-min, w_o is the walk along nauty's order -- different strings.
_GOLDEN_WORDS: dict[str, tuple[int, str]] = {
    "rank0|cyclic_triple_13_014": (
        530,
        "afe4e5d1970c7576b4e56d1e34706d89ff9afc5aebe777ab9fa99ef93993fba6",
    ),
    "rank0|cyclic_triple_13_016": (
        482,
        "f6f64e6131389dd19d1d45d94657555b8fdc1eb45b03e6a4f539a0068e8be62c",
    ),
    "rank0|fano_plane": (
        146,
        "0be77c374248f1af3f9ce69fb4bd293642100cdb40139d0a047a7750db90cd05",
    ),
    "rank0|gq_2_2_doily": (
        431,
        "815e8e939d4b7b35e566c5d32f602a1f3194061c59772e513eb7642136f3fb8e",
    ),
    "rank0|n4_pair_h1": (
        38,
        "06dd2dde1d004dc400ac894d2642ed82334c7a8d0b3fe8fd1f4b717b38f1d8ee",
    ),
    "rank0|n4_pair_h2": (
        42,
        "efc5944af346557c58d4715699ae72b97235d1645875c352b8ef6deaff40e444",
    ),
    "rank0|sts_9": (
        257,
        "99fca7697b604a4976fc09aea27087c1a7cb2d75d00f40fa62d84f8cf23a644a",
    ),
    "rank0|sts_catalog_13_0": (
        692,
        "fea7bdc4ad042a7317c4f9ec40a69278cbbd5fbe91db0f44546529cb24cf0b6d",
    ),
    "rank0|sts_catalog_13_1": (
        687,
        "2ea31445a75497128a70b3d04f5d73ad8d1c87b0051a9853521f69310816b97d",
    ),
    "rank0|sts_catalog_15_0": (
        901,
        "bbb2746bba5720d10d735cf1adfa8d104705fbe00311403851460874189d65cf",
    ),
    "rank0|sts_catalog_7_0": (
        146,
        "0be77c374248f1af3f9ce69fb4bd293642100cdb40139d0a047a7750db90cd05",
    ),
    "rank0|sts_catalog_9_0": (
        257,
        "99fca7697b604a4976fc09aea27087c1a7cb2d75d00f40fa62d84f8cf23a644a",
    ),
    "rank|cyclic_triple_13_014": (
        505,
        "3e76324a3e7142b86f11eb0abb3ee7033a9dc5aae18a2cdb85f262a5ee8a46ca",
    ),
    "rank|cyclic_triple_13_016": (
        482,
        "f6f64e6131389dd19d1d45d94657555b8fdc1eb45b03e6a4f539a0068e8be62c",
    ),
    "rank|fano_plane": (
        146,
        "0be77c374248f1af3f9ce69fb4bd293642100cdb40139d0a047a7750db90cd05",
    ),
    "rank|gq_2_2_doily": (
        431,
        "815e8e939d4b7b35e566c5d32f602a1f3194061c59772e513eb7642136f3fb8e",
    ),
    "rank|n4_pair_h1": (
        28,
        "0cdb1b7011fb618a4eecc1d7880aa6880eff12df395aa7cb7f20799fe172e672",
    ),
    "rank|n4_pair_h2": (
        42,
        "1dbc53280f2457a0255272dbb23bf9bfbc9db52ac86921ae24caefa4a5a4cbc2",
    ),
    "rank|sts_9": (
        257,
        "99fca7697b604a4976fc09aea27087c1a7cb2d75d00f40fa62d84f8cf23a644a",
    ),
    "rank|sts_catalog_13_0": (
        692,
        "fea7bdc4ad042a7317c4f9ec40a69278cbbd5fbe91db0f44546529cb24cf0b6d",
    ),
    "rank|sts_catalog_13_1": (
        687,
        "2ea31445a75497128a70b3d04f5d73ad8d1c87b0051a9853521f69310816b97d",
    ),
    "rank|sts_catalog_15_0": (
        901,
        "bbb2746bba5720d10d735cf1adfa8d104705fbe00311403851460874189d65cf",
    ),
    "rank|sts_catalog_7_0": (
        146,
        "0be77c374248f1af3f9ce69fb4bd293642100cdb40139d0a047a7750db90cd05",
    ),
    "rank|sts_catalog_9_0": (
        257,
        "99fca7697b604a4976fc09aea27087c1a7cb2d75d00f40fa62d84f8cf23a644a",
    ),
    "struct|cyclic_triple_13_014": (
        530,
        "afe4e5d1970c7576b4e56d1e34706d89ff9afc5aebe777ab9fa99ef93993fba6",
    ),
    "struct|cyclic_triple_13_016": (
        482,
        "f6f64e6131389dd19d1d45d94657555b8fdc1eb45b03e6a4f539a0068e8be62c",
    ),
    "struct|fano_plane": (
        146,
        "0be77c374248f1af3f9ce69fb4bd293642100cdb40139d0a047a7750db90cd05",
    ),
    "struct|gq_2_2_doily": (
        431,
        "815e8e939d4b7b35e566c5d32f602a1f3194061c59772e513eb7642136f3fb8e",
    ),
    "struct|n4_pair_h1": (
        28,
        "0cdb1b7011fb618a4eecc1d7880aa6880eff12df395aa7cb7f20799fe172e672",
    ),
    "struct|n4_pair_h2": (
        42,
        "1dbc53280f2457a0255272dbb23bf9bfbc9db52ac86921ae24caefa4a5a4cbc2",
    ),
    "struct|sts_9": (
        257,
        "99fca7697b604a4976fc09aea27087c1a7cb2d75d00f40fa62d84f8cf23a644a",
    ),
    "struct|sts_catalog_13_0": (
        692,
        "fea7bdc4ad042a7317c4f9ec40a69278cbbd5fbe91db0f44546529cb24cf0b6d",
    ),
    "struct|sts_catalog_13_1": (
        687,
        "2ea31445a75497128a70b3d04f5d73ad8d1c87b0051a9853521f69310816b97d",
    ),
    "struct|sts_catalog_15_0": (
        901,
        "bbb2746bba5720d10d735cf1adfa8d104705fbe00311403851460874189d65cf",
    ),
    "struct|sts_catalog_7_0": (
        146,
        "0be77c374248f1af3f9ce69fb4bd293642100cdb40139d0a047a7750db90cd05",
    ),
    "struct|sts_catalog_9_0": (
        257,
        "99fca7697b604a4976fc09aea27087c1a7cb2d75d00f40fa62d84f8cf23a644a",
    ),
}


def _pin(word: str) -> tuple[int, str]:
    return len(word), hashlib.sha256(word.encode()).hexdigest()


@pytest.mark.parametrize("key", sorted(_GOLDEN_WORDS))
def test_ordered_word_is_pinned(key: str, design_fixtures: dict[str, SparseHypergraph]) -> None:
    policy_name, fixture_name = key.split("|")
    word = serialize(
        ordered_word(design_fixtures[fixture_name], policy=POLICIES[policy_name]).tokens
    )
    assert _pin(word) == _GOLDEN_WORDS[key]


def test_the_pins_are_not_the_wstar_c_pins() -> None:
    """A guard against ever reconciling the two tables: they encode different forms."""
    from isalhg.core.canonical import canonical_string

    H = designs.fano_plane()
    assert serialize(ordered_word(H).tokens) != canonical_string(H, k=3, algorithm="canonical")


# ---------------------------------------------------------------------------
# 8. Policies and error paths
# ---------------------------------------------------------------------------


class TestPolicyAndErrors:
    def test_policy_names(self) -> None:
        assert OrderedWalkPolicy().name == "struct"
        assert OrderedWalkPolicy(rank_first=True).name == "rank"
        assert OrderedWalkPolicy(root_rule="rank0").name == "rank0"
        for name, policy in POLICIES.items():
            assert policy.name == name

    def test_empty_hypergraph_is_degenerate(self) -> None:
        with pytest.raises(DegenerateHypergraphError):
            ordered_walk(SparseHypergraph(0), ())

    def test_disconnected_input_is_refused(self) -> None:
        H = SparseHypergraph(4, [frozenset({0, 1}), frozenset({2, 3})])
        with pytest.raises(DisconnectedHypergraphError):
            ordered_walk(H, (0, 1, 2, 3))

    def test_malformed_ranks_are_refused(self) -> None:
        H = designs.fano_plane()
        with pytest.raises(OrderedWalkError):
            ordered_walk(H, (0, 1, 2))
        with pytest.raises(OrderedWalkError):
            ordered_walk(H, (0, 0, 1, 2, 3, 4, 5))

    def test_single_constant_emits_the_empty_word(self) -> None:
        H = SparseHypergraph(1)
        result = ordered_walk(H, (0,), k=2)
        assert result.tokens == ()
        assert result.creation_order == (0,)
        assert serialize(result.tokens) == ""

    def test_symbols_carry_the_seed_only_on_a_non_trivial_vocabulary(self) -> None:
        trivial = designs.fano_plane()
        assert ordered_symbols(trivial) == ordered_word(trivial).tokens

        labelled = SparseHypergraph(
            3,
            [frozenset({0, 1}), frozenset({1, 2})],
            n_vertex_labels=2,
            n_edge_labels=1,
            vertex_labels=[1, 0, 0],
        )
        symbols = ordered_symbols(labelled)
        assert symbols[0] == ("seed", ordered_word(labelled).root_label)
        assert symbols[1:] == ordered_word(labelled).tokens
