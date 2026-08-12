# Data v5.1 — real hypergraph corpora, formula benchmarks, and the gates

*Proposed replacement for `../DATA.md` §§1–2 and extension of §7. Status:
pending PI.*

**On-disk (author-directed, downloaded 2026-08-12).** The full ARB/Benson
collection — **all 28 datasets, 3.6 GB, zero failures** — is at
`/media/mpascual/Sandisk2TB/research/ISAL/isalhg/data/arb_benson/`, split
`temporal/<dataset>/` (17) and `labeled/<dataset>/` (11), with
`raw_archives/` (1.2 GB), `MANIFEST.md` and `download_log.json`.
`contact-high-school` and `contact-primary-school` appear in both families with
different contents and formats (`nverts`/`simplices`/`times` in temporal;
`hyperedges`/`node-labels`/`label-names` in labeled); both copies are kept and
are **not** interchangeable. Layout and formats verified independently of the
download log.

The author's instruction was explicit: *scrap the previous data plan if needed;
what matters is data the community accepts and that is tested correctly.* This
document is written on that basis — ARB is the anchor, and the synthetic corpora
are retained only where they carry a frozen result or a control that real data
cannot supply.

The v3 data plan rejected the ARB/Benson collection with one sentence: *"ARB /
XGI-DATA / Hypergraphx entries are each one giant network — no set of instances
to classify — so unsuitable for the corpus role […] an ego-net/snapshot
derivation from ARB was considered and declined to avoid a bespoke derivation
step reviewers can attack."*

**That objection does not survive v5, for two independent reasons.**

1. The v5 workloads are not whole-hypergraph classification. Cataloguing,
   deduplication, false-merge counting, enumeration and navigation need *many
   small hypergraphs*, not *labelled classes of hypergraphs*.
2. **The derivation step is not bespoke.** Qin et al. (ICDE 2023) — the paper
   whose HGED definition this article adopts verbatim — define ego networks
   (their Definition 1) over exactly these ARB datasets and use them as their
   own benchmark. The repo already implements it:
   `core/sparse_hypergraph.py::ego_network` reproduces Definition 1, and
   `datasets/arb_benson.py` already loads the ARB triple format. Using the
   community's own derivation on the community's own corpora is the opposite of
   a step reviewers can attack.

---

## 1. The real anchor — ARB / Benson (primary under v5)

**Source.** `https://www.cs.cornell.edu/~arb/data/` (Benson et al., PNAS 2018,
and the associated clustering/labelling papers). 28 datasets in two families.

**Derivation protocols (both citable, both already implemented or trivial).**

| Protocol | Definition | Yields | Serves |
|---|---|---|---|
| **Ego-hypergraphs** | `EGO_H(v)` = sub-hypergraph induced on the closed neighbourhood `NEI(v)`, keeping edges fully contained in it (Qin et al., ICDE 2023, Def. 1) | one small hypergraph per vertex → 10³–10⁶ instances per dataset | C5 census + completeness price; the ball-growth probe (G-B1) on real strings |
| **Temporal snapshots** | for the timestamped simplex sequences, the hypergraph of all simplices in a time window `[t, t+Δ)` | an ordered sequence of hypergraphs per dataset | C3 navigation on real data |
| **LCC restriction** | largest connected component (D-CONN1, already the standing policy) | connected instances | all |

**Dataset selection — measured, not assumed (2026-08-12).** The binding
constraint is the measured `w*_c` envelope (`k = 3` → `n ≈ 24` at low density;
`k = 5` → `n = 8`; `k ≥ 7` infeasible), so the first question is the simplex-size
distribution. All 28 datasets are on disk and were scanned
(`scripts/diagnostics/arb_arity_probe.py`, log alongside): per dataset,
`|E|`, and the min / median / p95 / max simplex size with the fractions at
arity ≤ 3, ≤ 5, ≤ 10. **This replaces the v5.0 tier *hypotheses*, two of which
the measurement refuted.**

*Tier 1 — clean by construction: **max arity ≤ 5, zero censoring**.*

| dataset | family | `\|E\|` | med | max | ≤ 3 |
|---|---|---|---|---|---|
| `tags-stack-overflow` | temporal | 14,458,875 | 3 | **5** | 0.667 |
| `tags-math-sx` | temporal | 822,059 | 2 | **5** | 0.870 |
| `tags-ask-ubuntu` | temporal | 271,233 | 3 | **5** | 0.734 |
| `contact-high-school` | temporal / labeled | 172,035 / 7,818 | 2 | **5** | 0.997 / 0.971 |
| `contact-primary-school` | temporal / labeled | 106,879 / 12,704 | 2 | **5** | 0.995 / 0.972 |

This is the material result of the scan: **five datasets need no arity filter at
all**, which is precisely the failure mode that sank the HIC anchor (corpus-level
arity 110). The `tags-*` family alone supplies over 15 M simplices at max arity 5.

