# T-M5c — Clustering + dendrogram (HGED-free)
**Declared:** 2026-07-08 13:40 CEST (split from T-M5)
**Status:** IN-PROGRESS
**Depends on:** T-M1b, T-M3a–d, T-M4 (+ T-M4' for the real anchor)
**Context to read first:**
- `docs/article/empirical/applications.md` §A2 — k-medoids + dendrogram, metrics
- `.claude/rules/coding_rules.md` — always
**Description:** k-medoids (PAM) + agglomerative dendrogram on `D_I` and
competitors; silhouette/Dunn/DB + ARI/NMI vs planted labels; cophenetic
correlation; medoid-representative reported inline as the PAM `k=1`
degenerate. Report metrics vs corpus density (descriptive; the Theorem-B
Δ-validation is retired at D-ART2). **No HGED.**
**Acceptance:** reproduces `applications.md` §A2 criteria; figures render.
**Out of scope here:** MDS/kNN/path; new `src/` code.
