# IsalHG journal article — competing representations

**Status:** ACTIVE (v3 rescope 2026-07-18). Companion to
`docs/article/PROPOSAL.md`.

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

## 4. Resolved / remaining

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
