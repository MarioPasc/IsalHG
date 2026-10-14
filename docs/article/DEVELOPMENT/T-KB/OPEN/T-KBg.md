# T-KBg — the prose fold and the PI one-page reading

**Status:** OPEN · declared 2026-09-07 22:10 CEST by the Isal-refinement
orchestrator (handoff §5.4). Depends on T-KBe (numbers) and, for the RQ
sections, T-KBf.

## What

1. Fill the *pending* markers in `docs/article/D_ART3/prose.md` §2.3, §3 RQ1
   and §4 with the campaign table; then RQ2–RQ7 as they land.
2. The one-page PI reading (brief deliverable 4): which canonical program,
   why, its cost, what it still cannot do (the R-list updated: R1 lifted for
   deletions and entity-anchored growth, not for insertions over existing
   arguments; R2 lifted in C++; R3 a proved property; R4 filed; R5 kept;
   R6 no longer conceded for the deterministic programs), and the nauty
   sentence (design §7).
3. `START_HERE.md` §0/§0.1/§6.0: replace the fact-rank narrative by a short
   pointer to the handoff (a longer rewrite is not needed; the file is
   history). `DESIGN.md` G1: the representation definition.
4. The proof file: PI review; a `research-rigor` pass on §6 (locality)
   before submission; `humanizer` on every passage over 200 words.

## Acceptance

`prose.md` reads as the article with no pending markers; the PI reading is
one page; the ledger and `DECISIONS.md` carry D-ART5.

## Correction the campaign numbers force in `prose.md` §2.3 (2026-09-09)

The paragraph "The consequence the paper states itself" ends: "…plus the one
locality the Isal walk owns outright, **deletions**." The per-corpus,
per-regime table makes that imprecise in two directions and it must be
rewritten with D-ART5's numbers:

- Against the **certificate**, what the Isal word owns outright is broader than
  deletions and must be named by regime: the certificate is within two rows on
  **0.000** of pendant deletions, pendant narrowings *and* constant-bringing
  insertions, on every corpus.
- Against the **fact list**, deletions are not owned: on *interior* deletions
  the fact list is within two on 57.8 % against the Isal word's 13.9 %. The
  Isal word owns the **pendant** regime, not deletion as a category.

The distinction the sentence needs is pendant vs interior, not deletion vs
insertion — the regime, not the edit kind. See T-KBe for the tables and for the
naming ("pendant" = the edit changed the constant inventory; "interior" = it
did not; `add_constant`/`remove_constant` are arity widening/narrowing of one
fact, not inventory changes).

---

## The corrections this campaign forces — compiled 2026-09-10

Assembled while RQ4/RQ7/RQ3 were still running, so it lists **only items that do
not depend on their numbers**. Each is measured and recorded in
`T-KBf.md`; this is the work list, not the evidence.

### Retractions — statements currently in the docs that are false

1. **"The consensus is worse than the medoids and than the majority merge"**
   (`RESULTS_WALKTHROUGH.md`, Corpus B). Measured under `reach′`: the consensus
   is better in point estimate than **all eleven** medoid arms and best-equal on
   recovery. The sentence and its causal story — *"a natural series is not a set
   of variants of one source, so there is nothing for a consensus to converge
   to"* — must be **retracted in print**, not dropped. Corpus B still goes to
   the supplement, but by the pre-registered gate, not by that reason.
   Supersession notes are already in place at both sites.

2. **`prose.md` §2.3's "the one locality the Isal walk owns outright,
   deletions"** — already flagged in this file; the axis is **pendant vs
   interior**, not deletion vs insertion.

3. **"H3d fails"**, if written unqualified. Prop 3's *proved* bound holds on
   **all 4,457 certificates, zero violations**; only the empirical "max ≤ 1.7"
   expectation fails, at 1.7778. Reporting the failure without the theorem is
   the misleading half.

4. **RQ6's headline, if taken from `summary.json`.** The analyzer names the
   **retired** alphabet as ours (`MODEL_OURS = "fact_ngram"`), whose validity is
   1.000 but whose **connectivity is 0.271**. Σ_HG is 1.000 on both.
   `prose.md` §2.2 already quotes the right numbers; the code and the analyzer
   must be brought into line so a cold reader cannot quote the weaker result.

### Statements that must be added

5. **H3a's deletion clause demanded what no method achieves.** It required
   ≥ 0.95; `majority_merge`, the identity-using reference the design itself
   names, scores **0.208** on ndc `del t=2`. Say the threshold was
   mis-specified, on the merge's own number — this locates our 0.130 rather
   than excusing it.

6. **The consensus reaches the identity-using ceiling on insertions** — 1.000
   against the merge's 0.995 on ndc `ins t=2`, 1.000 on both wd50k insertion
   cells, while **every medoid arm recovers 0.000 in every cell**. This is
   RQ3's claim in its cleanest form and is currently understated.

7. **Two readings that go against us**, both measured, both required by the
   author's standing rule: `wl_l1` merges nothing on these three corpora, so
   Prop 9's incompleteness does not materialise on this data; and
   `bipartite_ged_path` fails exactness in the *other* direction, splitting 557
   true classes into 574 — "0 false merges" is not "exact at zero".

8. **RQ5 is not merely a null.** The naive degree-sequence floor beats us
   significantly on all four comparisons, with rank-biserial **−1.000** on both
   corpora — it wins on every seed. The metric-space article's S7 found the same
   on different corpora. One sentence, stated once: degree structure dominates
   clustering and the canonical string does not capture it.

9. **The Corpus B gate is underpowered**, and the caption must say so: MDE
   ≈ 0.40 fact-tokens against observed differences of 0.03–0.11, and only 8 of
   63 pairs informative on the recovery axis. "No difference was detected at
   n = 63", never "no better".

10. **The division of labour on invariants**, one clause, framed as design not
    defect: the fact word is the right *internal* key for remainders because it
    keys disconnected inputs; the Isal word is the right *representation*
    because it decodes only to knowledge bases. `RemainderIndex` must be
    described as "any complete invariant", never as `F°`.

11. **The methods sentence the defect pattern earns.** Every defect this
    campaign found sat where the pipeline still used the retired representation
    or touched objects outside the representation's domain — both fact-rank-era
    residue. Worth one sentence, because it is also the reason the reader should
    trust the arm set now.

### Housekeeping already known

12. `START_HERE.md` §0/§0.1/§6.0 and `DESIGN.md` G1 still carry the fact-rank
    narrative (predates D-ART4).
