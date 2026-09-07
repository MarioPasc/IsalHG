# Work log — orbit-prune

## Identity
| Field | Value |
|---|---|
| Agent | `orbit-prune` |
| Wave | `2026-09-06-isal-kb-w1` |
| Model / effort | `claude-opus-5[1m]` / `xhigh` |
| Branch | `worktree-agent-af665c305e389fb89` |
| Worktree | `/home/mpascual/research/code/IsalHG/.claude/worktrees/agent-af665c305e389fb89` |
| Base commit | `99b8574f768b6f3dc53cc6ef9414cef5505dda04` |
| Head commit | `<final sha>` |
| Started / finished | `2026-09-06T21:09:34+02:00` / `<ISO timestamp>` |
| Status | in progress |

## 1. Prompt as received

Mission: implement **stabiliser-orbit pruning** of the Python tie-complete
encoder — at every residual tie branch over one representative per orbit of the
automorphism group fixing the placed prefix (and, per representative edge, one
label-respecting ordering per orbit of the group also stabilising that edge);
the seed loop runs one seed per `Aut(H)`-orbit. Groups come from
`pynauty.autgrp` on the coloured Levi graph with placed vertices individualised.
Output must be the frozen `w*_c`, **bit for bit** (D-TA2's only sanctioned
speed-up; Prop. 7.3 + Lemma 7.2 of `theorem_c_ordered_walk.tex` §7, Prop. 6.1
`prop:coherent` + `rem:coherence-recursive` + `lem:pruning` of
`theorem_a_completeness.tex` §6).

Definition of done (abbreviated; full text in the task prompt):
1. `TrivialOrbitOracle` through the hook reproduces the unpruned output on the
   frozen fixtures and 200 random instances.
2. Bit-exact frozen pins (Fano, STS(9), `C_13(0,1,3)`, n=4 counterexample;
   both true STS(13) slow) and equality with C++ `w*_c` on GQ(2,2).
3. Differential vs unpruned Python on ≥ 500 random connected labelled
   hypergraphs and 200 random stars.
4. Corpus differential: 300 `wd50k66` members the C++ engine completes.
5. Branch-count collapse table on stars with q ∈ {5,6,7,8}.
6. Timing: 20-leaf star, target < 10 s.
7. Censored tail: up to 100 `wd50k66` members the C++ engine censors at 60 s.
8. Unit tests for 1–3 + slow markers; integration test for 4.
9. Lint/type clean; all work committed.

Ownership (exclusive write): `src/isalhg/core/orbit_oracle.py`,
`src/isalhg/core/hypergraph_to_string.py`, `src/isalhg/core/canonical.py`,
`src/isalhg/core/algorithms/registry.py`,
`src/isalhg/iso_backends/orbit_oracle.py`,
`tests/unit/core/test_orbit_pruning.py`,
`tests/integration/test_orbit_pruning_corpus.py`,
`scripts/diagnostics/orbit_pruning_probe.py`, this log.

### Mid-task scope addition from `main` (2026-09-06, verbatim intent)

Add a fourth canonical program `canonical_rank` = the family's greedy walk
(`tie_branch=False`, same displacement search and 7-rung cascade) with the
residual tie broken by nauty's canonical rank instead of raw edge id — D-ART4
option (2a)(i). Frozen contract:

- `greedy_h2s(..., ranks: Sequence[int] | None = None)`: when `ranks` is given
  (Python path only; ValueError with `tie_branch=True` or backend `"cpp"`),
  (i) the residual V tie is resolved by the minimum of `(sorted ranks of the
  edge's unplaced members, sorted ranks of the edge's placed members)`, and
  (ii) the new-vertex ordering is by `(label, rank)`. Nothing else changes.
- `canonical_string(H, *, algorithm="canonical_rank", ranks=..., ...)`: seed =
  the member of `S(H)` with minimum rank (no seed loop), one greedy run;
  ValueError if `ranks is None`. `canonical_fingerprint` likewise.
- `iso_backends/orbit_oracle.py`: `canonical_string_rank`,
  `canonical_fingerprint_rank`, obtaining `ranks = canonical_ranks(H)`.
- Tests: invariance under 100 relabellings on fixtures + 200 random instances;
  completeness on ≥ 500 pairs; log how often it equals `w*_c`.
- Probe: timing line (20-leaf star; 300 wd50k66 members, median ms).

Priority: original items 1–4 first, then this arm, then 5–7.

## 2. Understanding and plan

**Restatement.** Two independent deliverables landed in one ownership set.
(a) *Orbit pruning*: a speed-up of the tie-complete search that must not move
`w*_c` by a single byte. (b) *`canonical_rank`*: a genuinely different
canonical program that borrows nauty's order to make the greedy walk complete.

