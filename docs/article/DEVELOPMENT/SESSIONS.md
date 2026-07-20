# Orchestrator session plan — v3 execution (D-ART2)

**Status:** ACTIVE (authored 2026-07-18 17:56 CEST, with the D-ART2 rescope).
**Owner:** the `task-orchestrator` (Fable). Workers never edit this file.

## How to use this file (orchestrator contract)

1. At session start, find the **first unticked row** of the master table. That
   row is your session. Its task structure (∥ / → below) overrides your own
   slot-filling; deviate only with a stated reason in the session's notes.
2. Run the standard `task-orchestrator` preflight first (clean tree, baselines,
   snapshot). Session-specific preconditions are listed per session under
   *Gates*.
3. Task ids resolve via the ledger (`find docs/article/DEVELOPMENT -name
   'T-<id>.md'`); each task's own file is the authority on its acceptance.
   Where a task's prose predates D-ART2, D-ART2 wins (`DECISIONS.md`).
4. At session end: tick the row's checkbox, and append to that session's
   **Orchestrator notes** block — what closed, what didn't and why, premises
   refuted, handoffs filed, baseline numbers, and anything the *next* session's
   orchestrator must know. Notes are append-only.

**Notation.** `A ∥ B` — run in parallel (isolated worktrees, disjoint lanes,
≤3 workers). `A → B` — B starts only after A is merged green. `[O]` —
orchestrator-only, done in the main tree with no workers running. `(filler)` —
optional small task to fill a freed slot; never blocks the session.

## Master checklist

| ✓ | Session | Goal | Task structure | Gates |
|---|---|---|---|---|
| ☑ | **S1** — Baseline & foundations | Ledger reconciled; connected domain; corpora + primitives exist | `[O]` branch decision → `[O]` T-TBf → { T-M1c ∥ T-M2c ∥ T-M4 } (+ T-M0b filler; stretch: pull S2 wave 1 forward) | v3 pushed at `5e6b73e`; D-ART2 PI-ratified — no approval gate |
| ☑ | **S2** — Competitors & real anchor | All five `D_rep` implementations + the real-anchor verdict | { T-M3a ∥ T-M3b ∥ T-M3c } → { T-M3d ∥ T-M4' } → `[O]` T-DQ3' | S1 merged green |
| ☑ | **S3** — Geometry instrumentation & HPC submit | Geometry helpers + G2 profiles + doc hygiene; E1' batch queued on Picasso | { T-M5f ∥ T-M5g ∥ T-TBg } → `[O]` T-M5a part 1 (DQ1' probe + HPC submission) | S1 (T-M2c, T-M4); S2 (T-M3a) |
| ☑ | **S4** — Applications (the body) | A1–A4 results + the per-corpus geometry table | T-M5b → { T-M5c ∥ T-M5d ∥ T-M5e } | S3 (T-M5f, T-M5g); T-DQ3' verdict decides corpora |
| ☐ | **S5** — Discussion evidence & closure | E1' figure + bits table; T-M0c executed; ledger truthful | `[O]` T-M5a part 2 (harvest + figure + bits) → `[O]` closure sweep (T-M0c execute; ledger truth) | HPC batch finished; T-M0c answer on file |
| ☐ | **S6** — Optional & stretch | Only if wanted after everything article-critical is closed | { T-M4a ∥ T-TBe } (either or none) → T-M6 | S1–S5 done; explicit human opt-in |

---

## S1 — Baseline & foundations

*Re-scoped 2026-07-18 18:23 CEST: D-ART2 is **PI-ratified** and the v3 rescope
is committed and pushed (`5e6b73e`), so the former commit and PI-approval
steps are gone. S1 starts on a clean tree; the only decision to surface is the
branch question.*

**Sequence.**
1. `[O]` **Branch decision (surface to the human, do not decide):** sessions
   currently sit on `perf/canonical-complete-orbit-pruning`, which carries
   in-flight orbit-pruning C++ perf work. Merge to `main` first, or continue
   here? Record the answer in the notes and run the preflight baselines on
   whichever tree the human picks.
2. `[O]` **T-TBf** — reconcile the unmerged T-TBb closure (cherry-pick
   `e6b0af7`, `a362657` if separate, the `T-TAi` file if it exists). Verified
   still pending on this branch at the re-scope: `T-TBb.md` sits in
   `T-TB/OPEN/`, and `scripts/probe_pointer_runs.py`,
   `scripts/tb3_coherence_criterion.py`,
   `tests/unit/core/test_no_w_tokens.py` are absent. Orchestrator-only; do it
   with no workers running, and re-run the suite after the cherry-pick before
   fanning out.
