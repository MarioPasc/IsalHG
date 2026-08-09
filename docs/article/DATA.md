# IsalHG journal article — data plan

**Status:** ACTIVE (v3 rescope 2026-07-18). Companion to
`docs/article/PROPOSAL.md`. Supersedes the *paper* data scope of
`docs/preprint/DATA.md` (the iso-benchmark cohort spec), which remains the
authoritative record of what the current data layer implements. Reuse from that
cohort is expected; this document records only what the metric-space paper
needs.

The v3 paper needs data for **four purposes** (v2's ordering inverted: the
body corpora lead; the exact-HGED corpus is a mini-corpus for one discussion
figure):

## 1. The size-controlled corpus (Stratum C — primary; serves A2–A3 and the G1/A1 geometry)

### ⚠ Critical design constraint 1 — classes must be non-isomorphic

The obvious shortcut (take iso-class representatives, generate `permute()`
copies as class members) is **invalid for classification/clustering**. Permuted
copies are *isomorphic*, so `w*_c` is identical and `d_I = 0` within class by
construction. Any clustering/kNN on such a corpus scores perfectly for a
trivial reason (it re-tests iso-invariance, the foundation's job) and says
nothing about the metric *geometry*. **Class members must be non-isomorphic
but structurally coherent.** Permuted copies are retained only as an
invariance sanity check (and as the `HGED = 0` anchor inside the mini-corpus,
§4).

### ⚠ Critical design constraint 2 — classes must be invisible to size and degrees

The first-generation primary corpus (Stratum A: 17 known-design families × 5
Qin-edit members = 85 items) violated a constraint we had not made explicit:
its 17 families occupy only **14 distinct `(n, m)` cells**, so family identity
is nearly a lookup on two integers. The falsifying measurement (2026-08-09,
reproduced byte-identical before any redesign): the structure-free distance
`|Δn| + |Δm|` scores A2 ARI 0.442 ± 0.040 and A3 AUC 0.932 ± 0.008 on that
corpus, outranking five of the seven representations on the first metric and
four of seven on the second. Neither axis alone suffices (incidence mass
alone: ARI 0.101; edge count alone: 0.111) — the pair resolves the families.
On such a corpus A2/A3 measure how directly each representation encodes size,
not representation quality; the Stratum A task numbers are withdrawn as a
comparison (`results/superseded/`). The repaired constraint: **the corpus
must hold `(n, m, k)` and the exact per-vertex degree sequence constant
across classes**, so both naive baselines (`size_l1`, `degree_seq_l1`) are
identically zero on every pair *by construction* and whatever a
representation scores is higher-order structural signal.

### The Stratum C generator (size-controlled swap-planted families)

Three independent cells, `(n, m) ∈ {(9, 12), (12, 20), (15, 35)}`, all
3-uniform, each analyzed separately (no cross-cell pairs, so no size axis
re-enters). Per cell and per corpus seed:

1. **Base.** One random connected 3-uniform hypergraph realizing the cell
   exactly.
2. **Family seeds.** 12 independent chains of `10·m` connectivity-preserving
   **incidence swaps** from the base (`swap_incidence`: `v1` and `v2` trade
   places between `e1` and `e2` — preserves every vertex degree, every arity,
   `n`, and `m` exactly; the bipartite double-edge swap on the incidence
   structure). Chains are pairwise far apart in edit space and verified
   pairwise non-isomorphic.
3. **Members.** 6 per family: the family seed + 5 rejection-sampled 2-swap
   perturbations, connected, pairwise non-isomorphic (pynauty-Levi oracle).

72 items per cell per corpus seed; deterministic under `(params, seed)`
(`datasets/synthetic/size_controlled_corpus.py`, dataset
`"size_controlled_corpus"`). The size/degree control is enforced as a build
invariant and pinned by an integration guard
(`tests/integration/test_corpus_confound_guard.py`): one `(n, m)` cell, one
degree sequence, both naive distance matrices exactly zero.

**Why not Steiner systems as the substrate (measured, 2026-08-09).** The 80
non-isomorphic STS(15) look ideal (all share `(15, 35)`, 3-uniform,
7-regular), but both feasibility and signal fail: pristine STS(15) `w*_c`
costs 617 s on the *most symmetric* instance (PG(3,2), |Aut| = 20160) and
> 900 s on every rigid or median-symmetry instance tested — the cost driver is
the Steiner pair-coverage tie structure, and |Aut| does not predict cost in
either direction; STS(19) (11.08 × 10⁹ systems, all sampled ones rigid) also
exceeds 900 s. Worse, near the Steiner manifold the canonical form is
maximally unstable: a 2-swap perturbation moves `d_I` as far as switching to a
different Steiner system entirely (within-family and between-family distance
distributions coincide; ARI ≈ 0.02–0.05), so STS-seeded families carry no
recoverable class structure for `d_I`. Random substrates (regular and
irregular) were piloted at four cells with the same outcome for `d_I` — the
single-edit response of `w*_c` is ≈ 30–50 % of the string everywhere (swap or
Qin edit alike), the avalanche mechanism of the discussion — while NetLSD
recovers the planted structure on the same items (positive control). The
corpus is therefore honest by construction and *solvable* (the planted signal
is real: within-family members share ~27/35 edges vs ~3/35 between), and the
task outcome is reported in whichever direction it falls, per the
pre-registered contract (`COMPETITORS.md` §4).

### The Qin-edit planted-family generator (Stratum A — superseded as primary)

`F` seed motifs; each family = a seed + `r` independent Qin-op edits per
member, enforced non-isomorphic within family
(`datasets/synthetic/planted_families.py`). Seeds: the design fixtures (Fano
n=7, STS(9) n=9, the cyclic C13 orbits n=13, GQ(2,2) n=15) plus the vendored
Steiner catalog (orders 3–15, `datasets/synthetic/sts_catalog.py`). It
remains the generator behind the ladder corpora's seed pool and the
G2-sensitivity fixtures, and its A2/A3/G1 role passed to Stratum C under
design constraint 2. A 2026-07-08 cohort survey found no existing corpus with
whole-hypergraph class labels, ≥2 instances/class, and sizes within our
wall-clock gate — hence the bespoke generators. Both are
bespoke-but-standard-practice (planted partitions); the paper states them
fully.

## 2. Real-world anchor (credibility; serves A1–A3 at scale)

The **HIC atlas (12 datasets)** is the only cohort member with genuine
whole-hypergraph class labels *and* many instances per class (e.g. IMDB→genre,
Steam→category), Apache-2.0, `github.com/iMoonLab/HIC` — and it is
community-known (the dataset suite of the hypergraph-WL TPAMI paper). Its
instances are real networks (n in the hundreds–thousands), so the **only gate
is `w*_c` wall-clock** (the applications are HGED-free): DQ3' below. ARB /
XGI-DATA / Hypergraphx entries are each one giant network — no set of
instances to classify — so unsuitable for the corpus role (kept out of scope
in v3; an ego-net/snapshot derivation from ARB was considered and declined to
avoid a bespoke derivation step reviewers can attack).

**Declared fallback.** If DQ3' fails (w*_c not computable in acceptable time
on HIC-scale instances), the real anchor falls back to the small real designs
+ the planted-family corpora, and the paper says so; the applications' claims
are then synthetic-scale claims. The scope survives the gate either way — the
gate decides reach, not viability.

