# IsalHG journal article — competing representations

**Status:** ACTIVE (v3 rescope 2026-07-18). Companion to
`docs/article/PROPOSAL.md`.

> **Running the competitors?** This file is the *why these* design
> rationale. For *how to invoke* them (registry names, the uniform
> `HypergraphDistance` interface, per-competitor setup incl. the pinned
> HyperCOT env, corpus building, and a runnable end-to-end example) see
> **`COMPETITORS_USAGE.md`**. All four T-M3 implementations
> (`nauty_levi_edit`, `hpd_jsd`, `netlsd_l2`, `hypercot`) landed on `main`
> 2026-07-15 (ledger scope T-M3).

The paper compares the **geometry each representation induces on hypergraph
space** and what that geometry lets you do. A competitor is any map

    rep :  H  ↦  fingerprint(H)        (a string or a vector)

together with a distance `d_rep` on fingerprints, yielding a dissimilarity
matrix `D_rep = { d_rep(fp(H_i), fp(H_j)) }`. **The head-to-head axes (v3):**

1. **Task metrics per application** — stress/`D̂` at matched dimension (A1),
   silhouette/ARI/NMI (A2), accuracy/F1/AUC (A3), path recovery and
   monotonicity (A4) — same pipeline, each representation's own `D_rep`.
2. **Per-representation geometry** — intrinsic dimension `D̂`, non-Euclidean
   mass `ν`, concentration/hubness profile: whose induced space is more
   compact and better conditioned (`theoretical/geometry.md`).
3. **The capability matrix** — what each representation *cannot* do: no
   decoder (all vector fingerprints), no navigable geometry (canonical-form
   contrast), scale limits (stated per method).

The v2 axis — correlation / MI against HGED — is **retired** with the proxy
framing (PROPOSAL §1, pivot 2). No competitor HGED head-to-head is run.

## 1. Requirements on a competitor

- Isomorphism-invariant fingerprint (so `D_rep` is well-defined on iso-classes).
- A natural distance on fingerprints (string edit distance, or a vector norm).
- Applicable to hypergraphs (natively, or via the Levi bipartite reduction we
  already ship in `iso_backends/levi_reduction.py`).

## 2. The competitor set (v3: five, NetLSD promoted)

Chosen per the standing rule: 2 standard baselines + 2 methods from specific
papers with **runnable open-source code** (no reimplementation), + the
canonical-form contrast. Full citations and runnability verdicts in
`../RELATED_WORK.md` §Competitors. Each is a *distinct geometric philosophy*,
which is the point of the comparison.

