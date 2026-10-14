# D-ART5 — the three decisions, and what the measurements say

*Written 2026-09-08 by the `[IsalHG-Refinement-Opusxhigh]` session for the
author, to be read cold. Every number is from the final merged tree
(`results/IEEETKDE/RQ1_isal/merged/`), on the intersection of units all
published arms completed at the 60 s budget, with cluster-bootstrap intervals
and Holm-corrected paired tests. Nothing here is pending or provisional.*

**Nothing has been submitted and no document asserts a decision.** When you
rule, D-ART5 goes into `DECISIONS.md` with your word, T-KBe closes, and
RQ2–RQ7 can be launched.

---

## 0. The three decisions in one page

| # | Decision | Recommendation | Why it is yours |
|---|---|---|---|
| 1 | Which canonical program carries the paper's tables | **A′ — the frozen `w*_c` computed by the orbit-pruned C++ engine** | It is the paper's representation; design §8(1) reserves it for you |
| 2 | The published budget | **60 s is the row; 600 s is tail characterisation, never merged** | It decides which numbers are printable |
| 3 | Where the retired fact-list arms' wins are reported | **One honest sentence in the main text, tables in the supplement** | It trades a reviewer risk against D-ART4 (1) |

If you agree with all three, reply with that and the campaign proceeds. If you
disagree with any, §6 says what changes.

---

## 1. What was measured

Three corpora, 7,369 knowledge bases, **139,492 seeded single edits**, five edit
kinds, on the C++ engine throughout (your 2026-09-07 rule).

| corpus | members | independent clusters | what it is |
|---|---|---|---|
| wd50k66 | 3,988 | 3,988 | Wikidata entity descriptions |
| ndc_classes | 1,381 | **171 drug classes** | quarterly co-formulation records |
| synthetic_rq1 | 2,000 | 2,000 | the envelope sweep |

The seven arms are the four cells of your nauty ablation plus the two
certificate tokenisations:

| cell | arm | what nauty does |
|---|---|---|
| no nauty | `isalhg_levenshtein` = `w*_c` | nothing |
| **oracle only** | **`wstar_orbit`** | supplies the automorphism group at ties |
| both | `wstar_rank` | supplies the tie key |
| order only | `isal_ow_struct/rank/rank0` | supplies the order |
| — | `nauty_cert`, `nauty_cert_rows` | the certificate, as bytes and as rows |

**Acceptance gate (H-M0): every Isal arm passes 0 false merges / 0 false splits
/ 0 invariance violations on all three corpora.** `fact_rank_roles` failed (247
false splits, 2,104 violations) and is out of every table.

---

## 2. Decision 1 — the representation

### What the pre-registered rule decided, and what it did not

The rule in `ISAL_VARIANT_DESIGN.md` §3 ranges **only over the ordered-walk
policies**. Applied to the final data, it selects **`isal_ow_struct`**
(0.0703 [0.0686, 0.0720], median 8) over `isal_ow_rank` (0.0700, median 9) and
`isal_ow_rank0` (0.0694, median 9) — first on the primary criterion, then on
the tie-break. *The three are not distinguishable at Holm-corrected 0.05; the
median breaks the tie.*

**Its escape clause fired.** No `ow_*` arm beats `nauty_cert_rows` (0.1787), so
the pre-registration itself says the paper argues from the language rather than
from a locality win by the ordered walk. **The rule therefore does not choose
the paper's representation — you do.**

### The four cells, measured

| | `w*_c` (unpruned) | **`wstar_orbit`** | `wstar_rank` | `isal_ow_struct` |
|---|---|---|---|---|
| is it the frozen `w*_c`? | yes | **yes — bit-identical** | no (65 % agree) | no (0 % agree) |
| censored of 7,369 | 356 | **77** | 53 | **0** |
| ndc cost, median → p90 | 5.5 ms → 2.21 s, p90 41 s | 5.5 ms → 284 ms, p90 33 s | 5.2 → 34 ms, p90 1.05 s | **0.5 → 0.9 ms, p90 2.4 ms** |
| needs a new theorem? | no | no | **yes** | no (Theorem C) |
| supersedes D-TA2? | no | **no** | **yes** | it would |

