# Discussion evidence — the HGED-relation figure + information content

**Status:** ACTIVE. **This layer is discussion
evidence, not a pillar.** The v2 scope ran a full HGED-faithfulness capstone
here (correlation study E1, density sweep E2 validating Theorem B, competitor
head-to-head on the HGED axis, MI). The v3 scope (PROPOSAL §1 pivot 2, §5)
retires that framing: the article makes **no proxy claim**, and this layer
produces exactly two things —

1. **E1' — one exact-HGED correlation figure** (ours only) for the closing
   discussion: the honest empirical footprint of the `d_I` ↔ HGED relation.
2. **The information-content (bits) comparison** for the compactness
   subsection (PROPOSAL §4).

The HGED definition and the exact oracle are **kept** — they produce the
figure, and the Qin cost model grounds the perturbation-ladder budgets used
throughout the body (`applications.md` G2/A4). The former experiments E2b
(sensitivity histograms) and E3 (ladder scaling) never used the oracle and now
live in the geometry pillar (`applications.md` G2).

## HGED — definition and oracle (kept; produces the figure and the budgets)

HGED is NP-hard but already formalized for hypergraphs: Qin et al. (ICDE 2023,
`../RELATED_WORK.md`) define it with the exact edit taxonomy below and a
branch-and-bound solver. We **adopt** their definition (unit costs), not invent
one; cite it as the HGED reference alongside the GED lineage (Riesen & Bunke
2009; Blumenthal et al., VLDB 2020).

**Definition (Qin et al. 2023, adopted verbatim — the article's single official
cost model, superseding an interim whole-edge
variant).** `HGED(H,H')` = min total cost of an edit sequence transforming `H`
into a hypergraph isomorphic to `H'`, over Qin's Definition-3 atomic ops, all
unit cost: (i) insert/delete a **cardinality-0** node or hyperedge (empty
shell); (ii) extend/reduce a hyperedge by one node; (iii) substitute a node or
hyperedge label. Hence deleting/inserting a whole arity-`a` hyperedge costs
`a+1` and deleting a degree-`h` node costs `h+1`. Implemented by two
exactly-agreeing solvers (property-tested): `exact_hged` (LSAP
branch-and-bound, the oracle) and `qin_hged` (the paper's HGED-BFS, the
fidelity anchor reproducing its Example 2 and Table II regime).

**Why Qin's costing also serves the v3 scope.** `|w*_c|` scales with incidence
mass (each hyperedge costs Θ(arity) tokens), and Qin prices structural edits by
incidence count too — the two axes of the E1' figure are commensurate. More
importantly for the body: the **perturbation-ladder budget** is the accumulated
Qin cost of the applied generator edits (`core/sparse_hypergraph.py::
qin_edit_cost`), so `HGED ≤ budget` holds by construction — this is what makes
the G2 ladder response and the A4 scoring well-defined *without* calling the
oracle.

**Deviation ledger vs Qin et al. (2023).** Complete enumeration; anything not
listed is verbatim. *Metric level: none* — the cost model is Definition 3
verbatim, including unit label substitution.

*Model level:*
- (M1) Hypergraphs are simple: `SparseHypergraph` merges duplicate
  `(label, member-set)` hyperedges (mathoverflow-answers: 5,446 file lines →
  5,445 edges). Consistent with Qin's own model (§III: `E` a set of unordered
  node sets, `|E| ≤ 2^|V|`); merges are counted and reported per dataset.
- (M2) Empty-shell intermediates are never materialized (`SparseHypergraph`
  requires arity ≥ 1). Value-identical: all solvers cost complete
  node+hyperedge *correspondences* — exactly the formulation of Qin's own
  Algorithm 2 — so no intermediate state is ever constructed.
- (M3) Multi-label nodes (mathoverflow tags) are encoded as one composite
  symbol: the lexicographically sorted tag names joined with `","`; label
  equality = tag-set equality. Qin's `l(v)` is single-valued with equality
  semantics and the paper does not state its reduction; the composite is the
  only deterministic choice that drops no information (decision D2).

