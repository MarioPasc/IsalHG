# T-TAb — Augment the IsalHG fingerprint with the seed label (labelled completeness)
**Declared:** 2026-07-08 23:39 CEST (handoff from T-TA)
**Status:** DONE
**Depends on:** —
**Context to read first:**
- `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/proofs/theorem_a_completeness.pdf` — Counterexample 4.3 (seed-label deficiency) + Remark 1.10 (why `(ℓ_max, w*)` suffices)
- `src/isalhg/iso_backends/isalhg_backend.py::{_fingerprint_bytes,are_isomorphic}` — the false-positive site (labels `[0,0]` vs `[1,0]`, one edge: returns True)
- `src/isalhg/core/canonical.py::canonical_string` — where `ℓ_max` is knowable (all seeds share it under both cascades)
- `tests/property/test_canonical_invariance.py` — extend with a labelled-vocabulary strategy
- `.claude/rules/coding_rules.md` — always
**Description:** The canonical string never emits the seed vertex's label, so
on non-trivial vertex vocabularies two non-isomorphic hypergraphs can share
`w*` and `IsalHGBackend.are_isomorphic` returns false positives. Fix: make the
fingerprint the augmented pair — prepend the (iso-invariant) seed label to the
serialised string (e.g. `f"{ell_max};{w}"`) or return it as a tuple. Decide
placement (backend-only vs a `canonical_fingerprint` core helper) and whether
cached preprint fingerprints need regeneration. Extend the labelled property
tests (labelled small_connected_hypergraph strategy + pynauty colored oracle).
**Acceptance:** the pinned labelled pair no longer collides; labelled
invariance + completeness property tests green; trivial-vocabulary
fingerprints unchanged OR the format change is flagged and the affected
golden/cached artefacts regenerated.
**Out of scope here:** the tie-branch work (T-TAa); labelled corpora (T-M4').
**Closing (2026-07-09 11:24 CEST):**
- *Defect reproduced first (machine-verified):* `IsalHGBackend().are_isomorphic`
  returned `True` on `|Σ_V|=2`, one edge, labels `[0,0]` vs `[1,0]`, where
  pynauty says `False`. Bare `w*` = `V[0;1;1;0]` for both under **every** variant
  (`greedy_min`, `greedy_min_nbrdeg`, `greedy_min_complete`, `exhaustive`,
  `pruned_exhaustive`, `greedy_single`), so the deficiency is in the alphabet, not
  in a seed rule: `V` tokens emit only the labels of vertices they *create* and
  `C` tokens emit none.
- *Decisions (PI, `AskUserQuestion`, this session):* **(D1) placement =
  `core/canonical.py` helper** (not backend-only) — `canonical_string`'s signature
  and return are untouched, so `d_I` and the C++ dispatch are unaffected and
  `metric_space` can reuse `F`. **(D2) format = conditional prefix**: fingerprint
  is `b"{ell}|{w}"` when `n_vertex_labels > 1` and the bare `w` bytes when
  `n_vertex_labels == 1`. Trivial-vocabulary fingerprints are therefore
  **byte-identical** — no preprint artefact, no `fp_bytes_length` figure, and no
  golden regenerated. `are_isomorphic` already refuses to compare hypergraphs of
  differing vocabularies, so both sides always agree on the format. **(D3) `d_I`
  fixed now, guarded** rather than parked: Corollary A requires the augmented
  fingerprint, and on a labelled corpus the bare-`w*` `d_I` reads 0 on
  non-isomorphic pairs (identity of indiscernibles fails).
- *Seed-label derivation (design note, generalises the proof's `ℓ_max`):*
  `seed_vertex_label(H, w)` recovers the label as the single element of
  `multiset(ℓ_V) − multiset(labels emitted by w)`. Every vertex but the seed is
  created by a `V` token that records its label, so the subtraction is exact and
  **independent of the seed cascade** — it is well-defined for `exhaustive` /
  `pruned_exhaustive`, whose seed sets are *not* label-homogeneous and for which
  the proof's `ℓ_max` is undefined. Uniqueness: two seeds of different labels
  cannot yield the same `w`, since they emit different label multisets. Under
  both production cascades it coincides with the shared seed label (unit-tested
  against `max_neighbor_degree_nodes` and `max_xi_nodes`). Cost `O(n + |w|)`,
  skipped entirely on trivial vocabularies.
- *Code:* `core/canonical.py` gains `seed_vertex_label` + `canonical_fingerprint`
  (raises `InvalidLabelError` when `w` is not a canonical string of `H`);
  `iso_backends/isalhg_backend.py` splits `_canonical_string` out of
  `_fingerprint_bytes` and serialises `F` (the isolated-subprocess worker now
  returns the string, augmentation happens in the parent — no extra fork cost);
  `metric_space/distances/isalhg_levenshtein.py` prepends a `("seed", ℓ)` symbol
  to each token sequence, which is exactly Corollary A's "seed-label-prefixed
  string" and costs one substitution iff the seed labels differ (works for
  `normalize=True` too, unlike a `+1[ℓ≠ℓ']` additive term, which would leave the
  unit interval).
- *Acceptance (a) — pinned pair:* `tests/unit/iso_backends/test_isalhg_labelled_fingerprint.py`
  (11 tests) — collision gone for all four variants, `b"1|V[0;1;1;0]"` pinned,
  trivial-vocabulary fingerprint asserted **equal to the bare canonical string**,
  empty hypergraph still `b""`.
- *Acceptance (b) — labelled property tests:* `test_canonical_invariance.py` gains
  a labelled-pair strategy (two labellings of one structure, `|Σ_V| ∈ {2,3}`) with
  invariance-under-`permute` and the forward implication (`F` equal ⇒ iso), 200
  examples × {greedy_min, greedy_min_nbrdeg}. `test_completeness.py` gains the
  labelled **biconditional** for `greedy_min_complete` (100 examples) plus labelled
  invariance under relabel+edge-reorder. Both verified to have teeth: monkey-patching
  the backend back to the bare string makes them fail immediately at
  `--hypothesis-seed=0`. Measured pre-fix false-positive rate: **51/1000**
  shared-structure labelled pairs (and 34/3000 independently-drawn pairs — which is
  why the strategy shares the structure).
- *Oracle finding (⇒ handoff T-TAe):* pynauty **cannot** serve as the labelled
  oracle. `core/levi_reduction.py::LeviGraph.color_classes` builds the colour
  classes from the colours *present*, so unused label ids vanish and the ordered
  partition forgets which label each cell carries: `PynautyLeviBackend` reports
  labels `(0,0)` ≅ `(1,1)`, which is false under Def. 1.3. The labelled properties
  therefore use an exhaustive `n!`-bijection oracle,
  `tests/property/_labelled_oracle.py::brute_force_iso`. The same defect is in the
  bliss and Traces backends. Parked as **T-TAe**; unlabelled corpora (all corpora to
  date, incl. the whole preprint) are unaffected.
- *Closing checks* (`pytest tests/unit tests/property tests/integration -m "not slow"
  --hypothesis-seed=0`): **601 passed, 8 skipped, 3 deselected, 0 failed**. Property
  suite alone (core changed): **60 passed**. ruff **3 == baseline** (all pre-existing;
  `isalhg_backend.py`'s shifted 36→52). mypy **21 == baseline**, none in the three
  changed files — `metric_space/distances/isalhg_levenshtein.py` is fully clean.
  No C++ change → no rebuild owed by this task.
- *Note on a concurrent run:* T-TAd's C++ `tie_branch` port was being built in this
  same working tree during the closing check; a first pass caught the tree mid-rebuild
  (stale `.so` vs new `bindings.cpp`) and reported 13 `greedy_h2s()` arity failures in
  `test_backend_equivalence` / `test_cpp_differential` / `test_s2h_roundtrip`. Those
  are T-TAd's, not T-TAb's — none touches the fingerprint path — and all pass once the
  extension is rebuilt. The numbers above are from the post-rebuild run.
- *Docs:* `CLAUDE.md` §Mathematical Foundation + §Isomorphism test,
  `docs/article/theoretical/stability.md` §1, and the three modules' docstrings now
  state that isomorphism decisions run on `F`, never on bare `w*`.
