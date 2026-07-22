# IsalHG metric-space article — a reader's walkthrough

**Purpose.** A plain-language pass through the finished article for an
unfamiliar reader: which studies are included, why, what each measures, how,
and the outcomes — followed by a publishability assessment. Written from the
v3 scope (`docs/article/PROPOSAL.md`, characterize → exploit). Numbers are the
measured values as of the S1–S5 closure (2026-07-21); primary corpus is the
planted-family corpus at `N = 240` unless noted.

This is author-facing prep, not article prose and not a ledger task.

---

## Part I — The premise (everything hangs off this)

**"A hypergraph is a word."**

IsalHG has a small virtual machine — a circular doubly-linked list (CDLL) of
vertices plus `k` pointers — and a five-token instruction alphabet `Σ_HG`:

- `V` — add a hyperedge over some existing + some new vertices,
- `C` — add a hyperedge over existing vertices,
- `P` / `N` — move a pointer forward / back one step,
- `W` — no-op (padding / alphabet closure).

Feed the machine a string and it builds a hypergraph (**S2H**). Take a
hypergraph and an encoder (**H2S**) walks it back into a string. The alphabet is
*closed*: every well-formed string decodes to a valid hypergraph; S2H never
rejects.

The move that makes this a research object rather than a serialization format:
for each hypergraph you can compute a **canonical** string `w*_c(H)` — the
shortlex-minimum over an isomorphism-invariant set of starting vertices, with a
*tie-complete* branching search so it is uniquely determined by the isomorphism
class alone. Two hypergraphs are isomorphic **iff** their canonical strings
(plus a seed-label prefix `F(H) = (ℓ_V(seed), w*_c(H))`) are equal. That is
**Theorem A**.

With that, one line does all the work:

```
d_I(H, H') = d_Lev( w*_c(H), w*_c(H') )
```

Raw Levenshtein distance on the canonical strings. Because `w*_c` is a
*complete* invariant, `d_I` satisfies identity of indiscernibles
(`d_I = 0 ⇔ isomorphic`); symmetry and the triangle inequality come free from
Levenshtein. So **`d_I` is a genuine metric on isomorphism classes of connected
hypergraphs** (Corollary A). Hypergraphs are now embedded, exactly and without
loss, into a metric space.

The rest of the paper answers one question: *now that hypergraphs live in a
metric space, what does that space look like, and what can you do with it?* The
spine is **foundation → compactness → geometry → usefulness → discussion**.

---

## Part II — The five studies, in reading order

### 1. Foundation — "it's really a metric" (Theorem A + Corollary A)

**What / why.** The non-negotiable core. If `w*_c` were not complete, `d_I`
would only be a pseudometric and every downstream application would be built on
sand.

**How.** Two halves:
- **Soundness** (`w*_c` equal ⇒ isomorphic): proved unconditionally from the
  round-trip property, for *every* encoder variant.
- **Completeness** (isomorphic ⇒ `w*_c` equal): the genuinely-new-for-hypergraphs
  part. Holds **only for the tie-complete encoder** (`"canonical"`). The cheaper
  greedy encoders are *provably incomplete* — a pinned `n = 4` counterexample
  (primal `K4`, constant structural tuples) where the greedy string depends on
  edge-insertion order. So the paper must, and does, use the expensive
  tie-complete form.

**Outcome.** Backed by a written proof
(`proofs/theorem_a_completeness.{tex,pdf}`) plus empirical pins: 150/150
shuffle+relabel invariance, biconditional agreement with pynauty under
Hypothesis fuzzing, and frozen regression pins on Fano, STS(9), the cyclic C13
orbit, the `n = 4` counterexample, and both true STS(13) systems.

**Subtlety to know.** `w*_c` is *frozen* as the **unpruned** tie-complete
lex-min. You may not "clean it up" with a smarter tie-break — that changes the
canonical form (lex-min over a subset ≠ lex-min over the full set). The only
permitted speed-up is stabiliser-orbit pruning (Prop 6.0). This is why the
encoder is worst-case exponential on highly symmetric designs — owned, not
hidden.

### 2. Compactness — "it's a *short* word" (the bits study)

**What / why.** Substantiates "a hypergraph is a *compact* word." Small but
rhetorically important: it is where the representation is introduced and shown
economical vs the natural incidence-list baseline.

