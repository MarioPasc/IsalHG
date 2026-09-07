# Wave 2026-09-06-isal-kb-w1 — the Isal instruction word for knowledge bases

*Orchestrator: the `[IsalHG-Refinement]` session (Fable 5.1, xhigh). Written
continuously; appended, never rewritten. If this session ends, a takeover
agent starts here, then reads `docs/article/D_ART3/experiments/ISAL_VARIANT_DESIGN.md`.*

## Date and base

- 2026-09-06. Branch `feature/isal-kb-word` cut from
  `integration/2026-09-05-tkde-w1` (df61eda).
- Commits before the wave: `85c565b` (the auditor's uncommitted D-ART4 record:
  brief, PI Q&A, audit, worked example, three probes) and `99b8574` (the
  pre-registered design). **BASE_SHA = 99b8574f768b6f3dc53cc6ef9414cef5505dda04.**
- Proof written and compiled (pdflatex, clean):
  `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/proofs/completeness/theorem_c_ordered_walk.tex` (+ .pdf).

## The user's prompt (verbatim)

> CONTEXT: Read docs/article/D_ART3/experiments/ISAL_REFINEMENT_BRIEF.md docs/article/D_ART3/START_HERE.md You are allowed to spawn sonnet agents to brief you on the results if needed or aggregate them for you (/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE/INDEX.md) TASK: I have been wrong on what the original agent proposed, the fact-rank proposal with nauty is completly off the table for this article, since it would not be a Isal member of the family, with our distinguishable CDLL+Alphabet structure. However, the Isal approach, as intended, would not exactly work 100% on this problem, as stated in docs/article/D_ART3/experiments/ISAL_REFINEMENT_BRIEF.md. You are tasked with exploring the options we have to steer IsalHG to fit better the knowledge databases scope of the paper, basically our main problems are the locallity and symmetry, but we also need to keep our main characteristics and correct representation. ACCEPTANCE CRITERIA: You have not spawned more than 2 opus subagents at thee same time and you have only spawned them for implementation and monitoring, checking their work when they have finished ( /parallel-agents ) ; You have modified, if needed, or created, the completeness or more proofs in /media/mpascual/Sandisk2TB/research/ISAL/isalhg/proofs ; You have correctly found and implemented (implementation for opus xhigh) a IsalHG variant that fits better the knowledge databases and the RQs we already have, although, and this rule is very important: If we can't max out any of the RQs prosed, we can settle for a representation that does for most and move the RQ to supplementary as a limitation, or find something else that has a real application at which our isalhg is the best at. If needed, update the project docs in docs/article/D_ART3/prose.md (I encourage you to do at the end). Think step by step, reason. Ask me anything you need from me. Stay aligned. You may message VERY OCCASIONALLY (HIGH-USAGE CONSUMER MODEL) the agent [Experimental-Interpreter] to interpret any results for you or give more context. The main goal at the end will be to have another entry to each RQ with the Isal representation.

## The user's rulings (2026-09-06, batched question, answered)

1. **nauty role — both accepted, with a four-cell ablation:** *no nauty* /
   *order only* / *oracle only* / *both*. Orchestrator's reading, recorded in
   the design doc §3b: the cells are the canonical programs `wstar` (the
   family's tie-complete lex-min, no nauty), `isal_ow_*` (the ordered walk:
   nauty's order drives the walk), `wstar_orbit` (the same `w*_c`, nauty as
   the automorphism oracle that prunes the search), and `wstar_rank` (the
   family's greedy walk with nauty's rank as the residual tie key — D-ART4
   option 2a-i — which uses the order *inside* the Isal search and needs no
   oracle because ties collapse). If the user meant a different fourth cell,
   this is the place to correct it.
2. **RQ4 / RQ5:** to the supplement as characterised limitations if the Isal
   row sits at the certificate's level.
3. **Picasso:** the orchestrator submits, using the `picasso-sbatch` skill.
4. **Roles (R4):** ledger task, later (`docs/article/DEVELOPMENT/T-KB/OPEN/T-KBa.md`).
5. **Quota:** the plan is at 78 % usage, reset in ~2 h 10 min; subagents may
   be cut off. Everything decided is on disk (this file, the design doc, the
   proof); the wave is recoverable from the agents' committed branches.

