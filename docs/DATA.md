# Data — benchmark cohort for IsalHG

**Status.** Authoritative as of 2026-06-16. Supersedes the cohort fragments
scattered in `PROPOSAL.md` §"Tier 1 — Correctness", §"Tier 4 — Real-world
structural calibration", §"Tier 5 — Exact iso-equivalence-class atlas",
and the resolution narrative in `docs/research/HANDOFF_hypergraph_benchmarks.md`.

**Scope.** This document is the single source of truth for *what data
IsalHG runs on, where to get it, what the ground truth is, and which prior
paper used it.* Code-design decisions live in `docs/CODE_DESIGN.md`;
validation methodology lives in `docs/PROPOSAL.md`; this file covers the
data layer end-to-end.

---

## 1. Framing — what IsalHG is benchmarking against

IsalHG is **a drop-in alternative to nauty / Traces / bliss** for canonical
labelling and isomorphism decision on hypergraphs. The competitors' route
is `H → B(H) → nauty/Traces/bliss canonical permutation`; IsalHG's route
is `H → greedy H2S → canonical string w*(H)`. The two routes solve the
same problem; the comparison is **time, memory, and partition agreement**,
not "who is more correct."

This reframing is the load-bearing assumption of the cohort design:

1. **Prior hypergraph-iso work treats nauty as ground truth.** Every
   classification of Steiner triple systems since Kaski-Östergård 2004
   uses nauty for isomorph rejection; every hypergraph kernel paper since
   Bai et al. 2014 verifies its WL collisions against nauty on `B(H)`;
   the design-theory community (Colbourn-Dinitz 2007 handbook,
   Payne-Thas 2009 for generalized quadrangles) operates against nauty
   end-to-end. **There is no published dataset whose ground truth is
   independent of nauty.** Demanding one would be holding IsalHG to a
   higher standard than the entire prior field, which is not the right
   competitive frame.
2. **Therefore "we agree with nauty" is a sufficient correctness story.**
   Tier 1 cross-backend partition agreement (Phase 3 / Phase 4 closing
   tables: 0 FP, 0 FN across `isalhg`, `pynauty_levi`, `bliss_levi`,
   `traces_levi`) is the operational form of this. Disagreement, when
   it happens, is either a bug in one backend (E23) or a Theorem-2
   counterexample (F28) — both of which are publishable.
3. **The competitive axis is runtime + memory + fingerprint compactness,
   not exactness.** All four exact methods are exact by their own
   construction proofs (Berge 1973 for the Levi reduction, McKay-Piperno
   2014 for nauty/Traces, Junttila-Kaski 2007 for bliss, the open
   Conjecture for IsalHG). The empirical question is which engine wins on
   wall-clock and `max_rss` per regime.

Under this framing, the cohort design has two halves:

| Half | Purpose | What it covers |
|---|---|---|
| **A. Downloadable real data** | "We benchmark on the same data prior work uses, so reviewers cannot ask 'where are the real datasets?'" | STS catalogs (combinatorics community), HIC-12 (ML community), ARB (network-science community), LLM4Hypergraph (the only existing iso-recognition corpus, ICLR 2025) |
| **B. Synthetic generators** | "We control distribution, scale, and ground truth by construction; we can do Tier-2 scaling sweeps and Tier-3 hardness families that no fixed corpus delivers" | XGI Erdős-Rényi + Chung-Lu (the de-facto random-hypergraph generators), Hypergraphx auxiliaries, design-theory constructions via SageMath, our `permute()` positive-pair oracle |

The two halves complement each other: real data establishes external
validity, synthetic data establishes coverage. Neither alone is enough.

---

## 2. Cohort A — downloadable real data

Ten sources, ordered by how the IsalHG paper uses them (Tier 1 first).

### 2.1 Kaski-Östergård STS catalogs

**What.** Plaintext files listing every non-isomorphic Steiner triple
system of orders 3, 7, 9, 13, 15. STS(v) is a 3-uniform hypergraph on
`v` vertices in which every pair of vertices lies in exactly one triple.

**Source.** `https://pottonen.kapsi.fi/sts19/` — small systems are
plaintext ASCII (one system per line, triples as 3-character groups over
`{a..o}`). Five files: `sts3.txt` (1 system), `sts7.txt` (Fano, 1
system), `sts9.txt` (1 system), `sts13.txt` (2 systems), `sts15.txt`
(80 systems). Total: 85 non-iso classes, no external tooling required.

**Ground truth.** Exhaustive classification by Mathon, Phelps & Rosa
1983 (STS(13), STS(15)) and verified by nauty-based isomorph rejection
in Kaski-Östergård 2006 monograph. The classification of STS(13) into
exactly 2 non-iso classes and STS(15) into exactly 80 non-iso classes is
mathematical fact, not an empirical artifact.

