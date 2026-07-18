# T-M1c — Metric-axiom property suite for `d_I`, degenerate-domain guard, ablation honesty
**Declared:** 2026-07-09 12:46 CEST (handoff from the "is it a metric space?" audit)
**Status:** DONE
**Depends on:** T-TAd (so `d_I` computes `w*_c`); authorable earlier by passing
`algorithm="greedy_min_complete"` explicitly
**Why out of scope:** T-M1b's acceptance was "`d_I = 0` on isomorphic pairs, `> 0`
otherwise", checked on the greedy default. Corollary A claims a **metric on
isomorphism classes**, and no test exercises the axioms as such. The audit that
declared this gap also found a live identity-of-indiscernibles failure at the
degenerate end.
**Context to read first:**
- `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/proofs/theorem_a_completeness.tex` — Corollary A (`cor:metric`) and Assumption 1.3 (connected, fixed `k`, fixed vocabularies, fixed structural depth `h`)
- `src/isalhg/core/canonical.py::canonical_string` — the `if H.n_nodes == 0: return ()` short-circuit that causes the bug below
- `src/isalhg/core/canonical.py::canonical_fingerprint` · `src/isalhg/iso_backends/isalhg_backend.py::_fingerprint_bytes` — the augmented invariant `F = (seed label, w*_c)` the metric is actually taken over
- `src/isalhg/metric_space/distances/isalhg_levenshtein.py::IsalHGLevenshtein` — `normalize=True`, the `k`-pinning convention in `matrix()` vs `pairwise()`, and the deferred token-aware cost matrix (T-M1b decision D3)
- `tests/property/_labelled_oracle.py::brute_force_iso` — the exhaustive `n!` oracle (pynauty is NOT a valid labelled oracle, see T-TAe)
- `tests/property/test_hged_metric.py` — the pattern to mirror (self-0, symmetry, triangle, permutation invariance)
- Marzal, A. & Vidal, E. *Computation of normalized edit distance and applications*. IEEE TPAMI 15(9), 1993 — the naive length-normalized edit distance is **not** a metric; theirs is
- `docs/article/PROPOSAL.md` §6 OQ-D — raw Levenshtein is primary, normalization is an ablation
- `.claude/rules/coding_rules.md` — always
**Description:** Four items, one of which is a defect.

**(a) The degenerate-domain bug (machine-verified 2026-07-09).** `canonical_string`
short-circuits on `n_nodes == 0` and returns the empty sequence, which is also what
the single-vertex hypergraph emits (it creates no tokens). Measured:
`w*(∅) == w*(•) == ''`, `IsalHGBackend().are_isomorphic(∅, •) is True`, and
`d_I(∅, •) == 0.0` — identity of indiscernibles fails on a non-isomorphic pair.
Fix: restrict the metric's domain to `n ≥ 1` (raise on `n = 0`), or give the empty
hypergraph its own fingerprint. Safe because for `n ≥ 1` the *only* hypergraph
emitting the empty string is the single vertex: any `m ≥ 1` emits at least one token.

**(b) Property-test the axioms directly, over `w*_c`.** Non-negativity, symmetry,
triangle inequality over random triples, and identity of indiscernibles against
`brute_force_iso` (unlabelled and labelled, `|Σ_V| ∈ {1,2,3}`). The triangle
inequality is *inherited* from `d_Lev`, so the test is a regression guard on the
token-encoding layer (the private-use-codepoint mapping and the `("seed", ℓ)`
prefix), not on the mathematics.

**(c) Pin the ablations as non-metrics.** `normalize=True` (Levenshtein over max
length) **violates the triangle inequality**; Marzal & Vidal (1993) give the
metric-preserving normalization. Add a *pinned witness triple* where the naive
normalized distance violates `d(x,z) ≤ d(x,y) + d(y,z)`, so the codebase documents
why raw is primary. Same for the deferred token-aware substitution costs: the
resulting edit distance is a metric only if the symbol cost matrix is itself a
metric (zero diagonal, symmetric, triangle inequality) — assert that precondition
where the matrix is introduced, or state it in the docstring now.

