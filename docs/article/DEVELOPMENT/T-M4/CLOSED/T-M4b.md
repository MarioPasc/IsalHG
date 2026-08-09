# T-M4b — The primary corpus does not measure representation quality; design and adopt a size-controlled replacement
**Declared:** 2026-08-09 18:30 CEST
**Status:** DONE (2026-08-09, session 1)
**Priority:** HIGHEST — gates every A1–A4 number in the article body.
**Depends on:** — (supersedes the corpus assumption behind T-M4, T-M7d, T-M5b/c/d)
**Delegation:** orchestrator-only. Deciding what the corpus *is* is deciding what
"correct" means for the whole body, and the task is authorised to invalidate
prior results — the automated orchestrator must not hand this to a worker. The
PI is dispatching a dedicated exploratory agent by hand (2026-08-09); that
dispatch is the intended execution path, not orchestrator delegation.
**Why out of scope:** Found while planning the article's figure set
(`docs/article/figures/`), not while executing any ledger task. The finding
invalidates the interpretation of closed tasks rather than extending one, so it
cannot be repaired inside them.

**Context to read first:**
- `docs/article/DEVELOPMENT/T-M4/README.md` — the scope's own invariant, which
  is what has been violated: corpora must have class structure "known and *not*
  trivially recoverable"
- `docs/article/figures/F7-task-metrics.md` §2–3 — the full measurement, the
  mechanism, and the four candidate fixes with a recommendation
- `scripts/diagnostics/size_confound_probe.py` + `size_confound.log` — the
  reproduction (5 seeds, 85 items, 7 representations + 3 naive distances)
- `scripts/diagnostics/sts_feasibility_probe.py` + `sts_feasibility.log` — the
  `w*_c` cost curve on the Steiner family
- `docs/article/theoretical/geometry.md` §4 (PC1 ≈ `|w*_c|`) and §5 (the
  length-difference floor, ρ = 0.867) — the two corroborating measurements
  already in the reasoning prose
- `docs/article/COMPETITORS.md` §4 — the pre-registered interpretation contract
  for the naive baseline, which binds how this is reported
- `src/isalhg/datasets/synthetic/known_design_catalog.py::build_stratum_a_corpus`
  — the current corpus builder
- `src/isalhg/datasets/synthetic/sts_catalog.py` — the vendored Steiner catalog
  (85 iso-classes, orders 3–15), the candidate substrate
- `src/isalhg/datasets/synthetic/planted_families.py` — the perturbation
  generator the replacement will likely reuse
- `.claude/rules/coding_rules.md` — always

**Description:** The Stratum A corpus (17 known-design families × 5 members = 85
items) is size-heterogeneous to the point that family identity is nearly a
lookup on two integers. `n` spans 5–15, `m` spans 3–15, incidence mass 12–45
(CV 0.499), `|w*_c|` 49–276 (CV 0.561), and the 17 families occupy only **14
distinct `(n,m)` cells** — three collisions are the sole pairs requiring
structural discrimination. A distance built from nothing but `|Δn| + |Δm|`
therefore scores **A2 ARI 0.442 ± 0.040 and A3 AUC@5 0.932 ± 0.008**, which
outranks five of the seven measured representations on ARI and four of seven on
AUC, ties NetLSD on AUC, and is within noise of degree-sequence L1 on ARI
(IsalHG: 0.274 / 0.915). Neither size axis alone does this — incidence mass
alone gives ARI 0.101, edge count alone 0.111 — it is the *pair* that resolves
the families, which is exactly what a degree sequence (length `n`, sum `Σ|e|`)
and a heat trace both encode almost directly. Three independent measurements
already in the reasoning prose corroborate the mechanism: `d_I` correlates 0.867
with the canonical-length gap, MDS PC1 correlates 0.960 with `|w*_c|` and 0.956
with `m`, and the leading representations are mutually redundant
(IsalHG↔degree-seq ρ = 0.799, NetLSD↔degree-seq ρ = 0.707).

The consequence is that A2 and A3 as measured do not compare representations —
they compare how directly each representation encodes `(n, m)`. Reporting the
current ranking in *either* direction is indefensible, and the falsifying check
is one line of code.

