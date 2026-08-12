# Venue — IEEE Transactions on Knowledge and Data Engineering

*PI decision, 2026-08-12: target **IEEE TKDE** (ISSN 1041-4347) instead of
*Information Sciences*. This file records what that costs and what it buys, so
the rescope is aimed rather than merely relabelled.*

---

## 1. What TKDE rewards

TKDE publishes work on how knowledge and data are **represented, stored,
indexed, searched, mined and reasoned over**. Read against the current draft,
the venue's implicit checklist is:

| TKDE expects | v3 article as it stands | v5 answer |
|---|---|---|
| A **data/knowledge problem**, not a mathematical characterization | geometry of a metric space | enumeration, deduplication and search over hypergraph space |
| An **algorithm or structure** with stated complexity | `w*_c` exists; no algorithmic consumer | the canonical-augmentation enumerator; the dedup key; the search driver |
| **Scalability analysis** with a stated envelope | measured, honest (k=3 → n≈24) | same measurement, now framed as the operating envelope of a system |
| **Real data** | HIC gate failed → censored exhibit | ARB/Benson ego-hypergraphs, the community's own corpora |
| **Baselines from the same community** | ML representation baselines | `nauty` canonical augmentation, MACE-style model finders, hypergraph-mining canonical forms |
| Theory that **licenses the algorithm** | theory that describes a space | Theorem A = correctness of dedup; P1 = correctness of the ambient space; P4 = correctness of the generator |

The conversion is therefore not cosmetic, but it is also not a rebuild: every
theorem and almost every measurement already in the tree keeps its place, and
what changes is **which consumer each result serves**.

## 2. The community objects we already touch

This is the strongest argument for TKDE: the paper's existing machinery is built
on this community's own artifacts.

- **Hypergraph edit distance.** Qin et al., *Computing Hypergraph Edit Distance*
  (ICDE 2023) — we adopt their Definition 3 cost model verbatim, reproduce their
  HGED-BFS, and use their **ego-network definition** (Definition 1) as our
  instance-derivation protocol. At TKDE this is in-community prior work, not an
  imported formalism; the E1' figure and the envelope proposition become
  contributions to a conversation the venue is already having.
- **Canonical forms as mining primitives.** gSpan's minimum DFS code (Yan & Han,
  ICDM 2002) is *an instruction-string canonical form for graphs*, used because
  it supports incremental extension with a canonicality test. `w*_c` is the
  hypergraph analogue, and the parallel is the cleanest way to explain to a TKDE
  reader why a *constructive* canonical form is worth having over a *certificate*
  canonical form like nauty's.
- **Isomorph-free exhaustive generation.** McKay, *Isomorph-free exhaustive
  generation* (J. Algorithms, 1998) and Kaski & Östergård, *Classification
  Algorithms for Codes and Designs* (Springer, 2006) — the latter is already in
  the repo's orbit (the vendored STS catalogue comes from that lineage). This is
  the correctness framework the C1 loop sits in — **borrowed, not claimed**: it
  is invariant-agnostic, and nauty is the better invariant for it
  (`competitors.md` §0).
- **Metric-space indexing.** Chávez, Navarro, Baeza-Yates & Marroquín,
  *Searching in metric spaces* (ACM Computing Surveys, 2001); Ciaccia, Patella &
  Zezula, *M-tree* (VLDB 1997). This literature gives the geometry section its
  engineering consumer: intrinsic dimensionality is *the* standard predictor of
  metric-index performance, so `D̂`, `ν` and the concentration profile stop being
  descriptive and start being design inputs.
- **Higher-order network data.** Benson, Abebe, Schaub, Jadbabaie & Kleinberg,
  *Simplicial closure and higher-order link prediction* (PNAS 2018) — the ARB
  collection. This is the standard hypergraph benchmark suite; using it removes
  the "synthetic-only" objection outright.

## 3. What must be added

1. **An algorithm with pseudocode and complexity.** The C1 search loop (move
   operator, cost levels, pluggable frontier key) and the C2 search driver. A
   TKDE paper without an algorithm box reads as a characterization paper.
2. **A system-shaped evaluation.** Throughput (objects/s), key size (bytes per
   isomorphism class), index/store size, memory, and the measured feasibility
   envelope as an *operating region* — not just correctness tables.
3. **Real corpora with a citable derivation protocol.** ARB + Qin's ego-network
   definition (already implemented as
   `core/sparse_hypergraph.py::ego_network`).
4. **A false-merge measurement.** The single most TKDE-legible way to show that
   completeness is not free: on real data, count how many *non-isomorphic*
   objects each incomplete representation collapses into one key
   (`applications.md` B4). Ground truth: `nauty`-Levi.
5. **Reproducibility artifact.** Code + corpora + scripts, stated in the paper.
   The repo already has the discipline (`../DEVELOPMENT/`, frozen results).

## 4. What must be cut or compressed

- **The MDS-as-application framing.** Keep one map figure and the geometry table;
  drop the dimension-selection methodology to an appendix (`geometry.md` §4).
- **The distortion bracket exposition** (Bourgain / Khot–Naor). Two sentences,
  cited, in the geometry section.
- **The estimator validation** (CV vs Horn, calibration probes, N-convergence) →
  appendix or supplementary.
- **The corpus-redesign forensics** (PC1–length correlation 0.960, length-floor
  ρ 0.867, the STS substrate autopsy). Compress to one paragraph in the limits
  subsection; it is excellent methodology but it is not the paper's subject.
- **The competitor set as a seven-row dissimilarity comparison.** Split into
  purpose-specific sets (`competitors.md`).

## 5. Risks specific to this venue

- **"Where is the data-management contribution?"** — answered by C1 (a search
  loop with a cost model, a measured branching factor, and throughput/state-size
  numbers) and C5 (a real-corpus structural census). If D1 is decided against the
  search-space flagship, this risk returns in full.
- **"Your canonical form is slower than nauty."** — true, measured, and
  **conceded in the introduction** (`competitors.md` §0). The answer is that
  identity is not the claim: nauty supplies a certificate, not a space, and the
  paper's applications require moving in the space rather than comparing points
  of it. The gSpan precedent explains why a pipeline wants a *constructive*
  canonical form even when a faster certificate exists.
- **"The logic application belongs at IJCAR/AAAI."** — a real risk if the FOL
  material is presented as a contribution to automated reasoning. It must be
  presented as an **instantiation of the enumeration engine** that demonstrates
  the capability, with the automated-reasoning baselines reported honestly and
  the deeper logic questions explicitly deferred (see `README.md` D2).
- **Scope.** TKDE regular papers are long-form but not unbounded; the eight-step
  spine in `proposal.md` §2 is already near the ceiling. The limits subsection
  and the geometry appendix are the compression levers.

## 6. Consequences for the existing docs

Ratification of D-ART3 v5 implies edits to `../PROPOSAL.md` (§0–§6 rewritten
from `proposal.md`), `../DATA.md` (§1–§2 rewritten from `data.md`, §7 corpus
policy extended), `../COMPETITORS.md` (restructured per `competitors.md`),
`../theoretical/geometry.md` (synthesized per `geometry.md`),
`../empirical/applications.md` (A1–A4 dispositions per `applications.md` §4),
plus two new documents mirroring `logic_models/` and the C1 framework spec. The
frozen empirical files (`../empirical/correlation.md`) need only their framing
paragraphs updated.