### The decisive fact for A′

`wstar_orbit` **is** `w*_c`. Verified at campaign scale, not asserted:

- identical words on **7,013 / 7,013** members where both completed;
- identical single-edit distances on **130,788 / 130,788** M1 units;
- identical M2 distances on **5,174 / 5,174** pairs, with ρ equal to four decimals.

So adopting it changes *nothing* about the paper's canonical string. **D-TA2 is
untouched, no new canonical form needs ratifying, and Theorem A carries over
unchanged.** Design §8(1)'s condition dissolves.

### What orbit pruning buys — the R2 result

| |Aut| bucket | unpruned | orbit-pruned |
|---|---|---|---|
| ≥ 10⁷ | 36 | **0** |
| 10³–10⁶ | 170 | **8** |
| < 10³ | 151 | 69 |
| wd50k66 total | 237 | **7** |

**R2 is lifted for symmetry.** What remains is a different mechanism: 69 of the
77 residual censorings are arity-10, all are arity ≥ 7, and 69 sit at
|Aut| < 10³ — displacement enumeration, which no stabiliser orbit can prune.
`wstar_rank` does not remove it either (all 53 of its censorings are arity 10).

### Locality — the argument for the search, per corpus

Fraction of edits landing **within two instructions** (higher is better):

| edit kind | corpus | **`wstar_orbit`** | `isal_ow_struct` | `nauty_cert_rows` |
|---|---|---|---|---|
| constant-bringing insertion | wd50k | **33.4 %** | 15.2 % | **0.0 %** |
| | ndc | **11.7 %** | 4.2 % | **0.0 %** |
| interior insertion | wd50k / ndc | **7.4 / 3.2 %** | 3.0 / 0.5 % | 0.0 % |
| interior widening | wd50k / ndc | 19.0 / 13.3 % | 10.9 / 2.0 % | **25.2 / 39.9 %** |
| interior narrowing | wd50k / ndc | **32.3** / 28.0 % | 4.4 / 22.2 % | 18.0 / **45.1 %** |
| pendant deletion | wd50k | **84.5 %** | 79.4 % | **0.0 %** |
| | ndc | 57.6 % | 59.4 % | **0.0 %** |
| pendant narrowing | wd50k / ndc | 81.4 / 85.9 % | 83.1 / 87.7 % | **0.0 %** |

**Read this way:** the search leads the order-only program on **every insertion
kind and every interior edit, on every corpus**. On pendant removals the two are
**statistically indistinguishable** (they give literally the same answer on 78 %
of entities), except WD50K deletion where the search leads (+0.047 [0.037,
0.058], p_Holm 1.7 × 10⁻¹⁸).

**The certificate never lands within two rows** on the five fact insertion and
deletion kinds, on any corpus. It *is* more local than us on interior widening
(both corpora) and interior narrowing (ndc).

### The case against A′, stated fairly

- **`isal_ow_struct` is 300× cheaper and censors nothing.** It is complete
  (Theorem C), its intermediate strings decode to connected knowledge bases
  (Prop. C.4), and it makes RQ4/RQ5's N×N matrices trivial. A reviewer will ask
  why the faster, uncensored arm is not the representation.
- **It is also more monotone than the search on the natural NDC series**
  (ρ = 0.556 vs 0.432 on pendant pairs, Δρ = −0.124 [−0.228, −0.037],
  p_Holm 0.025).
- **`wstar_rank` is 30× cheaper than orbit at the hard end** and censors less
  (53 vs 77), for a locality cost of about 2 points.

The answer to the reviewer is the honest trade-off sentence: *order alone gives
cost and monotonicity; the search adds locality on every insertion kind and
every interior edit; the oracle adds nothing but time.* That sentence is only
available if the ordered walk stays in the paper as the order-only cell of RQ1
and the cost floor of RQ7 — which is what A′ prescribes.