13. The caption clause on the per-comparison interval beside the Holm-corrected
    p, and the rank-biserial replacing the difference-of-means for median rows.
14. Name the regimes in words — **pendant** = the edit changed the constant
    inventory, **interior** = it did not — and state once that
    `add_constant`/`remove_constant` are arity widening/narrowing of one fact.

---

**2026-09-10 — PRECONDITION added (not a step inside the fold).** The fold does
**not start** until every number it would carry has an entry in
`docs/article/D_ART3/foundation/` naming its run root, job and table. Anything
unsourceable is **struck, not kept**.

Reason, measured rather than anticipated: three different figures for the
fact-list generator's connectivity were circulating one sentence apart in
`prose.md`, and one of them (`256/1,000`) matched no run on disk. Re-sourced, it
moved **against us** on NDC — the real value is 0.4157, better for the
comparator than the number we were quoting. The first RQ6 fact base is
`foundation/rq6_generation_facts.md`; the rest of the campaign's numbers need
the same treatment before the fold.

Already known to be stale or unsourceable, and **do-not-quote** until re-derived:

| number | status |
|---|---|
| `rows_samples.reach1_frac` "4.7 % / 9.6 %" | ~~do-not-quote~~ **RESOLVED**: struck; the sourced values are in `foundation/rq6_generation_facts.md` from job **2279079**, which passed the pre-registered check with all six eligible counts exact. Quote the three-column form (validity, reach1-given-valid, joint), never `reach1_frac` alone. |
| completion "within reach 1 75.3 % / 21.0 %" | pre-`reach′`; under `reach′` **76.7 % / 21.3 %** |
| "256 / 1,000" and "disconnected three times in four" | struck; the sourced values are 0.4157 (NDC) / 0.1260 (WD50K), and no single ratio describes both |

**2026-09-11 — sequencing, not relaxation.** The precondition gates **each
number at the moment it is folded**; it does not require all seven fact bases to
exist before any folding begins. The distinction matters because **a stale entry
is worse than a missing one — a missing entry blocks, a stale one passes** — so
an entry built for an experiment whose numbers can still move is work done twice
and a hazard the second time. Sequence by finality:

| RQ | state | action | prose mentions |
|---|---|---|---|
| RQ1 | **fact base written** — `rq1_addressing_facts.md`; 33/33 figures sourced, 0 unsourced | **screened**, awaiting predicate pass | 19 |
| RQ2 | **fact base written** — `rq2_wellposedness_facts.md`; the fold here is a **fill**, not an audit | **screened** | 7 |
| RQ6 | `rq6_generation_facts.md` | done | 10 |
| RQ7 | `rq7_envelope_facts.md` | done; revisit at 2271961 terminal | 6 |
| RQ3 | **verified unsettled** — re-runs under the corrected objective; ~180 of 4,457 collections change, "the re-run is not optional" (T-KBf L1411) | **blocked on the campaign** | 11 |
| RQ4 | depleted `iso_twin` cell awaiting the author | premature | 4 |
| RQ5 | status unchecked | check before building | 2 |

**RQ1 first, and not as clerical work.** It is the most cited and the most
settled, and its frozen deliverable makes sourcing a lookup rather than a
re-derivation — the seventeen files include the tables the numbers came from.
But all three of the 2026-09-11 corrections (a count reconstructed from a rounded
rate; sweep lengths quoted beside a `wd50k66` timing; a mean quoted as a
per-member cost) came out of exactly this exercise on RQ7's six mentions.
Nineteen mentions against a frozen deliverable is the largest single opportunity
for the same class, so **budget for it to find things**, and hold the rule when
it does: a number that cannot be sourced is **struck, not investigated into the
prose**.

This is an engineering precondition (it is not in `DECISIONS.md`), so the
sequencing is recorded here with its reasoning rather than referred upward.
Raised by `[IsalHG-Fable]`.

**2026-09-11 — "entry exists" was an aggregate, and the walk finds gaps.**
`[IsalHG-Fable]`: marking RQ6 *done against 10 mentions* and RQ7 *done against 6*
is an aggregate statement about a **per-number** requirement. Neither entry was
built by walking that RQ's prose mentions; each was built around the numbers
under discussion when it was written. Run rather than argued — every distinct
figure within ±1 line of an RQ6/RQ7 mention in `prose.md`, resolved against the
campaign fact bases:

| | |
|---|---|
| distinct figures near those mentions | **25** |
| resolve to a campaign `rq*_facts.md` | 19 |
| resolve to **none** | **6** |

So the precondition passes at RQ granularity and fails at number granularity —
the same aggregate-over-rows shape as everything else in this session, and the
worse case, because **a row marked done is one nobody re-checks**.

Of the six, chased against *every* `foundation/` file:

| figure | where it resolves |
|---|---|
| **1,300** | **sourced** — see the correction below; *not* struck |
| 74.8 % | `probes_2026-09.md` (a probe, not a campaign measurement) |
| 0.49, 0.62, 0.96 | `measured_facts.md` + probes — **the other article's file** |
| 6.1 | `measured_facts.md`, `proved_facts.md` |

**And the audit method is itself unsound, which is the more useful finding.**
Matching a figure as a *digit substring* over-reports: a bare `0.62` appears in
many documents by coincidence, so "resolves to `measured_facts.md`" is more
likely a collision than a provenance — and `measured_facts.md` is the **other
article's** fact base, the hazard flagged the same day. A numeric-substring sweep
is therefore a **screen, not an audit**: it can prove a number *unsourced*
(1,300 is, definitively) and cannot prove one *sourced*.

That is precisely what the **predicate pass** below exists for, and this
measurement is its justification rather than an alternative to it: provenance has
to match the number **together with its noun and its run**, not the digits. The
screen is still worth running first — it found 1,300 in seconds — but a figure it
marks resolved must still pass the predicate pass before it is folded.

#### Correction, same hour — 1,300 is sourced, and striking it would have been the worse error

`[IsalHG-Fable]` placed it and the quote checks out. `HANDOFF_2026-09-07_isal.md`
line 18, on the C++ ports:

> each port bit-identical to its Python reference on every differential (both
> full corpora for the ordered walk; **700 + 600 instances for the orbit path**;
> 1,000 + 300 + 300 for the rank key)

**700 + 600 = 1,300**, and `prose.md` uses it correctly — "implemented in C++,
bit-identical on 1,300 differentials" is the *port* differential. (Distinct from
the **7,013/7,013** at D-ART5, which verifies the same property — orbit pruning
is value-preserving — by a different route. Both are real and they are not
substitutes.)

