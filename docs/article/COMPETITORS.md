# IsalHG journal article — competing representations

**Status:** DRAFT (scoping session 2026-07-08). Companion to
`docs/article/PROPOSAL.md`.

> **Running the competitors?** This file is the *why these four* design
> rationale. For *how to invoke* them (registry names, the uniform
> `HypergraphDistance` interface, per-competitor setup incl. the pinned
> HyperCOT env, corpus building, and a runnable end-to-end example) see
> **`COMPETITORS_USAGE.md`**. All four (`nauty_levi_edit`, `hpd_jsd`,
> `netlsd_l2`, `hypercot`) landed on `main` 2026-07-15 (ledger scope T-M3).

The paper no longer compares *isomorphism-test wall-clock*. It compares the
**geometry each representation induces on hypergraph space**. A competitor is
now any map

    rep :  H  ↦  fingerprint(H)        (a string or a vector)

together with a distance `d_rep` on fingerprints, yielding a dissimilarity
matrix `D_rep = { d_rep(fp(H_i), fp(H_j)) }`. The head-to-head metric is the
correlation / mutual information between `D_rep` and `D_true = HGED`
(PROPOSAL §2), plus each application's own metric (PROPOSAL §4).

## 1. Requirements on a competitor

- Isomorphism-invariant fingerprint (so `D_rep` is well-defined on iso-classes).
- A natural distance on fingerprints (string edit distance, or a vector norm).
- Applicable to hypergraphs (natively, or via the Levi bipartite reduction we
  already ship in `iso_backends/levi_reduction.py`).

## 2. The competitor set (resolved 2026-07-08, code-verified)

Chosen per the user's rule: 2 standard baselines + 2 methods from specific
papers with **runnable open-source code** (no reimplementation). Full citations
and runnability verdicts in `../RELATED_WORK.md` §Competitors. Each is a
*distinct geometric philosophy*, which is the point of the comparison.

| Role | Method | Representation → distance | Code | Status |
|---|---|---|---|---|
| **ours** | IsalHG canonical H2S string `w*(H)` | raw Levenshtein | `isalhg.core` | shipped |
| **standard — fair** | hypergraph-WL colour histogram (Feng et al., TPAMI 2024, HG-WL subtree) | count vector → L1 / χ² | `core/hypergraph_wl.py` + `iMoonLab/HIC` (Apache-2.0) | partial (`hypergraph_wl.py` exists) |
| **standard — contrast** | nauty canonical form via Levi `B(H)` | canonical string → string edit | `iso_backends/pynauty_levi` | shipped |
| **paper+code — fair** | **HyperCOT** (Chowdhury et al., JACT 2024) — hypergraph co-optimal transport | transport coupling → metric distance (native pairwise) | `samirchowdhury/HyperCOT` (MIT, Python) | to wire; pins `hypernetx==1.2`, `POT==0.8.0` |
| **paper+code — fair** | **Hyperedge Portrait Divergence** (Agostinelli et al., JCN 2026) | hyperedge-path tensor → Jensen–Shannon divergence | `cosimoagostinelli/Hor_dissimilarity_measures` (MIT, Python) | to wire; extract from notebook |
| *optional spectral* | NetLSD heat-trace on Levi/clique expansion (Tsitsulin et al., KDD 2018) | spectral signature → L2 | `pip install netlsd` | optional 5th |

Why these four (besides ours): WL is vertex-neighborhood-centric; HPD is
hyperedge-path-centric and global (complements WL); HyperCOT is mass-transport
(a metric by construction, no pattern counting, no labelling); nauty is
canonical-labelling. They do not collapse into each other.

**Excluded (no runnable code):** HGSCKernel (Zhang et al., TPAMI 2025) — SOTA
structural kernel but **no code released**; cite in related work only (matches
`docs/engineering/DEVELOPMENT.md`, which already substitutes it with pynauty). Hypergraphlet
kernels (Lugo-Martínez/Pržulj 2021) — C++/BOOST, no Python, ~6k orbits,
impractical. Traces/bliss — redundant with nauty for the *contrast* role; drop.
Learned GNN embedding — dropped (needs training/features; PI steers classical).

**Note on HyperCOT's dual role.** It is *both* our theoretical anchor (its
arity-`k` Levi-Lipschitz result, `../theoretical/stability.md` §2.0) *and* a
runnable competitor. Cite it in related work for the theory; run it as a
baseline. State the dual role in the paper to avoid the appearance of
cherry-picking.

## 3. The fairness question (central design decision)

Two honest buckets, stated in the paper:
- **Fair metric baselines** — WL histogram, HyperCOT (a genuine metric), HPD
  (JS-divergence; its square root is a metric), optional NetLSD. These are real
  "representation induces a geometry" competitors; the head-to-head on
  HGED-correlation is a fair fight.
- **Contrast baseline** — nauty canonical-form edit distance, included precisely
  to *demonstrate* that iso-only canonical labelling yields **no navigable
  geometry**: a single edit can permute the whole labelling ⇒ large,
  structurally-meaningless edit distance (now backed by the non-lower-Lipschitz
  result, `../theoretical/stability.md` §2.0). Presenting it as a "competitor we
  beat" without this framing is a strawman; presenting it as the *contrast that
  motivates structure-incremental encoding* is the honest and stronger move.
  It also anchors A4 (shortest path): nauty structurally **cannot** do it.

## 4. Resolved / remaining

- CQ1. **[resolved]** Fair = WL, HyperCOT, HPD (+ optional NetLSD); contrast =
  nauty. See §3.
- CQ2. **[resolved]** No learned baseline — classical only.
- CQ3. **[per-method, resolved in table]** distances: L1/χ² (WL), transport
  metric (HyperCOT), JS-divergence (HPD), string edit (nauty), L2 (NetLSD).
- CQ4. **[resolved]** Minimum credible set = the four in §2 (ours + WL + nauty +
  {HyperCOT, HPD}); NetLSD optional.
- CQ5. **[new, engineering]** Adapter work: HyperCOT needs a pinned-version
  subprocess/conda env (API-incompatible with our HyperNetX); HPD needs
  extraction from a Jupyter notebook into a callable. Both wrap behind
  `iso_backends`/a new `representations/` layer emitting a pairwise `D_rep`.
  Decide the module home (these are *not* `IsoBackend`s — they yield distances,
  not iso decisions).
