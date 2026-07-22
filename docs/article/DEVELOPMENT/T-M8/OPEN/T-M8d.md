# T-M8d — Reproducibility artifact: assembly + REPRODUCING.md
**Declared:** 2026-07-22 11:56 CEST
**Status:** OPEN
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
