# Approach rigor — method- and framing-level items beyond data and statistics

**Status:** planning note (not yet a ledger task). Companion to `DATA.md` /
`DATA_RIGOR.md` (data) and `STATS_PASS_PLAN.md` (statistics). Four items,
user-selected from the wider approach review (2026-07-22): the naive baseline,
the structural-vs-label-aware status of `d_I`, application motivation, and the
reproducibility artifact.

---

## 1. Naive baseline (add to the whole comparison)

**Problem.** The five competitors (WL histogram, NetLSD, HyperCOT, HPD,
nauty-Levi edit) are all sophisticated. Standard rigor asks the question none of
the current tables answer: *do any of them beat a trivial structural distance?*
Without a floor, "IsalHG AUC 0.73" has no anchor — a reviewer cannot tell
whether the task is hard or whether everyone is barely above triviality.

**Fix.** Add **one** naive baseline to every comparison surface (geometry table,
A2, A3, A4-capability row, HIC exhibit). Candidates, pick one primary:

| Candidate | Definition | Notes |
|---|---|---|
| **Degree-sequence L1** (recommended primary) | L1 between sorted primal-degree sequences (padded) | pure structure, O(n log n), obviously incomplete |
| Size signature | `|Δn| + |Δm|` (+ arity-histogram L1) | even cheaper; near-content-free |
| Incidence-set Jaccard | 1 − Jaccard over canonical-ized edge sets | needs a vertex alignment convention — only if cheap to do honestly |

Degree-sequence L1 is the standard choice: interpretable, metric (L1 on sorted
vectors), and it slots into the existing pipeline as just another `D_rep`
(`D.npy` cache like every competitor).

**Interpretation contract (write it before seeing numbers).** If a sophisticated
method barely beats degree-sequence L1 on a task, report that plainly — it means
the task's signal is mostly first-order. If IsalHG and the field clearly beat
it, the naive row contextualizes the gains. Either outcome improves the paper;
neither is suppressed.

**Also fill its capability-matrix row** (`CAPABILITY_MATRIX.md`): complete ✗,
metric ✓, decodable ✗, navigable —, scales ✓. The matrix then spans naive →
lossy-vector → transport → complete, which strengthens the framing.

**Cost.** One distance function + one registry entry + re-run of the cached-`D`
analyses. The cheapest item in the whole revision.

**Ledger framing.** One small task; depends on the `metric_space/distances`
registry (T-M1a) and slots into the sweep harness. Acceptance: naive-baseline
row present in every comparison table and the capability matrix; interpretation
sentence present regardless of outcome.

---

## 2. Structural vs label-aware `d_I` — resolve as a small formal result

**Problem.** `d_I` is measured over the seed-label-prefixed token sequence
`F(H) = (ℓ_V(seed), w*_c(H))`, and the encoder threads vertex/edge labels
through `LabelVocabulary` (labels participate in the seed cascade, tie keys, and
token fields). Two regimes follow:

- **Synthetic corpora:** trivial vocabulary (`LabelVocabulary.trivial()`), so
  `F ≡ w*_c` and `d_I` is **purely structural**. All geometry headlines
  (ν = 0.250, D̂ = 26, stress 0.062) are structural-geometry claims.
- **Real labeled data (HIC IMDB):** the vocabulary is non-trivial, so `d_I`
  mixes **structure and labels**. The real-data ν/D̂ rows are therefore not
  measuring the same object as the synthetic rows, and the current prose does
  not say so.

**Fix — as a small formal result, not a prose caveat** (user decision: the
article is too long for an extended discussion; a compact statement is both
shorter and stronger). Add to the foundation section, immediately after
Corollary A:

> **Remark/Proposition (label-conditional metric family).** For each vocabulary
> `Σ = (Σ_V, Σ_E)`, `d_I^{k,h,Σ}` is a metric on isomorphism classes of
> connected `Σ`-labelled hypergraphs of arity ≤ k, where isomorphism means
> **label-preserving** isomorphism. Under the trivial vocabulary the metric is
> label-free and coincides with the structural metric on unlabelled hypergraphs.
> Metrics from different vocabularies are members of an index family and are not
> comparable; in particular, `d_I^Σ(H, H') ≥` [resp. is unrelated to] the
> structural `d_I^⊥(H, H')` obtained by forgetting labels.

Proof obligations are near-zero: the metric axioms are Corollary A verbatim per
fixed `Σ` (Theorem A is already proved for arbitrary vocabularies — the
augmented fingerprint `F` exists precisely for the non-trivial-vocabulary case).
The only genuinely new claim worth checking is the relation between labelled and
label-forgotten distances — if a one-line argument (or counterexample) is not
immediate, state it as a **conjecture/remark without the comparison clause** and
keep only the family statement, which is already established.

**Consequential edits (mechanical, small):**
- The geometry table and HIC rows gain a one-word column or footnote: metric =
  `d_I^⊥` (structural) for all synthetic corpora, `d_I^Σ` (label-aware) for HIC.
- One sentence in the HIC exhibit: "the real-data rows measure the label-aware
  member of the family; cross-regime ν/D̂ values are read as two objects, not
  one."
- This also cleanly explains *why* the HIC geometry may differ (D̂ ≈ 10–11)
  beyond just "real data is different."

