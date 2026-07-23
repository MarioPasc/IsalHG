# T-M8e — REVIEW/DATA docs: Stratum A pruning + synthetic/real figures + proxy assessment
**Declared:** 2026-07-23 13:15 CEST
**Status:** DONE
**Depends on:** T-M7h (Stratum A feasibility pilot, CLOSED — provides the pruning evidence)
**Delegation:** agent
**Why out of scope:** This is a docs-only update task; the code that produced the pruning evidence and figures was delivered in T-M7h and the viz commit (945a571).
**Context to read first:**
- `docs/article/REVIEW/DATA.md` §2A ("Stratum A") — the section to update
- `docs/article/REVIEW/DATA_RIGOR.md` §2 ("three coverage gaps") — Gap 2 resolution + figure embed
- `artifacts/feasibility_pilot/feasibility_pilot_stratum_a.json` — the admitted-catalog evidence (14 kept, 9 dropped, with reasons)
- `artifacts/feasibility_pilot/admitted_catalog.txt` — human-readable summary of the 14 kept
- `artifacts/synthetic_catalog/` — generated figures: stratum_a_kept_hnx.png, arity45_kept_hnx.png, stratum_b_random_hnx.png, hic_imdb_wri_genre.png, hic_imdb_dir_genre.png
- `docs/article/REVIEW/REAL_DATA_CORPUS.md` — HIC real-data characterization
- `.claude/rules/coding_rules.md` — always
**Description:** Record the approved Stratum A data-pruning decision in the two REVIEW spec docs. Nine families were dropped (3 affine/projective planes + 3 large Steiner systems for `w*_c` feasibility-DNF; 3 complete hypergraphs for perturbation-failure). Fourteen families are kept. Embed the generated HyperNetX catalog figures and add a synthetic-vs-real proxy subsection documenting that real HIC hypergraphs are mixed-arity/sparse and the genuine real-data proxy is Stratum B, not the designs. Add a pilot-power placeholder subsection for sample-size numbers (to be filled post-pilot).
**Acceptance:**
- `docs/article/REVIEW/DATA.md` §2A contains: (a) kept-14 catalog table with arity/n/symmetry, (b) 9-exclusion table with categorical reasons, (c) coarse-class scheme for A2/A3, (d) synthetic-vs-real proxy subsection with 2 HIC figures embedded, (e) pilot-power placeholder subsection.
- `docs/article/REVIEW/DATA_RIGOR.md` contains: (a) perturbation-failure finding under Gap 2, (b) prune recorded as resolution, (c) figures embedded, (d) stale arity-coverage claims updated.
- All five figure paths verified to exist before linking.
- Task moved to CLOSED/ on the branch; ledger README counts corrected.
**Out of scope here:** Any code changes to `src/`, `experiments/`, or `tests/`. Do not edit SESSIONS.md, PROPOSAL.md, or any other REVIEW file.

---

**Closing note (2026-07-23).**

Docs updated on branch `T-M8e-review-data-pruning-figures`. No code touched.

Files changed:
- `docs/article/REVIEW/DATA.md` — §2A replaced with kept-14 catalog table + exclusion
  table (categorical reasons: feasibility-DNF vs perturbation-failure) + coarse-class
  scheme for A2/A3; new subsection "Synthetic vs. real — proxy assessment" with
  hic_imdb_wri_genre.png and hic_imdb_dir_genre.png embedded; new placeholder
  subsection "Sample size and power (pilot-determined)".
- `docs/article/REVIEW/DATA_RIGOR.md` — Gap 2 updated with S7 resolution and new
  perturbation-failure finding + stratum_a_kept_hnx.png + arity45_kept_hnx.png
  embedded; Gap 3 updated with S7 resolution note; new §3 proxy assessment subsection
  with hic_imdb_wri_genre.png + hic_imdb_dir_genre.png + stratum_b_random_hnx.png
  embedded; S7 pruning note added to the verdict paragraph.

All 5 figure paths verified to exist in `artifacts/synthetic_catalog/` before linking.
Admitted-catalog data sourced from `artifacts/feasibility_pilot/admitted_catalog.txt`
(17 feasibility-admitted) and the prompt context (3 perturbation-failing complete
hypergraphs) → 14 final.

Checks: docs-only task, no pytest/ruff/mypy run needed.
