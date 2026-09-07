"""The Isal instruction-word arms, as the TKDE runners reach them.

Five things that can silently go wrong between an emitter and a campaign row,
each pinned here:

1. **Arm resolution.** Every name the runners put in an arm list resolves to a
   distance, and each one reports the name it was asked for. An arm whose
   engine has not landed is *reported* absent, never silently dropped by a
   registry that swallows the ImportError.
2. **Budget behaviour.** ``engine_word`` kills a child that overruns and returns
   a censored result rather than a value, and ``pointer_word`` is still the
   ``engine="cpp"`` case of it.
3. **``d_instr``.** The instruction-granular response on a hand-built pair,
   where the answer can be counted by hand rather than trusted.
4. **``aut_bucket``.** Fano's ``|Aut|`` is 168, which is ``<1e3``.
5. **RQ6's ordered-walk validity claim.** Proposition 5.1 says every word of the
   alphabet decodes, and to a *connected* hypergraph; a sample of n-gram
   outputs asserts both.

The two arms whose engine ``orbit-prune`` is still landing (``wstar_rank``,
``wstar_orbit``) skip with the reason rather than fail, so this file is green on
both sides of that merge.
"""

from __future__ import annotations

import random
import time
from typing import Any

import pytest

from experiments.tkde.budget import (
    ENGINES,
    TkdeBudgetError,
    cpp_fork_is_healthy,
    engine_word,
    pointer_word,
    run_with_budget_detail,
    symbol_distance,
)
from experiments.tkde.rq1 import (
    BUDGETED_ARMS,
    DEFAULT_ARMS,
    OW_ARMS,
    arm_is_available,
    aut_bucket,
    aut_order,
    instruction_symbols,
    member_word,
)
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.metric_space.registry import get_distance

pytestmark = pytest.mark.integration

ORBIT_ARMS: tuple[str, ...] = ("wstar_rank", "wstar_orbit")
ORBIT_SKIP = "orbit-prune not merged"
POISONED_SKIP = (
    "the C++ engine has already run in this pytest process, so a forked child "
    "deadlocks on it (see budget.cpp_fork_is_healthy)"
)


def _orbit_available(arm: str) -> bool:
    return arm_is_available(arm)[0]


def _require_healthy_fork() -> None:
    """Skip when this process can no longer fork a working C++ canonicalizer.

    Running this file alone, it can; running it after a suite that exercised the
    engine directly, it cannot, and the budget would report a censoring that
    never happened. The defect itself is pinned by
    :meth:`TestBudget.test_a_poisoned_process_refuses_rather_than_censoring`.
    """
    if not cpp_fork_is_healthy():
        pytest.skip(POISONED_SKIP)


@pytest.fixture
def two_facts() -> SparseHypergraph:
    """Four constants, two facts sharing ``{0, 1}`` -- small enough to count by hand."""
    return SparseHypergraph(4, [frozenset({0, 1, 2}), frozenset({0, 1, 3})])


# ---------------------------------------------------------------------------
# 1. Arm resolution
# ---------------------------------------------------------------------------