3. **Fan out (3 workers):** T-M1c ∥ T-M2c ∥ T-M4.
   - **T-M1c** — metric-axiom property suite; fixes the `n=0` identity bug.
     Lane: `core/canonical.py`, `metric_space/distances/isalhg_levenshtein.py`,
     `tests/property/`, `iso_backends/isalhg_backend.py` (guard only).
   - **T-M2c** — connectivity-preserving generators + LCC policy. Lane:
     `core/sparse_hypergraph.py` (edit guards),
     `datasets/synthetic/{_random_hg,perturbation_ladder,correlation_corpus}.py`,
     `DATA.md` wording.
   - **T-M4** — planted families + scoring primitives. Lane:
     `datasets/synthetic/planted_families.py` (new), `datasets/registry.py`,
     `metric_space/metrics/{association,information,embedding,geometry}.py`
     (new).
   - **(filler) T-M0b** — 2-line Python-path perf fix in
     `core/structural_tuples.py`; slot it if a worker returns early.
4. **Stretch refill (judgment call):** with the commit/PI steps gone this
   session is lighter. If a worker merges green with session time left, pull
   **S2 wave-1** tasks (T-M3a, T-M3b, T-M3c) into freed slots — they depend
   only on T-M1a (CLOSED) and conflict with no S1 lane; among themselves their
   collision file is `metric_space/registry.py` (trivial, merge is yours).
   Record any pull-forward in the notes so S2's orchestrator knows what
   remains.
5. **Human reminder (one line, non-blocking):** the only outstanding PI input
   is **T-M0c** (rename the cyclic-13 fixtures vs promote them to true
   STS(13)s — option (b) regenerates pinned `w*` values). Ask when convenient;
   S5 executes the answer.
6. **Lane watch-points:** T-M2c and T-M4 both live under `datasets/` — T-M2c
   edits existing generators, T-M4 adds a new module + registry entry; keep
   `datasets/registry.py` out of T-M2c's lane. T-M1c and T-M2c both touch
   `core/` but different files (`canonical.py` vs `sparse_hypergraph.py`).

**Exit criteria.** T-TBf artifacts present and `T-TBb.md` reads CLOSED; full
suite + ruff + mypy at (or better than) preflight baselines on the merged
tree; ladder/corpus generators emit only connected hypergraphs; a
planted-family corpus with verified non-isomorphic within-family members
exists; the metric-axiom suite is green over `w*_c`.

**Orchestrator notes (append-only).**

- **Session run 2026-07-18 ~18:30–22:00 CEST (Fable orchestrator). S1 CLOSED —
  all five exit criteria met.** Chronology and decisions below.
- *Branch decision (human):* commit the 8 uncommitted D-ART2 ratification doc
  edits (`b0908b0`), then **merge to `main`** and run S1 there. `main`
  fast-forwarded to the perf-branch tip.
- *Premise refuted, plan rewritten (human-approved):* `origin/main` carried
  ~28 executed commits (2026-07-09→07-15) the local v3-rescope line never saw:
  **T-M2c, T-M4, T-M4' , T-M3a–d implemented + CLOSED**, the T-TBb closure +
  T-TAi filing, and a **v2-scope T-M5a closure** with Picasso jobs
  1547131/32/33 submitted. SESSIONS.md's S1/S2 fan-out premise (redo T-M2c/
  T-M4, build competitors) was false. Human chose the **full reconciliation
  merge** (`65314ec`). Resolution policy: v3 prose wins every doc conflict;
  executed CLOSED statuses adopted; T-M5a stays OPEN in its v3 rescoped form
  (v2 closure record dropped, supersession note appended); **T-M5a' → BLOCKED**
  (parked at D-ART2); v3-delta notes appended to CLOSED T-M3c (promoted
  acceptance → S2 verification) and T-M4 (geometry-sweep params +
  `geometry.py` → owned by T-M5f); D-CONN1 generator facts grafted into
  `DATA.md` §3.
- *T-TBf:* closed via the merge rather than cherry-pick (`5f17dae`); all
  acceptance clauses re-verified (T-TBb in CLOSED/, both probe scripts + no-W
  test present, T-TAi on the ledger).
- *Fan-out (shrunk):* T-M1c ∥ T-M0b only. First launch died on the session
  usage limit (reset 20:50 CEST); relaunched 21:08, both DONE.
