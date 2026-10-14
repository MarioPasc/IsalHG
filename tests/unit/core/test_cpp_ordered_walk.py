"""The C++ ordered-walk emitter is the Python one, token for token.

The port is a *transcription*, not a reimplementation: every ordering decision in
``src/isalhg/core/_native/src/ordered_walk.cpp`` mirrors a Python tuple comparison in
``src/isalhg/core/algorithms/ordered_walk.py``. The only claim worth testing is
therefore agreement, and it is tested three ways:

1. **The golden table.** The ``(len, sha256)`` pins of ``test_ordered_walk.py`` --
   the ordered walk's own definitional record -- reproduced through ``backend="cpp"``.
   The table is *imported*, never copied: a pin edited there fails here too.
2. **Differential.** Token sequences, creation orders, roots and root types on the
   shared fixtures, on the random corpus of the reference file, and on binary stars
   (the substrate Proposition 6.3's locality claim is read off), for all three
   policies. Errors too: both backends refuse the same inputs the same way.
3. **The claims still hold through the port.** Round trip against pynauty and
   invariance under relabelling, re-pinned on the C++ path -- so a defect that
   preserved agreement with a broken Python emitter would still be caught.

Corpus-scale agreement on the two frozen knowledge bases lives in
``tests/integration/test_cpp_ordered_walk_corpus.py``.
"""

from __future__ import annotations

import hashlib
import importlib.util
import random
from pathlib import Path

import pytest

from isalhg.core.algorithms.ordered_walk import (
    _ORDERED_WALK_BACKENDS,
    OrderedWalkPolicy,
    OrderedWalkResult,
    ordered_walk,
)
from isalhg.core.canonical import required_k
from isalhg.core.instructions import serialize
from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.core.string_to_hypergraph import string_to_hypergraph
from isalhg.errors import DegenerateHypergraphError, DisconnectedHypergraphError

pytestmark = pytest.mark.unit

pytest.importorskip("pynauty")

from isalhg.iso_backends.canonical_order import canonical_ranks  # noqa: E402
from isalhg.iso_backends.isal_ordered import POLICIES, ordered_word  # noqa: E402
from isalhg.iso_backends.pynauty_levi import PynautyLeviBackend  # noqa: E402

POLICY_NAMES = ("struct", "rank", "rank0")

_N_RANDOM = 2000
_N_STARS = 400
_N_ROUNDTRIP = 300
_N_RELABELLINGS = 50