**So the general rule, which matters more than the instance: absence from
`foundation/` is not absence of a source.** The wave records, the design
document's §9, the decision record and the test suite are all sources, and a
numeric sweep of `foundation/` searches none of them. A screen that reports
"unsourced" is reporting **"not found in the files I looked at"**, which is a
statement about the search, not about the number.

Had the strike gone ahead it would have deleted a true, well-evidenced figure —
**a worse outcome than the unsourced numbers the precondition exists to catch**,
because a struck number leaves no trace to recover and the evidence for it stays
exactly where it was, unread. So: **nothing is struck on a screen's say-so.** A
strike requires a search of the wave notes, `DESIGN.md`, `DECISIONS.md` and the
tests, and the screen's role is to produce the candidate list, not the verdict.

**Consequence for the table above:** RQ6 and RQ7 move from *done* to
**screened**; 1,300 is sourced to the handoff and needs a `foundation/` entry
citing it rather than a strike; five figures need the predicate pass. No entry is *done* until the bidirectional walk plus the
predicate pass have both run against it.

**2026-09-11 — a corpus correction propagates to every figure derived from it,
and only the counts were checked.** `[IsalHG-Fable]` traced 74.8 % to the
pre-freeze census. Verified against the built corpus's own `census.json`
(`corpora/ndc_classes/`), which names the exact quantity:

| | built corpus | pre-freeze |
|---|---|---|
| `n_consecutive_pairs` | **528** | 555 |
| `n_pairs_constant_changing` | **400** | 415 |
| changing / consecutive | **0.7576 → 75.8 %** | 0.7478 → 74.8 % |

`prose.md` line 525 carried **74.8 %**. **Corrected to 75.8 % (400 of 528)** —
the one figure where the census names the quantity outright, so the substitution
is a lookup rather than an inference.

**The sibling sweep found more, and they are flagged rather than corrected.**
Line 502 describes the corpus as *"NDC-classes … (**1,432 members**, **21.6 %**
of consecutive quarters one-edit variants …)"*:

* **1,432** is the singleton-counting figure. `DESIGN.md` §corpora is explicit
  that the built corpus is **1,381** and that 1,432 is "the supplement's figure".
  The prose describes the corpus actually used, so it should say 1,381.
* **21.6 %** — resolved, and the method generalises. `[IsalHG-Fable]`:
  **reproduce the stale figure from the stale census.** `probes_2026-09.md`
  records the pre-freeze Δ histogram as **85 / 120 / 134 / 191 / 25** over
  **555** pairs (sums exactly), and `120 / 555 = 0.21622` → **21.6 %**, the
  prose's figure to three digits. A three-digit reproduction under the proposed
  reading is not coincidence, so *"one-edit variants"* **is** `delta_1`,
  established by construction with no code read. Corrected to
  `117 / 528` = **22.2 %**.

  **The general method: when a stale figure's definition is unclear, try to
  regenerate it from the superseded inputs.** If they reproduce it, the
  definition is settled and the correction is a lookup; if nothing reproduces
  it, *that is the finding* and the number goes to the predicate pass or to a
  strike under the condition above. It is cheaper than reading the code, it is
  checkable by anyone, and it inverts the usual difficulty — a stale number is
  normally a liability, and here **its staleness is the evidence**, because only
  the superseded inputs regenerate it.

**The general defect: the member-count reconciliation (1,432 → 1,381) was
propagated to the counts and not to the ratios computed over them.** A
member-count check cannot see it, because the exposed figure is a percentage.
So the fold's checklist gains a step: **after any corpus correction, re-derive
every figure computed *over* the corrected counts, not just the counts.**

**And the screen is a closed list, not a heuristic.** "Any percentage whose
denominator is a corpus quantity" both misses cases ("12 of 100" phrasings,
medians, per-member rates) and chases percentages unrelated to the corpus. The
bounded form: **the census's own fields are the complete set of exposed
quantities**, so for each field, find its value *and every ratio over it* in the
prose and check both against the built census. Run over `ndc_classes`'
twenty fields:

| | |
|---|---|
| stale values found in `prose.md` | **2** — `1,432` members, `21.6 %` |
| both corrected | 1,381 and 22.2 % |
| remaining flags | **2, both false positives**: `415` occurs inside another figure on the Prop 2 row, and `delta_gt5` is 25 in *both* censuses |

It found both of today's in **one pass**, where the sibling sweep found them one
after the other. The residual weakness is unchanged and must be stated: it
matches **digit strings**, so it yields candidates and the two flags above had to
be checked by hand. Bounded and complete beats unbounded and heuristic; neither
is an audit. (Raised by `[IsalHG-Fable]`.)

**2026-09-11 — the screen run over all five corpora, and improved so it needs no
pre-freeze census.** `[IsalHG-Fable]`: the reconciliation covered two corpora and
only `ndc_classes` had been swept. Correct, and the hit was where predicted.

**First version was the wrong shape.** It searched the prose for each census
field's **built** value and reported presence — which cannot detect staleness
without already knowing the superseded value, so it found the `ndc_classes`
figures (whose pre-freeze values I had) and nothing in the other four.

**The form that works: near-miss detection.** A prose integer **within 1 % of a
census value but not equal to it** is a stale-value candidate. No pre-freeze
census required, so it generalises to every corpus whose old numbers are not to
hand. Run over all five collections:

| corpus | census mismatches | prose hit |
|---|---|---|
| `wd50k66` | 2 | **3,167** against `n_records_with_arity_ge3` = **3,162** |
| `ndc_classes` | 10 | (the two already corrected) |
| `wd50k100` | 1 | none |
| `ndc_substances` | 3 | none |
| `wd50k66_full` | 0 | none |

`prose.md` §7 described **"3,167 genuinely n-ary members in the envelope"** — the
pre-freeze value, in the same paragraph shape as the 1,432, in the paper's
largest collection. **Corrected to 3,162.**

**Three prose corrections, all from one reconciliation that stopped at the
counts:** 74.8 → 75.8 %, 1,432 → 1,381 with 21.6 → 22.2 %, and 3,167 → 3,162.

**Residual after the sweep: none.** Two remaining candidates are false positives
and are recorded as such — *"one in 578"* is a collision rate unrelated to
`ndc_substances`'s `delta_gt5` = 576, and `1,381` is `n_records` (correct),
flagged only because the adjacent `n_records_with_arity_ge3` = 1,380 sits one
away. **Adjacent census fields differing by a hair will always flag**, which is
the near-miss screen's own cost and is cheaper than the figure it catches.

