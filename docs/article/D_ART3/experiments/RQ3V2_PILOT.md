# RQ3 v2 — the gates, and what they decided

Gates G0, G3.2 and G3.1 of `HEADLINE_DESIGN_2026-09-13.md` §2–§3, measured before
any campaign was submitted, plus the local pilot that prices the full run. Every
number here was produced by the code in `experiments/tkde/rq3v2.py` or by a
probe against the frozen corpora; none of it is an estimate.

Ledger task: `../../DEVELOPMENT/T-KB/IN-PROGRESS/T-KBz.md`. Fact base:
`../foundation/rq3v2_facts.md`.

---

## Gate G0 — the star census

A member is a **star** when one constant lies in every fact and no other
constant lies in two. WD50K's root is the entity and the definition recovers it
without reading the metadata; NDC has no root, so an NDC record is a star only
when such a constant happens to exist. The strata of §3 and §4 are built on this
predicate, because on a star the isomorphism class is the multiset of fact
patterns and counting determines it without any alignment.

**G0a — the whole frozen corpus.**

| corpus | N | stars | frac star | non-stars | frac non-star | non-star median shared constants | non-star median shared facts |
|---|---|---|---|---|---|---|---|
| `ndc_classes` | 1,381 | 42 | 0.030 | 1,339 | 0.970 | 2 | 3 |
| `wd50k66` | 3,988 | 2,128 | 0.534 | 1,860 | 0.466 | 3 | 4 |

**G0b — restricted to the RQ3 source window** (`4 ≤ n ≤ 12`, `4 ≤ m ≤ 12`,
max arity ≤ 6, constant identities present). This is the pool the experiment
actually draws sources from, and it is the table the data section should carry.

| corpus | pool | stars | non-stars | frac star | non-star median (shared constants / shared facts) | median m (star / non-star) |
|---|---|---|---|---|---|---|
| `ndc_classes` | 212 | **0** | 212 | 0.000 | 2 / 4 | — / 4 |
| `wd50k66` | 1,871 | 1,011 | 860 | 0.540 | 2 / 3 | 5 / 5 |

Reproduce with
`python -m experiments.tkde.rq3v2 --config experiments/tkde/configs/rq3v2.yaml --census`.

**Two findings, and one of them changes the design.**

*The `ndc_classes` star stratum is empty.* Not scarce — empty: zero of the 212
members inside the source window are stars, and even unrestricted only one of
the 522 members with `m ≥ 4` is. NDC co-formulation records are genuinely
relational, which is what the design predicted, but it means **H3.4, the star
control, is measured on `wd50k66` alone**. The empty cells are not dropped: each
emits one row with `method = cell_empty` carrying the reason, so the absence is a
recorded measurement rather than a gap in a table.

*The premise "most WD50K entity knowledge bases are stars" is true but weaker
than stated.* It is 53.4 % corpus-wide and 54.0 % in the source window, so
`wd50k66` supplies a genuinely balanced 1,011 / 860 split and both strata are
well powered. The design doc's "most" should be read as "about half".

---

## Gate G3.2 — the corrected v1 run, harvested

Source: `results/IEEETKDE_isal_consensus/RQ3_representative/corpus_a/rows_variants.csv`
(git `4eebccc`, 2026-09-10, 62,398 rows, 27 seeds, censoring 0.000 on every one
of the eleven arms). Read numerically, never by string comparison — v1 serialized
`exact_recovery` as `'1'` on one corpus and `'1.0'` on the other, and a `== "1"`
test silently reported a recovery collapse on the corpus it did not match
(T-KBs).

**Exact recovery by cell kind.**

| method | del | ins | mix |
|---|---|---|---|
| coverage consensus, r = 2 | **0.517** | 0.998 | 0.863 |
| `majority_merge_id` (oracle, has identities) | 0.680 | 0.999 | 0.913 |
| every one of the 11 medoids | 0.000 | 0.000 | 0.000 |

