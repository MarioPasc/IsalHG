# SESSION_LOG — `[IsalHG-Fable-Review]`, 2026-09-13

*Readiness assessment for the TKDE article ("knowledge bases as words"), written
after reading `START_HERE.md`, `prose.md`, the four handoff/state files of
2026-09-07…11, `DECISIONS.md` (D-ART4, D-ART5, D-KBg1), the `foundation/`
sheets, the T-KB ledger, and the result trees on the drive
(`results/IEEETKDE*`, `results/frozen`). Every number below names its source;
where a number comes from a summary I did not re-derive, the file is the
authority, not this log. §6 answers the five questions the author asked after
the first reading.*

---

## 1. Verdict — can we start writing?

**Yes for most of the paper; no for two sections.**

Five of seven research questions are measured, frozen and audited:

| RQ | status | frozen at |
|---|---|---|
| RQ1 canonical-program design / locality | FINAL | `results/IEEETKDE/RQ1_isal/merged/` (483 files, tag `47c8a42c` + C++ arms) |
| RQ2 well-posedness / false-merge census | DONE (step 4 re-runs after RQ3) | `results/IEEETKDE_isal/RQ2_wellposedness/` |
| RQ5 description patterns | DONE, negative | `results/IEEETKDE_isal/RQ5_patterns/analysis/` |
| RQ6 generation | DONE | `results/IEEETKDE_isal_reach1b/RQ6_generation/` (reach-1 corrected at job 2279079) |
| RQ7 operating envelope + tail-600 | COMPLETE, replicated | `results/frozen/rq7_envelope_2271960_reading/`, `results/frozen/tail600_2279006_verdict/` |

The theory is complete and typeset: Theorem A (`theorem_a_completeness.pdf`),
Theorem C + Props C.4–C.7 (`proofs/completeness/theorem_c_ordered_walk.pdf`
on the drive). The storyline (`prose.md` §12) is PI-ratified and stable.
Sections 1–6 of the paper, and the RQ1/RQ2/RQ5/RQ6/RQ7 result subsections,
can be drafted now.

What cannot be written yet:

- **RQ3 (the representative record).** Its numbers were superseded twice
  (the `reach′` domain fix, then the consensus-objective correction), the
  corrected run's verdict is explicitly *provisional* (`T-KBf` last section;
  `STATE_2026-09-11.md` §9), and about 180 of 4,457 Corpus A collections are
  expected to move. RQ3 is on the thesis's critical path (§4 below).
- **RQ4 (the data-quality screen).** 819 of 1,323 units run, no aggregation
  for the Isal arms exists on disk; the only finished RQ4 table is the retired
  fact-rank one of 2026-09-06.

Start writing anyway, in parallel with closing RQ3/RQ4. Leave those two result
subsections as marked placeholders, and write the abstract and the
contribution list last, because what the paper can promise about the
representative record depends on RQ3.

## 2. The model, in plain words

A knowledge base is a set of facts over constants whose names do not matter,
so it is a labelled hypergraph and two knowledge bases that differ only by a
renaming are the same object. IsalHG writes such an object as a *program* for a
tiny machine: a circular list of constants and `k` pointers, five instructions
(`V` new fact with new constants, `C` new fact over existing constants, `P`/`N`
move a pointer, `W` no-op). Many programs build the same knowledge base; a
*canonical program* picks one per isomorphism class. The paper has two:

- `w*_c` — the lexicographically smallest program, found by search over an
  isomorphism-invariant seed set (Theorem A). Nauty may be used as an
  automorphism oracle to prune the search without changing the value
  (Prop. C.7, orbit pruning).
- `w°` — the *ordered walk*, a program emitted deterministically along the
  constant order that nauty's canonical labelling supplies (Theorem C).

Because each canonical program is a complete isomorphism invariant, plain
Levenshtein distance between programs is a genuine metric on isomorphism
classes. Because every string over the alphabet runs on the machine, every
string is a knowledge base, and Prop. C.4 proves every string is a *connected*
one. Those two facts — exact metric, closed connected language — are the whole
foundation.

