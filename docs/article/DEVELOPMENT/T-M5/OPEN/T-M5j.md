# T-M5j — HIC OD6 real-data exhibit (A1/A2/A3 on IMDB genre, censored)
**Declared:** 2026-07-20 (PI-directed, OD6 resolved — `DECISIONS.md`)
**Status:** OPEN
**Depends on:** T-M5b ✔ (MDS + geometry helpers), T-M5c ✔ (clustering), T-M5d ✔ (kNN),
T-M4' ✔ (HIC atlas loader), T-M3a–d ✔ (competitors)
**Context to read first:**
- `docs/article/DATA.md` §2 — the real anchor / HIC gate + fallback
- `docs/article/empirical/applications.md` §A1/A2/A3 + competitor applicability
- `DECISIONS.md` OD6 (the resolution + censoring protocol)
- `src/isalhg/datasets/hic_atlas.py` — `HICAtlasDataset(root, hic_name)`; items carry
  `item.extra["class_label"]`; LCC already applied (D-CONN1), per-class retention tracked
- `experiments/article/analysis/{mds,clustering,knn}.py` — reuse their scoring functions
- `.claude/rules/coding_rules.md` — always

**Description.** The OD6 secondary credibility exhibit: run A1 (MDS + geometry
table), A2 (k-medoids + dendrogram, ARI/NMI vs genre), A3 (kNN acc/F1/AUC vs k,
read against the G1 profile) on **real HIC data** — the **6 IMDB genre
variants** (`IMDB-Wri-Genre`, `IMDB-Dir-Genre`, `IMDB-Wri-Genre-M`,
`IMDB-Dir-Genre-M`, `IMDB-Wri-Form`, `IMDB-Dir-Form`), **full arity ≤ 10
subset** each, HGED-free. Labels = `class_label` (genre). This runs **alongside**
the planted fallback (unchanged); it is a censored-subset exhibit, not the anchor.
**A4 is out of scope** (ladder-based; HIC has no ladder).

**Censoring protocol (critical — the pipelines' `matrix()` has no timeout and
will hang on the DNF tail):**
1. Per dataset: load `HICAtlasDataset`, keep items with max edge arity ≤ 10.
2. For each survivor, compute `canonical_fingerprint(H)` under a **hard 5 s
   per-instance timeout** via a killed `multiprocessing` process (fork context;
   the C++ tie-complete branching ignores SIGALRM, so a separate process +
   `terminate()` is required). Keep only instances that complete; **drop DNFs**.
   Reuse the validated pattern in
   `scratchpad/hic_probe2.py` (median `w*_c` ≈ 1 ms; ~7% DNF on Wri-Genre).
3. Record and report **per-class yield** (survivors / arity-capped) per dataset —
   this is the exhibit's honesty requirement (censoring is label-correlated).
4. Build `D` on the surviving instances only: `isalhg_levenshtein` (ours) +
   competitors `hypergraph_wl_l1`, `netlsd_l2`, `hpd_jsd`, `nauty_levi_edit`.
   **HyperCOT:** O(n³)/pair — run on a ≤ 40-instance stratified subsample only,
   or omit with the scale limit stated (mirror the fallback treatment). Cache
   `D.npy` per (dataset, representation) so the exhibit is reproducible.

**Deliverables (reuse the existing pipeline functions; do NOT fork them):**
- Per HIC dataset: the geometry table row(s) (ν, PSD, D̂ via OOS-CV, stress,
  concentration, hubness) from `mds.geometry_table_row` / `cv_dimension_selection`;
  MDS scatter + Shepard figures.
- A2: silhouette/Dunn/DB + **ARI/NMI vs genre labels** + cophenetic, via
  `clustering.py` functions; dendrogram figure.
- A3: kNN acc/macro-F1/AUC-OvR vs k (LOO or stratified CV) via `knn.py`, printed
  against the G1 hubness/concentration profile.
- One **censoring table** (per dataset: n items, arity≤10, w*_c-yield, per-class
  yield) — the exhibit's caveat, cited in the closing note.
- A short comparison line vs the planted fallback (do the real-data ARI/NMI/AUC
  orderings across representations agree with the planted findings? — OD6's stated
  acceptance test: does censoring flip any conclusion?).

**Results output:** `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/T-M5j/`
(D.npy caches, geometry/censoring tables as CSV/JSON, figures). Do NOT commit
binaries; commit code + config + the ledger closing note (quote the censoring
table + per-dataset A2/A3 scores verbatim).

**Acceptance:** all 6 IMDB genre datasets processed (or a documented DNF-only
skip with evidence); per-class censoring table produced; A1 geometry table + A2
ARI/NMI + A3 acc/F1/AUC reported per (dataset, representation); figures render;
the fallback-vs-HIC agreement line stated. Full suite + ruff + mypy green in the
cloned env (main baseline 1062/8/16, ruff 3, mypy 21).

**Out of scope:** A4 on HIC; changing the planted-corpus results; new `src/` code
(the loader + distances + pipeline functions already exist — this is a driver +
config + tests).