class TestArmResolution:
    """Every arm the runners name is reachable, or reported absent by name."""

    @pytest.mark.parametrize("arm", OW_ARMS)
    def test_ordered_walk_arms_resolve(self, arm: str, two_facts: SparseHypergraph) -> None:
        distance = get_distance(arm)
        assert distance.name == arm
        fingerprint = distance.fingerprint(two_facts)
        assert isinstance(fingerprint, tuple)
        assert fingerprint, "an ordered-walk word of a non-empty hypergraph is non-empty"

    @pytest.mark.parametrize("arm", ORBIT_ARMS)
    def test_engine_arms_resolve(self, arm: str) -> None:
        # The distance object must exist even before its engine lands: only the
        # call is allowed to fail, and it must name the arm when it does.
        distance = get_distance(arm)
        assert distance.name == arm
        available, reason = arm_is_available(arm)
        if not available:
            assert arm in reason
            pytest.skip(f"{ORBIT_SKIP}: {reason}")

    @pytest.mark.parametrize("arm", ORBIT_ARMS)
    def test_engine_arms_fingerprint(self, arm: str, two_facts: SparseHypergraph) -> None:
        if not _orbit_available(arm):
            pytest.skip(ORBIT_SKIP)
        fingerprint = get_distance(arm).fingerprint(two_facts)
        assert isinstance(fingerprint, tuple)
        assert fingerprint

    def test_rq1_default_arms_are_all_known(self) -> None:
        for arm in DEFAULT_ARMS:
            available, reason = arm_is_available(arm)
            if not available:
                assert arm in ORBIT_ARMS, f"{arm} is unavailable for an unexpected reason: {reason}"

    def test_budgeted_arms_are_the_two_unbounded_engines(self) -> None:
        # wstar_rank must NOT be here: budgeting it would fork thousands of
        # times for a computation that finishes in milliseconds.
        assert set(BUDGETED_ARMS) == {"isalhg_levenshtein", "wstar_orbit"}
        assert set(BUDGETED_ARMS.values()) <= set(ENGINES)


# ---------------------------------------------------------------------------
# 2. The budget
# ---------------------------------------------------------------------------


def _slow(seconds: float) -> str:
    """A deliberately slow callable, to be killed by the budget."""
    time.sleep(seconds)
    return "finished"


class TestBudget:
    """A budgeted call that overruns is censored, not waited for."""

    def test_slow_callable_is_killed_and_reported_censored(self) -> None:
        started = time.monotonic()
        result = run_with_budget_detail(_slow, (30.0,), seconds=0.5)
        elapsed = time.monotonic() - started
        assert result.censored is True
        assert result.value is None
        assert result.error is None
        assert not result.ok
        assert elapsed < 15.0, "the child was waited for instead of killed"

    def test_fast_callable_returns_its_value(self) -> None:
        result = run_with_budget_detail(_slow, (0.0,), seconds=10.0)
        assert result.ok
        assert result.value == "finished"

    def test_engine_word_cpp_matches_pointer_word(self, two_facts: SparseHypergraph) -> None:
        _require_healthy_fork()
        through_alias = pointer_word(two_facts, 3, 30.0)
        through_engine = engine_word(two_facts, 3, 30.0, engine="cpp")
        assert through_alias.ok and through_engine.ok
        assert through_alias.value == through_engine.value

    def test_a_poisoned_process_refuses_rather_than_censoring(
        self, two_facts: SparseHypergraph
    ) -> None:
        """The measured hazard, pinned: a false censoring must become an error.

        A parent that has already run the C++ canonicalizer leaves the extension
        in a state its forked children deadlock on. The budget cannot tell that
        deadlock from a genuine time-out, so a whole campaign column could read
        "censored" without a single computation having been attempted;
        ``engine_word`` therefore refuses. This runs in a subprocess so the
        poisoning does not leak into the rest of the session.
        """
        import subprocess
        import sys
        import textwrap

        program = textwrap.dedent(
            """
            from isalhg.core.canonical import canonical_string
            from isalhg.core.sparse_hypergraph import SparseHypergraph
            from experiments.tkde.budget import TkdeBudgetError, engine_word

            H = SparseHypergraph(4, [frozenset({0, 1, 2}), frozenset({0, 1, 3})])
            assert engine_word(H, 3, 30.0, engine="cpp").ok, "healthy before"
            canonical_string(H, k=3, algorithm="canonical", backend="cpp")
            try:
                engine_word(H, 3, 30.0, engine="cpp")
            except TkdeBudgetError as exc:
                print("REFUSED:", "already run in this process" in str(exc))
            else:
                print("REFUSED: False")
            """
        )
        completed = subprocess.run(
            [sys.executable, "-c", program],
            capture_output=True,
            text=True,
            timeout=300,
            check=True,
        )
        assert "REFUSED: True" in completed.stdout, completed.stdout + completed.stderr

    def test_engine_word_rejects_an_unknown_engine(self, two_facts: SparseHypergraph) -> None:
        with pytest.raises(TkdeBudgetError, match="unknown engine"):
            engine_word(two_facts, 3, 10.0, engine="nope")

    @pytest.mark.parametrize("arm", ORBIT_ARMS)
    def test_engine_word_reaches_the_python_engines(
        self, arm: str, two_facts: SparseHypergraph
    ) -> None:
        if not _orbit_available(arm):
            pytest.skip(ORBIT_SKIP)
        engine = BUDGETED_ARMS.get(arm, "rank")
        result = engine_word(two_facts, 3, 60.0, engine=engine)
        assert result.ok, result.error
        word, seed_label = result.value
        assert isinstance(word, str)
        assert isinstance(seed_label, int)

    def test_wstar_orbit_reproduces_the_frozen_word(self, two_facts: SparseHypergraph) -> None:
        # Orbit pruning is value-preserving, so the orbit engine's word IS w*_c.
        if not _orbit_available("wstar_orbit"):
            pytest.skip(ORBIT_SKIP)
        _require_healthy_fork()
        cpp = engine_word(two_facts, 3, 60.0, engine="cpp")
        orbit = engine_word(two_facts, 3, 60.0, engine="orbit")
        assert cpp.ok and orbit.ok
        assert cpp.value == orbit.value


