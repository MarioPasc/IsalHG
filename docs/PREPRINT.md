# IsalHG — Preprint Plan

**Status.** Authoritative as of 2026-06-17. PI directive (E.
López-Rubio, 2026-06-17) replaces the prior correctness-on-STS plan
with a **synthetic random-hypergraph characterisation study**. The
preprint maps the regime in which IsalHG outperforms the Levi
incidence baselines (nauty, Traces, bliss) across three axes: vertex
count, edge probability, and arity. The STS catalog and every other
catalog cohort move to the full empirical paper.

**Companion documents.**
- `docs/DATA.md` §3 — full synthetic-generator narrative (Cohort B).
- `docs/PROPOSAL.md` Tier 2 — original scaling-sweep specification
  (the preprint is a compressed-grid subset).
- `docs/CODE_DESIGN.md` — module organisation.

---

## 1. Scope and intent

The preprint addresses one question:

> *In which regime of (vertex count `n`, edge probability `p`, arity
> `r`) does IsalHG's native canonical-string fingerprint compute faster
> and consume less memory than the Levi-incidence-graph route through
> nauty, Traces, and bliss?*

The question is **descriptive**, not assertive. We do not commit a
priori to a winning regime; we map the (`n`, `p`, `r`) space and report
where IsalHG dominates, where it is competitive, and where the Levi
baselines win. The contribution is the characterisation itself —
following the framing "*saber en qué tipos de hipergrafos es más
ventajosa nuestra propuesta con respecto a sus competidoras*" (PI
directive, 2026-06-17).

What the preprint does **not** claim:
- No correctness claim on published combinatorial designs. The
  Kaski-Östergård STS catalog, GQ(2, 2) doily, and all real-world
  cohorts (HIC-12, ARB, XGI-DATA, Hypergraphx, LLM4Hypergraph) are
  reserved for the full empirical paper.
- No expressiveness claim against Weisfeiler-Leman variants.
- No real-world deduplication claim.
- No theoretical complexity bound. Empirical exponents only.

The preprint stakes a flag on the canonical-string framework's
*empirical competitiveness profile* while the full validation campaign
(Tiers 1, 3, 4, 5 of PROPOSAL) continues in parallel.

---

## 2. Title and abstract sketch

**Working title.** *IsalHG: A Native Canonical-String Algorithm for
Hypergraph Isomorphism — Empirical Characterisation on Random
Hypergraphs.*

**Abstract (≤ 200 words, draft).**

We introduce IsalHG, an exact native canonical-string algorithm for
hypergraph isomorphism testing. Where the established route reduces
the input hypergraph to the Levi incidence bipartite graph and invokes
a graph-isomorphism engine (nauty, Traces, or bliss), IsalHG encodes
the hypergraph directly through a compact instruction alphabet
executed against a circular-doubly-linked-list virtual machine. We
benchmark all four methods across a three-dimensional grid of random
uniform Erdős-Rényi hypergraphs spanning vertex counts `n ∈ {50, 200,
1000}`, arities `r ∈ {3, 5}`, and edge probabilities calibrated to
expected edge densities of 1, 5, and 25 hyperedges per vertex, with
10 seeds per cell. We report per-cell median wall-clock fingerprint
cost, peak resident-set size, and four-way partition agreement against
pynauty as ground truth. The resulting map identifies the (`n`, `p`,
`r`) region in which IsalHG's native route outperforms the Levi
reduction on wall-clock and memory, the region in which it is
competitive, and the region in which the Levi engines dominate. The
characterisation grounds the full empirical campaign documented
separately.

---

## 3. Cohort

**Generator.** XGI's
`xgi.generators.uniform.uniform_erdos_renyi_hypergraph(n, m, p,
p_type='prob', multiedges=False, seed=seed)` (Landry et al. 2023). For
each vertex set of size `n` and target arity `r`, each of the
`C(n, r)` possible hyperedges is included independently with
probability `p`. Per the PI's directive (2026-06-17, option (b)
second formulation), density is reported as the edge probability
`p = m / C(n, r)`.

**Grid.** Compressed sweep across three axes.