- *T-M0b merged (`0f96b2c`):* `_neighbour_degree_key` consumes the prebuilt
  adj (8→1 `primal_graph` builds on Fano); +2 call-count regression tests.
- *T-M1c merged (`e583732`):* `DegenerateHypergraphError` on n=0 (the
  identity-of-indiscernibles fix — `are_isomorphic(∅,•)` now `False`,
  `fingerprint(∅)` raises); metric-axiom Hypothesis suite over `w*_c`
  (labelled + unlabelled, vs `brute_force_iso`, with the seed-prefix teeth
  check); pinned `normalize=True` triangle-violation witness; index family
  `{d_I^{k,h,Σ}}` documented in `IsalHGLevenshtein` + `stability.md` §1.
  +16 tests.
- *Orchestrator verification of adopted work (PASS):* `canonical_string`
  raises `DisconnectedHypergraphError` on a disconnected input;
  `correlation_corpus` 30/30 and `perturbation_ladder` 30/30 connected;
  `planted_families` 12/12 connected, 4 families, labels present, **0
  isomorphic within-family pairs** (exact fingerprints, all 12 pairs).
- *Baselines at S1 close (merged `main`):* **895 passed, 18 skipped, 13
  deselected; ruff 3; mypy 21 in 7 files** (preflight was 685/8/7 + same
  ruff/mypy; growth = merged + new tests, zero failures, zero drift).
- **⚠ Hazard for the next orchestrator:** both agent worktrees were cut from
  the **stale `origin/main` tip (`3551a04`)**, not from local `main` — worker
  doc edits were v2-based and needed three-way care at merge (README table,
  T-M1c ledger file). At every launch, check `git merge-base main HEAD` in
  the new worktree before letting a worker touch shared prose.
- *S2 impact:* wave-1 **and** wave-2 code already exists (T-M3a–d, T-M4'
  CLOSED). S2 collapses to: the competitor verification pass (five `D_rep`
  `matrix()` runs on a small corpus, iso pairs → 0; incl. T-M3c's promoted
  acceptance) + `[O]` T-DQ3'. `COMPETITORS_USAGE.md` (merged) documents
  invocation; HyperCOT needs its pinned env rebuilt/checked.
- *Pending human (non-blocking):* T-M0c — rename cyclic-13 fixtures (a) vs
  promote to true STS(13) (b; regenerates pinned `w*`); S5 executes the
  answer. `main` is **not pushed** (not asked); push is a fast-forward of
  `origin/main`.

---

## S2 — Competitors & real anchor

**Sequence.**
1. **Wave 1 (3 workers):** T-M3a ∥ T-M3b ∥ T-M3c — nauty-Levi edit distance
   (contrast), HPD (vendored), NetLSD (full member since D-ART2). All add
   separate modules under `metric_space/representations/`; the shared collision
   file is `metric_space/registry.py` — trivial merges, but they are yours.
2. **Wave 2 (2 workers):** T-M3d ∥ T-M4' — HyperCOT (pinned
   `isalhg-hypercot` conda env + `SubprocessRepresentation`; the heaviest
   wiring) and the HIC atlas loader (`datasets/hic_atlas.py`). Disjoint lanes.
3. `[O]` **T-DQ3'** — time `w*_c` on a named HIC IMDB instance (loader from
   wave 2). One number, a go/no-go recommendation for the real anchor, recorded
   in the closing note and reflected in `DATA.md` §2's gate. Cheap; run it
   yourself after the T-M4' merge.

**Exit criteria.** Each of the five competitor distances produces a `matrix()`
on a small corpus with distance 0 on iso pairs (metric competitors); HyperCOT's
env documented; T-DQ3' verdict recorded (it decides S4's corpus list — the
declared fallback in `DATA.md` §2 applies if red).

**Orchestrator notes (append-only).**

- **Session run 2026-07-19 ~10:45–14:00 CEST (Fable orchestrator). S2 CLOSED —
  all three exit criteria met — plus a user-directed T-OPT extension.**
- *Shape change (stated reason):* per the S1 notes, wave-1/2 code was already
  CLOSED, so no workers were spawned for T-M3a–d/T-M4'; S2 ran as the
  orchestrator verification pass + `[O]` T-DQ3'. Preflight baselines
  910/18/15, ruff 3, mypy 21/7 (green).
