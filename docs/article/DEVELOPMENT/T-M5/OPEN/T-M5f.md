# T-M5f — Geometric characterization of `(w*_c, d_Lev)`: the article's headline object
**Declared:** 2026-07-17 20:30 CEST
**Status:** OPEN
**Depends on:** T-M1b (`d_I`), T-M2/T-M4 (`metric_space/metrics/embedding.py` classical-MDS solve); feeds T-M5b (MDS flagship)
**Delegation:** agent
**Why out of scope:** Surfaced in the 2026-07-17 way-forward analysis; the stated main strength of the paper is the metric's geometry, which is currently only gestured at (`stability.md` §5, PROPOSAL §5) and must become a first-class, measured contribution rather than a by-product of the MDS application.
**Context to read first:**
- `docs/article/theoretical/stability_reformulations.md` §7.3 — the characterization spec this task realizes
- `docs/article/theoretical/stability.md` §5 ("non-Euclidean geometry and MDS") — the thin section to develop
- `docs/article/PROPOSAL.md` §5 ("MDS intrinsic-dimension selection") — the PI's CV-MDS estimator, negative-eigenvalue floor, Mardia ratios
- `docs/article/DEVELOPMENT/T-M5/OPEN/T-M5b.md` — the flagship MDS run that consumes this spec
- `docs/article/RELATED_WORK.md` §Implementation dependencies — `scipy.linalg.eigh` classical-MDS solve
- `.claude/rules/coding_rules.md` — always
**Description:** Develop the geometry of `(w*_c, d_Lev)` as a first-class object. (a) **Theory** (textbook, no new theorem): finite discrete metric; generic non-Euclideanness (Schoenberg — double-centred Gram `B` has negative eigenvalues); Bourgain `O(log n)` `L2` embedding always available; JL for approximate dimension reduction. (b) **Measurement spec for T-M5b**: eigenvalue spectrum of `B`, negative-eigenvalue mass ratio `Σλ⁻/Σ|λ|`, cross-validated intrinsic dimension `D̂` (PI's estimator), stress-vs-dimension curve, Euclidean distortion, pairwise-distance concentration — with `D̂` reported as a standalone result. HGED-free, so it runs at application scale, not the exact-oracle ceiling.
**Acceptance:** `stability.md` §5 expanded into a full geometric-characterization section; T-M5b's measurement list extended with the invariants above; a `metric_space/metrics/` geometry-report helper (eigen-spectrum + negative-mass ratio + distortion) specced and unit-tested (pinned spectra on a small fixture; PSD vs non-PSD corpus flagged correctly).
**Out of scope here:** the reposition doc surgery (T-TBd); running the MDS experiment end-to-end (T-M5b owns the run); any HGED call (geometry self-validates); changes to `w*_c` or the distance.
