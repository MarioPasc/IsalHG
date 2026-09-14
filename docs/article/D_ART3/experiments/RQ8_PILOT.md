# RQ8 — valid completion of a record: the proposition, gate G0, gate G8.1

**Declared:** 2026-09-13, wave `2026-09-13-headline-w0`, agent `rq8`.
Pre-registration: `HEADLINE_DESIGN_2026-09-13.md` §0, §2, §4. Every number below
was measured before the Picasso submission, as the gate requires; nothing here
was tuned, and no threshold was moved after a result was seen.

---

## 1. Proposition C.8 — the prefix property

**Proposition C.8.** Let `K` be a connected knowledge base and `w°(K)` its
ordered-walk program. For every `u ∈ Σ_HG*`, the word `w°(K)·u` decodes, the
decoded knowledge base is connected, and it contains every constant and every
fact of `K`.

*Proof.* The decoder `S2H` is a deterministic machine reading one token at a
time: its state is `(H, L, p_1, …, p_k)` and each token is a total function on
that state. After consuming the prefix `w°(K)` the machine is in the state the
emitter simulated, so `H = K` up to the round-trip isomorphism (Lemma C.3) and
in particular `K` is connected.

It remains to show that no token, applied to a state whose `H` is connected and
contains `K`, can leave a state whose `H` fails either property. The alphabet
has five tokens and the argument is one line each:

* `P_i` and `N_i` move a pointer along `L`. They do not touch `H`, so both
  properties are preserved trivially.
* `W` is a no-op. Same.
* `C_i` adds the hyperedge over the constants at `p_1, …, p_i`, all of which are
  already in `L` and therefore in `H`. It adds a fact and removes none; the
  vertex set is unchanged, and a new edge over existing vertices cannot
  disconnect a connected graph.
* `V_{i,j}` adds one hyperedge over the `i` constants at `p_1, …, p_i` together
  with `j` freshly created constants, which the machine chains into `L`
  immediately after `p_1`. Again no fact and no constant is removed. The `j` new
  constants are not isolated: they lie in the new fact, which also contains the
  constant at `p_1`, an existing one — so each new constant is adjacent in the
  primal graph to a vertex of the already-connected component, and the result is
  connected. (`i ≥ 1` holds by the alphabet's own constraint `1 ≤ i`, which is
  what makes this step work; a token adding only fresh constants would not
  exist in `Σ_HG`.)

No token removes a fact or a constant, and no token disconnects. By induction on
`|u|` the claim holds for every continuation. ∎

**Corollary.** A sequence model over `w°` words, conditioned on `w°(K⁻)` as a
prefix, proposes only valid, connected knowledge bases that extend `K⁻`. Its
validity and connectivity are therefore 1.000 *by theorem*, not by filtering —
which is what H8.3 asserts and what the measurement below confirms. No
certificate and no vector fingerprint admits a completion operation at all,
which is why the non-generative rows of every RQ8 table carry the cell
"no completion definable" rather than a number.

**Empirical row beside the proof.** Two independent checks, both green:

| check | scope | result |
|---|---|---|
| pre-implementation probe | 25 members × 8 random continuations × 2 corpora = 400 | 400/400 decoded, 400/400 connected, 400/400 ⊇ `K⁻`, 0 failures |
| property test in the suite | `tests/experiments_tkde/test_rq8_prefix_property.py`, 4 base knowledge bases × 40 random continuations, plus a hypothesis pass at 60 examples | all green |
| the campaign itself | every `ow_ngram` unit of gate G8.1 | validity 1.0000, connectivity 1.0000 on both corpora |

---

## 2. Gate G0 — the star census

`is_star` as frozen in the design §2: **some constant occurs in every fact, and
every other constant occurs in at most one.** NDC declares no root, so the root
is existentially quantified rather than supplied — which is the design's own
phrasing, and makes the census independent of any root convention.

**Root convention** (used only for the *non-root* qualifier of the
interior/pendant rule, never by the census): the root is the **hub** — highest
fact-degree, ties by smallest constant id. On a star this is exactly the
constant contained in every fact, so nothing in §2 depends on the choice.