# ---------------------------------------------------------------------------
# 3. d_instr on a pair whose answer can be counted
# ---------------------------------------------------------------------------


class TestInstructionDistance:
    """``d_instr`` measures one symbol per instruction, for every arm shape."""

    def test_identical_members_are_at_distance_zero(self, two_facts: SparseHypergraph) -> None:
        for arm in (*OW_ARMS, "nauty_cert_rows", "fact_rank"):
            word, _secs, censored = member_word(arm, two_facts, None, k=3, budget=30.0)
            assert not censored
            symbols = instruction_symbols(arm, word, augment=False)
            assert symbols is not None
            assert symbol_distance(symbols, symbols) == 0

    def test_one_added_fact_is_a_positive_distance(self, two_facts: SparseHypergraph) -> None:
        edited = SparseHypergraph(
            5, [frozenset({0, 1, 2}), frozenset({0, 1, 3}), frozenset({0, 4})]
        )
        for arm in (*OW_ARMS, "nauty_cert_rows", "fact_rank"):
            base_word, _, _ = member_word(arm, two_facts, None, k=3, budget=30.0)
            edit_word, _, _ = member_word(arm, edited, None, k=3, budget=30.0)
            left = instruction_symbols(arm, base_word, augment=False)
            right = instruction_symbols(arm, edit_word, augment=False)
            assert left is not None and right is not None
            assert symbol_distance(left, right) > 0

    def test_budgeted_arm_instructions_carry_the_seed_prefix(
        self, two_facts: SparseHypergraph
    ) -> None:
        _require_healthy_fork()
        word, _secs, censored = member_word("isalhg_levenshtein", two_facts, None, k=3, budget=30.0)
        assert not censored
        bare = instruction_symbols("isalhg_levenshtein", word, augment=False)
        prefixed = instruction_symbols("isalhg_levenshtein", word, augment=True)
        assert bare is not None and prefixed is not None
        assert len(prefixed) == len(bare) + 1
        assert prefixed[0][0] == "seed"

    def test_a_missing_word_yields_no_symbols(self) -> None:
        assert instruction_symbols("isal_ow_struct", None, augment=False) is None

    def test_ordered_walk_instructions_are_the_fingerprint(
        self, two_facts: SparseHypergraph
    ) -> None:
        word, _secs, _censored = member_word("isal_ow_struct", two_facts, None, k=3, budget=30.0)
        symbols = instruction_symbols("isal_ow_struct", word, augment=False)
        assert symbols == get_distance("isal_ow_struct").fingerprint(two_facts)