The paper's claim is that five properties are needed for collection-level
operations on knowledge bases (exact at zero, metric, polynomial per pair,
closed language, local stability). The first four hold by construction. The
fifth is measured and holds conditionally. Nauty's certificate plus Levenshtein
already gives the first three, faster; the paper's differentiator is therefore
the *language*: decoding, a consensus that is itself a decoded object (RQ3),
generation with validity 1 (RQ6), and pendant locality (RQ1).

## 3. Results per research question

**RQ1 — locality, the nauty ablation.** Frozen, 27 seeds, cluster bootstrap +
Holm, 136,875 common units (`published_tables.md`, M1). The axis that matters
is *pendant* (the edit changes the constant inventory, regime 0) versus
*interior* (regime 1). Fraction of single edits within two instructions:

| edit kind | regime | `w*_c` (orbit) | `w°` (`isal_ow_struct`) | certificate rows |
|---|---|---|---|---|
| delete a fact | pendant | **0.771** (median 1) | 0.732 (1) | 0.000 (11) |
| remove a constant | pendant | 0.815 (2) | **0.826** (1) | 0.000 (11) |
| insert a fact with a new constant | pendant | **0.223** (6) | 0.096 (10) | 0.000 (14) |
| delete a fact | interior | **0.139** (9) | 0.087 (10) | 0.000 (11) |
| insert a fact | interior | **0.082** (7) | 0.047 (10) | 0.000 (9) |
| add a constant to a fact | interior | 0.156 (5) | 0.077 (6) | **0.324** (5) |
| remove a constant from a fact | interior | 0.194 (8) | 0.093 (8) | **0.355** (7) |