| corpus | N | stars | fraction | non-stars | non-star shared constants (median / mean) | non-star shared facts (median / mean) |
|---|---|---|---|---|---|---|
| `ndc_classes` | 1,381 | 42 | **0.0304** | 1,339 | 2 / 2.938 | 3 / 3.500 |
| `wd50k66` | 3,988 | 2,128 | **0.5336** | 1,860 | 3 / 3.254 | 4 / 4.719 |

Substrate pool at `m ≥ 4`, which is what RQ8 draws from:

| corpus | pool | non-star | star | non-stars with ≥ 1 interior fact |
|---|---|---|---|---|
| `ndc_classes` | 522 | 521 | 1 | 521 / 521 |
| `wd50k66` | 2,775 | 1,641 | 1,134 | 1,641 / 1,641 |

**Reading.** The design's pre-stated mechanism is confirmed quantitatively.
WD50K(66) is 53.4 % stars — structure exists in 46.6 % of WD50K entity
descriptions — and NDC-classes is 3.0 % stars, i.e. genuinely relational.
WD50K therefore supplies both strata and is where the star control lives.
**NDC's star stratum is a single member and is not a reportable stratum**; it is
printed as `n = 1, not reportable` rather than silently omitted, and the runner
refuses a stratum below `min_pool` with a logged warning.

The `rq3v2` agent computed its own copy independently and agrees to the member
(42 / 2,128).

---

## 3. Gate G8.1 — the local pilot

**Design, and why it cannot have tuned anything.** Three seeds, 200 interior
units per corpus per seed, every arm. The campaign runs the G7 schedule
`seeds(8, 27) = 80000…80026`; the pilot runs `seed_offset: 900`, i.e.
**80900–80902**, which lie outside it. The 80/20 split is drawn from the seed,
so the pilot's evaluation members and hidden facts are disjoint from every unit
the 27-seed run will score. The offset also enters the run tag, so no pilot row
can ever be served to the campaign.

### hit@10 and pattern@10, interior units, non-star stratum

`hit@10` **is** `usable@10`: a proposal counts only if it decoded, is connected,
and carries the truth's certificate. There is no separate corrected column.

| corpus | arm | N | hit@10 | pattern@10 | validity | connectivity | pattern right, attachment wrong |
|---|---|---|---|---|---|---|---|
| `ndc_classes` | **`ow_ngram` (ours)** | 600 | 0.1067 | 0.3750 | **1.0000** | **1.0000** | 0.716 |
| `ndc_classes` | `ow_ngram_ho` (secondary) | 600 | 0.1417 | 0.3850 | **1.0000** | **1.0000** | 0.632 |
| `ndc_classes` | `pattern_cooc` | 600 | **0.3033** | **0.8917** | 1.0000 | 1.0000 | 0.660 |
| `ndc_classes` | `pattern_freq` | 600 | 0.1867 | 0.4400 | 1.0000 | 1.0000 | 0.576 |
| `ndc_classes` | `fact_ngram` | 600 | 0.0950 | 0.3667 | 1.0000 | 0.8670 | 0.741 |
| `ndc_classes` | `incidence_ngram` | 600 | 0.0117 | 0.2700 | 0.1695 | 1.0000 | 0.957 |
| `ndc_classes` | `random_pattern` | 600 | 0.0267 | 0.0833 | 1.0000 | 1.0000 | 0.680 |
| `wd50k66` | **`ow_ngram` (ours)** | 600 | **0.0150** | 0.7317 | **1.0000** | **1.0000** | 0.979 |
| `wd50k66` | `ow_ngram_ho` (secondary) | 600 | 0.0100 | 0.6350 | **1.0000** | **1.0000** | 0.984 |
| `wd50k66` | `pattern_cooc` | 600 | 0.0133 | 0.7067 | 1.0000 | 1.0000 | 0.981 |
| `wd50k66` | `pattern_freq` | 600 | 0.0083 | 0.5850 | 1.0000 | 1.0000 | 0.986 |
| `wd50k66` | `fact_ngram` | 600 | 0.0050 | 0.7417 | 1.0000 | 0.5116 | 0.993 |
| `wd50k66` | `incidence_ngram` | 600 | 0.0000 | 0.4067 | 0.1427 | 1.0000 | 1.000 |
| `wd50k66` | `random_pattern` | 600 | 0.0000 | 0.0317 | 1.0000 | 1.0000 | 1.000 |

