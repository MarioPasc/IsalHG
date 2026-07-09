# T-TAc — WL-pruned variants use inadmissible id-dependent pruning
**Declared:** 2026-07-08 23:39 CEST (handoff from T-TA)
**Status:** DONE
**Depends on:** —
**Context to read first:**
- `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/proofs/theorem_a_completeness.pdf` — Lemma "admissible pruning" (raw-id keys are not admissible) + Prop. on automorphism-coherent ties
- `src/isalhg/core/hypergraph_to_string.py::_wl_orbit_canonical` — keeps only id-ascending orderings within WL colour classes; its "the lex-min is unaffected" docstring claim assumes WL-equivalent ⇒ interchangeable, which is exactly the coherent-tie hypothesis, not a theorem
- `src/isalhg/core/algorithms/pruned_exhaustive.py` — min-vertex-ID WL-class seed representatives; its "Iso-invariance is preserved regardless" docstring claim is wrong for the same reason
- `.claude/rules/coding_rules.md` — always
**Description:** The `*_wl_pruned` variants and `pruned_exhaustive` resolve
choices by raw vertex id inside WL colour classes. WL colour ⊇ automorphism
orbit, so on WL-degenerate-but-rigid inputs these variants are (like the
greedy edge-id tie-break) presentation-dependent while their docstrings claim
invariance. Either (a) re-document them honestly as heuristics with the exact
condition (WL classes = orbits) under which they are exact, or (b) construct
the counterexample and demote/remove. No behavioural change to defaults.
**Acceptance:** docstrings state the correct invariance status with the
condition; if (b), a pinned counterexample test mirrors the T-TA pattern;
suite green.
**Out of scope here:** C++ twins of these variants; the tie-branch port (T-TAa).
**Closing (2026-07-09 11:58 CEST):** option **(b)** — counterexamples constructed,
not just re-documented. Three findings; the task's premise was right about one
target and wrong about two.

- ***Premise correction 1 (the `*_wl_pruned` variants are sound).*** The task
  asserted that `greedy_min_wl_pruned` / `greedy_min_inplace_wl_pruned` "resolve
  choices by raw vertex id inside WL colour classes". They do not. Both call
  `_wl_filtered_seeds`, which keeps the **entire argmin-WL-colour class** of the
  max-ξ seed set. The key is the WL colour *value*, which is iso-invariant and
  (verified) `PYTHONHASHSEED`-independent; no vertex id is read. This is an
  admissible pruning of an iso-invariant seed set under the proof's Lemma 6.1.
  Neither variant passes `wl_colors` into `greedy_h2s` — their own docstrings
  already said V-branch pruning would be unsound and explicitly declined it.
  Empirically invariant across 200 random relabels × 2 fixtures × 2 variants, and
  no counterexample in ~11k WL-degenerate 3-uniform samples. Their docstrings were
  wrong only in the *class* one-liners ("WL filter on seeds **and on V-branch
  permutations**"), now corrected, plus the newly stated inherited caveat: they
  are invariant under vertex relabelling but still depend on hyperedge insertion
  order (greedy's raw-edge-id V-tie-break, T-TA), so they are not canonical forms.

- ***Premise correction 2 (`pruned_exhaustive` is worse than stated).*** It is
  genuinely defective — it keeps the **min-id vertex per WL colour class**, an
  inadmissible raw-id key — but the task expected failure only on
  "WL-degenerate-but-rigid" inputs. It fails on the **triangular prism**, which is
  vertex-transitive with one WL class equal to one automorphism orbit. Reason: the
  docstring's escape hatch ("when WL classes are orbits the output equals
  `exhaustive`'s") is *also* false, because greedy H2S is not constant on an orbit
  — its residual V-tie-break reads raw edge ids, so the 6 same-orbit prism seeds
  yield 3 distinct strings. Corrected exactness condition, now in the docstring:
  the output equals `exhaustive`'s **iff greedy H2S is constant on every WL colour
  class**, strictly stronger than "WL classes = orbits".

- ***New defect found (⇒ handoff T-TAh).*** The `wl_colors` V-branch pruning
  (`_label_respecting_perms` / `_wl_orbit_canonical`) **discards the lex-min
  completion**, falsifying its docstring's core claim. Minimal counterexample:
  `n=5`, `E={012,013,024,034}`, colours `[0,1,1,1,1]`, seed 0 — the pruned string
  is 9 tokens and lex-greater than the unpruned 8-token one. Independently, the
  path is unreachable through the default backend: `bindings.cpp:149` declares
  `int64` while `wl_hash` returns unsigned 64-bit colours, so
  `greedy_h2s(H, s, k, wl_colors=wl_hash(H))` raises `TypeError`. No registered
  algorithm passes it. Removal touches `bindings.cpp` + the C++ `h2s.cpp` twin,
  which this task's `Out of scope` excludes → **T-TAh**.

- *Methodological note.* The first counterexample search was **contaminated** and
  discarded: it built hypergraphs from a Python `set`, so rebuilding from the
  printed edge list changed the hyperedge insertion order, and greedy is
  edge-order dependent (T-TA). Every counterexample above is taken under a **fixed
  edge list**, and `permute` preserves edge insertion order, so a relabel isolates
  the seed/branch key from the T-TA edge-id defect. `Exhaustive` is pinned as the
  scientific control: relabel-invariant on the very same fixtures.

- *Code:* `core/algorithms/pruned_exhaustive.py` (module + class docstrings:
  "speed heuristic, not iso-invariant, defines no canonical form, must never feed
  `d_I`"); `core/algorithms/greedy_min_wl_pruned.py` and
  `greedy_min_inplace_wl_pruned.py` (why the seed filter is admissible; inherited
  edge-order caveat; class one-liners corrected); `core/hypergraph_to_string.py`
  (`_label_respecting_perms`, `_wl_orbit_canonical`, and both `wl_colors` parameter
  blocks now state the pruning is unsound and unused). **Docstrings only — no
  behavioural change, no default changed, no C++ change, no rebuild owed.**

- *Tests:* `tests/unit/core/algorithms/test_wl_pruned_variants.py` +9 —
  `test_pruned_exhaustive_is_not_relabel_invariant` (prism + a 4-regular rigid
  n=10 graph), `test_exhaustive_is_relabel_invariant_on_the_same_fixtures`
  (control), `test_pruned_exhaustive_differs_from_exhaustive_on_vertex_transitive`,
  `test_seed_filtered_wl_variants_are_relabel_invariant` (25 relabels × 2 fixtures
  × 2 variants), `test_wl_colors_pruning_discards_the_lex_min`. Module docstring
  rewritten: it previously claimed the variants were "conjectured canonical".

- *Closing checks:* `pytest tests/unit/core/ -q` → **280 passed, 0 failed**;
  `pytest tests/unit/core/algorithms/ -q` → **58 passed**. ruff **clean** on all
  five changed files. mypy `src/isalhg/` → **21 errors == baseline** (the
  pre-existing `resolve()`-dispatch set; the 4 reported in
  `hypergraph_to_string.py` are in that baseline and my edits to that file are
  docstring-only). The **full suite was not run**: T-M0a and T-TAe were executing
  concurrently in this same working tree, mutating `tests/conftest.py` and
  `core/levi_reduction.py`, so a whole-tree `pytest` would not have attributed its
  result to this task. Whoever merges the three branches owes the full closing
  check.
