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
*Pending: filled from `analyze_rq3v2.py` on the pilot rows once the run
completes. The table carries exact recovery and fact distance per method per
corpus × stratum × N × t, the censoring rate per arm, the two consensus arms'
pool sizes and wall-clocks, and the priced full-run cost.*
<!-- PILOT-TABLE-END -->

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