| Role | Method | Representation → distance | Code | Scale policy |
|---|---|---|---|---|
| **ours** | IsalHG canonical string `w*_c(H)` | raw Levenshtein | `isalhg.core` + `rapidfuzz` | all corpora (gated by `w*_c` wall-clock, T-DQ3') |
| **standard — fair** | hypergraph-WL colour histogram (Feng et al., TPAMI 2024) | count vector → L1 / χ² | `core/hypergraph_wl.py` + `iMoonLab/HIC` (Apache-2.0) | all corpora |
| **standard — fair** | **NetLSD** heat-trace on the Levi expansion (Tsitsulin et al., KDD 2018) | spectral signature → L2 | `pip install netlsd` (MIT) | all corpora — **promoted to full member (v3)**: it is the cheap spectral baseline that scales wherever we do |
| **paper+code — fair** | **HyperCOT** (Chowdhury et al., JACT 2024) — hypergraph co-optimal transport | transport coupling → metric distance | `samirchowdhury/HyperCOT` (MIT; pins `hypernetx==1.2`, `POT==0.8.0`) | small/mid corpora only — `O(n³)`/pair; **the limit is stated in every table, not hidden** |
| **paper+code — fair** | **Hyperedge Portrait Divergence** (Agostinelli et al., JCN 2026) | hyperedge-path tensor → Jensen–Shannon divergence | `cosimoagostinelli/Hor_dissimilarity_measures` (MIT; extract from notebook) | all corpora (cost permitting; measure and report) |
| **contrast** | nauty canonical form via Levi `B(H)` | canonical string → string edit | `iso_backends/pynauty_levi` | all corpora |

Why these (besides ours): WL is vertex-neighborhood-centric; HPD is
hyperedge-path-centric and global; NetLSD is spectral; HyperCOT is
mass-transport (a metric by construction, no pattern counting); nauty is
canonical-labelling. They do not collapse into each other.

**Excluded (no runnable code):** HGSCKernel (Zhang et al., TPAMI 2025) — no
code released; cite in related work only. Hypergraphlet kernels
(Lugo-Martínez/Pržulj 2021) — C++/BOOST, no Python, ~6k orbits, impractical.
Traces/bliss — redundant with nauty for the contrast role. Learned GNN
embeddings — dropped (need training/features; classical scope).

**Note on HyperCOT's dual role.** It is *both* a theory anchor (its arity-`k`
Levi-Lipschitz result is cited in the discussion's mechanism prose) *and* a
runnable competitor. State the dual role in the paper to avoid the appearance
of cherry-picking.

## 3. The fairness question (central design decision)

Two honest buckets, stated in the paper:

- **Fair metric baselines** — WL histogram, NetLSD, HyperCOT (a genuine
  metric), HPD (JS-divergence; its square root is a metric). Real
  "representation induces a geometry" competitors; the head-to-head on task
  metrics and induced geometry is a fair fight.
- **Contrast baseline** — nauty canonical-form edit distance, included
  precisely to *demonstrate* that iso-only canonical labelling yields **no
  navigable geometry**. In v3 this is **measured, not asserted**: the G2
  sensitivity profile (`empirical/applications.md`) computes nauty's `s(e)`
  histogram alongside ours — a single edit permutes the whole labelling, so
  its profile is avalanche-everywhere. Presenting nauty as a "competitor we
  beat" without this framing would be a strawman; presenting it as the
  measured contrast that motivates structure-incremental encoding is the
  honest and stronger move. It also anchors A4: nauty structurally **cannot**
  navigate paths.

**Symmetry of the argument (state it).** IsalHG's own sensitivity profile has
an avalanche regime too (near-symmetric inputs with incoherent ties — the
price any *complete* invariant pays; `theoretical/stability_reformulations.md`
§6). The contrast is not "we are stable, they are not"; it is "our profile is
compact outside a characterized regime; theirs is avalanche *everywhere*."
Stability-by-construction competitors (WL, NetLSD, HyperCOT) buy their
smoothness by giving up completeness — the frontier position the discussion
makes explicit.

## 4. Naive structural baseline (degree-sequence L1)

*Added at T-M7c, 2026-07-22. Contract written before any result is seen.*

**Definition.** For a hypergraph `H` with `n` vertices, let `deg(H)` be the
primal-degree sequence sorted in non-increasing order. The **degree-sequence L1
distance** is

    d_DS(H, H') = ||deg(H) - deg(H')||_1   (zero-padded to equal length)

where padding extends the shorter sequence with zeros. This is a metric:
non-negativity and symmetry are immediate; the triangle inequality is inherited
from L1 on finite-dimensional vectors after embedding both sequences into
ℝ^max(n,n').

**Incompleteness witness (documented here before seeing data).** The distance is
explicitly *not* a complete invariant: any two non-isomorphic hypergraphs that
share a primal-degree multiset receive distance 0. A pinned witness is the
`non_iso_pair_small` fixture — H1 (4 nodes, two 3-edges sharing a pair) and H2
(4 nodes, three 2-edges forming a path) both have degree sequence [2, 2, 1, 1],
so `d_DS(H1, H2) = 0` despite non-isomorphism. The distance is O(n log n) per
pair and purely structural.

**Interpretation contract (written before results are seen, 2026-07-22).**

The naive baseline answers the question no current table answers: *does any
method beat a trivially cheap structural signal?* Two outcomes are equally valid
and both improve the paper:

1. **If IsalHG and the sophisticated methods clearly exceed the naive row** on a
   task, the degree-sequence baseline contextualizes the gain: the task requires
   higher-order structure that the first-order degree profile cannot capture, and
   the sophisticated methods earn their complexity.
2. **If any sophisticated method barely beats the naive baseline** on a task,
   that is reported plainly — it means the task's discriminative signal is mostly
   first-order and the added complexity of a richer representation is not yet
   justified on that task. This is a scientific finding, not a failure.

Neither outcome is suppressed. The naive row is present in every comparison
surface (geometry table, A2 clustering, A3 kNN, A4 capability row, HIC exhibit)
and interpreted by the paragraph above, not cherry-picked after results are seen.

**Registry name.** `"degree_seq_l1"` — implemented in
`src/isalhg/metric_space/representations/degree_seq_l1.py` (T-M7c, 2026-07-22).

**Outcome (2026-08-09) — the contract discharged, and a second floor added.**
Outcome 2 obtained, and more sharply than anticipated: degree-sequence L1 not
only beat IsalHG on A2 and A3, it was itself matched by a cruder distance
still. `d_size(H,H') = |n−n'| + |m−m'|` — two integers per hypergraph, no
structural content — reaches ARI 0.442 and AUC-OvR 0.932 on the design corpus,
outranking five of seven representations on the first and four of seven on the
second. Per the contract, this is reported plainly: the discriminative signal
in that corpus is not merely first-order, it is size, and the corpus therefore
does not test the representations at all
(`../theoretical/geometry.md` §5). The conclusion falls on the corpus, not on
the competitor set.

Two consequences follow, both binding.

- **`d_size` joins the comparison as a second naive baseline**, registry name
  `"size_l1"`, present in the same surfaces as `degree_seq_l1` and carried
  through the same harness so it gains the same BCa intervals and Holm-corrected
  tests. A comparison whose floor is invisible cannot be read, and this floor is
  one line of code for a reviewer to reconstruct.
- **No competitor is removed on the basis of having won.** The contract above
  was written before results were seen precisely to bind this case, and it
  binds. NetLSD stays: it is the reference spectral descriptor (CQ4), and
  excluding the spectral family because it scores well would leave the paper
  without the one baseline every reader of this literature expects.
  Degree-sequence L1 stays: it is the floor, and a floor that is removed when it
  rises is not a floor. The right response to a naive baseline winning is to
  fix the corpus, which is what is being done.

**Resolution (2026-08-09) — the corpus fixed, the floors verified, the
outcome reported.** On the size-controlled replacement corpus (Stratum C,
`../DATA.md` §1; 3 cells, 27 seeds) both naive baselines sit at exactly the
structural floor by construction and by measurement: ARI −0.000
[−0.001, 0.000], AUC-OvR 0.492 at every cell, through the same BCa/Holm
harness as every other row. With the floor enforced, the contract's outcome
on the *structural* signal falls against IsalHG and is reported in that
direction: the nauty-Levi contrast baseline leads (ARI up to 0.614
[0.571, 0.657]), HPD second, NetLSD third, all three Holm-significantly above
IsalHG (which is itself Holm-significantly above the floors at every cell),
and the WL histogram is tie-degenerate at the floor. No competitor is
removed for winning — the contrast baseline winning the tasks is itself a
finding, and `../empirical/applications.md` §Usefulness carries its
mechanism (avalanche/drift) and its consequences.

## 5. Resolved / remaining

- CQ1. **[resolved]** Fair = WL, NetLSD, HyperCOT, HPD; contrast = nauty. §3.
- CQ2. **[resolved]** No learned baseline — classical only.
- CQ3. **[resolved]** Distances: L1/χ² (WL), L2 (NetLSD), transport metric
  (HyperCOT), JS-divergence (HPD), string edit (nauty).
- CQ4. **[resolved, v3]** Credible set = ours + the four fair + the contrast;
  NetLSD is no longer optional.
- CQ5. **[engineering, tracked in `DEVELOPMENT/`]** Adapter work: HyperCOT
  needs a pinned-env subprocess; HPD needs extraction from a notebook. Both
  wrap behind the `metric_space/representations/` layer emitting pairwise
  `D_rep` (they are *not* `IsoBackend`s — they yield distances, not iso
  decisions).
- CQ6. **[resolved, T-M7c 2026-07-22]** Naive structural baseline added:
  degree-sequence L1 (`degree_seq_l1`). One primary naive baseline per the
  REVIEW decision; the alternative candidates (size signature,
  incidence-Jaccard) are not added. Interpretation contract pre-registered in
  §4 above.
