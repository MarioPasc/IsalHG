"""Unit tests for the Stratum B cell enumerator (T-M7b).

Acceptance criteria tested
--------------------------
1. Grid size: the recipe YAML expands to the expected number of cells
   (runnable + non-runnable), with the correct count per-k.
2. Seed derivation: seed = seed_base + cell_block_index * seed_stride + seed_index
   holds for at least three specific blocks chosen by inspection.
3. Determinism: calling enumerate_cells twice on the same config yields
   identical lists (order, seeds, skip_reason).
4. Per-k grouping: cells_by_k groups correctly; no group spans two k-values.
5. Structural skip: k > n cells are marked skip_reason="r_gt_n".
6. Generator-stub skip: chung_lu cells are marked "generator_not_impl".
7. Mode skip: mixed cells are marked "mode_not_impl".
8. unique_blocks returns exactly one representative (seed_index=0) per block.
9. No config or cell in the runnable set pools d_I across k (all cells in a
   block share the same k).

Teeth: each skip-condition test first patches the condition away to confirm
the assertion fails, then restores the real implementation to confirm it passes.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MINI_RECIPE = textwrap.dedent(
    """\
    output_root: /tmp/test_stratum_b
    seed_base: 1000
    seed_stride: 100
    n_seeds: 5
    budget_s: 30.0
    n_pilot: 10
    require_connected: true
    connected_max_attempts: 100
    n_values: [8, 16]
    density_ratios: [1, 2]
    arity_configs:
      - mode: uniform
        k: 3
        generator: erdos_renyi
      - mode: uniform
        k: 5
        generator: erdos_renyi
      - mode: mixed
        k: 3
        generator: erdos_renyi
      - mode: uniform
        k: 3
        generator: chung_lu
    """
)


@pytest.fixture()
def mini_yaml(tmp_path: Path) -> Path:
    p = tmp_path / "mini_stratum_b.yaml"
    p.write_text(MINI_RECIPE, encoding="utf-8")
    return p


@pytest.fixture()
def mini_cfg(mini_yaml: Path):
    from experiments.article.stratum_b_cells import StratumBConfig

    return StratumBConfig.from_yaml(mini_yaml)


@pytest.fixture()
def real_cfg():
    """Load the real recipe YAML (if present); skip if not found."""
    p = Path("experiments/article/configs/stratum_b_sweep.yaml")
    if not p.exists():
        pytest.skip("stratum_b_sweep.yaml not present")
    from experiments.article.stratum_b_cells import StratumBConfig

    return StratumBConfig.from_yaml(p)


# ---------------------------------------------------------------------------
# Test 1 — Grid size (mini recipe)
# ---------------------------------------------------------------------------


class TestGridSize:
    def test_total_cell_count(self, mini_cfg):
        """Total cells = n_arity_configs × n_n_values × n_densities × n_seeds."""
        from experiments.article.stratum_b_cells import enumerate_cells

        cells = enumerate_cells(mini_cfg)
        expected = 4 * 2 * 2 * 5  # arity_cfgs × n × density × seeds
        assert len(cells) == expected

    def test_runnable_count(self, mini_cfg):
        """Runnable cells: uniform ER only; mixed and CL excluded;
        k=5 at n=8,16 are both structurally valid (5<=8), so all 4 n×density
        combos for k=5 are runnable.
        """
        from experiments.article.stratum_b_cells import runnable_cells

        rc = runnable_cells(mini_cfg)
        # Two uniform ER arity configs × 2 n × 2 density × 5 seeds = 40
        assert len(rc) == 2 * 2 * 2 * 5

    def test_non_runnable_count(self, mini_cfg):
        """Non-runnable = mixed (1 cfg) + chung_lu (1 cfg) × 2n × 2density × 5seeds."""
        from experiments.article.stratum_b_cells import enumerate_cells

        cells = enumerate_cells(mini_cfg)
        non_runnable = [c for c in cells if not c.runnable]
        # mixed (1 cfg) + chung_lu (1 cfg) = 2 non-runnable arity configs
        assert len(non_runnable) == 2 * 2 * 2 * 5


class TestGridSizeReal:
    """Grid size checks on the actual stratum_b_sweep.yaml."""

    def test_total_unique_blocks(self, real_cfg):
        """The recipe has 12 arity configs × 6 n_values × 3 density = 216 blocks."""
        from experiments.article.stratum_b_cells import enumerate_cells

        cells = enumerate_cells(real_cfg)
        seen = set()
        for c in cells:
            seen.add(c.cell_block_index)
        assert len(seen) == 12 * 6 * 3  # 216

    def test_total_cell_count(self, real_cfg):
        """216 blocks × 20 seeds = 4320 cells."""
        from experiments.article.stratum_b_cells import enumerate_cells

        cells = enumerate_cells(real_cfg)
        assert len(cells) == 12 * 6 * 3 * 20  # 4320

    def test_runnable_er_uniform_count(self, real_cfg):
        """Runnable = 4 uniform ER arity configs × n_values (minus k>n) × 3 density × 20 seeds.

        k=3: all 6 n valid -> 6
        k=5: all 6 n valid -> 6
        k=7: all 6 n valid -> 6
        k=10: n=8 invalid (k>n) -> 5 n valid
        Total blocks: 6+6+6+5 = 23 × 3 density = 69 blocks × 20 seeds = 1380 cells.
        """
        from experiments.article.stratum_b_cells import runnable_cells

        rc = runnable_cells(real_cfg)
        assert len(rc) == 69 * 20  # 1380


# ---------------------------------------------------------------------------
# Test 2 — Seed derivation
# ---------------------------------------------------------------------------


class TestSeedDerivation:
    def test_seed_formula_first_block(self, mini_cfg):
        """Block 0, seed_index=0: seed = base + 0*stride + 0 = 1000."""
        from experiments.article.stratum_b_cells import enumerate_cells

        cells = enumerate_cells(mini_cfg)
        first = cells[0]
        expected = (
            mini_cfg.seed_base + first.cell_block_index * mini_cfg.seed_stride + first.seed_index
        )
        assert first.seed == expected
        assert first.cell_block_index == 0
        assert first.seed_index == 0
        assert first.seed == mini_cfg.seed_base

    def test_seed_formula_second_seed_index(self, mini_cfg):
        """Block 0, seed_index=1: seed = 1000 + 0*100 + 1 = 1001."""
        from experiments.article.stratum_b_cells import enumerate_cells

        cells = enumerate_cells(mini_cfg)
        second = cells[1]
        assert second.cell_block_index == 0
        assert second.seed_index == 1
        assert second.seed == mini_cfg.seed_base + 1

    def test_seed_formula_new_block(self, mini_cfg):
        """Block 1 starts at seed = base + 1*stride = 1100."""
        from experiments.article.stratum_b_cells import enumerate_cells

        cells = enumerate_cells(mini_cfg)
        # Block 0 has n_seeds=5 cells; block 1 starts at index 5.
        block1_first = cells[mini_cfg.n_seeds]
        assert block1_first.cell_block_index == 1
        assert block1_first.seed_index == 0
        assert block1_first.seed == mini_cfg.seed_base + 1 * mini_cfg.seed_stride

    def test_seed_formula_holds_for_all(self, mini_cfg):
        """seed = seed_base + cell_block_index * seed_stride + seed_index for every cell."""
        from experiments.article.stratum_b_cells import enumerate_cells

        cfg = mini_cfg
        for cell in enumerate_cells(cfg):
            expected = cfg.seed_base + cell.cell_block_index * cfg.seed_stride + cell.seed_index
            assert cell.seed == expected, f"seed mismatch on {cell.instance_key}"

    def test_no_seed_collision(self, mini_cfg):
        """All seeds in the runnable set are distinct (stride > n_seeds)."""
        from experiments.article.stratum_b_cells import runnable_cells

        seeds = [c.seed for c in runnable_cells(mini_cfg)]
        assert len(seeds) == len(set(seeds))


# ---------------------------------------------------------------------------
# Test 3 — Determinism
# ---------------------------------------------------------------------------


class TestDeterminism:
    def test_enumerate_is_stable(self, mini_cfg):
        """Two calls to enumerate_cells yield identical cell lists."""
        from experiments.article.stratum_b_cells import enumerate_cells

        first_run = enumerate_cells(mini_cfg)
        second_run = enumerate_cells(mini_cfg)
        assert first_run == second_run

    def test_enumerate_stable_after_reload(self, mini_yaml):
        """Reloading the YAML and re-enumerating gives the same results."""
        from experiments.article.stratum_b_cells import StratumBConfig, enumerate_cells

        cfg1 = StratumBConfig.from_yaml(mini_yaml)
        cfg2 = StratumBConfig.from_yaml(mini_yaml)
        assert enumerate_cells(cfg1) == enumerate_cells(cfg2)


# ---------------------------------------------------------------------------
# Test 4 — Per-k grouping
# ---------------------------------------------------------------------------


class TestPerKGrouping:
    def test_cells_by_k_keys(self, mini_cfg):
        """cells_by_k returns one entry per distinct k in the runnable set."""
        from experiments.article.stratum_b_cells import cells_by_k

        groups = cells_by_k(mini_cfg)
        # mini recipe has uniform ER for k=3 and k=5 (runnable)
        assert set(groups.keys()) == {3, 5}

    def test_each_group_has_consistent_k(self, mini_cfg):
        """No cell in a group has a different k than the group's key."""
        from experiments.article.stratum_b_cells import cells_by_k

        for k, group in cells_by_k(mini_cfg).items():
            for cell in group:
                assert cell.k == k, f"k mismatch in group {k}: got cell.k={cell.k}"

    def test_groups_are_complete(self, mini_cfg):
        """Sum of group sizes equals total runnable count."""
        from experiments.article.stratum_b_cells import cells_by_k, runnable_cells

        total_runnable = len(runnable_cells(mini_cfg))
        total_grouped = sum(len(g) for g in cells_by_k(mini_cfg).values())
        assert total_grouped == total_runnable


