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
| ☑ | **S5** — Discussion evidence & closure | E1' figure + bits table; T-M0c executed; ledger truthful | `[O]` T-M5a part 2 (harvest + figure + bits) → `[O]` closure sweep (T-M0c execute; ledger truth) | HPC batch finished; T-M0c answer on file |
| ☑ | **S7** — Pre-writing revision (data + stats + framing) | Strict master corpus (known designs + parametric sweep); CIs + paired tests on the whole body; naive baseline; G3; real anchor; framing docs | { T-M7a ∥ T-M7b ∥ T-M7c } → { T-M7d ∥ T-M7e ∥ T-M8a } → { T-M7f ∥ T-M7g ∥ T-M8c } → T-M8b → `[O]` T-M8d | S1–S5 merged; `REVIEW/` specs on file (Mario-directed 2026-07-22); PI notified that S7 supersedes the N=240 headline numbers |
| ☐ | **S6** — Optional & stretch | Optional, post-article: fold the published Gray code into the bits axis; stretch theory + reparent | { T-M4a (incl. Gray-code bits column) ∥ T-TBe } (either/none) → T-M6 | S1–S5 done; explicit human opt-in; runs after S7 if both are wanted |

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

- **Post-S4 addendum #2, 2026-07-20 evening (PI's own parallel session —
  recorded here by the S5 orchestrator for continuity).** T-M5l (D̂
  robustness: Horn parallel analysis + N-scaling sweep + budget-Shepard)
  filed, executed, merged (`19fa344`); finding: D̂ = 21 at N = 60 is an
  under-resolved lower bound that plateaus at 26 (Horn bracket [12, 26]).
  Consequence executed in the same session: `planted_n240` (20 families × 12)
  added across the A1/A2/A3 pipelines (`a1a6e7a`) and **N = 240 promoted to
  the primary corpus** with a runtime axis (`0360b08`) — geometry and
  applications now measured on one object (ν = 0.250, D̂ = 26; A2 ARI: HPD
  0.120 > d_I 0.102; A3 AUC: HPD 0.83 > d_I 0.73, WL collapses at hubness
  4.586). E1'/bits are corpus-independent (own mini-corpus + body corpora)
  and were not invalidated; the S5 orchestrator synced the remaining prose
  (G1 block) and extended bits to planted_n240.

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

- **Session run 2026-07-20 ~16:00–00:00 CEST (Fable orchestrator). S5
  functionally complete; row left unticked pending only the T-M5a 12/12
  re-harvest (Picasso job 1618786, PI: let it run).** Preflight baselines
  1081/8/16, ruff 3, mypy 21/7; snapshot `wip/orchestrator-20260720-1602`.
- *Stated deviation from the `[O]`-only plan:* per the human's explicit
  directive, the three implementation lanes ran as ledger-workers
  (T-M5a pt-2 ∥ T-M5i ∥ T-M5k) with the orchestrator keeping HPC ops,
  verification, merges, and closure. Every worker needed exactly the
  verification discipline the plan assumes: **all three self-reported green
  and all three carried defects their own checks hid.**
- *Preflight finds:* (1) three fabricated stress@D̂ cells in the
  user-committed A1 prose table (0.643/0.170/0.242 vs artifact
  0.240/0.010/0.013; matched-D reading ruled out by recomputation) — fixed
  `e16d0d6` (later superseded by the N=240 rewrite). (2) The T-M5j R2 HPD
  patch had clobbered the two clean HIC datasets' tables to HPD-only rows —
  filed T-M5k. (3) The three missing E1' cells died OOM (16.7 GB)/timeout —
  resubmitted as job 1618786 (100 GB/72 h) before fan-out.
- *T-M5i (2 rounds, merged `9eb12cc`):* R1 fix left the injected `seed`
  kwarg reaching registry factories (its mock-based test hid it; caught by
  a real-path repro) → R2 passes `dataset_params` un-mutated + binds the
  cell seed via `HypergraphDataset.seed()`; real-path test T14. Named
  branches untouched.