- *Verification pass (PASS, re-runnable via `scripts/verify_competitors.py`):*
  all six representations on the planted corpus (18 hypergraphs, 5 planted
  iso pairs): iso pairs → 0 (netlsd 1.5e-14, hypercot 7.1e-16), both complete
  invariants separate every non-iso pair; d_I offdiag med 7 / max 17. T-M3c's
  promoted acceptance verified.
- *Defects found + fixed (commit `7dc30e8`):* (a) three test files' `HIC_ROOT`
  missed the `/hypergraph` segment — their "HIC data absent" skips were
  wrong-path skips (data on disk all along); 10 tests un-skipped. (b) `netlsd`
  was not installed in the main env (T-M3c tested only in its worker env) —
  installed, added to the `bench` extra. (c) `scripts/hypercot_worker.py`
  pinned commit `f190266` — a copy-paste of the **HPD** vendor hash; true
  HyperCOT HEAD is `5045539` (repo static since 2023-01-19). (d) T-M3d read
  `Status: BLOCKED` inside `CLOSED/` with a stale closing note — reconciled
  (the `c2fddd6` coordinator completion was never reflected in the ledger).
- *HyperCOT env:* rebuilt verbatim from `envs/hypercot.yml` (network up);
  10/10 tests incl. the HIC smoke on real RHG-10 data.
- *T-DQ3' (closed, `T-DQ/CLOSED/T-DQ3prime.md`): **NO-GO — fallback executed**
  (`DATA.md` §2, PROPOSAL OQ-B/OQ-C resolved).* Corpus k=110 on IMDB-Dir-Form
  is beyond `K_MAX` and Python-DNF on the *median* instance; the arity≤10
  sub-corpus keeps 78.7% (class retention 89/71/71%) but a 10 s budget
  completes only 73/100 — DNFs symmetry-driven, not size-driven (n=10, m=5
  DNF while n=22, m=79 completes). ≈57% yield under two label-correlated
  filters ≠ defensible anchor. **OD6 filed (pending PI):** optional
  censored-subset secondary exhibit. Arity-cap survival across all 12 HIC
  sets recorded in the closing note (Steam-Player worst at 24.8%).
- *User-directed extension (mid-session):* new scope **T-OPT** (C++ engine
  revision). **T-OPTa** merged (`40986e5`): runtime `k > K_MAX` via the
  `k_disp` clamp — orchestrator differential proved it value-preserving
  (40 hypergraphs × full k-sweep + matrix hash, byte-identical); **orbit
  pruning premise refuted** — the worker's per-node fingerprint is necessary
  but not sufficient for orbit membership (Hypothesis n=5 witness); encoder
  stays unpruned, `w*_c` untouched, budget re-run 74/100 ≈ baseline (verdict
  unchanged). Worker's AC2 claim corrected in the ledger (the named T-DQ3'
  DNFs are genuine timing DNFs — 000392 re-confirmed >330 s post-merge).
  **T-OPTb** merged: C++ S2H interpreter, corpus-scale parity verified;
  speedup flat ~1.24× (parse/validate stay Python-side) — decode is not a
  bottleneck; value = reach parity + 31 tests. **T-OPTc filed OPEN** (correct
  stabiliser-orbit pruning; the worker's promised-but-unfiled handoff).
  T-M3e (user-requested doc-propagation task) declared, executed, closed.
- *Baselines at S2 close (merged `main`):* **971 passed, 8 skipped, 15
  deselected; frozen pins 6/6 (~89 s); ruff 3; mypy 21 in 7 files;
  `verify_competitors.py` ALL PASS** — numbers identical before/after both
  C++ merges. `main` is **not pushed** (not asked).
- **⚠ Hazards for the next orchestrator:** (1) the worktree-isolation hazard
  recurred — T-OPTa's worktree was cut from the pre-session HEAD (`b30c8b6`);
  the fix that worked for T-OPTb: an explicit launch-prompt instruction to
  check `git merge-base main HEAD` and `git merge main` before starting.
  Check it at every launch. (2) The greedy encoder is slow at moderate n
  (`greedy_min_nbrdeg` ≈ 22 s at n=30, m=60; minutes at n=60) — size the DQ5
  geometry sweep and the A4 ladder pools against measured `w*_c` wall-clock,
  not assumptions. (3) S4's corpus list = the fallback (planted + small
  designs); include HIC only if the PI approves OD6.

---

## S3 — Geometry instrumentation & HPC submit