**Companion data.** `1k_sample`, `1M_sample`, `10M_sample` for STS(19)
(custom compressed binary, requires building the `stsc` C decompressor
shipped on the same page). Full enumeration (`sts19-01` … `sts19-88`)
is ~39 GB. STS(21) absent — Heinlein 2023 reports the count
(14,796,207,517,873,771 classes) but the catalog has not been released
publicly.

**License.** No explicit open license. Citation request: Kaski, P.,
Östergård, P.R.J., Pottonen, O. & Kiviluoto, L. (2009) "A Catalogue of
the Steiner Triple Systems of Order 19," *Bull. Inst. Comb. Appl.* 57:
35–41. We treat the data as academic-use; the paper cites the catalog.

**Role in IsalHG.** Tier 1 primary cross-class fixtures.
`sts13.txt` (2 classes) and `sts15.txt` (80 classes) load directly into
Python and become a `KaskiOstergardSTSDataset` (subclass of
`HypergraphDataset` per `CODE_DESIGN.md` §2.2). This replaces our
current cyclic-construction `sts_13_pair` (which used starter blocks
`{0,1,4}` and `{0,1,6}` over Z/13Z to materialise the 2 STS(13) iso
classes empirically) with the canonical published source. The STS(19)
`1k_sample` is deferred — it requires the `stsc` build and the
fingerprint cost on a single STS(19) is already several seconds under
the current bounded-backtracking IsalHG (open question #1 in
`DEVELOPMENT.md`).

**Prior literature using it.** Kaski-Östergård 2004 (*Math. Comp.*
73(248):2075-2092), Kaski-Östergård 2006 monograph, Heinlein 2023
(*J. Comb. Designs* 31(10):532-567, arXiv:2303.01207), and every
subsequent design-theory enumeration. The catalog is the field's
classification standard.

### 2.2 Generalized quadrangles GQ(2,2) "doily"

**What.** Point-line incidence hypergraph of the symplectic generalized
quadrangle W(2): 15 points, 15 lines, every line has 3 points, every
point lies on 3 lines, `|Aut| = 720`.

**Source.** SageMath `sage.combinat.designs.gen_quadrangles_with_spread.GeneralisedQuadrangle*`,
or hand-coded from Payne-Thas 2009 §1.2 (~30 lines of incidence data).
We currently ship the hand-coded version as `gq_2_2_doily` in
`tests/conftest.py` and `synthetic.exhaustive_small._large_named_designs`.

**Ground truth.** By mathematical construction (the symplectic W(2)
realisation is unique up to isomorphism).

**Role in IsalHG.** Tier 1 named-design fixture (large-Aut stress case).
Already shipped.

**Prior literature using it.** Payne-Thas 2009 *Finite Generalized
Quadrangles* (2nd ed., EMS, DOI:10.4171/066) is the canonical reference;
GAP+FinInG ships the same realisation.

### 2.3 Fano plane STS(7) and STS(9) = AG(2,3)

**What.** STS(7) (Fano plane = PG(2,2), 7 points, 7 lines,
`|Aut| = 168`) and STS(9) (= AG(2,3), 9 points, 12 lines,
`|Aut| = 432`). Both unique up to iso.

**Source.** Already shipped as `tests/conftest.py` fixtures (Phase 1).
Both are also one-line entries in `sts7.txt` and `sts9.txt` from
Cohort 2.1; on adoption of the Kaski-Östergård parser, these will fold
into the same dataset class.

**Role in IsalHG.** Tier 1 baseline correctness anchor.

**Prior literature using it.** The Fano plane is the most-cited
combinatorial design in the literature; STS(9) is the smallest
non-trivial STS. Both appear in every design-theory textbook.

### 2.4 SageMath designs library

**What.** Comprehensive library of combinatorial designs accessible
through SageMath: projective planes `PG(2, q)` (`designs.projective_plane(q)`),
balanced incomplete block designs (`designs.balanced_incomplete_block_design`),
Steiner systems of arbitrary order, generalized quadrangles with spread,
Latin squares (`designs.latin_squares`). All exposed through a uniform
`IncidenceStructure` API with `.is_isomorphic()` backed by nauty
internally.

**Source.** SageMath itself (`pip install sagemath` or
`conda install sage`). Not currently installed in the `isalhg` env;
plan is to install in a *sibling* conda env, run a one-time generation
script that dumps each design to JSON, commit the fixtures under
`tests/fixtures/sage_designs/`, and have `hardness.py` load the JSON
files at test time. SageMath thus stays out of IsalHG's runtime
dependency tree.

**Ground truth.** By mathematical construction; cross-checked with
Sage's internal nauty-backed `is_isomorphic`.