Design and adopt a replacement corpus in which `(n, m, k)` and, ideally, the
degree sequence are held constant across classes, so that the only remaining
discriminative signal is higher-order structure. The task is explicitly
authorised to **supersede and archive prior corpus results** (`results/T-M7d/`,
and the A1–A4 numbers folded into `theoretical/geometry.md` and
`empirical/applications.md`) once a replacement is validated — follow the
existing `superseded/` convention in `results/RESULTS_MANIFEST.md` rather than
deleting.

Candidate substrates, with what is already measured about each:
- **The 80 non-isomorphic STS(15)** — `n = 15`, `m = 35`, arity 3, 3-regular, so
  both naive baselines are *identically zero* on every pair and score ARI = 0 by
  construction. The ideal control. **Feasibility is the open question:** `w*_c`
  costs 0.00 s at STS(7), 0.08 s at STS(9), **29.6 s at STS(13)**, and a single
  STS(15) instance had not returned after 30 minutes on the local workstation.
  Two vertices of growth cost three orders of magnitude, and the driver is
  symmetry, not size — the same mechanism as the HIC NO-GO (`DATA.md` §2).
  A Picasso single-job run with a long wall is the right instrument to settle
  this; if one instance is tractable, 80 instances × 3,160 pairs is the budget
  question.
- **A new fixed-`(n, m, k)`, fixed-degree-sequence generator** with rejection to
  non-isomorphic members — controllable in both size and degree, with scale set
  by the measured feasibility envelope rather than by a fixed design. This is
  the recommended path if STS(15) proves out of reach.
- **A size-matched sub-corpus of the existing designs** — free, but only three
  usable `(n,m)`-matched pairs, and each differs in arity, which is itself
  degree-correlated. Underpowered; use as a sanity check, not as the corpus.

The wider concern the PI raised is in scope: the synthetic corpora are currently
ad hoc and inconsistent across experiments (Stratum A designs, Stratum B random
cells, planted families at N = 60/240/480, ladder corpora, the E1′ mini-corpus,
the G3 OFAT bases). Part of the deliverable is a **single documented corpus
policy** — which corpus each measurement uses and why — so that geometry and
applications describe the same objects, which is what `RESULTS_MANIFEST.md`
already claims but the lineage no longer supports. Real data (HIC) stays where
it is: a censored secondary exhibit entering only where it is computable.

**Acceptance:**
1. A replacement corpus exists, is registered in `datasets/registry.py`, is
   deterministic under `(params, seed)`, and its construction is documented in
   `docs/article/DATA.md` with the size/degree control stated as a property.
2. On that corpus, `|Δn| + |Δm|` and `degree_seq_l1` score at the structural
   floor (ARI ≈ 0 / AUC ≈ chance), demonstrated by a run of the same harness —
   this is the check that the confound is gone, and it must be *measured*, not
   argued.
3. `size_l1` (`|Δn| + |Δm|`) is registered as a distance alongside
   `degree_seq_l1` so it flows through the sweep harness with the same BCa CIs
   and Holm-corrected tests, and appears in every comparison surface.
4. `scripts/diagnostics/size_confound_probe.py` is productionised into the
   harness (or into `tests/`) so the confound cannot silently return.
5. The A1–A4 and geometry numbers are re-measured on the replacement corpus;
   superseded results are moved under `results/superseded/` with a manifest
   entry, and every claim in `theoretical/geometry.md` and
   `empirical/applications.md` that reads from the old corpus is updated or
   withdrawn.
6. A corpus policy section in `DATA.md` states, per measurement, which corpus it
   uses and why — replacing the current ad hoc lineage.
7. `COMPETITORS.md` §4's pre-registered contract is honoured verbatim in the new
   reporting: the outcome is stated in whichever direction it falls, and no
   competitor is removed on the basis of having won.

**Out of scope here:** changes to `w*_c`, the encoder, or the canonical
algorithm; the A4 ambient-decodability repair (T-M5m); the HGED oracle and the
frozen E1′ results (`results/T-M5a/`, do not re-run); dropping any competitor
from the comparison set — the competitor set is settled by `COMPETITORS.md`
CQ1/CQ4 and is not reopened by this task.

---

## Running log (append-only)

### 2026-08-09 19:43 CEST — session 1: reproduction, feasibility probes, pilots, design decision

**Reproduction (mandatory step 0).** `PYTHONPATH=. ~/.conda/envs/isalhg/bin/python
scripts/diagnostics/size_confound_probe.py` (5 seeds, ~6 min): output
**byte-identical** to the recorded `scripts/diagnostics/size_confound.log`
(`diff` clean). The finding stands as stated.