**Recommendation: ratify A′.** It keeps the frozen `w*_c`, requires no new
theorem, wins the axis the pre-registration named primary, and the four-cell
table becomes a measured cost/locality frontier rather than a defeat.

---

## 3. Decision 2 — the budget

Censoring is decided by a **wall-clock** budget, so it is not exactly
reproducible. Reading the same members, same code, same budget, at three times:
the unpruned engine gave **357, then 354, then 356** of 7,369.

The drift is predictable from how many members sit near the boundary:

| arm | completed | within 30 s of the budget | censored | drifted? |
|---|---|---|---|---|
| `w*_c` unpruned | 7,015 | 67 | 356 | **yes** |
| `wstar_orbit` | 7,292 | 32 | 77 | no |
| `wstar_rank` | 7,316 | **0** | 53 | no |
| `isal_ow_struct` | 7,369 | 0 | 0 | no |

**Recommendation: 60 s is the published row; the 600 s re-run of the 77
censored members is reported as tail characterisation and never merged into a
row.** Three reasons: 60 s is the pre-registered value, so keeping it is the
pre-registration honoured rather than a choice made after seeing numbers; a row
whose value depends on which budget you picked is not a property of the
representation; and it retires the `wstar_600` gap (design §3 names that arm but
the config never had it — under this rule its absence is correct, not an
omission).

A prediction is on record *before* the 600 s run, so it can refute us: the orbit
engine (32 completions just below the budget) should recover a material fraction
of its 77; `wstar_rank` (none) should not. If most of its 53 complete instead,
the "displacement, not symmetry" claim needs rewriting.

---

## 4. Decision 3 — the retired fact-list arms

D-ART4 (1) removed the fact-rank word from the paper: it has no machine. But it
is measurably **better than us on two axes**:

| | `fact_rank` / `fact_local_key` | `wstar_orbit` |
|---|---|---|
| interior insertion, within 2 | **56.7 %** | 8.2 % |
| interior deletion, within 2 | **57.8 %** | 13.9 % |
| monotonicity, NDC pendant | 0.292 / **0.632** | 0.432 |
| monotonicity, NDC interior | **0.979** / 0.968 | 0.949 |
| monotonicity, WD50K ladder | **0.589** / 0.587 | 0.537 |

**The options.**

- **(a) Supplement only**, per a strict reading of D-ART4 (1). Risk: a reviewer
  who reruns the retired arms finds they beat us on two axes and we did not say
  so. That is the kind of omission that costs a paper its credibility rather
  than a revision.
- **(b) One main-text sentence** naming the fact list's wins and why it is still
  not the representation — *it has no machine; its generated interiors are
  connected only 68.6 % of the time; it has no pendant locality; its role-carrying variant
  failed invariance* — with the tables in the supplement.

**Recommendation: (b).** It costs one sentence, it does not reopen D-ART4, and
it converts a discoverable weakness into evidence of care.

---

## 5. What you should be sceptical about

Read this section before ratifying. These are the soft spots.

1. **Three directional claims were asserted from point estimates during this
   session and all three dissolved under the paired test** — H-M2 "falsified for
   the ordered walk" (an artefact of scoring arms on different pair sets), the
   NDC pendant-deletion "reversal" (a tie, p_Holm 1), and the pendant-narrowing
   "win" (a tie on both corpora). Two were mine. The rule now in design §9: on
   these corpora **no direction is asserted from point estimates**. If a number
   in a draft has no interval, distrust it.
2. **The monotonicity claim is thinner than it looks.** The Isal word leads the
   row certificate in point estimate on all three series but the difference is
   established on **one** (WD50K ladder, +0.044 [0.025, 0.063], p_Holm 0.006).
   On the two NDC series — 50 and 34 drug classes — it is within noise. And the
   **byte** certificate beats us on the ladder (−0.140, p_Holm 0.006) by
   responding about five times larger per edit.
