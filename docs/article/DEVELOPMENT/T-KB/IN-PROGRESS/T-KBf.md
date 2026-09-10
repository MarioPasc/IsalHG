# T-KBf — RQ2–RQ7 with the Isal arms (the encoder swap)

**Status:** IN-PROGRESS (2026-09-09 08:47 CEST) · declared 2026-09-07 22:10 CEST by the Isal-refinement
orchestrator (handoff §5.3). Depends on T-KBe's decision for the headline
arm; the runs can start with both C++ candidates (`wstar_rank`,
`isal_ow_struct`) and `wstar_orbit` where budgets allow.

## What

- **Budgeting audit before any submission:** every in-process Isal engine
  call must fork under a budget or be provably milliseconds. Fixed: RQ1
  (`BUDGETED_ARMS`), RQ2 (`POINTER_ARMS`). To audit: the RQ7 sweep
  per-instance path (no `engine_word` at last grep); the N×N matrices for
  `wstar_rank` (fingerprint-first route in `toolkit/matrix.py` is
  unbudgeted; arity-10 members censor at 60 s) — implement a
  censoring-aware fingerprint step and report censored members per L15;
  `rq3.run_guarded` lacks the fork-health canary.
- Drop `fact_rank_roles` from every table (fails M0 invariance 43/60).
- Order: matrices → RQ2 → RQ3 (pilot one NDC cell first) → RQ4 → RQ5 → RQ6
  (the Isal `ow_ngram` generator; validity and connectivity 1,000/1,000
  measured locally) → RQ7 (with the `|Aut|` axis). Harvest each into the
  results root; persist tables.
- Pre-stated readings: RQ2 exact/metric/polynomial; RQ3 carries over with
  connected interiors; RQ4/RQ5 at the certificate's level → supplement
  (author ruling); RQ6 stronger; RQ7 the envelope from `|Aut|` to `m`.

## Acceptance

One Isal row (C++ engine) in every RQ table, with provenance stamps, under
`results/IEEETKDE/`; the negatives reported with the same directness.

---

## The two research decisions, settled 2026-09-09 08:47 CEST

Both were left unwired by the wave-6 budgeting audit and named in
`HANDOFF_2026-09-09_isal.md` §4.1 as things to decide before RQ3. Neither is
PI-level: the decision record answers the second outright and constrains the
first. Adversarially reviewed by the `[IsalHG-Fable]` session, which corrected
one of the three reasons and added the disclosure set, the third option and the
per-method census requirement; its corrections are folded in below.

### D-KBf1 — RQ3 censors at the **collection**, not the member

An arm that cannot canonicalise every member of a collection reports **no**
medoid for that collection: the row is `censored = 1` with `n_censored_members`
recorded. Every cross-arm number restricts to the collections the published
arms all completed (handoff rule 9, the RQ1 `restrict_to_common_units`
convention one level up).

*Why the collection is the unit.*

1. **The certificate is a statement about the N members.** Prop 3's
   `LB = Σ_{i<j} d(K_i,K_j)/(N−1) ≤ OPT ≤ cost(M)` bounds the optimum over
   *that* collection. Recomputed over a survivor subset it certifies a
   different object while being printed under a column headed "certified
   ratio" — a false guarantee, and the guarantee is precisely what RQ3 claims
   over the competitors.
2. **The medoid is `argmin` over the members.** Dropping members changes both
   the candidate set and the objective, so two arms scored on different member
   subsets of one collection are not answering the same question — the defect,
   one level down, that produced this campaign's three retracted directional
   claims (design §9 item 8).
3. **The measured cost lands on Corpus B only.** All 77 `wstar_orbit`
   censorings at 60 s have max arity ≥ 7 (ndc: 69 at k=10, 1 at k=9; wd50k: 6
   at k=7, 1 at k=8) and n ≥ 10; Corpus A's window is `4 ≤ n ≤ 12`,
   `4 ≤ m ≤ 12`, max arity ≤ 6. **Checked rather than assumed** (Fable's
   challenge): an inserted fact's arity is
   `max(2, min(rng.choice(_arity_pool(record)), record.n, envelope.k_max))`
   with `_arity_pool` = the arities *already present in the record*
   (`src/isalhg/datasets/kb/ladders.py:60`, applied at `:96`, `:176`, `:315`),
   so a Corpus A variant cannot exceed its source's maximum arity, and the
   consensus candidates transfer facts between members of that same
   collection. Corpus A is therefore expected to censor 0 — *expected*, not
   proved, since search cost is not monotone in `(n, m, k)`; the census runs
   there too and the number is reported.

*Direction of the bias, disclosed rather than denied.* Collection censoring
removes the arity-10 classes, plausibly the ones whose quarters change most,
which raises **every** arm's recovery rate — ours and the competitors' alike,
since the common-set rule removes the same collections from all of them. It
flatters the table's absolute numbers, not our arm relative to the others.
Member-level dropping is not less biased, only differently: within a class the
censoring hits several quarters (7 of 25, 6 of 16, 4 of 7), and if those are
the later, larger quarters they are the ones closest to the truth quarter, so
a survivor medoid would lose its best candidates for a reason unrelated to the
distance's quality. (A) is the unit where the bias is shared and measurable.

*Three disclosures the RQ3 caption must carry*, in this order:
1. "every arm is scored on the collections the Isal engine completed at 60 s;
   the restriction is ours, since the certificate completes everything" — the
   RQ1 sentence, reused;
2. for every uncensored arm, its score on the **full** Corpus B beside its
   score on the common set, so the reader sees whether the removed classes
   were harder;
3. the **survivor-medoid sensitivity row** (below), so the reader sees what
   member-level dropping would have given us.

*The third option, adopted as a supplement row and never in the main table.*
On the censored collections, `wstar_orbit`'s medoid over the survivors, scored
on the task axis, **ratio column suppressed**, labelled "not certified, N′ of
N members". It costs nothing (the survivors' words already exist) and it is
the only number that bounds the flattery directly. Defining Corpus B as "the
classes all arms complete" is **rejected**: that launders censoring into the
corpus definition, which is what L15 exists to forbid.

*Census granularity.* Censoring is recorded per **(collection, method)**, not
per (collection, arm): the coverage consensus canonicalises hundreds of
candidates per collection and an arity-10 class is where they are most
expensive, so a collection can be medoid-complete and consensus-censored. The
row schema already carries `censored` on both the medoid and the consensus
rows (`rq3.py` 490/511/527 and 580/638); what is missing is the medoid's
budget.

*Budget.* The RQ3 medoid screen is the **same 60 s per member** as RQ1 and as
`matrices.yaml`, or the censoring census is not the one the reader met in RQ1.
`rq3.yaml` gains `fingerprint_budget_s: 60.0`; the consensus keeps its own
`consensus_budget_s: 1800` (corpus B), which is a per-call, not per-member,
guard.

### D-KBf1a — the Corpus B reporting threshold, pre-registered before the count

Committed to disk **before** the 70 censored member ids are joined to the
series census. Corpus B was thin before censoring (the risk register records
15 classes with runs ≥ 3 and 2 with ≥ 5 in the constant-preserving regime), so
the threshold applies **per regime row**, not to Corpus B as a whole.

A regime row is **scored** only if both hold:

- **(a) absolute** — at least **20 collections** in the common set. The Wilson
  95 % half-width of a recovery rate near 0.5 at n = 20 is ≈ 0.21; below that
  a rate cannot separate one half from one third, the size of the effect RQ3
  argues about.
- **(b) relative** — the common set retains at least **two thirds** of the
  regime's pre-censoring collections. Below that the restricted set is no
  longer "the natural NDC series" but a selected sub-series, and the reader is
  entitled to the competitors' numbers on the series as defined.

If either fails, the row is a **yield statement** — collections completed /
defined, by `T` bucket and by the class's maximum arity (L15) — the uncensored
arms' full-corpus scores are printed, the Isal row reads "censored, n of N",
and **the paired comparison is not made**.

### D-KBf2 — RQ2/RQ4/RQ5 tolerate a censored arm's short matrix