Reading: on every pendant cell both Isal programs beat the certificate, which
never lands within two rows. The certificate wins only the two argument-level
interior edits (widening or narrowing an existing fact). The retired fact-list
word (not in the paper's tables, D-ART4) beats us on interior deletions
(57.8 % vs 13.9 %). Pooled over all kinds, no ordered-walk arm beats the
certificate rows (0.070 vs 0.179), so the pre-registered escape clause fired
and the paper argues from the language, not from locality (D-ART5). Ladder
monotonicity (M2): `w*_c` leads the WD50K ladder (ρ = 0.537), the ordered walk
leads the NDC natural pendant series (ρ = 0.556); the certificate leads the
WD50K ladder at the bytes tokenisation (ρ = 0.677).

**RQ2 — well-posedness.** `w*_c` induces the exact true partition on all three
collections (530 / 1,086 / 3,677 classes, zero false merges), as do the two
certificate tokenisations, the retired fact-rank word, and — on this data —
WL. NetLSD merges 2,516 / 1 / 185,917 non-isomorphic pairs, HPD
7,618 / 9,885 / 212,179. Bipartite GED (edit-path reading) fails the other way:
it splits 557 true classes into 574. (`rq2_wellposedness_facts.md` §1.)

**RQ3 — representative record.** Provisional. On constant-preserving ladders
(Corpus A) the ball-coverage consensus recovers the source in 83.5 % of
collections against 0 % for every medoid — but the medoid there is a
structural floor (it returns a member and the source is not a member), so
"beats the medoid" is not an achievement. It fails at deletion budget 2
(0.13–0.28), where the identity-using majority merge also fails (0.21), so the
pre-registered ≥ 0.95 threshold was unachievable by any method. On the natural
NDC quarterly series (Corpus B) the consensus *ties* the best medoid on both
axes with an underpowered test (MDE ≈ 0.40 vs observed Δ 0.03–0.11), which the
gate sent to the supplement. The objective was then corrected (tie-break moved
off the retired word; out-of-domain candidates excluded) and the re-run's
verdict is pending. (`T-KBf` §RQ3; `IEEETKDE_isal_consensus/`.)

**RQ4 — data-quality screen.** Not complete for the Isal arms. The retired
fact-rank table (2026-09-06) shows iso-twins detected at AUC 0.72–0.80 versus
chance 0.50, but below the best competitor in 39 of 42 cells. Expect "exact
but not competitive". Note for §6.2: `wl_l1` scored 0.805 on NDC iso-twins,
*above* fact-rank's 0.764, so the twin construction did not hide the twins
from WL as intended; check before claiming RQ4 exposes WL's incompleteness.

**RQ5 — description patterns.** Negative for everyone. Best ARI against
Wikidata types is 0.075 (HPD); ours 0.030–0.042; the naive size and
degree-sequence floors beat us significantly (rank-biserial −1.000 on two of
four comparisons). The non-Euclidean licence holds (ν = 0.10, 1,553 negative
eigenvalues); the hubness licence fails (5.4 vs 1.5 ceiling). Consistent with
the sibling article's S7 loss. Goes to the supplement as a stated negative.

**RQ6 — generation.** The strongest positive. An n-gram model over ordered-walk
words returns a valid *and connected* knowledge base on 270,000 of 270,000
samples per collection (validity 1.0000, connectivity 1.0000, by Prop. C.4).
The incidence-list generator rejects 98.10 % (NDC) / 98.98 % (WD50K) of its own
output. The fact-list generator is valid but connected only 41.6 % / 12.6 %.
Novelty favours the fact list (0.988 / 0.943 vs 0.917 / 0.914), but of its
novel WD50K samples only 7.3 % are connected, i.e. encodable at all.
(`rq6_generation_facts.md`.)

**RQ7 — operating envelope.** The ordered walk censors 0 of 7,776 sweep
instances at 60 s, including all 427 at `|Aut| ≥ 10⁷` where the pointer search
fails every one and orbit-pruned `w*_c` censors 91.8 %. The frontier is the
fact count `m`, not the constant count `n`. On the real collections the walk
canonicalises 8,951 of 8,951 members at 0.60–0.70 ms median. The full
3,988 × 3,988 matrix on `wd50k66` takes 1.39 s for the walk against 28.9 min
for `w*_c` (1,252×, same alphabet, same code path). Every speed claim against
the nauty certificate is withdrawn: at matched tokenisation the two are at
parity (1.09–1.19×), and a Python-loop bug in the rows arm (T-KBy) inflated
the certificate's timing 20× in our favour. The tail-600 study refuted D-ART5's
rationale for `w*_c`'s residual censored tail: the rank-keyed walk clears
50.9 % of it against orbit's 24.7 % (Fisher p = 0.0028), so the tail is search
cost, not an intrinsic property of arity-10 members.
(`rq7_envelope_facts.md`; `frozen/tail600_2279006_verdict.README.md`.)

## 4. The structural tension the writing will expose

D-ART5 makes `w*_c` (orbit-pruned) the paper's representation. But the two
headline positives belong to the ordered walk `w°`: the zero-censoring envelope
and the 1,252× matrix time (RQ7), and the RQ6 generator was fitted on
ordered-walk words (`ow_ngram`). `w*_c` still censors 77 real members at 60 s
and, on a 3,988-member collection, takes half an hour to build the matrix that
every application consumes. Meanwhile RQ2, RQ3 and RQ5 ran on `w*_c`. The paper
currently mixes programs across experiments without saying so. §6.5 resolves
this.

With RQ5 negative, RQ4 likely uncompetitive, and RQ1's escape clause fired, the
case that "a language beats a certificate" rests on RQ6 plus RQ3. RQ6 is
unconditional. RQ3 is provisional and, as it stands, wins only against a
structural floor and ties on the natural series. **RQ3 is the critical path.**

## 5. Blockers, in the order to clear them

1. **Land the corrected RQ3 re-run and re-apply the pre-registered gate** to the
   new numbers (`T-KBf`; job 2276107 lineage; `IEEETKDE_isal_consensus/`).
   Decide main text vs supplement for the natural series on the new rows.
2. **Finish RQ4 or cut it to the supplement.** Restore the depleted iso-twin
   cell (T-KBq, T-KBv) or drop the section. A half-run experiment cannot be
   cited.
3. **Fix T-KBy** (Python double loop in `nauty_cert_rows.matrix()`) and
   re-check every cost comparison in RQ1, RQ2, RQ5. Distance values are
   unaffected; only timings are.
4. **Resolve the data-section contradictions**: D-KBg1 (the supplement still
   prints 1,432 / 3,167 / 21.6 % and calls the retired word "the adopted
   encoding"; the prose prints 1,381 / 3,162 / 22.2 %) and T-KBk (519 NDC
   members dropped at the arity cap, unstated anywhere).
5. **Write the missing fact bases** for RQ3, RQ4, RQ5 (`foundation/rq*_facts.md`
   exist only for RQ1, RQ2, RQ6, RQ7). T-KBg's precondition stands: no number
   enters the prose without a sourced entry naming run root, job and table.
6. **Get the PI's word on D-ART5** (T-KBe's last acceptance line) — or, per
   §6.5, put the program decision back to the PI with the RQ7 evidence.

