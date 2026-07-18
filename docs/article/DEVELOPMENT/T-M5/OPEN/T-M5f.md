# T-M5f — Geometric characterization of `(w*_c, d_Lev)`: the static invariants
**Declared:** 2026-07-17 20:30 CEST · **extended** 2026-07-18 17:56 CEST (D-ART2)
**Status:** OPEN
**Depends on:** T-M1b (`d_I`), T-M4 (`metric_space/metrics/` home); feeds T-M5b (MDS flagship) and T-M5d (kNN precondition)
**Delegation:** agent
**Why out of scope:** Surfaced in the 2026-07-17 way-forward analysis; promoted by D-ART2 to the article's characterization leg (characterize → exploit).
**Context to read first:**
- `docs/article/theoretical/geometry.md` — the six invariants + the no-orphan-geometry rule (the spec this task realizes; the two *dynamic* invariants are T-M5g's)
- `docs/article/PROPOSAL.md` §2 — the invariant→consumer table
- `docs/article/DEVELOPMENT/T-M5/OPEN/T-M5b.md` — the flagship MDS run that consumes this spec
- `docs/article/RELATED_WORK.md` §Geometry diagnostics — Radovanović et al. 2010 (hubness)
- `docs/article/CODE_DESIGN.md` §2 tree (`metrics/{embedding,geometry}.py`) — where the helpers land
- `.claude/rules/coding_rules.md` — always
**Note (2026-07-17):** the theory half is drafted as
`theoretical/geometry.md`; refine it only if the measurement forces it.
**Description:** Implement and spec the **static** geometric invariants. (a)
`metric_space/metrics/embedding.py`: classical-MDS solve (double-centre → eig),
eigenvalue spectrum, negative-eigenvalue mass `ν = Σλ⁻/Σ|λ|`, PSD flag,
stress-1, Shepard data, CV-reconstruction-error harness input (`D̂` selection
runs in experiments). (b) `metric_space/metrics/geometry.py`: concentration
stats (pairwise histogram summary, diameter/median ratio, length-difference
floor) and **hubness** (`k`-occurrence `N_k` skewness). (c) The **per-corpus
geometry table** spec consumed by T-M5b's runner: one row per (corpus,
representation) with `ν`, PSD, `D̂`, stress@`D̂`, concentration, hubness — the
paper's characterization table, also the competitor-geometry axis.
**Acceptance:** `theoretical/geometry.md` consistent with the measured
invariants (refined if the measurement surfaces gaps); helpers unit-tested
(pinned spectra on a small fixture; PSD vs non-PSD corpus flagged correctly;
hubness skewness against a hand-computed value); the geometry-table spec
recorded in T-M5b before its run.
**Out of scope here:** the dynamic profiles (sensitivity/ladder — T-M5g);
running MDS end-to-end (T-M5b owns the run); any HGED call; changes to `w*_c`
or the distance.