- *T-M5k (1 round, merged `3a908f4`):* root cause = `run_hic_dataset` step 6
  truncating tables to current-run rows; `_merge_repr_rows` fix + 4
  regression tests; six tables regenerated from D.npy caches (backups under
  `.pre-t-m5k-backup/`). Orchestrator verification vs the raw matrices found
  **two transcription errors in the T-M5j closing note itself** (NetLSD
  Wri-Genre-M hub 0.403→1.571; NautyEdit clean-mean AUC@9 0.640→0.654, tying
  NetLSD) — correction note appended to T-M5j (`53a1555`), A3-HIC prose
  narrowed to "hubness contrast recurs".
- *T-M5a pt-2 (2 rounds, merged `6d35fd1`):* the worker's headline
  "PREMISE FALSIFIED (bits)" was **refuted by verification** — its
  `w.split(";")` token count fragments bracketed V/C tokens (~2×);
  with the repo parser every hypergraph compresses (median r 1.433/1.565,
  in-band). The false T-M5l handoff it had filed was retracted on-branch;
  regression tests pin the tokenizer. E1' side verified against an
  independent orchestrator computation (ρ=0.6033, N=5,661 — exact match).
  The same split-bug existed dormant in `runner.run_info_content_cell`
  (it had corrupted the v2 smoke bits, median r 0.51) — orchestrator fix
  `3fd94ce` with a fail-then-pass regression test (T15).
- *Post-merge, post-regime-change sync:* G1 measured block → N=240 values
  (verified vs `geometry_table_planted_n240`; `bcb0ba0`); bits extended to
  planted_n240 (`882b62f`; N=320 pooled median r=1.441, p=1.6e-54, β=0.749);
  measured E1'(provisional) + bits blocks folded into `correlation.md`
  (`b482ab4`). All A1/A2/A3 N=240 prose numbers verified against the drive
  artifacts (all faithful).
- *Closure sweep:* T-M0c proof-side renaming verified executed (0 STS(13)
  in the tex, PDF recompiled 2026-07-19; the "remaining S5 item" bullet
  above was stale). T-TAi's "gates T-M5a" claim expired (note appended,
  `fb225b8`) — **no OPEN task gates the paper** (T-M4a/T-M6/T-OPTc/T-TAi/
  T-TBe all optional/stretch). OD1/OD2/OD5 resolved (PI, `5ad163b`) —
  DECISIONS.md has no silently-unresolved entry. Baselines at sweep:
  **1108 passed / 8 skipped / 16 deselected, ruff 3, mypy 21/7** (+27 tests
  over preflight, zero failures, zero drift across three serial merges).
- *DQ1' probe-design lesson (for the record):* the probe timed ladder pairs
  only; the expensive E1' pairs are the cross-ladder ones — the (10,8)
  ceiling was optimistic for the oracle (not for `w*_c`). Recorded in the
  T-M5a addendum; `correlation.md` now carries the oracle-ceiling note as
  discussion-supporting evidence.
- *Remaining to tick this row:* job 1618786 lands → idempotent
  `e1prime_harvest` re-run (12/12), final ρ into `correlation.md`, T-M5a →
  `CLOSED/`, tick. Fallback if 72 h expires: pin E1' on the 9 completed
  cells (PI to confirm; protocol in the T-M5a addendum).
- **S5 CLOSED 2026-07-21 ~10:35 CEST.** Job 1618786 delivered n9_s1
  (8h29, 55 GB peak) and n10_s0 (7h50) → interim 11/12 harvest ρ=0.622
  (N=6,921), independently recomputed (exact match). n10_s1 then died
  **OUT_OF_MEMORY at 100 GB after ~18 h**; **PI decision (Mario): close E1'
  at 11 blocks** — whole-block exclusion (spec forbids per-pair censoring),
  recorded as the final composition in `DATA.md` §4 and as the measured
  oracle-ceiling data point in `correlation.md`. T-M5a → `CLOSED/` with the
  full acceptance check; README hub final (T-M5 0 open / 12 closed; no
  article-critical work remains; Runnable now = S6 opt-in). Closing
  baselines: **1108 passed / 8 skipped / 16 deselected, ruff 3, mypy 21 in
  7 files** (identical to the S5-sweep numbers; docs-only closure diff).
  `main` pushed.
