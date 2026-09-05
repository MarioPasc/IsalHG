#!/usr/bin/env bash
# Idempotent Picasso environment setup for the IEEE TKDE campaign.
#
# Runs ON PICASSO's LOGIN NODE (compute nodes have no outbound internet, so
# every download must happen here). Safe to re-run after a dependency change.
#
#   ssh picasso 'bash ~/fscratch/repos/IsalHG-tkde/scripts/tkde/picasso_env_setup.sh'
#
# Options:
#   --skip-deps    only rebuild the extension (no pip download traffic)
#   --recreate     delete and rebuild the conda env from scratch
#
# What it does, in order:
#   1. bootstrap conda
#   2. create isalhg-tkde (clone of isalhg, else fresh python=3.11)
#   3. install third-party dependencies
#   4. rm -rf build && pip install -e ".[dev]" from the TKDE repo
#   5. verify: import path, extension freshness, cpp==python canonical form
#
# The build uses the project's default flags (-O3 -march=native). The login node
# is a Xeon Gold 6230R (`sd` family, AVX-512); `sr` and `bl` are AMD without
# AVX-512, so the resulting .so SIGILLs there. Every TKDE job therefore pins
# --constraint=sd. Fallback if `sd` queue time becomes prohibitive: rebuild with
#   CMAKE_ARGS="-DCMAKE_CXX_FLAGS=-march=haswell" pip install -e ".[dev]"
# and relax to --constraint=cpu. Details in
# docs/article/D_ART3/experiments/PICASSO.md.

set -euo pipefail

TKDE_USER_ROOT="/mnt/home/users/tic_163_uma/mpascual"
REPO_DIR="${REPO_DIR:-${TKDE_USER_ROOT}/fscratch/repos/IsalHG-tkde}"
ENV_NAME="${TKDE_CONDA_ENV:-isalhg-tkde}"
ENV_PREFIX="${TKDE_CONDA_PREFIX:-${TKDE_USER_ROOT}/fscratch/conda_envs/${ENV_NAME}}"
SOURCE_ENV="${TKDE_SOURCE_ENV:-isalhg}"
DATA_ROOT="${ISALHG_DATA_ROOT:-${TKDE_USER_ROOT}/fscratch/datasets/isalhg_tkde}"
RESULTS_ROOT="${ISALHG_RESULTS_ROOT:-${TKDE_USER_ROOT}/fscratch/results/IEEETKDE}"
LOGS_DIR="${TKDE_LOGS_DIR:-${TKDE_USER_ROOT}/execs/tkde/logs}"
CONDA_SH="/mnt/home/soft/miniconda/programs/x86_64/miniconda3_py310_23.1.0/etc/profile.d/conda.sh"

SKIP_DEPS=0
RECREATE=0
for arg in "$@"; do
    case "${arg}" in
        --skip-deps) SKIP_DEPS=1 ;;
        --recreate)  RECREATE=1 ;;
        *) echo "ERROR: unknown option ${arg}" >&2; exit 2 ;;
    esac
done

echo "=== TKDE Picasso env setup ==="
echo "repo      : ${REPO_DIR}"
echo "env       : ${ENV_NAME}  (${ENV_PREFIX})"
echo "date      : $(date --iso-8601=seconds)"
echo "host      : $(hostname)"
echo "cpu       : $(lscpu 2>/dev/null | sed -n 's/^Model name: *//p' | head -1)"
echo "g++       : $(/usr/bin/g++ --version 2>/dev/null | head -1)"

[[ -d "${REPO_DIR}" ]] || { echo "ERROR: repo not deployed: ${REPO_DIR}" >&2
                            echo "       run scripts/tkde/sync_to_picasso.sh locally first" >&2
                            exit 1; }

mkdir -p "${DATA_ROOT}/raw" "${DATA_ROOT}/corpora" "${RESULTS_ROOT}" "${LOGS_DIR}"

# --- 1. conda -------------------------------------------------------------
# shellcheck source=/dev/null
source "${CONDA_SH}"

