"""Integration test: full Tier-1 orchestrator close on all available backends.

Runs a reduced-scope variant of the Tier 1 YAML against every backend
present in the environment (IsalHG + pynauty_levi + bliss_levi +
traces_levi when their deps resolve), asserts FP = FN = 0, verifies
bijection certificates on backends that expose them, and re-runs to
confirm idempotency.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

pynauty = pytest.importorskip("pynauty")  # noqa: F841


def _have_igraph() -> bool:
    try:
        import igraph  # noqa: F401
    except ImportError:
        return False
    return True


def _have_dreadnaut() -> bool:
    return shutil.which("dreadnaut") is not None


_BACKEND_BLOCK = """\
  - protocol: pairwise_iso
    backend: {backend}
    dataset: exhaustive_small
    seed: 0
    protocol_params:
      timeout_s: 60.0
      check_bijection: {check_bij}
    dataset_params:
      n_range: [3, 4]
      arity_range: [2, 3]
      max_edges: 3
      include_designs: false
      include_large_designs: false
      dedup_backend_name: pynauty_levi
      permutations_per_class: 2
      seed_value: 0
"""


def _write_mini_yaml(
    output_root: Path, config_path: Path, backends: list[tuple[str, bool]]
) -> None:
    cells = "".join(_BACKEND_BLOCK.format(backend=b, check_bij=str(c).lower()) for b, c in backends)
    config_path.write_text(
        f"""\
name: tier1_correctness_mini
description: Reduced-scope Tier 1 across all available backends.
output_root: {output_root}

cells:
{cells}""",
        encoding="utf-8",
    )


def _gather_backends() -> list[tuple[str, bool]]:
    backends: list[tuple[str, bool]] = [
        ("isalhg", False),
        ("pynauty_levi", True),
    ]
    if _have_igraph():
        backends.append(("bliss_levi", True))
    if _have_dreadnaut():
        backends.append(("traces_levi", False))
    return backends


def test_tier1_orchestrator_partition_agreement(tmp_path: Path) -> None:
    from experiments.orchestrator import run_experiment

    backends = _gather_backends()
    output_root = tmp_path / "tier1_out"
    config_path = tmp_path / "tier1_mini.yaml"
    _write_mini_yaml(output_root, config_path, backends)

    logs = run_experiment(config_path)
    assert len(logs) == len(backends)

    confusions = []
    for log in logs:
        conf = log.result.measurements["confusion"]
        assert conf["false_positive"] == 0, (log.cell, conf)
        assert conf["false_negative"] == 0, (log.cell, conf)
        confusions.append((log.cell.backend, conf))
        if log.cell.protocol_params.get("check_bijection"):
            violations = log.result.measurements["bijection_violations"]
            assert violations == [], (log.cell, violations)

    # Partition agreement: every backend induces the same TP / TN partition.
    tp_set = {c["true_positive"] for _, c in confusions}
    tn_set = {c["true_negative"] for _, c in confusions}
    assert len(tp_set) == 1, f"TP counts disagree: {confusions}"
    assert len(tn_set) == 1, f"TN counts disagree: {confusions}"


def test_tier1_orchestrator_idempotent_skip(tmp_path: Path) -> None:
    from experiments.orchestrator import run_experiment

    output_root = tmp_path / "tier1_out"
    config_path = tmp_path / "tier1_mini.yaml"
    _write_mini_yaml(output_root, config_path, [("isalhg", False), ("pynauty_levi", True)])

    logs1 = run_experiment(config_path)
    files1 = sorted(output_root.glob("*.json"))
    mtimes1 = {p.name: p.stat().st_mtime_ns for p in files1}

    logs2 = run_experiment(config_path)
    files2 = sorted(output_root.glob("*.json"))
    mtimes2 = {p.name: p.stat().st_mtime_ns for p in files2}

    assert [p.name for p in files1] == [p.name for p in files2]
    assert mtimes1 == mtimes2, "second run wrote files; idempotency broken"
    assert len(logs1) == len(logs2) == 2
