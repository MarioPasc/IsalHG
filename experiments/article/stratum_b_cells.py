"""Stratum B cell enumerator — T-M7b.

Reads the Stratum B recipe YAML (``configs/stratum_b_sweep.yaml``) and expands
it into a deterministic flat list of :class:`StratumBCell` objects.

k-family discipline (``stability.md`` §1 / ``REVIEW/DATA.md`` §5):
    ``d_I^{k,h,Σ}`` is an index family; absolute d_I values across different k
    are incomparable.  The analysis must compare only dimensionless descriptors
    (ν, D̂, stress, hubness) across k, and within-k application rankings.
    No downstream config or analysis stub may pool raw d_I across k.

Seed derivation::

    seed = seed_base + cell_block_index * seed_stride + seed_index
    seed_index  ∈  [0, n_seeds)

``cell_block_index`` is the 0-based rank of the (arity_config_idx, n_idx,
density_idx) triple in declaration order (arity configs × n ascending × density
ascending).  It is stable across calls to :func:`enumerate_cells` on the same
config.

Skip reasons (``runnable=False``)::

    r_gt_n              : arity k > n_nodes (structurally infeasible for uniform mode)
    generator_not_impl  : ChungLuHypergraphs raises NotImplementedError
    mode_not_impl       : mixed-arity mode has no package generator
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ArityCfg:
    """One entry in the recipe's ``arity_configs`` list."""

    mode: str  # "uniform" or "mixed"
    k: int  # arity cap (or uniform arity)
    generator: str  # "erdos_renyi" or "chung_lu"


@dataclass(frozen=True)
class StratumBConfig:
    """Parsed Stratum B recipe."""

    output_root: Path
    seed_base: int
    seed_stride: int
    n_seeds: int
    budget_s: float
    n_pilot: int
    require_connected: bool
    connected_max_attempts: int
    n_values: tuple[int, ...]
    density_ratios: tuple[float, ...]
    arity_configs: tuple[ArityCfg, ...]

    @classmethod
    def from_yaml(cls, path: Path | str) -> StratumBConfig:
        """Load a :class:`StratumBConfig` from *path*.

        Parameters
        ----------
        path : Path or str
            Path to the Stratum B recipe YAML.

        Returns
        -------
        StratumBConfig
        """
        with open(path, encoding="utf-8") as fh:
            raw: dict[str, Any] = yaml.safe_load(fh)

        arity_cfgs = tuple(
            ArityCfg(
                mode=str(ac["mode"]),
                k=int(ac["k"]),
                generator=str(ac["generator"]),
            )
            for ac in raw["arity_configs"]
        )
        return cls(
            output_root=Path(raw["output_root"]),
            seed_base=int(raw.get("seed_base", 1000)),
            seed_stride=int(raw.get("seed_stride", 100)),
            n_seeds=int(raw.get("n_seeds", 20)),
            budget_s=float(raw.get("budget_s", 30.0)),
            n_pilot=int(raw.get("n_pilot", 30)),
            require_connected=bool(raw.get("require_connected", True)),
            connected_max_attempts=int(raw.get("connected_max_attempts", 1000)),
            n_values=tuple(int(v) for v in raw["n_values"]),
            density_ratios=tuple(float(v) for v in raw["density_ratios"]),
            arity_configs=arity_cfgs,
        )


@dataclass(frozen=True)
class StratumBCell:
    """One (n, k, mode, generator, density_ratio, seed) cell.

    Attributes
    ----------
    n : int
        Number of vertices.
    k : int
        Arity cap (uniform arity for mode="uniform").
    mode : str
        "uniform" or "mixed".
    generator : str
        "erdos_renyi" or "chung_lu".
    density_ratio : float
        Target m/n value.
    seed : int
        PRNG seed for this instance, derived from the formula
        ``seed_base + cell_block_index * seed_stride + seed_index``.
    cell_block_index : int
        Flat index over (arity_cfg_idx × n_idx × density_idx); stable across
        calls with the same config.
    seed_index : int
        Position within this cell's seed range [0, n_seeds).
    runnable : bool
        False when the cell is structurally infeasible or the generator is
        not implemented; the pilot skips it with ``skip_reason``.
    skip_reason : str
        One of {"", "r_gt_n", "generator_not_impl", "mode_not_impl"}.
    """

    n: int
    k: int
    mode: str
    generator: str
    density_ratio: float
    seed: int
    cell_block_index: int
    seed_index: int
    runnable: bool
    skip_reason: str

    @property
    def block_key(self) -> str:
        """Unique key for the (arity, n, density) block, shared by all seeds."""
        rho = (
            int(self.density_ratio)
            if self.density_ratio == int(self.density_ratio)
            else self.density_ratio
        )
        return f"{self.generator}_{self.mode}_k{self.k}_n{self.n}_rho{rho}"

    @property
    def instance_key(self) -> str:
        """Unique key for this instance (includes seed_index)."""
        return f"{self.block_key}_s{self.seed_index}"

    def dataset_params(
        self, require_connected: bool = True, connected_max_attempts: int = 1000
    ) -> dict[str, Any]:
        """Return dataset_params dict for the registered 'random_erdos_renyi' dataset.

        Only valid when ``generator == 'erdos_renyi'`` and ``mode == 'uniform'``.

        Parameters
        ----------
        require_connected : bool
            Passed through to the dataset constructor.
        connected_max_attempts : int
            Passed through to the dataset constructor.

        Returns
        -------
        dict[str, Any]
            Constructor parameters (excluding ``seed``, which is passed via
            ``HypergraphDataset.seed()``).

        Raises
        ------
        RuntimeError
            If the cell is not runnable.
        """
        if not self.runnable:
            raise RuntimeError(f"cell {self.instance_key!r} is not runnable: {self.skip_reason}")
        return {
            "n": self.n,
            "r": self.k,  # uniform arity = k for mode=uniform
            "c": float(self.density_ratio),
            "require_connected": require_connected,
            "connected_max_attempts": connected_max_attempts,
        }