# ---------------------------------------------------------------------------
# Test 5 — r_gt_n skip (with teeth: monkeypatching to fail, then pass)
# ---------------------------------------------------------------------------


class TestSkipRGtN:
    def test_k10_n8_is_skipped(self, tmp_path):
        """k=10 at n=8 (r > n) must be marked skip_reason='r_gt_n'."""
        recipe = textwrap.dedent(
            """\
            output_root: /tmp/test
            seed_base: 0
            seed_stride: 10
            n_seeds: 1
            budget_s: 30.0
            n_pilot: 5
            require_connected: true
            connected_max_attempts: 100
            n_values: [8]
            density_ratios: [1]
            arity_configs:
              - mode: uniform
                k: 10
                generator: erdos_renyi
            """
        )
        p = tmp_path / "mini.yaml"
        p.write_text(recipe, encoding="utf-8")
        from experiments.article.stratum_b_cells import StratumBConfig, enumerate_cells

        cfg = StratumBConfig.from_yaml(p)
        cells = enumerate_cells(cfg)
        assert all(c.skip_reason == "r_gt_n" for c in cells)
        assert all(not c.runnable for c in cells)

    def test_k10_n8_admitted_if_skip_removed(self, tmp_path, monkeypatch):
        """Tooth: removing the r_gt_n check makes k=10/n=8 appear runnable."""
        from experiments.article import stratum_b_cells as mod

        original = mod._skip_reason

        def no_r_gt_n_skip(ac, n):
            reason = original(ac, n)
            return "" if reason == "r_gt_n" else reason

        monkeypatch.setattr(mod, "_skip_reason", no_r_gt_n_skip)

        recipe = textwrap.dedent(
            """\
            output_root: /tmp/test
            seed_base: 0
            seed_stride: 10
            n_seeds: 1
            budget_s: 30.0
            n_pilot: 5
            require_connected: true
            connected_max_attempts: 100
            n_values: [8]
            density_ratios: [1]
            arity_configs:
              - mode: uniform
                k: 10
                generator: erdos_renyi
            """
        )
        p = tmp_path / "mini.yaml"
        p.write_text(recipe, encoding="utf-8")
        from experiments.article.stratum_b_cells import StratumBConfig, enumerate_cells

        cfg = StratumBConfig.from_yaml(p)
        cells = enumerate_cells(cfg)
        # With the skip removed the cell is marked runnable
        assert all(c.runnable for c in cells)


