"""The results writers of ``DESIGN.md`` G6.

Every run writes exactly six kinds of file under
``<RESULTS_ROOT>/<RQ>/<experiment>/``::

    rows_<table>.csv    one row per finest measurement unit
    config.json         every parameter, seed, path, version, budget
    manifest.json       provenance: git SHA, host, CPU, versions, SLURM ids
    summary.json        the aggregates that feed the tables
    stats.json          intervals, Wilcoxon / Holm tables, effect sizes
    tables.md           the human-readable tables

The rows are written beside the statistics on purpose: a previous round of this
project lost the inputs a table was computed from, and no reader could
recompute it. Everything a number rests on stays next to the number.

Provenance has two sources because the deployed tree has two shapes. Locally
the repository is a git checkout and ``git rev-parse HEAD`` answers; on Picasso
``sync_to_picasso.sh`` rsyncs the tree *without* ``.git`` and stamps
``.tkde_deploy`` (``sha=... branch=... from=... at=...``) at the repo root, which
:func:`write_manifest` falls back to. ``ISALHG_REPO_ROOT`` overrides the
directory both are looked for in.

All writes are atomic (temporary file, then ``os.replace``), so an interrupted
job never leaves a half-written or zero-byte result file behind.
"""

from __future__ import annotations

import csv
import json
import os
import platform
import socket
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, is_dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from experiments.tkde.config import TkdeIOError

if TYPE_CHECKING:
    import pandas

REPO_ROOT_ENV = "ISALHG_REPO_ROOT"
DEPLOY_STAMP = ".tkde_deploy"
VERSIONED_PACKAGES: tuple[str, ...] = (
    "numpy",
    "scipy",
    "scikit-learn",
    "rapidfuzz",
    "pynauty",
    "pandas",
    "kmedoids",
    "netlsd",
)
SLURM_ENV_KEYS: tuple[str, ...] = (
    "SLURM_JOB_ID",
    "SLURM_ARRAY_JOB_ID",
    "SLURM_ARRAY_TASK_ID",
    "SLURM_JOB_NODELIST",
)

_PROCESS_START_ISO = datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class RunPaths:
    """Where one experiment's files go.

    Attributes
    ----------
    root : Path
        The results root (``<RESULTS_ROOT>``).
    rq : str
        Research-question folder, e.g. ``"RQ5_patterns"``.
    experiment : str
        Experiment folder inside it, e.g. ``"balanced"``.
    """

    root: Path
    rq: str
    experiment: str

    @property
    def dir(self) -> Path:
        """The directory the six files are written to."""
        return Path(self.root) / self.rq / self.experiment

    def ensure(self) -> Path:
        """Create :attr:`dir` (with parents) and return it."""
        target = self.dir
        target.mkdir(parents=True, exist_ok=True)
        return target


# ---------------------------------------------------------------------------
# Rows
# ---------------------------------------------------------------------------


def write_rows(
    paths: RunPaths,
    table: str,
    rows: Sequence[Mapping[str, Any]],
    *,
    columns: Sequence[str],
) -> Path:
    """Write ``rows_<table>.csv`` with ``columns`` in the given order.

    The file is overwritten, not appended: a runner is idempotent per unit and
    re-emits the whole table it owns, so an append would duplicate rows on a
    rerun.

    Parameters
    ----------
    paths : RunPaths
        Destination.
    table : str
        Table name; the file is ``rows_<table>.csv``.
    rows : Sequence[Mapping]
        The rows. A key absent from a row is written as an empty field.
    columns : Sequence[str]
        Column order. A row carrying a key not in ``columns`` is a schema
        violation and raises, rather than being silently dropped.

    Returns
    -------
    Path
        The written file.

    Raises
    ------
    TkdeIOError
        If ``columns`` is empty or a row carries an undeclared key.
    """
    if not columns:
        raise TkdeIOError(f"rows_{table}: columns must not be empty")

    declared = set(columns)
    for index, row in enumerate(rows):
        extra = sorted(set(row) - declared)
        if extra:
            raise TkdeIOError(
                f"rows_{table}: row {index} carries undeclared columns {extra}; "
                f"declared columns are {list(columns)}"
            )

    target = paths.ensure() / f"rows_{table}.csv"
    temporary = target.with_suffix(".csv.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns), restval="")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_value(row.get(key, "")) for key in columns})
    os.replace(temporary, target)
    return target


def _csv_value(value: Any) -> Any:
    """Render one cell: booleans as 0/1, containers as compact JSON, else itself."""
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (list, tuple, dict, set)):
        return json.dumps(_jsonable(value), separators=(",", ":"))
    return value


