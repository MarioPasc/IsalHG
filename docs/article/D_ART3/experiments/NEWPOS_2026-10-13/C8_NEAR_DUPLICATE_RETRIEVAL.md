# C8 — Near-neighbour retrieval of structural near-duplicates

**Status:** POSITIVE, candidate for the main text of the TKDE article.
**Date:** 2026-10-13. **Author:** `[IsalHG-Article-Iterator]`, reviewed twice by
`[IsalHG-Fable-Review]` (design, then attack). **Branch:**
`feature/newpos-experiments`. **Record of how it was found:** `LOG.md` in this
directory, §P-C8 onwards. Nothing here supersedes a frozen result; it is new
evidence.

---

## 1. The result in one paragraph

Under anonymization, the versions and near-copies of a KB record can only be
found by structure. We ask, for every representation's distance, whether a
record's nearest neighbour is truly one (or two) single-fact edits away. The
ground truth is exact and does not depend on any representation. When the
records differ by a **pendant** edit — a statement or qualifier added or
removed together with its value; 56–90 % of the one-edit pairs per collection —
the ordered-walk word `w°` ranks the true neighbour first far more often than
every competitor on all four collections, at radius 1 and at radius 2. MRR is
0.45–0.78 for `w°` against at most 0.53 for the best competitor, with
Holm-corrected p < 1e-32 everywhere. When they differ by an **interior** edit,
the nauty certificate, the canonical-rank fact list and the bipartite edit path
rank better, exactly as H2 predicts. Pooled over all edits, `w°` has the top
MRR on all four collections, but it ties the bipartite edit path on both NDC
series, and the pre-registered pooled-AP criterion failed on NDC-substances.

## 2. Why it is a language result (mechanism)

Two properties are needed at once, and only an Isal word has both:

- **Exact at zero (Theorem C).** Non-isomorphic look-alikes never sit at
  distance 0. The WL histogram, NetLSD, HPD, the bipartite assignment value and
  the floors have mass false zeros on these collections (H1: up to 212,179
  pairs). Their nearest-neighbour lists drown in ties, so the true neighbour is
  rarely first.
- **Pendant locality by name-freedom (Prop. C.6).** The word never names a
  constant, so adding or removing a statement with its own value changes one or
  two instructions. The certificate renames constants by canonical position and
  moves 11–13 rows per pendant edit (H2), which is as far as an unrelated record
  of similar size.

The certificate has the first property but not the second. The vector
representations have neither. That is why C8 measures the language, not only a
complete invariant: the certificate is the same family's identity and loses by
an order of magnitude on WD50K.

## 3. Task, ground truth, protocol

**Collections.** All four frozen TKDE collections:
- `wd50k66`: 3,988 members.
- `wd50k100`: 1,837 members.
- `ndc_classes`: 1,381 members.
- `ndc_substances`: 1,745 members.

The draft calls `wd50k100` and `ndc_substances` "controls" (exactness and
envelope only). Using them here requires the setup section to say so.

**Ground truth (exact, representation-free).** For every member K, enumerate its
down-neighbours:
- delete one fact; or
- remove one constant from one fact of arity ≥ 2.

Then drop the constants left in no fact (`compact`) and key the result by the
**nauty certificate** of the coloured incidence graph. A non-isomorphic pair is
a **radius-1 positive** iff one member is isomorphic to a down-neighbour of the
other. The four single-fact edits of §3 of the paper are covered, because up-edits
are the reverse of down-edits. Keying by `w°` instead gives the identical
partition and positive set (asserted on NDC-classes and WD50K(66)).

Two filters are lossless:
- Disconnected down-neighbours cannot match any member, since every member is
  connected.
- A constant removal that duplicates a fact equals a fact deletion, which is
  already enumerated.