## 6. The five questions

### 6.1 If `w*_c` is canonical, why compute the ordered walk at all? Is "Isal + nauty" a canonical string?

**Yes, `w°` is a canonical string.** Theorem C proves that any deterministic
emitter that follows a canonical labelling and round-trips through `S2H` is a
complete isomorphism invariant, so `w°(K) = w°(K') ⇔ K ≅ K'`, and Corollary C
makes its Levenshtein distance a metric on isomorphism classes. It is a
*different* canonical form from `w*_c` (the two agree on 0 % of instances,
`D_ART5_DECISION_BRIEF.md` §2), but equally canonical. The rank-keyed greedy
walk `w*_ρ` (the "both" cell) is *not* covered by Theorem C as stated and has no
theorem of its own; it is an RQ1 ablation cell only.

**What `w°` gives that `w*_c` does not.** `w*_c` is the minimum of a search.
The search is exponential on symmetric inputs, and orbit pruning removes the
symmetry cost but not the arity-10 displacement tail (77 real members censored
at 60 s; 91.8 % censored at `|Aut| ≥ 10⁷` in the sweep). `w°` has no search:
one nauty call plus a linear emission, 0 of 7,776 censored, 8,951 of 8,951 real
members canonicalised, 1.39 s instead of 28.9 min for the N × N matrix. That is
not a speed *win* over nauty (parity, RQ7); it is the removal of the one
property that would disqualify the representation from its own prerequisite
list — "polynomial per-pair cost *after one canonicalisation*" is void for a
member that never gets canonicalised.

**What `w*_c` gives that `w°` does not.** It is alphabet-intrinsic: Theorem A
needs no external engine, nauty enters only as an optional value-preserving
oracle. It is more local under insertions (RQ1: 0.223 vs 0.096 within two on
insert-with-new-constant; 0.082 vs 0.047 on interior insertion), because the
greedy search creates a constant's facts while that constant is one pointer
step away, whereas the ordered walk's breadth-first order defers them
(Obs 13). And it is the string D-TA2 froze.

**Why the ablation exists.** The PI's framing (D-ART4 addendum) is
"nauty + Isal" versus "nauty": the paper must show what a canonical-labelling
engine contributes *inside* an Isal encoder, in each of its two roles (as an
order, as an oracle), and what the language adds on top. Without `w°`, a
reviewer says "your representation is a slow search; nauty does identity in
microseconds." With `w°` the answer is: the language's properties (closure,
connectivity, decoding, generation, pendant locality by name-freedom,
Prop. C.6) are properties of the *alphabet and machine*, not of how the
canonical program is chosen; plug nauty's order in and you keep every one of
them at nauty's cost plus a linear emission. The ablation is what turns
"we depend on nauty" from a weakness into the mechanism of the paper.