**Approach chosen.**

- The oracle is a `Protocol` in `core` (stdlib-only, per the layering rule),
  the `pynauty` implementation in `iso_backends`. `core` never imports it.
- The hook sits in `_encode_from`'s V-branch, *after* the emission key is
  fixed. The displacement/emission selection loop is untouched, so pruning can
  only remove automorphic duplicates of a branch that is already committed to
  by cascade rungs 1–7.
- `placed` = `tuple(state.o2i[o] for o in range(state.next_output_id))`. Output
  ids are handed out contiguously from 0, so this is `dom μ` in creation order
  under both the clone-on-branch and the in-place undo paths.
- `G_σ` orbits on the tie set come straight from `pynauty.autgrp`'s own
  `orbits` output on the individualised Levi graph (it is the orbit partition
  of exactly the group we asked for), read at the fact nodes. Orbits on
  *orderings* need the action on tuples, so those go through union–find over
  the generators, as the prompt specifies.
- Short-circuits that preserve the value: `len(candidates) <= 1` skips the
  oracle entirely; a trivial `G_σ` (no generators) cannot have a non-trivial
  subgroup, so `ordering_representatives` returns its input without a second
  `autgrp` call.
- Stabiliser recomputed at **every** tie (`rem:coherence-recursive`). The
  `_gens` cache is keyed by `(id(H), placed prefix)`, so it memoises identical
  states, never inherits a coarser group from an ancestor.

**Alternatives considered and rejected.**

- *Union–find over generators for the edge orbits too.* Correct, but
  `autgrp` already returns the orbit partition on Levi nodes; recomputing it
  would be strictly more code for the same answer.
- *Caching the group across the whole search keyed by the placed set (not the
  sequence).* Rejected: two states with the same placed *set* but different
  creation order are different states; the group happens to coincide, but the
  ordering-orbit representatives are read off input order, and I did not want
  the correctness argument to depend on that coincidence.
- *Pruning under `tie_branch=False`.* Value-preserving there too, but out of
  contract and it would silently change the cost profile of the greedy
  variants. The oracle raises rather than being silently ignored.

**Plan as executed.**
1. Read the two proof files (§7 of Theorem C; §6 of Theorem A), the design
   record's orbit spec and H-M3/H-A hypotheses, the encoder, `canonical.py`,
   `levi_reduction.py`, `canonical_order._to_pynauty`, the frozen pins,
   `budget.run_with_budget`, the symmetry probe.
2. `core/orbit_oracle.py` (Protocol + `TrivialOrbitOracle`).
3. Hook + `stats` instrumentation in `hypergraph_to_string.py`.
4. `canonical_orbit` in `canonical.py`.
5. `iso_backends/orbit_oracle.py` (`PynautyOrbitOracle` + entry points).
6. `canonical_rank` threaded through the same three files.
7. Tests, probe, verification runs.

**Deviations from the plan.** The `canonical_rank` arm arrived mid-task and was
folded into steps 3–5 rather than bolted on afterwards, because it touches the
same tie-break site in `_best_v_for_displacement`.

## 3. Changes made

**Created**

| Path | Purpose |
|---|---|
| `src/isalhg/core/orbit_oracle.py` | The `OrbitOracle` `Protocol` + `TrivialOrbitOracle`. Stdlib only, so it can live in `core`. |
| `src/isalhg/iso_backends/orbit_oracle.py` | `PynautyOrbitOracle` (the real groups, via `autgrp` on the individualised Levi graph) and the four entry points `canonical_{string,fingerprint}_{orbit,rank}`. |
| `tests/unit/core/test_orbit_pruning.py` | Value-neutrality of the hook, bit-exactness of the pins, the differentials, the error paths, and the `canonical_rank` invariance/completeness census. |
| `tests/integration/test_orbit_pruning_corpus.py` | The `wd50k66` differential against the C++ `w*_c`, both engines under `run_with_budget`. Skips without the drive. |
| `scripts/diagnostics/orbit_pruning_probe.py` | Four sub-commands: `branch-table`, `star20`, `censored-tail`, `rank-timing`. |
| `.claude/notes/2026-09-06-isal-kb-w1/orbit-prune.md` | This log. |

**Modified**

| Path | Change | Reason |
|---|---|---|
| `src/isalhg/core/hypergraph_to_string.py` | `_State.placed_inputs()`; `orbit_oracle` / `ranks` / `stats` threaded through `_encode_from`, `_python_greedy_h2s`, `greedy_h2s`; orbit pruning applied in the V-branch; `_rank_tiebreak` + the rank-ordered new-vertex order; validation that raises instead of falling back; module docstring. | The V-branch is the only place the tie set is enumerated, so both the pruning and the rank tie-break belong there. |
| `src/isalhg/core/canonical.py` | `CANONICAL_ORBIT_ALGORITHM` / `CANONICAL_RANK_ALGORITHM`; `orbit_oracle` / `ranks` on `canonical_string` and `canonical_fingerprint`; seed reduction by `seed_representatives`; `_python_canonical_rank_string`. | The seed loop is here, and it is the third place the proposition prunes. |