A pair is **pendant** when the edit changes the constant inventory, otherwise
**interior** (the paper's definition).

**Radius-2 positives.** Non-isomorphic pairs not within radius 1 that are
reached either by two down-edits, or through a shared down-neighbour (one
down-edit on each side). The second route covers relabelling or moving one
fact. A pair is pendant when some path has two pendant steps. Pairs that need
two insertions and have no common down-neighbour are not enumerated; they count
as negatives for every arm alike.

| collection | non-iso pairs | radius-1 positives (pendant / interior) | radius-2 positives (pendant) | one-edit pairs that are versions or same-type |
|---|---|---|---|---|
| NDC-classes | 949,712 | 5,994 (4,451 / 1,543) | 17,887 (14,672) | 41 % same drug class |
| NDC-substances | 1,516,294 | 30,748 (17,162 / 13,586) | 90,692 (37,552) | 6 % same substance |
| WD50K(66) | 7,949,355 | 2,721 (2,437 / 284) | 19,649 (16,278) | 76 % same Wikidata type |
| WD50K(100) | 1,684,525 | 6,993 (5,215 / 1,778) | 25,708 (14,390) | 68 % same Wikidata type |

**Scoring (no tuning anywhere; distances are the cached campaign matrices).**
- **Queries:** every member with ≥ 1 positive partner.
- **Ranking:** a query ranks all non-isomorphic other members by the
  representation's distance.
- **Metrics:** the reciprocal rank of its nearest positive (MRR), hit@1, hit@10
  and the query's AP; ties are resolved by expectation (fair to the floors,
  which tie most). Global pairwise AP is also reported, with tie blocks entered
  whole.
- **Stratified retrieval:** a query's positives are its pendant (or interior)
  partners; partners of the other kind are removed from its candidate list. At
  radius 2, radius-1 partners are removed.
- **Statistics:** 95 % CIs from a bootstrap over queries, clustered by drug
  class on NDC (2,000 replicates). Each competitor is compared against `w°`
  with a one-sided paired Wilcoxon signed-rank test on per-query reciprocal
  ranks, Holm-corrected across the ten competitors, with the rank-biserial
  correlation as effect size.
- **Checks:** there are no censored cells in any matrix. The star fraction of
  the queries vs the corpus is 0.021 / 0.030, 0.240 / 0.158, 0.648 / 0.534 and
  0.159 / 0.148 (mild star skew on two collections).