### 6.2 RQ2: WL also had zero false merges. Can we argue it is vectorial rather than canonical?

Yes, but as two separate arguments, and neither should spin the zero.

**Argument 1 — guarantee versus count.** WL is provably incomplete
(refinement-based keys cannot separate all non-isomorphic hypergraphs;
Prop 9, cited). Its zero false merges on these three collections is an
empirical fact about *these corpora*: real, labelled, irregular knowledge bases
happen to contain no WL-indistinguishable non-isomorphic pair. The honest
sentence is: "WL's incompleteness did not materialise on these collections; what
separates the two is the guarantee, not the count." A WL histogram is a metric
on vectors and only a pseudometric on isomorphism classes (`d = 0` does not
imply `K ≅ K'`). That is exactly the "exact at zero" column of the capability
matrix, filled by theorem, and a measured zero does not fill it.

**Argument 2 — vectorial means no language.** Independently of exactness, a WL
vector has no decoder: no string of it is a knowledge base, no edit of it is an
edit of a knowledge base, no consensus computed on it is a decoded object, and
no generative model over it produces knowledge bases. That is the "closed
language / consensus is a decoded object / generative model definable" columns,
and WL is blank on all three by construction, as are NetLSD and HPD.

**Where WL's incompleteness is supposed to bite: RQ4.** The iso-twin
construction (non-isomorphic twin matching size, degree sequence *and
refinement colouring*) is designed so WL merges the twin with the original.
But the retired-arm RQ4 table shows `wl_l1` at AUC 0.805 on NDC iso-twins,
above fact-rank's 0.764 — so either the twins differ at a WL depth the
construction did not match, or the histogram distance separates them for a
reason other than the colouring. Verify this before the paper claims that RQ4
exhibits WL's false zeros; if it does not, the claim rests on Prop 9 alone.

### 6.3 Which results should be the headlines?

Criteria: (a) uses a property of IsalHG, (b) beats every competitor in the
paper's tables, (c) has a practical knowledge-base implication.

| candidate | (a) | (b) | (c) | verdict |
|---|---|---|---|---|
| **RQ6 generation** — 270,000/270,000 valid and connected; incidence list rejects 98–99 %; fact list connected 42 % / 13 %; certificates admit no generator | closed connected language (Prop. C.4/6) | yes, on the axis that matters (usable samples); novelty is lost to the fact list and the loss is stated | benchmark construction, synthetic stand-ins, completion suggestions | **headline 1** |
| **RQ1 pendant locality** — within two instructions on 73–83 % of pendant deletions/removals and 22 % of pendant insertions; certificate 0 % on all | name-freedom (Prop. C.6), the pointer machine | yes against every measured competitor on pendant cells; the interior loss (certificate on argument edits, fact list on interior deletions) is printed beside it; WL/NetLSD/HPD unmeasured, blank with reason | change tracking of a knowledge base across versions (quarterly co-formulation records); a new constant costs a constant number of instructions | **headline 2, stated with its condition** |
| **RQ3 consensus as a decoded object** — a representative that is not a member, computed in the language | closed language + reach | pending; currently wins only against a structural floor and ties on the natural series | golden-record construction | headline 3 *if* the corrected run supports it; otherwise an exhibit |
| RQ2 exactness — 0 false merges, exact partition | complete invariant (Thm A / C) | ties the certificate and WL; beats NetLSD, HPD, bipartite GED | duplicate handling, exact census | foundation table, not a headline: the certificate has it too |
| RQ7 envelope — 0/7,776 censored, 1.39 s matrix | deterministic canonical program | beats the pointer search, not the certificate (parity) | applications run interactively on thousands of members | enabling result: it prices the language's cost at "nauty + linear"; not a competitor-beating headline |
| Compactness — 6 / 8 instructions vs 12 certificate rows | length bound (Prop 1) | yes | key size | one sentence |
| Decodability figure — every interior word of an alignment path decodes | closed language | certificate interiors decode to nothing | interpolation, explanation | qualitative exhibit inside RQ6 |
| Certified medoid ratio ≤ 2 − 2/N | any metric | the certificate gets it too | guarantee for the representative | not IsalHG-specific; state as a property of the family |