# ---------------------------------------------------------------------------
# JSON files
# ---------------------------------------------------------------------------


def write_config(paths: RunPaths, config: Mapping[str, Any]) -> Path:
    """Write ``config.json`` -- every parameter, seed, path, version, budget."""
    return _write_json(paths, "config.json", config)


def write_summary(paths: RunPaths, summary: Mapping[str, Any]) -> Path:
    """Write ``summary.json`` -- the aggregates that feed the tables."""
    return _write_json(paths, "summary.json", summary)


def write_stats(paths: RunPaths, stats: Mapping[str, Any]) -> Path:
    """Write ``stats.json`` -- intervals, Wilcoxon / Holm tables, effect sizes."""
    return _write_json(paths, "stats.json", stats)


def write_manifest(paths: RunPaths, *, extra: Mapping[str, Any] | None = None) -> Path:
    """Write ``manifest.json`` -- the provenance of this run.

    Parameters
    ----------
    paths : RunPaths
        Destination.
    extra : Mapping or None, optional
        Additional fields, merged last so a runner can override any default
        (a ``start_iso`` it measured itself, for instance).

    Returns
    -------
    Path
        The written file.
    """
    provenance = _repo_provenance()
    manifest: dict[str, Any] = {
        "rq": paths.rq,
        "experiment": paths.experiment,
        "git_sha": provenance["git_sha"],
        "git_source": provenance["source"],
        "git_branch": provenance.get("branch"),
        "hostname": socket.gethostname(),
        "cpu_model": _cpu_model(),
        "platform": platform.platform(),
        "python_version": sys.version.split()[0],
        "package_versions": _package_versions(),
        "slurm": {key: os.environ.get(key) for key in SLURM_ENV_KEYS},
        "start_iso": _PROCESS_START_ISO,
        "end_iso": datetime.now(UTC).isoformat(),
        "row_counts": _row_counts(paths),
    }
    manifest.update(dict(extra or {}))
    return _write_json(paths, "manifest.json", manifest)


def _write_json(paths: RunPaths, filename: str, payload: Mapping[str, Any]) -> Path:
    target = paths.ensure() / filename
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(json.dumps(_jsonable(payload), indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, target)
    return target


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------


def write_tables_md(paths: RunPaths, tables: Mapping[str, pandas.DataFrame]) -> Path:
    """Write ``tables.md``, one ``##`` section per table.

    Parameters
    ----------
    paths : RunPaths
        Destination.
    tables : Mapping[str, pandas.DataFrame]
        Section name to table, rendered in the mapping's order.

    Returns
    -------
    Path
        The written file.
    """
    lines: list[str] = [
        f"# {paths.rq} / {paths.experiment}",
        "",
        f"Generated {datetime.now(UTC).isoformat()}.",
        "",
    ]
    for name, frame in tables.items():
        lines.append(f"## {name}")
        lines.append("")
        lines.extend(_markdown_table(frame))
        lines.append("")

    target = paths.ensure() / "tables.md"
    temporary = target.with_suffix(".md.tmp")
    temporary.write_text("\n".join(lines), encoding="utf-8")
    os.replace(temporary, target)
    return target


def _markdown_table(frame: pandas.DataFrame) -> list[str]:
    """Render a DataFrame as GitHub-flavoured markdown without ``tabulate``."""
    columns = [str(column) for column in frame.columns]
    if not columns:
        return ["*(empty table)*"]
    lines = ["| " + " | ".join(columns) + " |", "|" + "|".join(["---"] * len(columns)) + "|"]
    for record in frame.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(_cell(value) for value in record) + " |")
    return lines


