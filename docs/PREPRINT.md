# IsalHG — Preprint Plan

**Status.** Authoritative as of 2026-06-16. This document specifies a
short, single-cohort preprint to be submitted to arXiv ahead of the full
empirical paper. It carves a defensible correctness story out of the
existing implementation without front-running the broader Tier 2-5
validation campaign documented in `docs/PROPOSAL.md`.

**Companion documents.**
- `docs/DATA.md` §2.1 — full cohort narrative (Kaski-Östergård STS
  plaintext catalogs).
- `docs/PROPOSAL.md` — full validation methodology; the preprint scope
  is a strict subset of Tier 1.
- `docs/CODE_DESIGN.md` — module organisation.

---

## 1. Scope and intent

The preprint establishes one claim and one claim only:

> *IsalHG produces canonical strings that distinguish every published
> non-isomorphic Steiner triple system of orders 7, 9, 13, 15 and the
> generalized quadrangle GQ(2, 2), and agrees with the canonical-form
> partitions produced by nauty, Traces, and bliss (each applied to the
> Levi incidence graph) on every pair within the cohort.*

The cohort is the Kaski-Östergård plaintext catalog: 85 published
non-isomorphic Steiner triple system representatives plus the GQ(2, 2)
doily. The partition-agreement test runs across all C(86, 2) = 3,655
unordered pairs (3,160 of them STS(15)/STS(15) hard negatives) plus N
permutation-derived positive copies of each representative.

What the preprint does **not** claim:
- No speedup claim. Per-fingerprint wall-clock and peak resident-set
  size are reported alongside the correctness table for transparency,
  but the preprint makes no comparative runtime statement. Runtime
  characterisation is reserved for the full empirical paper.
- No real-world deduplication claim. Tier 5 (HIC-12 partition
  agreement) is out of scope.
- No expressiveness claim against Weisfeiler-Leman variants. The Feng
  Fig. 3 and Zhang Fig. 3 fixtures (PROPOSAL Tier 1 acceptance criteria
  5-7) are out of scope until Phase 3.5 extracts the explicit edge
  lists.
- No three-way LLM comparison. The LLM4Hypergraph corpus (decision I49)
  is reserved for the full empirical paper.

The preprint's purpose is to plant a flag on the canonical-string
formulation and on the partition-agreement protocol while the wider
empirical campaign continues.

---

## 2. Title and abstract sketch

**Working title.** *IsalHG: A Native Canonical-String Algorithm for
Hypergraph Isomorphism — Correctness Validation on the Steiner Triple
System Catalog.*

**Abstract (≤ 200 words, draft).**

We introduce IsalHG, an exact native canonical-string algorithm for
hypergraph isomorphism testing. Where established hypergraph
isomorphism pipelines reduce the input hypergraph to the Levi
incidence bipartite graph and invoke a graph-isomorphism engine
(nauty, Traces, bliss), IsalHG operates on the hypergraph directly
through a compact instruction alphabet executed against a
circular-doubly-linked-list virtual machine. The canonical string is
the lexicographically-minimal greedy hypergraph-to-string encoding
seeded from the vertex of maximum structural tuple. We validate
IsalHG against the full plaintext Steiner triple system catalog of
Kaski and Östergård (orders 7, 9, 13, 15) and the generalized
quadrangle GQ(2, 2). On all 85 published non-isomorphic Steiner
representatives plus GQ(2, 2), IsalHG's canonical-string partition
agrees with the canonical-form partitions of nauty, Traces, and bliss
on every pair, including the 3,160 STS(15) hard negatives matched on
arity, regularity, and degree sequence. We further verify on N
random vertex permutations per representative that
`canonical(H) = canonical(π(H))`. The agreement establishes the
canonical-string framework as a correctness-preserving alternative to
the Levi reduction; runtime and scaling analyses are reserved for
subsequent work.

---

## 3. Cohort

Five sources, all from `https://pottonen.kapsi.fi/sts19/` plus one
hand-coded design. Total 86 representatives, 3,655 unordered pairs.

| Source | Order | Reps | Hard negatives (within-source pairs) | Provenance |
|---|---|---|---|---|
| `sts7.txt` | 7 (Fano = PG(2,2)) | 1 | 0 | classical, |Aut|=168 |
| `sts9.txt` | 9 (AG(2,3)) | 1 | 0 | classical, |Aut|=432 |
| `sts13.txt` | 13 | 2 | 1 | Mathon-Phelps-Rosa 1983 |
| `sts15.txt` | 15 | 80 | 3,160 | Mathon-Phelps-Rosa 1983 |
| Payne-Thas §1.2 | GQ(2,2) doily | 1 | 0 | |Aut|=720 |