def _load_reference_module() -> object:
    """Import ``test_ordered_walk.py`` by path -- it owns the golden table and corpora."""
    path = Path(__file__).with_name("test_ordered_walk.py")
    spec = importlib.util.spec_from_file_location("_ordered_walk_reference_tests", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_REFERENCE = _load_reference_module()


@pytest.fixture(scope="module")
def design_fixtures() -> dict[str, SparseHypergraph]:
    return _REFERENCE._design_fixtures()  # type: ignore[attr-defined]


@pytest.fixture(scope="module")
def random_corpus() -> list[SparseHypergraph]:
    """The reference file's own random corpus, under its pinned seed."""
    rng = random.Random(20260906)
    return [_REFERENCE._random_connected(rng) for _ in range(_N_RANDOM)]  # type: ignore[attr-defined]


@pytest.fixture(scope="module")
def star_corpus() -> list[SparseHypergraph]:
    """Random binary stars -- the substrate of the star-locality proposition."""
    rng = random.Random(20260907)
    corpus: list[SparseHypergraph] = []
    for _ in range(_N_STARS):
        leaves = rng.randint(1, 12)
        n = leaves + 1
        corpus.append(
            SparseHypergraph(
                n,
                [frozenset({0, leaf}) for leaf in range(1, n)],
                n_vertex_labels=3,
                n_edge_labels=3,
                vertex_labels=[rng.randrange(3) for _ in range(n)],
                edge_labels=[rng.randrange(3) for _ in range(leaves)],
            )
        )
    return corpus


def _both(H: SparseHypergraph, policy: OrderedWalkPolicy) -> tuple[OrderedWalkResult, ...]:
    ranks = canonical_ranks(H)
    return (
        ordered_walk(H, ranks, policy=policy, backend="python"),
        ordered_walk(H, ranks, policy=policy, backend="cpp"),
    )


def _assert_identical(name: str, left: OrderedWalkResult, right: OrderedWalkResult) -> None:
    assert left.tokens == right.tokens, f"{name}: tokens differ"
    assert left.creation_order == right.creation_order, f"{name}: creation order differs"
    assert left.root == right.root, f"{name}: root differs"
    assert left.root_label == right.root_label, f"{name}: root type differs"


# ---------------------------------------------------------------------------
# 0. The backend is wired up and is the default
# ---------------------------------------------------------------------------


class TestBackendRegistration:
    def test_the_extension_is_registered(self) -> None:
        assert "cpp" in _ORDERED_WALK_BACKENDS, "the C++ emitter is not built into this env"

    def test_the_default_is_the_extension(self) -> None:
        H = SparseHypergraph(3, [frozenset({0, 1}), frozenset({1, 2})])
        ranks = canonical_ranks(H)
        assert ordered_walk(H, ranks) == ordered_walk(H, ranks, backend="cpp")

    def test_an_unknown_backend_is_refused(self) -> None:
        H = SparseHypergraph(2, [frozenset({0, 1})])
        with pytest.raises(ValueError, match="unknown backend"):
            ordered_walk(H, (0, 1), backend="rust")


# ---------------------------------------------------------------------------
# 1. The golden table, through the C++ path
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("key", sorted(_REFERENCE._GOLDEN_WORDS))  # type: ignore[attr-defined]
def test_cpp_reproduces_the_golden_pins(
    key: str, design_fixtures: dict[str, SparseHypergraph]
) -> None:
    """The definitional record of the emitter, recomputed on the engine.

    A failure here means the port changed the canonical form -- not that the pin
    needs refreshing. The table belongs to ``test_ordered_walk.py``.
    """
    policy_name, fixture_name = key.split("|")
    H = design_fixtures[fixture_name]
    result = ordered_walk(H, canonical_ranks(H), policy=POLICIES[policy_name], backend="cpp")
    word = serialize(result.tokens)
    pin = (len(word), hashlib.sha256(word.encode()).hexdigest())
    assert pin == _REFERENCE._GOLDEN_WORDS[key]  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# 2. Differential
# ---------------------------------------------------------------------------


class TestDifferential:
    @pytest.mark.parametrize("policy_name", POLICY_NAMES)
    def test_design_fixtures(
        self, policy_name: str, design_fixtures: dict[str, SparseHypergraph]
    ) -> None:
        policy = POLICIES[policy_name]
        for name, H in design_fixtures.items():
            _assert_identical(f"{policy_name}/{name}", *_both(H, policy))

    @pytest.mark.parametrize("policy_name", POLICY_NAMES)
    def test_random_corpus(self, policy_name: str, random_corpus: list[SparseHypergraph]) -> None:
        policy = POLICIES[policy_name]
        for index, H in enumerate(random_corpus):
            _assert_identical(f"{policy_name}/random[{index}]", *_both(H, policy))

    @pytest.mark.parametrize("policy_name", POLICY_NAMES)
    def test_binary_stars(self, policy_name: str, star_corpus: list[SparseHypergraph]) -> None:
        policy = POLICIES[policy_name]
        for index, H in enumerate(star_corpus):
            _assert_identical(f"{policy_name}/star[{index}]", *_both(H, policy))

    def test_shared_conftest_fixtures(
        self,
        trivial_hypergraph: SparseHypergraph,
        single_edge_hypergraph: SparseHypergraph,
        fano_plane: SparseHypergraph,
        sts_9: SparseHypergraph,
        gq_2_2_doily: SparseHypergraph,
        qin_fig1_hypergraph: SparseHypergraph,
        cyclic_triple_13_pair: tuple[SparseHypergraph, SparseHypergraph],
        iso_pair_small: tuple[SparseHypergraph, SparseHypergraph, list[int]],
        non_iso_pair_small: tuple[SparseHypergraph, SparseHypergraph],
    ) -> None:
        corpus = [
            trivial_hypergraph,
            single_edge_hypergraph,
            fano_plane,
            sts_9,
            gq_2_2_doily,
            qin_fig1_hypergraph,
            *cyclic_triple_13_pair,
            iso_pair_small[0],
            iso_pair_small[1],
            *non_iso_pair_small,
        ]
        for policy_name in POLICY_NAMES:
            policy = POLICIES[policy_name]
            for index, H in enumerate(corpus):
                _assert_identical(f"{policy_name}/conftest[{index}]", *_both(H, policy))


class TestErrorParity:
    """Both backends refuse the same inputs; the domain checks precede the dispatch."""

    @pytest.mark.parametrize("backend", ["python", "cpp"])
    def test_empty_hypergraph(self, backend: str) -> None:
        with pytest.raises(DegenerateHypergraphError):
            ordered_walk(SparseHypergraph(0), (), backend=backend)

    @pytest.mark.parametrize("backend", ["python", "cpp"])
    def test_disconnected_input(self, backend: str) -> None:
        H = SparseHypergraph(4, [frozenset({0, 1}), frozenset({2, 3})])
        with pytest.raises(DisconnectedHypergraphError):
            ordered_walk(H, (0, 1, 2, 3), backend=backend)

    @pytest.mark.parametrize("backend", ["python", "cpp"])
    def test_malformed_ranks(self, backend: str) -> None:
        from isalhg.core.algorithms.ordered_walk import OrderedWalkError
        from isalhg.datasets.synthetic import designs

        H = designs.fano_plane()
        with pytest.raises(OrderedWalkError):
            ordered_walk(H, (0, 1, 2), backend=backend)
        with pytest.raises(OrderedWalkError):
            ordered_walk(H, (0, 0, 1, 2, 3, 4, 5), backend=backend)


# ---------------------------------------------------------------------------
# 3. The claims, re-pinned on the C++ path
# ---------------------------------------------------------------------------


class TestRoundTripThroughTheExtension:
    """``S2H(w_o(H); k, root type) ~ H``, decided by pynauty (Lemma C.3)."""

    @staticmethod
    def _decode(H: SparseHypergraph, policy: OrderedWalkPolicy) -> SparseHypergraph:
        result = ordered_walk(H, canonical_ranks(H), policy=policy, backend="cpp")
        return string_to_hypergraph(
            serialize(result.tokens),
            k=required_k(H),
            n_vertex_labels=H.n_vertex_labels,
            n_edge_labels=H.n_edge_labels,
            seed_label=result.root_label,
        )

    @pytest.mark.parametrize("policy_name", POLICY_NAMES)
    def test_design_fixtures(
        self, policy_name: str, design_fixtures: dict[str, SparseHypergraph]
    ) -> None:
        backend = PynautyLeviBackend()
        policy = POLICIES[policy_name]
        for name, H in design_fixtures.items():
            assert backend.are_isomorphic(H, self._decode(H, policy)), f"{policy_name}/{name}"

    @pytest.mark.parametrize("policy_name", POLICY_NAMES)
    def test_random_instances(
        self, policy_name: str, random_corpus: list[SparseHypergraph]
    ) -> None:
        backend = PynautyLeviBackend()
        policy = POLICIES[policy_name]
        for index, H in enumerate(random_corpus[:_N_ROUNDTRIP]):
            assert backend.are_isomorphic(H, self._decode(H, policy)), (
                f"{policy_name}/random[{index}]"
            )


class TestInvarianceThroughTheExtension:
    """Relabelling the constants leaves ``(root type, word)`` untouched."""

    @staticmethod
    def _fingerprint(H: SparseHypergraph, policy: OrderedWalkPolicy) -> tuple[int, str]:
        result = ordered_walk(H, canonical_ranks(H), policy=policy, backend="cpp")
        return result.root_label, serialize(result.tokens)

    @pytest.mark.parametrize("policy_name", POLICY_NAMES)
    def test_design_fixtures(
        self, policy_name: str, design_fixtures: dict[str, SparseHypergraph]
    ) -> None:
        policy = POLICIES[policy_name]
        rng = random.Random(11235)
        for name, H in design_fixtures.items():
            expected = self._fingerprint(H, policy)
            for _ in range(_N_RELABELLINGS):
                sigma = list(range(H.n_nodes))
                rng.shuffle(sigma)
                assert self._fingerprint(permute(H, sigma), policy) == expected, (
                    f"{policy_name}/{name}"
                )

    @pytest.mark.parametrize("policy_name", POLICY_NAMES)
    def test_random_instances(
        self, policy_name: str, random_corpus: list[SparseHypergraph]
    ) -> None:
        policy = POLICIES[policy_name]
        rng = random.Random(58132)
        for index, H in enumerate(random_corpus[:_N_ROUNDTRIP]):
            expected = self._fingerprint(H, policy)
            for _ in range(_N_RELABELLINGS):
                sigma = list(range(H.n_nodes))
                rng.shuffle(sigma)
                assert self._fingerprint(permute(H, sigma), policy) == expected, (
                    f"{policy_name}/random[{index}]"
                )


class TestKIndependenceThroughTheExtension:
    """The word is the same for every admissible pointer count (claim 5)."""

    @pytest.mark.parametrize("policy_name", POLICY_NAMES)
    def test_every_admissible_k(
        self, policy_name: str, design_fixtures: dict[str, SparseHypergraph]
    ) -> None:
        policy = POLICIES[policy_name]
        for name, H in design_fixtures.items():
            ranks = canonical_ranks(H)
            base = ordered_walk(H, ranks, policy=policy, backend="cpp").tokens
            for k in range(required_k(H), 11):
                assert ordered_walk(H, ranks, policy=policy, k=k, backend="cpp").tokens == base, (
                    f"{policy_name}/{name} at k={k}"
                )


# ---------------------------------------------------------------------------
# 4. The public entry points inherit the default
# ---------------------------------------------------------------------------


class TestEntryPoints:
    @pytest.mark.parametrize("policy_name", POLICY_NAMES)
    def test_ordered_word_threads_the_backend(
        self, policy_name: str, design_fixtures: dict[str, SparseHypergraph]
    ) -> None:
        policy = POLICIES[policy_name]
        for name, H in design_fixtures.items():
            assert ordered_word(H, policy=policy, backend="cpp") == ordered_word(
                H, policy=policy, backend="python"
            ), f"{policy_name}/{name}"

    def test_the_distance_arm_threads_the_backend(self) -> None:
        from isalhg.metric_space.distances.isal_ordered import IsalOrderedLevenshtein

        H1 = SparseHypergraph(4, [frozenset({0, 1, 2}), frozenset({0, 1, 3})])
        H2 = SparseHypergraph(4, [frozenset({0, 1}), frozenset({1, 2}), frozenset({2, 3})])
        for policy_name in POLICY_NAMES:
            cpp = IsalOrderedLevenshtein(policy_name, backend="cpp")
            py = IsalOrderedLevenshtein(policy_name, backend="python")
            assert cpp.fingerprint(H1) == py.fingerprint(H1)
            assert cpp.pairwise(H1, H2) == py.pairwise(H1, H2)