| Axis | Values | Rationale |
|---|---|---|
| Vertex count `n` | 50, 200, 1000 | Three decade-spaced sizes covering small (Tier 1-like), medium, and the lower end of Tier 2. n=1000 is the largest size at which we expect every backend to terminate within a 600 s per-fingerprint timeout under all density settings. |
| Arity `r` | 3, 5 | r=3 matches the Steiner triple system regime and the bulk of the design-theory literature; r=5 stresses the alphabet `Σ_HG` more (longer `V_{i,j}` and `C_i` token suffixes) and produces denser Levi graphs (`\|B(H)\| = n + m` with larger `m` per probability). |
| Edge probability `p` | per-cell, calibrated | For each (n, r) cell, `p` is chosen at three target densities corresponding to expected edge counts `E[m] = c · n` for `c ∈ {1, 5, 25}`; concretely `p(n, r, c) = c · n / C(n, r)`. Reported in tables as both `p` and the resulting realised `m/n` for cross-comparability with the random-hypergraph literature (Chodrow 2020). |
| Seeds | 10 per cell | Median + IQR per cell. Reproducible via `np.random.default_rng(seed)` for `seed ∈ {0, ..., 9}`. |

Total: 3 × 2 × 3 × 10 = **180 random hypergraph instances**, each
fingerprinted by 4 backends = **720 fingerprint computations**, plus
**90 paired isomorphism decisions** (one positive pair per cell from
`core.permute(H, σ)` to verify within-cell partition agreement).

**Realised parameter table** (illustrative; verified at cohort
construction):

| `n` | `r` | `c` | `p = c·n / C(n,r)` | `E[m]` | `\|B(H)\| = n + E[m]` |
|---|---|---|---|---|---|
| 50 | 3 | 1 | 2.55e-3 | 50 | 100 |
| 50 | 3 | 5 | 1.28e-2 | 250 | 300 |
| 50 | 3 | 25 | 6.38e-2 | 1250 | 1300 |
| 50 | 5 | 1 | 2.36e-5 | 50 | 100 |
| 50 | 5 | 5 | 1.18e-4 | 250 | 300 |
| 50 | 5 | 25 | 5.90e-4 | 1250 | 1300 |
| 200 | 3 | 1 | 1.51e-4 | 200 | 400 |
| 200 | 3 | 5 | 7.55e-4 | 1000 | 1200 |
| 200 | 3 | 25 | 3.78e-3 | 5000 | 5200 |
| 200 | 5 | 1 | 4.71e-8 | 200 | 400 |
| 200 | 5 | 5 | 2.36e-7 | 1000 | 1200 |
| 200 | 5 | 25 | 1.18e-6 | 5000 | 5200 |
| 1000 | 3 | 1 | 6.01e-6 | 1000 | 2000 |
| 1000 | 3 | 5 | 3.01e-5 | 5000 | 6000 |
| 1000 | 3 | 25 | 1.50e-4 | 25000 | 26000 |
| 1000 | 5 | 1 | 1.20e-10 | 1000 | 2000 |
| 1000 | 5 | 5 | 6.02e-10 | 5000 | 6000 |
| 1000 | 5 | 25 | 3.01e-9 | 25000 | 26000 |

The two density definitions PI introduced — `m/n` and
`m / C(n, r)` — agree up to the deterministic mapping above. We use
`p = m / C(n, r)` as the axis label (PI's option b, second
formulation) and supply `m/n` in the supplementary for readers from
the random-hypergraph tradition.

**Reproducibility.** All seeds are pinned. The cohort regenerates
deterministically from a single YAML
(`experiments/configs/preprint_random_sweep.yaml`) plus the seed list
`{0, ..., 9}`. No external data, no checksums needed — the entire
cohort is reproducible from XGI + a 12-line config.

---

## 4. Methods

### 4.1 Backends

Four backends wired through the `IsoBackend` ABC (`docs/CODE_DESIGN.md`
§2.1):

- `isalhg` — IsalHG canonical string via `core.canonical` +
  `algorithms.greedy_min`.
- `pynauty_levi` — nauty 2.8.8 via the `pynauty` 2.8.8.1 Python
  binding, applied to the 2-coloured Levi incidence graph (decision
  I47).
- `bliss_levi` — bliss 0.77 via `python-igraph`'s
  `canonical_permutation` / `isomorphic_bliss` on the same Levi
  graph.
- `traces_levi` — Traces via subprocess to the `dreadnaut` CLI
  shipped with the `nauty` 2.9 conda-forge package, parsing the
  canonical `b6` output line.

All four implement `fingerprint(H) -> bytes` and
`are_isomorphic(H1, H2) -> bool`.

### 4.2 Protocol

The `FingerprintTimingProtocol` (`isalhg.protocols.fingerprint_timing`,
to be wired) drives the matrix `Backend × Cell × Seed`. For each
backend M, each cell `(n, r, c)`, and each seed s:

1. Construct `H_{n,r,c,s}` via
   `xgi.uniform_erdos_renyi_hypergraph(n, r, p(n,r,c), p_type='prob', seed=s)`.
