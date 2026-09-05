"""Configuration, roots and seeds for the TKDE experiment runners.

Three responsibilities, all of them one-liners with a single authority:

* where the data and the results live (``ISALHG_DATA_ROOT`` /
  ``ISALHG_RESULTS_ROOT``, falling back to the drive defaults of ``DESIGN.md``
  G6; on Picasso both variables are exported by ``slurm/tkde/common.sh``);
* how a YAML configuration is read;
* the seed schedule -- master ``20260905``, per-RQ seeds
  ``rq_index * 10_000 + s`` for ``s in 0..S-1`` (``DESIGN.md`` G7). Every runner
  derives its seeds from :func:`seeds` so two research questions never share
  one, and a rerun of one question reproduces exactly.

This module also carries the exception root for ``experiments.tkde``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

DEFAULT_DATA_ROOT = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/data")
DEFAULT_RESULTS_ROOT = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE")
DATA_ROOT_ENV = "ISALHG_DATA_ROOT"
RESULTS_ROOT_ENV = "ISALHG_RESULTS_ROOT"

MASTER_SEED = 20_260_905
SEED_STRIDE = 10_000
DEFAULT_SEED_COUNT = 27


class TkdeError(Exception):
    """Root exception for the TKDE experiment harness."""


class TkdeConfigError(TkdeError):
    """A configuration file is missing, unreadable, or not a mapping."""


class TkdeIOError(TkdeError):
    """A results file could not be written, or a row violates its schema."""


class TkdeStatsError(TkdeError):
    """A statistic was requested on input it is not defined for."""


def load_yaml(path: Path | str) -> dict[str, Any]:
    """Read a YAML configuration file into a plain dictionary.

    Parameters
    ----------
    path : Path or str
        The ``.yaml`` file.

    Returns
    -------
    dict
        The parsed mapping; an empty file yields ``{}``.

    Raises
    ------
    TkdeConfigError
        If the file is absent, unparseable, or does not hold a mapping.
    """
    import yaml

    config_path = Path(path)
    if not config_path.is_file():
        raise TkdeConfigError(f"no configuration file at {config_path}")
    try:
        loaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise TkdeConfigError(f"{config_path} is not valid YAML: {exc}") from exc
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise TkdeConfigError(f"{config_path} must hold a mapping, got {type(loaded).__name__}")
    return loaded


def seeds(rq_index: int, S: int = DEFAULT_SEED_COUNT) -> list[int]:
    """Return the seed schedule of one research question.

    Parameters
    ----------
    rq_index : int
        The research-question number (1..7); a non-negative integer.
    S : int, optional
        Number of replications. Default 27 (``DESIGN.md`` G5).

    Returns
    -------
    list[int]
        ``[rq_index * 10_000 + s for s in range(S)]``.

    Raises
    ------
    TkdeConfigError
        If ``rq_index`` is negative or ``S`` is not positive.
    """
    if rq_index < 0:
        raise TkdeConfigError(f"rq_index must be non-negative, got {rq_index}")
    if S <= 0:
        raise TkdeConfigError(f"S must be positive, got {S}")
    return [rq_index * SEED_STRIDE + s for s in range(S)]


def results_root() -> Path:
    """Resolve the results root from ``ISALHG_RESULTS_ROOT``, else the default."""
    return _root_from_env(RESULTS_ROOT_ENV, DEFAULT_RESULTS_ROOT)


def data_root() -> Path:
    """Resolve the data root from ``ISALHG_DATA_ROOT``, else the default."""
    return _root_from_env(DATA_ROOT_ENV, DEFAULT_DATA_ROOT)


def _root_from_env(variable: str, default: Path) -> Path:
    import os

    value = os.environ.get(variable)
    return Path(value) if value else default


__all__ = [
    "DEFAULT_DATA_ROOT",
    "DEFAULT_RESULTS_ROOT",
    "DEFAULT_SEED_COUNT",
    "MASTER_SEED",
    "TkdeConfigError",
    "TkdeError",
    "TkdeIOError",
    "TkdeStatsError",
    "data_root",
    "load_yaml",
    "results_root",
    "seeds",
]
