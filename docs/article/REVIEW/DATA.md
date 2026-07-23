# Strict data specification for the IsalHG article

**Status:** design spec (not yet a ledger task). Standalone. Takes the article's
methodology *as-is* (`w*_c`, `d_I`, the six geometry invariants, A1–A4,
competitors, bits, E1′) and specifies the **data changes** needed so every result
is consistent, generalizable, broad, standard, and — because we will *visualize*
hypergraphs to check algorithm outputs — **inspectable**. Supersedes the ad-hoc
per-experiment corpora audited in `DATA_RIGOR.md`; that file holds the evidence
this one acts on.

The guiding rule: **one master corpus, sampled by strict grids from known
structures; every experiment is a documented *slice* of it, never its own
generator.**

---

## 0. What "strict" means here (design principles)

1. **One master corpus, sliced.** All experiments draw from a single
   corpus specification. G2/A4/E1′ still need perturbation ladders and an
   HGED-feasible sub-corpus, but those are *derived* from the same seed catalog
   and the same grid — not independently invented. This is what makes results
   comparable across sections.
2. **Known structures, not random blobs.** Class labels and visual targets come
   from standard combinatorial families (Steiner systems, projective/affine
   planes, generalized quadrangles, complete/loose/tight uniform hypergraphs),
   plus standard random-null generators (Erdős–Rényi, Chung–Lu) as the
   unstructured baseline. Random seeds are a *null class*, not the whole corpus.
3. **Full grid over the real axes of variation.** Vary, explicitly:
   **size** `n`, **density** `m/n`, **arity** `k`, **symmetry** (designs → random
   → irregular). One-point corpora are forbidden.
4. **Multi-seed, deterministic.** ≥ `S = 20` seeds per cell; seed =
   `base + cell_index·stride`; every seed printed into the result record.
5. **Log realized parameters, not just requested ones.** Record the realized
   `(n, m, arity histogram, density, connectivity)` distribution per corpus, not
   only the generator's request parameters. (Current configs log the *attempt*
   count, never the realized `m` — this must change.)
6. **Feasibility-gated.** Each cell is admitted only after its `w*_c` (and, for
   E1′, exact-HGED) cost is measured under a budget; the feasible envelope is a
   reported figure, not a hidden filter.
7. **Fixed metric-family triple.** State `(k, h, vocabulary)` once and hold it.
   `d_I^{k,h,Σ}` is an index family: **absolute `d_I` values across different `k`
   are incomparable.** The arity sweep therefore compares only (a) dimensionless
   geometry *descriptors* across `k` and (b) *within-`k`* application rankings —
   never pooled raw `d_I` across `k`.
8. **Visualizable scale.** Structured instances are kept small enough to draw
   (`n ≲ 30`) so the hypergraph, its decoded A4/G3 intermediates, and its MDS
   trajectory can be shown side by side. Larger `n` lives only in the random
   sweep stratum, for the scale/feasibility axis.

---

## 1. The hypergraph taxonomy the corpus must cover

A "broad" hypergraph corpus spans five axes. The master corpus is designed to
tile them:

| Axis | Range to cover | Where covered |
|---|---|---|
| **Size** `n` | small (8) → moderate (32) → scale (48–64) | Stratum A (≤ 32), Stratum B (up to 64) |
| **Density** `m/n` | sparse (~1) → medium (~2–3) → dense (~4+) | Stratum B grid; Stratum A designs are fixed-density |
| **Arity** `k` | uniform 3,4,5 (designs) + 3,5,7,10 (random) + **mixed arity** | A (uniform 3–5), B (uniform + mixed 3–10) |
| **Symmetry** | high (designs, vertex-transitive) → medium (random regular) → low (irregular) | A (high), B (low/medium) |
| **Connectivity** | connected only (domain restriction `n ≥ 1`) | all strata (LCC filter) |

Coverage of all five is the concrete meaning of "generalizable." Any headline
claim (non-Euclidean, moderate `D̂`, low distortion, mild hubness; the A1–A4
competitor orderings) must be shown *stable in character* across these axes, not
asserted from one cell.

---

## 2. The master corpus — four strata + real anchor

### Stratum A — Structured / known-design corpus (interpretable, visualizable)

**Role.** Class labels for A2/A3, visual targets for A1/A4/G3, symmetric-regime
targets for G2. Members are recognizable, drawable, and carry a *meaningful*
family label (unlike the current random-seed families).