3. **Pooled numbers are mixtures.** WD50K supplies 3,946 of the 4,535
   pendant-deletion clusters, so a pooled "77 % within two" is really its 84 %;
   NDC gives 58 % and synthetic 9 %. The main-text tables should print the two
   real corpora side by side and never a pooled column.
4. **The corpus is smaller than the supplement says, and one exclusion is
   unreported.** NDC drops **519 members** for containing a fact of arity above
   the alphabet cap `k_max = 10` — an order of magnitude more than the 51 the
   supplement's count differs by, and the supplement never mentions it. A scope
   sentence that omits it overstates what the representation covers.
   (Filed as T-KBk.)
5. **The synthetic corpus behaves very differently** from both real ones —
   pendant deletion locality 9 % against 58 % and 84 %. It is the envelope
   sweep, not a knowledge base; keep it out of headline numbers.
6. **`w*_c` cannot navigate its own space cheaply.** p90 of 33 s on the NDC
   arity-10 tail, and every N×N matrix must fork under a budget because the C++
   canonicaliser poisons `fork` (measured; the ordered walk does not). RQ4/RQ5
   will carry a censored subset that must be reported.

---

## 6. What changes if you rule differently

| your ruling | consequence |
|---|---|
| **`wstar_rank` instead of A′** | You ratify a *second* canonical value beside `w*_c` (65 % agreement). Needs a theorem it does not yet have — Theorem C covers the ordered walk, not the rank-keyed walk. Buys 30× speed and 24 fewer censored members; costs ~2 points of locality. |
| **`isal_ow_struct` instead of A′** | Fastest, zero censoring, best monotonicity on NDC. But it loses the pre-registered locality criterion to the certificate, and the paper's representation would no longer be the family's own canonical string. |
| **Both A′ and the ordered walk as co-headline** | Two "ours" rows in every table; invites "which one is your representation?". |
| **600 s merged into the row** | Every M1–M4 number must be recomputed at that budget, and the published numbers then depend on a budget chosen after seeing the data. |
| **Fact arms supplement-only** | Saves a sentence; accepts the reviewer risk in §4(a). |

---

## 7. Where everything is

| what | where |
|---|---|
| The RQ1 deliverable (17 files) | `results/IEEETKDE/RQ1_isal/merged/` |
| Analyzer tables, all gates passed | `tables.md` |
| Intervals + Holm tests, pooled | `rq1_statistics.md` |
| The same, per corpus | `rq1_statistics_{wd50k66,ndc_classes,synthetic_rq1}.md` |
| Verification checks (agreement, common-set, censoring, M4) | `verification_checks.md` |
| Per-kind instruction breakdown | `m1_instructions_by_kind.md` |
| Provenance: which arm came from which run | `merge_manifest.json` |
| The full record of this session's findings | `docs/article/DEVELOPMENT/T-KB/IN-PROGRESS/T-KBe.md` |
| Deviations from the pre-registration | `ISAL_VARIANT_DESIGN.md` §9 |
| Fable's drafted D-ART5 text and paper sentences | its scratchpad file, header-stamped *not the decision record* |

Open follow-ups filed rather than solved inline: **T-KBh** (analyzers pool
launch tags), **T-KBi** (a private cross-module import behind the walk's
rendering), **T-KBj** (the fork poison and its `spawn` fix — must not land
between RQ1 and RQ2), **T-KBk** (the data section's corpus numbers).

## 8. After you rule

1. D-ART5 into `DECISIONS.md` with your word; T-KBe → CLOSED.
2. T-KBf submissions, in order: matrices → RQ2 → RQ3 (pilot one NDC cell first)
   → RQ4 → RQ5 → RQ6 → RQ7 (with the 600 s tail folded in).
3. T-KBg: the prose fold and the one-page reading.

One housekeeping item needs a word from you either way: **job 2247395** is still
re-running shards that are already complete and can only make the cluster tree
drift from the frozen deliverable. Cancelling it needs you to name it
explicitly — the permission guard refuses a generic authorisation.