Cross-source pairs (e.g. STS(13) vs STS(15)) are trivially non-iso by
order mismatch and do not load-bear the headline number; they are
included for completeness. The 3,160 STS(15)/STS(15) pairs are the
load-bearing negatives because every Steiner triple system of order 15
is 7-regular with 35 triples — every easy invariant (degree sequence,
edge-size distribution, density) matches across all 80 representatives,
so the partition test is forced down to genuine iso-level structure.

Positive pairs come from `core.permute(H, σ)`: for each representative
H we draw N permutations σ ∈ S_{|V|} under a pinned RNG, materialise
`σ(H)`, and emit the pair `(H, σ(H))` with σ as the bijection
certificate. Default `N = 100` per representative gives 8,600 positive
pairs across the cohort. The bijection certificate is independently
verified by `verify_bijection_certificate`
(`isalhg.metrics.correctness`).

**Reproducibility.** The five `sts*.txt` files are committed under
`tests/fixtures/kaski_ostergard/` with their MD5 checksums against the
upstream catalog as of the cohort-freeze date. GQ(2,2) is hand-coded
from Payne-Thas 2009 §1.2 in
`synthetic.exhaustive_small._large_named_designs`. The full cohort
regenerates from a single deterministic call to
`KaskiOstergardSTSDataset.seed(42)` plus the existing GQ(2,2) fixture.

---

## 4. Methods

### 4.1 Backends

Four backends, all wired through the `IsoBackend` ABC
(`docs/CODE_DESIGN.md` §2.1):

- `isalhg` — IsalHG canonical string via `core.canonical` +
  `algorithms.greedy_min`.
- `pynauty_levi` — nauty 2.8.8 via the `pynauty` 2.8.8.1 Python
  binding, applied to the 2-coloured Levi incidence graph (decision
  I47).
- `bliss_levi` — bliss 0.77 via `python-igraph`'s
  `canonical_permutation` / `isomorphic_bliss` on the same Levi graph.
- `traces_levi` — Traces via subprocess to the `dreadnaut` CLI shipped
  with the `nauty` 2.9 conda-forge package, parsing the canonical `b6`
  output line.

All four implement `fingerprint(H) -> bytes` and
`are_isomorphic(H1, H2) -> bool`. The IsalHG canonical string is a
sequence of `Sigma_HG` tokens (decision I46) serialised to a
self-delimiting bracketed form; the three Levi backends return their
respective canonical graph-permutation labels.

### 4.2 Protocol

The `PairwiseIsoProtocol` (`isalhg.protocols.pairwise_iso`) drives the
matrix `Backend × Pair`. For each backend M and each pair
`(H_1, H_2)`:

1. Compute `fp_M(H_1)` and `fp_M(H_2)`.
2. Verdict: `iso_M(H_1, H_2) := (fp_M(H_1) == fp_M(H_2))`.
3. Compare to ground truth: positive pairs from `permute()` carry the
   ground truth label `True` (with σ as bijection certificate);
   negative pairs from within-source distinct lines carry ground truth
   `False` (by published classification).
4. Tally FP (M says iso, ground truth says non-iso) and FN (reverse).

The headline acceptance condition is `FP_M = FN_M = 0` for all four
backends M ∈ {isalhg, pynauty_levi, bliss_levi, traces_levi}.

### 4.3 Bijection-certificate verification

For backends that emit an explicit bijection (`pynauty_levi`,
`bliss_levi`), the certificate π : V(H_1) → V(H_2) is verified
edge-preserving by `verify_bijection_certificate`
(`isalhg.metrics.correctness`). Verification failures are reported
separately from FP/FN — a backend that produces a correct verdict but
an incorrect certificate has a bug worth flagging. Traces and IsalHG
do not currently emit bijection certificates and are excluded from
this sub-table.

### 4.4 Runtime and memory transparency reporting

Per-fingerprint wall-clock (`time.perf_counter` median over 10
repeats) and peak resident-set size
(`resource.getrusage(RUSAGE_SELF).ru_maxrss` delta) are recorded for
every (backend, representative) pair. Numbers appear in the
supplementary as a transparency artifact; the main text states that
comparative runtime characterisation is reserved for subsequent work.

---

## 5. Headline deliverable

A single 4-row table in the main text:

| Backend | Positive pairs (TP / total) | Negative pairs (TN / total) | FP | FN | Bijection violations |
|---|---|---|---|---|---|
| `isalhg` | 8,600 / 8,600 | 3,160 / 3,160 | 0 | 0 | n/a |
| `pynauty_levi` | 8,600 / 8,600 | 3,160 / 3,160 | 0 | 0 | 0 / 8,600 |
| `bliss_levi` | 8,600 / 8,600 | 3,160 / 3,160 | 0 | 0 | 0 / 8,600 |
| `traces_levi` | 8,600 / 8,600 | 3,160 / 3,160 | 0 | 0 | n/a |