**Final admitted catalog (14 families).** Admission required (a) `w*_c` p90 ≤ 30 s
under a 300 s cluster budget (Picasso A100, single instance each), and (b)
successful Qin perturbation: at least one non-isomorphic connected member found
within 300 bounded-budget attempts. Both conditions were verified in the T-M7h
feasibility pilot (`artifacts/feasibility_pilot/feasibility_pilot_stratum_a.json`).

| Family | k | n | m | `w*_c` p50 (s) | Class | Notes |
|---|---|---|---|---|---|---|
| `sts7` | 3 | 7 | 7 | 0.024 | design | Fano plane STS(7) |
| `sts9` | 3 | 9 | 12 | 0.299 | design | Steiner triple system STS(9) |
| `gq22` | 3 | 15 | 15 | 3.045 | design | GQ(2,2) doily; the hardest admitted case |
| `loose_path_k3` | 3 | 9 | 4 | 0.002 | path | sparse, drawable |
| `tight_path_k3` | 3 | 6 | 4 | 0.003 | path | |
| `loose_cycle_k3` | 3 | 8 | 4 | 0.003 | cycle | |
| `tight_cycle_k3` | 3 | 5 | 5 | 0.004 | cycle | |
| `loose_path_k4` | 4 | 10 | 3 | 0.003 | path | m=3: visual anchor only (see note) |
| `tight_path_k4` | 4 | 6 | 3 | 0.007 | path | m=3: visual anchor only |
| `loose_cycle_k4` | 4 | 12 | 4 | 0.056 | cycle | perturbable |
| `tight_cycle_k4` | 4 | 5 | 5 | 0.007 | cycle | |
| `loose_path_k5` | 5 | 13 | 3 | 0.043 | path | m=3: visual anchor only |
| `tight_path_k5` | 5 | 7 | 3 | 0.046 | path | m=3: visual anchor only |
| `tight_cycle_k5` | 5 | 7 | 7 | 0.356 | cycle | perturbable |

The m=3 path families (k=4,5) have too few hyperedges to generate non-isomorphic
perturbations within a bounded budget; they serve as **single-instance visual and
geometry anchors** in A1/A4/G3, not as A2/A3 classification targets.

![Stratum A — 14 kept designs visualized with HyperNetX](../../../artifacts/synthetic_catalog/stratum_a_kept_hnx.png)

*Stratum A admitted catalog (14 families). Top section: arity-3 designs and paths/cycles. Bottom section: arity-4/5 paths and cycles. Each hyperedge is drawn as a filled polygon; label = family id.*

![Arity-4/5 kept members (detail)](../../../artifacts/synthetic_catalog/arity45_kept_hnx.png)

*Arity-4 and arity-5 kept members in detail. The m=3 paths provide visual anchors; the k=4 and k=5 cycles are the perturbable arity-4/5 members in the article corpus.*

**Excluded catalog (9 families).** All 23 candidate families were measured; 9 were
rejected before entering the corpus. Reasons are mutually exclusive and categorical.

| Family | k | n | m | Reason | Category |
|---|---|---|---|---|---|
| `ag24` | 4 | 9 | 12 | `w*_c` DNF at 300 s cluster budget | feasibility-DNF |
| `pg23` | 4 | 13 | 13 | `w*_c` DNF at 300 s cluster budget | feasibility-DNF |
| `pg24` | 5 | 21 | 21 | `w*_c` DNF at 300 s cluster budget | feasibility-DNF |
| `sts13_0` | 3 | 13 | 26 | `w*_c` p90 = 166 s >> 30 s threshold | feasibility-DNF |
| `sts13_1` | 3 | 13 | 26 | `w*_c` p90 = 159 s >> 30 s threshold | feasibility-DNF |
| `sts15_0` | 3 | 15 | 35 | `w*_c` DNF at 300 s cluster budget | feasibility-DNF |
| `complete_k3_n5` | 3 | 5 | 10 | Automorphism group `S_5` exhausts 300 Qin attempts without leaving iso-class | perturbation-failure |
| `complete_k4_n6` | 4 | 6 | 15 | Automorphism group `S_6` exhausts 300 Qin attempts; all bounded edits stay in same iso-class | perturbation-failure |
| `complete_k5_n6` | 5 | 6 | 6 | Same mechanism as `complete_k4_n6` | perturbation-failure |

