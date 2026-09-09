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