A second supplementary table reports per-(backend, representative)
fingerprint wall-clock and peak RSS, with no comparative narrative.

A third supplementary appendix lists the MD5 checksums of the
`sts*.txt` files at the cohort-freeze date and the random-seed values
used for the permutation oracle.

The preprint is publishable iff this table populates with FP = FN = 0
across all four backends on the full cohort.

---

## 6. Section structure (target: 8 pages two-column, or 12 single-column)

1. **Introduction** (~1 page). Hypergraph isomorphism, the Levi
   reduction, the gap that motivates a native algorithm. The
   preprint's single claim.
2. **The IsalHG canonical string** (~2 pages). `Sigma_HG` alphabet,
   the VM state `(H, L, p_1, ..., p_k)`, S2H interpreter, H2S greedy
   encoder, structural tuples ξ and η, canonical-seed selection,
   tie-breaking cascade. One worked example on STS(7).
3. **Cohort and protocol** (~1 page). §3-4 of this document
   compressed.
4. **Results** (~2 pages). The headline table + the two supplementary
   tables (runtime/memory transparency, MD5 checksums).
5. **Related work** (~1 page). Levi reduction (Berge 1973,
   Beigel-Bernasconi 1999); IR canonical labelling (McKay 1981,
   McKay-Piperno 2014, Junttila-Kaski 2007); group-theoretic exact
   methods (Luks 1999, Babai-Codenotti 2008, Neuen 2022); native WL
   approximate methods (Feng 2024, Zhang 2025) — cited as
   predecessors, not benchmarked. Steiner triple system enumeration
   tradition (Mathon-Phelps-Rosa 1983, Kaski-Östergård 2004, 2006).
   The IsalGraph and IsalSR sibling projects.
6. **Conclusion** (~0.5 page). The canonical-string framework is
   correctness-preserving on the gold-standard combinatorics cohort.
   Pointers to the full empirical paper for runtime, real-world
   deduplication, and the LLM comparison.
7. **References + supplementary**.

---

## 7. Acceptance criteria for the preprint

The preprint goes on arXiv iff:

1. **Headline table populated.** `FP = FN = 0` for all four backends
   on the full cohort (85 STS representatives + GQ(2,2), 8,600
   positive pairs from `permute()` at N = 100, 3,160 STS(15) hard
   negatives).
2. **Bijection certificates accepted.**
   `verify_bijection_certificate` returns 0 violations on the
   `pynauty_levi` and `bliss_levi` columns over all 8,600 positive
   pairs.
3. **Reproducibility artefact shipped.** The five `sts*.txt` files
   are committed with checksums; the run is reproducible from a
   single YAML and a pinned RNG seed.
4. **Supplementary runtime/memory recorded.** Per-fingerprint
   wall-clock and peak RSS captured for every (backend,
   representative) pair, without comparative claims in the main text.

Failure on (1) is either a bug or a Theorem-2 counterexample —
publishable independently per F28 framing in PROPOSAL.

---

## 8. What is explicitly out of scope

| Item | Reserved for |
|---|---|
| Runtime/memory comparison and speedup claims | Full empirical paper (Tier 2-5, JEA/ALENEX/JCD) |
| HIC-12 partition agreement (Tier 5) | Full empirical paper |
| Random hypergraph scaling (Tier 2, XGI ER + Chung-Lu) | Full empirical paper |
| Tier 3 hardness families (PG(2, q), large-Aut STS, GQ(2,4)/(3,5), non-group Latin squares) | Full empirical paper |
| LLM4Hypergraph three-way comparison (decision I49) | Full empirical paper |
| ARB / XGI-DATA / Hypergraphx structural calibration (Tier 4) | Full empirical paper |
| Feng / Zhang WL-failure fixtures (Tier 1 criteria 5-7) | Phase 3.5 + full empirical paper |
| STS(19) `1k_sample` (1000 reps, requires `stsc` decompressor) | Full empirical paper |
| Theorems 1, 2, 3 (expressiveness, completeness, backtracking bound) | Theoretical paper (JSC / SIDMA) |
| HG-CFI construction | Companion paper (open) |

The preprint is the smallest publishable claim that establishes the
canonical-string framework on a published-iso-class cohort.
Everything else waits for the full paper.

---

## 9. Implementation tickets (to land the preprint)

In dependency order:

1. **Port the Kaski-Östergård plaintext parser.** New module
   `src/isalhg/datasets/catalog/kaski_ostergard.py` shipping
   `KaskiOstergardSTSDataset`. Parses the `{a..o}` 3-character triple
   format; one system per line. ~80 lines including the
   `HypergraphDataset` boilerplate.