**Sequence.**
1. **Fan out (3 workers):** T-M5f ∥ T-M5g ∥ T-TBg.
   - **T-M5f** — static-invariant helpers (`metrics/{embedding,geometry}.py`
     completeness) + the per-corpus geometry-table spec. May refine
     `theoretical/geometry.md` — that file is in ITS lane this session.
   - **T-M5g** — G2 harness in `experiments/article/`: `s(e)` histograms (ours
     **and** nauty contrast), ladder-response curves; confronts the
     three-regime coherence prediction (`stability.md` §4.2).
   - **T-TBg** — reasoning/tracking disentangle. Lane:
     `theoretical/stability.md`, `empirical/correlation.md`, other legacy
     prose — but **not** `geometry.md` (T-M5f owns it this session) and not
     the `DEVELOPMENT/` tree beyond relocating checklist content into
     `T-TB/`.
2. `[O]` **T-M5a part 1** — after T-M2c/T-M4 corpora exist: run the DQ1'
   oracle wall-clock probe, pin the mini-corpus, submit the E1' exact-HGED
   batch to Picasso (`picasso-sbatch` skill). `git mv` T-M5a to
   `IN-PROGRESS/`. Queue latency is why this submits now and harvests in S5.

**Exit criteria.** Geometry helpers unit-tested (pinned spectra; hubness vs
hand-computed value); G2 profiles rendered on the four design fixtures + one
synthetic corpus; T-TBg's acceptance grep clean; E1' batch visible in the
Picasso queue; T-M5a in `IN-PROGRESS/`.

**Orchestrator notes (append-only).**

- **Session run 2026-07-19 ~16:00–17:00 CEST (Fable orchestrator). S3 CLOSED
  — all five exit criteria met.** Preflight baselines 971/8/15, ruff 3,
  mypy 21/7 (identical to S2 close); snapshot `wip/orchestrator-20260719-1610`.
- *Fan-out as planned:* T-M5f ∥ T-M5g ∥ T-TBg, all three DONE and merged
  serially (`87bb172`, `80c9978`, `6537298`). All three worktrees were cut
  from the current main tip — the S1/S2 stale-base hazard did not recur
  (launch-prompt `git merge main` instruction kept).
- *T-M5f merged:* ν + Shepard added to `embedding.py`; new `geometry.py`
  (concentration, length floor, N_k, hubness skewness — hand-checked
  0.8165 pin); 31 tests; geometry-table spec appended to T-M5b;
  `geometry.md` needed no refinement. Worktree suite 1002/8/15 green.
- *T-M5g merged after a round-1 correction:* the worker's closing note was
  smoke-only; orchestrator ran the FULL harness in its worktree (8/8
  sensitivity cells 214 s, 6/6 ladder cells 23 s, RTX-4060) and the analysis
  (records merged across cells — the CLI takes one JSON per type).
  **Three-regime confrontation (stability.md §4.2): 5 confirmed, 2
  FALSIFIED** — C13 orbit and GQ(2,2) predicted heavy-tailed, measured
  heavy-tail 0.000 (narrow ours-profile under single arity≤3 Qin edits).
  Nauty avalanche contrast confirmed everywhere (IQR_nauty 2.5–9.5× ours).
  Ladders near-monotone (80% monotone steps; mean Δd_I 3.2→11.7 with size).
  Worker updated its closing note with the full-run table (`8618a75`).
  Figures + confrontation JSON on the results drive under `T-M5g/analysis/`.
- *T-TBg merged:* stability.md §6 checklist (~90 lines) relocated to
  `T-TB/`; task ids/dates/audit phrasing stripped from stability.md,
  correlation.md, applications.md + 4 READMEs; acceptance grep re-run by the
  orchestrator — only the deliberate ledger-pointer lines remain; deleted
  lines audited, no scientific claim lost.
- *`[O]` T-M5a part 1 executed:* DQ1' probe (0 DNFs to n=10; ceiling
  (10,8); `DATA.md` §6 resolved), mini-corpus pinned
  (`e1prime_mini_corpus.yaml`, 12 cells, ≈7,560 pairs), local smoke green
  (ρ=0.633 on cell 0; HGED=0 ⇔ d_I=0), repo rsynced + editable install
  rebuilt on Picasso, **job 1616143 submitted and RUNNING (all 12 array
  tasks)**; results →
  `fscratch/isalhg_results/T-M5a/e1prime`. T-M5a → `IN-PROGRESS/` with the
  part-1 record appended.
- *Handoffs:* **T-M5h filed (OPEN, user-directed)** — propagate the S3
  measured outcomes (incl. the §4.2 partial falsification) into
  stability.md/geometry.md/applications.md prose.