- *S6 entry state:* everything article-facing is measured, verified, and
  reproducible from `experiments/article/` (harvests idempotent). Optional
  pool: T-M4a (entropy-coded bits), T-TBe (crossing peak), T-M6 (reparent),
  T-OPTc / T-TAi (encoder optimization, value-preserving only). None gates
  the paper.

---

## S7 — Pre-writing revision: data, statistics, framing

*Declared 2026-07-22 11:56 CEST, directed by Mario, from the `docs/article/REVIEW/`
audit (walkthrough + data-rigor + strict-data spec + stats plan + approach
rigor). Purpose: close the two co-equal evidence gaps found there — (1) the body
is a single-point study (planted random-seed families at n=10, k=3; no measured
result at k∈{5..10}) and (2) no A1–A3 result carries a CI or significance test —
plus the selected framing items (naive baseline, label-family Remark,
capability-matrix figure, practitioner motivation, reproducibility artifact) and
the G3 geometry-response experiment. Scopes: **T-M7 = code**, **T-M8 = docs**.
The task files are the authority on acceptance; the REVIEW specs are their
context, not their replacement.*

**Gates.** S1–S5 merged green; the seven `REVIEW/` files on file; the PI is
aware that S7 **supersedes the N=240 headline numbers** (geometry table and
A1–A3 move to the master corpus with CIs — the N=240 artifacts remain on the
drive as the superseded record, per the T-M5l precedent for the N=60→240
regime change). **All gates satisfied — PI approved S7 (relayed by Mario,
2026-07-22).** The T-M7g optional label-stripped HIC run remains an in-session
PI/human call (non-gating), not covered by this blanket approval.

**Sequence.**

Wave 1 — foundations, disjoint lanes:
{ **T-M7a** (known-design seed catalog + Stratum A + realized-parameter
logging + feasibility pilot) ∥ **T-M7b** (Stratum B factorial sweep configs +
feasibility envelope; the k=10 cells exercised or their exclusion measured) ∥
**T-M7c** (naive baseline degree-sequence L1 — must merge before T-M7d so its
row rides the harness) }

Wave 2 — the heavy re-run + independent lanes:
{ **T-M7d** (combined sweep + statistics harness: G1/A1/A2/A3/bits over
Strata A+B, seven representations, S≥20 seeds/cell, BCa CIs + Holm-corrected
paired Wilcoxon + effect sizes; geometry-vs-axis curves; **landmine:** bits
through the bracket-aware parser, T15 pins) ∥ **T-M7e** (Stratum C design-seeded
ladders; G2 + A4 re-run; arity-≥4 cells re-score the §4.2 three-regime
confrontation) ∥ **T-M8a** (label-conditional metric family Remark +
`d_I^⊥`/`d_I^Σ` table annotations — doc lane) }

Wave 3 — consumers of the harness + writing lane:
{ **T-M7f** (G3 OFAT geometry response: five move axes, response curves, MDS
trajectories, ν-contribution, decoded+drawn filmstrips, competitor contrast) ∥
**T-M7g** (real anchor: designs-catalog exhibit through the harness +
gate-first real-world corpus, ≥85% yield + label-independent censoring;
optional label-stripped HIC per PI) ∥ **T-M8c** (A1–A4 practitioner motivation,
verified citations — writing lane) }

Wave 4 — synthesis, then closure:
**T-M8b** (capability-matrix main figure + §Usefulness reframing; needs
T-M7c's row and T-M7d's final numbers) → `[O]` **T-M8d** (reproducibility
artifact + `REPRODUCING.md` + deposit — orchestrator-only, last, after all
caches are final).

**Worker cautions.** (a) The `(k, h, vocabulary)` triple is an index family:
never pool raw `d_I` across `k` — compare dimensionless descriptors and
within-`k` rankings only (T-M7b/d/f all touch this). (b) One rendering
convention for every drawn hypergraph (G3 filmstrips, A4 intermediates,
capability-matrix-adjacent figures) — stated once, used everywhere. (c) The
conda-env hazard applies as always: cloned env per worker, never the shared
one. (d) E1′ stays closed — no task re-opens the oracle.