**The deletion regime, by (N, t).**

| method | N5 t1 | N5 t2 | N9 t1 | N9 t2 |
|---|---|---|---|---|
| coverage consensus | 0.826 | 0.195 | 1.000 | 0.525 |
| `majority_merge_id` | 1.000 | 0.252 | 1.000 | 0.950 |

**Mean fact-level distance, deletion regime.** Consensus 0.19 at `t = 1` and
1.32 at `t = 2`; every medoid at exactly `t` (1.00 and 2.00) — the structural
floor, visible as a flat column.

**Winner origin.** 93.3 % of collections returned `transfer`, i.e. an object no
member wrote. That is the claim RQ3 makes, measured rather than inferred.

**What the gate decided.** v1's deletion regime was 0.13–0.28 before the
objective was corrected; the corrected run is 0.517 pooled and 1.000 in two of
the four deletion cells. v2 inherits the fix, and the pre-registered ≥ 0.95
threshold that no method could meet is not carried forward.

---

## Gate G3.1 — reach coverage of the noise model

The gate asks whether the noise model's edits stay inside the neighbourhood the
consensus explores. It has two halves, because the design's wording and the
machinery it gates are in different spaces (orchestrator ruling, 2026-09-13:
report both).

### G3.1(a) — fact reach, the precondition of the `reach′` pool

200 real members per corpus, stratified, one edit of each kind per member;
1,200 units; zero censored.

`reach_F(K, K ⊕ e) ≤ 1` has coverage **1.000** for every corpus × stratum × edit
kind. The fact-space candidate pool therefore has complete coverage of the noise
model at `r = 1`, and a fortiori at the `r = 2` the design fixes.

Availability is itself a measurement: `wd50k66` star × `del_interior` is **0.00**
by definition — a star has no interior fact — and `wd50k66` non-star ×
`del_interior` is 0.54. Every other cell is 0.95–1.00.

### G3.1(b1) — canonical-word distance, the locality contrast

`d(w(K), w(K ⊕ e))` in tokens, for `w°` (`isal_ow_struct`) and `w*_c`
(`wstar_orbit`) on the same units. `w*_c` censoring 0 / 1,200 at a 20 s budget.

| cell | `w°` cov r=2 | `w°` median | `w*_c` cov r=2 | `w*_c` median |
|---|---|---|---|---|
| ndc non-star `del_pendant` | 0.589 | 1 | 0.568 | 1 |
| ndc non-star `del_interior` | 0.101 | 4 | 0.384 | 3 |
| ndc non-star `ins_existing` | 0.020 | 14 | 0.010 | 8 |
| ndc non-star `ins_new_constant` | 0.060 | 10 | 0.070 | 7 |
| wd50k non-star `del_pendant` | 0.576 | 2 | 0.707 | 1 |
| wd50k non-star `del_interior` | 0.093 | 9 | 0.056 | 6 |
| wd50k non-star `ins_existing` | 0.030 | 9 | 0.020 | 6 |
| wd50k non-star `ins_new_constant` | 0.030 | 11 | 0.190 | 5 |
| wd50k star `del_pendant` | **1.000** | 1 | 1.000 | 1 |
| wd50k star `ins_existing` | 0.020 | 8 | 0.040 | 5 |
| wd50k star `ins_new_constant` | 0.240 | 4 | 0.370 | 3 |

Two things follow, and both are used later.

*A deletion is local and an insertion is not.* Deleting a pendant fact moves the
word by a median of one token; inserting a fact moves it by 5 to 14. The walk is
rooted at the hub and ordered by nauty's canonical order, so an inserted fact
changes the rank order and rewrites the walk from the insertion point onward.
This asymmetry is what makes the coverage objective unusable in word space
(§"The objective" below) and what H3.6 predicts will bite the median at small
`N`.