**Decision point for the PI:** whether HIC should *additionally* be run with the
trivial vocabulary (labels stripped) to give a structural-only real-data row.
One extra `D.npy` per HIC dataset; makes the synthetic↔real geometry comparison
apples-to-apples. Recommended if cheap; not gating.

**Ledger framing.** One doc-side task (the Remark + table annotations) + an
optional compute task (label-stripped HIC re-run). Acceptance: every reported
`d_I` value in the article is unambiguously attributable to `d_I^⊥` or
`d_I^Σ`; the Remark states the family; no cross-vocabulary value is pooled or
directly compared.

---

## 3. Application motivation — one practitioner use case per application

**Problem.** A1–A4 are currently motivated by geometry licences (correct,
internal) but not by *external* need. For an applied venue (*Information
Sciences*), each application must open with one concrete practitioner scenario,
or the section reads as a toy demonstration suite.

**Fix.** One or two sentences per application, at the top of each subsection.
Candidate use cases (verify domain fit against the literature before writing;
prefer ones with a citable precedent for the task, not for our method):

| App | Candidate practitioner scenario |
|---|---|
| **A1 (map)** | Surveying a corpus of chemical reaction networks (reactions = hyperedges over species) or logic-circuit motifs: an at-a-glance similarity map of structural variants, e.g. triaging which reaction mechanisms in a database are structurally redundant. |
| **A2 (clustering/medoids)** | Grouping protein-complex or pathway hypergraphs by structural family and returning a *medoid* — an actual representative hypergraph, not a centroid in feature space — as the exemplar shown to the analyst. |
| **A3 (kNN)** | Classifying a new co-authorship or collaboration hypergraph by structural type ("which known collaboration pattern does this team resemble?"); any setting where whole-hypergraph labels exist and instances arrive one at a time. |
| **A4 (path)** | Interpolating between two network states — e.g. two snapshots of a metabolic or co-membership hypergraph — with every intermediate a *valid, inspectable hypergraph*: a structural morphing / edit-plan tool no fingerprint method can offer. |

**Discipline:** each scenario must match the measured scale honestly (small
connected hypergraphs, arity within cap). Do not promise metabolome-scale
analysis the feasibility envelope excludes; phrase as motif-/module-scale.

**Ledger framing.** Writing-only; lands in `empirical/applications.md` (one
opening paragraph per application) at article-drafting time. Pairs with the
`literature-search` agent to find one citable precedent per scenario.
Acceptance: each of A1–A4 opens with a practitioner scenario consistent with the
feasibility envelope, with ≥ 1 citation.

---

## 4. Reproducibility artifact

**Problem.** *Information Sciences* increasingly expects a released artifact.
Nearly everything exists in-repo but is not assembled or stated: pinned envs,
seeds, vendored competitor code, the proof volume, the result caches.

**Fix — assemble and state.** The artifact is a tagged repository release (plus
archived deposit, e.g. Zenodo DOI) containing:

| Component | Source (already exists) | Action |
|---|---|---|
| Code | `src/isalhg` + `experiments/` at the submission tag | tag + freeze |
| Environments | `environment.yml`; the pinned HyperCOT conda env (`hypernetx==1.2`, POT) | export exact `conda list` lockfiles for main + HyperCOT envs |
| Seeds & configs | seed values printed into result JSONs; `experiments/article/configs/*.yaml` | verify every result record carries its seed (standing rule) |
| Competitor versions + licenses | `netlsd` (MIT), `pynauty`, `rapidfuzz`, vendored HPD (`Hor_dissimilarity_measures`, MIT, provenance header), HyperCOT (MIT), HIC (Apache-2.0) | one VERSIONS/LICENSES table in the artifact README; confirm vendored provenance headers are present |
| Proof | `theorem_a_completeness.{tex,pdf}` | include as supplement (also satisfies the proof-inclusion requirement) |
| Result caches | `D.npy` + meta.json trees (drive: `results/`) | include the small caches (`D.npy` are KB–MB); document how to regenerate the large ones |
| Reproduction entry point | — | a top-level `REPRODUCING.md`: env setup → per-figure command → expected output hash/values |

**One genuine gap to close:** the Picasso-only steps (E1′ exact-HGED blocks) are
not reproducible on a laptop. State the resource envelope honestly in
`REPRODUCING.md` (per-block hours/GB, the measured 100 GB/18 h ceiling) and ship
the resulting `D.npy` caches so downstream figures reproduce without the HPC
step.

**Ledger framing.** One assembly task at pre-submission time (after the sweep
re-runs land, so the caches are final). Acceptance: a clean-machine dry run
reproduces at least the bits table, the geometry table, and one application
figure from the artifact alone, following `REPRODUCING.md`; the
VERSIONS/LICENSES table is complete; the proof PDF is in the supplement.

---

## Sequencing note

Item 1 (naive baseline) should enter **before** the sweep + stats re-runs
(`DATA.md` §7, `STATS_PASS_PLAN.md`) so its row is produced by the same harness
and carries the same CIs — retrofitting it later doubles the compute. Item 2's
Remark is doc-side and can land any time before drafting; its optional
label-stripped HIC run rides with the real-data tasks. Items 3–4 are
drafting-time and pre-submission-time respectively.
