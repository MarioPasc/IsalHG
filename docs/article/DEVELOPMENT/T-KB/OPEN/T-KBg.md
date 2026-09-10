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