- *Baselines at S3 close (merged `main`):* **1010 passed, 8 skipped, 15
  deselected; ruff 3; mypy 21 in 7 files.** `main` not pushed (not asked).
- **⚠ Hazards for the next orchestrator:** (1) S5's harvest must check the
  Picasso outputs' `meta.json` per cell (idempotent re-submit fills any
  missing cell — resubmit only failed indices with `--array=<idx>`).
  (2) The `rtk` git proxy hides merge commits in `git log` output — use
  `git show -s --format='%h %p %s'` for ground truth. (3) S4's T-M5b
  should read T-M5f's geometry-table spec appended at the bottom of its
  task file, and the G2 falsification may deserve a caveat line in the
  geometry table's prose (T-M5h owns the prose change).
- *S3 addendum (2026-07-19 ~17:15 CEST):* **T-M5h executed and merged**
  (`63d9a5d`) in this session per the human's direction (S4 deferred to a
  fresh session). The worker grounded every number in
  `g2_regime_confrontation.json` and corrected the orchestrator's own
  earlier ratio claim (nauty/ours IQR spans **1.25–9.5×**, not 2.5–9.5× —
  GQ(2,2) is 10.0/8.0). stability.md §4.2 now carries the measured-outcome
  block (5 confirmed / 2 falsified + candidate explanations), geometry.md §6
  the measured profile + ladder summary, applications.md §G2 the
  measured-results framing; PROPOSAL.md untouched (no contradicted claim).
  Acceptance grep re-run clean by the orchestrator; all numbers re-verified
  against the JSON and the ladder configs (large base n=12 confirmed).
  Docs-only merge — no suite rerun needed. S4 entry state: T-M5b first,
  alone; T-M5h is DONE, so S4 has no prose-lane companion task.

---

## S4 — Applications (the body)

**Sequence.**
1. **T-M5b first, alone** — it builds the shared cached-`D`-matrix runner in
   `experiments/article/`, the MDS/CV-dimension pipeline, and emits the
   per-corpus geometry table. Every later application reuses its caches; that
   is why it is sequential.
2. **Then fan out (3 workers):** T-M5c ∥ T-M5d ∥ T-M5e — clustering +
   dendrogram; kNN (reported against the G1 concentration/hubness profile);
   shortest path (ladder-scored, decoded S2H intermediates). All under
   `experiments/article/analysis/`, disjoint modules, shared caches read-only.
3. Corpus list per T-DQ3': planted families (+ small real designs) always;
   HIC only if the S2 verdict was green — otherwise invoke the declared
   fallback (`DATA.md` §2) and say so in the notes.

**Exit criteria.** Geometry table complete for every (corpus, representation);
A1–A4 task metrics + figures render for ours and every applicable competitor;
HyperCOT rows present where feasible with the scale limit stated; capability
matrix filled (A4).

**Orchestrator notes (append-only).**

