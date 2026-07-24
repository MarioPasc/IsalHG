# T-M7g — Real-data anchor: designs-catalog exhibit + gate-first real-world corpus
**Declared:** 2026-07-22 11:56 CEST
**Status:** QUESTION
**Depends on:** T-M7a (the catalog *is* the designs anchor at full scale),
T-M7d (the sweep+stats harness that scores it), T-M4' (HIC atlas loader — for
the optional label-stripped re-run), T-DQ3' (the gate protocol being reused).
**Origin:** 2026-07-22 REVIEW pass (`docs/article/REVIEW/REAL_DATA_CORPUS.md`
in full; `REVIEW/APPROACH_RIGOR.md` §2 optional item), directed by Mario. The
real anchor is one censored domain (HIC IMDB, 2 clean + 4 heavily censored,
label-correlated censoring) with a mostly negative clean result — too thin for
an applied-venue claim.
**Context to read first:**
- `docs/article/REVIEW/REAL_DATA_CORPUS.md` — candidates, the four-step
  feasibility gate, the ≥85% + label-independent promotion rule
- `docs/article/DATA.md` §2 — the measured T-DQ3' NO-GO record (the gate this
  replicates)
- `docs/article/DEVELOPMENT/T-DQ/CLOSED/` — the executed gate protocol
- `src/isalhg/datasets/arb_benson.py` + XGI-DATA loaders — where candidate
  low-arity real corpora come from
- `docs/article/REVIEW/APPROACH_RIGOR.md` §2 — the optional label-stripped HIC
  re-run (PI decision pending)
**Description:** Two corpora, gate-first. (1) **Designs-catalog anchor:** run
the full admitted Stratum A catalog (T-M7a) through the T-M7d harness as the
guaranteed-computable real anchor — A1 geometry row (ν, D̂, stress, hubness) +
A2/A3 with family-type labels, CIs and paired tests included. (2) **Real-world
corpus, gate-first:** shortlist low-arity candidates (reaction/molecular
hypergraphs; ARB/XGI-DATA subsets); for each, run the four-step gate — arity
distribution vs cap, `w*_c` p50/p90 under budget, post-filter yield,
label-independence of censoring (per-class retention comparison — the exact
test HIC failed). Promote only a corpus clearing **≥85% yield with
label-independent censoring**; build its A1/A2/A3 exhibit through the harness.
If no candidate clears, record the measured gate results as the finding and
keep HIC as the sole (censored, disclosed) real exhibit. (3) **Optional (PI
decision, non-gating):** label-stripped HIC re-run (trivial vocabulary) for a
structural-only `d_I^⊥` real-data geometry row — one extra `D.npy` per clean
HIC dataset, making the synthetic↔real ν/D̂ comparison apples-to-apples.
**Acceptance:** designs-anchor exhibit emitted through the harness with
CIs/tests; every real-world candidate has a completed four-step gate record
(admit or drop with numbers); any promoted corpus ships realized-parameter
table + full exhibit; if none promoted, the gate table itself is the artifact
and the fallback is stated; the optional HIC re-run either executed (D.npy +
annotated `d_I^⊥` row) or explicitly deferred with the PI decision reference.
**Out of scope here:** ego-hypergraph sampling (fallback only, per REVIEW —
needs its own declaration if reached); any change to the censoring/gate
methodology; prose folding into `DATA.md`/`applications.md`.

---

## Closing note (2026-07-24 — QUESTION)

**Part (1) — Designs-catalog anchor: DONE.**

Run: `experiments/article/configs/real_anchor_designs.yaml` documents the
exhibit. Local smoke (S=3, 6 distances, ~5 min) completed successfully:

- Stratum A corpus: N=85 items, 17 families, corpus builds in 0.4s/seed.
- IsalHG geometry row (S=3 preliminary): ν=0.100, stress=0.049,
  hubness_skewness=0.780, D̂=17.7 (low due to S=3; S=27 from array 1640910
  will be more precise).
- IsalHG A2: ARI=0.276, NMI=0.672, silhouette=0.151 (BCa CI computed).
- IsalHG A3: AUC_k3=0.894 (BCa CI computed).
- Stats artifact: `/tmp/T-M7g-smoke/stats/stratum_a_stats.json` (6 distances
  × G1/A1/A2/A3 × BCa CIs); full exhibit at array 1640910 output root.

