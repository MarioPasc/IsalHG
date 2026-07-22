# T-M8c — Practitioner motivation for A1–A4 (one cited use case each)
**Declared:** 2026-07-22 11:56 CEST
**Status:** DONE
**Depends on:** nothing code-side. Independent of T-M7 lanes; must respect the
feasibility envelope T-M7b measures (do not promise scales the envelope
excludes — coordinate the final wording with the merged envelope figure).
**Origin:** 2026-07-22 REVIEW pass (`docs/article/REVIEW/APPROACH_RIGOR.md`
§3), directed by Mario. A1–A4 are motivated by geometry licences (internal) but
not by external need; for an applied venue each application must open with a
concrete practitioner scenario or the section reads as a toy demonstration
suite.
**Context to read first:**
- `docs/article/REVIEW/APPROACH_RIGOR.md` §3 — the candidate scenarios per
  application and the honesty discipline (motif-/module-scale phrasing)
- `docs/article/empirical/applications.md` — where the paragraphs land (top of
  each application subsection)
- `docs/article/RELATED_WORK.md` — where the new citations are recorded
- The `humanizer` skill conventions (academic register; no significance
  inflation) — applies to all new prose
**Description:** For each of A1–A4, write a one-to-two-sentence opening
practitioner scenario with ≥1 verifiable citation for the *task* (not for our
method). Candidates from the REVIEW spec — A1: at-a-glance structural triage of
reaction-network / circuit-motif corpora; A2: grouping pathway/complex
hypergraphs with a *medoid* (an actual representative hypergraph) as the
exemplar; A3: classifying an incoming collaboration/co-authorship hypergraph by
structural type; A4: interpolating between two network states with every
intermediate a valid, inspectable hypergraph (structural morphing / edit-plan).
Verify domain fit via the `literature-search` agent before writing; every
citation checked against the source (title, authors, venue, DOI — no
unverified references). Scale honesty: each scenario phrased at the
motif-/module-scale the feasibility envelope supports.
**Acceptance:** each of A1–A4 opens with a practitioner scenario; ≥1 citation
per scenario, verified and added to `RELATED_WORK.md` with its verification
note; no scenario implies scales outside the measured envelope; prose passes
the humanizer conventions (no "novel/groundbreaking", direct verbs); the
scenarios name the capability that makes IsalHG apt for the task (medoid =
real hypergraph; A4 intermediates decodable) without task-dominance claims.
**Out of scope here:** any change to the applications' methodology or results;
the §Usefulness reframing (T-M8b); competitor prose.

---

**Closing note (2026-07-22):**

Acceptance check — all items verified against the task's Acceptance field:

- A1 opens with: "Biochemical reaction networks represent each reaction as a
  hyperedge over its participating molecular species; a database of module-scale
  reaction networks therefore forms a corpus of small hypergraphs whose structural
  diversity an analyst surveys before selecting candidate mechanisms for experimental
  validation (Klamt, Haus, and Theis 2009; Benson, Gleich, and Leskovec 2016)."
  Citations: 2. `<!-- envelope-sensitive -->` flag present.

- A2 opens with: "Databases of biological network motifs and signaling-pathway
  submodules catalog structurally distinct higher-order interaction patterns;
  grouping these module-scale hypergraphs into structural families and returning a
  *medoid* — an actual representative hypergraph that an analyst can directly
  inspect, rather than a centroid undefined in non-Euclidean space — makes the
  structural taxonomy actionable (Milo et al. 2002)." Citation: 1. Medoid
  capability named. `<!-- envelope-sensitive -->` flag present.

- A3 opens with: "In co-authorship and collaboration networks, each paper or
  project forms a hyperedge over its participants; assigning an incoming
  team-structure hypergraph to one of a set of known structural types — using only
  its distance to labelled examples, without retraining — is a recurring
  classification task in the analysis of these systems (Newman 2001; Chodrow,
  Veldt, and Benson 2021)." Citations: 2. `<!-- envelope-sensitive -->` flag present.

- A4 opens with: "Temporal higher-order network datasets record a system's
  interaction structure at successive time points; comparing two snapshots asks not
  just how different the states are but which structural path connects them, with
  every intermediate a valid, inspectable hypergraph — a requirement that no
  fingerprinting method without a closed, decodable alphabet can satisfy (Holme and
  Saramäki 2012; Battiston et al. 2020)." Citations: 2. Decodability capability
  named. `<!-- envelope-sensitive -->` flag present.

- All 7 citations added to RELATED_WORK.md §"Application motivation — practitioner
  domains (A1–A4)" with verification notes (authors, title, venue, DOI; confidence
  level stated).

- No methodology or results prose touched. No d_I^⊥/d_I^Σ annotations touched
  (T-M8a not yet executed; those do not exist yet in applications.md).

- Scale honesty: all scenarios phrase at "module-scale" consistent with the locally
  admitted envelope (n≤21, k=3 Stratum B; n≤21 arity 3-5 Stratum A). The
  `<!-- envelope-sensitive -->` flag marks each scenario sentence so the T-M8b/final
  pass can reconcile if larger cells are admitted.

- Humanizer conventions: no "novel/groundbreaking"; direct verbs ("surveys",
  "assigns", "records", "connects"); academic register throughout.

- Capabilities named: A2 names medoid = actual representative hypergraph (not
  centroid); A4 names decodable intermediates via closed alphabet (requirement no
  fingerprinting method without decoder can satisfy). No task-dominance claims.

Checks: documentation-only task — pytest/ruff/mypy not run (no source code changed;
per agent instructions no conda env needed for docs/ work). ruff and mypy baselines
unaffected.
