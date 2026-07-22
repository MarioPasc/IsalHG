"""Unit tests for the --list-blocks mode and key normalisation in T-M7h.

Covers three invariants:
1. list_blocks() returns the enumerator's actual block keys — no hard-coding.
2. --pending-envelope filtering works with the legacy "er_uniform_*" key form.
3. _shorten_block_key() in the merge script maps "erdos_renyi_uniform_*" →
   "er_uniform_*" so cluster result JSONs patch existing envelope entries
   rather than appending duplicates.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Helper: import scripts/T-M7h_merge_envelope.py via importlib (hyphen in name)
# ---------------------------------------------------------------------------


def _import_merge_script() -> Any:
    """Return the merge script module, loaded via importlib (filename has a hyphen)."""
    script_path = (
        Path(__file__).parent.parent.parent.parent  # tests/unit/experiments/ -> repo root
        / "scripts"
        / "T-M7h_merge_envelope.py"
    )
    module_name = "T_M7h_merge_envelope_test_module"
    if module_name in sys.modules:
        return sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


# ---------------------------------------------------------------------------
# Minimal YAML recipe shared by tests 1 and 2
# ---------------------------------------------------------------------------

_MINIMAL_YAML = """
output_root: /tmp/test_list_blocks
seed_base: 1000
seed_stride: 100
n_seeds: 1
budget_s: 30.0
n_pilot: 2
require_connected: true
connected_max_attempts: 10
n_values: [4, 8]
density_ratios: [1.0]
arity_configs:
  - mode: uniform
    k: 3
    generator: erdos_renyi
