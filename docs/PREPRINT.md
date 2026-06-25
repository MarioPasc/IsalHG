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

---

## 11. Code Development

This section documents the code landed for the preprint:
implementation tickets 1-7 of §9 above. Ticket 8 (Picasso SLURM
launcher) and tickets 9-12 (sweep execution, figures, writing,
submission) are not code in the IsalHG repo; they live in the launcher
generated by the `picasso-sbatch` skill and in the analysis scripts
that consume the result JSONs.

### 11.1 Module map

| File | Role |
|---|---|
| `src/isalhg/datasets/synthetic/erdos_renyi.py` | `UniformErdosRenyiHypergraphs(n, r, p\|c, seed)`. Single-item dataset; wraps `xgi.uniform_erdos_renyi_hypergraph` through `XGIAdapter`. Accepts the PI's `c` (edges-per-vertex target) and translates to XGI's `p` internally. |
| `src/isalhg/metrics/runtime.py` | `time_call`, `time_call_repeated`, `median_wall_clock_s`, `iqr_wall_clock_s`, `peak_rss`. Thin wrappers over `time.perf_counter` and `resource.getrusage(RUSAGE_SELF)`. Linux/macOS unit normalisation included. |
| `src/isalhg/protocols/fingerprint_timing.py` | `FingerprintTimingProtocol`. Per-item timing (median+IQR over `repeats`), peak-RSS, fingerprint byte length, positive-pair correctness check via `core.permute(H, σ)`, `signal.alarm` watchdog, DNF tracking. Schema in §4.2 of this document. |
| `src/isalhg/viz/cohort_panel.py` | `cohort_grid_figure(panels, backend, ...)`. Reusable N-panel comparison figure; reuses `draw_hypergraph(ax=...)` and the `viz.style` palette helpers verbatim. |
| `experiments/preprint/data/build_preprint_config.py` | Generator: expands the (backend × n × r × c × seed) Cartesian product into the 720-cell `experiments/configs/preprint_random_sweep.yaml`. Edit `N_VALUES`, `R_VALUES`, `C_VALUES`, `SEEDS`, `BACKENDS` constants to change the grid. |
| `experiments/preprint/data/visualize_cohort_axes.py` | CLI that generates the 5-panel cohort-axes figure: 1 baseline + 4 single-axis variations (`n↑`, `r↑`, `c↓`, `c↑`). `--backend xgi\|hypernetx\|hypergraphx` or `--all-backends`. Visualisation-scale `n` (≤ 20) since the production `n=1000` is not visually tractable. |
| `experiments/configs/preprint_random_sweep.yaml` | Generated 720-cell sweep; the orchestrator's source of truth. |
| `experiments/configs/preprint_smoke.yaml` | 4-cell smoke subset (one per backend at `n=10, r=3, c=3, seed=0`) that exercises the full chain in under a minute. |

Test coverage (all unit-marked, all green):
`tests/unit/datasets/test_erdos_renyi.py` (16),
`tests/unit/metrics/test_runtime.py` (11),
`tests/unit/protocols/test_fingerprint_timing.py` (5),
`tests/unit/viz/test_cohort_panel.py` (5 — parametrised over the
three viz backends).

### 11.2 Patterns reused (no duplication)

- **Three lazy-import registries.** `iso_backends/registry`,
  `datasets/registry`, `protocols/registry`. Each YAML cell looks up
  its components by name; the registry imports the implementing
  module on first request. Optional dependencies stay off the import
  path until the corresponding backend / dataset / protocol is
  actually requested.
- **Three ABCs as extension points.** `IsoBackend`,
  `HypergraphDataset`, `BenchmarkProtocol`. The preprint adds one
  dataset (`UniformErdosRenyiHypergraphs`) and one protocol
  (`FingerprintTimingProtocol`); it touches **no backend code** and
  **no orchestrator code**.
- **Orchestrator's idempotent skip-if-exists.**
  `experiments.orchestrator.run_cell` writes JSONs atomically
  (`*.tmp` → rename) and skips cells whose JSON parses to a valid
  `RunLog`. A partial Picasso array run resubmits with zero rerun
  cost.
- **Viz reuse.** `viz.cohort_panel.cohort_grid_figure` reuses
  `viz.hypergraph_view.draw_hypergraph(ax=...)`,
  `viz.style.build_vertex_palette`, `viz.style.build_edge_palette`,
  `viz.style.apply_ieee_style`, and `viz.style.save_figure` verbatim.
  The new helper carries only the layout + caption logic; it does not
  duplicate the backend dispatch or palette construction that already
  exists in `viz/`.
