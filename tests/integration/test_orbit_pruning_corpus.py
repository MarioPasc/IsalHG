"""Corpus differential: the orbit-pruned engine equals the C++ ``w*_c``.

The unit differential samples small synthetic instances. This one runs the two
engines against each other on real knowledge-base members -- ``wd50k66``, the
corpus whose symmetric tail motivated the pruning in the first place -- so the
value-preservation claim is checked on the distribution it will be used on.

Both engines run under :func:`experiments.tkde.budget.run_with_budget`: the
Python search does not return on ``SIGALRM``, so a censored member has to be
killed in a forked child rather than interrupted. Members the C++ engine cannot
finish inside the budget are skipped here (they are the subject of the probe's
censored-tail measurement, not of an equality assertion).

Skipped whole when the frozen corpora are not mounted.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.slow]

pytest.importorskip("pynauty")

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

COLLECTION = "wd50k66"
N_MEMBERS = 300
BUDGET_S = 60.0
SEED = 20260906


def _load_members() -> list:
    """Return the sampled ``wd50k66`` hypergraphs, or skip if unavailable."""
    try:
        from experiments.tkde import corpora
    except ImportError as exc:  # pragma: no cover - defensive
        pytest.skip(f"experiments.tkde unavailable: {exc}")
    try:
        collection = corpora.load_collection(COLLECTION)
    except Exception as exc:  # noqa: BLE001 - a missing drive is a skip, not a failure
        pytest.skip(f"frozen corpus {COLLECTION!r} unavailable: {exc}")
    members = corpora.hypergraphs(collection)
    rng = random.Random(SEED)
    if len(members) > N_MEMBERS:
        members = rng.sample(members, N_MEMBERS)
    return members


def _cpp_wstar(H: object) -> str:
    from isalhg.core.canonical import canonical_string

    return canonical_string(H, algorithm="canonical", backend="cpp")  # type: ignore[arg-type]


def _orbit_wstar(H: object) -> str:
    from isalhg.iso_backends.orbit_oracle import canonical_string_orbit

    return canonical_string_orbit(H)  # type: ignore[arg-type]


def test_orbit_engine_matches_cpp_wstar_c_on_wd50k66() -> None:
    """Every member both engines complete yields the identical ``w*_c``."""
    from experiments.tkde.budget import run_with_budget

    members = _load_members()
    compared = 0
    cpp_censored = 0
    orbit_censored: list[int] = []
    for index, H in enumerate(members):
        expected, _secs, censored = run_with_budget(_cpp_wstar, (H,), seconds=BUDGET_S)
        if censored or expected is None:
            cpp_censored += 1
            continue
        actual, _secs, censored = run_with_budget(_orbit_wstar, (H,), seconds=BUDGET_S)
        if censored or actual is None:
            orbit_censored.append(index)
            continue
        assert actual == expected, f"member {index} diverged from the C++ w*_c"
        compared += 1
    assert compared > 0, (
        f"no member of {COLLECTION!r} completed on both engines "
        f"({cpp_censored} C++ censored, {len(orbit_censored)} orbit censored)"
    )