**Competitors (all ten of the paper's capability table that have matrices).**
- nauty certificate, bytes and rows;
- canonical-rank fact list;
- WL histogram;
- NetLSD;
- HPD;
- bipartite GED, assignment value and edit-path cost;
- degree-sequence and size floors.

HyperCOT has no matrix (its environment never ran). The search form `w*_c` is
an ablation inside our family (§5).

## 4. Results

### 4.1 Radius 1, stratified (the headline)

MRR of the nearest true neighbour, `w°` [95 % CI] vs the runner-up; p is the
largest Holm-corrected p of `w°` against any competitor.

| collection | pendant: `w°` | pendant: runner-up | max p_Holm | interior: `w°` | interior: best |
|---|---|---|---|---|---|
| NDC-classes | **0.449** [0.392, 0.503] | bipartite path 0.263 | 2.6e-33 | 0.133 | fact list **0.742** |
| NDC-substances | **0.726** [0.690, 0.760] | degree-seq 0.349 | 2.4e-95 | 0.209 | bipartite path **0.742** |
| WD50K(66) | **0.552** [0.534, 0.572] | bipartite path 0.065 | 1.9e-183 | 0.049 | fact list **0.390** |
| WD50K(100) | **0.691** [0.666, 0.714] | bipartite path 0.175 | 4.0e-129 | 0.145 | fact list **0.532** |

Pendant stratum, certificate (bytes / rows): 0.007 / 0.018, 0.017 / 0.062,
0.005 / 0.008, 0.020 / 0.023. Rank-biserial of `w°` vs every competitor on the
pendant stratum: ≥ +0.47 (NDC-classes), ≥ +0.77, ≥ +0.97, ≥ +0.93.

### 4.2 Radius 2

| collection | all: `w°` | all: runner-up (p_Holm) | pendant: `w°` | pendant: runner-up (p_Holm) |
|---|---|---|---|---|
| NDC-classes | **0.664** | bipartite path 0.583 (1.3e-8) | **0.689** | bipartite path 0.509 (1.5e-33) |
| NDC-substances | **0.745** | bipartite path 0.713 (0.64, **tie**) | **0.666** | degree-seq 0.486 (1.7e-42) |
| WD50K(66) | **0.762** | fact list 0.535 (9.0e-130) | **0.778** | fact list 0.531 (8.4e-143) |
| WD50K(100) | **0.715** | bipartite path 0.499 (2.9e-56) | **0.696** | bipartite path 0.475 (3.1e-58) |

The ranking generalises beyond the radius where an exact enumeration is the
trivial detector (§6, objection 1).

### 4.3 Radius 1, pooled (table only, not the headline sentence)

| collection | `w°` MRR | runner-up MRR (p_Holm) | `w°` AP | best AP |
|---|---|---|---|---|
| NDC-classes | **0.416** | bipartite path 0.413 (0.19, tie) | **0.168** | fact list 0.150 |
| NDC-substances | **0.717** | bipartite path 0.701 (1.0, tie) | 0.430 | **degree-seq 0.459** |
| WD50K(66) | **0.541** | fact list 0.101 (2e-155) | **0.139** | HPD 0.003 |
| WD50K(100) | **0.685** | fact list 0.318 (3e-70) | **0.181** | fact list 0.089 |

The pre-registered pooled hypothesis H-ND (highest MRR **and** AP on every
collection) **failed** on NDC-substances AP, where 44 % of the positives are
interior. That failure is printed.

### 4.4 Figure

`/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/NEWPOS_2026-10-13/neardup/fig_neardup_retrieval.{pdf,png}`
(script `scripts/newpos/fig_neardup.py`). It is a double-column dot plot with
three panels — (a) radius 1, pendant; (b) radius 1, interior; (c) radius 2, all.
There is one row per representation and one marker per collection, each with
its 95 % CI, and `w°` sits in the shaded top row. Panel (b) shows the loss
openly; the condition is in the figure, not only in the text. Palette: the
validated categorical slots 1–4 (CVD ΔE 9.1); marker shape is the secondary
encoding.

## 5. Ablation inside the family: the search form `w*_c`

On the members `w*_c` canonicalises (`--restrict-to-arm wstar_orbit`), the
MRR at radius 1, pooled, is:
- **NDC-classes:** `w*_c` 0.525 vs `w°` 0.410. `w*_c` beats the bipartite edit
  path (0.410), which ties `w°` there. This is consistent with `w*_c`'s better
  insertion locality (RQ1).
- **WD50K(66):** `w°` 0.541 vs `w*_c` 0.475.

A reviewer will ask why the headline program is the weaker one on NDC. The
answer is coverage: `w*_c` censors 70 NDC-classes members at 60 s, and `w°`
censors none (H1/H3).

## 6. Reviewer objections and the answers

1. *"Radius-1 pairs are found exactly by enumeration plus any complete
   invariant."* True. That is how the ground truth is built, and the text must
   say so. The experiment measures what a *distance* does for similarity
   search: whether a record's nearest neighbour is its true near-duplicate.
   That matters because exact enumeration grows as `deg^r` with the radius.
   Radius 2 (§4.2) shows the ranking generalises.
2. *"The pooled score is a mixture of pendant and interior shares."* Hence the
   stratified headline, with the shares printed per collection (§3 table).
3. *"Your edit set favours you."* The four edits are the paper's §3 edits and
   include the interior ones, where `w°` loses (§4.1, Fig. panel b). Radius 2
   adds relabelling and moving a fact through the shared-down-neighbour route.
4. *"The certificate is a strawman (Levenshtein over a certificate is your
   construction)."* The fact list and the bipartite edit path are in every row
   and are the credible comparators. They win the interior stratum, so they are
   not weak baselines.
5. *"Queries are selected toward stars."* Only mildly (§3 checks); WD50K(100)
   and NDC-classes are 85–97 % relational and give the same pendant result.
6. *"Cost."* `w°` builds the full WD50K(66) matrix in 1.39 s. The bipartite
   edit path takes 10.6 min and is not a metric (asymmetric on 44–58 % of
   pairs; H1).
7. *"Ground truth keyed by your own canonical form."* No — it is keyed by the
   nauty certificate, and the `w°` key gives the identical truth.