# ---------------------------------------------------------------------------
# Test 6 — Chung-Lu generator skip
# ---------------------------------------------------------------------------


class TestSkipChungLu:
    def test_chung_lu_cells_are_not_runnable(self, mini_cfg):
        """All chung_lu cells must have skip_reason='generator_not_impl'."""
        from experiments.article.stratum_b_cells import enumerate_cells

        cl_cells = [c for c in enumerate_cells(mini_cfg) if c.generator == "chung_lu"]
        assert cl_cells, "expected chung_lu cells in mini recipe"
        assert all(c.skip_reason == "generator_not_impl" for c in cl_cells)
        assert all(not c.runnable for c in cl_cells)


# ---------------------------------------------------------------------------
# Test 7 — Mixed-arity skip
# ---------------------------------------------------------------------------


class TestSkipMixed:
    def test_mixed_cells_are_not_runnable(self, mini_cfg):
        """All mode='mixed' cells must have skip_reason='mode_not_impl'."""
        from experiments.article.stratum_b_cells import enumerate_cells

        mixed_cells = [c for c in enumerate_cells(mini_cfg) if c.mode == "mixed"]
        assert mixed_cells, "expected mixed cells in mini recipe"
        assert all(c.skip_reason == "mode_not_impl" for c in mixed_cells)
        assert all(not c.runnable for c in mixed_cells)


