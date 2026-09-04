# Supplementary material — the collections

*Self-contained data section for the article (target: the supplementary
material of the TKDE submission; the main text carries one table). It
documents every collection the experiments run on: source, derivation into
knowledge bases, sizes, arity, envelope yield, structural repetition,
canonicalization timing, and the ground truth it carries. Written 2026-09-03
from the probes in `foundation/probes_2026-09.md`; numbers are the probe
numbers and are re-measured by the experiment pipeline. The storyline that
consumes these collections is `prose.md` §7.*

**Selection rule.** Few collections, each carrying one research question,
each with a ground truth that is either real or obtained by controlled
intervention on real members. Fully synthetic data appears in exactly one
place, the operating-envelope sweep, because no real collection spans
sizes systematically. The synthetic planted families and size-controlled
strata of the previous iteration are retired.

**Why the two remaining interventions are kept, stated for the reviewer.**
(i) Outlier ground truth does not exist in the wild: an unsupervised outlier
list has no label to score against, and every anomaly-detection benchmark
scores injected anomalies on real substrates. We inject fact-level errors of
stated type and budget into real knowledge bases and score their recovery.
(ii) An operating envelope is a property of the algorithm over sizes and
arities; real collections cover a corner of that space. Random knowledge
bases over a grid of `(m, k, |Σ|)` are the only way to draw the frontier, and
the real collections are placed on the same figure as points.

---

## S1. Entity knowledge bases of a hyper-relational knowledge graph — WD50K(66)

**Source.** WD50K and its qualifier-enriched subsets WD50K(33), WD50K(66),
WD50K(100), released with StarE (Galkin, Trivedi, Maheshwari, Usbeck &
Lehmann, EMNLP 2020, DOI 10.18653/v1/2020.emnlp-main.596); statement files
`train/valid/test.txt`, one statement per line `s, r, o, (q_r, q_v)*`. On
disk: `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/data/wd50k_66/` (md5
recorded in `foundation/probes_2026-09.md` §7). WD50K(66) is the subset in
which 66 % of statements carry at least one qualifier.

**Derivation.** One knowledge base per entity `e`: the set of statements
with `e` as subject. Reading E1: vertices are the entities and values that
occur in those statements (anonymized — the isomorphism-invariant comparison
is the point), one hyperedge per statement over `{subject, object, qualifier
values}`, labelled by the main relation; qualifier relations are not encoded
(folding them into the edge label multiplies the label alphabet by 3.3× and
changes the isomorphism census by 0–3 %, measured). Entities with fewer than
three statements are dropped. The anchored variant E1⊤ (an anchor constant
joined to every vertex by a `dom` edge) is used wherever the language-scale
operations of Proposition 4 are run.

**Sizes** (all 4,554 entity knowledge bases; min / p25 / median / p75 / p90 /
max): constants `n` 3 / 6 / 9 / 15 / 27 / 377; hyperedges `m` 2 / 3 / 5 / 9 /
18 / 303; maximum arity 2 / 3 / 3 / 4 / 5 / 67. Arity histogram of the 42,472
hyperedges: 2 → 12,488; 3 → 19,375; 4 → 9,085; 5 → 859; 6 → 303; 7 → 252;
8 → 26; 9 → 11; ≥ 10 → 60 (13 of arity 1 are self-statements). 70.6 % of
hyperedges have arity ≥ 3; 81.8 % of knowledge bases contain at least one.

**Envelope yield** (`n ≤ 24` and `m ≤ 110`, the measured canonicalization
frontier): 3,994 knowledge bases (87.7 %), of which 3,167 are genuinely
n-ary (maximum arity ≥ 3); 14 dropped for a statement of arity above the
alphabet cap. Median in-envelope `n = 8`, `m = 5`; 54.7 % of in-envelope
hyperedges have arity ≥ 3.

**Structural repetition** (exact isomorphism census, labels honoured):
3,686 classes among 3,994 (0.92 per knowledge base; 3,518 singletons; the ten
largest classes hold 2.1 %). With labels stripped: 1,317 classes (the ten
largest hold 37.6 %) — star shapes of a given size. Labelled fingerprints are
therefore near-unique, which is the regime in which exact identity matters
(RQ2, RQ4) and which the census reports as such.