*`w°` is below `w*_c` where the design said it would be.* Materially so on
`ins_new_constant` (0.030 against 0.190 on wd50k non-star; 0.240 against 0.370
on stars) and on ndc `del_interior` (0.101 against 0.384); above it on ndc
`del_pendant`. This reproduces `SESSION_LOG.md` §6.5, which measured `w*_c` as
the more local of the two and made `w°` headline on cost and censoring instead.
Reported, as the gate requires; it does not block, because (b1) is not the
question the consensus asks.

### G3.1(b2) — ball reachability, the operative gate

The consensus does not need the source's *canonical word* to be near a member's;
it needs the source's *class* to be in the decoded image of the members' balls.
A word one token from `w(K)` can decode to the class of `K + f` even when
`w(K + f)` is ten tokens away — the Prop-4 argument in `isalhg/language/ball.py`.
The gate is therefore: is the source's class in the decoded image of
`⋃ᵢ B_r(w°(Kᵢ))`, enumerated over the collection's own token vocabulary?

Ten families per cell. The ball is **not** collapsed by a multiset signature —
the ordered walk is a program and token order decides the decode — only by the
decoded structure, before the canonical key is paid for.

| cell | ball | source in ball | classes (median) | s median / max |
|---|---|---|---|---|
| wd50k non-star N5 t1, mixed | indel r=1 | **1.000** | 300 | 0.06 / 0.12 |
| wd50k non-star N5 t1, mixed | indel r=2 | **1.000** | 12,511 | 7.7 / 25.8 |
| wd50k non-star N5 t1, deletions only | indel r=1 | 1.000 | 60 | 0.00 / 0.01 |
| wd50k non-star N5 t2, deletions only | indel r=2 | **1.000** | 261 | 0.23 / 1.05 |
| wd50k star N5 t1, mixed | indel r=2 | 1.000 | 5,592 | 2.4 / 16.0 |
| ndc non-star N5 t1, mixed | indel r=2 | **1.000** | 19,108 | 13.7 / 39.3 |
| ndc non-star N5 t1, mixed | restricted, append ≤ 3 / delete ≤ 2 | **1.000** | 2,983 | 1.6 / 3.0 |
| ndc non-star N5 t2, deletions only | indel r=2 | **0.375** | 1,052 | 0.33 / 0.80 |

**The gate passes at r = 2** on the mixed noise model at `t = 1`: 1.000 on both
corpora and both strata. No edit kind is restricted out, and the noise model of
`configs/rq3v2.yaml` keeps all four.

**The envelope boundary, stated rather than patched.** The deletion-heavy `t = 2`
cell on `ndc_classes` reaches 0.375, because a member missing two facts is two
insertions from the source and `r = 2` is exactly that budget with nothing to
spare. The radius is **not** raised for it (orchestrator ruling): the cell stays
in the run, is printed, and is reported as where the `r = 2` envelope ends.

**The ball choice is a cost choice, not a coverage choice.** The restricted ball
reaches the same 1.000 with 2,983 classes in 1.6 s where the full indel ball
needs 19,108 in 13.7 s — a factor of nine on the heaviest cell. The primary
remains the full indel ball at `r = 2`; the restricted family is the declared
fallback if the priced full run does not fit.

**Ambient decodability, free of charge.** 426,433 ball words were decoded during
these probes and 426,433 decoded to a *connected* knowledge base — no exception,
no disconnected result. That is Prop. C.4 measured on the ambient space rather
than on objects that were already knowledge bases, which is the distinction
lesson L19 insists on.

---

## The objective, and why it is not v1's

`consensus_ow` at `r = 2` under v1's objective — maximise coverage, then minimise
the summed distance — does **not** return the source, even though the source is
always in its pool. Diagnosed on three collections: the source ranked 1st, 3rd
and 3rd of 3,629–11,451 classes and had the *lowest* summed distance of the
leaders every time (7, 9, 11). It loses on coverage, the first criterion.