**2026-09-11 — the screen is now a script that gates, and screen 1 is exact.**
`scripts/diagnostics/corpus_figure_screen.py`, **exit non-zero on any open
candidate** so it can hold the fold rather than merely inform it.

**Screen 1 (primary, exact).** `[IsalHG-Fable]`: `freeze_corpora.py` already
records the answer. Each corpus's `census.json` carries `audit.rows` with
`quantity / expected / obtained / delta / match`, and **`expected` is the
pre-freeze value**. So a prose figure equal to a mismatched row's `expected` is
stale *by construction* — no threshold, no inference, a **certainty**, and
complete over every quantity the freeze audit compared. Over all six corpora,
16 mismatched quantities: **clean.** The three corrections account for all of
them.

**Screen 2 (second net) and why its window cannot be tuned.** The first version
used 1 %, fitted to the one case it caught — which excludes **two of the three**
figures actually corrected (1,432 → 1,381 is 3.69 %; 555 → 528 is 5.11 %; only
3,167 → 3,162 at 0.16 % is inside). Widened to 6 %, the largest recorded delta.
That is the honest window and it is noisy by construction, because the census
fields sit closer together than the reconciliation deltas: 18 candidates, of
which **zero** were stale.

Two defects in the instrument, found by clearing those candidates by hand:

* **the extractor split decimals** — `0.4157` yielded `4157` and `0.0386` yielded
  `386`, putting four numbers that *do not appear in the prose* on the list;
* **bare four-digit years** collided with `synthetic_rq1`'s `n_records = 2,000`.
  The prose comma-formats every data figure, so an uncommaed 1900–2100 is a date.

18 → 13 → **7** after both fixes, and the seven are real prose numbers colliding
with a nearby field (1,300 differentials against 1,381 members, and so on). They
are recorded in `KNOWN_BENIGN` **with their reasons**, so a later reader can
re-check the judgement rather than inherit a silent filter.

**Standing status: both screens clean, exit 0.** The residual limitation stays
stated — it matches digit strings and cannot see whether the noun beside a number
is the right noun, which is the predicate pass's job. Screen 1 proves a figure
stale; neither screen proves one correct.

**2026-09-11 — the screen widened to all 44 D_ART3 documents: nine stale values
in live documents.** `[IsalHG-Fable]`: `prose.md` is not the only document
carrying these figures, and `RESULTS_WALKTHROUGH.md` had already proved they
diverge. Correct.

Two defects in the screen surfaced first and are fixed:

* **screen 1 had no floor** — an expected value of `20` (`n_classes_run_ge5`)
  matched "20" in nineteen documents. `MIN_VALUE` now applies to both screens;
  four small quantities are skipped and named as skipped.
* **dated records were treated as live.** A handoff, audit, state note or probe
  *correctly* quotes the numbers current when it was written. Those are now
  reported separately — three pre-freeze values appear **only** in dated records
  and are right as history.

**The nine, all certainties from the freeze audit's own `expected` values:**

| corpus | quantity | pre-freeze → built | live documents |
|---|---|---|---|
| `ndc_classes` | `n_records` | 1,432 → 1,381 | START_HERE, CODE_PLAN, DESIGN |
| `ndc_classes` | `n_consecutive_pairs` | 555 → 528 | DESIGN |
| `ndc_classes` | `delta_1` | 120 → 117 | DESIGN, RESULTS_WALKTHROUGH, rq7_envelope_facts, idea3_median |
| `ndc_classes` | `delta_2` | 134 → 129 | DESIGN, literature_verified, proved_facts |
| `ndc_classes` | `n_pairs_constant_preserving` | 140 → 128 | START_HERE, ENCODINGS_WORKED_EXAMPLE, rq7_envelope_facts |
| `ndc_classes` | `n_pairs_constant_changing` | 415 → 400 | START_HERE |
| `ndc_substances` | `n_records` | **2,222 → 1,745** | DESIGN |
| `wd50k66` | `n_records` | 3,994 → 3,988 | DESIGN |
| `wd50k66` | `n_records_with_arity_ge3` | 3,167 → 3,162 | START_HERE |

**`ndc_substances` 2,222 → 1,745 is the largest and it is in `DESIGN.md`**, the
document every experiment is specified from.

**One caveat the screen cannot resolve, and it is the predicate pass again.** A
live document may quote a pre-freeze value **as** a pre-freeze value — this
task's own entries do, and `rq7_envelope_facts.md` appears above for exactly
that reason (it records 120 and 140 while explaining the reconciliation). The
screen matches digits, not nouns, so each of the nine is *located*, not
adjudicated. **Correcting them is fold work and belongs in the fold**, one
document at a time, with the noun checked.

**2026-09-11 — `DESIGN.md` adjudicated, and one figure was *used*, not quoted.**
`[IsalHG-Fable]`: the nine are not equivalent. Six sit in documents that
*describe*; three sit in `DESIGN.md`, which experiments are **specified from**, so
a stale figure there may have sized a cell or set a sampling frame. Checked, one
by one:

| `DESIGN.md` site | verdict |
|---|---|
| §corpora L136–137 — "1,381 members and 528 pairs (1,432 / 555 when singletons are counted)"; "control (1,745; 2,222 counting singletons)" | **correct as written.** The built values lead; the pre-freeze ones are labelled as the other counting convention. |
| L456 — "census: 42 classes with runs ≥ 3, 19 with ≥ 5" | **already built values** (not 45 / 20). The below-floor blind spot does not bite here. |
| L254 — M2's frame: *"(a) the **555** NDC natural consecutive pairs"* | **STALE AND USED.** This is the *sampling frame* of a measurement: the design specified 555 pairs where 528 exist. **Corrected to 528**, with the pre-freeze value noted. |

So Fable's distinction is the right one and it earned its keep on the first pass:
**a specification document is exposed differently from a descriptive one**, and
the one genuine error among the three was in the clause that sets what a
measurement runs over.

**The screen still flags that line, and it is right to.** The correction keeps
"(555 pre-freeze; the built corpus has 528)" so the reconciliation is legible —
and the screen cannot tell a labelled historical mention from a live use. That is
the predicate-pass limit, now demonstrated rather than asserted: **screen 1
locates every occurrence and adjudicates none.**