"""


def _write_config(tmp_path: Path) -> Path:
    cfg = tmp_path / "mini_sweep.yaml"
    cfg.write_text(_MINIMAL_YAML, encoding="utf-8")
    return cfg


# ---------------------------------------------------------------------------
# Test 1: list_blocks returns enumerator keys, not hard-coded strings
# ---------------------------------------------------------------------------


class TestListBlocks:
    def test_returns_enumerator_keys(self, tmp_path: Path) -> None:
        """list_blocks() keys match the enumerator — no hard-coded shorthand."""
        from experiments.article.feasibility_pilot import list_blocks
        from experiments.article.stratum_b_cells import StratumBConfig, unique_blocks

        cfg_path = _write_config(tmp_path)
        returned = list_blocks(cfg_path)
        cfg = StratumBConfig.from_yaml(cfg_path)
        expected = [b.block_key for b in unique_blocks(cfg, runnable_only=True)]

        assert returned == expected, f"list_blocks() returned {returned!r}, expected {expected!r}"

    def test_keys_use_full_prefix_not_abbreviated(self, tmp_path: Path) -> None:
        """Keys produced by list_blocks() start with the full generator_mode prefix."""
        from experiments.article.feasibility_pilot import list_blocks

        cfg_path = _write_config(tmp_path)
        keys = list_blocks(cfg_path)
        for k in keys:
            assert not k.startswith("er_uniform_"), (
                f"list_blocks() returned abbreviated key {k!r}; "
                "expected full 'erdos_renyi_uniform_' form"
            )
            assert k.startswith("erdos_renyi_uniform_"), (
                f"list_blocks() key {k!r} does not start with 'erdos_renyi_uniform_'"
            )


# ---------------------------------------------------------------------------
# Test 2: pending_envelope filtering expands legacy short keys
# ---------------------------------------------------------------------------


def _write_envelope(tmp_path: Path, pending_legacy_keys: list[str]) -> Path:
    """Write a minimal envelope JSON with the given pending_cluster keys."""
    env: dict[str, Any] = {
        "pending_cluster": [{"block_key": k, "reason": "test"} for k in pending_legacy_keys],
        "block_results": [],
    }
    p = tmp_path / "envelope.json"
    p.write_text(json.dumps(env), encoding="utf-8")
    return p


class TestListBlocksPendingFilter:
    def test_filters_to_pending_legacy_keys(self, tmp_path: Path) -> None:
        """--pending-envelope with a legacy 'er_uniform_*' key filters correctly."""
        from experiments.article.feasibility_pilot import list_blocks

        cfg_path = _write_config(tmp_path)
        # The mini config has 2 runnable blocks:
        #   erdos_renyi_uniform_k3_n4_rho1  (legacy: er_uniform_k3_n4_rho1)
        #   erdos_renyi_uniform_k3_n8_rho1  (legacy: er_uniform_k3_n8_rho1)
        # Put only the first in the envelope's pending_cluster using its legacy form.
        envelope_path = _write_envelope(tmp_path, ["er_uniform_k3_n4_rho1"])

        result = list_blocks(cfg_path, pending_envelope_path=envelope_path)

        assert len(result) == 1, f"Expected 1 pending block, got {result}"
        assert result[0] == "erdos_renyi_uniform_k3_n4_rho1", (
            f"Expected canonical key 'erdos_renyi_uniform_k3_n4_rho1', got {result[0]!r}"
        )

    def test_no_pending_returns_empty(self, tmp_path: Path) -> None:
        """With an empty pending_cluster the result is an empty list."""
        from experiments.article.feasibility_pilot import list_blocks

        cfg_path = _write_config(tmp_path)
        envelope_path = _write_envelope(tmp_path, [])
        result = list_blocks(cfg_path, pending_envelope_path=envelope_path)
        assert result == [], f"Expected empty list, got {result}"

    def test_pre_fix_would_fail_with_short_key(self, tmp_path: Path) -> None:
        """Demonstrate that without _expand_envelope_key, legacy keys would not match.

        The pre-fix behaviour (string equality, no expansion) would produce an
        empty result because 'er_uniform_k3_n4_rho1' != 'erdos_renyi_uniform_k3_n4_rho1'.
        This test verifies the pre-fix case fails, proving the fix is necessary.
        """
        from experiments.article.feasibility_pilot import _expand_envelope_key

        # Confirm the expansion is non-trivial.
        short_key = "er_uniform_k3_n4_rho1"
        expanded = _expand_envelope_key(short_key)
        assert expanded != short_key, "Expected expansion to change the key"
        assert expanded == "erdos_renyi_uniform_k3_n4_rho1"

        # Without expansion, a naive set-membership check would fail.
        canonical_key = "erdos_renyi_uniform_k3_n4_rho1"
        assert short_key not in {canonical_key}, (
            "Pre-fix: legacy key must NOT match the canonical key directly"
        )


# ---------------------------------------------------------------------------
# Test 3: _shorten_block_key normalises enumerator keys for envelope lookup
# ---------------------------------------------------------------------------


class TestMergeScriptKeyNormalisation:
    def test_shorten_maps_erdos_renyi_to_er_uniform(self) -> None:
        """_shorten_block_key maps 'erdos_renyi_uniform_*' to 'er_uniform_*'."""
        mod = _import_merge_script()
        _shorten_block_key = mod._shorten_block_key

        assert _shorten_block_key("erdos_renyi_uniform_k3_n24_rho1") == "er_uniform_k3_n24_rho1"
        assert _shorten_block_key("erdos_renyi_uniform_k5_n8_rho2") == "er_uniform_k5_n8_rho2"
        assert _shorten_block_key("erdos_renyi_uniform_k10_n16_rho1") == "er_uniform_k10_n16_rho1"

    def test_shorten_is_identity_for_unknown_prefix(self) -> None:
        """Keys with no shortening rule are returned unchanged."""
        mod = _import_merge_script()
        _shorten_block_key = mod._shorten_block_key

        unchanged = "chung_lu_uniform_k3_n8_rho1"
        assert _shorten_block_key(unchanged) == unchanged

    def test_merge_patches_envelope_entry_not_appends(self, tmp_path: Path) -> None:
        """_merge_stratum_b patches an existing 'er_uniform_*' entry from a
        cluster JSON that uses 'erdos_renyi_uniform_*' naming — no duplicate."""
        mod = _import_merge_script()
        _merge_stratum_b = mod._merge_stratum_b

        # Build a minimal envelope with one pending block under the short key.
        envelope: dict[str, Any] = {
            "block_results": [
                {
                    "block_key": "er_uniform_k3_n24_rho1",
                    "n": 24,
                    "k": 3,
                    "mode": "uniform",
                    "generator": "erdos_renyi",
                    "density_ratio": 1.0,
                    "cell_block_index": 0,
                    "n_pilot": 5,
                    "admitted": False,
                    "local_status": "pending_cluster",
                    "reason": "local_pilot_budget_exceeded",
                }
            ],
            "admitted_block_keys": [],
            "pending_cluster": [{"block_key": "er_uniform_k3_n24_rho1", "reason": "test"}],
            "cluster_excluded": [],
            "summary": {},
        }
        envelope_path = tmp_path / "envelope.json"
        envelope_path.write_text(json.dumps(envelope), encoding="utf-8")

        # Build a cluster per-block JSON using the enumerator's long key form.
        cluster_result: dict[str, Any] = {
            "block_results": [
                {
                    "block_key": "erdos_renyi_uniform_k3_n24_rho1",
                    "n": 24,
                    "k": 3,
                    "mode": "uniform",
                    "generator": "erdos_renyi",
                    "density_ratio": 1.0,
                    "cell_block_index": 0,
                    "n_pilot": 30,
                    "n_ok": 30,
                    "n_timeout": 0,
                    "n_error": 0,
                    "times_ms": [500.0] * 30,
                    "p50_ms": 500.0,
                    "p90_ms": 600.0,
                    "admitted": False,
                    "reason": "p90=0.6s exceeds budget=0.03s",
                }
            ]
        }
        cluster_dir = tmp_path / "per_block"
        cluster_dir.mkdir()
        (cluster_dir / "block_erdos_renyi_uniform_k3_n24_rho1.json").write_text(
            json.dumps(cluster_result), encoding="utf-8"
        )

        _merge_stratum_b(cluster_dir, envelope_path, dry_run=False)

        # Reload and verify: exactly 1 block_result entry (patched, not appended).
        with envelope_path.open() as fh:
            updated: dict = json.load(fh)
        results = updated["block_results"]
        assert len(results) == 1, (
            f"Expected 1 block_result (patch, not append), got {len(results)}: "
            f"{[r['block_key'] for r in results]}"
        )
        entry = results[0]
        # The envelope key must be preserved (short form), not overwritten.
        assert entry["block_key"] == "er_uniform_k3_n24_rho1"
        # The cluster measurements must have been merged in.
        assert entry.get("cluster_n_pilot") == 30
        assert entry.get("cluster_status") == "cluster_excluded"