## 7. Where it goes in the paper (suggestions for the writer)

- **Placement.** It is the task-level form of H2. Option A: a new subsection
  "H6: Near-duplicate retrieval" after H2, with the figure (double column) and
  the §4.1 table in compact form. Option B: replace H2's absolute-movement table
  `tab_locality` with the figure, keeping H2's numbers in one sentence. Option
  B saves space and gives H2 the all-competitor comparison it lacks (the
  capability table's locality column is "n/a" for WL/NetLSD/HPD/bipartite; it
  can now carry the pendant MRR).
- **Pages.** The draft is at the 14-page limit. The PI suggested moving
  literature to the supplement. Option B costs about 0.3 pages net: one
  double-column figure (≈ 0.35 page) minus `tab_locality` (≈ 0.15), plus about
  150 words.
- **Setup changes.** Name `wd50k100` and `ndc_substances` as evaluation
  collections for this experiment.
- **Draft sentence (scope in the same sentence, per the framing rules):** "On
  pairs that differ by one pendant edit, the word ranks the true neighbour first
  in 0.41–0.69 of queries across the four collections, against at most 0.26 for
  any other representation (Holm-corrected p < 10⁻³²); on interior edits the
  certificate, the fact list and the bipartite edit path rank better, and
  pooled over all edits the bipartite edit path ties the word on both NDC
  series." (hit@1, pendant stratum: `w°` 0.408 / 0.690 / 0.501 / 0.642; best
  competitor 0.202 / 0.264 / 0.026 / 0.085.)

## 8. Reproduce

```bash
PY=~/.conda/envs/isalhg/bin/python   # repo root, branch feature/newpos-experiments
SP=<scratch dir for matrices missing from the cache>
$PY scripts/newpos/build_ow_matrix.py --collection ndc_substances --out $SP
for a in nauty_cert_rows netlsd hpd_jsd bipartite_ged_assign bipartite_ged_path; do
  $PY scripts/newpos/build_ow_matrix.py --collection wd50k100 --arm $a --out $SP; done
OUT=/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/NEWPOS_2026-10-13/neardup
for c in ndc_classes ndc_substances wd50k66 wd50k100; do
  $PY scripts/newpos/neardup.py    --collection $c --key cert --extra-matrix-dir $SP --out $OUT
  $PY scripts/newpos/neardup_r2.py --collection $c --workers 10 --extra-matrix-dir $SP --out $OUT; done
$PY scripts/newpos/neardup.py --collection ndc_classes --key both --extra-matrix-dir $SP --out $OUT   # truth-key check
$PY scripts/newpos/neardup.py --collection ndc_classes --restrict-to-arm wstar_orbit --extra-matrix-dir $SP --out $OUT
$PY scripts/newpos/fig_neardup.py
$PY scripts/newpos/tab_neardup.py      # writes tab_neardup.tex (table*, generated from the JSONs)
```

The LaTeX table `D/results/NEWPOS_2026-10-13/neardup/tab_neardup.tex` is
generated from the JSONs, so no number is copied by hand. It uses the draft's
macros (`\WDK`, `\WDKc`, `\NDCc`, `\NDCs`, `\nauty`, `\IsalHG`, `\wo`). Each
collection has three columns: P (pendant, radius 1), I (interior, radius 1),
2 (radius 2, all). Bold marks the best per column; a dagger marks a competitor
that is not significantly below `w°`.

Wall-clock on the workstation: radius 1, 6–32 s per collection; radius 2,
25–48 s with 8–10 processes. Deterministic; the bootstrap seed is 0.

## 9. Open items before it enters the paper

- Mirror the four locally built WD50K(100) matrices and the NDC-substances
  `w°` matrix into `D/results/IEEETKDE/matrices/` with manifests (they live in
  the session scratchpad; regenerate with §8 if lost).
- Unit tests for `neardup.py` (down-neighbour enumeration, AP with ties,
  expected rank) — the probes are untested scripts.
- Decide placement (§7) with the writing plan and the PI.
- Optional: a version-only stratum on NDC (same-class pairs only, 41 % /
  6 % of positives) as the "versions" exhibit.
