"""The C++ orbit engine against the unpruned ``w*_c`` on the KB corpora.

The unit differential (``tests/unit/core/test_cpp_orbit.py``) samples random
hypergraphs small enough for the Python reference to run. The corpora are where
the port is actually used and where the inputs it has to survive live: labelled
members with arities the Python engine refuses outright, and the symmetric tail
that motivated the pruning in the first place.

Both arms go through :func:`experiments.tkde.budget.engine_word`, so this also
pins the harness contract -- ``engine_word(engine="orbit")`` reaching the C++
path through a forked child, with no harness edit beyond ``_runs_in_python``.

Skipped without the results drive; the collections are not in the repository.
"""

from __future__ import annotations

import os
import random
import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.slow]

pytest.importorskip("isalhg.core._core", reason="C++ extension not built")
pytest.importorskip("pynauty", reason="pynauty is required by PynautyOrbitOracle")

_DEFAULT_ROOT = "/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE"
RESULTS_ROOT = os.environ.get("ISALHG_RESULTS_ROOT", _DEFAULT_ROOT)

#: Members per collection. Small: this is a contract check, not the campaign
#: measurement (that lives in the wave log, run over 300 members per corpus).
N_MEMBERS = 25

#: Wall-clock budget per member, per arm.
BUDGET_S = 60.0


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def tkde_modules():  # type: ignore[no-untyped-def]
    """``experiments.tkde`` is at the repo root, not in the installed package."""
    root = str(_repo_root())
    if root not in sys.path:
        sys.path.insert(0, root)
    corpora = pytest.importorskip("experiments.tkde.corpora")
    budget = pytest.importorskip("experiments.tkde.budget")
    if not Path(RESULTS_ROOT).is_dir():
        pytest.skip(f"results drive not mounted at {RESULTS_ROOT}")
    return corpora, budget


def test_orbit_engine_runs_in_cpp(tkde_modules) -> None:  # type: ignore[no-untyped-def]
    """The harness routes the orbit engine to the extension, not to Python.

    This is the whole point of the ``_runs_in_python`` change: with it False,
    ``engine_word`` takes the fork-health path and skips the Python memory
    guard, which is what refused every arity-5 member before.
    """
    _corpora, budget = tkde_modules
    assert budget._runs_in_python("orbit") is False


@pytest.mark.parametrize("collection_name", ["wd50k66", "ndc_classes"])
def test_orbit_matches_unpruned_wstar_c(  # type: ignore[no-untyped-def]
    collection_name: str, tkde_modules
) -> None:
    """Orbit pruning returns the frozen ``w*_c``, on real KB members.

    Members are drawn under a fixed seed and compared only where the unpruned
    arm itself completes inside the budget -- a censored baseline has nothing
    to compare against, and censoring the pruned arm instead is the *expected*
    asymmetry, not a failure.
    """
    from isalhg.core.canonical import required_k

    corpora, budget = tkde_modules
    collection = corpora.load_collection(collection_name, RESULTS_ROOT)
    members = corpora.hypergraphs(collection)
    rng = random.Random(20260907)
    sample = rng.sample(members, min(4 * N_MEMBERS, len(members)))

    compared = 0
    for H in sample:
        if compared >= N_MEMBERS:
            break
        k = required_k(H)
        base = budget.engine_word(H, k, BUDGET_S, engine="cpp")
        if not base.ok:
            continue
        pruned = budget.engine_word(H, k, BUDGET_S, engine="orbit")
        if not pruned.ok:
            continue
        assert pruned.value == base.value, f"{collection_name}: orbit != w*_c on a member"
        compared += 1

    assert compared >= N_MEMBERS // 2, (
        f"{collection_name}: only {compared} members completed on both arms; "
        "too few to call this a differential"
    )