**Gate outcome (measured 2026-07-19): the fallback applies.** On
IMDB-Dir-Form (1,869 post-LCC instances) the corpus-level `k` is 110 (max
hyperedge arity), beyond both the compiled arity cap (`K_MAX = 10`, decision
B12) and the uncapped Python encoder (median instance, n=12: DNF at 330 s).
Restricting to instances with arity ≤ 10 keeps 78.7% (per-class retention
89%/71%/71%), and within that sub-corpus a 10 s/instance budget completes
only 73% of a seeded 100-instance sample (median 7 ms, p90 1.4 s) — the
failures are automorphism-driven, not size-driven (n=10, m=5 instances DNF
while n=22, m=79 completes), so no size ceiling separates feasible from
infeasible and a wall-clock filter would censor by structural symmetry. A
corpus kept at ≈57% yield under two label-correlated filters is not a
defensible primary anchor. The real anchor is therefore the small real
designs + the planted-family corpora; a censored-subset HIC exhibit as a
*secondary* experiment, and a re-test after stabiliser-orbit pruning (the
symmetry cost is exactly what that value-preserving speedup removes), remain
open options and are not assumed by any claim.

## 3. Ladder corpora (serve G2 and A4)

Perturbation ladders `H_0 → H_1 → ⋯ → H_t` from `edit_path(H, t, rng)` with
accumulated Qin-cost budgets (`qin_edit_cost`): the known-budget axis for the
G2 ladder-response measurement and the A4 endpoints/intermediates pool
(plus same-corpus distractors). No oracle calls — the budget is known by
construction. Built over both §1 seeds and §2 instances (post-gate).

