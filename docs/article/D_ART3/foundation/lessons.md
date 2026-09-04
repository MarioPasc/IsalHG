# Lessons — what the previous iterations teach the new experiments

*Foundation sheet for the D-ART3 re-scope, 2026-09-03. Standing instruction
from the author (2026-09-03): **prior results are not assets to reuse; every
experiment of the new article may start from zero.** What carries over is the
experience. This file turns that experience into design rules. Each rule names
the episode that taught it (provenance in `measured_facts.md`).*

---

## 1. Corpus design

- **L1 — Size confounds everything.** On the first design corpus a distance
  built from `|Δn| + |Δm|` alone reached ARI 0.442 / AUC 0.932 and beat five
  of seven representations (Stratum A, retracted 2026-08-09). Every corpus
  with class labels must fix `(n, m, k)` — and where possible the degree
  sequence — across classes, and must always include the two naive floors
  `size_l1` and `degree_seq_l1`. A confound guard test exists
  (`tests/integration/test_corpus_confound_guard.py`); port it.
- **L2 — Regular, trivially-labelled substrates are a dead end for `d_I`.**
  On d-regular k-uniform hypergraphs a degree-preserving 2-edge swap rewrites
  ≈30 of ≈50 canonical tokens, and the maximum ARI reachable over four
  constructions was 0.234 (T-M7p, "impossibility record"). WL is also blind
  there (one colour). KB corpora must be **labelled** (unary predicates on
  constants, predicate names on facts) and structurally **anchored**; never
  build a class structure out of small perturbations of an unlabelled regular
  substrate.
- **L3 — Steiner-type and highly symmetric substrates are uncomputable.**
  STS(13) ≈ 160 s per instance, STS(15)/PG/AG designs DNF at 300 s, rigid
  STS(15)/STS(19) > 900 s; the cost driver is the pair-coverage tie structure,
  not `|Aut|`. Do not use combinatorial designs as KB substrates.
- **L4 — The feasibility envelope is the binding constraint, and it is per
  item.** Unlabelled random 3-uniform: p50 1.7 s at `n = 24` low density,
  DNF beyond `n ≈ 24–32`; `k = 5` only at `n = 8`. Canonicalization is paid
  once per KB, so the envelope caps each KB, not `N`. **Measured 2026-09-03
  on real KBs (`probes_2026-09.md` §4–§5): the frontier is the incidence
  mass `m`, not `n`** (an ego-net with `n = 25, m = 150` runs in 0.06 s while
  `n = 14, m = 114` times out; `m ≤ 111` → 20/21 complete, `m ≥ 253` →
  0/15), and **labels are the tie-breaker** (WD50K: labelled milliseconds,
  unlabelled 33 % DNF at `n ≈ 13`; ARB: labelled 1.9× faster). Size KB
  corpora by `m` and always keep the labels.
- **L5 — Corpus-level arity must fit the cap.** HIC failed the gate because
  the corpus-level `k` was 110 against `K_MAX = 10`; the arity-capped
  sub-corpus lost 21 % of items and the DNF tail was symmetry-driven, not
  size-driven. Pick datasets whose *maximum* fact arity is small (ARB tier 1:
  max arity 5) rather than filtering a heavy tail.
- **L6 — Real "single giant network" datasets are collections only after a
  citable derivation.** The ego-network of Qin et al. (ICDE 2023, Def. 1) is
  the citable derivation and is implemented (`core/sparse_hypergraph.py::ego_network`).
  Ego-nets of one dataset are exactly "N knowledge bases over one signature".

## 2. Distance and representation hygiene

- **L7 — `d_I` runs on tokens, not characters.** The idea-3 draft's "384×
  slower" figure used character length; the token length at `n = 10` is
  ≈ 22–44 tokens and `L²` is the same order as `n³` (gate G-L4). Never quote
  character lengths.
- **L8 — Labelled inputs need the augmented fingerprint.** The bare `w*_c`
  omits its own seed vertex's label; `d_I` on labelled inputs is taken over the
  seed-label-prefixed token sequence (one substitution when seed labels
  differ). KBs are always labelled, so the whole article runs on `d_I^Σ`, and
  every prior geometry number (measured on `d_I^⊥`) is from a different
  member of the family — another reason to re-measure rather than reuse.
- **L9 — The nauty contrast baseline is byte-level.** `NautyLeviEditDistance`
  computes Levenshtein over `color_signature ++ pynauty.certificate(B(H))`
  *bytes*. The prior "3/5/9 vs 20/30/37" sensitivity contrast therefore
  compares IsalHG tokens against certificate bytes. If a canonical-labelling
  edit distance stays in the paper, its tokenization must be stated and
  defensible (e.g. one symbol per canonical adjacency row), and the contrast
  re-measured on that basis.