The only result that meets all three criteria unconditionally is RQ6. RQ1 meets
them on the pendant axis with the interior loss printed. That is thin for TKDE,
which is why RQ3 matters: a consensus that no certificate or vector can compute
is the second unconditional language result the paper needs, and it is the one
still unsettled.

### 6.4 Who are the competitors?

Grouped by the prerequisite each one lacks (`prose.md` §6, `COMPETITOR_AUDIT.md`):

| competitor | what it is | what it lacks |
|---|---|---|
| exact structural edit distance (HGED oracle) | the true fact-level distance, small instances only | polynomial cost (NP-hard per pair) |
| bipartite GED, assignment value (`bipartite_ged_assign`) | Hungarian lower bound | exact at zero (pseudometric, false zeros) |
| bipartite GED, edit-path cost (`bipartite_ged_path`) | Hungarian upper bound | the metric axioms (38 % asymmetric, 1.4 % triangle violations, Serratosa 2019); splits true classes (RQ2) |
| identity-using majority merge | the RQ3 reference; uses constant identities we deny ourselves | not a distance; not isomorphism-invariant |
| WL histogram (`wl_l1`) | refinement colour counts, L1 | exact at zero by theorem (Prop 9); no language |
| NetLSD (`netlsd`) | heat-trace spectrum on the Levi graph | exact at zero (185,917 merges on WD50K); no language |
| hyperedge portrait divergence (`hpd_jsd`) | shortest-path portrait, JSD | exact at zero (212,179 merges); no language |
| HyperCOT (gated) | hypergraph optimal transport | polynomial cost in practice (local optima, O(n³) per pair); external measure; no decoder |
| **the certificate member** (`nauty_cert` bytes, `nauty_cert_rows` rows) | nauty canonical labelling + Levenshtein: the same family, exact, metric, polynomial | a language: no decoder, no edit closure, no consensus object, no generator; pendant locality |
| naive floors (`size_l1`, `degree_seq_l1`) | size and degree-sequence distances | everything; they are the confound guard (L1) |
| *record only*: the fact-rank word and its addressing arms | the retired 2026-09-04 encoding | a machine (D-ART4); disconnected samples 58 % / 87 % |

The certificate member is the comparison that decides the paper. It matches us
on exactness, metric, cost and compactness; it loses on the language columns,
on pendant locality, and nowhere else.

### 6.5 One headline program: `w*_c` or `w°`?

Agreed that the paper cannot say "this one for this, that one for that". The
evidence, arm against arm:

| axis | `w*_c` (orbit-pruned) | `w°` (ordered walk) | source |
|---|---|---|---|
| exact + metric | Theorem A, alphabet-intrinsic | Theorem C, needs nauty's order | proofs |
| censoring, real collections at 60 s | 77 of 7,369 (arity-10 tail; search cost per tail-600) | **0** of 8,951 | RQ1 M3, RQ7 yield |
| censoring, sweep at `\|Aut\| ≥ 10⁷` | 91.8 % | **0 %** | RQ7 |
| N = 3,988 matrix | 28.9 min | **1.39 s** | RQ7 |
| pendant locality, within two | **0.771 / 0.815 / 0.223** | 0.732 / 0.826 / 0.096 | RQ1 M1 |
| interior locality, within two | **0.139 / 0.082 / 0.156 / 0.194** | 0.087 / 0.047 / 0.077 / 0.093 | RQ1 M1 |
| ran RQ2, RQ3, RQ5 | yes | no | drive |
| ran RQ6 | no | **yes** (`ow_ngram`) | drive |
| continuity with D-TA2 / the preprint | the frozen string | a new canonical form | DECISIONS |