**Role in IsalHG.** Tier 3 hardness families (PG(2, q), large-Aut STS,
GQ(2,4) and GQ(3,5), Latin squares of given autotopy). This is the
single largest piece of cohort engineering currently outstanding — see
§5 below for the gap analysis.

**Prior literature using it.** Colbourn & Dinitz 2007 *Handbook of
Combinatorial Designs* (2nd ed., CRC Press) is the bible; SageMath's
designs module is the most accessible computational entry point.

### 2.5 HIC's 12 real-world hypergraph datasets

**What.** 12 datasets bundled with the HIC GitHub repo:
- **RHG-10, RHG-3, RHG-Table, RHG-Pyramid** — synthetic random
  hypergraphs in four parameter regimes.
- **IMDB-Dir-Form, IMDB-Dir-Genre, IMDB-Dir-Genre-M** — actor-cast
  hypergraphs where vertex labels are directors and hyperedge labels are
  movie metadata.
- **IMDB-Wri-Form, IMDB-Wri-Genre, IMDB-Wri-Genre-M** — same with
  writers.
- **Steam-Player** — gaming-session co-purchase hypergraphs.
- **Twitter-Friend** — social hypergraphs from follower groups.

All 12 are labelled (vertex labels and hyperedge labels carry domain
semantics: actor IDs, movie genres, game tags, Twitter handles).

**Source.** github.com/iMoonLab/HIC (Feng et al. 2024). Datasets ship as
serialised hypergraph files alongside the HIC reference implementation.

**Ground truth.** None published as iso-class partitions. The downstream
task is hypergraph classification with class labels; iso-class
membership is not annotated. We therefore compute the partition with
each backend (IsalHG, pynauty_levi, bliss_levi, traces_levi) and assert
agreement across all four. Disagreement is either a bug or a Theorem-2
counterexample.

**License.** Apache 2.0 (per HIC repo).

**Role in IsalHG.** Tier 5 partition agreement (the real-world
deduplication atlas). The acceptance criterion is identical partitions
across all four backends on every dataset; the headline metric is
geometric-mean speedup over best-of-`{pynauty, Traces, bliss}` on at
least 4 of 12 datasets.

**Prior literature using it.** Feng et al. 2024 (TPAMI 46(5):3880-3893,
DOI:10.1109/TPAMI.2024.3353199), Zhang et al. 2025 (ICML, PMLR v267,
OpenReview pD5oklKrDV) — both for classification accuracy, not iso
partition. We are the first to compute and report the iso partition on
these 12 datasets.

### 2.6 LLM4Hypergraph iso-recognition corpus (Feng et al. ICLR 2025)

**What.** A synthetic iso-recognition benchmark distributed alongside
the LLM4Hypergraph paper. Pairs of small hypergraphs (n ∈ {5–9, 10–14,
15–19}, edge count Uniform(0.2n, 1.5n), arity geometric) labelled
`Yes`/`No` for "are these two isomorphic?". Generator path:
positive pairs via `HyperGraph.shuffleNode()` (random vertex
permutation, semantically identical to our `core.permute(H, σ)`);
negative pairs via resampling with matched arity sequence, then
filtered for accidental iso.

**Source.** github.com/iMoonLab/LLM4Hypergraph (Apache 2.0). Files:
`hypergraph_generator.py`, `hypergraph_task.py` (class
`IsomorphismRecognition`, line 1286), `hyper_graph.py::shuffleNode`
(lines 90-103), `RHG-data/` (four pre-computed base hypergraph `.txt`
files). Default seed: 1234.

**Ground truth.** Was *intended* to be the `test_isomo.HGSCKernel`
filter on resampled negatives (line 1327), but **`test_isomo.py` is
missing from the public repo**. The generator crashes as-shipped. The
straightforward fix is to substitute `PynautyLeviBackend.are_isomorphic()`
for the missing oracle — which is exactly what the three-way comparison
needs anyway.

**Role in IsalHG.** Tier 1c three-way comparison cohort. Concretely:

1. Vendor LLM4Hypergraph as a git submodule or copy under
   `third_party/llm4hypergraph/` (license-compatible).
2. Patch the missing oracle in `IsomorphismRecognition.prepare_examples_dict`
   to call `PynautyLeviBackend.are_isomorphic()`.
3. Regenerate the iso-recognition cohort with `--random_seed=1234`,
   producing pairs with pynauty-certified ground truth.
4. Define `LLM4HypergraphIsoRecognition` as a
   `HypergraphDataset` subclass (under `datasets/llm4hypergraph.py`).
5. Run IsalHG via the standard `PairwiseIsoProtocol` and report
   verdict-by-verdict.
6. The LLM verdicts (GPT-4, Claude, etc.) reported in Feng et al. ICLR
   2025 supplementary give the third column. No re-running of LLMs
   required for the headline number.

