# Handoff — Hypergraph-Native Benchmark Cohort

**Status:** open investigation.
**Owner of next iteration:** TBD.
**Last touched:** 2026-06-14.
**Parent docs:** `docs/PROPOSAL.md` (Tier 1-5), `docs/DEVELOPMENT.md` (open
question #8 — isomorphism-pair generation), `docs/CODE_DESIGN.md` §2.2
(`HypergraphDataset` ABC).

---

## 1. Problem surfacing

### 1.1 What we noticed

The Phase 3 close used `ExhaustiveSmallHypergraphs` with
`pynauty_levi` as the iso-class dedup oracle. The dataset itself
*defines* the iso-class partition, so the protocol's FP/FN counts
necessarily measure **agreement with pynauty**, not absolute
correctness. If pynauty mislabels a pair as non-iso and IsalHG
correctly labels it as iso, IsalHG is recorded as a False Positive.
This was item #2 in the Phase-3/4 self-review on 2026-06-13.

A complementary observation came when looking at the pallini benchmarks
suite (`https://pallini.di.uniroma1.it/Graphs.html`). The suite is the
de-facto standard for canonical-labelling timing — but it is a
**graph** benchmark library. We do not want to rely on it as our
primary cohort.

### 1.2 Why we cannot use graph-only benchmarks

IsalHG's research claim is **native hypergraph isomorphism testing**
without round-tripping through a graph encoding. The four baselines
(pynauty, Traces, bliss) reach hypergraphs only via the Levi bipartite
reduction. If our Tier 1-3 cohort is sourced from graph benchmarks
(pallini, McKay's ANU catalog), then:

- **Asymmetric playing field.** Competitors solve their native problem
  (graph iso); IsalHG solves its native problem AND eats the cost of
  Levi-inverse reconstruction (which is not currently implemented in
  the package). This biases timing comparisons.
- **Hardness families don't transfer.** The pallini `mz` (Miyazaki),
  `cfi` (Cai-Fürer-Immerman), and `had` (Hadamard) families are designed
  to fool *graph* colour refinement. The bipartite Levi structure
  preserves their hardness for the graph-iso baselines but the
  underlying hypergraph reconstruction may collapse the structure that
  made them hard — we are no longer comparing on the same instances.
- **Reviewer optics.** Submitting a hypergraph-iso paper benchmarked on
  classical graph datasets invites the criticism "you tested on graphs,
  not hypergraphs; show that your hypergraph-native step is actually
  doing work." That criticism is fatal at top venues.

**Constraint inherited by next iteration**: the cohort must consist of
**hypergraphs that exist natively as hypergraphs**, not as Levi-graphs
of graphs. Pallini may be used as a **side-channel for the graph-iso
backends' timing baselines** but must not be the primary correctness
cohort.

### 1.3 Why this matters for Tier 5

`docs/PROPOSAL.md` Tier 5 (partition agreement on the 12 HIC datasets
from Feng et al. TPAMI 2024) already operates on real hypergraphs. The
gap is between the empirical Tier 5 setup (no published partition;
ground truth = unanimous backend verdict) and the principled cohort we
need for Tier 1 / Tier 3 correctness (published partition,
oracle-independent).

---

## 2. How we proceeded

### 2.1 Three avenues investigated

**Avenue A — Permutation orbit.** Decision I44 (`docs/PROPOSAL.md`,
2026-06-11) gave us `core.sparse_hypergraph.permute(H, σ)` as the
positive-iso-pair oracle. The σ is the ground-truth bijection,
verifiable independently by `verify_bijection_certificate`. This
eliminates oracle dependence for *positive* (within-class) pairs
entirely.

**Avenue B — Constructive catalogs.** Published enumerations of
combinatorial designs with proven iso-class membership:

| Source | What it gives | Native hypergraph? |
|---|---|---|
| Mathon, Phelps, Rosa 1983 — *Small Steiner Triple Systems and Their Properties* (Ars Combinatoria 15: 3-110) | All STS(v) for v ≤ 15 with explicit blocks and proofs of non-iso | **Yes** — STSs are 3-uniform hypergraphs |
| Kaski & Östergård 2004 — *The Steiner triple systems of order 19* (Math. Comp. 73: 2075-2092) | 11,084,874 non-iso STS(19) | **Yes** |
| Heinlein 2023 — arXiv:2303.01207 | Updated STS classifications | **Yes** |
| Colbourn & Dinitz 2007 — *Handbook of Combinatorial Designs*, 2nd ed., CRC Press | Comprehensive catalog: BIBDs, t-designs, resolvable designs, Latin squares, affine/projective planes | **Yes — these are all hypergraphs** |
| Payne & Thas 2009 — *Finite Generalized Quadrangles*, EMS | All small GQ(s,t) with explicit incidence | **Yes** — GQs are point-line hypergraphs |
| McKay's catalog at `users.cecs.anu.edu.au/~bdm/data/` | Listings include some incidence designs alongside graphs | Mixed — must filter |

**Avenue C — Cayley hypergraph construction.** For high-symmetry stress
tests: given a finite group G and a generating subset S ⊆ G of size
≥ 3, the Cayley hypergraph has vertex set G and hyperedge
`{g·s : s ∈ S}` per g. Non-iso Cayley hypergraphs from non-isomorphic
groups (or non-equivalent generating sets) give a parametric family
with combinatorially-proven non-iso. Reference: Lauri & Scapellato
2003, *Topics in Graph Automorphisms and Reconstruction*, LMS LNS 246.

**Avenue D (rejected as primary)** — pallini.di.uniroma1.it.
See §1.2.

### 2.2 What was implemented so far

Phase 3 added two named designs to `tests/conftest.py` and to
`isalhg.datasets.synthetic.exhaustive_small._large_named_designs`:
- `sts_13_pair` — two non-iso STS(13) via cyclic difference sets
  `{0, 1, 4}` and `{0, 1, 6}` over `Z/13Z`. Non-iso is verified
  empirically against pynauty but is also established by the
  Mendelsohn-Mathon classification (Heinlein 2023 gives a modern
  treatment).
- `gq_2_2_doily` — the symplectic W(2) realisation of GQ(2,2): 15
  points, 15 lines (Payne & Thas §1.2).

Phase 3.5 (queued in `docs/DEVELOPMENT.md`) will add the Feng et al.
TPAMI 2024 Fig. 3 HG WL collision pair and the Zhang et al. ICML 2025
Fig. 3(a)/(b) k-GWL pairs — sources are PDFs in `docs/`. Feng's figure
is a raster image (`figs/alg_failed.jpg` per arXiv source); exact
vertex-to-blob assignments require either author contact, manual
visual reconstruction with high-confidence flag, or a re-render at
higher DPI.

### 2.3 Subagent findings (2026-06-14)

A literature-search subagent confirmed pallini hosts ~1,600 graphs
across 25+ families, *all undirected simple graphs, no per-instance
iso-class labels, no native hypergraphs*. The families it serves
(`cfi`, `mz`, `had`, `paley`, `pg`, `pp`, `sts`, `ag`, `latin`,
`ranreg`, `tran`) are timing-stress instances for canonical-labelling
benchmarks, not pairwise-iso fixtures. Useful as a side-channel for
**graph-iso baselines' timing comparison only** (which we are not
running — IsalHG vs pynauty/bliss/Traces, all going through the same
Levi reduction internally, would compare canonicalisation cost on the
*bipartite Levi graphs* of these instances, which is a measurement of
the baselines, not of IsalHG).

---

## 3. Current state of the search

### 3.1 What we have

- `permute(H, σ)` (decision I44) — exhaustive positive-pair oracle.
- Two non-iso STS(13) via cyclic construction.
- GQ(2,2) doily.
- Fano plane STS(7) and STS(9) = AG(2,3) (Phase-1 conftest fixtures).
- Tier 5 plan with the 12 HIC datasets (queued, Phase 6).

### 3.2 What is missing

1. **A `CatalogDataset` class** wrapping handpicked, literature-cited
   non-iso hypergraph cohorts. Skeleton:
   - Subclass `HypergraphDataset` per `docs/CODE_DESIGN.md` §2.2.
   - One concrete subclass per literature source (`MathonPhelpsRosaSTS`,
     `ColbournDinitzBIBD`, `PayneThasGQ`, `KaskiOstergardSTS19`).
   - Each item carries a non-trivial `iso_class` proven by the source
     publication, NOT by an iso oracle.
   - Register in `datasets/registry.py` under names like
     `catalog_mphr_sts15`, `catalog_payne_thas_gq`.

2. **A `PermutationOrbitDataset`** for within-class pairs.
   - Takes a base hypergraph (or a list of base hypergraphs) and
     `permutations_per_class`.
   - Emits canonical + N-1 permutations, all with the same `iso_class`,
     all with the σ permutation in `extra["sigma"]` so the verifier can
     check.
   - Replaces the within-class half of `ExhaustiveSmallHypergraphs`
     (the enumeration half stays as a separate dataset class).
   - Does **not** require any backend at construction.

3. **A `MultiOracleEnumeratedDataset`** for fallback enumeration where
   no published catalog exists.
   - Same itertools enumeration as today.
   - Dedup uses TWO independent backends (`pynauty_levi` + `bliss_levi`)
     and asserts agreement. Disagreement → raise (not silently pick
     one). This addresses item #2 from the self-review for the
     unavoidable-enumeration case.

4. **The HG-CFI (hypergraph Cai-Fürer-Immerman) construction** — open
   research question #5 in `docs/DEVELOPMENT.md`. This is the
   hypergraph analogue of the standard graph-iso hardness benchmark. It
   is required for Theorem 2 falsification but is not yet built. A
   working HG-CFI would give us a parametric non-iso family that side-
   steps both oracle dependence (non-iso is by construction) and
   graph-vs-hypergraph asymmetry (it lives natively as hypergraphs).

5. **Feng / Zhang figure extraction.** Phase 3.5 work. Three viable
   paths:
   - Manual visual reconstruction from the rendered PDF with the
     `read-paper` agent (current uncertainty: vertex labels not legible
     at PDF render resolution).
   - Re-render the figure at higher DPI from arXiv LaTeX source.
     Confirmed by a subagent that Feng's figure is `figs/alg_failed.jpg`
     — a raster image, not TikZ. Zhang's source has not been checked.
   - Author contact / replication via independent construction (Feng's
     pair has a structural description in the paper text — both
     hypergraphs are 2-regular 3-uniform on 6 vertices with 4 edges,
     and one is linear / the other is not).

### 3.3 What the next iteration should produce

A concrete deliverable proposal:

1. Write a 1-page design note as `docs/research/cohort_design.md`
   selecting Avenue A + Avenue B as the primary cohort and explicitly
   documenting why Avenue D (pallini) is not used.
2. Implement `PermutationOrbitDataset` + `MathonPhelpsRosaSTSDataset`
   (minimum viable catalog dataset).
3. Refactor the Phase-3 `tier1_correctness.yaml` to use these two
   datasets instead of `exhaustive_small` for the FP=FN=0 acceptance.
   Keep `exhaustive_small` as a stress dataset for coverage but
   downgrade it to "multi-oracle agreement" mode.
4. Plan integration of HG-CFI (open question #5) — owner is the PI
   (companion paper task C14). Until that ships, we have a structural
   gap in the cross-class cohort that cannot be closed by catalog
   alone.

### 3.4 Constraint reminders for the next agent

- **Hypergraphs only.** No graph datasets at the cohort level. Pallini
  may appear in a side-channel comparison of baseline timing, not as
  Tier 1-3 cohort.
- **Published iso-class proofs.** Each cross-class fixture must cite a
  publication that proves non-iso, not "we asked nauty".
- **Permute-witness for positive pairs.** Avenue A is essentially free
  and removes all oracle dependence from the iso direction. Use it.
- **Follow `docs/CODE_DESIGN.md` §2.2 ABC contract.** New datasets
  subclass `HypergraphDataset`, register in `datasets/registry.py`, ship
  unit + integration tests, declare `LabelVocabulary.trivial()` until
  Phase 6 (HIC atlas) needs labelled vocabularies.

---

## 4. Open questions for the PI

- Q1. Is the HG-CFI construction (open question #5) on the roadmap
  before Phase 5, or after? If before, it should be paired with this
  cohort work because HG-CFI is the only known parametric non-iso
  hypergraph family at scale.
- Q2. Are the Mathon-Phelps-Rosa 1983 block lists worth manually
  transcribing into a Python module, or do we want a downloader that
  fetches them from `users.cecs.anu.edu.au/~bdm/data/`? The transcribed
  approach is auditable and reproducible offline; the downloader
  approach is sensitive to URL stability.
- Q3. Tier 5 currently uses "unanimous backend verdict" as ground truth.
  Should we keep that, or switch to "Mathon-Phelps-Rosa-style published
  catalog for the small HIC subsets" once that catalog exists in our
  codebase? The latter is stronger but only applies where a catalog is
  available.