### What the gate decides

**H8.1 fails on `ndc_classes` and is a wash on `wd50k66`.** `pattern_cooc`
scores 0.3033 against our 0.1067 on the corpus the design calls genuinely
relational — the stratum where the headline was stated. On `wd50k66` ours leads
0.0150 to 0.0133, which at these rates is noise. The **pre-registered fallback
therefore applies**: the claim reduces to H8.3 plus the measured gap to the
recommender, and **RQ8 is a supporting exhibit, not a headline**. Ruled by the
orchestrator, 2026-09-13, before submission.

**The attachment reading of this table is WITHDRAWN — see §3b.** It was computed
on an unmatched denominator: `ow_ngram` is free-running and only 31.6 % of its
accepted proposals add exactly one fact, so a proposal carrying the right
pattern plus two unrelated facts was scored as an *attachment* miss. The
corrected, fact-count-matched numbers are in §3c, and they reverse the sign of
the effect. What survives from this table unchanged: the gap on `ndc_classes` is
a **pattern-prediction** gap (`pattern@10` 0.375 against 0.892), not an
attachment gap, and H8.1 fails.

**The secondary arm was enabled by the pre-registered rule, and it does not
close the gap.** The rule fired: `0.1067 < 0.5 × 0.3033 = 0.1517` on
`ndc_classes`. The design named a one-layer GRU; torch is absent from the
campaign environment and adding a dependency was out of scope, so the
orchestrator substituted **`ow_ngram_ho`** — a higher-order n-gram (order 6,
same interpolated Kneser–Ney smoothing, same training words), declared before
the pilot's second pass so it can never be read as post hoc. Order 6 buys
+0.035 `hit@10` on NDC and loses 0.005 on WD50K, and `pattern@10` barely moves
(0.375 → 0.385). It closes about a sixth of a 3× gap on one corpus and nothing
on the other. The finding is a sentence about sequence models, not about the
language: **the n-gram family is a weaker pattern predictor than item–item
co-occurrence.** The arm stays in the full run regardless.

**H8.3: two clauses hold, the third is inapplicable as written and was not
relaxed.**

* ours valid **1.0000** and connected **1.0000** on both corpora — the theorem,
  clean;
* `fact_ngram` connectivity 0.8670 / 0.5116, below 1 as predicted;
* `incidence_ngram` validity 0.1695 / 0.1427, **not** below the pre-registered
  0.05. **The number was not moved.** The 0.05 ceiling was ported from RQ6,
  where sampling is *unconditional*; under *conditional completion* the prefix
  is itself a well-formed serialization, so a truncated continuation decodes far
  more often and the threshold is measuring a different experiment. The clause
  is reported failed with that reason. The paper's sentence is the measured
  0.17 / 0.14 against 1.000 by theorem, which is enough.

### Two construction decisions that would otherwise have measured the harness

Both were found by reading the first smoke's numbers, both are pinned by
regression tests shown failing against the pre-fix behaviour, and both are
recorded here because each changes a reported column.

1. **The incidence prefix drops its `("END",)` terminator.** Keeping it put
   every continuation after the point the strict decoder stops at, so the arm
   decoded its own prefix every time and reported validity **1.0000** — the
   inverse of the H8.3 contrast. Measured on `ndc_classes`: 1.0000 with the
   terminator, 0.1718 without. The declared constant count *is* kept, because
   that is a real constraint of the flat language: a completion over a new
   constant contradicts it and is rejected.
2. **A counting arm whose attachment reproduces an existing fact emits nothing**
   rather than an invalid proposal. Recorded as invalid, it put a counting
   artefact in the validity column at 0.5 — the column H8.3 is read from.

One baseline-strengthening decision, stated so it is not mistaken for a thumb on
the scale: the attachment heuristic retries **three positions** down the degree
ranking when its top choice repeats an existing fact, and anchors on the hub
when no operand type occurs in the record. Without the retry a deterministic
heuristic emits at most one proposal per pattern and the recommender is capped
below `k`; without the hub anchor it would score the recommender's connectivity
instead of its recommendation. Both strengthen the baseline, never ours (L12).

