"""The output path a `w°`-swap worker symlinks must be the one its runner writes.

This pins the coupling that cost the 2026-09-13 RQ2_ow run. `experiments/tkde/rq2.py`
builds its output directory from **module constants**, not from the config's
``experiment:`` key, so a worker that renames the experiment for subtree
separation points its symlink at a directory the runner never writes to. The
copy-back then mirrors an empty tree, reports success, and every row dies on the
node --- 22 tasks, zero rows, no error anywhere.

The tests read the shell scripts as text on purpose. What failed was not Python:
it was the agreement between a bash variable and a Python constant, and only a
test that reads both can hold it.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import experiments.tkde.rq2 as rq2
import experiments.tkde.rq8 as rq8

pytestmark = pytest.mark.unit

SLURM = Path(__file__).resolve().parents[2] / "slurm" / "tkde"


def _assignment(script: Path, name: str) -> str:
    """The literal a top-level ``NAME="value"`` assignment gives, first match."""
    match = re.search(rf'^{name}="([^"$]*)"', script.read_text(encoding="utf-8"), re.MULTILINE)
    assert match is not None, f"{script.name} has no literal {name}= assignment"
    return match.group(1)


class TestRQ2OwWorkerAgreesWithItsRunner:
    """The regression: the symlinked directory is the one rq2.py writes to."""

    @pytest.fixture
    def worker(self) -> Path:
        path = SLURM / "rq2_ow_worker.sh"
        assert path.is_file()
        return path

    def test_rq2_takes_its_experiment_from_a_module_constant(self):
        # The fact that makes the coupling necessary. If rq2.py ever starts
        # reading config["experiment"], this test is the place to find out.
        source = Path(rq2.__file__).read_text(encoding="utf-8")
        assert "RunPaths(root=results_root, rq=RQ_FOLDER, experiment=EXPERIMENT)" in source
        assert rq2.EXPERIMENT == "wellposedness"
        assert rq2.RQ_FOLDER == "RQ2_wellposedness"

    def test_the_worker_experiment_matches_the_runner_constant(self, worker):
        assert _assignment(worker, "EXPERIMENT") == rq2.EXPERIMENT

    def test_the_worker_folder_matches_the_runner_constant(self, worker):
        assert _assignment(worker, "RQ_FOLDER") == rq2.RQ_FOLDER

    def test_the_worker_asserts_the_coupling_at_run_time(self, worker):
        # A static match today is not enough: the worker must also refuse to run
        # if the constant moves under it.
        text = worker.read_text(encoding="utf-8")
        assert "runner.EXPERIMENT == want_experiment" in text
        assert "runner.RQ_FOLDER == want_folder" in text

    def test_the_worker_checks_the_link_lands_in_the_mirrored_tree(self, worker):
        text = worker.read_text(encoding="utf-8")
        assert "readlink -f" in text
        assert "MYLOCALSCRATCH}/out" in text

    def test_the_config_experiment_key_is_inert_for_paths_and_says_so(self):
        # rq2_ow.yaml may carry `experiment:` (it enters the run tag), but the
        # worker must not derive a path from it.
        worker = (SLURM / "rq2_ow_worker.sh").read_text(encoding="utf-8")
        assert "module constant" in worker.lower() or "MODULE CONSTANT" in worker


class TestRQ8WorkerIsNotExposed:
    """RQ8 escaped the same defect because its runner reads the config key."""

    def test_rq8_takes_its_experiment_from_the_config(self):
        source = Path(rq8.__file__).read_text(encoding="utf-8")
        assert 'config.get("experiment", EXPERIMENT)' in source

    def test_rq8_worker_stages_the_root_so_any_subdir_is_mirrored(self):
        text = (SLURM / "rq8_worker.sh").read_text(encoding="utf-8")
        # Staging "." makes OUT_DIR the results root, so whatever folder the
        # runner creates beneath it is inside the mirrored tree by construction.
        assert 'tkde_stage_localscratch "."' in text
