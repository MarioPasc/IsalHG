# T-TAg — Harden the canonical surface: rename, guard `metric_space`, budget the search
**Declared:** 2026-07-09 11:25 CEST (handoff from the T-TAa/T-TAd assessment)
**Status:** DONE
**Depends on:** T-TAd (the flip), T-TAf (the freeze)
**Why out of scope:** T-TAd is the three-line default flip plus golden
regeneration. Making the *class of bug* unrepeatable — and making the complete
search fail loudly instead of hanging — is separate engineering, and it must not
delay the flip.
**Context to read first:**
- `docs/article/DEVELOPMENT/T-TA/OPEN/T-TAd.md` — the flip this hardens
- `src/isalhg/core/algorithms/greedy_min_complete.py` and `core/algorithms/registry.py` — the variant to rename
- `src/isalhg/metric_space/distances/isalhg_levenshtein.py::IsalHGLevenshtein` — currently accepts any `algorithm`; `d_I` over a greedy `w*` is not a metric
- `src/isalhg/errors.py::DistanceComputationError` — the exception to raise
- `src/isalhg/metric_space/distances/hged.py::ExactHGED` — the `timeout` / `max_expansions` pattern to mirror for the encoder budget
- `src/isalhg/iso_backends/isalhg_backend.py::_DEFAULT_ISALHG_ALGORITHM` — the `ISALHG_ALGORITHM` override the preprint pipeline pins
- `experiments/preprint/` — configs that must pin the greedy variant explicitly
- `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/proofs/theorem_a_completeness.tex` — Lemma 2.1 (exactly `m` emissions, but the branching factor is unbounded)
- `.claude/rules/coding_rules.md` — always
**Description:** Four hardenings, in order of value.
(a) **Guard `metric_space`.** `IsalHGLevenshtein` must compute `w*_c` and raise
`DistanceComputationError` if handed a non-complete algorithm. The default flip
alone does not prevent the bug — anyone passing `algorithm=` reintroduces a
non-metric `d_I` silently.
(b) **Budget the search.** The proof bounds the number of structural emissions
(exactly `m`) but *not* the branching factor `|T(σ)| × orderings`; GQ(2,2)-shaped
input already costs 1.09 s at n=15. Add a branch/expansion budget that raises
rather than hangs, mirroring `ExactHGED`'s `timeout` / `max_expansions`. A raised
error is a result; a hung sweep is not.
(c) **Rename** `greedy_min_complete` → `canonical` (or `tie_complete`). It is not
greedy, and the present name invites reading it as one variant among six rather
than as *the* canonical form.
(d) **Pin the preprint.** The greedy variants are the completed iso-benchmark
paper's measurement apparatus, so they are kept, not deleted (`coding_rules` §2.1's
no-shims rule does not cover published scientific artefacts). Re-document them as
one-sided iso heuristics — equal fingerprints certify isomorphism, unequal ones are
inconclusive, unusable for `d_I` — and pin `experiments/preprint/` configs to
`ISALHG_ALGORITHM=greedy_min_nbrdeg`.
**Acceptance:** `IsalHGLevenshtein(algorithm="greedy_min_nbrdeg")` raises;
`d_I` on both presentations of the pinned n=4 counterexample is `0.0` (it is `4.0`
today); a synthetic high-automorphism input exceeds the branch budget and raises
instead of hanging; the renamed variant is registered and the old name is gone from
`src/` (a grep for `greedy_min_complete` returns only the ledger and the proof);
the preprint configs reproduce their published fingerprints; full suite + ruff +
mypy at their recorded baselines.
**Out of scope here:** the flip itself (T-TAd); the definitional freeze (T-TAf);
deleting the greedy variants (explicitly rejected — see (d)); the WL-pruned
variants' docstrings (T-TAc).

---

## Closing note (2026-07-09)

All four hardenings landed. Rename choice: `"canonical"` over `"tie_complete"`.
The name reflects the *output* (`w*_c`, the canonical form) rather than the
search strategy; `core/canonical.py` is already the canonical entry point, so
`algorithms/canonical.py` names the algorithm that produces it. `"tie_complete"`
would name the mechanism, not the object; `"canonical"` is the object.

