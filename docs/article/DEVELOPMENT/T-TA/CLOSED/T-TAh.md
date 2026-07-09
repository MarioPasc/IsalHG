# T-TAh — Remove the unsound `wl_colors` V-branch pruning from `greedy_h2s` and its C++ binding
**Declared:** 2026-07-09 11:58 CEST (handoff from T-TAc)
**Status:** DONE
**Depends on:** T-TAg (which already touches the C++ encoder for the branch budget — land together)
**Delegation:** agent — but **do not spawn a fresh worker.** T-TAg and T-TAh edit the
same file (`core/_native/src/h2s.cpp`), so they can never run in parallel, and a new
worker would pay a second conda clone and a second LTO/PGO build for nothing.
Continue T-TAg's worker with `SendMessage`: same worktree, same env, extension
already built, and the context that produced the budget is still loaded.
**Why out of scope:** T-TAc's boundary is "docstrings state the correct invariance
status; no behavioural change to defaults", and it explicitly excludes the C++
twins. Deleting the parameter changes the public `greedy_h2s` signature and the
nanobind binding, so it is a code change across both backends.
**Context to read first:**
- `src/isalhg/core/hypergraph_to_string.py::{_label_respecting_perms,_wl_orbit_canonical}` — the unsound branch and its (now corrected) docstrings
- `src/isalhg/core/hypergraph_to_string.py::{_encode_from,greedy_h2s}` — the `wl_colors` parameter threaded through both
- `src/isalhg/core/_native/bindings.cpp:149` — `std::optional<std::vector<std::int64_t>> wl_colors` in the binding signature
- `tests/unit/core/algorithms/test_wl_pruned_variants.py::test_wl_colors_pruning_discards_the_lex_min` — the pinned counterexample this removal makes moot
- `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/proofs/theorem_a_completeness.tex` — Lemma 6.1 (admissible pruning): raw ids are not an admissible key
- `.claude/rules/coding_rules.md` — always
**Description:** Two defects, one removal. **(a) Unsound.** Passing `wl_colors`
into `greedy_h2s` keeps only orderings in which WL-equivalent new inputs appear in
ascending vertex id. Raw ids are not transported by an isomorphism, so the
surviving ordering is a function of the numbering, and the pruning **discards the
lex-min completion** — pinned five-vertex counterexample (`n=5`,
`E={012,013,024,034}`, seed 0: the pruned string is strictly lex-greater than the
unpruned one). Its docstring claimed "the lex-min is unaffected". **(b) Dead and
broken.** No registered algorithm passes `wl_colors` — the two `*_wl_pruned`
variants filter the *seed set* only, which is admissible — and the C++ binding
declares `int64` while `wl_hash` returns unsigned 64-bit colours, so
`greedy_h2s(H, s, k, wl_colors=wl_hash(H))` raises `TypeError` on the default
backend. The feature cannot be used as documented, and should not be.
Remove `wl_colors` from `_label_respecting_perms`, `_encode_from`, `greedy_h2s`,
`_python_greedy_h2s`/`_cpp_greedy_h2s`, `bindings.cpp`, and the C++ `h2s.cpp`
twin; delete `_wl_orbit_canonical`; delete the pinned counterexample test with it.
If a V-branch speedup is ever wanted, the only sanctioned key is
stabiliser-orbit pruning (D-TA2), not a raw-id order.
**Acceptance:** `grep -rn wl_colors src/` returns nothing; `greedy_h2s`'s signature
and the nanobind binding no longer accept it; `w*` byte-identical on every fixture
and under the `tests/property/test_cpp_differential.py` sweep before and after;
full suite + ruff + mypy at their recorded baselines; C++ rebuilt.
**Out of scope here:** `PrunedExhaustive`'s min-id seed key (documented at T-TAc,
kept as a speed heuristic); implementing stabiliser-orbit pruning (a research
subtask flagged in D-TA2).

---

## Closing note (2026-07-09)

**Premise verified.** All premises held: `wl_colors` threaded through 6
Python functions + 4 C++ layers; `wl_orbit_canonical_stack` present in both
backends; the C++ binding in `canonical.cpp` already passed `std::nullopt`
(`wl_for_h2s = std::nullopt` on line 99 of the pre-change file), confirming the
feature was dead on every registered code path.

**Changes.**

*Python (`src/isalhg/core/hypergraph_to_string.py`):*
- Deleted `_wl_orbit_canonical`.
- `_label_respecting_perms`: removed `wl_colors` parameter and the
  `if wl_colors is not None and not _wl_orbit_canonical(...)` filter branch;
  updated docstring.
- `_encode_from`: removed `wl_colors` parameter and 4 forwarding kwargs;
  removed `wl_colors=wl_colors` from the `_label_respecting_perms` call.
- `_python_greedy_h2s`, `_cpp_greedy_h2s`, `greedy_h2s`: removed parameter and
  forwarding; updated docstrings.

*C++ (`src/isalhg/core/_native/`):*
- `h2s.hpp`: removed `wl_colors` from both function declarations.
- `h2s.cpp`: deleted `wl_orbit_canonical_stack`; removed `wl_colors` parameter
  from `enumerate_label_perms_cb` (always emitting all permutations now) and
  from both `encode_from` declaration + definition + all recursive call sites;
  removed from `greedy_h2s_tokens` and `greedy_h2s_str`.
- `canonical.cpp`: removed `wl_for_h2s = std::nullopt` declaration and updated
  both `greedy_h2s_tokens` call sites (parallel + sequential) to 4-arg form.
- `bindings.cpp`: removed `wl_colors` from both `greedy_h2s` and
  `greedy_h2s_tokens` nanobind bindings; updated docstrings.
- `_core.pyi`: updated both stubs to replace `wl_colors: list[int] | None = None`
  with `tie_branch: bool = False` as the 4th parameter.

*Tests:*
- Deleted `test_wl_colors_pruning_discards_the_lex_min` from
  `tests/unit/core/algorithms/test_wl_pruned_variants.py`.
- Removed now-unused imports: `from isalhg.core.hypergraph_to_string import greedy_h2s`
  and `sequence_sort_key` from `from isalhg.core.instructions import ...`.

**No canonical value changed.** The only caller that ever passed a non-None
`wl_colors` was the deleted test; `canonical.cpp` was already using
`std::nullopt`. The frozen-pin suite (`test_wstar_c_frozen.py`) confirmed 4/4
fixtures byte-identical before and after removal.

### Closing checks

```
grep -rn wl_colors src/ --include="*.py" --include="*.cpp" --include="*.hpp" --include="*.pyi":
    no matches (binary .pyc cache excluded)
pytest tests/unit tests/property tests/integration -q -m "not slow" --hypothesis-seed=0:
    685 passed, 8 skipped, 7 deselected
    (baseline 686; -1 = deleted test_wl_colors_pruning_discards_the_lex_min; zero regressions)
ruff check src/ tests/: 3 errors (baseline 3)
mypy src/isalhg/: 20 errors in 6 files
    (baseline 21; -1 from removal of wl_colors typed parameters — improvement)
test_wstar_c_frozen.py: 4/4 frozen pins pass unchanged
```

Files changed:
`src/isalhg/core/hypergraph_to_string.py`,
`src/isalhg/core/_core.pyi`,
`src/isalhg/core/_native/include/isalhg/h2s.hpp`,
`src/isalhg/core/_native/src/h2s.cpp`,
`src/isalhg/core/_native/src/canonical.cpp`,
`src/isalhg/core/_native/bindings.cpp`,
`tests/unit/core/algorithms/test_wl_pruned_variants.py`.