- **Session run 2026-07-19 ~17:20–19:40 CEST (Opus orchestrator). S4 CLOSED —
  all four exit criteria met.** Preflight baselines 1010/8/15, ruff 3, mypy
  21/7 (green); snapshot `wip/orchestrator-20260719-1718`. Corpus = the
  declared **fallback** (planted families; NO HIC — T-DQ3' NO-GO). OD6
  (secondary censored-HIC exhibit) stayed pending-PI and non-gating.
- *Main advanced mid-session:* **T-M5h** (S3 doc-propagation) was merged to
  `main` by a parallel actor during the run (`3489ba5`+`63d9a5d`+`390756e`) —
  prose-only, off every S4 code lane; adopted cleanly. `ca214b3` remained an
  ancestor; code baseline unchanged (T-M5h added no code).
- *Phase 1 — T-M5b first, alone:* MDS flagship + geometry table.
  **Round-1 correction (orchestrator-caught):** the worker's CV `D̂` selector
  was **in-sample** (embedded the full matrix, read "held-out" RMSE off the
  same fit) → D̂ pinned to the cap for every non-Euclidean rep (incl. IsalHG).
  Sent back; worker replaced it with genuine K-fold leave-out-points CV +
  Gower (1968) out-of-sample extension, raised the cap to min(n−1,40), and
  added an L1-from-R³ test that fails under the old code (recovers D̂≈3).
  Corrected table: **IsalHG D̂=21** (real elbow, ν=0.123, non-Euclidean);
  WL-L1/HPD D̂=40, NautyEdit D̂=39 (censored, PSD Euclidean-like, monotone
  curve — honestly flagged); NetLSD D̂=5. Merged `5802ae9`. Also filed:
  **T-M5i** (runner `_build_dataset` kwarg bug; worker worked around with a
  bespoke cache writer of identical layout; low-priority, OPEN).
- *Phase 2 — { T-M5c ∥ T-M5d ∥ T-M5e }, 3 isolated worktrees.* All read
  T-M5b's cached `D.npy`; README/SESSIONS reserved to the orchestrator (zero
  worker README edits → no 3-way churn); merged serially, each on a
  re-verified canonical suite.
  - **T-M5c (A2 clustering)** — PAM (`kmedoids.fasterpam`; sklearn-extra had a
    numpy ABI break) + UPGMA dendrogram; silhouette/Dunn/DB/ARI/NMI/cophenetic.
    **Round-1 correction:** `kmedoids` was imported but undeclared → merged
    suite would have errored; sent back to declare `kmedoids>=0.5` in the
    `bench` extra (orchestrator pre-installed it in the shared env). Result
    (planted_main): IsalHG ARI 0.181/NMI 0.318 — **mid-pack** (HPD-JSD leads
    at ARI 0.331; WL/NautyEdit ARI≈0). Merged.
  - **T-M5d (A3 kNN)** — precomputed KNN, LOO/stratified CV, acc/macro-F1/
    AUC-OvR vs k, read against the G1 profile. **Clean first pass.** Headline:
    the G1 hubness prediction is confirmed — **WL hubness 1.777 → AUC-OvR
    ≈0.50**; IsalHG 65%/AUC 0.80; HPD best 72%/0.87; NautyEdit ~27%
    (avalanche destroys neighbourhoods regardless of hubness). Merged.
  - **T-M5e (A4 shortest-path)** — Dijkstra on a kNN(k=3) `D`-graph;
    path-recovery + monotonicity + S2H-decoded intermediates. **Clean first
    pass** (scorer verified correct on a planted-recoverable path).
    Result (44-item ladder pool): **monotonicity=1.00 all reps**; the
    **decodability differentiator holds** — IsalHG decodes 3 valid S2H
    intermediates, WL collapses to a 2-node direct path, NetLSD/HPD have no
    decoder, nauty cannot navigate (G2 avalanche); capability matrix filled.
    **Path recovery is a null** (0.00 ours/WL/NetLSD, 0.33 HPD) — the d_I
    geodesic shortcuts the specific edit path; honest and *consistent with §5's
    no-proxy thesis*, not a defect. Merged.
