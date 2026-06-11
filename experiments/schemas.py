"""Experiment-config and result dataclasses.

Wraps :class:`isalhg.protocols.base.ProtocolResult` with the run-level
metadata needed for idempotent re-runs (atomic JSON skip-if-exists pattern
ported from IsalSR ``experiments/models/orchestrator.py``).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from isalhg.protocols.base import ProtocolResult
from isalhg.types import BackendName, DatasetName, ProtocolName, Seed


@dataclass(frozen=True)
class CellSpec:
    """One ``(protocol, backend, dataset, seed)`` cell of the experiment matrix."""

    protocol: ProtocolName
    backend: BackendName
    dataset: DatasetName
    seed: Seed
    protocol_params: dict[str, Any] = field(default_factory=dict)
    dataset_params: dict[str, Any] = field(default_factory=dict)
    backend_params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExperimentConfig:
    """Top-level YAML schema."""

    name: str
    description: str
    output_root: Path
    cells: tuple[CellSpec, ...]

    @classmethod
    def from_yaml(cls, path: Path) -> ExperimentConfig:
        """Load and validate an experiment YAML."""
        raise NotImplementedError


@dataclass(frozen=True)
class RunLog:
    """Persisted record of one cell's execution."""

    cell: CellSpec
    result: ProtocolResult
    hardware: dict[str, Any] = field(default_factory=dict)
    git_sha: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "cell": asdict(self.cell),
            "result": {
                "protocol": self.result.protocol,
                "backend": self.result.backend,
                "dataset": self.result.dataset,
                "seed": self.result.seed,
                "wall_clock_s": self.result.wall_clock_s,
                "measurements": self.result.measurements,
            },
            "hardware": self.hardware,
            "git_sha": self.git_sha,
        }

    def save_json(self, path: Path) -> None:
        """Atomic write: write to temp file then rename."""
        raise NotImplementedError

    @classmethod
    def load_json(cls, path: Path) -> RunLog:
        raise NotImplementedError

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> RunLog:
        raise NotImplementedError
