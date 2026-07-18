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
| ☐ | **S1** — Baseline & foundations | Clean committed baseline; connected domain; corpora + primitives exist | `[O]` commit v3 rescope + branch decision + PI email → `[O]` T-TBf → { T-M1c ∥ T-M2c ∥ T-M4 } (+ T-M0b filler) | dirty tree is expected at start — committing it IS the first action |
| ☐ | **S2** — Competitors & real anchor | All five `D_rep` implementations + the real-anchor verdict | { T-M3a ∥ T-M3b ∥ T-M3c } → { T-M3d ∥ T-M4' } → `[O]` T-DQ3' | S1 merged green |
| ☐ | **S3** — Geometry instrumentation & HPC submit | Geometry helpers + G2 profiles + doc hygiene; E1' batch queued on Picasso | { T-M5f ∥ T-M5g ∥ T-TBg } → `[O]` T-M5a part 1 (DQ1' probe + HPC submission) | S1 (T-M2c, T-M4); S2 (T-M3a) |
| ☐ | **S4** — Applications (the body) | A1–A4 results + the per-corpus geometry table | T-M5b → { T-M5c ∥ T-M5d ∥ T-M5e } | S3 (T-M5f, T-M5g); T-DQ3' verdict decides corpora |
| ☐ | **S5** — Discussion evidence & closure | E1' figure + bits table; PI decisions executed; ledger truthful | `[O]` T-M5a part 2 (harvest + figure + bits) → `[O]` PI checkpoint (T-TBc unblock/retire; T-M0c execute) | PI answer on D-ART2; HPC batch finished |
| ☐ | **S6** — Optional & stretch | Only if wanted after everything article-critical is closed | { T-M4a ∥ T-TBe } (either or none) → T-M6 | S1–S5 done; explicit human opt-in |

---

## S1 — Baseline & foundations

**Sequence.**
1. `[O]` **Commit the v3 rescope** sitting uncommitted on
   `perf/canonical-complete-orbit-pruning` (docs + skills; conventional
   `docs(article):` message). The standard preflight requires a clean tree —
   this commit is how you get one.
2. `[O]` **Branch decision (surface to the human, do not decide):** continue
   sessions on `perf/canonical-complete-orbit-pruning` or merge it to `main`
   first. The branch carries in-flight orbit-pruning C++ perf work; the human
   knows its state, you do not.
3. `[O]` **PI email reminder (human sends):** the D-ART2 ratification package
   (`DECISIONS.md`, points a–e) plus the T-M0c naming decision (option (a)
   rename vs (b) promote to true STS(13)). Sessions S1–S4 do not depend on the
   answer; S5 does.
4. `[O]` **T-TBf** — reconcile the unmerged T-TBb closure (cherry-pick
   `e6b0af7`, `a362657` if separate, the `T-TAi` file if it exists). Marked
   orchestrator-only; do it with no workers running.
5. **Fan out (3 workers):** T-M1c ∥ T-M2c ∥ T-M4.
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
6. **Lane watch-points:** T-M2c and T-M4 both live under `datasets/` — T-M2c
   edits existing generators, T-M4 adds a new module + registry entry; keep
   `datasets/registry.py` out of T-M2c's lane. T-M1c and T-M2c both touch
   `core/` but different files (`canonical.py` vs `sparse_hypergraph.py`).

**Exit criteria.** Full suite + ruff + mypy at (or better than) preflight
baselines on the merged tree; ladder/corpus generators emit only connected
hypergraphs; a planted-family corpus with verified non-isomorphic within-family
members exists; the metric-axiom suite is green over `w*_c`.

**Orchestrator notes (append-only).**

- _(empty)_

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

- _(empty)_

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

- _(empty)_

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

- _(empty)_

---

## S5 — Discussion evidence & closure

**Sequence.**
1. `[O]` **T-M5a part 2** — harvest the Picasso E1' results; produce the
   ours-only ρ + scatter figure and the bits/Wilcoxon table; close T-M5a.
   **PI-gated:** if D-ART2 came back modified (e.g. MI reinstated, sweep
   requested), rescope before running — do not produce v2 artifacts silently.
2. `[O]` **PI checkpoint** — execute the answers now on file:
   - T-TBc: unblock (run as ablation on the sanctioned axes) or retire to
     follow-up; move the file accordingly.
   - T-M0c: execute option (a) rename or (b) promote (note (b) regenerates
     pinned `w*` values — orchestrator-only if chosen).
   - Any other D-ART2 deltas → update `PROPOSAL.md`/ledger, file handoffs.
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
