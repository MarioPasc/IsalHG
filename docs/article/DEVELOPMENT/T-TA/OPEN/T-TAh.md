# T-TAh — Remove the unsound `wl_colors` V-branch pruning from `greedy_h2s` and its C++ binding
**Declared:** 2026-07-09 11:58 CEST (handoff from T-TAc)
**Status:** OPEN
**Depends on:** T-TAg (which already touches the C++ encoder for the branch budget — land together)
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