**Exit criteria.** Every A1/A2/A3/G1/bits table cell on the master corpus
carries a 95% CI; every competitor-vs-IsalHG claim carries a Holm-corrected p +
effect size; geometry-vs-axis curves exist for ≥3 values per axis (n, density,
arity) with error bands; the feasibility envelope is an artifact; the
naive-baseline row is on every surface; G2/A4 run on design-seeded ladders and
the three-regime confrontation is re-scored; G3 ships five filmstrip artifacts
with monotone fractions and trajectory-continuity statistics; the real-anchor
gate records exist (promoted corpus or measured no-go); the Remark and metric
annotations are in the reasoning prose; the capability matrix is a figure and
§Usefulness leads with it; the artifact dry-run reproduces bits + geometry +
one application figure from `REPRODUCING.md`. Ledger truthful; baselines
re-recorded; `main` pushed.

**Orchestrator notes (append-only).**

- **2026-07-24/25 — S7 re-run executed and closed (orchestrator).** The re-run
  of the HGED-free body on the corrected corpus (17-family Stratum A + 10
  admitted Stratum B, S=27, 7 representations) is complete. Sequence as run,
  not as planned: the Wave-1/2 corpus and harness work (T-M7a/b/c/m/o/p/h/n)
  had already merged in the data-correction phase; this session unblocked and
  ran **T-M7d** (sweep+stats, S=8 validation on Picasso then S=27 array
  1640910), re-ran **T-M7q** (G2/A4 on the corrected corpus — G3/T-M7f was
  verified corpus-valid and *not* re-run, so T-M7r was withdrawn on evidence),
  **T-M7g** (real anchor = designs catalog; real-world gate all-NO_GO),
  harvested via **T-M7s**, and produced the docs (**T-M8b** capability matrix,
  **T-M8f** prose fold, **T-M8d** repro artifact).
- **Two defects caught in verification, both filed and fixed rather than
  merged:** (1) the S=27 array never persisted paired tests — every stats file
  had an empty `wilcoxon` dict and the harvest counted in-memory objects
  (**T-M7t**: aggregation now written to disk, bidirectional Wilcoxon + Holm +
  BCa, cross-checked against an independent computation); (2) the T-M8f fold
  initially carried self-derived percentile-bootstrap p-values, corrected to
  the pipeline BCa artifacts.
- **Findings folded into the article, not hidden:** A2/A3 reported honestly
  (IsalHG beats WL/nauty on A2-ARI + all A3 points and HPD on A3, ties HPD on
  A2, loses A2 clustering to the degree baseline and NetLSD); the scalability
  frontier (k=3→n≈24, k=5→n=8, k=7/10 infeasible) and the three IsalHG-only
  4-hour timeouts stated as findings; the arity-axis shortfall recorded
  (`all_acceptance_pass: false`).
- **Exit criteria:** every A1/A2/A3/G1/bits cell carries a 95% BCa CI; every
  competitor comparison carries a Holm-corrected p (both directions) + effect
  size; naive baseline on every surface; G2/A4 on design-seeded ladders + §4.2
  re-scored (16/17); real-anchor gate records exist (NO_GO); Remark + capability
  matrix + prose fold + repro artifact in place; dry-run reproduces geometry +
  bits + a paired test from shipped caches. **Not fully met on one axis:** the
  Stratum B arity sweep has 2 points (k∈{3,5}) not 3 — a measured consequence
  of the feasibility envelope, reported as a limitation. `main` clean, baselines
  1478/9/29 · ruff 3 · mypy 21. Deposit DOI pending PI.

---

## S6 — Optional & stretch (explicit human opt-in)