**(d) Document the index family.** `w*_c` depends on `k` and on the structural
depth `h`, so `d_I` is a family `{d_I^{k,h}}`; values from different `k` are not
comparable. `matrix()` already pins the corpus-max `k` and `pairwise()` the
pair-max. Promote that convention from an implementation detail to a stated remark
in `IsalHGLevenshtein`'s docstring and in `stability.md` §1, and property-test that
a fixed `k` gives the same `d_I` regardless of which side is larger.
**Acceptance:** `d_I(∅, •) != 0` (or `n = 0` raises) and `are_isomorphic(∅, •)` is
`False`; a Hypothesis suite asserts the four metric axioms for `d_I` over `w*_c`,
labelled and unlabelled, against `brute_force_iso`; a pinned triple witnesses the
triangle-inequality violation of `normalize=True`, and its docstring calls it a
dissimilarity, not a metric; `IsalHGLevenshtein`'s docstring and `stability.md` §1
state the `(k, h, vocabulary)` indexing; the tests are shown to fail when the
`("seed", ℓ)` prefix is removed (teeth check, T-TAe pattern); full suite + ruff +
mypy at their recorded baselines.
**Out of scope here:** the default flip (T-TAd); the `metric_space` guard against
non-complete algorithms (T-TAg); implementing Marzal–Vidal normalization (an
ablation, not the primary distance); the stability bound (T-TB).
**Note for the paper (not a task):** topological completeness of `(X, d_I)` is
*trivially true and carries no information* — `d_I` is integer-valued, hence
uniformly discrete (`d ≥ 1` between distinct classes), hence every Cauchy sequence
is eventually constant. Do not state it as a result; it would be read as padding.
The only word "complete" earns is Theorem A's — `w*_c` is a **complete invariant**.
All geometric content is in the geometry pillar (`theoretical/geometry.md`),
not in a completeness statement.

---

## Closing check — 2026-07-18

**Branch:** `worktree-agent-a39b2a9aec8a4f0f3` (worker branch, merged to `main`)
**Worktree:** `/home/mpascual/research/code/IsalHG/.claude/worktrees/agent-a39b2a9aec8a4f0f3`
**Env:** `isalhg-T-M1c`

### Changes

- `src/isalhg/errors.py` — `DegenerateHypergraphError` added after `DisconnectedHypergraphError`
- `src/isalhg/core/canonical.py` — raises `DegenerateHypergraphError` on `n_nodes == 0` (replaces silent `return ""`)
- `src/isalhg/iso_backends/isalhg_backend.py` — n=0 guards in `fingerprint()` and `are_isomorphic()`
- `src/isalhg/metric_space/distances/isalhg_levenshtein.py` — docstring updated: index family `{d_I^{k,h,Σ}}`, `normalize=True` is a dissimilarity (Marzal & Vidal 1993), cost-matrix precondition
- `src/isalhg/datasets/synthetic/planted_families.py` — n=0 guard in `_build()` before fingerprint call
- `tests/property/test_di_metric_axioms.py` — NEW: full metric-axiom property suite (non-negativity, symmetry, triangle inequality, identity of indiscernibles; labelled + unlabelled; teeth check proving test fails without `("seed", ℓ)` prefix; `k`-pinning convention test)
- `tests/unit/metric_space/test_isalhg_levenshtein.py` — `TestDegenerateDomain` + `TestNormalizedNonMetric` (pinned triangle-violation witness `("Āā","ĀāĂ","āĂ")` with NLD 1/3,1/3,1.0)
- `tests/unit/iso_backends/test_isalhg_labelled_fingerprint.py` — `test_empty_hypergraph_fingerprint_raises` replaces old `test_empty_hypergraph_fingerprint_is_empty`
- `docs/article/theoretical/stability.md` — Index family remark added to §1 (domain restriction n≥1, normalized ablation note, Marzal & Vidal 1993 citation)

### Acceptance checks

- `are_isomorphic(∅, •)` is `False` (n=0 guard in `are_isomorphic`) ✓
- `d_I(∅, •)` raises `DegenerateHypergraphError` (propagated via `fingerprint`) ✓
- Hypothesis axiom suite passes over `w*_c`, labelled and unlabelled ✓
- Teeth check confirms suite FAILS when seed-label prefix is monkeypatched away ✓
- Pinned triple witnesses `normalize=True` triangle violation ✓
- `normalize=True` docstring says "dissimilarity, not a metric" ✓
- `{d_I^{k,h,Σ}}` index family documented in `IsalHGLevenshtein` docstring + `stability.md §1` ✓

### Test results

```
893 passed, 18 skipped, 13 deselected   (+16 vs baseline of 877)
ruff check src/ tests/ : 3 errors (pre-existing; no new violations)
mypy src/isalhg/       : 21 errors in 7 files (pre-existing baseline matched)
```