# ---------------------------------------------------------------------------
# 4. The |Aut| stratum
# ---------------------------------------------------------------------------


class TestAutBucket:
    """``|Aut|`` of the coloured Levi graph, and its three strata."""

    def test_fano_has_order_168(self, fano_plane: SparseHypergraph) -> None:
        assert aut_order(fano_plane) == pytest.approx(168.0)

    def test_fano_is_in_the_low_bucket(self, fano_plane: SparseHypergraph) -> None:
        assert aut_bucket(fano_plane) == "<1e3"

    def test_a_rigid_member_is_in_the_low_bucket(self, two_facts: SparseHypergraph) -> None:
        assert aut_bucket(two_facts) == "<1e3"

    def test_a_large_symmetric_member_is_in_a_higher_bucket(self) -> None:
        # Ten pairwise-disjoint-except-at-0 facts: every pair of leaves is
        # interchangeable, so |Aut| = 10! = 3.6e6, in the middle stratum.
        star = SparseHypergraph(11, [frozenset({0, i}) for i in range(1, 11)])
        assert aut_order(star) == pytest.approx(3_628_800.0, rel=1e-6)
        assert aut_bucket(star) == "1e3-1e6"

    def test_the_buckets_are_exhaustive(self) -> None:
        big = SparseHypergraph(21, [frozenset({0, i}) for i in range(1, 21)])
        assert aut_bucket(big) == ">=1e7"


# ---------------------------------------------------------------------------
# 5. RQ6's ordered-walk generation model
# ---------------------------------------------------------------------------


class TestOrderedWalkGeneration:
    """Proposition 5.1, measured: every sampled word decodes, and to one piece."""

    N_SAMPLES = 50

    def _corpus(self) -> list[SparseHypergraph]:
        rng = random.Random(20260906)
        members: list[SparseHypergraph] = []
        while len(members) < 40:
            n = rng.randint(4, 8)
            edges = {
                frozenset(rng.sample(range(n), rng.randint(2, 3))) for _ in range(rng.randint(3, 6))
            }
            H = SparseHypergraph(n, sorted(edges, key=sorted))
            if H.is_connected():
                members.append(H)
        return members

    def test_every_sample_decodes_to_a_connected_hypergraph(self) -> None:
        from experiments.tkde.rq6 import _ow_decode, _ow_tokens, _ow_word
        from isalhg.core.canonical import required_k
        from isalhg.generation.ngram import TokenNGram

        corpus = self._corpus()
        roots_words = [_ow_word(H) for H in corpus]
        model = TokenNGram(order=3).fit([_ow_tokens(word) for _root, word in roots_words])
        k = max(required_k(H) for H in corpus)

        samples = model.sample(self.N_SAMPLES, seed=0, max_len=200)
        assert len(samples) == self.N_SAMPLES

        decoded: list[Any] = []
        for sample in samples:
            decoded.append(_ow_decode(sample, k, 1, 1, 0))
        assert len(decoded) == self.N_SAMPLES, "the decoder is total (Theorem C)"
        assert all(H.is_connected() for H in decoded), "and its image is connected (Prop. 5.1)"

    def test_alignment_interiors_decode_and_are_connected(self) -> None:
        from experiments.tkde.rq6 import _ow_interiors, _ow_word

        corpus = self._corpus()
        left_root, left = _ow_word(corpus[0])
        _right_root, right = _ow_word(corpus[1])
        path_len, n_interior, decoded = _ow_interiors(left, right, 3, 1, 1, left_root)
        assert path_len >= 2
        assert len(decoded) == n_interior, "every interior of the path decoded"
        assert all(connected for _n, _m, connected in decoded)
