# Empirical track

**Status:** DRAFT (scoping 2026-07-08). Breaks down the empirical claims of
`docs/article/PROPOSAL.md`. Companion: `../theoretical/` (the theorems these
experiments test).

## Three layers (the paper's empirical logic, per PI 2026-07)

The PI's stated structure — *theoretical proof → empirical proof under
controlled conditions → applications that exploit the theorem*:

```
  Layer 1  CONTROLLED VALIDATION of Theorem B          →  correlation.md
           d_I vs HGED correlation; density sweep;      (Exp E1–E3)
           single-edit sensitivity histograms;          (validates ../theoretical/stability.md)
           information-content comparison.

  Layer 2  APPLICATIONS that exploit stability          →  applications.md
           MDS (flagship, tutor-emphasized), k-medoids,  (Exp A1–A4)
           dendrograms, kNN classification, shortest path.
```

Layer 1 must land first: the applications are only justified once the
`d_I ≈ HGED` faithfulness (Theorem B) is empirically established. An application
that works is *because* the stability holds in that regime.

## Files

- `correlation.md` — Layer 1. HGED definition + oracle tiering (exact / BP-GED /
  perturbation-ladder), the correlation experiments E1–E3, the density-sweep
  that validates Theorem B's `C(k,Δ)`, and the information-content (bits)
  comparison.
- `applications.md` — Layer 2. MDS-forward. Each application, its corpus, its
  performance metric, and which competitors can run it.

## Mapping to PROPOSAL points

| PROPOSAL point | Empirical treatment |
|---|---|
| §2 central claim (correlation/MI) | `correlation.md` Exp E1 |
| §2 theory↔empirics (density) | `correlation.md` Exp E2 (tests Thm B) |
| §3 information content | `correlation.md` §Information content |
| §4 A1 MDS | `applications.md` §A1 (flagship) |
| §4 A3/A5 clustering, dendrogram | `applications.md` §A2 |
| §4 A6 kNN | `applications.md` §A3 |
| §4 A4 shortest path | `applications.md` §A4 |
| §5 MDS dimension selection | `applications.md` §A1 |