The resulting table is (LLM-from-paper) × (pynauty = ground truth) ×
(IsalHG) on the same cohort. This is the only published hypergraph
iso-recognition benchmark in the field, so adopting it is the cheapest
way to obtain external validity outside the combinatorics tradition.

**Prior literature using it.** Feng et al. 2025 *"Beyond Graphs: Can
Large Language Models Comprehend Hypergraphs?"* (ICLR, arXiv:2410.10083).
No follow-up papers known as of 2026-06-16; we are likely the first to
treat the corpus as an exact iso-decision benchmark.

### 2.7 ARB collection (Benson et al.)

**What.** Austin Benson's collection of real-world higher-order
networks. ~19 datasets including `contact-high-school`,
`congress-bills`, `email-Enron`, `NDC-substances`, `DAWN`, and others.
Hyperedges are maximal simplices of simplicial complexes (e.g.
co-authorship groups, contact events, voting blocs); per-vertex metadata
includes domain labels (political affiliation, role).

**Source.** `https://www.cs.cornell.edu/~arb/data/`. Per-dataset
folders ship raw edge lists and metadata.

**Ground truth.** None as iso partitions. Used here for **structural
distribution** only (arity histograms, degree distributions, density).

**Role in IsalHG.** Tier 4 structural calibration. We pass the ARB
distributions through our adapter, compute arity/degree histograms, and
calibrate the Tier 2 sweep ranges (`n`, `m/n`, `r`) so the synthetic
random hypergraphs actually cover the realistic regime. No iso testing
on ARB itself.

**Prior literature using it.** Benson, Abebe, Schaub, Jadbabaie &
Kleinberg 2018 *"Simplicial Closure and Higher-Order Link Prediction"*
(PNAS 115(48):E11221-E11230, arXiv:1802.06916). Canonical citation for
the corpus. Subsequently the de facto real-world hypergraph reference
in the network-science community.

### 2.8 XGI-DATA loaders

**What.** XGI's `xgi-data` registry: a curated set of real-world
hypergraph datasets exposed through a single `xgi.load_xgi_data(name)`
API. Includes `email-Enron`, `contact-high-school`,
`contact-primary-school`, `congress-bills`, `senate-bills`,
`senate-committees`, `tags-stack-overflow`, several more. Overlaps with
ARB but adds non-ARB sources.

**Source.** PyPI `xgi` (already installed in the `isalhg` conda env);
data fetched on first call.

**Ground truth.** Same as ARB — none as iso partitions. Used for
structural distribution.

**Role in IsalHG.** Tier 4 structural calibration alongside ARB.
Cross-comparison of the two sources lets us detect whether either is
systematically biased in its distribution coverage.

**Prior literature using it.** Landry, Lucas, Iacopini, Petri,
Schwarze, Patania & Torres 2023 *"XGI: A Python package for higher-order
interaction networks"* (JOSS 8(85):5162). The XGI library itself is the
most-used hypergraph manipulation library in network science as of
2026; reviewers will expect IsalHG to demonstrate compatibility.

### 2.9 Hypergraphx datasets

**What.** Lotito et al.'s curated multi-domain corpus:
social, biological, collaboration, temporal, multiplex hypergraphs.
Extended catalogue documented in arXiv:2605.18166.

**Source.** github.com/HGX-Team/hypergraphx (PyPI `hypergraphx`,
installed in the `isalhg` env).

**Ground truth.** None as iso partitions.

**Role in IsalHG.** Tier 4 structural calibration (third source, after
ARB and XGI-DATA). Hypergraphx's strong suit is multiplex and temporal
hypergraphs that ARB and XGI-DATA underweight; using all three together
diversifies the calibration.

**Prior literature using it.** Lotito, Contisciani, De Bacco et al.
2023 *"Hypergraphx: A Library for Higher-Order Network Analysis"*
(*Journal of Complex Networks* 11(3):cnad019, arXiv:2303.15356).

### 2.10 Yaveroglu PPI hypergraphlets

**What.** 15 protein-protein interaction networks treated as
hypergraphs, plus an enumeration of the 6 non-iso 3-node hypergraphlets
used as a kernel basis.

**Source.** Supplementary of Yaveroglu et al. 2021 *"Classification in
Biological Networks with Hypergraphlet Kernels"* (Bioinformatics
37(7):1000-1008, arXiv:1703.04823).

**Ground truth.** The 6 hypergraphlet iso classes are an implicit
partition (by enumeration). Per-PPI graphs carry biological node labels
but no iso ground truth on whole hypergraphs.

**Role in IsalHG.** Tier 1 micro-fixtures (6 small iso classes
constructively enumerated). Optional Tier-4-style calibration on the
PPI networks themselves (15 instances, small, easy).

**Prior literature using it.** Yaveroglu et al. 2021; one of the few
hypergraph papers to compute explicit iso classes (even if downstream
metric is classification accuracy).