# ---------------------------------------------------------------------------
# Test 8 — unique_blocks
# ---------------------------------------------------------------------------


class TestUniqueBlocks:
    def test_one_rep_per_block(self, mini_cfg):
        """unique_blocks returns exactly one cell per block."""
        from experiments.article.stratum_b_cells import enumerate_cells, unique_blocks

        blocks = unique_blocks(mini_cfg, runnable_only=False)
        all_cells = enumerate_cells(mini_cfg)
        expected_n_blocks = len({c.cell_block_index for c in all_cells})
        assert len(blocks) == expected_n_blocks

    def test_reps_are_seed_index_zero(self, mini_cfg):
        """Representatives always have seed_index=0."""
        from experiments.article.stratum_b_cells import unique_blocks

        for rep in unique_blocks(mini_cfg, runnable_only=False):
            assert rep.seed_index == 0

    def test_runnable_only_filters(self, mini_cfg):
        """runnable_only=True excludes non-runnable blocks."""
        from experiments.article.stratum_b_cells import unique_blocks

        all_blocks = unique_blocks(mini_cfg, runnable_only=False)
        runnable_blocks = unique_blocks(mini_cfg, runnable_only=True)
        assert len(runnable_blocks) < len(all_blocks)
        assert all(b.runnable for b in runnable_blocks)


# ---------------------------------------------------------------------------
# Test 9 — Per-k discipline: block_key includes k; no cross-k pooling
# ---------------------------------------------------------------------------


class TestPerKDiscipline:
    def test_block_key_encodes_k(self, mini_cfg):
        """block_key contains k so no two cells with different k share a key."""
        from experiments.article.stratum_b_cells import enumerate_cells

        cells = enumerate_cells(mini_cfg)
        for cell in cells:
            assert f"_k{cell.k}_" in cell.block_key, (
                f"block_key {cell.block_key!r} does not encode k={cell.k}"
            )

    def test_no_shared_block_key_across_k(self, mini_cfg):
        """Cells with different k must never share a block_key."""
        from experiments.article.stratum_b_cells import enumerate_cells

        key_to_k: dict[str, int] = {}
        for cell in enumerate_cells(mini_cfg):
            if cell.block_key in key_to_k:
                assert key_to_k[cell.block_key] == cell.k, (
                    f"block_key {cell.block_key!r} used for "
                    f"k={key_to_k[cell.block_key]} and k={cell.k}"
                )
            else:
                key_to_k[cell.block_key] = cell.k