The mechanism is G3.1(b1) again. A deletion costs about one token and an
insertion five to ten, so inside a fixed radius every member can delete its way
to a common core while none can insert its way to a larger object. The winners
were `n = 7, m = 3` against sources of `n = 9, m = 4`. Coverage is therefore a
*biased* statistic in word space. In fact space, where `reach′` charges an
insertion and a deletion alike, the bias does not exist — which is why v1 could
put coverage first and why `consensus_fact` still does.

The pre-registered primary (orchestrator ruling, 2026-09-13, before any
campaign number was seen) is the **generalized median in the word metric**:
minimise `Σᵢ d_I(w°(M), w°(Kᵢ))`, ties by coverage, then by the shortlex of `w°`.
Three a-priori grounds:

1. it is the classical consensus objective in string spaces;
2. the medoid is the same objective restricted to the members, so the consensus
   cost is **at most** the medoid's by construction;
3. Prop 3's pairwise bound `LB = Σ_{i<j} d(Kᵢ, Kⱼ) / (N − 1)` lower-bounds the
   optimum over *every* point of the space, so the arm carries a **certified
   ratio** `cost / LB` reportable beside every medoid's. A coverage objective
   admits no such certificate.

### Pre-registration amendment, 2026-09-13: the metric is indel, not Levenshtein

Measured after the objective was fixed and before any campaign number was seen.
On a star whose `N` members each drop one distinct fact, the median under
**Levenshtein** cannot separate the source from its own sub-records:

| candidate | word length | distance to each member | cost |
|---|---|---|---|
| source | 5 | 1, 1, 1, 1 | **4** |
| member 0 | 4 | 0, 1, 2, 2 | 5 |
| member 1 | 4 | 1, 0, 1, 2 | **4** |
| member 2 | 4 | 2, 1, 0, 1 | **4** |
| member 3 | 4 | 2, 2, 1, 0 | 5 |

Coverage ties as well (all four classes are reached by all four balls at `r = 2`),
so the *tie break* returned the answer — and shortlex returns the shorter word,
hence the smaller record.

The cause is a substitution. Two members differ by a fact **swap**: one member
has fact *a* where another has fact *b*. Levenshtein charges that one
substitution; at fact level it is two edits, a deletion and an insertion. The
under-charge falls precisely on the candidates that compete with the source.

**The primary metric is therefore the indel distance**
`d(w₁,w₂) = |w₁| + |w₂| − 2·|LCS(w₁,w₂)|` — insertions and deletions at unit
cost, no substitutions. Two reasons, both a priori: it is the metric of the ball
this arm enumerates, so the objective and the candidate set live in one geometry;
and a substitution has no fact-level counterpart at unit cost. Under indel the
source costs `N` and every sub-record `2(N − 1)`, a strict win for `N ≥ 3`, so the
outcome no longer rests on a tie break. Remaining ties break by coverage, then by
the augmented-fingerprint order, which is size-neutral. Shortlex is retired as a
tie break and survives only as a test documenting its downward bias.