---

## 3. Cohort B — synthetic generators

Eleven generator paths, ordered by what's already implemented vs what
needs to be added.

### 3.1 `core.permute(H, σ)` — positive-pair oracle

**What.** A stdlib-only free function on `SparseHypergraph` (decision
I44): given a hypergraph `H` and a permutation `σ ∈ Sym(V)`, returns
`σ(H)`. The known `σ` is the bijection-certificate ground truth (E24).

**Where.** `src/isalhg/core/sparse_hypergraph.py::permute`. Already
shipped (Phase 1).

**Role.** Primary source of positive iso pairs across all tiers. Used
in Hypothesis property tests and in dataset `__iter__` methods that
need to generate `permutations_per_class` instances of each iso class.

### 3.2 XGI uniform Erdős-Rényi

**What.** `xgi.generators.uniform.uniform_erdos_renyi_hypergraph(n, m, p, p_type='prob', multiedges=False, seed=None)`.
Generates a uniform `r`-uniform random hypergraph with `n` vertices and
`m` hyperedges, each present with probability `p`. Seeded.

**Where.** XGI library (installed). Scaffold subclass
`UniformErdosRenyiHypergraphs` exists in
`src/isalhg/datasets/synthetic/erdos_renyi.py` (52 lines,
`__iter__`/`metadata` currently raise `NotImplementedError`); wiring is
~30 lines.

**Ground truth.** Cross-checked with nauty per pair (decision E23).

**Role.** Tier 2 R2 (sparse, `m/n = 1`) and R3 (medium, `m/n = 5`)
backbone. The headline Tier 2 grid is `n ∈ {50, 100, 250, 500, 1000,
2500}`, `r ∈ {3, 4, 5}`, `m/n ∈ {1, 5, 25}`, 10 seeds per cell.

**Prior literature using it.** Chodrow 2020 *"Configuration Models of
Random Hypergraphs"* (J. Complex Networks 8(3):cnaa018) and every
subsequent XGI-based paper.

### 3.3 XGI Chung-Lu

**What.** `xgi.generators.random.chung_lu_hypergraph(k1, k2, seed=None)`.
Generates a heavy-tailed degree-sequence hypergraph with vertex degree
sequence `k1` and edge size sequence `k2`. Seeded.

**Where.** XGI library. Scaffold subclass `ChungLuHypergraphs` exists
in `src/isalhg/datasets/synthetic/chung_lu.py` (52 lines, same
NotImplementedError status).

**Ground truth.** Same as 3.2 — nauty per pair.

**Role.** Tier 2 R3 (medium/dense heavy-tailed). Most real-world
hypergraphs have power-law degree distributions, so Chung-Lu is the
fairer dense-regime stress test than uniform Erdős-Rényi.

**Prior literature using it.** Chodrow 2020; the de-facto heavy-tailed
hypergraph generator.

### 3.4 XGI secondary generators

**What.** `uniform_hypergraph_configuration_model(k, m, seed)`,
`fast_random_hypergraph(n, ps, order, seed)`, `uniform_HPPM(n, m, k,
epsilon, rho, seed)`, `dcsbm_hypergraph(k1, k2, g1, g2, omega, seed)`.

**Where.** XGI library, currently unused by IsalHG.

**Role.** Tier 2 secondary stress (degree-matched configuration,
planted-partition, degree-corrected SBM). Add when Tier 2 primary
results call for distribution diversification.

### 3.5 Hypergraphx auxiliary generators

**What.** `hypergraphx.generation.random_uniform_hypergraph`,
`random_hypergraph`, `configuration_model`, `directed_configuration_model`,
`scale_free_hypergraph`, `HOADmodel`.

**Where.** Hypergraphx library (installed). Currently unused.

**Role.** Tier 2 extras. The `scale_free_hypergraph` and `HOADmodel`
generators are the two XGI does not ship; useful as a third axis of
distribution coverage.

### 3.6 Cyclic STS construction

**What.** Steiner triple systems over `Z/pZ` with a chosen starter
block `{0, 1, k}` (cyclic difference-set construction). For prime `p ≡ 1
or 3 (mod 6)`, starter `{0, 1, k}` generates an STS(p) when the
corresponding difference set is well-formed.

**Where.** Currently inlined inside `synthetic.exhaustive_small`
(`_large_named_designs`); produces our two STS(13) representatives.

**Role.** Tier 1 historical (will be partly replaced by Cohort A.1 — the
Kaski-Östergård plaintext catalog gives canonical representatives for
STS(13)/15 without our needing to construct them).

### 3.7 Cayley hypergraph from `(G, S)`