**Below the floor: named, not counted.** `MIN_VALUE` excludes exactly the
quantities that are small *because they are scarce*, and scarcity is what makes
them load-bearing — `n_classes_run_ge5` (20 → 19) is what helped decide Corpus B
could not carry RQ3 alone. The screen now **lists** them instead of reporting a
count, so "unscreenable" cannot read as "clean":

| corpus | quantity | pre-freeze → built |
|---|---|---|
| `ndc_classes` | `delta_0` | 85 → 77 |
| `ndc_classes` | `n_classes_run_ge3` | 45 → 42 |
| `ndc_classes` | `n_classes_run_ge5` | 20 → 19 |
| `ndc_substances` | `delta_1` | 35 → 31 |

Four, hand-checkable, and the first check (`DESIGN.md` L456) came back clean.

**2026-09-11 — the class closed behind L254, and the below-floor four cleared.**
Three items from `[IsalHG-Fable]`, all closed with evidence.

**1. Name the census field, not its value.** L254 went stale because it wrote a
*count* where it meant a *quantity*. The corpus has already moved once (singleton
products, arity cap, fact floor) and there is no reason to expect it never moves
again, so **every literal count in a specification is a future stale figure** and
the screen catches those only after the fact. The durable form names the field —
*"the NDC natural consecutive pairs (`census: n_consecutive_pairs`)"* — which
cannot go stale, tells a reader where to look, and makes the spec agree with the
corpus by construction rather than by audit.

Swept `DESIGN.md` for other populations written as literals. **One candidate,
and it is benign:** L395's *"1,146 of the 1,400 natural Corpus B member pairs"*
is a measurement **result** — what the pre-`reach′` reading returned — not a
population to be measured, so a literal is correct there. **L254 was the only
one**, and the class is closed rather than the instance.

**2. The below-floor four: all clear.** `delta_0` (85→77) was clean from
`DESIGN.md` L456. The remaining three are now checked by hand in the live
documents: **45** (`n_classes_run_ge3`) does not occur in any class/run context;
the **20**s are all `≥ 20 members` label thresholds, unrelated to
`n_classes_run_ge5`; **35** (`ndc_substances delta_1`) does not occur. Carried as
three outstanding rather than "hand-checked", per Fable, until each was actually
done.

**3. `KNOWN_BENIGN` split, because it held two things with different
re-validation rules:**

| list | meaning | re-validated |
|---|---|---|
| `COLLISIONS` (9) | a prose number landing near a census value by accident | **whenever a corpus is rebuilt** — the collision depends on the current value |
| `LABELLED_HISTORY` (1) | a pre-freeze value deliberately kept *and labelled as such* | **never** — it does not depend on the census at all |

Screen 1 now honours `LABELLED_HISTORY` too, so `DESIGN.md` L254's
"(555 pre-freeze…)" is reported as deliberate rather than as stale: **9 → 8**.
Without the split, a maintainer re-checks the permanent entries forever and stops
re-checking the conditional ones.

**Standing: 8 stale values in live documents**, located and awaiting the fold's
predicate pass.

**2026-09-11 — RESOLVED: RQ1 *is* ready; the alarm below was raised by a check
that could not have found the deliverable.** Kept in full because the sequence of
errors is the point.

`[IsalHG-Fable]` named the path from the handoff and it is exactly there:
`results/IEEETKDE/RQ1_isal/merged/` — 483 files, `465` row files plus the
deliverable set (`merge_manifest.json`, `manifest.json`, `config.json`,
`published_tables.md`, `m1_instructions_by_kind.md`, …). I had searched
`results/frozen/` — **tonight's convention, which postdates RQ1 by three days** —
and globbed `*.csv`, so a `merged/` subdirectory could not have appeared. **The
absence I found was evidence about the convention's coverage, not about RQ1.**

**And the lineage was already recorded, in the artefact built for it.**
`merge_manifest.json` answers both checks Fable named:

| | |
|---|---|
| `source_tags_used.addressing` | **`["47c8a42c"]`** — the Isal campaign tag alone |
| tags *available* under `addressing` | `47c8a42c` **and** `c3fb21de`, 155 files each — **both campaigns present, one selected** |
| `duplicate_audit` | **0 duplicate rows** in all five tables (m0items 88,428 · m1 1,673,904 · m2 66,336 · m3 88,428 · m4 36,000), each with its key named and `rows == unique_observations` |
| per-arm provenance | Isal arms from `addressing_cpp` (`ebda0b71`); `wstar_rank` from `addressing_rank` (`28536068`); the rest from `addressing` (`47c8a42c`); `fact_rank_roles` dropped |

So the 904,442-row double-count is **provably absent here** — the merge saw both
campaigns and took one, which is what `--only-tags` and the duplicate audit were
built for at T-KBe. RQ1's fact base is a **walk of `published_tables.md` against
the 19 prose mentions**, not an investigation.

*(One imprecision, recorded rather than propagated: the handoff says "17 files";
the deliverable set is 18 non-row files beside 465 row files. Immaterial to the
lineage, but it is the kind of count that becomes a citation.)*

---

**The superseded alarm, kept because the error chain is the lesson.** The sequencing table was written from `[IsalHG-Fable]`'s summary, which
gave RQ1 as *"final (frozen deliverable, D-ART5 recorded)"*. I copied that into a
planning table without opening the results tree — the session's own recurring
defect, committed one exchange after both parties called the thread closed, in
the artefact that schedules the work.

