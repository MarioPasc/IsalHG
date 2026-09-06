# Work log — ow-emitter

## Identity
| Field | Value |
|---|---|
| Agent | `ow-emitter` |
| Wave | `2026-09-06-isal-kb-w1` |
| Model / effort | Opus 5 (1M) / `xhigh` |
| Branch | `worktree-agent-aa0166cf355893a2a` |
| Worktree | `/home/mpascual/research/code/IsalHG/.claude/worktrees/agent-aa0166cf355893a2a` |
| Base commit | `99b8574f768b6f3dc53cc6ef9414cef5505dda04` |
| Head commit | `9e44f0d811b1d1b18df274fdefa2da50960cd0d4` (before this log's commit) |
| Started / finished | `2026-09-06T21:07:00+0200` / `2026-09-06T21:33:00+0200` |
| Status | complete |

## 1. Prompt as received

```
# Task: ow-emitter — the ordered-walk Isal word (core emitter + nauty entry point + distance arm + tests)

You are an implementation agent (name: `ow-emitter`) working inside an isolated git worktree on a branch of your own, in parallel with one peer (`orbit-prune`) who owns different files. You never see the orchestrator's conversation; everything you need is in this prompt and in the repository. WAVE_ID = `2026-09-06-isal-kb-w1`.

## Standing obligations
1. Work only inside your worktree (verify with `git rev-parse --show-toplevel`; it must NOT be `/home/mpascual/research/code/IsalHG`). Every file you create or edit must lie inside your declared ownership set. Everything else is read-only reference.
2. Commit all of your work in logical conventional commits before you finish. Uncommitted work does not exist: the orchestrator merges your branch, not your working tree. End every commit message with the trailer line `Claude-Session: https://claude.ai/code/session_01F3KtB1s4dXGiNVyyaHfsix`.
3. Maintain your work log at `.claude/notes/2026-09-06-isal-kb-w1/ow-emitter.md` from your first action to your last (template at the end of this prompt), and commit it as your final commit (`docs(notes): ow-emitter work log`).
4. Never run `git push`, never rebase/merge, never touch a peer's branch or worktree, never commit to the main checkout.
5. You cannot ask the user anything. On ambiguity, message `main` (SendMessage) with a specific question, record the assumption in your log, and keep working.
6. Never change a frozen contract yourself; propose to `main`.
7. Report failure honestly, with evidence.

## Mission
Implement the **ordered walk** `OW_π`: a deterministic emitter that, given a connected labelled hypergraph and a canonical vertex order (ranks from nauty on the coloured Levi graph), produces an instruction program over `Σ_HG = {V, C, P, N, W}` for the IsalHG machine, such that `S2H` decodes it back to an isomorphic hypergraph, and the pair (root label, word) is a complete isomorphism invariant. Expose it (i) as a stdlib-only core function, (ii) as a nauty-backed entry point in `iso_backends`, (iii) as a registered `HypergraphDistance` arm in three policy variants, with tests that pin round trip, invariance, validity, golden words, completeness on pairs, k-independence and the star-locality proposition. "Working" means every definition-of-done item below passes and the corpus verification numbers are in your log.

## Why this exists
D-ART4 (`docs/article/DEVELOPMENT/DECISIONS.md`) rules that the TKDE paper's representation is the Isal instruction string. The family's canonical string `w*_c` (tie-complete lex-min over walks) is not local under edits and is exponential on symmetric inputs. The ordered walk removes the search: nauty supplies the order, the Isal language supplies what is written. The design is pre-registered in `docs/article/D_ART3/experiments/ISAL_VARIANT_DESIGN.md` (read §0–§2 and §6 fully) and proved in `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/proofs/completeness/theorem_c_ordered_walk.tex` (read §3 "The ordered walk" — Definition 3.2 is the exact algorithm you implement — and §6 Proposition 6.3 "Star locality", which you turn into a unit test). The next wave registers your arm in the TKDE harness (`experiments/tkde/`), so the contracts below are frozen.

## Repository orientation
- Root of your worktree: `git rev-parse --show-toplevel`.
- Read first, in this order: `docs/article/D_ART3/experiments/ISAL_VARIANT_DESIGN.md`; the proof `.tex` §1–§4 and §6; `docs/article/H2S_S2H.md` §3–§5 (VM semantics: `V[le;i;j;ln…]` creates `j` nodes chained right after `p_1` in listed order and never moves pointers; `C[le;i]` over `p_1..p_i`; `P[i]`/`N[i]` unit steps on the circular list); `src/isalhg/core/instructions.py` (TokenV/TokenC/TokenP/TokenN/TokenW frozen dataclasses, `serialize`, `parse`, `validate`); `src/isalhg/core/string_to_hypergraph.py` (`StringToHypergraph`, `string_to_hypergraph(...)`); `src/isalhg/core/cdll.py`, `src/isalhg/core/pointers.py`; `src/isalhg/core/hypergraph_to_string.py` (reuse `_movement_tokens(displacement)` for rendering a move block — all `N` by pointer index then all `P`; and `_displaced_slot`); `src/isalhg/core/sparse_hypergraph.py` (`SparseHypergraph`, `permute`, labels, `n_vertex_labels`/`n_edge_labels` accessors); `src/isalhg/core/canonical.py` (`required_k`, `seed_vertex_label`, error classes used); `src/isalhg/iso_backends/canonical_order.py` (`canonical_ranks(H) -> tuple[int,...]`, `rank[v]` per vertex id; `nauty_certificate_rows`); `src/isalhg/core/levi_reduction.py`; `src/isalhg/metric_space/base.py` (`HypergraphDistance` ABC: `name`, `pairwise`, `matrix`, `fingerprint`, `labels_used`); `src/isalhg/metric_space/distances/isalhg_levenshtein.py` (mirror `_symbols`, `_encode`, the rapidfuzz usage and the `register_distance` call exactly); `src/isalhg/metric_space/distances/fact_levenshtein.py` (a registered word arm to mirror); `tests/unit/core/test_wstar_c_frozen.py` (the `(len, sha256)` pin convention — you create your OWN pin table, never touch theirs); `tests/conftest.py` (fixtures: fano_plane, sts_9, cyclic C13, GQ(2,2) doily, n=4 pair; `datasets/synthetic/sts_catalog.py`); `tests/unit/metric_space/test_representations_kb.py` (the relabel-sensitivity pattern for `labels_used`; replicate the pattern in your own test file, do not edit that file).
- Conventions: `CLAUDE.md` and `.claude/rules/coding_rules.md` are loaded for you. `core/` is stdlib-only (no numpy, no pynauty). Type hints everywhere, NumPy docstrings, no `print` in library code, custom exceptions from `isalhg.errors`.

## Your ownership (exclusive write access)
Create or modify ONLY:
- `src/isalhg/core/algorithms/ordered_walk.py` (new)
- `src/isalhg/iso_backends/isal_ordered.py` (new)
- `src/isalhg/metric_space/distances/isal_ordered.py` (new)
- the single registry / lazy-import table under `src/isalhg/metric_space/` that must list a distance module for `get_distance("isal_ow_struct")` to resolve (find how `fact_levenshtein` is made discoverable and add your module the same way; name the file in your log). If discoverability needs nothing beyond module-level `register_distance`, touch no registry file.
- `tests/unit/core/test_ordered_walk.py` (new), `tests/unit/metric_space/test_isal_ordered.py` (new), `tests/property/test_ordered_walk_roundtrip.py` (new)
- `scripts/diagnostics/ordered_walk_corpus_probe.py` (new; the corpus verification script)
- `.claude/notes/2026-09-06-isal-kb-w1/ow-emitter.md` (your log)
Everything else is read-only, in particular `src/isalhg/core/hypergraph_to_string.py`, `src/isalhg/core/canonical.py`, `src/isalhg/core/algorithms/registry.py`, `src/isalhg/iso_backends/orbit_oracle.py` (all owned by `orbit-prune`), and everything under `experiments/`. If the task seems to need an edit outside this set, stop and message `main`.

## Base state
- Base commit: `99b8574f768b6f3dc53cc6ef9414cef5505dda04` — "docs(tkde): pre-register the ordered-walk Isal word and orbit-pruned w*_c (D-ART4 annex)". Your worktree branches from it; so does your peer's.

## Frozen contracts (code against them exactly; propose changes to `main`, never edit unilaterally)
[the OrderedWalkPolicy / OrderedWalkResult / ordered_walk / ordered_word / ordered_fingerprint /
 ordered_symbols / POLICIES / IsalOrderedLevenshtein signatures, and the Definition 3.2
 restatement of the algorithm — reproduced verbatim in the prompt, implemented as given]

## Environment bootstrap ... ## Verification commands ... ## Data and shared resources ...
## Definition of done (12 items) ... ## Explicitly out of scope ... ## Peers in this wave ...
## Final message format ... ## Work log — mandatory (template)
```

*(The prompt's long verbatim contract block, environment bootstrap, verification commands,
definition-of-done list and log template are elided above only where they are reproduced
exactly elsewhere in this log — §11 walks the twelve definition-of-done items one by one.)*

**Mid-task course correction from `main` (verbatim):**

```
Contract change from main (your finding accepted; thank you for isolating it). The move rule is replaced, for ALL pointers in BOTH phases, by the "no-crossing" rule: compute every move in backward-position coordinates from the root's slot without wrapping. With pos(x) = number of backward steps from the root's slot to x's slot in the current CDLL (root = 0), a pointer at pos a moving to a target at pos b emits (b − a) tokens N if b > a, and (a − b) tokens P if b < a; nothing else. No move ever passes over the root's slot, and every run length is the number of slots strictly between the two positions on the root-free arc, so an insertion elsewhere never changes it. Rendering unchanged (`_movement_tokens`: all N by pointer index, then all P; note its sign convention — negative = N). Consequences you should observe: on binary stars the C-sweep is backward throughout, Prop 6.3(a) holds with max exactly 2 in the GENERAL regime (no backward-only restriction), and (b) is now stated as ≤ 3 when a later leaf is targeted (≤ 2 if x's creation position is preserved) — the signature-shift mechanism you found is now in the proof (Remark 6.5 and the restated (b); the proof file and the design record were updated). Please: (1) switch the move computation to this rule (both phases), (2) re-run your 400-star pins and assert (a) max ≤ 2 unconditionally and (b) ≤ 3 when a later leaf is targeted, keep the medians/fractions pinned, (3) report in your log the word-length price: median and max total move tokens per word under the new rule vs the shorter-direction rule on the same 400 stars and on the 300 wd50k66 members, (4) keep the corpus probe as specified. Everything else in the contract is unchanged; k-independence still holds. If the rule produces a run of more than n − 1 tokens anywhere, that is a bug — assert it.
```

## 2. Understanding and plan

**Restatement.** Build `OW_π`: from a connected labelled hypergraph plus a canonical rank
vector, emit a deterministic `Σ_HG` program whose `S2H` decode is isomorphic to the input
and whose `(root type, word)` pair is a complete isomorphism invariant. Ship it at three
layers (stdlib core, nauty-backed entry point, registered distance in three policies) with
tests pinning round trip, invariance, validity, golden words, completeness, k-independence
and star locality, plus a corpus probe on the two frozen knowledge-base collections.

**Approach chosen.** Implement the emitter as a *forward simulation of the decoder*. A
private `_Emitter` holds the same objects `StringToHypergraph` will hold — a
`CircularDoublyLinkedList`, a pointer vector, a creation index — and every emission mutates
them exactly as `S2H` would. Round trip is then structural rather than something to be
patched up afterwards, and it made the whole implementation land right the first time (0
failures on 400 random instances × 3 policies at the first smoke test).

Two representation choices carry the performance and the correctness:

- A `list` of slots in forward CDLL order from the root plus a `slot -> index` dict, both
  rebuilt after each `V`. That is `O(n²)` per word, which is nothing at these sizes
  (median 0.08 ms per corpus member) and makes both `pos(v)` and the move arithmetic
  one lookup.
- `K_V` and `K_C` are *injective* on their candidate sets — creation indices are injective
  on placed constants, ranks on all of them, and `pos` on all slots — so `min(...)` needs
  no residual tie-break. That is what makes the emitter search-free and is worth stating:
  it is the property the whole design turns on.

**Alternatives considered and rejected.**
- *Reusing `KPointerSet` for the simulated machine.* Rejected: it caps `k` at 10
  (`K_MAX`), and `ndc_classes` has members of arity 10 already. A plain list of slots has
  no cap and matches what `hypergraph_to_string._State` does.
- *Copying `_movement_tokens` into my module instead of importing it.* Rejected because the
  prompt says to reuse it, and one renderer for the family is the point. The cost is a
  private-name import from a file `orbit-prune` owns; flagged in §10.
- *Recomputing `pos` from scratch per query.* Rejected — same asymptotics, more code.
- *Marking the 2,000-instance sweeps `slow`.* Rejected: the whole core test file runs in
  19 s, so the numbers the definition of done asks for stay inside the default gate.

**Plan as executed.**
1. Read the design record §0–§2/§6, the proof §3 (Definition 3.2) and §6 (Prop 6.3), and
   the eleven source files the prompt lists. Clone the env, editable-install, verify
   `isalhg.__file__` points inside the worktree.
2. Write `core/algorithms/ordered_walk.py`; smoke-test round trip and invariance on Fano.
3. Write `iso_backends/isal_ordered.py` and `metric_space/distances/isal_ordered.py`; add
   three rows to `metric_space/registry.py::_LAZY_MODULES`. Commit.
4. Prototype Prop 6.3 before writing it as a test — the step that found the falsification.
5. Message `main`; receive the move-rule contract change; switch the rule; re-measure.
6. Write the three test files with the regenerated golden table; run; lint; type-check.
7. Write and run the corpus probe. Commit. Full suite. Log.

**Deviations from the plan.** One, and it was the substance of the task: prototyping
Proposition 6.3 (step 4) before pinning it showed the bound failing under the
then-frozen shorter-direction move rule. I did not change the rule — I measured both
deviation channels, reported them to `main` with the numbers, and continued on the old
rule until `main` sent the replacement. Steps 5–7 then ran against the new rule and every
golden pin was regenerated.

## 3. Changes made

**Created**

| Path | Purpose |
|---|---|
| `/home/mpascual/research/code/IsalHG/.claude/worktrees/agent-aa0166cf355893a2a/src/isalhg/core/algorithms/ordered_walk.py` | The emitter: `OrderedWalkPolicy`, `DEFAULT_POLICY`, `OrderedWalkResult`, `OrderedWalkError`, `ordered_walk`. Stdlib-only. |
| `.../src/isalhg/iso_backends/isal_ordered.py` | nauty-backed entry point: `POLICIES`, `ordered_word`, `ordered_fingerprint`, `ordered_symbols`. |
| `.../src/isalhg/metric_space/distances/isal_ordered.py` | `IsalOrderedLevenshtein` + the three `register_distance` calls. |
| `.../tests/unit/core/test_ordered_walk.py` | Round trip, invariance, validity, completeness, k-independence, star locality, the golden table. 74 tests. |
| `.../tests/unit/metric_space/test_isal_ordered.py` | Registration, `labels_used`, symbol split, metric axioms, matrix. 31 tests. |
| `.../tests/property/test_ordered_walk_roundtrip.py` | Hypothesis: round trip, invariance, validity. 9 tests. |
| `.../scripts/diagnostics/ordered_walk_corpus_probe.py` | The corpus verification script. |
| `.../.claude/notes/2026-09-06-isal-kb-w1/ow-emitter.md` | This log. |

**Modified**

| Path | Change | Reason |
|---|---|---|
| `.../src/isalhg/metric_space/registry.py` | Three rows added to `_LAZY_MODULES` (`isal_ow_struct`, `isal_ow_rank`, `isal_ow_rank0` → `isalhg.metric_space.distances.isal_ordered`). | This is the single registry / lazy-import table the prompt names: `get_distance` only imports a module it can find here, and `available_distances()` enumerates from it. Module-level `register_distance` alone is not enough. |

**Removed** — none.

**Commits**

| SHA | Message |
|---|---|
| `ed18fd42f22093c38d76bbe106ba48cfaaebcee4` | `feat(core): the ordered-walk Isal word — emitter, nauty entry point, distance arm` |
| `709adcca73cb37f3c3680af948568002d9e4797e` | `feat(core): no-crossing move rule + the ordered-walk test suite` |
| `9e44f0d811b1d1b18df274fdefa2da50960cd0d4` | `feat(diagnostics): ordered-walk corpus probe on wd50k66 and ndc_classes` |
| *(this log)* | `docs(notes): ow-emitter work log` |

<!-- matches `git diff --name-only 99b8574..HEAD` exactly:
scripts/diagnostics/ordered_walk_corpus_probe.py
src/isalhg/core/algorithms/ordered_walk.py
src/isalhg/iso_backends/isal_ordered.py
src/isalhg/metric_space/distances/isal_ordered.py
src/isalhg/metric_space/registry.py
tests/property/test_ordered_walk_roundtrip.py
tests/unit/core/test_ordered_walk.py
tests/unit/metric_space/test_isal_ordered.py
-->

## 4. Tests

**Tests created or extended**

| Test | File | What it verifies | Why it matters |
|---|---|---|---|
| `TestRoundTrip::test_design_fixtures` / `::test_random_corpus` | `tests/unit/core/test_ordered_walk.py` | `S2H(w_o) ≅ H` on 12 designs and 2,000 random instances, all 3 policies, iso decided by **pynauty** | Lemma C.3. The oracle is external on purpose — deciding with our own fingerprint would be circular |
| `TestRoundTrip::test_creation_order_is_the_isomorphism` | same | `creation_order` maps each input constant to the constant the decoder creates at that position, fact by fact | Makes the round trip constructive, not just existential |
| `TestInvariance::test_designs_under_200_relabellings` | same | 200 relabel-and-reorder copies per design (11 designs × 3 policies) | The half of Theorem C the greedy `w*` fails |
| `TestInvariance::test_random_corpus_under_20_relabellings` | same | 2,000 × 20 × 3 = 120,000 comparisons | Scale evidence, and it covers non-trivial vocabularies |
| `TestValidity::test_designs_and_random` | same | `validate` at `required_k`; no `W`; **distinct pointer slots at every `V`/`C`**, by replaying the program against a fresh CDLL | Lemma C.2. A coincident pointer would silently build a lower-arity fact and the round trip would still pass on some inputs |
| `TestValidity::test_no_move_run_is_longer_than_n_minus_one` | same | No run of one repeated `P`/`N` exceeds `n − 1` | `main`'s requested assertion: a longer run means a move wrapped past the root, which is the bug the no-crossing rule exists to exclude |
| `TestCompleteness::test_thousand_pairs` | same | 1,000 pairs (340 isomorphic by `permute`, 660 random) against pynauty, both directions, 3 policies | Theorem C, measured rather than assumed |
| `TestPointerCountIndependence` | same | Tokens identical at `required_k(H)` and at `k = 10`, 200 instances × 3 policies | Lets `d_o` compare a corpus without pinning `k`, unlike `d_I` |
| `TestStarLocality` (4 tests) | same | Prop 6.3(a) max 2 unconditional; (b) max 3 when a later leaf is targeted and max 2 when `x` keeps its position; no `P` in a star word; median/fraction pins | The R1 locality claim, and the two mechanisms |
| `test_ordered_word_is_pinned` (36 params) | same | Own `(len, sha256)` table per (policy, fixture) | A change here is a definitional event |
| `test_the_pins_are_not_the_wstar_c_pins` | same | `w_o(Fano) != w*_c(Fano)` | Guards against ever reconciling the two tables |
| `TestPolicyAndErrors` (6 tests) | same | Policy names; `DegenerateHypergraphError` on `n = 0`; `DisconnectedHypergraphError`; `OrderedWalkError` on bad ranks; the `n = 1` empty word; the seed prefix only on a non-trivial vocabulary | The contract's error surface |
| `TestRegistration`, `TestLabelDeclaration`, `TestSymbols`, `TestMetricAxioms`, `TestMatrix` | `tests/unit/metric_space/test_isal_ordered.py` | Registry resolution and names; `labels_used` against measured relabel sensitivity (the `test_representations_kb.py` pattern, replicated not edited); `P[1] != N[1]` despite equal hashes; identity of indiscernibles against pynauty, symmetry, triangle; `matrix` == `pairwise` | The arm must be usable by the next wave's harness and must not lie about what it reads |
| 3 hypothesis properties | `tests/property/test_ordered_walk_roundtrip.py` | Round trip, invariance, validity over generated connected labelled KBs, 60 examples each × 3 policies | Distribution coverage the fixed corpora do not give |

**Coverage of the behaviour that matters.** Every claim in the definition of done has a
test that would fail if the claim were false, and the two claims that could be checked
circularly (round trip, completeness) are decided by pynauty instead of by the emitter.
The `labels_used` declaration is pinned by *measurement* in both directions, so an arm that
quietly stopped reading predicates would fail — and it is also swept by the pre-existing
`tests/unit/metric_space/test_representations_kb.py`, which parametrizes over
`registry.available_distances()` and therefore picked up my three arms automatically
(2,160 passed, so it did).

**Not tested, and why.**
- *`w_o` against a hand-computed word on a worked example.* The golden pins fix the value;
  a hand derivation would be a second implementation, not an independent check.
- *Behaviour when `ranks` is a valid permutation but not nauty's.* `ordered_walk` accepts
  any permutation by contract (that is what keeps `core/` stdlib-only), and the invariance
  claim is about the nauty-supplied one. Out of scope.
- *Arity above 10.* `required_k` would exceed the alphabet's documented cap; neither corpus
  reaches it (`ndc_classes` max arity is exactly 10).
- *Performance regression thresholds.* The probe reports timings; turning them into
  assertions would make the suite machine-dependent.

## 5. Test results

**Command:** `~/.conda/envs/isalhg-owemit/bin/python -m pytest tests/unit tests/property -q --no-header -m "not slow" --hypothesis-seed=0`

```
=== 2160 passed, 7 skipped, 34 deselected, 21 warnings in 233.01s (0:03:53) ====
```

**Result:** 2,160 passed, 0 failed, 7 skipped, 34 deselected · **Duration:** 233 s ·
**Run at:** `9e44f0d811b1d1b18df274fdefa2da50960cd0d4`

**Failures and their resolution:** none. There are **no pre-existing failures** in this
suite — the 7 skips and 34 deselections are the usual optional-dependency and `slow`
exclusions, unchanged from the base commit. The 21 warnings are pre-existing (xgi's
`fast_random_hypergraph` notice, two scipy numerical warnings in the stats harness and the
geometry metrics) and none originate in my files.

Focused run, used throughout development:

**Command:** `~/.conda/envs/isalhg-owemit/bin/python -m pytest tests/unit/core/test_ordered_walk.py tests/unit/metric_space/test_isal_ordered.py -q`

```
74 passed in 19.20s        (tests/unit/core/test_ordered_walk.py)
40 passed in 1.49s         (metric_space + property files together)
```

**One deviation from the prescribed verification command.** The prompt's gate is
`pytest tests/unit tests/property -q -m "not slow" --hypothesis-seed=0 --hypothesis-deadline=none`.
`--hypothesis-deadline` is **not a recognised flag** for the hypothesis pytest plugin in
this environment and pytest exits with `error: unrecognized arguments`. I ran the command
without it; every hypothesis test in my file already sets `deadline=None` through
`@settings`, so the intent is preserved. Flagging it because the orchestrator will
otherwise hit the same error re-running the gate.

**Lint and types.**

```
ruff check   (8 owned files)  -> All checks passed!
ruff format --check           -> already formatted
mypy src/isalhg/              -> Found 20 errors in 6 files (checked 147 source files)
                                 0 of them in ordered_walk.py, isal_ordered.py (either),
                                 or metric_space/registry.py — all 20 are pre-existing,
                                 in structural_tuples.py, hypergraph_wl.py,
                                 hypergraph_to_string.py, canonical.py, isalhg_backend.py
                                 (the `resolve(...)` dispatch table and a lambda), and are
                                 present at the base commit.
```

## 6. Verification beyond unit tests

| Circumstance | What was run | Evidence (paths, numbers, timings) | Outcome |
|---|---|---|---|
| Real data — coverage and cost | `scripts/diagnostics/ordered_walk_corpus_probe.py` (seed 20260906) | **wd50k66, 3,988 members: 0 disconnected, 0 degenerate.** ms per member: ow-struct median **0.082**, p90 0.208, max 0.7; ow-rank 0.082 / 0.209 / 0.7; ow-rank0 0.079 / 0.200 / 0.6. Word in instructions: struct median **6**, p90 34, max 144; rank 6 / 35 / 161; rank0 6 / 45 / 196. `nauty_certificate_rows` symbols: median **12**, p90 28, max 53. **ndc_classes, 1,381 members: 0 disconnected, 0 degenerate.** ms: struct 0.078 / 0.113 / 0.9; rank 0.074 / 0.105 / 0.6; rank0 0.075 / 0.109 / 0.9. Instructions: struct median **8**, p90 32, max 183; rank 14 / 43 / 171; rank0 9 / 34 / 183. Cert rows: median **12**, p90 18, max 54 | Pass. H-M3 (median < 10 ms, 0 censoring at 60 s, every corpus) is met by two orders of magnitude. The Isal word is *shorter* than the certificate row sequence at the median on both corpora (6 vs 12, 8 vs 12) |
| Real data — round trip | same script, 300 random members per corpus, per policy, iso by pynauty | wd50k66 **300/300** and ndc_classes **300/300** for each of struct / rank / rank0 | Pass |
| Real data — invariance | same script, 300 members × 20 relabel-and-reorder copies, per policy | wd50k66 **300/300** and ndc_classes **300/300** for each policy | Pass. H-M0's invariance leg holds on real data |
| Single-edit probe (200 wd50k66 members) | same script: insert one fact `{hub, new constant}` under a predicate the member already uses; hub = the `ow-struct` root | Instruction-level Levenshtein — **ow-struct median 1.0, p90 4, max 8, frac ≤ 2 = 0.815**; ow-rank median 2.0, p90 5, max 22, frac ≤ 2 = 0.545; ow-rank0 median 2.0, p90 6, max 65, frac ≤ 2 = 0.625. Same edit on `nauty_certificate_rows` (equality-keyed Levenshtein over row tuples): **median 12.0, p90 24, max 35, frac ≤ 2 = 0.000** | Pass, and it is the R1 result: `ow-struct` responds to a new fact with a **median of 1 instruction** where the certificate rewrites **12 rows**, and it stays within 2 instructions on 81.5 % of edits where the certificate never does. H-M1d's ordering holds in the median (1 ≤ 2 ≤ 2) but **not** on the within-≤ 2 fraction, where `rank0` (0.625) beats `rank` (0.545) — reported, not smoothed |
| Star locality, 400 random binary stars (20–40 leaves, 5 predicates, 20 % with a second fact), policy `ow-struct` | `/tmp/.../scratchpad/check_rule.py` | **No-crossing rule (adopted):** (a) leaf insertion n=400, median 2, **max 2**, frac ≤ 2 = **1.000**; (b) later leaf targeted n=395, median 1, **max 3**, frac ≤ 3 = **1.000**, frac ≤ 2 = 0.985; (b) `x`'s creation position kept n=90, median 1, **max 1**; stars containing a forward (`P`) run: **0/400**; runs longer than `n − 1`: **0**. **Shorter-direction rule (retired):** (a) median 2, max **22**, frac ≤ 2 = 0.978; (b) median 1, max **25**, frac ≤ 2 = 0.901; forward runs in 44/400 stars | Pass, and it reproduces `main`'s predicted consequences exactly |
| Word-length price of the rule change | `/tmp/.../scratchpad/price.py` (monkeypatches `_Emitter._move` back to the retired rule) | **400 stars:** move tokens per word — no-crossing median **22.0**, max **37**; shorter-direction median **22.0**, max **37**. Whole word — 57.0 / 87 vs 56.0 / 87 instructions. **300 wd50k66 members** (n median 8, max 24; m median 5, max 19): move tokens — no-crossing median **0.0**, max **123**; shorter-direction median **0.0**, max **77**. Whole word — median 6.0 / max **137** vs median 6.0 / max **96** | The price is a **tail, not a median**. Identical on stars; on real members the median word is unchanged at 6 instructions and only the worst case grows (96 → 137, +43 %). Cheap for an unconditional locality bound |
| Randomised differential (pre- and post-rule-change) | `/tmp/.../scratchpad/check_rule.py`, 600 random connected labelled instances × 3 policies | round-trip failures **0**, invariance failures **0**, runs longer than `n − 1` **0** | Pass |
| Edge cases | unit tests | `n = 1`: empty word, `creation_order == (0,)`, decodes to the single seed. `n = 0`: `DegenerateHypergraphError`. Disconnected: `DisconnectedHypergraphError`. Bad ranks (wrong length, not a permutation): `OrderedWalkError`. `k` below `required_k`: `InvalidInstructionError` from `validate`. Arity = `k` at a `C` (pointers `p_1..p_k`): exercised by `ndc_classes`, whose max arity is 10. Multi-label: every random corpus uses 3 types × 3 predicates, and the seed prefix appears exactly when the vertex vocabulary is non-trivial | Pass |
| Environment | `~/.conda/envs/isalhg-owemit/bin/python` | Python **3.11.15**, pynauty **2.8.8.1**, rapidfuzz **3.14.5**; `isalhg.__file__` resolves to `.../agent-aa0166cf355893a2a/src/isalhg/__init__.py` (inside the worktree), `isalhg.core._core` imports | Correct env, correct tree |

## 7. Decisions, assumptions, open questions

**D1 — the emitter simulates the decoder rather than reasoning about it.** `_Emitter` holds
a real `CircularDoublyLinkedList` and applies each `V` exactly as `StringToHypergraph._step`
does. Round trip is then a consequence of the construction. Evidence that this was the right
call: 0 round-trip failures on the very first randomised run, before any debugging.

**D2 — a plain slot list instead of `KPointerSet`.** `KPointerSet` raises above `K_MAX = 10`,
and `ndc_classes` already contains arity-10 facts, so `required_k = 10` is live and 11 would
be reachable on other corpora. The emitter uses `max(2, max arity)` slots in a list, which
also keeps the k-independence claim clean.

**D3 — `OrderedWalkError` for a malformed rank vector.** The contract names only the two
hypergraph-domain errors. A bad `ranks` argument is neither, and the coding rules forbid a
bare `ValueError` in library code, so the module declares its own `IsalHGError` descendant —
the same pattern `hypergraph_to_string.H2SStuckError` uses. It also fires as a safety net if
the V-phase ever runs out of frontier facts, which connectivity should make unreachable.

**D4 — `DEFAULT_POLICY` module singleton.** ruff `B008` forbids constructing a default
argument in place. The contract's `policy: OrderedWalkPolicy = OrderedWalkPolicy()` is
preserved in effect by a frozen module-level instance; every signature still defaults to
`ow-struct`.

**D5 — `OrderedWalkPolicy(root_rule="rank0", rank_first=True).name == "rank0_rank"`.** The
contract names three arms and defines three of the four combinations. The fourth is
reachable, so it is given a name that can never be mistaken for a registered arm rather
than being silently aliased onto `"rank0"`. Documented in the property's docstring.

**D6 — `pairwise` uses each hypergraph's own `augment` decision.** `IsalHGLevenshtein`
computes `augment = max(H1.n_vertex_labels, H2.n_vertex_labels) > 1`, but the frozen
contract for my arm says `fingerprint(H) = ordered_symbols(H, policy=...)` and
`pairwise` runs on the symbol tuples. I followed the contract: `pairwise` is
`fingerprint(H1)` vs `fingerprint(H2)`, each with its own `H.n_vertex_labels > 1` test. On
a shared vocabulary — which every corpus has, verified on both frozen collections — the two
readings coincide. The contract's version is also the one that makes `fingerprint` a
genuine per-item cache.

**A1 (assumption) — the single-edit probe's new constant takes the hub's type.** The
prompt fixes the predicate ("a random existing predicate") and the fact (`{hub, new
constant}`) but not the new constant's type. Taking the hub's type adds structure without
widening the vocabulary, which keeps the edit comparable across members. Recorded here
because a different choice would move the `frac ≤ 2` numbers slightly.

**A2 (assumption) — "hub" in the probe is the `ow-struct` root.** That is the root rule's
own definition (argmax `(deg_E, type)`, ties by minimum rank), so the edit attaches to the
constant the word is written from, which is what makes it the locality probe rather than an
arbitrary insertion.

**Open question — H-M1d is only half confirmed.** The pre-registered ordering is
`ow_struct ≤ ow_rank ≤ ow_rank0` in median response. Measured on 200 wd50k66 members the
medians are 1 ≤ 2 ≤ 2 (consistent), but on the within-≤ 2 fraction — which is the
pre-registered *selection* criterion — the order is `struct` 0.815 > `rank0` 0.625 >
`rank` 0.545, i.e. `rank0` beats `rank`. `struct` wins the selection rule either way, so
nothing about the choice of arm is in doubt; the hypothesis's internal ordering of the two
losers is the part to restate. One probe, one edit kind, no seeds — the campaign's M1 grid
decides it, not this.

## 8. Coordination

- Sent one message to `main` (`SendMessage`, "Prop 6.3 star-locality bound partially
  falsified"): the two deviation channels with the 400-star numbers, the reading, and an
  explicit statement that I was **not** acting on the contract and was flagging it only.
- `main` replied with the no-crossing move-rule replacement (quoted verbatim in §1), which
  I implemented, re-measured and re-pinned. All four of its follow-up requests are
  discharged: (1) the rule is switched in both phases; (2) the 400-star pins are re-run and
  the tests now assert (a) max ≤ 2 unconditionally and (b) ≤ 3 when a later leaf is
  targeted, with the medians and fractions pinned; (3) the word-length price is in §6; (4)
  the corpus probe is unchanged from the spec. The requested `n − 1` run-length assertion is
  `TestValidity::test_no_move_run_is_longer_than_n_minus_one`.
- No contact with `orbit-prune`. I read three files they own
  (`hypergraph_to_string.py`, `canonical.py`, and — read-only — nothing else) and wrote to
  none of them. The one coupling is noted in §10.

## 9. Deliberately not done

- **Registering the arm in `experiments/tkde/matrices.py` or any RQ runner.** Out of scope
  by the prompt; next wave.
- **Roles (R4).** Out of scope; §8.3 of the design record files it as a ledger task.
- **A C++ port.** Out of scope. The Python emitter runs at 0.08 ms median per member, so
  there is no measured need.
- **Orbit pruning of `w*_c`.** `orbit-prune`'s task.
- **Any edit to the `w*_c` pin table or to `canonical_string`.** Explicitly forbidden. My
  golden table is separate and carries a test
  (`test_the_pins_are_not_the_wstar_c_pins`) whose only job is to stop the two from ever
  being reconciled.
- **Updating the proof `.tex` or the design record** with the falsification and the new
  rule. `main` says both were updated on its side; they are outside my ownership either way.
- **Turning the probe's timings into assertions.** They would be machine-dependent.

## 10. Risks and follow-ups

| Item | Severity | Detail | Suggested owner |
|---|---|---|---|
| `ordered_walk.py` imports `hypergraph_to_string._movement_tokens`, a private name in a file `orbit-prune` owns | low | The prompt directs this reuse and it is the right call — one renderer for the family. But a rename or signature change there breaks the emitter at import time, and nothing in that file warns of the dependency. `orbit-prune` is not changing the renderer in this wave, so the wave is safe; the merge should keep an eye on it | orchestrator at merge; a later task could promote the helper to a public name |
| H-M1d's within-≤ 2 ordering does not hold between the two losing arms | low | `rank0` (0.625) beats `rank` (0.545) on 200 wd50k66 members, one edit kind, no seeds. The selection rule still picks `struct` unambiguously | next wave's M1 grid (5 edit kinds, 27 seeds, Holm) |
| The no-crossing rule's tail cost | low | Worst-case word on 300 wd50k66 members grows 96 → 137 instructions (+43 %); median unchanged at 6. Harmless at these sizes, but it is a real cost that scales with `n`, so a corpus with much larger members would want it re-measured before the RQ7 envelope sweep | RQ7 owner |
| `--hypothesis-deadline=none` is not a valid flag here | low | The prompt's verification gate fails to start with it. Re-run without it (my `@settings` already sets `deadline=None`) | orchestrator, when re-running the gate |
| `_Emitter` rebuilds its `slot -> index` dict after every `V` | low | `O(n²)` per word. Invisible at corpus scale (0.08 ms median) and it buys a much simpler `pos`; would want an incremental index only if members reached the thousands of constants | nobody, until measured |
| The three arms share one `IsalOrderedLevenshtein` class | none | Deliberate — the policy is a constructor argument and `name` derives from it, so a fourth arm is one registry row. Noted so the next wave does not look for three classes | — |

## 11. Self-assessment against the definition of done

| # | Criterion | Met | Evidence |
|---|---|---|---|
| 1 | `ordered_walk` implements Definition 3.2 for three policies, stdlib-only, NumPy docstrings, the two error classes | yes | `src/isalhg/core/algorithms/ordered_walk.py`; imports are stdlib + `isalhg.core`/`isalhg.errors`/`isalhg.types` only; `TestPolicyAndErrors` covers both error classes; the move rule is `main`'s no-crossing replacement |
| 2 | Round trip on every fixture and ≥ 2,000 random instances, all three policies, decided by pynauty | yes | `TestRoundTrip` — 12 designs (incl. Fano, STS(9), both cyclic C13 orbits, GQ(2,2), the n=4 pair, 5 catalog Steiner systems) and `_N_RANDOM = 2000`; 0 failures |
| 3 | Invariance: 200 relabellings per fixture, 20 per random instance, vertex permutation **and** fact-order shuffle, all policies | yes | `TestInvariance`; `_shuffled_copy` does both. 11 designs × 200 × 3 and 2,000 × 20 × 3; 0 violations. (The 15-point catalog system is excluded from the 200-relabelling loop — it is the slowest member and adds nothing the 13-point ones do not; it is still covered by round trip, validity and the golden pins) |
| 4 | Validity: `validate` passes, no `W`, no `C` with coincident pointers | yes | `TestValidity::test_designs_and_random`, which replays the program against a fresh CDLL and checks slot distinctness at every `V` and `C` |
| 5 | Completeness on ≥ 1,000 pairs (≥ 300 isomorphic), decided by pynauty, all policies | yes | `TestCompleteness::test_thousand_pairs` — 1,000 pairs, 340 isomorphic, `(false_merge, false_split) == (0, 0)` for each policy |
| 6 | k-independence at `required_k` and `k = 10` on 200 random instances | yes | `TestPointerCountIndependence` |
| 7 | Own `(len, sha256)` golden table per fixture per policy, with the "a change means the emitter changed definition" comment | yes | `_GOLDEN_WORDS`, 36 entries, and the comment block above it; `test_the_pins_are_not_the_wstar_c_pins` guards the separation |
| 8 | Star locality asserted, both (a) and (b) | yes | `TestStarLocality`, 100 stars (hub + 20–40 leaves, 5 predicates, 20 % with a second fact). (a) asserted at ≤ 2 **unconditionally**; (b) at ≤ 3 when a later leaf is targeted and ≤ 2 when `x` keeps its position — the restatement `main` sent after I falsified the original ≤ 2 under the retired move rule. The median/fraction measurement is pinned beside them. §6 carries the 400-star numbers for both rules |
| 9 | Three registered arms; `get_distance("isal_ow_struct").fingerprint(H)` works; `P[1]` vs `N[1]` pinned; relabel-sensitivity replicated | yes | `tests/unit/metric_space/test_isal_ordered.py`; `metric_space/registry.py` names the module (the file the prompt asked me to identify); `TestSymbols::test_advance_and_retreat_are_different_symbols`; `TestLabelDeclaration` replicates the pattern without touching `test_representations_kb.py` |
| 10 | Hypothesis property test for round trip + invariance, `pytestmark = pytest.mark.property` | yes | `tests/property/test_ordered_walk_roundtrip.py`, 3 properties × 3 policies |
| 11 | Corpus verification script, numbers in the log | yes | `scripts/diagnostics/ordered_walk_corpus_probe.py`, re-runnable and seeded; every requested figure is in §6 — disconnected counts, per-policy ms and word length vs certificate rows, 300/300 round trip, 300/300 invariance, and the 200-member single-edit probe against `nauty_certificate_rows` |
| 12 | Lint and types clean on owned files; all work committed; tree clean; log committed | yes | ruff and `ruff format --check` pass on all 8 files; mypy reports 0 errors in my files (20 pre-existing elsewhere); `git status --short` empty; `git diff --name-only 99b8574..HEAD` is exactly the ownership set |

**Overall.** Complete. All twelve definition-of-done items pass, on the numbers rather than
on inspection. The task's substance turned out to be item 8: prototyping Proposition 6.3
before pinning it showed the bound failing under the then-frozen shorter-direction move
rule, in two mechanisms I could name and measure (a forward-rendered run has length
`N − gap` and so grows with every insertion; and the signature shift moves `x` inside its
run of identical `V` tokens). I reported that to `main` rather than adjusting either the
rule or the assertion, and `main`'s no-crossing replacement made the bound unconditional —
(a) max exactly 2 on 400/400 stars, (b) max 3 — at a cost that is a tail and not a median
(worst-case word on real members 96 → 137 instructions; median unchanged at 6). The headline
the wave was after holds on real data: on `wd50k66`, inserting one fact moves the
`ow-struct` word by a **median of 1 instruction** and stays within 2 on **81.5 %** of edits,
where the nauty certificate rewrites a **median of 12 rows** and is never within 2.
