# Empirical track

**Status:** ACTIVE (v3 rescope 2026-07-18). Breaks down the empirical work of
`docs/article/PROPOSAL.md`. Companion: `../theoretical/` (the theory the
measurements realize).

## The empirical logic (characterize → exploit; discussion evidence last)

```
  GEOMETRY + USEFULNESS  (the paper's body, HGED-free, at scale)   →  applications.md
      A1 MDS measures the geometry (D̂, ν, distortion) and is the      (A1–A4 + the
      flagship map; A2 k-medoids/dendrogram, A3 kNN, A4 path are       G-profiles)
      each licensed by a measured invariant and scored on task
      metrics vs competitors; the sensitivity + ladder profiles
      supply the smoothness evidence and the nauty contrast.

  DISCUSSION EVIDENCE    (small, closes the paper)                 →  correlation.md
      one exact-HGED correlation figure (ours only, no sweep,
      no competitor head-to-head) + the information-content
      (bits) comparison that substantiates the premise.
```

**Why the applications are the body.** They self-validate on task metrics and
on the measured geometry — no HGED oracle — so they run at real scale and carry
the usefulness claim on their own. The HGED relation is a *limit statement*
made in the closing discussion (envelope + impossibility + mechanisms +
one figure); it is evidence for honesty, not a validation layer the
applications depend on. The v2 reading — "the applications work *because*
stability holds" — is retired with the conditional bound; the v3 reading is
"the applications work, as measured, and no bound could have certified it."

## Files

- `applications.md` — **the body**. The geometry measurement (A1: MDS ⇒ `D̂`,
  `ν`, distortion; realizes `../theoretical/geometry.md`), the corpus-level
  profiles (concentration + hubness; local sensitivity `s(e)`; ladder
  response), and the applications (A2 k-medoids + dendrogram, A3 kNN, A4
  shortest path with HGED-free scoring). Each application: its corpus, its
  licence, its task metric, which competitors run it.
- `correlation.md` — **the discussion evidence**. The HGED definition + exact
  oracle (kept: it produces the single §5 figure and grounds the ladder
  budgets), the rescoped correlation figure E1', and the information-content
  (bits) comparison. The v2 density sweep and HGED head-to-head are recorded
  as out-of-scope.

## Mapping to PROPOSAL points

| PROPOSAL point | Empirical treatment |
|---|---|
| §2 geometry: `D̂`, `ν`, distortion | `applications.md` A1 (MDS) ← `../theoretical/geometry.md` |
| §2 concentration + hubness | `applications.md` G1 |
| §2 sensitivity + ladder profiles | `applications.md` G2 |
| §3 A1 MDS (flagship + geometry) | `applications.md` A1 |
| §3 A2 clustering + dendrogram | `applications.md` A2 |
| §3 A3 kNN | `applications.md` A3 |
| §3 A4 shortest path | `applications.md` A4 |
| §4 compactness (bits) | `correlation.md` §Information content |
| §5 discussion figure (ρ vs exact HGED) | `correlation.md` E1' |