2. **Commit `sts{3,7,9,13,15}.txt`** under
   `tests/fixtures/kaski_ostergard/`. Record upstream MD5 checksums
   in a `CHECKSUMS.md5` sibling file.
3. **Register the dataset** in `src/isalhg/datasets/registry.py`
   under `kaski_ostergard_sts`.
4. **Write `experiments/configs/preprint_kaski_ostergard.yaml`.** One
   cell per backend (4 cells total), one dataset, seed 42, N=100
   permutations per representative.
5. **Run the orchestrator.** `python -m experiments.orchestrator
   --config experiments/configs/preprint_kaski_ostergard.yaml`.
   Verify the headline table populates.
6. **Add runtime/memory capture** in `protocols.pairwise_iso` (10
   repeats per fingerprint via `time.perf_counter`; RSS delta via
   `resource.getrusage`). Persist in the result JSON under
   `measurements.runtime_per_fp` and `measurements.peak_rss`.
7. **Generate the supplementary tables** with
   `experiments/analysis/preprint_tables.py` (new file). Outputs
   CSV-formatted runtime and partition-agreement tables.
8. **Write the preprint** against the §6 structure.
9. **arXiv submission** under `cs.DM` (Discrete Mathematics) primary,
   `cs.DS` (Data Structures and Algorithms) secondary.

Steps 1-7 are implementation; steps 8-9 are writing and submission.

---

## 10. References used in the preprint

- Berge, C. (1973). *Graphs and Hypergraphs.* North-Holland. §17.
- Beigel, R. & Bernasconi, A. (1999). *Hypergraph Isomorphism and
  Structural Equivalence of Boolean Functions.* STOC 1999, pp.
  217-225. DOI:10.1145/301250.301427.
- McKay, B.D. (1981). *Practical Graph Isomorphism.* Congressus
  Numerantium 30:45-87.
- McKay, B.D. & Piperno, A. (2014). *Practical Graph Isomorphism, II.*
  J. Symbolic Computation 60:94-112. arXiv:1301.1493.
- Junttila, T. & Kaski, P. (2007). *Engineering an Efficient
  Canonical Labeling Tool for Large and Sparse Graphs.* ALENEX 2007.
  DOI:10.1137/1.9781611972870.13.
- Luks, E.M. (1999). *Hypergraph Isomorphism and Structural
  Equivalence of Boolean Functions.* STOC 1999.
  DOI:10.1145/301250.301427.
- Babai, L. & Codenotti, P. (2008). *Isomorphism of Hypergraphs of
  Low Rank in Moderately Exponential Time.* FOCS 2008.
  DOI:10.1109/FOCS.2008.80.
- Neuen, D. (2022). *Hypergraph Isomorphism for Groups with
  Restricted Composition Factors.* ACM TALG 18(3) art. 21.
  DOI:10.1145/3527667.
- Mathon, R., Phelps, K.T. & Rosa, A. (1983). *Small Steiner Triple
  Systems and Their Properties.* Ars Combinatoria 15:3-110.
- Kaski, P. & Östergård, P.R.J. (2004). *The Steiner Triple Systems
  of Order 19.* Math. Comp. 73(248):2075-2092.
  DOI:10.1090/S0025-5718-04-01626-6.
- Kaski, P. & Östergård, P.R.J. (2006). *Classification Algorithms
  for Codes and Designs.* Springer ACM 15.
- Kaski, P., Östergård, P.R.J., Pottonen, O. & Kiviluoto, L. (2009).
  *A Catalogue of the Steiner Triple Systems of Order 19.*
  Bull. Inst. Comb. Appl. 57:35-41.
- Payne, S.E. & Thas, J.A. (2009). *Finite Generalized Quadrangles*
  (2nd ed.). EMS. DOI:10.4171/066.
- Feng, Y., Han, J., Ying, S. & Gao, Y. (2024). *Hypergraph
  Isomorphism Computation.* IEEE TPAMI 46(5):3880-3893.
  arXiv:2307.14394.
- Zhang, D. et al. (2025). *Improved Expressivity of Hypergraph
  Neural Networks through High-Dimensional Generalized
  Weisfeiler-Leman Algorithms.* ICML 2025. PMLR v267.
- López-Rubio, E. & Pascual-González, M. (2026). *Representation of
  Graphs by Sequences of Instructions.* Preprint (IsalGraph
  sibling).
- López-Rubio, E., Pascual-González, M. & Thurnhofer-Hemsi, K.
  (2026). *Representation of Directed Acyclic Graphs by Sequences of
  Instructions for Symbolic Regression.* IEEE TPAMI submission
  (IsalSR sibling).
