# Stability after T-TBb: value assessment and reformulation space

**Status:** ANALYSIS (2026-07-17, session with the PI email of 2026-07-17 on
arithmetic-coded pointer displacements). Companion to `stability.md` (normative)
and the proof volume
`/media/mpascual/Sandisk2TB/research/ISAL/isalhg/proofs/stability/`. Nothing
here changes the frozen `w*_c` (D-TA2). Two ledger tasks were filed from this
analysis: `T-TBc` (displacement-token distance substrate) and `T-M4a`
(entropy-coded information-content estimator).

**Housekeeping flag.** The T-TBb closure (commit `e6b0af7`, 2026-07-14: ledger
move, `scripts/probe_pointer_runs.py`, `scripts/tb3_coherence_criterion.py`,
`tests/unit/core/test_no_w_tokens.py`) is **not merged** into
`perf/canonical-complete-orbit-pruning`; on this branch `T-TBb.md` still reads
OPEN. Reconcile before the next orchestrator run.

---

## 1. What Theorem B can and cannot be (the "proxy" question)

`d_I ≤ C·HGED` alone never made `d_I` a *proxy* for HGED. A proxy in the
algorithmic sense is a **two-sided** (bi-Lipschitz) equivalence
`c·HGED ≤ d_I ≤ C·HGED`, and:

- The **lower** direction is provably out of reach for canonical-form and
  WL-type representations (RELATED_WORK: FSW-GNN LoG 2025; Chen et al. 2023) —
  non-isomorphic pairs can have vanishing representation distance at fixed
  structural distance. This was already the T-TB scope README's position.
- Even a bi-Lipschitz bound would **not** contradict the NP-hardness of HGED
  (Zeng et al., VLDB 2009, for GED; hypergraph case at least as hard): computing
  `w*_c` is worst-case exponential (tie-complete branching; the complete-binary-
  tree blow-up measured at T-TBb), so no polynomial-time approximation of HGED
  would follow. There was never a complexity miracle at stake — and therefore
  also no complexity-theoretic reason to expect failure. The failure mechanisms
  found (drift, avalanche) are *encoder geometry*, not complexity theory.
- **B-worst is an envelope, not a stability statement.** Its proof is
  `d_Lev(s,t) ≤ max(|s|,|t|)` plus `HGED ≥ 1`; its entire content is the length
  lemma `|w*_c| ≤ m(1+kn)`. The paper must not present it as a Lipschitz result.

The claim the paper can honestly defend: `d_I` is a **complete, computable
metric whose distortion relative to HGED is mechanistically explained,
regime-characterized, and per-instance measurable**. That is strictly more than
the sibling paper (empirical ρ only, no bound, no mechanism) and more than any
competitor representation offers (nauty/bliss canonical forms have *no*
non-trivial stable regime; hash-like avalanche is their generic behaviour).

## 2. Value inventory if the bound never improves

With B-cond conditional on (i)–(v), (v) refuted generically (orphaned
introducer, `R(e)=Θ(n)` at Qin cost 1), average-(iv) failing asymptotically
(`E[T_span] ≤ M(H)/n`, measured `M/n ≈ n^0.75` at fixed density), and B-avg
demoted, the theorem still delivers:

1. **The falsifiable Δ-prediction** (ρ decays with density, window term
   `1+Δ`), already matched by the sibling's data trend. This is the article's
   theory↔empirics bridge and survives unchanged — drift is Δ-independent to
   first order (pointer_run_amortization.tex, Rem. consequence).
2. **Attribution instrumentation.** T-M5a logs `R(e)`, `T_span(e)`, `M(H)`,
   first-incoherent-tie depth per edit. The correlation scatter is then
   *decomposable* into window + drift + avalanche — reviewers get an error
   budget, not a correlation coefficient.
3. **Finite-size validity where it matters.** The exact-HGED corpus (§2 of
   PROPOSAL) is confined to small `n` by the oracle anyway; at the measured
   scales (`n ≤ 48`) drift sits below the `kΔ` budget. The regime where the
   Lipschitz bound is quantitatively meaningful and the regime where HGED
   ground truth exists largely coincide.
4. **The competitive contrast.** "IsalHG has a characterized stable regime;
   canonical-form baselines have none" is defensible, novel, and empirically
   testable (compare `s(e)` histograms of `d_I` vs nauty-canonical distances).
5. **Honest negative results.** The orphaned-introducer mechanism, the
   crossing-averaging identity, and the STS(9) strict-sufficiency obstruction
   are publishable analysis in their own right.

