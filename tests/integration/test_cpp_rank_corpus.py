"""``canonical_rank`` on the knowledge-base corpora, at corpus scale.

The unit differential (``tests/unit/core/test_cpp_rank.py``) runs on generated
instances the Python reference can still encode. This file runs on the two
frozen KB collections the arm is actually for, and asks the questions the
generated instances cannot:

1. *The engines still agree on real data.* wd50k66 members that satisfy the
   Python-engine guard -- ``min(k, max arity) <= 4`` and at most
   ``2e6`` displacement tuples -- encode identically on both backends. About
   10 % of wd50k66 fails that guard and is C++-only.
2. *The C++-only regime is sound.* ndc_classes has arity median 6, so the
   Python reference cannot encode it at all. Its strings must still be
   invariant under relabelling and must still separate isomorphism classes,
   checked against pynauty.

Skipped in full when the frozen collections are absent: they live on the
results drive, not in the repository.
"""

from __future__ import annotations

import os
import random
from pathlib import Path

import pytest

from isalhg.core.canonical import canonical_string, required_k
from isalhg.core.sparse_hypergraph import SparseHypergraph, permute

pynauty = pytest.importorskip("pynauty")

from isalhg.iso_backends.canonical_order import canonical_ranks  # noqa: E402
from isalhg.iso_backends.orbit_oracle import canonical_fingerprint_rank  # noqa: E402
from isalhg.iso_backends.pynauty_levi import PynautyLeviBackend  # noqa: E402

pytestmark = pytest.mark.integration

#: Largest ``min(k, max arity)`` the pure-Python engine accepts, and the largest
#: displacement table it may materialise. Both restate
#: ``experiments/tkde/budget.py``: the Python search builds all ``(2r+1)^k``
#: tuples per frame, so arity 5 already asks for 1e8--7e11 of them.
PYTHON_MAX_K = 4
PYTHON_MAX_TUPLES = 2_000_000

_N_DIFFERENTIAL = 300
_N_INVARIANCE = 60
_N_RELABELLINGS = 20
_N_PAIRS = 300


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


def _python_guard_ok(H: SparseHypergraph) -> bool:
    """True iff the pure-Python engine may be run on ``H`` without exhausting RAM."""
    k = required_k(H)
    return k <= PYTHON_MAX_K and (2 * H.n_nodes - 1) ** k <= PYTHON_MAX_TUPLES


class TestWd50kBackendsAgree:
    """The engines agree on every wd50k66 member the Python one can encode."""

    def test_300_guard_satisfying_members(self) -> None:
        pool = [H for H in _load("wd50k66") if _python_guard_ok(H)]
        assert len(pool) >= _N_DIFFERENTIAL, f"only {len(pool)} guard-satisfying members"
        rng = random.Random(20260907)
        rng.shuffle(pool)
        for i, H in enumerate(pool[:_N_DIFFERENTIAL]):
            k = required_k(H)
            ranks = canonical_ranks(H)
            common = {"k": k, "algorithm": "canonical_rank", "ranks": ranks}
            w_py = canonical_string(H, backend="python", **common)
            w_cpp = canonical_string(H, backend="cpp", **common)
            assert w_py == w_cpp, f"member {i} (n={H.n_nodes}, m={H.n_edges}, k={k}) differs"


class TestNdcClassesIsCppOnly:
    """ndc_classes has arity median 6; only the C++ engine reaches it."""

    def test_most_members_fail_the_python_guard(self) -> None:
        pool = _load("ndc_classes")
        reachable = sum(1 for H in pool if _python_guard_ok(H))
        assert reachable < len(pool) // 2, (
            "the Python engine reaches most of ndc_classes; the C++-only premise "
            "of this file no longer holds"
        )

    def test_invariance_under_relabelling(self) -> None:
        pool = _load("ndc_classes")
        rng = random.Random(4242)
        rng.shuffle(pool)
        for i, H in enumerate(pool[:_N_INVARIANCE]):
            k = required_k(H)
            expected = canonical_fingerprint_rank(H, k=k)
            for _ in range(_N_RELABELLINGS):
                order = list(range(H.n_nodes))
                rng.shuffle(order)
                assert canonical_fingerprint_rank(permute(H, order), k=k) == expected, (
                    f"member {i} (n={H.n_nodes}, arity<={k}) is not relabelling-invariant"
                )

    def test_agrees_with_pynauty_on_300_pairs(self) -> None:
        pool = _load("ndc_classes")
        rng = random.Random(31337)
        backend = PynautyLeviBackend()
        iso_pairs = 0
        for i in range(_N_PAIRS):
            left = rng.choice(pool)
            if i % 2 == 0:
                order = list(range(left.n_nodes))
                rng.shuffle(order)
                right = permute(left, order)
                iso_pairs += 1
            else:
                # Comparing across vocabulary sizes is undefined: the Levi
                # colouring offsets edge colours by |Sigma_v|, so pynauty_levi
                # separates structurally identical inputs that declare
                # different vocabularies while every canonical string merges
                # them. Draw the partner from the same declaration.
                right = rng.choice(pool)
                while (right.n_vertex_labels, right.n_edge_labels) != (
                    left.n_vertex_labels,
                    left.n_edge_labels,
                ):
                    right = rng.choice(pool)
            k = max(required_k(left), required_k(right))
            same = canonical_fingerprint_rank(left, k=k) == canonical_fingerprint_rank(right, k=k)
            assert same == backend.are_isomorphic(left, right), f"pair {i} disagrees with pynauty"
        assert iso_pairs == _N_PAIRS // 2

    def test_wstar_rank_arm_runs_on_an_arity_6_member(self) -> None:
        """The harness arm inherits the C++ backend through its entry point.

        ``wstar_rank`` calls ``canonical_fingerprint_rank`` with no ``backend``
        argument, so it runs wherever that function's default runs. Before the
        port the default was Python and this member was out of reach.
        """
        from isalhg.metric_space.registry import get_distance

        pool = [H for H in _load("ndc_classes") if required_k(H) == 6]
        assert pool, "no arity-6 member in ndc_classes"
        H = pool[0]
        arm = get_distance("wstar_rank")
        symbols = arm.fingerprint(H)
        assert symbols
        assert arm.pairwise(H, H) == 0.0