*Algorithm level (all value-preserving; equality property-tested against both
the paper's HGED-BFS and exhaustive enumeration on small pairs):*
- (A1) The oracle is an LSAP branch-and-bound over vertex correspondences with
  Riesen–Bunke-seeded incumbents, not the paper's HGED-BFS. Measured
  justification: HGED-BFS's Definition-5 node bound is identically zero on
  unlabelled inputs, leaving no node-phase pruning (15/15 DNF at every density
  from n=10 in the gate probe), while the B&B's partial-map LSAP bounds reach
  the required regime.
- (A2) Source/target orientation with no node insertions is Qin's own
  Lemma 4.1 (listed for completeness, not a deviation).
- (A3) No-cross pruning: an optimal correspondence never deletes a real edge
  *and* inserts a real edge it could match, since matching costs
  `Hamming + label ≤ |E| + |E'| + 1 < (1+|E|) + (1+|E'|)`; the analogous
  claim for nodes is Lemma 4.1's argument. Prunes only suboptimal solutions.
- (A4) The Definition-5+6 bound is evaluated once at the root (then
  incrementally), so clamped queries on far pairs return "> bound" in
  `O(n + m log m)`.
- (A5) HGED-BFS engineering (bitmask incidence sets, O(1)-incremental Ψ,
  cheapest-candidate-first ordering): value-identical. ReRank tie-breaking
  differs from the paper's Example-6 order, which is not derivable from its
  stated rules; ReRank affects wall-clock only, never the returned value.

*Protocol level:*
- (P1) The perturbation-ladder budget is the accumulated Qin cost of the
  applied generator edits, not the op count — the path realises an actual Qin
  edit sequence of exactly that cost, so `HGED ≤ budget` holds under the
  official model.
- (P2) Table II's pair-sampling is unspecified in the paper; the reproduction
  reports both uniform-random and HEP-neighbor (`v ∈ NEI(u)`) sampling, under
  the paper's stated clamp (upper bound ≈ 10).

**Oracle use in v3 (tiering collapsed):** the exact oracle (`exact_hged`, HPC
parallel) is called **only** for the E1' mini-corpus. The ladder tier survives
as the budget-accounting device of the body (no oracle calls). BP-HGED is
retired from the article (was an optional cross-check of a study that no
longer runs); the implementation remains in the tree.

## E1' — the discussion figure (rescoped from v2's E1)

- Corpus: one small **connected** corpus with exact HGED computable (the
  mini-corpus, `../DATA.md` §4); all pairs with `HGED>0`.
- Report: **Spearman ρ** (rank-based, matching the discrete/tied nature of
  both axes; Pearson r optional in caption) and the scatter/joint-density
  plot. **Ours only** — no competitor head-to-head (that axis is retired with
  the proxy framing), no density sweep, no MI (dropped with the head-to-head;
  PROPOSAL OQ-F, PI-ratified).
- Placement and interpretation: inside the closing discussion (PROPOSAL §5),
  *after* the envelope and impossibility statements — offered as
  characterization ("this is the measured footprint of the relation on a small
  corpus"), never as validation of a bound.

**Measured (final — the 11-block mini-corpus, `../DATA.md` §4).** Pooled over
all pairs with HGED > 0: Spearman ρ = 0.622 (N = 6,921 pairs, p ≈ 0; Pearson
r = 0.663; OLS slope of `d_I` on HGED 0.568); per-cell ρ ranges 0.48–0.81,
with the two largest cells at the top of the range (n = 9: 0.72; n = 10:
0.69). Every HGED = 0 pair has `d_I` = 0 — the identity-of-indiscernibles
cross-check between the two metrics. The cost boundary is itself informative:
the n = 9–10 cells exhausted a first 16 GB / 6 h allocation, the completed
reruns needed up to 8.5 h and a 55 GB peak per 630-pair cell, and the twelfth
block (the second n = 10 seed) exceeded 100 GB after 18 h and is excluded
whole-block (per-pair censoring would bias ρ; `../DATA.md` §4). The exact
oracle thus reaches its practical ceiling *at the boundary of this
mini-corpus* — a concrete illustration of why the article's methodology
validates usefulness on task metrics rather than on an HGED axis.

**Out of scope (recorded):** the v2 density sweep E2 (ρ vs Δ, the Theorem-B
Δ-prediction) and the competitor HGED head-to-head. Both are follow-up
material; the prediction itself is recorded in `../theoretical/stability.md`
§4.

## Information content (bits) — the compactness subsection

Ported from the sibling (its estimator is reviewer-tested): a **uniform
fixed-width code**, *not* Shannon entropy and *not* compressed length.

- IsalHG bits: `B_IsalHG(w) = |w| · log2 |Σ_HG(k)|` (the alphabet is
  k-dependent — count `V_{i,j}, C_i, P_i, N_i, W`).
- Competitor "construction model" bits: incidence-list encoding — per
  hyperedge, `1` type bit + `(arity)·⌈log2 n⌉` endpoint-address bits; plus
  `n−1` vertex-insertion bits. (Generalizes the sibling's
  `B_GED = (N−1+M) + 2M⌈log2 N⌉`, whose `2M` assumed arity 2.)
- Compression ratio `r(H) = B_comp(H)/B_IsalHG(w)`, `r>1` favours IsalHG.
- One-sided **Wilcoxon signed-rank** on `r−1`; OLS `B_IsalHG = a+β·B_comp`,
  `β<1` ⇒ systematic compression. Sibling reference points: median
  r ∈ [1.45, 1.89], shorter for 98.8–99.6% of graphs.
- Placement: the short compactness subsection where the representation is
  introduced (PROPOSAL §4). Corpora: the body corpora (no oracle needed).
- An entropy-coded refinement of the estimator is optional future work, not
  load-bearing.

**Measured (the three planted body corpora, N = 320 pooled).** Every
hypergraph compresses: `r > 1` on 320/320 (fraction shorter = 1.000), pooled
median r = 1.441 (per-corpus: 1.433 on the five-family N = 60 corpus, 1.565
on the small N = 20 corpus, 1.439 on the N = 240 primary corpus), one-sided
Wilcoxon p = 1.6 × 10⁻⁵⁴, OLS β = 0.749 < 1. Median canonical-string lengths
are 22 tokens (n = 10 corpora) and 8 tokens (n = 6) — 81.4 and 29.6 bits at
`log2 |Σ_HG(3)| = log2 13 ≈ 3.70` bits/token — against incidence-list codes
of 114.0 and 44.5 bits (medians).
The medians sit at the lower edge of the graph sibling's reported band
(median r ∈ [1.45, 1.89]): "a hypergraph is a compact word" holds uniformly
on the article's own corpora. Token counting goes through the bracket-aware
parser (`;` separates fields inside `V[...]`/`C[...]` as well as tokens — a
raw split overcounts ≈2× and *reverses* this conclusion; pinned by a
regression test).

## Open (this layer)

- Mini-corpus size + (n,m) ceiling for E1' under the HPC-parallel exact oracle
  (→ `../DATA.md` §4); connected-domain generators gate it.
- None else — the MI-estimator and density-sweep questions are retired with
  the v2 scope.
