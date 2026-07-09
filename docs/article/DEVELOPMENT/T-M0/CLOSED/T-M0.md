# T-M0 — Seed-selection optimization (label → degree → lex-max neighbour-degree)
**Declared:** 2026-07-08 12:20 CEST
**Status:** DONE
**Depends on:** —
**Context to read first:**
- `docs/article/CODE_DESIGN.md` §6 ("Seed-selection optimization") — the spec
- `docs/article/PROPOSAL.md` §6 — the PI directive it implements
- `docs/article/theoretical/stability.md` §3 ("avalanche obstruction") — why fewer seeds shrink the avalanche surface
- `src/isalhg/core/structural_tuples.py::max_xi_nodes` and `::max_neighbor_degree_nodes` — the existing seeders to extend (the second, PI 2026-06-23, is the starting point)
- `src/isalhg/core/canonical.py::_python_canonical_string` — the dispatch site
- `src/isalhg/core/_native/include/isalhg/structural_tuples.hpp` and `src/isalhg/core/_native/src/canonical.cpp::canonical_string_compute` — the C++ twin + variant enum
- `tests/property/test_canonical_invariance.py` — the iso-invariance guard-rail
- IsalGraph paper `/media/mpascual/Sandisk2TB/research/ISAL/completed/isalgraph/article/69b82c5859ed47c5468ca199/methodology.tex` — seed-selection precedent
- `.claude/rules/coding_rules.md` — always
**Description:** Refine the H2S seed set to fewer starting nodes — maximal label,
then maximal degree, then lexicographically-maximal decreasing neighbour-degree
list — preserving isomorphism-invariance of `w*`, in both the Python reference
and the C++ core. Shrinks `w*` wall-clock (unblocks every downstream sweep) and
reduces the stability-theorem avalanche surface.
**Acceptance:** `tests/property/test_canonical_invariance.py` green under
Hypothesis (`--hypothesis-seed=0 --hypothesis-deadline=none`); iso-backend
partition agreement unchanged; measured wall-clock drop reported on the design
fixtures (Fano / STS(9) / STS(13) / GQ(2,2)).
**Out of scope here:** the pruned-backtracking variant (`canonical_pruned.py`) —
that is the separate Algorithm-R&D track; the stability *proof* (T-TB).
**Closing (2026-07-08 13:13 CEST):**
- *Premise correction:* the three-level cascade was **already implemented** (PI
  2026-06-23) in both `_python_max_neighbor_degree_nodes` and the C++ twin
  `max_neighbor_degree_nodes_compute`, wired as variants `greedy_min_nbrdeg`(5) /
  `greedy_single_nbrdeg`(6). The task therefore reduced to **validate → promote →
  measure**, not writing the seeder.
- *Promotion (global flip, per PI decision this session):* default `algorithm`
  → `"greedy_min_nbrdeg"` at all three surfaces — `canonical_string`,
  `IsalHGBackend.__init__`, `_DEFAULT_ISALHG_ALGORITHM` (env override
  `ISALHG_ALGORITHM` preserved, so the preprint pipeline is unaffected).
  Registered `isalhg_greedy_min_nbrdeg` / `isalhg_greedy_single_nbrdeg` backends.
  Updated Critical Invariant #4 (CLAUDE.md) + the `max_xi_nodes` "only admissible"
  docstring to "any iso-invariant seed set".
- *(a) property test:* `test_canonical_invariance.py` parametrized over
  `{greedy_min, greedy_min_nbrdeg}` — green under Hypothesis, `--hypothesis-seed=0`,
  incl. pynauty cross-check. Python≡C++ locked via `test_backend_equivalence.py`
  (nbrdeg added). New `tests/unit/iso_backends/test_isalhg_nbrdeg.py`.
- *(b) partition agreement:* `test_nbrdeg_partition_matches_pynauty` — the nbrdeg
  backend induces the **same iso-partition** as pynauty on {Fano, Fano′, STS(9),
  STS(9)′, STS(13)_a, STS(13)_b}. `w*` is **identical** to the ξ seeder on every
  design fixture (empirically verified).
- *(c) wall-clock:* `scripts/bench_seed_selection.py`. Honest result: **no drop in
  the default parallel regime** (parity) — the designs are vertex-transitive
  (identical seed sets) and the C++ pool parallelizes the fan-out (critical-path-
  bound). The seed-count win (gq22: 10→7) surfaces only under core saturation:
  `taskset -c 0` gives **1.34× on gq22** (561→420 ms), parity on the transitive
  designs. "Shrinks `w*` wall-clock" is really "shrinks seed-count / CPU work,"
  realized as wall-clock only on saturated cores; promotion stands on
  correctness + avalanche-surface reduction + never regressing.
- *Closing checks:* `pytest tests/unit tests/property tests/integration
  -m "not slow" --hypothesis-seed=0` → **408 passed, 8 skipped, 0 failed** (after
  fixing 3 pre-existing stale `name` assertions surfaced by the flip:
  `test_isalhg_backend.py`, `iso_backends/test_registry.py`,
  `protocols/test_fingerprint_timing.py`). ruff/mypy: **no new violations** (mypy
  baseline == current == 21 pre-existing `resolve()`-dispatch errors; 3 pre-existing
  ruff violations, none in changed logic). No C++ change → no rebuild.
- *Handoffs spawned:* T-M0a (conftest `gq_2_2_doily` is not a valid GQ(2,2)),
  T-M0b (Python `_neighbour_degree_key` rebuilds `primal_graph()` per node).