**Caveat to carry:** the `M/n ~ n^0.75` growth law is a power fit over a 4×
range (`n = 12..48`); over that range a polylog fit is barely distinguishable.
The asymptotic-failure claim for average-(iv) should be re-probed at larger `n`
once orbit pruning lands (this branch). Logged inside T-TBc's empirics.

## 3. Three dials: where each failure lives

Decompose the pipeline `d_I = d_Lev ∘ (T × T) ∘ (w*_c × w*_c)` where `T` is
the *presentation* (how VM operations are spelled as tokens; currently unary
`P/N` runs). Each failure mode attaches to exactly one dial:

| Failure | Mechanism | Dial | Fixable? |
|---|---|---|---|
| Drift `R(e)` | unary runs pay CDLL distance; orphaned introducer | presentation `T` | **Yes** — displacement tokens (T-TBc) |
| Drift `T_span(e)` | ±1 per arc crossing an inserted slot | presentation `T` (count is geometric) | Count invariant under recoding; cost per crossing stays 1. Bounded by `max_u X(u)` (measured ≈ Δ; conj. `O(k(Δ+log m))`) |
| Avalanche (sources 1–5) | tie/seed discontinuity of the lex-min | canonicalization `w*_c` | **No** at fixed completeness (see §6); tamed by regime characterization |
| Block-permutation blindness | Levenshtein charges Θ(block) for reordered intact blocks | metric `d_Lev` | Partially — block-move edit distance (§5) |

## 4. The PI's displacement-coding idea, reinterpreted (→ T-TBc, T-M4a)

**Framing decision (2026-07-17, see §7).** Displacement transcoding is an
**ablation on the raw metric, not its replacement**. The raw instruction-string
`d_I` stays the article's primary distance (premise integrity + the fixed
decisions); the transcoder is computed alongside it on the same pinned corpus so
we can (a) prove the drift carries no structural signal and (b) hold promotion in
reserve as an evidence-gated PI decision. The math below is what T-TBc builds and
measures; it is not a commitment to change the substrate.

The PI email (2026-07-17) proposes replacing pointer-movement instructions with
a coded integer tuple of per-pointer displacements — arithmetic coding with
corpus-trained frequencies, or a sign bit + Gray-coded magnitude — to shorten
strings. Motivation is compression; the mechanism is exactly the cure for the
layout-locality failure, because the current alphabet encodes displacement
magnitudes in **unary** (one token per CDLL slot), which is the sole reason
`R(e)` and the `n`-factor in `|w*_c| ≤ m(1+kn)` exist.

**Definition (transcoding).** `T` maps each emission's movement block (one
unidirectional arc per pointer) to displacement tokens `D(l, δ_l)`, `δ_l ∈
[-n, n]`, preserving the V/C token and the seed-label prefix. `T` is injective
on encoder outputs (blocks are delimited by V/C tokens; the rendering order of
per-pointer sub-runs is deterministic), and is applied **after**
canonicalization — the frozen `w*_c` is untouched, so D-TA2 is respected and
Theorem A transfers: `T(w*_c(H₁)) = T(w*_c(H₂)) ⇔ w*_c(H₁) = w*_c(H₂) ⇔ H₁ ≅
H₂`. Define `d_I' := d_Lev` over transcoded token sequences.

**What it fixes (to be proved at T-TBc):**
- `R'(e) ≤ k(1+Δ)` **unconditionally**: a window re-encoding changes at most
  the `≤ k` displacement tokens of each of the `≤ 1+Δ` affected emissions.
  The orphaned introducer collapses from `Θ(n)` inserted tokens to one
  token-value change — Prop. orphan of `pointer_run_amortization.tex` ceases
  to be a counterexample. Hypothesis (v) becomes a lemma.
- Length envelope `|T(w*_c)| ≤ m(1+k)`: **B-worst′** reads `d_I' ≤
  (1+k)·max(m,m')·HGED` — the previously *retracted* `(2k+1)max(m,m')`-shaped
  constant becomes legitimate, because retraction was forced precisely by unary
  unboundedness.
- B-cond′ needs only (i)–(iii) plus span-boundedness; and per-edit `T_span` is
  bounded by the crossing peak `max_u X(u)`, measured ≈ Δ and conjectured
  `O(k(Δ+log m))` (conj:peak). Hypothesis count: five → three combinatorial +
  one quantitative with an exact per-instance certificate (`M(H)/n`,
  `max_u X(u)` from the probe).
