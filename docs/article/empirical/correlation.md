# Layer 1 — controlled validation of the stability theorem

**Status:** DRAFT (scoping 2026-07-08). Tests `../theoretical/stability.md`
Theorem B. Ports and extends the IsalGraph correlation methodology (their
Table 2, Spearman ρ up to 0.934) and information-content methodology (their
Table 1, median compression ratio 1.45–1.89).

## HGED — definition and oracle tiering

HGED is NP-hard but — unlike I assumed last turn — **already formalized for
hypergraphs**: Qin et al. (ICDE 2023, `../RELATED_WORK.md`) define it with the
exact edit taxonomy below and a branch-and-bound solver. We **adopt** their
definition (unit costs), not invent one; cite it as the HGED reference and the
GED lineage (Riesen & Bunke 2009 for the bipartite approximation; Blumenthal
et al., VLDB 2020, for the density-dependence of approximation error, which
dovetails with the avalanche story).

**Definition (Qin et al. 2023, adopted verbatim — the article's single official
cost model; PI decision 2026-07-08 at T-M2a close, superseding the earlier
whole-edge variant).** `HGED(H,H')` = min total cost of an edit sequence
transforming `H` into a hypergraph isomorphic to `H'`, over Qin's Definition-3
atomic ops, all unit cost: (i) insert/delete a **cardinality-0** node or
hyperedge (empty shell); (ii) extend/reduce a hyperedge by one node; (iii)
substitute a node or hyperedge label. Hence deleting/inserting a whole arity-`a`
hyperedge costs `a+1` and deleting a degree-`h` node costs `h+1`. Implemented by
two exactly-agreeing solvers (property-tested): `exact_hged` (LSAP
branch-and-bound, the oracle the experiments call) and `qin_hged` (the paper's
HGED-BFS, the fidelity anchor reproducing its Example 2 and Table II regime).

**Why Qin's costing is the best fit for this paper (not just the citable
choice).** `|w*|` scales with incidence mass (each hyperedge costs Θ(arity)
tokens to encode), and Qin prices structural edits by incidence count too
(whole arity-`a` edge = `a+1`). The two axes of the correlation study are
therefore *commensurate*: the per-unit-HGED sensitivity of `d_I` stays O(1)
in arity for the direct term, where a unit whole-edge op would inflate it to
O(k) (see the remark in `../theoretical/stability.md` §2.2). The interim
whole-edge variant's sole rationale — the ladder guarantee — is fully
recovered by Qin-cost budget accounting, so it retains no advantage.

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
- (A1) The experiments' oracle is an LSAP branch-and-bound over vertex
  correspondences with Riesen–Bunke-seeded incumbents, not the paper's
  HGED-BFS. Measured justification: HGED-BFS's Definition-5 node bound is
  identically zero on unlabelled inputs, leaving no node-phase pruning
  (15/15 DNF at every density from n=10 in the T-M2a gate probe), while the
  B&B's partial-map LSAP bounds reach the Layer-1/density-sweep regime.
- (A2) Source/target orientation with no node insertions is Qin's own
  Lemma 4.1 (listed for completeness, not a deviation).
- (A3) No-cross pruning: an optimal correspondence never deletes a real edge
  *and* inserts a real edge it could match, since matching costs
  `Hamming + label ≤ |E| + |E'| + 1 < (1+|E|) + (1+|E'|)`; the analogous
  claim for nodes is Lemma 4.1's argument. Prunes only suboptimal solutions.
- (A4) The Definition-5+6 bound is evaluated once at the root (then
  incrementally), so clamped queries on far pairs return "> bound" in
  `O(n + m log m)` — the source of the 10²–10⁴× speed advantage over the
  paper's Table II timings on identical queries.
- (A5) HGED-BFS engineering (bitmask incidence sets, O(1)-incremental Ψ,
  cheapest-candidate-first ordering): value-identical. ReRank tie-breaking
  differs from the paper's Example-6 order, which is not derivable from its
  stated rules; ReRank affects wall-clock only, never the returned value.

*Protocol level:*
- (P1) The perturbation-ladder budget is the accumulated Qin cost of the
  applied generator edits (`core/sparse_hypergraph.py::qin_edit_cost`), not
  the op count — the path realises an actual Qin edit sequence of exactly
  that cost, so `HGED ≤ budget` holds under the official model.
- (P2) Table II's pair-sampling is unspecified in the paper; the reproduction
  reports both uniform-random and HEP-neighbor (`v ∈ NEI(u)`) sampling, under
  the paper's stated clamp (upper bound ≈ 10).

**Oracle tiering (by scale):**

| Tier | Regime | HGED oracle | Note |
|---|---|---|---|
| exact | n past 10 (HPC) | branch-and-bound over Qin's atomic ops (`exact_hged`) | ground truth; **runs on HPC with high parallelism**, so the `n`-ceiling is well past the sibling's ≤12 — T-M2 benchmarks where it actually falls |
| ladder | large n | perturbation ladder: `H' = H after t random generator edits` ⇒ `HGED ≤ budget` (accumulated Qin cost of the applied ops, `qin_edit_cost`) known by construction | **upper bound only** — edits may cancel; honest caveat required |
| approx (optional) | medium n | **BP-HGED** — Riesen–Bunke bipartite (Hungarian) assignment on incidence stars | demoted to an *optional cross-check* that the ladder's `t` proxies true HGED — not load-bearing |

**Decision (DQ2, updated 2026-07-08):** exact HGED is the ground truth and now
runs on **HPC with high parallelism**, so the exact-oracle corpus for the density
sweep reaches larger `n` than first assumed (was ~10–12). Exact (small–medium) +
ladder (scale) are load-bearing; BP-HGED is optional. **This is where all HGED
computation lives** — the Layer-2 applications (`applications.md`) do not use HGED
at all, so they are not bound by this ceiling.