# ---------------------------------------------------------------------------
# Enumerator
# ---------------------------------------------------------------------------


def _skip_reason(ac: ArityCfg, n: int) -> str:
    """Return a non-empty skip reason if the cell is not runnable, else ''."""
    if ac.mode == "mixed":
        return "mode_not_impl"
    if ac.generator == "chung_lu":
        return "generator_not_impl"
    if ac.mode == "uniform" and ac.k > n:
        return "r_gt_n"
    return ""


def enumerate_cells(cfg: StratumBConfig) -> list[StratumBCell]:
    """Expand the recipe into a flat, deterministic list of :class:`StratumBCell`.

    Ordering is: arity_configs (declaration order) × n (ascending) × density
    (ascending) × seed_index (ascending).  ``cell_block_index`` is the rank of
    the (arity_cfg, n, density) triple; ``seed`` derives from it deterministically.

    Parameters
    ----------
    cfg : StratumBConfig
        Parsed recipe.

    Returns
    -------
    list[StratumBCell]
        All cells in stable order.  Non-runnable cells are included with
        ``runnable=False`` and a non-empty ``skip_reason``.
    """
    cells: list[StratumBCell] = []
    block_index = 0
    for ac in cfg.arity_configs:
        for n in cfg.n_values:
            for density in cfg.density_ratios:
                reason = _skip_reason(ac, n)
                runnable = reason == ""
                for si in range(cfg.n_seeds):
                    seed = cfg.seed_base + block_index * cfg.seed_stride + si
                    cells.append(
                        StratumBCell(
                            n=n,
                            k=ac.k,
                            mode=ac.mode,
                            generator=ac.generator,
                            density_ratio=density,
                            seed=seed,
                            cell_block_index=block_index,
                            seed_index=si,
                            runnable=runnable,
                            skip_reason=reason,
                        )
                    )
                block_index += 1
    return cells


def runnable_cells(cfg: StratumBConfig) -> list[StratumBCell]:
    """Return only the runnable subset of :func:`enumerate_cells`.

    Parameters
    ----------
    cfg : StratumBConfig
        Parsed recipe.

    Returns
    -------
    list[StratumBCell]
        Cells with ``runnable=True``, in stable order.
    """
    return [c for c in enumerate_cells(cfg) if c.runnable]


def cells_by_k(cfg: StratumBConfig) -> dict[int, list[StratumBCell]]:
    """Group runnable cells by k-value for per-k analysis.

    The k-family discipline requires that no downstream analysis pools raw d_I
    across different k.  This helper enforces the grouping.

    Parameters
    ----------
    cfg : StratumBConfig
        Parsed recipe.

    Returns
    -------
    dict[int, list[StratumBCell]]
        Keys are k values; values are lists of runnable cells with that k.
    """
    groups: dict[int, list[StratumBCell]] = {}
    for cell in runnable_cells(cfg):
        groups.setdefault(cell.k, []).append(cell)
    return groups


def unique_blocks(cfg: StratumBConfig, *, runnable_only: bool = True) -> list[StratumBCell]:
    """Return one representative cell per (arity_cfg, n, density) block.

    Useful for the feasibility pilot, which measures one set of instances per
    block (not per seed).

    Parameters
    ----------
    cfg : StratumBConfig
        Parsed recipe.
    runnable_only : bool
        If True, only include runnable blocks.

    Returns
    -------
    list[StratumBCell]
        The seed_index=0 representative of each block.
    """
    all_cells = enumerate_cells(cfg)
    seen: set[int] = set()
    reps: list[StratumBCell] = []
    for cell in all_cells:
        if runnable_only and not cell.runnable:
            continue
        if cell.cell_block_index not in seen:
            seen.add(cell.cell_block_index)
            reps.append(cell)
    return reps


# ---------------------------------------------------------------------------
# Realized-parameter table
# ---------------------------------------------------------------------------


def realized_params_for_cell(cell: StratumBCell, hypergraph: Any) -> dict[str, Any]:
    """Emit the realized-parameter record for one generated instance.

    Called from the pilot or the corpus runner after materialising a
    hypergraph so the record captures *actual* (not requested) parameters.

    Parameters
    ----------
    cell : StratumBCell
        The cell specification.
    hypergraph : SparseHypergraph
        The materialised hypergraph.

    Returns
    -------
    dict[str, Any]
        Realized-parameter record with both requested and actual values.
    """
    import math

    n_actual = hypergraph.n_nodes
    m_actual = hypergraph.n_edges
    density_actual = m_actual / n_actual if n_actual > 0 else 0.0

    arities = [len(e) for e in hypergraph.hyperedges()] if m_actual > 0 else []
    arity_hist: dict[int, int] = {}
    for a in arities:
        arity_hist[a] = arity_hist.get(a, 0) + 1

    return {
        "instance_key": cell.instance_key,
        "block_key": cell.block_key,
        "requested": {
            "n": cell.n,
            "k": cell.k,
            "mode": cell.mode,
            "generator": cell.generator,
            "density_ratio": cell.density_ratio,
            "seed": cell.seed,
        },
        "realized": {
            "n_nodes": n_actual,
            "n_edges": m_actual,
            "density": round(density_actual, 4),
            "arity_histogram": {str(a): cnt for a, cnt in sorted(arity_hist.items())},
            "max_arity": max(arities) if arities else 0,
            "connected": hypergraph.is_connected(),
        },
        "universe_size": math.comb(cell.n, cell.k) if cell.mode == "uniform" else None,
    }