- *Verification discipline:* every worker's closing check re-run by the
  orchestrator in its own env under the canonical `-m "not slow"` scope
  (workers' own counts used ad-hoc scopes); two undeclared-dependency /
  leakage defects caught that the workers' green self-checks had hidden.
  Confirmed the workers' "ruff 14" was a wider-scope artifact — canonical
  `src/ tests/` ruff stayed **3**.
- *Baselines at S4 close (merged `main`):* **1062 passed, 8 skipped, 16
  deselected; ruff 3; mypy 21 in 7 files** (1010 → +12 M5b +13 M5c +13 M5d
  +14 M5e, zero failures, zero drift). `main` **not pushed** (not asked).
- *Follow-ups for S5 / prose:* (1) the geometry table shows censored D̂ as a
  bare cap number for WL/HPD/NautyEdit — a `d_hat_censored` flag / prose
  caveat belongs in the geometry-table prose (T-M5h owns prose; note for the
  writer). (2) A4 recovery was measured on one endpoint pair / one target
  ladder — averaging over more pairs would strengthen scores (i)/(ii);
  optional polish, non-blocking (A4 is a capability differentiator, not a
  benchmark statistic). (3) On task metrics IsalHG is competitive but not
  dominant (HPD-JSD leads A2/A3 on the planted corpus) — the paper's edge is
  the geometry licences + the A4 capability matrix, reported honestly.
- **⚠ Hazards for the next orchestrator:** (1) `main` advanced mid-S4 (T-M5h);
  always re-check `git merge-base main HEAD` and prefer `git show -s
  --format='%h %p %s'` over `git log` (rtk hides merge commits). (2) Worker
  self-reported ruff/pytest counts use inconsistent scopes — always re-run the
  canonical `pytest tests/{unit,property,integration} -m "not slow"` +
  `ruff check src/ tests/`. (3) `kmedoids` is now a `bench`-extra dependency —
  a fresh env needs `pip install -e ".[dev]"` to get it.

- **Post-S4 addendum 2026-07-20 (PI-directed): Picasso copy-back + OD6 HIC
  exhibit (T-M5j).** Two user asks after the S4 close.
  - *Picasso E1' copy-back:* job 1616143 finished; rsynced
    `fscratch/isalhg_results/T-M5a/e1prime/` → local — 21 `D.npy` (12/12
    `isalhg_levenshtein`, **9/12 `exact_hged`**; 3 expensive HGED cells DNF'd →
    S5 must resubmit `--array=<missing>`). Nothing else on the Picasso drive.
  - *OD6 resolved (PI: include HIC)* — recorded in `DECISIONS.md`; **A4 excluded**
    (ladder-based). Feasibility probed first: local `w*_c` on IMDB genre is fast
    (median ≈ 1 ms; the earlier "HIC infeasible" read was the high-symmetry RHG
    datasets, which lack labels). **T-M5j** filed + orchestrated:
    A1/A2/A3 on all 6 IMDB genre variants, full arity≤10 subset, 5 s `w*_c`
    timeout censoring.
  - *T-M5j (2 rounds, merged):* censoring is bimodal — **2 clean** (Wri-Genre
    92.5%, Wri-Genre-M 91.7%), **4 heavily censored** (Dir-*/Wri-Form 34–43%
    yield, min-class 14–38%; the T-DQ3' label-correlated tail). **Round-1
    correction (orchestrator-caught):** HPD-JSD silently vanished from the two
    clean datasets — a *vendored* `hyperedge_portrait` `IndexError` on degenerate
    instances (Wri-Genre 295/833, Wri-Genre-M 102/266) swallowed into a log
    warning; and the worker's aggregate "IsalHG mid-pack 3/5 / NetLSD leads"
    conflated clean with the ≤43%-censored Dir-* sets. Sent back; worker surfaced
    HPD on its per-instance-computable subset (flagged) and re-drew conclusions
    from clean data only. **Honest clean-HIC read:** genre is near-unclusterable
    from structure (A2 ARI < 0.10 for *every* rep); A3 kNN AUC led by IsalHG +
    NetLSD, WL-L1 trails (hub_skew 4.5–7.4 → the same G1 hubness story as
    planted). **OD6 acceptance test: censoring does NOT flip the IsalHG
    conclusion.** Suite 1062 → **1081** (+12 R1 +7 R2), ruff 3, mypy 21.
    Artifacts under `results/T-M5j/` (D caches, per-dataset geometry/clustering/
    kNN tables, censoring table, figures). `main` not pushed.

---

## S5 — Discussion evidence & closure

**Sequence.**
1. `[O]` **T-M5a part 2** — harvest the Picasso E1' results; produce the
   ours-only ρ + scatter figure and the bits/Wilcoxon table; close T-M5a. The
   spec is final (D-ART2 ratified as packaged): no MI, no sweep, no competitor
   rows.
2. `[O]` **Closure sweep** —
   - T-M0c: **executed early, 2026-07-18** (PI answered (b) right after S1
     closed): true STS catalog vendored (orders 3–15, Pottonen/Kaski–
     Östergård), cyclic partial systems truthfully renamed, true-STS(13)
     `w*_c` pins added under `slow` (~44 s each; distinct hashes). Closing
     note in `T-M0/CLOSED/T-M0c.md`. Remaining S5 item: the proof-side
     naming fix (6 spots in `theorem_a_completeness.tex`) — PI-owned.
   - T-TBc stays parked (D-ART2 point (d), ratified) — no action unless the
     PI reopens it.
3. Final ledger sweep: statuses, scope counts, dependency graph in
   `README.md` reflect reality; every closed task carries its closing check.

**Exit criteria.** Every article-facing figure/table exists and is
reproducible from `experiments/article/`; no OPEN task claims to gate the
paper; `DECISIONS.md` has no silently-unresolved entry.

**Orchestrator notes (append-only).**

- _(empty)_

---

## S6 — Optional & stretch (explicit human opt-in)

**Sequence.** { T-M4a ∥ T-TBe } — entropy-coded bits estimator; crossing-peak
conjecture — either or none, per the human's call → T-M6 (the `isomorphisms/`
reparent) last, only if the symmetry is wanted.

**Exit criteria.** Whatever ran is green and merged; nothing here ever blocks
the paper.

**Orchestrator notes (append-only).**

- _(empty)_