**Exact-`ExactHGED` implementation note (OD4, resolved):** own A*/ILP over the
six edit ops — **not** `networkx.graph_edit_distance` on the Levi graph, whose
equality with HGED is not established (the bipartite vertex/edge-node cost lift
needs an unproven correctness argument). A 2026-07-08 search confirmed **no
public HGED solver exists** (Qin et al. released none); read `networkx`
`optimize_graph_edit_distance` and `LijunChang/Graph_Edit_Distance` as A*
*scaffolds only*, and `scipy.optimize.linear_sum_assignment` for the optional
BP-HGED.

## Distance under test

Primary: **raw Levenshtein** `d_I = d_Lev(w*(H), w*(H'))` (matches sibling; it
achieved ρ=0.934 raw). Ablations (secondary, one table): length-normalized edit
distance; token-aware substitution costs over `Σ_HG` (`V`↔`C` vs pointer-index
substitutions). Do **not** lead with normalization — evidence says raw suffices.

## Experiments

**Exp E1 — correlation (ports IsalGraph Table 2).** Corpus of small hypergraphs
with exact HGED; all pairs with `HGED>0, d_I>0`. Report, per corpus and per
competitor representation: Spearman ρ, Pearson r, OLS slope β (sibling found
β≈0.8 <1: `d_I` grows slower than HGED), and **mutual information** `I(HGED;d)`
(PI's requested second statistic; the sibling did *not* report MI — a novelty).
Scatter/joint-density figure per representation (cf.
`fig_aggregated_density_correlation.pdf`).

**Exp E2 — density sweep (validates Theorem B; NOT in the sibling).** Fix `n`
(HPC exact HGED lets this go past n=10, widening the sweep), sweep density
(m/n and arity `k`) so Δ ranges widely. Plot ρ(d_I,HGED) vs Δ.
**Prediction from stability.md §4:** ρ decreases as `1/C(k,Δ)` with C=O(k·Δ).
Overlay the predicted envelope. This is the experiment that *couples* theorem to
data — its success is the empirical proof of Theorem B's Δ-dependence.

**Exp E2b — single-edit sensitivity histogram (tests the avalanche, §3, revised at T-TBa).**
Directly measure `s(e)=d_I(H,H⊕e)` over many single edits (all Qin edit types),
per density and on the four design fixtures (Fano, STS(9), STS(13), GQ(2,2)).
**Revised prediction:** The histogram shape follows three regimes determined by the
automorphism-coherence of ties (`stability.md` §3, Proposition 6.0):
- *Generic sparse*: ties absent at every search depth → tie-set transparency holds
  for almost all edits → **unimodal, O(kΔ) peak, no avalanche tail**.
- *Coherent-tie symmetric designs (Fano, STS(9))*: `w*_greedy = w*_c` verified
  (T-TAa); all ties coherent at all depths → coherence is robust to local edits on
  vertex-transitive designs → **near-unimodal O(kΔ), despite high symmetry**.
  *(Changed from the earlier "symmetric ⇒ bimodal" prediction; the greedy-based
  analysis incorrectly placed all vertex-transitive designs in the avalanche regime.)*
- *Incoherent-tie symmetric designs (STS(13), GQ(2,2))*: `w*_greedy ≠ w*_c`
  verified (T-TAa); incoherent ties exist at depth > 0 → edits that touch the
  relevant neighbourhood perturb those tie sets → **heavy-tailed or bimodal
  histogram** with rare large-`s(e)` spikes. Tail mass ∝ fraction of edits
  reaching an incoherent tie.

This three-way split is the **falsification target for `stability.md` §3**: if the
two coherent designs (Fano, STS(9)) do not show near-unimodal histograms — or if
the two incoherent designs (STS(13), GQ(2,2)) do not show heavier tails than the
sparse baseline — the Proposition 6.0 coherence characterization is incomplete.

**Exp E3 — perturbation-ladder scaling.** Large hypergraphs, `d_I` vs known
edit-budget `t`; monotone tracking confirms faithfulness beyond the exact regime.

## Information content (bits) — ports IsalGraph Table 1

The sibling's estimator is a **uniform fixed-width code**, *not* Shannon entropy
and *not* compressed length — clean and reviewer-tested. Port directly:

- IsalHG bits: `B_IsalHG(w) = |w| · log2 |Σ_HG(k)|`  (sibling: `|Σ|=9`, here the
  alphabet is k-dependent — count `V_{i,j},C_i,P_i,N_i,W`).
- Competitor "construction model" bits for a hypergraph: incidence-list encoding
  — per hyperedge, `1` type bit + `(arity)·⌈log2 n⌉` endpoint-address bits; plus
  `n−1` vertex-insertion bits. (Generalizes the sibling's
  `B_GED = (N−1+M) + 2M⌈log2 N⌉`, whose `2M` assumed arity 2.)
- Compression ratio `r(H) = B_comp(H)/B_IsalHG(w)`, `r>1` favours IsalHG.
- One-sided **Wilcoxon signed-rank** on `r−1`; OLS `B_IsalHG = a+β·B_comp`, β<1
  ⇒ systematic compression. Sibling: median r∈[1.45,1.89], shorter for
  98.8–99.6% of graphs.

This is IsalHG's likely *win* axis (PI 2026-07: "ahí quizá tengamos ventaja"):
comparable structural discrimination at fewer bits.

## Open (this layer)

- DQ1 exact-HGED corpus size + (n,m) ceiling.
- Which real small-hypergraph corpora admit exact/BP HGED (→ `../DATA.md`).
- Confirm MI estimator (binning vs k-NN Kraskov) for `I(HGED;d)`.