*Tier 2 — usable under a stated arity filter (retention ≥ 0.95 at arity ≤ 5).*
`DAWN` (2.27 M, max 16, 0.990 ≤ 5), `NDC-substances` (112 k, max 25, 0.959),
`email-Eu` (235 k, max 25, 0.966), `email-Enron` (10.9 k, max 18, 0.968),
`threads-ask-ubuntu` (193 k, max 14, 0.998), `threads-math-sx` (720 k, 0.989),
`threads-stack-overflow` (11.3 M, 0.983), `trivago-clicks` (233 k, max 85,
0.916).

*Tier 3 — out of envelope without heavy, label-correlated censoring.*
`coauth-DBLP` / `-MAG-Geology` / `-MAG-History` and `congress-bills` (max 25;
congress retains only 0.819 at arity ≤ 5), `NDC-classes` (max 24, 0.854 —
**refuting the v5.0 guess that put it in Tier 1**), `walmart-trips` (0.577),
`senate-bills` (0.606), `house-bills` (0.374), `mathoverflow-answers`
(max 1,784), `stackoverflow-answers` (max 61,315), `amazon-reviews`
(max 9,350), `senate-committees` (median 19), `house-committees` (median 40).

**What is resolved and what is not.** The *arity* half of gate G-D1 is closed:
the admitted list above is measured. The *size* half is open and is the binding
one — an ego-network's arity is bounded by its source's (it keeps only edges
fully contained in `NEI(v)`), but its **vertex count `n = |NEI(v)|`** is not,
and `n` is what the `w*_c` envelope actually constrains. The contact datasets in
particular are dense enough that some closed neighbourhoods will be large. So:
**no dataset is committed until the ego-net size distribution and the `w*_c`
wall-clock distribution are measured** (G-D1, remaining half). The arity result
is what makes it worth measuring.

**Censoring policy (inherited discipline).** Per-instance `w*_c` under a fixed
wall-clock budget; DNFs dropped and counted; yield reported per dataset and per
size stratum; any label-correlated censoring stated. This is exactly the protocol
that made the HIC exhibit defensible even when its gate failed, and it carries
over unchanged.

**Comparison to HIC.** ARB replaces HIC as the real anchor. HIC's gate outcome
(corpus-level arity 110; symmetry-driven DNF tail; 57–92 % yields) stays on the
record in `../DATA.md` §2 and in the ledger; the HIC exhibit itself is proposed
for retirement from the paper (`README.md` D5). ARB is a better anchor for three
reasons: the instances are *small by construction* (ego-nets), the derivation is
the HGED paper's own, and the corpora are the field's standard benchmark.

## 2. Retained synthetic corpora (nothing is thrown away)

| Corpus | Status | Serves |
|---|---|---|
| **Stratum C** (3 size-controlled cells, 12 swap-families × 6, 27 seeds) | retained, frozen | the measured-limits subsection (A2/A3); the falsifiable-corpus methodology |
| **Ladder corpora** (known Qin budgets) | retained | C3 monotonicity; the ladder-response invariant |
| **Design fixtures** (17 regimes, 1700 single edits) | retained | G2 sensitivity + the nauty contrast |
| **E1' mini-corpus** (11 blocks, 6,921 pairs) | retained, FROZEN | the discussion figure; the P5 filtering measurement |
| **Bits corpora** (Stratum A 85 + planted_n240, 320/320) | retained, FROZEN | compactness → key-size |
| **`exhaustive_small`** | retained, new role | B1's ground-truth verification (census vs brute force) |
| **`permute()` pairs** | retained | iso-invariance sanity |
| **Stratum B** (density/size sweep) | retained | the feasibility envelope figure |
| **HIC atlas** | loader retained; exhibit proposed for retirement | the record of the gate |

## 3. New synthetic corpus — the enumeration census

For B1, the "corpus" is generated, not loaded: all connected labelled
hypergraphs of cost `≤ C` for small `C`, under a given `(k, |Σ_V|, |Σ_E|)`.
Its purpose is verification and the scalability curve, and its ground truth is
brute-force enumeration modulo `pynauty`-Levi at the sizes where that is
possible. No new generator module is needed beyond the engine itself.

## 4. Data for the logic application (C2)

*Full detail in [`logic_models/`](logic_models/) §5; summarized here so the
data plan is readable on its own.* Four sources, each discharging a different
obligation:

1. **Hand-written non-theorems** — failed transitivity, antisymmetry, Euclidean
   property, "every element has a distinct successor". Minimal countermodels
   known by hand ⇒ these are the unit fixtures that pin the search.
2. **TPTP** (Sutcliffe) — the community's FOL problem library and the substrate
   every MACE-style finder is evaluated on. The slices that matter: problems with
   status **`Satisfiable`** / **`CounterSatisfiable`**; the **CASC `FNT`**
   (First-order Non-Theorems) and `SAT` division problem lists — i.e. the
   model-finding competition tracks; and the **quasigroup existence problems
   (QG1–QG7)**, historically the driver of SEM and Mace4 and exactly the
   high-symmetry stress case. Selection rule (relational, equality-free, small
   arity, capped signature) must be stated in the paper.
