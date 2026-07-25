# T-M8d — Reproducibility artifact: assembly + REPRODUCING.md
**Declared:** 2026-07-22 11:56 CEST
**Status:** DONE (closed 2026-07-25)
**Depends on:** T-M7d, T-M7e, T-M7f, T-M7g merged (the caches and tables must
be final — assembling earlier means assembling twice). Last task of the S7
session.
**Origin:** 2026-07-22 REVIEW pass (`docs/article/REVIEW/APPROACH_RIGOR.md`
§4), directed by Mario. *Information Sciences* increasingly expects a released
artifact; nearly everything exists in-repo but is not assembled or stated.
**Context to read first:**
- `docs/article/REVIEW/APPROACH_RIGOR.md` §4 — the component table and the
  Picasso-gap handling
- `docs/article/RELATED_WORK.md` §Implementation dependencies — the verified
  repo URLs + licenses the VERSIONS/LICENSES table draws from
- `docs/article/DEVELOPMENT/README.md` §Public code to leverage — the vendored
  components (HPD provenance header, HyperCOT pinned env)
- `docs/article/DEVELOPMENT/T-M5/CLOSED/T-M5a.md` — the E1′ HPC resource record
  (per-block hours/GB, the 100 GB/18 h ceiling) for the resource-envelope
  statement
**Description:** Assemble the release artifact: (1) tag the repository at the
final post-S7 state; (2) export exact lockfiles (`conda list --explicit` or
equivalent) for the main `isalhg` env and the pinned HyperCOT env; (3) write
the VERSIONS/LICENSES table (netlsd MIT, pynauty, rapidfuzz, vendored HPD
`Hor_dissimilarity_measures` MIT with provenance header verified present,
HyperCOT MIT, HIC Apache-2.0, plus exact versions); (4) include the proof
volume (`theorem_a_completeness.{tex,pdf}`) as the supplement; (5) include the
small `D.npy` + `meta.json` caches (KB–MB scale) and document regeneration for
the large ones; (6) write the top-level `REPRODUCING.md`: env setup → per-figure
command → expected output values; state the HPC-only steps (E1′ exact-HGED
blocks) honestly with the measured resource envelope, and ship their caches so
downstream figures reproduce without the HPC step; (7) verify every result JSON
carries its seed in-content (standing rule — spot-check, fix stragglers);
(8) deposit the tagged artifact (Zenodo or equivalent) and record the DOI.
**Acceptance:** a clean-machine dry run (fresh env from the lockfile, no
network beyond package install) reproduces at least the bits table, the
geometry table, and one application figure from the artifact alone following
`REPRODUCING.md`, with values matching the published ones; the VERSIONS/LICENSES
table is complete and license-compatible; the proof PDF is in the supplement;
the E1′ resource envelope is stated and its caches ship; the DOI (or the
deposit-pending note with the PI) is recorded.
**Out of scope here:** any code or result change discovered during the dry run
beyond trivial path fixes — file follow-ups via `task-handoff`; journal
submission mechanics.

---

## Closing note — 2026-07-25 (orchestrator, drained tree)

Assembled the release artifact against the final post-S7 caches.

**Deliverables (all committed):**
- `REPRODUCING.md` — env setup, the verified reproduction command, expected
  values, the HPC-only steps with their measured resource envelope, and the
  arity-axis limitation stated honestly.
- `scripts/reproduce_tables.py` — the reproduction driver. Re-aggregates
  Stratum A from the shipped `seed_metrics` with the published BCa/Wilcoxon/Holm
  pipeline and diffs against the committed stats.
- `artifacts/reproducibility/{VERSIONS_LICENSES.md, isalhg_env.lock.txt,
  isalhg_hypercot_env.lock.txt, isalhg_pip_freeze.txt}` — the dependency /
  license table (all MIT/Apache-2.0, HPD provenance header verified present in
  `_hpd_vendor.py`) and exact lockfiles for both envs.
- `<results-drive>/RESULTS_MANIFEST.md` — the single-folder results map: which
  corpus each experiment used, the directory inventory, the two protection
  rules (local `stats/` authoritative; `superseded/` kept-not-current), and the
  statistics provenance. (Lives on the drive with the results, not in git — no
  large binaries in-tree.)

**Dry-run — actually executed, not asserted.**
```
PYTHONPATH=. python scripts/reproduce_tables.py --results-root <results>/T-M7d
geometry nu                 committed 0.0974229  reproduced 0.0974229  PASS
geometry d_hat                        16.8148              16.8148     PASS
geometry stress                       0.0461492            0.0461492   PASS
geometry hubness_skewness             0.907314             0.907314    PASS
bits median_ratio                     1.3048               1.3048      PASS
wilcoxon degree_seq a2::ari rev p_holm 4.47035e-07         4.47035e-07 PASS
DRY-RUN PASS
```
The geometry table, bits, and a paired Holm-corrected Wilcoxon reproduce from
the shipped per-seed caches alone (no cluster, no D-matrix recompute) and match
the committed stats to full precision.

**Seed-in-content:** spot-checked `T-M7d/seed_metrics/` — every JSON carries its
`seed` field.

**Proof supplement:** `proofs/completeness/theorem_a_completeness.{tex,pdf}` on
the results drive, referenced in `REPRODUCING.md` §7.

**DOI:** deposit-pending (Zenodo, at PI direction on submission) — permitted by
the task's acceptance as the recorded deposit note. The tag below is the deposit
content.

**Closing checks:** suite 1478 passed / 9 skipped / 29 deselected; ruff 3
(driver adds 0); mypy 21. Baselines matched.