*Refined 2026-07-21 (directed by Mario): fold the now-published variable-length
Gray code into S6 on the **bits axis only**. Ezequiel's displacement-coding idea
(email 2026-07-17, analysed in `../theoretical/stability_reformulations.md` §4)
is now a proved, citable primitive — López-Rubio, *A Variable-Length Gray Code
for the Natural Numbers*, arXiv 2607.16088 (2026); its §5.3 names IsalHG and
proposes this integration. `V : ℕ → {0,1}*` is bijective/complete (Thm 4.1),
Gray — consecutive integers one edit apart (Thm 4.2) — and near-log compact
(`L(V(n)) = ⌊log₂(n+1)⌋`, Thm 4.3). **Placement holds with D-ART1/D-ART2:** `V`
enters the information-content (bits) estimator (T-M4a), not the `d_I` metric
substrate. For IsalHG the only unbounded operand — the pointer displacement — is
already unit-edit-local under the unary `P/N` encoding (`../H2S_S2H.md` §3), so
`V` buys **compactness, not new locality**; re-metrizing `d_I` is a different
object that re-opens the geometry pillar (measured on raw `d_I`, N=240) and
targets drift, which the avalanche dominates and D-ART2 de-scoped. The
metric-substrate integration stays parked (T-TBc), as follow-up-paper material:
the preprint's §5.3(b) program — encoder integration + correlation effect +
downstream LM processing — is that sequel, and `V` is its admissible metric
instrument there (Thm 4.2 ⇒ no code-level avalanche, unlike arithmetic coding).*

**Sequence.** { T-M4a ∥ T-TBe } — either or none, per the human's call → T-M6
last, only if the symmetry is wanted.

1. **T-M4a — bits estimators, now including the Gray code `V`.** Emit the
   PROPOSAL-§4 compression table under **three** estimators as side-by-side
   columns, never substituting one for another (a coded IsalHG side against the
   naive incidence-list competitor would stack the deck):
   - (i) **fixed-width** `B = |w|·log₂|Σ_HG(k)|` — the shipped, reviewer-tested
     baseline (median r = 1.441 on 320/320, Wilcoxon p = 1.6e-54); the honest
     floor, kept.
   - (ii) **universal / model-free — the Gray column** — sign bit + `V`(|δ|) per
     displacement, ≈ `1 + ⌊log₂(|δ|+1)⌋` bits; replaces the unary `Θ(|δ|)`
     accounting so bits scale with structure, not layout. **Model-free ⇒ no
     training corpus and no `w*_c` recomputation** — re-render the cached
     move-blocks and recount. Expect `r` to rise (Gray shortens the operand),
     strengthening "a hypergraph is a compact word".
   - (iii) **arithmetic-coded** — static frequencies on a random corpus
     **disjoint from every experiment corpus** (`../DATA.md`). Compression-only:
     an AC bitstream must never be a distance substrate (code-level avalanche,
     `../theoretical/stability_reformulations.md` §4).
   - **Landmine:** count tokens/bits through the bracket-aware parser — a raw
     `w.split(";")` overcounts ≈2× and *reversed* the bits conclusion twice in
     S5; reuse the pinned regression tests.
   - **Doc touch (with the run):** cite the preprint in the §4 bits subsection,
     add it to `../RELATED_WORK.md`, and drop a one-line future-work pointer in
     `../PROPOSAL.md` §5 / `../empirical/correlation.md` naming `V` as the
     published instrument for the deferred displacement transcoding.
2. **T-TBe** — crossing-peak conjecture (stretch theory; raw-metric drift).
   Unchanged, non-blocking.
3. **T-M6** — the `isomorphisms/` reparent, last, only if the symmetry is wanted
   (OD1 reopens only along this path).

**T-TBc stays BLOCKED — S6 does not reopen it.** It moves only on an explicit
PI decision to run the metric-substrate ablation or to open the follow-up paper
(D-ART2 point (d)).

**Exit criteria.** Whatever ran is green and merged; nothing here ever blocks the
paper. If T-M4a ran: the §4 table carries all three estimator columns on the body
corpora with the Wilcoxon test rerun per estimator; the Gray/`V` column reuses the
cached `w*_c` (no re-canonicalization) and is counted through the bracket-aware
parser + its regression tests; the preprint is cited in the bits subsection and
listed in `../RELATED_WORK.md`.

**Orchestrator notes (append-only).**

- _(empty)_