2. Convert to `SparseHypergraph` via `XGIAdapter`.
3. Measure `T_M(H) = time.perf_counter()` delta of
   `M.fingerprint(H)`, median over 10 repeats per instance to
   suppress per-call noise.
4. Measure `R_M(H)` = `resource.getrusage(RUSAGE_SELF).ru_maxrss`
   delta over the same call.
5. Persist `(M, n, r, c, s, T_M, R_M, fingerprint_bytes_length)` in
   `experiments/outputs/preprint_random_sweep/<cell>/<seed>.json`.

A backend that exceeds the 600 s per-fingerprint wall-clock budget is
recorded as DNF (did-not-finish) for that (instance, backend) pair.
DNF cells are reported in the characterisation map as a distinct
category, not aggregated into the runtime medians.

### 4.3 Ground truth and correctness invariant

Each cell `(n, r, c)` additionally yields one positive pair
`(H, π(H))` via `core.permute(H, σ)` (decision I44) with σ pinned by
the cell's seed. The four backends compute `are_isomorphic(H, π(H))`
and the protocol asserts:

- `iso_M(H, π(H)) = True` for all M (no false negatives on the
  positive pair).
- `iso_M(H_{s_1}, H_{s_2}) = iso_M'(H_{s_1}, H_{s_2})` across all
  backend pairs (M, M') for the 45 cross-seed pairs per cell
  (four-way partition agreement at the cell level).

The combination is sufficient to certify pairwise iso correctness on
each cell up to the unlikely event that nauty/Traces/bliss all agree on
a wrong answer for a pair. Disagreement between IsalHG and the three
Levi backends on any pair is recorded and flagged.

### 4.4 Reporting

Per (n, r, c) cell, the preprint reports:

- **Median wall-clock per fingerprint** across the 10 seeds, per
  backend, with IQR.
- **Median peak `max_rss`** across the 10 seeds, per backend, with
  IQR.
- **Fingerprint byte length** distribution per backend.
- **Cross-backend partition agreement** indicator (boolean per cell:
  did all four backends induce the same partition?).
- **Speedup ratio** `T_best-of-Levi / T_isalhg` per cell, geometric
  mean across seeds.
- **DNF count** per backend per cell.

### 4.5 Hardware

Target: **Picasso CPU partition** (UMA HPC), SLURM-submitted via the
`picasso-sbatch` skill. Iso testing is CPU-bound for every backend
(nauty, Traces, bliss canonical labelling and IsalHG's
canonical-string encoding all run single-threaded on CPU); no GPU
needed. The sweep is embarrassingly parallel — every
`(backend, n, r, c, seed)` fingerprint is independent — so we follow
the IsalSR convention of one SLURM **array job** with one task per
unit of work, scheduled across the CPU pool.

Layout. The 180 hypergraph instances × 4 backends × 10 timing repeats
decompose naturally as a SLURM array with one task per
`(backend, n, r, c, seed)` tuple = 720 array tasks. Each task is
single-core (`--cpus-per-task=1`), short-walled
(`--time=00:45:00` covering the 600 s per-fingerprint timeout × 10
repeats + overhead), low-memory (`--mem-per-cpu=8G`, raised to
`16G` for the `n=1000, r=5, c=25` cells), and writes its result JSON
under `experiments/outputs/preprint_random_sweep/<cell>/<seed>/<backend>.json`.
Job array dispatch uses the standard Picasso CPU partition with no
`--constraint=dgx` and no `--gres=gpu`.

Why this scales. Picasso's CPU pool absorbs the 720 array tasks in
parallel (subject to the user's concurrent-task cap); the
slowest-cell wall-clock approximates the total wall-clock to first
result, not the sum of all tasks. This is the same pattern IsalSR
uses for its scaling sweep across model × dataset × seed cells.

Local fallback: the smaller cells (n ∈ {50, 200}) run on either
local workstation for development iteration; the orchestrator's
idempotent skip-if-exists JSON persistence (PROPOSAL Reproducibility
§) lets a single sweep be partially executed locally and finished on
Picasso without rerunning completed cells.

---

## 5. Headline deliverable

The preprint's headline is a **characterisation map**, not a single
FP/FN table. Three primary figures:

**Figure 1 — Wall-clock characterisation.** A heat-grid (rows: arity
`r` × density `c`, columns: vertex count `n`) coloured by
`log_10(T_isalhg / T_best-of-Levi)`. Cells where IsalHG dominates are
blue (ratio < 1, log < 0); cells where Levi dominates are red (ratio
> 1, log > 0); white near 0. DNF cells are crosshatched.

**Figure 2 — Memory characterisation.** Same grid coloured by
`max_rss(IsalHG) / max_rss(best-of-Levi)`. Same colour convention.

**Figure 3 — Fingerprint byte-length characterisation.** Per-cell box
plot of `|fp(H)|` for each backend, log-scaled axis.

**Table 1 — Per-cell summary.** 18 rows (one per (n, r, c) cell), 5
columns (median T per backend, median R per backend, partition
agreement boolean, speedup ratio, DNF count). The "where IsalHG wins"
region is the subset of rows with speedup ratio > 1.

**Table 2 — Correctness invariant.** Single row asserting four-way
partition agreement across all 180 instances (boolean).

If the headline characterisation is "IsalHG wins in region X, loses in
region Y, competitive in region Z", that *is* the preprint's
contribution per PI's framing. The preprint is publishable regardless
of where the boundary falls, provided the correctness invariant holds
and the sweep completes (modulo DNFs which are themselves data).

---

## 6. Section structure (target: 8 pages two-column)

1. **Introduction** (~1 page). Hypergraph isomorphism, the Levi
   reduction, the gap that motivates a native algorithm. The
   preprint's descriptive question and the characterisation framing.
2. **The IsalHG canonical string** (~2 pages). `Σ_HG` alphabet, the
   VM state `(H, L, p_1, ..., p_k)`, S2H interpreter, H2S greedy
   encoder, structural tuples ξ and η, canonical-seed selection,
   tie-breaking cascade. One worked example on a small random
   hypergraph.
3. **Experimental design** (~1 page). §3-4 of this document
   compressed: generator, grid, protocol, ground truth, hardware.
4. **Results** (~2.5 pages). Figures 1-3, Tables 1-2, narrative
   walk-through of the characterisation map. Honest reporting of
   where IsalHG wins, ties, and loses.
5. **Related work** (~1 page). Levi reduction (Berge 1973,
   Beigel-Bernasconi 1999); IR canonical labelling (McKay 1981,
   McKay-Piperno 2014, Junttila-Kaski 2007); group-theoretic exact
   methods (Luks 1999, Babai-Codenotti 2008, Neuen 2022); native WL
   approximate methods (Feng 2024, Zhang 2025) — cited as
   predecessors, not benchmarked. Random hypergraph generation
   tradition (Chodrow 2020, Landry 2023). IsalGraph and IsalSR
   sibling projects.
6. **Conclusion and future work** (~0.5 page). The characterisation
   identifies regime X as the operational sweet spot for the native
   canonical-string route. Pointers to the full empirical paper for
   the Kaski-Östergård STS catalog, the LLM4Hypergraph corpus, HIC-12
   partition agreement, and Tier 3 hardness families.
7. **References + supplementary**.

---

## 7. Acceptance criteria for the preprint

The preprint goes on arXiv iff:

1. **Sweep completes.** All 180 instances generated with pinned seeds.
   DNF cells are reported, not omitted.
2. **Correctness invariant holds.** Cross-backend partition
   agreement on every cell where every backend completes (DNFs
   excused). Any disagreement is investigated and either resolved as
   a bug fix or reported as a Theorem-2 counterexample (PROPOSAL F28
   framing).
3. **Characterisation map populated.** Figures 1-3 and Tables 1-2
   produced. The "where does IsalHG win" question receives an
   answer, even if the answer is "nowhere in the tested grid" — that
   is itself a publishable finding per the PI's framing.
4. **Reproducibility artefact shipped.** The YAML config, the seed
   list, and the per-cell result JSONs are committed under
   `experiments/outputs/preprint_random_sweep/` and referenced in the
   paper's supplementary.

---

## 8. What is explicitly out of scope

| Item | Reserved for |
|---|---|
| Kaski-Östergård STS catalogs (STS(7/9/13/15), STS(19) `1k_sample`) | Full empirical paper (Tier 1 published-iso-class cohort) |
| GQ(2, 2) doily and other named combinatorial designs | Full empirical paper |
| HIC-12 partition agreement | Full empirical paper (Tier 5) |
| LLM4Hypergraph three-way comparison (decision I49) | Full empirical paper |
| ARB / XGI-DATA / Hypergraphx structural calibration | Full empirical paper (Tier 4) |
| Feng / Zhang WL-failure fixtures | Phase 3.5 + full empirical paper |
| Tier 3 hardness families (PG(2, q), large-Aut STS, GQ(2,4)/(3,5), non-group Latin squares) | Full empirical paper |
| Chung-Lu heavy-tailed degree generator | Full empirical paper (Tier 2 R3) |
| Theorems 1, 2, 3 (expressiveness, completeness, backtracking bound) | Theoretical paper (JSC / SIDMA) |
| HG-CFI construction | Companion paper (open) |

The preprint is the smallest publishable claim that maps IsalHG's
competitive regime against the Levi baselines on a controllable
synthetic distribution. Everything else waits for the full paper.

---

## 9. Implementation tickets (to land the preprint)

In dependency order:

1. **Wire the Erdős-Rényi dataset class.** Fill `__iter__` and
   `metadata` in `src/isalhg/datasets/synthetic/erdos_renyi.py` (~30
   lines). The class takes `(n, r, p, seed)` and yields one
   `DatasetItem` per seed. Register in `datasets/registry.py` under
   `random_erdos_renyi`.
2. **Implement `metrics/runtime.py`.** Wall-clock helper
   (`time.perf_counter` median over `n_repeats`) and peak-RSS helper
   (`resource.getrusage(RUSAGE_SELF).ru_maxrss` delta). ~40 lines.
3. **Implement `protocols/fingerprint_timing.py`.** Subclass
   `BenchmarkProtocol`. Per (backend, dataset, seed): call
   `metrics.runtime.measure_fingerprint(backend, hypergraph)`, return
   a `ProtocolResult` with `measurements = {median_time, iqr_time,
   peak_rss, fp_bytes_length}`. Register in `protocols/registry.py`.
   ~80 lines.
4. **Add DNF / timeout handling.** Wrap `backend.fingerprint(H)` in
   a `signal.alarm`-based 600 s watchdog (POSIX-only; matches the
   PROPOSAL E26 convention). Persist DNF status in the result JSON.
   ~30 lines.
5. **Add the positive-pair partition check.** Per cell, generate one
   `(H, σ(H))` pair via `core.permute(H, σ)` and assert all four
   backends return `True` from `are_isomorphic`. ~20 lines inside the
   protocol.
6. **Add the cross-backend partition assertion.** Per cell with 10
   seeds, build the 4-backend partition over the 10 hypergraphs and
   assert they all coincide. ~30 lines.
7. **Write `experiments/configs/preprint_random_sweep.yaml`.** 18
   cells × 4 backends, seed list `{0, ..., 9}`. Single file.
8. **Generate the SLURM array script via the `picasso-sbatch`
   skill.** Single array job, 720 tasks (one per
   `(backend, n, r, c, seed)` tuple), CPU partition, no GPU.
   `--cpus-per-task=1`, `--time=00:45:00`, `--mem-per-cpu=8G`
   (raised to `16G` on the `n=1000, r=5, c=25` cells via a
   per-task override or a separate array). Pattern matches IsalSR's
   scaling sweep launcher.
9. **Run the sweep on Picasso.** Submit the array; monitor via
   `squeue` and the orchestrator's incremental JSON output tree.
   Wall-clock to last result depends on Picasso's concurrent-task
   cap and the slowest cell; idempotent skip-if-exists allows
   resubmission of only the DNF / failed tasks.
10. **Build `experiments/analysis/preprint_figures.py`.** Generates
    Figures 1-3 and Tables 1-2 from the JSON output tree. ~150 lines
    with `matplotlib` + `pandas`.
11. **Write the preprint.** Against the §6 structure.
12. **arXiv submission.** `cs.DM` (Discrete Mathematics) primary,
    `cs.DS` (Data Structures and Algorithms) secondary.

Steps 1-7 are core implementation; steps 8-10 are run-and-analyse;
steps 11-12 are writing and submission.

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
- Feng, Y., Han, J., Ying, S. & Gao, Y. (2024). *Hypergraph
  Isomorphism Computation.* IEEE TPAMI 46(5):3880-3893.
  arXiv:2307.14394.
- Zhang, D. et al. (2025). *Improved Expressivity of Hypergraph
  Neural Networks through High-Dimensional Generalized
  Weisfeiler-Leman Algorithms.* ICML 2025. PMLR v267.
- Chodrow, P.S. (2020). *Configuration Models of Random Hypergraphs
  and their Applications.* J. Complex Networks 8(3):cnaa018.
  arXiv:1902.09302.
- Landry, N.W., Lucas, M., Iacopini, I. et al. (2023). *XGI: A
  Python package for higher-order interaction networks.* JOSS
  8(85):5162.
- López-Rubio, E. & Pascual-González, M. (2026). *Representation of
  Graphs by Sequences of Instructions.* Preprint (IsalGraph
  sibling).
- López-Rubio, E., Pascual-González, M. & Thurnhofer-Hemsi, K.
  (2026). *Representation of Directed Acyclic Graphs by Sequences of
  Instructions for Symbolic Regression.* IEEE TPAMI submission
  (IsalSR sibling).
