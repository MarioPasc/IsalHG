# Handoff — the Isal instruction word for knowledge bases (D-ART4), 2026-09-07

*Written by the `[IsalHG-Refinement]` orchestrator session for the agent that
continues this work. Everything below is either on disk (path given), a job
id on Picasso, or a rule the author gave in session. Read it end to end, then
the design record, then the wave summary; do not re-derive what is settled.*

## 0. State in one paragraph

The paper's representation is the **Isal instruction string** (D-ART4; the
fact-rank word is out). Two limits of the family's canonical string `w*_c`
were diagnosed to one cause — it is the *minimum of a search* — and treated
separately: **locality** by canonical programs that do not search (the
ordered walk `w°`, Theorem C; the rank-keyed greedy walk `w*_ρ`, the "both"
cell) and **symmetric-input cost** by stabiliser-orbit pruning of the search
itself (value-preserving, `w*_c` bit-identical). All three, plus the original
`w*_c`, run on the **C++ engine** — the author's rule is that only C++ results
reach the article — each port bit-identical to its Python reference on every
differential (both full corpora for the ordered walk; 700 + 600 instances for
the orbit path; 1,000 + 300 + 300 for the rank key). The RQ1 measurement of
all cells is running on Picasso as three experiments on identical seeded
units; a local 60-member preview already shows the shape: both Isal walks are
the most local representation under **deletions** (median 1–3 instructions
against 10–15 for certificate rows), `w*_c` is 2–3× more local than the
ordered walk under **insertions** (the ordered walk's breadth-first order
defers a leaf's facts; the greedy walk creates them one pointer step away),
and the rank-keyed greedy walk is the deterministic polynomial form of the
walk that gets this right — its own row is what the running rank experiment
supplies. Every prediction and its status is in the design record.

## 1. Read, in order

| # | file | what it settles |
|---|---|---|
| 1 | `docs/article/D_ART3/experiments/ISAL_VARIANT_DESIGN.md` | the pre-registration: definitions, theorem sentences, hypotheses H-M0…H-M4/H-A, the four-cell nauty ablation (§3b), the selection rule, the per-RQ swap plan, the implementation map; §9 (added today) records the measured deviations |
| 2 | `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/proofs/completeness/theorem_c_ordered_walk.tex` (+ `.pdf`) | Theorem C (completeness of any deterministic emitter along a canonical labelling), Prop. 5.1 (closed **and connected** language), Props. 6.3/6.5 (star locality; name-freedom), Prop. 7.3 (orbit pruning returns `w*_c`); compiles with `pdflatex` |
| 3 | `.claude/notes/2026-09-06-isal-kb-w1/summary.md` | the wave record: every agent, verdict, intervention, defect, merge, job id, and the user's rulings verbatim |
| 4 | `docs/article/DEVELOPMENT/T-KB/` | the ledger scope: what is open, in progress, closed |
| 5 | `docs/article/D_ART3/prose.md` §2–§4, §6, §11 | the storyline, rewritten today for the Isal word (numbers marked *pending* where the campaign run must fill them) |
| 6 | `docs/article/DEVELOPMENT/DECISIONS.md` D-ART4, D-TA2 | the binding decisions; D-TA2 is untouched (`w*_c` unchanged) |
| 7 | the wave logs `.claude/notes/2026-09-0{6,7}-isal-kb-w{1,2,3,4,5}/*.md` | per-agent detail (numbers, tests, follow-ups) |

## 2. Standing rules (the author's, in session)

1. **C++ only in the article.** Every arm in a final table runs on the C++
   engine. The Python engines are references and guards, never results.
2. **No heavy local runs.** The workstation went out of memory once; every
   measurement runs on Picasso. A local analyzer run on the harvested rows is
   light but was declined once — ask before running anything heavier than a
   test file locally.
3. **At most 2 Opus subagents at once; Opus only for implementation and
   monitoring;** Sonnet for briefings and operations; `model:` passed
   explicitly on every spawn (the environment sets `CLAUDE_CODE_SUBAGENT_MODEL=sonnet`).
4. **Worktrees + cloned envs** for every implementation agent (`CLAUDE.md`
   §Environment hazard): `conda create -y -n isalhg-<slug> --clone isalhg` and
   `pip install -e ".[dev]"` inside the worktree; use only that env's python.
5. **Commits** on `feature/isal-kb-word`, conventional, each ending with
   `Claude-Session: https://claude.ai/code/session_01F3KtB1s4dXGiNVyyaHfsix`
   (replace with your own session trailer).
6. **The parallel-agents skill** governs waves: file-disjoint ownership,
   committed work logs, verification against the diff before merge, `--no-ff`
   merges from the **main checkout** (a merge run from inside a worktree is a
   no-op there — it happened once).
7. **Report failures with the same directness as successes**; the pre-stated
   negatives (RQ4/RQ5 at the certificate's level) go to the supplement.

## 3. What is running on Picasso (results root on HOME: `~/results/IEEETKDE/`)

| job | experiment | config | what | state at handoff |
|---|---|---|---|---|
| 2247394 (array, 48 tasks) + 2247395 (recovery sweep, `afterany`) | `RQ1_addressing/addressing` | `configs/rq1.yaml` (all arms except `wstar_rank`) | the campaign RQ1 | ~22 completed, 8 OUT_OF_MEMORY (all started before the memory guard was synced at 15:18; the sweep redoes their units under the fix), 16 running |
| 2248782 (recovery sweep of the cancelled 2248781) | `RQ1_addressing/addressing_rank` | `configs/rq1_rank.yaml` (`wstar_rank`, `nauty_cert`, `nauty_cert_rows`) | the rank arm on the same units | 6/8 completed |
| 2248907 (array, 16 tasks) + 2248908 (sweep) | `RQ1_addressing/addressing_cpp` | `configs/rq1_cpp.yaml` (`wstar_orbit`, `isal_ow_*`, the two certificate arms) | C++ timing (M3) + full coverage for the orbit and ordered-walk arms | 12/16 completed |

The cluster tree is `~/fscratch/repos/IsalHG-tkde` (synced by
`scripts/tkde/sync_to_picasso.sh`, which rebuilds the extension on the login
node; no `.git` there). FSCRATCH is over its file-count soft quota (results
go to HOME on purpose). Launch pattern for any RQ1 experiment:

```bash
ssh picasso 'REPO=/mnt/home/users/tic_163_uma/mpascual/fscratch/repos/IsalHG-tkde; cd "$REPO" && \
  RQ1_CONFIG="$REPO/experiments/tkde/configs/<config>.yaml" REPO_DIR="$REPO" bash slurm/tkde/rq1_launcher.sh --smoke'   # then without --smoke
```

## 4. Set up the monitor (first thing)

One persistent watch that emits only on job-state changes and ends when all
groups are terminal (the previous session's exact command; adjust the ids):

```bash
prev=""; while true; do st=$(timeout 60 ssh -o BatchMode=yes picasso 'for j in 2247394 2247395 2248782 2248907 2248908; do echo "$j: $(sacct -j $j -X -n -P -o State 2>/dev/null | sort | uniq -c | tr -s " " | tr "\n" ";")"; done' 2>/dev/null || echo "ssh failed"); if [ "$st" != "$prev" ] && [ "$st" != "ssh failed" ]; then files=$(timeout 60 ssh -o BatchMode=yes picasso 'echo "addressing=$(ls ~/results/IEEETKDE/RQ1_addressing/addressing/ 2>/dev/null | wc -l) rank=$(ls ~/results/IEEETKDE/RQ1_addressing/addressing_rank/ 2>/dev/null | wc -l) cpp=$(ls ~/results/IEEETKDE/RQ1_addressing/addressing_cpp/ 2>/dev/null | wc -l)"' 2>/dev/null); echo "$(date +%H:%M) $(echo "$st" | tr '\n' ' ') files: $files"; prev="$st"; fi; if [ "$st" != "ssh failed" ] && ! echo "$st" | grep -q "RUNNING\|PENDING"; then echo "ALL RQ1 JOBS TERMINAL"; break; fi; sleep 300; done
```

Arm it with the `Monitor` tool (`persistent: true`). Do not include file
counts in the change key (they change every few minutes).

## 5. The next steps, in order

### 5.1 Harvest → merge → analyze → the RQ1 table (when all five groups are terminal)

1. Harvest the three experiments into a **separate** root so the frozen
   campaign record on the drive is not muddled:
   ```bash
   D=/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE_isal/RQ1_addressing
   mkdir -p "$D" && for e in addressing addressing_rank addressing_cpp; do
     rsync -a picasso:results/IEEETKDE/RQ1_addressing/$e/ "$D/$e/"; done
   ```
   (`scripts/tkde/harvest_from_picasso.sh RQ1_addressing` would write into the
   campaign's directory; do not use it for these.)
2. Merge with one source per arm (tool committed; `--out-root` keeps the
   analyzer's default experiment name):
   ```bash
   python -m experiments.tkde.merge_rq1_experiments \
     --root  /media/.../results/IEEETKDE_isal \
     --experiments addressing addressing_rank addressing_cpp \
     --prefer wstar_rank=addressing_rank wstar_orbit=addressing_cpp \
              isal_ow_struct=addressing_cpp isal_ow_rank=addressing_cpp isal_ow_rank0=addressing_cpp \
     --out addressing --out-root /media/.../results/IEEETKDE_isal_merged
   ```
   Then `python -m experiments.tkde.analyze_rq1 --root /media/.../results/IEEETKDE_isal_merged`
   (ask before running locally, or run it on the cluster login node).
   Check `merge_manifest.json`; the certificate arms come from the campaign
   experiment, the Isal arms from the C++ runs.
3. Verify the join: the three experiments share `(collection, seed, base_id,
   edit_kind, edit_idx)` for M1 — assert equal edit sets per unit before
   trusting paired statistics. The rows carry `git_sha`/`host_cpu` provenance.
4. Read `tables.md`: M0 per arm (must be 0/0/0 for every Isal arm); M1 per
   `(collection, edit_kind, regime)` — `d_instr` medians, the ≤ 2 fraction,
   `zero_shift`, `aut_bucket`; M3 cost and censoring per `(arm, m, |Aut|)`;
   M4 ρ vs both certificate tokenisations. Apply the **pre-registered
   selection rule** (design §3): among exact, uncensored arms, the highest
   constant-preserved "within ≤ 2 instructions" fraction, ties by median.
   Expected from the preview: the greedy walks win deletions outright; on
   insertions `fact_rank` (the record) and the certificate rows lead; the
   ordered walk loses insertions by its ordering, not by the machine.
5. Persist under `results/IEEETKDE/RQ1_isal/` (the brief's deliverable 3):
   `tables.md`, `stats.json`, `manifest.json`, with the three source
   experiments and the merge manifest.

### 5.2 The representation decision (with the author/PI)

Bring the table and the diagnosis; the candidate order is
`wstar_rank` (deterministic, polynomial, displacement-aware, C++) →
`w*_c` orbit-pruned (the frozen form, now computable on symmetric inputs;
its own R2 table is in the cpp-orbit log: wd50k66 98/100 of the
highest-|Aut| censored members complete, ndc_classes 48/100 because its tail
is arity-10 displacement) → the ordered walk (order-only ablation with a
named mechanism). Points reserved for the PI: (i) which canonical program
the tables run on (D-TA2 untouched either way); (ii) the nauty sentence
(design §7: order, oracle, or both).

### 5.3 RQ2–RQ7 with the Isal arms (ledger T-KBf)

The runners already accept the arms (wave 2). Before submitting:
- **Budgeting audit.** Every place that calls an Isal engine in-process
  must fork under a budget or be provably ms: RQ1 and RQ2 are fixed
  (`BUDGETED_ARMS`, `POINTER_ARMS`); RQ7's sweep per-instance path had no
  `engine_word` call at last grep — audit `rq7.py` before the sweep; the
  N×N **matrices** for `wstar_rank` need a censoring-aware fingerprint
  step (arity-10 members censor at 60 s; the fingerprint-first route in
  `toolkit/matrix.py` is unbudgeted) — decide the policy (drop censored
  members from the matrix and report them per L15) and implement it.
- Also fix `rq3.run_guarded` (no fork-health guard; found by the harness
  agent) and drop `fact_rank_roles` from any table (fails M0, 43/60).
- Order: matrices (`matrices_launcher.sh`) → RQ2 → RQ3 (pilot one NDC cell
  first: the consensus canonicalises hundreds of candidates) → RQ4 → RQ5 →
  RQ6 (`ow_ngram` / the Isal generator; validity **and connectivity** 1,000/1,000
  already measured locally) → RQ7 (with the `|Aut|` axis). Harvest each.
- Expected readings are pre-stated in design §5 and D-ART4 (3): RQ2 exact +
  metric + polynomial; RQ3 carries over with connected interiors; RQ4/RQ5
  at the certificate's level → supplement; RQ6 stronger (connectivity by
  theorem); RQ7 the envelope moves from `|Aut|` to `m`.

### 5.4 Writing (ledger T-KBg)

- The **one-page PI reading** (brief deliverable 4): which variant, why, cost,
  what it still cannot do (R-list updated: R1 partially lifted — deletions;
  insertions over existing arguments remain the certificate's/fact list's;
  R2 lifted in C++; R3 stated with Prop. 5.1; R4 filed as T-KBa; R5 kept;
  R6 no longer conceded for the ordered/greedy programs, whose cost is one
  nauty call), and the nauty sentence.
- `prose.md`: fill the *pending* numbers; `START_HERE.md` §0/§0.1/§6.0 are
  superseded by the handoff pointer added today; `DESIGN.md` G1 (the
  fact-rank definition) becomes the Isal word; apply the `humanizer` skill to
  any passage over 200 words.
- The proof file: PI review; consider a `research-rigor` pass on §6
  (locality) before it goes out.

## 6. Defects found and fixed today (do not re-find them)

| defect | fix | commit |
|---|---|---|
| Python `canonical_rank` applied ranks at depth 0 only (edge-order dependent, exponential below the root) | ranks threaded through every frame; edge-order invariance pinned | wave 3 (`3ec5c16` in its branch) |
| Python engines materialise `(2r+1)^k` tuples per radius and cache them: 9.8 GB in a 60 s budget | guard on `Σ_{r<n}(2r+1)^{k_eff} ≤ 2e6` and `k_eff ≤ 4` | `2ccc9fa`, `e40b327` |
| `wstar_rank` ran in-process, unbudgeted (12-min hang on an arity-10 member) | budgeted arm in RQ1 and RQ2 | `7ed77aa`, `30067fe` |
| runner hardcoded the experiment name → a second experiment's rows were written to an unlinked node-scratch directory and lost | `experiment_name(config)` drives paths and stamps | `cf391fe` |
| launchers defaulted to retired per-agent remote trees | shared tree default | `17355b7` |
| a forked child deadlocks after any in-process C++ canonicalisation in the parent (false censoring) | `cpp_fork_is_healthy` canary in `engine_word` (harness wave); `rq3.run_guarded` still unguarded | wave 2 |

## 7. Open follow-ups (ledger)

T-KBa roles (later) · T-KBb/T-KBd code done, closed when RQ7/M3 re-measure
lands · T-KBc nauty-free ordered walk (future work) · T-KBe RQ1 harvest,
table, decision · T-KBf RQ2–RQ7 swap · T-KBg prose + PI reading · the
`pynauty_levi` vs `w*_c` disagreement on inputs declaring different
vocabulary sizes (fingerprint contract, PI) · trivial-stabiliser pre-filter
for the orbit oracle (speed only) · `analyze_rq1.py` hardcodes `EXPERIMENT`
(harmless with `--out-root`).

## 8. Which model

The reasoning-bound part — the diagnosis of the search as the common root,
the ordered walk and its move rule, the four-cell reading of nauty's roles,
Theorem C and the locality propositions, the bit-exactness gates for three
C++ ports, and the diagnoses of the four defects — is done and recorded.
What remains is orchestration (jobs, harvests, merges), analysis against a
pre-registered rule, an encoder swap across seven runners with two
budgeting decisions, and writing. **Opus at xhigh is sufficient** for all of
it; use Sonnet for the reading and operations steps. Re-engage a
top-tier session only if the RQ1 table contradicts the preview in a way
that reopens the design (for instance, if the rank-keyed walk does not
track `w*_c`'s locality) — then the design record's §9 is where the
re-think starts.