**Recommendation: make `w°` the headline program, and put that to the PI as a
revision of D-ART5, with this table.** The decisive reason is the paper's own
prerequisite list. Prerequisite 3 is "polynomial per-pair cost after one
canonicalisation"; a program that fails to canonicalise 77 real members and
takes half an hour to build the matrix every application consumes does not
satisfy it on the collections the paper runs on, and no amount of orbit
pruning fixes the tail (tail-600 showed the tail is the search itself). `w°`
satisfies it everywhere measured. `w*_c`'s advantages are locality (real, but
0.22 vs 0.10 on the one pendant cell where it is large, and both beat the
certificate on every pendant cell regardless) and theoretical self-containment
(real, and kept: Theorem A stays as the family's foundation; `w*_c` appears in
RQ1's ablation as the "no-search" cell and nowhere else).

Cost of the switch: RQ2 (a census, 0.6 ms per member), RQ3 (re-running now
anyway, so the arm swap is free) and RQ5 (negative, cheap) re-run on `w°`
words. Cost of *not* switching: RQ6 must be re-fitted on `w*_c` words, RQ7's
headline becomes a footnote, and the paper ships a representation that
violates its own third prerequisite on its own data, which a reviewer will
find in the yield table.

The reviewer's "it is just nauty written as a program" objection lands equally
on both (nauty is inside `w*_c` as the oracle and inside `w°` as the order); the
answer is the same in both cases and is the language argument of §6.1. It does
not decide the choice.

If the PI keeps D-ART5, the paper is still writable: state once that every
table uses `w*_c`, re-fit RQ6 on `w*_c` words, and carry the 77 censored
members and the 28.9 min in the envelope table as a stated limit. What is not
acceptable is the current state, where RQ6 and RQ7 headline one program and
RQ2/3/5 run on the other without the prose saying so.

## 7. Open threads for the next session

- Put §6.5 to the PI (D-ART5 revision or confirmation) before any table is
  transcribed into the draft.
- Re-verify the RQ4 iso-twin / WL observation of §6.2 on the RQ4 rows once RQ4
  completes.
- Extract the RQ1 per-corpus tables (the pooled pendant-deletion 0.771 is
  WD50K's 0.845 averaged with NDC 0.576 and synthetic 0.090, `T-KBe` §M2) and
  quote per corpus in the paper, never pooled.
- Two RQ7 headline numbers exist only in `results/frozen/` (the N = 3,988
  `w*_c` timing reads *censored* at the 3,600 s cap in the live tree); cite
  the frozen copy.
- Ledger items still open: T-KBa, c, g, h, i, j, k, l, m, n, p, q, r, s, t, u,
  v, w, x, y; T-KBb/d/e/f in progress. T-KBj (the `fork` fix) must not land
  mid-campaign.

---

## 8. Addendum 2026-09-13 (second turn) — the author's rulings and the campaign

The author ruled on §6: `w°` is the headline program (D-ART6); the headline
exhibits are RQ6, a redesigned RQ3 and one new experiment, each meeting
(a) uses a property of IsalHG, (b) beats every competitor that can be scored,
(c) answers a knowledge-base question; every competitor appears in every
table; a measured capability table with IsalHG last and bold.

**One finding that shaped the design.** Most WD50K entity knowledge bases are
stars (every fact contains the root, no non-root constant shared), and the
isomorphism class of a star is the multiset of its fact patterns — which WL,
degree sequences and plain counting determine exactly. That is why RQ5 and RQ4
were lost and why RQ2's WL count was zero. The hypergraph machinery matters
only where constants are shared across facts (NDC by construction; WD50K on
its non-star subset). Every new experiment is stratified star / non-star,
claims the relational stratum, and reports the star stratum as the control
where counting is expected to tie. Gate G0 measures the star fraction.

**What was written.** `experiments/HEADLINE_DESIGN_2026-09-13.md` (the
pre-registered spec: RQ3 v2 golden record with anonymous alignment-merge and
pattern-vote baselines and the reach-coverage gate; RQ8 valid completion with
the recommender baselines and the pilot gate; the `w°` swap of RQ2/RQ5; the
table spec), `tables/tab_kb_representation_properties.tex`, D-ART6 in
`DECISIONS.md`, banners on `prose.md` and `START_HERE.md`.

**Wave `2026-09-13-headline-w0`.** Two Opus agents in isolated worktrees:
`rq3v2` (Agent A) and `rq8` (Agent B, also the RQ2/RQ5 swap). Each: cloned env,
tests, local pilot gate reported to the orchestrator, `picasso-sbatch`
scripts, sync and submit, job ids in its note. Verification and merge by the
orchestrator per the parallel-agents protocol; summary in
`.claude/notes/2026-09-13-headline-w0/summary.md`.

**Honest risk statement.** Neither RQ3 v2 nor RQ8 is guaranteed to satisfy
(b). Each has a pre-stated mechanism for the win (reference-anchored merges
cannot recover pendant facts the reference lacks; counting cannot choose
attachments on non-stars) and a pre-registered fallback. The pilots decide
before anything is submitted; the fallbacks are printed, not argued around.

## 9. Outcome of wave `2026-09-13-headline-w0` (same day)

Both agents delivered and were merged on `integration/2026-09-13-headline-w0`
(638 passed, the six pre-existing failures unchanged, ruff 38, mypy 20). Wave
record: `.claude/notes/2026-09-13-headline-w0/summary.md`; the pre-registration
amendments and every ruling are in `experiments/HEADLINE_DESIGN_2026-09-13.md`
§8.

**Measured before any campaign number (the gates).** WD50K(66) is 53.4 %
stars, NDC-classes 3.0 %; the NDC star stratum is empty everywhere. Every
single fact edit is one fact-space step away; at word radius 2 the source is
in the union of the members' balls on every mixed `t = 1` cell; 426,433 ball
words all decoded connected. The corrected v1 consensus recovers 0.998
insertion / 0.863 mixed / 0.517 deletion against 0.000 for every medoid.

**Three rulings that changed the science, each pre-registered.** (1) The
consensus is computed in word space; v1's fact-space machinery is the
ablation. (2) Coverage-first is size-biased in word space, and the word median
under Levenshtein cannot separate a source from its sub-records on deletion
noise because a substitution charges a fact swap 1–2 while a deletion costs 1;
the primary is the generalized median under the **indel** distance, under
which the source strictly wins for `N ≥ 3`, with a certified ratio and a
like-for-like indel medoid. On the first real smoke collection this returned
the source exactly (ratio 1.091 vs medoid 1.152) where the Levenshtein median
tied and lost it. (3) RQ8's counting baselines add exactly one fact by
construction; fact-count-matched arms were added before re-measurement.

**RQ8 verdict.** H8.1 fails on NDC (co-occurrence recommender 0.303 vs ours
0.175 matched hit@10, a pattern gap: 0.29 vs 0.89 pattern@10) and holds on
WD50K only at three seeds (0.038 vs 0.013, untested). Matched, every
ordered-walk arm attaches better than either recommender (NDC 0.35–0.39 vs
0.66 / 0.58), so the attachment mechanism is supported. RQ8 is a supporting
exhibit under the pre-registered fallback. The paper's task-metric pattern
holds: we lose to task-specific counting where the structure is a multiset,
and win on the structural guarantees.

**Running on Picasso.** RQ3 v2 `2308421` (122 tasks); RQ8 `2308339`
(completed, free-running record) and `2308489` (matched); RQ2_ow `2308342`,
`2308343`; RQ5_ow `2308368`. Results root `~/results/IEEETKDE_ow/`.

**Pending the author.** Merge `integration/2026-09-13-headline-w0` into
`feature/isal-kb-word`; the PI's word on D-ART6; the FSCRATCH quota question;
harvesting the four campaigns into the fact bases and the `\todo` cells of the
capability table.