The counting arms rank **3·k = 30** patterns rather than `k`, for the same
reason: a pattern whose attachment is refused must not cost a slot. The extra
depth is measured **inert** — at the pilot `pattern_cooc` consumed **9.60
patterns per unit** to fill ten slots, so ranks beyond the first ten are
essentially never reached and cannot be inflating the recommender.

---

## 3b. Amendment A1 — the fact-count-matched comparison (pre-registered 2026-09-13, before re-measurement)

**Declared before any number below the amendment was computed.** An
independent read-only review of `rq8.attach` found no leakage and no spec
violation, but one real asymmetry between the arms, which invalidates the
attachment sentence of §3 and required a matched arm before anything further
could be read.

**The asymmetry.** A counting arm attaches exactly one fact by construction, so
every one of its ten proposals is a candidate for a truth that has exactly one
more fact than `K⁻`. `ow_ngram` is free-running: it continues until the end
token, so its accepted proposals add *whatever the model writes*. The review
measured, on 40 `ndc_classes` non-star units at seed 80900: **607 of 1,923
accepted `ow_ngram` proposals add exactly one fact (31.6 %); median 2, max 35.**
Two consequences, both of which distort §3:

1. Roughly two thirds of ours' ten slots are spent on proposals that cannot be
   a hit at all, so `hit@10` compares ten candidate completions against roughly
   three.
2. The attach-miss statistic `pattern_hit ∧ ¬hit` counts an *extra-fact* miss
   as an *attachment* miss, because a proposal carrying the right pattern plus
   two other facts is not isomorphic to the truth for a reason that has nothing
   to do with attachment.

On the review's matched counterfactual (first ten distinct one-fact proposals)
`hit@10` moves 0.075 → 0.100 and attach-miss 0.750 → **0.556, below
`pattern_cooc`'s 0.660** — the sign of the §3 attachment sentence reverses. The
headline ordering does not change (0.100 against 0.303; `pattern@10` 0.225
against 0.892) and **H8.1 still fails**.

**What is amended, fixed here before re-measurement.**

1. **Δfacts is recorded per proposal** — facts added relative to `K⁻` — and
   aggregated per `(unit, arm)`. It was previously only thresholded at `> 0` and
   thrown away.
2. **Two matched arms are added:** `ow_ngram_1f` and `ow_ngram_ho_1f`. Same
   model, same seed, same draw sequence, same order and smoothing as their
   free-running counterparts; the *only* difference is the acceptance
   predicate, which becomes `Δfacts = 1` instead of `Δfacts ≥ 1`. They take the
   first ten distinct such proposals. **The R budget rule is unchanged and its
   value is unchanged: `R = 20` attempts per slot, ten slots, so at most 200
   draws — exactly the free arms' budget.** A stricter acceptance under an
   identical budget may leave slots unfilled; the fill is reported
   (`n_accepted`) rather than compensated, because raising `R` for one arm would
   replace the asymmetry being removed with a new one.
3. **The free-running arms stay exactly as they are.** `ow_ngram` and
   `ow_ngram_ho` are unchanged and still reported. The matched arms are an
   addition, not a replacement: "what the model writes" and "what the model
   writes when asked for one fact" are different questions and the paper reports
   both.
4. **attach-miss is computed only over Δfacts = 1 proposals, for every arm,**
   and the column is renamed so its denominator is explicit:
   `attach_miss | pattern hit on a one-fact proposal`. For the counting arms
   this changes nothing (every proposal is one-fact); for the generative arms it
   is the correction. Note that `hit` needs no restriction: the truth carries
   exactly one fact more than `K⁻`, so any proposal isomorphic to it necessarily
   has `Δfacts = 1`.
5. **The §3 sentence "the recommender attaches better than the generator" is
   withdrawn** and replaced by the matched numbers in §3c. It was computed on an
   unmatched denominator and does not survive the correction.

Two documentation mismatches the same review found, corrected here:

- The attachment retry goes **three positions** down the degree ranking, not
  one (`propose_patterns(attachment_ranks=3)`); §3's earlier wording said one.
- The counting arms rank **3·k = 30** patterns, not `k`, so that a pattern
  whose attachment is refused does not cost a slot. Measured inert: at the
  pilot, `pattern_cooc` consumed **9.60 patterns per unit** to fill ten slots,
  so the extra depth is never reached in practice and cannot be inflating the
  recommender.