def _cell(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value).replace("|", "\\|")


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------


def repo_root() -> Path:
    """Directory git and the deploy stamp are looked for in.

    ``ISALHG_REPO_ROOT`` wins; otherwise the repository root inferred from this
    file's location (``experiments/tkde/io.py`` sits two levels below it).
    """
    override = os.environ.get(REPO_ROOT_ENV)
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[2]


def _repo_provenance() -> dict[str, Any]:
    """Return ``{git_sha, branch, source}`` from git, else the deploy stamp."""
    root = repo_root()
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=15,
            check=True,
        )
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        return {
            "git_sha": completed.stdout.strip(),
            "branch": branch.stdout.strip() or None,
            "source": "git",
        }
    except (OSError, subprocess.SubprocessError):
        pass

    stamp = root / DEPLOY_STAMP
    if stamp.is_file():
        fields = _parse_deploy_stamp(stamp.read_text(encoding="utf-8"))
        return {
            "git_sha": fields.get("sha"),
            "branch": fields.get("branch"),
            "source": f"{DEPLOY_STAMP}:{stamp}",
        }
    return {"git_sha": None, "branch": None, "source": "unavailable"}


def _parse_deploy_stamp(text: str) -> dict[str, str]:
    """Parse ``sha=... branch=... from=... at=...`` into a mapping."""
    fields: dict[str, str] = {}
    for token in text.split():
        if "=" in token:
            key, _, value = token.partition("=")
            fields[key] = value
    return fields


def _cpu_model() -> str:
    """CPU model name from ``lscpu``, else ``/proc/cpuinfo``, else ``unknown``."""
    try:
        completed = subprocess.run(
            ["lscpu"], capture_output=True, text=True, timeout=15, check=True
        )
        for line in completed.stdout.splitlines():
            if line.strip().startswith("Model name:"):
                return line.split(":", 1)[1].strip()
    except (OSError, subprocess.SubprocessError):
        pass
    try:
        for line in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return "unknown"


def _package_versions() -> dict[str, str]:
    """Installed version of each package the results depend on."""
    from importlib.metadata import PackageNotFoundError, version

    versions: dict[str, str] = {}
    for name in VERSIONED_PACKAGES:
        try:
            versions[name] = version(name)
        except PackageNotFoundError:
            versions[name] = "not installed"
    return versions


def _row_counts(paths: RunPaths) -> dict[str, int]:
    """Data-row count of every ``rows_*.csv`` already written in this directory."""
    counts: dict[str, int] = {}
    directory = paths.dir
    if not directory.is_dir():
        return counts
    for path in sorted(directory.glob("rows_*.csv")):
        with path.open("r", encoding="utf-8", newline="") as handle:
            counts[path.stem.removeprefix("rows_")] = max(0, sum(1 for _ in handle) - 1)
    return counts


# ---------------------------------------------------------------------------
# JSON coercion
# ---------------------------------------------------------------------------


def _jsonable(value: Any) -> Any:
    """Coerce numpy scalars/arrays, Paths, sets and dataclasses into JSON types."""
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_jsonable(item) for item in value]
    if is_dataclass(value) and not isinstance(value, type):
        if hasattr(value, "as_dict"):
            return _jsonable(value.as_dict())
        from dataclasses import asdict

        return _jsonable(asdict(value))
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (str, bool, int, float)) or value is None:
        return value
    # A numpy array has both .item and .tolist, but .item() only works at size
    # 1; the rank test must come first or every array raises.
    if hasattr(value, "ndim") and hasattr(value, "item"):
        if value.ndim == 0:
            return _jsonable(value.item())
        return _jsonable(value.tolist())
    if hasattr(value, "tolist"):
        return _jsonable(value.tolist())
    return str(value)


__all__ = [
    "RunPaths",
    "repo_root",
    "write_config",
    "write_manifest",
    "write_rows",
    "write_stats",
    "write_summary",
    "write_tables_md",
]
