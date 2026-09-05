#!/usr/bin/env bash
# TKDE environment smoke test -- SLURM worker.
#
# Submit via smoke_launcher.sh. Do NOT submit directly.
#
# This is the ONE job in the campaign allowed to run under two hours: it exists
# to prove the environment before any real work is queued, so its whole value is
# in finishing fast. Every other TKDE job bundles units to >= 2 h (SCBI request,
# 2026-08-07).
#
# What it proves, on an `sd` COMPUTE node (not the login node):
#   1. the isalhg-tkde interpreter resolves inside IsalHG-tkde
#   2. the C++ extension isalhg.core._core imports (the AVX-512/SIGILL gate)
#   3. canonical_string(Fano, backend="cpp") == backend="python"
#   4. pynauty.canon_label runs on the Fano Levi graph
#   5. rapidfuzz imports
#   6. pytest tests/unit/core -q -m unit passes
#
# Node family. The extension is built on the login node (Xeon Gold 6230R,
# AVX-512) with the project's default -march=native. Array 2206615 pinned to
# `sr` died with SIGILL on every task in 8 s -- `sr` is AMD EPYC without
# AVX-512. `sd` is the login node's own family. Do NOT relax to `cpu` without
# rebuilding with -march=haswell (fallback documented in PICASSO.md).

#SBATCH --job-name=tkde-smoke
#SBATCH --time=0-00:30:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --constraint=sd
#SBATCH --account=tic_163_uma

set -euo pipefail

: "${REPO_DIR:?REPO_DIR not set -- submit via smoke_launcher.sh}"
# shellcheck source=/dev/null
source "${REPO_DIR}/slurm/tkde/common.sh"

tkde_job_header "tkde-smoke"
tkde_stage_localscratch "_smoke"

cd "${REPO_DIR}"

echo ""
echo "---------- check 1-5: interpreter, extension, engines ----------"
"${PY}" - <<'PYEOF' | tee "${OUT_DIR}/smoke_checks.txt"
import sys, json, pathlib

report = {}
ok = True

def check(name, fn):
    global ok
    try:
        value = fn()
        report[name] = {"status": "PASS", "value": str(value)}
        print(f"[PASS] {name}: {value}")
    except Exception as exc:                      # noqa: BLE001 - smoke test
        ok = False
        report[name] = {"status": "FAIL", "value": f"{type(exc).__name__}: {exc}"}
        print(f"[FAIL] {name}: {type(exc).__name__}: {exc}")

def _pkg_path():
    import isalhg
    p = isalhg.__file__
    assert "IsalHG-tkde" in p, f"interpreter resolves isalhg OUTSIDE IsalHG-tkde: {p}"
    return p

def _native():
    # The compiled module is isalhg.core._core (CMake: install TARGETS _core
    # DESTINATION isalhg/core). `isalhg.core._native` is the C++ SOURCE
    # directory and is not an importable module -- see PICASSO.md.
    import isalhg.core._core as native
    return native.__file__

def _canonical():
    from isalhg.core.canonical import canonical_string
    from isalhg.datasets.synthetic.designs import fano_plane
    H = fano_plane()
    cpp = canonical_string(H, backend="cpp")
    py = canonical_string(H, backend="python")
    assert cpp == py, f"cpp != python\n  cpp={cpp!r}\n  py ={py!r}"
    return f"w*_c(Fano) len={len(cpp)} cpp==python"

def _pynauty():
    import pynauty
    from isalhg.core.levi_reduction import to_levi
    from isalhg.datasets.synthetic.designs import fano_plane
    from isalhg.iso_backends.pynauty_levi import _to_pynauty
    g = _to_pynauty(to_levi(fano_plane()))
    lab = pynauty.canon_label(g)
    assert len(lab) == 14, f"Fano Levi has 7+7 nodes, canon_label gave {len(lab)}"
    return f"canon_label on Fano Levi, {len(lab)} nodes"

def _rapidfuzz():
    import rapidfuzz
    from rapidfuzz.distance import Levenshtein
    assert Levenshtein.distance("kitten", "sitting") == 3
    return f"rapidfuzz {rapidfuzz.__version__}"

print(f"[info] python  : {sys.executable}")
print(f"[info] version : {sys.version.split()[0]}")
check("isalhg_package_path", _pkg_path)
check("cpp_extension_import", _native)
check("canonical_cpp_eq_python", _canonical)
check("pynauty_canon_label", _pynauty)
check("rapidfuzz", _rapidfuzz)

report["python_executable"] = sys.executable
pathlib.Path("smoke_report.json").write_text(json.dumps(report, indent=2))
sys.exit(0 if ok else 1)
PYEOF
cp -f smoke_report.json "${OUT_DIR}/smoke_report.json" 2>/dev/null || true
rm -f smoke_report.json

echo ""
echo "---------- check 6: unit tests ----------"
"${PY}" -m pytest tests/unit/core -q -m unit 2>&1 | tee "${OUT_DIR}/pytest_unit_core.txt"
PYTEST_STATUS="${PIPESTATUS[0]}"
echo "PYTEST EXIT: ${PYTEST_STATUS}"
[[ "${PYTEST_STATUS}" -eq 0 ]] || { echo "[FATAL] unit tests failed" >&2; exit "${PYTEST_STATUS}"; }

{
    echo "node=$(hostname)"
    echo "cpu=$(lscpu 2>/dev/null | sed -n 's/^Model name: *//p' | head -1)"
    echo "job=${SLURM_JOB_ID:-local}"
    # The deployed tree has no .git; the provenance comes from the stamp
    # sync_to_picasso.sh writes.
    echo "deploy=$(tr '\n' ' ' < "${REPO_DIR}/.tkde_deploy" 2>/dev/null || echo n/a)"
    echo "date=$(date --iso-8601=seconds)"
} > "${OUT_DIR}/provenance.txt"

echo ""
echo "ALL SMOKE CHECKS PASSED"
tkde_job_footer