**What.** Given a finite group `G` and a generating subset `S ⊆ G`
with `|S| ≥ 3`, the Cayley hypergraph has vertex set `G` and hyperedges
`{g · s : s ∈ S}` for each `g ∈ G`. Non-iso Cayley hypergraphs from
non-isomorphic groups or non-equivalent generating sets give a
parametric family with combinatorially-proven non-iso structure.

**Where.** Not yet implemented. Would live in `synthetic.cayley.py` (~80
lines stdlib + optional pynauty cross-check).

**Role.** Tier 1/3 high-symmetry parametric stress. HANDOFF Avenue C.

**Prior literature.** Lauri & Scapellato 2003 *Topics in Graph
Automorphisms and Reconstruction* (LMS LNS 246).

### 3.8 Random `r`-uniform `d`-regular at threshold

**What.** Rejection sampler on XGI's configuration model: draw a
hypergraph, accept iff every vertex has degree exactly `d`.

**Where.** Not yet implemented; ~50 lines on top of
`xgi.uniform_hypergraph_configuration_model`.

**Role.** Tier 3 family E — the only Tier 3 hardness family runnable
without SageMath or GAP. Graph-iso solvers behave erratically at the
regularity threshold; expected to translate to hypergraphs.

### 3.9 PG(2, q) via SageMath

**What.** Projective plane of order `q`: `q² + q + 1` points,
`q² + q + 1` lines, every line has `q + 1` points, every point on
`q + 1` lines.

**Where.** SageMath `designs.projective_plane(q)`. SageMath not
installed in the IsalHG env; planned workflow is a one-time generation
script in a sibling env that emits JSON fixtures committed under
`tests/fixtures/sage_designs/pg2_q*.json`.

**Role.** Tier 3 family A. The PROPOSAL specifies
`q ∈ {7, 8, 9, 11, 13}`, with `q = 9` including the 4 non-Desarguesian
planes accessible via GAP+FinInG.

### 3.10 Large-Aut STS, GQ(2,4)/(3,5), non-group Latin squares

**What.** Same JSON-fixture workflow as PG(2,q) but for the other Tier 3
families (B/C/D in PROPOSAL §"Tier 3"). GQ(2,4) and GQ(3,5) require GAP
+ FinInG; non-group Latin squares with large autotopy require a
construction + autotopy filter.

**Where.** Not yet implemented; deferred until the SageMath env exists.

**Role.** Tier 3 families B/C/D.

### 3.11 HG-CFI construction

**What.** Hypergraph analogue of the Cai-Fürer-Immerman 1992
construction: a parametric non-iso family that fools `k`-WL on the Levi
bipartite graph. If realised, would give synthetic hard negatives that
match every WL-bounded invariant.

**Where.** **No public implementation exists** (confirmed by
literature search 2026-06-16). Open question #5 in `DEVELOPMENT.md`,
companion paper task C14 in PROPOSAL.

**Role.** Tier 1/3 if realised. Not blocking — the design-theoretic
catalogs (Cohort A.1, A.4) provide the same role at lower coverage.

---

## 4. Implementation status (snapshot 2026-06-16)

| Cohort | Status | Module path / file |
|---|---|---|
| **A.1** Kaski-Östergård STS(13)/15 plaintext | Not yet ported; planned `KaskiOstergardSTSDataset` | `src/isalhg/datasets/catalog/kaski_ostergard.py` |
| **A.1** STS(19) `1k_sample` | Not yet ported; deferred (needs `stsc`) | `src/isalhg/datasets/catalog/kaski_ostergard.py` |
| **A.2** GQ(2,2) doily | **Shipped** (Phase 1) | `tests/conftest.py`, `synthetic.exhaustive_small._large_named_designs` |
| **A.3** Fano, STS(9) | **Shipped** (Phase 1) | `tests/conftest.py` |
| **A.4** SageMath designs | Not yet ported; needs sibling Sage env | `src/isalhg/datasets/catalog/sage_designs.py` (to be created) |
| **A.5** HIC-12 | Scaffold | `src/isalhg/datasets/hic_atlas.py` |
| **A.6** LLM4Hypergraph | Not yet ported; planned `LLM4HypergraphIsoRecognition` | `src/isalhg/datasets/llm4hypergraph.py` (to be created) |
| **A.7** ARB | Scaffold | `src/isalhg/datasets/arb_benson.py` |
| **A.8** XGI-DATA | Scaffold | `src/isalhg/datasets/xgi_loader.py` |
| **A.9** Hypergraphx | Not yet planned | `src/isalhg/datasets/hypergraphx_loader.py` (to be created) |
| **A.10** Yaveroglu hypergraphlets | Not yet planned | `src/isalhg/datasets/catalog/hypergraphlets.py` (to be created) |
| **B.1** `permute(H, σ)` | **Shipped** (Phase 1) | `src/isalhg/core/sparse_hypergraph.py::permute` |
| **B.2** XGI Erdős-Rényi | Scaffold (52 lines, `NotImplementedError`) | `src/isalhg/datasets/synthetic/erdos_renyi.py` |
| **B.3** XGI Chung-Lu | Scaffold (52 lines, `NotImplementedError`) | `src/isalhg/datasets/synthetic/chung_lu.py` |
| **B.4** XGI secondary | Not yet planned | extends `erdos_renyi.py` |
| **B.5** Hypergraphx aux | Not yet planned | new files under `synthetic/` |
| **B.6** Cyclic STS | **Shipped** (Phase 3) | `synthetic.exhaustive_small._large_named_designs` |
| **B.7** Cayley | Not yet planned | `synthetic/cayley.py` (to be created) |
| **B.8** Regular threshold | Not yet planned | `synthetic/hardness.py` |
| **B.9** PG(2, q) via Sage | Not yet ported; needs sibling Sage env | `synthetic/hardness.py` + JSON fixtures |
| **B.10** Sage STS/GQ/Latin | Not yet ported; needs Sage + GAP | `synthetic/hardness.py` + JSON fixtures |
| **B.11** HG-CFI | Open | n/a |