## Design decisions taken by the orchestrator (not the user)

- Representation candidate = the **ordered walk** `w°` (policy `ow-struct`:
  structural keys, local signature, nauty rank last); ablations `ow-rank`,
  `ow-rank0`. Reason: removes the search (the root of R1 and R2) while
  keeping CDLL + `Σ_HG` + `S2H`; complete by Theorem C; locality provable on
  binary stars (Prop. C.5) and otherwise measured.
- `w*_c` kept as the family's search-based form, made computable by
  **stabiliser-orbit pruning** (value-preserving, D-TA2 untouched).
- Alphabet unchanged. No new instruction.
- The tokens of `w°` are independent of `k` for every `k ≥ max arity`, so
  the arm's fingerprint needs no corpus `k` (validation and decoding do).

## Agents of this wave

| name | model / effort | mission | ownership | status |
|---|---|---|---|---|
| `ow-emitter` | opus5-xhigh (model pinned `opus`; `CLAUDE_CODE_SUBAGENT_MODEL=sonnet` is set in this env, so the model is passed per call) | ordered-walk emitter (core), nauty entry point (iso_backends), distance arm `isal_ow_{struct,rank,rank0}`, tests, corpus probe | `core/algorithms/ordered_walk.py`, `iso_backends/isal_ordered.py`, `metric_space/distances/isal_ordered.py` (+ registry entry), 3 test files, `scripts/diagnostics/ordered_walk_corpus_probe.py` | running |
| `orbit-prune` | opus5-xhigh (`opus`) | `OrbitOracle` protocol + pynauty oracle; hook in the Python tie-branch; `algorithm="canonical_orbit"`; frozen-pin bit-exactness; differentials; branch-count table; censored-tail probe; **added by message:** `canonical_rank` (`wstar_rank`) arm | `core/orbit_oracle.py`, `core/hypergraph_to_string.py`, `core/canonical.py`, `core/algorithms/registry.py`, `iso_backends/orbit_oracle.py`, 2 test files, `scripts/diagnostics/orbit_pruning_probe.py` | running |

Worktrees: created by the harness under `.claude/worktrees/agent-*` on
branches `worktree-agent-*`; logs at `.claude/notes/2026-09-06-isal-kb-w1/<name>.md`
inside each worktree, committed.

## Plan after this wave

1. Verify both logs against the diffs; re-run their fast tests in their
   worktrees with their cloned envs (`~/.conda/envs/isalhg-owemit`,
   `~/.conda/envs/isalhg-orbit`); merge into `feature/isal-kb-word`
   (`--no-ff`), fast suite after each merge.
2. **Wave 2 (one agent, opus xhigh):** harness integration —
   `experiments/tkde/matrices.py` (WORD_ARMS + DEFAULT_SPECS: `isal_ow_struct`,
   `isal_ow_rank`, `isal_ow_rank0`, `wstar_rank`; `wstar_orbit` where the
   budget allows), `rq1.py` (arm branches with the forked-child budget for the
   Python engines; instruction-granularity distances beside `symbol_distance`;
   `zero_shift` and `|Aut|` columns), `rq7.py` (the `|Aut|` axis), RQ3
   `MEDOID_ARMS`, RQ4 `DEFAULT_ARMS` + cache, RQ5 cache, RQ6 (`_ow_word`,
   interiors, and an n-gram generator over the `w°` alphabet mirroring
   `fact_ngram`); local smoke on subsamples; then Picasso RQ1 (`RQ1_isal`).
3. Selection from the RQ1 table by the pre-registered rule; then RQ2–RQ7 on
   Picasso with the adopted arm; harvest to the drive; stats harness G5.
4. Prose: `docs/article/D_ART3/prose.md` §2.1–2.3, §3 RQ1, §4 theory table,
   §6, §11 — the Isal word replaces the fact-rank word; `START_HERE.md`
   §0/§0.1/§6.0 reversal note; `DESIGN.md` G1. One-page PI reading. Ledger
   notes. Dated summary here.

## Interventions