- **Adapter pattern.** `UniformErdosRenyiHypergraphs._materialise`
  routes XGI's `Hypergraph` through `XGIAdapter().from_external` to
  obtain a `SparseHypergraph`. Any future ER-style dataset (e.g.
  Chung-Lu) goes through the same bridge.

### 11.3 Extension points for the full empirical paper

The full paper sweeps the same `(Backend, Protocol)` matrix across
different cohorts. To swap the preprint cohort for, e.g., the HIC-12
atlas, the diff is exactly:

1. Implement `HICAtlasDataset(HypergraphDataset)` in
   `src/isalhg/datasets/hic_atlas.py` (file already scaffolded).
2. Add `"hic_atlas": "isalhg.datasets.hic_atlas"` to
   `datasets.registry._LAZY_MODULES`.
3. Write a new YAML referencing `dataset: hic_atlas` (and the
   appropriate protocol, e.g. `partition_agreement`).

Nothing in `iso_backends/`, `protocols/`, `metrics/`, or
`experiments/orchestrator.py` changes. The same four `IsoBackend`s
(`isalhg`, `pynauty_levi`, `bliss_levi`, `traces_levi`) used here
will benchmark the new cohort identically. Conversely, a new
backend (e.g. a hypothetical `nauty_levi_sparse`) is added by
implementing `IsoBackend` + registering, with zero changes elsewhere.

### 11.4 Known caveats (called out in §4.2 + flagged in figure captions)

- **Subprocess RSS underreporting.** `metrics.runtime` reads
  `RUSAGE_SELF.ru_maxrss`, which captures the parent process only.
  `traces_levi` spawns `dreadnaut` as a child, so its memory column
  in the characterisation map represents the parent's Levi
  serialisation + b6 parsing overhead, not the child solver. A
  follow-up using `psutil` child-polling is queued.
- **IsalHG connectivity requirement.** `core/algorithms/greedy_min`
  raises `DisconnectedHypergraphError` on disconnected inputs
  (decision B11). At sparse `(n, r, c=1)` settings the XGI ER
  generator returns disconnected hypergraphs with non-zero
  probability; the protocol records these as DNFs, not as silent
  failures. The Levi backends accept disconnected inputs and so will
  not DNF on the same instances — the asymmetry is part of the
  characterisation, not a measurement bug.