**Premise correction.** The recorded `sts_feasibility.log` shows STS(15) at
**613.19 s** (completed), not ">30 min DNF" as this file and the handoff state.
The timed instance is `sel[0]` = catalog index 0 = PG(3,2) — measured
|Aut| = 20160, the most symmetric of all 80.

**STS(15) symmetry ranking** (pynauty on the bipartition-coloured Levi graph,
all 80 in 0.2 s): 36/80 rigid (|Aut| = 1) — matches the published
Kaski–Östergård count; distribution {1:36, 2:6, 3:12, 4:8, …, 288:1, 20160:1}.
Pairwise shared triples over 3,160 pairs: min 9 / median 16 / max 31 of 35.
Vendored `sts15.txt` verified **byte-identical** to Pottonen's GT
(`pottonen.kapsi.fi/sts19/sts15.txt`; PI-pointed).

**STS(19)** (PI-pointed): 11,084,874,829 systems; Pottonen hosts them
stsc-compressed. Built `stsc-1.1` locally; decoded the 1k random sample to the
catalog's letter-triple format; |Aut| = 1 for **1000/1000** sampled — an
effectively unlimited rigid pool at (19, 57), pending one `w*_c` timing
(queued).

**`w*_c` wall-clocks** (scratchpad `timing_driver.py`, subprocess-isolated,
900 s cap, this workstation):

| instance | t |
|---|---|
| STS(15) idx22 pristine (rigid, |Aut|=1) | **TIMEOUT > 900 s** |
| STS(15) idx23 pristine (rigid) | **TIMEOUT > 900 s** |
| STS(15) idx0 = PG(3,2) pristine (|Aut|=20160) | 613 s (recorded log) |
| idx22 + 1 swap | 30.3 s |
| idx0 + 1 swap | 32.1 s |
| idx22 + 2 swaps | 12.1 s |
| idx22 + 200 swaps (randomized 7-regular) | 0.24 s |

Cost is driven by the Steiner near-uniform pair coverage (tie structure), NOT
by |Aut| — a rigid pristine STS(15) is *slower* than PG(3,2). One swap off the
manifold costs ~30 s regardless of starting symmetry.
(Incident recorded: the first timing run was killed by an explicit 10-min Bash
timeout; relaunched uncapped with per-candidate subprocess caps.)

**Pilot 1 — STS-seeded swap families (negative).** 4 rigid, max-min-separated
seeds (idx 22/64/53/38; pairwise 19–23 differing triples) × 4 members at
t = 2 degree-preserving swaps; 16/16 distinct `w*_c`; 1 degree sequence,
1 (n,m) cell. Token-level within-family d_I {117/138/154 min/med/max} vs
between {113/139/159} — **identical**; PAM ARI 0.02–0.05. A 2-swap edit
avalanches the string as far as switching Steiner systems.

**Pilot 2 — random substrates at (15,35,3) (negative).** Regular arm
(7-regular, 300-swap randomizations of idx22) and irregular arm (random
connected base): within ≈ between in both (ratio ≈ 1.0); ARI ≤ 0.16; yet the
planted structure is combinatorially real — within-family members share median
27/35 edges vs 3/35 between. Encodings 1.24 s (regular) / 0.25 s (irregular).

**Pilot 3 — cell sweep (decisive).** Irregular fixed-degree swap-planted
families (4 × 4, t = 2) at (9,12)/(10,15)/(12,20)/(15,35), k = 3,
repo-registered distances:

| cell | swap1 sens med | qin1 sens med | IsalHG b/w ratio · ARI | WL | NetLSD ratio · ARI |
|---|---|---|---|---|---|
| (9,12) | 13 | 17 | 0.97 · ≈0 | 1.00 · 0 | 1.20 · 0.06 |
| (10,15) | 19 | 19 | 1.02 · ≈0 | 1.00 · 0 | 1.59 · 0.32 |
| (12,20) | 32 | 32 | 1.06 · ≈0 | 1.00 · 0 | 1.77 · 0.03 |
| (15,35) | 59 | 56 | 1.01 · ≈0 | 1.00 · 0 | 4.55 · 0.33 |

