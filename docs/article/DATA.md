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

## 5. Reuse from the existing data layer

The current `isalhg.datasets` layer (exhaustive_small, permute-based iso
pairs, STS/design fixtures) is directly reusable for the mini-corpus and the
sensitivity fixtures. The planted-family generator and the ladder corpus
wiring are new `datasets/synthetic/` modules → tracked in `DEVELOPMENT/`.

## 6. Open data questions

- DQ1'. Mini-corpus size + (n, m) ceiling for all-pairs exact HGED under HPC
  parallelism (one probe run pins it). Rescoped from v2's DQ1 (which sized a
  full correlation corpus + density sweep).
- DQ3'. **[blocking the real anchor]** Measure whether `w*_c` is computable in
  acceptable time on a HIC IMDB instance (post seed-opt + C++ + orbit
  pruning). Decides §2's gate; fallback declared there.
- DQ5. **[new, v3]** Sweep grid for the geometry-vs-density/size reporting
  (§1): which (n, m/n, arity-mix) cells, sized to the `w*_c` wall-clock
  budget. Replaces the v2 density-sweep grid (whose purpose was Theorem-B
  validation).

Resolved and retired: DQ2 (oracle tiering — collapsed: exact for E1' only,
ladder budgets for the body, BP-HGED retired), DQ3 (planted families vs cohort
— resolved: bespoke generator), DQ4 (two corpora with different purposes —
superseded by the four-purpose split above).