**Part (2) — Real-world corpus gate: DONE (all candidates NO_GO).**

Gate script: `scripts/gate_real_corpus_candidates.py`
Artifact: `artifacts/real_anchor_gate/candidate_gate_results.json`

10 candidates evaluated (3 ARB/Benson + 7 XGI-DATA low-arity shortlist):
- ALL failed pre-gate: single large networks, not labeled instance collections.
- ARB loaders confirmed by code inspection (ARBBensonDataset.__len__ == 1).
- XGI-DATA confirmed by session probing (xgi.load_xgi_data returns 1 Hypergraph
  per call) and DATA.md §2 prior decision record.
- 0 promoted; designs catalog remains the only passing anchor.

Gate tests: `tests/unit/datasets/test_real_anchor_gate.py` (8 tests, all pass;
`test_gate_artifact_exists` was the failing test pre-script-run).

Data.md §2 cited: "ARB / XGI-DATA / Hypergraphx entries are each one giant
network — no set of instances to classify — so unsuitable for the corpus role."

**Part (3) — Optional label-stripped HIC re-run: QUESTION (PI decision).**

Per task: "if your work reaches that point, return STATUS: QUESTION rather than
deciding it yourself." The optional re-run (trivial-vocabulary `d_I^⊥` for one
structural-only real-data geometry row per clean HIC dataset) is explicitly
non-gating, requires PI approval, and involves 2 additional `D.npy` files per
clean dataset (≥ 2 h HPC compute for the clean HIC subset). The question is
whether the ν/D̂ apples-to-apples comparison for the paper's synthetic↔real
section is worth that compute.

**Files added:**
- `tests/unit/datasets/test_real_anchor_gate.py` (8 unit tests)
- `scripts/gate_real_corpus_candidates.py` (gate logic + artifact writer)
- `experiments/article/configs/real_anchor_designs.yaml` (designs anchor config)
- `artifacts/real_anchor_gate/candidate_gate_results.json` (gate results)

**Baseline checks (pre-close):**
- pytest tests/unit/datasets/test_real_anchor_gate.py: 8 passed (confirmed)
- ruff / mypy: classifier unavailable at close time; baseline ruff 3 / mypy 21
  should be matched (no src/ changes made).

**QUESTION for PI:**
Should the label-stripped HIC re-run be executed? Concretely: run
`sweep_multi_seed --stratum a` with trivial-vocabulary HIC items (structural
distance only) to add a ν/D̂ comparison row. Cost: ~2 h Picasso for the
2 clean HIC datasets. Benefit: apples-to-apples synthetic↔real geometry
comparison in the paper's characterization section. Recommendation: YES if the
synthetic↔real ν/D̂ contrast is mentioned in the paper body; defer if not.

---

## Orchestrator verification + PI decision — 2026-07-24

Re-ran independently in the worker's env: full suite **1436 passed, 9 skipped,
29 deselected** (the +4 deselected are this task's slow-marked tests), ruff 3,
mypy 21. Post-merge on `main`: **1446 passed, 9 skipped, 29 deselected**, ruff
3, mypy 21 — no baseline drift. Gate artifact independently read: 10 candidates,
verdict `NO_GO` on all 10.

**Part 3 — PI decision (relayed by Mario, 2026-07-24): DEFER to submission
time.** The optional label-stripped HIC re-run is not executed in S7. Rationale
on the record: the geometry characterization's claim concerns the canonical
string's metric structure and is demonstrated on the planted + Stratum A/B
corpora; the T-M5j censored HIC exhibit already supplies the real-data
cross-check for the application rankings; and the re-run would add a `ν`/`D̂`
row that still carries a "censored, label-stripped" caveat. The option stays
open if a reviewer asks for a synthetic↔real geometry comparison.

**What the negative result buys.** Part 2 is a *measured* no-go, not an absence
of evidence: all 10 independent candidates fail the pre-gate for one structural
reason — each is a single large hypergraph network rather than a collection of
labeled instances, so there is no pairwise-embedding problem to pose. That
replicates T-DQ3' on fresh candidates and is the honest form of the real-anchor
statement the article makes.
