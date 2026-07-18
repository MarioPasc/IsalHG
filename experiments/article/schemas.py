"""Dataclasses for the T-M5a article experiment configuration.

A configuration file (YAML) declares a list of *cells*, each of which is one
atomic unit of computation.  The runner executes one cell per SLURM array task
(or all cells when run locally without --cell-index).

Cell types
----------
d_matrix
    Compute pairwise distance matrices for a corpus under one or more
    HypergraphDistance instances.  Produces per-distance D.npy + meta.json.
sensitivity
    E2b — per-edit d_I sensitivity histogram.  Produces sensitivity.json.
ladder
    E3 + T-TBb proxy — per-step d_I along perturbation ladders.  Produces
    ladder.json with cumulative and incremental d_I values.
info_content
    Fixed-width-code bit counts and compression ratios.  Produces
    info_content.json.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class CellSpec:
    """One atomic unit of computation in the T-M5a pipeline."""

    type: str
    """Cell type: 'd_matrix' | 'sensitivity' | 'ladder' | 'info_content'."""

    dataset: str
    """Registered dataset name (e.g. 'correlation_corpus', 'perturbation_ladder')."""

    seed: int = 0
    """Random seed passed to the dataset constructor and any stochastic steps."""

    dataset_params: dict[str, Any] = field(default_factory=dict)
    """Keyword arguments forwarded to the dataset constructor (excluding 'seed')."""

    distances: list[str] = field(default_factory=list)
    """Distance names for d_matrix cells; each gets its own D.npy + meta.json."""

    distance_params: dict[str, dict[str, Any]] = field(default_factory=dict)
    """Per-distance constructor kwargs keyed by distance name."""

    label: str = ""
    """Optional human label used in the output path (e.g. density-sweep bins)."""

    def output_key(self) -> str:
        """Return a slash-separated path fragment unique to this cell.

        Used to derive the output directory: ``output_root / output_key()``.
        """
        parts = [self.type, self.dataset]
        if self.label:
            parts.append(self.label)
        parts.append(f"seed{self.seed}")
        return "/".join(parts)


@dataclass
class ArticleConfig:
    """Full experiment configuration loaded from YAML."""

    output_root: Path
    """Root directory for all results.  Must be outside the git tree."""

    cells: list[CellSpec] = field(default_factory=list)
    """Ordered list of cells; SLURM array index maps 1-to-1 to this list."""

    @classmethod
    def from_yaml(cls, path: Path | str) -> ArticleConfig:
        """Load an ArticleConfig from *path*.

        Parameters
        ----------
        path : Path or str
            Path to the YAML configuration file.

        Returns
        -------
        ArticleConfig
        """
        with open(path) as f:
            raw = yaml.safe_load(f)

        output_root = Path(raw["output_root"])
        cells = [_parse_cell(c) for c in raw.get("cells", [])]
        return cls(output_root=output_root, cells=cells)

    def cell_output_dir(self, cell: CellSpec) -> Path:
        """Return the absolute output directory for *cell*."""
        return self.output_root / Path(cell.output_key())


def _parse_cell(raw: dict[str, Any]) -> CellSpec:
    return CellSpec(
        type=raw["type"],
        dataset=raw.get("dataset", ""),
        seed=int(raw.get("seed", 0)),
        dataset_params=dict(raw.get("dataset_params", {})),
        distances=list(raw.get("distances", [])),
        distance_params={k: dict(v) for k, v in raw.get("distance_params", {}).items()},
        label=raw.get("label", ""),
    )