**Not a research decision**: L15 ("DNFs under a fixed per-item budget are
dropped and counted, yield reported per size bucket, label-correlated
censoring stated") fixes the mechanics, and the item in RQ2/RQ4/RQ5 *is* the
member. `matrices.yaml`'s header already declares the behaviour, and
`matrices.py` already writes the sidecar; what is missing is the consumer.

- The matrix and its manifest describe the **survivors** (`member_order_sha1`
  and `n` are over `kept_ids`, `matrices.py:733,753`), while `rq4.py:563`,
  `rq5.py:579` and `rq2.py:363–386` validate against the **full** frozen order
  and therefore read a censored arm as a cache miss. `read_censoring`
  (`matrices.py:212`) exists for exactly this and has no consumer outside
  `matrices.py`.
- Fix: a loader that, when the sidecar is present, validates against the kept
  order and returns `(matrix, kept_ids)`; consumers align **by member id**;
  every cross-arm statistic is computed on the **intersection** of survivor
  sets, with the per-arm census printed.

*L15's third clause, which bites in RQ4 and RQ5* (Fable): a corrupted member
carries one more fact than its clean original, so its displacement cost is
higher and it is marginally likelier to censor. An AUC computed on a set from
which the positives were preferentially removed is not the AUC claimed.
**Pre-registered:** RQ4 prints the censoring rate **by label (corrupted vs
clean) and by corruption type**; RQ5 prints it **by Wikidata type**, since
arity-heavy types will censor more. Mechanics unchanged; the caption changes.

### D-KBf3 — `wstar_orbit` must have an `N×N` matrix (defect found)

`ISAL_MATRIX_ARMS` (`matrices.py:101`) excludes `wstar_orbit` and
`isalhg_levenshtein` on the rationale that "a budget is a per-member notion
that a whole-matrix build has nowhere to record". **Wave 6 made that
obsolete**: `BUDGETED_MATRIX_ARMS = CPP_ENGINE_ARMS` *includes* `wstar_orbit`,
`arm_fingerprint_screen` supplies the per-member screen, `build_matrix_censored`
applies it and the `<arm>.censored.json` sidecar is exactly the place to record
it. Left as is, **the paper's representation under D-ART5 would have no row in
RQ4 or RQ5.**

Cost, measured from the frozen RQ1 M3 rows rather than estimated (screen ≈ the
per-member canonicalisation, censored members charged the full 60 s):

| arm | corpus | members | censored | median | p99 | screen total |
|---|---|---|---|---|---|---|
| `wstar_orbit` | wd50k66 | 3,988 | 7 | 5.47 ms | 2.13 s | ≈ 1,002 s |
| `wstar_orbit` | ndc_classes | 1,381 | 70 | 6.83 ms | 43.18 s | ≈ 5,823 s |
| `isal_ow_struct` | wd50k66 / ndc | 3,988 / 1,381 | 0 / 0 | 0.54 / 0.53 ms | — | 2 s / 1 s |
| `nauty_cert_rows` | wd50k66 / ndc | 3,988 / 1,381 | 0 / 0 | 0.14 ms | — | ≈ 1 s |

≈ 1.9 core-hours of screen for both corpora, plus the build's recomputation of
the survivors — affordable, and dominated by the 77 × 60 s the censored
members spend. `wstar_orbit` is added to the matrix arms and the stale comment
corrected.

### The arm set for RQ2–RQ7 (D-ART5, handoff §4.1)

`wstar_orbit` (the one Isal row) · `nauty_cert` + `nauty_cert_rows` (both
tokenisations, everywhere) · `fact_rank` (the retired comparator's record,
D-ART4 note (c); supplement only) · `wl_l1`, `netlsd`, `hpd_jsd`,
`bipartite_ged_path`, `bipartite_ged_assign`, `size_l1`, `degree_seq_l1`.
**Out:** `wstar_rank` (RQ1 only), `isal_ow_rank`, `isal_ow_rank0` (RQ1 policy
ablation), `fact_rank_roles` (fails M0). `isal_ow_struct` appears **only in
RQ7**, as the deterministic cost floor.

### D-KBf1a applied — the count, taken after the rule was committed

Rule committed at `6ebbc2f`; the join was run afterwards
(`scripts/` scratch, `corpora.consecutive_runs(ndc_classes, 4)` against the
70 censored `wstar_orbit` member ids of the frozen M3 rows).

| | units | with a censored collection member | surviving | retention |
|---|---|---|---|---|
| Corpus B, all runs `T ≥ 4` | **69** | 6 | **63** | **0.913** |
| `T ≥ 5` subset | 46 | 6 | **40** | 0.870 |

**Both conditions hold on both rows** — (a) 63 ≥ 20 and 40 ≥ 20; (b) 0.913 and
0.870, both ≥ 2/3 — so Corpus B is **scored**, with the three disclosures, not
reduced to a yield statement.

The footprint is much narrower than the 27-of-171 class figure implies: the
censoring touches **3 drug classes** (470, 471, 472), each contributing two
maximal runs, because most of the 27 censored classes have no run of four
consecutive encodable quarters at all. The survivor-medoid sensitivity row
therefore covers 6 units.

Still open at run time, and governed by the same rule: the
**constant-preserving regime row**, whose thinness predates censoring (128 of
528 consecutive pairs are constant-preserving, so runs all of whose pairs
preserve the constant set are rare). It is counted when the RQ3 analyzer
splits the regimes, and falls to a yield statement if either condition fails.

---

## Execution log

### Cluster tree synced (2026-09-09 08:45, re-synced 08:59 and 09:0x)

`scripts/tkde/sync_to_picasso.sh` at `80472bb`, then again at `d53b686` and
`6c8d2a4`. Each run rebuilt the extension on the login node and verified it:
`PIP EXIT 0`, `.so` mtime post-dating the sync, `cpp == python` on the Fano
plane. Safe because no job was running — `squeue` showed only the long-standing
admin-held 2132239 (PD).

**Operational rule for the rest of the campaign:** the extension lives in the
shared conda env (`.../conda_envs/isalhg-tkde/lib/python3.11/site-packages/`),
so a rebuild swaps the `.so` under any *running* task. Nothing ahead touches
C++, so every further deploy uses **`sync_to_picasso.sh --no-build`** unless
`squeue` shows no running campaign job.

### D-KBf3 executed

`ISAL_MATRIX_ARMS = ("wstar_orbit", "isal_ow_struct")`; `matrices.yaml` on the
D-ART5 arm set; 31 units (was 37). 28 new tests pin the screen/matrix
agreement, 4 pin the arm set. Suite baseline verified rather than assumed: the
three affected test files give **8 failed / 151 passed both before and after**,
the identical eight pre-existing failures; the one failure the change caused
was the frozen-arm count, fixed at `6c8d2a4`.

**The objection that had to be cleared first.** `fingerprint()` resolves `k` as
`required_k(H)` and the seed-prefix flag per member; `matrix()` resolves `k` as
the corpus maximum and the flag over the corpus. If those differ, the screen
certifies a member for a search the matrix then runs differently and
*unbudgeted* — the twelve-minute-hang class of defect. Measured on both
corpora rather than argued:

- **k**: 0 word mismatches over 43 ndc members stratified across
  `required_k` 2–9 against the corpus `k` of 10; cost ratio corpus-k /
  per-member-k **median 0.96, max 1.03**. The encoder never names a pointer
  index above the widest edge's, so surplus pointers are neither written nor
  searched.
- **prefix flag**: uniform per corpus — every ndc member carries 4 vertex
  labels, every wd50k66 member carries 1 — so the member-level and
  corpus-level flags agree on every member of both.

So the screen's census *is* the matrix's census, and it is RQ1's: `rq1.py:682`
also uses `required_k(H)` per member. The doubled computation
(`build_matrix_censored` recomputes the survivors) is real, bounded and
deliberate. Poisoning was already handled: `_build_censored_child` runs the
whole build in a forked child that dies, and RQ4/RQ5 read cached `.npy` rather
than building.

### Submitted

| job | what | submitted | note |
|---|---|---|---|
| **2264827** | `tkde-matrices`, 31 units, 32 cpus / 64 GB / 12 h | 2026-09-09 ~09:05 CEST | `--test-only` estimated a start of 2026-09-10T16:28 — the queue holds 4,274 jobs |

Monitor armed on job state only (never on file counts), self-terminating on the
terminal condition.

### Provenance obligation for the matrices harvest

The `k`-invariance measurement is not a curiosity: it is **the fact that
licenses RQ4/RQ5's budget to be read from the RQ1 census**. Without it, a
reviewer is entitled to ask why a matrix built at the corpus `k` may be censored
by a screen run at each member's own `k`. It must therefore travel with the
matrices, not only with this ledger entry.

Job **2264827** started before this was written, so its `config.json` stamp
does not carry the citation. Two follow-ups, both cheap:

1. At harvest, attach to the matrices run record: *"the censoring census is the
   per-member screen's; screen and build agree because `w°`/`w*_c` are
   invariant to surplus pointers (0 mismatches / 43 members, `required_k` 2–9
   at corpus `k` = 10, cost ratio 0.96–1.03) and the vertex-label count is
   uniform per corpus (ndc 4, wd50k66 1); pinned by
   `tests/unit/metric_space/test_isal_engine_k_invariance.py`."*
2. Fold the same sentence into `matrices.py`'s module docstring at the merge of
   the RQ2–RQ5 consumer wave, so every later run stamps it. Not done inline
   here: `matrices.py` is held by the consumer agent's worktree.

Raised by `[IsalHG-Fable]`, which also conceded the reuse fix and asked for its
precise form to be filed rather than applied — parked as **T-KBl**, landing
window with or after T-KBj, never between RQ1 and RQ2.

### Job 2264827 FAILED in 5 s — the nested-budget defect, and what it says about the smoke

```
experiments.tkde.config.TkdeConfigError: budgeted matrix unit
wd50k66/wstar_orbit did not produce a matrix:
AssertionError: daemonic processes are not allowed to have children
```

**Mechanism.** The matrices job nests two budgets: `run_unit` forks a child for
the unit (so the build's in-process canonicalisation cannot poison the runner),
and inside it `build_matrix_censored` forks one screen per member.
`run_with_budget_detail` created every child with `daemon=True` — correct for a
*leaf*, since it ties the child's lifetime to its parent, and wrong for a
*supervisor*, since Python forbids a daemonic process from having children. The
unit died on its first screen. Unit 0 (`fact_rank`) was a cache hit, so nothing
on disk was touched and no compute was wasted.

**Fix** (`c6a9a8c`): `daemon` is a keyword on both budget entry points,
defaulting to `True`; the single supervisor call site passes `False`. A
non-daemonic child is still killed on time-out, and SLURM's cgroup reaps it if
the runner dies outright.

**Why it reached a submission.** `BUDGETED_MATRIX_ARMS` has contained
`wstar_rank` since wave 3, but **no budgeted arm was ever in `DEFAULT_SPECS`**,
so the nesting existed from wave 6 and had never executed. Wave 6 unit-tested
both budget levels in isolation; composition is the only place the defect
lives. Two guards now:

1. `tests/experiments_tkde/test_budget_nesting.py` — 5 tests reproducing the
   failure as behaviour and pinning the fix, the default, and that opting out
   of `daemon` does not weaken the time-out.
2. `wstar_orbit` added to `SMOKE_SPECS`. **A smoke that omits the only budgeted
   arm cannot exercise the mechanism the campaign depends on**, which is
   exactly how this reached the cluster. The rule the smoke encodes is *cover
   every code path the real run takes*, not every arm.

Verified on the real path before resubmitting: the local 40-member smoke builds
**11/11 units**, both `wstar_orbit` matrices included (ndc 5.7 s). No sidecar
was written because nothing censored at that size — the censored branch is
covered synthetically in the consumer wave.

**Resubmitted as 2264831** at `c6a9a8c`, deployed with `--no-build` (Python-only
change; the extension is current from the 09:07 rebuild).

### The censoring branch pre-tested before the cluster reached it

Job 2264831 hits `ndc_classes/wstar_orbit` — the first real censoring build in
the campaign's history — about half an hour after launch. The branch was
exercised locally first, at a 4 ms budget to force censoring:

| unit | censored | result |
|---|---|---|
| `ndc_classes/wstar_orbit` | 12 of 40 | 28×28 matrix; sidecar `n_requested 40, n_censored 12, member_ids 28`; manifest `n = 28` over the kept order |
| `wd50k66/wstar_orbit` | **40 of 40** | `(0, 0)` matrix, `manifest.n = 0`, **reported as success** |

Two things settled. The sidecar **partitions the frozen order** exactly as the
consumer loader's assertion requires, so D-KBf2's design is sound against the
real artefact rather than only against synthetic frames. And the fork canary
**survived 12 censorings inside the non-daemonic supervisor child** — the risk
that `guarded_budget_call`'s `cpp_fork_is_healthy(recheck=True)` would fire on a
censored screen and kill the unit does not materialise, which is what licenses
the 70 censorings the ndc unit is about to take.

The degenerate row is a genuine silent-wrong-result hazard and is parked as
**T-KBm** rather than fixed inline: the campaign's 60 s budget censors 7 of
3,988 and 70 of 1,381, so it is not on the submission path, and changing
censoring behaviour mid-campaign would break census comparability.

### Matrices 2264831 COMPLETED (3:10:11, 31/31 units) — and it re-measures the census

The `wstar_orbit` screen inside the matrix build is an **independent re-run** of
the RQ1 M3 census, so it tests the k-invariance argument of D-KBf3 at campaign
scale rather than on 43 sampled members.

| corpus | matrices job | RQ1 M3 | relation |
|---|---|---|---|
| ndc_classes | 70 of 1,381 | 70 | **identical member ids** |
| wd50k66 | 5 of 3,988 | 7 | **strict subset** — `Q183066`, `Q707986` completed |
| wd50k100 | 11 of 1,837 | — | new collection |

**This confirms the argument rather than straining it.** A screen running a
*different*, harder search (the corpus `k`) would censor a **superset**, and
ndc — the corpus with the whole arity-10 tail — would not match to the id. A
strict subset on the other corpus is the signature of the same search meeting a
less loaded node.

**A correction to the record.** T-KBe reports `wstar_orbit` as stable at 77
across four reads while the unpruned engine drifted 357/354/356/353. Those were
four reads of **one run's rows**, not four runs. This is the first independent
re-run, and the arm does drift — by 2 on wd50k66, none on ndc. That is exactly
what its near-boundary mass predicts (6 completions in [55, 60) s), so the drift
model stands; only the claim "the published arms never moved" needs the
qualifier *within a run*. Nothing published moves: `d_I` values are identical
(same seeds, same words), and censoring decides only which units enter a table.
The two members are the smallest of the seven (n=22 m=16 and n=20 m=12).

`ndc_substances` carries matrices for the cheap arms from an earlier campaign
but **no `wstar_orbit`**, so RQ2's own budgeted build — the path fixed at
`afab7c5` — is exercised on exactly the collection it was written for.

### Submitted

| job | what | note |
|---|---|---|
| 2264827 | matrices | FAILED in 5 s, nested-budget defect |
| **2264831** | matrices, 31 units | **COMPLETED** 3:10:11 |
| **2265308** | **RQ3 pilot** — one NDC cell | D-ART4 note (b): pilot before the full RQ3, since the consensus canonicalises hundreds of candidates per cell and NDC sources are symmetric |
| **2265309** | RQ2 non-census kinds | exact0, bipartite, oracle, hypercot |
| **2265310** | RQ2 census array | `afterok:2264831`, dependency read back and verified |

### The RQ3 pilot earned its place — it caught a silent stale-row defect (T-KBn)

D-ART4 note (b) asks for one NDC cell before the full RQ3, on the grounds that
the consensus canonicalises hundreds of candidates per cell. It found something
else, and worse.

Job 2265308 completed in 5 minutes with 0 errors and looked healthy. It was not:

| | pilot on the dirty tree | fresh local run |
|---|---|---|
| rows | 44 variants / 20 natural | **58 / 27** |
| wall-clock | 0.3 s | **80 s** |
| `wstar_orbit` rows | **0** | matrix built, n=20, 1.32 s |
| `nauty_cert_rows`, `bipartite_ged_assign` | **0** | present |
| persisted `config.json` | the **new** 11-arm list | the new list |

RQ3 decides what to skip by reading its own **untagged** aggregated row files,
so a changed arm set leaves every unit "done": it re-aggregated the 2026-09-05
rows and wrote a fresh `config.json` naming arms those rows do not contain. On
the real tree (49,027 pre-D-ART5 rows) the full RQ3 would have produced a
complete, plausible table **with no Isal row at all**, over a provenance stamp
saying otherwise.

**Scope of the hazard, checked per runner rather than assumed.** Only RQ3 calls
`_done_units`. RQ4/RQ5/RQ6/RQ7 do not skip; but RQ4/RQ5/RQ6 do not tag either,
so they would *overwrite* the pre-D-ART5 rows D-ART4 (1) requires be kept. RQ2
is correct as it stands — it writes `rows_census__<tag>-<unit>.csv`, and today's
`ndc_classes-wstar_orbit` sits beside the untagged Sep-5 files rather than
replacing them.

**Operational fix, following this campaign's own precedent.** RQ3–RQ7 run into a
clean root `~/results/IEEETKDE_isal/` with `matrices` symlinked to the shared
build — the same separation T-KBe used for the RQ1 harvest
(`results/IEEETKDE_isal/RQ1_addressing/`, "not into the campaign's frozen
record"). Nothing is moved or deleted. The runner defect is filed as **T-KBn**.

**Submitted:** full RQ3 as **2265353** into the clean root. RQ2 (2265309 /
2265310) continues in the shared tree; its rows are tag-separable and its
census already carries `wstar_orbit`.

### D-KBf2 verified on real data (RQ5 smoke, job 2265369)

The consumer side was tested only on synthetic frames before this. The smoke
read the real `wstar_orbit` matrix with its sidecar and behaved as designed:

```
WARNING matrices  arm wstar_orbit on wd50k66: 5 of 3988 members censored by the matrices job
WARNING __main__  unit 11 (wd50k66_balanced__seed50000): 1 of 280 selected members censored;
                  clustering the rest
```

**The intersection is applied at the scoring level, not merely recorded.** Every
arm in the unit reports `n_members = 279`, `n_censored_members = 1` — including
the ten arms that censor nothing:

| arm | n_members | n_censored |
|---|---|---|
| `wstar_orbit` | 279 | 1 |
| `fact_rank`, `nauty_cert`, `nauty_cert_rows`, `wl_l1`, `netlsd`, `hpd_jsd`, `bipartite_ged_{path,assign}`, `size_l1`, `degree_seq_l1` | 279 each | 1 each |

So the uncensored arms are scored on exactly the members the Isal arm could
represent. This is rule 9 made structural, and it is the property whose absence
produced the three retracted directional claims of RQ1 (design §9 item 8): there,
each arm was scored on its own completed subset and an eyeballed ordering was an
artefact of the differing unit sets.

The D-ART5 arm set is present and complete — 11 arms, `wstar_orbit` among them,
no `wstar_rank`, no `isal_ow_*`.

**Submitted:** full RQ5 as **2265389**. RQ4's smoke (2265368) carries the more
delicate L15 requirement — the censoring rate by corrupted-vs-clean and by
corruption type — and gates the full RQ4.

### RQ4 smoke TIMEOUT (job 2265368) — the anomaly scoring is O(A·N) unbudgeted canonicalisations

The smoke spent its whole 30-minute wall on **one unit**
(`ndc_classes__spurious_fact_b1__seed40000`, 1,311 members, 11 arms), logging the
censoring line at 13:07:39 and nothing after.

**Mechanism.** `rq4.anomaly_rows` scores each anomaly against every member
through `_row_worker`'s
`[distance.pairwise(anomaly, other) for other in items]`, and the Isal engine's
`pairwise` **re-canonicalises both sides on every call**. So `wstar_orbit` pays
O(anomalies × N × 2) canonicalisations with no budget, on the corpus whose p99
is 43 s and 70 of whose 1,381 members never finish at 60 s. One of those hangs
the unit for ever.

**The fix was already written — for the wrong arm.** `anomaly_rows`' docstring
says it itself:

> "`fact_rank` is served from precomputed words (one encoding per member, then
> token Levenshtein) rather than through `pairwise`, which would re-derive the
> canonical labelling on both sides of every call."

`WORD_ARM = "fact_rank"` is the representation **D-ART4 retired**. The
optimisation was never extended to the representation that replaced it, so the
paper's own arm takes the slow path the comparator was spared. Generalising it
is delegated (wave `2026-09-09-isal-kb-w9`), together with budgeting the
canonicalisation and censoring an **anomaly** that does not finish — a case the
matrices job cannot cover, since an anomaly is a hypergraph that never passed
through it.

Caught because the RQ4 smoke was run before the full submission. The full RQ4
carries an 8-hour wall over 1,323 units; unfixed it would have burned it and
produced nothing.

### RQ3 Corpus A: the deletion variants violate R3 — measured 2026-09-09 14:2x

Job 2265353 censors `wstar_orbit` on **2,616 collections** in its first 647
units, and the pattern is a mechanism, not noise: **every censored cell is
`_del` or `_mix`; no `_ins` cell censors at all.**

**Cause: isolated constants, i.e. R3 — not cost.** Measured on 25 sampled
Corpus A sources with the real generator:

| kind | members | carrying an isolated constant | clean |
|---|---|---|---|
| `ins` | 350 | **0 (0 %)** | 350 |
| `del` | 172 | **168 (97.7 %)** | 4 |
| `mix` | 350 | **153 (43.7 %)** | 197 |

The correspondence with the censoring pattern is exact.

**The record already ruled the fix, and it was never implemented.**

- R3 (D-ART4 (2)): "Connected only; isolated constants not representable
  (**RQ3's deletion variants** and RQ6's interiors must respect this)."
- D-ART4 (3): "**Variant generator: reject stranding deletions (R3).**"
- `ladders.py::variant_collection` docstring: "the constant set is fixed,
  **isolated constants are legal**." `DESIGN.md` §4 still says the same — both
  predate D-ART4 and were never revised.

**Why my D-KBf1 reason (iii) missed it.** Fable forced me to check that reason
for **arity**, and arity was fine (`_arity_pool` bounds an insertion by the
arities already in the record). Neither of us checked **connectivity**. The
Corpus A window bounds `n`, `m` and arity; it says nothing about whether an
edit leaves a constant in no fact. The lesson is that "outside the censoring
regime" needed checking against *every* clause of the domain, not the one that
was challenged.

**The measured consequence of implementing D-ART4 (3) literally** — 40 sampled
sources, collections keeping the full pre-registered `N` after rejection:

| cell | wd50k66 | ndc_classes |
|---|---|---|
| `ins_*` (all four) | **40 / 40** | **40 / 40** |
| `del_*` (all four) | **0 / 40** | **0 / 40** |
| `mix_*` (all four) | 0–2 / 40 | 0–6 / 40 |

Structural, not incidental: a constant-preserving deletion removes a fact and
keeps the constant, and with `n ≤ 12`, `m ≤ 12` most constants sit in exactly
one fact. `del_N9_t1` cannot be built at all, which the 2026-09-05 `m ≥ N + 1`
amendment already knew for a different reason.

**Status: not decided, nothing changed, job not cancelled.** The running job's
`_ins` cells and Corpus B are unaffected and valid. Three options are on the
table — implement the rejection and lose the deletion cells; keep the corpus and
report the Isal arm as censored-by-domain there; or let deletions drop the
stranded constant, abandoning "constant-preserving". D-ART4 (3) rules the
*mechanism*; it does not rule what happens when the fix makes a pre-registered
cell infeasible, and that gap is the author's. Put to `[IsalHG-Fable]` for the
claim question and to the author for the scope call.

### D-KBf5 — RQ3 adopts `reach′` on compacted remainders (author-ruled 2026-09-09)

**Ruling (author, in session):** coherent option (C). Criterion he gave:
*"keep it scoped inside the Isal paradigm as much as possible and be as general
as possible within the knowledge-bases domain."*

**What is adopted.** `reach′_F(K, K′) = min{|A| + |B| : compact(K − A) ≅
compact(K′ − B)}`. A deletion that leaves a constant with no fact removes the
constant, because a knowledge base **is** its set of facts (prose §2.1), which
is what `datasets/kb/base.py::compact` already implements and documents. Every
Corpus A member is then in the domain Prop. C.4 fixes, and all three edit kinds
survive at the full pre-registered `N` on both corpora.

**Why the one-flag version was rejected — verified, not argued.** Flipping
`require_connected` in `_variant_member` alone fails by construction:

- `language/reach.py` docstring: "Constants are never deleted, so an isolated
  constant left behind by a removed fact is legal and **the two remainders
  always carry the same constant count**."
- `language/reach.py::compatible`: `if K.n_nodes != K2.n_nodes: return False`.

A compacted deletion member has `n − 1` constants, so it is at **infinite
reach** from its source; `cov_r` collapses and H3a fails for every deletion
cell by definition rather than by evidence. `[IsalHG-Fable]` found this and
withdrew its own earlier (A)+sub-pool proposal; the lines check out.

**The finding that enlarges the ruling.** The same gate already cripples
**Corpus B**, independently of anything in this campaign. On the 69 natural
`T ≥ 4` runs:

| | |
|---|---|
| member pairs | 1,400 |
| **at infinite reach under the frozen `compatible()`** | **1,146 (81.9 %)** |
| runs with ≥ 1 incompatible pair | **60 of 69** |

`DATA`/`DESIGN` already record that constants change in 400 of 528 natural
consecutive pairs; what was not recorded is that the frozen reach therefore
returns ∞ on most of them, so the triangle-complete candidate set is mostly
empty and **the coverage consensus — RQ3's flagship, "a decoded consensus that
is no member" — has been measuring a crippled method on the real-data corpus.**
`reach′` repairs that. This is a larger gain than the deletion cells and was
not part of the case put to the author when he ruled; it is recorded here as
supporting evidence found immediately after.

**Scope of the change** (verified against the sources):
1. `language/reach.py` — compact both remainders before keying; replace
   `compatible()`'s `n_nodes` equality with a test on the constants surviving
   compaction (or drop it and pay the canonicalisations).
2. `language/consensus.py` — `node_map` is documented "always the identity,
   because every candidate is built inside its anchor's constant space"; it
   must admit a partial map and create an unmapped constant with the donor's
   type and identity. In the language that is `insert_fact_new_constant`, the
   one insertion kind the Isal word owns outright (RQ1).
3. `datasets/kb/ladders.py::_variant_member` — stop passing
   `require_connected=False` and keep `source.n`.
4. **Prop. 5 must be re-measured** under `reach′` (its "source unique maximiser
   12/12, member-to-member reach 0.00–0.02" is cited in `prose.md` §4).
5. Design record: Corpus A is renamed off "constant-preserving"; `DESIGN.md` §4
   gains `reach′` with the date; prose §2.1/§4 gain the disclosure sentences.

**A prose caution for T-KBg**, found on the way: `RemainderIndex` keys
remainders on the **fact word** — chosen because remainders may be disconnected,
and used as an internal complete invariant, not as a representation claim. The
prose must say "any complete invariant" there rather than `F°`, or it will
contradict the code.

**D-ART4 (3) is satisfied in purpose, not in letter:** no member is left outside
R3's domain, but deletions are resolved by compaction rather than by rejection.
Recorded so the instruction is not left looking violated.

### The Corpus B demotion was decided by the crippled measurement — gate void

`DESIGN.md` §4's A → A′ gate reads: *"If Corpus B shows the consensus no better
than the medoid, Corpus B goes to the supplement as the characterized weak
regime."* It fired. `RESULTS_WALKTHROUGH.md` records the numbers that fired it —
fact distance 2.60 against 1.84–2.40, exact recovery 0.145 against up to 0.226 —
and explains them: *"A natural series is not a set of variants of one source, so
there is nothing for a consensus to converge to."*

Both are void. Those numbers were produced with **81.9 % of Corpus B's member
pairs at infinite reach**, so the consensus was not given a candidate set to
work with; and the explanation is an untested causal claim the measurement
cannot support. The gate is re-run under `reach′`, and **Corpus B's placement is
undecided rather than "supplement"** until it is. Supersession notes are written
in place at both sites so neither can be inherited by inertia into T-KBg.

**Fable's hypothesis that the audit's §3.3 is this same gate is wrong**, and the
reason matters. §3.3 ("the deletion boundary is real, the stated mechanism is
wrong") concerns **Corpus A** `t = 2` deletion cells, and under the *old*
generator every Corpus A member keeps `n = source.n` — isolated constants were
retained — so `compatible()` always passed there and the reach gate never bit.
§3.3's measured mechanism stands: the source is in the candidate set 108/108 and
the plain union equals the source 108/108, so the consensus loses to the
objective's summed-reach criterion or its lexicographic tie-break, "a property
of the objective, not of the data".

**But §3.3 now needs re-checking for a new reason.** Under `reach′` Corpus A
deletion members *do* change constant count, so the summed-reach criterion is
computed over different quantities than when §3.3 tested it. Its conclusion may
survive or may not; it must be re-run alongside Prop. 5 rather than assumed.

### D-KBf5a — the operative A → A′ gate for Corpus B, pre-registered before the re-run

The rule in `DESIGN.md` §4 is *"If Corpus B shows the consensus no better than
the medoid, Corpus B goes to the supplement"* — a verdict with **no threshold
and no test**. It was applied once, informally, on a crippled measurement, and
the placement of an entire real-data corpus followed. Committed here **before**
`reach′` produces a single number, so the placement cannot be read as chosen.

**The comparison.** Coverage consensus against the **certified medoid**, on two
axes: exact fact-level distance to the held-out quarter, and exact-recovery rate.

- **Comparator:** the *best-performing medoid arm on each axis*, not the Isal
  one — the gate must be conservative against us. `majority_merge` is reported
  beside them as the reference ceiling and is **not** part of the gate, since it
  uses constant identities that every other method is denied (`DESIGN.md` §4
  Methods).
- **Units:** the common set of Corpus B runs — the D-KBf1 rule, 63 of 69 at
  present. Corpus B members are real quarters, not generated variants, so the
  generator change does not move that set; if the re-run's censoring differs,
  the common set is recomputed and the number stated.
- **Test:** paired Wilcoxon under the 27-seed harness where seeds exist, sign
  test on the paired runs where they do not; Holm across the two axes; 0.05.
- **Verdict:** *"no better"* means the consensus fails to beat the best medoid
  at Holm-corrected 0.05 **on both** axes. Placement follows from that and from
  nothing else.

**Both readings pre-stated, so neither is written after the fact.**

- *If the consensus wins under `reach′`:* the explanation of record — "a natural
  series is not a set of variants of one source, so there is nothing for a
  consensus to converge to" — is **retracted as an artefact of the reach gate**,
  and Corpus B becomes the main-text real-data result. The retraction is printed,
  not silently dropped.
- *If it still loses:* the explanation **stands**, restated as measured under a
  working candidate set for the first time, and Corpus B goes to the supplement
  exactly as the pre-registered rule says.

**One ambiguity resolved rather than left open:** the rule says "the medoid"
while the campaign now runs eleven medoid arms. Read as the best arm per axis
(above). Recorded so the reading is not chosen later.

#### D-KBf5a amendment — two pre-named comparisons, not one

The gate above answers *"may Corpus B carry the main text?"*. It does not answer
the question RQ3 actually asks. Both are pre-named here; neither is chosen after
the numbers.

**Primary comparison (the paper's claim):** coverage consensus versus
**`medoid[wstar_orbit]`** — the paper's own metric. RQ3's claim is that *the
language buys something beyond the metric*: a representative that is a decoded
object no member wrote, against the best object the same distance can return by
picking an input. That question is answered by our own medoid, not by the
strongest competitor, and it is the row the RQ3 table leads with.

**Placement gate (conservative check):** coverage consensus versus the
**best-performing medoid arm per axis**, as pre-registered above. This decides
main text versus supplement and nothing else.

**Winner's-curse disclosure, required in the caption.** The best of eleven arms
chosen per axis *after seeing the numbers* is a selection-biased comparator, and
the Holm correction across the two axes does not account for that selection: the
bias grows with the number of arms and runs **against** the consensus. That is
the right direction for a gate deciding the placement of our own corpus, so it
is kept — but the caption states plainly that the comparator is the post-hoc
best of eleven and that the bias runs against us. A reader must not have to
infer either.

### Wave outcome, 2026-09-09 15:30 — what is banked and what is superseded

| job | what | state | verdict |
|---|---|---|---|
| 2264827 | matrices | FAILED 5 s | nested-budget defect, fixed |
| 2264831 | matrices, 31 units | COMPLETED 3:10:11 | **banked** |
| 2265308 | RQ3 pilot | COMPLETED | caught T-KBn; rows discarded |
| 2265309 | RQ2 main | 11/13 done | in progress |
| 2265310 | RQ2 census | **COMPLETED 9/9** | **banked** |
| 2265353 | RQ3 full + RQ6 | COMPLETED 2:30:26 | **part banked, part superseded** |
| 2265368 | RQ4 smoke | TIMEOUT | diagnosed, fix merged |
| 2265389 | RQ5 full | COMPLETED | **banked** |

**RQ2's headline, on the campaign's most arity-heavy collection.**
`ndc_substances` / `wstar_orbit`, built by the budgeted path added at `afab7c5`
(without it the unit hangs rather than screens): 1,661 of 1,745 members
(84 censored, 4.8 %), 1,378,630 pairs of which 1,373,305 non-isomorphic,
**0 false merges**, and the induced partition equal to the true one at
**1,086 = 1,086**. 8,446 s. That is RQ2's exactness result, measured rather
than inherited from the theorem.

**RQ3's censoring tally confirms the R3 mechanism exactly**, on the full run
rather than a 25-source sample:

| cell kind | collections censored |
|---|---|
| `ins` | **0** |
| `del` | 982 |
| `mix` | 1,638 |
| Corpus B | **6** — classes 470, 471, 472, two runs each |

Insertions never strand a constant, so they never censor; `del` and `mix` do.
The Corpus B figure is exactly the 6 units D-KBf1a predicted from those three
classes, so the cost-censoring model and the domain-censoring mechanism are
cleanly separated in the data.

**Banked from 2265353:** the Corpus A `ins` cells (64,293 Corpus A rows contain
them) and Corpus B's **medoid** rows. **Superseded:** every `del`/`mix` cell
(D-KBf5) and every Corpus B **consensus** row (the reach gate). RQ6 ran bundled
(162 sample, 60 alignment rows) and its **alignment** rows need re-checking
under `reach′`, since an alignment interior is built from the same machinery;
its sample rows do not.

### D-KBf5 measured — the gate re-opens Corpus B

`reach′` merged. The Corpus B probe re-run independently from the merged tree
(`scripts/diagnostics/reach_prime_corpus_b_probe.py`), reproducing the
implementer's numbers exactly:

| Corpus B, 1,400 pairs / 69 runs, r = 2 | frozen | `reach′` |
|---|---|---|
| gate-rejected | **1,146 (81.9 %)** | **387 (27.6 %)** |
| no finite reach within r = 2 | 1,148 | 446 (31.9 %) |
| runs carrying such a pair | 60 / 69 | 51 / 69 |

**Consensus, the worst run** (class 389, T = 36, 35 members, 595 pairs):
1.4 s, 319 candidates, 495 of 595 pairs finite, **coverage 34 of 35** — against
the frozen 0.4 s, 103 candidates, 112 finite, **coverage 13 of 35**. The
consensus goes from covering a third of a run to covering all but one member,
and the 1,800 s guard is cleared by three orders of magnitude, so the array is
safe. Median run: 0.0 s, 48 candidates against 12.

**Prop. 5 is unchanged — for a reason worth recording.** Unique maximiser 12/12
at both noise levels, copy-to-copy 0.00–0.02, identical to the published
numbers. But its probe measures the **token-level** ball and never imports
`isalhg.language`, so Prop. 5 is *independent of* this change rather than
validated by it. The prose must not cite it as evidence for `reach′`.

**Three corrections from the implementer, all verified.**
1. **My suggested gate was wrong.** "Type multiset of constants occurring in
   ≥ 1 fact" is not a necessary condition, because compaction removes occurring
   constants — counterexample at `reach′ = 1` with multisets `[0,0,1]` vs
   `[0,0]`, now a regression test. The shipped gate uses a fact-profile budget
   and undeletable-type containment, both necessary, and takes `r_max` because
   the second depends on it.
2. **"Infinite reach" does not exist under `reach′`**: deleting every fact on
   both sides always matches, so `reach′ ≤ m + m′`. The reportable quantity is
   "no finite reach within `r`", and the prose must say that.
3. `_variant_member` also had to stop reading `source.types` and
   `source.constant_ids`, not only `source.n` — all stale after a compacting
   step.

**One consequence left unfixed, filed as T-KBo:** `rq6.Reach1Index._shape()`
hard-codes the frozen precondition and buckets members by constant count, so it
withholds exactly the pairs `reach′` admits (`reach(sample, src, 1) == 1` while
`within_one(sample)` returns `None`). RQ6's `reach1` column must be re-derived;
nothing else in RQ6 is implicated.

**Every RQ3 and RQ6 result on disk is now stale.** The re-run goes into the
clean root under the D-KBf5a gate, which was committed before any of these
numbers existed.

### The RQ4 smoke is a structurally invalid gate — do not read its TIMEOUT as a failure

Job 2265661 (the fix's re-run) sat at 28:43 with no unit complete, the same
shape as the pre-fix 2265368. It is **not** the same failure, and the process
table proves it: the parent had **29:15 elapsed against 00:01:06 of CPU
(3.7 %)**, spawning one short-lived child at a time. That is a sequential
budgeted-fork warm-up, not a hang — the pre-fix job was burning CPU inside an
unbounded `pairwise`.

**Why one unit cannot finish in 30 minutes, by design.** `member_words_for_unit`
memoises pristine members' words **per process, per sub-collection**, so "the
budgeted fork is paid once each" across the run; only the ~66 corrupted members
are recomputed per unit. A single-unit smoke therefore pays the whole warm-up —
for `ndc_classes` / `wstar_orbit` that is the ≈ 5,823 s the matrices job itself
paid — and amortises it over nothing. The full run has **1,323 units in one
process** and pays it once.

So the smoke's 30-minute wall can never be met by the first unit, and the
correct gate is the first two unit timings of the real run: unit 0 pays the
warm-up, unit 1 shows the steady state. That measurement comes free from the
submission and is what decides whether the 8-hour wall holds.

Recorded because the obvious reading — "the fix did not work" — is wrong, and
because the same trap applies to any runner that memoises across units: a
one-unit smoke measures warm-up, never throughput.

### D-KBf5 verified on the cluster (RQ3 pilot 2267401)

| | pre-`reach′` full run | pilot under `reach′` |
|---|---|---|
| collections censored | 2,626 (`del` 982, `mix` 1,638, B 6) | **1** |
| Corpus A rows | — | 56 (was 44 at the same cell set) |
| Corpus B rows | — | 27 (was 20) |
| Corpus A domain censoring | heavy | **0** |
| Corpus B censoring | — | 1, the residual **cost** censoring |
| `medoid_survivors` rows | — | **1**, on that one collection |
| coverage rows carrying a result | — | A 8/8, B **2/2** |

Three things confirmed at once. The R3 domain violation is **gone** — no Corpus
A collection is censored, so every variant is now a knowledge base and all
eleven arms including `wstar_orbit` produce medoids. D-KBf1's **cost**
censoring still fires correctly and independently, on exactly one Corpus B
collection, with its survivor-medoid supplement row beside it — so the two
censoring mechanisms remain separated in the data, which was the point of
giving them different reasons. And the coverage consensus **returns a result on
every Corpus B unit it was given**, where the frozen reach left it with a
mostly empty candidate set.

Full RQ3 submitted under `reach′` into `IEEETKDE_isal_reachprime/`, leaving the
superseded run intact as the record.

### RQ2 complete — the false-merge census, and an OOM that cost nothing

Task `2265309_10` was **OUT_OF_MEMORY**, and it is a non-event for the data:
the log shows `unit bipartite-ndc_classes done in 7792.2 s: {'bipartite': 8992}`
and the kill **nine seconds later**, after the rows were written
(`rows_bipartite__da0ff0af-bipartite-ndc_classes.csv`, 1.46 MB, on disk). The
job asked for 32 GB and peaked at 33.4 GB — it overran by ~1.4 GB in the
in-job finalisation. **All 85 of 85 units have rows; nothing is missing.** Only
`tables.md` / `stats.json` / `summary.json` were lost, and they regenerate from
the rows; done on the login node.

**The census (`n_false_merges`, and whether the induced partition equals the
true one):**

| arm | ndc_classes | ndc_substances | wd50k66 | partition |
|---|---|---|---|---|
| **`wstar_orbit`** | **0** | **0** | **0** | **exact** (530 / 1,086 / 3,677) |
| `nauty_cert`, `nauty_cert_rows` | 0 | 0 | 0 | exact |
| `fact_rank` | 0 | 0 | 0 | exact |
| `wl_l1` | 0 | 0 | 0 | exact |
| `bipartite_ged_path` | 0 | 0 | 0 | **splits** — 574 classes against 557 |
| `netlsd` | 2,516 | 1 | 185,917 | merges |
| `hpd_jsd` | 7,618 | 9,885 | 212,179 | merges |
| `bipartite_ged_assign` | 59 | 1,332 | 201,010 | merges |
| `degree_seq_l1` | 5,397 | 1,332 | 201,010 | merges |
| `size_l1` | 52,660 | 33,713 | 291,227 | merges |

Two readings the prose must carry. **`wl_l1` merges nothing on these three
corpora** — refinement-based keys are incomplete on hypergraphs in theory
(Prop 9), and on *this data* the incompleteness does not materialise; that is a
measured negative for our own contrast and must be stated as such rather than
quietly omitted. And **`bipartite_ged_path` fails exactness in the other
direction**: no merges, but it splits isomorphic pairs into 574 classes where
557 exist, so "0 false merges" is not "exact at zero".

**D-KBf2's intersection is visible in the table.** Every uncensored arm carries
two rows — its own full set (557 / 1,156 / 3,682) and the common set restricted
to `wstar_orbit`'s survivors (530 / 1,086 / 3,677). The reader can see both, and
the cross-arm comparison is on the second.

**Caveat to clear before the RQ2 tables are quoted:** the analyzer reported
`certificate validity: read`, and the file it read is the **pre-`reach′`** RQ3
certificate output, because those rows live in `IEEETKDE/` while the `reach′`
RQ3 writes to `IEEETKDE_isal_reachprime/`. RQ2 step 4 must be re-run against
the new certificate file once RQ3 lands. Every other RQ2 section is independent
of RQ3 and final.

### D-KBf5a applied — the gate says SUPPLEMENT, and the old explanation is refuted

RQ3 under `reach′` (job 2267425, 2:40:19): 62,398 Corpus A rows, 901 Corpus B
rows, 49,027 certificate rows, and **6 censored collections against 2,626** —
all six the Corpus B *cost* censorings of classes 470/471/472, **zero `del`/`mix`
domain censorings**. The R3 violation is gone across the full run.

**The gate, applied exactly as pre-registered** (common set **63 units**, the
number D-KBf5a named in advance; paired Wilcoxon; Holm across two axes; 0.05):

| | consensus | best medoid | Δ | p |
|---|---|---|---|---|
| fact distance | **1.873** | `wl_l1` 1.905 | −0.032 | 0.679 |
| exact recovery | **0.286** | `wstar_orbit` 0.286 | +0.000 | 1.000 |

Holm 1.358 / 1.000. **The consensus does not beat the best medoid on either
axis → Corpus B goes to the supplement**, which is what the rule says and what
it said before any of these numbers existed.

**Primary comparison** (the paper's claim, consensus vs `medoid[wstar_orbit]`):
fact distance −0.111 (p = 0.265), recovery ±0.000 (p = 1.000). The language
does not buy a measurable advantage over its own metric on this corpus.

**But the explanation of record is refuted, and that must be printed.** The
superseded numbers had the consensus at fact distance 2.60 against medoids
1.84–2.40 and recovery 0.145 against up to 0.226 — *worse than every medoid and
worse than the merge* — and concluded "a natural series is not a set of variants
of one source, so there is nothing for a consensus to converge to". Under a
working candidate set the consensus is **better in point estimate than all
eleven medoid arms** (1.873 against 1.905–2.270) and **best-equal on recovery**
(0.286, tying `wstar_orbit` and beating the other ten). It even **beats
`majority_merge` on recovery** — 0.286 against 0.254 — and that reference uses
constant identities every other method is denied, though it still leads on fact
distance (1.667).

So the sentence "the consensus is worse than the medoids and than the majority
merge" is **false**, and the causal story built on it does not survive. What
survives is the weaker, measured statement: *on 63 natural runs the consensus is
not distinguishable from the best medoid at 0.05 on either axis.* The placement
is unchanged; the reason for it is not the reason previously given.

This is what the pre-registration was for. Had the gate been applied after
seeing these numbers, "better on all eleven arms but not significantly" could
have been written up either way.

### The gate is badly underpowered — "no better" is the wrong sentence

Measured on the same 63 paired runs, minimum detectable effect at 80 % power,
two-sided 0.05:

| comparison | observed Δ | paired SD | MDE | observed / MDE | informative pairs |
|---|---|---|---|---|---|
| fact distance vs `wl_l1` | −0.032 | 1.126 | **0.397** | **0.08** | 29 of 63 |
| fact distance vs `wstar_orbit` | −0.111 | 0.910 | 0.321 | 0.35 | 29 of 63 |
| recovery vs `wl_l1` | +0.032 | 0.355 | 0.125 | 0.25 | **8 of 63** |
| recovery vs `wstar_orbit` | ±0.000 | 0.356 | 0.126 | 0.00 | **8 of 63** |

The study can detect a fact-distance difference of about **0.40 tokens**; the
differences in play are **0.03–0.11**, an eighth to a third of that. On the
recovery axis only **8 of 63 pairs differ at all** — the other 55 are ties, so
that axis is close to uninformative at this corpus size.

**Consequence for the wording.** "The consensus is no better than the medoid" is
not what was measured. What was measured is: *no difference was detected on 63
paired runs, where the smallest detectable difference is an order of magnitude
larger than the one observed.* The pre-registered placement rule fires on the
null and Corpus B goes to the supplement — the rule is honoured — but the
supplement's text must state the power, or a reader will take a null for a
finding. This is a defect in how D-KBf5a was written (it treats a
non-rejection as evidence of no effect) and it is recorded as such rather than
patched after the fact.

### The forensics — Corpus A carries RQ3, and the tie-break barely fires

Five questions put by `[IsalHG-Fable]` against the gate, answered from rows on
disk (`scripts/diagnostics/rq3_consensus_forensics.py`).

**Corpus A is the result the paper wants, and it is overwhelming** (4,457 common
units, `reach′`):

| axis | consensus | medoid (`wl_l1`, `wstar_orbit` alike) | discordant | rank-biserial |
|---|---|---|---|---|
| fact distance | **0.269** | 1.521 | 3,901 better / 37 worse of 3,938 | **+0.981** |
| exact recovery | **0.835** | **0.000** | 3,723 better / **0 worse** of 3,723 | **+1.000** |

The medoid recovers the source **never** — which is H3b holding exactly as
written ("the medoid's distance to the source is ≥ t by construction, since it
returns a member"). The consensus recovers it in 83.5 % of runs and is never
once worse on recovery. So RQ3's claim — *a representative that is a decoded
object no member wrote does what no method returning an input can* — is
confirmed at scale on the controlled corpus. The Corpus B tie is a statement
about the natural series, not about the method.

**The tie-break barely fires**, which bounds what the retired-word defect can
have cost:

| | consensus rows | `n_ties = 0` (tie-break never fired) |
|---|---|---|
| Corpus A | 8,914 | **8,442 (94.7 %)** |
| Corpus B | 69 | **54 (78.3 %)** |

A run with `n_ties = 0` is invariant-neutral: no candidate was separated by the
word rule, so its result stands unchanged under any complete invariant. The
defect can therefore have touched at most 5.3 % of Corpus A runs and 21.7 % of
Corpus B's — and touching is not the same as changing, since a different word
may pick the same candidate. Candidates per run: median 118 (max 1,330) on
Corpus A, median 40 (max 319) on Corpus B.

**The medoid has no tie-break of its own** — `medoid.py` is `int(np.argmin(costs))`
with no lexicographic fallback, so ties there resolve by member index. Arbitrary,
but representation-neutral, so the medoid rows are unaffected by any of this.

**Two of the five are not answerable from the rows**: the winner's origin
(`member:` vs `transfer:`) and the disconnected-candidate count are computed
inside `consensus.py` and never persisted. They need an instrumented re-run of
the consensus, not a query. Filed rather than guessed.

**A near-miss recorded.** The first version of this script labelled the sign of
the recovery axis as though lower were better, and printed "consensus worse in
3,723 of 3,723 pairs" for what is in fact "better in 3,723 of 3,723". Caught
before it reached the ledger by checking the printed means against the signs;
the axis-direction is now explicit per axis in the code.

### The pre-registered hypotheses, measured under `reach′` — H3a's deletion clause fails

**H3a** (≥ 95 % exact recovery on insertion-only and deletion-only, ≥ 80 % on
mixed, at `r = 2`, `t ∈ {1,2}`), on Corpus A. The deletion cells are scored here
for the first time on in-domain members:

| kind | t | recovery | n | pre-registered | verdict |
|---|---|---|---|---|---|
| `ins` | 1 | 0.995 | 864 | ≥ 0.95 | **pass** |
| `ins` | 2 | **1.000** | 864 | ≥ 0.95 | **pass** |
| `mix` | 1 | 0.921 | 864 | ≥ 0.80 | pass |
| `mix` | 2 | 0.806 | 864 | ≥ 0.80 | pass, barely |
| `del` | 1 | 0.845 | 406 | ≥ 0.95 | **fail** |
| `del` | 2 | **0.276** | 595 | ≥ 0.95 | **fail badly** |

**The deletion boundary survives `reach′`.** The audit's §3.3 recorded it at
0.23–0.81 at two deletions and argued the stated mechanism ("the information is
gone") was wrong; under `reach′`, with every member in-domain, `del` `t=2` is
0.276. So the boundary is not an artefact of stranded constants either. Its
mechanism remains §3.3's — the objective's summed-reach criterion or the word
tie-break — and §3.3 is on the re-measurement list for exactly that reason.

**H3c** (the consensus matches `majority_merge` on recovery within 5 points):
majority 0.894 against consensus 0.835 — **5.9 points, so H3c marginally
fails**. On fact distance the identity-using reference leads 0.116 to 0.269.
Reported as measured; `majority_merge` uses constant identities every other
method is denied, which is why it is the ceiling and not a competitor.

**The 37 Corpus A losses, by cell** — `[IsalHG-Fable]` predicted deletion and
mixed cells before seeing them:

| kind | losses | of | rate |
|---|---|---|---|
| `del` | 27 | 1,001 | **2.70 %** |
| `mix` | 6 | 1,728 | 0.35 % |
| `ins` | 4 | 1,728 | 0.23 % |

Deletion cells lose **twelve times more often** than insertion cells, and the
losses split evenly across corpora (ndc 18, wd50k 19). The prediction holds and
the losses are the same regime as the H3a failure, not a separate phenomenon.

**Scope of the pending consensus change (Fable's item 4):** only `rq3.py`
imports the consensus objective. RQ6 imports `alignment` and `reach`, not
`consensus`, so it is touched by `reach′` (already landed; `Reach1Index` filed
as T-KBo) and not by the tie-break or the disconnected-candidate exclusion.

**A correction I accept.** I argued the disconnected-candidate exclusion "changes
the candidate set on 100 % of runs" and was therefore a large perturbation.
Wrong twice: removing *losing* candidates from an argmax is a no-op, so the
exclusion changes a result only where the **winner** is disconnected — and on
exactly those runs the current deliverable is already wrong, since the reported
representative has no Isal string. The blast radius equals the count of
currently-invalid rows. That count is not persisted and is the first thing the
instrumented re-run must measure.

### RQ5 analysed — negative on every clause, as pre-stated, and worse than "no claim"

The RQ5 job completed but its analyzer had never been run (its 144 row files had
no `tables.md`). Run now against `IEEETKDE_isal`:

**H5a — not supported, and the two halves must not be reported together.**
`ν = 0.1015` with 1,553 negative eigenvalues, so the space **is** non-Euclidean
and the licence it exists to grant — PAM over centroid methods, metric MDS over
classical — **holds**. What fails is the hubness clause: `k = 10` occurrence
skewness **5.408 against a ceiling of 1.5**. The analyzer's own note draws the
line correctly: a failure of the hubness half does not withdraw the PAM licence.
The prose must keep them apart or it will report a licence as revoked.

This is also a **standing prediction for RQ4**: hubness that severe is the kNN
precondition failing, so RQ4's screen should be degraded. RQ4 is running; the
link is testable rather than asserted.

**H5b — not supported, and the naive floors beat us significantly on all four
comparisons**, which is stronger than "no claim":

| corpus | floor | ours ARI | floor ARI | rank-biserial |
|---|---|---|---|---|
| wd50k100 | `degree_seq_l1` | 0.030 | **0.089** | **−1.000** |
| wd50k100 | `size_l1` | 0.030 | 0.040 | −0.878 |
| wd50k66 | `degree_seq_l1` | 0.042 | **0.053** | **−1.000** |
| wd50k66 | `size_l1` | 0.042 | 0.049 | −0.952 |

A rank-biserial of −1.000 means the degree-sequence floor wins on **every
seed**, both corpora. D-ART4 (3) pre-stated "expected negative for every arm";
the measured outcome is that a naive baseline is significantly *better*, and
that is what goes in the table.

**H5c — not supported.** Best competitor `hpd_jsd` at ARI 0.064
[0.061, 0.068] against ours 0.030 [0.025, 0.036]; the intervals do not overlap.

**H5d — not evaluable, not null.** The analyzer reports "no `fact_rank_roles`
comparison" because that arm was disqualified at the M0 gate (247 false splits,
2,104 invariance violations). The verdict must be printed as *not evaluable
because the arm failed acceptance*, never as an inconclusive result — those are
different statements.

**Cross-project consistency worth one sentence.** The metric-space article's S7
sweep found degree-seq and NetLSD leading A2-ARI over `d_I` on planted families;
RQ5 finds the degree-sequence floor leading over `wstar_orbit` on knowledge
bases. Two independent campaigns, different corpora, same conclusion: degree
structure is the dominant clustering signal and the canonical string does not
capture it. That is a limitation to state once, plainly, not to rediscover.

### RQ6 — every clause holds, and it is the capability differentiator measured at scale

Analysed from the `reach′` run (`IEEETKDE_isal_reachprime/RQ6_generation/`):

| hypothesis | measured | holds |
|---|---|---|
| H6a validity by theorem | **540,000 of 540,000 samples decode** (validity 1.000) | ✔ |
| H6a baseline rejects | the strict decoder rejects **0.9854 [0.9850, 0.9857]** of 540,000 | ✔ |
| H6b fidelity | largest mean JSD over the five histograms **0.2118** | ✔ |
| H6c interiors decode, `fact_rank` | 86 of 86 on wd50k66, 0 pairs censored | ✔ |
| H6c interiors decode, `isal_ow_struct` | **119 of 119**, 0 censored | ✔ |
| H6c interiors decode, `pointer` | 86 of 86, 0 censored | ✔ |

**Validity 1.000 against a baseline that rejects 98.5 % of its own samples** is
the sharpest statement of the closed-alphabet claim the campaign has produced —
sharper than the 256/1,000-connected figure `prose.md` currently quotes, which
measures connectivity rather than validity. Both belong; they are different
properties and the prose should not merge them.

**The "pointer" arm is `w*_c` — the paper's representation, under its
pre-D-ART5 name.** `rq6._pointer_word` is
`canonical_string(H, algorithm="canonical", backend="cpp")`, which is the frozen
tie-complete form. RQ6 needs no separate `wstar_orbit` arm **because orbit
pruning is value-preserving**: the word is bit-identical (verified 7,013/7,013
at D-ART5) and only the wall-clock differs, and generation is a statement about
words. So RQ6's arm set is correct as it stands; what must change is the label
in the table, from `pointer` to `w*_c`. Recorded so nobody "fixes" RQ6 by adding
a redundant arm.

Caveat carried: RQ6's **`reach1` column** still needs re-deriving (T-KBo) —
`Reach1Index` buckets on the frozen precondition. Nothing above depends on it;
validity, fidelity and the interiors do not use that index.

### RQ3's analyzer verdicts — and a correction to my own H3a reading

The analyzer scores H3a **per cell**, which is how it was pre-registered
("exact recovery ≥ 0.95 **in every cell**"). My earlier entry aggregated by
`(kind, t)` and reported *mix* as "pass, barely" at 0.806. **That was wrong** —
the same pooling error this campaign keeps finding, made by me one level down.
Per cell:

| hypothesis | claim | measured | holds |
|---|---|---|---|
| H3a `ins` | ≥ 0.95 in every cell | min over 8 cells = **0.991** | **yes** |
| H3a `del` | ≥ 0.95 in every cell | min over 6 cells = **0.130** | no |
| H3a `mix` | ≥ 0.80 in every cell | min over 8 cells = **0.722** | **no** |
| H3b | a medoid returns an input, so its distance to the source is ≥ t | fraction of medoid rows with `fact_dist ≥ t` = **1.0000** | **yes** |
| H3c | recovery within 0.05 of the identity merge | gap **0.0606** | no |
| H3d | every ratio ≤ 2 − 2/N, and max ≤ 1.7 | **0 of 4,457 exceed the bound**; max **1.7778** | no |
| H2d | LB ≤ cost under a metric; a non-metric arm may violate | `bipartite_ged_path` = **27** violations | yes |

Three readings worth keeping distinct.

**H3b holds exactly, on every row.** The medoid's distance to the source is
≥ t in 4,457 of 4,457 — the floor is not a tendency, it is structural, and it
is what makes the Corpus A consensus result meaningful rather than a better
score on the same task.

**H3d fails only on its tightness clause.** Prop 3's *theorem* — ratio
≤ 2 − 2/N — holds on **all 4,457 certificates, zero violations**. What fails is
the empirical expectation that the measured max would stay under 1.7; it is
1.7778. The prose must not report "H3d fails" without saying the proved bound
never broke.

**H2d is RQ2 step 4, already computed here**, and it holds: `bipartite_ged_path`
violates `LB ≤ cost` 27 times, which is the pre-stated consequence of its not
being a metric. So the RQ2 step-4 gap is narrower than recorded — the
certificate-validity verdict exists under `reach′`; what still needs the final
RQ2 pass is the identity-timing section, which waits on RQ7.

### The per-cell recovery table — and H3a's deletion clause was unachievable by construction

`coverage_r2` against `majority_merge`, the identity-using reference, per cell
(every medoid arm is 0.000 in every cell, so the floor is omitted):

| collection | kind | t | consensus | merge (identities) |
|---|---|---|---|---|
| ndc | ins | 1 | 0.991 | 1.000 |
| ndc | ins | 2 | **1.000** | **0.995** |
| wd50k | ins | 1 | **1.000** | 1.000 |
| wd50k | ins | 2 | **1.000** | 1.000 |
| ndc | mix | 1 | 0.944 | 1.000 |
| ndc | mix | 2 | 0.854 | 0.803 |
| wd50k | mix | 1 | 0.898 | 1.000 |
| wd50k | mix | 2 | 0.757 | 0.850 |
| ndc | del | 1 | 0.792 | 1.000 |
| ndc | del | 2 | **0.130** | **0.208** |
| wd50k | del | 1 | 0.905 | 1.000 |
| wd50k | del | 2 | 0.359 | 0.607 |

**On insertions the consensus reaches the identity-using ceiling and once
exceeds it** — 1.000 against the merge's 0.995 on ndc `ins t=2`, and 1.000 on
both wd50k insertion cells. A method denied constant identities matches a method
given them. That is the cleanest statement of RQ3's claim in the campaign.

**H3a's deletion clause asked for something no method achieves.** It required
≥ 0.95 exact recovery on deletion cells; the identity-using merge itself scores
**0.208** on ndc `del t=2` and 0.607 on wd50k. So the threshold was not merely
missed, it was **unachievable by the oracle the design itself names as the
reference**. The honest report is that the pre-registration was mis-specified on
that clause, not that the method failed a reachable bar — and the evidence is
the merge's own number, not ours. This does not rescue our 0.130; it locates it.

**The deletion boundary is a property of the task at `t = 2`.** Both methods
collapse together (0.130/0.208 on ndc, 0.359/0.607 on wd50k) while both are
near-perfect at `t = 1` (0.792/1.000, 0.905/1.000). Two deletions from a small
source destroy the information, which is what the *original* explanation said
before the audit's §3.3 disputed it — §3.3 disputed it for **Corpus A under the
old generator**, where the objective's tie-break was implicated. Under `reach′`,
with the merge's numbers beside ours, the information-loss reading is supported
for `t = 2` specifically. §3.3 remains on the re-measurement list; this is
evidence for it, not a substitute.

Note the `mix` minimum the analyzer reports (0.722) is below the lowest cell
here (0.757) because H3a is scored over both consensus labels, `coverage_r2`
and `coverage_rt`; 0.722 is a `coverage_rt` cell.

### RQ4's L15 disclosure is live on real data (interim, machinery only)

Verified on 819 completed units — **the machinery, not the science**; RQ4 is
incomplete (T-KBq) and no conclusion is drawn from a partial corpus.

All nine census columns are present and populated: `censored`,
`n_censored_members`, `n_censored_anomaly`, `n_censored_clean`,
`censor_rate_anomaly`, `censor_rate_clean`, `n_censored_word_anomaly`,
`n_censored_word_clean`, `word_censored_arms`. All eleven D-ART5 arms are
present, `wstar_orbit` among them, and `censored = 0` on every sampled row (no
unit lost).

The pair that answers Fable's L15 concern — *are corrupted members
preferentially censored, so that the AUC is computed on a set whose positives
were removed?* — is now measurable rather than assumed. Interim shape only:
`censor_rate_clean` sits tightly around **0.049–0.055** across units while
`censor_rate_anomaly` ranges **0.029–0.101**, straddling it in both directions.
The wider spread is expected from the denominators alone (≈ 69 anomalies against
≈ 1,300 clean members per unit), so nothing here suggests a systematic bias —
**but that is a shape, not a test.** The paired comparison over the full corpus
is what the caption will carry, and it is deferred until RQ4 completes.

Recorded now because the columns being *populated* is the thing that could have
silently failed; the disclosure was pre-registered before the run and is not
retrofittable.

### RQ6's analyzer names the retired alphabet "ours", and understates the result

Found by a systematic sweep for surviving fact-alphabet couplings, run to test
rather than assert the pattern that every defect so far sat where the pipeline
still used the retired representation.

`rq6.py:63` sets `MODEL_OURS = "fact_ngram"`, so the analyzer's H6a verdict
reads *"every sample **over the fact alphabet** decodes (validity 1.000)"*. Both
halves of that are true and it is **the wrong arm and the weaker claim**:

| model | validity | connectivity | rejection |
|---|---|---|---|
| `fact_ngram` (labelled ours) | 1.0000 | **0.2709** | 0.0000 |
| `incidence_ngram` (baseline) | 0.0146 | 0.0494 | 0.9854 |
| **`ow_ngram` (Σ_HG)** | **1.0000** | **1.0000** | 0.0000 |

The fact alphabet is **total but not connected**: 73 % of its samples are
disconnected knowledge bases, which R3 places outside the Isal domain entirely.
The Isal alphabet is total **and** connected — validity 1.000 *and*
connectivity 1.000 — which is Prop. C.4 measured, and is strictly the stronger
guarantee. `rq6.py:66–68` already says so in a comment; the constant and the
analyzer verdict disagree with the comment.

**`prose.md` §2.2 already has this right** — "1,000/1,000 samples of the Isal
generator are connected, against 256/1,000 for a fact-list generator" is this
measurement (0.271 here). So the prose is safe; what is mislabelled is the
analyzer's headline, and anyone reading `summary.json` cold would quote the
weaker number as the paper's.

**Two actions, neither urgent, both before the tables are drawn.** Rename
`MODEL_OURS` to the Isal model so the verdict quotes Σ_HG, keeping the fact
alphabet as the retired comparator it is (D-ART4 (1)); and state the connectivity
column beside validity everywhere, since validity alone is the property the
retired alphabet also has.

**One question for the arm set, flagged not decided:** `ow_ngram` is the
**ordered walk**, and D-ART5 puts the ordered walk in RQ7 alone. For generation
that is defensible — Prop. C.4 is a property of the *alphabet*, not of a
canonical form, so any Σ_HG word model inherits validity and connectivity — but
if the paper wants its one Isal row to be `w*_c` throughout, RQ6's model should
be fitted on `w*_c` words. The measurement would not change (both are Σ_HG);
only the label would.

### The consensus change landed — the audit number is zero, and the fix nearly broke the medoids

Merged. Three parts, in the order that made each measurable: persist the
winner's origin, connectivity and out-of-domain counts; exclude candidates
outside the representation's domain; move the objective's final tie break off
the retired fact word onto `w*_c`, evaluated lazily over the tied set only. The
dedup key stays the fact word — deduplication is invariant-neutral, a tie break
is not.

**The audit answers the question nobody could answer.** Over **323 real Corpus A
collections across all 24 cells, zero out-of-domain winners** on either corpus:
731 out-of-domain candidate classes were generated and **every one lost**. So
the exclusion is a guarantee costing nothing here, not a repair — which is what
"removing losing candidates from an argmax is a no-op" predicts, now measured
rather than argued.

| | exclusion | tie break |
|---|---|---|
| ndc_classes | 0 | 7 / 160 |
| wd50k66 | 0 | 6 / 163 |
| **pooled** | **0** | **13 / 323 (4.0 %)** |

`n_ties` histogram unchanged; **221 of 221 tie-free collections bit-identical**
— invariant-neutrality holding in the data. Of the 13 movers, 3 land closer to
truth, 1 further, 9 the same (+3 exact recoveries, none lost). Recorded as
provenance; **n = 13 supports no claim** and must not be quoted as one.

**Two corrections that changed the work.**

*The domain has two walls, not one.* The empty knowledge base is reachable when
`A′` takes every fact, and it **wins outright** — it covers every member at
`r = 2`. Excluding only disconnected candidates would have left the worse defect
standing. Neither this session nor `[IsalHG-Fable]` saw it.

*The change reintroduced the fork-poisoning hazard.* With `w*_c` in the tie
break the consensus reaches the C++ engine; Corpus A ran it **unguarded in the
parent** (`consensus_budget_s: null`), and one in-parent fingerprint flips
`cpp_fork_is_healthy` to False, after which **every later guarded build is
written `censored=1` without running** — silent corruption of the medoid rows,
caused by my own brief. Fixed with `cpp_engine=True` and a Corpus A budget of
1800 s. The agent also found `run_guarded`'s docstring claim that the medoid
loop poisons the parent is **false**: `medoid_matrix` forks.

**Flagged for the author, not decided:** D-ART4 (3) says "candidate key = the
Isal string"; this brief narrowed that to the tie break alone. Nothing is wrong
— the dedup key is invariant-neutral — but it is a narrower reading than the
ruling's words, and the agent followed the brief rather than widening scope
silently.

**Consequence:** RQ3 re-runs under the corrected objective once the suite
confirms. At 4.0 % movement over 4,457 Corpus A collections, roughly 180
collections change, so the published numbers move slightly and the re-run is not
optional.

### The suite's two unexplained failures were load, not a mismatch — D-ART5 stands

The full-suite run over the merged consensus change gave **8 failed / 2,942
passed**, reproducing the agent's result exactly. Two failures were ones this
session had not seen before, and they guard D-ART5's own claim:
`test_orbit_matches_unpruned_wstar_c[wd50k66]` and `[ndc_classes]`.

Settled before submitting anything:

| run | result |
|---|---|
| inside the full suite, three ssh monitors + an agent active | **2 failed** |
| the same two tests alone | **2 passed** (254 s) |

The test compares only where the unpruned arm completes, then requires 12
successful comparisons. A value mismatch would be **deterministic** and would
have failed in isolation too; it did not. So the failing assert is the count
guard — under load more members exhaust the 60 s budget, fewer pairs are
comparable, and the test fails having found no disagreement at all. Filed as
**T-KBr**.

Neither recent merge could have caused it either: the consensus change touched
`rq3.py`, `consensus.py`, `language/__init__.py`; the `reach′` change touched
`reach.py`, `consensus.py`, `ladders.py`. The test calls `budget.engine_word`
directly, through neither path.

**And the claim never depended on this test.** D-ART5 rests on 7,013/7,013
identical words, 130,788 identical single-edit distances and 5,174 ladder
pairs, with the matrices job independently reproducing RQ1's censoring census to
the member id. The 25-member contract check is the weakest evidence for that
claim, not the strongest — which is exactly why a load-sensitive verdict on it
is worth fixing rather than tolerating.

### Correction — the empty knowledge base is real but narrow, and it never happened in the corpus

`[IsalHG-Fable]` challenged the arithmetic of "the empty KB wins outright" and
was right to. The bound is `|A′| + |B′| ≤ r = 2`, so `K_i − A′` is empty only
when `K_i` carries at most two facts, and ∅ covers a member only when that
member's facts can all be deleted inside the same budget. Corpus A sources carry
`4 ≤ m ≤ 12`, so ∅ can only arise from a member already reduced to `m ≤ 2` by a
`t = 2` deletion, and can only win when **every** member of the collection is at
`m ≤ 2`.

The fixture confirms the bound rather than straining it. `EMPTY_WINNER` in
`tests/unit/language/test_consensus_domain_tiebreak.py:129` is documented as
*"two two-fact members"* — both members at `m = 2`, `r = 2`. It was found by a
search over **random** variant collections (seed 20260910), not in Corpus A.

**And it never occurred in the real corpus:** the audit over 323 Corpus A
collections across all 24 cells found **zero** out-of-domain winners of any
kind, empty or disconnected.

So the accurate statement is: *the domain has two walls, and the exclusion
guards both; on the real corpus neither was ever breached.* My earlier wording
let "wins outright" imply it was happening in Corpus A. It was not, no bound is
violated, and the candidate set is the pre-registered one. The guard stays —
∅ is out of domain for the same reason a disconnected candidate is — but it is a
**guarantee, not a repair**, and the rows were never wrong.

### No fork-poisoning residue is possible

Fable asked whether any harvested deliverable contains rows from a run made
after `w*_c` entered the tie break and before `cpp_engine=True` landed.

**There was no such window.** Both changes are in the same commit, `60c9b98` —
the tie break, `cpp_engine=True` and the Corpus A `consensus_budget_s: 1800`
were never separately deployed. The first cluster run on this code is the RQ3
pilot 2275979, submitted after the merge. Nothing on disk can carry poisoned
rows.

Its detector is still worth having as a **standing** check rather than for this
instance: RQ3's medoid screen runs the same engine at the same 60 s budget on
the same members as RQ1, so its censored set should be RQ1's restricted to the
collections in play, and a count materially above that is poisoning rather than
cost. That is a cheap in-run assertion and catches the class, not the case.
Folded into T-KBm's acceptance, which already covers censoring that reports
success it did not earn.

### Pre-registered validity check on `winner_origin` — committed before the re-run lands

Proposed by `[IsalHG-Fable]` and recorded here **before any value of the new
field has been looked at**, so it can fail.

**The prediction.** On Corpus A, `winner_origin` must read `transfer` on **at
least 83.5 %** of runs.

**Why it is forced, not expected.** `variant_collection` builds members that are
pairwise non-isomorphic *and* non-isomorphic to the source (`ladders.py`:
`fingerprints = {source_fingerprint}`, and a candidate whose fingerprint is
already present is rejected). So no member lies in the source's isomorphism
class. Exact recovery is `|F(out) △ F(truth)| = 0`, i.e. the winner *is* the
source — stronger than isomorphic. And `origin` labels a class by how it was
first produced, keeping `member` only for a class first produced as a member,
which the source's class cannot be. Therefore **exact recovery implies a
transfer winner**, and the transfer fraction is bounded below by the measured
recovery rate of 0.835. Plausibly higher, since a transfer candidate that is not
the source can also win.

**What a failure would mean.** A transfer fraction materially below 0.835 does
not describe the corpus — it means either the new field is wrong or the recovery
number is. Either way the distribution must not be used to write the Corpus B
supplement until it is resolved.

**Why this is a test of the instrument and not a finding.** Corpus A's answer is
derivable from what is already measured, which is exactly what makes it a
validity check. **Corpus B is where the measurement is informative**, because
nothing there predicts it: whether the consensus returns an input or a decoded
object no member wrote is the question that decides what the supplement can
claim, and D-KBf5a's gate result — a tie against the best medoid — reads very
differently depending on the answer. A tie achieved by returning inputs is a
medoid with extra steps; a tie achieved by returning decoded objects is the
capability claim holding on real data.

### The pilot under the corrected objective — instrumentation live, prediction consistent

Pilot 2275979 (`IEEETKDE_isal_consensus/`), 8 coverage rows:

| field | value |
|---|---|
| `winner_origin` | `transfer:i,j` on **8 of 8** |
| transfer fraction | **1.0000** |
| exact recovery | 1.0000 |
| `winner_connected` | **1.0 on all 8** |
| `n_disconnected_candidates` | 0 on some collections, **10** on another |

The pre-registered check is **consistent**: transfer 1.0000 ≥ the 0.835 bound.
It is also a *weak* instance — recovery is 1.0 on this tiny smoke, so the bound
is trivially met. The real test is the full run, where recovery is 0.835 and the
bound has room to fail.

The instrumentation works end to end: one collection generated **10 disconnected
candidates**, all were excluded, and its winner is connected — the guard doing
its job on real data rather than on a fixture. Medoid rows correctly carry empty
values for the coverage-only columns.

**A mis-read of my own, recorded because it is the second today.** I first
reported `winner_connected` as "not all 1" and treated it as a possible defect
in the fix. The field serialises as `'1.0'`, not `'1'`, and my one-liner
compared against the wrong string; every winner was connected. The earlier one
was the recovery-axis sign convention in `rq3_consensus_forensics.py`, which
printed "consensus worse in 3,723 of 3,723" for what was "better in 3,723 of
3,723". Both were caught by checking values against the summary rather than
trusting the summary — which is the only reason neither reached the ledger as a
finding. Ad-hoc analysis one-liners are the least-reviewed code in this campaign
and have now been wrong twice; anything they produce that would change a
conclusion gets re-derived from a committed script.

### RQ6's `reach1` is a lower bound, not a measurement — and it cannot be re-derived

RQ6 runs **bundled inside RQ3**, so job 2276107 is producing RQ6 rows now with
T-KBo unfixed. Two facts settle what to do.

**It cannot be repaired from disk.** `rows_samples.csv` carries only aggregates —
`reach1_frac`, `reach1_eligible`, `reach1_hits` — and the sampled hypergraphs
are not persisted. Re-deriving the column needs generation re-run.

**The current value is a lower bound.** `Reach1Index` buckets members by the
frozen precondition (constant count + type multiset) and so **withholds exactly
the pairs `reach′` admits**, which can only suppress hits. The measured
`reach1_frac = 0.0508` (45 hits of 885 eligible) is therefore a floor: the true
value under `reach′` is **≥ 0.0508**. Reported that way it is honest; reported
as a measurement it is not.

**The fix does not cost an RQ3 re-run.** `slurm/tkde/rq6_launcher.sh` runs RQ6
standalone, so T-KBo can be fixed and RQ6 re-run on its own — the RQ3 rows from
2276107 stand regardless, since nothing in RQ3 reads `reach1`.

Nothing else in RQ6 is implicated: validity 1.000, connectivity, fidelity and
the alignment interiors do not use the index. The headline results are unchanged.
