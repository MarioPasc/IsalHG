#!/usr/bin/env bash
# bootstrap.sh -- IsalHG project scaffolding.
#
# Creates the full Isal-family directory layout (src/, tests/, benchmarks/,
# experiments/, slurm/, docs/, assets/, scripts/) with empty module stubs.
# No algorithm code is written here; bodies are placeholder docstrings only.
#
# Idempotent: existing files are NOT overwritten. Re-running the script after
# editing scaffold files is safe; the script prints "skip" per existing file
# and "create" per newly-written file.
#
# Usage:
#   bash scripts/bootstrap.sh                 # default: repo root = $(pwd)
#   bash scripts/bootstrap.sh /path/to/repo
#
# Run from the IsalHG repo root, or pass the root path as $1.

set -euo pipefail

ROOT="${1:-$(pwd)}"
ROOT="$(cd "$ROOT" && pwd)"

CREATED=0
SKIPPED=0

mk_dir() {
    local d="$ROOT/$1"
    if [[ -d "$d" ]]; then
        return 0
    fi
    mkdir -p "$d"
    echo "  mkdir  $1"
}

# Write a file only if it does not already exist.
# Usage: write_file <relative_path> <<'EOF'
#   contents
# EOF
write_file() {
    local rel="$1"
    local path="$ROOT/$rel"
    if [[ -e "$path" ]]; then
        echo "  skip   $rel"
        SKIPPED=$((SKIPPED + 1))
        # drain stdin so the heredoc does not leak into the next command
        cat >/dev/null
        return 0
    fi
    mkdir -p "$(dirname "$path")"
    cat >"$path"
    echo "  create $rel"
    CREATED=$((CREATED + 1))
}

py_stub() {
    # Emit a one-line module docstring stub.
    local purpose="$1"
    printf '"""%s."""\n' "$purpose"
}

echo "IsalHG bootstrap"
echo "  root: $ROOT"
echo

# ---------------------------------------------------------------------------
# Top-level directories
# ---------------------------------------------------------------------------

for d in \
    src/isalhg \
    src/isalhg/core \
    src/isalhg/core/algorithms \
    src/isalhg/adapters \
    tests/unit \
    tests/integration \
    tests/property \
    tests/eval_validation \
    benchmarks/real_data \
    benchmarks/synthetic_data \
    experiments \
    slurm \
    scripts \
    docs \
    assets
do
    mk_dir "$d"
done

# ---------------------------------------------------------------------------
# pyproject.toml
# ---------------------------------------------------------------------------

write_file pyproject.toml <<'TOML'
[build-system]
requires = ["setuptools>=68.0", "setuptools-scm>=8.0"]
build-backend = "setuptools.build_meta"

[project]
name = "isalhg"
version = "0.0.1"
description = "Instruction Set and Language for Hypergraphs"
readme = "README.md"
license = "MIT"
requires-python = ">=3.10"
authors = [
    {name = "Ezequiel Lopez-Rubio", email = "ezeqlr@lcc.uma.es"},
    {name = "Mario Pascual Gonzalez", email = "mpascual@uma.es"},
]
keywords = [
    "hypergraph",
    "hypergraph-representation",
    "instruction-strings",
    "hypergraph-isomorphism",
    "canonical-string",
    "combinatorics",
]
classifiers = [
    "Development Status :: 2 - Pre-Alpha",
    "Intended Audience :: Science/Research",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Scientific/Engineering",
    "Topic :: Scientific/Engineering :: Mathematics",
    "Typing :: Typed",
]
# Core has zero dependencies.
dependencies = []

[project.urls]
Homepage = "https://github.com/MarioPasc/IsalHG"
Repository = "https://github.com/MarioPasc/IsalHG"
Issues = "https://github.com/MarioPasc/IsalHG/issues"

[project.optional-dependencies]
# HyperNetX 2.4.0 has a missing transitive dep (fastjsonschema); pin it explicitly.
hypernetx = ["hypernetx>=2.4", "fastjsonschema>=2.20"]
xgi = ["xgi>=0.10"]
hypergraphx = ["hypergraphx>=1.7"]
viz = ["matplotlib>=3.7"]
bench = [
    "isalhg[hypernetx,xgi,viz]",
    "scipy>=1.10",
    "pandas>=2.0",
    "pyyaml>=6.0",
    "numpy>=1.26",
    "scikit-learn>=1.3",
]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "hypothesis>=6.0",
    "ruff>=0.4",
    "mypy>=1.0",
]
# pynauty wraps McKay's nauty 2.8.8 -- the iso baseline for the bipartite reduction.
eval = [
    "isalhg[hypernetx,xgi,viz,bench]",
    "python-Levenshtein>=0.21",
    "pynauty>=2.8",
]
all = ["isalhg[hypernetx,xgi,hypergraphx,viz,bench,dev,eval]"]

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
isalhg = ["py.typed"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"
markers = [
    "unit: Unit tests (no external deps)",
    "integration: Integration tests (external hypergraph libs)",
    "property: Property-based tests (hypothesis)",
    "slow: Long-running tests",
    "eval_validation: Validation tests on Picasso-generated eval data",
]

[tool.mypy]
python_version = "3.10"
strict = true
warn_return_any = true

[[tool.mypy.overrides]]
module = [
    "hypernetx", "hypernetx.*",
    "xgi", "xgi.*",
    "hypergraphx", "hypergraphx.*",
    "pynauty", "pynauty.*",
    "Levenshtein", "Levenshtein.*",
]
ignore_missing_imports = true

[tool.ruff]
target-version = "py310"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "ANN", "B", "SIM"]