- Avalanche ceiling drops from `m + M(H)` to `m(1+k)` tokens.

**What it does not fix:** the `T_span` *count* (a crossing arc's token changes
value either way — cost 1 per crossing under both codings), and the avalanche
(orthogonal to pointer presentation). Average-(iv)'s `M/n` growth persists as
the bound on mean insertion drift.

**Falsifiable side-prediction:** `ρ(HGED, d_I') ≥ ρ(HGED, d_I)` on the same
pinned corpus — unary run-lengths are layout accidents uncorrelated with
structural distance, so removing them should raise signal-to-noise. If ρ
*drops*, run lengths carried structural signal and the ablation says so.

**Topology (the PI's own caveat) resolves per axis:**
- *Metric axis:* unit-cost substitution between `D(l,δ)` and `D(l,δ')` erases
  magnitude topology — which is a *feature* for stability (drift immunity) and
  plausibly harmless for HGED-fidelity (magnitudes are layout accidents). If
  magnitude sensitivity is wanted, use a weighted substitution cost
  `c(D(l,δ), D(l,δ')) = f(|δ-δ'|)` with `f` a bounded concave metric-compatible
  gauge (weighted edit distance is a metric iff the token-space cost is a
  metric on `Σ' ∪ {ε}`); the Gray-coded bitstring is exactly the bit-level
  version of this (adjacent magnitudes differ in one bit), at the price of a
  `log n` token-length factor that inflates avalanche costs.
- *Compression axis:* arithmetic coding with static corpus-trained frequencies
  is ideal — **but only there**. An AC bitstream must never be the metric
  substrate: one changed symbol re-scales every subsequent coding interval, so
  Levenshtein between AC outputs is avalanche-dominated *at the code level* —
  it would reintroduce, in the code, the exact instability Theorem B fights in
  the encoder. Codec for §3 bits (T-M4a); tokens for `d_I'` (T-TBc).

## 5. Other reformulations considered

- **Normalized Levenshtein.** Yujian & Bo (IEEE TPAMI 29(6), 2007,
  10.1109/TPAMI.2007.1078) give a normalization that *is* a metric. Already
  demoted to an ablation by OQ4; unchanged.
- **Edit distance with block moves** (Cormode & Muthukrishnan, ACM TALG 3(1),
  2007, 10.1145/1186810.1186812). Charges `O(1)` for relocating an intact
  block. Post-avalanche strings are often near-permutations of intact emission
  blocks (especially after transcoding, when per-edge emissions are
  `O(k)`-token units), so a block-move distance could absorb much of the
  avalanche cost that Levenshtein maximally penalizes. Still a metric
  (identity/symmetry/triangle hold), still complete over `w*_c`. Cost: exact
  computation is NP-hard; `O(log n log* n)`-approx embeddable into `L1` in
  near-linear time (edit-sensitive parsing). Future-work candidate, not
  primary.
- **Structure-first tour (encoder variant).** The current cascade is
  displacement-cost-first, i.e. the emission *order* itself is
  layout-dependent — a nearest-first tour, and nearest-first tours are
  classically unstable under perturbation. A structure-first key (η before
  displacement) would make emission order layout-independent; under unary
  pointers this was unaffordable (string length explodes), but under
  displacement tokens every gather costs `O(k)` tokens regardless of distance,
  so the length penalty largely vanishes. This defines a *different* canonical
  form (a new tie-complete lex-min over a permuted key cascade): D-TA2 forbids
  calling it `w*_c`, Theorem A would need its own (likely mechanical) instance
  of the tie-complete argument, and the PI would have to sanction a second
  frozen form. High potential, high procedural cost — recorded here, not
  tasked.

## 6. What remains impossible: the completeness–stability tension

The avalanche is not an implementation defect. Any *complete* invariant must
separate every non-isomorphic pair, and any deterministic symmetry-breaking
(lex-min over seeds/branches) is discontinuous exactly where the object is
nearly symmetric: an edit that flips which branch is minimal moves the output
to a different orbit representative wholesale. The known non-lower-Lipschitz
results (§1) are one face of this; the incoherent-tie avalanche is another.
Representations that are Lipschitz-stable by construction (WL vectors, spectral
embeddings, HyperCOT couplings) buy it by *giving up completeness*. IsalHG's
position — completeness held, stability characterized by regime with
per-instance diagnostics — is a genuine point on the frontier, and after T-TBc
the unstable surface would shrink to the avalanche alone, which is exactly the
part every complete invariant must own.

## 7. Recommended way forward (2026-07-17) — the article spine

Under the fixed decisions (Levenshtein as the metric; `w*_c` the tie-complete
canonical algorithm; the **raw** instruction string as the object; connected
domain D-CONN1), the cleanest strong proposal is a **repositioning**, not a new
construction. Four moves; the last one is a verdict on Ezequiel's proposals.

### 7.1 Move the headline from the bound to the geometry (→ T-TBd, D-ART1)

`theoretical/README.md` calls Theorem B "★ core novelty"; `stability.md` §2 calls
it "the core contribution." That aims the paper's reception at its weakest point —
T-TBb proved the clean Lipschitz bound is conditional on five hypotheses, two of
which (run-locality (v), average span-boundedness (iv)) fail generically. Lead
instead with the object the metric **is**:

> **Thesis.** `w*_c` embeds hypergraphs into the discrete metric space
> `(Σ_HG*, d_Lev)`. We prove the embedding is injective on isomorphism classes
> (Theorem A ⇒ `d_I` is a metric), **characterize the geometry it induces** — its
> faithfulness to hypergraph structure, its intrinsic dimension, its Euclidean
> distortion — and show standard metric pipelines (MDS, k-medoids, kNN,
> dendrograms, shortest path) operate in it. Faithfulness is not asserted but
> **decomposed**: each `ρ(d_I, HGED)` carries an error budget attributing its
> scatter to the window, drift, and avalanche terms the theory predicts.

Theorem B keeps its role as the **engine** that explains and predicts the
geometry (the Δ-decay of ρ, the two named deviation mechanisms). That is still
strictly more than the sibling delivered — IsalGraph stated locality as "empirical
claim, no bound." The differentiator is restated honestly as *"a
regime-characterized bound with named mechanisms and per-instance diagnostics —
a decomposable error model for the correlation,"* not *"a clean Lipschitz
theorem."* The paper stops being judged on a bound whose failure would sink it.

### 7.2 Keep the raw instruction-string metric primary; do not transcode by default (→ T-TBc)

Three reasons the raw metric stays primary, and one procedure that still honors
the displacement idea:

1. **Premise integrity.** The fixed decision is *Levenshtein over instruction
   strings*. Transcoded displacement tokens are a derived encoding; making them
   primary turns the pitch "a hypergraph is a word" into "a hypergraph is an
   arithmetic-coded derivative of a word." The elegance is the selling point.
2. **The dominant deviation is the avalanche, which transcoding does not fix.**
   The T-TBb probe (density 1.5, n=32) measured median `s(e) ≈ 0.6–0.75·|w*_c|`,
   attributed to avalanche, not drift. Transcoding removes the drift term `R(e)`
   and shortens strings (`m(1+k)` vs `m+M`), so it lowers avalanche cost in
   absolute terms — but it changes neither the avalanche's *probability* nor the
   qualitative regime-dependence. It fixes a worst-case (`R(e)=Θ(n)`) that rarely
   bites, not the effect that dominates.
3. **The operating regime already works.** The sibling hit ρ = 0.934 on sparse
   graphs with the raw unary metric; at the exact-HGED corpus scale (n ≤ 48) the
   measured drift `M/n` sits below the `kΔ` budget. The raw metric is faithful
   exactly where the theorem is testable. Do not complicate what works.

**Procedure (T-TBc, evidence-gated).** Compute `d_I` (raw) and `d_I'`
(transcoded) on the *same* pinned corpus in T-M5a. Report `ρ(HGED, d_I)` vs
`ρ(HGED, d_I')`. This (a) proves drift carries no structural signal if
`ρ' ≥ ρ` (unary run-lengths are layout accidents), (b) strengthens the
raw-metric robustness story, (c) honors Ezequiel. **Promotion of `d_I'` to
primary is a PI decision gated on evidence** (D-ART1 keeps the default raw): it
happens only if `d_I'` materially beats raw on the geometry *and* the premium
outweighs the premise change. Default outcome: raw stays primary, transcoding is
a robustness ablation.

### 7.3 Develop the geometry as first-class — the actual strength (→ T-M5f)

The premise the user wants ("geometric properties of `(w*_c, d_Lev)`") is
currently thin: `stability.md` §5 and PROPOSAL §5 gesture at non-Euclideanness
and MDS dimension in a few lines. Make it a proper characterization:

- **Theory (textbook, no new theorem needed):** a finite discrete metric,
  generically **non-Euclidean** (Schoenberg — the double-centred Gram `B` has
  negative eigenvalues); a Bourgain `O(log n)`-distortion `L2` embedding always
  exists; JL for dimension reduction if isometry is not required.
- **Measured (feeds the flagship MDS, T-M5b):** the eigenvalue spectrum of `B`,
  the negative-eigenvalue mass ratio `Σλ⁻/Σ|λ|` (how non-Euclidean, per corpus),
  the cross-validated intrinsic dimension `D̂` (PI's chosen estimator, PROPOSAL
  §5), the stress-vs-dimension curve, and the pairwise-distance concentration.
  **`D̂` is itself a headline result:** "hypergraph space under `d_I` has estimated
  intrinsic dimension `D̂`."

This is where "geometric properties" become the paper's spine, and it is
HGED-free, so it runs at the larger application scale, not the exact-oracle
ceiling.

### 7.4 Verdict on Ezequiel's proposals

| Proposal | Verdict | Where |
|---|---|---|
| Arithmetic coding for the **bits / info-content** axis (§3) | **Implement.** Clean win on a separate axis; makes bits scale with structure, not unary layout distance. | T-M4a |
| Displacement transcoding as the **metric substrate** | **Implement as an ablation, not the primary.** Measure `ρ'` vs `ρ`; promotion evidence-gated (§7.2). | T-TBc |
| Sign-bit + **Gray-coded** magnitude (topology-preserving) | **Optional sub-ablation** of T-TBc — the bit-level form of a magnitude-weighted substitution cost; the comparison point for "does magnitude carry HGED signal?" | T-TBc |

His compression instinct is right and his own topology caveat is right; the
reinterpretation is only that the *same* mechanism cures the layout-locality
proof gap, and the two halves of his email split cleanly across the two axes
(metric vs bits) — which must never share a substrate (AC bitstreams are
avalanche-dominated at the code level; §4).

### 7.5 What NOT to spend effort on

- **Chasing a clean unconditional Lipschitz bound.** T-TBb settled that it does
  not exist in the raw metric (orphaned introducer). Effort here has diminishing
  returns; the honest regime-characterization is the stronger and more novel
  product.
- **A second canonical form** (the structure-first tour, §5) — high procedural
  cost (new D-TA2 freeze, a fresh Theorem A instance) for a benefit the ablation
  can probe first. Recorded, not tasked.
- **Block-move edit distances** (§5) — violates "Levenshtein fixed"; parked as
  future work only.

### 7.6 Task roadmap

```
D-ART1 (PI ratifies reposition)
   └─► T-TBd  reposition docs (headline = geometry; Thm B = engine)   [orchestrator-only]

T-M5f  geometry characterization (non-Euclidean, D̂, distortion)  ──► feeds T-M5b (MDS)   [the strength]
T-M5a  correlation + density sweep + s(e) histogram + info-content ──► carries T-TBc ablation
   ├─ T-TBc  transcoding ablation (ρ' vs ρ; promotion gated)
   └─ T-M4a  arithmetic-coded bits estimator
T-TBe  crossing-peak conjecture (stretch theory; raw-metric drift)   [non-blocking]
T-TBf  reconcile the unmerged T-TBb closure into this branch          [housekeeping]
```

Critical path to a strong proposal: **T-M5f + T-M5a/b** (validated geometry) with
the reposition (T-TBd) framing it. T-TBc, T-M4a, T-TBe are strengthening
side-quests; T-TBf is hygiene.

## 8. References (beyond the project canon)

- L. Yujian, L. Bo. *A Normalized Levenshtein Distance Metric.* IEEE TPAMI
  29(6), 2007. doi:10.1109/TPAMI.2007.1078
- G. Cormode, S. Muthukrishnan. *The string edit distance matching problem
  with moves.* ACM Trans. Algorithms 3(1), 2007. doi:10.1145/1186810.1186812
- Z. Zeng, A.K.H. Tung, J. Wang, J. Feng, L. Zhou. *Comparing Stars: On
  Approximating Graph Edit Distance.* PVLDB 2(1), 2009.
  doi:10.14778/1687627.1687631
- I.H. Witten, R.M. Neal, J.G. Cleary. *Arithmetic coding for data
  compression.* CACM 30(6), 1987. doi:10.1145/214762.214771
- P. Elias. *Universal codeword sets and representations of the integers.*
  IEEE Trans. Inf. Theory 21(2), 1975. doi:10.1109/TIT.1975.1055349
- C. Savage. *A survey of combinatorial Gray codes.* SIAM Review 39(4), 1997.
  doi:10.1137/S0036144595295272