**Reason categories.** The two categories reflect distinct mechanisms:

1. **Feasibility-DNF (6 families).** `w*_c` wall-clock exceeds the 30 s admission
   threshold (or does not terminate within the 300 s cluster budget). Root cause:
   symmetry-driven branch explosion in the tie-complete encoder at moderate `n`. The
   affine/projective planes (ag24, pg23, pg24) are vertex-transitive with very large
   automorphism groups; the large Steiner systems (sts13_0/1, sts15_0) are
   3-uniform but `n ≥ 13` tips them into the exponential regime. These families are
   not in the corpus; they are the measured boundary of the feasibility envelope.

2. **Perturbation-failure (3 families).** `w*_c` is fast (p90 < 1 s) but the
   automorphism group `S_n` of `K_n^{(k)}` is so large that every Qin edit within
   the bounded budget (300 attempts, connectivity-preserving) maps back to the same
   isomorphism class. No non-isomorphic Stratum-A member can be generated. These
   families cannot serve as A2/A3 classification targets (a class of size 1 has no
   intra-class variation to measure ARI/NMI against) and are excluded.

**Coarse-class scheme for A2/A3.** Classification experiments (A2 clustering, A3 kNN)
use **three coarse structural classes** — design, path, cycle — **within a single fixed
arity `k`**. Raw `d_I` values are never pooled across `k` (the metric family triple
`(k, h, Σ)` must be fixed; see §5 and `REVIEW/DATA.md` §0 principle 7).

| Arity | Class: design | Class: path | Class: cycle |
|---|---|---|---|
| k=3 | sts7, sts9, gq22 | loose_path_k3, tight_path_k3 | loose_cycle_k3, tight_cycle_k3 |
| k=4 | — | — (anchors only) | loose_cycle_k4, tight_cycle_k4 |
| k=5 | — | — (anchors only) | tight_cycle_k5 |

At k=4 and k=5, the path families are single-instance anchors (m=3 edges, not
perturbable into a class). A2/A3 at k=4/5 therefore have only one non-singleton
class (cycle); the k=4/5 analyses are power-limited and treated as supporting evidence
rather than primary comparisons. Primary A2/A3 results come from k=3 (three classes,
multiple perturbable members per class).

### Stratum B — Parametric random sweep (generalizability)

**Role.** The generalization evidence. Random hypergraphs have *low* symmetry, so
`w*_c` stays cheap even at high `n` and high `k` — this stratum reaches exactly
the region designs cannot.

**Grid** (full factorial, feasibility-gated):
- `n ∈ {8, 16, 24, 32, 48, 64}`
- density `m/n ∈ {1 (sparse), 2 (medium), 4 (dense)}`
- arity: **uniform** `k ∈ {3, 5, 7, 10}` **and** **mixed** arity `∈ [2, k]`
- generator ∈ {Erdős–Rényi hypergraph, Chung–Lu} (both already in
  `datasets/synthetic/{erdos_renyi,chung_lu}.py`) as two symmetry-null regimes.