---

## 5. Open gaps and required work

Ordered by priority for the empirical paper:

1. **Wire Tier 2 generators (B.2, B.3).** Estimated 60 lines of code
   across `erdos_renyi.py` and `chung_lu.py`, plus
   `tier2_scaling.yaml`, plus `metrics/runtime.py` and
   `protocols/fingerprint_timing.py`. Single focused implementation
   session. Tier 2 is currently the highest-leverage missing piece
   because the headline competitive number (geometric-mean speedup
   over best-of-Levi at the largest `(n, r, m/n)` cell) lives here.
2. **Port Kaski-Östergård STS catalogs (A.1, plaintext only).**
   Estimated 80 lines (`KaskiOstergardSTSDataset` plus parser for the
   `{a..o}` triple format). Replaces the cyclic-construction STS(13)
   we currently ship with the canonical published source and adds 80
   STS(15) classes as Tier 1 fixtures. No external tooling required.
3. **Port LLM4Hypergraph corpus (A.6) and substitute pynauty oracle.**
   Estimated 200 lines split across vendoring the third-party code,
   patching the missing `HGSCKernel` call, and writing the
   `LLM4HypergraphIsoRecognition` dataset class. Yields the three-way
   (LLM, pynauty, IsalHG) comparison table.
4. **Build SageMath sibling env + JSON fixture pipeline (A.4, B.9, B.10).**
   This is the largest single piece of cohort engineering. Estimated 1
   day for the Sage install + generation script + JSON serialiser, plus
   ad-hoc time per family for hand-checking the dumps against published
   incidence tables. Required for Tier 3.
