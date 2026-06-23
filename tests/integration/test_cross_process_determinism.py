"""Cross-process determinism of WL hash and canonical_string.

The C++ port replaces Python's salted ``hash()`` with FNV-1a 64-bit so
that ``wl_hash`` and any ``canonical_string`` variant that uses WL
(``greedy_min_wl_pruned``, ``greedy_min_inplace_wl_pruned``) produces the
same output regardless of ``PYTHONHASHSEED``.

A failure here means the C++ FNV-1a constants drifted from the
Python-side constants in ``isalhg.core.hypergraph_wl``, or that the
Python-side fallback still calls ``hash()``.
"""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap

import pytest

pytestmark = pytest.mark.integration


_DRIVER = textwrap.dedent(
    """
    import sys
    from isalhg.core.sparse_hypergraph import SparseHypergraph
    from isalhg.core.hypergraph_wl import wl_hash
    from isalhg.core.canonical import canonical_string

    fano = SparseHypergraph(
        n_nodes=7,
        hyperedges=[
            [0, 1, 2], [0, 3, 4], [0, 5, 6],
            [1, 3, 5], [1, 4, 6], [2, 3, 6], [2, 4, 5],
        ],
    )
    wl = wl_hash(fano)
    cs_min = canonical_string(fano, algorithm="greedy_min")
    cs_wl = canonical_string(fano, algorithm="greedy_min_wl_pruned")
    sys.stdout.write(repr(wl) + "\\n")
    sys.stdout.write(cs_min + "\\n")
    sys.stdout.write(cs_wl + "\\n")
    """
)


def _run(seed: str) -> tuple[str, str, str]:
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = seed
    out = subprocess.run(
        [sys.executable, "-c", _DRIVER],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    lines = out.stdout.splitlines()
    assert len(lines) == 3, out.stdout
    return lines[0], lines[1], lines[2]


def test_wl_hash_stable_across_processes() -> None:
    """Two subprocesses with different PYTHONHASHSEED produce identical wl_hash."""
    wl_a, _, _ = _run("0")
    wl_b, _, _ = _run("123")
    wl_c, _, _ = _run("random")
    assert wl_a == wl_b == wl_c


def test_canonical_string_stable_across_processes() -> None:
    """greedy_min canonical_string is stable across PYTHONHASHSEED values."""
    _, cs_a, _ = _run("0")
    _, cs_b, _ = _run("123")
    _, cs_c, _ = _run("random")
    assert cs_a == cs_b == cs_c


def test_wl_pruned_canonical_string_stable_across_processes() -> None:
    """greedy_min_wl_pruned canonical_string is stable across PYTHONHASHSEED."""
    _, _, cs_a = _run("0")
    _, _, cs_b = _run("123")
    _, _, cs_c = _run("random")
    assert cs_a == cs_b == cs_c