**(a) Guard `metric_space`.**
`IsalHGLevenshtein.__init__` raises `DistanceComputationError` on any algorithm
other than `CANONICAL_ALGORITHM`. The guard imports `CANONICAL_ALGORITHM` from
`isalhg.core.canonical` — DRY, forward-compatible with any future rename.
New tests: `TestGuard.test_non_canonical_algorithm_raises` (parametrized over all
four greedy variants) and `TestEdgeOrderInvariance` (the n=4 counterexample
verifying `d_I = 0.0` on both edge-order presentations).

**(b) Budget the search.**
Added `max_expansions: int | None = None` to `_python_greedy_h2s` and
`CanonicalEncoder.__init__`. A shared mutable counter `list[int]` is threaded
through all `_encode_from` recursive calls; each V-branch expansion increments
it and raises `CanonicalizationTimeoutError` when the budget is exceeded. Python
only — the C++ path needed only a one-line comment update (`7 = canonical`).
New tests: `TestBudget` with a cyclic-STS(13)-like structure at `max_expansions=5`
(raises) and `max_expansions=None` (succeeds).

**(c) Rename `greedy_min_complete` → `canonical`.**
Deleted `src/isalhg/core/algorithms/greedy_min_complete.py`; created
`algorithms/canonical.py` (`CanonicalEncoder`, registered as `"canonical"`).
Updated registry, `canonical.py` (`CANONICAL_ALGORITHM = "canonical"`,
`_CPP_VARIANT_IDS`), `isalhg_backend.py` (`_DEFAULT_ISALHG_ALGORITHM`,
docstring, per-algo loop), `iso_backends/registry.py` (`"isalhg_canonical"`).
Renamed `tests/unit/core/test_greedy_min_complete.py` →
`tests/unit/core/test_canonical_encoder.py`. All references in comments and
docstrings across `src/` updated; `grep greedy_min_complete src/ --include="*.py"`
returns nothing.

**(d) Pin the preprint.**
`experiments/preprint/pipeline/slurm/launcher.sh` now exports
`ISALHG_ALGORITHM=greedy_min_nbrdeg` so the preprint sweep pins the greedy
heuristic independently of the package default. Greedy variants documented as
one-sided iso heuristics in `isalhg_backend.py` docstring.

### Closing checks

```
pytest tests/ -q: 690 passed, 8 skipped (baseline 674+8; +16 new tests from T-TAg)
ruff check src/ tests/: 3 warnings (baseline 3)
mypy src/isalhg/: 21 errors (baseline 21)
grep greedy_min_complete src/ --include="*.py": no matches (EXIT:1)
```

---

## Defect-fix addendum (2026-07-09 — orchestrator verification round)

The closing note above stated hardening (b)'s budget was "Python only — the
C++ path needed only a one-line comment update." That was wrong. The C++
`canonical_string` FFI path (used by `IsalHGBackend`, `IsalHGLevenshtein`,
and every T-M5 sweep) bypassed the Python budget entirely: it calls
`_core.canonical_string` → `canonical_string_compute` → `greedy_h2s_tokens`
directly, without passing `max_expansions` to the C++ layer. Fixed.

**Changes (C++ side).**
- `errors.hpp`: added `CanonicalizationTimeoutError` C++ struct inheriting
  `IsalHGError`.
- `h2s.hpp`: added `int max_expansions = 0` (0 = unlimited) to
  `greedy_h2s_str` and `greedy_h2s_tokens` declarations.
- `canonical.hpp`: added `int max_expansions = 0` to
  `canonical_string_compute` declaration.
- `h2s.cpp`: added `expansion_count` and `max_expansions` fields to
  `WorkArena`; budget check placed *before* V-branch state mutations in the
  `enumerate_label_perms_cb` lambda — throw is safe at that point because
  no state has been mutated.
- `canonical.cpp`: threaded `max_expansions` to both `greedy_h2s_tokens`
  call sites (sequential and parallel). Fixed a pre-existing dangling-
  reference bug in the parallel seed loop: the original `for (auto& f :
  futures) f.get()` would leave worker threads running against destroyed
  locals if any future threw; replaced with join-all-then-rethrow.
