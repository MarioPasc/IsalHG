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

## 1. The planted-family corpus (primary; serves G1/G2, A1–A3)

### ⚠ Critical design constraint — classes must be non-isomorphic

The obvious shortcut (take iso-class representatives, generate `permute()`
copies as class members) is **invalid for classification/clustering**. Permuted
copies are *isomorphic*, so `w*_c` is identical and `d_I = 0` within class by
construction. Any clustering/kNN on such a corpus scores perfectly for a
trivial reason (it re-tests iso-invariance, the foundation's job) and says
nothing about the metric *geometry*. **Class members must be non-isomorphic
but structurally coherent.** Permuted copies are retained only as an
invariance sanity check (and as the `HGED = 0` anchor inside the mini-corpus,
§4).

### The generator

`F` seed motifs; each family = a seed + `r` independent perturbations (a few
random Qin-op edits per member, enforced non-isomorphic within family). Yields:

- non-isomorphic within-family members at small, controllable edit budget
  (Qin-cost accounting: intra-family structural distance is bounded by
  construction);
- known family membership ⇒ **class labels for A2 (ARI/NMI) and A3 (kNN)**;
- **controlled sweeps for the geometry pillar**: vary density (m/n, arity mix)
  and size across corpora so `ν`, `D̂`, concentration/hubness are reported as
  functions of the controlled parameters, not single numbers.

This is **new code** (`datasets/synthetic/planted_families.py`) — no library
provides the non-isomorphic-within-family constraint. Seeds: the design
fixtures already shipped (Fano n=7, STS(9) n=9, the cyclic C13 orbits n=13,
GQ(2,2) n=15) plus the vendored **Steiner-triple-system catalog** (T-M0c,
2026-07-18: all iso-classes for orders 3–15 — 1/1/1/2/80 systems,
`datasets/synthetic/sts_catalog.py`, dataset `"sts_catalog"`) and SageMath
PG(2,q) small designs. All generated hypergraphs **connected** (the article's
domain; generator-level guarantee).

A 2026-07-08 cohort survey found no existing corpus with all three of:
whole-hypergraph class label, ≥2 instances/class, sizes within our wall-clock
gate — hence the bespoke generator. It is bespoke-but-standard-practice
(planted partitions); the paper states the generator fully.

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
superseded by the four-purpose split above).