*Measured consequence on the first real collection of the smoke:* under indel
`consensus_ow` **recovers the source** (`fact_dist = 0`, `n_ties = 0`, certified
ratio 1.091 against the indel medoid's 1.152); under Levenshtein the same
collection returns a non-source at `fact_dist = 3` with `n_ties = 2`.

**Arms, all on every collection.** `consensus_ow` (indel median), and the three
pre-registered ablations `consensus_ow_lev` (metric only), `consensus_ow_coverage`
(first criterion only) and `consensus_fact` (fact space, H3.5).

**Certificates are comparable only within a metric.** The medoid arm
`isal_ow_indel` is the members' medoid under the *same* indel metric, so
`consensus_ow`'s `cost / LB` can be read against it. The `isal_ow_struct` medoid
row is the Levenshtein one and belongs to the cross-representation table; the two
ratios must never be read against each other.

**H3.6, pre-registered here.** The same asymmetry touches the median at small
`N`: dropping a fact that one member lacks saves that member an insertion (5–10
tokens) and costs the other `N − 1` a deletion (≈ 1 each), so at `N = 5` the word
median can prefer a sub-record and at `N = 15` it should not. H3.6 states that
`consensus_ow` exact recovery under `distance_first` increases with `N`, and that
the `N = 5` shortfall is a **sub-record** rather than an arbitrary object. Every
consensus row carries `sub_record_drop` so the claim is checkable.

---

## The local pilot

3 seeds, 20 sources per stratum, `N ∈ {5, 9}`, `t ∈ {1, 2}`, every arm; 48 units
over 8 worker processes on this workstation (i7-13700KF, CPU only). Command:

```
python -m experiments.tkde.rq3v2 --config experiments/tkde/configs/rq3v2.yaml \
    --pilot --out <root> --data-root <corpora> --shard i/8 --start-cutoff-s 5400
```

<!-- PILOT-TABLE-START -->
## The measured price, from campaign 2308421 itself

The local pilot is superseded: the campaign measured the same quantity at the
campaign's own scale, on the campaign's own hardware, over 358 units. Median
wall-clock **per unit** (each unit = 50 collections), taken from the tasks' own
`unit done` timestamps — not from the rows' `secs`, which both over- and
under-count (the exact-HGED judge runs outside the timer, and the three ball arms
each carry the one bundled enumeration).

| cell | median h/unit | status |
|---|---|---|
| wd50k66 star N5 t1 | 0.19 | clean |
| wd50k66 star N9 t1 | 0.55 | clean |
| wd50k66 star N5 t2 | 0.61 | clean |
| ndc_classes non-star N5 t1 | 0.76 | clean |
| wd50k66 non-star N5 t1 | 0.97 | clean |
| ndc_classes non-star N5 t2 | 1.90 | clean |
| wd50k66 star N15 t1 | 1.94 | clean |
| wd50k66 star N9 t2 | 2.24 | clean |
| ndc_classes non-star N9 t1 | 2.39 | clean |
| wd50k66 non-star N5 t2 | 2.42 | clean |
| wd50k66 non-star N9 t1 | 3.13 | clean |
| ndc_classes non-star N9 t2 | ≥ 6.42 | **censored at the 8 h wall** |
| ndc_classes non-star N15 t1 | ≥ 7.47 | **censored** |
| wd50k66 star N15 t2 | ≥ 7.49 | **censored** |
| wd50k66 non-star N9 t2 | ≥ 7.59 | **censored** |
| ndc_classes non-star N15 t2 | — | no unit ever completed |
| wd50k66 non-star N15 t1 | — | no unit ever completed |
| wd50k66 non-star N15 t2 | — | no unit ever completed |

Every censored median sits just under 27,600 s, which is the wall minus
teardown. Those four rows are not measurements of the work; they are
measurements of the wall.

**Where the time goes, and it is not the ball.** Median seconds per *collection*,
from the rows:

| | N = 5 | N = 9 | N = 15 |
|---|---|---|---|
| bundled ball (all three arms, one enumeration) | 33.4 | 85.7 | 127.0 |
| `consensus_fact` | 0.28 | 0.85 | 2.70 |
| all twelve medoids together | ~0.01 | ~0.01 | ~0.01 |

At `N = 15` a unit is ≥ 27,000 s over 50 collections, i.e. ≥ 540 s per
collection, of which the ball is 127 s. The remaining ~410 s is the **exact-HGED
judge**: about 20 calls per collection (12 medoids + 4 merges + 4 consensus) at
~20 s each, and 46,463 of 261,169 judged rows (17.8 %) already fall back to
`bipartite_ged_path` *after* burning the full 60 s budget. The cost grows with
`N` because the merges return larger wrong records at larger `N` —
`align_merge_iter` admits a constant once ≥ N/2 members carry an unmatched one of
the same type and pattern — and exact HGED on a large wrong record is
exponential.

**The declared restricted-ball fallback was therefore not applied.** It addresses
the ball, which is ~20 % of the cost at `N = 15`, and would have left those cells
well over the wall while looking like a remedy. The lever that matches the cause
is the oracle budget.

### The pricing error, stated plainly

The estimate in this document before the campaign — 1.6–3.3 h per *task* of
about five units — was wrong by one to two orders of magnitude on the heavy
cells. It was extrapolated from a two-collection smoke at `N = 5` on
`ndc_classes` (12.6 s per collection; the truth at that cell is 55 s) and `N = 9`
and `N = 15` were never measured at all: both pricing runs that would have
measured them were killed by later code changes of my own. The submission went
ahead on the reasoning that a deferral is safe, which it was — no row is wrong —
but the honest label at that moment was "unpriced", not a range.

---

## The recovery pass (2026-09-14)

| array | job | cells | units | tasks | wall | mem | tag |
|---|---|---|---|---|---|---|---|
| light | 2311518 | the 7 cells at ≤ 3.13 h/unit | 40 missing | 40, one unit each | 6 h | 32G | `ef0c58b4` (frozen) |
| empty | 2311519 | the 6 `ndc_classes` star cells | 79 missing | 1 | 1 h | 8G | `ef0c58b4` (frozen) |
| heavy | 2311520 | the 7 cells at ≥ 6.4 h/unit | all 189 (27 seeds × 7) | 189, one unit each | 6 h | 64G | `1efdcf54` (8 s oracle) |

**Why the heavy cells re-run all 27 seeds and not only the 171 missing.** The
oracle budget is a *measured* parameter, so a shorter budget is a different run
tag. A cell scored half under the 60 s budget and half under the 8 s one is two
instruments averaged together, which no footnote repairs, so the analyzer refuses
it (`check_one_tag_per_cell`). The 18 heavy-cell units the first pass did write
are superseded at analysis time with `--supersede-tag ef0c58b4`, which drops that
tag's rows **only** in cells another tag also measured.

**Why 8 s.** At `N = 15` a unit is 50 collections × ~20 judge calls = 1,000
calls. Every one timing out at 8 s is 8,000 s; the measured ball is 127 s × 50 =
6,350 s; merges and medoids are under 1 s each. Worst case ≈ 14,500 s = 4.0 h
against a 6 h wall.

**Why 64G on the heavy array.** The first campaign peaked at 25.9 GB
(`2308421_39`, a heavy task) against `--mem=32G`. A 6 GB margin on the cells that
grow fastest is not a margin. There was **no** OOM in 2308421 — that belonged to
another job in the wave.

**Coverage arithmetic, which closes exactly:** 358 written + 40 light + 79 empty
= 477 under the frozen tag, of which the 18 heavy-cell units are superseded →
459 = 17 cells × 27. Plus 189 = 7 cells × 27 under the heavy tag. Total 648.

Fill the tables, once all three arrays land, with

```
python -m experiments.tkde.analyze_rq3v2 --root <root> --supersede-tag ef0c58b4
```

⚠ **Do not run the hypothesis tests on partial coverage.** A partial table must
not be read.

---

## The local pilot (superseded)

Kept for the record only; the campaign's own price above replaces it. Fill it, if
anyone wants it, with

```
python -m experiments.tkde.analyze_rq3v2 \
    --root /media/.../results/IEEETKDE_ow/RQ3v2/pilot2 --run-tag <tag>
```

and paste the headline, capability, cost and edit-mix tables here.

⚠ **Pass `--run-tag`.** That directory holds **two** tags — `171dabce` from a run
made before the indel amendment and `edf96e8e` from the final code — because the
pilot was restarted when the configuration changed. They sit side by side without
either serving the other, which is the T-KBn guard working as designed, but an
analysis that pools them is pooling two experiments. The final tag is
`edf96e8e`; read the definitive one from `manifest.json`.

The campaign (job 2308421) does not wait on this table: the ball choice is
already recorded below with its arithmetic, and the worker writes per unit and
defers what it cannot start, so a slower-than-expected cell costs a deferral that
the resume pass collects, never a wrong row. The per-task `Elapsed` figures from
2308421 are in any case a better price than this pilot, being measured at the
campaign's own scale on the campaign's own hardware.

What the table must carry when filled: exact recovery and fact distance per
method per corpus × stratum × N × t; the censoring rate per arm; the consensus
arms' pool sizes and enumeration wall-clocks; and the realised edit mix.
<!-- PILOT-TABLE-END -->

### The ball choice, and the arithmetic behind it

Gate G3.1(b2) measured the two families at **identical** coverage — 1.000 each on
the mixed model at `t = 1` — so this is a cost decision and nothing else, which
is how the orchestrator framed it.

Measured cost of one `consensus_ow` call, six families per cell, on this
workstation:

| cell | ball | recovery | sub-record share of misses | median s | classes |
|---|---|---|---|---|---|
| wd50k66 non-star N5 t1 | restricted a≤3/d≤2 | 0.167 | 0.500 | 1.8 | 2,028 |
| wd50k66 non-star N5 t1 | indel r=2 | 0.333 | 0.333 | 14.4 | 14,153 |
| wd50k66 non-star N9 t1 | restricted a≤3/d≤2 | 0.333 | 0.167 | 9.3 | 7,886 |

(Measured before the scoring loop was hoisted and before the metric amendment,
so the times are upper bounds and the recoveries are the Levenshtein ones. Both
were re-measured afterwards; the re-priced table replaces this one.)

The full indel ball buys about twice the recovery for about eight times the cost
at `N = 5`, and the orchestrator's rule prefers it if the partition fits in
≤ 24 h.

**The partition.** 486 non-empty units × 50 sources = 24,300 collections. At the
measured whole-collection cost — the Picasso smoke ran 2 collections at `N = 5`
in 57 s, i.e. ≈ 28 s each including every medoid, merge and consensus arm — and
allowing for the larger balls at `N = 9` and `N = 15`, the campaign is on the
order of 200–400 CPU-hours. Split into 122 array tasks of 4 shards each, that is
1.6–3.3 h per task: above SCBI's two-hour floor and well inside the 8 h wall.
With a throttle of 64 the campaign runs in two rounds, so the makespan is
3–7 h — comfortably inside the 24 h the rule allows.

**Choice recorded: the full indel ball at `r = 2`.** The restricted family stays
as the declared fallback if a re-price at `N = 15` moves the per-collection cost
by an order of magnitude.

---

## Deviations from the brief, and why

| # | Deviation | Reason |
|---|---|---|
| D1 | `ndc_classes` star cells emit one `cell_empty` row instead of collections | G0 measured the stratum empty; H3.4 is scoped to `wd50k66` |
| D2 | `sources_per_cell = 50`, not 100 | 50 per stratum gives `wd50k66` the specified 100 per corpus per seed across its two strata; `ndc_classes` reaches 50 because it has one stratum |
| D3 | Primary objective is the generalized median, not v1's coverage order | Orchestrator ruling on the a-priori grounds above; coverage runs as a named ablation on every collection |
| D4 | `consensus_fact` added as a pre-registered arm (H3.5) | Orchestrator ruling: a reviewer will ask whether word space costs us the task against the fact-space computation, so we ask first |
| D5 | Picasso deploys to `~/repos/IsalHG-rq3v2` on HOME, shared env `isalhg-tkde`, `--no-build` | FSCRATCH measured at its file quota with grace expired, so it is read-only; nothing under `src/` changes, so a private env would rebuild an identical extension |

---

## Reproduction

| What | Command |
|---|---|
| G0 | `python -m experiments.tkde.rq3v2 --config experiments/tkde/configs/rq3v2.yaml --census` |
| Smoke | `python -m experiments.tkde.rq3v2 --config … --smoke --out <root>` |
| Pilot | `python -m experiments.tkde.rq3v2 --config … --pilot --out <root> --shard i/8` |
| Analysis | `python -m experiments.tkde.analyze_rq3v2 --root <root>` |
| Tests | `python -m pytest tests/experiments_tkde/test_rq3v2.py -q` |
| Picasso | `bash slurm/tkde/rq3v2_sync.sh` then, on the login node, `bash slurm/tkde/rq3v2_launcher.sh --smoke` and `… rq3v2_launcher.sh` |

---

## The harvest (2026-10-04, agent `harvest`)

*Appended; nothing above is edited. The numbers are in
`../foundation/rq3v2_facts.md` §6–§12, which is the verdict of record.*

**Coverage closed short.** 490 row files (477 `ef0c58b4`, 13 `1efdcf54`). The
light (2311518, 40/40) and empty (2311519) arrays completed; the heavy array
2311520 wrote 13 of 189 units (11 COMPLETED, 178 TIMEOUT, one finished unit
lost because it ended 17 s after the time-limit cancel and its copy-back never
ran). After superseding `ef0c58b4` where `1efdcf54` also measured: **11 cells
complete, 4 partial, 3 absent, 6 empty by construction.** All seven heavy cells
are incomplete and none is tested; the "every N" of H3.1 is therefore not
established, and nothing is claimed at non-star `N = 15` or at non-star
`N = 9, t = 2`.

**The re-price above was wrong about the cause, and so was "Why 8 s".** The
heavy pass ran with the judge at 8 s and still exceeded 6 h, because the cost
is the ball: on the 13 written units `consensus_ow` is 99.1–99.7 % of the wall
and the judge with every other untimed step is 2–7 s per unit; 145 judge
timeouts in 6,252 started collections. The 127 s per collection at `N = 15`
that both the re-price and the 8 s arithmetic rested on was a median pooled over
the `N = 15` units 2308421 had written, 27 of 35 of them from the one easy cell
(`wd50k66` star `N = 15, t = 1`, 96.7 s); on the heavy cells the ball is a median
278–340 s per collection with a tail to the 1,800 s method budget. And the
"17.8 % fall back after the full 60 s" is the `n > 10` ceiling: rows with a
source above `n = 10` are judged bipartite 100 % of the time, rows at or below it
2.5 %. In 2311520 the judge was not the lever; the ball at `t = 2` and non-star
`N = 15` is. How much of 2308421's time the 60 s judge took cannot be read from
the rows (it runs outside the timers) and was not re-derived from that job's
logs; what is established is that the fallback share once read as timeouts is
the ceiling. Nothing was resubmitted.

**The analyzer needed three repairs before it could be run.** It crashed on the
real tree (pandas 3 keeps a missing `judge_timeout_s` a float under
`astype(str)`); it had no coverage gate, so a hypothesis test would have pooled
partial cells; and its H3.2 family omitted the like-for-like indel medoid. A
fourth change reads H3.6 within corpus × stratum × t series, because under
partial coverage the pooled per-`N` mean changes composition with `N`. Each has a
failing-first test in `tests/experiments_tkde/test_rq3v2_analysis.py`; the rule
for H3.6 was fixed before any per-`N` number was read.

**Verdicts in one line each** (complete cells only): H3.1 supported on the tested
cells, not testable at `N = 15` and non-star `N = 9, t = 2`; H3.2 supported
against 11 medoids (`hypercot` unscored); H3.3 not supported (0.385 vs oracle
0.921); H3.4 not supported (no tie: 0.491 vs 0.032, with the `pattern_vote`
construction unaudited); H3.5 not supported (0.433 vs `consensus_fact` 0.984,
which is also cheaper); H3.6 monotone in 4/4 series but most small-`N` misses
are not sub-records, so not supported as stated.