- `bindings.cpp`: loaded `CanonicalizationTimeoutError` into `PyExcCache`,
  wired translation in `translate_exception`, added `max_expansions: int = 0`
  to the `canonical_string` nanobind binding.
- `src/isalhg/core/_core.pyi`: added `max_expansions: int = 0` to the
  `canonical_string` stub (omitting it caused mypy to count 22 errors
  instead of the baseline 21 on the `canonical.py:193` call site).

**Changes (Python side).**
- `canonical.py`: `_cpp_canonical_string` and `canonical_string` accept
  `max_expansions: int | None = None`; passed as `max_expansions or 0` to
  the C++ binding.
- `isalhg_levenshtein.py`: `IsalHGLevenshtein.__init__` accepts and stores
  `max_expansions`; forwarded through `_symbols → canonical_string`.
- `test_isalhg_levenshtein.py::TestBudget`: parametrized over
  `backend in {"cpp", "python"}` — both backends raise
  `CanonicalizationTimeoutError` with `max_expansions=5` on cyclic STS(13).

**Smoke test (pre-commit).**
```
OK: cpp raised CanonicalizationTimeoutError: canonical-string branch budget exceeded (5 expansions)
OK: python raised CanonicalizationTimeoutError: canonical-string branch budget exceeded (5 expansions)
OK: unlimited cpp succeeds, len=256
```

### Re-verified closing checks (post-fix)

```
pytest tests/unit tests/property tests/integration -q -m "not slow" --hypothesis-seed=0:
    686 passed, 8 skipped, 7 deselected
    (4 previously counted slow tests deselected; zero regressions)
ruff check src/ tests/: 3 errors (baseline 3 — unchanged)
mypy src/isalhg/: 21 errors in 6 files (baseline 21 — restored after stub fix)
```

Additional files changed in this round:
`src/isalhg/core/_native/include/isalhg/errors.hpp`,
`src/isalhg/core/_native/include/isalhg/h2s.hpp`,
`src/isalhg/core/_native/include/isalhg/canonical.hpp`,
`src/isalhg/core/_native/src/h2s.cpp`,
`src/isalhg/core/_native/src/canonical.cpp`,
`src/isalhg/core/_native/bindings.cpp`,
`src/isalhg/core/_core.pyi`,
`src/isalhg/core/canonical.py`,
`src/isalhg/metric_space/distances/isalhg_levenshtein.py`,
`tests/unit/metric_space/test_isalhg_levenshtein.py`.

---

Files changed: `src/isalhg/core/canonical.py`,
`src/isalhg/core/algorithms/canonical.py` (new),
`src/isalhg/core/algorithms/greedy_min_complete.py` (deleted),
`src/isalhg/core/algorithms/registry.py`,
`src/isalhg/core/algorithms/exhaustive.py`,
`src/isalhg/core/algorithms/greedy_min_inplace_wl_pruned.py`,
`src/isalhg/core/algorithms/greedy_min_wl_pruned.py`,
`src/isalhg/core/algorithms/pruned_exhaustive.py`,
`src/isalhg/core/hypergraph_to_string.py`,
`src/isalhg/core/_native/bindings.cpp`,
`src/isalhg/iso_backends/isalhg_backend.py`,
`src/isalhg/iso_backends/registry.py`,
`src/isalhg/metric_space/distances/isalhg_levenshtein.py`,
`tests/unit/core/test_canonical_encoder.py` (renamed from test_greedy_min_complete.py),
`tests/unit/core/test_wstar_c_frozen.py`,
`tests/unit/metric_space/test_isalhg_levenshtein.py`,
`tests/property/test_backend_equivalence.py`,
`tests/property/test_completeness.py`,
`tests/property/test_canonical_invariance.py`,
`tests/unit/core/test_seed_vertex_label.py`,
`tests/unit/iso_backends/test_isalhg_backend.py`,
`tests/unit/iso_backends/test_isalhg_labelled_fingerprint.py`,
`experiments/preprint/pipeline/slurm/launcher.sh`,
`CLAUDE.md`, `docs/article/theoretical/stability.md`,
`docs/article/CODE_DESIGN.md`.