**Label = grid cell** (for the sweep analysis; not used as an A2/A3 semantic
class — that is Stratum A's job). ≥ `S = 20` seeds per cell. This is the corpus
the geometry-vs-parameter curves (ν, `D̂`, stress, hubness vs `n`/density/arity)
are read from, each point with a CI (`STATS_PASS_PLAN.md`).

### Stratum C — Perturbation ladders (G2, A4, and the new G3)

**Role.** Known-budget edit trajectories. **Change from current state:** seed the
ladders from **Stratum A designs** (visualizable endpoints) *and* a matched
random control, rather than from standalone random bases. Keep the `qin_edit_cost`
budget accounting (HGED-free). This makes A4's decoded intermediates and G3's
trajectories drawable and their endpoints recognizable.

### Stratum D — Exact-HGED mini-corpus (E1′ only)

**Role.** The single discussion figure. Keep the shape (connected, arity ≤ 3,
`n = 5..10`, the measured oracle ceiling `(n,m) ≈ (10,8)`), but draw its bases
from the **same** Stratum A/C seed catalog at feasible sizes, so E1′ is a slice
of the master corpus, not a separate world. The whole-block exclusion protocol
(no per-pair censoring) stands.

### Real anchor

Per `REAL_DATA_CORPUS.md`: the **designs catalog** as a guaranteed-computable real
anchor (it *is* Stratum A at full catalog scale), plus one **gate-first low-arity
real-world corpus**. Replaces the single censored IMDB exhibit. Real data feeds
A1 geometry (ν, `D̂`) and A2/A3 — same slots as now, broader source.

---

### Synthetic vs. real — proxy assessment

**Finding (measured in T-M7h / S7 real-data exhibit).** Real HIC IMDB-genre
hypergraphs are characterized by three properties that distinguish them sharply
from Stratum A designs:

1. **Mixed arity.** Hyperedge sizes vary within a single hypergraph (arity
   histogram spans multiple values); there is no uniform `k`.
2. **Sparse and small.** Median `n ≈ 7–12` vertices per hypergraph (tail to
   ~270); median `m/n` well below 1 for the cleaner datasets.
3. **Low structural symmetry.** Random and organic incidence structure, not
   design-theoretic.

![HIC IMDB Wri-Genre hypergraph sample](../../../artifacts/synthetic_catalog/hic_imdb_wri_genre.png)

*Sample of HIC IMDB Wri-Genre hypergraphs (genre as hyperedge, movies as vertices). Mixed arity, sparse, small. Genre classes overlap heavily in structure — the near-unclusterable result (ARI < 0.10 for every representation) is visible from the drawing.*

![HIC IMDB Dir-Genre hypergraph sample](../../../artifacts/synthetic_catalog/hic_imdb_dir_genre.png)

*Sample of HIC IMDB Dir-Genre hypergraphs (genre as hyperedge, directors as vertices). Similar structural character: mixed arity, sparse, irregular.*

**Two-purpose framing.** The Stratum A designs and the real HIC hypergraphs serve
**complementary roles** — they are not in competition and Stratum A is **not** an
arity proxy for real data:

| Role | Stratum A designs | Real HIC hypergraphs |
|---|---|---|
| Arity | Uniform k=3/4/5, controlled | Mixed, uncontrolled |
| Symmetry | High (design-theoretic) | Low (organic) |
| Class labels | Structural family (design/path/cycle) | Domain label (genre) |
| A2/A3 purpose | Primary: clean labels, multiple members per class | Supporting: cross-domain sanity check |
| G2/G3 purpose | Symmetric-regime targets; drawable intermediates | Not used (w*_c DNF at corpus scale) |
| A1 purpose | Labeled map (interpretable trajectories) | Geometry rows (ν, D̂ on real data) |

**The genuine real-data proxy** — the generator whose structural character matches
HIC hypergraphs — is the **mixed-arity Stratum B generator** (Erdős–Rényi and
Chung–Lu with `arity ∈ [2, k]`), not Stratum A. Stratum B reaches the
mixed-arity, sparse, low-symmetry regime that real data occupies. The Chung–Lu
generator is a secondary proxy because it models degree heterogeneity; the
plain Erdős–Rényi model is the null (structural) baseline.

This two-purpose framing must be stated explicitly in the paper's methods section
to forestall the misreading that "the designs corpus is representative of
real-world hypergraphs."

---

### Sample size and power (pilot-determined)

**Placeholder — numbers to be filled post-pilot.**

The target sample sizes `N_corpus` (number of hypergraphs per corpus cell) and
`S` (number of seeds per cell) for each experiment are determined by a power
analysis: a pilot run estimates the within-cell variance, then `N` and `S` are
set to achieve 80% power at a pre-declared minimum effect size (Cohen's d = 0.5
for pairwise comparisons; ARI difference ≥ 0.10 for clustering). All pilot
measurements and the resulting `(N, S)` targets will be recorded here before the
production sweep runs.

Current placeholder values (from the N-scaling sweep in T-M5l, superseded by the
S7 redesign): `N = 240`, `S = 1` per cell (single seed). These are the pre-S7
numbers and are **not valid** under the strict master corpus; they are retained
only as a lower-bound reference.

---

## 3. Per-experiment corpus map (the consistency contract)

Every experiment is a named slice. No experiment generates its own bespoke data.

| Experiment | Stratum / slice | Why this slice |
|---|---|---|
| **G1** concentration + hubness | B (full sweep) + A (per-family) | hubness must be shown across the grid, not one cell |
| **G2** sensitivity + ladder | C (design-seeded + random control) | needs known-budget single edits; symmetric + null regimes |
| **A1** MDS + geometry table | B primary (curves vs axes) + A (labeled map) | geometry table becomes a *curve* per axis; A gives a drawable map |
| **A2** clustering | A (family labels) | ARI/NMI only interpretable against *meaningful* classes |
| **A3** kNN | A (family labels) + B (per-cell) | classify family type; read against G1 hubness |
| **A4** shortest path | C (design-seeded ladders) | drawable endpoints + decodable intermediates |
| **G3** *(new)* geometry response | C + dedicated OFAT sequences (§6) | one-factor-at-a-time moves from design bases |
| **bits** compactness | A + B (broad) | compression shown across sizes/arities, not one corpus |
| **E1′** HGED correlation | D | oracle-feasible slice only |

**What this fixes vs today:** A2/A3 stop classifying random blobs; the geometry
table stops being a single point and becomes axis-curves; G2/A4/E1′ stop being
disconnected corpora; bits is shown broadly; and every drawable experiment
(A1/A4/G3) is seeded from structures a reader can recognize on sight.

---

## 4. Feasibility-envelope protocol (run before committing any cell)

For each candidate cell (Stratum A design or Stratum B grid point):

1. Sample a pilot of ~30 instances under the cell's seeds.
2. Measure `w*_c` wall-clock at p50/p90 under a fixed budget (e.g. 30 s).
3. Admit the cell only if p90 ≤ budget with 0 DNFs; else record it as
   **out-of-envelope** and drop it *with a logged reason*.
4. For Stratum D, additionally measure exact-HGED all-pairs memory/time
   (the `(10,8)` ceiling and the cross-ladder branch-and-bound blow-up are known;
   respect them).

The admitted region is plotted as the **feasibility envelope** (`w*_c` cost vs
`n`, faceted by symmetry regime and arity). This doubles as the paper's honest
scalability figure — the exponential-`w*_c` limitation stops being an apology and
becomes a measured boundary.

---

## 5. Standardization & reporting rules (apply everywhere)

- **Fixed triple.** One `(k, h, vocabulary)` per corpus, stated in the methods.
  Never mix `d_I` values across `k`.
- **Realized-parameter table.** Every corpus ships a table of realized
  `n, m, density, arity histogram, connectivity, N, families, seeds`.
- **Competitor parity.** Every representation is computed on the *identical*
  instances and seeds; the distance caches (`D.npy`) are shared, as they already
  are for A1→A2→A3.
- **`D̂` censoring flag.** Any censored `D̂` (rides to the search cap) is labeled
  `≥ cap` with the cap value in-cell — never a bare number.
- **Seeds printed.** Into the result JSON content, not just the filename.
- **Arity-sweep analysis discipline.** Across `k`: compare ν, `D̂`, stress,
  hubness skew (shape descriptors) and within-`k` rankings; do not pool raw `d_I`.

---

## 6. NEW experiment — G3: controlled single-parameter geometry response

**Yes, add it.** The methodology already has G2 (aggregate single-edit
sensitivity histograms + ladder monotonicity). What is *missing*, and what the
visualization goal specifically calls for, is a **designed, one-factor-at-a-time
"move one value of the hypergraph, watch the geometry respond"** study with
recognizable, drawable instances. G3 is that study. It is HGED-free (budgets are
known by construction), it consumes the local-sensitivity and ladder-response
invariants (no orphan geometry), and it is the natural home for the hypergraph
visualizations.

**Difference from G2.** G2 answers "how big is a typical single edit?"
(magnitude, aggregated). G3 answers "as I move *one specific structural knob*
monotonically, where does the object travel in the geometry, and is that travel
smooth, monotone, and decodable?" — direction and trajectory, per move, visualized.

### The five move axes (OFAT — vary one, hold the rest)

Starting from a base `H_0` drawn from a Stratum A design (so the base and every
step are drawable):

| Axis | The move (repeated to make a sequence) | Structural meaning |
|---|---|---|
| M1 **vertex growth** | add one vertex into an existing edge (`V` op) | `n ↑`, density held |
| M2 **densification** | add one hyperedge over existing vertices (`C` op) | `m ↑` at fixed `n` |
| M3 **arity increase** | grow one edge's arity `a → a+1` | `k`-profile ↑ (mind the triple: analyze per base `k`) |
| M4 **incidence edit** | add/remove one vertex–edge incidence (Qin op) | fine-grained, the drift probe |
| M5 **symmetry break** | one edit moving a symmetric design toward/away from a random layout | tie/avalanche probe |

Each axis produces a sequence `H_0, H_1, …, H_T` with **known accumulated budget
`t`**.

### Measured responses (per axis, per step)

- **Response curve:** `d_I(H_0, H_t)` and step increments `s_t = d_I(H_{t-1}, H_t)`
  vs `t` — magnitude, monotonicity, smoothness.
- **Embedding trajectory:** the path `{H_t}` projected onto the A1 MDS map — is
  the trajectory smooth/continuous, or does it jump (avalanche)?
- **Curvature contribution:** does the move push the corpus's non-Euclidean mass
  `ν` up or down (does this structural change add or remove Euclidean-embeddable
  structure)?
- **Sensitivity-by-move-type:** `s(e)` distribution *conditioned on the axis* —
  which structural knob the geometry is most/least sensitive to.
- **Decodability:** every `H_t` is decoded via S2H and **drawn**, confirming the
  trajectory passes through valid, recognizable hypergraphs.

### Competitor contrast (reuses the cast)

Run the identical `{H_t}` sequences through each competitor representation and
plot the parallel trajectories:
- **nauty-Levi**: expected to avalanche (the G2 IQR 10–20 contrast) — trajectory
  jumps discontinuously; visually striking.
- **WL / NetLSD / HPD**: smooth or not, but **no decoder** — cannot draw the
  intermediates. G3 makes the decodability differentiator (A4) a *moving picture*,
  not a single figure.

### Visualization protocol (the reason G3 exists)

For one exemplar per axis: a filmstrip of the drawn hypergraphs `H_0 … H_T`
(HyperNetX / incidence drawing; `n ≲ 20` for readability), the overlaid MDS
trajectory, and the `(t, d_I)` response curve — side by side. This is the figure
that lets a reader *see* that a structural move corresponds to a coherent motion
in the metric space, and that only IsalHG can show the intermediates.

### Acceptance for G3

Per axis: response monotone (report the monotone fraction, as ladders do); MDS
trajectory continuity quantified (max single-step embedded jump vs median);
`ν`-contribution sign reported; all `H_t` decoded and drawn; competitor
trajectories shown with nauty's discontinuity and the vectors' non-decodability
made explicit.

---

## 7. Migration plan (concrete changes)

1. **Add a labeled known-design seed loader** feeding `PlantedFamilyDataset`'s
   existing `seeds=` argument (no generator rewrite; the vendored STS catalog is
   the first source). → replaces random-seed families in Stratum A.
2. **Add the Stratum B sweep configs** (full factorial `n × density × arity ×
   generator`), reusing `erdos_renyi` / `chung_lu`.
3. **Re-seed Stratum C ladders** from design bases + random controls.
4. **Add realized-parameter logging** to the dataset metadata emit (record `m`,
   arity histogram, density — not just request params).
5. **Add the feasibility-envelope pilot** as a preflight step gating every cell.
6. **Add the G3 experiment** (OFAT sequence generator + response/trajectory
   analysis + visualization module).
7. **Fold the stats pass** (`STATS_PASS_PLAN.md`) into the sweep so every sweep
   point carries a CI + paired competitor test.
8. **Point E1′ and bits** at slices of the master corpus.

## 8. Acceptance criteria for "strict data" (the whole paper)

- [ ] Every experiment names its master-corpus slice; no bespoke generators.
- [ ] Every headline geometry/application claim is shown across ≥ 3 values on each
      of the `n`, density, and arity axes (curves, not points), each with a CI.
- [ ] Arity `k ∈ {3,5,7,10}` is measured; the `k = 10` advertised cap is exercised
      (Stratum B random, where feasible).
- [ ] A2/A3 classes are known families with meaningful labels; ARI/NMI are
      reported against them, not against random blobs.
- [ ] Every corpus ships a realized-parameter table and printed seeds.
- [ ] The feasibility envelope is a reported figure; every dropped cell has a
      logged reason.
- [ ] `(k, h, vocabulary)` fixed and stated; no raw `d_I` pooled across `k`.
- [ ] Real data covers the designs catalog + ≥ 1 gate-passing real-world corpus.
- [ ] G3 delivers, per move axis, a decoded+drawn trajectory with a competitor
      contrast.
