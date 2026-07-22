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

**Seed catalog** (all standard, arity-controlled; feasibility-gated per §4):

| Family | Uniform arity `k` | Example orders `n` | Symmetry | Notes |
|---|---|---|---|---|
| Steiner triple system STS(v) | 3 | 7, 9, 13, 15 | high | `v ≡ 1,3 (mod 6)`; vendored catalog exists |
| Affine plane AG(2,q) | q | 9 (q=3), 16 (q=4), 25 (q=5) | high | lines = arity `q`; gives arity 3–5 |
| Projective plane PG(2,q) | q+1 | 7 (Fano), 13, 21 | high | lines = arity `q+1`; arity 3–5 (higher orders gate out) |
| Steiner S(2,4,v) / S(2,5,v) | 4 / 5 | 13,16 / 21,25 | high | direct arity-4/5 designs |
| Generalized quadrangle GQ(2,2) | 3 | 15 | very high | the doily; already a fixture |
| Complete `k`-uniform K_n^(k) | k | small n | maximal | dense, symmetric stress test |
| Loose / tight `k`-uniform path & cycle | k | any | low | sparse, easy to draw; contrast to designs |

**Class label = family type** (e.g. "STS", "projective-plane", "complete",
"loose-path"). **Members per class** = the base design plus `r` *non-isomorphic,
connectivity-preserving* Qin perturbations of bounded budget `t` (small enough
that family identity is visually preserved — this is checkable *because* the
instances are drawable). Permuted copies are the `d_I = 0` sanity anchor only,
never class members.

**Feasibility reality (important, and it works in our favor).** `w*_c` cost rises
with *both* symmetry and `n`. Highly symmetric high-order designs (PG(2,5) n=31,
PG(2,7) n=57) will gate out. So Stratum A delivers **interpretability and arity
3–5 at small n**; it is *not* where high arity or large `n` come from.

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