**Canonicalization** (tie-complete `w*_c`, C++ engine, labelled, 30 s budget,
stratified by `n`): median 0.0003 s / 0.004 s / 0.004 s / 0.57 s / 2.44 s in
the buckets `≤ 8` / 9–12 / 13–16 / 17–20 / 21–24; time-outs 0 / 0 / 0 / 1 / 4
of 8; median word length 4–21 tokens. Overall 13 % time-outs, concentrated in
the two largest buckets and reported as yield per bucket. Cost tracks label
degeneracy (many spokes with the same relation), not size.

**Class labels.** Wikidata `instance of` (P31) fetched for every in-envelope
entity (100 % coverage; `data/wd50k/types/p31_types.tsv`). One label per
entity: the most frequent type over the population, ties by identifier
order. Fourteen classes with at least twenty members cover 87.5 %: human
1,830, film 1,092, big city 171, television series 75, animated film 49,
sovereign state 47, public educational institution of the United States 41,
U.S. state 36, business 34, private not-for-profit educational institution
30, type of disease 25, city 24, musical group 22, modern language 20. The
imbalance (human and film are 73 %) is stated; clustering scores report
per-class support, and a super-class coarsening is the pre-agreed fallback.

**Serves.** RQ1 (the addressing comparison), RQ2 (prerequisite consequences on
a real collection), RQ4 (corruption substrate; rare-class census), RQ5
(k-medoids and hierarchy against types), RQ6 (generative model and the
decodability figure), RQ7 (yield row).

**Purity control — WD50K(100).** Same derivation on the subset in which
every statement carries a qualifier: 1,847 in-envelope knowledge bases, 99.8 %
of hyperedges of arity ≥ 3, median `n = 11`, sub-second canonicalization
below 17 constants; its type labels collapse to eight usable classes (human
925, film 572), so it serves only as the "this is not a graph problem"
control in the supplementary tables. **Rejected after probing:** JF17K
(qualifier roles are a deterministic function of the main relation, and 33 %
time-outs from label degeneracy), WikiPeople (88 % plain triples; the
densest stars), WD50K itself as the primary (13.6 % of statements with
qualifiers; kept only as the source of the pooled type vocabulary).

## S2. Time series of interaction knowledge bases — ARB temporal datasets

**Source.** The Cornell higher-order interaction collection (Benson, Abebe,
Schaub, Jadbabaie & Kleinberg, PNAS 2018), timestamped simplex lists
(`-nverts.txt`, `-simplices.txt`, `-times.txt`). All 17 temporal datasets
are on disk under `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/data/arb_benson/temporal/`.

**Derivation.** For a node `v` and a time window `t` (natural unit chosen per
dataset so that the median knowledge base has 3–30 facts), the knowledge
base `S_t(v)` = the distinct group interactions containing `v` whose
timestamp falls in `t`, read as a labelled hypergraph on `v` and its
co-members (node labels where the dataset provides them). Consecutive
windows of the same node are **real variants**: because node identities
persist across windows, the fact-level change `Δ_t(v) = |S_t(v) △ S_{t+1}(v)|`
is exact ground truth that no isomorphism computation touches; the methods
see only the anonymized members.

**Selection.** Twelve temporal datasets were probed (`foundation/probes_2026-09.md`
§6) and ranked by (i) the number of in-envelope knowledge bases with one-edit
consecutive variants, (ii) the presence of arity ≥ 3, (iii) usable labels,
(iv) canonicalization time. The *encodable* envelope adds two walls to the
size frontier: at least three facts (a one-fact knowledge base carries no
structure) and maximum arity ≤ 10 (the compiled alphabet cap, which removes
4–54 % of in-envelope members on the high-arity corpora). One dataset is
kept as the variant-series collection and one as its control:

**NDC-classes, quarterly windows — the variant-series collection.** The FDA
National Drug Code directory read as a hypergraph: nodes are pharmacologic
classes, each simplex is a marketed drug product as the set of classes it
belongs to, timestamped by first-marketing date; 49,724 products over 1,088
classes, arity 1–24. The knowledge base of class `c` in quarter `t` is the
set of distinct co-formulation facts (products containing `c`) marketed in
that quarter; consecutive quarters of the same class are real variants of
`c`'s co-formulation pattern. In the encodable envelope: **1,432 knowledge
bases, 555 consecutive pairs, of which 85 identical (Δ = 0), 120 one-edit
(Δ = 1, 21.6 %), 134 two-edit, 191 within 3–5 and 25 beyond 5**; 45 classes
with a run of ≥ 3 consecutive encodable quarters, 20 with ≥ 5, 14 classes
with ≥ 3 one-edit pairs — the only corpus in the family with a one-edit rate
above 3 %. Facts are genuinely n-ary: 66.9 % of in-envelope hyperedges have
arity ≥ 3 (4,548 of arity 3, 3,787 of 4, 3,960 of 5, 6,393 of 6–10).
Structural repetition is real: 1,500 sampled in-envelope members fall into
213 unlabelled isomorphism classes (7 per class) where the tag and contact
corpora give 1.6–3.4. *Labels.* The node names are identities and are **not**
used as labels (identity labels would defeat the isomorphism-invariant
comparison); the unary predicate is the FDA pharmacologic-class *type*
carried as a suffix of the name — `[epc]` established pharmacologic class
(514 classes), `[moa]` mechanism of action (278), `[pe]` physiologic effect
(113), and 256 names without a suffix (a fourth, "untyped" value) — so
constants stay anonymous and typed. *Canonicalization.* With
identities as labels every instance completes in 0.003–0.75 s (a 10× speed-up
over unlabelled, the regime the probe timed); with anonymous constants the
small members (≤ 10 facts) canonicalize in a median 2.0 s with no time-outs
and the 11–30-fact bucket times out in 3 of 4 at 30 s — the class-type
labelling sits between the two and is measured by the experiment pipeline,
with yield reported per bucket. Caveat stated in the paper: the corpus-wide
median is one product per class-quarter, so the usable collection is the
1,432 encodable members, not the 22,892 in-envelope class-quarters.

**NDC-substances, quarterly windows — the control.** Same directory with
nodes = active substances (9,906 substances, 5,311 products): 2,222 encodable
members, 1,106 pairs, 35 one-edit (3.2 %), 37 substances with runs ≥ 5,
48.7 % of hyperedges of arity ≥ 3, and the only corpus where every timing
instance finished in both the labelled and the unlabelled mode (medians
0.0006–0.008 s and 0.0005–0.26 s). It is the corpus on which the
unlabelled-constant regime can be run in full, and it is reported in the
supplementary tables only.

**Not kept, with the number that decides it.** contact-primary-school at
15-minute windows has the volume (9,159 encodable members, 217 nodes with
runs ≥ 5) and the only categorical vocabulary (11 classes, join verified
exact against the labeled release), but contacts churn almost completely
between windows: 53 one-edit pairs (0.8 %), 82.6 % of pairs beyond five
edits. email-Enron (2 one-edit pairs), contact-high-school (2), email-Eu (20;
0.9 %), DAWN (1 of 1,886), tags-math-sx and tags-ask-ubuntu (0 of 12,626 and
19,619), threads-ask-ubuntu (0), coauth-MAG-History (6), congress-bills (62
encodable pairs in total, 54 % of members above the arity cap). Retired on
measurement: the induced (Qin-style) ego-networks of the contact datasets —
dense, not large (median 37 constants carrying 454 facts), 26 usable members
at the safe density, every one a singleton class.