**What the filesystem says.** There is **no RQ1 deliverable under
`results/frozen/`** (which holds only tonight's two freezes). Instead there are
**five** candidate directories across four roots, all last written 2026-09-08:

| directory | csv files |
|---|---|
| `IEEETKDE/RQ1_addressing` | 661 |
| `IEEETKDE/RQ1_isal` | 466 |
| `IEEETKDE_isal/RQ1_addressing` | 630 |
| `IEEETKDE_isal_preview/RQ1_addressing` | 464 |
| `IEEETKDE_isal_merged/RQ1_addressing` | 466 |

**This is the worst possible shape for the most-cited RQ.** `RQ1_addressing` is
*the* directory that held two campaigns under different launch tags and
double-counted **904,442 of 2,506,837** rows when concatenated (T-KBe, T-KBh,
T-KBn); the counts above differ by up to 197 files; and the campaign has a live
precedent for reading the wrong root, which cost a whole set of RQ4 progress
figures earlier in this session.

**So RQ1's fact base cannot start with the numbers — it starts with the
lineage**, exactly like T-KBx:

0. establish **which root and which launch tags** are the record, from the wave
   notes and `DECISIONS.md`, before a single figure is read;
1. confirm the `--only-tags` selection and the duplicate audit (`314b4a3`) apply,
   since a bare concatenation is known to double-count;
2. only then walk the 19 prose mentions.

**RQ2 is unaffected and remains "build now"** — it closed tonight against rows
whose root and job are named in this session's own record.

**And the lesson is the one already at the top of L26, arriving again:** a
summary from a careful peer is not a check, and a planning table is exactly where
an unverified premise does the most damage, because everything scheduled after it
inherits the error silently.

**2026-09-11 — the predicate pass run on the located values: four live errors,
three correct, and the screen was under-reporting.**

The screen located 8 stale values but **adjudicates none** — a document may quote
a pre-freeze value *as* a pre-freeze value. Read in context, the noun decides,
and it split them cleanly:

| site | text | verdict |
|---|---|---|
| `CODE_PLAN.md` L150 | "reproducing S2: **1,432 encodable class-quarters**" | **correct** — names `n_encodable_counting_singleton_products`, which *is still 1,432* |
| `DESIGN.md` L133/136/137 | "3,988 (3,994 without the `m ≥ 3` floor)"; "(1,432 / 555 when singletons are counted)"; "control (1,745; 2,222 counting singletons)" | **correct** — built value leads, pre-freeze labelled |
| `START_HERE.md` L282 | "NDC-classes (**1,432 members**, 21.6 % …)" | **ERROR** → 1,381 / 22.2 % |
| `DESIGN.md` L230 | "`ndc_classes` (1,432), `wd50k66` (3,994) — **all members**" | **ERROR ×2** → 1,381 / 3,988 |
| `DESIGN.md` L514 | "`ndc_classes`, **all 1,432 members**" | **ERROR** → 1,381 |
| `DESIGN.md` L708 | N-scaling grid `N ∈ {…, 3,994}` | **ERROR** → 3,988, **verified against the frozen RQ7 rows** (`[250, 500, 1000, 2000, 3988]`) |

**Three of the four errors are in `DESIGN.md` and three of those are
specifications** — a corpora list, a corpus for an experiment, and an `N` grid.
That is the describe-versus-specify distinction holding for a second time, and
the fourth instance of a *population written as a literal*: with L254's sampling
frame, `DESIGN.md` has now had four.

**And the screen was under-reporting, which is why L708 was nearly missed.** It
reported *documents*, not *occurrences*: "1,432 in `DESIGN.md`" was **one line
covering three sites with three different verdicts**, so a document could read as
adjudicated after one of them was checked. It now counts occurrences
(`DESIGN.md x2`), and that change surfaced L708 **within a minute of being
made** — a second `3,994` that the document-level report had hidden behind the
first.

**A screen that collapses occurrences under-reports the work by exactly the
number it hides**, and the hidden ones are the ones nobody looks for, because the
report says the document has been seen.

**2026-09-11 — the predicate pass is COMPLETE over the located values: screen 1
is clean, and seven live errors were fixed.** Every occurrence read in context;
the noun decided each one.

| document | text | verdict |
|---|---|---|
| `START_HERE.md` L280 | "WD50K(66) (**3,167** n-ary members" | **ERROR** → 3,162 |
| `START_HERE.md` L282 | "NDC-classes (**1,432 members**, 21.6 %" | **ERROR** → 1,381 / 22.2 % |
| `START_HERE.md` L376–7 | "(**140** constant-preserving pairs, **415** changing)" | **ERROR ×2** → 128 / 400 |
| `DESIGN.md` L230 | "`ndc_classes` (1,432), `wd50k66` (3,994) — **all members**" | **ERROR ×2** → 1,381 / 3,988 |
| `DESIGN.md` L514 | "`ndc_classes`, **all 1,432 members**" | **ERROR** → 1,381 |
| `DESIGN.md` L708 | N-grid `{…, 3,994}` | **ERROR** → 3,988, checked against the frozen rows |
| `CODE_PLAN.md` L150 | "1,432 **encodable class-quarters**" | correct — names a field still equal to 1,432 |
| `DESIGN.md` L133/136/137 | labelled alternatives | correct |
| `DESIGN.md` L695 · `RESULTS_WALKTHROUGH` L326 | the sweep grid's `m = 120`; "from m = 120" | **collision** with `delta_1` |
| `DESIGN.md` L749 · `literature_verified` L77 | "`n + m ≤ 134`"; *Pattern Recognition Letters* **volume 134** | **collision** with `delta_2` |
| `ENCODINGS_WORKED_EXAMPLE` L94 | a 140-token certificate row | **collision** with `n_pairs_constant_preserving` |

**Screen 1 now reports clean and the script exits 0.** All adjudications are in
`LABELLED_HISTORY` **with their reasons**, so the judgement is re-checkable.

**A journal volume number colliding with `delta_2` is the clearest case for the
predicate pass there will be**: `134` is a correct, sourced, meaningful number in
a bibliography, and *no* string method distinguishes it from a stale pair count.

**And screen 2 has been demoted from gate to opt-in (`--near-miss`).** Over
`prose.md` alone its 6 % window gave 18 candidates; over 46 documents it gives
**655, none of them stale**. Its window is wider than the gaps between census
fields, so at this scale it cannot discriminate — a net whose mesh is larger than
the fish. **Screen 1 scales because it is exact; screen 2 does not because it is
approximate**, and a 655-item candidate list is indistinguishable from no check at
all, since nobody will clear it.

**2026-09-11 — screen 2's problem is coverage, not window, and the fix is already
scheduled.** `[IsalHG-Fable]`: tuning the near-miss window cannot save it, because
the window is wider than the gaps between census fields — any value near one field
is near several. But the gap it was built for is narrow: **stale values of
quantities the freeze audit never compared.** That is a *coverage* problem with a
bounded fix.

> Extend the freeze audit's compared set to the quantities the prose actually
> cites, and **screen 1 — exact, no window, no false positives — becomes complete
> over them, and screen 2 retires.**

**And the list of cited quantities is a by-product of work already scheduled.**
Building the remaining fact bases enumerates exactly which census quantities the
prose uses, so the sequence closes on itself:

> fact bases → the list of cited quantities → extend `EXPECTED` in
> `freeze_corpora.py` → the exact screen is complete → the approximate one is
> unnecessary.

Recorded here rather than acted on now, because the list does not exist until
RQ3/4/5's fact bases do. Screen 2 stays opt-in meanwhile.

**2026-09-11 — the locality fold is now a DEPENDENCY of a headline table, and
its input is already on disk.** `[IsalHG-Fable]`, verified here.

`prose.md` §6's capability matrix was rewritten to carry **two locality columns —
pendant and interior — for every row**, because no row of §2.3's locality table is
uniform (the ordered walk owns pendant, the fact list owns interior, and the
certificate's only non-zero cells are interior widening). That is the right table.
**But its numbers currently come from the 60-member preview**, and the exposure is
different in kind: §2.3's table is read as provisional because it says so three
times around it, whereas **a capability matrix is what a reviewer scans first and
takes as the paper's summary of itself**. A preview marking there reads as a
caveat about precision, not about which arm wins a column.

**The campaign's figures are already frozen — this is transcription, not a run.**
`IEEETKDE/RQ1_isal/merged/` (read-only, provenance in §"RQ1"):

| | |
|---|---|
| `m1_instructions_by_kind.md` | columns `collection, edit_kind, regime, arm, n, n_base, median_d_instr, iqr, **within_2**` |
| collections | `ndc_classes`, `wd50k66`, `synthetic_rq1` **and** `(pooled)` — per corpus, not only pooled |
| arms | **12**, including both Isal walks, both certificate tokenisations, the pointer alphabet and the retired fact-rank record |
| `rq1_statistics{,_ndc_classes,_synthetic_rq1,_wd50k66}.md` | **`regime` IS the pendant/interior axis** — `regime 0 (pendant)` over 3 edit kinds, `regime 1 (interior)` over 4: **seven regime × kind cells** |

So the pendant/interior classification the new matrix needs is **not** something to
derive: it is the `regime` column, already computed, already per corpus, at 27
seeds, in a frozen deliverable.

**Priority, stated as a dependency rather than a preference.** RQ3/4/5's fact
bases wait on experiments. **This one waits only on transcription, and it now has
a headline table downstream of it** — so it is the one remaining fold item that
can be done now and the one whose absence is most visible. *A table that
summarises the paper cannot be the last thing to inherit the campaign.*

**The precondition runs in BOTH directions.** As written above it audits every
number the prose carries against a `foundation/` entry. That is silent on the
inverse, which has already occurred: the word "novel" appeared nowhere in
`prose.md`, so an RQ6 result and its caveat existed only in the fact base and
would have been folded by nobody. So the checklist also walks each
`foundation/` entry and asks which of its results the prose states — and, for
any it does not, whether that is a deliberate cut or an omission. A result
present in the fact base and absent from the prose is as much a defect as a
number in the prose absent from the fact base.

**A predicate pass, because provenance cannot check the noun.** A `foundation/`
entry records a number, a run and a table. It cannot record whether the **noun**
attached to the number is the right noun, and neither direction of the
bidirectional audit above would catch it: a sentence claiming every novel sample
of ours is a *hypergraph*, or a *canonical form*, or a *knowledge base*, sources
identically to the true one. `rowsio` cannot see it either — nothing about it is
a row.

This already fired once: "of the fact list's genuinely new samples, 7.3 % are
**knowledge bases at all**" was wrong, because §2.1 defines a knowledge base as a
finite set of facts and a disconnected fact set is one. The correct noun is
**connected** (R3). The quantity had been verified from two independent
directions; the predicate had never been checked.

So the fold runs one pass over the folded prose checking, for each quoted number,
the **noun and the qualifier** against the document that defines them — cheap,
because they are all written down:

| term | defining source |
|---|---|
| knowledge base | `prose.md` §2.1 ("a finite set of facts") |
| connected / domain | R3 (`DECISIONS.md`), Prop. C.4 |
| reach, coverage | design §4 |
| `w*_c` | D-TA2 |

Like the "reproduce a campaign quantity alongside the new one" rule, this is a
**second opinion** rather than a second check, and it catches what looking harder
at what is there cannot.

**Obligation: a transformed form goes into the entry as it is written.** The
fold's job is to turn stored figures into prose, and prose does not use stored
forms. Today's prose already prints "one in 578", "one in 11,739", "58 %",
"87 %", "7.3 %" and "270,000/270,000" — reciprocals, complements, percentages
and ratios of values the fact base stores as 0.001730, 0.000085, 0.4157, 0.1260,
0.0726 and 1.0000. **A grep for the stored value finds none of them**, and a
reader checking the paper greps for what the paper prints.

So this is a fold obligation, not a sweep afterwards: **when the fold writes a
number in a transformed form, that form goes into its `foundation/` entry beside
the stored one, in the same edit.** One line per number, no judgement required.
Stated before the fold begins because the fold produces one such gap per
sentence, and repairing a batch afterwards is what the precondition exists to
avoid.

The first table is `foundation/rq6_generation_facts.md` §"Quoted forms", which
back-fills the twelve forms the prose already carries.


**A cross-document consistency pass, over the claims corrected today.** Every
other check here is **per-number or per-sentence**: the bidirectional audit
compares prose against entries, the predicate pass checks nouns against
definitions, the quoted-forms rule matches transformations. **None reads two
corrected sentences against each other**, and inheritance across documents is
where drift lives. A paper saying the residual tail is displacement in one
section and the search in another is worse than one that says either
consistently — and a reviewer finds it in ten minutes, because contradictions are
easier to spot than errors.

So the fold runs one pass reading the corrected claims **together**, scoped to
the list below. Homes verified by grep, not from memory:

| claim | where it lives |
|---|---|
| **residual-tail explanation** (displacement vs the search) | `prose.md` §"symmetric-input cost" (**marked QUALIFIED**), `T-KBe`, `T-KBp`, `T-KBf`, `STATE` §10–11. `DECISIONS.md` R2 states only *counts* and is unaffected. |
| **joint rate / conditional denominators** | `foundation/rq6_generation_facts.md`, `prose.md` (generation ¶), `STATE`, `T-KBo`, `lessons.md` |
| **per-corpus rule** ("no single ratio describes both") | `prose.md`, `foundation/rq6_generation_facts.md`, this file |
| **Corpus A's structural floor** (eleven arms = one row) | `T-KBf`, `STATE` §10 |
| **`reach1` is characterisation, scores nobody** | `foundation/rq6_generation_facts.md`, `RESULTS_WALKTHROUGH.md`, this file |
| **struck `256/1,000` and "three times in four"** | `prose.md` (replaced), `RESULTS_WALKTHROUGH.md`, `foundation/`, this file |
| **the Corpus B "collapse" retraction** | `T-KBf`, `STATE` §10 |

Cheap, once, and **at** the fold rather than after it.

### The replacement sentence for the residual-tail paragraph

The QUALIFIED marker in `prose.md` says what fails; the fold needs what to write
instead, and it is a **mechanism** rather than a negation (`[IsalHG-Fable]`).

**Both engines run the displacement search.** The rank arm is the family's greedy
walk with displacement enumeration and the seven-rung cascade; the orbit arm adds
**tie-complete branching over that same enumeration**. So the cost on this tail is
neither the displacement search *instead of* the branching nor the branching
alone — it is the **displacement enumeration multiplied by the branch factor**,
and only the multiplier is specific to the search-based program.

**Measured decomposition** (M3 census, `IEEETKDE_isal_merged`), which is stronger
than the argument alone:

| arm | censored | arity |
|---|---|---|
| `wstar_rank` | 53 | **all 53 at k = 10** — not one below |
| `wstar_orbit` | 77 | 69 at k = 10, **plus 6 at k=7, 1 at k=8, 1 at k=9** |

`rank ⊆ orbit` (zero rank-only censorings, T-KBe), so the **24 orbit-only**
censorings split cleanly:

- **16 extra at k = 10** — branching *amplifying* a displacement cost that is
  already high;
- **8 below k = 10** — members displacement alone handles and branching does not.

**CORRECTED: those 8 are not all branching-only.** `[IsalHG-Fable]` noticed that
the census reports **8** at `|Aut|` 10³–10⁶ and **8** below k = 10, and **69**
below 10³ and **69** at k = 10 — two matched pairs — and asked whether they are
the same members. Cross-tabbed:

| k | `\|Aut\|` 10³–10⁶ | `\|Aut\|` < 10³ | total |
|---|---|---|---|
| 7 | 5 | 1 | 6 |
| 8 | 1 | 0 | 1 |
| 9 | 0 | 1 | 1 |
| **10** | 2 | **67** | **69** |

**The two eights overlap in six.** Six of the eight sub-arity-10 members sit at
`|Aut|` 10³–10⁶, so **residual symmetry after pruning is a live alternative
explanation for them** — a member with `|Aut|` in the millions can retain enough
branches after orbit pruning to exhaust the budget at modest arity.

**Only 2 of 77 are low arity *and* low symmetry** (k = 7 and k = 9, both at
`|Aut|` < 10³). Those two are the genuinely branching-only casualties: neither
displacement (k < 10) nor residual symmetry (`|Aut|` < 10³) explains them.

**So the paragraph may not lean on "eight".** At n = 2 the branching-only set
establishes *existence* and nothing more — the same discipline as the three
transfer-and-recovered runs on Corpus B. The multiplication reading keeps its
strong evidence, which was never the eight: the **16 extra at k = 10**, and the
**24.7 % vs 50.9 %** recovery differential with its two tests. And one clause of
the surviving half needs care: *"pruning cannot touch it, the members are
asymmetric"* is true of the 67 at k = 10 and **false of six of the eight**, which
are precisely the members the earlier draft leaned on.

**Every number fits**: displacement is why both arms censor at arity 10 and
essentially nowhere else; branching is why one recovers a quarter of its tail at
a tenfold budget and the other half; and it is the same complexity split, because
multiplying a polynomial enumeration by an exponential branch factor is exactly
what makes ten times the time buy almost nothing.

**Both surviving halves keep their evidence.** *Pruning cannot touch it* —
the members are asymmetric, so there is no orbit to prune. *The residual cost is
the branching* — the same enumeration without it clears half the tail.

### The illustration the paragraph should use: 15 matched members

Proposed by `[IsalHG-Fable]` from marginals, **with the explicit instruction not
to use it until joined** — the operation that had just cost the "eight". Joined
member-by-member on `(collection, member_id)`, orbit's censored set against
rank's:

| | |
|---|---|
| `rank ⊆ orbit` | **confirmed** — 0 rank-only censorings |
| orbit-only | **24** |

| k | `\|Aut\|` | orbit-only |
|---|---|---|
| 7 | 10³–10⁶ | 5 |
| 7 | < 10³ | 1 |
| 8 | 10³–10⁶ | 1 |
| 9 | < 10³ | 1 |
| 10 | 10³–10⁶ | 1 |
| **10** | **< 10³** | **15** |

> **15 members sit at maximum arity and negligible symmetry, where the
> deterministic walk completes and the branching search does not.**

**The fifteen has a denominator, and the rate is the better sentence.** Within
that matched stratum (`k = 10`, `|Aut| < 10³`), taken from the join and not by
subtraction:

| | |
|---|---|
| orbit fails | **67** |
| rank fails (⊆ orbit) | **52** |
| **orbit-only** | **15 = 22.4 %** |
| **defeat both engines** | **52 = 77.6 %** |

> **Displacement alone accounts for 52 of the 67 hardest members; branching
> converts a further 15 — about a fifth — from survivable into failures.**

A bare count says branching *can* cause failure; the rate says **how much of the
hardest stratum it accounts for**, with arity and symmetry held fixed by
construction rather than by argument. It is also the more credible sentence
because it **concedes the larger share to displacement in the same breath**.

Two independent magnitudes for one mechanism, on different axes: **22.4 % of the
hardest stratum at the published budget**, and **24.7 % against 50.9 % recovery
at a tenfold budget**.

**This controls for both alternatives by matching rather than by argument:**
identical arity (k = 10), so the displacement cost is the same; `|Aut| < 10³`, so
there is no orbit structure to explain the difference; and the strict-subset
result makes them genuinely orbit-only. **The only remaining difference is
tie-complete branching against deterministic tie resolution** — which is exactly
the mechanism the paragraph claims, evidenced at **15** rather than at 2.

The marginal estimate happened to be right this time. It was still worth joining:
the same subtraction across two marginals is what produced the "eight", and both
marginals reproduced exactly there too.

### The surviving clause, in its accurate form

Not *"the members are asymmetric"* — true of 69 and false of 8. Write the
proportion and name the exception:

> **69 of the 77 sit below `|Aut|` 10³, where there is no symmetry to prune; the
> remaining 8 carry moderate symmetry that pruning reduced without eliminating.**

Nine in ten, stated as a count, with the exception named rather than
contradicted by the paragraph's own load-bearing evidence.

