# T-M7g — Real-data anchor: designs-catalog exhibit + gate-first real-world corpus
**Declared:** 2026-07-22 11:56 CEST
**Status:** OPEN
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
