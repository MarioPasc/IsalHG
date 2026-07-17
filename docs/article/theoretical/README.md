# Theoretical track

**Status:** DRAFT (scoping 2026-07-08). Breaks down the theoretical claims of
`docs/article/PROPOSAL.md`. Companion: `../empirical/` (the experiments that
test each theorem). Literature positioning pending the background
literature-search (results to be folded in next iteration).

## The logical spine

The paper's theory is a three-link chain; each link is a prerequisite for the
next, and each maps to an empirical validation in `../empirical/`.

```
  Theorem A (Completeness)            ── w*(H1)=w*(H2) ⇔ H1≅H2
        │  needed for
        ▼
  Corollary A (Metric)               ── d_I is a metric on iso-classes
        │  gives well-posed distance for
        ▼
  Theorem B (Stability / Lipschitz)  ── d_I(H,H') ≤ C(k,Δ)·HGED(H,H')   ★ core novelty
        │  its Δ-dependence predicts
        ▼
  Empirical prediction               ── correlation ρ(d_I, HGED) decays with density
                                        (falsifiable; tested in ../empirical/correlation.md)
```

- **Theorem A** — **proved for `w*_c`** (T-TA, PI-reviewed 2026-07-09; false for
  the greedy variants). The metric property (Corollary A) is established, not
  contingent. See `stability.md` §1.
- **Corollary A** — direct port of IsalGraph Corollary 1 (metric on iso-classes)
  once Theorem A holds. See `stability.md` §1.
- **Theorem B** — the contribution IsalGraph did **not** make. IsalGraph stated
  locality as "a claim supported by empirical evidence" (no bound). We prove the
  bound (or a conditional/average-case version) for hypergraphs. See
  `stability.md` §2–§4.

## Files

- `stability.md` — the core: completeness/metric foundation (§1), the stability
  theorem and its proof strategy (§2), the avalanche/seed-flip obstruction (§3),
  and the theory↔empirics bridge via C(k,Δ) (§4). This is the document to iterate.
- `stability_reformulations.md` — post-T-TBb analysis (2026-07-17): what Theorem B
  is worth if the bound never improves, the proxy-question resolution, and the
  reformulation space (displacement-token transcoding → T-TBc, entropy-coded
  bits → T-M4a, block-move distance, structure-first tour). Non-normative.

## Mapping to PROPOSAL points

| PROPOSAL point | Theoretical treatment |
|---|---|
| §1 pivot (metric space) | Cor. A (metric) — `stability.md` §1 |
| §2 central claim (correlation) | Thm B *explains* the correlation — `stability.md` §4 |
| §2 metric-vs-pseudometric | Thm A status — `stability.md` §1 |
| §4 applications well-posedness | MDS embeddability ← non-Euclidean d_I — `stability.md` §5 |
| §6 seed-selection refinement | interacts with the avalanche condition — `stability.md` §3 |