3. **Verifiable enumeration ground truth** — small-order counts of
   non-isomorphic **groups, semigroups/monoids, quasigroups/Latin squares**
   (literature + OEIS), plus the in-repo **Steiner triple systems** (`sts_catalog`,
   orders 3–15, 85 classes — free). Reproducing published counts is what makes
   the census claim checkable independently of any performance claim.
4. **Specification-debugging examples** (optional) — small Alloy/Kodkod specs and
   the Nitpick example suite, for the repair-path story (C3).

Selection, sizes and the domain/fact ceiling are gated by **G-L1**.

## 5. Gates (blocking, measure before scoping)

- **G-D1 — ARB feasibility probe. [arity half CLOSED 2026-08-12; size half
  OPEN.]** *Closed:* max/median/p95 simplex arity and the ≤3/≤5/≤10 retention
  fractions for all 28 datasets (§1; `scripts/diagnostics/arb_arity_probe.py`).
  Five datasets carry max arity 5 and need no filter; the tier table is measured.
  *Open, and binding:* the **ego-net size distribution** (`n`, `m`, max arity)
  over a seeded vertex sample per admitted dataset, and the `w*_c` wall-clock
  distribution under a fixed per-instance budget, yielding the retention table.
  `n = |NEI(v)|` is what the envelope constrains, and it is not bounded by the
  arity result. *Blocks:* C5, and C3 on real data.
- **G-L1 — encoded-structure feasibility probe.** `w*_c` wall-clock across
  `(|D|, |F|)` for each surviving encoding (E1, E2, and `Σ_FO` if D3′ adopts
  one). *Hypothesis under test:* heavily labelled arity-2 structures are far
  cheaper than the unlabelled 3-uniform envelope suggests, because labels
  strengthen tie-breaking and shrink the automorphism group. *Known
  counter-mechanism:* label-stripping can only make the tie-complete search
  equal or slower (OD7's correction), so the direction is expected favourable —
  magnitude unknown, worst case super-polynomial. *Blocks:* the whole C2 scope,
  and it is an input to the D3′ alphabet decision.
- **G-B1 — ball growth / branching-factor probe.** For a sample of corpus
  strings and small `r`: `|B_r(w)|`, the number of decoded objects, the number of
  **distinct isomorphism classes** among them, and the wall-clock of the whole
  expand-decode-canonize cycle. *Produces:* the new geometry invariant
  (`geometry.md` §1) and the branching factor of C1. *Blocks:* any cost model
  for the search, and the feasibility of C2's radius-`r` neighbourhood queries.
- **G-B2 — frontier ceiling probe.** Objects/s and memory for hash-set frontier
  dedup as a function of cost level; the level at which the frontier stops
  fitting in RAM; the same numbers with a Levi-nauty key substituted. *Blocks:*
  nothing scientific — it sets the demonstrable scale and supplies the conceded
  comparison of `competitors.md` §2.

## 6. Corpus policy (extension of `../DATA.md` §7)

| Measurement | Corpus | Why |
|---|---|---|
| C1 framework verification (census vs brute force) | generated + `exhaustive_small` | ground truth available by brute force |
| C1 ball growth (G-B1) | Stratum C strings + ARB ego-net strings | the invariant must be measured on the objects the search runs on |
| C2 minimal countermodels | formula suite §4 | the objective is defined on formulas, not on corpora |
| C2 census verification | algebraic counts §4.3 + `sts_catalog` | published counts to reproduce |
| C3 navigation (synthetic) | ladder corpora | known Qin budgets |
| C3 navigation (real) | ARB temporal snapshots | the only real corpus with an intrinsic ordering |
| C4 black-box optimization | generated, one verifiable predicate | the answer must be known at small size |
| C5 census + completeness price | ARB ego-nets, admitted subset | many small real instances; community-standard derivation |
| Measured limits (A2/A3) | Stratum C, frozen | both naive floors identically zero by construction |
| Geometry invariants | Stratum C + ARB ego-nets | the geometry must describe the objects the applications run on |
| Compactness / search-state size | bits corpora, frozen | per-object claim; size heterogeneity is appropriate here |
| Discussion figure + P5 | E1' mini-corpus, frozen | the only place the exact oracle is feasible for all pairs |

## 7. Open data questions

- **DQ-6.** Ego radius: strict Qin Definition 1 (closed neighbourhood, fully
  contained edges) only, or also a 2-hop variant? Default: Definition 1 only —
  it is the citable one.
- **DQ-7.** Sampling policy for ego-nets: all vertices, or a seeded sample per
  dataset? Default: seeded sample with the seed reported, sized to the wall-clock
  budget; full enumeration only where it is cheap.
- **DQ-8.** Do ARB node labels enter (`d_I^Σ`, the label-aware family member) or
  are instances stripped to `d_I^⊥`? The two are different metric family members
  (`../theoretical/stability.md` §1 Remark) and must not be mixed in one series.
  Default: **`d_I^⊥` for the census and false-merge work** (a structural claim),
  labels as a separate, clearly-marked exhibit if wanted.
- **DQ-9.** Temporal window `Δ` for snapshots, per dataset. Gated by G-D1.