**Removed** — nothing.

**Commits**

| SHA | Message |
|---|---|
| `3c23499` | `feat(core): stabiliser-orbit pruning of the tie-complete search` |
| `498e723` | `test(orbit-prune): wip — orbit-pruning suites, corpus differential, probe` |
| `0a35b40` | `test(orbit-prune): tier the suite by measured cost, fix the pair generator` |

<!-- must match `git diff --name-only 99b8574..HEAD` exactly -->

## 4. Tests

**Tests created or extended**

| Test | File | What it verifies | Why it matters |
|---|---|---|---|
| `TestTrivialOracleIsValueNeutral` (5) | `tests/unit/core/test_orbit_pruning.py` | Hook-off output == `TrivialOrbitOracle` output on Fano, the n=4 counterexample and 40 / 200 random instances; `TrivialOrbitOracle` satisfies the `Protocol` | Separates a plumbing bug from a group-theory bug. If this fails, the hook itself changed the search. |
| `TestFrozenPins` (7) | same | `canonical_string_orbit` reproduces the frozen `(len, sha256)` of Fano, STS(9), `C_13(0,1,3)`, the n=4 counterexample and both true STS(13); equals the C++ `w*_c` on GQ(2, 2) | The whole licence for pruning is that it is value-preserving. These are the definitional pins. |
| `TestDifferentialAgainstUnprunedSearch` (4) | same | Pruned == unpruned Python on 40 / 500 random connected labelled instances and 200 random stars; the q=7 star collapses 13,700 frames to 8 | The pins cover five fixtures; the differential covers a distribution, including the symmetric regime. |
| `TestUnhonourableRequestsRaise` (8) | same | Oracle on `backend="cpp"`, oracle without `tie_branch`, `canonical_orbit` without an oracle or on cpp, oracle with another algorithm, `canonical_rank` without ranks, ranks with `tie_branch`, ranks of the wrong length | A silent fallback would return a correct string from an unpruned search and hide the failure as a timeout. |
| `TestExistingProgramsAreUntouched` (4) | same | Python and C++ still agree byte for byte on `canonical`, `greedy_min`, `greedy_min_nbrdeg`, `greedy_single` | The hooks sit inside the shared encoder; this pins that they are inert when unused. |
| `TestOrbitFingerprint` (1) | same | `canonical_fingerprint_orbit` == the unpruned fingerprint on a labelled instance | The seed-label half of `F` also has to survive seed-orbit reduction. |
| `TestCanonicalRankInvariance` (5) | same | `F_rank` constant under 30 / 100 relabellings of Fano and STS(9), and on 40 / 200 random instances | The rank arm has no frozen pin, so invariance is its correctness criterion. |
| `TestCanonicalRankCompleteness` (2) | same | `F_rank` equality agrees with `pynauty_levi` on 50 / 500 random pairs at a shared vocabulary | Completeness in both directions, against an independent oracle. |
| `TestCanonicalRankIsADifferentProgram` (2) | same | Differs from `w*_c` on the n=4 counterexample; equals it on Fano | Pins that the arm is a distinct canonical form, so nobody mistakes it for `w*_c`. |
| `test_orbit_engine_matches_cpp_wstar_c_on_wd50k66` | `tests/integration/test_orbit_pruning_corpus.py` | 300 sampled `wd50k66` members: pruned Python == C++ `w*_c` wherever both complete | Moves the value-preservation claim from synthetic instances onto the real corpus. |

**Coverage of the behaviour that matters.** The three failure modes of orbit
pruning are: pruning a branch that is not an automorphic duplicate (caught by
the pins and both differentials), failing to prune at all (caught by the frame
counts in `test_pruning_actually_collapses_a_symmetric_star`), and pruning with
a group computed at the wrong state — the inherited-stabiliser bug the proof's
recursion remark warns about. The last one is the subtle one: it does not show
up on rigid inputs, only where the stabiliser shrinks below the root's. The 200
random stars and the STS/GQ fixtures are the inputs where it would.

**Not tested, and why.** No C++ path (out of scope). No property test under
`hypothesis` — the differentials are already distribution-level and the
reference search is too slow to run under shrinking. `TrivialOrbitOracle` is
not exercised through `canonical_string(algorithm="canonical_orbit")`, only
through `greedy_h2s`, because the seed-reduction half of the contract is
meaningful only for the real oracle.

