"""Experiment-config and result dataclasses.

Wraps :class:`isalhg.protocols.base.ProtocolResult` with the run-level
metadata needed for idempotent re-runs (atomic JSON skip-if-exists pattern
ported from IsalSR ``experiments/models/orchestrator.py``).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from isalhg.protocols.base import ProtocolResult
from isalhg.types import BackendName, DatasetName, ProtocolName, Seed

_REQUIRED_TOP_LEVEL_KEYS: tuple[str, ...] = ("name", "description", "output_root", "cells")
_REQUIRED_CELL_KEYS: tuple[str, ...] = ("protocol", "backend", "dataset", "seed")


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
        """Load and validate an experiment YAML.

        Raises
        ------
        ValueError
            On missing required key or on a non-dict cell entry.
        """
        try:
            import yaml
        except ImportError as exc:  # pragma: no cover - yaml is a hard dep
            raise ValueError(
                "experiment configs require PyYAML; install via `pip install pyyaml`"
            ) from exc
        with path.open("r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh)
        if not isinstance(raw, dict):
            raise ValueError(f"{path}: top-level YAML must be a mapping")
        missing = [k for k in _REQUIRED_TOP_LEVEL_KEYS if k not in raw]
        if missing:
            raise ValueError(f"{path}: missing required key(s) {missing}")

        cells_raw = raw["cells"]
        if cells_raw is None:
            cells_raw = []
        if not isinstance(cells_raw, list):
            raise ValueError(f"{path}: 'cells' must be a list, got {type(cells_raw).__name__}")
        cells: list[CellSpec] = []
        for idx, cell in enumerate(cells_raw):
            if not isinstance(cell, dict):
                raise ValueError(f"{path}: cells[{idx}] must be a mapping")
            cell_missing = [k for k in _REQUIRED_CELL_KEYS if k not in cell]
            if cell_missing:
                raise ValueError(f"{path}: cells[{idx}] missing key(s) {cell_missing}")
            cells.append(
                CellSpec(
                    protocol=str(cell["protocol"]),
                    backend=str(cell["backend"]),
                    dataset=str(cell["dataset"]),
                    seed=int(cell["seed"]),
                    protocol_params=dict(cell.get("protocol_params", {}) or {}),
                    dataset_params=dict(cell.get("dataset_params", {}) or {}),
                    backend_params=dict(cell.get("backend_params", {}) or {}),
                )
            )

        return cls(
            name=str(raw["name"]),
            description=str(raw["description"]),
            output_root=Path(raw["output_root"]),
            cells=tuple(cells),
        )


# ---------------------------------------------------------------------------
# Run log
# ---------------------------------------------------------------------------


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
                "measurements": _jsonable(self.result.measurements),
            },
            "hardware": self.hardware,
            "git_sha": self.git_sha,
        }

    def save_json(self, path: Path) -> None:
        """Atomic write: write to ``path.with_suffix(...tmp)`` then rename."""
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        payload = json.dumps(self.to_dict(), indent=2, sort_keys=True, default=_json_fallback)
        tmp.write_text(payload, encoding="utf-8")
        tmp.replace(path)

    @classmethod
    def load_json(cls, path: Path) -> RunLog:
        with path.open("r", encoding="utf-8") as fh:
            return cls.from_dict(json.load(fh))

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> RunLog:
        cell_d = d["cell"]
        cell = CellSpec(
            protocol=cell_d["protocol"],
            backend=cell_d["backend"],
            dataset=cell_d["dataset"],
            seed=int(cell_d["seed"]),
            protocol_params=dict(cell_d.get("protocol_params", {}) or {}),
            dataset_params=dict(cell_d.get("dataset_params", {}) or {}),
            backend_params=dict(cell_d.get("backend_params", {}) or {}),
        )
        res_d = d["result"]
        result = ProtocolResult(
            protocol=res_d["protocol"],
            backend=res_d["backend"],
            dataset=res_d["dataset"],
            seed=int(res_d["seed"]),
            wall_clock_s=float(res_d["wall_clock_s"]),
            measurements=dict(res_d.get("measurements", {}) or {}),
        )
        return cls(
            cell=cell,
            result=result,
            hardware=dict(d.get("hardware", {}) or {}),
            git_sha=str(d.get("git_sha", "")),
        )


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------


def _jsonable(value: Any) -> Any:
    """Recursively convert tuples/sets to JSON-serialisable shapes.

    JSON has no tuple type; round-tripping a measurement dict through
    ``json.dumps`` then ``json.loads`` would otherwise turn every tuple
    into a list silently. We pre-flatten here so the post-load shape
    matches the pre-save shape exactly for the keys callers compare on.
    """
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, (set, frozenset)):
        return sorted(_jsonable(v) for v in value)
    if isinstance(value, bytes):
        return {"__bytes_b64__": value.hex()}
    return value


def _json_fallback(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, bytes):
        return value.hex()
    raise TypeError(f"cannot JSON-serialise {type(value).__name__}")