(a) Single-edit d_I response — swap or Qin, indistinguishable — is ≈30–50% of
the string at every cell: the avalanche is universal, not Steiner-specific
(G2's "IQR 3–9 tokens" is ~31% relative on its short strings). (b) Planted
edit-proximity classes are unrecoverable by d_I at every tested cell.
(c) The controlled construction itself works: both naive baselines are
identically zero on every pair by construction, and NetLSD recovers the
planted structure (positive control). (d) WL is blind at fixed degrees.
`degree_seq_l1` within = between = 0 exactly.

**Decision (PI-ratified this session, AskUserQuestion 2026-08-09).**
Build the size-controlled corpus and report the honest outcome per the
pre-registered `COMPETITORS.md` §4 contract ("we want to have good data
first" — PI). Full replacement of the primary corpus authorized; the binding
requirement is a clean, clearly-motivated data-decision story in `DATA.md`.
Alternatives considered and rejected: STS(15)-seeded families (measured dead —
avalanche, pilot 1; pristine seeds infeasible >900 s); old corpus + disclosure
row (F7's D — concedes A2/A3 measure size); rescoping A2/A3 out (PI-level
surgery, not taken now; PI reserves post-hoc scope calls after data is in).

**Adopted corpus spec (Stratum C, size-controlled).** Per cell
(n,m) ∈ {(9,12), (12,20), (15,35)}, k = 3: base = random connected 3-uniform
hypergraph at the cell (per corpus seed); 12 family seeds = 10·m-swap MCMC
randomizations of the base (all share (n, m, k) and the base's irregular
degree sequence exactly); 6 members per family at t = 2 swaps; pairwise
non-isomorphic (pynauty-Levi dedup); connected throughout; per-cell analysis
only (no cross-cell pairs — no size axis re-enters). 12 × 6 = 72 items/cell,
216 per corpus seed; `w*_c` cost ≈ 2 min per corpus seed (measured envelope
0.25–1.2 s/item), 27-seed sweep local.
New core edit: degree/size-preserving incidence swap (the repo has no such op;
verified zero grep hits) — spec: e1 ≠ e2, v1 ∈ e1∖e2, v2 ∈ e2∖e1;
e1 ← e1∖{v1}∪{v2}, e2 ← e2∖{v2}∪{v1}; rejects duplicate edges and
disconnection; preserves every degree, every arity, n, m.

**Completed `w*_c` timing table** (original probe ran to completion; the
relaunched driver double-covered some rows under mutual CPU contention —
original-probe numbers are authoritative):

| instance | t |
|---|---|
| STS(15) idx0 = PG(3,2) pristine (|Aut| 20160) | **616.96 s** (reproduces the recorded 613.19 s) |
| STS(15) idx22 pristine (rigid) | TIMEOUT > 900 s |
| STS(15) idx23 pristine (rigid) | TIMEOUT > 900 s |
| STS(15) idx41 pristine (median symmetry, |Aut| 3–4) | TIMEOUT > 900 s |
| STS(19) sample#0 pristine (rigid) | TIMEOUT > 900 s |
| idx0 + 1 swap | 39.3 s |
| idx22 + 1 swap | 36.7 s |
| idx22 + 2 swaps | 17.4 s |
| idx22 + 200 swaps | 0.35 s |

PG(3,2) — the *most* symmetric STS(15) — is the *cheapest* pristine instance
measured; two rigid and one median-symmetry instance all exceed 900 s. The
cost driver is the Steiner pair-coverage tie structure, and |Aut| is not a
usable cost predictor in either direction. Recorded as the negative result
closing the "STS as corpus" option (handoff §4) together with the pilot-1
avalanche result.

### 2026-08-09 (contd.) — session 1: implementation

All code Plan → failing-test → implement → green (`coding_rules.md` §2.3):

- `core/sparse_hypergraph.py`: `swap_incidence` (unit op; partner-exchange
  legal, third-party duplicate rejected) + `random_swap_edit` (rejection
  sampler, returns `None` when no valid swap). 12 new tests in
  `tests/unit/core/test_sparse_hypergraph_edits.py` — 42/42 green.
- `datasets/synthetic/planted_families.py`: `edit_kind: "qin"|"swap"`
  parameter; `seed()` now also propagates `allow_partial`,
  `coarse_class_labels`, `edit_kind` (pre-existing omission, latent re-seed
  bug, fixed in passing); `edit_kind` recorded in `metadata.source`.
- `datasets/synthetic/size_controlled_corpus.py` (new):
  `SizeControlledCellDataset`, registered `"size_controlled_corpus"`.
  Base draw rejects realized `(n,m)` ≠ requested (found by test:
  `random_connected_hypergraph`'s `n_edges` is attempts, not a guarantee);
  family seeds = `10·m`-swap connected chains; hard invariant check: every
  item must match the base's degree sequence and cell. 12 tests green
  (determinism, full-rebuild `seed()`, cell contract, global non-iso).
- `metric_space/representations/size_l1.py` (new): `size_l1` =
  `|Δn| + |Δm|`, registered; 7 tests green.
- `experiments/article/analysis/sweep_multi_seed.py`: `size_l1` added to
  `ALL_DISTANCES` + labels; Stratum C (`STRATUM_C_CELLS =
  [(9,12), (12,20), (15,35)]`, k=3, 12 families × 6 members, t=2 swaps);
  `build_stratum_c_seed_corpus` / `run_stratum_c_seed` (mirrors the A-runner;
  no per-arity split; single-member families excluded from A2/A3; HyperCOT
  gated out up front — N=72 > HYPERCOT_MAX_CORPUS); `--stratum c` CLI;
  cache layout `d_matrix/stratum_c_n{n}m{m}/seed{S}/{dist}/D.npy`.
  Existing harness tests: 220/220 green.
- `tests/integration/test_corpus_confound_guard.py` (new, the productionised
  probe): per production cell — exactly one `(n,m)`, one degree sequence,
  `size_l1` and `degree_seq_l1` **identically zero** on every pair. 3/3 green,
  0.70 s total (corpus builds measured 0.06/0.13/0.32 s per cell).

### 2026-08-09 (contd.) — session 1: the S=27 re-measurement (FINAL)

Verification gate before the sweep: 1,448 unit+property tests passed (0
failed; property suite re-run because `core/` changed), confound guard 3/3,
ruff 3 (= baseline), mypy 20 (< 21 baseline).

Sweep: `--stratum c --n-seeds 27`, three cell-parallel local workers,
`results/T-M4b/` on the drive; wall ≈ 45 min; zero warnings/errors. One
aggregator gap found and fixed (stats emitted no A2/A3 rows for stratum "c";
three `stratum == "a"` gates widened to `("a", "c")`; stats regenerated from
the cached seed metrics — 81/81 cache hits). Digest (mean [95% BCa], S=27;
AUC at k=5; full tables in `results/T-M4b/stats/`):

| cell | IsalHG | nauty-edit | HPD | NetLSD | WL | size_l1 / deg-seq |
|---|---|---|---|---|---|---|
| (9,12) ARI | 0.026 [.019,.038] | 0.235 [.207,.265] | 0.108 | 0.045 | −0.000 | −0.000 [−.001,.000] |
| (9,12) AUC | 0.545 | 0.804 | 0.677 | 0.589 | 0.492 | 0.492 |
| (12,20) ARI | 0.028 | 0.399 [.365,.439] | 0.259 | 0.064 | −0.000 | −0.000 |
| (12,20) AUC | 0.569 | 0.888 | 0.828 | 0.626 | 0.492 | 0.492 |
| (15,35) ARI | 0.016 | 0.614 [.571,.657] | 0.519 [.481,.555] | 0.123 | −0.000 | −0.000 |
| (15,35) AUC | 0.565 | 0.938 | 0.942 | 0.714 | 0.492 | 0.492 |

- **Acceptance #2 met, measured:** both naive baselines at the structural
  floor at every cell (ARI −0.000 [−0.001, 0.000]; AUC 0.492 = the harness's
  degenerate-tie chance level), through the same BCa/Holm harness as every
  other row.
- IsalHG is Holm-significantly **above** all three floor rows at every cell
  (p ≤ 7.5×10⁻³) — a real but small structural signal.
- nauty-Levi edit, HPD, and NetLSD are Holm-significantly **above IsalHG** at
  every cell (p ≤ 0.028, mostly ≤ 10⁻⁶). WL is *at* the floor exactly —
  blind at fixed degree sequence.
- Geometry (IsalHG): ν = 0.137/0.061/0.011 across the cells; D̂ = 27.4 [26.9,
  28.0] at (9,12), censored at the CV cap (40) at the two larger cells;
  stress 0.055/0.021/0.059; hubness ≈ 0.93. Bits on Stratum C: median ratio
  1.563/1.334/1.190, `r > 1` on 100 % of items at all cells.

Supersede executed: `T-M7d` Stratum A slices (189 D.npy + seed metrics +
stats) → `results/superseded/T-M7d_stratum_a/`;
`size_confound_probe.py` re-pointed at the archive (forensic reproduction
stays runnable); `RESULTS_MANIFEST.md` reconciled (T-M4b FINAL row, Stratum B
row split out, superseded row with rationale, provenance re-pointed).

### 2026-08-09 (contd.) — session 1: doc propagation + close

Doc propagation (reasoning docs state what is true; this file tracks the
work): `DATA.md` §1 rewritten (design constraint 2, the Stratum C generator,
the measured substrate rejections) + new §7 corpus policy (per measurement:
corpus + why); `theoretical/geometry.md` §3 (Stratum C ν/D̂ table, censoring
read as concentration, descriptor + calibration prose), §4 (residual
distortion on Stratum C; the PC1-size finding reframed as the superseded
corpus's mechanism, silenced by construction on Stratum C), §5 (floor +
confound record reframed as the redesign's motivation; resolution paragraph
with the measured floors and outcome), §6 (absolute-vs-relative sensitivity
scope: single-edit response ≈30–50 % of the string on unanchored substrates;
the honest nauty note); `empirical/applications.md` (preamble, usefulness
framing + axis 2 rewritten, capability-matrix caveat, G1/A1/A2/A3 measured
blocks replaced with the S=27 Stratum C tables, corpora table, runtime
section corrected); `COMPETITORS.md` §4 resolution paragraph;
`figures/F7-task-metrics.md` §7 resolution; `DECISIONS.md` D-M4b.

**Acceptance walk-through:** (1) corpus registered
(`"size_controlled_corpus"`), deterministic under `(params, seed)` (tested),
documented in `DATA.md` §1 with the control stated — ✓. (2) Floors measured
through the harness: ARI −0.000 [−0.001, 0.000], AUC 0.492 at all 3 cells —
✓. (3) `size_l1` registered, in `ALL_DISTANCES`, same BCa/Holm treatment, in
every comparison surface — ✓. (4) Probe productionised:
`tests/integration/test_corpus_confound_guard.py` — ✓. (5) Body re-measured
(S=27, FINAL); superseded results archived with manifest entry; every
affected claim updated or withdrawn — ✓. (6) Corpus policy = `DATA.md` §7 —
✓. (7) `COMPETITORS.md` §4 honoured verbatim: outcome reported in the
direction it fell (against IsalHG); no competitor removed — ✓.

**Closing checks (verbatim):**

```
pytest tests/unit/ tests/property/ -q  →  1448 passed, 6 skipped  (test-runner, this session)
pytest tests/unit/experiments_article/ tests/unit/datasets/test_size_controlled_corpus.py \
  tests/unit/metric_space/test_size_l1.py tests/unit/core/test_sparse_hypergraph_edits.py \
  tests/integration/test_corpus_confound_guard.py -q  →  284 passed, 2 warnings in 11.13s
ruff check src/ tests/  →  Found 3 errors.   (= standing baseline 3: ANN001, E731, SIM108)
mypy src/isalhg/        →  Found 20 errors in 6 files   (standing baseline 21; 1 below)
```

Probe provenance: the session's diagnostics and their recorded logs are
archived in `scripts/diagnostics/` (`sts15_symmetry_probe.py` + log — |Aut|
ranking, GT verification, `w*_c` timings; `timing_driver.py`/`time_wstar.py`
+ log; `separability_pilot{,2,3}.py` + logs — the STS avalanche, the
random-substrate arms, and the decisive cell sweep with the repo distances).

Out-of-scope items respected: `w*_c`/encoder untouched; T-M5m untouched (its
ambient-decodability repair is independent and remains OPEN); E1′ not re-run;
no competitor removed. Follow-up candidates left for the PI/next session, not
filed as tasks by this one: (a) a k=5 secondary cell at n=8 if the envelope's
family count can be made to fit; (b) a G2-style swap-sensitivity figure from
the T-M4b pilot data if the discussion wants it rendered.
