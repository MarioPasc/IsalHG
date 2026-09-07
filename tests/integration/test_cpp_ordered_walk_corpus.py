"""The two engines agree on every member of both frozen knowledge bases.

The unit differential (``tests/unit/core/test_cpp_ordered_walk.py``) runs on generated
instances; this file runs the port over the collections the article is actually written
on -- ``wd50k66`` (3,988 members, arity up to 10) and ``ndc_classes`` (1,381 members,
arity median 6) -- exhaustively, all three policies, both backends. It is affordable
where the ``w*_c`` differential is not: both ordered-walk emitters are microseconds per
member, so nothing here needs a sample or a wall-clock guard.

Unlike ``w*_c``, the ordered walk has no Python-side reachability limit: the emitter is
one linear pass per fact, so the pure-Python reference encodes the arity-10 tail that
the displacement search cannot touch. The whole corpus is therefore differential-tested,
not just the guard-satisfying part.

Skipped in full when the frozen collections are absent: they live on the results drive,
not in the repository.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from isalhg.core.algorithms.ordered_walk import OrderedWalkPolicy, ordered_walk
from isalhg.core.instructions import serialize, validate
from isalhg.core.sparse_hypergraph import SparseHypergraph

pytest.importorskip("pynauty")

from isalhg.iso_backends.canonical_order import canonical_ranks  # noqa: E402
from isalhg.iso_backends.isal_ordered import POLICIES  # noqa: E402

pytestmark = pytest.mark.integration

COLLECTIONS = ("wd50k66", "ndc_classes")
POLICY_NAMES = ("struct", "rank", "rank0")


def _corpora_root() -> Path | None:
    raw = os.environ.get("ISALHG_RESULTS_ROOT")
    if not raw:
        return None
    root = Path(raw) / "corpora"
    return root if root.is_dir() else None


def _load(name: str) -> list[SparseHypergraph]:
    root = _corpora_root()
    if root is None or not (root / name).is_dir():
        pytest.skip(f"frozen collection {name!r} not on this machine (set ISALHG_RESULTS_ROOT)")
    from isalhg.datasets.kb.io import read_jsonl

    return [r.to_hypergraph() for r in read_jsonl(root / name).records if r.is_connected()]


@pytest.fixture(scope="module")
def collections() -> dict[str, list[SparseHypergraph]]:
    return {name: _load(name) for name in COLLECTIONS}


def _max_arity(H: SparseHypergraph) -> int:
    return max((len(H.members(e)) for e in H.edges()), default=2)


class TestBackendsAgreeOnTheWholeCorpus:
    @pytest.mark.parametrize("collection", COLLECTIONS)
    @pytest.mark.parametrize("policy_name", POLICY_NAMES)
    def test_every_member(
        self,
        collection: str,
        policy_name: str,
        collections: dict[str, list[SparseHypergraph]],
    ) -> None:
        policy: OrderedWalkPolicy = POLICIES[policy_name]
        members = collections[collection]
        assert members, f"{collection} is empty"
        differing: list[int] = []
        for index, H in enumerate(members):
            ranks = canonical_ranks(H)
            left = ordered_walk(H, ranks, policy=policy, backend="python")
            right = ordered_walk(H, ranks, policy=policy, backend="cpp")
            if (left.tokens, left.creation_order, left.root, left.root_label) != (
                right.tokens,
                right.creation_order,
                right.root,
                right.root_label,
            ):
                differing.append(index)
        assert differing == [], (
            f"{collection}/{policy_name}: {len(differing)} of {len(members)} members differ"
        )


class TestTheCppWordsAreWellFormed:
    """Every emitted program validates in ``Sigma_HG(k)`` at its own pointer count."""

    @pytest.mark.parametrize("collection", COLLECTIONS)
    def test_validate_at_required_k(
        self, collection: str, collections: dict[str, list[SparseHypergraph]]
    ) -> None:
        for index, H in enumerate(collections[collection]):
            k = max(2, _max_arity(H))
            ranks = canonical_ranks(H)
            for policy_name in POLICY_NAMES:
                result = ordered_walk(H, ranks, policy=POLICIES[policy_name], k=k, backend="cpp")
                validate(
                    list(result.tokens),
                    k=k,
                    n_vertex_labels=H.n_vertex_labels,
                    n_edge_labels=H.n_edge_labels,
                )
                assert len(result.creation_order) == H.n_nodes, (
                    f"{collection}[{index}]/{policy_name}: creation order is short"
                )


class TestTheArityTailIsCovered:
    """The differential above really does reach the arity-10 members.

    ``w*_c``'s corpus tests stop below the compiled ``K_MAX`` because the displacement
    search saturates there. The ordered walk has no such tail, and this test fails if a
    future change quietly reintroduces one.
    """

    def test_wd50k66_contains_arity_10_members_and_they_encode(
        self, collections: dict[str, list[SparseHypergraph]]
    ) -> None:
        wide = [H for H in collections["wd50k66"] if _max_arity(H) >= 10]
        assert wide, "no arity-10 member in wd50k66; the claim above is vacuous"
        for H in wide:
            ranks = canonical_ranks(H)
            for policy_name in POLICY_NAMES:
                left = ordered_walk(H, ranks, policy=POLICIES[policy_name], backend="python")
                right = ordered_walk(H, ranks, policy=POLICIES[policy_name], backend="cpp")
                assert serialize(left.tokens) == serialize(right.tokens)