- **L10 — `k` and the tuple depth index the metric family.** `w*_c` depends on
  the pointer count `k` and the structural-tuple depth; distances computed
  under different `(k, h)` live in different spaces. One `k` per comparison
  (the corpus maximum).
- **L11 — Length-normalized edit distance is not a metric.** Keep raw
  Levenshtein primary; report a normalized variant only as an ablation and
  never feed it to an algorithm that needs the triangle inequality.

## 3. Evaluation discipline

- **L12 — Pre-register the interpretation.** Every competitor table carries a
  written contract before results are seen; no baseline is removed for
  winning. This is what made the T-M4b loss reportable without loss of face
  and it is what a TKDE reviewer will check.
- **L13 — Task metrics vs planted labels are where `d_I` lost.** On the FINAL
  size-controlled corpus nauty-Levi edit, HPD and NetLSD beat `d_I` on ARI
  and kNN AUC, all Holm-significant. The new article must not make "recover
  planted small-perturbation classes" the headline evaluation of any
  application. Evaluate what the theory guarantees (metric, exactness,
  certificates, decodability) and what the application delivers (a decoded
  consensus, a certified ratio, a false-merge count), with class-recovery
  reported under contract as a secondary axis.
- **L14 — Statistics harness: 27 seeds, 95 % BCa CIs, bidirectional
  Holm-corrected Wilcoxon.** Reuse the harness, not the numbers. Persist the
  Wilcoxon results explicitly (they were silently never written once).
- **L15 — Censoring must be reported per stratum.** DNFs under a fixed
  per-item budget are dropped and counted, yield reported per size bucket,
  label-correlated censoring stated. Inherited from the HIC exhibit.
- **L16 — Measure the gate before scoping the experiment.** Every prior plan
  that skipped a gate (HIC arity, Stratum A size) paid for it. The gates for
  the new article are the ego-net size/`N` distribution, the labelled
  canonicalization time, and the consensus-search landscape (all probed
  2026-09-03; see `probes_2026-09.md`).

## 4. Claims discipline

- **L17 — Concede identity and deduplication speed to nauty/bliss/Traces**
  in the introduction; `w*_c` is orders of magnitude slower on symmetric
  inputs and equally exact. Never build a claim on canonicalization speed.
- **L18 — Never call `d_I` a proxy for an edit distance.** Spearman ρ = 0.622
  against exact HGED, an unconditional but enormous envelope
  `d_I ≤ m(1+kn)·HGED`, and an impossibility argument for any bi-Lipschitz
  relation. `d_I`-minimal is *constructively* minimal, not fact-minimal; say
  so and measure the gap where an oracle runs.
- **L19 — Decodability claims must be about the ambient space.** The shipped
  A4 "decodability score" was vacuous (it decoded objects that were already
  hypergraphs). The real statement is P1: every word in `Σ_HG*` decodes to a
  connected hypergraph, and the interior of an alignment path is non-canonical
  words that still decode (62/62 measured). Prove it, pin it, and use it
  where it matters: a consensus word that is not any input's canonical form
  still names a knowledge base.
- **L20 — Every geometric invariant needs a consumer.** The v3 geometry grew
  unreadable (PI: "se pierde uno leyendo"). Measure `ν` (licenses
  medoid-type methods and metric MDS over classical MDS), hubness (kNN-based
  outlier scores), and the single-edit response (the limitation), and nothing
  without a consumer.
- **L21 — Apply the PI's criterion literally.** *"Buscar aplicaciones en las
  que sea imprescindible o muy ventajoso lo que diferencia IsalHG: un espacio
  con una distancia definida, formado por puntos que son invariantes frente a
  isomorfismos."* Applications are metric-space operations over collections
  of iso-classes; the differentiators are exactness, metric guarantees,
  polynomial pairwise cost, and a decodable ambient space.

## 5. Engineering

- **L22 — Editable installs are path-pinned.** Any worktree agent must clone
  the conda env; a stale `.so` produces phantom failures (`CLAUDE.md`).
- **L23 — The oracle is expensive and frozen.** Exact HGED peaked at
  > 100 GB / 18 h for one 630-pair block at `n = 10`. Any new oracle use is
  `n ≤ 10, m ≲ 8` per pair, on HPC, and scoped before it is scheduled.
- **L24 — HyperCOT is gated at `N ≤ 20`.** It never ran on the FINAL corpus;
  either drop it or state the gate.
- **L25 — Verify before trusting a "VERIFIED" tag.** The idea-3 development
  marked the non-metricity of bipartite GED as verified on the strength of a
  sketch and unverified citations. This re-scope re-checked it computationally
  (`probes_2026-09.md`). Treat every prior verification tag the same way.