[tool.ruff.lint.per-file-ignores]
"tests/integration/*.py" = ["E402"]
"tests/**/*.py" = ["N802"]
"benchmarks/**/*.py" = ["E402", "ANN"]
"tests/eval_validation/*.py" = ["E402", "ANN", "N806"]
TOML

# ---------------------------------------------------------------------------
# README.md
# ---------------------------------------------------------------------------

write_file README.md <<'MD'
# IsalHG

**Instruction Set and Language for Hypergraphs.** Third member of the *Isal*
algorithm family (Grupo de Inteligencia Computacional y Análisis de Imagen,
UMA). Sibling projects: [IsalGraph](https://github.com/MarioPasc/IsalGraph) and
IsalSR.

IsalHG represents a hypergraph as a string over a compact instruction alphabet
executed against a Circular Doubly-Linked List + `k`-pointer virtual machine.
The canonical-string output is conjectured to be a complete hypergraph-
isomorphism invariant.

## Status

Pre-alpha. Project scaffolding only. The seed proposal (`docs/isalhg_idea.pdf`)
is being translated into modules under `src/isalhg/core/`.

## Install

```bash
conda create -n isalhg python=3.11
conda activate isalhg
pip install -e ".[dev]"
```

Optional adapter extras: `pip install -e ".[hypernetx,xgi,hypergraphx]"`.

## Layout

```
src/isalhg/
  core/         zero non-stdlib deps; the algorithm itself
  adapters/     optional bridges to HyperNetX, XGI, HyperGraphX
tests/          unit / integration / property / eval_validation
benchmarks/     real_data + synthetic_data benchmark scripts
experiments/    paper-pipeline workers
slurm/          Picasso (UMA HPC) submission scripts
docs/           specs, idea seeds, papers
```

## Family

- **IsalGraph** — graphs (preprint 2026).
- **IsalSR** — labeled DAGs for symbolic regression (IEEE TPAMI 2026).
- **IsalHG** — hypergraphs (this repo).

## License

MIT.
MD

# ---------------------------------------------------------------------------
# LICENSE (MIT placeholder; confirm with PI before publishing)
# ---------------------------------------------------------------------------

write_file LICENSE <<'LIC'
MIT License

Copyright (c) 2026 Ezequiel López-Rubio, Mario Pascual González

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
LIC

# ---------------------------------------------------------------------------
# .gitignore (subset of IsalGraph's)
# ---------------------------------------------------------------------------

write_file .gitignore <<'GI'
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[codz]
*$py.class

# C extensions
*.so

# Caches
.mypy_cache/
.pytest_cache/
.ruff_cache/
.hypothesis/

# Packaging
build/
dist/
*.egg-info/
*.egg
.eggs/
share/python-wheels/

# Coverage / test
.coverage
.coverage.*
htmlcov/
coverage.xml

# Environments
.env
.envrc
.venv
env/
venv/

# Editor / IDE
.vscode/
.idea/

# Jupyter
.ipynb_checkpoints/

# Pipeline outputs
runs/
slurm-*.out

# OS / misc
.DS_Store
GI

# ---------------------------------------------------------------------------
# Repo-root conftest.py (empty hook)
# ---------------------------------------------------------------------------

write_file conftest.py <<'PY'
"""Repo-root pytest configuration hook. Per-suite conftest lives under tests/."""
PY

# ---------------------------------------------------------------------------
# src/isalhg package
# ---------------------------------------------------------------------------

write_file src/isalhg/__init__.py <<'PY'
"""IsalHG -- Instruction Set and Language for Hypergraphs."""

__version__ = "0.0.1"
PY

write_file src/isalhg/py.typed <<'PY'
PY

write_file src/isalhg/errors.py <<'PY'
"""Custom exception hierarchy for IsalHG."""


class IsalHGError(Exception):
    """Base class for IsalHG-specific errors."""


class InvalidInstructionError(IsalHGError):
    """Raised when an instruction token violates the alphabet's constraints."""


class CanonicalizationTimeoutError(IsalHGError):
    """Raised when canonical-string computation exceeds its time budget."""


class ArityMismatchError(IsalHGError):
    """Raised when an operation references more pointers than the machine has."""
PY

write_file src/isalhg/types.py <<'PY'
"""Type aliases used across the package."""

from __future__ import annotations

from typing import TypeAlias

NodeId: TypeAlias = int
EdgeId: TypeAlias = int
PointerIndex: TypeAlias = int
InstructionToken: TypeAlias = str
HyperedgeSet: TypeAlias = frozenset[NodeId]
PY

# ---------------------------------------------------------------------------
# src/isalhg/core (algorithm; zero non-stdlib deps)
# ---------------------------------------------------------------------------

write_file src/isalhg/core/__init__.py <<'PY'
"""IsalHG core: the algorithm itself. Zero non-stdlib dependencies."""
PY

write_file src/isalhg/core/cdll.py <<'PY'
"""CircularDoublyLinkedList -- array-backed CDLL of node identifiers.

Port template: IsalGraph/src/isalgraph/core/cdll.py.
"""
PY

write_file src/isalhg/core/pointers.py <<'PY'
"""KPointerSet -- manages the k pointers p_1..p_k of the IsalHG VM.

Generalizes IsalGraph's primary/secondary pointer pair to arbitrary k.
"""
PY

write_file src/isalhg/core/sparse_hypergraph.py <<'PY'
"""SparseHypergraph -- adjacency-set hypergraph with contiguous int node IDs.

Generalizes IsalGraph/src/isalgraph/core/sparse_graph.py: hyperedges are
frozensets of NodeId (arity >= 2). No multi-hyperedges (a given node-set
appears at most once).
"""
PY

write_file src/isalhg/core/instructions.py <<'PY'
"""Sigma_HG instruction tokens: V_{i,j}, C_i, P_i, N_i, W.

Parsing, validation, and constraint checks.
"""
PY

write_file src/isalhg/core/string_to_hypergraph.py <<'PY'
"""S2H interpreter: execute a string in Sigma_HG* and return the hypergraph."""
PY

write_file src/isalhg/core/hypergraph_to_string.py <<'PY'
"""H2S greedy encoder with the PI's tie-breaking cascade."""
PY

write_file src/isalhg/core/structural_tuples.py <<'PY'
"""Structural tuples xi (per-node) and eta (per-edge), depth 3 by default."""
PY

write_file src/isalhg/core/canonical.py <<'PY'
"""Canonical encoder: greedy seeded from nodes of max lexicographic xi."""
PY

write_file src/isalhg/core/canonical_pruned.py <<'PY'
"""Backtracking canonical variant. Algorithm currently unspecified by the PI."""
PY

write_file src/isalhg/core/algorithms/__init__.py <<'PY'
"""Algorithm variants for H2S / canonical encoding."""
PY

write_file src/isalhg/core/algorithms/base.py <<'PY'
"""H2SAlgorithm ABC -- shared interface for all encoder variants."""
PY

write_file src/isalhg/core/algorithms/greedy_min.py <<'PY'
"""Greedy from every seed; return shortest string."""
PY

write_file src/isalhg/core/algorithms/greedy_single.py <<'PY'
"""Greedy from one max-xi seed."""
PY

write_file src/isalhg/core/algorithms/exhaustive.py <<'PY'
"""Exhaustive search over all seed nodes."""
PY

write_file src/isalhg/core/algorithms/pruned_exhaustive.py <<'PY'
"""Exhaustive search with structural-triplet pruning."""
PY

# ---------------------------------------------------------------------------
# src/isalhg/adapters (optional library bridges)
# ---------------------------------------------------------------------------

write_file src/isalhg/adapters/__init__.py <<'PY'
"""Optional bridges to external hypergraph libraries.

Each adapter guards its external import; importing this package does NOT
require any of the optional deps to be installed.
"""
PY

write_file src/isalhg/adapters/base.py <<'PY'
"""HypergraphAdapter ABC -- bridge pattern between external libs and core.

Port template: IsalGraph/src/isalgraph/adapters/base.py.
"""
PY

write_file src/isalhg/adapters/hypernetx_adapter.py <<'PY'
"""Adapter for HyperNetX (PNNL)."""
PY

write_file src/isalhg/adapters/xgi_adapter.py <<'PY'
"""Adapter for XGI (Complex Networks group, UVM)."""
PY

write_file src/isalhg/adapters/hypergraphx_adapter.py <<'PY'
"""Adapter for HyperGraphX."""
PY

# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

write_file tests/conftest.py <<'PY'
"""Shared pytest fixtures for the IsalHG test suite."""
PY

# Unit tests (one per core module).
for f in \
    test_cdll.py \
    test_pointers.py \
    test_sparse_hypergraph.py \
    test_instructions.py \
    test_string_to_hypergraph.py \
    test_hypergraph_to_string.py \
    test_structural_tuples.py \
    test_canonical.py \
    test_canonical_pruned.py
do
    write_file "tests/unit/$f" <<PY
"""Unit tests for isalhg.core ${f%.py}."""
PY
done

# Integration tests (one per adapter; pytest.importorskip guards).
for f in \
    test_hypernetx_adapter.py \
    test_xgi_adapter.py \
    test_hypergraphx_adapter.py
do
    write_file "tests/integration/$f" <<PY
"""Integration tests for isalhg.adapters ${f%.py}. Optional dep guard via pytest.importorskip()."""
PY
done

# Property tests.
write_file tests/property/test_roundtrip.py <<'PY'
"""Hypothesis property: S2H(H2S(H)) ~ H for every valid hypergraph H."""
PY

write_file tests/property/test_canonical_invariance.py <<'PY'
"""Hypothesis property: canonical(H1) == canonical(H2) iff H1 ~ H2."""
PY

# Placeholder so the empty dir survives git.
write_file tests/eval_validation/.gitkeep <<'PY'
PY

# ---------------------------------------------------------------------------
# benchmarks / experiments / slurm / scripts / docs / assets stubs
# ---------------------------------------------------------------------------

write_file benchmarks/README.md <<'MD'
# benchmarks

`real_data/` and `synthetic_data/` benchmark scripts. Populated as the algorithm
matures. Mirror the layout used in IsalGraph (`benchmarks/real_data/` has one
sub-experiment per dataset).
MD

write_file benchmarks/real_data/.gitkeep <<'PY'
PY

write_file benchmarks/synthetic_data/.gitkeep <<'PY'
PY

write_file experiments/README.md <<'MD'
# experiments

Paper-pipeline workers (Hypothesis sweeps, ablations, end-to-end validations).
MD

write_file slurm/README.md <<'MD'
# slurm

Picasso (UMA HPC) SLURM submission scripts. Generated via the `picasso-sbatch`
skill. Constraints: Singularity-only (no Docker), conda activation, A100 nodes
via `--constraint=dgx`.
MD

write_file docs/DEVELOPMENT.md <<'MD'
# Development notes

Living document for IsalHG development. Pair-read with `CLAUDE.md` at the repo
root and the seed proposal (`docs/isalhg_idea.pdf`).

## TODO

- Port `cdll.py` from IsalGraph.
- Port `sparse_hypergraph.py` from IsalGraph's `sparse_graph.py`, generalizing
  edges to hyperedge sets.
- Implement Sigma_HG token parser and the constraint validator.
- Implement S2H interpreter.
- Implement H2S greedy with the tie-breaking cascade.
- Implement structural tuples xi and eta.
- Implement canonical entry point (greedy seeded from max-xi).
- Add HyperNetX and XGI adapters first; HyperGraphX after the core
  stabilizes. DHG dropped (see project memory).
- Hypothesis property tests for round-trip and canonical invariance.

## Open research questions (from the seed proposal)

1. Backtracking procedure for greedy ties: unspecified.
2. Value of `k`: global / input-dependent / adaptive.
3. Structural-tuple depth: fixed at 3 by analogy; ablation needed.
4. Complexity bound for canonical encoding.
5. Completeness proof for canonical-string invariant.
MD

write_file docs/README.md <<'MD'
# docs

Specs, seed proposals, papers, and development notes.

- `isalhg_idea.pdf` -- PI's seed proposal (2026-06-06).
- `DEVELOPMENT.md` -- living development notes and TODO.
MD

write_file scripts/README.md <<'MD'
# scripts

Utility scripts for the IsalHG repo.

- `bootstrap.sh` -- this scaffolding script. Idempotent.
MD

write_file assets/.gitkeep <<'PY'
PY

# ---------------------------------------------------------------------------
# Placeholder src/isalhg/core/README.md (referenced from CLAUDE.md)
# ---------------------------------------------------------------------------

write_file src/isalhg/core/README.md <<'MD'
# isalhg.core

Pure-stdlib core. Mathematical and architectural spec for the IsalHG algorithm.
Populated incrementally; for the seed proposal see `docs/isalhg_idea.pdf` and
the project memory file `idea_060626.md`.
MD

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

echo
echo "Bootstrap complete."
echo "  created: $CREATED"
echo "  skipped: $SKIPPED (already existed)"