# --- 2. environment -------------------------------------------------------
if [[ "${RECREATE}" -eq 1 && -d "${ENV_PREFIX}" ]]; then
    echo "[env] --recreate: removing ${ENV_PREFIX}"
    conda env remove -y -p "${ENV_PREFIX}"
fi

if [[ -d "${ENV_PREFIX}" ]]; then
    echo "[env] ${ENV_NAME} already exists -- reusing"
else
    echo "[env] creating ${ENV_NAME} by cloning ${SOURCE_ENV}"
    if ! conda create -y -p "${ENV_PREFIX}" --clone "${SOURCE_ENV}"; then
        echo "[env] clone failed; creating fresh python=3.11"
        conda create -y -p "${ENV_PREFIX}" python=3.11
    fi
fi

PY="${ENV_PREFIX}/bin/python"
[[ -x "${PY}" ]] || { echo "ERROR: no interpreter at ${PY}" >&2; exit 1; }
echo "[env] python: $("${PY}" --version 2>&1)"

# --- 3. dependencies ------------------------------------------------------
if [[ "${SKIP_DEPS}" -eq 0 ]]; then
    echo "[deps] installing third-party packages (login node -- has internet)"
    "${PY}" -m pip install --upgrade pip
    "${PY}" -m pip install \
        pynauty rapidfuzz scikit-learn scipy pandas pyarrow pyyaml \
        hypothesis pytest netlsd kmedoids \
        nanobind scikit-build-core cmake ninja
else
    echo "[deps] --skip-deps: leaving packages untouched"
fi

# --- 4. build -------------------------------------------------------------
cd "${REPO_DIR}"
echo "[build] rm -rf build  (a cached CMakeInit.txt pins the previous compiler)"
rm -rf build

echo "[build] pip install -e '.[dev]' --no-deps"
set +e
"${PY}" -m pip install -e ".[dev]" --no-deps --no-build-isolation > /tmp/tkde_build.log 2>&1
BUILD_STATUS=$?
set -e
echo "PIP EXIT: ${BUILD_STATUS}"
if [[ "${BUILD_STATUS}" -ne 0 ]]; then
    echo "[build] no-build-isolation failed; retrying with isolation"
    set +e
    "${PY}" -m pip install -e ".[dev]" --no-deps > /tmp/tkde_build.log 2>&1
    BUILD_STATUS=$?
    set -e
    echo "PIP EXIT: ${BUILD_STATUS}"
fi
if [[ "${BUILD_STATUS}" -ne 0 ]]; then
    echo "=== last 40 lines of /tmp/tkde_build.log ==="
    tail -40 /tmp/tkde_build.log
    exit "${BUILD_STATUS}"
fi
tail -3 /tmp/tkde_build.log

# --- 5. verification ------------------------------------------------------
echo "[verify] import path, extension freshness, cpp == python"
cd "${REPO_DIR}"
PYTHONPATH="${REPO_DIR}/src:${REPO_DIR}" "${PY}" - <<'PYEOF'
import datetime, os, sys

import isalhg
print("isalhg      :", isalhg.__file__)
assert "IsalHG-tkde" in isalhg.__file__, "resolves OUTSIDE IsalHG-tkde"

import isalhg.core._core as native
mtime = datetime.datetime.fromtimestamp(os.path.getmtime(native.__file__))
print("extension   :", native.__file__)
print("built at    :", mtime.isoformat(timespec="seconds"))

from isalhg.core.canonical import canonical_string
from isalhg.datasets.synthetic.designs import fano_plane
H = fano_plane()
cpp = canonical_string(H, backend="cpp")
py = canonical_string(H, backend="python")
assert cpp == py, "cpp backend disagrees with python backend"
print("w*_c(Fano)  : len", len(cpp), "cpp == python OK")

import pynauty, rapidfuzz
print("pynauty     :", getattr(pynauty, "__version__", "?"))
print("rapidfuzz   :", rapidfuzz.__version__)
print("python      :", sys.version.split()[0])
PYEOF

echo ""
echo "=== SETUP OK ==="
echo "PY = ${PY}"
echo "Next: bash ${REPO_DIR}/slurm/tkde/smoke_launcher.sh --test-only"