5. **STS(19) `1k_sample` decompressor wiring (A.1, binary).** Build the
   `stsc` C tool (~10 lines of subprocess shim), parse its decoded
   output. Adds 1000 STS(19) classes to Tier 1/3. Lower priority because
   fingerprint cost on a single STS(19) under current IsalHG is already
   several seconds (open question #1).
6. **Tier 4 calibration loaders (A.7, A.8, A.9).** Three dataset
   classes plus arity/degree histogram code. ~200 lines. Required for
   Tier 4 but not blocking Tier 1/2/3.
7. **Cayley hypergraph generator (B.7).** ~80 lines, optional. Adds a
   parametric Tier 1/3 family on top of the static catalog.
8. **Random regular threshold sampler (B.8).** ~50 lines. The only
   Tier 3 family runnable without SageMath/GAP; ship first to unblock
   partial Tier 3 execution.
9. **HG-CFI construction (B.11).** Research effort, PI-led. Companion
   paper. Not blocking.

The SageMath dependency is the single hardest blocker. Items 1–3, 5–8
can ship without it; only Tier 3 families A/B/C/D wait on item 4.

---

## 6. The paper sentence

The cohort coverage above lets us write the following sentence in the
empirical paper's evaluation section:

> "We benchmark IsalHG across (i) the exhaustive Steiner-triple-system
> catalogs of Kaski & Östergård [2004, 2006] for orders 13, 15, and a
> 1,000-class subsample of order 19; (ii) standard combinatorial designs
> from the SageMath library following Colbourn & Dinitz [2007]
> (projective planes PG(2, q) for q ∈ {7, 8, 9, 11, 13}, generalized
> quadrangles GQ(2, 2) [Payne & Thas 2009], GQ(2, 4), GQ(3, 5),
> large-automorphism Steiner systems, non-group Latin squares); (iii)
> random hypergraphs generated by XGI [Landry et al. 2023] under the
> uniform Erdős-Rényi and Chung-Lu [Chodrow 2020] models across a
> three-dimensional grid (n, r, m/n) with 10 seeds per cell; (iv) the 12
> real-world datasets of Feng et al. [TPAMI 2024] for Tier-5
> cross-backend partition agreement; (v) the ARB collection of Benson et
> al. [2018] and the XGI-DATA registry [Landry et al. 2023] for
> structural calibration of the synthetic sweep; and (vi) the
> iso-recognition corpus of Feng et al. [ICLR 2025] for which we provide
> the first nauty-certified ground-truth oracle, enabling a three-way
> (LLM, nauty, IsalHG) comparison."

This sentence cites the combinatorics canon (Kaski-Östergård,
Colbourn-Dinitz, Payne-Thas), the ML hypergraph canon
(Feng-TPAMI/ICLR, XGI), and the network-science canon (Benson) in one
paragraph. The "first nauty-certified ground-truth oracle" framing on
LLM4Hypergraph turns a known gap in their public release into an IsalHG
contribution.

---

## 7. References (cohort-relevant only)

Cohort sources cited above:

- Kaski, P. & Östergård, P.R.J. (2004). *The Steiner Triple Systems of
  Order 19.* Math. Comp. 73(248):2075-2092. DOI:10.1090/S0025-5718-04-01626-6.
- Kaski, P. & Östergård, P.R.J. (2006). *Classification Algorithms for
  Codes and Designs.* Springer ACM 15. ISBN 3-540-28990-9.
- Kaski, P., Östergård, P.R.J., Pottonen, O. & Kiviluoto, L. (2009).
  *A Catalogue of the Steiner Triple Systems of Order 19.*
  Bull. Inst. Comb. Appl. 57:35-41.
- Heinlein, D. (2023). *Enumerating Steiner Triple Systems.*
  J. Comb. Designs 31(10):532-567. arXiv:2303.01207.
- Mathon, R., Phelps, K.T. & Rosa, A. (1983). *Small Steiner Triple
  Systems and Their Properties.* Ars Combinatoria 15:3-110.
- Colbourn, C.J. & Dinitz, J.H. (2007). *Handbook of Combinatorial
  Designs* (2nd ed.). CRC Press.
- Payne, S.E. & Thas, J.A. (2009). *Finite Generalized Quadrangles*
  (2nd ed.). European Mathematical Society. DOI:10.4171/066.
- Lauri, J. & Scapellato, R. (2003). *Topics in Graph Automorphisms and
  Reconstruction.* LMS LNS 246.
- Feng, Y., Han, J., Ying, S. & Gao, Y. (2024). *Hypergraph Isomorphism
  Computation.* IEEE TPAMI 46(5):3880-3893. DOI:10.1109/TPAMI.2024.3353199.
  arXiv:2307.14394.
- Feng, Y., Yang, C., Hou, X. et al. (2025). *Beyond Graphs: Can Large
  Language Models Comprehend Hypergraphs?* ICLR 2025. arXiv:2410.10083.
- Zhang, D., Zhang, C., Rao, Y., Li, Q. & Zhu, C. (2025). *Improved
  Expressivity of Hypergraph Neural Networks through High-Dimensional
  Generalized Weisfeiler-Leman Algorithms.* ICML 2025. PMLR v267.
  OpenReview pD5oklKrDV.
- Benson, A.R., Abebe, R., Schaub, M.T., Jadbabaie, A. & Kleinberg, J.
  (2018). *Simplicial Closure and Higher-Order Link Prediction.*
  PNAS 115(48):E11221-E11230. arXiv:1802.06916.
- Landry, N.W., Lucas, M., Iacopini, I. et al. (2023). *XGI: A Python
  package for higher-order interaction networks.* JOSS 8(85):5162.
- Lotito, Q.F., Contisciani, M., De Bacco, C. et al. (2023).
  *Hypergraphx: A Library for Higher-Order Network Analysis.*
  J. Complex Networks 11(3):cnad019. arXiv:2303.15356.
- Yaveroglu, O.N. et al. (2021). *Classification in Biological Networks
  with Hypergraphlet Kernels.* Bioinformatics 37(7):1000-1008.
  arXiv:1703.04823.
- Chodrow, P.S. (2020). *Configuration Models of Random Hypergraphs
  and their Applications.* J. Complex Networks 8(3):cnaa018.
  arXiv:1902.09302.
- Bai, L., Ren, P. & Hancock, E.R. (2014). *A Hypergraph Kernel from
  Isomorphism Tests.* ICPR 2014. DOI:10.1109/ICPR.2014.667.
- Martino, A. & Rizzi, A. (2020). *(Hyper)graph Kernels over Simplicial
  Complexes.* Entropy 22(10):1155. DOI:10.3390/e22101155.
- Cai, J.-Y., Fürer, M. & Immerman, N. (1992). *An Optimal Lower Bound
  on the Number of Variables for Graph Identification.* Combinatorica
  12(4):389-410.