- 21:20 — `orbit-prune` scope extended by message with the fourth ablation
  cell `canonical_rank` (`wstar_rank`): the family's greedy walk with the
  residual tie and the new-vertex order resolved by nauty's rank; contract
  in the message and in the design doc §3b. Priority: after its items 1–4.
- 21:35 — `ow-emitter` reported Prop. C.5 partially falsified under the
  frozen "shorter circular direction" move rule (forward-rendered runs have
  length `N − gap`, grow under every insertion, flip at `N/2`; measured max
  22 on 400 random binary stars vs exactly 2 in the backward regime).
  **Decision (orchestrator): the move rule is replaced by the no-crossing
  rule** — moves computed in backward-position coordinates from the root
  without wrapping, both phases, all pointers. Proof file (Def. 3.2, the
  star-shape lemma, Prop. C.5(b) now ≤ 3 with the signature-shift mechanism,
  new Remark "Why the move rule is not shorter direction") and the design
  record updated; corrected contract sent to `ow-emitter` with the request
  to pin (a) ≤ 2 unconditionally and report the word-length price.

## Verdicts

- **`ow-emitter` — ACCEPT** (branch `worktree-agent-aa0166cf355893a2a`, head
  `1863553`, 4 commits). Verified: clean tree; 9 changed files = the log's
  list; 114 owned tests pass in its env and again from the main checkout
  after the merge; `get_distance("isal_ow_struct")` resolves (the agent added
  three rows to `metric_space/registry.py::_LAZY_MODULES`). Corpus probe
  (`scripts/diagnostics/ordered_walk_corpus_probe.py`, seed 20260906):
  wd50k66 3,988 / ndc_classes 1,381 — 0 disconnected, 0 degenerate; median
  0.08 ms per member (max 0.9 ms); word median 6 (wd50k66) / 8 (ndc)
  instructions vs `nauty_certificate_rows` median 12; round trip 300/300 and
  invariance 300/300 per policy per corpus. Single-edit `{hub, new constant}`
  on 200 wd50k66 members: `ow_struct` median 1 instruction, ≤ 2 in 0.815;
  `ow_rank` 2 / 0.545; `ow_rank0` 2 / 0.625; `nauty_cert_rows` median 12,
  ≤ 2 in 0.000. Prop. C.5 under the no-crossing rule on 400 binary stars:
  (a) max 2, (b) max 3 (position kept: max 1); forward runs 0/400.
  Word-length price of the rule is a tail: 300 wd50k66 words median 6→6,
  max 96→137. Flag: H-M1d only half confirmed (median order holds; on the
  ≤ 2 fraction `rank0` 0.625 > `rank` 0.545; `struct` wins either way).
  Note: `ordered_walk.py` imports the private `_movement_tokens` from
  `hypergraph_to_string.py` (orbit-prune's file) — harmless; keep at merge.
- **`orbit-prune`** — cut off by the plan's rate limit mid-work
  (2026-09-06 ~22:30; one commit `3c23499` with the four core/iso_backends
  files; tests, probe and log left uncommitted in its worktree). Resumed
  in place on 2026-09-07 with a message listing its state and priorities.

- **`orbit-prune` — ACCEPT** (head `467e6a4`, 10 commits; clean tree; 8 files
  all inside ownership; 35 orbit + frozen-pin tests pass in its env).
  Pins bit-exact on Fano, STS(9), `C_13(0,1,3)`, n=4 and GQ(2,2) vs the C++
  `w*_c`; the two STS(13) pins are written, slow-marked, never completed
  (> 50 min in Python). Branch collapse on symmetric stars: unpruned frames
  326 / 1,957 / 13,700 / 109,601 for q = 5..8 (= Σ q!/(q−d)!) → 6 / 7 / 8 / 9
  pruned, q − 1 oracle calls, same string. 20-leaf star (|Aut| = 2.4e18):
  0.024 s. Censored tail (C++-censored wd50k66 members, highest |Aut| first,
  60 s): 41/52 complete — 97 % at |Aut| ≥ 1e7 (median 0.30 s), 33 % at
  1e3–1e7. Corpus differential 267/267 wd50k66 members agree. Added the
  `canonical_rank` arm (invariant under 200 relabellings, complete on 500
  pairs). Two facts to carry: (i) `_enum_displacements` is now `lru_cache`d
  (byte-identical, 7–20× on the pruned engine); (ii) **the Python encoder
  materialises `(2r+1)^k` displacement tuples and OOMs at `k ≥ 5`** —
  pre-existing; it makes every Python engine (`wstar_orbit`, `wstar_rank`)
  infeasible on arity ≥ 5 members (≈ 9 % of wd50k66, most of ndc_classes);
  the C++ engine's Round-11 inversion avoids it. Also flagged for the PI:
  `pynauty_levi` and `w*_c` disagree on inputs declaring different
  vocabulary sizes (fingerprint contract).
- **`harness-isal` — ACCEPT** (head `022abcc`, 5 commits; 27 files all inside
  the extended ownership; 22 integration tests pass + 7 skipped pending the
  orbit merge). All seven runners produce Isal rows; fingerprint-first
  matrices (`ndc_classes` N = 1,381 `isal_ow_struct` in 0.21 s vs 183 s
  pairwise); RQ1 has `d_instr`, `n_instr`, `zero_shift`, `aut_bucket`, the
  selection table, Holm vs `nauty_cert_rows`, censoring per (arm, m, |Aut|);
  RQ6 `ow_ngram`: validity 1,000/1,000 **and connectivity 1,000/1,000**
  (Prop. C.4) vs `fact_ngram` 1,000/1,000 valid but **256/1,000 connected**.
  Two defects it found, not its own: a forked child deadlocks after any
  in-process C++ `canonical_string` call (guarded in `engine_word`;
  `rq3.run_guarded` unguarded — audit needed); `fact_rank_roles` fails M0
  invariance 43/60 on wd50k66 (a retired arm; the known roles defect).

## The local RQ1 preview (60 members × 3 corpora, 1 replication) — the diagnosis

Median `d_instr` (one symbol per instruction / row / token) and the ≤ 2
fraction, uncensored rows, constant-preserving and changing kinds:

| corpus | edit | `isal_ow_struct` | `w*_c` | `nauty_cert_rows` | `fact_rank` |
|---|---|---|---|---|---|
| wd50k66 | delete_fact | **1** (0.61) | **1** (0.77) | 15.5 (0.00) | 6 (0.12) |
| wd50k66 | remove_constant | **2** (0.51) | **2** (0.66) | 14.5 (0.07) | 6.5 (0.12) |
| wd50k66 | insert_fact_new_constant | 13 (0.09) | **4** (0.31) | 17 (0.00) | 7 (0.08) |
| wd50k66 | add_constant | 7 (0.08) | **4** (0.16) | 11 (0.18) | 5 (0.32) |
| wd50k66 | insert_fact (existing) | 14 (0.02) | 6 (0.07) | 8 (0.00) | **3** (0.49) |
| ndc_classes | delete_fact | **3** (0.43) | **3** (0.47) | 12 (0.00) | 5 (0.20) |
| ndc_classes | remove_constant | **2** (0.51) | **2** (0.58) | 10 (0.13) | 3 (0.39) |
| ndc_classes | insert_fact_new_constant | 14.5 (0.02) | 7 (0.04) | 13 (0.00) | **4** (0.18) |
| ndc_classes | add_constant | 6 (0.05) | 4 (0.14) | 4.5 (0.32) | **2** (0.66) |
| ndc_classes | insert_fact | 17 (0.00) | 8 (0.03) | 10 (0.00) | **2** (0.52) |
| synthetic_rq1 | all five | 13–19.5 | 12–23.5 | 7–23 | **1–13** |

Reading. (1) **The Isal walks — both of them — are the most local
representation under deletions** on the real corpora: removing a fact or a
constant removes tokens without renumbering anything, while rank-addressed
serialisations renumber. (2) **On insertions `w*_c` is 2–3× more local than
the ordered walk**: the greedy walk creates a constant's facts while the
constant is still adjacent to `p_1` (one `P` step), whereas the ordered
walk's breadth-first-by-anchor order defers them until the constant has been
pushed far from the root and then pays the excursion twice. That is a policy
defect of the ordered walk, not a limit of the machine. The displacement-
aware deterministic walk already exists: **`wstar_rank`**, the family's
greedy walk with the canonical labelling as the residual tie key (the
"both" cell of the ablation). (3) The pre-registered H-M1a is falsified for
the ordered walk; H-M1b (relative addressing) holds only for root-anchored
growth (the emitter's probe: median 1 vs 12) and fails for leaf-anchored
insertions. (4) `synthetic_rq1` (random KBs) is bad for every Isal arm and
is not the paper's data.

Consequence for the plan: measure `wstar_rank` on the same protocol;
if it tracks `w*_c`'s locality, it becomes the representation candidate
(complete, deterministic, one greedy run, no exponential case); the
ordered walk stays as the order-only ablation with its named mechanism. The
Python engines need the C++ engine for arity ≥ 5 (NDC), so the rank tie
key must be ported to `h2s.cpp` (wave 3) before the Picasso RQ1.

## 2026-09-07 morning — after the merges

- HEAD `2ccc9fa` on `feature/isal-kb-word`: merges of `orbit-prune` (`02e42c5`
  lineage) and `harness-isal`, plus two guard commits in
  `experiments/tkde/budget.py`: the Python engines (`wstar_rank`,
  `wstar_orbit`) are refused above `min(k, arity) = 4` or above 2e6
  displacement tuples, censored with the reason (the workstation went out of
  memory on the six-arm local preview; the user stopped it).
- **User instruction (2026-09-07):** run on Picasso, not locally; spawn a
  cheap agent for the upload. → `picasso-rq1` (sonnet5-high) is syncing the
  branch, rebuilding the cluster env, running the smoke and submitting the
  full RQ1 array (`configs/rq1.yaml`, all arms, ≥ 8 GB per task).
- **Wave 3 spawned:** `cpp-rank` (opus xhigh, worktree from `2091ac6`) ports
  the rank tie key to the C++ engine so `wstar_rank` covers arity ≥ 5
  (`ndc_classes`); acceptance = bit-identical to the Python engine wherever
  it runs, frozen pins untouched, timing vs C++ `w*_c`.
- **Defect found by `cpp-rank` (2026-09-07):** the orbit-prune deliverable
  `canonical_rank` applies `ranks` only in the root frame of `_encode_from`
  (not forwarded to the four recursive calls), so below depth 0 it falls
  back to min-edge-id ties and full permutation branching — edge-order
  dependent (3/400 random instances change under an edge-order shuffle;
  vertex relabelling 0/400, which is why the existing test passed) and
  exponential. **Ruling:** the described semantics (ranks threaded through
  every frame; singleton ties; one deterministic path) are the definition;
  `cpp-rank`'s ownership extended to the `ranks` path of
  `hypergraph_to_string.py` and the `TestCanonicalRank*` classes (edge-order
  invariance test added). Every `wstar_rank` row computed before the fix is
  void; `wstar_rank` removed from today's Picasso RQ1 submission (message to
  `picasso-rq1`) and re-run after the C++ port. `wstar_orbit` is unaffected
  (tie-branch path; its pruning is verified at depth by the branch-count
  table and the 267/267 differential).
- The six-arm local preview produced no rows before the stop; the decisive
  `wstar_rank` locality numbers will come from the Picasso RQ1 (Python engine
  on guard-satisfying members) and, with full coverage, after the C++ port.

## Wave 3 — `cpp-rank` (2026-09-07) — ACCEPT, merged `9f29962`

Head `7161357`, 7 commits, clean tree; the one file outside the listed
ownership is `src/isalhg/core/_core.pyi` (the extension's type stub — part of
the bindings, accepted). 34 fast tests pass in its env; full suite 2,233
passed / 7 skipped in its log. Built: C++ `AlgorithmVariant::GreedyMinRank = 8`
(rank vector in the arena; residual tie key computed on demand; single
`(label, rank)` ordering; min-rank seed; no branching), bindings validate
the permutation; `canonical_string_rank` / `canonical_fingerprint_rank`
default to C++. **Fixed the Python `ranks` path** (forwarded through every
frame; edge-order shuffle invariance 0/400 after, 3/400 before; pinned).
Differentials, all bit-identical: fixtures 13/13, random 1,000/1,000, stars
300/300, relabelled 200/200, guard-satisfying wd50k66 300/300;
`ndc_classes` C++-only: 6,000/6,000 invariant, 300/300 pairs agree with
pynauty; Round-11 three-way check under the rank key 90/90. Timing (N = 200
per corpus, engine time): `wstar_rank` 0.47 ms / 0 censored (wd50k66),
0.59 ms / 6 censored (ndc_classes) vs `w*_c` 0.55 ms / 10 and 1.14 ms / 23.
Censoring is exactly the arity-10 members (0/294 at arity 3–9, 16/41 at
arity 10): the displacement search's `k_disp` blow-up, not the key — filed
as a Round-13 lever in the optimisation log. Slow orbit STS(13) pins never
got a clean run (long processes were killed by the session limit); the
frozen `w*_c` STS(13) pins pass. Its post-completion turn hit the plan's
session limit (resets 13:10); no work lost.

Consequence: `wstar_rank` is now runnable on every corpus member at ms
cost; it must be (re-)submitted on Picasso as its own RQ1 experiment on the
same seeded edits, then merged into the RQ1 table with the other arms.

## User rule (2026-09-07, mid-turn): "Everything that will go in the final article must be run in the C++ engine"

Consequences for the arms: `w*_c` (C++) and `wstar_rank` (C++ since wave 3)
qualify; `wstar_orbit` (Python oracle hook) and `isal_ow_*` (Python emitter)
do **not** yet — both need bit-identical C++ ports (T-KBb for the orbit hook;
a new task for the ordered-walk emitter) before their rows count in a final
table. Because the ports must be bit-identical, the locality rows measured
under the Python implementations remain valid evidence during design; the
timing rows (M3) must be re-measured in C++. The RQ6 decoder already has a
C++ backend (`string_to_hypergraph(backend="cpp")`); the n-gram sampler is
harness code, not the engine. Planned: wave 4 after the quota window
reopens (13:10): (a) `cpp-orbit` — the orbit oracle as a nanobind callback
or native automorphism orbits inside `encode_from`; (b) `cpp-ow` — the
ordered-walk emitter in C++ with the golden-pin table as the acceptance
gate. Until then, the article's candidate tables are built from the C++
arms only.

## 2026-09-07 13:25 — wave 4A spawned; rank experiment on the cluster

- `cpp-orbit` (opus xhigh, worktree from `45ce493`): the orbit oracle as a
  nanobind callback inside the C++ tie-complete search; acceptance = frozen
  pins incl. both STS(13) through C++, differentials vs the Python orbit
  engine and vs unpruned C++ `w*_c`, branch collapse, and the article's R2
  table (censored tail per |Aut| bucket on both corpora). `cpp-ow` (T-KBd)
  runs after it (shared `bindings.cpp`).
- Branch synced to the cluster at `6d5a579` (`configs/rq1_rank.yaml`,
  `RQ1_CONFIG` in launcher/worker); rank smoke 2248491 submitted 13:2x;
  the full rank array (`addressing_rank`, 24 shards) follows its completion.
  Main array 2247394: 218 row files at 13:22.

## Merge record

- 2026-09-06 `4037e67` merge(ow-emitter) into `feature/isal-kb-word`
  (`--no-ff`); OW tests green from the main checkout (114 passed).
- (orbit-prune pending)

## Wave 2

- `harness-isal` spawned 2026-09-07 on base `4037e67` (opus xhigh, worktree):
  harness arms + RQ runners + local RQ1 smoke. Runs concurrently with the
  resumed `orbit-prune` (2 opus agents — the ceiling).
- Intervention: `WORD_ARMS` lives in `src/isalhg/metric_space/toolkit/matrix.py`
  (not in `experiments/tkde/matrices.py` as the prompt assumed). Ownership of
  that file granted to `harness-isal`; instruction: route any arm whose
  distance object returns a non-None `fingerprint(H)` through
  `distance.matrix(items)` (fingerprint-once + cdist) before the pairwise
  fallback; fact path untouched; routing unit test.

## Open follow-ups

- Roles variant (T-KBa). C++ port of orbit pruning (T-KBb). nauty-free ordered
  walk = structural keys + orbit-pruned tie-complete residual (option C; T-KBc,
  future work).
