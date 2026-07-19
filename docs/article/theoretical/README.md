# Theoretical track

**Status:** ACTIVE. Breaks down the theoretical claims
of `docs/article/PROPOSAL.md`. Companion: `../empirical/` (the experiments that
measure what the theory frames).

## The logical spine

The theory builds a **foundation** (Theorem A: a complete invariant ⇒ a metric),
frames the **geometry** of the resulting space (the characterization the paper
leads with), and closes with the **relation to HGED** (a discussion of limits:
envelope + impossibility + mechanisms — not a pillar). Each link maps to a
measurement in `../empirical/`.

```
  Theorem A (Completeness)   ── w*_c(H1)=w*_c(H2) ⇔ H1≅H2            [FOUNDATION]
        │  ⇒ (Corollary A)
        ▼
  Metric  (·, d_I)           ── d_I a metric on isomorphism classes
        │  whose geometry we characterize
        ▼
  Geometry  (characterize)   ── ν · D̂ · distortion · concentration/hubness      ★
        │                        · local sensitivity s(e) · ladder response
        │  licenses
        ▼
  Applications (exploit)     ── MDS · k-medoids/dendrogram · kNN · path
        │                        (task metrics vs competitors)
        ▼
  Discussion (limits)        ── |w*_c| ≤ m(1+kn) ; d_I ≤ m(1+kn)·HGED (envelope)
                                ; no bi-Lipschitz proxy possible (drift, avalanche)
                                ; one exact-HGED figure (ours only)
```

**The siblings are under review — we own the whole chain for hypergraphs.**
Completeness and the metric corollary are re-proved here from first principles
(*not a port*: hypergraph completeness required the tie-complete encoder, the
greedy one being provably incomplete — a pinned counterexample). The geometric
characterization and the geometry-licensed applications exist in neither
sibling.

- **Theorem A (foundation)** — **proved for `w*_c`**; with Corollary A
  (`d_I` is a metric on isomorphism classes), the only formal theorem +
  corollary pair the paper states in full. See `stability.md` §1.
- **Geometry (characterize)** — the measured shape of `(·, d_I)`: non-Euclidean
  mass `ν`, intrinsic dimension `D̂`, distortion, concentration + hubness, the
  local sensitivity profile, the ladder response. Governed by the
  **no-orphan-geometry rule**: every invariant is consumed by an application
  licence or a competitor contrast. See `geometry.md`.
- **Applications (exploit)** — each licensed by a measured invariant, scored on
  task metrics vs competitors. See `../empirical/applications.md`.
- **Relation to HGED (discussion)** — the surviving content of the retired
  Theorem-B capstone: the length lemma and the unconditional envelope as short
  propositions, the impossibility of a bi-Lipschitz proxy (literature + our
  drift/avalanche mechanisms) in prose, one correlation figure. The conditional
  bound and its five hypotheses stay out of the article. See `stability.md`
  §2–4 (analysis record) and PROPOSAL §5 (what the paper actually states).

## Files

- `geometry.md` — the **characterization**: the intrinsic geometry of
  `(·, d_I)` — non-Euclidean mass, intrinsic dimension, distortion,
  concentration/hubness, local sensitivity, ladder response — and the
  no-orphan-geometry rule binding each invariant to its consumer.
- `stability.md` — the **foundation** (§1 completeness → metric: Theorem A +
  Corollary A, the paper's formal core) and the **HGED-relation analysis**
  (§2–4: the envelope, the conditional bound and why it fails generically, the
  avalanche/drift mechanisms). §2–4 are the *internal record* the discussion
  section compresses; only the §5-of-PROPOSAL subset reaches the paper.
- `stability_reformulations.md` — value analysis after the stability
  post-mortem: the proxy-question resolution (§1), what the analysis is still
  worth (§2), the reformulation space (transcoding, block moves), and the
  completeness–stability frontier argument (§6) the discussion's impossibility
  prose draws on. Non-normative; engineering follow-ups tracked in
  `DEVELOPMENT/`.

## Mapping to PROPOSAL points

| PROPOSAL point | Theoretical treatment |
|---|---|
| §0 premise / foundation | Thm A + Cor. A — `stability.md` §1 |
| §2 geometry (pillar 1) | the measured invariants — `geometry.md` |
| §3 applications well-posedness | non-Euclidean `d_I`, MDS brackets, hubness — `geometry.md` |
| §5 discussion (HGED relation) | envelope + impossibility + mechanisms — `stability.md` §2–4, `stability_reformulations.md` §1/§6 |