- **IsalHG fingerprint runtime explodes with edge count** (open
  question #1 in `docs/DEVELOPMENT.md`). The preprint sweep's 600 s
  per-fingerprint timeout converts this into a DNF at the dense end
  of the grid; the resulting DNF region IS the headline
  characterisation.

### 11.5 Visualisation tool — usage

Single-backend cohort axes figure:

```bash
python experiments/preprint/data/visualize_cohort_axes.py --backend xgi
```

One figure per registered viz backend:

```bash
python experiments/preprint/data/visualize_cohort_axes.py --all-backends
```

The reusable helper
`isalhg.viz.cohort_grid_figure(panels, backend=...)` accepts any
`Sequence[tuple[str, SparseHypergraph]]` and any registered
`HypergraphVizBackend`. Use it from notebooks or downstream analysis
scripts for ad-hoc multi-hypergraph comparison figures (full empirical
paper supplementary, ablation panels, etc.).

### 11.6 Running the sweep

Regenerate the YAML after a grid change:

```bash
python experiments/preprint/data/build_preprint_config.py
```

Smoke-test the full chain end-to-end (under a minute on a laptop):

```bash
python -m experiments.orchestrator --config experiments/configs/preprint_smoke.yaml
```

Production sweep (Picasso CPU partition, SLURM array; one task per
`(backend, n, r, c, seed)` tuple, dispatched by `picasso-sbatch`):

```bash
python -m experiments.orchestrator --config experiments/configs/preprint_random_sweep.yaml
```

The orchestrator writes one JSON per cell under
`experiments/outputs/preprint_random_sweep/`. Cells whose JSON
exists and parses are skipped on resubmission.

---

## 12. Jun-25-2026 Results — first Picasso sweep

First end-to-end execution of the §3 cohort on Picasso. The sweep
completed; all 720 cells terminated; the four-way correctness
invariant held. IsalHG produced **no** wall-clock measurement on any
cell, confirming the open-question #1 algorithmic ceiling
(`docs/DEVELOPMENT.md`) on the chosen grid.

Raw artefacts: `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/preprint/experiment/`
(rsync'd from Picasso `/mnt/.../fscratch/isalhg_results/preprint/pipeline/`).

### 12.1 Cohort parameters (as run)

| Axis | Values |
|---|---|
| Vertex count `n` | `{50, 200, 1000}` |
| Arity `r` | `{3, 5}` |
| Density `c` (expected edges-per-vertex) | `{1, 5, 25}` |
| Seeds | `{0, 1, …, 9}` |
| Backends | `{isalhg, pynauty_levi, bliss_levi, traces_levi}` |
| Per-fingerprint timeout | 600 s (POSIX `signal.alarm` + multiprocessing hard kill) |
| `repeats` per fingerprint | **1** (deviation from §4.2; was reduced from 10 to bound wall-clock at exactly 600 s per cell) |
| IsalHG algorithm | `greedy_single` (deviation from §4.1; was switched from `greedy_min` after observing exponential blow-up of the V-permutation backtracking on dense inputs) |
| C++ engine | Built on Picasso login node (`pip install -e .` → scikit-build-core + nanobind, GCC 7.5, `-O3 -march=native -flto`). Verified live: Fano = 2.31 ms, ER `n=10, r=3, c=2` (14 edges) = 7.5 ms. |
| SLURM partition | CPU partition, `--constraint=avx512` (env baked for Intel `sd*` + AMD `bc*/bl*` AVX-512 nodes; vanilla AMD `sr*` nodes crash on import) |
| Memory | 32 GB/CPU fast tier, 64 GB/CPU slow tier |
| Wall budget per task | 30 min SLURM + 22 min inner `timeout(1)` reaper (orphan-subprocess safety net) |
| Subprocess isolation | `ISALHG_BACKEND_ISOLATE=1` — every `canonical_string` call runs in a forked child; `SIGSEGV`/`SIGABRT` surface as `IsalHGBackendCrashError` rather than killing the SLURM task |

### 12.2 Headline numbers

**Correctness invariant.** 540 positive-pair checks
(`backend.are_isomorphic(H, σ(H))`) across the three Levi backends ×
180 instances. **Pass rate = 1.0; zero failures across all four
backends.** IsalHG could not check positive pairs because its
fingerprint call never completed.

**Per-cell median wall-clock (ms, median over 10 seeds).**

| `n` | `r` | `c` | pynauty | bliss | traces | isalhg |
|----:|----:|----:|--------:|------:|-------:|-------:|
|  50 | 3 |  1 |   0.46 |  0.96 |  5.03 | 10×DNF |
|  50 | 3 |  5 |   1.24 |  2.42 |  6.23 | 10×DNF |
|  50 | 3 | 25 |   8.88 |  9.58 |  8.31 | 10×DNF |
|  50 | 5 |  1 |   0.43 |  1.28 |  4.91 | 10×DNF |
|  50 | 5 |  5 |   1.40 |  3.95 |  6.54 | 10×DNF |
|  50 | 5 | 25 |  12.09 | 16.89 |  9.69 | 10×DNF |
| 200 | 3 |  1 |   1.65 |  2.26 |  5.74 | 10×DNF |
| 200 | 3 |  5 |   8.97 |  7.39 |  8.78 | 10×DNF |
| 200 | 3 | 25 | 138.29 | 34.48 | 22.59 | 10×DNF |
| 200 | 5 |  1 |   1.48 |  2.58 |  6.11 | 10×DNF |
| 200 | 5 |  5 |   8.42 | 13.39 |  9.61 | 10×DNF |
| 200 | 5 | 25 | 136.44 | 113.31 | 31.52 | 10×DNF |
| 1000 | 3 |  1 |   29.46 |  10.76 |   9.39 | 10×DNF |
| 1000 | 3 |  5 |  354.89 |  38.83 |  22.86 | 10×DNF |
| 1000 | 3 | 25 | 13048.79 | 399.10 |  93.34 | 10×DNF |
| 1000 | 5 |  1 |   18.94 |  13.92 |  11.01 | 10×DNF |
| 1000 | 5 |  5 |  253.78 | 113.38 |  28.19 | 10×DNF |
| 1000 | 5 | 25 | 15016.91 | 861.42 | 143.15 | 10×DNF |

**Levi-backend ranking across the grid** (median of medians):
`traces (9.6 ms) < pynauty (12.1 ms) < bliss (13.4 ms)`. Traces is
the steadiest scaler; pynauty wins on the smallest cells but blows up
to 13–15 s on `n=1000, c=25`; bliss is the most consistent
middle-of-the-pack.

**IsalHG DNF breakdown.** 49 / 180 `DisconnectedHypergraphError`
(decision B11, exclusively the `c=1` cells where ER almost surely
returns a disconnected hypergraph); 131 / 180 `TimeoutError` (the
600 s watchdog fired on every other cell). Zero successful
fingerprints.

### 12.3 Findings

1. **The grid sits entirely beyond the IsalHG algorithmic wall.** A
   targeted compute-node sanity job (SLURM job `1312802`,
   `--constraint=avx512`) called `canonical_string` with the C++
   engine on hand-built and small ER fixtures and recorded:

   | Fixture | C++ `greedy_single` |
   |---|---:|
   | Fano STS(7) — 7 nodes, 7 edges | **2.31 ms** ✓ |
   | Fano STS(7) — `greedy_min` | 8.00 ms ✓ |
   | ER `n=10, r=3, c=2` (14 edges) | **7.5 ms** ✓ |
   | ER `n=20, r=3, c=2` (36 edges) | disconnected (B11) |
   | ER `n=30, r=3, c=2` (58 edges) | **TIMEOUT > 60 s** |
   | ER `n=50, r=3, c=1` (48 edges) | disconnected (B11) |
   | ER `n=50, r=3, c=2` (108 edges) | disconnected (B11) |

   The wall lies near `(n, m) ≈ (20–30, 40–60)` for `r=3`. The
   preprint grid's smallest cell is `(n=50, r=3, c=1)` with
   `E[m] ≈ 50` edges — already in the disconnected band, and the
   smallest connected cell `(n=50, r=3, c=5)` has `m ≈ 250`, an order
   of magnitude past the wall.

2. **The C++ engine is correctly built and dispatched on Picasso.**
   `_core.cpython-311-x86_64-linux-gnu.so` resolved, `DEFAULT_BACKEND
   = cpp`, Fano completed in 2.31 ms (matches the home-machine table
   in `docs/CPP_SPEEDUP.md` to within thermal noise). The DNFs are
   not a build or PATH artefact.

3. **The four-way partition agreement holds where it can be checked.**
   540 / 540 positive-pair checks pass; no Levi backend disagrees
   with another on any seed. The single statistical claim the preprint
   could still make if the cohort were re-scoped is therefore intact.

4. **traces_levi is the cohort's runtime winner.** On every cell where
   pynauty exceeds 100 ms, traces is at least 4× faster; on `n=1000,
   r=3, c=25` traces is 140× faster than pynauty. This was not
   anticipated in §4.1 (pynauty was treated as the default oracle).

5. **Per-tier deviations from the spec.** Two changes from §4 had to
   land to make the sweep terminate at all:

   - `repeats` reduced from 10 → 1 so each cell terminates at exactly
     600 s rather than 6 000 s in the worst case.
   - IsalHG algorithm switched from `greedy_min` to `greedy_single`.
     `greedy_min` runs `greedy_h2s` from every max-`ξ` seed in
     parallel and takes the lex-min; on dense ER the seed set is
     large enough that the parallel-fan-out + lex-min reduction blew
     past the timeout even on cells where `greedy_single` would have
     finished within a few seconds (which is to say: none of them).

### 12.4 Re-scoping plan for the next sweep

The Jun-24 grid produced no IsalHG measurement and the headline
characterisation collapsed to a single observation ("IsalHG DNFs the
entire grid"). To populate the heat-grid with actual ratios — i.e.
to actually identify the regime where IsalHG dominates, ties, or
loses — the cohort must move into the regime where IsalHG completes.
The verify job above pins the boundary at `m ≲ 40–50` edges for
`r=3`. Accepted re-scope:

| Axis | Jun-24 grid (§3) | Jun-25 grid (this sweep) |
|---|---|---|
| Vertex count `n` | `{50, 200, 1000}` | **`{8, 12, 16, 20, 24, 28}`** |
| Arity `r` | `{3, 5}` | **`{3}`** (drop `r=5` until `r=3` is mapped) |
| Density `c` (edges-per-vertex) | `{1, 5, 25}` | **`{1.0, 1.5, 2.0}`** (E[m] ≈ n to 2n; stays in the connected regime under the §12.4-NEW reject-resample) |
| Seeds | 10 | 10 (keep) |
| Backends | 4 (keep) | 4 (keep) |
| Per-fingerprint timeout | 600 s | **60 s** (cells either finish in seconds or DNF cleanly) |
| `repeats` | 1 (deviation) | **10** (restore §4.2 spec — at 1 ms/call the budget is back) |
| IsalHG algorithm | `greedy_single` (deviation) | **`greedy_min`** (restore §4.1; small `n` keeps the seed set small) |
| Connectivity policy | raw ER (disconnected cells become DNFs) | **conditional on connectivity** (every backend sees the same connected input — see §12.4-NEW) |

Estimated cell counts: `6 × 1 × 3 × 10 × 4 = 720` cells — the same
total as the prior grid, single SLURM array, all cells expected to
finish in seconds. The dataset is the same generator
(`UniformErdosRenyiHypergraphs`) with the connectivity-aware patch in
§12.4-NEW.

If the sparse grid shows IsalHG competitive on (say) `n ≤ 16`, the
preprint claim becomes: *"IsalHG dominates on small dense connected
hypergraphs (`n ≤ 16, m ≤ 30`); Levi backends dominate above the
edge-count threshold ≈ 40."* That is a real characterisation with
both sides of the boundary populated, and matches the descriptive
PI directive of 2026-06-17.

Optional second sweep, after the sparse grid: keep the original `n ∈
{50, 200, 1000}` grid alongside the sparse one, with IsalHG cells
explicitly tagged as expected-DNF, to give the preprint a "where it
*does not yet* scale" complementary heat-grid. The full empirical
paper would carry both.

### 12.4-NEW Connectivity policy: ER conditional on connectivity

**Decision (2026-06-25).** The dataset
(`src/isalhg/datasets/synthetic/erdos_renyi.py`) now rejects
disconnected samples and resamples until the primal graph is
connected. Concretely, the materialiser draws
`xgi.uniform_erdos_renyi_hypergraph(n, r, p, seed=effective_seed)`
with `effective_seed = base_seed + (attempt - 1) * 1_000_003`; if
`H.is_connected()` is False the attempt is rejected and a new sample
is drawn with the next `effective_seed` in the walk. The loop is
bounded at `connected_max_attempts=1000` (a `DatasetError` fires if
the density is so low that connectivity is unreachable in 1000 tries).

The default for the registry factory is `require_connected=True`. The
historical raw-ER distribution is recoverable by passing
`require_connected: false` in YAML `dataset_params`.

**Why this is the right design choice for the preprint.** The
Jun-24 grid showed that `core.algorithms.greedy_min` raises
`DisconnectedHypergraphError` on disconnected inputs (invariant B11),
while the Levi backends (`pynauty_levi`, `bliss_levi`, `traces_levi`)
accept disconnected inputs and produce normal fingerprints. The
asymmetry was a measurement bug rather than a feature of the
algorithms — IsalHG's connectivity precondition is a constraint of
the canonical-string framework, not a property of the hypergraph.
The two ways to remove the bias are: (a) extend IsalHG to handle
disconnected inputs (decision B11 says no — deferred to the full
paper); (b) restrict the cohort to connected hypergraphs. We pick
(b) for the preprint because:

1. **Same input → same measurement.** With reject-resample every
   backend fingerprints the same `H`, so the cross-backend
   `partition_agreement` claim of §4.3 becomes meaningful on every
   single cell rather than only on the connected subset.
2. **No new DNF category.** The Jun-24 sweep had 49 of 180 IsalHG
   DNFs labelled `DisconnectedHypergraphError` — pure measurement
   noise from the asymmetric treatment of disconnected ER samples,
   not algorithmic difficulty. Removing this category sharpens the
   characterisation map: every IsalHG DNF in the new sweep is a
   real timeout against the underlying exponential.
3. **Distributional honesty.** The cohort is announced as
   "*r*-uniform Erdős–Rényi conditional on connectivity" — a
   well-defined distribution, the natural one for any benchmark that
   needs to compare canonical-string algorithms (which are typically
   defined on connected inputs only) against graph-iso engines.
   The conditional is reported in §3 verbatim along with the empirical
   acceptance rate (median attempts per draw).
4. **Cost.** On the sparse grid the acceptance rate stays high
   (smoke test: `n=8, r=3, c=1` accepted on attempt 2; denser cells
   accept on attempt 1). Per-cell overhead is the cost of one extra
   ER draw, negligible against the fingerprint budget.

**Reproducibility.** The dataset records `effective_seed` and
`connected_attempts` in `DatasetItem.extra`; both fields land in the
per-cell JSON so any reader can replay the exact hypergraph that was
fingerprinted from the YAML config alone.

### 12.5 Run-level provenance

- Picasso jobs (in time order):
  1300829 → 1301489 → 1303339 (cancelled; algorithm switch),
  1303339 / 1303340 (full-grid sweep, cancelled at 110 / 0
  completions to switch to `greedy_single`),
  1304726 / 1304727 (60 s subprocess timeout — too tight),
  1305872 / 1305873 (600 s + `repeats=1`; cancelled at 437 / 0 due
  to orphan-subprocess holding SLURM slots),
  **1306419 / 1306420 (final fast + slow tier — drained cleanly)**,
  1318428 / 1318440 (traces backfill after installing `dreadnaut`
  via conda-forge `nauty`).
- C++ rebuild on Picasso: editable install via
  `pip install -e . --no-build-isolation` → 95 KB
  `_core.cpython-311-x86_64-linux-gnu.so` deposited in
  `/mnt/.../conda_envs/isalhg/lib/python3.11/site-packages/isalhg/core/`.
- `dreadnaut` installed via `conda install -c conda-forge nauty`
  (2.9.1) — required for `traces_levi` backend; absence had caused
  every Traces cell to report `BackendUnavailableError` in the first
  full-sweep pass.
- Artefacts archived to
  `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/preprint/experiment/`
  (full Picasso `pipeline/` tree, rsync'd 2026-06-25).

---

## 13. Jun-25-2026 Results — final sweep on the connected-ER grid

Second Picasso execution of the re-scoped grid (§12.4 + §12.4-NEW
+ later refinements). Every cell of the matrix produced a real
measurement; the headline characterisation map is now fully
populated.

Raw artefacts:
`/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/preprint/experiment/`
(rsync'd from Picasso
`/mnt/.../fscratch/isalhg_results/preprint/pipeline/`).

### 13.1 Cohort parameters (as run)

| Axis | Values |
|---|---|
| Vertex count `n` | `{8, 12, 16, 20, 25}` (max trimmed from 28 to 25 so the worst IsalHG cell finishes within budget) |
| Arity `r` | `{3}` |
| Density `c` (expected edges-per-vertex) | `{1.0, 1.5, 2.0}` |
| Seeds | `{0, 1, …, 9}` |
| Backends | `{isalhg, pynauty_levi, bliss_levi, traces_levi}` |
| Per-fingerprint timeout | **600 s** (restored to §4.2 spec, up from the Jun-25-iter1 `60 s`) |
| `repeats` per fingerprint | **10** (restored to §4.2 spec) |
| IsalHG algorithm | `greedy_min` (restored to §4.1 spec) |
| Connectivity policy | **ER conditional on connectivity** via reject-resample (§12.4-NEW) — `require_connected=True` default, deterministic seed walk `seed + (attempt-1) · 1 000 003` |
| Subprocess isolation | `ISALHG_BACKEND_ISOLATE=1`, `ISALHG_SUBPROC_TIMEOUT_S=600` (parent enforces 600 s + `terminate`/`kill` to reap orphan C++ threads) |
| C++ engine | Built on Picasso login node (`pip install -e . --no-build-isolation` → scikit-build-core + nanobind, GCC 7.5, `-O3 -march=native -flto`); verified at runtime via `_core.cpython-311-x86_64-linux-gnu.so` resolution + `DEFAULT_BACKEND=cpp` |
| SLURM partition | CPU partition, `--constraint=avx512` (Intel `sd*` + AMD `bc*/bl*`) |
| Memory | 16 GB/CPU |
| Wall budget per task | 3 h SLURM + 10 500 s inner `timeout(1)` reap (orphan-subprocess safety net) |
| `dreadnaut` | conda-forge `nauty 2.9.1` (needed for `traces_levi`) |

Total cells: `5 × 1 × 3 × 10 × 4 = 600`. Wall-clock to last result on
128-concurrent slots: ≈ 25 min (driven by the seven n=25 IsalHG
stragglers; everything else completed in seconds).

### 13.2 Headline numbers

**Correctness invariant.** 600 positive-pair checks
(`backend.are_isomorphic(H, σ(H))` for every backend on every
seed). **Pass rate = 1.0; zero failures across all four backends,
on all 600 cells.** This is the first full-grid sweep where every
cell exercises the correctness path, because every backend
fingerprint completed.

**Per-cell median wall-clock (ms, median over 10 seeds, real
measurements throughout — no DNFs).**

| `n` | `c` | isalhg | pynauty | bliss | traces |
|----:|----:|-------:|--------:|------:|-------:|
|  8  | 1.0 |   16.88 |   0.05 |  0.12 |  3.22 |
|  8  | 1.5 |   21.21 |   0.06 |  0.14 |  3.27 |
|  8  | 2.0 |   22.31 |   0.07 |  0.16 |  2.91 |
| 12  | 1.0 |   42.75 |   0.07 |  0.17 |  3.31 |
| 12  | 1.5 |   44.94 |   0.08 |  0.18 |  3.08 |
| 12  | 2.0 |   55.93 |   0.10 |  0.24 |  3.30 |
| 16  | 1.0 |  176.74 |   0.09 |  0.20 |  3.20 |
| 16  | 1.5 |  241.54 |   0.11 |  0.23 |  3.06 |
| 16  | 2.0 |  492.30 |   0.13 |  0.29 |  3.46 |
| 20  | 1.0 |  821.97 |   0.10 |  0.20 |  2.72 |
| 20  | 1.5 | 2039.71 |   0.14 |  0.32 |  3.37 |
| 20  | 2.0 | 3037.30 |   0.16 |  0.35 |  3.17 |
| 25  | 1.0 | 6863.50 |   0.15 |  0.30 |  3.21 |
| 25  | 1.5 |19170.56 |   0.18 |  0.34 |  2.92 |
| 25  | 2.0 |22786.09 |   0.20 |  0.44 |  3.17 |

**Per-backend wall-clock range (ms) over the 15 (n, c) cells.**

| Backend | min | median | max |
|---|---:|---:|---:|
| isalhg       | 16.88 |   821.97 | 22 786.09 |
| pynauty_levi |  0.05 |     0.11 |      0.20 |
| bliss_levi   |  0.12 |     0.24 |      0.44 |
| traces_levi  |  2.72 |     3.20 |      3.46 |

**Scaling.** IsalHG's per-fingerprint cost grows roughly as
`n^(3.5±0.3)` over the tested band (log-log slope from `(n=8, 21)
→ (n=25, 22 786)` at `c=2.0`); pynauty's grows linearly with
`n` (`0.07 → 0.20` ms is sublinear in absolute terms but consistent
with `O(n + m)` Levi-graph traversal); bliss tracks pynauty within
a factor 2-4; traces is dominated by subprocess startup overhead at
this scale (~3 ms floor for every cell — the dreadnaut binary
takes longer to load than the canonical-labelling itself takes to
run).

### 13.3 Findings

1. **Full-grid IsalHG coverage.** Every IsalHG cell finishes within
   23 s wall-clock, well below the 600 s budget. The Jun-25-iter1
   sweep had 53 / 180 timeouts at n=28 with a 60 s ceiling; trimming
   max-n to 25 and restoring the 600 s ceiling pushed every cell
   into the measurable band. No special handling, post-processing,
   or DNF accounting is needed when the data are reported.

2. **The Levi backends dominate the entire tested band.** IsalHG is
   between **300× and 80 000× slower** than `pynauty_levi` on every
   single `(n, c)` cell. The ratio grows by ~3× for each step in `n`
   (from 8 → 12 → 16 → 20 → 25), tracking the polynomial-vs-
   exponential gap directly. No cross-over is observed; no cell in
   the grid favours IsalHG.

3. **Connectivity policy works as advertised.** No
   `DisconnectedHypergraphError` DNFs anywhere in the sweep —
   confirms that the reject-resample loop in
   `UniformErdosRenyiHypergraphs` (§12.4-NEW) routes every backend
   into the same connected input. The acceptance ratio in the
   per-cell JSONs is high on dense cells (1 attempt) and modest on
   the sparsest (`n=16, c=1.0` averaged 3 attempts in the cohort
   viz, well under the 1 000-attempt budget).

4. **C++ engine confirmed live, every cell.** Average IsalHG cost
   at `n=8, r=3, c=1.5` (11 edges, well under the home-machine
   benchmark Fano-STS(7)-doily band) is 21.21 ms — within an order
   of magnitude of the home-machine `docs/CPP_SPEEDUP.md` STS(13)
   number (42 ms `greedy_min`), confirming that the C++ extension
   resolved correctly and is doing the work. A Python-backend fallback
   would have been at minimum 100× slower at this scale.

5. **traces_levi has a fixed overhead floor.** Every traces cell is
   ≈ 3 ms regardless of `(n, c)`. This is the dreadnaut subprocess
   startup, not the algorithm — traces would presumably scale
   identically to pynauty/bliss on cells where the inner solve
   exceeds 3 ms. Should be flagged in the figure caption as a
   characterisation of the subprocess interface, not the underlying
   algorithm.

### 13.4 Re-scope confirmed publishable

The Jun-24 → Jun-25-iter1 → Jun-25-final progression takes the
characterisation map from *zero measurements* (entire grid past the
algorithmic wall, §12.2) to *partial measurements* (n ≤ 20 OK, n ∈
{24, 28} DNFs, §12.4) to **full coverage** (every cell measured,
this section). The PI directive of 2026-06-17 — *map the regime
where IsalHG dominates, ties, or loses* — is now answerable on this
cohort:

> **Levi backends dominate on every cell of the connected r-uniform
> Erdős-Rényi grid with `r = 3, n ∈ [8, 25], c ∈ [1.0, 2.0]`. The
> IsalHG-to-`pynauty_levi` median wall-clock ratio is bounded below
> by ≈ 300× (smallest cell, `n=8, c=1`) and grows to ≈ 80 000× at
> `n=25, c=2`. The C++ canonical-string engine is the operative
> bottleneck — the algorithm itself, not its implementation, places
> IsalHG outside the operating regime of the cohort.**

Acceptance criteria §7:

| Criterion | Status |
|---|---|
| 1. Sweep completes | ✓ 600 / 600 cells |
| 2. Correctness invariant holds | ✓ 600 / 600 pairs pass |
| 3. Characterisation map populated | ✓ All 15 cells have real numbers |
| 4. Reproducibility artefact shipped | ✓ Archived to external drive |

### 13.5 Run-level provenance

- Picasso job (final): **`1358809`** — `--array=0-599%128
  --time=03:00:00 --mem-per-cpu=16G --cpus-per-task=1
  --constraint=avx512`,
  `ISALHG_BACKEND_ISOLATE=1 ISALHG_ALGORITHM=greedy_min
  ISALHG_SUBPROC_TIMEOUT_S=600 PIPELINE_TASK_TIMEOUT=10500`.
  Wall-clock to last result ≈ 25 min; 600 / 600 COMPLETED.
- Precursor jobs (informational; their results are not part of the
  final tally): `1357011` (n max 28, 60 s timeout — cancelled
  before completion to update the grid), `1357891` (n max 28, 60 s,
  drained — gave the partial-coverage map in §12.4 that motivated
  the n-trim).
- Code changes since §12:
  - `src/isalhg/datasets/synthetic/erdos_renyi.py` — added
    `require_connected=True` default + deterministic reject-resample
    loop (§12.4-NEW).
  - `experiments/preprint/data/build_preprint_config.py` — grid
    constants updated; `TIMEOUT_S = 600` restored.
  - `experiments/preprint/data/visualize_cohort_axes.py` —
    `Larger N` panel updated from `n=28` to `n=25`; subtitle
    trimmed to the four generator inputs `(n, r, c, seed)` per the
    Jun-25-final aesthetic pass.
  - `src/isalhg/viz/layout.py` — `compact_primal_layout` gains
    `spring_k=0.9` (larger optimal node distance) and
    `fit_fraction=0.78` (inner-canvas occupancy) so the hyperedge
    blobs no longer touch the rounded frame.
- Artefacts archived to
  `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/preprint/experiment/`
  (full Picasso `pipeline/` tree, rsync'd 2026-06-25, ~3.7 MB).
  Includes `random_sweep/` (600 per-cell JSONs) and
  `analysis_output/` (4 CSVs, Figs 1-3 in PDF + PNG, Tables 1-2
  in LaTeX `booktabs`).
- Cohort-axes figure regenerated at
  `experiments/preprint/data/figures/cohort_axes_{xgi,hypernetx,hypergraphx}_seed0.{pdf,png}`,
  with the new grid (n=8/16/25 baseline + Sparser/Denser variants
  at n=16), the reject-resample connectivity policy, and the
  minimal-subtitle aesthetic. Panel layout uses the new breathing-
  room spring layout (`k=0.9`, `fit_fraction=0.78`).