**How.** A uniform fixed-width code (deliberately *not* Shannon entropy, *not*
gzip — the estimator is the sibling-graph-paper's reviewer-tested one):

```
B_IsalHG(w) = |w| · log2 |Σ_HG(k)|
```

compared against an incidence-list construction model (per edge: a type bit +
arity·⌈log2 n⌉ address bits, plus vertex-insertion bits). Compression ratio
`r = B_comp / B_IsalHG`; `r > 1` favours IsalHG. One-sided Wilcoxon
signed-rank on `r − 1`.

**Outcome (N = 320 pooled planted).** `r > 1` on **320/320**; pooled median
`r = 1.441`; Wilcoxon `p = 1.6 × 10⁻⁵⁴`; OLS slope `β = 0.749 < 1` (systematic
compression). Sits at the low edge of the sibling's `[1.45, 1.89]` band —
expected, hypergraphs pack more structure per vertex.

**War story.** An early tokenizer bug (`split(";")` fragmenting bracketed
`V[...]` tokens, ~2× overcount) had *reversed* this to `r = 0.51`. Caught and
regression-pinned. The bits result is fragile to tokenization and rests on one
estimator choice.

### 3. Geometry — "what does the space look like?" (Pillar 1, the characterization)

The paper's central *contribution* in the authors' framing: no
hypergraph-dissimilarity space has been characterized this way. Six measured
invariants, under a strict **no-orphan-geometry rule** — every invariant is
measured because a specific downstream application or competitor contrast needs
it. Primary corpus: planted families, `N = 240`, 20 families.

| Invariant | What it measures | IsalHG (N=240) | Licenses |
|---|---|---|---|
| Non-Euclidean mass `ν` | `Σ_{λ<0}|λ| / Σ|λ|` of the double-centred Gram (Schoenberg) | `ν = 0.250`, not PSD | metric methods (k-medoids) over centroid methods |
| Intrinsic dimension `D̂` | CV on held-out dissimilarities (Gower placement) | `D̂ = 26` (CV plateau N≥240; Horn floor 12 → bracket **[12, 26]**) | MDS target dim; competitor axis |
| Distortion | Kruskal stress-1 at matched `D`, Shepard | stress `= 0.062` | qualifies every MDS map |
| Concentration + hubness | diam/median; skewness of `N_k` (Radovanović 2010) | diam/med 1.75, hub skew 1.280 | kNN precondition (A3) |
| Local sensitivity `s(e)` | `d_I(H, H⊕e)` per single edit | IQR 2–8 tokens, no heavy tail | neighbourhood methods; nauty contrast |
| Ladder response | `d_I` vs known accumulated edit budget `t` | ~80% steps monotone; increment 3.2→11.7 | A4 scoring; smoothness evidence |

**Why the numbers matter.** IsalHG lands in a *moderately-high-dimensional,
non-Euclidean, low-distortion, mildly-hubby* space. The competitors contrast
sharply: WL histogram and HPD are Euclidean by construction (`ν = 0`) but their
`D̂` is **censored** (rides to the search cap — no finite estimate), and WL is
*pathologically* hub-prone (skew 4.586). NetLSD is low-dimensional (`D̂ = 5`)
but strongly concentrated (diam/med 5.03). This table is a per-representation
geometric fingerprint that the applications then confirm.

**Honesty flag inside the section.** The local-sensitivity study made a
three-regime prediction (from the stability analysis) that **partially failed**:
heavy tails predicted on the "incoherent-tie" designs (cyclic C13, GQ(2,2)) but
compact profiles measured under single arity-≤3 edits — 2 of 7 regimes
falsified. Reported as a partial falsification rather than buried.

### 4. Usefulness — "what can you do with it?" (Pillar 2, four applications)

All four run off the *same* pairwise matrix `D_I` (competitors: their own
`D_rep`); each cites the geometric property that licenses it.

- **A1 — Similarity map (MDS).** Classical + SMACOF. Dual-purpose: an
  application *and* how `ν`, `D̂`, distortion are produced. Licensed by Bourgain
  (`O(log N)` distortion guaranteed) and Khot–Naor (some residual distortion
  unavoidable for string-edit metrics). Outcome: IsalHG map at stress 0.062,
  genuinely non-Euclidean; vector competitors Euclidean but high/censored-dim.

- **A2 — Clustering (k-medoids + dendrogram).** Licensed by `ν` (PAM needs only
  a metric, no coordinates — which is *why* k-means is unavailable here).
  Outcome (N=240): **ARI** — IsalHG 0.102, HPD 0.120, NetLSD 0.051, nauty
  0.018, WL ≈ 0; **NMI** — IsalHG 0.407, HPD 0.445. **IsalHG a close second to
  HPD; nauty and WL essentially fail.** Recovery modest across the board (hard
  20-class task — stated honestly).

- **A3 — Classification (kNN, precomputed metric).** Licensed by the G1 hubness
  profile, measured *first* so the result is a confirmed prediction. Outcome
  (N=240): WL hubness 4.586 → **AUC collapses to chance, 0.49** (predicted).
  Among benign-hubness reps: **HPD 0.83 > IsalHG 0.73 > NetLSD 0.66 > nauty
  0.61**. Prediction lands decisively at the extreme; residual ordering follows
  measured geometry.

- **A4 — Hypergraph-to-hypergraph shortest path (the capability differentiator).**
  Shortest accumulated-`d_I` path through a pool of 44 hypergraphs. Scored
  HGED-free: monotonicity vs edit budget, path recovery, decodability demo.
  Outcome: monotonicity `= 1.00` all reps; exact recovery near-null (0.00
  IsalHG/WL/NetLSD, 0.33 HPD) — reported as a *feature* (the geodesic routes
  through same-budget alternatives, proving `d_I` is not an edit-distance
  proxy). **Categorical result: only IsalHG exhibits the intermediate
  hypergraphs** — three intermediate strings decode via S2H to valid
  hypergraphs. WL collapses to a 2-node hop; NetLSD/HPD have no decoder; nauty
  cannot navigate at all (avalanche-everywhere geometry). No competitor can do
  this.

**Honest summary of Pillar 2.** On pure task metrics (A2, A3) **IsalHG is a
strong second, not the winner — HPD-JSD leads.** IsalHG's differentiators are
(i) the only *complete/exact* representation, (ii) the only *decodable* one
(A4), (iii) a single metric drives all four tasks. That is the paper's real
value proposition — defensible, but not "we beat everyone on every metric," and
the paper does not claim that.

**Real-data cross-check (HIC IMDB genre, censored).** The intended real anchor
**failed a feasibility gate** (NO-GO): real IMDB hypergraphs have corpus-level
arity `k = 110`, far beyond the arity cap, and near-symmetric instances make
`w*_c` blow up. The feasible subset censors by structural symmetry (which
correlates with labels), so it cannot be the primary anchor. Fallback: a
**censored secondary exhibit** on the two "clean" datasets (91–92% yield) —
genre is near-unclusterable from structure for *every* representation (honest
negative), and the kNN hubness story reproduces on real data (WL hubness
4.5–7.4 trails; IsalHG/NetLSD lead at AUC ≈ 0.67). Application claims are
therefore explicitly **synthetic-scale claims, cross-checked on real data where
computable.**

### 5. Discussion — the relation to edit distance (retired capstone, compressed)

Deliberately *last* and *small*: it is the paper's weakest axis, and leading
with it invites the reviewer to read it as "a mediocre HGED-approximation
paper." The logic, in order:

1. **Length lemma:** `|w*_c| ≤ m(1+kn)` (string linear in incidence mass).
2. **Envelope proposition:** `d_I ≤ m(1+kn)·HGED` — *unconditional*, presented
   honestly as an envelope (its whole content is the length lemma), **not** a
   stability bound.
3. **Impossibility (the key move):** a two-sided bi-Lipschitz relation
   `c·HGED ≤ d_I ≤ C·HGED` is **provably out of reach**. The lower direction
   fails generically for *any* complete canonical-form / WL-type invariant
   (FSW-GNN LoG 2025; Chen et al. 2023). The upper direction fails through two
   named, measured mechanisms: **drift** (unit-step pointer runs cost `Θ(n)` in
   adversarial layouts) and **avalanche** (near-symmetric inputs — the price
   *any* complete invariant pays, because deterministic symmetry-breaking is
   discontinuous exactly where objects are nearly symmetric). Framed as a
   *frontier*: stability-by-construction (WL, spectra, transport) is bought by
   *giving up completeness*; IsalHG sits on the completeness side.
4. **One figure (E1′):** Spearman `ρ` between `d_I` and *exact* HGED on a small
   connected mini-corpus, ours only. Outcome: **`ρ = 0.622`, `N = 6,921`
   pairs**, per-cell 0.48–0.81, and `HGED = 0 ⇔ d_I = 0` confirmed. Offered as
   honest characterization, not a proxy claim.
5. **Consequence:** because no bound can certify usefulness, usefulness was
   established *directly* (Pillars 1–2). The discussion closes the loop on the
   paper's own methodology.

**E1′ reader note.** The corpus is 11 of 12 planned blocks — the 12th (`n = 10`,
second seed) blew past 100 GB / 18 h on the exact-HGED oracle and was excluded
*whole-block* (per-pair exclusion would bias `ρ`). Documented as the measured
practical ceiling of exact HGED (NP-hard, barely computable at `n = 10`).

---

## Part III — The cast of competitors

| Competitor | Representation | Role | Fatal limitation |
|---|---|---|---|
| **IsalHG** (ours) | canonical string, Levenshtein | — | slow on near-symmetric / high-arity instances |
| **Hypergraph-WL histogram** | count vector, L1 | standard baseline | no decoder; pathological hubness → kNN dies |
| **NetLSD** | spectral heat-trace, L2 | full member | no decoder; not complete; concentrated |
| **HyperCOT** | optimal-transport coupling | paper+code member | `O(n³)`/pair — small corpora only |
| **HPD** (portrait divergence) | hyperedge-path tensor, JSD | paper+code member | no decoder; JSD not a metric; index error on ~⅓ of real instances |
| **nauty-Levi canonical + edit** | canonical string, edit | **contrast, not "beaten"** | avalanche everywhere (IQR 10–20); cannot navigate paths |

nauty is the sharpest device: it is *also* a complete canonical form, so it
isolates what IsalHG's specific encoder design buys — a *navigable* geometry
(IQR 2–8 vs nauty 10–20) that a hash-like canonical form does not have.

---

## Part IV — Is it 100% publishable? Straight assessment

**Short answer.** A publishable, genuinely solid paper — but not "submit as-is."
The honest ceiling is a good applied venue like *Information Sciences* (the
target). It is *not* a Q1-flagship "we beat SOTA" result and must not be framed
as one.

### Genuinely strong (the load-bearing case)

1. **The foundation is airtight.** Theorem A + Corollary A is a real, proved
   theorem with a written proof, empirical pins, and a correctly-handled
   subtlety (greedy incomplete; only tie-complete works).
2. **The characterize → exploit narrative is disciplined.** The
   no-orphan-geometry rule is a strong organizing principle most
   representation papers lack. Every geometry number is consumed.
3. **The A4 decodability differentiator is real and unique.** "Only our
   representation can produce the intermediate hypergraphs along a path" is a
   clean, categorical, non-cherry-pickable claim. This is the defensible
   headline.
4. **Intellectual honesty is a feature.** Retired proxy claim, partial
   falsification, HIC NO-GO, tokenizer bug caught — plus the impossibility
   argument that turns "no bound" into a *principled* completeness–stability
   frontier statement.

### Holes a reviewer *will* find (fix before submission)

1. **No significance tests / CIs on the headline task-metric comparisons.** A
   top gap for a data-science journal. Bits Wilcoxon and E1′ `ρ` have stats;
   **A1/A2/A3 (ARI, NMI, AUC, stress) have none.** "HPD 0.83 > IsalHG 0.73" is
   currently unfalsifiable. Add bootstrap CIs + paired tests over multiple corpus
   seeds. → `STATS_PASS_PLAN.md`.
2. **Near-zero variance in synthesis parameters (co-equal top gap).** Every
   headline number (ν = 0.250, D̂ = 26, stress 0.062, all A2/A3 scores) is
   measured at a **single point**: `n = 10, k = 3`, fixed density. The N = 60 →
   480 sweep varies the *number of hypergraphs*, not the per-hypergraph
   structure — it sharpens the D̂ estimate, it does not establish
   generalization. There is no sweep over n, density, or arity; and **arity ≤ 3
   almost everywhere** while the thesis advertises k up to 10 (no measured result
   at k = 5..10; all design fixtures 3-uniform). The planted "families" are also
   *random seeds*, not known designs, which weakens what ARI-vs-planted-labels
   means. Significance testing quantifies uncertainty at the point; a
   **parameter-variation sweep** is what licenses "generalizable." Both are
   needed. → `DATA_RIGOR.md`.
4. **On pure task metrics you lose to HPD** (A2, A3). The honest answer
   (completeness + decodability + one-metric-drives-all) is fine, but the
   framing must be airtight that usefulness = "licensed, competitive, uniquely
   capable," not "best-in-class clustering/kNN." Promote a **capability matrix**
   to a main figure — that is where you win. → `CAPABILITY_MATRIX.md`.
5. **The real-data anchor is weak.** One domain (IMDB via HIC), 2 clean + 4
   heavily-censored datasets, and the clean result is a *negative* (genre
   near-unclusterable). Real data does appear in the geometry table (ν, D̂ on
   HIC), not only in applications — but it is too thin for a strong applied
   claim. Add ≥1 real corpus within the arity cap where `w*_c` *is* computable.
   → `REAL_DATA_CORPUS.md`.
6. **`D̂` censoring must be labeled everywhere.** WL/HPD/nauty report `D̂ ≥ 40`
   "censored at cap" — a legitimate contrast, but every cell needs the caveat or
   it reads as a bug in *your* pipeline.
7. **The 2/7 partial falsification needs a clean landing** — explained and
   bounded (single arity-≤3 edits under-sample the deep-tie mechanism; closing
   the arity gap in `DATA_RIGOR.md` also resolves this), not left as an
   unresolved crack.
8. **Complexity honesty.** `w*_c` is worst-case exponential (GQ(2,2): ~4.5×10⁵
   recursion nodes for a 276-token string; the HIC blow-up). State it plainly
   with the runtime table (nauty is also exponential worst-case — fine, but do
   not let it surface only in an appendix).
9. **Method/framing items beyond data and stats** — a naive baseline for the
   whole comparison, the structural-vs-label-aware status of `d_I` (resolved as
   a small formal Remark, not prose), practitioner motivation for A1–A4, and
   the reproducibility artifact. → `APPROACH_RIGOR.md`.

### Best way to arrange everything

- **Lead with the theorem and the picture, close with the caveat.** Keep the
  spine (foundation → compactness → geometry → usefulness → discussion). Do
  **not** move the HGED discussion earlier — burying it is correct.
- **Headline: "a complete, decodable metric representation of hypergraphs, with
  a characterized geometry"** — not "a better clustering method." The uniqueness
  claims (complete + decodable) are what no competitor has; competitive task
  metrics are enough *given* the uniqueness.
- **Close the two data gaps first** — the significance pass (`STATS_PASS_PLAN.md`)
  *and* the parameter-variation sweep over n / density / arity
  (`DATA_RIGOR.md`). Run the sweep under multiple seeds so each sweep point
  carries a CI and both gaps close together. This is the difference between a
  point-estimate paper and a generalizable one.
- **Promote the capability matrix to a main figure**, with the A4 decoded-
  intermediates figure beside it (the matrix claims decodable; the figure shows
  it).
- **State the two big limitations up front in the discussion:**
  worst-case-exponential `w*_c`, and synthetic-scale claims with a real-data
  cross-check. Owning these disarms the reviewer.

**Bottom line.** Science sound, foundation proved, narrative unusually
disciplined, decodability/completeness a real unique contribution. **Publishable
at *Information Sciences*, but not yet** — the current evidence is a
*single-point* study (n = 10, k = 3, random-seed families, uncertainty
unquantified). The two critical pre-writing additions are (i) significance
testing on the application comparisons and (ii) a parameter-variation sweep over
n / density / arity, ideally with the families re-seeded from known designs so
arity > 3 and interpretable classes come for free. With those, plus the
capability-matrix reframing, a broadened real-data anchor, and the two
limitations (exponential `w*_c`; scale) stated up front, this is a credible
accept. Sold correctly (complete + decodable + characterized geometry,
competitive on tasks, uniquely capable on A4) and backed by a sweep rather than
a point, it is a clean, honest contribution that will survive review.