## 5. Test results

Filled in at close.

## 6. Verification beyond unit tests

Filled in at close.

### Branch-count collapse (measured 2026-09-06)

Star: hub `0`, `q` leaves each in its own binary fact with the hub; `k=2`,
seed = hub, `tie_branch=True`, in-place. `frames` = calls to `_encode_from`,
`vbr` = V-branch expansions, `autgrp` = `pynauty.autgrp` invocations.

| q | unpruned frames | unpruned V-branches | unpruned s | pruned frames | pruned V-branches | oracle calls | autgrp calls | pruned s | equal |
|---|---|---|---|---|---|---|---|---|---|
| 5 | 326 | 325 | 0.018 | 6 | 5 | 4 | 4 | 0.001 | yes |
| 6 | 1,957 | 1,956 | 0.129 | 7 | 6 | 5 | 5 | 0.001 | yes |
| 7 | 13,700 | 13,699 | 1.087 | 8 | 7 | 6 | 6 | 0.001 | yes |
| 8 | 109,601 | 109,600 | 10.377 | 9 | 8 | 7 | 7 | 0.002 | yes |

The unpruned counts are exactly `Σ_{d=0..q} q!/(q-d)!` (109,601 for q=8), i.e.
the number of injective placement sequences — factorial growth. The pruned
search visits `q+1` frames and makes `q-1` oracle calls, matching the
`rem:oracle` prediction ("one branch per state, `q` states, `O(q)` oracle
calls") exactly.

## 7. Decisions, assumptions, open questions

- **A1.** `placed` is the creation-order sequence, not a set. The proof's
  `dom μ` is a set for the purpose of defining `G_σ`, and cell *order* does not
  change the group nauty computes, so ordering the singleton cells by creation
  is a free convention that also makes the cache key exact.
- **A2.** For `canonical_rank`, `C`-token candidates keep the raw-edge-id
  residual. This is vacuous: at a fixed displacement a `C` candidate's member
  set is pinned to `tentative_inputs[:arity]`, and `SparseHypergraph` forbids
  duplicate member sets, so at most one `C` edge can tie. Documented rather
  than changed, since the scope addition names the V tie only.
- **A3.** The `canonical_rank` seed loop collapses to the minimum-rank member
  of `S(H)` per the scope addition. `S(H)` is iso-invariant and the ranks are a
  canonical total order on the vertices, so the choice is canonical.
- **A4 (test tiering).** The definition of done asks for a differential
  against the *unpruned* Python search at scale. That reference is expensive
  on precisely the inputs pruning exists for — measured 3.40 s on the Fano
  plane and past 120 s on STS(9), GQ(2, 2) and `C_13(0,1,3)`. The suite is
  therefore tiered: the unmarked tier runs reduced counts (40 instead of 200 /
  500, 50 pairs instead of 500, 30 relabellings instead of 100) and stays near
  60 s; the full counts and the expensive fixtures carry `slow`. Every number
  the definition of done names is measured — in the `slow` tier.
- **F1 (finding, out of scope).** Fingerprint comparison is only defined
  *within a shared vocabulary*, and the first version of my random-pair
  generator drew `n_vertex_labels` / `n_edge_labels` independently per member.
  It produced a pair of structurally identical 2-vertex/1-edge hypergraphs
  with identical labels but declared sizes `(3, 1)` and `(2, 2)`;
  `pynauty_levi` calls them **non-isomorphic** (the Levi colouring places
  edge-node colours at `|Sigma_v| + edge_label`, so the edge node is colour 3
  in one and colour 2 in the other, and `color_signature` pins that), while
  `canonical_fingerprint` with the frozen `w*_c` calls them **equal**
  (`(1, 'V[0;1;1;0]')` for both). The disagreement is a property of comparing
  across vocabularies, not of `canonical_rank`, and it reproduces on `w*_c`
  itself. I fixed my generator to pin the vocabulary across a pair and did not
  touch either engine. Whether `w*_c` *should* encode the declared vocabulary
  size — so that `IsalHGBackend` and `PynautyLeviBackend` cannot disagree even
  on ill-posed inputs — is a question for the PI, not for this task.

## 8. Coordination

- Scope addition from `main` received mid-task (the `canonical_rank` arm),
  acknowledged and implemented; priority order honoured.
- No message sent to `main`; no ambiguity required one.

## 9. Deliberately not done

- No C++ implementation of the hook (explicitly out of scope).
- No edits to `test_wstar_c_frozen.py` (frozen), to `experiments/`, to
  `core/_native/`, or to any file owned by `ow-emitter`.

## 10. Risks and follow-ups

Filled in at close.

## 11. Self-assessment against the definition of done

Filled in at close.