**Connected-domain implementation (D-CONN1, T-M2c — executed 2026-07-09).**
`d_I` is defined exclusively on connected hypergraphs (`canonical.py` raises
`DisconnectedHypergraphError` otherwise). The generators enforce this at
construction: `CorrelationCorpusHypergraphs` (§4) and
`PerturbationLadderHypergraphs` sample **connected Erdős–Rényi** via
rejection sampling (`random_connected_hypergraph`), and
connectivity-preserving edits (`random_connected_edit`) keep every ladder
snapshot connected. Honest consequence: conditioning on connectivity changes
the ensemble — the paper says "connected ER" and **reports the per-corpus
acceptance rate** (fraction of unconstrained ER draws already connected;
stored per item in `extra["acceptance_attempts"]`). The backbone fallback
(spanning star + random edges) is logged as `acceptance_attempts ==
max_attempts + 1` and counts as a rejection for the rate.

## 4. The exact-HGED mini-corpus (serves E1' only)

One small **connected** corpus on which the exact oracle (`exact_hged`, HPC
parallel) is feasible for all pairs; produces the single discussion figure
(ρ, scatter — `empirical/correlation.md` E1'). Composition: spread the
structural-similarity range (perturbation pairs at several budgets + unrelated
pairs) so the scatter is populated across its range, not only near 0 and max.
Size: pinned by an oracle wall-clock probe (DQ1'); no density sweep is run, so
the v2 requirement of a wide (n, Δ) grid is gone — one honest corpus suffices.

**Final composition (measured, 2026-07-21).** 11 of the 12 pinned blocks:
n = 5..10 × 2 seeds, minus the second n = 10 block, whose exact-HGED
all-pairs run exceeded a 100 GB memory allocation after 18 h (its two sibling
hard blocks completed at up to 8.5 h / 55 GB peak per 630-pair block). The
exclusion is whole-block — the E1' protocol forbids per-pair censoring (a
censored pair would bias ρ) — and is reported as the measured practical
ceiling of the exact oracle; the DQ1' probe, which timed within-ladder pairs
only, did not expose the cross-ladder branch-and-bound blow-up. Final corpus:
11 blocks × 630 = 6,930 pairs (6,921 with HGED > 0).

## 5. Reuse from the existing data layer

The current `isalhg.datasets` layer (exhaustive_small, permute-based iso
pairs, STS/design fixtures) is directly reusable for the mini-corpus and the
sensitivity fixtures. The planted-family generator and the ladder corpus
wiring are new `datasets/synthetic/` modules → tracked in `DEVELOPMENT/`.

## 6. Open data questions

- DQ1'. **[resolved 2026-07-19 — probe run, corpus pinned]** Exact HGED on
  connected ladder-corpus pairs (arity ≤ 3) costs median 1–92 ms, p90 ≤ 2.5 s,
  max 4.8 s per pair with zero DNFs under a 30 s cap for n ≤ 10, m ≲ 8 —
  the mini-corpus ceiling is (n, m) = (10, 8). The pinned E1' corpus:
  12 blocks (base sizes n = 5..10 × 2 seeds), each 4 perturbation ladders ×
  9 snapshots = 36 items → 630 all-pairs per block, ≈ 7,560 (d_I, HGED)
  pairs total; within-ladder pairs supply the perturbation budgets,
  cross-ladder pairs the unrelated range (§4 composition). A single-block
  local check: exact HGED all-pairs in 15.8 s at n = 5; HGED spans 1–29 and
  the HGED = 0 pairs coincide exactly with d_I = 0.
- DQ3'. **[resolved 2026-07-19 — NO-GO, fallback executed]** `w*_c` is not
  computable in acceptable time across a HIC IMDB corpus (corpus-level `k`
  exceeds the arity cap; the arity-capped sub-corpus has a symmetry-driven
  DNF tail). Measurement and consequences recorded in §2; re-testable after
  stabiliser-orbit pruning.
- DQ5. **[new, v3]** Sweep grid for the geometry-vs-density/size reporting
  (§1): which (n, m/n, arity-mix) cells, sized to the `w*_c` wall-clock
  budget. Replaces the v2 density-sweep grid (whose purpose was Theorem-B
  validation).

Resolved and retired: DQ2 (oracle tiering — collapsed: exact for E1' only,
ladder budgets for the body, BP-HGED retired), DQ3 (planted families vs cohort
— resolved: bespoke generator), DQ4 (two corpora with different purposes —
superseded by the four-purpose split above), DQ5 (geometry-vs-density grid —
absorbed: Stratum B carries the density axis; Stratum C carries the
size-controlled axis).

## 7. Corpus policy — which corpus serves which measurement

One corpus per measurement, chosen by what the measurement must control;
geometry and applications read the *same* objects. Any table where a naive
baseline (`size_l1`, `degree_seq_l1`) scores above its floor is measuring the
corpus, not the representations — that is the standing falsifier every corpus
below is checked against.

| Measurement | Corpus | Why this corpus |
|---|---|---|
| A2 clustering, A3 kNN (task metrics, all representations) | **Stratum C** (§1): 3 size-controlled cells, 12 swap-families × 6, 27 seeds | class signal must be purely higher-order: `(n, m, k)` + degree sequence fixed ⇒ both naive baselines identically 0 by construction |
| G1 concentration/hubness + A1 MDS geometry table (per representation) | **Stratum C**, same cells and seeds | the geometry must describe the same objects the applications run on (no-orphan-geometry rule) |
| Geometry vs density/size trends | **Stratum B**: admitted connected-ER cells (k3 to n=24 at ρ≤2; k5 at n=8) | controlled `(n, k, ρ)` axes inside the measured `w*_c` envelope; no class labels needed |
| G2 local sensitivity + regime confrontations | design fixtures (17 regimes) + single edits | anchored, interpretable per-regime predictions; sensitivity is a per-object profile, not a task |
| G2 ladder response, A4 path scoring | ladder corpora (§3), known Qin budgets | HGED-free budget axis is known by construction |
| E1' correlation figure | exact-HGED mini-corpus (§4), FROZEN | the only place the oracle is feasible for all pairs |
| Compactness (bits) | Stratum A 85-item corpus + planted_n240 (FROZEN, 320/320) | measured pre-rescope; a size-heterogeneous corpus is *appropriate* here — compactness is a per-object claim, not a class-discrimination task |
| Real-data exhibit (secondary, censored) | HIC IMDB clean subsets (§2 gate) | the only labelled real corpus; enters only where `w*_c` is computable |
| Iso-invariance sanity | `permute()` pairs | tests the foundation, not the geometry |

Superseded: the Stratum A task/geometry numbers (A2/A3/G1/A1 on the 85-item
design corpus) are withdrawn under design constraint 2 (§1) and archived under
`results/superseded/`; Stratum A survives as the bits corpus (frozen result),
as the G2-fixture seed pool, and as the seed catalog for the ladder corpora.