**The two regimes inside this collection, and what they cost RQ3.** Of the 555
consecutive encodable pairs, **140 (25.2 %) preserve the constant set and 415
(74.8 %) change it** — a class gains or loses member classes between quarters,
median 6 constants moved. The distinction is not cosmetic: it is exactly the
boundary of the adopted encoding (`foundation/probes_2026-09.md` §9), which
gives a one-token distance for a one-fact difference in the first regime and
loses to the pointer alphabet in the second. Restricted to preserving runs the
corpus collapses to **15 drug classes with ≥ 3 consecutive preserving quarters
and 2 with ≥ 5** (longest run 5), so the natural series alone cannot carry the
consensus experiment. Plan of record: RQ3 is run on constant-preserving
ladders built over *real* members of this collection (injected fact edits,
constant set held fixed), with the 555 natural pairs reported beside them as
the harder, unmodified case; both are stated, neither is hidden.

**Serves.** RQ3 (the representative record: the exact fact-level distance from
the returned representative to the held-out next quarter; the identity-using
majority merge as the reference), RQ1 (the addressing comparison on a real
variant series — this is the collection where "similar knowledge bases" has a
ground-truth meaning, and where the two regimes are separable), RQ2 (false
merges on real members), RQ7 (yield rows).

## S3. Controlled corruptions of real members (RQ4)

Real members of S1 and S2 inside the envelope; one corruption per member of
a stated type and budget `b ∈ {1, 2}`: *spurious fact* (a fact over existing
constants that is not in the member), *missing fact*, *wrong argument* (one
argument of a fact replaced by another constant); and the *iso-twin*
construction (a degree- and WL-colouring-preserving swap applied to a real
member, yielding a non-isomorphic twin that every statistic of the member
matches). Corrupted members are re-anonymized. Ground truth is the injection
label; the evaluation is the area under the ROC curve of the outlier score,
per corruption type and representation. Rates and budgets are reported with
every table.

## S4. Operating-envelope sweep (RQ7)

Random connected labelled knowledge bases over a grid of fact counts
`m ∈ {10, 20, 40, 80, 120, 160}`, maximum arity `k ∈ {2, 3, 4, 5}`, edge
vocabularies `|Σ_E| ∈ {1, 3, 10}` and vertex vocabularies `|Σ_V| ∈ {1, 4}`,
27 seeds per cell, anchored (E1⊤). Reported: median and p90 wall-clock of
`w*_c`, time-out fraction at 60 s, and word length; the real collections of
S1–S2 are placed on the same figure by their `(m, k, |Σ|)`. Prior envelope
facts that this sweep re-measures: the frontier is the fact count, not the
constant count (an ego-network with 25 constants and 150 facts canonicalizes
in 0.06 s, one with 14 constants and 114 facts times out), and labels are the
tie-breaker (labelled milliseconds where the unlabelled form fails at
thirteen constants).

## S5. The addressing schemes not adopted

The main text carries one encoding: fact tokens addressed by global canonical
rank, selected on measured local stability (RQ1). The **four** it displaced are
documented here with their full measurements, because together they are what
makes the frontier proposition credible: pointer addressing inherited from the
earlier work; local `(refinement colour, index)` addressing; and the two
locally-keyed schemes, `(type + incident predicate/arity multiset, index)` and
its coarse control `(type + degree, index)`. The supporting locality
experiments belong here too — one fact edit moves 92–98 % of depth-3
refinement colours (36–52 % at depth 1) while the canonical rank order
survives 68–85 % of edits, and no edit among 21,528 left a content-determined
address map intact, against a 22–57 % zero-cost fraction for ranks:
single-edit response per edit kind, correlation with the true fact-level
difference on the variant series, empirical completeness and iso-invariance,
token counts, wall-clock, and the correlation of each with the
canonical-labelling certificate distance. Reporting them is what makes the
adopted scheme a measured choice rather than an assertion, and it is where the
earlier alphabet's clustering and nearest-neighbour numbers now live: they
describe the pointer representation, which this article replaces.

## S6. Retired collections (kept in the record, not in the paper)

Planted swap families and the size-controlled Stratum C corpus of the
previous iteration (synthetic; superseded by S1–S3); the contact induced
ego-networks (too dense); the HIC IMDB atlas (corpus-level arity 110); JF17K
and WikiPeople (above). Their measurements remain in
`foundation/measured_facts.md` and `foundation/probes_2026-09.md`.