## 3a-bis. Amendment A2 — the star control was a hole in the baseline (pre-registered 2026-09-14, before re-measurement)

**Declared before the re-run it governs.** At 27 seeds the star control came out
backwards: on `wd50k66/star` ours scored 0.1156 and `pattern_cooc` scored
**exactly 0.0000**. A recommender that never once proposes the right completion
on 27 seeds is not losing a contest; it is unable to enter one.

**The mechanism, and why it is the baseline's defect and not a finding.** A star
is a hub plus pendant facts, and a star's facts frequently **share a pattern** —
same predicate, same arity, same operand types, different leaf. The attachment
heuristic is deterministic: given that pattern it resolves to the hub plus the
highest-degree constant of the matching type, which *is* a fact the record
already carries, so the attachment is refused (§3's "an attachment reproducing
an existing fact is refused"). The three-deep rank retry does not rescue it,
because a star has few distinct constants of the required type. The baseline
therefore **cannot express "another instance of a repeated pattern"**, which is
precisely what a star completion is. The 0.0000 measures this implementation on
stars, not counting as such.

**What is amended, fixed here before re-measurement.** When the deterministic
attachment — and its rank retries — would reproduce a fact the record already
carries, the pattern is instead instantiated with **fresh constants**: the hub
takes one slot (pendant attachment) and every remaining operand is a newly
created constant of the required type. A fact over fresh constants cannot
duplicate an existing one, so the arm always has a proposal to make. This is
strictly **in the baseline's favour**; it takes nothing from ours.

**Scope of the re-run, and why it is only the star units.** The fallback fires
only where the old path emitted nothing, and on the non-star stratum that is
nearly never: at 27 seeds the counting arms already filled **9.9–10.0 of 10**
slots there (`pattern_cooc` 9.9 on `ndc_classes`, 10.0 on `wd50k66`;
`pattern_freq` and `random_pattern` 10.0 on both). At most ≈ 0.1 slots per unit
are lost to refusal on non-star units, so A2 can move those numbers by ≈ 1 % at
the very most, and the non-star tables of §3c and the campaign stand unchanged.
**Only `wd50k66/star` is re-run**, same 27 seeds, under its own run tag; the
analyzer merges the star rows with the non-star rows **by stratum**, refusing
any merge in which a `(collection, stratum, seed, arm, kind)` key appears under
two tags — so merging can never become pooling.

**What the re-measurement can show, both stated in advance.** If ours still
leads on stars once the recommender can propose, that is a **result** and the
star stratum stops being a control. If the recommender takes the lead, that is
the **expected control** of the design and it is reported as such. Either way
the 0.0000 is retired.

## 3a-ter. Amendment A3 — the counting baseline must learn attachment from data (pre-registered 2026-09-14, before re-measurement)

**Declared before the re-run it governs.** A2 lifted `pattern_cooc` off exactly
zero on stars, and the decomposition then showed it getting the *pattern* right
62.4 % of the time and the *attachment* wrong 93.5 % of the time. On a star,
where the correct attachment is always "fresh constants pendant to the hub",
that is not evidence that counting cannot attach — **it is a crippled
baseline**, and a reviewer will say so first.

**The defect.** The heuristic tries **existing constants of matching type
first**, and only falls back to fresh when that duplicates an existing fact. On
a star with repeated operand types the existing-constant choice is almost always
wrong, and the fallback fires only on exact duplication, so the arm is
systematically attaching in the one place a star completion never goes. That is
a **fixed rule**, while our arm learns attachment from the training words. The
comparison is therefore not between two attachers but between a learner and a
constant.

**What is amended.** For the pattern baselines (`pattern_cooc`, `pattern_freq`
and, for consistency of construction, `random_pattern`), attachment becomes
**data-driven**:

1. On the **training split only**, for each pattern `(predicate, arity, operand
   types)`, count its instances that are **pendant** — every operand other than
   the hub occurs in no other fact — against those that are **interior** — some
   non-hub operand is shared with another fact.
2. Propose the **majority form** for that pattern; **ties go to pendant**.
3. The interior form keeps the existing rule: highest-degree constant of
   matching type, with the three-position retry.
4. A2's fresh fallback remains underneath both, so the arm still never emits
   nothing.

**Nothing changes for our arms.** The before/after control of §5 is repeated:
every ordered-walk arm must come back byte-identical, and if one moves, the
amendment leaked and the re-run is void.

**Scope: both strata are re-run** — `ndc_classes/non_star`,
`wd50k66/non_star`, `wd50k66/star` — same 27 seeds, locally, under a new run tag
merged with `--supersede`. Unlike A2 this is not a star-local change: a
data-driven rule can move the non-star numbers too, and asserting otherwise
without measuring would repeat the mistake A3 exists to correct.

**What the re-measurement can show, both stated in advance.**

- **If the star lead is cut or reversed** — the expected outcome, since a
  majority-pendant rule attaches correctly on stars by construction, so the
  recommender's `hit@10` should climb toward its `pattern@10` of 0.624 against
  our 0.185 — then the star row becomes **the control §0 predicted**, and RQ8's
  claim rests on the **relational stratum only**. That is the stronger paper:
  the star loss then *explains* why the win is where it is.
- **If our lead survives a data-driven attacher**, it is a result about
  attachment that a fixed-rule baseline could not have established.

Either way it is measured, not argued.

## 3c. Gate G8.1, amended — the matched comparison

*Same three pilot seeds (80900–80902), same 200 interior units per corpus, run
tag `42875bca`. The §3 table is retained above as the free-running measurement;
this one is the fact-count-matched one. Both are reported.*

`Δ1 share` is the fraction of accepted proposals adding exactly one fact;
`Δ̄` their mean fact delta; `acc` the mean number of slots filled out of ten.
**attach-miss is `pattern hit on a one-fact proposal ∧ ¬hit`, over one-fact
proposals only** — for the counting arms this is unchanged, since every one of
their proposals adds one fact.

| corpus | arm | Δ1 share | Δ̄ | hit@10 | pattern@10 | attach-miss ∣ 1f | acc |
|---|---|---|---|---|---|---|---|
| `ndc_classes` | `ow_ngram` | 0.328 | 2.87 | 0.1067 | 0.3750 | **0.347** | 9.2 |
| `ndc_classes` | **`ow_ngram_1f`** | 1.000 | 1.00 | **0.1750** | 0.2883 | 0.393 | 7.2 |
| `ndc_classes` | `ow_ngram_ho` | 0.358 | 2.46 | 0.1417 | 0.3850 | **0.303** | 7.9 |
| `ndc_classes` | **`ow_ngram_ho_1f`** | 1.000 | 1.00 | **0.1950** | 0.2983 | 0.346 | 5.8 |
| `ndc_classes` | `pattern_cooc` | 1.000 | 1.00 | **0.3033** | **0.8917** | 0.660 | 9.9 |
| `ndc_classes` | `pattern_freq` | 1.000 | 1.00 | 0.1867 | 0.4400 | 0.576 | 10.0 |
| `ndc_classes` | `fact_ngram` | 0.199 | 4.34 | 0.0950 | 0.3667 | 0.287 | 8.0 |
| `ndc_classes` | `incidence_ngram` | 0.411 | 2.52 | 0.0117 | 0.2700 | 0.854 | 6.9 |
| `ndc_classes` | `random_pattern` | 1.000 | 1.00 | 0.0267 | 0.0833 | 0.680 | 10.0 |
| `wd50k66` | `ow_ngram` | 0.248 | 5.15 | 0.0150 | 0.7317 | 0.892 | 9.8 |
| `wd50k66` | **`ow_ngram_1f`** | 1.000 | 1.00 | **0.0383** | 0.2967 | **0.871** | 8.7 |
| `wd50k66` | `ow_ngram_ho` | 0.261 | 4.20 | 0.0100 | 0.6350 | 0.933 | 9.6 |
| `wd50k66` | **`ow_ngram_ho_1f`** | 1.000 | 1.00 | 0.0367 | 0.2917 | 0.874 | 8.2 |
| `wd50k66` | `pattern_cooc` | 1.000 | 1.00 | 0.0133 | 0.7067 | 0.981 | 10.0 |
| `wd50k66` | `pattern_freq` | 1.000 | 1.00 | 0.0083 | 0.5850 | 0.986 | 10.0 |
| `wd50k66` | `fact_ngram` | 0.234 | 7.93 | 0.0050 | 0.7417 | 0.944 | 9.5 |
| `wd50k66` | `incidence_ngram` | 0.447 | 2.81 | 0.0000 | 0.4067 | 1.000 | 6.8 |
| `wd50k66` | `random_pattern` | 1.000 | 1.00 | 0.0000 | 0.0317 | 1.000 | 10.0 |

### What the matched comparison changes, and what it does not

**The attachment sentence reverses, more strongly than the review's
counterfactual indicated.** On `ndc_classes`, every ordered-walk arm attaches
better than either recommender on a matched denominator: **0.303–0.393 against
`pattern_cooc`'s 0.660 and `pattern_freq`'s 0.576.** On `wd50k66`, where every
arm is near-hopeless, ours is still ahead (0.871/0.874 against 0.981/0.986). So
the design's §0 mechanism — *the completion must choose attachments, which the
generator learns and counting cannot* — **is supported on the attachment axis
after all.** The §3 reading that contradicted it was an artefact of the
unmatched denominator, and it is withdrawn.

**The `ndc_classes` loss is therefore entirely a pattern-prediction loss, and a
larger one than §3 showed.** Restricting to one-fact proposals *lowers*
`pattern@10` for the generative arms (0.375 → 0.288 and 0.385 → 0.298), because
the extra facts of a free-running proposal were incidentally covering the hidden
pattern. Against `pattern_cooc`'s 0.892, the matched gap is 3×. The n-gram
family is a weaker pattern predictor than item–item co-occurrence; it is the
better attacher. That is the honest decomposition.

**Matching moves ours materially, and on `wd50k66` it flips the ordering.**
`hit@10` rises 0.1067 → 0.1750 on NDC and 0.0150 → 0.0383 on WD50K — where the
matched arm now **leads every baseline**, `pattern_cooc` included (0.0383
against 0.0133, ~2.9×). `ow_ngram_ho_1f` is the best ordered-walk arm on NDC at
0.1950, above `pattern_freq`'s 0.1867 and still below `pattern_cooc`'s 0.3033.

**H8.1 still fails, now as a scoped failure rather than a flat one.** It asks
for ours above *every* baseline on the interior units of *both* corpora:
satisfied on `wd50k66`, not on `ndc_classes`. The pre-registered fallback still
applies and **RQ8 remains a supporting exhibit**; the 27-seed run decides
whether the `wd50k66` lead is Holm-significant, which three seeds cannot.

**Two readings of "matched", and which one is reported.** Re-reading the
*original* draws and keeping the first ten one-fact proposals among them gives
`hit@10` **0.100**; the pre-registered re-draw rule reported here — first ten
distinct one-fact proposals under the **unchanged** `R = 20` per slot, so a
rejected multi-fact draw costs an attempt and the arm keeps drawing — gives
**0.175**, and its price is the `acc` column, where the matched arms fill
5.8–8.7 slots of ten against the free-running 7.9–9.8. The re-draw rule is the
one written down before the numbers were seen, so it is the one reported;
unfilled slots are stated, never bought back with a larger budget.

**Status of each claim, for the prose fold.** The attachment mechanism is
**supported**. The `ndc_classes` deficit is a **pattern gap**. The `wd50k66`
lead is **untested** until the Holm-corrected comparison at 27 seeds — three
pilot seeds cannot test it, and it must not be quoted as a result before then.

---

## 4. Provenance

| what | where |
|---|---|
| pilot rows | `results/IEEETKDE_ow/RQ8/pilot/RQ8_completion/pilot_g8_1/` (drive) |
| pilot config | `experiments/tkde/configs/rq8_pilot.yaml` |
| campaign config | `experiments/tkde/configs/rq8.yaml` |
| runner / analyzer | `experiments/tkde/{rq8,analyze_rq8}.py` |
| tests | `tests/experiments_tkde/test_rq8_{units,prefix_property,smoke}.py` (82) |
| ledger | `docs/article/DEVELOPMENT/T-KB/IN-PROGRESS/T-KBaa.md` |
| job ids and campaign tables | `docs/article/D_ART3/foundation/rq8_facts.md` |
